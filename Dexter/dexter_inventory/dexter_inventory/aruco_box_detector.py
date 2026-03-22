#!/usr/bin/env python3
"""
aruco_box_detector.py  –  Dexter Inventory ArUco Localizer
===========================================================
Always shows an OpenCV window (set ARUCO_SHOW_WINDOW=0 to disable).

The window shows:
  - All detected markers drawn with IDs
  - Reference marker positions (cyan dots + labels)
  - Homography grid projected back onto image
  - Box-slot crosshairs (where the arm will go)
  - Status panel: FPS, homography state, per-slot detection info
"""

from __future__ import annotations

import json
import math
import os
import threading
import time
from collections import deque
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

try:
    from sensor_msgs.msg import Image
    from cv_bridge import CvBridge
    _ROS_IMG_OK = True
except ImportError:
    _ROS_IMG_OK = False

# ── Config ────────────────────────────────────────────────────────────────────

USE_GAZEBO_CAM   = True
USE_IP_WEBCAM    = False
IP_WEBCAM_URL    = "http://192.168.1.100:8080/video"
GAZEBO_IMG_TOPIC = "/camera/image_raw"
USB_CAMERA_INDEX = 0

SHOW_WINDOW = os.environ.get("ARUCO_SHOW_WINDOW", "1") != "0"

REF_WORLD_MM: Dict[int, List[float]] = {
    1: [500.0,  -650.0],   # front-left
    # Matches inventory.sdf ref_marker positions,
    2: [1550.0, -650.0],   # front-right
    3: [500.0,  +650.0],   # back-left
    4: [1550.0, +650.0],   # back-right
}
REF_IDS = list(REF_WORLD_MM.keys())

BOX_MARKER_TO_SLOT: Dict[int, int] = {10: 0, 11: 1, 12: 2, 13: 3}

SLOT_FALLBACK_M: Dict[int, Tuple[float, float]] = {
    0: (1.048, -0.642),
    1: (1.209, -0.220),
    2: (1.209, +0.220),
    3: (1.048, +0.642),
}
BOX_Z_M      = 1.156
H_HISTORY    = 10
POSE_HISTORY = 5
POSE_TIMEOUT = 2.0

COL_REF    = (0,  200, 255)
COL_DET    = (0,  255, 100)
COL_FALLBK = (80, 80,  80)
COL_WARN   = (0,  100, 255)
COL_OK     = (0,  220, 0)
COL_GRID   = (180, 30, 30)


class ArucoBoxDetector(Node):

    def __init__(self):
        super().__init__("aruco_box_detector")

        self.poses_pub = self.create_publisher(String, "/inventory/box_poses", 10)

        d = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
        p = cv2.aruco.DetectorParameters()
        p.cornerRefinementMethod        = cv2.aruco.CORNER_REFINE_SUBPIX
        p.minMarkerPerimeterRate        = 0.02
        p.maxMarkerPerimeterRate        = 0.9
        p.polygonalApproxAccuracyRate   = 0.10
        p.errorCorrectionRate           = 0.8
        p.minDistanceToBorder           = 2
        p.adaptiveThreshWinSizeMin      = 3
        p.adaptiveThreshWinSizeMax      = 23
        p.adaptiveThreshWinSizeStep     = 4
        p.adaptiveThreshConstant        = 7
        p.cornerRefinementWinSize       = 5
        p.cornerRefinementMaxIterations = 50
        p.cornerRefinementMinAccuracy   = 0.005
        p.perspectiveRemovePixelPerCell = 8
        p.perspectiveRemoveIgnoredMarginPerCell = 0.13
        self.detector = cv2.aruco.ArucoDetector(d, p)

        self.H_matrix  : Optional[np.ndarray] = None
        self.stable_H  : Optional[np.ndarray] = None
        self.H_history : deque = deque(maxlen=H_HISTORY)
        self.pose_hist : Dict[int, deque] = {}
        self._lock     = threading.Lock()
        self._fps_cnt  = 0
        self._fps_ts   = time.time()
        self._fps      = 0.0

        self.slot_pos: Dict[int, dict] = {
            s: {"x": fx, "y": fy, "z": BOX_Z_M,
                "detected": False, "yaw_deg": 0.0}
            for s, (fx, fy) in SLOT_FALLBACK_M.items()
        }

        self.cam_mtx = np.array([[1200, 0, 640],
                                  [0, 1200, 360],
                                  [0, 0, 1]], dtype=np.float32)
        self.dist    = np.zeros(4, dtype=np.float32)

        if USE_GAZEBO_CAM and _ROS_IMG_OK:
            self.bridge    = CvBridge()
            self._last_frm = 0.0
            self.image_sub = self.create_subscription(
                Image, GAZEBO_IMG_TOPIC, self._ros_cb, 10)
            self.create_timer(5.0, self._watchdog)
            self.get_logger().info(
                f"Subscribed to {GAZEBO_IMG_TOPIC}")
        else:
            self._start_cam()

        self.create_timer(0.2, self._publish)

        self.get_logger().info("=" * 60)
        self.get_logger().info("ArucoBoxDetector ready")
        self.get_logger().info(
            f"  Window: {'ENABLED' if SHOW_WINDOW else 'disabled (set ARUCO_SHOW_WINDOW=1)'}")
        for mid, (wx, wy) in REF_WORLD_MM.items():
            self.get_logger().info(
                f"  REF ID {mid}: x={wx:.0f}mm  y={wy:.0f}mm")
        self.get_logger().info("=" * 60)

    def _start_cam(self):
        url = IP_WEBCAM_URL if USE_IP_WEBCAM else USB_CAMERA_INDEX
        self.cap = cv2.VideoCapture(url)
        if not self.cap.isOpened():
            self.get_logger().error(f"Camera open failed: {url}")
            return
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        threading.Thread(target=self._cap_loop, daemon=True).start()

    def _cap_loop(self):
        while rclpy.ok():
            ret, frame = self.cap.read()
            if ret:
                self._process(frame)
            else:
                time.sleep(0.05)

    def _ros_cb(self, msg):
        try:
            frame = self.bridge.imgmsg_to_cv2(msg, "bgr8")
            self._last_frm = time.time()
            self._process(frame)
        except Exception as e:
            self.get_logger().error(f"ros_cb: {e}")

    def _watchdog(self):
        if not hasattr(self, "_last_frm"):
            return
        if self._last_frm == 0.0:
            self.get_logger().warn(
                f"No frames from {GAZEBO_IMG_TOPIC} — "
                "check ros2 topic hz /camera/image_raw")
        elif time.time() - self._last_frm > 5.0:
            self.get_logger().warn("Camera feed stalled")

    def _preprocess(self, g: np.ndarray) -> List[np.ndarray]:
        n  = cv2.normalize(g, None, 0, 255, cv2.NORM_MINMAX)
        cl = cv2.createCLAHE(4.0, (8, 8)).apply(n)
        ga = cv2.LUT(cl, (np.arange(256)/255.0**(1/0.7)*255).astype(np.uint8))
        bi = cv2.bilateralFilter(ga, 9, 75, 75)
        sh = cv2.filter2D(bi, -1, np.array([[-1,-1,-1],[-1,9,-1],[-1,-1,-1]]))
        return [n, ga, sh]

    def _detect(self, gray: np.ndarray):
        best: Dict[int, tuple] = {}
        for proc in self._preprocess(gray):
            corners, ids, _ = self.detector.detectMarkers(proc)
            if ids is None:
                continue
            for i, mid in enumerate(ids.flatten()):
                area = cv2.contourArea(corners[i][0])
                if mid not in best or area > best[mid][1]:
                    best[mid] = (corners[i], area)
        if not best:
            return None, None
        return ([v[0] for v in best.values()],
                np.array([[k] for k in best]))

    def _update_H(self, pix: List, world: List):
        if len(pix) < 4:
            return
        H, _ = cv2.findHomography(
            np.array(pix, dtype=np.float32),
            np.array(world, dtype=np.float32),
            cv2.RANSAC, 5.0)
        if H is None:
            return
        self.H_matrix = H
        self.H_history.append(H)
        self.stable_H = (np.median(np.array(list(self.H_history)), axis=0)
                         if len(self.H_history) >= 3 else H)

    def _px2mm(self, px: float, py: float):
        H = self.stable_H or self.H_matrix
        if H is None:
            return None, None
        w = cv2.perspectiveTransform(
            np.array([[[px, py]]], dtype=np.float32), H)
        return float(w[0, 0, 0]), float(w[0, 0, 1])

    @staticmethod
    def _yaw(c: np.ndarray) -> float:
        dx, dy = c[1, 0]-c[0, 0], c[1, 1]-c[0, 1]
        d = math.degrees(math.atan2(dy, dx))
        if d < 0: d += 360
        return d if d < 180 else -(360 - d)

    def _smooth(self, mid: int, x: float, y: float, yaw: float):
        now = time.time()
        if mid not in self.pose_hist:
            self.pose_hist[mid] = deque(maxlen=POSE_HISTORY)
        h = self.pose_hist[mid]
        h.append((x, y, yaw, now))
        while h and now - h[0][3] > POSE_TIMEOUT:
            h.popleft()
        return (float(np.median([p[0] for p in h])),
                float(np.median([p[1] for p in h])),
                float(np.median([p[2] for p in h])))

    def _process(self, frame: np.ndarray):
        # FPS
        self._fps_cnt += 1
        now = time.time()
        if now - self._fps_ts >= 1.0:
            self._fps     = self._fps_cnt / (now - self._fps_ts)
            self._fps_cnt = 0
            self._fps_ts  = now

        und  = cv2.undistort(frame, self.cam_mtx, self.dist)
        gray = cv2.cvtColor(und, cv2.COLOR_BGR2GRAY)
        corners, ids = self._detect(gray)

        vis = und.copy()
        if ids is not None:
            cv2.aruco.drawDetectedMarkers(vis, corners, ids)

        # Collect reference markers
        ref_pix, ref_world, ref_seen = [], [], []
        if ids is not None:
            for i, mid in enumerate(ids.flatten()):
                if mid in REF_IDS:
                    ctr = corners[i][0].mean(axis=0)
                    ref_pix.append(ctr)
                    ref_world.append(REF_WORLD_MM[mid])
                    ref_seen.append(mid)
                    cx, cy = int(ctr[0]), int(ctr[1])
                    cv2.circle(vis, (cx, cy), 9, COL_REF, -1)
                    cv2.putText(vis, f"REF {mid}",
                                (cx+12, cy-8),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.55, COL_REF, 2)

        self._update_H(ref_pix, ref_world)
        H = self.stable_H or self.H_matrix

        # Draw grid
        if H is not None and len(ref_pix) >= 2:
            self._draw_grid(vis, H)

        # Detect box markers
        if H is not None and ids is not None:
            with self._lock:
                for i, mid in enumerate(ids.flatten()):
                    if mid not in BOX_MARKER_TO_SLOT:
                        continue
                    slot = BOX_MARKER_TO_SLOT[mid]
                    c    = corners[i][0]
                    px   = float(c[:, 0].mean())
                    py   = float(c[:, 1].mean())
                    xmm, ymm = self._px2mm(px, py)
                    if xmm is None:
                        continue
                    yaw = self._yaw(c)
                    sx, sy, sdeg = self._smooth(mid, xmm, ymm, yaw)
                    xm, ym = sx/1000.0, sy/1000.0
                    if not (0.5 < xm < 1.8 and -1.2 < ym < 1.2):
                        continue
                    self.slot_pos[slot] = {
                        "x": round(xm, 4), "y": round(ym, 4),
                        "z": BOX_Z_M, "detected": True,
                        "yaw_deg": round(sdeg, 1),
                    }
                    ix, iy = int(px), int(py)
                    cv2.circle(vis, (ix, iy), 7, COL_DET, -1)
                    cv2.putText(vis,
                                f"S{slot} ({xm:.3f},{ym:.3f}m)",
                                (ix, iy-28),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, COL_DET, 2)

        # Status overlay
        self._status(vis, len(ref_seen), ref_seen, H)

        if SHOW_WINDOW:
            try:
                disp = cv2.resize(vis, (960, 540))
                cv2.imshow("Dexter ArUco Detector", disp)
                cv2.waitKey(1)
            except Exception as e:
                pass  # headless — silently ignore

    def _draw_grid(self, vis: np.ndarray, H: np.ndarray):
        try:
            Hi = np.linalg.inv(H)
            pts = np.array([REF_WORLD_MM[1], REF_WORLD_MM[2],
                            REF_WORLD_MM[4], REF_WORLD_MM[3]],
                           dtype=np.float32)
            proj = cv2.perspectiveTransform(
                pts.reshape(1, -1, 2), Hi)[0].astype(int)
            cv2.polylines(vis, [proj.reshape(-1, 1, 2)], True, COL_GRID, 2)
            for slot, (fx, fy) in SLOT_FALLBACK_M.items():
                w = cv2.perspectiveTransform(
                    np.array([[[fx*1000, fy*1000]]], dtype=np.float32), Hi)
                ix, iy = int(w[0,0,0]), int(w[0,0,1])
                cv2.drawMarker(vis, (ix, iy),
                               (255, 180, 0), cv2.MARKER_CROSS, 20, 2)
                cv2.putText(vis, f"S{slot}", (ix+7, iy-7),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,180,0), 1)
        except Exception:
            pass

    def _status(self, vis: np.ndarray, ref_cnt: int,
                ref_seen: List[int], H):
        h_ok  = H is not None
        lines = [
            (f"FPS: {self._fps:.1f}", (180, 180, 180)),
            (f"Homography: {'OK ✓' if h_ok else 'WAITING — need 4 refs'}",
             COL_OK if h_ok else COL_WARN),
            (f"Refs visible: {ref_cnt}/4   IDs={ref_seen}",
             COL_OK if ref_cnt == 4 else (COL_WARN if ref_cnt >= 2 else (0,0,200))),
        ]
        for slot, info in self.slot_pos.items():
            col  = COL_DET if info["detected"] else COL_FALLBK
            mode = "ARUCO" if info["detected"] else "FK fallback"
            lines.append(
                (f"Slot {slot}: {mode}  ({info['x']:.3f},{info['y']:.3f})", col))

        # dark background
        ov = vis.copy()
        cv2.rectangle(ov, (0, 0), (470, 20 + len(lines)*24), (10,10,10), -1)
        cv2.addWeighted(ov, 0.7, vis, 0.3, 0, vis)

        for k, (txt, col) in enumerate(lines):
            cv2.putText(vis, txt, (8, 18 + k*24),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, col,
                        2 if k < 3 else 1)

    def _publish(self):
        with self._lock:
            payload = {str(s): info for s, info in self.slot_pos.items()}
        msg      = String()
        msg.data = json.dumps(payload)
        self.poses_pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = ArucoBoxDetector()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if hasattr(node, "cap"):
            node.cap.release()
        cv2.destroyAllWindows()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
