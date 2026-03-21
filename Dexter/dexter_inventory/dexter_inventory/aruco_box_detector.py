#!/usr/bin/env python3
"""
aruco_box_detector.py  –  Dexter Inventory ArUco Localizer
===========================================================
Adapted from holonomic_perception.py (EnhancedPoseDetector).

Physical setup (REAL ROBOT)
---------------------------
Mount your phone (IP Webcam app on Android) DIRECTLY OVERHEAD,
pointing straight down, at ~2 m height above the shelf.

Print 4 reference ArUco markers (DICT_4X4_50, print at ≥7 cm square)
and place them FLAT on the table / shelf surface at these positions,
measured in mm from the robot's base_link origin (XY plane, z ignored):

    ID 1  →  (700,  -800) mm   front-left  of reference rectangle
    ID 2  →  (1450, -800) mm   front-right
    ID 3  →  (700,  +800) mm   back-left
    ID 4  →  (1450, +800) mm   back-right

                  Y=−800
        ID1 ──────────── ID2
         |                |
         |   shelf area   |
         |                |
        ID3 ──────────── ID4
                  Y=+800
        X=700           X=1450

Print 4 box ArUco markers and stick them on TOP of each box:
    ID 10  →  Slot 0  (Resistors,  red   box)
    ID 11  →  Slot 1  (Capacitors, amber box)
    ID 12  →  Slot 2  (LEDs,       blue  box)
    ID 13  →  Slot 3  (Arduino,    green box)

Simulation
----------
Set USE_IP_WEBCAM=False, USE_GAZEBO_CAM=True.
The world SDF must have the overhead camera and gz_ros2_bridge running.
In sim, physical ArUco marker positions on boxes are from the SDF.

Output topic
------------
/inventory/box_poses  (std_msgs/String, JSON, ~5 Hz)
{
  "0": {"x": 1.048, "y": -0.642, "z": 1.156, "detected": true,  "yaw_deg": 0.0},
  "1": {"x": 1.209, "y": -0.220, "z": 1.156, "detected": false, "yaw_deg": 0.0},
  ...
}
Undetected slots fall back to hardcoded FK positions and "detected": false.
z is always BOX_Z_M (1.156 m) — constant shelf height.

Marker printing
---------------
Generate printable markers with:
    python3 -c "
    import cv2, numpy as np
    d = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
    for mid in [1,2,3,4,10,11,12,13]:
        img = cv2.aruco.generateImageMarker(d, mid, 300)
        cv2.imwrite(f'marker_{mid}.png', img)
    print('Saved marker_*.png — print each at 7 cm square')
    "
"""

from __future__ import annotations

import json
import math
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
    _ROS_IMG_AVAILABLE = True
except ImportError:
    _ROS_IMG_AVAILABLE = False


# ── Configuration ──────────────────────────────────────────────────────────────

# Camera source: pick ONE
USE_IP_WEBCAM  = False          # Android IP Webcam app
USE_GAZEBO_CAM = True           # ROS2 topic from Gazebo (overrides IP webcam when True)

IP_WEBCAM_URL  = "http://192.168.1.100:8080/video"   # ← change to your phone's IP
GAZEBO_IMG_TOPIC = "/camera/image_raw"               # Gazebo camera topic

# Local USB camera fallback (USE_IP_WEBCAM=False, USE_GAZEBO_CAM=False)
USB_CAMERA_INDEX = 0

# ── Shelf geometry (mm, robot base_link XY frame) ──────────────────────────────
# 4 reference markers placed around the shelf at KNOWN positions
REFERENCE_WORLD_COORDS_MM: Dict[int, List[float]] = {
    1: [700.0,  -800.0],   # front-left
    2: [1450.0, -800.0],   # front-right
    3: [700.0,  +800.0],   # back-left
    4: [1450.0, +800.0],   # back-right
}
REFERENCE_MARKER_IDS = list(REFERENCE_WORLD_COORDS_MM.keys())

# Box ArUco markers → shelf slot index
BOX_MARKER_TO_SLOT: Dict[int, int] = {
    10: 0,   # Slot 0 – Resistors
    11: 1,   # Slot 1 – Capacitors
    12: 2,   # Slot 2 – LEDs
    13: 3,   # Slot 3 – Arduino
}

# Fallback FK positions (meters, robot frame) — used when not detected
SLOT_FALLBACK_M: Dict[int, Tuple[float, float]] = {
    0: (1.048, -0.642),
    1: (1.209, -0.220),
    2: (1.209, +0.220),
    3: (1.048, +0.642),
}

# Box centre height above floor (shelf surface 1.096 + half-box 0.060)
BOX_Z_M = 1.156

# Homography temporal filter
H_HISTORY_LEN   = 10
POSE_HISTORY_LEN = 5
POSE_TIMEOUT_S   = 2.0

# Detection window - set to False if running headless or via SSH without X forwarding
# Can also be overridden with ARUCO_SHOW_WINDOW=0 environment variable
import os
SHOW_WINDOW = os.environ.get("ARUCO_SHOW_WINDOW", "1") != "0"


# ── Node ───────────────────────────────────────────────────────────────────────

class ArucoBoxDetector(Node):
    """
    Top-down ArUco localizer for Dexter's inventory shelf.
    Publishes detected box positions as JSON on /inventory/box_poses.
    """

    def __init__(self):
        super().__init__("aruco_box_detector")

        # ── Publishers ────────────────────────────────────────────────────────
        self.poses_pub = self.create_publisher(String, "/inventory/box_poses", 10)

        # ── ArUco detector ────────────────────────────────────────────────────
        self.aruco_dict   = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
        params = cv2.aruco.DetectorParameters()
        # Tuned for overhead phone camera
        params.cornerRefinementMethod        = cv2.aruco.CORNER_REFINE_SUBPIX
        params.minMarkerPerimeterRate        = 0.02
        params.maxMarkerPerimeterRate        = 0.9
        params.polygonalApproxAccuracyRate   = 0.10
        params.errorCorrectionRate           = 0.8
        params.minDistanceToBorder           = 2
        params.adaptiveThreshWinSizeMin      = 3
        params.adaptiveThreshWinSizeMax      = 23
        params.adaptiveThreshWinSizeStep     = 4
        params.adaptiveThreshConstant        = 7
        params.cornerRefinementWinSize       = 5
        params.cornerRefinementMaxIterations = 50
        params.cornerRefinementMinAccuracy   = 0.005
        params.perspectiveRemovePixelPerCell = 8
        params.perspectiveRemoveIgnoredMarginPerCell = 0.13
        self.detector = cv2.aruco.ArucoDetector(self.aruco_dict, params)

        # ── State ─────────────────────────────────────────────────────────────
        self.H_matrix     : Optional[np.ndarray] = None
        self.stable_H     : Optional[np.ndarray] = None
        self.H_history    : deque = deque(maxlen=H_HISTORY_LEN)
        self.pose_history : Dict[int, deque] = {}   # marker_id → deque of (x,y,yaw,t)
        self._lock        = threading.Lock()
        self.frame_count  = 0

        # Last known slot positions (meters, robot frame)
        self.slot_positions: Dict[int, dict] = {
            s: {"x": fx, "y": fy, "z": BOX_Z_M, "detected": False, "yaw_deg": 0.0}
            for s, (fx, fy) in SLOT_FALLBACK_M.items()
        }

        # Default camera calibration (good enough for 1080p overhead view)
        self.camera_matrix = np.array([[1200, 0, 960],
                                        [0, 1200, 540],
                                        [0, 0, 1]], dtype=np.float32)
        self.dist_coeffs = np.zeros(4, dtype=np.float32)

        # ── Camera source ─────────────────────────────────────────────────────
        if USE_GAZEBO_CAM and _ROS_IMG_AVAILABLE:
            self.bridge = CvBridge()
            self.image_sub = self.create_subscription(
                Image, GAZEBO_IMG_TOPIC, self._ros_image_callback, 10
            )
            self.get_logger().info(f"Subscribed to Gazebo camera: {GAZEBO_IMG_TOPIC}")
            # Add status timer to warn if no images received
            self._last_frame_time = 0.0
            self.create_timer(5.0, self._check_camera_status)
        else:
            self._start_camera_thread()

        # Publish timer at 5 Hz
        self.create_timer(0.2, self._publish_poses)

        self.get_logger().info("=" * 60)
        self.get_logger().info("ArucoBoxDetector ready")
        self.get_logger().info(f"  Reference marker IDs : {REFERENCE_MARKER_IDS}")
        self.get_logger().info(f"  Box marker IDs       : {list(BOX_MARKER_TO_SLOT)}")
        self.get_logger().info(f"  Output topic         : /inventory/box_poses")
        if USE_IP_WEBCAM and not USE_GAZEBO_CAM:
            self.get_logger().info(f"  IP Webcam URL        : {IP_WEBCAM_URL}")
        self.get_logger().info("=" * 60)
        self.get_logger().info("Place reference markers at (mm from base_link):")
        for mid, (wx, wy) in REFERENCE_WORLD_COORDS_MM.items():
            self.get_logger().info(f"  Marker ID {mid}: x={wx:.0f}mm, y={wy:.0f}mm")

    # ── Camera thread ─────────────────────────────────────────────────────────

    def _start_camera_thread(self):
        if USE_IP_WEBCAM:
            url = IP_WEBCAM_URL
            self.get_logger().info(f"Connecting to IP Webcam: {url}")
        else:
            url = USB_CAMERA_INDEX
            self.get_logger().info(f"Opening local USB camera: {url}")

        self.cap = cv2.VideoCapture(url)
        if not self.cap.isOpened():
            self.get_logger().error(
                f"Failed to open camera source: {url}\n"
                "  For IP Webcam: install 'IP Webcam' from Play Store, "
                "start server, update IP_WEBCAM_URL in this file."
            )
            return

        # Reduce internal buffer so we always get the freshest frame
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self.get_logger().info("Camera opened successfully")

        t = threading.Thread(target=self._capture_loop, daemon=True)
        t.start()

    def _capture_loop(self):
        while rclpy.ok():
            ret, frame = self.cap.read()
            if not ret:
                time.sleep(0.05)
                continue
            self._process_frame(frame)

    def _ros_image_callback(self, msg: Image):
        try:
            frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")
            self.frame_count += 1
            self._last_frame_time = time.time()
            if self.frame_count % 30 == 1:
                self.get_logger().info(f"Receiving camera frames (frame #{self.frame_count}, {frame.shape})")
            self._process_frame(frame)
        except Exception as e:
            self.get_logger().error(f"ROS image callback error: {e}")

    def _check_camera_status(self):
        """Warn if no camera frames received recently."""
        if not hasattr(self, '_last_frame_time'):
            return
        elapsed = time.time() - self._last_frame_time
        if self._last_frame_time == 0.0:
            self.get_logger().warn(
                f"No camera frames received yet on {GAZEBO_IMG_TOPIC}!\n"
                "  Check if Gazebo camera is working:\n"
                "  1. In Gazebo GUI: Add 'Image Display' plugin from top-right menu\n"
                "  2. Run: gz topic -l | grep image\n"
                "  3. Run: ros2 topic list | grep camera"
            )
        elif elapsed > 5.0:
            self.get_logger().warn(f"No camera frames for {elapsed:.1f}s")

    # ── Core detection ────────────────────────────────────────────────────────

    def _preprocess(self, gray: np.ndarray) -> List[np.ndarray]:
        """Multi-pass preprocessing — same robust approach as holonomic_perception.py."""
        imgs = []

        # 1. Raw normalized
        normalized = cv2.normalize(gray, None, 0, 255, cv2.NORM_MINMAX)
        imgs.append(normalized)

        # 2. CLAHE + gamma
        clahe   = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(8, 8))
        clahe_img = clahe.apply(normalized)
        table   = (np.arange(256) / 255.0 ** (1.0 / 0.7) * 255).astype(np.uint8)
        gamma_img = cv2.LUT(clahe_img, table)
        imgs.append(gamma_img)

        # 3. Bilateral + sharpened
        bilateral = cv2.bilateralFilter(gamma_img, 9, 75, 75)
        kernel    = np.array([[-1,-1,-1],[-1,9,-1],[-1,-1,-1]])
        sharpened = cv2.filter2D(bilateral, -1, kernel)
        imgs.append(sharpened)

        return imgs

    def _detect_robust(self, gray: np.ndarray):
        """Detect across multiple preprocessed versions, keep highest-area detection."""
        best: Dict[int, tuple] = {}   # marker_id → (corners_array, area)

        for processed in self._preprocess(gray):
            corners, ids, _ = self.detector.detectMarkers(processed)
            if ids is None:
                continue
            for i, mid in enumerate(ids.flatten()):
                c     = corners[i][0]
                area  = cv2.contourArea(c)
                if mid not in best or area > best[mid][1]:
                    best[mid] = (corners[i], area)

        if not best:
            return None, None

        merged_corners = [v[0] for v in best.values()]
        merged_ids     = np.array([[mid] for mid in best.keys()])
        return merged_corners, merged_ids

    def _update_homography(self, pixel_pts: List, world_pts: List):
        """Compute and temporally smooth the pixel→world homography."""
        if len(pixel_pts) < 4:
            return

        src = np.array(pixel_pts, dtype=np.float32)
        dst = np.array(world_pts,  dtype=np.float32)
        H, status = cv2.findHomography(src, dst, cv2.RANSAC, 5.0)

        if H is None:
            return

        self.H_matrix = H
        self.H_history.append(H)

        # Median filter across history for stability
        if len(self.H_history) >= 3:
            self.stable_H = np.median(np.array(list(self.H_history)), axis=0)
        else:
            self.stable_H = H

    def _pixel_to_world_mm(self, px: float, py: float) -> Tuple[Optional[float], Optional[float]]:
        H = self.stable_H if self.stable_H is not None else self.H_matrix
        if H is None:
            return None, None
        pts = np.array([[[px, py]]], dtype=np.float32)
        w   = cv2.perspectiveTransform(pts, H)
        return float(w[0, 0, 0]), float(w[0, 0, 1])

    def _marker_yaw_deg(self, corners: np.ndarray) -> float:
        dx = corners[1, 0] - corners[0, 0]
        dy = corners[1, 1] - corners[0, 1]
        rad = math.atan2(dy, dx)
        if rad < 0:
            rad += 2 * math.pi
        deg = math.degrees(rad)
        return deg if deg < 180 else -(360 - deg)

    def _smooth_pose(self, marker_id: int, x_mm: float, y_mm: float, yaw: float
                     ) -> Tuple[float, float, float]:
        """Temporal median filter — mirrors holonomic_perception.py."""
        now = time.time()
        if marker_id not in self.pose_history:
            self.pose_history[marker_id] = deque(maxlen=POSE_HISTORY_LEN)

        hist = self.pose_history[marker_id]
        hist.append((x_mm, y_mm, yaw, now))

        # Drop stale entries
        while hist and now - hist[0][3] > POSE_TIMEOUT_S:
            hist.popleft()

        xs   = [p[0] for p in hist]
        ys   = [p[1] for p in hist]
        yaws = [p[2] for p in hist]
        return float(np.median(xs)), float(np.median(ys)), float(np.median(yaws))

    def _process_frame(self, frame: np.ndarray):
        # Note: frame_count is incremented in _ros_image_callback for Gazebo camera
        # Only increment here for USB/IP camera path
        if not (USE_GAZEBO_CAM and _ROS_IMG_AVAILABLE):
            self.frame_count += 1

        undistorted = cv2.undistort(frame, self.camera_matrix, self.dist_coeffs)
        gray        = cv2.cvtColor(undistorted, cv2.COLOR_BGR2GRAY)
        corners, ids = self._detect_robust(gray)

        vis = undistorted.copy()
        if ids is not None:
            cv2.aruco.drawDetectedMarkers(vis, corners, ids)

        # ── Collect reference markers for homography ──────────────────────────
        ref_pixels, ref_world = [], []
        if ids is not None:
            for i, mid in enumerate(ids.flatten()):
                if mid in REFERENCE_MARKER_IDS:
                    centre = corners[i][0].mean(axis=0)
                    ref_pixels.append(centre)
                    ref_world.append(REFERENCE_WORLD_COORDS_MM[mid])

        self._update_homography(ref_pixels, ref_world)

        # ── Detect box markers ────────────────────────────────────────────────
        H = self.stable_H if self.stable_H is not None else self.H_matrix
        if H is None:
            if self.frame_count % 60 == 0:
                self.get_logger().warn(
                    "Homography not ready — need ≥4 reference markers visible. "
                    f"Currently visible: {ref_pixels.__len__()} reference marker(s)."
                )
        else:
            with self._lock:
                if ids is not None:
                    for i, mid in enumerate(ids.flatten()):
                        if mid not in BOX_MARKER_TO_SLOT:
                            continue

                        slot = BOX_MARKER_TO_SLOT[mid]
                        c    = corners[i][0]
                        px   = float(c[:, 0].mean())
                        py   = float(c[:, 1].mean())

                        x_mm, y_mm = self._pixel_to_world_mm(px, py)
                        if x_mm is None:
                            continue

                        yaw = self._marker_yaw_deg(c)
                        sx, sy, sy_deg = self._smooth_pose(mid, x_mm, y_mm, yaw)

                        # Convert mm → meters for robot frame
                        x_m = sx / 1000.0
                        y_m = sy / 1000.0

                        # Sanity check: position must be within plausible shelf reach
                        if not (0.5 < x_m < 1.8 and -1.2 < y_m < 1.2):
                            self.get_logger().warn(
                                f"Slot {slot} detected at suspicious position "
                                f"({x_m:.3f}, {y_m:.3f}) m — ignoring frame"
                            )
                            continue

                        self.slot_positions[slot] = {
                            "x": round(x_m, 4),
                            "y": round(y_m, 4),
                            "z": BOX_Z_M,
                            "detected": True,
                            "yaw_deg": round(sy_deg, 1),
                        }

                        # Mark on visualisation
                        cv2.putText(
                            vis,
                            f"Slot{slot} ({x_m:.3f},{y_m:.3f}m)",
                            (int(px), int(py) - 22),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.55,
                            (0, 255, 100), 2,
                        )

        # ── Overlay reference marker labels ───────────────────────────────────
        if ids is not None:
            for i, mid in enumerate(ids.flatten()):
                if mid in REFERENCE_MARKER_IDS:
                    centre = corners[i][0].mean(axis=0).astype(int)
                    cv2.putText(vis, f"REF:{mid}",
                                tuple(centre - [0, 15]),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 200, 255), 2)

        # ── Status overlay ────────────────────────────────────────────────────
        ref_count = len(ref_pixels)
        h_ok      = H is not None
        cv2.putText(vis,
                    f"Refs visible: {ref_count}/4  |  Homography: {'OK' if h_ok else 'WAIT'}",
                    (10, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.65,
                    (0, 255, 0) if h_ok else (0, 100, 255), 2)

        for slot, info in self.slot_positions.items():
            color = (0, 255, 80) if info["detected"] else (80, 80, 80)
            cv2.putText(vis,
                        f"S{slot}: {'det' if info['detected'] else 'fallback'} "
                        f"({info['x']:.3f},{info['y']:.3f})",
                        (10, 55 + slot * 22),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.50, color, 1)

        if SHOW_WINDOW:
            try:
                disp = cv2.resize(vis, (960, 540))
                cv2.imshow("Dexter ArUco Detector", disp)
                cv2.waitKey(1)
            except cv2.error as e:
                # Display not available (headless, no X11, etc.)
                if self.frame_count <= 5:
                    self.get_logger().warn(f"cv2.imshow failed (display unavailable?): {e}")

    # ── ROS2 publisher ────────────────────────────────────────────────────────

    def _publish_poses(self):
        with self._lock:
            payload = {str(s): info for s, info in self.slot_positions.items()}

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
        if hasattr(node, "cap"):
            node.cap.release()
        cv2.destroyAllWindows()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
