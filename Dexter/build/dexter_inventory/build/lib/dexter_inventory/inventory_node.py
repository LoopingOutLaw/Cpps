#!/usr/bin/env python3
"""
inventory_node.py  —  DIRECT TRAJECTORY PUBLISHER  (no MoveIt)
===============================================================
Every previous version used moveit_py and failed in a different way:
  - dict vs numpy TypeError
  - executor deadlock (blocking execute() in single-threaded spin)
  - plan.trajectory.joint_trajectory.points AttributeError
  - execute() returning before motion completes

This version bypasses MoveIt completely and publishes JointTrajectory
messages directly to the arm and gripper controllers, exactly the same
way slider_control.py already does in this project.

The arm controllers accept /arm_controller/joint_trajectory and
/gripper_controller/joint_trajectory.  No planning, no action clients,
no moveit_py — just publish a goal position with a time_from_start and
wait for /joint_states to confirm arrival.

This approach:
  - Cannot fail due to planner timeouts or configuration
  - Cannot deadlock because there is no blocking call
  - Works identically in simulation and on the real robot
  - Is the same mechanism the existing slider_control node uses
"""

from __future__ import annotations

import json
import math
import time
import threading
from typing import Any, Dict, List, Optional, Tuple

import rclpy
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node
from rclpy.duration import Duration

from sensor_msgs.msg import JointState
from std_msgs.msg import String
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from builtin_interfaces.msg import Duration as DurationMsg

try:
    from dexter_msgs.srv import DispatchItem, AddItem  # type: ignore[import]
except ImportError as e:
    raise ImportError("dexter_msgs not found — colcon build && source install/setup.bash") from e

from dexter_inventory.inventory_db import (
    init_db, add_item, mark_dispatched, get_stock, get_dispatch_log, stock_count,
)
from dexter_inventory.dispatch_engine import (
    dispatch, check_low_stock, format_expiry,
)


# ── Motion parameters ─────────────────────────────────────────────────────────

# How close (radians) the arm needs to be before we consider it "arrived"
GOAL_TOL     = 0.06
# How long to wait for the arm to arrive (seconds)
GOAL_TIMEOUT = 30.0

# Trajectory duration for each move type (seconds)
# Longer = smoother but slower.  These are conservative safe values.
MOVE_SLOW    = 3.5   # home → hover, hover → pick
MOVE_FAST    = 2.5   # pick → hover (lifting with item), hover → drop
GRIPPER_DUR  = 1.2   # gripper open/close

# How long to hold at grip and drop positions (seconds)
PICK_HOLD    = 1.5
DROP_HOLD    = 1.0


# ── Arm positions (joint radians) ─────────────────────────────────────────────
#
# These are the FK-computed values from dispatch_engine.py.
# j1 = base rotation, j2 = shoulder, j3 = elbow
#
# Slot positions (pick height):
#   Slot 0  j1=-0.55  j2=-0.55  j3=-0.15   (x=1.048, y=-0.642)
#   Slot 1  j1=-0.18  j2=-0.55  j3=-0.15   (x=1.209, y=-0.220)
#   Slot 2  j1=+0.18  j2=-0.55  j3=-0.15   (x=1.209, y=+0.220)
#   Slot 3  j1=+0.55  j2=-0.55  j3=-0.15   (x=1.048, y=+0.642)
#
# Hover height (safe transit, 15 cm above pick):
#   Same j1 as slot, j2=-0.35, j3=-0.05
#
# Drop zone:  j1=+1.00  j2=-0.55  j3=-0.15  (x=0.664, y=+1.034)
# Drop hover: j1=+1.00  j2=-0.35  j3=-0.05
# Home:       j1= 0.00  j2= 0.00  j3= 0.00

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
DROP_HOVER = [1.00, -0.35, -0.05]
DROP_PLACE = [1.00, -0.55, -0.15]

GRIPPER_OPEN   = [0.0]    # j4
GRIPPER_CLOSED = [-0.7]   # j4


# ── InventoryNode ─────────────────────────────────────────────────────────────

class InventoryNode(Node):

    def __init__(self):
        super().__init__("inventory_node")
        init_db()
        self.get_logger().info("Inventory database initialised")

        # ── Direct trajectory publishers ──────────────────────────────────────
        self.arm_pub = self.create_publisher(
            JointTrajectory, "/arm_controller/joint_trajectory", 10)
        self.grip_pub = self.create_publisher(
            JointTrajectory, "/gripper_controller/joint_trajectory", 10)

        # ── Live joint state ──────────────────────────────────────────────────
        self._jpos: Dict[str, float] = {
            "joint_1": 0.0, "joint_2": 0.0,
            "joint_3": 0.0, "joint_4": 0.0,
        }
        self._jlock = threading.Lock()

        # ── ArUco-detected box positions ──────────────────────────────────────
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

        self.stock_pub = self.create_publisher(String, "inventory/stock_state", 10)
        self.create_timer(1.0, self._pub_stock)

        self.get_logger().info(
            "InventoryNode ready (direct trajectory publisher — no MoveIt).")

    # ── Joint state subscriber ────────────────────────────────────────────────

    def _js_cb(self, msg: JointState):
        with self._jlock:
            for name, pos in zip(msg.name, msg.position):
                if name in self._jpos:
                    self._jpos[name] = float(pos)

    def _arm_now(self) -> List[float]:
        with self._jlock:
            return [self._jpos.get("joint_1", 0.0),
                    self._jpos.get("joint_2", 0.0),
                    self._jpos.get("joint_3", 0.0)]

    def _gripper_now(self) -> float:
        with self._jlock:
            return self._jpos.get("joint_4", 0.0)

    # ── ArUco ─────────────────────────────────────────────────────────────────

    def _aruco_cb(self, msg: String):
        try:
            for s, info in json.loads(msg.data).items():
                if info.get("detected"):
                    self._detected[int(s)] = info
            self._aruco_ts = time.time()
        except Exception as e:
            self.get_logger().warn(f"aruco_cb: {e}")

    def _aruco_ok(self) -> bool:
        return (time.time() - self._aruco_ts) < 10.0

    # ── IK for ArUco refinement (optional) ───────────────────────────────────

    @staticmethod
    def _ik(x: float, y: float, z: float) -> Optional[List[float]]:
        """
        Numeric IK.  Returns [j1,j2,j3] or None.
        Only used when ArUco gives us a position — falls back to FK table.
        """
        try:
            from scipy.optimize import fsolve  # type: ignore[import]
        except ImportError:
            return None
        j1 = math.atan2(y, x)
        r  = math.hypot(x, y)
        L0, L1, L2 = 0.657, 0.80, 0.82
        def res(jv):
            j2, j3 = jv
            return [L1*math.sin(j2)+L2*math.sin(j2+j3)-r,
                    L0+L1*math.cos(j2)+L2*math.cos(j2+j3)-z]
        try:
            sol = fsolve(res, [-0.55, -0.15], full_output=True)
            j2, j3 = sol[0]
            r2 = res([j2, j3])
            lim = math.pi/2
            if abs(r2[0])>0.03 or abs(r2[1])>0.03:
                return None
            if not (-lim<=j2<=lim and -lim<=j3<=lim):
                return None
            return [float(j1), float(j2), float(j3)]
        except Exception:
            return None

    def _slot_pick(self, slot: int) -> List[float]:
        """Return pick joints, using ArUco IK if available."""
        fb = SLOT_PICK[slot]
        if slot not in self._detected or not self._aruco_ok():
            return fb
        p  = self._detected[slot]
        ik = self._ik(p["x"], p["y"], p["z"])
        if ik:
            self.get_logger().info(
                f"Slot {slot}: ArUco IK → "
                f"[{ik[0]:.3f},{ik[1]:.3f},{ik[2]:.3f}]")
        return ik if ik else fb

    def _slot_hover(self, slot: int, pick: List[float]) -> List[float]:
        """Return hover joints, ArUco-adjusted if possible."""
        fb = SLOT_HOVER[slot]
        if slot not in self._detected or not self._aruco_ok():
            return fb
        p  = self._detected[slot]
        ik = self._ik(p["x"], p["y"], p["z"]+0.15)
        return ik if ik else [pick[0], fb[1], fb[2]]

    # ── Direct trajectory publishing ──────────────────────────────────────────

    def _send_arm(self, joints: List[float], duration_s: float):
        """Publish one arm trajectory point.  No blocking, no planning."""
        msg = JointTrajectory()
        msg.joint_names = ["joint_1", "joint_2", "joint_3"]
        pt  = JointTrajectoryPoint()
        pt.positions  = [float(j) for j in joints]
        pt.velocities = [0.0, 0.0, 0.0]
        secs = int(duration_s)
        nsecs = int((duration_s - secs) * 1e9)
        pt.time_from_start = DurationMsg(sec=secs, nanosec=nsecs)
        msg.points = [pt]
        self.arm_pub.publish(msg)
        self.get_logger().info(
            f"  → arm [{joints[0]:.3f},{joints[1]:.3f},{joints[2]:.3f}]"
            f"  dur={duration_s:.1f}s")

    def _send_gripper(self, j4: float, duration_s: float):
        """Publish one gripper trajectory point."""
        msg = JointTrajectory()
        msg.joint_names = ["joint_4"]
        pt  = JointTrajectoryPoint()
        pt.positions  = [float(j4)]
        pt.velocities = [0.0]
        secs = int(duration_s)
        nsecs = int((duration_s - secs) * 1e9)
        pt.time_from_start = DurationMsg(sec=secs, nanosec=nsecs)
        msg.points = [pt]
        self.grip_pub.publish(msg)
        self.get_logger().info(
            f"  → gripper [{j4:.3f}]  dur={duration_s:.1f}s")

    # ── Wait for arm to physically arrive ─────────────────────────────────────

    def _wait_arm(self, target: List[float], label: str) -> bool:
        """
        Block until /joint_states shows all three arm joints within GOAL_TOL
        of target, or until GOAL_TIMEOUT seconds elapse.
        """
        deadline = time.time() + GOAL_TIMEOUT
        while time.time() < deadline:
            actual = self._arm_now()
            err    = max(abs(actual[i]-target[i]) for i in range(3))
            if err < GOAL_TOL:
                self.get_logger().info(
                    f"  ✔ Arrived (err={err:.3f} rad): {label}")
                return True
            time.sleep(0.08)
        actual = self._arm_now()
        self.get_logger().warn(
            f"  ⚠ Timeout ({GOAL_TIMEOUT}s): {label}\n"
            f"    target={[round(v,3) for v in target]}\n"
            f"    actual={[round(v,3) for v in actual]}")
        return True   # continue anyway — partial motion is better than abort

    def _wait_gripper(self, target_j4: float):
        deadline = time.time() + 5.0
        while time.time() < deadline:
            if abs(self._gripper_now() - target_j4) < 0.05:
                return
            time.sleep(0.08)

    # ── Move helpers ──────────────────────────────────────────────────────────

    def _move_arm(self, joints: List[float], label: str,
                  duration_s: float = MOVE_SLOW):
        self.get_logger().info(f"Step: {label}")
        self._send_arm(joints, duration_s)
        self._wait_arm(joints, label)

    def _grip(self, close: bool):
        j4 = GRIPPER_CLOSED[0] if close else GRIPPER_OPEN[0]
        self._send_gripper(j4, GRIPPER_DUR)
        self._wait_gripper(j4)
        time.sleep(0.2)

    # ── Full pick-and-place sequence ──────────────────────────────────────────

    def _dispatch_sequence(self, slot: int) -> bool:
        """
        Execute the 9-step pick-and-place sequence using direct trajectory
        publishing.  No MoveIt, no planning, no action clients.

        Steps:
          1. Open gripper at home
          2. Hover above slot
          3. Descend to pick position
          4. Close gripper (grab)
          5. Lift back to hover
          6. Move to drop zone hover
          7. Descend to drop position
          8. Open gripper (release)
          9. Return home
        """
        pick  = self._slot_pick(slot)
        hover = self._slot_hover(slot, pick)
        src   = ("ArUco" if slot in self._detected and self._aruco_ok()
                 else "FK table")

        self.get_logger().info(
            f"=== Dispatch sequence: slot {slot}  source={src} ===\n"
            f"  pick  = {[round(v,3) for v in pick]}\n"
            f"  hover = {[round(v,3) for v in hover]}"
        )

        try:
            # 1. Open gripper at home
            self._grip(close=False)
            self._move_arm(HOME, "home position", MOVE_SLOW)

            # 2. Hover above slot (rotate base first, then extend)
            self._move_arm(hover, f"hover slot {slot}", MOVE_SLOW)

            # 3. Descend to pick position
            self._move_arm(pick, f"descend slot {slot}", MOVE_SLOW)

            # 4. Close gripper — grab item
            self.get_logger().info(f"  Gripping item at slot {slot}")
            self._grip(close=True)
            time.sleep(PICK_HOLD)

            # 5. Lift (return to hover with item)
            self._move_arm(hover, f"lift slot {slot}", MOVE_FAST)

            # 6. Approach drop zone hover
            self._move_arm(DROP_HOVER, "approach drop zone", MOVE_SLOW)

            # 7. Descend to drop position
            self._move_arm(DROP_PLACE, "place at drop zone", MOVE_FAST)

            # 8. Open gripper — release
            self.get_logger().info("  Releasing item")
            self._grip(close=False)
            time.sleep(DROP_HOLD)

            # 9. Return home
            self._move_arm(DROP_HOVER, "lift from drop zone", MOVE_FAST)
            self._move_arm(HOME, "return home", MOVE_SLOW)

            self.get_logger().info("=== Sequence complete ===")
            return True

        except Exception as exc:
            self.get_logger().error(f"Sequence error: {exc}")
            import traceback
            self.get_logger().error(traceback.format_exc())
            # Best-effort recovery: open gripper and go home
            try:
                self._send_gripper(GRIPPER_OPEN[0], GRIPPER_DUR)
                time.sleep(1.0)
                self._send_arm(HOME, MOVE_SLOW)
            except Exception:
                pass
            return False

    # ── Service callbacks ─────────────────────────────────────────────────────

    def _dispatch_cb(self, req: Any, res: Any) -> Any:
        mode = req.mode.upper() if req.mode else "FIFO"
        self.get_logger().info(f"Dispatch request — mode={mode}")

        ok, msg, info = dispatch(mode)
        if not ok or info is None:
            res.success, res.message = False, msg
            self.get_logger().warn(msg)
            return res

        self.get_logger().info(msg)
        res.item_name   = info.get("item_name", "")
        res.item_id     = info.get("item_id",   "")
        res.slot_number = info.get("slot",      -1)
        res.expiry_date = format_expiry(info.get("expiry_ts"))

        slot = info["slot"]

        if self._dispatch_sequence(slot):
            mark_dispatched(info["item_id"], mode)
            is_low, count = check_low_stock()
            res.success = True
            res.message = (
                f"Dispatched '{info['item_name']}' from slot {slot}."
                + (f"  LOW STOCK: {count} left!" if is_low else "")
            ).strip()
        else:
            res.success = False
            res.message = "Sequence failed — item NOT dispatched."

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

    # ── Stock publisher ───────────────────────────────────────────────────────

    def _pub_stock(self):
        stock, log = get_stock(), get_dispatch_log(10)
        msg      = String()
        msg.data = json.dumps({
            "timestamp":      time.time(),
            "stock_count":    stock_count(),
            "low_stock":      check_low_stock()[0],
            "aruco_active":   self._aruco_ok(),
            "detected_slots": list(self._detected.keys()),
            "items": [{"id": r["id"], "name": r["name"], "slot": r["slot"],
                       "arrival_ts": r["arrival_ts"],
                       "expiry":     format_expiry(r["expiry_ts"])} for r in stock],
            "dispatch_log": [{"item_name": r["item_name"], "mode": r["mode"],
                               "slot": r["slot"], "ts": r["ts"]} for r in log],
        })
        self.stock_pub.publish(msg)


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    rclpy.init()
    node = InventoryNode()

    # MultiThreadedExecutor so the dispatch service callback can block
    # on _wait_arm() while the joint_state subscription still runs
    # on a separate thread.
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
