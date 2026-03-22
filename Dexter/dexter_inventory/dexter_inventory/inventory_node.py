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

Pick-and-place sequence per slot
---------------------------------
Step 1  Open gripper at HOME
Step 2  Move to HOVER above slot  (safe height)
Step 3  Descend to PICK position
Step 4  Close gripper + dwell
Step 5  Lift back to HOVER
Step 6  Transit to DROP ZONE HOVER
Step 7  Descend to DROP ZONE PLACE
Step 8  Open gripper + dwell
Step 9  Lift from drop zone
Step 10 Return to HOME

Joint positions
---------------
HOME            [0.00,  0.00,  0.00]
SLOT_PICK[s]    joint angles that position TCP above box centre
SLOT_HOVER[s]   same j1, raised j2/j3
DROP_HOVER      over dispatch tray
DROP_PLACE      tray level
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


# ── Motion parameters ─────────────────────────────────────────────────────────

GOAL_TOL     = 0.07    # rad – "close enough" threshold
GOAL_TIMEOUT = 35.0    # s   – max wait per move step

MOVE_SLOW    = 3.5     # s   – slow moves (home → hover, hover → pick)
MOVE_FAST    = 2.5     # s   – fast moves (retract, transit)
GRIPPER_DUR  = 1.0     # s   – gripper open / close
PICK_DWELL   = 1.8     # s   – hold grip after closing
DROP_DWELL   = 1.0     # s   – hold position after releasing

ARUCO_MAX_AGE = 8.0    # s   – ignore ArUco data older than this

# ── Arm joint positions (radians) ────────────────────────────────────────────
#
#  FK-verified against pedestal positions:
#    Slot 0  (1.048, -0.642) m  →  j1=-0.55  j2=-0.55  j3=-0.15
#    Slot 1  (1.209, -0.220) m  →  j1=-0.18  j2=-0.55  j3=-0.15
#    Slot 2  (1.209, +0.220) m  →  j1=+0.18  j2=-0.55  j3=-0.15
#    Slot 3  (1.048, +0.642) m  →  j1=+0.55  j2=-0.55  j3=-0.15

SLOT_PICK: Dict[int, List[float]] = {
    0: [-0.55, -0.55, -0.15],
    1: [-0.18, -0.55, -0.15],
    2: [ 0.18, -0.55, -0.15],
    3: [ 0.55, -0.55, -0.15],
}

SLOT_HOVER: Dict[int, List[float]] = {
    0: [-0.55, -0.35, -0.05],
    1: [-0.18, -0.35, -0.05],
    2: [ 0.18, -0.35, -0.05],
    3: [ 0.55, -0.35, -0.05],
}

HOME       = [0.00,  0.00,  0.00]
DROP_HOVER = [1.00, -0.35, -0.05]   # hover above dispatch tray
DROP_PLACE = [1.00, -0.55, -0.15]   # descend to tray level

GRIPPER_OPEN   = [0.0]
GRIPPER_CLOSED = [-0.7]


# ── InventoryNode ─────────────────────────────────────────────────────────────

class InventoryNode(Node):

    def __init__(self):
        super().__init__("inventory_node")
        init_db()
        self.get_logger().info("Inventory database initialised")

        # ── Trajectory publishers ─────────────────────────────────────────
        self.arm_pub = self.create_publisher(
            JointTrajectory, "/arm_controller/joint_trajectory", 10)
        self.grip_pub = self.create_publisher(
            JointTrajectory, "/gripper_controller/joint_trajectory", 10)

        # ── Joint state tracking ──────────────────────────────────────────
        self._jpos: Dict[str, float] = {
            "joint_1": 0.0, "joint_2": 0.0,
            "joint_3": 0.0, "joint_4": 0.0,
        }
        self._jlock = threading.Lock()

        # ── ArUco pose data ───────────────────────────────────────────────
        self._detected: Dict[int, dict] = {}
        self._aruco_ts: float = 0.0

        # ── Callback group (allow concurrent sub + service) ───────────────
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
            "InventoryNode ready — direct trajectory publisher (no MoveIt).")

    # ── Joint state ───────────────────────────────────────────────────────

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

    # ── ArUco ─────────────────────────────────────────────────────────────

    def _aruco_cb(self, msg: String):
        try:
            data = json.loads(msg.data)
            for s, info in data.items():
                if info.get("detected"):
                    self._detected[int(s)] = info
                else:
                    # Remove stale detection
                    self._detected.pop(int(s), None)
            self._aruco_ts = time.time()
        except Exception as e:
            self.get_logger().warn(f"aruco_cb error: {e}")

    def _aruco_ok(self) -> bool:
        return (time.time() - self._aruco_ts) < ARUCO_MAX_AGE

    # ── Optional IK refinement ────────────────────────────────────────────

    @staticmethod
    def _ik(x: float, y: float, z: float) -> Optional[List[float]]:
        """
        Analytic-style IK for 3-DOF planar arm.
        Returns [j1, j2, j3] (rad) or None if unreachable.
        L0=0.657 m (base height), L1=0.80 m, L2=0.82 m.
        """
        try:
            from scipy.optimize import fsolve  # type: ignore[import]
        except ImportError:
            return None
        j1 = math.atan2(y, x)
        r  = math.hypot(x, y)
        L0, L1, L2 = 0.657, 0.80, 0.82

        def residual(jv: List[float]) -> List[float]:
            j2, j3 = jv
            return [
                L1 * math.sin(j2) + L2 * math.sin(j2 + j3) - r,
                L0 + L1 * math.cos(j2) + L2 * math.cos(j2 + j3) - z,
            ]

        try:
            sol, _, ier, _ = fsolve(residual, [-0.55, -0.15],
                                    full_output=True)
            if ier != 1:
                return None
            j2, j3 = sol
            if max(abs(residual([j2, j3]))) > 0.04:
                return None
            lim = math.pi / 2
            if not (-lim <= j2 <= lim and -lim <= j3 <= lim):
                return None
            return [float(j1), float(j2), float(j3)]
        except Exception:
            return None

    # ── Slot positions (with optional ArUco IK refinement) ───────────────

    def _pick_joints(self, slot: int) -> List[float]:
        """Return pick joints, refined by ArUco if available."""
        fb = SLOT_PICK[slot]
        if slot not in self._detected or not self._aruco_ok():
            return fb
        p  = self._detected[slot]
        ik = self._ik(p["x"], p["y"], p["z"])
        if ik:
            self.get_logger().info(
                f"  Slot {slot}: ArUco IK → [{ik[0]:.3f}, {ik[1]:.3f}, {ik[2]:.3f}]")
            return ik
        return fb

    def _hover_joints(self, slot: int, pick: List[float]) -> List[float]:
        """Return hover joints, ArUco-adjusted if possible."""
        fb = SLOT_HOVER[slot]
        if slot not in self._detected or not self._aruco_ok():
            return fb
        p  = self._detected[slot]
        ik = self._ik(p["x"], p["y"], p["z"] + 0.15)
        return ik if ik else [pick[0], fb[1], fb[2]]

    # ── Trajectory publishing ─────────────────────────────────────────────

    def _send_arm(self, joints: List[float], duration_s: float):
        """Publish one arm trajectory point."""
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
            f"  → arm [{joints[0]:.3f}, {joints[1]:.3f}, {joints[2]:.3f}]  "
            f"dur={duration_s:.1f}s")

    def _send_gripper(self, j4: float, duration_s: float):
        """Publish one gripper trajectory point."""
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
        self.get_logger().info(f"  → gripper [{j4:.3f}]  dur={duration_s:.1f}s")

    # ── Wait for arm ──────────────────────────────────────────────────────

    def _wait_arm(self, target: List[float], label: str) -> bool:
        """Block until arm reaches target (within GOAL_TOL) or timeout."""
        deadline = time.time() + GOAL_TIMEOUT
        while time.time() < deadline:
            actual = self._arm_now()
            err    = max(abs(actual[i] - target[i]) for i in range(3))
            if err < GOAL_TOL:
                self.get_logger().info(f"  ✔ {label}  (err={err:.3f} rad)")
                return True
            time.sleep(0.05)
        self.get_logger().warn(
            f"  ⚠ Timeout on '{label}'. "
            f"target={[round(v,3) for v in target]}  "
            f"actual={[round(v,3) for v in self._arm_now()]}")
        return True   # continue anyway — partial motion is still progress

    def _wait_gripper(self, target_j4: float, timeout: float = 6.0):
        deadline = time.time() + timeout
        while time.time() < deadline:
            if abs(self._gripper_now() - target_j4) < 0.06:
                return
            time.sleep(0.05)

    # ── High-level move helpers ───────────────────────────────────────────

    def _move(self, joints: List[float], label: str,
              duration_s: float = MOVE_SLOW):
        self.get_logger().info(f"Step: {label}")
        self._send_arm(joints, duration_s)
        self._wait_arm(joints, label)

    def _grip(self, close: bool):
        """Open (close=False) or close (close=True) the gripper."""
        j4 = GRIPPER_CLOSED[0] if close else GRIPPER_OPEN[0]
        self._send_gripper(j4, GRIPPER_DUR)
        self._wait_gripper(j4)
        time.sleep(0.15)

    # ── Full pick-and-place ───────────────────────────────────────────────

    def _dispatch_sequence(self, slot: int, item_name: str) -> bool:
        """
        Execute the 10-step pick-and-place sequence.
        Returns True on success (including partial completion).
        """
        pick  = self._pick_joints(slot)
        hover = self._hover_joints(slot, pick)
        src   = ("ArUco" if slot in self._detected and self._aruco_ok()
                 else "FK table")

        self.get_logger().info(
            f"\n{'='*55}\n"
            f"  DISPATCH: slot {slot}  item='{item_name}'  src={src}\n"
            f"  pick  = {[round(v,3) for v in pick]}\n"
            f"  hover = {[round(v,3) for v in hover]}\n"
            f"{'='*55}"
        )

        try:
            # 1. Open gripper first
            self._grip(close=False)

            # 2. Go home (safe start position)
            self._move(HOME, "home position", MOVE_SLOW)

            # 3. Rotate base + hover above slot
            self._move(hover, f"hover above slot {slot}", MOVE_SLOW)

            # 4. Descend to pick position
            self._move(pick, f"descend to slot {slot}", MOVE_SLOW)

            # 5. Close gripper – grab
            self.get_logger().info(f"  Gripping '{item_name}' at slot {slot}")
            self._grip(close=True)
            time.sleep(PICK_DWELL)

            # 6. Lift back to hover
            self._move(hover, f"lift from slot {slot}", MOVE_FAST)

            # 7. Transit to drop zone hover
            self._move(DROP_HOVER, "transit to drop zone", MOVE_SLOW)

            # 8. Descend to drop position
            self._move(DROP_PLACE, "place at dispatch tray", MOVE_FAST)

            # 9. Release
            self.get_logger().info("  Releasing item")
            self._grip(close=False)
            time.sleep(DROP_DWELL)

            # 10. Lift & return home
            self._move(DROP_HOVER, "retract from tray",    MOVE_FAST)
            self._move(HOME,       "return to home",        MOVE_SLOW)

            self.get_logger().info("=== Dispatch sequence complete ===")
            return True

        except Exception as exc:
            self.get_logger().error(f"Sequence error: {exc}")
            import traceback
            self.get_logger().error(traceback.format_exc())
            # Best-effort recovery
            try:
                self._send_gripper(GRIPPER_OPEN[0], GRIPPER_DUR)
                time.sleep(1.0)
                self._send_arm(HOME, MOVE_SLOW)
            except Exception:
                pass
            return False

    # ── Service: dispatch ─────────────────────────────────────────────────

    def _dispatch_cb(self, req: Any, res: Any) -> Any:
        mode = (req.mode or "FIFO").upper()
        self.get_logger().info(f"Dispatch request — mode={mode}")

        ok, msg, info = dispatch(mode)
        if not ok or info is None:
            res.success, res.message = False, msg
            self.get_logger().warn(msg)
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

    # ── Service: add item ─────────────────────────────────────────────────

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

    # ── Stock publisher ───────────────────────────────────────────────────

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
    # MultiThreadedExecutor: dispatch service can block on _wait_arm()
    # while joint_state / aruco subscriptions run on separate threads.
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
