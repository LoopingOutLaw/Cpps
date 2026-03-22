#!/usr/bin/env python3
"""
inventory_node.py  —  Direct Trajectory Pick-and-Place  (no MoveIt)
====================================================================
Receives  /inventory/dispatch  (DispatchItem.srv) from the web interface.
Reads     /inventory/box_poses (String/JSON from aruco_box_detector)
          /joint_states        (sensor_msgs/JointState)
Publishes /arm_controller/joint_trajectory
          /gripper_controller/joint_trajectory
          /inventory/stock_state  (String/JSON dashboard feed)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
IK VERIFICATION  (URDF arm, L0=0.657 L1=0.80 L2=0.82 m)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
z   = L0 + L1*cos(j2)      + L2*cos(j2+j3)
r   = L1*sin(j2)            + L2*sin(j2+j3)   (radial reach, -ve = toward shelf)

All 4 shelf slots have the same radial distance r=1.229 m,
so j2 and j3 are IDENTICAL across all slots — only j1 (yaw) changes.

Pick  (z=1.216 m):  j2=-0.5502  j3=-1.1711
  z = 0.657 + 0.80*cos(-0.55) + 0.82*cos(-1.72) = 1.216 m  ✓
  r = 0.80*sin(-0.55) + 0.82*sin(-1.72)           = -1.229 m ✓ (magnitude)

Hover (z≈1.36 m, ~15 cm above pick):  j2=-0.55  j3=-1.00
  z = 0.657 + 0.80*cos(-0.55) + 0.82*cos(-1.55) = 1.355 m  ✓

Drop tray at world (0.664, 1.034, ~1.15 m):
  j1_drop = atan2(1.034, 0.664) ≈ 1.01 rad
  r_drop  = sqrt(0.664²+1.034²) ≈ 1.229 m  (SAME as shelf slots!)
  → j2/j3 unchanged, only j1 changes to reach the tray

Joint table:
         j1        j2       j3      world (x, y) m
Slot 0  -0.5496  -0.5502  -1.1711  (1.048, -0.642)
Slot 1  -0.1800  -0.5500  -1.1714  (1.209, -0.220)
Slot 2  +0.1800  -0.5500  -1.1714  (1.209, +0.220)
Slot 3  +0.5496  -0.5502  -1.1711  (1.048, +0.642)
Drop    +1.0122  -0.5502  -1.1711  (0.664,  1.034)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
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
    from dexter_msgs.srv import DispatchItem, AddItem  # type: ignore[import]
except ImportError as e:
    raise ImportError(
        "dexter_msgs not found — run: colcon build && source install/setup.bash"
    ) from e

from dexter_inventory.inventory_db import (
    init_db, add_item, mark_dispatched, get_stock, get_dispatch_log, stock_count,
)
from dexter_inventory.dispatch_engine import (
    dispatch, check_low_stock, format_expiry,
)


# ── Motion parameters ──────────────────────────────────────────────────────────

GOAL_TOL     = 0.07   # rad – "close enough" per joint
GOAL_TIMEOUT = 45.0   # s   – max wait per motion step

MOVE_SLOW   = 4.5     # s   – careful approach/depart
MOVE_FAST   = 3.0     # s   – transit moves
GRIPPER_DUR = 1.2     # s
PICK_DWELL  = 2.0     # s   – hold grip after closing
DROP_DWELL  = 1.0     # s   – hold after releasing

ARUCO_MAX_AGE = 8.0   # s

# ── IK-VERIFIED joint positions ────────────────────────────────────────────────
#
#  j2 and j3 are BOTH NEGATIVE:
#    +j2 tilts the arm UPWARD (wrong direction, old error)
#    -j2 tilts the arm toward the shelf (correct)
#    -j3 folds the elbow to achieve correct height
#
#  z = 0.657 + 0.80*cos(j2) + 0.82*cos(j2+j3)
#  At j2=-0.55, j3=-1.17:  z = 0.657+0.682-0.123 = 1.216 m  ← box height
#  At j2=-0.55, j3=-1.00:  z = 0.657+0.682+0.016 = 1.355 m  ← hover height

SLOT_PICK: Dict[int, List[float]] = {
    0: [-0.5496, -0.5502, -1.1711],   # (1.048, -0.642) m  z=1.216
    1: [-0.1800, -0.5500, -1.1714],   # (1.209, -0.220) m  z=1.216
    2: [ 0.1800, -0.5500, -1.1714],   # (1.209, +0.220) m  z=1.216
    3: [ 0.5496, -0.5502, -1.1711],   # (1.048, +0.642) m  z=1.216
}

# Hover ≈ 14 cm above pick (same j1 and j2, j3 less negative)
SLOT_HOVER: Dict[int, List[float]] = {
    0: [-0.5496, -0.5502, -1.0000],   # z≈1.355 m
    1: [-0.1800, -0.5500, -1.0000],
    2: [ 0.1800, -0.5500, -1.0000],
    3: [ 0.5496, -0.5502, -1.0000],
}

HOME = [0.00, 0.00, 0.00]   # arm pointing straight up, safe park

# Dispatch tray: world (0.664, 1.034) → j1=1.01, same r=1.229 m as shelf
DROP_HOVER = [1.0122, -0.5502, -1.0000]   # z≈1.355 m above tray
DROP_PLACE = [1.0122, -0.5502, -1.1711]   # z≈1.216 m at tray level

GRIPPER_OPEN   = [0.0]
GRIPPER_CLOSED = [-0.7]


# ── InventoryNode ──────────────────────────────────────────────────────────────

class InventoryNode(Node):

    def __init__(self):
        super().__init__("inventory_node")
        init_db()
        self.get_logger().info("Inventory database initialised")

        # Trajectory publishers
        self.arm_pub = self.create_publisher(
            JointTrajectory, "/arm_controller/joint_trajectory", 10)
        self.grip_pub = self.create_publisher(
            JointTrajectory, "/gripper_controller/joint_trajectory", 10)

        # Joint state tracking
        self._jpos: Dict[str, float] = {
            "joint_1": 0.0, "joint_2": 0.0,
            "joint_3": 0.0, "joint_4": 0.0,
        }
        self._jlock = threading.Lock()

        # ArUco pose data
        self._detected: Dict[int, dict] = {}
        self._aruco_ts: float = 0.0

        cb = ReentrantCallbackGroup()

        self.create_subscription(
            JointState, "/joint_states",
            self._js_cb, 10, callback_group=cb)
        self.create_subscription(
            String, "/inventory/box_poses",
            self._aruco_cb, 10, callback_group=cb)

        self.create_service(
            DispatchItem, "inventory/dispatch",
            self._dispatch_cb, callback_group=cb)
        self.create_service(
            AddItem, "inventory/add_item",
            self._add_item_cb, callback_group=cb)

        self.stock_pub = self.create_publisher(
            String, "inventory/stock_state", 10)
        self.create_timer(1.0, self._pub_stock_cb)

        self.get_logger().info(
            "\n"
            "  InventoryNode ready — IK-verified joint values\n"
            "  z=L0+L1*cos(j2)+L2*cos(j2+j3):\n"
            "  PICK  j2=-0.55 j3=-1.17 → z=1.216 m (box height)\n"
            "  HOVER j2=-0.55 j3=-1.00 → z=1.355 m (14 cm above)\n"
            "  DROP  j1=1.01  j2=-0.55 j3=-1.17 → tray"
        )

    # ── Joint state ──────────────────────────────────────────────────────────

    def _js_cb(self, msg: JointState):
        with self._jlock:
            for name, pos in zip(msg.name, msg.position):
                if name in self._jpos:
                    self._jpos[name] = float(pos)

    def _arm_now(self) -> List[float]:
        with self._jlock:
            return [self._jpos.get(f"joint_{i}", 0.0) for i in range(1, 4)]

    def _gripper_now(self) -> float:
        with self._jlock:
            return self._jpos.get("joint_4", 0.0)

    # ── ArUco ────────────────────────────────────────────────────────────────

    def _aruco_cb(self, msg: String):
        try:
            data = json.loads(msg.data)
            for s, info in data.items():
                if info.get("detected"):
                    self._detected[int(s)] = info
                else:
                    self._detected.pop(int(s), None)
            self._aruco_ts = time.time()
        except Exception as e:
            self.get_logger().warn(f"aruco_cb: {e}")

    def _aruco_ok(self) -> bool:
        return (time.time() - self._aruco_ts) < ARUCO_MAX_AGE

    # ── IK refinement (optional, corrected seed) ─────────────────────────────

    @staticmethod
    def _ik(x: float, y: float, z: float) -> Optional[List[float]]:
        """
        2-link IK for the planar arm after joint_1 rotation.
        z   = L0 + L1*cos(j2)    + L2*cos(j2+j3)
        r   = L1*sin(j2)          + L2*sin(j2+j3)   (negative = toward shelf)
        """
        try:
            from scipy.optimize import fsolve  # type: ignore[import]
        except ImportError:
            return None

        j1 = math.atan2(y, x)
        r  = math.hypot(x, y)   # positive radial distance
        L0, L1, L2 = 0.657, 0.80, 0.82

        def residual(jv):
            j2, j3 = jv
            # Note: formula uses -r because reach is "negative" in this arm
            return [
                L1 * math.sin(j2) + L2 * math.sin(j2 + j3) + r,   # reaches -r
                L0 + L1 * math.cos(j2) + L2 * math.cos(j2 + j3) - z,
            ]

        try:
            # Seed from the correct elbow-down configuration
            sol, _, ier, _ = fsolve(residual, [-0.55, -1.17], full_output=True)
            if ier != 1:
                return None
            j2, j3 = sol
            if max(abs(v) for v in residual([j2, j3])) > 0.05:
                return None
            lim = math.pi / 2
            if not (-lim <= j2 <= 0 and -lim * 2 <= j3 <= 0):
                return None
            return [float(j1), float(j2), float(j3)]
        except Exception:
            return None

    # ── Slot joint positions ─────────────────────────────────────────────────

    def _pick_joints(self, slot: int) -> List[float]:
        fb = SLOT_PICK[slot]
        if slot not in self._detected or not self._aruco_ok():
            return fb
        p  = self._detected[slot]
        ik = self._ik(p["x"], p["y"], p["z"])
        if ik:
            self.get_logger().info(
                f"  Slot {slot}: ArUco IK → {[round(v,3) for v in ik]}")
            return ik
        return fb

    def _hover_joints(self, slot: int, pick: List[float]) -> List[float]:
        fb = SLOT_HOVER[slot]
        if slot not in self._detected or not self._aruco_ok():
            return fb
        p  = self._detected[slot]
        ik = self._ik(p["x"], p["y"], p["z"] + 0.14)
        return ik if ik else [pick[0], fb[1], fb[2]]

    # ── Trajectory publishing ─────────────────────────────────────────────────

    def _send_arm(self, joints: List[float], duration_s: float):
        msg = JointTrajectory()
        msg.joint_names = ["joint_1", "joint_2", "joint_3"]
        pt  = JointTrajectoryPoint()
        pt.positions  = [float(j) for j in joints]
        pt.velocities = [0.0, 0.0, 0.0]
        secs  = int(duration_s)
        nsecs = int((duration_s - secs) * 1e9)
        pt.time_from_start = DurationMsg(sec=secs, nanosec=nsecs)
        msg.points = [pt]
        self.arm_pub.publish(msg)
        self.get_logger().info(
            f"  → arm {[round(j,3) for j in joints]}  ({duration_s:.1f}s)")

    def _send_gripper(self, j4: float, duration_s: float):
        msg = JointTrajectory()
        msg.joint_names = ["joint_4"]
        pt  = JointTrajectoryPoint()
        pt.positions  = [float(j4)]
        pt.velocities = [0.0]
        secs  = int(duration_s)
        nsecs = int((duration_s - secs) * 1e9)
        pt.time_from_start = DurationMsg(sec=secs, nanosec=nsecs)
        msg.points = [pt]
        self.grip_pub.publish(msg)
        self.get_logger().info(f"  → gripper [{j4:.3f}]  ({duration_s:.1f}s)")

    def _wait_arm(self, target: List[float], label: str) -> bool:
        deadline = time.time() + GOAL_TIMEOUT
        while time.time() < deadline:
            actual = self._arm_now()
            err    = max(abs(actual[i] - target[i]) for i in range(3))
            if err < GOAL_TOL:
                self.get_logger().info(f"  ✔ {label}  err={err:.3f} rad")
                return True
            time.sleep(0.05)
        self.get_logger().warn(f"  ⚠ Timeout '{label}' — continuing")
        return True

    def _wait_gripper(self, target: float, timeout: float = 8.0):
        deadline = time.time() + timeout
        while time.time() < deadline:
            if abs(self._gripper_now() - target) < 0.06:
                return
            time.sleep(0.05)

    def _move(self, joints: List[float], label: str, dur: float = MOVE_SLOW):
        self.get_logger().info(f"Step: {label}")
        self._send_arm(joints, dur)
        self._wait_arm(joints, label)

    def _grip(self, close: bool):
        j4 = GRIPPER_CLOSED[0] if close else GRIPPER_OPEN[0]
        self._send_gripper(j4, GRIPPER_DUR)
        self._wait_gripper(j4)
        time.sleep(0.2)

    # ── Pick-and-place sequence ───────────────────────────────────────────────

    def _dispatch_sequence(self, slot: int, item_name: str) -> bool:
        pick  = self._pick_joints(slot)
        hover = self._hover_joints(slot, pick)
        src   = ("ArUco" if slot in self._detected and self._aruco_ok()
                 else "FK table")

        self.get_logger().info(
            f"\n{'='*60}\n"
            f"  DISPATCH  slot={slot}  item='{item_name}'  src={src}\n"
            f"  pick  = {[round(v,3) for v in pick]}  (z≈1.216 m)\n"
            f"  hover = {[round(v,3) for v in hover]}  (z≈1.355 m)\n"
            f"{'='*60}"
        )

        try:
            # 1. Open gripper, go home
            self._grip(close=False)
            self._move(HOME,  "home position",          MOVE_SLOW)

            # 2. Hover above target slot
            self._move(hover, f"hover slot {slot}",     MOVE_SLOW)

            # 3. Descend to pick
            self._move(pick,  f"descend slot {slot}",   MOVE_SLOW)

            # 4. Grip
            self.get_logger().info(f"  Gripping '{item_name}'")
            self._grip(close=True)
            time.sleep(PICK_DWELL)

            # 5. Lift to hover
            self._move(hover, f"lift slot {slot}",      MOVE_FAST)

            # 6. Transit to drop-zone hover
            self._move(DROP_HOVER, "transit to tray",   MOVE_SLOW)

            # 7. Descend to tray
            self._move(DROP_PLACE, "place at tray",     MOVE_FAST)

            # 8. Release
            self.get_logger().info("  Releasing item")
            self._grip(close=False)
            time.sleep(DROP_DWELL)

            # 9. Retract and home
            self._move(DROP_HOVER, "retract from tray", MOVE_FAST)
            self._move(HOME,       "return to home",    MOVE_SLOW)

            self.get_logger().info("=== Dispatch complete ===")
            return True

        except Exception as exc:
            self.get_logger().error(f"Sequence error: {exc}")
            import traceback
            self.get_logger().error(traceback.format_exc())
            try:
                self._send_gripper(GRIPPER_OPEN[0], GRIPPER_DUR)
                time.sleep(1.5)
                self._send_arm(HOME, MOVE_SLOW)
            except Exception:
                pass
            return False

    # ── Service: dispatch ────────────────────────────────────────────────────

    def _dispatch_cb(self, req: Any, res: Any) -> Any:
        mode = (req.mode or "FIFO").upper()
        self.get_logger().info(f"Dispatch request — mode={mode}")

        ok, msg, info = dispatch(mode)
        if not ok or info is None:
            res.success, res.message = False, msg
            return res

        self.get_logger().info(msg)
        res.item_name   = str(info.get("item_name", ""))
        res.item_id     = str(info.get("item_id",   ""))
        res.slot_number = int(info.get("slot",      -1))
        res.expiry_date = format_expiry(info.get("expiry_ts"))

        slot      = info["slot"]
        item_name = info.get("item_name", f"item@slot{slot}")

        if self._dispatch_sequence(slot, item_name):
            mark_dispatched(info["item_id"], mode)
            is_low, count = check_low_stock()
            res.success = True
            res.message = (
                f"Dispatched '{item_name}' from slot {slot} ({mode})."
                + (f"  LOW STOCK: {count} item(s) left!" if is_low else "")
            )
        else:
            res.success = False
            res.message = "Motion sequence failed — item NOT dispatched."

        self.get_logger().info(res.message)
        return res

    # ── Service: add item ────────────────────────────────────────────────────

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

    # ── Stock publisher ──────────────────────────────────────────────────────

    def _pub_stock_cb(self):
        stock = get_stock()
        log   = get_dispatch_log(10)
        msg   = String()
        msg.data = json.dumps({
            "timestamp":      time.time(),
            "stock_count":    stock_count(),
            "low_stock":      check_low_stock()[0],
            "aruco_active":   self._aruco_ok(),
            "detected_slots": list(self._detected.keys()),
            "arm_now":        self._arm_now(),
            "items": [
                {
                    "id":         r["id"],
                    "name":       r["name"],
                    "slot":       r["slot"],
                    "arrival_ts": r["arrival_ts"],
                    "expiry":     format_expiry(r["expiry_ts"]),
                    "expiry_ts":  r["expiry_ts"],
                }
                for r in stock
            ],
            "dispatch_log": [
                {
                    "item_name": r["item_name"],
                    "mode":      r["mode"],
                    "slot":      r["slot"],
                    "ts":        r["ts"],
                }
                for r in log
            ],
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
