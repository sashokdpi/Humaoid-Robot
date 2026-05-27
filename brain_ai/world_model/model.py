"""Semantic world model built from perception and robot state."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from brain_ai.types import DetectedObject, PerceptionResult, RobotState, Vector3


@dataclass
class WorldModelState:
    objects: list[DetectedObject] = field(default_factory=list)
    robot: RobotState | None = None
    obstacles: list[Vector3] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class WorldModel:
    def __init__(self) -> None:
        self.state = WorldModelState()

    def update_from_perception(self, perception: PerceptionResult, robot: RobotState) -> WorldModelState:
        self.state.objects = list(perception.objects)
        self.state.robot = robot
        self.state.obstacles = [
            o.position for o in perception.objects if o.label.lower() in {"human", "obstacle"}
        ]
        self.state.metadata["scene_summary"] = perception.scene_summary
        self.state.metadata["free_space_ratio"] = perception.free_space_ratio
        return self.state

    def get_object_by_label_color(self, label: str, color: str | None) -> DetectedObject | None:
        for obj in self.state.objects:
            if obj.label.lower() != label.lower():
                continue
            if color and obj.color and obj.color.lower() != color.lower():
                continue
            return obj
        return None
