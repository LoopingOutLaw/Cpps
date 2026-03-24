#!/usr/bin/env python3
"""
visual_servo_node.py  -  2-Phase ArUco pick-and-place for Dexter Arm
=====================================================================

BUG FIX SUMMARY (v2):
  The original node used an incorrect FK formula (mixed sin/cos) and joint values
  derived from that wrong formula.  The correct URDF FK is:

      z = L0 + L1*cos(j2) + L2*cos(j2+j3)          ← cos/cos, NOT cos/sin
      r = -(L1*sin(j2) + L2*sin(j2+j3))             ← both sin, negated

  This is consistent with inventory_node.py and dispatch_engine.py, whose joint
  values are verified to reach every shelf slot in Gazebo.

  Joint values (hover / pick) now match dispatch_engine.py exactly:
      Hover: j2 = -0.5502, j3 = -1.0000  → claw z ≈ 1.354 m, gripper ≈ 1.254 m
      Pick:  j2 = -0.5502, j3 = -1.1711  → claw z ≈ 1.216 m, gripper ≈ 1.116 m

Trigger:
    ros2 topic pub --once /visual_servo/pick_request std_msgs/msg/Int32 "{data: 0}"
Watch:
    ros2 topic echo /visual_servo/status

Workflow:
    Phase 1 – raise to hover height with j1=0 (arm along +x)
    Phase 2 – rotate j1 toward slot; refine with ArUco feedback (up to 8 iter)
    Descend  – lower j3 to pick height, j1 locked
    Grip     – close gripper
    Lift     – raise back to hover height
    Transit  – move to drop-zone hover → drop-zone place
    Drop     – open gripper, retract
    Home     – return to [0,0,0]
"""

from __future__ import annotations
import json, math, threading, time
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

# ── Arm kinematics (URDF-verified) ────────────────────────────────────────────
L0, L1, L2 = 0.657, 0.800, 0.820
GRIP_OFFSET = 0.100   # approx distance from claw_support to gripper fingers

# ── FIXED: correct hover/pick joint values (same as dispatch_engine.py) ───────
#
#   OLD (wrong):  J2_HOVER=-0.54203, J3_HOVER=+0.63688  ← positive j3!
#   NEW (correct): J2_HOVER=-0.5502,  J3_HOVER=-1.0000  ← negative j3
#
#   With the OLD values + correct URDF physics:
#     actual z ≈ 2.16 m, r ≈ 0.33 m  (arm nearly straight up, barely extended!)
#   With the NEW values:
#     actual z ≈ 1.354 m, r ≈ 1.237 m (correct hover above shelf slots)
#
J2_HOVER = -0.5502;  J3_HOVER = -1.0000   # hover: claw z≈1.354 m
J2_PICK  = -0.5502;  J3_PICK  = -1.1711   # pick:  claw z≈1.216 m

CLAW_HOVER_Z = 1.354   # FK(j2=J2_HOVER, j3=J3_HOVER)
CLAW_PICK_Z  = 1.216   # FK(j2=J2_PICK,  j3=J3_PICK)

# Slot base-yaw angles (j1) and world (x,y) targets
J1_SLOT: Dict[int, float] = {0: -0.54963, 1: -0.18000, 2: +0.18000, 3: +0.54963}

SLOT_GT: Dict[int, Tuple[float, float]] = {
    0: (1.048, -0.642), 1: (1.209, -0.220),
    2: (1.209, +0.220), 3: (1.048, +0.642),
}

HOME       = [0.00,   0.00,    0.00   ]
DROP_HOVER = [1.0122, J2_HOVER, J3_HOVER]   # hover above dispatch tray
DROP_PLACE = [1.0122, J2_PICK,  J3_PICK ]   # place into dispatch tray

# ── Motion parameters ─────────────────────────────────────────────────────────
TRAJ_S     = 6.0    # trajectory duration sent to controller (seconds)
RESEND_S   = 3.0    # re-publish goal every N s to prevent controller drop
JOINT_TOL  = 0.04   # rad — "arrived" threshold
MAX_WAIT   = 90.0   # s  — timeout per motion step
POLL_S     = 0.15   # s  — polling interval in wait loop
ARUCO_AGE  = 8.0    # s  — ArUco reading max staleness
PICK_DWELL = 2.0    # s  — wait after gripping
DROP_DWELL = 1.0    # s  — wait after releasing
GRIP_DUR   = 1.5    # s  — gripper motion duration
ALIGN_TOL  = 30.0   # mm — xy alignment OK threshold for Phase 2


# ── FIXED: correct FK matching URDF joint axes ────────────────────────────────
def fk(j1: float, j2: float, j3: float) -> Tuple[float, float, float]:
    """
    Forward kinematics for Dexter URDF.

    Both joints 2 and 3 rotate about the local X-axis.
    The arm extends along Z (L1 segment) then along Y (L2 segment via fixed
    horizontal_arm_to_claw_support joint), which in the planar arm model gives:

        z = L0 + L1*cos(j2) + L2*cos(j2+j3)
        r = -(L1*sin(j2) + L2*sin(j2+j3))    (negative because arm bends away)

    Then rotation by j1 about world Z maps radial reach to world X-Y:
        x = r * cos(j1),  y = r * sin(j1)

    Verification with SLOT_PICK[0] = [-0.5496, -0.5502, -1.1711]:
        z = 0.657 + 0.8*cos(-0.5502) + 0.82*cos(-1.7213) = 1.216 m  ✓
        r = -(0.8*sin(-0.5502) + 0.82*sin(-1.7213)) = 1.225 m  ✓
        x = 1.225*cos(-0.5496) = 1.044 ≈ 1.048  ✓
        y = 1.225*sin(-0.5496) = -0.640 ≈ -0.642  ✓
    """
    r = -(L1 * math.sin(j2) + L2 * math.sin(j2 + j3))
    z =  L0 + L1 * math.cos(j2) + L2 * math.cos(j2 + j3)
    return round(r * math.cos(j1), 4), round(r * math.sin(j1), 4), round(z, 4)


class State(Enum):
    IDLE    = auto()
    PH1_Z   = auto()
    PH2_XY  = auto()
    DESCEND = auto()
    GRIP    = auto()
    LIFT    = auto()
    TRANSIT = auto()
    DROP    = auto()
    HOME    = auto()


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
                                 self._js_cb,    10, callback_group=cb)
        self.create_subscription(String,     "/inventory/box_poses",
                                 self._boxes_cb, 10, callback_group=cb)
        self.create_subscription(Int32,      "/visual_servo/pick_request",
                                 self._req_cb,   10, callback_group=cb)

        self._state    = State.IDLE
        self._slot:    Optional[int] = None
        self._lock_j1: float = 0.0
        self._lock_xy: Optional[Tuple[float, float]] = None
        self._mu       = threading.Lock()

        self._j: Dict[str, float] = {f"joint_{i}": 0.0 for i in range(1, 6)}
        self._bdata: Dict[int, dict] = {}
        self._ats:   float = 0.0

        threading.Thread(target=self._sm, daemon=True).start()

        # Startup diagnostics
        cx, cy, cz = fk(0, J2_HOVER, J3_HOVER)
        px, py, pz = fk(0, J2_PICK, J3_PICK)
        self.get_logger().info(
            f"\n{'='*62}"
            f"\n  Visual Servo Node  (fixed FK + joint values)"
            f"\n  Hover: j2={J2_HOVER} j3={J3_HOVER}"
            f"  → claw=({cx},{cy},{cz})  gripper~{cz-GRIP_OFFSET:.3f}m"
            f"\n  Pick:  j2={J2_PICK}  j3={J3_PICK}"
            f"  → claw=({px},{py},{pz})  gripper~{pz-GRIP_OFFSET:.3f}m"
            f"\n  Trigger: ros2 topic pub --once /visual_servo/pick_request"
            f"\n           std_msgs/msg/Int32 \"{{data: 0}}\""
            f"\n{'='*62}"
        )

    # ── Callbacks ──────────────────────────────────────────────────────────────

    def _js_cb(self, msg: JointState):
        with self._mu:
            for n, p in zip(msg.name, msg.position):
                if n in self._j:
                    self._j[n] = float(p)

    def _boxes_cb(self, msg: String):
        try:
            d = json.loads(msg.data)
            with self._mu:
                for k, v in d.items():
                    self._bdata[int(k)] = v
                self._ats = time.time()
        except Exception as e:
            self.get_logger().warn(f"boxes_cb: {e}")

    def _req_cb(self, msg: Int32):
        slot = int(msg.data)
        if slot not in range(4):
            self.get_logger().warn(f"Invalid slot {slot} (0-3 only)")
            return
        with self._mu:
            if self._state != State.IDLE:
                self.get_logger().warn(
                    f"Pick request ignored — currently busy: {self._state.name}")
                return
            self._slot    = slot
            self._lock_xy = None
            self._state   = State.PH1_Z
        self.get_logger().info(f"Pick request accepted: slot {slot}")

    # ── Helpers ────────────────────────────────────────────────────────────────

    def _fresh(self) -> bool:
        with self._mu:
            return (time.time() - self._ats) < ARUCO_AGE

    def _best_xy(self, slot: int) -> Tuple[float, float]:
        """Return ArUco-measured box XY if fresh, else FK fallback."""
        with self._mu:
            info = self._bdata.get(slot, {})
        if info.get("detected") and self._fresh():
            return float(info["x"]), float(info["y"])
        return SLOT_GT[slot]

    def _arm(self) -> List[float]:
        with self._mu:
            return [self._j[f"joint_{i}"] for i in range(1, 4)]

    def _log(self, txt: str):
        m = String(); m.data = txt
        self.status_pub.publish(m)
        self.get_logger().info(f"[SERVO] {txt}")

    def _set(self, s: State):
        with self._mu:
            self._state = s
        self._log(f"-> {s.name}")

    # ── Trajectory helpers ─────────────────────────────────────────────────────

    def _pub_arm(self, joints: List[float]):
        msg = JointTrajectory()
        msg.joint_names = ["joint_1", "joint_2", "joint_3"]
        pt = JointTrajectoryPoint()
        pt.positions  = [float(j) for j in joints]
        pt.velocities = [0.0, 0.0, 0.0]
        s = int(TRAJ_S); ns = int((TRAJ_S - s) * 1e9)
        pt.time_from_start = DurationMsg(sec=s, nanosec=ns)
        msg.points = [pt]
        self.arm_pub.publish(msg)

    def _pub_grip(self, j4: float):
        msg = JointTrajectory()
        msg.joint_names = ["joint_4"]
        pt = JointTrajectoryPoint()
        pt.positions  = [float(j4)]
        pt.velocities = [0.0]
        pt.time_from_start = DurationMsg(sec=int(GRIP_DUR), nanosec=0)
        msg.points = [pt]
        self.grip_pub.publish(msg)

    def _move(self, joints: List[float], label: str) -> bool:
        """
        Send arm goal and wait for arrival.
        Re-publishes every RESEND_S seconds so the controller cannot drop the goal.
        Returns True on success, False on timeout (caller can choose to continue).
        """
        j1t, j2t, j3t = joints[0], joints[1], joints[2]
        cx, cy, cz = fk(j1t, j2t, j3t)
        self._log(
            f"MOVE {label}  [{j1t:.4f},{j2t:.4f},{j3t:.4f}]"
            f"  claw→({cx},{cy},{cz})  gripper~{cz-GRIP_OFFSET:.3f}m"
        )

        deadline  = time.time() + MAX_WAIT
        last_send = 0.0
        last_log  = 0.0

        while time.time() < deadline:
            cur = self._arm()
            err = max(abs(cur[i] - joints[i]) for i in range(3))
            now = time.time()

            if err < JOINT_TOL:
                cx2, cy2, cz2 = fk(*cur)
                self._log(
                    f"  ✔ {label}  err={err:.4f}rad"
                    f"  claw=({cx2},{cy2},{cz2})  gripper~{cz2-GRIP_OFFSET:.3f}m"
                )
                return True

            if now - last_send >= RESEND_S:
                self._pub_arm(joints)
                last_send = now

            if now - last_log >= 5.0:
                cx2, cy2, cz2 = fk(*cur)
                self._log(
                    f"  [{label}] err={err:.4f}  claw=({cx2},{cy2},{cz2})"
                )
                last_log = now

            time.sleep(POLL_S)

        self._log(f"  ⚠ TIMEOUT {label} — proceeding anyway")
        return False

    def _wait_grip(self, j4: float, timeout: float = 6.0):
        deadline = time.time() + timeout
        while time.time() < deadline:
            with self._mu:
                if abs(self._j["joint_4"] - j4) < 0.06:
                    return
            time.sleep(0.05)

    # ── State machine (runs in a dedicated thread) ────────────────────────────

    def _sm(self):
        while rclpy.ok():
            with self._mu:
                state = self._state
                slot  = self._slot
            if state == State.IDLE or slot is None:
                time.sleep(0.1)
                continue
            try:
                {
                    State.PH1_Z:   self._ph1_z,
                    State.PH2_XY:  self._ph2_xy,
                    State.DESCEND: self._descend,
                    State.GRIP:    self._do_grip,
                    State.LIFT:    self._lift,
                    State.TRANSIT: self._transit,
                    State.DROP:    self._do_drop,
                    State.HOME:    self._home,
                }[state](slot)
            except Exception as e:
                import traceback
                self.get_logger().error(f"State machine exception: {e}\n"
                                        f"{traceback.format_exc()}")
                self._set(State.HOME)
            time.sleep(0.05)

    # ── PHASE 1: raise to hover height, j1=0 (arm along world +X) ────────────

    def _ph1_z(self, slot: int):
        hover_z = fk(0, J2_HOVER, J3_HOVER)[2]
        self._log(
            f"PHASE 1  raise to hover height"
            f"\n  j1=0.0  j2={J2_HOVER}  j3={J3_HOVER}"
            f"\n  target claw z={hover_z:.3f}m  gripper~{hover_z-GRIP_OFFSET:.3f}m"
        )

        # Open gripper first
        self._pub_grip(0.0)
        time.sleep(GRIP_DUR + 0.3)

        ok = self._move([0.0, J2_HOVER, J3_HOVER], "ph1-hover")
        if not ok:
            self._log("Phase 1 timeout → aborting to HOME")
            self._set(State.HOME)
            return

        j = self._arm()
        cx, cy, cz = fk(*j)
        self._log(
            f"  Phase 1 done  claw=({cx},{cy},{cz})  gripper~{cz-GRIP_OFFSET:.3f}m"
        )
        self._set(State.PH2_XY)

    # ── PHASE 2: rotate j1 to point at box while keeping hover height ─────────

    def _ph2_xy(self, slot: int):
        tx, ty  = self._best_xy(slot)
        j1_tgt  = J1_SLOT[slot]
        hover_z = fk(j1_tgt, J2_HOVER, J3_HOVER)[2]

        self._log(
            f"PHASE 2  rotate j1 to box  (j2,j3 frozen at hover)"
            f"\n  target=({tx:.3f},{ty:.3f})  j1={j1_tgt:.4f}"
            f"  claw z≈{hover_z:.3f}m  gripper~{hover_z-GRIP_OFFSET:.3f}m"
        )

        ok = self._move([j1_tgt, J2_HOVER, J3_HOVER], "ph2-rotate")
        if not ok:
            self._log("Phase 2 timeout → aborting to HOME")
            self._set(State.HOME)
            return

        j     = self._arm()
        ax, ay, az = fk(*j)
        xy_err = math.hypot(ax - tx, ay - ty) * 1000
        self._log(
            f"  After rotate: claw=({ax},{ay},{az})"
            f"  xy_err={xy_err:.0f}mm"
        )

        # ArUco-guided j1 refinement (up to 8 iterations)
        best_err = xy_err
        for it in range(1, 9):
            time.sleep(1.0)
            tx, ty = self._best_xy(slot)
            j_now  = self._arm()
            ax, ay, az = fk(*j_now)
            err = math.hypot(ax - tx, ay - ty) * 1000
            self._log(
                f"  ArUco {it}: target=({tx:.3f},{ty:.3f})"
                f"  fk=({ax:.3f},{ay:.3f})  err={err:.0f}mm"
            )

            if err < best_err:
                best_err = err

            if err < ALIGN_TOL:
                self._log(f"  ✔ aligned  err={err:.0f}mm  (< {ALIGN_TOL:.0f}mm threshold)")
                break

            # Correct j1 toward the ArUco-detected box centre
            j1_corr = math.atan2(ty, tx)
            diff    = abs(j1_corr - j_now[0])
            if diff < 0.003:
                self._log(
                    f"  j1 already optimal (diff={diff:.4f}rad) → proceeding"
                )
                break

            self._log(
                f"  j1 correction: {j_now[0]:.4f} → {j1_corr:.4f}"
                f"  (Δ={diff:.4f}rad)"
            )
            self._move([j1_corr, J2_HOVER, J3_HOVER], f"ph2-refine-{it}")
        else:
            self._log(f"  Refinement exhausted  best_err={best_err:.0f}mm")

        if best_err > 80.0:
            self._log(
                f"ABORT: xy_err={best_err:.0f}mm > 80mm"
                f" — ArUco may not be visible or arm miscalibrated → HOME"
            )
            self._set(State.HOME)
            return

        j_now = self._arm()
        with self._mu:
            self._lock_j1 = j_now[0]
            self._lock_xy = self._best_xy(slot)

        self._log(
            f"  LOCKED  j1={self._lock_j1:.4f}"
            f"  locked_xy={self._lock_xy}  → DESCEND"
        )
        self._set(State.DESCEND)

    # ── DESCEND: lower j3 to pick height, j1 locked ──────────────────────────

    def _descend(self, slot: int):
        with self._mu:
            j1  = self._lock_j1
            lxy = self._lock_xy

        pick_z = fk(j1, J2_PICK, J3_PICK)[2]
        self._log(
            f"DESCEND  j1={j1:.4f} (locked)"
            f"\n  j2: {J2_HOVER} → {J2_PICK}"
            f"  j3: {J3_HOVER} → {J3_PICK}"
            f"\n  claw: {CLAW_HOVER_Z:.3f}m → {pick_z:.3f}m"
            f"  gripper: {CLAW_HOVER_Z-GRIP_OFFSET:.3f}m → {pick_z-GRIP_OFFSET:.3f}m"
        )

        self._move([j1, J2_PICK, J3_PICK], "descend")

        j = self._arm()
        cx, cy, cz = fk(*j)
        xy_err = (math.hypot(cx - lxy[0], cy - lxy[1]) * 1000
                  if lxy else -1.0)
        self._log(
            f"  FK@pick: claw=({cx},{cy},{cz})"
            f"  gripper~{cz-GRIP_OFFSET:.3f}m"
            f"  xy_err={xy_err:.0f}mm"
        )
        self._set(State.GRIP)

    # ── GRIP ──────────────────────────────────────────────────────────────────

    def _do_grip(self, slot: int):
        self._log("GRIP  closing gripper")
        self._pub_grip(-0.7)
        self._wait_grip(-0.7)
        time.sleep(PICK_DWELL)
        self._set(State.LIFT)

    # ── LIFT ──────────────────────────────────────────────────────────────────

    def _lift(self, slot: int):
        with self._mu:
            j1 = self._lock_j1
        lift_z = fk(j1, J2_HOVER, J3_HOVER)[2]
        self._log(
            f"LIFT  j1={j1:.4f}  j3: {J3_PICK} → {J3_HOVER}"
            f"  claw: {CLAW_PICK_Z:.3f}m → {lift_z:.3f}m"
        )
        self._move([j1, J2_HOVER, J3_HOVER], "lift")
        self._set(State.TRANSIT)

    # ── TRANSIT ───────────────────────────────────────────────────────────────

    def _transit(self, slot: int):
        dh_x, dh_y, dh_z = fk(*DROP_HOVER)
        dp_x, dp_y, dp_z = fk(*DROP_PLACE)
        self._log(
            f"TRANSIT  to drop zone"
            f"\n  hover  → claw=({dh_x},{dh_y},{dh_z})"
            f"\n  place  → claw=({dp_x},{dp_y},{dp_z})"
        )
        self._move(DROP_HOVER, "transit-hover")
        self._move(DROP_PLACE, "transit-place")
        self._set(State.DROP)

    # ── DROP ──────────────────────────────────────────────────────────────────

    def _do_drop(self, slot: int):
        self._log("DROP  releasing item")
        self._pub_grip(0.0)
        self._wait_grip(0.0)
        time.sleep(DROP_DWELL)
        self._move(DROP_HOVER, "drop-retract")
        self._set(State.HOME)

    # ── HOME ──────────────────────────────────────────────────────────────────

    def _home(self, slot: int):
        self._log("HOME  returning to [0,0,0]")
        self._move(HOME, "home")
        with self._mu:
            self._state   = State.IDLE
            self._slot    = None
            self._lock_xy = None
        self._log("IDLE  ✔ ready for next pick request")


# ── Entry point ───────────────────────────────────────────────────────────────

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
        try:
            rclpy.shutdown()
        except Exception:
            pass


if __name__ == "__main__":
    main()
