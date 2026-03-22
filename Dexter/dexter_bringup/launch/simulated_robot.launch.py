import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

    gazebo = IncludeLaunchDescription(
        os.path.join(
            get_package_share_directory("dexter_description"),
            "launch", "gazebo.launch.py"))

    controller = IncludeLaunchDescription(
        os.path.join(
            get_package_share_directory("dexter_controller"),
            "launch", "controller.launch.py"),
        launch_arguments={"is_sim": "True"}.items())

    moveit = IncludeLaunchDescription(
        os.path.join(
            get_package_share_directory("dexter_moveit"),
            "launch", "moveit.launch.py"),
        launch_arguments={"is_sim": "True"}.items())

    remote_interface = IncludeLaunchDescription(
        os.path.join(
            get_package_share_directory("dexter_remote"),
            "launch", "remote_interface.launch.py"),
        launch_arguments={"is_sim": "True"}.items())

    # inventory_node no longer needs MoveIt — just use_sim_time
    inventory_node = TimerAction(
        period=6.0,
        actions=[Node(
            package="dexter_inventory",
            executable="inventory_node",
            name="inventory_node",
            output="screen",
            parameters=[{"use_sim_time": True}],
        )]
    )

    display_val = os.environ.get("DISPLAY", ":0")

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

    rqt_image = TimerAction(
        period=6.0,
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
        aruco_detector,
        rqt_image,
    ])
