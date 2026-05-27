"""RL execution layer: motor skill policies."""

from __future__ import annotations

from abc import ABC, abstractmethod

from brain_ai.types import DetectedObject, RLAction, RobotState, Vector3
from config.ai_models import ModelPaths
from config.settings import Settings


class GraspPolicy(ABC):
    @abstractmethod
    def propose_grasp(self, target: DetectedObject, robot: RobotState) -> RLAction:
        raise NotImplementedError


class SimulatedGraspPolicy(GraspPolicy):
    """Heuristic stand-in when no trained checkpoint exists."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def propose_grasp(self, target: DetectedObject, robot: RobotState) -> RLAction:
        n = len(robot.joint_angles_deg) or self.settings.joint_count
        return RLAction(
            joint_torques=[2.5] * n,
            gripper_force=22.0 if target.label == "bottle" else 15.0,
            ee_velocity=Vector3(0.9, 0.2, 0.1),
        )


def build_grasp_policy(settings: Settings) -> GraspPolicy:
    paths = ModelPaths()

    if paths.rl_onnx.exists():
        try:
            from brain_ai.reinforcement_learning.onnx_policy import OnnxGraspPolicy

            return OnnxGraspPolicy(paths.rl_onnx, settings)
        except ImportError:
            pass

    if paths.rl_torch.exists():
        try:
            from brain_ai.reinforcement_learning.onnx_policy import TorchGraspPolicy

            return TorchGraspPolicy(paths.rl_torch, settings)
        except ImportError:
            pass

    return SimulatedGraspPolicy(settings)
