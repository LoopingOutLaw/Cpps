#!/usr/bin/env python3
"""
aruco_box_detector.py  –  Dexter Inventory ArUco Localizer
===========================================================
Camera at (1.0, 0, 6.0 m), pitch=π/2, 80° FOV, 1280×720.

Floor reference markers at wall corners (IDs 1-4, 200×200 mm):
    ID 1  (-800, -2200) mm   front-left
    ID 2  (2300, -2200) mm   back-right
    ID 3  (-800, +2200) mm   front-right
    ID 4  (2300, +2200) mm   back-left

Arm base floor marker  (ID 5,  150×150 mm) at (0, 0)
Box markers on box tops (IDs 10-13, 90×90 mm)
Arm plate marker        (ID 20, 90×90 mm)  on base_plate link

SEGFAULT FIX:
  cv2.aruco.DetectorParameters has different attributes across OpenCV versions.
  We now set only the attributes that exist at runtime and catch every error.
  cv2.aruco.ArucoDetector was introduced in OpenCV 4.7.  On older builds we
  fall back to the legacy detectMarkers() API.

DISPLAY FIX:
  cv2.namedWindow/imshow MUST run on the main thread.  rclpy.spin() runs on a
  daemon background thread.  All display calls are guarded so a missing DISPLAY
  or headless environment never crashes the node.
"""

from __future__ import annotations

import json
import math
import os
import threading
import time
from collections import deque
from typing import Dict, List, Optional, Tuple

# ── OpenCV import with graceful degradation ────────────────────────────────────
try:
    import cv2
    import numpy as np
    _CV2_OK = True
except ImportError:
    _CV2_OK = False

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from sensor_msgs.msg import Image, CameraInfo
from cv_bridge import CvBridge

# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────

CAM_X_MM: float = 1000.0
CAM_Y_MM: float =    0.0
CAM_Z_MM: float = 6000.0

BOX_Z_MM:       float = 1218.0
ARM_PLATE_Z_MM: float =  457.0

_T_BOX: float = (CAM_Z_MM - BOX_Z_MM)       / CAM_Z_MM   # 0.797
_T_ARM: float = (CAM_Z_MM - ARM_PLATE_Z_MM) / CAM_Z_MM   # 0.924

REF_WORLD_MM: Dict[int, List[float]] = {
    1: [ -800.0, -2200.0],   # front-left  corner
    2: [ 2300.0, -2200.0],   # back-right  corner
    3: [ -800.0, +2200.0],   # front-right corner
    4: [ 2300.0, +2200.0],   # back-left   corner
}
REF_IDS = list(REF_WORLD_MM.keys())

ARM_BASE_MARKER_ID  = 5
ARM_PLATE_MARKER_ID = 20

BOX_MARKER_TO_SLOT: Dict[int, int] = {10: 0, 11: 1, 12: 2, 13: 3}

SLOT_FALLBACK_MM: Dict[int, Tuple[float, float]] = {
    0: (1048.0, -642.0),
    1: (1209.0, -220.0),
    2: (1209.0, +220.0),
    3: (1048.0, +642.0),
}

H_HISTORY    = 12
POSE_HISTORY = 8
POSE_TIMEOUT = 3.0

SHOW_WINDOW = (_CV2_OK and os.environ.get("ARUCO_SHOW_WINDOW", "1") != "0")

_C_REF   = (  0, 200, 255)
_C_BOX   = (  0, 240,  80)
_C_ARM   = (255, 120,  30)
_C_GRID  = (180,  30,  30)
_C_CROSS = (255, 180,   0)
_C_WARN  = (  0, 120, 255)
_C_OK    = (  0, 220,   0)


# ─────────────────────────────────────────────────────────────────────────────
# Safe ArUco detector factory
# Handles OpenCV version differences without crashing
# ─────────────────────────────────────────────────────────────────────────────

def _make_detector():
    """Return (detector_obj, use_new_api: bool).
    Falls back to legacy API if ArucoDetector is unavailable."""
    aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)

    # Build DetectorParameters, only setting attrs that exist in this build
    params = cv2.aruco.DetectorParameters()

    _safe_set = {
        "cornerRefinementMethod":              cv2.aruco.CORNER_REFINE_SUBPIX,
        "cornerRefinementWinSize":             7,
        "cornerRefinementMaxIterations":       60,
        "cornerRefinementMinAccuracy":         0.01,
        "minMarkerPerimeterRate":              0.008,
        "maxMarkerPerimeterRate":              0.90,
        "polygonalApproxAccuracyRate":         0.08,
        "errorCorrectionRate":                 0.75,
        "minDistanceToBorder":                 2,
        "adaptiveThreshWinSizeMin":            3,
        "adaptiveThreshWinSizeMax":            25,
        "adaptiveThreshWinSizeStep":           4,
        "adaptiveThreshConstant":              9.0,
        "perspectiveRemovePixelPerCell":       6,
        "perspectiveRemoveIgnoredMarginPerCell": 0.10,
    }
    for attr, val in _safe_set.items():
        try:
            setattr(params, attr, val)
        except (AttributeError, TypeError):
            pass   # attribute absent in this OpenCV version – skip silently

    # Try new API (OpenCV >= 4.7)
    try:
        detector = cv2.aruco.ArucoDetector(aruco_dict, params)
        return detector, True
    except AttributeError:
        pass

    # Legacy API
    return (aruco_dict, params), False


def _detect_with(detector, gray: "np.ndarray", use_new_api: bool):
    """Run marker detection regardless of API version."""
    if use_new_api:
        return detector.detectMarkers(gray)
    else:
        aruco_dict, params = detector
        return cv2.aruco.detectMarkers(gray, aruco_dict, parameters=params)


# ─────────────────────────────────────────────────────────────────────────────
# Node
# ─────────────────────────────────────────────────────────────────────────────

class ArucoBoxDetector(Node):

    def __init__(self):
        super().__init__("aruco_box_detector")

        if not _CV2_OK:
            self.get_logger().error("opencv-python not installed — detector inactive")
            return

        # Publishers
        self.poses_pub    = self.create_publisher(String, "/inventory/box_poses", 10)
        self.arm_pose_pub = self.create_publisher(String, "/inventory/arm_pose",  10)

        # Build detector safely
        try:
            self._detector, self._new_api = _make_detector()
            self.get_logger().info(
                f"ArUco detector ready  (new API={self._new_api})")
        except Exception as e:
            self.get_logger().error(f"ArUco init failed: {e}")
            self._detector = None
            self._new_api  = False

        # Camera intrinsics (defaults for 1280×720 / 80° FOV)
        self.cam_K = np.array([[762.6, 0.0, 640.0],
                                [0.0, 762.6, 360.0],
                                [0.0, 0.0,   1.0 ]], dtype=np.float64)
        self.cam_dist = np.zeros(5, dtype=np.float64)
        self._cam_info_rcvd = False

        # State
        self.H_matrix  : Optional[np.ndarray] = None
        self.stable_H  : Optional[np.ndarray] = None
        self._H_history: deque = deque(maxlen=H_HISTORY)
        self._pose_hist: Dict[int, deque] = {}
        self._lock = threading.Lock()

        self._fps_cnt = 0
        self._fps_ts  = time.time()
        self._fps     = 0.0
        self._last_frm = 0.0

        self.slot_pos: Dict[int, dict] = {
            s: {"x": fx/1000.0, "y": fy/1000.0,
                "z": BOX_Z_MM/1000.0,
                "detected": False, "yaw_deg": 0.0}
            for s, (fx, fy) in SLOT_FALLBACK_MM.items()
        }
        self.arm_pose: dict = {
            "base_detected":  False, "plate_detected": False,
            "base_x": 0.0, "base_y": 0.0,
            "plate_x": 0.0, "plate_y": 0.0, "plate_yaw_deg": 0.0,
        }

        # Thread-safe display frame (main thread reads this)
        self._display_frame: Optional[np.ndarray] = None
        self._display_lock  = threading.Lock()

        self.bridge = CvBridge()

        self.create_subscription(CameraInfo, "/camera/camera_info", self._camera_info_cb, 10)
        self.create_subscription(Image,      "/camera/image_raw",   self._image_cb, 1)
        self.create_timer(0.2, self._publish_cb)
        self.create_timer(5.0, self._watchdog_cb)

        self.get_logger().info(
            f"ArucoBoxDetector ready  |  cam={CAM_Z_MM/1000:.0f}m  "
            f"t_box={_T_BOX:.3f}  t_arm={_T_ARM:.3f}  "
            f"cv_window={'ON' if SHOW_WINDOW else 'OFF'}")

    # ── display frame (main-thread access) ───────────────────────────────

    def get_display_frame(self) -> Optional["np.ndarray"]:
        with self._display_lock:
            return self._display_frame.copy() if self._display_frame is not None else None

    # ── camera info ───────────────────────────────────────────────────────

    def _camera_info_cb(self, msg: CameraInfo):
        if self._cam_info_rcvd:
            return
        K = np.array(msg.k, dtype=np.float64).reshape(3, 3)
        if K[0, 0] > 1.0:
            self.cam_K = K
        d = np.array(msg.d, dtype=np.float64)
        self.cam_dist = d[:5] if d.shape[0] >= 5 else np.pad(d, (0, max(0, 5-d.shape[0])))
        self._cam_info_rcvd = True
        self.get_logger().info(
            f"CameraInfo: fx={self.cam_K[0,0]:.1f} cx={self.cam_K[0,2]:.1f}")

    # ── image callback ────────────────────────────────────────────────────

    def _image_cb(self, msg: Image):
        if self._detector is None:
            return
        try:
            frame = self.bridge.imgmsg_to_cv2(msg, "bgr8")
        except Exception as e:
            self.get_logger().error(f"imgmsg_to_cv2: {e}")
            return
        self._last_frm = time.time()
        try:
            self._process(frame)
        except Exception as e:
            self.get_logger().warn(f"_process error: {e}")

    def _watchdog_cb(self):
        if self._last_frm == 0.0:
            self.get_logger().warn("No frames yet on /camera/image_raw")
        elif time.time() - self._last_frm > 5.0:
            self.get_logger().warn("Camera feed stalled > 5 s")

    # ── preprocessing ─────────────────────────────────────────────────────

    @staticmethod
    def _preprocess_variants(gray: "np.ndarray") -> List["np.ndarray"]:
        norm  = cv2.normalize(gray, None, 0, 255, cv2.NORM_MINMAX)
        clahe = cv2.createCLAHE(clipLimit=3.5, tileGridSize=(8, 8)).apply(norm)
        lut   = (np.arange(256) / 255.0) ** (1.0 / 1.4) * 255
        gamma = cv2.LUT(clahe, lut.astype(np.uint8))
        kern  = np.array([[-1,-1,-1],[-1,9,-1],[-1,-1,-1]])
        sharp = cv2.filter2D(clahe, -1, kern)
        return [norm, clahe, gamma, sharp]

    # ── detection (version-safe) ──────────────────────────────────────────

    def _detect_markers(self, gray: "np.ndarray"):
        best: Dict[int, tuple] = {}
        for proc in self._preprocess_variants(gray):
            try:
                corners, ids, _ = _detect_with(
                    self._detector, proc, self._new_api)
            except Exception:
                continue
            if ids is None:
                continue
            for i, mid in enumerate(ids.flatten()):
                area = cv2.contourArea(corners[i][0])
                if mid not in best or area > best[mid][1]:
                    best[mid] = (corners[i], area)
        if not best:
            return None, None
        return ([v[0] for v in best.values()],
                np.array([[k] for k in best.keys()], dtype=np.int32))

    # ── homography ────────────────────────────────────────────────────────

    def _update_homography(self, pix_pts, world_pts):
        if len(pix_pts) < 4:
            return
        H, _ = cv2.findHomography(
            np.array(pix_pts, dtype=np.float32),
            np.array(world_pts, dtype=np.float32),
            cv2.RANSAC, 5.0)
        if H is None:
            return
        self.H_matrix = H
        self._H_history.append(H)
        self.stable_H = (np.median(np.array(list(self._H_history)), axis=0)
                         if len(self._H_history) >= 3 else H)

    def _pixel_to_floor_mm(self, px, py):
        H = self.stable_H or self.H_matrix
        if H is None:
            return None, None
        w = cv2.perspectiveTransform(np.array([[[px, py]]], dtype=np.float32), H)
        return float(w[0, 0, 0]), float(w[0, 0, 1])

    @staticmethod
    def _correct_parallax(xf, yf, t):
        return (CAM_X_MM + t * (xf - CAM_X_MM),
                CAM_Y_MM + t * (yf - CAM_Y_MM))

    # ── smoothing ─────────────────────────────────────────────────────────

    def _smooth_pose(self, mid, x_mm, y_mm, yaw):
        now = time.time()
        if mid not in self._pose_hist:
            self._pose_hist[mid] = deque(maxlen=POSE_HISTORY)
        h = self._pose_hist[mid]
        h.append((x_mm, y_mm, yaw, now))
        while h and now - h[0][3] > POSE_TIMEOUT:
            h.popleft()
        return (float(np.median([p[0] for p in h])),
                float(np.median([p[1] for p in h])),
                float(np.median([p[2] for p in h])))

    @staticmethod
    def _marker_yaw(corners):
        dx = corners[1, 0] - corners[0, 0]
        dy = corners[1, 1] - corners[0, 1]
        d  = math.degrees(math.atan2(dy, dx))
        return round(d, 1)

    # ── main processing ───────────────────────────────────────────────────

    def _process(self, frame: "np.ndarray"):
        # FPS
        self._fps_cnt += 1
        now = time.time()
        if now - self._fps_ts >= 1.0:
            self._fps = self._fps_cnt / (now - self._fps_ts)
            self._fps_cnt = 0
            self._fps_ts  = now

        undist = cv2.undistort(frame, self.cam_K, self.cam_dist)
        gray   = cv2.cvtColor(undist, cv2.COLOR_BGR2GRAY)
        corners, ids = self._detect_markers(gray)
        vis = undist.copy()
        if ids is not None:
            cv2.aruco.drawDetectedMarkers(vis, corners, ids)

        ref_pix, ref_world, ref_seen = [], [], []
        arm_base_det = False

        if ids is not None:
            for i, mid in enumerate(ids.flatten()):
                ctr = corners[i][0].mean(axis=0)
                ix, iy = int(ctr[0]), int(ctr[1])

                if mid in REF_IDS:
                    ref_pix.append(ctr)
                    ref_world.append(REF_WORLD_MM[mid])
                    ref_seen.append(mid)
                    cv2.circle(vis, (ix, iy), 10, _C_REF, -1)
                    cv2.circle(vis, (ix, iy), 14, _C_REF,  2)
                    cv2.putText(vis, f"REF{mid}", (ix+14, iy-10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.50, _C_REF, 2)
                elif mid == ARM_BASE_MARKER_ID:
                    arm_base_det = True
                    cv2.circle(vis, (ix, iy), 12, _C_ARM, -1)
                    cv2.putText(vis, "ARM_BASE", (ix+14, iy-10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.50, _C_ARM, 2)

        self._update_homography(ref_pix, ref_world)
        H = self.stable_H or self.H_matrix

        if H is not None and len(ref_pix) >= 2:
            self._draw_grid(vis, H)

        new_slots: Dict[int, dict] = {}
        arm_plate_info = None

        if H is not None and ids is not None:
            for i, mid in enumerate(ids.flatten()):
                c   = corners[i][0]
                px  = float(c[:, 0].mean())
                py  = float(c[:, 1].mean())
                yaw = self._marker_yaw(c)
                ix, iy = int(px), int(py)

                if mid in BOX_MARKER_TO_SLOT:
                    slot = BOX_MARKER_TO_SLOT[mid]
                    xf, yf = self._pixel_to_floor_mm(px, py)
                    if xf is None:
                        continue
                    x_mm, y_mm = self._correct_parallax(xf, yf, _T_BOX)
                    sx, sy, syaw = self._smooth_pose(mid, x_mm, y_mm, yaw)
                    xm, ym = sx / 1000.0, sy / 1000.0
                    if not (0.4 < xm < 1.8 and -1.2 < ym < 1.2):
                        continue
                    new_slots[slot] = {
                        "x": round(xm, 4), "y": round(ym, 4),
                        "z": round(BOX_Z_MM / 1000.0, 4),
                        "detected": True, "yaw_deg": round(syaw, 1),
                    }
                    cv2.circle(vis, (ix, iy), 8, _C_BOX, -1)
                    cv2.putText(vis, f"S{slot}({xm:.3f},{ym:.3f})",
                                (ix-50, iy-28), cv2.FONT_HERSHEY_SIMPLEX,
                                0.50, _C_BOX, 2)

                elif mid == ARM_PLATE_MARKER_ID:
                    xf, yf = self._pixel_to_floor_mm(px, py)
                    if xf is None:
                        continue
                    x_mm, y_mm = self._correct_parallax(xf, yf, _T_ARM)
                    sx, sy, syaw = self._smooth_pose(mid, x_mm, y_mm, yaw)
                    arm_plate_info = {
                        "x": round(sx/1000, 4), "y": round(sy/1000, 4),
                        "z": round(ARM_PLATE_Z_MM/1000, 4),
                        "yaw_deg": round(syaw, 1), "detected": True,
                    }
                    cv2.circle(vis, (ix, iy), 12, _C_ARM, -1)
                    cv2.circle(vis, (ix, iy), 16, _C_ARM,  2)
                    cv2.putText(vis, f"ARM yaw={syaw:.1f}",
                                (ix-60, iy-34), cv2.FONT_HERSHEY_SIMPLEX,
                                0.50, _C_ARM, 2)

        with self._lock:
            for slot, info in new_slots.items():
                self.slot_pos[slot] = info
            for slot in range(4):
                if slot not in new_slots:
                    self.slot_pos[slot]["detected"] = False
            self.arm_pose["base_detected"] = arm_base_det
            if arm_plate_info:
                self.arm_pose["plate_detected"] = True
                self.arm_pose["plate_x"]        = arm_plate_info["x"]
                self.arm_pose["plate_y"]        = arm_plate_info["y"]
                self.arm_pose["plate_yaw_deg"]  = arm_plate_info["yaw_deg"]
            else:
                self.arm_pose["plate_detected"] = False

        self._draw_hud(vis, ref_seen, H)

        disp = cv2.resize(vis, (960, 540))
        with self._display_lock:
            self._display_frame = disp

    # ── overlays ──────────────────────────────────────────────────────────

    def _draw_grid(self, vis, H):
        try:
            Hi = np.linalg.inv(H)
            corners_mm = np.array([
                REF_WORLD_MM[1], REF_WORLD_MM[2],
                REF_WORLD_MM[4], REF_WORLD_MM[3],
            ], dtype=np.float32)
            proj = cv2.perspectiveTransform(
                corners_mm.reshape(1, -1, 2), Hi)[0].astype(int)
            cv2.polylines(vis, [proj.reshape(-1, 1, 2)], True, _C_GRID, 2)
            for slot, (fx, fy) in SLOT_FALLBACK_MM.items():
                w = cv2.perspectiveTransform(
                    np.array([[[fx, fy]]], dtype=np.float32), Hi)
                ix, iy = int(w[0, 0, 0]), int(w[0, 0, 1])
                cv2.drawMarker(vis, (ix, iy), _C_CROSS, cv2.MARKER_CROSS, 22, 2)
                cv2.putText(vis, f"S{slot}", (ix+8, iy-8),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.44, _C_CROSS, 1)
            ap = cv2.perspectiveTransform(
                np.array([[[0.0, 0.0]]], dtype=np.float32), Hi)
            ax, ay = int(ap[0, 0, 0]), int(ap[0, 0, 1])
            cv2.drawMarker(vis, (ax, ay), _C_ARM, cv2.MARKER_STAR, 30, 2)
            cv2.putText(vis, "ARM_BASE", (ax+10, ay-10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.50, _C_ARM, 2)
        except Exception:
            pass

    def _draw_hud(self, vis, ref_seen, H):
        h_ok = H is not None
        with self._lock:
            ap   = self.arm_pose.get("plate_detected", False)
            ayaw = self.arm_pose.get("plate_yaw_deg",  0.0)
        lines = [
            (f"FPS:{self._fps:.1f}  cam={CAM_Z_MM/1000:.0f}m  "
             f"refs={len(ref_seen)}/4  hom={'OK' if h_ok else 'SEARCHING'}",
             _C_OK if (h_ok and len(ref_seen)==4) else _C_WARN),
            (f"ArmPlate(ID20): {'yaw='+str(ayaw)+'deg' if ap else 'not detected'}",
             _C_ARM if ap else (80,80,80)),
        ]
        with self._lock:
            for s in range(4):
                info = self.slot_pos[s]
                col  = _C_BOX if info["detected"] else (80, 80, 80)
                lines.append(
                    (f"Slot{s}: {'ARUCO' if info['detected'] else 'FK'}"
                     f"  ({info['x']:.3f},{info['y']:.3f})", col))

        ov = vis.copy()
        cv2.rectangle(ov, (0, 0), (520, 14 + len(lines)*21), (8,8,8), -1)
        cv2.addWeighted(ov, 0.72, vis, 0.28, 0, vis)
        for k, (txt, col) in enumerate(lines):
            cv2.putText(vis, txt, (6, 14 + k*21),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.46, col, 1)

    # ── publish ───────────────────────────────────────────────────────────

    def _publish_cb(self):
        with self._lock:
            box_pl = {str(s): info for s, info in self.slot_pos.items()}
            arm_pl = dict(self.arm_pose)
        msg_b = String(); msg_b.data = json.dumps(box_pl)
        msg_a = String(); msg_a.data = json.dumps(arm_pl)
        self.poses_pub.publish(msg_b)
        self.arm_pose_pub.publish(msg_a)


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ROS spins in a background daemon thread.
# cv2 window lives entirely in the main thread (Qt/X11 requirement).
# ─────────────────────────────────────────────────────────────────────────────

def main(args=None):
    if not _CV2_OK:
        print("ERROR: opencv-python is not installed.  "
              "Run:  pip install opencv-python  --break-system-packages")
        return

    rclpy.init(args=args)
    node = ArucoBoxDetector()

    spin_thread = threading.Thread(target=rclpy.spin, args=(node,), daemon=True)
    spin_thread.start()

    window_ok = False
    if SHOW_WINDOW:
        try:
            # Force xcb backend; never use wayland for cv2
            os.environ.setdefault("QT_QPA_PLATFORM", "xcb")
            cv2.namedWindow("Dexter ArUco Detector", cv2.WINDOW_NORMAL)
            cv2.resizeWindow("Dexter ArUco Detector", 960, 540)

            placeholder = np.zeros((540, 960, 3), dtype=np.uint8)
            cv2.putText(placeholder,
                        "Waiting for /camera/image_raw ...",
                        (160, 270), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (80,80,80), 2)
            cv2.putText(placeholder,
                        "Press Q or Esc to quit",
                        (320, 310), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (60,60,60), 1)
            cv2.imshow("Dexter ArUco Detector", placeholder)
            cv2.waitKey(1)
            window_ok = True
            node.get_logger().info(
                "OpenCV window opened  |  press Q or Esc to close")
        except Exception as e:
            node.get_logger().warn(
                f"Could not open cv2 window ({e}).  "
                "Running headless — node still publishes topics.")

    try:
        while rclpy.ok() and spin_thread.is_alive():
            if window_ok:
                frame = node.get_display_frame()
                if frame is not None:
                    try:
                        cv2.imshow("Dexter ArUco Detector", frame)
                    except Exception:
                        window_ok = False

                try:
                    key = cv2.waitKey(30) & 0xFF
                    if key in (ord('q'), 27):
                        node.get_logger().info("Window closed by user")
                        break
                except Exception:
                    window_ok = False
            else:
                # No window — just keep the thread alive
                time.sleep(0.05)

    except KeyboardInterrupt:
        node.get_logger().info("Interrupted")
    finally:
        if window_ok:
            try:
                cv2.destroyAllWindows()
            except Exception:
                pass
        node.destroy_node()
        try:
            rclpy.shutdown()
        except Exception:
            pass


if __name__ == "__main__":
    main()
