"""Motion planning (MoveIt2 interface in hardware mode)."""

from __future__ import annotations

from abc import ABC, abstractmethod
import math

from brain_ai.types import MotionPlan, RobotState, Vector3
from config.settings import RobotBackend, Settings


class MotionPlanner(ABC):
    @abstractmethod
    def plan_to_pose(
        self, robot: RobotState, target_position: Vector3, place_position: Vector3 | None
    ) -> MotionPlan:
        raise NotImplementedError


class SimulatedMotionPlanner(MotionPlanner):
    """IK + trajectory stub; used in simulation and as MoveIt fallback."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def plan_to_pose(
        self, robot: RobotState, target_position: Vector3, place_position: Vector3 | None
    ) -> MotionPlan:
        start = list(robot.joint_angles_deg)
        approach = self._pose_to_joints(target_position, offset_z=0.08)
        grasp = self._pose_to_joints(target_position, offset_z=0.0)
        waypoints = [start, approach, grasp]
        if place_position:
            waypoints.append(self._pose_to_joints(place_position, offset_z=0.05))
        return MotionPlan(waypoints_deg=waypoints, duration_s=2.5, collision_free=True)

    def _pose_to_joints(self, position: Vector3, offset_z: float = 0.0) -> list[float]:
        z = position.z + offset_z
        return [
            math.degrees(math.atan2(position.y, position.x)),
            30.0 + z * 20,
            45.0 - z * 10,
            0.0,
            60.0,
            0.0,
        ][: self.settings.joint_count]


def build_motion_planner(settings: Settings) -> MotionPlanner:
    if settings.robot_backend == RobotBackend.ROS2:
        from robotics.moveit_client import MoveItMotionPlanner

        return MoveItMotionPlanner(settings)
    return SimulatedMotionPlanner(settings)
