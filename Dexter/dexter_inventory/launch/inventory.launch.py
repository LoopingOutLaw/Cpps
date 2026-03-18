"""
inventory.launch.py
Launches the complete FEFO/FIFO Inventory Control System.

This starts:
- inventory_node: ROS2 node with MoveIt2 for arm control and inventory services
- web_interface: Flask dashboard on port 5000

Prerequisites:
- Robot simulation must be running first:
    ros2 launch dexter_bringup simulated_robot.launch.py

Usage:
    ros2 launch dexter_inventory inventory.launch.py

Then open http://localhost:5000 in your browser.
"""

import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, LogInfo, TimerAction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from moveit_configs_utils import MoveItConfigsBuilder
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    
    # Launch arguments
    is_sim_arg = DeclareLaunchArgument(
        "is_sim",
        default_value="True",
        description="Use simulation time"
    )
    is_sim = LaunchConfiguration("is_sim")
    
    # MoveIt configuration
    moveit_config = (
        MoveItConfigsBuilder("dexter", package_name="dexter_moveit")
        .robot_description(
            file_path=os.path.join(
                get_package_share_directory("dexter_description"),
                "urdf",
                "dexter.urdf.xacro",
            )
        )
        .robot_description_semantic(file_path="config/dexter.srdf")
        .trajectory_execution(file_path="config/moveit_controllers.yaml")
        .moveit_cpp(file_path="config/planning_python_api.yaml")
        .to_moveit_configs()
    )
    
    # Inventory Node (handles dispatch services and arm control)
    inventory_node = Node(
        package="dexter_inventory",
        executable="inventory_node",
        name="inventory_node",
        output="screen",
        parameters=[
            moveit_config.to_dict(),
            {"use_sim_time": is_sim},
        ],
    )
    
    # Web Interface Node (Flask dashboard with RFID, RL, etc.)
    # Delayed start to allow inventory_node to initialize
    web_interface_node = TimerAction(
        period=2.0,
        actions=[
            Node(
                package="dexter_remote",
                executable="web_interface.py",
                name="web_interface",
                output="screen",
                parameters=[
                    {"use_sim_time": is_sim},
                ],
            )
        ]
    )
    
    return LaunchDescription([
        is_sim_arg,
        LogInfo(msg="================================================"),
        LogInfo(msg="  DEXTER FEFO/FIFO Inventory Control System"),
        LogInfo(msg="================================================"),
        LogInfo(msg="  Starting inventory_node..."),
        inventory_node,
        LogInfo(msg="  Starting web_interface (http://localhost:5000)..."),
        web_interface_node,
        LogInfo(msg="================================================"),
    ])
