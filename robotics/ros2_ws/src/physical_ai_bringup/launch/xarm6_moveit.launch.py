"""
MoveIt2 for xArm6 — uses official xarm_moveit_config when installed.

Typical upstream launch (run in separate terminal before Physical AI pipeline):
  ros2 launch xarm_moveit_config xarm6_moveit_fake.launch.py add_gripper:=false

Or real hardware:
  ros2 launch xarm_bringup xarm6.launch.py robot_ip:=192.168.1.XXX
"""

from launch import LaunchDescription
from launch.actions import LogInfo


def generate_launch_description():
    return LaunchDescription(
        [
            LogInfo(
                msg=(
                    "Start MoveIt2 via xarm_ros2, e.g.:\n"
                    "  ros2 launch xarm_moveit_config xarm6_moveit_fake.launch.py\n"
                    "Config reference: physical_ai_description/config/xarm6_moveit_controllers.yaml"
                )
            ),
        ]
    )
