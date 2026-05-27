"""UFACTORY xArm6 presets (matches xarm_ros2 Humble)."""

from __future__ import annotations

from dataclasses import dataclass

from config.gripper import GripperSettings, GripperType
from config.settings import Ros2Settings


@dataclass(frozen=True)
class RobotPreset:
    robot_name: str
    arm_variant: str
    joint_count: int
    joint_names: tuple[str, ...]
    ros2: Ros2Settings
    gripper: GripperSettings
    home_joint_deg: tuple[float, ...] = (0.0, -45.0, 0.0, 30.0, 0.0, 0.0)
    # Pinned xarm_ros2 Humble launch files (Jetson)
    launch_driver: str = "xarm_moveit_config xarm6_moveit_realmove.launch.py"
    launch_moveit_fake: str = "xarm_moveit_config xarm6_moveit_fake.launch.py"
    launch_rviz: str = "xarm_controller xarm6_control_rviz_display.launch.py"


# Standard UFACTORY parallel gripper (add_gripper:=true, NOT add_bio_gripper / add_vacuum_gripper)
XARM6_GRIPPER = GripperSettings(enabled=True, gripper_type=GripperType.UFACTORY_STANDARD)

# xarm_ros2: xarm_moveit_config/config/xarm6/controllers.yaml
XARM6_PRESET = RobotPreset(
    robot_name="xarm6",
    arm_variant="xarm6",
    joint_count=6,
    joint_names=("joint1", "joint2", "joint3", "joint4", "joint5", "joint6"),
    ros2=Ros2Settings(
        joint_states_topic="/joint_states",
        trajectory_action="/xarm6_traj_controller/follow_joint_trajectory",
        detections_topic="/physical_ai/detections",
        move_group_action="/move_action",
        move_group_name="xarm6",
        planning_frame="link_base",
        ee_link="link_eef",
        twin_validate_service="/physical_ai/twin/validate_motion",
        spin_timeout_s=5.0,
    ),
    gripper=XARM6_GRIPPER,
    home_joint_deg=(0.0, -45.0, 0.0, 30.0, 0.0, 0.0),
)

PRESETS: dict[str, RobotPreset] = {
    "xarm6": XARM6_PRESET,
    "xarm": XARM6_PRESET,
}
