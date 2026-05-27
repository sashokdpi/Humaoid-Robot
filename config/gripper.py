"""xArm gripper configuration (Humble / xarm_api).

Default: standard UFACTORY parallel gripper on xArm6 (NOT bio_gripper / vacuum).
See https://github.com/xArm-Developer/xarm_ros2 — use add_gripper:=true only.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class GripperType(str, Enum):
    """Supported gripper models."""

    UFACTORY_STANDARD = "ufactory_standard"  # Default xArm parallel gripper
    # Future: BIO = "bio", VACUUM = "vacuum"


# Standard UFACTORY gripper — xarm_api §8 (NOT bio_gripper / lite_gripper services)
UFACTORY_STANDARD_GRIPPER = GripperType.UFACTORY_STANDARD


@dataclass
class GripperSettings:
    enabled: bool = True
    gripper_type: GripperType = GripperType.UFACTORY_STANDARD
    joint_name: str = "drive_joint"
    # control_msgs/GripperCommand action (0 rad = open, 0.86 rad = closed)
    action_name: str = "/xarm_gripper/gripper_action"
    service_enable: str = "/xarm/set_gripper_enable"
    service_mode: str = "/xarm/set_gripper_mode"
    service_speed: str = "/xarm/set_gripper_speed"
    service_set_position: str = "/xarm/set_gripper_position"
    service_get_position: str = "/xarm/get_gripper_position"
    open_position_mm: int = 850  # 0 = closed, 850 = fully open (UFACTORY units)
    close_position_mm: int = 120
    open_rad: float = 0.0
    close_rad: float = 0.86
    default_speed: int = 1500
    move_group_gripper: str = "xarm_gripper"  # MoveIt group when add_gripper:=true

    def position_mm_from_force(self, gripper_force: float, max_force: float = 25.0) -> int:
        """Map RL grip force to UFACTORY gripper open distance (lower = tighter)."""
        ratio = min(max(gripper_force / max_force, 0.0), 1.0)
        span = self.open_position_mm - self.close_position_mm
        return int(self.open_position_mm - ratio * span)

    def rad_from_open_ratio(self, open_ratio: float) -> float:
        """open_ratio 1.0 = fully open, 0.0 = closed."""
        open_ratio = min(max(open_ratio, 0.0), 1.0)
        return self.close_rad * (1.0 - open_ratio)
