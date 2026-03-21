#!/usr/bin/env python3
"""
inventory_node.py  (ArUco-aware version)
ROS 2 node that bridges the FIFO/FEFO inventory system with the Dexter arm.
Now subscribes to /inventory/box_poses from aruco_box_detector.py and uses
detected positions for motion planning instead of pure hardcoded FK values.

Services exposed
----------------
/inventory/dispatch          dexter_msgs/srv/DispatchItem
/inventory/add_item          dexter_msgs/srv/AddItem

Topics subscribed
-----------------
/inventory/box_poses         std_msgs/msg/String  (JSON from aruco_box_detector)

Topics published
----------------
/inventory/stock_state       std_msgs/msg/String  (JSON, 1 Hz)
"""

from __future__ import annotations

import json
import math
import time
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import rclpy
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.node import Node
from std_msgs.msg import String

try:
    from dexter_msgs.srv import DispatchItem, AddItem  # type: ignore[import]
except ImportError as e:
    raise ImportError(
        "dexter_msgs not found — build and source the workspace first."
    ) from e

try:
    from moveit.planning import MoveItPy  # type: ignore[import]
    from moveit.core.robot_state import RobotState  # type: ignore[import]
except ImportError as e:
    raise ImportError("moveit_py not found — install MoveIt 2.") from e

from dexter_inventory.inventory_db import (
    init_db, add_item, mark_dispatched, get_stock, get_dispatch_log,
    stock_count, clear_all,
)
from dexter_inventory.dispatch_engine import (
    dispatch, build_motion_sequence, check_low_stock, format_expiry,
    SLOT_POSES, SLOT_HOVER, HOME_POSE,
    DROP_ZONE_HOVER, DROP_ZONE_PLACE,
)


# Joint names explicit so ordering inside planning group never matters
ARM_JOINT_NAMES    = ["joint_1", "joint_2", "joint_3"]
GRIPPER_JOINT_NAME = "joint_4"


# ── Inverse kinematics helper ──────────────────────────────────────────────────
def _compute_ik(x: float, y: float, z: float
                ) -> Optional[Tuple[float, float, float]]:
    """
    Compute arm joint angles for end-effector at (x, y, z) in robot base frame.
    Returns (j1, j2, j3) in radians, or None if unreachable / scipy missing.

    Link geometry from URDF:
      shoulder height  L0_z = 0.307 + 0.35 = 0.657 m
      upper arm        L1   = 0.80 m
      forearm          L2   = 0.82 m
    """
    try:
        from scipy.optimize import fsolve  # type: ignore[import]
    except ImportError:
        return None

    j1      = math.atan2(y, x)
    r_tgt   = math.hypot(x, y)
    z_tgt   = z
    L0_z, L1, L2 = 0.657, 0.80, 0.82

    def residuals(jv):
        j2, j3 = jv
        r_fk = L1 * math.sin(j2) + L2 * math.sin(j2 + j3)
        z_fk = L0_z + L1 * math.cos(j2) + L2 * math.cos(j2 + j3)
        return [r_fk - r_tgt, z_fk - z_tgt]

    try:
        sol    = fsolve(residuals, [-0.55, -0.15], full_output=True)
        j2, j3 = sol[0]
        res    = residuals([j2, j3])
        if abs(res[0]) > 0.02 or abs(res[1]) > 0.02:
            return None
        lim = math.pi / 2
        if not (-lim <= j2 <= lim and -lim <= j3 <= lim):
            return None
        return j1, j2, j3
    except Exception:
        return None


# ── InventoryNode ──────────────────────────────────────────────────────────────

class InventoryNode(Node):

    def __init__(self):
        super().__init__("inventory_node")
        init_db()
        self.get_logger().info("Inventory database initialised")

        # ── MoveIt 2 ──────────────────────────────────────────────────────────
        self.dexter      = MoveItPy(node_name="inventory_moveit")
        self.arm         = self.dexter.get_planning_component("arm")
        self.gripper     = self.dexter.get_planning_component("gripper")
        self.robot_model = self.dexter.get_robot_model()
        self.get_logger().info("MoveIt 2 ready")

        # Detected slot positions from ArUco detector
        self._detected_poses: Dict[int, dict] = {}
        self._aruco_last_msg_time: float = 0.0

        cb = ReentrantCallbackGroup()

        # ── Subscribers ───────────────────────────────────────────────────────
        self.box_poses_sub = self.create_subscription(
            String, "/inventory/box_poses",
            self._box_poses_callback, 10, callback_group=cb,
        )

        # ── Services ──────────────────────────────────────────────────────────
        self.dispatch_srv = self.create_service(
            DispatchItem, "inventory/dispatch",
            self._dispatch_callback, callback_group=cb,
        )
        self.add_item_srv = self.create_service(
            AddItem, "inventory/add_item",
            self._add_item_callback, callback_group=cb,
        )

        # ── Publisher ─────────────────────────────────────────────────────────
        self.stock_pub = self.create_publisher(String, "inventory/stock_state", 10)
        self.create_timer(1.0, self._publish_stock)

        self.get_logger().info(
            "InventoryNode ready.\n"
            "  Services : /inventory/dispatch  /inventory/add_item\n"
            "  Listening: /inventory/box_poses (ArUco detector)"
        )

    # ── ArUco callback ────────────────────────────────────────────────────────

    def _box_poses_callback(self, msg: String):
        try:
            data    = json.loads(msg.data)
            updated = []
            for slot_str, info in data.items():
                slot = int(slot_str)
                if info.get("detected"):
                    self._detected_poses[slot] = info
                    updated.append(
                        f"slot{slot}=({info['x']:.3f},{info['y']:.3f})"
                    )
            if updated:
                self._aruco_last_msg_time = time.time()
                self.get_logger().info(
                    f"ArUco update: {', '.join(updated)}",
                    throttle_duration_sec=2.0,
                )
        except Exception as e:
            self.get_logger().warn(f"box_poses_callback error: {e}")

    def _aruco_fresh(self, max_age_s: float = 10.0) -> bool:
        return (time.time() - self._aruco_last_msg_time) < max_age_s

    # ── Pick-pose resolver ────────────────────────────────────────────────────

    def _resolve_slot_arm_joints(self, slot: int) -> List[float]:
        """
        Return [j1, j2, j3] for the pick position.
        Priority: ArUco IK  →  FK table fallback.
        """
        fallback = SLOT_POSES[slot]["arm"]

        if slot not in self._detected_poses or not self._aruco_fresh():
            self.get_logger().info(
                f"Slot {slot}: FK table {fallback} (ArUco unavailable)"
            )
            return fallback

        p       = self._detected_poses[slot]
        x, y, z = p["x"], p["y"], p["z"]
        self.get_logger().info(
            f"Slot {slot}: ArUco @ ({x:.4f},{y:.4f},{z:.4f}) m — solving IK"
        )

        ik = _compute_ik(x, y, z)
        if ik is None:
            self.get_logger().warn(
                f"Slot {slot}: IK failed → FK table fallback"
            )
            return fallback

        j1, j2, j3 = ik
        self.get_logger().info(
            f"Slot {slot}: IK ok → j1={j1:.3f} j2={j2:.3f} j3={j3:.3f} rad"
        )
        return [j1, j2, j3]

    def _resolve_hover_joints(self, slot: int, pick_j: List[float]) -> List[float]:
        if slot not in self._detected_poses or not self._aruco_fresh():
            return SLOT_HOVER[slot]
        p = self._detected_poses[slot]
        ik_hover = _compute_ik(p["x"], p["y"], p["z"] + 0.15)
        if ik_hover:
            return list(ik_hover)
        h = SLOT_HOVER[slot]
        return [pick_j[0], h[1], h[2]]

    # ── Motion sequence ───────────────────────────────────────────────────────

    def _build_steps(self, slot: int) -> List[dict]:
        pick  = self._resolve_slot_arm_joints(slot)
        hover = self._resolve_hover_joints(slot, pick)
        go    = [0.0, 0.0]     # gripper open
        gc    = [-0.7, 0.7]    # gripper closed
        return [
            {"label": "open gripper at home",        "arm": HOME_POSE,      "gripper": go},
            {"label": f"hover above slot {slot}",     "arm": hover,          "gripper": go},
            {"label": f"descend to slot {slot}",      "arm": pick,           "gripper": go},
            {"label": f"grip item at slot {slot}",    "arm": pick,           "gripper": gc},
            {"label": f"lift from slot {slot}",       "arm": hover,          "gripper": gc},
            {"label": "approach drop zone",           "arm": DROP_ZONE_HOVER,"gripper": gc},
            {"label": "place at drop zone",           "arm": DROP_ZONE_PLACE,"gripper": gc},
            {"label": "release item",                 "arm": DROP_ZONE_PLACE,"gripper": go},
            {"label": "return to home",               "arm": HOME_POSE,      "gripper": go},
        ]

    # ── Arm motion helpers ────────────────────────────────────────────────────

    def _plan_arm(self, joints: List[float]) -> Any:
        goal = RobotState(self.robot_model)
        # MoveIt2 expects numpy array, not dict
        joint_values = np.array([float(joints[i]) for i in range(3)], dtype=np.float64)
        goal.set_joint_group_positions("arm", joint_values)
        self.arm.set_start_state_to_current_state()
        self.arm.set_goal_state(robot_state=goal)
        return self.arm.plan()

    def _plan_gripper(self, open_: bool) -> Any:
        goal = RobotState(self.robot_model)
        # MoveIt2 expects numpy array, not dict
        joint_values = np.array([0.0 if open_ else -0.7], dtype=np.float64)
        goal.set_joint_group_positions("gripper", joint_values)
        self.gripper.set_start_state_to_current_state()
        self.gripper.set_goal_state(robot_state=goal)
        return self.gripper.plan()

    def _plan_ok(self, plan: Any) -> Tuple[bool, str]:
        """Check if plan is valid. Returns (ok, reason)."""
        try:
            if plan is None:
                return False, "plan is None"
            if not hasattr(plan, 'trajectory') or plan.trajectory is None:
                return False, "no trajectory"
            traj = plan.trajectory
            if not hasattr(traj, 'joint_trajectory'):
                return False, "no joint_trajectory"
            pts = traj.joint_trajectory.points
            if len(pts) == 0:
                return False, "empty trajectory (0 points)"
            return True, f"{len(pts)} points"
        except Exception as e:
            return False, f"exception: {e}"

    def _move(self, arm_j: List[float], grip_j: List[float], label: str) -> bool:
        try:
            self.get_logger().info(
                f"  Plan arm [{arm_j[0]:.3f},{arm_j[1]:.3f},{arm_j[2]:.3f}] — {label}"
            )
            p = self._plan_arm(arm_j)
            ok, reason = self._plan_ok(p)
            
            if not ok:
                # Check if "empty trajectory" means we're already at goal
                if "empty" in reason or "0 points" in reason:
                    self.get_logger().info(f"  ✓ Already at goal (no motion needed): {label}")
                else:
                    self.get_logger().error(f"  ✗ Arm plan FAILED ({reason}): {label}")
                    return False
            else:
                # Execute and wait for completion (blocking=True)
                self.get_logger().info(f"  Executing trajectory ({reason})...")
                self.dexter.execute(p.trajectory, blocking=True, controllers=[])
                self.get_logger().info(f"  ✓ Arm motion complete: {label}")
            
            time.sleep(0.3)  # Small pause between motions

            gp = self._plan_gripper(grip_j[0] > -0.35)
            gp_ok, gp_reason = self._plan_ok(gp)
            if gp_ok:
                self.dexter.execute(gp.trajectory, blocking=True, controllers=[])
                time.sleep(0.2)
            elif "empty" in gp_reason or "0 points" in gp_reason:
                self.get_logger().info(f"  Gripper already at position: {label}")
            else:
                self.get_logger().warn(f"  ⚠ Gripper plan failed ({gp_reason}): {label}")
            return True
        except Exception as exc:
            self.get_logger().error(f"  ✗ Motion error ({label}): {exc}")
            return False

    def _execute_sequence(self, steps: List[dict]) -> bool:
        for step in steps:
            if not self._move(step["arm"], step["gripper"], step["label"]):
                return False
        return True

    # ── Service callbacks ─────────────────────────────────────────────────────

    def _dispatch_callback(self, req: Any, res: Any) -> Any:
        mode = req.mode.upper() if req.mode else "FIFO"
        self.get_logger().info(f"Dispatch request — mode={mode}")

        ok, msg, info = dispatch(mode)
        if not ok or info is None:
            res.success = False
            res.message = msg
            self.get_logger().warn(msg)
            return res

        self.get_logger().info(msg)
        res.item_name   = info.get("item_name", "")
        res.item_id     = info.get("item_id",   "")
        res.slot_number = info.get("slot",      -1)
        res.expiry_date = format_expiry(info.get("expiry_ts"))

        slot  = info["slot"]
        steps = self._build_steps(slot)

        src = "ArUco" if (slot in self._detected_poses and self._aruco_fresh()) \
              else "FK table"
        self.get_logger().info(f"  Pick position source: {src}")

        motion_ok = self._execute_sequence(steps)

        if motion_ok:
            mark_dispatched(info["item_id"], mode)
            is_low, count = check_low_stock()
            low = f"  LOW STOCK: {count} item(s) remaining!" if is_low else ""
            res.success = True
            res.message = (
                f"Dispatched '{info['item_name']}' from slot {slot}. {low}"
            ).strip()
        else:
            res.success = False
            res.message = "Motion planning/execution failed — item not dispatched."

        self.get_logger().info(res.message)
        return res

    def _add_item_callback(self, req: Any, res: Any) -> Any:
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

    # ── Stock publisher ───────────────────────────────────────────────────────

    def _publish_stock(self):
        stock   = get_stock()
        log     = get_dispatch_log(10)
        payload = {
            "timestamp":      time.time(),
            "stock_count":    stock_count(),
            "low_stock":      check_low_stock()[0],
            "aruco_active":   self._aruco_fresh(),
            "detected_slots": list(self._detected_poses.keys()),
            "items": [
                {"id": r["id"], "name": r["name"], "slot": r["slot"],
                 "arrival_ts": r["arrival_ts"],
                 "expiry":     format_expiry(r["expiry_ts"])}
                for r in stock
            ],
            "dispatch_log": [
                {"item_name": r["item_name"], "mode": r["mode"],
                 "slot": r["slot"],           "ts":   r["ts"]}
                for r in log
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
