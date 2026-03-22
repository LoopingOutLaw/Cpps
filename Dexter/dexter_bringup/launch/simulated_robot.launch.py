"""
simulated_robot.launch.py
=========================
Full simulation bringup:
  1. Gazebo (inventory.sdf world + robot URDF)
  2. ros2_control controllers
  3. MoveIt 2 move_group + RViz
  4. Web interface (Flask dashboard on :5000)
  5. inventory_node (direct trajectory pick-and-place)
  6. aruco_box_detector (overhead camera → ArUco → box poses)
  7. rqt_image_view (/camera/image_raw preview)

Startup order (TimerActions ensure controllers are ready first):
  t=0  : Gazebo + controllers + MoveIt
  t=5  : aruco_box_detector  (needs camera bridge which starts with Gazebo)
  t=7  : inventory_node      (needs controllers + aruco data)
  t=7  : rqt_image_view
"""

import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

    display_val = os.environ.get("DISPLAY", ":0")

    # ── Gazebo simulation + URDF ──────────────────────────────────────────
    gazebo = IncludeLaunchDescription(
        os.path.join(
            get_package_share_directory("dexter_description"),
            "launch", "gazebo.launch.py"))

    # ── ros2_control controllers ──────────────────────────────────────────
    controller = IncludeLaunchDescription(
        os.path.join(
            get_package_share_directory("dexter_controller"),
            "launch", "controller.launch.py"),
        launch_arguments={"is_sim": "True"}.items())

    # ── MoveIt 2 + RViz ──────────────────────────────────────────────────
    moveit = IncludeLaunchDescription(
        os.path.join(
            get_package_share_directory("dexter_moveit"),
            "launch", "moveit.launch.py"),
        launch_arguments={"is_sim": "True"}.items())

    # ── Web interface (task server + Flask dashboard) ─────────────────────
    remote_interface = IncludeLaunchDescription(
        os.path.join(
            get_package_share_directory("dexter_remote"),
            "launch", "remote_interface.launch.py"),
        launch_arguments={"is_sim": "True"}.items())

    # ── ArUco box detector  (t=5 s) ───────────────────────────────────────
    aruco_detector = TimerAction(
        period=5.0,
        actions=[Node(
            package="dexter_inventory",
            executable="aruco_box_detector",
            name="aruco_box_detector",
            output="screen",
            parameters=[{"use_sim_time": True}],
            additional_env={
                "DISPLAY":           display_val,
                "ARUCO_SHOW_WINDOW": "1",
                "QT_QPA_PLATFORM":   "xcb",
            },
        )]
    )

    # ── Inventory node  (t=7 s, needs controllers + aruco) ───────────────
    inventory_node = TimerAction(
        period=7.0,
        actions=[Node(
            package="dexter_inventory",
            executable="inventory_node",
            name="inventory_node",
            output="screen",
            parameters=[{"use_sim_time": True}],
        )]
    )

    # ── rqt_image_view (camera feed preview, t=7 s) ───────────────────────
    rqt_image = TimerAction(
        period=7.0,
        actions=[Node(
            package="rqt_image_view",
            executable="rqt_image_view",
            name="camera_viewer",
            arguments=["/camera/image_raw"],
            output="log",
            additional_env={
                "DISPLAY":         display_val,
                "QT_QPA_PLATFORM": "xcb",
            },
        )]
    )

    return LaunchDescription([
        gazebo,
        controller,
        moveit,
        remote_interface,
        aruco_detector,
        inventory_node,
        rqt_image,
    ])
