#!/usr/bin/env python3
"""
visual_servo_node.py  –  ArUco Direct-IK Visual Servo for Dexter Arm
=====================================================================
Key design decisions
--------------------
1. MOVE_HOVER    – compute IK, send arm to hover height, wait on joint states
2. SERVO_VERIFY  – re-read ArUco several times to refine (x,y) while arm is
                   still at hover (markers visible).  CACHE final target here.
3. DESCEND       – use CACHED target only (no ArUco re-read).
                   Arm blocks the camera during descent, ArUco disappears —
                   that is expected and fine because IK is analytically exact.
4. Descent is slow (5 s) so joint trajectory controller tracks smoothly.

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

import rclpy
from builtin_interfaces.msg import Duration as DurationMsg
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node

from sensor_msgs.msg import JointState
from std_msgs.msg import String, Int32
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint

# ── Arm geometry ──────────────────────────────────────────────────────────────
L0 = 0.657   # m
L1 = 0.800   # m
L2 = 0.820   # m

# ── Heights ───────────────────────────────────────────────────────────────────
HOVER_Z  = 1.40    # m  hover height (raised a bit so markers stay visible longer)
PICK_Z   = 1.216   # m  box top

# ── Tolerances ────────────────────────────────────────────────────────────────
XY_TOL      = 0.020  # m  xy alignment
JOINT_TOL   = 0.05   # rad

# ── Timing ────────────────────────────────────────────────────────────────────
MOVE_TIMEOUT  = 15.0   # s
DESCEND_DUR   = 6.0    # s  — slow, smooth descent so controller tracks it
HOVER_DUR     = 4.0    # s
HOME_DUR      = 5.0    # s
FAST_DUR      = 3.0    # s
PICK_DWELL    = 2.5    # s
DROP_DWELL    = 1.0    # s
GRIPPER_DUR   = 1.2    # s
ARUCO_MAX_AGE = 4.0    # s
SERVO_ITERS   = 6      # number of refinement iterations at hover

# ── FK table ──────────────────────────────────────────────────────────────────
SLOT_GT: Dict[int, Tuple[float, float]] = {
    0: (1.048, -0.642), 1: (1.209, -0.220),
    2: (1.209, +0.220), 3: (1.048, +0.642),
}
HOME       = [0.00,    0.00,    0.00   ]
DROP_HOVER = [1.0122, -0.5502, -1.0000]
DROP_PLACE = [1.0122, -0.5502, -1.1711]


class State(Enum):
    IDLE         = auto()
    MOVE_HOVER   = auto()
    SERVO_VERIFY = auto()
    DESCEND      = auto()
    GRIP         = auto()
    LIFT         = auto()
    TRANSIT      = auto()
    DROP         = auto()
    GOING_HOME   = auto()


# ── IK / FK ───────────────────────────────────────────────────────────────────

def ik(x: float, y: float, z: float) -> Optional[List[float]]:
    """Analytical IK.  Returns [j1,j2,j3] or None."""
    j1 = math.atan2(y, x)
    r  = math.hypot(x, y)
    A  = -r
    B  = z - L0
    c3 = (A*A + B*B - L1*L1 - L2*L2) / (2.0 * L1 * L2)
    if abs(c3) > 1.0:
        return None
    s3 = -math.sqrt(max(0.0, 1.0 - c3*c3))
    j3 = math.atan2(s3, c3)
    j2 = math.atan2(A, B) - math.atan2(L2*s3, L1 + L2*c3)
    if not (-math.pi/2 <= j1 <= math.pi/2): return None
    if not (-math.pi/2 <= j2 <= 0.0):       return None
    if not (-math.pi   <= j3 <= 0.0):       return None
    return [round(j1,5), round(j2,5), round(j3,5)]


def fk(j1: float, j2: float, j3: float) -> Tuple[float,float,float]:
    r = -(L1*math.sin(j2) + L2*math.sin(j2+j3))
    x =  r*math.cos(j1)
    y =  r*math.sin(j1)
    z =  L0 + L1*math.cos(j2) + L2*math.cos(j2+j3)
    return x, y, z


# ── Node ──────────────────────────────────────────────────────────────────────

class VisualServoNode(Node):

    def __init__(self):
        super().__init__("visual_servo_node")
        cb = ReentrantCallbackGroup()

        self.arm_pub    = self.create_publisher(
            JointTrajectory, "/arm_controller/joint_trajectory", 10)
        self.grip_pub   = self.create_publisher(
            JointTrajectory, "/gripper_controller/joint_trajectory", 10)
        self.status_pub = self.create_publisher(
            String, "/visual_servo/status", 10)

        self.create_subscription(JointState, "/joint_states",
                                 self._js_cb,   10, callback_group=cb)
        self.create_subscription(String, "/inventory/box_poses",
                                 self._boxes_cb, 10, callback_group=cb)
        self.create_subscription(String, "/inventory/gripper_pose",
                                 self._grip_pose_cb, 10, callback_group=cb)
        self.create_subscription(Int32, "/visual_servo/pick_request",
                                 self._pick_req_cb, 10, callback_group=cb)

        self._state       = State.IDLE
        self._target_slot: Optional[int]  = None
        # ── CACHED target locked at end of SERVO_VERIFY ──────────────────
        # Once confirmed, descent uses this — not live ArUco.
        # This survives the arm blocking the camera during descent.
        self._locked_xy: Optional[Tuple[float,float]] = None
        self._locked_z:  float = PICK_Z

        self._lock = threading.Lock()
        self._j: Dict[str,float] = {f"joint_{i}": 0.0 for i in range(1,6)}
        self._box_data:  Dict[int,dict] = {}
        self._grip_data: dict = {"detected": False}
        self._aruco_ts:  float = 0.0

        threading.Thread(target=self._sm_loop, daemon=True).start()

        self.get_logger().info(
            "\n" + "="*60 +
            "\n  Visual Servo Node — direct IK, cached descent" +
            "\n  Trigger: ros2 topic pub --once /visual_servo/pick_request" +
            "\n           std_msgs/msg/Int32 \"{data: 0}\"" +
            "\n  Watch:   ros2 topic echo /visual_servo/status" +
            "\n" + "="*60)

    # ── Callbacks ──────────────────────────────────────────────────────────────

    def _js_cb(self, msg: JointState):
        with self._lock:
            for n,p in zip(msg.name, msg.position):
                if n in self._j: self._j[n] = float(p)

    def _boxes_cb(self, msg: String):
        try:
            data = json.loads(msg.data)
            with self._lock:
                for k,v in data.items(): self._box_data[int(k)] = v
                self._aruco_ts = time.time()
        except Exception as e:
            self.get_logger().warn(f"boxes_cb: {e}")

    def _grip_pose_cb(self, msg: String):
        try:
            with self._lock: self._grip_data = json.loads(msg.data)
        except Exception: pass

    def _pick_req_cb(self, msg: Int32):
        slot = int(msg.data)
        if slot not in range(4):
            self.get_logger().warn(f"Invalid slot {slot}"); return
        with self._lock:
            if self._state != State.IDLE:
                self.get_logger().warn(f"Busy ({self._state.name}) — ignoring"); return
            self._target_slot = slot
            self._locked_xy   = None
            self._state       = State.MOVE_HOVER
        self.get_logger().info(f"Pick request: slot {slot}")

    # ── Helpers ────────────────────────────────────────────────────────────────

    def _aruco_fresh(self) -> bool:
        with self._lock: return (time.time() - self._aruco_ts) < ARUCO_MAX_AGE

    def _best_xy(self, slot: int) -> Tuple[float,float]:
        """ArUco-measured if fresh, else FK ground-truth."""
        with self._lock:
            info = self._box_data.get(slot,{})
        if info.get("detected") and self._aruco_fresh():
            return float(info["x"]), float(info["y"])
        return SLOT_GT[slot]

    def _arm_j(self) -> List[float]:
        with self._lock:
            return [self._j["joint_1"],self._j["joint_2"],self._j["joint_3"]]

    def _arm_err(self, target: List[float]) -> float:
        c = self._arm_j()
        return max(abs(c[i]-target[i]) for i in range(3))

    def _j4(self) -> float:
        with self._lock: return self._j["joint_4"]

    # ── Publishers ─────────────────────────────────────────────────────────────

    def _send_arm(self, joints: List[float], dur: float):
        msg = JointTrajectory()
        msg.joint_names = ["joint_1","joint_2","joint_3"]
        pt  = JointTrajectoryPoint()
        pt.positions  = [float(j) for j in joints]
        pt.velocities = [0.0,0.0,0.0]
        s = int(dur); ns = int((dur-s)*1e9)
        pt.time_from_start = DurationMsg(sec=s, nanosec=ns)
        msg.points = [pt]
        self.arm_pub.publish(msg)

    def _send_grip(self, j4: float, dur: float):
        msg = JointTrajectory()
        msg.joint_names = ["joint_4"]
        pt  = JointTrajectoryPoint()
        pt.positions  = [float(j4)]
        pt.velocities = [0.0]
        s = int(dur); ns = int((dur-s)*1e9)
        pt.time_from_start = DurationMsg(sec=s, nanosec=ns)
        msg.points = [pt]
        self.grip_pub.publish(msg)

    def _wait_arm(self, joints: List[float], label: str,
                  timeout: float = MOVE_TIMEOUT) -> bool:
        deadline = time.time() + timeout
        while time.time() < deadline:
            err = self._arm_err(joints)
            if err < JOINT_TOL:
                self._log(f"  ✔ {label}  err={err:.3f}rad"); return True
            time.sleep(0.05)
        self._log(f"  ⚠ Timeout '{label}'  err={self._arm_err(joints):.3f}rad")
        return True

    def _wait_grip(self, j4: float, timeout: float = 8.0):
        deadline = time.time() + timeout
        while time.time() < deadline:
            if abs(self._j4()-j4) < 0.06: return
            time.sleep(0.05)

    def _log(self, txt: str):
        msg = String(); msg.data = txt
        self.status_pub.publish(msg)
        self.get_logger().info(f"[SERVO] {txt}")

    # ── State machine ──────────────────────────────────────────────────────────

    def _sm_loop(self):
        while rclpy.ok():
            with self._lock:
                state = self._state
                slot  = self._target_slot
            if state == State.IDLE or slot is None:
                time.sleep(0.1); continue
            {
                State.MOVE_HOVER:   self._do_hover,
                State.SERVO_VERIFY: self._do_verify,
                State.DESCEND:      self._do_descend,
                State.GRIP:         self._do_grip,
                State.LIFT:         self._do_lift,
                State.TRANSIT:      self._do_transit,
                State.DROP:         self._do_drop,
                State.GOING_HOME:   self._do_home,
            }[state](slot)
            time.sleep(0.05)

    def _set_state(self, s: State):
        with self._lock: self._state = s
        self._log(f"→ {s.name}")

    # ─────────────────────────────────────────────────────────────────────────
    # MOVE_HOVER
    # ─────────────────────────────────────────────────────────────────────────
    def _do_hover(self, slot: int):
        tx, ty = self._best_xy(slot)
        self._log(f"MOVE_HOVER  slot={slot}  target=({tx:.3f},{ty:.3f})  z={HOVER_Z}")

        joints = ik(tx, ty, HOVER_Z)
        if joints is None:
            self._log(f"  IK unreachable — check target position"); return

        self._log(f"  IK  [{joints[0]:.4f}, {joints[1]:.4f}, {joints[2]:.4f}]")
        self._send_grip(0.0, GRIPPER_DUR)   # open gripper
        time.sleep(0.5)

        # safe: go home first
        self._log("  Going home first...")
        self._send_arm(HOME, HOME_DUR)
        self._wait_arm(HOME, "home", HOME_DUR+3)

        # move to hover
        self._log("  Moving to hover position...")
        self._send_arm(joints, HOVER_DUR)
        self._wait_arm(joints, "hover", HOVER_DUR+5)

        # verify FK
        j1,j2,j3 = self._arm_j()
        ax,ay,az = fk(j1,j2,j3)
        self._log(f"  FK result: ({ax:.3f},{ay:.3f},{az:.3f})  "
                  f"xy_err={math.hypot(ax-tx,ay-ty)*1000:.0f}mm")

        self._set_state(State.SERVO_VERIFY)

    # ─────────────────────────────────────────────────────────────────────────
    # SERVO_VERIFY
    # Read ArUco several times, refine IK, cache final target.
    # Arm is still at hover — markers are fully visible.
    # ─────────────────────────────────────────────────────────────────────────
    def _do_verify(self, slot: int):
        self._log(f"SERVO_VERIFY  refining from ArUco  ({SERVO_ITERS} iters)")

        best_xy   = None
        best_err  = float("inf")

        for i in range(SERVO_ITERS):
            time.sleep(0.5)   # wait for fresh ArUco reading

            tx, ty   = self._best_xy(slot)
            j1,j2,j3 = self._arm_j()
            ax,ay,_  = fk(j1,j2,j3)
            err_xy   = math.hypot(tx-ax, ty-ay)

            self._log(f"  iter {i+1}/{SERVO_ITERS}  "
                      f"target=({tx:.3f},{ty:.3f})  "
                      f"arm_fk=({ax:.3f},{ay:.3f})  "
                      f"err={err_xy*1000:.0f}mm")

            # track best reading
            if err_xy < best_err:
                best_err = err_xy
                best_xy  = (tx, ty)

            if err_xy < XY_TOL:
                self._log(f"  ✔ aligned  err={err_xy*1000:.0f}mm")
                break

            # recompute and resend IK with fresh reading
            joints = ik(tx, ty, HOVER_Z)
            if joints is not None:
                self._log(f"  Resending IK [{joints[0]:.4f},{joints[1]:.4f},{joints[2]:.4f}]")
                self._send_arm(joints, 2.0)
                time.sleep(2.2)   # wait for arm to settle

        # ── LOCK the best target position ────────────────────────────────────
        # From here on, ALL subsequent states use self._locked_xy / _z.
        # ArUco is NOT consulted again until the next pick request.
        if best_xy is None:
            best_xy = self._best_xy(slot)

        with self._lock:
            self._locked_xy = best_xy
            # get z from latest ArUco reading
            info = self._box_data.get(slot,{})
            self._locked_z = float(info.get("z", PICK_Z)) if info.get("detected") else PICK_Z

        self._log(f"  ★ TARGET LOCKED: xy={best_xy}  z={self._locked_z:.3f}  "
                  f"final_err={best_err*1000:.0f}mm")
        self._log("  (ArUco will be occluded during descent — using cached target)")

        self._set_state(State.DESCEND)

    # ─────────────────────────────────────────────────────────────────────────
    # DESCEND
    # Uses ONLY the locked target — no ArUco.
    # Slow (6 s) so the joint controller tracks smoothly.
    # ─────────────────────────────────────────────────────────────────────────
    def _do_descend(self, slot: int):
        with self._lock:
            lxy = self._locked_xy
            lz  = self._locked_z

        if lxy is None:
            self._log("  ERROR: no locked target — aborting"); return

        tx, ty = lxy

        self._log(f"DESCEND  (CACHED target)  ({tx:.3f},{ty:.3f},{lz:.3f})")
        self._log("  ARM WILL BLOCK CAMERA — using joint states only")

        joints = ik(tx, ty, lz)
        if joints is None:
            self._log(f"  IK unreachable at pick height — aborting")
            self._set_state(State.GOING_HOME); return

        self._log(f"  IK  [{joints[0]:.4f},{joints[1]:.4f},{joints[2]:.4f}]")
        self._log(f"  Sending slow descent ({DESCEND_DUR}s)...")

        self._send_arm(joints, DESCEND_DUR)
        self._wait_arm(joints, "pick position", DESCEND_DUR + 5.0)

        # verify with FK
        j1,j2,j3 = self._arm_j()
        ax,ay,az  = fk(j1,j2,j3)
        self._log(f"  FK after descent: ({ax:.3f},{ay:.3f},{az:.3f})")
        self._log(f"  xy_err={math.hypot(ax-tx,ay-ty)*1000:.0f}mm  "
                  f"z_err={abs(az-lz)*1000:.0f}mm")

        self._set_state(State.GRIP)

    # ─────────────────────────────────────────────────────────────────────────
    # GRIP
    # ─────────────────────────────────────────────────────────────────────────
    def _do_grip(self, slot: int):
        self._log("GRIP  closing gripper")
        self._send_grip(-0.7, GRIPPER_DUR)
        self._wait_grip(-0.7)
        time.sleep(PICK_DWELL)
        self._set_state(State.LIFT)

    # ─────────────────────────────────────────────────────────────────────────
    # LIFT  — go back to hover height using cached target
    # ─────────────────────────────────────────────────────────────────────────
    def _do_lift(self, slot: int):
        with self._lock: lxy = self._locked_xy
        tx, ty = lxy if lxy else self._best_xy(slot)

        self._log(f"LIFT  to hover z={HOVER_Z}")
        joints = ik(tx, ty, HOVER_Z)
        if joints is None:
            # fallback: raise j3 from current position
            cur = self._arm_j()
            joints = [cur[0], cur[1], max(cur[2]+0.17, -1.0)]
            self._log("  IK failed — raising j3 from current")

        self._send_arm(joints, FAST_DUR)
        self._wait_arm(joints, "lift to hover", FAST_DUR+5)
        self._set_state(State.TRANSIT)

    # ─────────────────────────────────────────────────────────────────────────
    # TRANSIT
    # ─────────────────────────────────────────────────────────────────────────
    def _do_transit(self, slot: int):
        self._log("TRANSIT  moving to drop zone (FK table)")
        self._send_arm(DROP_HOVER, HOVER_DUR)
        self._wait_arm(DROP_HOVER, "drop hover", HOVER_DUR+5)
        self._send_arm(DROP_PLACE, FAST_DUR)
        self._wait_arm(DROP_PLACE, "drop place", FAST_DUR+5)
        self._set_state(State.DROP)

    # ─────────────────────────────────────────────────────────────────────────
    # DROP
    # ─────────────────────────────────────────────────────────────────────────
    def _do_drop(self, slot: int):
        self._log("DROP  opening gripper")
        self._send_grip(0.0, GRIPPER_DUR)
        self._wait_grip(0.0)
        time.sleep(DROP_DWELL)
        self._send_arm(DROP_HOVER, FAST_DUR)
        self._wait_arm(DROP_HOVER, "retract", FAST_DUR+5)
        self._set_state(State.GOING_HOME)

    # ─────────────────────────────────────────────────────────────────────────
    # HOME
    # ─────────────────────────────────────────────────────────────────────────
    def _do_home(self, slot: int):
        self._log("HOME  returning")
        self._send_arm(HOME, HOME_DUR)
        self._wait_arm(HOME, "home", HOME_DUR+5)
        with self._lock:
            self._state       = State.IDLE
            self._target_slot = None
            self._locked_xy   = None
        self._log("IDLE  ready for next pick ✓")


def main(args=None):
    rclpy.init(args=args)
    node = VisualServoNode()
    exe  = MultiThreadedExecutor(num_threads=4)
    exe.add_node(node)
    try:
        exe.spin()
    except KeyboardInterrupt:
        pass
    finally:
        exe.shutdown()
        node.destroy_node()
        try: rclpy.shutdown()
        except: pass


if __name__ == "__main__":
    main()
