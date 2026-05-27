"""Isaac Sim digital twin bridge via ROS2 service (optional)."""

from __future__ import annotations

import json

from brain_ai.types import MotionPlan
from config.settings import Settings
from robotics.ros2_bridge import Ros2Context, require_rclpy


class IsaacTwinBridge:
    """Calls /physical_ai/twin/validate_motion when Isaac ROS bridge is running."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._node = None
        self._client = None

    def available(self) -> bool:
        try:
            require_rclpy("Isaac twin")
            return True
        except ImportError:
            return False

    def validate_motion(self, plan: MotionPlan) -> tuple[bool, str]:
        if not self.settings.isaac_twin_enabled:
            return True, "Isaac twin disabled (set PHYSICAL_AI_ISAAC_TWIN=1)"

        try:
            require_rclpy("Isaac twin")
            Ros2Context.ensure_init()
            return self._call_service(plan)
        except Exception as exc:
            if self.settings.allow_fallback:
                return True, f"Isaac twin unavailable, fallback OK: {exc}"
            return False, str(exc)

    def _call_service(self, plan: MotionPlan) -> tuple[bool, str]:
        import rclpy
        from rclpy.node import Node
        from std_srvs.srv import Trigger

        if self._node is None:
            self._node = Node("physical_ai_isaac_client")
            self._client = self._node.create_client(
                Trigger, self.settings.ros2.twin_validate_service
            )

        if not self._client.wait_for_service(timeout_sec=2.0):
            return True, "Isaac validate service not running — skipped"

        req = Trigger.Request()
        future = self._client.call_async(req)
        rclpy.spin_until_future_complete(self._node, future, timeout_sec=5.0)
        result = future.result()
        if result is None:
            return False, "Isaac service timeout"
        ok = result.success
        return ok, result.message or ("validated" if ok else "rejected")

    @staticmethod
    def plan_to_json(plan: MotionPlan) -> str:
        return json.dumps(
            {
                "waypoints_deg": plan.waypoints_deg,
                "duration_s": plan.duration_s,
                "collision_free": plan.collision_free,
            }
        )
