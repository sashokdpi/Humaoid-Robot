"""Runtime configuration. Default mode is simulation for safe testing."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from config.gripper import GripperSettings


class RunMode(str, Enum):
    SIMULATION = "simulation"
    HYBRID = "hybrid"  # sim robot + real perception (camera testing)
    HARDWARE = "hardware"


class PerceptionBackend(str, Enum):
    SIM = "sim"
    REALSENSE_YOLO = "realsense_yolo"  # Direct pyrealsense2 + ultralytics (Jetson / PC)
    ROS2 = "ros2"  # Subscribe to /physical_ai/detections


class RobotBackend(str, Enum):
    SIM = "sim"
    ROS2 = "ros2"


@dataclass
class Ros2Settings:
    joint_states_topic: str = "/joint_states"
    trajectory_action: str = "/arm_controller/follow_joint_trajectory"
    detections_topic: str = "/physical_ai/detections"
    move_group_action: str = "/move_action"
    move_group_name: str = "arm_group"
    planning_frame: str = "base_link"
    ee_link: str = "tool0"
    twin_validate_service: str = "/physical_ai/twin/validate_motion"
    node_namespace: str = ""
    spin_timeout_s: float = 2.0


@dataclass
class RealSenseSettings:
    serial: str = ""  # empty = first device
    color_width: int = 640
    color_height: int = 480
    fps: int = 30
    align_depth: bool = True


@dataclass
class YoloSettings:
    model_path: str = "yolov8n.pt"
    confidence: float = 0.5
    device: str = "auto"  # auto | cuda:0 | cpu
    target_classes: list[str] = field(
        default_factory=lambda: ["bottle", "cup", "person", "scissors", "book"]
    )


@dataclass
class Settings:
    project_root: Path = field(default_factory=lambda: Path(__file__).resolve().parents[1])
    mode: RunMode = RunMode.SIMULATION
    perception_backend: PerceptionBackend = PerceptionBackend.SIM
    robot_backend: RobotBackend = RobotBackend.SIM
    robot_name: str = "xarm6"
    arm_variant: str = "xarm6"  # xarm6 | industrial_arm | ur5
    ros2: Ros2Settings = field(default_factory=Ros2Settings)
    realsense: RealSenseSettings = field(default_factory=RealSenseSettings)
    yolo: YoloSettings = field(default_factory=YoloSettings)
    gripper: GripperSettings = field(default_factory=GripperSettings)
    xarm_ip: str = "192.168.1.206"
    add_gripper: bool = True
    allow_fallback: bool = True
    sim_objects: list[dict] = field(
        default_factory=lambda: [
            {"label": "bottle", "color": "red", "position": [0.45, 0.12, 0.82]},
            {"label": "bottle", "color": "blue", "position": [0.55, -0.08, 0.82]},
            {"label": "tool", "color": "gray", "position": [0.30, 0.25, 0.85]},
            {"label": "human", "color": "n/a", "position": [1.20, 0.0, 1.0]},
        ]
    )
    recycle_bin_position: list[float] = field(default_factory=lambda: [0.70, 0.40, 0.75])
    joint_count: int = 6
    joint_names: list[str] = field(
        default_factory=lambda: [
            "joint_1",
            "joint_2",
            "joint_3",
            "joint_4",
            "joint_5",
            "joint_6",
        ]
    )
    trace_enabled: bool = True
    api_host: str = "127.0.0.1"
    api_port: int = 8080
    isaac_twin_enabled: bool = False

    @property
    def is_simulation(self) -> bool:
        return self.mode == RunMode.SIMULATION

    @property
    def ros2_ws_path(self) -> Path:
        return self.project_root / "robotics" / "ros2_ws"

    @property
    def urdf_path(self) -> Path:
        return (
            self.project_root
            / "robotics"
            / "ros2_ws"
            / "src"
            / "physical_ai_description"
            / "urdf"
            / f"{self.robot_name}.urdf.xacro"
        )


def _parse_mode(raw: str) -> RunMode:
    mapping = {
        "simulation": RunMode.SIMULATION,
        "sim": RunMode.SIMULATION,
        "hybrid": RunMode.HYBRID,
        "hardware": RunMode.HARDWARE,
        "hw": RunMode.HARDWARE,
    }
    return mapping.get(raw.lower(), RunMode.SIMULATION)


def _parse_perception(raw: str, mode: RunMode) -> PerceptionBackend:
    mapping = {
        "sim": PerceptionBackend.SIM,
        "realsense_yolo": PerceptionBackend.REALSENSE_YOLO,
        "realsense": PerceptionBackend.REALSENSE_YOLO,
        "ros2": PerceptionBackend.ROS2,
    }
    if raw:
        return mapping.get(raw.lower(), PerceptionBackend.SIM)
    if mode == RunMode.HYBRID:
        return PerceptionBackend.REALSENSE_YOLO
    if mode == RunMode.HARDWARE:
        return PerceptionBackend.ROS2
    return PerceptionBackend.SIM


def _parse_robot(raw: str, mode: RunMode) -> RobotBackend:
    mapping = {"sim": RobotBackend.SIM, "ros2": RobotBackend.ROS2}
    if raw:
        return mapping.get(raw.lower(), RobotBackend.SIM)
    if mode == RunMode.HARDWARE:
        return RobotBackend.ROS2
    return RobotBackend.SIM


def _apply_robot_preset(settings: Settings) -> Settings:
    from config.robots import PRESETS

    key = settings.robot_name.lower().replace("-", "")
    if settings.arm_variant.lower() in PRESETS:
        key = settings.arm_variant.lower()
    preset = PRESETS.get(key)
    if preset is None:
        return settings

    settings.robot_name = preset.robot_name
    settings.arm_variant = preset.arm_variant
    settings.joint_count = preset.joint_count
    settings.joint_names = list(preset.joint_names)
    settings.ros2 = preset.ros2
    settings.gripper = preset.gripper
    return settings


def get_settings() -> Settings:
    mode = _parse_mode(os.getenv("PHYSICAL_AI_MODE", "simulation"))
    perception = _parse_perception(os.getenv("PHYSICAL_AI_PERCEPTION", ""), mode)
    robot = _parse_robot(os.getenv("PHYSICAL_AI_ROBOT_BACKEND", ""), mode)

    joint_names_raw = os.getenv("PHYSICAL_AI_JOINT_NAMES", "")
    joint_names = [n.strip() for n in joint_names_raw.split(",") if n.strip()]

    robot_name = os.getenv("PHYSICAL_AI_ROBOT", "xarm6")
    arm_variant = os.getenv("PHYSICAL_AI_ARM_VARIANT", robot_name)

    settings = Settings(
        mode=mode,
        perception_backend=perception,
        robot_backend=robot,
        robot_name=robot_name,
        arm_variant=arm_variant,
        allow_fallback=os.getenv("PHYSICAL_AI_ALLOW_FALLBACK", "1") == "1",
        trace_enabled=os.getenv("PHYSICAL_AI_TRACE", "1") != "0",
        api_host=os.getenv("PHYSICAL_AI_API_HOST", "127.0.0.1"),
        api_port=int(os.getenv("PHYSICAL_AI_API_PORT", "8080")),
        isaac_twin_enabled=os.getenv("PHYSICAL_AI_ISAAC_TWIN", "0") == "1",
        xarm_ip=os.getenv("XARM_IP", os.getenv("PHYSICAL_AI_XARM_IP", "192.168.1.206")),
        add_gripper=os.getenv("PHYSICAL_AI_GRIPPER", "1") == "1",
        gripper=GripperSettings(
            enabled=os.getenv("PHYSICAL_AI_GRIPPER", "1") == "1",
            action_name=os.getenv(
                "PHYSICAL_AI_GRIPPER_ACTION", "/xarm_gripper/gripper_action"
            ),
        ),
        joint_count=int(os.getenv("PHYSICAL_AI_JOINT_COUNT", "6")),
        joint_names=joint_names or Settings().joint_names,
        yolo=YoloSettings(
            model_path=os.getenv("PHYSICAL_AI_YOLO_MODEL", "yolov8n.pt"),
            confidence=float(os.getenv("PHYSICAL_AI_YOLO_CONF", "0.5")),
            device=os.getenv("PHYSICAL_AI_YOLO_DEVICE", "auto"),
        ),
        realsense=RealSenseSettings(
            serial=os.getenv("PHYSICAL_AI_REALSENSE_SERIAL", ""),
            color_width=int(os.getenv("PHYSICAL_AI_RS_WIDTH", "640")),
            color_height=int(os.getenv("PHYSICAL_AI_RS_HEIGHT", "480")),
        ),
        ros2=Ros2Settings(
            joint_states_topic=os.getenv("PHYSICAL_AI_JOINT_STATES_TOPIC", "/joint_states"),
            trajectory_action=os.getenv(
                "PHYSICAL_AI_TRAJECTORY_ACTION", "/arm_controller/follow_joint_trajectory"
            ),
            detections_topic=os.getenv("PHYSICAL_AI_DETECTIONS_TOPIC", "/physical_ai/detections"),
            move_group_name=os.getenv("PHYSICAL_AI_MOVE_GROUP", "arm_group"),
            planning_frame=os.getenv("PHYSICAL_AI_PLANNING_FRAME", "base_link"),
            ee_link=os.getenv("PHYSICAL_AI_EE_LINK", "tool0"),
        ),
    )

    if joint_names:
        settings.joint_names = joint_names
    else:
        settings = _apply_robot_preset(settings)

    if os.getenv("PHYSICAL_AI_TRAJECTORY_ACTION"):
        settings.ros2.trajectory_action = os.environ["PHYSICAL_AI_TRAJECTORY_ACTION"]
    if os.getenv("PHYSICAL_AI_MOVE_GROUP"):
        settings.ros2.move_group_name = os.environ["PHYSICAL_AI_MOVE_GROUP"]
    if os.getenv("PHYSICAL_AI_PLANNING_FRAME"):
        settings.ros2.planning_frame = os.environ["PHYSICAL_AI_PLANNING_FRAME"]
    if os.getenv("PHYSICAL_AI_EE_LINK"):
        settings.ros2.ee_link = os.environ["PHYSICAL_AI_EE_LINK"]
    if os.getenv("PHYSICAL_AI_JOINT_STATES_TOPIC"):
        settings.ros2.joint_states_topic = os.environ["PHYSICAL_AI_JOINT_STATES_TOPIC"]
    if os.getenv("PHYSICAL_AI_GRIPPER") == "0":
        settings.gripper.enabled = False
    if os.getenv("PHYSICAL_AI_GRIPPER_ACTION"):
        settings.gripper.action_name = os.environ["PHYSICAL_AI_GRIPPER_ACTION"]

    return settings
