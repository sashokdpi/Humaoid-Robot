"""Standard UFACTORY parallel gripper — simulation + ROS2 (/xarm/set_gripper_*)."""

from __future__ import annotations

from abc import ABC, abstractmethod

from config.gripper import GripperSettings
from config.settings import Settings, RobotBackend


class GripperController(ABC):
    @abstractmethod
    def open(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def close(self, gripper_force: float = 15.0) -> None:
        raise NotImplementedError

    @property
    @abstractmethod
    def is_open(self) -> bool:
        raise NotImplementedError


class SimulatedGripper(GripperController):
    def __init__(self, settings: GripperSettings) -> None:
        self.settings = settings
        self._open = True

    @property
    def is_open(self) -> bool:
        return self._open

    def open(self) -> None:
        self._open = True

    def close(self, gripper_force: float = 15.0) -> None:
        self._open = False


class XArmRos2Gripper(GripperController):
    """Uses /xarm/set_gripper_* services and optional GripperCommand action."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.gripper = settings.gripper
        self._node = None
        self._open = True
        self._initialized = False

    @property
    def is_open(self) -> bool:
        return self._open

    def _ensure_node(self) -> None:
        if self._node is not None:
            return
        from robotics.ros2_bridge import Ros2Context, require_rclpy

        require_rclpy("xArm gripper")
        Ros2Context.ensure_init()
        from rclpy.node import Node

        self._node = Node("physical_ai_gripper")
        if not self._initialized:
            self._call_enable()
            self._initialized = True

    def _call_enable(self) -> None:
        try:
            self._call_set_int16(self.gripper.service_enable, 1)
            self._call_set_int16(self.gripper.service_mode, 0)
            self._call_set_float32(self.gripper.service_speed, float(self.gripper.default_speed))
        except Exception:
            pass  # Services may already be configured by xarm driver

    def open(self) -> None:
        self._ensure_node()
        pos = self.gripper.open_position_mm
        if self._set_position_mm(pos):
            self._open = True
            return
        self._send_gripper_action(self.gripper.open_rad)

    def close(self, gripper_force: float = 15.0) -> None:
        self._ensure_node()
        pos = self.gripper.position_mm_from_force(gripper_force)
        if self._set_position_mm(pos):
            self._open = False
            return
        rad = self.gripper.rad_from_open_ratio(0.05)
        self._send_gripper_action(rad)

    def _set_position_mm(self, pos_mm: int) -> bool:
        try:
            from xarm_msgs.srv import GripperMove

            client = self._node.create_client(GripperMove, self.gripper.service_set_position)
            if not client.wait_for_service(timeout_sec=1.5):
                return False
            req = GripperMove.Request()
            req.pos = float(pos_mm)
            future = client.call_async(req)
            import rclpy

            rclpy.spin_until_future_complete(self._node, future, timeout_sec=3.0)
            return future.result() is not None
        except ImportError:
            return False
        except Exception:
            return False

    def _send_gripper_action(self, position_rad: float) -> None:
        try:
            from control_msgs.action import GripperCommand
            from rclpy.action import ActionClient
            import rclpy

            client = ActionClient(
                self._node, GripperCommand, self.gripper.action_name
            )
            if not client.wait_for_server(timeout_sec=1.5):
                return
            goal = GripperCommand.Goal()
            goal.command.position = float(position_rad)
            goal.command.max_effort = 0.0
            send = client.send_goal_async(goal)
            rclpy.spin_until_future_complete(self._node, send, timeout_sec=3.0)
            handle = send.result()
            if handle and handle.accepted:
                result_f = handle.get_result_async()
                rclpy.spin_until_future_complete(self._node, result_f, timeout_sec=5.0)
            self._open = position_rad < 0.1
        except Exception:
            pass

    def _call_set_int16(self, service: str, value: int) -> None:
        from xarm_msgs.srv import SetInt16
        import rclpy

        client = self._node.create_client(SetInt16, service)
        if not client.wait_for_service(timeout_sec=1.0):
            return
        req = SetInt16.Request()
        req.data = int(value)
        future = client.call_async(req)
        rclpy.spin_until_future_complete(self._node, future, timeout_sec=2.0)

    def _call_set_float32(self, service: str, value: float) -> None:
        from xarm_msgs.srv import SetFloat32
        import rclpy

        client = self._node.create_client(SetFloat32, service)
        if not client.wait_for_service(timeout_sec=1.0):
            return
        req = SetFloat32.Request()
        req.data = float(value)
        future = client.call_async(req)
        rclpy.spin_until_future_complete(self._node, future, timeout_sec=2.0)


def build_gripper(settings: Settings) -> GripperController | None:
    if not settings.gripper.enabled:
        return None
    if settings.robot_backend == RobotBackend.ROS2 and not settings.is_simulation:
        try:
            return XArmRos2Gripper(settings)
        except ImportError:
            if settings.allow_fallback:
                return SimulatedGripper(settings.gripper)
            raise
    return SimulatedGripper(settings.gripper)


def is_pick_command(command: str) -> bool:
    c = command.lower()
    return any(w in c for w in ("pick", "grasp", "grab", "take"))

def is_place_command(command: str) -> bool:
    c = command.lower()
    return any(w in c for w in ("place", "put", "drop", "release"))
