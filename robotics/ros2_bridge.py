"""Optional ROS2 helpers — imports rclpy only when available (Linux / Jetson)."""

from __future__ import annotations

import json
import math
import threading
from typing import Any, Callable

_RCLPY = None
_RCLPY_CHECKED = False


def rclpy_available() -> bool:
    global _RCLPY, _RCLPY_CHECKED
    if _RCLPY_CHECKED:
        return _RCLPY is not None
    _RCLPY_CHECKED = True
    try:
        import rclpy  # noqa: F401

        _RCLPY = True
    except ImportError:
        _RCLPY = False
    return _RCLPY


def require_rclpy(feature: str) -> None:
    if not rclpy_available():
        raise ImportError(
            f"ROS2 rclpy required for {feature}. Source ROS2 Humble on Ubuntu/Jetson: "
            "source /opt/ros/humble/setup.bash"
        )


class Ros2Context:
    """Minimal rclpy lifecycle for short-lived bridge calls."""

    _lock = threading.Lock()
    _initialized = False

    @classmethod
    def ensure_init(cls) -> None:
        require_rclpy("ROS2 context")
        with cls._lock:
            if cls._initialized:
                return
            import rclpy

            if not rclpy.ok():
                rclpy.init()
            cls._initialized = True

    @classmethod
    def spin_once(cls, node: Any, timeout_s: float = 0.5) -> None:
        import rclpy

        rclpy.spin_once(node, timeout_sec=timeout_s)


def rad_list_to_deg(values: list[float]) -> list[float]:
    return [math.degrees(v) for v in values]


def deg_list_to_rad(values: list[float]) -> list[float]:
    return [math.radians(v) for v in values]


def parse_detection_json(payload: str) -> list[dict[str, Any]]:
    data = json.loads(payload)
    if isinstance(data, dict) and "objects" in data:
        return list(data["objects"])
    if isinstance(data, list):
        return data
    return []
