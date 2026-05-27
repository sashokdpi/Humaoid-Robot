from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription(
        [
            Node(
                package="physical_ai_twin",
                executable="twin_validate_node",
                name="physical_ai_twin_validate",
                output="screen",
            ),
        ]
    )
