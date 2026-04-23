"""
simulated_robot.launch.py
=========================
Full simulation bringup:
  1. Gazebo (inventory.sdf world + robot URDF)
  2. ros2_control controllers
  3. MoveIt 2 move_group + RViz
  4. Web interface (Flask dashboard on :5000)
  5. aruco_box_detector   (headless, t=10 s) — publishes /inventory/box_poses
  6. visual_servo_node    (t=12 s) — closed-loop pick-and-place
  7. rqt_image_view       (optional camera preview, t=10 s)

NOTE — To see the ArUco OpenCV window run in a SEPARATE terminal:
    source install/setup.bash
    ARUCO_SHOW_WINDOW=1 ros2 run dexter_inventory aruco_box_detector

After launch, seed the database:
    ros2 run dexter_inventory seed_data --clear

Then open http://localhost:5000 and use FIFO / FEFO / RL-OPT buttons.
Dispatch triggers visual_servo_node via /visual_servo/pick_request.
"""

import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

    display_val = os.environ.get("DISPLAY", ":0")

    # ── Gazebo ────────────────────────────────────────────────────────────
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

    # ── MoveIt 2 + RViz ───────────────────────────────────────────────────
    moveit = IncludeLaunchDescription(
        os.path.join(
            get_package_share_directory("dexter_moveit"),
            "launch", "moveit.launch.py"),
        launch_arguments={"is_sim": "True"}.items())

    # ── Web interface (Flask dashboard :5000) ──────────────────────────────
    remote_interface = IncludeLaunchDescription(
        os.path.join(
            get_package_share_directory("dexter_remote"),
            "launch", "remote_interface.launch.py"),
        launch_arguments={"is_sim": "True"}.items())

    # ── ArUco box detector (headless, t=10 s) ─────────────────────────────
    # Publishes /inventory/box_poses  →  consumed by visual_servo_node
    # Set ARUCO_SHOW_WINDOW=1 in env if you want the OpenCV debug window.
    aruco_detector_node = TimerAction(
        period=10.0,
        actions=[Node(
            package="dexter_inventory",
            executable="aruco_box_detector",
            name="aruco_box_detector",
            output="screen",
            parameters=[{"use_sim_time": True}],
            additional_env={
                "ARUCO_SHOW_WINDOW": "0",
                "DISPLAY":           display_val,
                "QT_QPA_PLATFORM":   "xcb",
            },
        )]
    )

    # ── Visual servo node (t=12 s) ────────────────────────────────────────
    # Subscribes to /visual_servo/pick_request (Int32 slot number)
    # Published by web_interface.py when dispatch button is pressed.
    visual_servo = TimerAction(
        period=12.0,
        actions=[Node(
            package="dexter_inventory",
            executable="visual_servo_node",
            name="visual_servo_node",
            output="screen",
            parameters=[{"use_sim_time": True}],
        )]
    )

    # ── rqt_image_view (optional camera preview, t=10 s) ─────────────────
    rqt_image = TimerAction(
        period=10.0,
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
        aruco_detector_node,
        visual_servo,
    ])