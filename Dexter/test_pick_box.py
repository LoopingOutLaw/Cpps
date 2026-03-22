#!/usr/bin/env python3
"""
test_pick_box.py - Direct test of arm motion to pick a box
==========================================================
No visual detection, no database - just raw arm motion.

Usage:
    # Terminal 1: Start simulation
    ros2 launch dexter_bringup simulated_robot.launch.py
    
    # Terminal 2: Run this test (wait ~10s for MoveIt to initialize)
    cd ~/Cpps/Dexter
    source /opt/ros/jazzy/setup.bash
    source install/setup.bash
    python3 test_pick_box.py [slot]
    
    slot: 0, 1, 2, or 3 (default: 0)
"""

import sys
import time
import threading
from typing import Dict, List, Any

import numpy as np
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState

# MoveIt imports
from moveit.planning import MoveItPy
from moveit.core.robot_state import RobotState


# ── Hardcoded positions (IK-calculated for box positions) ─────────────────────
# Gripper at z=1.216m, boxes at z=1.156m

SLOT_POSES = {
    0: [-0.5496,  0.5502,  1.1711],  # x=1.048, y=-0.642
    1: [-0.1800,  0.5500,  1.1714],  # x=1.209, y=-0.220
    2: [ 0.1800,  0.5500,  1.1714],  # x=1.209, y=+0.220
    3: [ 0.5496,  0.5502,  1.1711],  # x=1.048, y=+0.642
}

SLOT_HOVER = {
    0: [-0.5496,  0.5371,  1.0073],  # 15cm above slot 0
    1: [-0.1800,  0.5368,  1.0077],  # 15cm above slot 1
    2: [ 0.1800,  0.5368,  1.0077],  # 15cm above slot 2
    3: [ 0.5496,  0.5371,  1.0073],  # 15cm above slot 3
}

DROP_ZONE_HOVER = [1.0122, 0.1599, 1.5096]  # hover above drop
DROP_ZONE_PLACE = [1.0122, 0.1951, 1.6547]  # drop position
HOME_POSE = [0.00, 0.00, 0.00]


class PickTest(Node):
    GOAL_TOL = 0.06
    GOAL_TIMEOUT = 20.0

    def __init__(self, slot: int):
        super().__init__("pick_test")
        self.slot = slot
        
        # Joint state tracking
        self._jpos: Dict[str, float] = {}
        self._jlock = threading.Lock()
        self.create_subscription(JointState, "/joint_states", self._js_cb, 10)
        
        self.get_logger().info("=" * 60)
        self.get_logger().info(f"Pick Test - Slot {slot}")
        self.get_logger().info("=" * 60)
        
        # Initialize MoveIt
        self.get_logger().info("Initializing MoveIt... (this may take a few seconds)")
        self.dexter = MoveItPy(node_name="pick_test_moveit")
        self.arm = self.dexter.get_planning_component("arm")
        self.gripper = self.dexter.get_planning_component("gripper")
        self.robot_model = self.dexter.get_robot_model()
        self.get_logger().info("MoveIt ready!")
        
        # Wait for joint states
        self.get_logger().info("Waiting for joint states...")
        time.sleep(1.0)
        
    def _js_cb(self, msg: JointState):
        with self._jlock:
            for name, pos in zip(msg.name, msg.position):
                self._jpos[name] = float(pos)
    
    def _arm_now(self) -> List[float]:
        with self._jlock:
            return [
                self._jpos.get("joint_1", 0.0),
                self._jpos.get("joint_2", 0.0),
                self._jpos.get("joint_3", 0.0),
            ]
    
    def _wait_goal(self, target: List[float], label: str) -> bool:
        """Wait until arm reaches target position."""
        deadline = time.time() + self.GOAL_TIMEOUT
        while time.time() < deadline:
            rclpy.spin_once(self, timeout_sec=0.05)
            actual = self._arm_now()
            err = max(abs(actual[i] - target[i]) for i in range(3))
            if err < self.GOAL_TOL:
                self.get_logger().info(f"  OK Arrived: {label} (err={err:.3f})")
                return True
            time.sleep(0.05)
        
        actual = self._arm_now()
        self.get_logger().error(
            f"  TIMEOUT: {label}\n"
            f"    target={[round(v,3) for v in target]}\n"
            f"    actual={[round(v,3) for v in actual]}"
        )
        return False
    
    def _plan_arm(self, joints: List[float]) -> Any:
        """Create arm motion plan."""
        goal = RobotState(self.robot_model)
        goal.set_joint_group_positions(
            "arm",
            np.array(joints, dtype=np.float64)
        )
        self.arm.set_start_state_to_current_state()
        self.arm.set_goal_state(robot_state=goal)
        return self.arm.plan()
    
    def _plan_gripper(self, open_: bool) -> Any:
        """Create gripper motion plan."""
        goal = RobotState(self.robot_model)
        val = 0.0 if open_ else -0.7
        goal.set_joint_group_positions(
            "gripper",
            np.array([val], dtype=np.float64)
        )
        self.gripper.set_start_state_to_current_state()
        self.gripper.set_goal_state(robot_state=goal)
        return self.gripper.plan()
    
    def _ok(self, plan: Any) -> bool:
        """Check if plan is valid."""
        if plan is None:
            return False
        try:
            return plan.trajectory is not None
        except:
            return False
    
    def move_arm(self, joints: List[float], label: str) -> bool:
        """Move arm to joint position."""
        now = self._arm_now()
        self.get_logger().info(
            f"\n>> {label}\n"
            f"   target: [{joints[0]:.3f}, {joints[1]:.3f}, {joints[2]:.3f}]\n"
            f"   current: [{now[0]:.3f}, {now[1]:.3f}, {now[2]:.3f}]"
        )
        
        plan = self._plan_arm(joints)
        if not self._ok(plan):
            self.get_logger().error(f"  PLAN FAILED: {label}")
            return False
        
        self.get_logger().info(f"  Executing...")
        self.dexter.execute(plan.trajectory, controllers=[])
        return self._wait_goal(joints, label)
    
    def move_gripper(self, open_: bool) -> bool:
        """Open or close gripper."""
        label = "OPEN gripper" if open_ else "CLOSE gripper"
        self.get_logger().info(f"\n>> {label}")
        
        plan = self._plan_gripper(open_)
        if not self._ok(plan):
            self.get_logger().warn(f"  Gripper plan failed (may already be at target)")
            return True  # Non-fatal
        
        self.dexter.execute(plan.trajectory, controllers=[])
        time.sleep(0.5)
        self.get_logger().info(f"  OK {label}")
        return True
    
    def run_pick_sequence(self) -> bool:
        """Execute full pick and place sequence."""
        slot = self.slot
        pick = SLOT_POSES[slot]
        hover = SLOT_HOVER[slot]
        
        self.get_logger().info("\n" + "=" * 60)
        self.get_logger().info(f"STARTING PICK SEQUENCE FOR SLOT {slot}")
        self.get_logger().info("=" * 60)
        
        steps = [
            # (joints, label, is_gripper, gripper_open)
            (HOME_POSE, "1. Go to HOME", False, None),
            (None, "2. Open gripper", True, True),
            (hover, f"3. Hover above slot {slot}", False, None),
            (pick, f"4. Descend to slot {slot}", False, None),
            (None, "5. Close gripper (GRAB)", True, False),
            (hover, f"6. Lift from slot {slot}", False, None),
            (DROP_ZONE_HOVER, "7. Move to drop zone hover", False, None),
            (DROP_ZONE_PLACE, "8. Lower to drop zone", False, None),
            (None, "9. Open gripper (RELEASE)", True, True),
            (HOME_POSE, "10. Return HOME", False, None),
        ]
        
        for joints, label, is_gripper, grip_open in steps:
            self.get_logger().info("\n" + "-" * 50)
            
            if is_gripper:
                if not self.move_gripper(grip_open):
                    return False
            else:
                if not self.move_arm(joints, label):
                    return False
            
            # Pause for observation
            time.sleep(1.0)
        
        self.get_logger().info("\n" + "=" * 60)
        self.get_logger().info("PICK SEQUENCE COMPLETE!")
        self.get_logger().info("=" * 60)
        return True


def main():
    # Parse slot argument
    slot = 0
    if len(sys.argv) > 1:
        try:
            slot = int(sys.argv[1])
            if slot not in [0, 1, 2, 3]:
                print(f"Invalid slot {slot}. Using slot 0.")
                slot = 0
        except ValueError:
            print(f"Invalid argument '{sys.argv[1]}'. Using slot 0.")
    
    print(f"\n{'='*60}")
    print(f"TEST PICK BOX - SLOT {slot}")
    print(f"{'='*60}\n")
    
    rclpy.init()
    
    try:
        node = PickTest(slot)
        
        # Give time for subscriptions
        for _ in range(10):
            rclpy.spin_once(node, timeout_sec=0.1)
        
        success = node.run_pick_sequence()
        
        if success:
            print("\n*** SUCCESS ***\n")
        else:
            print("\n*** FAILED ***\n")
            
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
    finally:
        rclpy.shutdown()


if __name__ == "__main__":
    main()
