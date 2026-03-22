#!/usr/bin/env python3
"""
aruco_box_detector.py  –  Dexter Inventory ArUco Localizer
===========================================================
Overhead camera at (1.0, 0, 3.0 m), pitch=π/2, looking straight down.
FOV = 80°  →  fx=fy≈762 px,  1280×720.

Reference ArUco markers on the FLOOR (IDs 1-4, 200×200 mm):
    ID 1: (300, -900) mm   front-left
    ID 2: (1700, -900) mm  front-right
    ID 3: (300, +900) mm   back-left
    ID 4: (1700, +900) mm  back-right

Box ArUco markers on TOP of boxes (IDs 10-13, 90×90 mm, z≈1218 mm):
    ID 10 → slot 0  (1048, -642, 1218) mm
    ID 11 → slot 1  (1209, -220, 1218) mm
    ID 12 → slot 2  (1209, +220, 1218) mm
    ID 13 → slot 3  (1048, +642, 1218) mm

PARALLAX CORRECTION
-------------------
The homography is calibrated with floor-level reference markers (z=0).
Box markers sit at z=1218 mm ≈ 40% of camera height (3000 mm).
A ray from camera (Cx=1000, Cy=0, Cz=3000) through pixel (u,v) hits:
    floor  at (x_f, y_f, 0)
    box top at (x_b, y_b, 1218)  where:
        t = (Cz - z_box) / Cz = (3000-1218)/3000 = 0.594
        x_b = Cx + t * (x_f - Cx)
        y_b = Cy + t * (y_f - Cy)
Without this correction the Y error for slot 0 would be ~440 mm.

Publishes: /inventory/box_poses  (std_msgs/String, JSON payload)
Shows:     OpenCV window "Dexter ArUco Detector"
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
from cv_bridge import CvBridge

# ── Constants ─────────────────────────────────────────────────────────────────

# Camera world position in mm (matches SDF: x=1.0m, y=0m, z=3.0m)
CAM_X_MM: float = 1000.0
CAM_Y_MM: float = 0.0
CAM_Z_MM: float = 3000.0

# Box top height (z = 1.156 + 0.06 + 0.002 = 1.218 m)
BOX_Z_MM: float = 1218.0

# Parallax scale factor: (Cz - z_box) / Cz
_T_BOX: float = (CAM_Z_MM - BOX_Z_MM) / CAM_Z_MM   # ≈ 0.594

# Reference marker world positions in mm (Gazebo world frame)
REF_WORLD_MM: Dict[int, List[float]] = {
    1: [300.0,  -900.0],   # front-left
    2: [1700.0, -900.0],   # front-right
    3: [300.0,  +900.0],   # back-left
    4: [1700.0, +900.0],   # back-right
}
REF_IDS = list(REF_WORLD_MM.keys())

# Box marker → shelf slot mapping
BOX_MARKER_TO_SLOT: Dict[int, int] = {10: 0, 11: 1, 12: 2, 13: 3}

# Fallback world positions (mm) for each slot when ArUco is unavailable
SLOT_FALLBACK_MM: Dict[int, Tuple[float, float]] = {
    0: (1048.0, -642.0),
    1: (1209.0, -220.0),
    2: (1209.0, +220.0),
    3: (1048.0, +642.0),
}

# History / smoothing
H_HISTORY    = 12   # frames to median-filter homography matrix
POSE_HISTORY = 8    # frames to median-filter box pose
POSE_TIMEOUT = 3.0  # seconds before a pose is considered stale

# OpenCV window
SHOW_WINDOW = os.environ.get("ARUCO_SHOW_WINDOW", "1") != "0"

# Colour palette
_C_REF    = (0,  200, 255)   # cyan   – reference marker
_C_BOX    = (0,  240,  80)   # green  – box marker detected
_C_GRID   = (180,  30,  30)  # dark red – homography grid
_C_CROSS  = (255, 180,   0)  # amber  – slot crosshair
_C_WARN   = (0,  120, 255)   # orange – warning
_C_OK     = (0,  220,   0)   # green  – ok


# ── Node ──────────────────────────────────────────────────────────────────────

class ArucoBoxDetector(Node):
    """
    ROS 2 node that:
    1. Receives images from the overhead Gazebo camera.
    2. Detects ArUco markers (DICT_4X4_50).
    3. Computes a homography from the 4 floor reference markers.
    4. Applies parallax correction for elevated box markers.
    5. Publishes per-slot poses as JSON on /inventory/box_poses.
    6. Shows an annotated OpenCV window.
    """

    def __init__(self):
        super().__init__("aruco_box_detector")

        # ── Publishers ────────────────────────────────────────────────────
        self.poses_pub = self.create_publisher(String, "/inventory/box_poses", 10)

        # ── ArUco detector ────────────────────────────────────────────────
        aruco_dict   = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
        aruco_params = cv2.aruco.DetectorParameters()

        # Tuned for small markers viewed from a height
        aruco_params.cornerRefinementMethod        = cv2.aruco.CORNER_REFINE_SUBPIX
        aruco_params.cornerRefinementWinSize       = 7
        aruco_params.cornerRefinementMaxIterations = 60
        aruco_params.cornerRefinementMinAccuracy   = 0.01
        aruco_params.minMarkerPerimeterRate        = 0.015   # allow small markers
        aruco_params.maxMarkerPerimeterRate        = 0.90
        aruco_params.polygonalApproxAccuracyRate   = 0.08
        aruco_params.errorCorrectionRate           = 0.75
        aruco_params.minDistanceToBorder           = 2
        aruco_params.adaptiveThreshWinSizeMin      = 3
        aruco_params.adaptiveThreshWinSizeMax      = 25
        aruco_params.adaptiveThreshWinSizeStep     = 4
        aruco_params.adaptiveThreshConstant        = 9
        aruco_params.perspectiveRemovePixelPerCell = 6
        aruco_params.perspectiveRemoveIgnoredMarginPerCell = 0.10

        self.detector = cv2.aruco.ArucoDetector(aruco_dict, aruco_params)

        # ── Camera intrinsics (updated from /camera/camera_info) ──────────
        # Defaults for 1280×720, 80° FOV: fx = fy ≈ 762.6
        self.cam_K    = np.array([[762.6, 0.0, 640.0],
                                   [0.0, 762.6, 360.0],
                                   [0.0, 0.0,   1.0 ]], dtype=np.float64)
        self.cam_dist = np.zeros(5, dtype=np.float64)
        self._cam_info_rcvd = False

        # ── State ─────────────────────────────────────────────────────────
        self.H_matrix  : Optional[np.ndarray] = None   # current frame
        self.stable_H  : Optional[np.ndarray] = None   # median-smoothed
        self._H_history: deque = deque(maxlen=H_HISTORY)
        self._pose_hist: Dict[int, deque] = {}          # per-marker history
        self._lock      = threading.Lock()
        self._fps_cnt   = 0
        self._fps_ts    = time.time()
        self._fps       = 0.0
        self._last_frm  = 0.0   # timestamp of last image

        # Per-slot output (fallback = FK positions)
        self.slot_pos: Dict[int, dict] = {
            s: {
                "x": fx / 1000.0, "y": fy / 1000.0,
                "z": BOX_Z_MM / 1000.0,
                "detected": False, "yaw_deg": 0.0,
            }
            for s, (fx, fy) in SLOT_FALLBACK_MM.items()
        }

        self.bridge = CvBridge()

        # ── ROS subscriptions ─────────────────────────────────────────────
        self.create_subscription(CameraInfo, "/camera/camera_info",
                                 self._camera_info_cb, 10)
        self.create_subscription(Image, "/camera/image_raw",
                                 self._image_cb, 1)          # queue=1: drop old frames

        # ── Timers ────────────────────────────────────────────────────────
        self.create_timer(0.2,  self._publish_cb)  # 5 Hz publish
        self.create_timer(5.0,  self._watchdog_cb)

        self.get_logger().info("=" * 60)
        self.get_logger().info("ArucoBoxDetector node started")
        self.get_logger().info(f"  Window display : {'ENABLED' if SHOW_WINDOW else 'DISABLED'}")
        self.get_logger().info(f"  Camera pos     : ({CAM_X_MM:.0f}, {CAM_Y_MM:.0f}, {CAM_Z_MM:.0f}) mm")
        self.get_logger().info(f"  Box height     : {BOX_Z_MM:.0f} mm")
        self.get_logger().info(f"  Parallax scale : {_T_BOX:.4f}")
        for mid, (wx, wy) in REF_WORLD_MM.items():
            self.get_logger().info(f"  REF ID {mid}: ({wx:.0f}, {wy:.0f}) mm")
        self.get_logger().info("=" * 60)

    # ── Camera info ───────────────────────────────────────────────────────

    def _camera_info_cb(self, msg: CameraInfo):
        if self._cam_info_rcvd:
            return
        # Extract K matrix from camera_info (row-major 3×3)
        K = np.array(msg.k, dtype=np.float64).reshape(3, 3)
        if K[0, 0] > 1.0:       # sanity check
            self.cam_K = K
        # Extract distortion (up to 5 coefficients)
        d = np.array(msg.d, dtype=np.float64)
        if d.shape[0] >= 4:
            self.cam_dist = d[:5] if d.shape[0] >= 5 else np.pad(d, (0, 5-d.shape[0]))
        else:
            self.cam_dist = np.zeros(5, dtype=np.float64)
        self._cam_info_rcvd = True
        self.get_logger().info(
            f"Camera info received: fx={self.cam_K[0,0]:.1f}  "
            f"cx={self.cam_K[0,2]:.1f}  cy={self.cam_K[1,2]:.1f}")

    # ── Image callback ────────────────────────────────────────────────────

    def _image_cb(self, msg: Image):
        try:
            frame = self.bridge.imgmsg_to_cv2(msg, "bgr8")
        except Exception as e:
            self.get_logger().error(f"imgmsg_to_cv2: {e}")
            return
        self._last_frm = time.time()
        self._process(frame)

    # ── Watchdog ──────────────────────────────────────────────────────────

    def _watchdog_cb(self):
        if self._last_frm == 0.0:
            self.get_logger().warn("No frames yet from /camera/image_raw")
        elif time.time() - self._last_frm > 5.0:
            self.get_logger().warn("Camera feed stalled (>5 s since last frame)")

    # ── Image preprocessing ───────────────────────────────────────────────

    @staticmethod
    def _preprocess_variants(gray: np.ndarray) -> List[np.ndarray]:
        """Return several preprocessed images to maximise detection rate."""
        variants = []
        # 1. Normalised
        norm = cv2.normalize(gray, None, 0, 255, cv2.NORM_MINMAX)
        variants.append(norm)
        # 2. CLAHE (local contrast)
        clahe = cv2.createCLAHE(clipLimit=3.5, tileGridSize=(8, 8)).apply(norm)
        variants.append(clahe)
        # 3. Gamma-brightened CLAHE (helps thin white borders)
        lut = (np.arange(256) / 255.0) ** (1.0 / 1.4) * 255
        gamma = cv2.LUT(clahe, lut.astype(np.uint8))
        variants.append(gamma)
        # 4. Sharpened
        kernel = np.array([[-1,-1,-1],[-1,9,-1],[-1,-1,-1]])
        sharp  = cv2.filter2D(clahe, -1, kernel)
        variants.append(sharp)
        return variants

    # ── ArUco detection ───────────────────────────────────────────────────

    def _detect_markers(self, gray: np.ndarray):
        """
        Run detector on multiple preprocessed variants and return the
        best (largest-area) detection per marker ID.
        Returns (corners_list, ids_array) or (None, None).
        """
        best: Dict[int, tuple] = {}
        for proc in self._preprocess_variants(gray):
            corners, ids, _ = self.detector.detectMarkers(proc)
            if ids is None:
                continue
            for i, mid in enumerate(ids.flatten()):
                area = cv2.contourArea(corners[i][0])
                if mid not in best or area > best[mid][1]:
                    best[mid] = (corners[i], area)
        if not best:
            return None, None
        c_list = [v[0] for v in best.values()]
        id_arr = np.array([[k] for k in best.keys()], dtype=np.int32)
        return c_list, id_arr

    # ── Homography ────────────────────────────────────────────────────────

    def _update_homography(self, pix_pts: List, world_pts: List):
        """Compute and smooth the floor homography."""
        if len(pix_pts) < 4:
            return
        H, mask = cv2.findHomography(
            np.array(pix_pts, dtype=np.float32),
            np.array(world_pts, dtype=np.float32),
            cv2.RANSAC, 5.0,
        )
        if H is None:
            return
        self.H_matrix = H
        self._H_history.append(H)
        if len(self._H_history) >= 3:
            self.stable_H = np.median(
                np.array(list(self._H_history)), axis=0)
        else:
            self.stable_H = H

    def _pixel_to_floor_mm(self, px: float, py: float
                           ) -> Tuple[Optional[float], Optional[float]]:
        """Map a pixel (u, v) to floor-level world (x_mm, y_mm) via homography."""
        H = self.stable_H if self.stable_H is not None else self.H_matrix
        if H is None:
            return None, None
        w = cv2.perspectiveTransform(
            np.array([[[px, py]]], dtype=np.float32), H)
        return float(w[0, 0, 0]), float(w[0, 0, 1])

    # ── Parallax correction ───────────────────────────────────────────────

    @staticmethod
    def _correct_parallax(x_floor_mm: float, y_floor_mm: float
                          ) -> Tuple[float, float]:
        """
        Project a floor-homography position to actual box-top world position.

        A box marker at (x_true, y_true, BOX_Z_MM) casts the same ray to
        the camera as a floor point at (x_floor, y_floor, 0).  Inverting:

            x_true = Cx + t * (x_floor - Cx)
            y_true = Cy + t * (y_floor - Cy)

        where  t = (Cz - z_box) / Cz = _T_BOX ≈ 0.594
        """
        x_true = CAM_X_MM + _T_BOX * (x_floor_mm - CAM_X_MM)
        y_true = CAM_Y_MM + _T_BOX * (y_floor_mm - CAM_Y_MM)
        return x_true, y_true

    # ── Pose smoothing ────────────────────────────────────────────────────

    def _smooth_pose(self, marker_id: int, x_mm: float, y_mm: float,
                     yaw_deg: float) -> Tuple[float, float, float]:
        """Median-filter pose over recent detections."""
        now = time.time()
        if marker_id not in self._pose_hist:
            self._pose_hist[marker_id] = deque(maxlen=POSE_HISTORY)
        h = self._pose_hist[marker_id]
        h.append((x_mm, y_mm, yaw_deg, now))
        # Prune stale
        while h and now - h[0][3] > POSE_TIMEOUT:
            h.popleft()
        xs  = [p[0] for p in h]
        ys  = [p[1] for p in h]
        yws = [p[2] for p in h]
        return (float(np.median(xs)),
                float(np.median(ys)),
                float(np.median(yws)))

    @staticmethod
    def _marker_yaw(corners: np.ndarray) -> float:
        """Yaw angle (deg) of a marker from the top-left→top-right edge."""
        dx = corners[1, 0] - corners[0, 0]
        dy = corners[1, 1] - corners[0, 1]
        deg = math.degrees(math.atan2(dy, dx))
        if deg < -180: deg += 360
        if deg >  180: deg -= 360
        return round(deg, 1)

    # ── Main processing ───────────────────────────────────────────────────

    def _process(self, frame: np.ndarray):
        # FPS counter
        self._fps_cnt += 1
        now = time.time()
        if now - self._fps_ts >= 1.0:
            self._fps     = self._fps_cnt / (now - self._fps_ts)
            self._fps_cnt = 0
            self._fps_ts  = now

        # Undistort
        undist = cv2.undistort(frame, self.cam_K, self.cam_dist)

        # Grayscale
        gray = cv2.cvtColor(undist, cv2.COLOR_BGR2GRAY)

        # Detect
        corners, ids = self._detect_markers(gray)
        vis = undist.copy()
        if ids is not None:
            cv2.aruco.drawDetectedMarkers(vis, corners, ids)

        # ── Collect reference markers ──────────────────────────────────
        ref_pix, ref_world, ref_seen = [], [], []
        if ids is not None:
            for i, mid in enumerate(ids.flatten()):
                if mid not in REF_IDS:
                    continue
                ctr = corners[i][0].mean(axis=0)
                ref_pix.append(ctr)
                ref_world.append(REF_WORLD_MM[mid])
                ref_seen.append(mid)
                cx, cy = int(ctr[0]), int(ctr[1])
                cv2.circle(vis, (cx, cy), 10, _C_REF, -1)
                cv2.circle(vis, (cx, cy), 13, _C_REF,  2)
                cv2.putText(vis, f"REF{mid}",
                            (cx + 14, cy - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.55, _C_REF, 2)

        # ── Update homography ──────────────────────────────────────────
        self._update_homography(ref_pix, ref_world)
        H = self.stable_H if self.stable_H is not None else self.H_matrix

        # ── Draw projected work-area grid ──────────────────────────────
        if H is not None and len(ref_pix) >= 2:
            self._draw_grid(vis, H)

        # ── Detect & locate box markers ────────────────────────────────
        new_slots: Dict[int, dict] = {}
        if H is not None and ids is not None:
            for i, mid in enumerate(ids.flatten()):
                if mid not in BOX_MARKER_TO_SLOT:
                    continue
                slot = BOX_MARKER_TO_SLOT[mid]
                c    = corners[i][0]
                px   = float(c[:, 0].mean())
                py   = float(c[:, 1].mean())
                yaw  = self._marker_yaw(c)

                # Floor homography → parallax correction → true world pos
                xf, yf = self._pixel_to_floor_mm(px, py)
                if xf is None:
                    continue
                x_mm, y_mm = self._correct_parallax(xf, yf)

                # Smooth
                sx, sy, syaw = self._smooth_pose(mid, x_mm, y_mm, yaw)
                xm, ym = sx / 1000.0, sy / 1000.0   # convert to metres

                # Sanity bounds (workspace limits in metres)
                if not (0.6 < xm < 1.6 and -1.0 < ym < 1.0):
                    self.get_logger().warn(
                        f"  Slot {slot}: out of bounds ({xm:.3f}, {ym:.3f})")
                    continue

                new_slots[slot] = {
                    "x": round(xm, 4), "y": round(ym, 4),
                    "z": round(BOX_Z_MM / 1000.0, 4),
                    "detected": True, "yaw_deg": round(syaw, 1),
                }

                # Annotate
                ix, iy = int(px), int(py)
                cv2.circle(vis, (ix, iy), 8, _C_BOX, -1)
                cv2.putText(vis,
                            f"S{slot} ({xm:.3f},{ym:.3f}m)",
                            (ix - 60, iy - 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.58, _C_BOX, 2)
                cv2.putText(vis,
                            f"raw_floor=({xf/1000:.3f},{yf/1000:.3f})",
                            (ix - 60, iy - 14),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.42, (160, 160, 255), 1)

        # ── Update slot_pos (thread-safe) ──────────────────────────────
        with self._lock:
            for slot, info in new_slots.items():
                self.slot_pos[slot] = info
            # Mark slots as undetected if ArUco not seen this frame
            for slot in range(4):
                if slot not in new_slots:
                    self.slot_pos[slot]["detected"] = False

        # ── HUD overlay ────────────────────────────────────────────────
        self._draw_hud(vis, ref_seen, H)

        # ── Show window ────────────────────────────────────────────────
        if SHOW_WINDOW:
            try:
                disp = cv2.resize(vis, (960, 540))
                cv2.imshow("Dexter ArUco Detector", disp)
                cv2.waitKey(1)
            except Exception:
                pass

    # ── Grid overlay ──────────────────────────────────────────────────────

    def _draw_grid(self, vis: np.ndarray, H: np.ndarray):
        """Project the work-area boundary and slot crosshairs onto the image."""
        try:
            Hi = np.linalg.inv(H)
            # Work-area boundary (mm)
            corners_mm = np.array([
                REF_WORLD_MM[1], REF_WORLD_MM[2],
                REF_WORLD_MM[4], REF_WORLD_MM[3],
            ], dtype=np.float32)
            proj = cv2.perspectiveTransform(
                corners_mm.reshape(1, -1, 2), Hi)[0].astype(int)
            cv2.polylines(vis, [proj.reshape(-1, 1, 2)], True, _C_GRID, 2)

            # Slot crosshairs
            for slot, (fx_mm, fy_mm) in SLOT_FALLBACK_MM.items():
                w = cv2.perspectiveTransform(
                    np.array([[[fx_mm, fy_mm]]], dtype=np.float32), Hi)
                ix, iy = int(w[0, 0, 0]), int(w[0, 0, 1])
                cv2.drawMarker(vis, (ix, iy), _C_CROSS,
                               cv2.MARKER_CROSS, 22, 2)
                cv2.putText(vis, f"S{slot}", (ix + 8, iy - 8),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.48, _C_CROSS, 1)
        except Exception:
            pass

    # ── HUD overlay ───────────────────────────────────────────────────────

    def _draw_hud(self, vis: np.ndarray, ref_seen: List[int],
                  H: Optional[np.ndarray]):
        h_ok = H is not None
        lines = [
            (f"FPS: {self._fps:.1f}", (180, 180, 180)),
            (f"Refs: {len(ref_seen)}/4  IDs={ref_seen}",
             _C_OK if len(ref_seen) == 4 else (_C_WARN if len(ref_seen) >= 2 else (0, 60, 220))),
            (f"Homography: {'LOCKED' if h_ok else 'SEARCHING (need 4 refs)'}",
             _C_OK if h_ok else _C_WARN),
        ]
        with self._lock:
            for slot in range(4):
                info = self.slot_pos[slot]
                detected = info["detected"]
                col  = _C_BOX if detected else (80, 80, 80)
                mode = "ARUCO" if detected else "FK fallback"
                lines.append(
                    (f"Slot {slot}: {mode}  ({info['x']:.3f}, {info['y']:.3f}) m",
                     col))

        overlay = vis.copy()
        cv2.rectangle(overlay, (0, 0), (480, 18 + len(lines) * 23),
                      (8, 8, 8), -1)
        cv2.addWeighted(overlay, 0.70, vis, 0.30, 0, vis)
        for k, (txt, col) in enumerate(lines):
            cv2.putText(vis, txt, (8, 16 + k * 23),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.52, col,
                        2 if k <= 2 else 1)

    # ── Publisher callback ────────────────────────────────────────────────

    def _publish_cb(self):
        with self._lock:
            payload = {str(s): info for s, info in self.slot_pos.items()}
        msg      = String()
        msg.data = json.dumps(payload)
        self.poses_pub.publish(msg)


# ── Entry point ───────────────────────────────────────────────────────────────

def main(args=None):
    rclpy.init(args=args)
    node = ArucoBoxDetector()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        cv2.destroyAllWindows()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
