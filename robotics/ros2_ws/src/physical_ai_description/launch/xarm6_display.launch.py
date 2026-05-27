"""Display xArm6 in RViz (simplified URDF or official xarm_description)."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import Command, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    pkg = FindPackageShare("physical_ai_description")
    model = PathJoinSubstitution([pkg, "urdf", "xarm6.urdf.xacro"])

    return LaunchDescription(
        [
            DeclareLaunchArgument("use_official_urdf", default_value="false"),
            DeclareLaunchArgument("use_sim_time", default_value="false"),
            Node(
                package="robot_state_publisher",
                executable="robot_state_publisher",
                parameters=[
                    {
                        "robot_description": ParameterValue(
                            Command(
                                [
                                    "xacro ",
                                    model,
                                    " use_official_urdf:=",
                                    LaunchConfiguration("use_official_urdf"),
                                ]
                            ),
                            value_type=str,
                        ),
                        "use_sim_time": LaunchConfiguration("use_sim_time"),
                    }
                ],
            ),
            Node(
                package="joint_state_publisher_gui",
                executable="joint_state_publisher_gui",
            ),
            Node(package="rviz2", executable="rviz2"),
        ]
    )
