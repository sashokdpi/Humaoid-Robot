from brain_ai.types import RobotState, Vector3
from config.settings import Settings, get_settings


def initial_robot_state(joint_count: int | None = None, settings: Settings | None = None) -> RobotState:
    settings = settings or get_settings()
    n = joint_count or settings.joint_count

    if settings.robot_name == "xarm6" or settings.arm_variant == "xarm6":
        try:
            from config.robots.xarm6 import XARM6_PRESET

            angles = list(XARM6_PRESET.home_joint_deg)[:n]
        except ImportError:
            angles = [0.0, -45.0, 0.0, 30.0, 0.0, 0.0][:n]
        return RobotState(
            joint_angles_deg=angles,
            gripper_open=True,
            ee_position=Vector3(0.40, 0.0, 0.55),
        )

    angles = [0.0, 15.0, 30.0, 0.0, 45.0, 0.0][:n]
    return RobotState(
        joint_angles_deg=angles,
        gripper_open=True,
        ee_position=Vector3(0.35, 0.0, 0.90),
    )
