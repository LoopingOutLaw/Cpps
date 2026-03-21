import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
from moveit_configs_utils import MoveItConfigsBuilder


def generate_launch_description():
    # MoveIt configuration for inventory_node
    moveit_config = (
        MoveItConfigsBuilder("dexter", package_name="dexter_moveit")
        .robot_description(file_path=os.path.join(
            get_package_share_directory("dexter_description"),
            "urdf",
            "dexter.urdf.xacro"
            )
        )
        .robot_description_semantic(file_path="config/dexter.srdf")
        .trajectory_execution(file_path="config/moveit_controllers.yaml")
        .moveit_cpp(file_path="config/planning_python_api.yaml")
        .to_moveit_configs()
    )

    gazebo = IncludeLaunchDescription(
            os.path.join(
                get_package_share_directory("dexter_description"),
                "launch",
                "gazebo.launch.py"
            )
        )
    
    controller = IncludeLaunchDescription(
            os.path.join(
                get_package_share_directory("dexter_controller"),
                "launch",
                "controller.launch.py"
            ),
            launch_arguments={"is_sim": "True"}.items()
        )
    
    moveit = IncludeLaunchDescription(
            os.path.join(
                get_package_share_directory("dexter_moveit"),
                "launch",
                "moveit.launch.py"
            ),
            launch_arguments={"is_sim": "True"}.items()
        )
    
    remote_interface = IncludeLaunchDescription(
            os.path.join(
                get_package_share_directory("dexter_remote"),
                "launch",
                "remote_interface.launch.py"
            ),
            launch_arguments={"is_sim": "True"}.items()
        )
    
    # Inventory Node - provides dispatch/add_item services
    # Delayed start to ensure MoveIt is ready
    inventory_node = TimerAction(
        period=5.0,
        actions=[
            Node(
                package="dexter_inventory",
                executable="inventory_node",
                name="inventory_node",
                output="screen",
                parameters=[
                    moveit_config.to_dict(),
                    {"use_sim_time": True},
                ],
            )
        ]
    )
    
    # ArUco box detector - provides /inventory/box_poses for visual servoing
    # Delayed start to ensure camera bridge is ready
    aruco_detector = TimerAction(
        period=3.0,
        actions=[
            Node(
                package="dexter_inventory",
                executable="aruco_box_detector",
                name="aruco_box_detector",
                output="screen",
                parameters=[{"use_sim_time": True}],
            )
        ]
    )
    
    return LaunchDescription([
        gazebo,
        controller,
        moveit,
        remote_interface,
        inventory_node,
        aruco_detector,
    ])