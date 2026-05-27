"""Hardware abstraction: ROS2 drivers in production, in-memory sim for testing."""

from __future__ import annotations

from abc import ABC, abstractmethod

from brain_ai.types import ExecutionResult, MotionPlan, RobotState, Vector3
from config.settings import RobotBackend, Settings
from robotics.robot_state import initial_robot_state


class RobotDriver(ABC):
    @abstractmethod
    def get_state(self) -> RobotState:
        raise NotImplementedError

    @abstractmethod
    def execute_plan(self, plan: MotionPlan) -> ExecutionResult:
        raise NotImplementedError


class SimulatedRobotDriver(RobotDriver):
    def __init__(self, initial: RobotState) -> None:
        self._state = initial

    def get_state(self) -> RobotState:
        return self._state

    def execute_plan(self, plan: MotionPlan) -> ExecutionResult:
        if not plan.waypoints_deg:
            return ExecutionResult(success=False, final_state=self._state, message="Empty plan")
        final_joints = plan.waypoints_deg[-1]
        self._state = RobotState(
            joint_angles_deg=final_joints,
            gripper_open=self._state.gripper_open,
            ee_position=Vector3(0.45, 0.12, 0.82),
        )
        return ExecutionResult(
            success=True,
            final_state=self._state,
            message=f"Simulated execution over {len(plan.waypoints_deg)} waypoints",
        )


def build_robot_driver(settings: Settings) -> RobotDriver:
    initial = initial_robot_state(settings.joint_count, settings)
    sim = SimulatedRobotDriver(initial)

    if settings.robot_backend == RobotBackend.ROS2:
        try:
            from hardware.ros2_driver import Ros2RobotDriver

            return Ros2RobotDriver(settings, fallback=sim if settings.allow_fallback else None)
        except ImportError:
            if settings.allow_fallback:
                return sim
            raise
    return sim
