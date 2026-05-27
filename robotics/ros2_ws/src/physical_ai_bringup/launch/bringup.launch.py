"""Full stack: robot description + perception + ros2_control (when hardware connected)."""

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    desc = FindPackageShare("physical_ai_description")
    perception = FindPackageShare("physical_ai_perception")

    return LaunchDescription(
        [
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource([desc, "/launch/display.launch.py"])
            ),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource([perception, "/launch/perception.launch.py"])
            ),
        ]
    )
