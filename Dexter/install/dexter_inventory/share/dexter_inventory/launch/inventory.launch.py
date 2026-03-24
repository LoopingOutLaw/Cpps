"""
inventory.launch.py
Starts ONLY the inventory_node on top of an already-running robot simulation.

The web_interface is already started by simulated_robot.launch.py via
remote_interface.launch.py — do NOT start it again here or you get a
port-5000 conflict that silently breaks all /inventory/* routes.

Workflow
--------
Terminal 1:
    ros2 launch dexter_bringup simulated_robot.launch.py
    # Wait for: "Configured and activated arm_controller"

Terminal 2:
    ros2 run dexter_inventory seed_data --clear
    ros2 launch dexter_inventory inventory.launch.py
    # Open http://localhost:5000
"""

import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, LogInfo
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from moveit_configs_utils import MoveItConfigsBuilder
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

    is_sim_arg = DeclareLaunchArgument("is_sim", default_value="True")
    is_sim = LaunchConfiguration("is_sim")

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

    return LaunchDescription([
        is_sim_arg,
        LogInfo(msg="[inventory] Starting inventory_node only."),
        LogInfo(msg="[inventory] Dashboard already on http://localhost:5000 via simulated_robot.launch.py"),
        inventory_node,
    ])
