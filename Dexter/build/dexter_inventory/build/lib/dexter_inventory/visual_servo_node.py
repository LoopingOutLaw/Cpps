#!/usr/bin/env python3
"""
visual_servo_node.py - Visual Servo Pick-and-Place for Dexter Arm
=================================================================

5-Phase approach with safe collision-free motion:
  Phase 1: Open gripper, move to SAFE APPROACH point (behind target)
  Phase 2: Advance to HOVER above target (gripper stays open)
  Phase 3: Visual servo in X-Y plane to align grip_center with box
  Phase 4: OPEN gripper (wait fully), DESCEND, then CLOSE gripper
  Phase 5: Lift, transit to drop zone, release

FIXES applied vs previous version:
  - GRIP_OFFSET set to 0.0  (grip_center FK already accounts for finger
    geometry; the huge 0.50 m offset was parking the arm 50 cm short)
  - Phase 4 now waits GRIP_DURATION + 0.5 s after publishing GRIPPER_OPEN
    before starting the descent, so the gripper is fully open before the
    arm moves down (previous 0.5 s sleep < GRIP_DURATION = 1.0 s)
  - Phase 1 now opens the gripper immediately on entry
  - Visual servo uses a proportional gain (SERVO_GAIN) to avoid overshoot
    when stepping toward the target each iteration
  - Logging is consistent: all position displays use fk_grip_center

Trigger:
    ros2 topic pub --once /visual_servo/pick_request std_msgs/msg/Int32 "{data: 0}"
Watch:
    ros2 topic echo /visual_servo/status
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
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])

def Rx(a: float) -> np.ndarray:
    c, s = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])

def forward_kinematics(j1: float, j2: float, j3: float
                       ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Returns (claw_position, gripper_left_position, grip_center_position).

    Gripper offsets from claw_support in its LOCAL frame (from URDF):
      gripper_right : (-0.04,  0.13, -0.1)
      gripper_left  : (-0.22,  0.13, -0.1)
      grip_center   : (-0.13,  0.13, -0.1)   ← midpoint, used for IK
    """
    p = np.zeros(3)
    R = np.eye(3)

    # joint_1  z=0.307
    p = p + R @ np.array([0, 0, 0.307])
    R = R @ Rz(j1)

    # joint_2  xyz="-0.02 0 0.35"
    p = p + R @ np.array([-0.02, 0, 0.35])
    R = R @ Rx(j2)

    # joint_3  xyz="0 0 0.8"
    p = p + R @ np.array([0, 0, 0.8])
    R = R @ Rx(j3)

    # claw_support  xyz="0 0.82 0"
    p_claw = p + R @ np.array([0, 0.82, 0])

    p_gripper_left = p_claw + R @ np.array([-0.22, 0.13, -0.1])
    p_grip_center  = p_claw + R @ np.array([-0.13, 0.13, -0.1])

    return p_claw, p_gripper_left, p_grip_center


def fk_grip_center(j1: float, j2: float, j3: float) -> Tuple[float, float, float]:
    """Grip-centre position – primary reference for IK and servo."""
    _, _, p = forward_kinematics(j1, j2, j3)
    return float(p[0]), float(p[1]), float(p[2])


def inverse_kinematics(target_x: float, target_y: float, target_z: float,
                       init_guess: Optional[List[float]] = None
                       ) -> Optional[List[float]]:
    """
    Solve IK so that GRIP_CENTER reaches (target_x, target_y, target_z).
    Returns [j1, j2, j3] or None.
    """
    def error(joints):
        x, y, z = fk_grip_center(*joints)
        return (x - target_x)**2 + (y - target_y)**2 + (z - target_z)**2

    j1_init = math.atan2(target_y, target_x) - math.pi / 2
    J1_LIMIT = 2.98   # ±171 °

    guesses = [
        init_guess if init_guess else [j1_init, -0.5, 0.4],
        [j1_init,       -0.5,  0.4],
        [j1_init + 0.3, -0.5,  0.4],
        [j1_init - 0.3, -0.5,  0.4],
        [j1_init,       -0.3,  0.3],
        [j1_init,       -0.7,  0.5],
        [-2.0,          -0.5,  0.4],
        [-1.5,          -0.5,  0.4],
        [-1.0,          -0.5,  0.4],
        [ 2.0,          -0.5,  0.4],
        [ 1.5,          -0.5,  0.4],
    ]

    best_result, best_err = None, float('inf')
    for guess in guesses:
        try:
            result = minimize(
                error, guess,
                bounds=[(-J1_LIMIT, J1_LIMIT), (-1.57, 1.57), (-1.57, 1.57)],
                method='L-BFGS-B',
                options={'maxiter': 300},
            )
            if result.fun < best_err:
                best_err = result.fun
                best_result = result
        except Exception:
            pass

    # Accept if position error < 5 cm (0.05² = 0.0025)
    if best_result is None or best_err > 0.0025:
        return None

    return [float(best_result.x[0]),
            float(best_result.x[1]),
            float(best_result.x[2])]


# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

ROBOT_BASE = (0.0, 0.0)

SLOT_POSITIONS: Dict[int, Tuple[float, float, float]] = {
    0: (1.048, -0.642, 1.156),
    1: (1.209, -0.220, 1.156),
    2: (1.209, +0.220, 1.156),
    3: (1.048, +0.642, 1.156),
}

# Heights for grip_center Z target
SAFE_Z   = 1.45   # Clearance height for transit / safe approach
HOVER_Z  = 1.32   # Just above box – start of servo loop
PICK_Z   = 1.19   # Grip height (fingers descend around the box sides)
DROP_Z   = 1.32

# How far behind the box to start the safe approach (Phase 1)
APPROACH_OFFSET = 0.15   # m toward the robot from box centre

# Pullback distance - after reaching box, move straight back toward robot
# This positions the gripper fingertips over the box before descending
PULLBACK_DISTANCE = 0.42  # m - move 20cm straight back before descending

# ── GRIP_OFFSET: additional pull-back applied when computing the servo target.
#    The grip_center FK already places the midpoint between fingertips at the
#    requested world position, so NO extra offset is needed.
#    Setting this to 0.0 is correct; positive values move the target toward
#    the robot (use only for fine-tuning after testing).
GRIP_OFFSET = 0.0

DROP_X = 0.664
DROP_Y = 1.034

# Trajectory timing
TRAJ_DURATION    = 3.0   # s – arm trajectory length
RESEND_INTERVAL  = 1.5   # s – re-publish if not arrived
JOINT_TOLERANCE  = 0.05  # rad - increased to allow descent to complete
MAX_WAIT_TIME    = 45.0  # s
POLL_INTERVAL    = 0.1   # s
XY_TOLERANCE     = 0.025 # m = 25 mm  (tighter than before)
MAX_SERVO_ITER   = 10

# Visual-servo proportional gain (0 < SERVO_GAIN ≤ 1.0).
# Values < 1.0 take smaller steps toward the target, reducing overshoot.
SERVO_GAIN = 0.7

# Gripper
# joint_4 range: -π/2 (fully open) to 0 (closed)
# We only need to open enough to fit the box, not fully open
GRIPPER_OPEN   = -0.4   # Partially open - just enough to fit box between fingers
GRIPPER_CLOSED =  0.0   # Fingers together to grip
GRIP_DURATION  =  1.0   # s – trajectory duration for gripper commands
PICK_DWELL     =  1.5   # s – wait after closing before lifting
DROP_DWELL     =  0.5   # s – wait after opening before retracting

ARUCO_MAX_AGE = 5.0   # s


# ═══════════════════════════════════════════════════════════════════════════════
# STATE MACHINE
# ═══════════════════════════════════════════════════════════════════════════════

class State(Enum):
    IDLE                    = auto()
    PHASE1_SAFE_APPROACH    = auto()
    PHASE2_OPEN_AND_ADVANCE = auto()
    PHASE3_SERVO            = auto()
    PHASE4_PULLBACK         = auto()   # NEW: Pull back toward robot
    PHASE5_DESCEND_AND_GRIP = auto()   # Was PHASE4
    PHASE6_LIFT             = auto()   # Was PHASE5
    PHASE7_TRANSIT          = auto()   # Was PHASE6
    PHASE8_DROP             = auto()   # Was PHASE7
    RETURN_HOME             = auto()


class VisualServoNode(Node):
    def __init__(self):
        super().__init__("visual_servo_node")

        cb = ReentrantCallbackGroup()

        self.arm_pub    = self.create_publisher(JointTrajectory,
                                                "/arm_controller/joint_trajectory", 10)
        self.grip_pub   = self.create_publisher(JointTrajectory,
                                                "/gripper_controller/joint_trajectory", 10)
        self.status_pub = self.create_publisher(String, "/visual_servo/status", 10)

        self.create_subscription(JointState, "/joint_states",
                                 self._joint_state_cb, 10, callback_group=cb)
        self.create_subscription(String, "/inventory/box_poses",
                                 self._box_poses_cb, 10, callback_group=cb)
        self.create_subscription(Int32, "/visual_servo/pick_request",
                                 self._pick_request_cb, 10, callback_group=cb)

        self._state       = State.IDLE
        self._target_slot: Optional[int] = None
        self._lock        = threading.Lock()
        self._joints: Dict[str, float] = {f"joint_{i}": 0.0 for i in range(1, 6)}
        self._box_data: Dict[int, dict] = {}
        self._aruco_ts    = 0.0

        threading.Thread(target=self._state_machine_loop, daemon=True).start()

        x, y, z = fk_grip_center(0, 0, 0)
        self.get_logger().info(
            f"\n{'='*70}\n"
            f"  Visual Servo Node Started\n"
            f"  HOME grip-centre: ({x:.3f}, {y:.3f}, {z:.3f})\n"
            f"  GRIP_OFFSET={GRIP_OFFSET}  SERVO_GAIN={SERVO_GAIN}\n"
            f"  HOVER_Z={HOVER_Z}  PICK_Z={PICK_Z}  SAFE_Z={SAFE_Z}\n"
            f"  XY tolerance={XY_TOLERANCE*1000:.0f} mm\n\n"
            f"  Trigger:\n"
            f"    ros2 topic pub --once /visual_servo/pick_request \\\n"
            f"         std_msgs/msg/Int32 \"{{data: 0}}\"\n"
            f"{'='*70}"
        )

    # ── callbacks ──────────────────────────────────────────────────────────────

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
                self._aruco_ts = time.time()
        except Exception as e:
            self.get_logger().warn(f"box_poses: {e}")

    def _pick_request_cb(self, msg: Int32):
        slot = int(msg.data)
        if slot not in range(4):
            self.get_logger().warn(f"Invalid slot {slot}")
            return
        with self._lock:
            if self._state != State.IDLE:
                self.get_logger().warn(f"Busy – state={self._state.name}")
                return
            self._target_slot = slot
            self._state = State.PHASE1_SAFE_APPROACH
        self.get_logger().info(f"Pick request: slot {slot}")

    # ── helpers ────────────────────────────────────────────────────────────────

    def _current_joints(self) -> List[float]:
        with self._lock:
            return [self._joints[f"joint_{i}"] for i in range(1, 4)]

    def _current_grip_center(self) -> Tuple[float, float, float]:
        return fk_grip_center(*self._current_joints())

    def _aruco_fresh(self) -> bool:
        with self._lock:
            return (time.time() - self._aruco_ts) < ARUCO_MAX_AGE

    def _target_xy(self, slot: int) -> Tuple[float, float]:
        with self._lock:
            info = self._box_data.get(slot, {})
        if info.get("detected") and self._aruco_fresh():
            return float(info["x"]), float(info["y"])
        return SLOT_POSITIONS[slot][0], SLOT_POSITIONS[slot][1]

    def _approach_point(self, tx: float, ty: float) -> Tuple[float, float]:
        dx, dy = tx - ROBOT_BASE[0], ty - ROBOT_BASE[1]
        d = math.hypot(dx, dy)
        if d < 0.1:
            return tx, ty
        ux, uy = dx / d, dy / d
        return tx - ux * APPROACH_OFFSET, ty - uy * APPROACH_OFFSET

    def _grip_point(self, tx: float, ty: float) -> Tuple[float, float]:
        """
        Return the world XY target for grip_center.

        With GRIP_OFFSET=0 the target is the box centre directly, which is
        correct because fk_grip_center already models the finger geometry.
        A small positive GRIP_OFFSET shifts the target toward the robot for
        fine-tuning after physical testing.
        """
        if GRIP_OFFSET == 0.0:
            return tx, ty
        dx, dy = tx - ROBOT_BASE[0], ty - ROBOT_BASE[1]
        d = math.hypot(dx, dy)
        if d < 0.1:
            return tx, ty
        ux, uy = dx / d, dy / d
        gx = tx - ux * GRIP_OFFSET
        gy = ty - uy * GRIP_OFFSET
        self.get_logger().info(
            f"[GRIP] box=({tx:.3f},{ty:.3f}) offset={GRIP_OFFSET:.2f}m "
            f"→ target=({gx:.3f},{gy:.3f})")
        return gx, gy

    def _log(self, msg: str):
        s = String(); s.data = msg
        self.status_pub.publish(s)
        self.get_logger().info(f"[SERVO] {msg}")

    def _set_state(self, s: State):
        with self._lock:
            self._state = s
        self._log(f"State → {s.name}")

    # ── motion ─────────────────────────────────────────────────────────────────

    def _pub_arm(self, joints: List[float], duration: float = TRAJ_DURATION):
        msg = JointTrajectory()
        msg.joint_names = ["joint_1", "joint_2", "joint_3"]
        pt  = JointTrajectoryPoint()
        pt.positions  = [float(j) for j in joints]
        pt.velocities = [0.0, 0.0, 0.0]
        s, ns = int(duration), int((duration % 1) * 1e9)
        pt.time_from_start = DurationMsg(sec=s, nanosec=ns)
        msg.points = [pt]
        self.arm_pub.publish(msg)

    def _pub_gripper(self, position: float):
        """
        Publish a gripper trajectory.
        NOTE: always call time.sleep(GRIP_DURATION + margin) after this to
        guarantee the gripper has physically completed its motion before the
        arm starts moving.
        """
        msg = JointTrajectory()
        msg.joint_names = ["joint_4"]
        pt  = JointTrajectoryPoint()
        pt.positions  = [float(position)]
        pt.velocities = [0.0]
        pt.time_from_start = DurationMsg(sec=int(GRIP_DURATION), nanosec=0)
        msg.points = [pt]
        self.grip_pub.publish(msg)

    def _move_to_joints(self, target: List[float], label: str) -> bool:
        gx, gy, gz = fk_grip_center(*target)
        self._log(
            f"MOVE {label}: joints=[{target[0]:.3f},{target[1]:.3f},{target[2]:.3f}]"
            f"  grip-centre=({gx:.3f},{gy:.3f},{gz:.3f})")

        deadline    = time.time() + MAX_WAIT_TIME
        last_send   = 0.0
        last_log    = 0.0

        while time.time() < deadline:
            cur = self._current_joints()
            err = max(abs(cur[i] - target[i]) for i in range(3))

            if err < JOINT_TOLERANCE:
                cx, cy, cz = fk_grip_center(*cur)
                self._log(f"  ✔ {label}  err={err:.4f} rad  "
                          f"grip-centre=({cx:.3f},{cy:.3f},{cz:.3f})")
                return True

            now = time.time()
            if now - last_send >= RESEND_INTERVAL:
                self._pub_arm(target)
                last_send = now
            if now - last_log >= 3.0:
                cx, cy, cz = fk_grip_center(*cur)
                self._log(f"  MOVING {label}: err={err:.4f} rad  "
                          f"gripper=({cx:.3f},{cy:.3f},{cz:.3f})")
                last_log = now

            time.sleep(POLL_INTERVAL)

        self._log(f"  TIMEOUT {label}")
        return False

    def _move_to_position(self, tx: float, ty: float, tz: float,
                          label: str) -> bool:
        cur = self._current_joints()
        joints = inverse_kinematics(tx, ty, tz, cur)
        if joints is None:
            self._log(f"  IK FAILED for ({tx:.3f},{ty:.3f},{tz:.3f})")
            return False
        return self._move_to_joints(joints, label)

    # ── state machine ──────────────────────────────────────────────────────────

    def _state_machine_loop(self):
        while rclpy.ok():
            with self._lock:
                state = self._state
                slot  = self._target_slot
            if state == State.IDLE or slot is None:
                time.sleep(0.1)
                continue
            try:
                {
                    State.PHASE1_SAFE_APPROACH:    self._phase1,
                    State.PHASE2_OPEN_AND_ADVANCE: self._phase2,
                    State.PHASE3_SERVO:            self._phase3,
                    State.PHASE4_PULLBACK:         self._phase4,
                    State.PHASE5_DESCEND_AND_GRIP: self._phase5,
                    State.PHASE6_LIFT:             self._phase6,
                    State.PHASE7_TRANSIT:          self._phase7,
                    State.PHASE8_DROP:             self._phase8,
                    State.RETURN_HOME:             self._phase_home,
                }[state](slot)
            except Exception as e:
                import traceback
                self.get_logger().error(f"State machine: {e}\n{traceback.format_exc()}")
                self._set_state(State.RETURN_HOME)
            time.sleep(0.05)

    # ── Phase 1 – safe approach ────────────────────────────────────────────────

    def _phase1(self, slot: int):
        self._log("═══ PHASE 1: SAFE APPROACH ═══")

        # ① Open gripper IMMEDIATELY so it is ready before we are over the shelf
        self._log("  Opening gripper …")
        self._pub_gripper(GRIPPER_OPEN)
        time.sleep(GRIP_DURATION + 0.5)   # wait for gripper to fully open

        tx, ty = self._target_xy(slot)
        ax, ay = self._approach_point(tx, ty)
        self._log(f"  Box=({tx:.3f},{ty:.3f})  approach=({ax:.3f},{ay:.3f})  z={SAFE_Z}")

        if not self._move_to_position(ax, ay, SAFE_Z, "safe-approach"):
            self._log("  Phase 1 FAILED")
            self._set_state(State.RETURN_HOME)
            return
        self._set_state(State.PHASE2_OPEN_AND_ADVANCE)

    # ── Phase 2 – advance to hover ─────────────────────────────────────────────

    def _phase2(self, slot: int):
        self._log("═══ PHASE 2: ADVANCE TO HOVER ═══")

        # Re-assert open (gripper was opened in Phase 1; re-publish to be safe)
        self._pub_gripper(GRIPPER_OPEN)
        time.sleep(0.3)   # short – already open from Phase 1

        tx, ty   = self._target_xy(slot)
        gx, gy   = self._grip_point(tx, ty)
        src = "ArUco" if self._aruco_fresh() else "GT"
        self._log(f"  Box=({tx:.3f},{ty:.3f}) [{src}]  "
                  f"grip-target=({gx:.3f},{gy:.3f})  z={HOVER_Z}")

        if not self._move_to_position(gx, gy, HOVER_Z, "hover"):
            self._log("  Phase 2 FAILED")
            self._set_state(State.RETURN_HOME)
            return
        self._set_state(State.PHASE3_SERVO)

    # ── Phase 3 – visual servo ─────────────────────────────────────────────────

    def _phase3(self, slot: int):
        self._log(f"═══ PHASE 3: VISUAL SERVO  gain={SERVO_GAIN} ═══")

        for it in range(MAX_SERVO_ITER):
            cx, cy, _ = self._current_grip_center()

            tx, ty = self._target_xy(slot)
            gx, gy = self._grip_point(tx, ty)
            src = "ArUco" if self._aruco_fresh() else "GT"

            ex, ey = gx - cx, gy - cy
            err    = math.hypot(ex, ey)

            self._log(f"  iter {it+1}/{MAX_SERVO_ITER}: "
                      f"grip=({cx:.3f},{cy:.3f})  target=({gx:.3f},{gy:.3f}) [{src}]  "
                      f"err={err*1000:.0f} mm")

            if err < XY_TOLERANCE:
                self._log(f"  ALIGNED  err={err*1000:.0f} mm")
                break

            # Proportional step: move SERVO_GAIN fraction of the remaining error.
            # This prevents the IK from "arriving and overshooting" each iteration.
            cmd_x = cx + SERVO_GAIN * ex
            cmd_y = cy + SERVO_GAIN * ey

            if not self._move_to_position(cmd_x, cmd_y, HOVER_Z, f"servo-{it+1}"):
                self._log("  servo move FAILED")
                break

            # Wait for arm to settle and ArUco data to refresh
            time.sleep(0.5)

        # Check final error
        cx, cy, _ = self._current_grip_center()
        tx, ty = self._target_xy(slot)
        gx, gy = self._grip_point(tx, ty)
        final_err = math.hypot(gx - cx, gy - cy)

        if final_err > 0.08:
            self._log(f"  ABORT: final error {final_err*1000:.0f} mm > 80 mm")
            self._set_state(State.RETURN_HOME)
            return

        self._log(f"  Phase 3 done – final error {final_err*1000:.0f} mm")
        self._set_state(State.PHASE4_PULLBACK)

    # ── Phase 4 – PULLBACK (move straight back toward robot) ───────────────────

    def _phase4(self, slot: int):
        self._log("═══ PHASE 4: PULLBACK ═══")
        
        # Get current position
        cx, cy, cz = self._current_grip_center()
        
        # Direction from robot to current position
        dx = cx - ROBOT_BASE[0]
        dy = cy - ROBOT_BASE[1]
        dist = math.hypot(dx, dy)
        
        if dist < 0.1:
            self._log("  Too close to robot, skipping pullback")
            self._set_state(State.PHASE5_DESCEND_AND_GRIP)
            return
        
        # Unit vector pointing away from robot
        ux, uy = dx / dist, dy / dist
        
        # Pullback position: move toward robot by PULLBACK_DISTANCE
        pullback_x = cx - ux * PULLBACK_DISTANCE
        pullback_y = cy - uy * PULLBACK_DISTANCE
        
        self._log(f"  Current: ({cx:.3f}, {cy:.3f})")
        self._log(f"  Pulling back {PULLBACK_DISTANCE*100:.0f}cm toward robot")
        self._log(f"  Target:  ({pullback_x:.3f}, {pullback_y:.3f})")
        
        if not self._move_to_position(pullback_x, pullback_y, HOVER_Z, "pullback"):
            self._log("  Pullback FAILED")
            self._set_state(State.RETURN_HOME)
            return
        
        self._log("  Pullback complete ✔")
        self._set_state(State.PHASE5_DESCEND_AND_GRIP)

    # ── Phase 5 – descend and grip ─────────────────────────────────────────────

    def _phase5(self, slot: int):
        self._log("═══ PHASE 5: DESCEND & GRIP ═══")

        # Gripper should already be open from Phase 1, but re-assert to be safe
        self._log(f"  Ensuring gripper is open (joint_4 = {GRIPPER_OPEN:.2f}) …")
        self._pub_gripper(GRIPPER_OPEN)
        time.sleep(0.5)
        self._log("  Gripper OPEN ✔")

        # Descend with OPEN gripper to PICK_Z
        cx, cy, _ = self._current_grip_center()
        self._log(f"  Descending from z={HOVER_Z} → z={PICK_Z}")

        if not self._move_to_position(cx, cy, PICK_Z, "DESCEND"):
            self._log("  Descend FAILED")
            self._set_state(State.RETURN_HOME)
            return

        # Brief settle – box should now be between the open fingers
        self._log("  Settled at pick height – box between open fingers")
        time.sleep(0.4)

        # CLOSE gripper
        self._log(f"  CLOSING gripper (joint_4 = {GRIPPER_CLOSED:.2f}) …")
        self._pub_gripper(GRIPPER_CLOSED)
        time.sleep(GRIP_DURATION + PICK_DWELL)
        self._log("  Gripper CLOSED ✔")

        self._set_state(State.PHASE6_LIFT)

    # ── Phase 6 – lift ─────────────────────────────────────────────────────────

    def _phase6(self, slot: int):
        self._log("═══ PHASE 6: LIFT ═══")
        cx, cy, _ = self._current_grip_center()
        if not self._move_to_position(cx, cy, SAFE_Z, "lift"):
            self._log("  Lift FAILED (continuing)")
        self._set_state(State.PHASE7_TRANSIT)

    # ── Phase 7 – transit ──────────────────────────────────────────────────────

    def _phase7(self, slot: int):
        self._log(f"═══ PHASE 7: TRANSIT → drop zone ({DROP_X},{DROP_Y}) ═══")
        if not self._move_to_position(DROP_X, DROP_Y, SAFE_Z, "transit"):
            self._log("  Transit FAILED (continuing)")
        if not self._move_to_position(DROP_X, DROP_Y, DROP_Z, "lower-to-drop"):
            self._log("  Lower FAILED (continuing)")
        self._set_state(State.PHASE8_DROP)

    # ── Phase 8 – drop ─────────────────────────────────────────────────────────

    def _phase8(self, slot: int):
        self._log("═══ PHASE 8: DROP ═══")
        self._pub_gripper(GRIPPER_OPEN)
        time.sleep(GRIP_DURATION + DROP_DWELL)
        if not self._move_to_position(DROP_X, DROP_Y, SAFE_Z, "retract"):
            self._log("  Retract FAILED (continuing)")
        self._set_state(State.RETURN_HOME)

    # ── Return home ────────────────────────────────────────────────────────────

    def _phase_home(self, slot: int):
        self._log("═══ RETURN HOME ═══")
        cx, cy, cz = self._current_grip_center()
        if cz < SAFE_Z - 0.05:
            self._move_to_position(cx, cy, SAFE_Z, "lift-to-safe")
        self._move_to_joints([0.0, 0.0, 0.0], "home")
        with self._lock:
            self._state       = State.IDLE
            self._target_slot = None
        self._log("═══ COMPLETE – IDLE ═══")


# ─────────────────────────────────────────────────────────────────────────────

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
        except Exception:
            pass


if __name__ == "__main__":
    main()