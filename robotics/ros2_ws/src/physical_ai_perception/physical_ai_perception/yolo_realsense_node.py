#!/usr/bin/env python3
"""ROS2 node: RealSense D455 + YOLO -> /physical_ai/detections (JSON)."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

# Project root: set PHYSICAL_AI_ROOT when running from colcon install
_ROOT = Path(os.environ.get("PHYSICAL_AI_ROOT", Path(__file__).resolve().parents[5]))
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from config.settings import get_settings  # noqa: E402
from brain_ai.perception.realsense_yolo import RealSenseYoloPerceptor  # noqa: E402


class YoloRealSenseNode(Node):
    def __init__(self) -> None:
        super().__init__("yolo_realsense_node")
        self.declare_parameter("yolo_model", "yolov8n.pt")
        self.declare_parameter("device", "cuda:0")
        self.declare_parameter("rate_hz", 5.0)
        self.declare_parameter("detections_topic", "/physical_ai/detections")

        settings = get_settings()
        settings.yolo.model_path = self.get_parameter("yolo_model").value
        settings.yolo.device = self.get_parameter("device").value

        topic = self.get_parameter("detections_topic").value
        self._pub = self.create_publisher(String, topic, 10)
        self._perceptor = RealSenseYoloPerceptor(settings)
        rate = float(self.get_parameter("rate_hz").value)
        self.create_timer(1.0 / rate, self._tick)
        self.get_logger().info(f"Publishing detections on {topic}")

    def _tick(self) -> None:
        try:
            result = self._perceptor.perceive()
        except Exception as exc:
            self.get_logger().error(f"Perception failed: {exc}")
            return

        payload = {
            "scene_summary": result.scene_summary,
            "free_space_ratio": result.free_space_ratio,
            "objects": [
                {
                    "label": o.label,
                    "color": o.color,
                    "position": o.position.as_list(),
                    "confidence": o.confidence,
                    "bbox": o.bbox,
                }
                for o in result.objects
            ],
        }
        msg = String()
        msg.data = json.dumps(payload)
        self._pub.publish(msg)


def main() -> None:
    rclpy.init()
    node = YoloRealSenseNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node._perceptor.close()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
