from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription(
        [
            DeclareLaunchArgument("yolo_model", default_value="yolov8n.pt"),
            DeclareLaunchArgument("device", default_value="cuda:0"),
            DeclareLaunchArgument("rate_hz", default_value="5.0"),
            Node(
                package="physical_ai_perception",
                executable="yolo_realsense_node",
                name="yolo_realsense_node",
                output="screen",
                parameters=[
                    {
                        "yolo_model": LaunchConfiguration("yolo_model"),
                        "device": LaunchConfiguration("device"),
                        "rate_hz": LaunchConfiguration("rate_hz"),
                    }
                ],
            ),
        ]
    )
