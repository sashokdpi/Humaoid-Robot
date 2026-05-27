"""
MoveIt2 launch stub.

On Jetson / Ubuntu install MoveIt2 for your arm, then either:
  - point move_group to this URDF/SRDF, or
  - replace this launch with your vendor MoveIt config (UR5, xArm, etc.)

Example after MoveIt setup:
  ros2 launch moveit_configs_utils demo.launch.py
"""

from launch import LaunchDescription
from launch.actions import LogInfo


def generate_launch_description():
    return LaunchDescription(
        [
            LogInfo(
                msg="Configure MoveIt2 for industrial_arm — see robotics/README.md"
            ),
        ]
    )
