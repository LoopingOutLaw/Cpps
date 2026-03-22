"""
simulated_robot.launch.py
=========================
Full simulation bringup:
  1. Gazebo (inventory.sdf world + robot URDF)
  2. ros2_control controllers
  3. MoveIt 2 move_group + RViz
  4. Web interface (Flask dashboard on :5000)
  5. inventory_node (direct trajectory pick-and-place)

NOTE – aruco_box_detector is NOT launched here automatically.
Run it in a SEPARATE terminal so the OpenCV window is visible:

    # Terminal 2 (after simulation is up, ~10 s):
    source install/setup.bash
    ros2 run dexter_inventory aruco_box_detector

The detector publishes /inventory/box_poses and /inventory/arm_pose
as normal; the cv2 window will open in that terminal's display session.
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

    # ── Web interface ─────────────────────────────────────────────────────
    remote_interface = IncludeLaunchDescription(
        os.path.join(
            get_package_share_directory("dexter_remote"),
            "launch", "remote_interface.launch.py"),
        launch_arguments={"is_sim": "True"}.items())

    # ── Inventory node (t=7 s) ────────────────────────────────────────────
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

    # ── rqt_image_view  (optional camera preview, t=7 s) ─────────────────
    # Kept as a lightweight topic monitor; the OpenCV ArUco window
    # is started manually in a separate terminal (see note above).
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
        inventory_node,
        rqt_image,
    ])
