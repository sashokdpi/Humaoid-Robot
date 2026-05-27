"""
xArm6 + Physical AI perception.

Prerequisites on Jetson/Ubuntu 22.04:
  1. Install xarm_ros2 (Humble): https://github.com/xArm-Developer/xarm_ros2
  2. Start xArm driver + ros2_control (see scripts/xarm6_ros2_start.sh)
  3. source this workspace + xarm_ros2 workspace
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, LogInfo
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    desc = FindPackageShare("physical_ai_description")
    perception = FindPackageShare("physical_ai_perception")

    return LaunchDescription(
        [
            LogInfo(msg="Physical AI xArm6 — ensure xarm_ros2 driver is running for hardware"),
            DeclareLaunchArgument("use_official_urdf", default_value="false"),
            DeclareLaunchArgument("yolo_device", default_value="cuda:0"),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource([desc, "/launch/xarm6_display.launch.py"]),
                launch_arguments={
                    "use_official_urdf": LaunchConfiguration("use_official_urdf"),
                }.items(),
            ),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource([perception, "/launch/perception.launch.py"]),
                launch_arguments={"device": LaunchConfiguration("yolo_device")}.items(),
            ),
        ]
    )
