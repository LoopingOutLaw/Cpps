import os
from pathlib import Path
from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument, IncludeLaunchDescription,
    SetEnvironmentVariable, ExecuteProcess,
)
from launch.substitutions import Command, LaunchConfiguration
from launch.launch_description_sources import PythonLaunchDescriptionSource

from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    dexter_description = get_package_share_directory("dexter_description")

    model_arg = DeclareLaunchArgument(
        name="model",
        default_value=os.path.join(dexter_description, "urdf", "dexter.urdf.xacro"),
    )
    world_arg = DeclareLaunchArgument(
        name="world",
        default_value=os.path.join(dexter_description, "worlds", "inventory.sdf"),
    )

    gazebo_resource_path = SetEnvironmentVariable(
        name="GZ_SIM_RESOURCE_PATH",
        value=[str(Path(dexter_description).parent.resolve())],
    )

    ros_distro = os.environ.get("ROS_DISTRO", "jazzy")
    is_ignition = "True" if ros_distro == "humble" else "False"

    robot_description = ParameterValue(
        Command([
            "xacro ",
            LaunchConfiguration("model"),
            " is_ignition:=", is_ignition,
        ]),
        value_type=str,
    )

    robot_state_publisher_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        parameters=[{"robot_description": robot_description, "use_sim_time": True}],
    )

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            os.path.join(get_package_share_directory("ros_gz_sim"), "launch"),
            "/gz_sim.launch.py",
        ]),
        launch_arguments=[("gz_args", [" -v 4 -r ", LaunchConfiguration("world")])],
    )

    gz_spawn_entity = Node(
        package="ros_gz_sim",
        executable="create",
        output="screen",
        arguments=["-topic", "robot_description", "-name", "dexter"],
    )

    # ── Bridge: clock + camera ────────────────────────────────────────────────
    #
    # For ROS 2 Jazzy + Gazebo Harmonic, ros_gz_bridge parameter_bridge is the
    # standard way to bridge camera images.  ros_gz_image (image_bridge) is a
    # separate optional package that is NOT installed by default.
    #
    # Type string syntax:
    #   <gz_topic>@<ros_type>[<gz_type>    ← Gazebo → ROS2  (we only need this)
    #   <gz_topic>@<ros_type>]<gz_type>    ← ROS2 → Gazebo
    #   <gz_topic>@<ros_type>@<gz_type>    ← bidirectional
    #
    # The camera sensor in inventory.sdf publishes to /gz/camera/image.
    # We remap it to /camera/image_raw for the ArUco detector.
    # ──────────────────────────────────────────────────────────────────────────
    gz_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        output="screen",
        arguments=[
            "/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock",
            "/gz/camera/image@sensor_msgs/msg/Image[gz.msgs.Image",
            "/gz/camera/camera_info@sensor_msgs/msg/CameraInfo[gz.msgs.CameraInfo",
        ],
        remappings=[
            ("/gz/camera/image",       "/camera/image_raw"),
            ("/gz/camera/camera_info", "/camera/camera_info"),
        ],
    )

    return LaunchDescription([
        model_arg,
        world_arg,
        gazebo_resource_path,
        robot_state_publisher_node,
        gazebo,
        gz_spawn_entity,
        gz_bridge,
    ])
