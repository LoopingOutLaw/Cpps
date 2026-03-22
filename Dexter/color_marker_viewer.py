#!/usr/bin/env python3
"""
color_marker_viewer.py - Color-Based Marker Detection for Dexter Inventory
===========================================================================
Detects colored circular markers in the Gazebo simulation for establishing
homography and tracking box positions.

Reference Markers (on floor):
  Marker 1 (CYAN)    at (0.30, -0.50)m - front-left
  Marker 2 (MAGENTA) at (1.10, -0.50)m - front-right
  Marker 3 (YELLOW)  at (0.30, +0.50)m - back-left
  Marker 4 (RED)     at (1.10, +0.50)m - back-right

Box Markers (on boxes):
  Box 0 (WHITE marker on RED box)   at slot 0
  Box 1 (ORANGE marker on AMBER box) at slot 1  
  Box 2 (BLUE marker on BLUE box)   at slot 2
  Box 3 (GREEN marker on GREEN box) at slot 3

Usage:
    ros2 launch dexter_bringup simulated_robot.launch.py
    # In another terminal:
    cd ~/Cpps/Dexter && source install/setup.bash
    python3 color_marker_viewer.py

Press 'q' to quit, 's' to save screenshot.
"""

import cv2
import numpy as np
import json
import time
from typing import Dict, List, Optional, Tuple
from collections import deque

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from sensor_msgs.msg import Image
from cv_bridge import CvBridge

# ── Configuration ─────────────────────────────────────────────────────────────

CAMERA_TOPIC = "/camera/image_raw"

# Reference marker world positions (meters from robot base_link)
REF_WORLD_M: Dict[int, Tuple[float, float]] = {
    1: (0.300, -0.500),   # CYAN - front-left
    2: (1.100, -0.500),   # MAGENTA - front-right
    3: (0.300, +0.500),   # YELLOW - back-left
    4: (1.100, +0.500),   # RED - back-right
}

# HSV color ranges for reference markers (H: 0-179, S: 0-255, V: 0-255)
# These are tuned for the Gazebo simulation colors
REF_COLORS: Dict[int, Tuple[Tuple[int,int,int], Tuple[int,int,int], str]] = {
    # ID: (lower_hsv, upper_hsv, name)
    1: ((80, 100, 100), (100, 255, 255), "CYAN"),      # Cyan
    2: ((140, 100, 100), (170, 255, 255), "MAGENTA"),  # Magenta/Pink
    3: ((20, 100, 100), (35, 255, 255), "YELLOW"),     # Yellow
    4: ((0, 150, 150), (10, 255, 255), "RED"),         # Red (low hue)
}

# Box marker colors
BOX_COLORS: Dict[int, Tuple[Tuple[int,int,int], Tuple[int,int,int], str]] = {
    # Slot: (lower_hsv, upper_hsv, name)
    0: ((0, 0, 200), (180, 50, 255), "WHITE"),         # White marker
    1: ((10, 150, 150), (25, 255, 255), "ORANGE"),     # Orange marker
    2: ((100, 100, 100), (130, 255, 255), "BLUE"),     # Blue marker
    3: ((40, 100, 100), (80, 255, 255), "GREEN"),      # Green marker
}

# Fallback positions (meters)
SLOT_FALLBACK_M: Dict[int, Tuple[float, float]] = {
    0: (1.048, -0.642),
    1: (1.209, -0.220),
    2: (1.209, +0.220),
    3: (1.048, +0.642),
}
BOX_Z_M = 1.156

# Detection parameters
MIN_MARKER_AREA = 100
MAX_MARKER_AREA = 50000
MIN_CIRCULARITY = 0.5


class ColorMarkerViewer(Node):
    def __init__(self):
        super().__init__("color_marker_viewer")
        
        self.bridge = CvBridge()
        self.latest_frame = None
        self.frame_count = 0
        self.fps = 0.0
        self.fps_time = time.time()
        self.fps_count = 0
        
        # Homography
        self.H_matrix: Optional[np.ndarray] = None
        self.H_history: deque = deque(maxlen=10)
        
        # Slot positions
        self.slot_pos: Dict[int, dict] = {
            s: {"x": fx, "y": fy, "z": BOX_Z_M, "detected": False}
            for s, (fx, fy) in SLOT_FALLBACK_M.items()
        }
        
        # Publisher for box poses
        self.poses_pub = self.create_publisher(String, "/inventory/box_poses", 10)
        
        # Subscriber
        self.image_sub = self.create_subscription(
            Image, CAMERA_TOPIC, self.image_callback, 10)
        
        self.get_logger().info("=" * 60)
        self.get_logger().info("Color Marker Viewer Started")
        self.get_logger().info(f"  Subscribing to: {CAMERA_TOPIC}")
        self.get_logger().info("  Press 'q' to quit, 's' for screenshot")
        self.get_logger().info("=" * 60)
        
        cv2.namedWindow("Color Marker Viewer", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Color Marker Viewer", 1280, 720)
    
    def image_callback(self, msg: Image):
        try:
            self.latest_frame = self.bridge.imgmsg_to_cv2(msg, "bgr8")
            self.frame_count += 1
        except Exception as e:
            self.get_logger().error(f"Image conversion error: {e}")
    
    def find_colored_marker(self, hsv: np.ndarray, lower: Tuple, upper: Tuple
                           ) -> Optional[Tuple[float, float, float]]:
        """Find a colored circular marker. Returns (cx, cy, area) or None."""
        lower = np.array(lower, dtype=np.uint8)
        upper = np.array(upper, dtype=np.uint8)
        
        mask = cv2.inRange(hsv, lower, upper)
        
        # Clean up mask
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        best = None
        best_area = 0
        
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < MIN_MARKER_AREA or area > MAX_MARKER_AREA:
                continue
            
            # Check circularity
            perimeter = cv2.arcLength(cnt, True)
            if perimeter == 0:
                continue
            circularity = 4 * np.pi * area / (perimeter * perimeter)
            if circularity < MIN_CIRCULARITY:
                continue
            
            # Get centroid
            M = cv2.moments(cnt)
            if M["m00"] == 0:
                continue
            cx = M["m10"] / M["m00"]
            cy = M["m01"] / M["m00"]
            
            if area > best_area:
                best = (cx, cy, area)
                best_area = area
        
        return best
    
    def update_homography(self, ref_pixels: List[Tuple[float, float]], 
                          ref_world: List[Tuple[float, float]]):
        """Update homography from detected reference markers."""
        if len(ref_pixels) < 4:
            return
        
        src = np.array(ref_pixels, dtype=np.float32)
        dst = np.array([[w[0]*1000, w[1]*1000] for w in ref_world], dtype=np.float32)
        
        H, _ = cv2.findHomography(src, dst, cv2.RANSAC, 5.0)
        if H is None:
            return
        
        self.H_history.append(H)
        if len(self.H_history) >= 3:
            self.H_matrix = np.median(np.array(list(self.H_history)), axis=0)
        else:
            self.H_matrix = H
    
    def pixel_to_world_m(self, px: float, py: float) -> Optional[Tuple[float, float]]:
        if self.H_matrix is None:
            return None
        pts = np.array([[[px, py]]], dtype=np.float32)
        w = cv2.perspectiveTransform(pts, self.H_matrix)
        return float(w[0, 0, 0]) / 1000.0, float(w[0, 0, 1]) / 1000.0
    
    def process_frame(self, frame: np.ndarray) -> np.ndarray:
        vis = frame.copy()
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # Detect reference markers
        ref_pixels = []
        ref_world = []
        ref_ids = []
        
        for ref_id, (lower, upper, name) in REF_COLORS.items():
            result = self.find_colored_marker(hsv, lower, upper)
            if result:
                cx, cy, area = result
                ref_pixels.append((cx, cy))
                ref_world.append(REF_WORLD_M[ref_id])
                ref_ids.append(ref_id)
                
                # Draw reference marker
                cv2.circle(vis, (int(cx), int(cy)), 15, (0, 255, 255), 3)
                cv2.putText(vis, f"REF {ref_id} ({name})",
                           (int(cx) + 20, int(cy) - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        
        # Update homography
        self.update_homography(ref_pixels, ref_world)
        
        # Draw homography grid
        if self.H_matrix is not None:
            self.draw_grid(vis)
        
        # Detect box markers
        for slot, (lower, upper, name) in BOX_COLORS.items():
            result = self.find_colored_marker(hsv, lower, upper)
            if result:
                cx, cy, area = result
                
                # Convert to world coordinates
                world = self.pixel_to_world_m(cx, cy)
                if world:
                    x_m, y_m = world
                    # Sanity check
                    if 0.5 < x_m < 2.0 and -1.2 < y_m < 1.2:
                        self.slot_pos[slot] = {
                            "x": round(x_m, 4),
                            "y": round(y_m, 4),
                            "z": BOX_Z_M,
                            "detected": True,
                        }
                        
                        # Draw box marker
                        cv2.circle(vis, (int(cx), int(cy)), 12, (0, 255, 0), 3)
                        cv2.putText(vis, f"BOX {slot} ({x_m:.2f},{y_m:.2f}m)",
                                   (int(cx) + 15, int(cy) - 15),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 0), 2)
        
        # Draw status
        self.draw_status(vis, len(ref_ids), ref_ids)
        
        # Publish poses
        self.publish_poses()
        
        return vis
    
    def draw_grid(self, vis: np.ndarray):
        """Draw reference grid on image."""
        if self.H_matrix is None:
            return
        try:
            Hi = np.linalg.inv(self.H_matrix)
            
            # Draw reference rectangle
            pts_mm = np.array([
                [REF_WORLD_M[1][0]*1000, REF_WORLD_M[1][1]*1000],
                [REF_WORLD_M[2][0]*1000, REF_WORLD_M[2][1]*1000],
                [REF_WORLD_M[4][0]*1000, REF_WORLD_M[4][1]*1000],
                [REF_WORLD_M[3][0]*1000, REF_WORLD_M[3][1]*1000],
            ], dtype=np.float32)
            
            proj = cv2.perspectiveTransform(pts_mm.reshape(1, -1, 2), Hi)[0].astype(int)
            cv2.polylines(vis, [proj.reshape(-1, 1, 2)], True, (180, 30, 30), 2)
            
            # Draw slot positions
            for slot, (fx, fy) in SLOT_FALLBACK_M.items():
                pt_mm = np.array([[[fx*1000, fy*1000]]], dtype=np.float32)
                proj = cv2.perspectiveTransform(pt_mm, Hi)
                ix, iy = int(proj[0,0,0]), int(proj[0,0,1])
                cv2.drawMarker(vis, (ix, iy), (255, 180, 0), cv2.MARKER_CROSS, 20, 2)
                cv2.putText(vis, f"S{slot}", (ix+8, iy-8),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 180, 0), 1)
        except Exception:
            pass
    
    def draw_status(self, vis: np.ndarray, ref_count: int, ref_ids: List[int]):
        h_ok = self.H_matrix is not None
        
        lines = [
            (f"FPS: {self.fps:.1f}  |  Frame: {self.frame_count}", (180, 180, 180)),
            (f"Homography: {'OK' if h_ok else 'WAITING (need 4 refs)'}",
             (0, 220, 0) if h_ok else (0, 100, 255)),
            (f"Refs: {ref_count}/4  IDs: {sorted(ref_ids)}",
             (0, 220, 0) if ref_count == 4 else (0, 100, 255)),
        ]
        
        for slot, info in self.slot_pos.items():
            col = (0, 255, 100) if info["detected"] else (80, 80, 80)
            mode = "DETECTED" if info["detected"] else "fallback"
            lines.append(
                (f"Slot {slot}: {mode} ({info['x']:.3f}, {info['y']:.3f})m", col))
        
        # Background
        overlay = vis.copy()
        cv2.rectangle(overlay, (0, 0), (480, 20 + len(lines) * 26), (10, 10, 10), -1)
        cv2.addWeighted(overlay, 0.7, vis, 0.3, 0, vis)
        
        for i, (text, color) in enumerate(lines):
            cv2.putText(vis, text, (10, 22 + i * 26),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)
    
    def publish_poses(self):
        payload = {str(s): info for s, info in self.slot_pos.items()}
        msg = String()
        msg.data = json.dumps(payload)
        self.poses_pub.publish(msg)
    
    def spin_with_display(self):
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
                wait_img = np.zeros((720, 1280, 3), dtype=np.uint8)
                cv2.putText(wait_img, "Waiting for camera feed...",
                           (400, 350), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 150, 255), 2)
                cv2.putText(wait_img, f"Topic: {CAMERA_TOPIC}",
                           (450, 400), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (150, 150, 150), 1)
                cv2.imshow("Color Marker Viewer", wait_img)
            else:
                vis = self.process_frame(self.latest_frame)
                cv2.imshow("Color Marker Viewer", vis)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('s'):
                filename = f"marker_screenshot_{int(time.time())}.png"
                if self.latest_frame is not None:
                    cv2.imwrite(filename, self.process_frame(self.latest_frame))
                    self.get_logger().info(f"Screenshot saved: {filename}")
        
        cv2.destroyAllWindows()


def main():
    rclpy.init()
    viewer = ColorMarkerViewer()
    try:
        viewer.spin_with_display()
    except KeyboardInterrupt:
        pass
    finally:
        viewer.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
