"""Subscribe to perception JSON published by physical_ai_perception ROS2 node."""

from __future__ import annotations

import json

from brain_ai.perception.vision import VisionSystem
from brain_ai.types import DetectedObject, PerceptionResult, Vector3
from config.settings import Settings
from robotics.ros2_bridge import Ros2Context, parse_detection_json, require_rclpy


class Ros2VisionSystem(VisionSystem):
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._node = None
        self._latest: PerceptionResult | None = None

    def _ensure_node(self) -> None:
        if self._node is not None:
            return
        require_rclpy("ROS2 perception")
        Ros2Context.ensure_init()
        import rclpy
        from rclpy.node import Node
        from std_msgs.msg import String

        topic = self.settings.ros2.detections_topic
        node = Node("physical_ai_vision_client")

        def callback(msg: String) -> None:
            self._latest = self._parse_msg(msg.data)

        node.create_subscription(String, topic, callback, 10)
        self._node = node
        for _ in range(10):
            rclpy.spin_once(node, timeout_sec=0.2)
            if self._latest is not None:
                break

    def perceive(self) -> PerceptionResult:
        self._ensure_node()
        import rclpy

        for _ in range(20):
            rclpy.spin_once(self._node, timeout_sec=0.25)
            if self._latest is not None:
                return self._latest
        raise RuntimeError(
            f"No detections on {self.settings.ros2.detections_topic}. "
            "Launch: ros2 launch physical_ai_bringup perception.launch.py"
        )

    def _parse_msg(self, raw: str) -> PerceptionResult:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            data = {"objects": parse_detection_json(raw)}

        if isinstance(data, list):
            items = data
            summary = f"ROS2 detections: {len(items)} objects"
            free_space = 0.7
        else:
            items = data.get("objects", parse_detection_json(raw))
            summary = str(data.get("scene_summary", f"ROS2 detections: {len(items)} objects"))
            free_space = float(data.get("free_space_ratio", 0.7))

        objects: list[DetectedObject] = []
        for item in items:
            pos = item.get("position", [0, 0, 0])
            objects.append(
                DetectedObject(
                    label=str(item.get("label", "object")),
                    color=item.get("color"),
                    position=Vector3.from_list(pos),
                    confidence=float(item.get("confidence", 0.0)),
                    bbox=item.get("bbox"),
                )
            )
        return PerceptionResult(objects=objects, scene_summary=summary, free_space_ratio=free_space)
