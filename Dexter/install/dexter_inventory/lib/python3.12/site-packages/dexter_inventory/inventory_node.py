#!/usr/bin/env python3
"""
inventory_node.py  –  Closed-loop ArUco-guided pick-and-place
=============================================================
Subscribes to:
    /inventory/box_poses    (aruco_box_detector → measured slot world pos)
    /inventory/gripper_pose (aruco_box_detector → measured gripper world pos)
    /joint_states

Services:
    inventory/dispatch   (DispatchItem)
    inventory/add_item   (AddItem)

Pick logic (per slot):
    1. If ArUco measured the slot → compute IK from measured (x, y, z)
    2. Else fall back to FK lookup table

IK formula (URDF arm):
    L0=0.657 m  (world z of joint_2 = base z + 0.307 + 0.35)
    L1=0.800 m  (forward_drive_arm length along joint_3 z)
    L2=0.820 m  (horizontal_arm to claw_support along local y)

    j1 = atan2(y, x)            (base yaw toward target)
    r  = -sqrt(x²+y²)           (negative because arm bends away from +x)

    solve for j2, j3:
        L1*sin(j2) + L2*sin(j2+j3) = -r
        L0 + L1*cos(j2) + L2*cos(j2+j3) = z

    seed: j2=-0.55, j3=-1.17  (known-good pick configuration)

FK lookup table (always available):
    Slot 0  j1=-0.5496  j2=-0.5502  j3=-1.1711   (1.048,-0.642)
    Slot 1  j1=-0.1800  j2=-0.5500  j3=-1.1714   (1.209,-0.220)
    Slot 2  j1=+0.1800  j2=-0.5500  j3=-1.1714   (1.209,+0.220)
    Slot 3  j1=+0.5496  j2=-0.5502  j3=-1.1711   (1.048,+0.642)
"""

from __future__ import annotations

import json
import math
import threading
import time
from typing import Any, Dict, List, Optional, Tuple

import rclpy
from builtin_interfaces.msg import Duration as DurationMsg
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node

from sensor_msgs.msg import JointState
from std_msgs.msg import String
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint

try:
    from dexter_msgs.srv import DispatchItem, AddItem
except ImportError as e:
    raise ImportError(
        "dexter_msgs not found — run: colcon build && source install/setup.bash"
    ) from e

from dexter_inventory.inventory_db import (
    init_db, add_item, mark_dispatched, get_stock, get_dispatch_log, stock_count,
)
from dexter_inventory.dispatch_engine import dispatch, check_low_stock, format_expiry

# ── Motion params ─────────────────────────────────────────────────────────────
GOAL_TOL     = 0.06   # rad
GOAL_TIMEOUT = 45.0   # s
MOVE_SLOW    = 4.5    # s
MOVE_FAST    = 3.0    # s
GRIPPER_DUR  = 1.2    # s
PICK_DWELL   = 2.0    # s
DROP_DWELL   = 1.0    # s
ARUCO_MAX_AGE = 10.0  # s — ignore ArUco older than this

# ── Arm kinematics ────────────────────────────────────────────────────────────
L0 = 0.657   # m  (world z of joint_2 axis)
L1 = 0.800   # m
L2 = 0.820   # m

# FK lookup table — verified joint angles per slot
SLOT_PICK: Dict[int, List[float]] = {
    0: [-0.5496, -0.5502, -1.1711],
    1: [-0.1800, -0.5500, -1.1714],
    2: [ 0.1800, -0.5500, -1.1714],
    3: [ 0.5496, -0.5502, -1.1711],
}
SLOT_HOVER: Dict[int, List[float]] = {
    0: [-0.5496, -0.5502, -1.0000],
    1: [-0.1800, -0.5500, -1.0000],
    2: [ 0.1800, -0.5500, -1.0000],
    3: [ 0.5496, -0.5502, -1.0000],
}

HOME       = [0.00,  0.00,  0.00]
DROP_HOVER = [1.0122, -0.5502, -1.0000]
DROP_PLACE = [1.0122, -0.5502, -1.1711]

GRIPPER_OPEN   = [0.0]
GRIPPER_CLOSED = [-0.7]


# ── IK solver ─────────────────────────────────────────────────────────────────

def _ik(x: float, y: float, z: float) -> Optional[List[float]]:
    """
    Closed-form 2-link IK for the Dexter arm.

    Given target world position (x, y, z) metres:
        j1 = atan2(y, x)
        r  = sqrt(x²+y²)   (radial distance from arm base)

    The 2-link planar arm (in the vertical plane defined by j1):
        L1*sin(j2) + L2*sin(j2+j3) = -r   (negative: arm bends away)
        L0 + L1*cos(j2) + L2*cos(j2+j3) = z

    Uses scipy.optimize.fsolve with seed from FK table.
    Falls back to FK table if scipy unavailable or solution invalid.
    """
    try:
        from scipy.optimize import fsolve
    except ImportError:
        return None

    j1 = math.atan2(y, x)
    r  = math.hypot(x, y)

    def residual(jv):
        j2, j3 = jv
        return [
            L1 * math.sin(j2) + L2 * math.sin(j2 + j3) + r,
            L0 + L1 * math.cos(j2) + L2 * math.cos(j2 + j3) - z,
        ]

    try:
        sol, _, ier, _ = fsolve(residual, [-0.55, -1.17], full_output=True)
        if ier != 1:
            return None
        j2, j3 = float(sol[0]), float(sol[1])
        # validate residual
        res = residual([j2, j3])
        if max(abs(v) for v in res) > 0.05:
            return None
        # check joint limits
        if not (-math.pi/2 <= j2 <= 0.0 and -math.pi <= j3 <= 0.0):
            return None
        return [round(j1, 4), round(j2, 4), round(j3, 4)]
    except Exception:
        return None


# ── InventoryNode ─────────────────────────────────────────────────────────────

class InventoryNode(Node):

    def __init__(self):
        super().__init__("inventory_node")
        init_db()

        # Publishers
        self.arm_pub  = self.create_publisher(
            JointTrajectory, "/arm_controller/joint_trajectory", 10)
        self.grip_pub = self.create_publisher(
            JointTrajectory, "/gripper_controller/joint_trajectory", 10)

        # Joint state
        self._jpos: Dict[str, float] = {f"joint_{i}": 0.0 for i in range(1, 6)}
        self._jlock = threading.Lock()

        # ArUco data
        self._slot_data:  Dict[int, dict] = {}   # slot → {x,y,z,detected,yaw_deg,err_mm}
        self._grip_data:  dict = {"detected": False, "x": 0.0, "y": 0.0}
        self._aruco_ts:   float = 0.0

        cb = ReentrantCallbackGroup()

        self.create_subscription(JointState, "/joint_states",
                                 self._js_cb, 10, callback_group=cb)
        self.create_subscription(String, "/inventory/box_poses",
                                 self._box_poses_cb, 10, callback_group=cb)
        self.create_subscription(String, "/inventory/gripper_pose",
                                 self._gripper_pose_cb, 10, callback_group=cb)

        self.create_service(DispatchItem, "inventory/dispatch",
                            self._dispatch_cb, callback_group=cb)
        self.create_service(AddItem, "inventory/add_item",
                            self._add_item_cb, callback_group=cb)

        self.stock_pub = self.create_publisher(String, "inventory/stock_state", 10)
        self.create_timer(1.0, self._pub_stock_cb)

        self.get_logger().info(
            "\nInventoryNode ready — ArUco closed-loop mode\n"
            "  Subscribing to /inventory/box_poses + /inventory/gripper_pose\n"
            "  IK solver: scipy.optimize.fsolve  (FK fallback if unavailable)"
        )

    # ── subscriptions ─────────────────────────────────────────────────────────

    def _js_cb(self, msg: JointState):
        with self._jlock:
            for name, pos in zip(msg.name, msg.position):
                if name in self._jpos:
                    self._jpos[name] = float(pos)

    def _box_poses_cb(self, msg: String):
        try:
            data = json.loads(msg.data)
            for s_str, info in data.items():
                self._slot_data[int(s_str)] = info
            self._aruco_ts = time.time()
        except Exception as e:
            self.get_logger().warn(f"box_poses: {e}")

    def _gripper_pose_cb(self, msg: String):
        try:
            self._grip_data = json.loads(msg.data)
        except Exception as e:
            self.get_logger().warn(f"gripper_pose: {e}")

    def _aruco_fresh(self) -> bool:
        return (time.time() - self._aruco_ts) < ARUCO_MAX_AGE

    # ── joint helpers ─────────────────────────────────────────────────────────

    def _arm_now(self) -> List[float]:
        with self._jlock:
            return [self._jpos.get(f"joint_{i}", 0.0) for i in range(1, 4)]

    def _gripper_now(self) -> float:
        with self._jlock:
            return self._jpos.get("joint_4", 0.0)

    # ── pick joint computation ────────────────────────────────────────────────

    def _pick_joints(self, slot: int) -> Tuple[List[float], str]:
        """
        Return (joint_angles, source) where source is 'ArUco-IK', 'ArUco-FK', or 'FK'.
        Priority:
            1. ArUco detected + IK solved  → most accurate
            2. ArUco detected + IK failed  → FK with ArUco j1 correction
            3. No ArUco                    → pure FK lookup
        """
        fb_pick  = list(SLOT_PICK[slot])
        fb_label = "FK"

        if slot not in self._slot_data or not self._aruco_fresh():
            return fb_pick, fb_label

        info = self._slot_data[slot]
        if not info.get("detected", False):
            return fb_pick, fb_label

        x = float(info["x"])
        y = float(info["y"])
        z = float(info["z"])

        # Try full IK
        sol = _ik(x, y, z)
        if sol is not None:
            self.get_logger().info(
                f"  Slot {slot}: ArUco-IK ({x:.3f},{y:.3f},{z:.3f})m "
                f"→ [{sol[0]:.3f},{sol[1]:.3f},{sol[2]:.3f}]  "
                f"err={info.get('err_mm',-1):.0f}mm")
            return sol, "ArUco-IK"

        # IK failed — correct j1 from ArUco, keep j2/j3 from FK
        j1_aruco = math.atan2(y, x)
        corrected = [round(j1_aruco, 4), fb_pick[1], fb_pick[2]]
        self.get_logger().info(
            f"  Slot {slot}: ArUco-FK (IK failed) "
            f"j1 corrected to {j1_aruco:.3f}")
        return corrected, "ArUco-FK"

    def _hover_joints(self, pick: List[float]) -> List[float]:
        """Same j1, same j2, j3 less negative → 14 cm higher."""
        return [pick[0], pick[1], pick[2] + 0.17]

    # ── trajectory publishing ─────────────────────────────────────────────────

    def _send_arm(self, joints: List[float], dur: float):
        msg = JointTrajectory()
        msg.joint_names = ["joint_1", "joint_2", "joint_3"]
        pt  = JointTrajectoryPoint()
        pt.positions  = [float(j) for j in joints]
        pt.velocities = [0.0, 0.0, 0.0]
        s = int(dur); ns = int((dur - s) * 1e9)
        pt.time_from_start = DurationMsg(sec=s, nanosec=ns)
        msg.points = [pt]
        self.arm_pub.publish(msg)
        self.get_logger().info(
            f"  → arm [{joints[0]:.3f},{joints[1]:.3f},{joints[2]:.3f}] {dur:.1f}s")

    def _send_grip(self, j4: float, dur: float):
        msg = JointTrajectory()
        msg.joint_names = ["joint_4"]
        pt  = JointTrajectoryPoint()
        pt.positions  = [float(j4)]
        pt.velocities = [0.0]
        s = int(dur); ns = int((dur - s) * 1e9)
        pt.time_from_start = DurationMsg(sec=s, nanosec=ns)
        msg.points = [pt]
        self.grip_pub.publish(msg)
        self.get_logger().info(f"  → grip [{j4:.3f}] {dur:.1f}s")

    def _wait_arm(self, target: List[float], label: str) -> bool:
        deadline = time.time() + GOAL_TIMEOUT
        while time.time() < deadline:
            actual = self._arm_now()
            err    = max(abs(actual[i] - target[i]) for i in range(3))
            if err < GOAL_TOL:
                self.get_logger().info(f"  ✔ {label}  err={err:.3f}rad")
                return True
            time.sleep(0.05)
        self.get_logger().warn(f"  ⚠ Timeout '{label}' — continuing")
        return True

    def _wait_grip(self, j4: float, timeout: float = 8.0):
        deadline = time.time() + timeout
        while time.time() < deadline:
            if abs(self._gripper_now() - j4) < 0.06:
                return
            time.sleep(0.05)

    def _move(self, joints: List[float], label: str, dur: float = MOVE_SLOW):
        self.get_logger().info(f"Step: {label}")
        self._send_arm(joints, dur)
        self._wait_arm(joints, label)

    def _grip(self, close: bool):
        j4 = GRIPPER_CLOSED[0] if close else GRIPPER_OPEN[0]
        self._send_grip(j4, GRIPPER_DUR)
        self._wait_grip(j4)
        time.sleep(0.2)

    # ── pick-and-place sequence ───────────────────────────────────────────────

    def _dispatch_sequence(self, slot: int, item_name: str) -> bool:
        pick, src = self._pick_joints(slot)
        hover     = self._hover_joints(pick)

        self.get_logger().info(
            f"\n{'='*60}\n"
            f"  DISPATCH  slot={slot}  item='{item_name}'  mode={src}\n"
            f"  hover = {[round(v,3) for v in hover]}\n"
            f"  pick  = {[round(v,3) for v in pick]}\n"
            f"{'='*60}"
        )

        try:
            self._grip(close=False)
            self._move(HOME,  "home",              MOVE_SLOW)
            self._move(hover, f"hover S{slot}",    MOVE_SLOW)
            self._move(pick,  f"descend S{slot}",  MOVE_SLOW)

            self.get_logger().info(f"  Gripping '{item_name}'")
            self._grip(close=True)
            time.sleep(PICK_DWELL)

            self._move(hover,      f"lift S{slot}",     MOVE_FAST)
            self._move(DROP_HOVER, "transit to tray",   MOVE_SLOW)
            self._move(DROP_PLACE, "place at tray",     MOVE_FAST)

            self.get_logger().info("  Releasing")
            self._grip(close=False)
            time.sleep(DROP_DWELL)

            self._move(DROP_HOVER, "retract from tray", MOVE_FAST)
            self._move(HOME,       "return home",       MOVE_SLOW)

            self.get_logger().info("=== Dispatch complete ===")
            return True

        except Exception as exc:
            self.get_logger().error(f"Sequence error: {exc}")
            import traceback
            self.get_logger().error(traceback.format_exc())
            try:
                self._send_grip(GRIPPER_OPEN[0], GRIPPER_DUR)
                time.sleep(1.5)
                self._send_arm(HOME, MOVE_SLOW)
            except Exception:
                pass
            return False

    # ── services ──────────────────────────────────────────────────────────────

    def _dispatch_cb(self, req: Any, res: Any) -> Any:
        mode = (req.mode or "FIFO").upper()
        self.get_logger().info(f"Dispatch request mode={mode}")

        ok, msg, info = dispatch(mode)
        if not ok or info is None:
            res.success, res.message = False, msg
            return res

        res.item_name   = str(info.get("item_name", ""))
        res.item_id     = str(info.get("item_id",   ""))
        res.slot_number = int(info.get("slot",      -1))
        res.expiry_date = format_expiry(info.get("expiry_ts"))

        slot = info["slot"]; item_name = info.get("item_name", f"item@{slot}")

        if self._dispatch_sequence(slot, item_name):
            mark_dispatched(info["item_id"], mode)
            is_low, count = check_low_stock()
            res.success = True
            res.message = (f"Dispatched '{item_name}' slot {slot} ({mode})."
                           + (f" LOW STOCK: {count} left!" if is_low else ""))
        else:
            res.success = False
            res.message = "Motion sequence failed."

        self.get_logger().info(res.message)
        return res

    def _add_item_cb(self, req: Any, res: Any) -> Any:
        try:
            expiry_ts   = float(req.expiry_ts) if req.expiry_ts else None
            res.item_id = add_item(req.item_name, req.slot, expiry_ts)
            res.success = True
            res.message = f"Added '{req.item_name}' to slot {req.slot}"
        except ValueError as e:
            res.success, res.message = False, str(e)
        self.get_logger().info(res.message)
        return res

    # ── stock publisher ───────────────────────────────────────────────────────

    def _pub_stock_cb(self):
        stock = get_stock(); log = get_dispatch_log(10)
        msg   = String()
        msg.data = json.dumps({
            "timestamp":      time.time(),
            "stock_count":    stock_count(),
            "low_stock":      check_low_stock()[0],
            "aruco_active":   self._aruco_fresh(),
            "detected_slots": [s for s, d in self._slot_data.items()
                               if d.get("detected")],
            "arm_now":        self._arm_now(),
            "items": [{"id": r["id"], "name": r["name"], "slot": r["slot"],
                       "arrival_ts": r["arrival_ts"],
                       "expiry": format_expiry(r["expiry_ts"]),
                       "expiry_ts": r["expiry_ts"]} for r in stock],
            "dispatch_log": [{"item_name": r["item_name"], "mode": r["mode"],
                              "slot": r["slot"], "ts": r["ts"]} for r in log],
        })
        self.stock_pub.publish(msg)


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    rclpy.init()
    node = InventoryNode()
    executor = MultiThreadedExecutor(num_threads=4)
    executor.add_node(node)
    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        executor.shutdown()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
