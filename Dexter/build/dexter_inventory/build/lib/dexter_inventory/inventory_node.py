#!/usr/bin/env python3
"""
inventory_node.py
ROS 2 node that bridges the FIFO/FEFO inventory system with the Dexter arm.

Services exposed
----------------
/inventory/dispatch          dexter_msgs/srv/DispatchItem
    Trigger a FIFO or FEFO dispatch.  The node will plan and execute the full
    pick-and-place sequence using MoveIt 2.

/inventory/add_item          dexter_msgs/srv/AddItem
    Add an item to a shelf slot (called from the web dashboard).

Topics published
----------------
/inventory/stock_state       std_msgs/msg/String  (JSON, 1 Hz)
    Current stock summary for the dashboard.
"""

from __future__ import annotations

import json
import time
from typing import TYPE_CHECKING, Any, List

import rclpy
import numpy as np
from rclpy.node import Node
from rclpy.callback_groups import ReentrantCallbackGroup
from std_msgs.msg import String

# ROS2 message imports - these are generated at build time
# Type checking is disabled for these imports as they're resolved at runtime
try:
    from dexter_msgs.srv import DispatchItem, AddItem  # type: ignore[import]
except ImportError as e:
    raise ImportError(
        "dexter_msgs not found. Make sure to build and source the workspace first.\n"
        "Run: colcon build && source install/setup.bash"
    ) from e

try:
    from moveit.planning import MoveItPy  # type: ignore[import]
    from moveit.core.robot_state import RobotState  # type: ignore[import]
except ImportError as e:
    raise ImportError(
        "moveit_py not found. Make sure MoveIt 2 is installed and sourced."
    ) from e

from dexter_inventory.inventory_db import (
    init_db, add_item, mark_dispatched, get_stock, get_dispatch_log,
    stock_count, clear_all,
)
from dexter_inventory.dispatch_engine import (
    dispatch, build_motion_sequence, check_low_stock, format_expiry,
)


class InventoryNode(Node):

    def __init__(self):
        super().__init__("inventory_node")
        init_db()
        self.get_logger().info("Inventory database initialised")

        # ── MoveIt 2 ──────────────────────────────────────────────────────
        self.dexter      = MoveItPy(node_name="inventory_moveit")
        self.arm         = self.dexter.get_planning_component("arm")
        self.gripper     = self.dexter.get_planning_component("gripper")
        self.robot_model = self.dexter.get_robot_model()
        self.get_logger().info("MoveIt 2 ready")

        cb = ReentrantCallbackGroup()

        # ── Services ──────────────────────────────────────────────────────
        self.dispatch_srv = self.create_service(
            DispatchItem, "inventory/dispatch",
            self._dispatch_callback,
            callback_group=cb,
        )
        self.add_item_srv = self.create_service(
            AddItem, "inventory/add_item",
            self._add_item_callback,
            callback_group=cb,
        )

        # ── Publisher ─────────────────────────────────────────────────────
        self.stock_pub = self.create_publisher(String, "inventory/stock_state", 10)
        self.create_timer(1.0, self._publish_stock)

        self.get_logger().info(
            "InventoryNode ready.  Services: /inventory/dispatch  /inventory/add_item"
        )

    # ── Arm helpers ───────────────────────────────────────────────────────

    def _move(self, arm_joints: list, gripper_joints: list, label: str) -> bool:
        """Plan and execute one arm+gripper motion step."""
        try:
            arm_state     = RobotState(self.robot_model)
            gripper_state = RobotState(self.robot_model)

            arm_state.set_joint_group_positions("arm", np.array(arm_joints))
            gripper_state.set_joint_group_positions("gripper", np.array(gripper_joints))

            self.arm.set_start_state_to_current_state()
            self.gripper.set_start_state_to_current_state()
            self.arm.set_goal_state(robot_state=arm_state)
            self.gripper.set_goal_state(robot_state=gripper_state)

            arm_plan     = self.arm.plan()
            gripper_plan = self.gripper.plan()

            # Check if plans are valid (MoveIt returns PlanResult with trajectory attribute)
            arm_ok = arm_plan is not None and hasattr(arm_plan, 'trajectory') and arm_plan.trajectory is not None
            gripper_ok = gripper_plan is not None and hasattr(gripper_plan, 'trajectory') and gripper_plan.trajectory is not None

            if arm_ok and gripper_ok:
                self.get_logger().info(f"  -> {label}")
                self.dexter.execute(arm_plan.trajectory,     controllers=[])
                self.dexter.execute(gripper_plan.trajectory, controllers=[])
                return True

            self.get_logger().error(f"  X Planning failed: {label}")
            return False
            
        except Exception as e:
            self.get_logger().error(f"  X Motion error ({label}): {str(e)}")
            return False

    def _execute_sequence(self, steps: list) -> bool:
        """Execute an ordered list of motion steps.  Aborts on first failure."""
        for step in steps:
            ok = self._move(step["arm"], step["gripper"], step["label"])
            if not ok:
                return False
        return True

    # ── Service callbacks ─────────────────────────────────────────────────

    def _dispatch_callback(self, req: Any, res: Any) -> Any:
        """Handle dispatch service request."""
        mode = req.mode.upper() if req.mode else "FIFO"
        self.get_logger().info(f"Dispatch request received - mode={mode}")

        ok, msg, info = dispatch(mode)
        if not ok or info is None:
            res.success = False
            res.message = msg
            self.get_logger().warn(msg)
            return res

        # info is guaranteed to be a dict at this point
        self.get_logger().info(msg)
        res.item_name = info.get("item_name", "")
        res.item_id = info.get("item_id", "")
        res.slot_number = info.get("slot", -1)
        res.expiry_date = format_expiry(info.get("expiry_ts"))

        # Execute the full pick-and-place motion
        steps = info.get("steps", [])
        motion_ok = self._execute_sequence(steps)

        if motion_ok:
            item_id = info.get("item_id", "")
            mark_dispatched(item_id, mode)
            is_low, count = check_low_stock()
            low_msg = f"  LOW STOCK: only {count} item(s) remaining!" if is_low else ""
            res.success = True
            item_name = info.get("item_name", "unknown")
            slot = info.get("slot", -1)
            res.message = f"Dispatched '{item_name}' from slot {slot}. {low_msg}".strip()
        else:
            res.success = False
            res.message = "Motion planning/execution failed - item not dispatched."

        self.get_logger().info(res.message)
        return res

    def _add_item_callback(self, req: Any, res: Any) -> Any:
        """Handle add item service request."""
        try:
            expiry_ts = float(req.expiry_ts) if req.expiry_ts else None
            item_id   = add_item(req.item_name, req.slot, expiry_ts)
            res.success = True
            res.item_id = item_id
            res.message = f"Added '{req.item_name}' to slot {req.slot}"
            self.get_logger().info(res.message)
        except ValueError as e:
            res.success = False
            res.message = str(e)
            self.get_logger().warn(res.message)
        return res

    # ── Publisher ─────────────────────────────────────────────────────────

    def _publish_stock(self):
        """Publish stock summary as JSON for the web dashboard."""
        stock = get_stock()
        log   = get_dispatch_log(10)

        payload = {
            "timestamp":    time.time(),
            "stock_count":  stock_count(),
            "low_stock":    check_low_stock()[0],
            "items": [
                {
                    "id":         row["id"],
                    "name":       row["name"],
                    "slot":       row["slot"],
                    "arrival_ts": row["arrival_ts"],
                    "expiry":     format_expiry(row["expiry_ts"]),
                }
                for row in stock
            ],
            "dispatch_log": [
                {
                    "item_name": row["item_name"],
                    "mode":      row["mode"],
                    "slot":      row["slot"],
                    "ts":        row["ts"],
                }
                for row in log
            ],
        }

        msg      = String()
        msg.data = json.dumps(payload)
        self.stock_pub.publish(msg)


def main():
    rclpy.init()
    node = InventoryNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
