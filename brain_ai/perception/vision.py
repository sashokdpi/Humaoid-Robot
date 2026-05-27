"""Perception layer: object detection and scene understanding."""

from __future__ import annotations

from abc import ABC, abstractmethod

from brain_ai.types import DetectedObject, PerceptionResult, Vector3
from config.settings import PerceptionBackend, Settings


class VisionSystem(ABC):
    @abstractmethod
    def perceive(self) -> PerceptionResult:
        raise NotImplementedError


class SimulatedVisionSystem(VisionSystem):
    """Simulates YOLO + depth fusion until RealSense + YOLO node is wired."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def perceive(self) -> PerceptionResult:
        objects: list[DetectedObject] = []
        for item in self.settings.sim_objects:
            objects.append(
                DetectedObject(
                    label=item["label"],
                    color=item.get("color"),
                    position=Vector3.from_list(item["position"]),
                    confidence=0.98,
                    bbox=[0.1, 0.1, 0.3, 0.3],
                )
            )
        labels = ", ".join(f"{o.color or ''} {o.label}".strip() for o in objects)
        return PerceptionResult(
            objects=objects,
            scene_summary=f"Simulated RGB-D frame: {labels}",
            free_space_ratio=0.72,
        )


def build_vision_system(settings: Settings) -> VisionSystem:
    backend = settings.perception_backend

    if backend == PerceptionBackend.SIM:
        return SimulatedVisionSystem(settings)

    if backend == PerceptionBackend.REALSENSE_YOLO:
        try:
            from brain_ai.perception.realsense_yolo import RealSenseYoloPerceptor

            return _PerceptorAdapter(RealSenseYoloPerceptor(settings))
        except ImportError as exc:
            if settings.allow_fallback:
                return SimulatedVisionSystem(settings)
            raise ImportError(
                "Install pyrealsense2 and ultralytics for RealSense+YOLO perception"
            ) from exc

    if backend == PerceptionBackend.ROS2:
        try:
            from brain_ai.perception.ros2_vision import Ros2VisionSystem

            return Ros2VisionSystem(settings)
        except ImportError as exc:
            if settings.allow_fallback:
                return SimulatedVisionSystem(settings)
            raise

    return SimulatedVisionSystem(settings)


class _PerceptorAdapter(VisionSystem):
    def __init__(self, inner) -> None:
        self._inner = inner

    def perceive(self) -> PerceptionResult:
        return self._inner.perceive()
