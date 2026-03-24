#!/usr/bin/env python3
"""
visual_servo_node.py - Visual Servo Pick-and-Place for Dexter Arm
=================================================================

5-Phase approach with safe collision-free motion:
  Phase 1: Move to SAFE APPROACH point (behind target, toward robot)
  Phase 2: Open gripper and move forward to HOVER above target
  Phase 3: Visual servo in X-Y plane to align with target box
  Phase 4: Descend to PICK height, close gripper
  Phase 5: Lift, transit to drop zone, release

The approach direction is always FROM the robot TOWARD the box, so the arm
never passes over other boxes.

Trigger:
    ros2 topic pub --once /visual_servo/pick_request std_msgs/msg/Int32 "{data: 0}"
Watch:
    ros2 topic echo /visual_servo/status

Robot structure (from URDF):
    - joint_1: z-axis rotation at z=0.307m (base rotation)
    - joint_2: x-axis rotation at z=0.657m (shoulder)  
    - joint_3: x-axis rotation at z=1.457m (elbow)
    - claw_support: fixed at 0.82m from joint_3
    - gripper_left: offset from claw by (-0.22, 0.13, -0.1)

At HOME (j1=j2=j3=0):
    gripper_left is at (x=-0.24, y=0.95, z=1.357)
"""

from __future__ import annotations
import json
import math
import threading
import time
from enum import Enum, auto
from typing import Dict, List, Optional, Tuple

import numpy as np
from scipy.optimize import minimize

import rclpy
from builtin_interfaces.msg import Duration as DurationMsg
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node
from sensor_msgs.msg import JointState
from std_msgs.msg import String, Int32
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint


# ═══════════════════════════════════════════════════════════════════════════════
# KINEMATICS
# ═══════════════════════════════════════════════════════════════════════════════

def Rz(a: float) -> np.ndarray:
    """Rotation matrix around z-axis."""
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])

def Rx(a: float) -> np.ndarray:
    """Rotation matrix around x-axis."""
    c, s = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])

def forward_kinematics(j1: float, j2: float, j3: float) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Compute forward kinematics.
    Returns (claw_position, gripper_left_position, grip_center_position) in world frame.
    
    Gripper geometry (offsets from claw_support in local frame):
      - gripper_right: (-0.04, 0.13, -0.1)
      - gripper_left:  (-0.22, 0.13, -0.1)
      - grip_center:   (-0.13, 0.13, -0.1)  <- midpoint between fingers
      
    The fingertips extend further along local +Y. When arm reaches outward,
    local +Y points AWAY from robot, so fingertips are furthest from robot.
    
    For picking, we want the GRIP CENTER (between fingers) at the box position.
    """
    p = np.array([0.0, 0.0, 0.0])
    R = np.eye(3)
    
    # joint_1 origin: z=0.307
    p = p + R @ np.array([0, 0, 0.307])
    R = R @ Rz(j1)
    
    # joint_2 origin: xyz="-0.02 0 0.35"
    p = p + R @ np.array([-0.02, 0, 0.35])
    R = R @ Rx(j2)
    
    # joint_3 origin: xyz="0 0 0.8"
    p = p + R @ np.array([0, 0, 0.8])
    R = R @ Rx(j3)
    
    # claw_support: xyz="0 0.82 0"
    p_claw = p + R @ np.array([0, 0.82, 0])
    
    # gripper_left: xyz="-0.22 0.13 -0.1"
    p_gripper_left = p_claw + R @ np.array([-0.22, 0.13, -0.1])
    
    # grip_center: midpoint between gripper_left and gripper_right
    # gripper_right is at (-0.04, 0.13, -0.1), gripper_left at (-0.22, 0.13, -0.1)
    # center x = (-0.04 + -0.22) / 2 = -0.13
    p_grip_center = p_claw + R @ np.array([-0.13, 0.13, -0.1])
    
    return p_claw, p_gripper_left, p_grip_center

def fk_gripper(j1: float, j2: float, j3: float) -> Tuple[float, float, float]:
    """Get gripper_left position (legacy, for compatibility)."""
    _, p, _ = forward_kinematics(j1, j2, j3)
    return float(p[0]), float(p[1]), float(p[2])

def fk_grip_center(j1: float, j2: float, j3: float) -> Tuple[float, float, float]:
    """Get grip center position (between fingertips) - USE THIS FOR PICKING."""
    _, _, p = forward_kinematics(j1, j2, j3)
    return float(p[0]), float(p[1]), float(p[2])

def inverse_kinematics(target_x: float, target_y: float, target_z: float,
                       init_guess: Optional[List[float]] = None) -> Optional[List[float]]:
    """
    Solve inverse kinematics for GRIP CENTER to reach target position.
    Returns [j1, j2, j3] or None if no solution found.
    
    This targets the grip center (between fingertips), NOT gripper_left,
    so when we command the arm to go to a box position, the grip center
    (where the box will be held) ends up at that position.
    
    Joint limits: j1: ±171° (±2.98 rad), j2/j3: ±90° (±1.57 rad)
    """
    import math
    
    def error(joints):
        j1, j2, j3 = joints
        # Use grip center, not gripper_left!
        x, y, z = fk_grip_center(j1, j2, j3)
        return (x - target_x)**2 + (y - target_y)**2 + (z - target_z)**2
    
    # Compute initial j1 guess based on target direction
    # The arm extends 90° from j1 direction (along local +Y)
    target_angle = math.atan2(target_y, target_x)
    j1_init = target_angle - math.pi/2
    
    # Try multiple initial guesses with expanded j1 range
    guesses = [
        init_guess if init_guess else [j1_init, -0.5, 0.4],
        [j1_init, -0.5, 0.4],
        [j1_init + 0.3, -0.5, 0.4],
        [j1_init - 0.3, -0.5, 0.4],
        [j1_init, -0.3, 0.3],
        [j1_init, -0.7, 0.5],
        [-2.0, -0.5, 0.4],
        [-1.5, -0.5, 0.4],
        [-1.0, -0.5, 0.4],
        [2.0, -0.5, 0.4],
        [1.5, -0.5, 0.4],
    ]
    
    best_result = None
    best_err = float('inf')
    
    # j1 limit: ±171° = ±2.98 rad (PI * 0.95)
    J1_LIMIT = 2.98
    
    for guess in guesses:
        try:
            result = minimize(
                error, guess,
                bounds=[(-J1_LIMIT, J1_LIMIT), (-1.57, 1.57), (-1.57, 1.57)],
                method='L-BFGS-B',
                options={'maxiter': 300}
            )
            if result.fun < best_err:
                best_err = result.fun
                best_result = result
        except:
            pass
    
    if best_result is None or best_err > 0.01:  # 10cm tolerance
        return None
    
    return [float(best_result.x[0]), float(best_result.x[1]), float(best_result.x[2])]


# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

# Robot base position
ROBOT_BASE = (0.0, 0.0)

# Target positions for boxes (ground truth from SDF)
SLOT_POSITIONS: Dict[int, Tuple[float, float, float]] = {
    0: (1.048, -0.642, 1.156),
    1: (1.209, -0.220, 1.156),
    2: (1.209, +0.220, 1.156),
    3: (1.048, +0.642, 1.156),
}

# Heights
SAFE_Z = 1.45         # Safe height for approach (above all boxes)
HOVER_Z = 1.32        # Hover height just above the box
PICK_Z = 1.19         # Pick height (gripper z, slightly above box to grip sides)
DROP_Z = 1.32         # Drop zone height

# Approach offset - how far back from target to start approach
APPROACH_OFFSET = 0.20  # 20cm back from target (toward robot)

# Grip offset - how far back from box center to position grip center
# IMPORTANT: The FK/IK targets grip_center, but there's still an offset between
# where the FK thinks the gripper is and where it physically ends up.
# Positive value = arm stops CLOSER to robot (grip point is pulled back)
# Tune this value until the gripper fingers are centered over the box
GRIP_OFFSET = 0.50    # 35cm back from box - TUNE THIS VALUE

# Drop zone position (dispatch tray)
DROP_X = 0.664
DROP_Y = 1.034

# Timing
TRAJ_DURATION = 3.0      # Trajectory execution time
RESEND_INTERVAL = 1.5    # Resend trajectory every N seconds
JOINT_TOLERANCE = 0.03   # Joint position tolerance (rad)
MAX_WAIT_TIME = 45.0     # Maximum wait for motion
POLL_INTERVAL = 0.1      # Polling interval
XY_TOLERANCE = 0.03      # XY position tolerance (m) = 30mm
MAX_SERVO_ITERATIONS = 8

# Gripper
# joint_4 limits: -π/2 (open/spread) to 0.0 (closed/together)
# joint_5 mimics joint_4 with multiplier -1
GRIPPER_OPEN = -1.2      # Fingers spread apart (toward -π/2)
GRIPPER_CLOSED = 0.0     # Fingers together (at 0)
GRIP_DURATION = 1.0
PICK_DWELL = 1.5         # Wait after closing gripper
DROP_DWELL = 0.5

# ArUco
ARUCO_MAX_AGE = 5.0  # Maximum age of ArUco data (seconds)


# ═══════════════════════════════════════════════════════════════════════════════
# STATE MACHINE
# ═══════════════════════════════════════════════════════════════════════════════

class State(Enum):
    IDLE = auto()
    PHASE1_SAFE_APPROACH = auto()    # Move to safe point behind target
    PHASE2_OPEN_AND_ADVANCE = auto() # Open gripper, move to hover above target
    PHASE3_SERVO = auto()            # Visual servo alignment
    PHASE4_DESCEND_AND_GRIP = auto() # Lower and grip
    PHASE5_LIFT = auto()             # Lift with box
    PHASE6_TRANSIT = auto()          # Move to drop zone
    PHASE7_DROP = auto()             # Release box
    RETURN_HOME = auto()


class VisualServoNode(Node):
    def __init__(self):
        super().__init__("visual_servo_node")
        
        cb = ReentrantCallbackGroup()
        
        # Publishers
        self.arm_pub = self.create_publisher(
            JointTrajectory, "/arm_controller/joint_trajectory", 10)
        self.grip_pub = self.create_publisher(
            JointTrajectory, "/gripper_controller/joint_trajectory", 10)
        self.status_pub = self.create_publisher(
            String, "/visual_servo/status", 10)
        
        # Subscribers
        self.create_subscription(
            JointState, "/joint_states", self._joint_state_cb, 10, callback_group=cb)
        self.create_subscription(
            String, "/inventory/box_poses", self._box_poses_cb, 10, callback_group=cb)
        self.create_subscription(
            Int32, "/visual_servo/pick_request", self._pick_request_cb, 10, callback_group=cb)
        
        # State
        self._state = State.IDLE
        self._target_slot: Optional[int] = None
        self._lock = threading.Lock()
        
        # Joint state
        self._joints: Dict[str, float] = {f"joint_{i}": 0.0 for i in range(1, 6)}
        
        # ArUco box detection
        self._box_data: Dict[int, dict] = {}
        self._aruco_timestamp: float = 0.0
        
        # Start state machine thread
        threading.Thread(target=self._state_machine_loop, daemon=True).start()
        
        # Log startup
        x, y, z = fk_gripper(0, 0, 0)
        self.get_logger().info(
            f"\n{'='*70}\n"
            f"  Visual Servo Node Started (Safe Approach Version)\n"
            f"  HOME position: gripper at ({x:.3f}, {y:.3f}, {z:.3f})\n"
            f"  SAFE_Z: {SAFE_Z}m, HOVER_Z: {HOVER_Z}m, PICK_Z: {PICK_Z}m\n"
            f"  APPROACH_OFFSET: {APPROACH_OFFSET*100:.0f}cm\n"
            f"  XY tolerance: {XY_TOLERANCE*1000:.0f}mm\n"
            f"\n"
            f"  Trigger: ros2 topic pub --once /visual_servo/pick_request \\\n"
            f"           std_msgs/msg/Int32 \"{{data: 0}}\"\n"
            f"{'='*70}"
        )
    
    # ───────────────────────────────────────────────────────────────────────────
    # CALLBACKS
    # ───────────────────────────────────────────────────────────────────────────
    
    def _joint_state_cb(self, msg: JointState):
        with self._lock:
            for name, pos in zip(msg.name, msg.position):
                if name in self._joints:
                    self._joints[name] = float(pos)
    
    def _box_poses_cb(self, msg: String):
        try:
            data = json.loads(msg.data)
            with self._lock:
                for k, v in data.items():
                    self._box_data[int(k)] = v
                self._aruco_timestamp = time.time()
        except Exception as e:
            self.get_logger().warn(f"Box poses parse error: {e}")
    
    def _pick_request_cb(self, msg: Int32):
        slot = int(msg.data)
        if slot not in range(4):
            self.get_logger().warn(f"Invalid slot {slot}, must be 0-3")
            return
        
        with self._lock:
            if self._state != State.IDLE:
                self.get_logger().warn(f"Busy in state {self._state.name}")
                return
            self._target_slot = slot
            self._state = State.PHASE1_SAFE_APPROACH
        
        self.get_logger().info(f"Pick request received: slot {slot}")
    
    # ───────────────────────────────────────────────────────────────────────────
    # HELPERS
    # ───────────────────────────────────────────────────────────────────────────
    
    def _get_current_joints(self) -> List[float]:
        """Get current arm joint positions [j1, j2, j3]."""
        with self._lock:
            return [
                self._joints["joint_1"],
                self._joints["joint_2"],
                self._joints["joint_3"],
            ]
    
    def _get_current_gripper_pos(self) -> Tuple[float, float, float]:
        """Get current GRIP CENTER position from FK (between fingertips)."""
        joints = self._get_current_joints()
        return fk_grip_center(*joints)
    
    def _aruco_is_fresh(self) -> bool:
        """Check if ArUco data is recent."""
        with self._lock:
            return (time.time() - self._aruco_timestamp) < ARUCO_MAX_AGE
    
    def _get_target_xy(self, slot: int) -> Tuple[float, float]:
        """Get target XY from ArUco or fall back to ground truth."""
        with self._lock:
            info = self._box_data.get(slot, {})
        
        if info.get("detected") and self._aruco_is_fresh():
            return float(info["x"]), float(info["y"])
        
        # Fall back to ground truth
        return SLOT_POSITIONS[slot][0], SLOT_POSITIONS[slot][1]
    
    def _compute_approach_point(self, target_x: float, target_y: float) -> Tuple[float, float]:
        """
        Compute approach point - offset from target TOWARD the robot base.
        This ensures the arm approaches from behind, not passing over other boxes.
        """
        # Direction from robot to target
        dx = target_x - ROBOT_BASE[0]
        dy = target_y - ROBOT_BASE[1]
        dist = math.hypot(dx, dy)
        
        if dist < 0.1:
            return target_x, target_y
        
        # Unit vector from robot to target
        ux, uy = dx / dist, dy / dist
        
        # Approach point is offset BACK from target (toward robot)
        approach_x = target_x - ux * APPROACH_OFFSET
        approach_y = target_y - uy * APPROACH_OFFSET
        
        return approach_x, approach_y
    
    def _compute_grip_point(self, target_x: float, target_y: float) -> Tuple[float, float]:
        """
        Compute grip point - where to position the GRIP CENTER to grab the box.
        
        Since the FK/IK now targets the grip center (between fingertips) directly,
        we just need to apply GRIP_OFFSET if we want to grab off-center.
        With GRIP_OFFSET=0, grip center goes directly to box center.
        """
        # Direction from robot to target
        dx = target_x - ROBOT_BASE[0]
        dy = target_y - ROBOT_BASE[1]
        dist = math.hypot(dx, dy)
        
        if dist < 0.1:
            return target_x, target_y
        
        # Unit vector from robot to target
        ux, uy = dx / dist, dy / dist
        
        # GRIP_OFFSET: move toward robot if we want to grab the near edge of the box
        # With GRIP_OFFSET=0, grip center aligns with box center
        grip_x = target_x - ux * GRIP_OFFSET
        grip_y = target_y - uy * GRIP_OFFSET
        
        self.get_logger().info(f"[GRIP] Box: ({target_x:.3f}, {target_y:.3f}) -> "
                               f"Grip point: ({grip_x:.3f}, {grip_y:.3f})")
        
        return grip_x, grip_y
    
    def _log(self, msg: str):
        """Log and publish status."""
        status_msg = String()
        status_msg.data = msg
        self.status_pub.publish(status_msg)
        self.get_logger().info(f"[SERVO] {msg}")
    
    def _set_state(self, new_state: State):
        """Set state machine state."""
        with self._lock:
            self._state = new_state
        self._log(f"State -> {new_state.name}")
    
    # ───────────────────────────────────────────────────────────────────────────
    # MOTION
    # ───────────────────────────────────────────────────────────────────────────
    
    def _publish_arm_trajectory(self, joints: List[float], duration: float = TRAJ_DURATION):
        """Publish arm trajectory command."""
        msg = JointTrajectory()
        msg.joint_names = ["joint_1", "joint_2", "joint_3"]
        
        pt = JointTrajectoryPoint()
        pt.positions = [float(j) for j in joints]
        pt.velocities = [0.0, 0.0, 0.0]
        
        sec = int(duration)
        nanosec = int((duration - sec) * 1e9)
        pt.time_from_start = DurationMsg(sec=sec, nanosec=nanosec)
        
        msg.points = [pt]
        self.arm_pub.publish(msg)
    
    def _publish_gripper(self, position: float):
        """Publish gripper command."""
        msg = JointTrajectory()
        msg.joint_names = ["joint_4"]
        
        pt = JointTrajectoryPoint()
        pt.positions = [float(position)]
        pt.velocities = [0.0]
        pt.time_from_start = DurationMsg(sec=int(GRIP_DURATION), nanosec=0)
        
        msg.points = [pt]
        self.grip_pub.publish(msg)
    
    def _move_to_joints(self, target_joints: List[float], label: str) -> bool:
        """
        Move arm to target joint positions.
        Re-publishes trajectory periodically until reached or timeout.
        Returns True on success.
        """
        x, y, z = fk_gripper(*target_joints)
        self._log(f"MOVE {label}: joints=[{target_joints[0]:.3f}, {target_joints[1]:.3f}, {target_joints[2]:.3f}] "
                  f"-> gripper=({x:.3f}, {y:.3f}, {z:.3f})")
        
        deadline = time.time() + MAX_WAIT_TIME
        last_send = 0.0
        last_log = 0.0
        
        while time.time() < deadline:
            current = self._get_current_joints()
            err = max(abs(current[i] - target_joints[i]) for i in range(3))
            
            if err < JOINT_TOLERANCE:
                cx, cy, cz = fk_gripper(*current)
                self._log(f"  ARRIVED {label}: err={err:.4f}rad, gripper=({cx:.3f}, {cy:.3f}, {cz:.3f})")
                return True
            
            now = time.time()
            
            # Re-send trajectory periodically
            if now - last_send >= RESEND_INTERVAL:
                self._publish_arm_trajectory(target_joints)
                last_send = now
            
            # Log progress periodically
            if now - last_log >= 3.0:
                cx, cy, cz = fk_gripper(*current)
                self._log(f"  MOVING {label}: err={err:.4f}rad, gripper=({cx:.3f}, {cy:.3f}, {cz:.3f})")
                last_log = now
            
            time.sleep(POLL_INTERVAL)
        
        self._log(f"  TIMEOUT {label}")
        return False
    
    def _move_to_position(self, target_x: float, target_y: float, target_z: float, 
                          label: str) -> bool:
        """
        Move gripper to target XYZ position using IK.
        Returns True on success.
        """
        current = self._get_current_joints()
        joints = inverse_kinematics(target_x, target_y, target_z, current)
        
        if joints is None:
            self._log(f"  IK FAILED for ({target_x:.3f}, {target_y:.3f}, {target_z:.3f})")
            return False
        
        return self._move_to_joints(joints, label)
    
    # ───────────────────────────────────────────────────────────────────────────
    # STATE MACHINE
    # ───────────────────────────────────────────────────────────────────────────
    
    def _state_machine_loop(self):
        """Main state machine loop."""
        while rclpy.ok():
            with self._lock:
                state = self._state
                slot = self._target_slot
            
            if state == State.IDLE or slot is None:
                time.sleep(0.1)
                continue
            
            try:
                if state == State.PHASE1_SAFE_APPROACH:
                    self._do_phase1_safe_approach(slot)
                elif state == State.PHASE2_OPEN_AND_ADVANCE:
                    self._do_phase2_open_and_advance(slot)
                elif state == State.PHASE3_SERVO:
                    self._do_phase3_servo(slot)
                elif state == State.PHASE4_DESCEND_AND_GRIP:
                    self._do_phase4_descend_and_grip(slot)
                elif state == State.PHASE5_LIFT:
                    self._do_phase5_lift(slot)
                elif state == State.PHASE6_TRANSIT:
                    self._do_phase6_transit(slot)
                elif state == State.PHASE7_DROP:
                    self._do_phase7_drop(slot)
                elif state == State.RETURN_HOME:
                    self._do_return_home(slot)
            except Exception as e:
                import traceback
                self.get_logger().error(f"State machine error: {e}\n{traceback.format_exc()}")
                self._set_state(State.RETURN_HOME)
            
            time.sleep(0.05)
    
    def _do_phase1_safe_approach(self, slot: int):
        """Phase 1: Move to safe approach point (behind and above target)."""
        self._log(f"═══ PHASE 1: SAFE APPROACH ═══")
        
        # Get target position
        target_x, target_y = self._get_target_xy(slot)
        self._log(f"  Target: slot {slot} at ({target_x:.3f}, {target_y:.3f})")
        
        # Compute approach point (behind target, toward robot)
        approach_x, approach_y = self._compute_approach_point(target_x, target_y)
        self._log(f"  Approach point: ({approach_x:.3f}, {approach_y:.3f}) at z={SAFE_Z}m")
        
        # Move to safe approach point at high altitude
        if not self._move_to_position(approach_x, approach_y, SAFE_Z, "safe-approach"):
            self._log("  Phase 1 FAILED - going home")
            self._set_state(State.RETURN_HOME)
            return
        
        self._set_state(State.PHASE2_OPEN_AND_ADVANCE)
    
    def _do_phase2_open_and_advance(self, slot: int):
        """Phase 2: Open gripper and advance to hover position above target."""
        self._log(f"═══ PHASE 2: OPEN GRIPPER & ADVANCE ═══")
        
        # Open gripper
        self._log("  Opening gripper...")
        self._publish_gripper(GRIPPER_OPEN)
        time.sleep(GRIP_DURATION + 0.3)
        
        # Get target position and compute grip point (offset toward robot)
        target_x, target_y = self._get_target_xy(slot)
        grip_x, grip_y = self._compute_grip_point(target_x, target_y)
        source = "ArUco" if self._aruco_is_fresh() else "GT"
        self._log(f"  Box center: ({target_x:.3f}, {target_y:.3f}) [{source}]")
        self._log(f"  Grip point: ({grip_x:.3f}, {grip_y:.3f}) (offset {GRIP_OFFSET*100:.0f}cm toward robot)")
        
        # Move to hover position above grip point (not box center!)
        if not self._move_to_position(grip_x, grip_y, HOVER_Z, "hover"):
            self._log("  Phase 2 FAILED - going home")
            self._set_state(State.RETURN_HOME)
            return
        
        self._set_state(State.PHASE3_SERVO)
    
    def _do_phase3_servo(self, slot: int):
        """Phase 3: Visual servo to align precisely with grip point."""
        self._log(f"═══ PHASE 3: VISUAL SERVO ═══")
        
        for iteration in range(MAX_SERVO_ITERATIONS):
            # Get current gripper position
            curr_x, curr_y, curr_z = self._get_current_gripper_pos()
            
            # Get target from ArUco and compute grip point
            target_x, target_y = self._get_target_xy(slot)
            grip_x, grip_y = self._compute_grip_point(target_x, target_y)
            source = "ArUco" if self._aruco_is_fresh() else "GT"
            
            # Compute error to grip point (not box center!)
            err_x = grip_x - curr_x
            err_y = grip_y - curr_y
            err_dist = math.hypot(err_x, err_y)
            
            self._log(f"  Iter {iteration+1}: pos=({curr_x:.3f}, {curr_y:.3f}), "
                      f"grip=({grip_x:.3f}, {grip_y:.3f}) [{source}], "
                      f"err={err_dist*1000:.0f}mm")
            
            # Check if aligned
            if err_dist < XY_TOLERANCE:
                self._log(f"  ALIGNED! err={err_dist*1000:.0f}mm < {XY_TOLERANCE*1000:.0f}mm")
                break
            
            # Move toward grip point (at hover height)
            if not self._move_to_position(grip_x, grip_y, HOVER_Z, f"servo-{iteration+1}"):
                self._log("  Servo move FAILED")
                break
            
            # Small delay to let ArUco update
            time.sleep(0.3)
        
        # Final check
        curr_x, curr_y, curr_z = self._get_current_gripper_pos()
        target_x, target_y = self._get_target_xy(slot)
        grip_x, grip_y = self._compute_grip_point(target_x, target_y)
        final_err = math.hypot(grip_x - curr_x, grip_y - curr_y)
        
        if final_err > 0.08:  # 8cm max acceptable error
            self._log(f"  ABORT: final error {final_err*1000:.0f}mm too large")
            self._set_state(State.RETURN_HOME)
            return
        
        self._log(f"  Phase 3 complete: final error = {final_err*1000:.0f}mm")
        self._set_state(State.PHASE4_DESCEND_AND_GRIP)
    
    def _do_phase4_descend_and_grip(self, slot: int):
        """Phase 4: Descend to pick height with open gripper, then close to grip."""
        self._log(f"═══ PHASE 4: DESCEND & GRIP ═══")
        
        # ENSURE gripper is open before descending (re-assert in case command was lost)
        self._log("  Ensuring gripper is OPEN before descent...")
        self._publish_gripper(GRIPPER_OPEN)
        time.sleep(0.5)  # Brief wait for gripper to open
        
        # Get current XY (keep it, just lower Z)
        curr_x, curr_y, _ = self._get_current_gripper_pos()
        
        self._log(f"  Descending with OPEN gripper from z={HOVER_Z}m to z={PICK_Z}m")
        
        if not self._move_to_position(curr_x, curr_y, PICK_Z, "descend"):
            self._log("  Descend FAILED - going home")
            self._set_state(State.RETURN_HOME)
            return
        
        # Small dwell at pick height with gripper still open (box between fingers)
        self._log("  At pick height - box should be between open fingers")
        time.sleep(0.3)
        
        # Now close gripper to grab the box
        self._log("  CLOSING gripper to grab box...")
        self._publish_gripper(GRIPPER_CLOSED)
        time.sleep(GRIP_DURATION + PICK_DWELL)
        
        self._set_state(State.PHASE5_LIFT)
    
    def _do_phase5_lift(self, slot: int):
        """Phase 5: Lift with the box."""
        self._log(f"═══ PHASE 5: LIFT ═══")
        
        curr_x, curr_y, _ = self._get_current_gripper_pos()
        
        # Lift to safe height
        if not self._move_to_position(curr_x, curr_y, SAFE_Z, "lift"):
            self._log("  Lift FAILED")
        
        self._set_state(State.PHASE6_TRANSIT)
    
    def _do_phase6_transit(self, slot: int):
        """Phase 6: Transit to drop zone."""
        self._log(f"═══ PHASE 6: TRANSIT TO DROP ZONE ═══")
        self._log(f"  Drop zone: ({DROP_X:.3f}, {DROP_Y:.3f})")
        
        # Move to drop zone at safe height
        if not self._move_to_position(DROP_X, DROP_Y, SAFE_Z, "transit"):
            self._log("  Transit FAILED")
        
        # Lower to drop height
        if not self._move_to_position(DROP_X, DROP_Y, DROP_Z, "lower-to-drop"):
            self._log("  Lower FAILED")
        
        self._set_state(State.PHASE7_DROP)
    
    def _do_phase7_drop(self, slot: int):
        """Phase 7: Release the box."""
        self._log(f"═══ PHASE 7: DROP ═══")
        
        # Open gripper to release
        self._log("  Opening gripper to release...")
        self._publish_gripper(GRIPPER_OPEN)
        time.sleep(GRIP_DURATION + DROP_DWELL)
        
        # Retract upward
        if not self._move_to_position(DROP_X, DROP_Y, SAFE_Z, "retract"):
            self._log("  Retract FAILED")
        
        self._set_state(State.RETURN_HOME)
    
    def _do_return_home(self, slot: int):
        """Return to home position."""
        self._log(f"═══ RETURN HOME ═══")
        
        # First move to a safe intermediate position
        curr_x, curr_y, curr_z = self._get_current_gripper_pos()
        if curr_z < SAFE_Z - 0.05:
            self._move_to_position(curr_x, curr_y, SAFE_Z, "lift-to-safe")
        
        # Move to home using joints directly
        home_joints = [0.0, 0.0, 0.0]
        self._move_to_joints(home_joints, "home")
        
        # Reset state
        with self._lock:
            self._state = State.IDLE
            self._target_slot = None
        
        self._log("═══ COMPLETE - IDLE ═══")


def main(args=None):
    rclpy.init(args=args)
    node = VisualServoNode()
    executor = MultiThreadedExecutor(num_threads=4)
    executor.add_node(node)
    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        executor.shutdown()
        node.destroy_node()
        try:
            rclpy.shutdown()
        except:
            pass


if __name__ == "__main__":
    main()
