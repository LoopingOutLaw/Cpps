#!/usr/bin/env python3
"""
visual_servo_node.py - Visual Servo Pick-and-Place for Dexter Arm
=================================================================

3-Phase approach:
  Phase 1: Move to HOVER height above boxes (z ≈ 1.25m)
  Phase 2: Visual servo in X-Y plane to align with target box
  Phase 3: Descend to PICK height (z ≈ 1.16m), grip, lift, drop

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

def forward_kinematics(j1: float, j2: float, j3: float) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute forward kinematics.
    Returns (claw_position, gripper_left_position) in world frame.
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
    p_gripper = p_claw + R @ np.array([-0.22, 0.13, -0.1])
    
    return p_claw, p_gripper

def fk_gripper(j1: float, j2: float, j3: float) -> Tuple[float, float, float]:
    """Get gripper_left position."""
    _, p = forward_kinematics(j1, j2, j3)
    return float(p[0]), float(p[1]), float(p[2])

def inverse_kinematics(target_x: float, target_y: float, target_z: float,
                       init_guess: Optional[List[float]] = None) -> Optional[List[float]]:
    """
    Solve inverse kinematics for gripper_left to reach target position.
    Returns [j1, j2, j3] or None if no solution found.
    
    Joint limits: j1: ±171° (±2.98 rad), j2/j3: ±90° (±1.57 rad)
    """
    import math
    
    def error(joints):
        j1, j2, j3 = joints
        x, y, z = fk_gripper(j1, j2, j3)
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

# Target positions for boxes (ground truth from SDF)
SLOT_POSITIONS: Dict[int, Tuple[float, float, float]] = {
    0: (1.048, -0.642, 1.156),
    1: (1.209, -0.220, 1.156),
    2: (1.209, +0.220, 1.156),
    3: (1.048, +0.642, 1.156),
}

# Heights
HOVER_Z = 1.25    # Hover height (gripper z)
PICK_Z = 1.16     # Pick height (gripper z, at box level)
DROP_Z = 1.25     # Drop zone height

# Drop zone position (to the side)
DROP_X = 0.5
DROP_Y = 0.9

# Timing
TRAJ_DURATION = 4.0      # Trajectory execution time
RESEND_INTERVAL = 2.0    # Resend trajectory every N seconds
JOINT_TOLERANCE = 0.03   # Joint position tolerance (rad)
MAX_WAIT_TIME = 60.0     # Maximum wait for motion
POLL_INTERVAL = 0.1      # Polling interval
XY_TOLERANCE = 0.03      # XY position tolerance (m) = 30mm
MAX_SERVO_ITERATIONS = 10

# Gripper
GRIPPER_OPEN = 0.0
GRIPPER_CLOSED = -0.7
GRIP_DURATION = 1.5
PICK_DWELL = 2.0
DROP_DWELL = 1.0

# ArUco
ARUCO_MAX_AGE = 5.0  # Maximum age of ArUco data (seconds)


# ═══════════════════════════════════════════════════════════════════════════════
# STATE MACHINE
# ═══════════════════════════════════════════════════════════════════════════════

class State(Enum):
    IDLE = auto()
    PHASE1_HOVER = auto()
    PHASE2_SERVO = auto()
    PHASE3_DESCEND = auto()
    GRIP = auto()
    LIFT = auto()
    TRANSIT = auto()
    DROP = auto()
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
            f"  Visual Servo Node Started\n"
            f"  HOME position: gripper at ({x:.3f}, {y:.3f}, {z:.3f})\n"
            f"  HOVER height: {HOVER_Z}m, PICK height: {PICK_Z}m\n"
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
            self._state = State.PHASE1_HOVER
        
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
        """Get current gripper position from FK."""
        joints = self._get_current_joints()
        return fk_gripper(*joints)
    
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
                if state == State.PHASE1_HOVER:
                    self._do_phase1_hover(slot)
                elif state == State.PHASE2_SERVO:
                    self._do_phase2_servo(slot)
                elif state == State.PHASE3_DESCEND:
                    self._do_phase3_descend(slot)
                elif state == State.GRIP:
                    self._do_grip(slot)
                elif state == State.LIFT:
                    self._do_lift(slot)
                elif state == State.TRANSIT:
                    self._do_transit(slot)
                elif state == State.DROP:
                    self._do_drop(slot)
                elif state == State.RETURN_HOME:
                    self._do_return_home(slot)
            except Exception as e:
                import traceback
                self.get_logger().error(f"State machine error: {e}\n{traceback.format_exc()}")
                self._set_state(State.RETURN_HOME)
            
            time.sleep(0.05)
    
    def _do_phase1_hover(self, slot: int):
        """Phase 1: Move to hover height above the target area."""
        self._log(f"═══ PHASE 1: HOVER ═══")
        self._log(f"  Target: slot {slot}, hover z={HOVER_Z}m")
        
        # Open gripper first
        self._publish_gripper(GRIPPER_OPEN)
        time.sleep(GRIP_DURATION + 0.5)
        
        # Get target XY from ArUco or ground truth
        target_x, target_y = self._get_target_xy(slot)
        self._log(f"  Target XY from {'ArUco' if self._aruco_is_fresh() else 'ground truth'}: "
                  f"({target_x:.3f}, {target_y:.3f})")
        
        # Move to hover position
        if not self._move_to_position(target_x, target_y, HOVER_Z, "phase1-hover"):
            self._log("  Phase 1 FAILED - going home")
            self._set_state(State.RETURN_HOME)
            return
        
        self._set_state(State.PHASE2_SERVO)
    
    def _do_phase2_servo(self, slot: int):
        """Phase 2: Visual servo to align precisely with target."""
        self._log(f"═══ PHASE 2: VISUAL SERVO ═══")
        
        for iteration in range(MAX_SERVO_ITERATIONS):
            # Get current gripper position
            curr_x, curr_y, curr_z = self._get_current_gripper_pos()
            
            # Get target from ArUco
            target_x, target_y = self._get_target_xy(slot)
            source = "ArUco" if self._aruco_is_fresh() else "GT"
            
            # Compute error
            err_x = target_x - curr_x
            err_y = target_y - curr_y
            err_dist = math.hypot(err_x, err_y)
            
            self._log(f"  Iter {iteration+1}: pos=({curr_x:.3f}, {curr_y:.3f}), "
                      f"target=({target_x:.3f}, {target_y:.3f}) [{source}], "
                      f"err={err_dist*1000:.0f}mm")
            
            # Check if aligned
            if err_dist < XY_TOLERANCE:
                self._log(f"  ALIGNED! err={err_dist*1000:.0f}mm < {XY_TOLERANCE*1000:.0f}mm")
                break
            
            # Move toward target (at hover height)
            if not self._move_to_position(target_x, target_y, HOVER_Z, f"servo-{iteration+1}"):
                self._log("  Servo move FAILED")
                break
            
            # Small delay to let ArUco update
            time.sleep(0.5)
        
        # Final check
        curr_x, curr_y, curr_z = self._get_current_gripper_pos()
        target_x, target_y = self._get_target_xy(slot)
        final_err = math.hypot(target_x - curr_x, target_y - curr_y)
        
        if final_err > 0.08:  # 8cm max acceptable error
            self._log(f"  ABORT: final error {final_err*1000:.0f}mm too large")
            self._set_state(State.RETURN_HOME)
            return
        
        self._log(f"  Phase 2 complete: final error = {final_err*1000:.0f}mm")
        self._set_state(State.PHASE3_DESCEND)
    
    def _do_phase3_descend(self, slot: int):
        """Phase 3: Descend to pick height."""
        self._log(f"═══ PHASE 3: DESCEND ═══")
        
        # Get current XY (keep it, just lower Z)
        curr_x, curr_y, _ = self._get_current_gripper_pos()
        
        self._log(f"  Descending from z={HOVER_Z}m to z={PICK_Z}m")
        self._log(f"  Keeping XY at ({curr_x:.3f}, {curr_y:.3f})")
        
        if not self._move_to_position(curr_x, curr_y, PICK_Z, "descend"):
            self._log("  Descend FAILED")
            self._set_state(State.RETURN_HOME)
            return
        
        self._set_state(State.GRIP)
    
    def _do_grip(self, slot: int):
        """Close gripper to grab item."""
        self._log(f"═══ GRIP ═══")
        
        self._publish_gripper(GRIPPER_CLOSED)
        time.sleep(GRIP_DURATION + PICK_DWELL)
        
        self._set_state(State.LIFT)
    
    def _do_lift(self, slot: int):
        """Lift item to hover height."""
        self._log(f"═══ LIFT ═══")
        
        curr_x, curr_y, _ = self._get_current_gripper_pos()
        
        if not self._move_to_position(curr_x, curr_y, HOVER_Z, "lift"):
            self._log("  Lift FAILED")
        
        self._set_state(State.TRANSIT)
    
    def _do_transit(self, slot: int):
        """Move to drop zone."""
        self._log(f"═══ TRANSIT TO DROP ZONE ═══")
        
        # Move to drop zone at hover height
        if not self._move_to_position(DROP_X, DROP_Y, HOVER_Z, "transit-hover"):
            self._log("  Transit hover FAILED")
        
        # Lower to drop height
        if not self._move_to_position(DROP_X, DROP_Y, DROP_Z, "transit-lower"):
            self._log("  Transit lower FAILED")
        
        self._set_state(State.DROP)
    
    def _do_drop(self, slot: int):
        """Release item."""
        self._log(f"═══ DROP ═══")
        
        self._publish_gripper(GRIPPER_OPEN)
        time.sleep(GRIP_DURATION + DROP_DWELL)
        
        # Lift away
        if not self._move_to_position(DROP_X, DROP_Y, HOVER_Z, "drop-retract"):
            self._log("  Drop retract FAILED")
        
        self._set_state(State.RETURN_HOME)
    
    def _do_return_home(self, slot: int):
        """Return to home position."""
        self._log(f"═══ RETURN HOME ═══")
        
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
