#!/usr/bin/env python3
"""
aruco_viewer.py - Standalone ArUco Detection Viewer for Dexter Inventory
=========================================================================
Run this SEPARATELY from the main launch to see the ArUco detection window.

Usage:
    # First, start the simulation:
    ros2 launch dexter_bringup simulated_robot.launch.py

    # Then in another terminal, run this viewer:
    cd ~/Cpps/Dexter
    source install/setup.bash
    python3 aruco_viewer.py

This script:
  - Subscribes to /camera/image_raw from Gazebo
  - Detects ArUco markers (reference IDs 1-4, box IDs 10-13)
  - Shows a live window with detection overlay
  - Computes and displays the homography grid
  - Publishes detected poses to /inventory/box_poses (same as the ROS node)

Press 'q' to quit, 's' to save a screenshot.
"""

import cv2
import numpy as np
import json
import math
import time
from collections import deque
from typing import Dict, List, Optional, Tuple

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from sensor_msgs.msg import Image
from cv_bridge import CvBridge

# ── Configuration ─────────────────────────────────────────────────────────────

CAMERA_TOPIC = "/camera/image_raw"

# Reference marker world positions (mm from robot base_link)
# MUST MATCH inventory.sdf ref_marker positions!
REF_WORLD_MM: Dict[int, List[float]] = {
    1: [500.0,  -650.0],   # front-left
    2: [1550.0, -650.0],   # front-right
    3: [500.0,  +650.0],   # back-left
    4: [1550.0, +650.0],   # back-right
}
REF_IDS = list(REF_WORLD_MM.keys())

# Box marker → slot mapping
BOX_MARKER_TO_SLOT: Dict[int, int] = {10: 0, 11: 1, 12: 2, 13: 3}

# Fallback positions (meters)
SLOT_FALLBACK_M: Dict[int, Tuple[float, float]] = {
    0: (1.048, -0.642),
    1: (1.209, -0.220),
    2: (1.209, +0.220),
    3: (1.048, +0.642),
}
BOX_Z_M = 1.156

# Colors (BGR)
COL_REF     = (0,   200, 255)   # cyan - reference markers
COL_BOX     = (0,   255, 100)   # green - detected boxes
COL_FALLBK  = (80,  80,  80)    # gray - fallback positions
COL_GRID    = (180, 30,  30)    # dark blue - homography grid
COL_OK      = (0,   220, 0)     # green - status OK
COL_WARN    = (0,   100, 255)   # orange - warning


class ArucoViewer(Node):
    def __init__(self):
        super().__init__("aruco_viewer")
        
        self.bridge = CvBridge()
        self.latest_frame = None
        self.frame_count = 0
        self.fps = 0.0
        self.fps_time = time.time()
        self.fps_count = 0
        
        # ArUco detector
        self.aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
        params = cv2.aruco.DetectorParameters()
        params.cornerRefinementMethod = cv2.aruco.CORNER_REFINE_SUBPIX
        params.minMarkerPerimeterRate = 0.02
        params.maxMarkerPerimeterRate = 0.9
        params.adaptiveThreshWinSizeMin = 3
        params.adaptiveThreshWinSizeMax = 23
        params.adaptiveThreshWinSizeStep = 4
        self.detector = cv2.aruco.ArucoDetector(self.aruco_dict, params)
        
        # Homography state
        self.H_matrix: Optional[np.ndarray] = None
        self.H_history: deque = deque(maxlen=10)
        
        # Slot positions
        self.slot_pos: Dict[int, dict] = {
            s: {"x": fx, "y": fy, "z": BOX_Z_M, "detected": False, "yaw_deg": 0.0}
            for s, (fx, fy) in SLOT_FALLBACK_M.items()
        }
        
        # Camera calibration (approximate for wide-angle)
        self.cam_mtx = np.array([[800, 0, 640],
                                  [0, 800, 360],
                                  [0, 0, 1]], dtype=np.float32)
        self.dist = np.zeros(4, dtype=np.float32)
        
        # Publisher for box poses
        self.poses_pub = self.create_publisher(String, "/inventory/box_poses", 10)
        
        # Subscriber
        self.image_sub = self.create_subscription(
            Image, CAMERA_TOPIC, self.image_callback, 10)
        
        self.get_logger().info("=" * 60)
        self.get_logger().info("ArUco Viewer Started")
        self.get_logger().info(f"  Subscribing to: {CAMERA_TOPIC}")
        self.get_logger().info("  Press 'q' to quit, 's' to save screenshot")
        self.get_logger().info("=" * 60)
        
        # Create window
        cv2.namedWindow("ArUco Viewer", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("ArUco Viewer", 1280, 720)
        
    def image_callback(self, msg: Image):
        try:
            self.latest_frame = self.bridge.imgmsg_to_cv2(msg, "bgr8")
            self.frame_count += 1
        except Exception as e:
            self.get_logger().error(f"Image conversion error: {e}")
    
    def preprocess(self, gray: np.ndarray) -> List[np.ndarray]:
        """Multi-pass preprocessing for robust detection."""
        results = []
        
        # 1. Normalized
        norm = cv2.normalize(gray, None, 0, 255, cv2.NORM_MINMAX)
        results.append(norm)
        
        # 2. CLAHE + gamma correction
        clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(8, 8))
        clahe_img = clahe.apply(norm)
        gamma_table = (np.arange(256) / 255.0 ** (1.0 / 0.7) * 255).astype(np.uint8)
        gamma_img = cv2.LUT(clahe_img, gamma_table)
        results.append(gamma_img)
        
        # 3. Bilateral filter + sharpening
        bilateral = cv2.bilateralFilter(gamma_img, 9, 75, 75)
        kernel = np.array([[-1,-1,-1],[-1,9,-1],[-1,-1,-1]])
        sharpened = cv2.filter2D(bilateral, -1, kernel)
        results.append(sharpened)
        
        return results
    
    def detect_markers(self, gray: np.ndarray):
        """Detect ArUco markers with multi-pass preprocessing."""
        best: Dict[int, tuple] = {}
        
        for processed in self.preprocess(gray):
            corners, ids, _ = self.detector.detectMarkers(processed)
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
    
    def update_homography(self, pix_pts: List, world_pts: List):
        """Compute pixel-to-world homography from reference markers."""
        if len(pix_pts) < 4:
            return
        
        src = np.array(pix_pts, dtype=np.float32)
        dst = np.array(world_pts, dtype=np.float32)
        H, _ = cv2.findHomography(src, dst, cv2.RANSAC, 5.0)
        
        if H is None:
            return
        
        self.H_history.append(H)
        if len(self.H_history) >= 3:
            self.H_matrix = np.median(np.array(list(self.H_history)), axis=0)
        else:
            self.H_matrix = H
    
    def pixel_to_world_mm(self, px: float, py: float) -> Tuple[Optional[float], Optional[float]]:
        if self.H_matrix is None:
            return None, None
        pts = np.array([[[px, py]]], dtype=np.float32)
        w = cv2.perspectiveTransform(pts, self.H_matrix)
        return float(w[0, 0, 0]), float(w[0, 0, 1])
    
    def marker_yaw(self, corners: np.ndarray) -> float:
        dx = corners[1, 0] - corners[0, 0]
        dy = corners[1, 1] - corners[0, 1]
        deg = math.degrees(math.atan2(dy, dx))
        if deg < 0:
            deg += 360
        return deg if deg < 180 else -(360 - deg)
    
    def draw_grid(self, vis: np.ndarray):
        """Draw the homography reference grid."""
        if self.H_matrix is None:
            return
        
        try:
            Hi = np.linalg.inv(self.H_matrix)
            
            # Draw reference rectangle
            pts = np.array([REF_WORLD_MM[1], REF_WORLD_MM[2],
                           REF_WORLD_MM[4], REF_WORLD_MM[3]], dtype=np.float32)
            proj = cv2.perspectiveTransform(pts.reshape(1, -1, 2), Hi)[0].astype(int)
            cv2.polylines(vis, [proj.reshape(-1, 1, 2)], True, COL_GRID, 2)
            
            # Draw slot target positions
            for slot, (fx, fy) in SLOT_FALLBACK_M.items():
                w = cv2.perspectiveTransform(
                    np.array([[[fx*1000, fy*1000]]], dtype=np.float32), Hi)
                ix, iy = int(w[0,0,0]), int(w[0,0,1])
                cv2.drawMarker(vis, (ix, iy), (255, 180, 0), cv2.MARKER_CROSS, 25, 2)
                cv2.putText(vis, f"S{slot}", (ix+10, iy-10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 180, 0), 2)
        except Exception:
            pass
    
    def draw_status(self, vis: np.ndarray, ref_count: int, ref_ids: List[int]):
        """Draw status overlay."""
        h_ok = self.H_matrix is not None
        
        lines = [
            (f"FPS: {self.fps:.1f}  |  Frame: {self.frame_count}", (180, 180, 180)),
            (f"Homography: {'OK' if h_ok else 'WAITING (need 4 refs)'}",
             COL_OK if h_ok else COL_WARN),
            (f"Refs visible: {ref_count}/4  IDs: {ref_ids}",
             COL_OK if ref_count == 4 else COL_WARN),
        ]
        
        for slot, info in self.slot_pos.items():
            col = COL_BOX if info["detected"] else COL_FALLBK
            mode = "DETECTED" if info["detected"] else "fallback"
            lines.append(
                (f"Slot {slot}: {mode} ({info['x']:.3f}, {info['y']:.3f})m", col))
        
        # Dark semi-transparent background
        overlay = vis.copy()
        cv2.rectangle(overlay, (0, 0), (500, 20 + len(lines) * 26), (10, 10, 10), -1)
        cv2.addWeighted(overlay, 0.7, vis, 0.3, 0, vis)
        
        for i, (text, color) in enumerate(lines):
            cv2.putText(vis, text, (10, 22 + i * 26),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
    
    def process_frame(self, frame: np.ndarray) -> np.ndarray:
        """Process a frame and return visualization."""
        # Undistort
        und = cv2.undistort(frame, self.cam_mtx, self.dist)
        gray = cv2.cvtColor(und, cv2.COLOR_BGR2GRAY)
        
        # Detect markers
        corners, ids = self.detect_markers(gray)
        
        vis = und.copy()
        
        # Draw detected markers
        if ids is not None:
            cv2.aruco.drawDetectedMarkers(vis, corners, ids)
        
        # Collect reference markers
        ref_pix, ref_world, ref_ids = [], [], []
        if ids is not None:
            for i, mid in enumerate(ids.flatten()):
                if mid in REF_IDS:
                    ctr = corners[i][0].mean(axis=0)
                    ref_pix.append(ctr)
                    ref_world.append(REF_WORLD_MM[mid])
                    ref_ids.append(int(mid))
                    
                    # Draw reference marker label
                    cx, cy = int(ctr[0]), int(ctr[1])
                    cv2.circle(vis, (cx, cy), 12, COL_REF, -1)
                    cv2.putText(vis, f"REF {mid}",
                               (cx + 15, cy - 10),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, COL_REF, 2)
        
        # Update homography
        self.update_homography(ref_pix, ref_world)
        
        # Draw grid
        self.draw_grid(vis)
        
        # Process box markers
        if self.H_matrix is not None and ids is not None:
            for i, mid in enumerate(ids.flatten()):
                if mid not in BOX_MARKER_TO_SLOT:
                    continue
                
                slot = BOX_MARKER_TO_SLOT[mid]
                c = corners[i][0]
                px, py = float(c[:, 0].mean()), float(c[:, 1].mean())
                
                x_mm, y_mm = self.pixel_to_world_mm(px, py)
                if x_mm is None:
                    continue
                
                x_m, y_m = x_mm / 1000.0, y_mm / 1000.0
                yaw = self.marker_yaw(c)
                
                # Sanity check
                if not (0.3 < x_m < 2.0 and -1.5 < y_m < 1.5):
                    continue
                
                self.slot_pos[slot] = {
                    "x": round(x_m, 4),
                    "y": round(y_m, 4),
                    "z": BOX_Z_M,
                    "detected": True,
                    "yaw_deg": round(yaw, 1),
                }
                
                # Draw box marker
                ix, iy = int(px), int(py)
                cv2.circle(vis, (ix, iy), 10, COL_BOX, -1)
                cv2.putText(vis, f"BOX {slot} ({x_m:.2f},{y_m:.2f})",
                           (ix, iy - 35),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.65, COL_BOX, 2)
        
        # Draw status
        self.draw_status(vis, len(ref_ids), sorted(ref_ids))
        
        # Publish poses
        self.publish_poses()
        
        return vis
    
    def publish_poses(self):
        payload = {str(s): info for s, info in self.slot_pos.items()}
        msg = String()
        msg.data = json.dumps(payload)
        self.poses_pub.publish(msg)
    
    def spin_with_display(self):
        """Main loop with OpenCV display."""
        self.get_logger().info("Waiting for camera frames...")
        
        while rclpy.ok():
            rclpy.spin_once(self, timeout_sec=0.01)
            
            # Update FPS
            self.fps_count += 1
            now = time.time()
            if now - self.fps_time >= 1.0:
                self.fps = self.fps_count / (now - self.fps_time)
                self.fps_count = 0
                self.fps_time = now
            
            if self.latest_frame is None:
                # Show waiting message
                wait_img = np.zeros((720, 1280, 3), dtype=np.uint8)
                cv2.putText(wait_img, "Waiting for camera feed...",
                           (400, 350), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 150, 255), 2)
                cv2.putText(wait_img, f"Topic: {CAMERA_TOPIC}",
                           (450, 400), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (150, 150, 150), 1)
                cv2.putText(wait_img, "Make sure Gazebo simulation is running",
                           (350, 450), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (100, 100, 100), 1)
                cv2.imshow("ArUco Viewer", wait_img)
            else:
                vis = self.process_frame(self.latest_frame)
                cv2.imshow("ArUco Viewer", vis)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('s'):
                filename = f"aruco_screenshot_{int(time.time())}.png"
                if self.latest_frame is not None:
                    cv2.imwrite(filename, self.process_frame(self.latest_frame))
                    self.get_logger().info(f"Screenshot saved: {filename}")
        
        cv2.destroyAllWindows()


def main():
    rclpy.init()
    viewer = ArucoViewer()
    try:
        viewer.spin_with_display()
    except KeyboardInterrupt:
        pass
    finally:
        viewer.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
