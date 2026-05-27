"""Shared data contracts across Brain AI and robotics layers."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    RECOVERING = "recovering"


@dataclass
class Vector3:
    x: float
    y: float
    z: float

    @classmethod
    def from_list(cls, values: list[float]) -> "Vector3":
        return cls(float(values[0]), float(values[1]), float(values[2]))

    def as_list(self) -> list[float]:
        return [self.x, self.y, self.z]


@dataclass
class DetectedObject:
    label: str
    color: str | None
    position: Vector3
    confidence: float
    bbox: list[float] | None = None


@dataclass
class PerceptionResult:
    objects: list[DetectedObject]
    scene_summary: str
    free_space_ratio: float = 1.0


@dataclass
class SubGoal:
    id: str
    description: str
    module: str  # perception | pinns | rl | motion | safety
    status: TaskStatus = TaskStatus.PENDING
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Plan:
    command: str
    sub_goals: list[SubGoal]
    target_object: DetectedObject | None = None
    place_position: Vector3 | None = None


@dataclass
class RobotState:
    joint_angles_deg: list[float]
    gripper_open: bool = True
    ee_position: Vector3 | None = None


@dataclass
class RLAction:
    joint_torques: list[float]
    gripper_force: float
    ee_velocity: Vector3


@dataclass
class PhysicsVerdict:
    safe: bool
    corrected_action: RLAction | None
    reason: str
    corrections: dict[str, float] = field(default_factory=dict)


@dataclass
class MotionPlan:
    waypoints_deg: list[list[float]]
    duration_s: float
    collision_free: bool


@dataclass
class ExecutionResult:
    success: bool
    final_state: RobotState
    message: str


@dataclass
class PipelineResult:
    command: str
    plan: Plan
    perception: PerceptionResult
    physics: PhysicsVerdict
    motion: MotionPlan
    execution: ExecutionResult
    trace_id: str
