#!/usr/bin/env python3
"""
aruco_box_detector.py  –  Dexter Inventory ArUco Localizer (production)
========================================================================
Camera at (1.0, 0, 6.0 m), pitch=π/2, 80° FOV, 1280×720.

Publishes:
    /inventory/box_poses    (std_msgs/String  JSON)
    /inventory/gripper_pose (std_msgs/String  JSON)

NO cv_bridge — raw byte decoding avoids NumPy 1.x/2.x ABI crash.
Homography strictly requires 4 reference markers (OpenCV minimum).
Multi-scale (1× + 2×) + 6 preprocessing variants + 3 param sets.

Reference markers (IDs 1-4, 200 mm, floor level):
    ID 1  (-600, -1900) mm   front-left
    ID 2  (2000, -1900) mm   back-right
    ID 3  (-600, +1900) mm   front-right
    ID 4  (2000, +1900) mm   back-left

Box markers (IDs 10-13, 150 mm):
    ID 10  slot 0  (1048, -642,  1218) mm
    ID 11  slot 1  (1209, -220,  1280) mm  ← raised 6 cm vs default
    ID 12  slot 2  (1209, +220,  1218) mm
    ID 13  slot 3  (1048, +642,  1218) mm

Gripper tip marker (ID 21, 120 mm) on claw_support link.

Parallax correction (6 m camera):
    t = (6000 - z_object) / 6000
    t_box  = (6000 - 1218) / 6000 = 0.7970
    t_box1 = (6000 - 1280) / 6000 = 0.7867   (slot 1 raised)
    t_grip = (6000 -  850) / 6000 = 0.8583   (gripper tip approx)

box_poses JSON schema per slot:
    {
        "0": {"x": 1.048, "y": -0.642, "z": 1.218,
              "detected": true, "yaw_deg": 0.0,
              "err_mm": 5.2},
        ...
    }

gripper_pose JSON schema:
    {"x": ..., "y": ..., "detected": true/false}
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
from sensor_msgs.msg import Image, CameraInfo

# ── Camera / world constants ──────────────────────────────────────────────────
CAM_X_MM: float = 1000.0
CAM_Y_MM: float =    0.0
CAM_Z_MM: float = 6000.0      # 6 m

BOX_Z = {0: 1218.0, 1: 1280.0, 2: 1218.0, 3: 1218.0}   # mm, slot-specific
GRIP_Z_MM: float = 850.0       # approx claw_support height at pick pose

T_BOX  = {s: (CAM_Z_MM - z) / CAM_Z_MM for s, z in BOX_Z.items()}
T_GRIP = (CAM_Z_MM - GRIP_Z_MM) / CAM_Z_MM   # 0.8583

REF_WORLD: Dict[int, List[float]] = {
    1: [ -600.0, -1900.0],
    2: [ 2000.0, -1900.0],
    3: [ -600.0, +1900.0],
    4: [ 2000.0, +1900.0],
}
SLOT_GT: Dict[int, Tuple[float, float]] = {
    0: (1048.0, -642.0),
    1: (1209.0, -220.0),
    2: (1209.0, +220.0),
    3: (1048.0, +642.0),
}
BOX_TO_SLOT: Dict[int, int] = {10: 0, 11: 1, 12: 2, 13: 3}

SHOW_WINDOW = os.environ.get("ARUCO_SHOW_WINDOW", "1") != "0"

_C_REF  = ( 20, 180, 255)
_C_BOX  = (  0, 220,  80)
_C_GRIP = (  0,  80, 255)
_C_ARM  = (255, 120,  30)
_C_OK   = (  0, 220,   0)
_C_WARN = (  0, 120, 255)


# ── ArUco detector factory ────────────────────────────────────────────────────

def _make_params(min_p: float, tc: float, tmax: int):
    p = cv2.aruco.DetectorParameters()
    for attr, val in {
        "cornerRefinementMethod":               getattr(cv2.aruco, "CORNER_REFINE_SUBPIX", 2),
        "cornerRefinementWinSize":              5,
        "cornerRefinementMaxIterations":        50,
        "cornerRefinementMinAccuracy":          0.05,
        "minMarkerPerimeterRate":               min_p,
        "maxMarkerPerimeterRate":               4.0,
        "polygonalApproxAccuracyRate":          0.10,
        "errorCorrectionRate":                  0.90,
        "minDistanceToBorder":                  1,
        "adaptiveThreshWinSizeMin":             3,
        "adaptiveThreshWinSizeMax":             tmax,
        "adaptiveThreshWinSizeStep":            4,
        "adaptiveThreshConstant":               tc,
        "perspectiveRemovePixelPerCell":        4,
        "perspectiveRemoveIgnoredMarginPerCell":0.13,
    }.items():
        try:
            setattr(p, attr, val)
        except (AttributeError, TypeError):
            pass
    return p

_ADICT = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
_PARAMS = [
    _make_params(0.004, 7.0,  35),
    _make_params(0.002, 5.0,  51),
    _make_params(0.002, 11.0, 23),
]
_NEW_API = False
try:
    _DETECTORS = [cv2.aruco.ArucoDetector(_ADICT, p) for p in _PARAMS]
    _NEW_API   = True
except AttributeError:
    _DETECTORS = [(_ADICT, p) for p in _PARAMS]


def _detect_one(det, gray):
    if _NEW_API:
        return det.detectMarkers(gray)
    d, p = det
    return cv2.aruco.detectMarkers(gray, d, parameters=p)


def _detect_all(gray: np.ndarray) -> Dict[int, tuple]:
    """Multi-scale (1× + 2×), multi-param, multi-preprocessing detection."""
    best: Dict[int, tuple] = {}
    for sc in (1.0, 2.0):
        g = gray if sc == 1.0 else cv2.resize(
            gray, None, fx=sc, fy=sc, interpolation=cv2.INTER_LINEAR)
        for proc in _preprocess(g):
            for det in _DETECTORS:
                try:
                    corners, ids, _ = _detect_one(det, proc)
                except Exception:
                    continue
                if ids is None:
                    continue
                for i, mid in enumerate(ids.flatten()):
                    c = (corners[i][0] / sc).reshape(1, 4, 2)
                    area = cv2.contourArea(c[0])
                    if mid not in best or area > best[mid][1]:
                        best[mid] = (c, area)
    return best


def _preprocess(gray: np.ndarray) -> List[np.ndarray]:
    norm  = cv2.normalize(gray, None, 0, 255, cv2.NORM_MINMAX)
    clahe = cv2.createCLAHE(clipLimit=3.5, tileGridSize=(8, 8)).apply(norm)
    lut   = (np.arange(256, dtype=np.float32) / 255.0) ** (1.0 / 1.6) * 255
    gamma = cv2.LUT(clahe, lut.astype(np.uint8))
    kern  = np.array([[-1,-1,-1],[-1,9,-1],[-1,-1,-1]])
    sharp = cv2.filter2D(clahe, -1, kern)
    bilat = cv2.bilateralFilter(norm, 9, 75, 75)
    _, otsu = cv2.threshold(clahe, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return [norm, clahe, gamma, sharp, bilat, otsu]


# ── Image decoder (no cv_bridge) ──────────────────────────────────────────────

def _ros_to_bgr(msg) -> np.ndarray:
    enc = msg.encoding.lower().replace("-", "")
    h, w = msg.height, msg.width
    raw  = np.frombuffer(bytes(msg.data), dtype=np.uint8)
    if enc in ("bgr8", "8uc3"):   return raw.reshape(h, w, 3).copy()
    if enc == "rgb8":             return cv2.cvtColor(raw.reshape(h, w, 3), cv2.COLOR_RGB2BGR)
    if enc in ("bgra8", "8uc4"): return cv2.cvtColor(raw.reshape(h, w, 4), cv2.COLOR_BGRA2BGR)
    if enc == "rgba8":           return cv2.cvtColor(raw.reshape(h, w, 4), cv2.COLOR_RGBA2BGR)
    if enc in ("mono8", "8uc1"): return cv2.cvtColor(raw.reshape(h, w),   cv2.COLOR_GRAY2BGR)
    try:    return raw.reshape(h, w, 3).copy()
    except: raise ValueError(f"Unsupported encoding: {msg.encoding}")


# ── Node ──────────────────────────────────────────────────────────────────────

class ArucoBoxDetector(Node):

    def __init__(self):
        super().__init__("aruco_box_detector")

        self.poses_pub   = self.create_publisher(String, "/inventory/box_poses",    10)
        self.gripper_pub = self.create_publisher(String, "/inventory/gripper_pose", 10)

        # Homography state
        self._H_history: deque = deque(maxlen=15)
        self._H: Optional[np.ndarray] = None

        # Pose smoothing (per marker)
        self._pose_hist: Dict[int, deque] = {}

        # Fallback slot poses (FK table)
        self._slot_pos: Dict[int, dict] = {
            s: {"x": gx/1000, "y": gy/1000,
                "z": BOX_Z[s]/1000,
                "detected": False, "yaw_deg": 0.0, "err_mm": -1.0}
            for s, (gx, gy) in SLOT_GT.items()
        }
        self._grip_pos: dict = {"x": 0.0, "y": 0.0, "detected": False}

        self._lock       = threading.Lock()
        self._disp_lock  = threading.Lock()
        self._disp_frame: Optional[np.ndarray] = None

        self._fps_cnt = 0
        self._fps_ts  = time.time()
        self._fps     = 0.0
        self._last_frm = 0.0

        self.create_subscription(Image, "/camera/image_raw", self._img_cb, 1)
        self.create_timer(0.2, self._publish_cb)
        self.create_timer(5.0, self._watchdog_cb)

        self.get_logger().info(
            f"ArucoBoxDetector ready  cam={CAM_Z_MM/1000:.0f}m  "
            f"cv_window={'ON' if SHOW_WINDOW else 'OFF'}")

    # ── display frame ─────────────────────────────────────────────────────────

    def get_display_frame(self) -> Optional[np.ndarray]:
        with self._disp_lock:
            return self._disp_frame.copy() if self._disp_frame is not None else None

    # ── image callback ─────────────────────────────────────────────────────────

    def _img_cb(self, msg):
        self._last_frm = time.time()
        try:
            frame = _ros_to_bgr(msg)
        except Exception as e:
            self.get_logger().warn(f"decode: {e}")
            return
        try:
            self._process(frame)
        except Exception as e:
            self.get_logger().warn(f"process: {e}")

    def _watchdog_cb(self):
        if self._last_frm == 0.0:
            self.get_logger().warn("No frames on /camera/image_raw")
        elif time.time() - self._last_frm > 5.0:
            self.get_logger().warn("Camera feed stalled > 5 s")

    # ── homography ────────────────────────────────────────────────────────────

    def _update_H(self, pix_pts: List, world_pts: List):
        if len(pix_pts) < 4:   # OpenCV hard minimum
            return
        H, _ = cv2.findHomography(
            np.array(pix_pts, np.float32),
            np.array(world_pts, np.float32),
            cv2.RANSAC, 5.0)
        if H is None:
            return
        self._H_history.append(H)
        self._H = (np.median(np.array(list(self._H_history)), axis=0)
                   if len(self._H_history) >= 3 else H)

    def _px2world(self, px: float, py: float, t: float
                  ) -> Tuple[Optional[float], Optional[float]]:
        if self._H is None:
            return None, None
        w  = cv2.perspectiveTransform(
            np.array([[[px, py]]], np.float32), self._H)
        xf = float(w[0, 0, 0])
        yf = float(w[0, 0, 1])
        return (CAM_X_MM + t * (xf - CAM_X_MM),
                CAM_Y_MM + t * (yf - CAM_Y_MM))

    def _world2px(self, xw: float, yw: float) -> Optional[Tuple[int, int]]:
        if self._H is None:
            return None
        Hi = np.linalg.inv(self._H)
        p  = cv2.perspectiveTransform(
            np.array([[[xw, yw]]], np.float32), Hi)
        return (int(p[0, 0, 0]), int(p[0, 0, 1]))

    # ── pose smoothing ────────────────────────────────────────────────────────

    def _smooth(self, mid: int, x: float, y: float,
                yaw: float) -> Tuple[float, float, float]:
        now = time.time()
        if mid not in self._pose_hist:
            self._pose_hist[mid] = deque(maxlen=8)
        h = self._pose_hist[mid]
        h.append((x, y, yaw, now))
        # prune stale
        while h and now - h[0][3] > 3.0:
            h.popleft()
        return (float(np.median([p[0] for p in h])),
                float(np.median([p[1] for p in h])),
                float(np.median([p[2] for p in h])))

    @staticmethod
    def _yaw(corners: np.ndarray) -> float:
        dx = corners[1, 0] - corners[0, 0]
        dy = corners[1, 1] - corners[0, 1]
        return round(math.degrees(math.atan2(dy, dx)), 1)

    # ── main processing ───────────────────────────────────────────────────────

    def _process(self, frame: np.ndarray):
        # FPS
        self._fps_cnt += 1
        now = time.time()
        if now - self._fps_ts >= 1.0:
            self._fps = self._fps_cnt / (now - self._fps_ts)
            self._fps_cnt = 0
            self._fps_ts  = now

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        best = _detect_all(gray)
        vis  = frame.copy()

        # collect refs → update H
        ref_pix, ref_wld = [], []
        for mid, (ci, _) in best.items():
            if int(mid) in REF_WORLD:
                ref_pix.append(ci[0].mean(axis=0))
                ref_wld.append(REF_WORLD[int(mid)])
        self._update_H(ref_pix, ref_wld)

        # draw ArUco outlines
        if best:
            c_list = [v[0] for v in best.values()]
            id_arr = np.array([[k] for k in best.keys()], dtype=np.int32)
            cv2.aruco.drawDetectedMarkers(vis, c_list, id_arr)

        # draw expected grid
        if self._H is not None:
            try:
                Hi = np.linalg.inv(self._H)
                pts = np.array([REF_WORLD[1], REF_WORLD[2],
                                REF_WORLD[4], REF_WORLD[3]], np.float32)
                proj = cv2.perspectiveTransform(pts.reshape(1,-1,2), Hi)[0].astype(int)
                cv2.polylines(vis, [proj.reshape(-1,1,2)], True, (50,50,160), 2)
                for s, (sx, sy) in SLOT_GT.items():
                    px = self._world2px(sx, sy)
                    if px:
                        cv2.drawMarker(vis, px, (0,140,50), cv2.MARKER_CROSS, 22, 2)
                        cv2.putText(vis, f"S{s}", (px[0]+6,px[1]-6),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0,140,50), 1)
            except Exception:
                pass

        # annotate & compute world positions
        new_slots: Dict[int, dict] = {}
        new_grip:  Optional[dict]  = None

        for mid, (ci, _) in best.items():
            ctr = ci[0].mean(axis=0).astype(int)
            ix, iy = int(ctr[0]), int(ctr[1])
            yaw    = self._yaw(ci[0])

            if int(mid) in REF_WORLD:
                cv2.circle(vis, (ix,iy), 10, _C_REF, -1)
                cv2.putText(vis, f"REF{mid}", (ix+14,iy-8),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.50, _C_REF, 2)

            elif int(mid) in BOX_TO_SLOT and self._H is not None:
                slot = BOX_TO_SLOT[int(mid)]
                t    = T_BOX[slot]
                xw, yw = self._px2world(float(ix), float(iy), t)
                if xw is None:
                    continue
                sx, sy, syaw = self._smooth(int(mid), xw, yw, yaw)
                xm, ym = sx / 1000.0, sy / 1000.0
                ex, ey = SLOT_GT[slot]
                err_mm = math.hypot(sx - ex, sy - ey)

                # sanity bounds (world workspace)
                if not (0.5 < xm < 1.7 and -1.1 < ym < 1.1):
                    continue

                new_slots[slot] = {
                    "x": round(xm, 4), "y": round(ym, 4),
                    "z": round(BOX_Z[slot] / 1000.0, 4),
                    "detected": True,
                    "yaw_deg":  round(syaw, 1),
                    "err_mm":   round(err_mm, 1),
                }

                cv2.circle(vis, (ix,iy), 12, _C_BOX, -1)
                cv2.circle(vis, (ix,iy), 16, _C_BOX,  2)
                cv2.putText(vis, f"S{slot}({xm:.3f},{ym:.3f})",
                            (ix+16, iy-10), cv2.FONT_HERSHEY_SIMPLEX,
                            0.52, _C_BOX, 2)
                cv2.putText(vis, f"err={err_mm:.0f}mm",
                            (ix+16, iy+12), cv2.FONT_HERSHEY_SIMPLEX,
                            0.40, _C_BOX, 1)

            elif int(mid) == 21 and self._H is not None:
                xw, yw = self._px2world(float(ix), float(iy), T_GRIP)
                if xw is None:
                    continue
                sx, sy, syaw = self._smooth(21, xw, yw, yaw)
                xm, ym = sx / 1000.0, sy / 1000.0

                new_grip = {
                    "x": round(xm, 4), "y": round(ym, 4),
                    "detected": True, "yaw_deg": round(syaw, 1),
                }

                cv2.circle(vis, (ix,iy), 14, _C_GRIP, -1)
                cv2.circle(vis, (ix,iy), 20, _C_GRIP,  3)
                cv2.putText(vis, f"GRIP({xm:.3f},{ym:.3f})",
                            (ix+18, iy-10), cv2.FONT_HERSHEY_SIMPLEX,
                            0.52, _C_GRIP, 2)

        # update shared state
        with self._lock:
            for slot, info in new_slots.items():
                self._slot_pos[slot] = info
            for slot in range(4):
                if slot not in new_slots:
                    self._slot_pos[slot]["detected"] = False
            if new_grip:
                self._grip_pos = new_grip
            else:
                self._grip_pos["detected"] = False

        # HUD
        refs_seen = sum(1 for m in best if m in REF_WORLD)
        h_ok      = self._H is not None
        ov = vis.copy()
        cv2.rectangle(ov, (0,0), (680,110), (8,8,8), -1)
        cv2.addWeighted(ov, 0.72, vis, 0.28, 0, vis)
        cv2.putText(vis,
            f"FPS:{self._fps:.1f}  Refs:{refs_seen}/4  "
            f"Hom:{'LOCKED' if h_ok else f'need {4-refs_seen} more'}",
            (8,22), cv2.FONT_HERSHEY_SIMPLEX, 0.52,
            _C_OK if h_ok else _C_WARN, 1)
        with self._lock:
            detected_slots = [s for s in range(4) if self._slot_pos[s]["detected"]]
            missing_slots  = [s for s in range(4) if not self._slot_pos[s]["detected"]]
        cv2.putText(vis,
            f"Detected slots: {detected_slots}  FK fallback: {missing_slots}",
            (8,46), cv2.FONT_HERSHEY_SIMPLEX, 0.50, _C_BOX, 1)
        with self._lock:
            gd = self._grip_pos.get("detected", False)
            gx = self._grip_pos.get("x", 0)
            gy = self._grip_pos.get("y", 0)
        cv2.putText(vis,
            f"Gripper: {'({:.3f},{:.3f})m'.format(gx,gy) if gd else 'not visible'}",
            (8,70), cv2.FONT_HERSHEY_SIMPLEX, 0.50,
            _C_GRIP if gd else (80,80,80), 1)
        cv2.putText(vis, "Publishing /inventory/box_poses  /inventory/gripper_pose",
            (8,92), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (80,80,80), 1)

        with self._disp_lock:
            self._disp_frame = cv2.resize(vis, (960, 540))

    # ── publish ───────────────────────────────────────────────────────────────

    def _publish_cb(self):
        with self._lock:
            box_pl  = {str(s): dict(info) for s, info in self._slot_pos.items()}
            grip_pl = dict(self._grip_pos)

        msg_b = String(); msg_b.data = json.dumps(box_pl)
        msg_g = String(); msg_g.data = json.dumps(grip_pl)
        self.poses_pub.publish(msg_b)
        self.gripper_pub.publish(msg_g)


# ── Entry point ───────────────────────────────────────────────────────────────

def main(args=None):
    rclpy.init(args=args)
    node = ArucoBoxDetector()

    spin_t = threading.Thread(target=rclpy.spin, args=(node,), daemon=True)
    spin_t.start()

    if SHOW_WINDOW:
        os.environ.setdefault("QT_QPA_PLATFORM", "xcb")
        try:
            cv2.namedWindow("Dexter ArUco", cv2.WINDOW_NORMAL)
            cv2.resizeWindow("Dexter ArUco", 960, 540)
            placeholder = np.zeros((540, 960, 3), dtype=np.uint8)
            cv2.putText(placeholder, "Waiting for /camera/image_raw ...",
                        (160, 270), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (60,60,60), 2)
            cv2.imshow("Dexter ArUco", placeholder)
            cv2.waitKey(1)
            node.get_logger().info("OpenCV window open | press Q to quit")
        except Exception as e:
            node.get_logger().warn(f"Could not open window: {e}")

    try:
        while rclpy.ok() and spin_t.is_alive():
            if SHOW_WINDOW:
                f = node.get_display_frame()
                if f is not None:
                    try:
                        cv2.imshow("Dexter ArUco", f)
                    except Exception:
                        pass
                key = cv2.waitKey(30) & 0xFF
                if key in (ord('q'), 27):
                    break
            else:
                time.sleep(0.05)
    except KeyboardInterrupt:
        pass
    finally:
        if SHOW_WINDOW:
            try: cv2.destroyAllWindows()
            except Exception: pass
        node.destroy_node()
        try: rclpy.shutdown()
        except Exception: pass


if __name__ == "__main__":
    main()
