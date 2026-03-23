#!/usr/bin/env python3
"""
visual_servo_node.py  -  2-Phase ArUco pick-and-place for Dexter Arm
Trigger:
    ros2 topic pub --once /visual_servo/pick_request std_msgs/msg/Int32 "{data: 0}"
Watch:
    ros2 topic echo /visual_servo/status

CORRECT FK (verified Gazebo HOME -> claw z=1.457, gripper_left z=1.357):
    z = L0 + L1*cos(j2) + L2*sin(j2+j3)
    r = -L1*sin(j2) + L2*cos(j2+j3)

2-Phase approach:
    Phase1: j2+j3 only -> set gripper height (j1=0, arm along +x)
    Phase2: j1 only    -> rotate to box (z fixed, pure 2D)
    Descend: j2+j3 only -> lower onto box (j1 locked)
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

L0, L1, L2  = 0.657, 0.800, 0.820
GRIP_OFFSET  = 0.100   # gripper_left is 0.1m below claw_support

CLAW_HOVER_Z = 1.420   # gripper ~1.320m  (above box)
CLAW_PICK_Z  = 1.316   # gripper ~1.216m  (box top)

J2_HOVER = -0.54203;  J3_HOVER = +0.63688
J2_PICK  = -0.53736;  J3_PICK  = +0.50291

J1_SLOT: Dict[int, float] = {0: -0.54963, 1: -0.18000, 2: +0.18000, 3: +0.54963}

SLOT_GT: Dict[int, Tuple[float,float]] = {
    0: (1.048, -0.642), 1: (1.209, -0.220),
    2: (1.209, +0.220), 3: (1.048, +0.642),
}

HOME       = [0.00,    0.00,     0.00    ]
DROP_HOVER = [1.0122,  J2_HOVER, J3_HOVER]
DROP_PLACE = [1.0122,  J2_PICK,  J3_PICK ]

TRAJ_S     = 6.0
RESEND_S   = 3.0
JOINT_TOL  = 0.03
MAX_WAIT   = 300.0
POLL_S     = 0.2
ARUCO_AGE  = 6.0
PICK_DWELL = 2.5
DROP_DWELL = 1.0
GRIP_DUR   = 1.5


def fk(j1: float, j2: float, j3: float) -> Tuple[float,float,float]:
    r = -L1*math.sin(j2) + L2*math.cos(j2+j3)
    z =  L0 + L1*math.cos(j2) + L2*math.sin(j2+j3)
    return round(r*math.cos(j1),4), round(r*math.sin(j1),4), round(z,4)


class State(Enum):
    IDLE=auto(); PH1_Z=auto(); PH2_XY=auto(); DESCEND=auto()
    GRIP=auto(); LIFT=auto(); TRANSIT=auto(); DROP=auto(); HOME=auto()


class VisualServoNode(Node):

    def __init__(self):
        super().__init__("visual_servo_node")
        cb = ReentrantCallbackGroup()

        self.arm_pub    = self.create_publisher(JointTrajectory, "/arm_controller/joint_trajectory", 10)
        self.grip_pub   = self.create_publisher(JointTrajectory, "/gripper_controller/joint_trajectory", 10)
        self.status_pub = self.create_publisher(String, "/visual_servo/status", 10)

        self.create_subscription(JointState, "/joint_states",              self._js_cb,    10, callback_group=cb)
        self.create_subscription(String,     "/inventory/box_poses",       self._boxes_cb, 10, callback_group=cb)
        self.create_subscription(Int32,      "/visual_servo/pick_request", self._req_cb,   10, callback_group=cb)

        self._state    = State.IDLE
        self._slot:    Optional[int]             = None
        self._lock_j1: float                     = 0.0
        self._lock_xy: Optional[Tuple[float,float]] = None
        self._mu       = threading.Lock()
        self._j:       Dict[str, float] = {f"joint_{i}": 0.0 for i in range(1, 6)}
        self._bdata:   Dict[int, dict]  = {}
        self._ats:     float            = 0.0

        threading.Thread(target=self._sm, daemon=True).start()

        cx, cy, cz = fk(0, 0, 0)
        self.get_logger().info(
            f"\n{'='*60}"
            f"\n  Visual Servo Node"
            f"\n  FK HOME: claw=({cx},{cy},{cz})  gripper~{cz-GRIP_OFFSET:.3f}m"
            f"\n  Box top: 1.216m  Hover: {CLAW_HOVER_Z-GRIP_OFFSET:.3f}m"
            f"\n  Trigger: ros2 topic pub --once /visual_servo/pick_request"
            f"\n           std_msgs/msg/Int32 \"{{data: 0}}\""
            f"\n{'='*60}"
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
            self.get_logger().warn(f"boxes: {e}")

    def _req_cb(self, msg: Int32):
        slot = int(msg.data)
        if slot not in range(4):
            self.get_logger().warn(f"Bad slot {slot}")
            return
        with self._mu:
            if self._state != State.IDLE:
                self.get_logger().warn(f"Busy: {self._state.name}")
                return
            self._slot    = slot
            self._lock_xy = None
            self._state   = State.PH1_Z
        self.get_logger().info(f"Pick request: slot {slot}")

    # ── Helpers ────────────────────────────────────────────────────────────────

    def _fresh(self) -> bool:
        with self._mu:
            return (time.time() - self._ats) < ARUCO_AGE

    def _best_xy(self, slot: int) -> Tuple[float, float]:
        with self._mu:
            info = self._bdata.get(slot, {})
        if info.get("detected") and self._fresh():
            return float(info["x"]), float(info["y"])
        return SLOT_GT[slot]

    def _arm(self) -> List[float]:
        with self._mu:
            return [self._j["joint_1"], self._j["joint_2"], self._j["joint_3"]]

    def _log(self, txt: str):
        m = String()
        m.data = txt
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
        s  = int(TRAJ_S)
        ns = int((TRAJ_S - s) * 1e9)
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
        Publish arm command every RESEND_S seconds until joints arrive.
        Returns True on success, False on timeout.
        """
        j1t, j2t, j3t = joints[0], joints[1], joints[2]
        cx, cy, cz = fk(j1t, j2t, j3t)
        self._log(
            f"MOVE {label}  [{j1t:.4f},{j2t:.4f},{j3t:.4f}]"
            f"  claw->({cx},{cy},{cz})  gripper~{cz-GRIP_OFFSET:.3f}m"
        )

        deadline  = time.time() + MAX_WAIT
        last_send = 0.0
        last_log  = 0.0

        while time.time() < deadline:
            cur = self._arm()
            err = max(abs(cur[i] - joints[i]) for i in range(3))
            cx2, cy2, cz2 = fk(cur[0], cur[1], cur[2])
            now = time.time()

            if err < JOINT_TOL:
                self._log(
                    f"  OK {label}  err={err:.4f}"
                    f"  claw=({cx2},{cy2},{cz2})  gripper~{cz2-GRIP_OFFSET:.3f}m"
                )
                return True

            # Re-send every RESEND_S so controller can't ignore the goal
            if now - last_send >= RESEND_S:
                self._pub_arm(joints)
                last_send = now

            if now - last_log >= 5.0:
                self._log(
                    f"  [{label}] err={err:.4f}"
                    f"  claw=({cx2},{cy2},{cz2})  gripper~{cz2-GRIP_OFFSET:.3f}m"
                )
                last_log = now

            time.sleep(POLL_S)

        self._log(f"  TIMEOUT {label}")
        return False

    # ── State machine ──────────────────────────────────────────────────────────

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
                    State.DESCEND:  self._descend,
                    State.GRIP:    self._do_grip,
                    State.LIFT:    self._lift,
                    State.TRANSIT: self._transit,
                    State.DROP:    self._do_drop,
                    State.HOME:    self._home,
                }[state](slot)
            except Exception as e:
                import traceback
                self.get_logger().error(f"SM: {e}\n{traceback.format_exc()}")
                self._set(State.HOME)
            time.sleep(0.05)

    # ── PHASE 1: set z, j1=0 ──────────────────────────────────────────────────

    def _ph1_z(self, slot: int):
        _, _, cz_home = fk(0, 0, 0)
        self._log(
            f"PHASE 1  set hover height  j1=0  j2={J2_HOVER:.4f}  j3={J3_HOVER:.4f}"
            f"\n  gripper: {cz_home-GRIP_OFFSET:.3f}m -> {CLAW_HOVER_Z-GRIP_OFFSET:.3f}m"
        )
        self._pub_grip(0.0)
        time.sleep(GRIP_DUR + 0.5)

        ok = self._move([0.0, J2_HOVER, J3_HOVER], "ph1-hover")
        if not ok:
            self._log("Ph1 timeout -> HOME")
            self._set(State.HOME)
            return

        j = self._arm()
        cx, cy, cz = fk(*j)
        self._log(f"  Phase1 done  claw=({cx},{cy},{cz})  gripper~{cz-GRIP_OFFSET:.3f}m")
        self._set(State.PH2_XY)

    # ── PHASE 2: rotate j1 to box, j2+j3 frozen ──────────────────────────────

    def _ph2_xy(self, slot: int):
        tx, ty = self._best_xy(slot)
        j1_tgt = J1_SLOT[slot]

        self._log(
            f"PHASE 2  rotate j1 to box  j2/j3 frozen"
            f"\n  target=({tx:.3f},{ty:.3f})  j1={j1_tgt:.4f}  z={CLAW_HOVER_Z}m"
        )

        ok = self._move([j1_tgt, J2_HOVER, J3_HOVER], "ph2-rotate")
        if not ok:
            self._log("Ph2 timeout -> HOME")
            self._set(State.HOME)
            return

        j = self._arm()
        ax, ay, az = fk(*j)
        err_mm = math.hypot(ax - tx, ay - ty) * 1000
        self._log(f"  After rotate: claw=({ax},{ay},{az})  xy_err={err_mm:.0f}mm")

        best_err = err_mm
        for it in range(1, 8):
            time.sleep(1.0)
            tx, ty   = self._best_xy(slot)
            j_now    = self._arm()
            ax, ay, az = fk(*j_now)
            err = math.hypot(ax - tx, ay - ty) * 1000
            self._log(f"  ArUco {it}: target=({tx:.3f},{ty:.3f})  fk=({ax:.3f},{ay:.3f})  err={err:.0f}mm")
            if err < best_err:
                best_err = err
            if err < 25.0:
                self._log(f"  aligned  err={err:.0f}mm")
                break
            j1_corr = math.atan2(ty, tx)
            diff = abs(j1_corr - j_now[0])
            if diff < 0.003:
                self._log(f"  j1 optimal (diff={diff:.4f}rad)")
                break
            self._log(f"  j1: {j_now[0]:.4f} -> {j1_corr:.4f}")
            ok = self._move([j1_corr, J2_HOVER, J3_HOVER], f"ph2-refine-{it}")
            if not ok:
                self._log(f"  refine-{it} timeout")
                break

        if best_err > 60.0:
            self._log(f"ABORT: err={best_err:.0f}mm > 60mm -> HOME")
            self._set(State.HOME)
            return

        j_now = self._arm()
        with self._mu:
            self._lock_j1 = j_now[0]
            self._lock_xy = self._best_xy(slot)

        self._log(f"  LOCKED  j1={self._lock_j1:.4f}  xy={self._lock_xy}  -> DESCEND")
        self._set(State.DESCEND)

    # ── DESCEND: lower j2+j3, j1 locked ──────────────────────────────────────

    def _descend(self, slot: int):
        with self._mu:
            j1  = self._lock_j1
            lxy = self._lock_xy

        self._log(
            f"DESCEND  j1={j1:.4f}  j2:{J2_HOVER:.4f}->{J2_PICK:.4f}  j3:{J3_HOVER:.4f}->{J3_PICK:.4f}"
            f"\n  gripper: {CLAW_HOVER_Z-GRIP_OFFSET:.3f}m -> {CLAW_PICK_Z-GRIP_OFFSET:.3f}m  "
            f"(drop {(CLAW_HOVER_Z-CLAW_PICK_Z)*1000:.0f}mm)"
        )

        self._move([j1, J2_PICK, J3_PICK], "descend")

        j = self._arm()
        cx, cy, cz = fk(*j)
        xy_err = math.hypot(cx - lxy[0], cy - lxy[1]) * 1000 if lxy else -1
        self._log(
            f"  FK@pick: claw=({cx},{cy},{cz})"
            f"  gripper~{cz-GRIP_OFFSET:.3f}m"
            f"  xy_err={xy_err:.0f}mm"
        )
        self._set(State.GRIP)

    # ── GRIP ──────────────────────────────────────────────────────────────────

    def _do_grip(self, slot: int):
        self._log("GRIP  closing")
        self._pub_grip(-0.7)
        time.sleep(GRIP_DUR + PICK_DWELL)
        self._set(State.LIFT)

    # ── LIFT ──────────────────────────────────────────────────────────────────

    def _lift(self, slot: int):
        with self._mu:
            j1 = self._lock_j1
        self._log(f"LIFT  gripper -> {CLAW_HOVER_Z-GRIP_OFFSET:.3f}m")
        self._move([j1, J2_HOVER, J3_HOVER], "lift")
        self._set(State.TRANSIT)

    # ── TRANSIT ───────────────────────────────────────────────────────────────

    def _transit(self, slot: int):
        self._log("TRANSIT  to drop zone")
        self._move(DROP_HOVER, "drop-hover")
        self._move(DROP_PLACE, "drop-place")
        self._set(State.DROP)

    # ── DROP ──────────────────────────────────────────────────────────────────

    def _do_drop(self, slot: int):
        self._log("DROP  releasing")
        self._pub_grip(0.0)
        time.sleep(GRIP_DUR + DROP_DWELL)
        self._move(DROP_HOVER, "drop-retract")
        self._set(State.HOME)

    # ── HOME ──────────────────────────────────────────────────────────────────

    def _home(self, slot: int):
        self._log("HOME  returning")
        self._move(HOME, "home")
        with self._mu:
            self._state   = State.IDLE
            self._slot    = None
            self._lock_xy = None
        self._log("IDLE  ready")


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
