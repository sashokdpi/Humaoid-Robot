"""ROS2 robot driver: joint_states + FollowJointTrajectory."""

from __future__ import annotations

import time

from brain_ai.types import ExecutionResult, MotionPlan, RobotState, Vector3
from config.settings import Settings
from hardware.simulator import RobotDriver
from robotics.ros2_bridge import Ros2Context, deg_list_to_rad, rad_list_to_deg, require_rclpy


class Ros2RobotDriver(RobotDriver):
    def __init__(self, settings: Settings, fallback: RobotDriver | None = None) -> None:
        self.settings = settings
        self.fallback = fallback
        self._node = None
        self._joint_state: RobotState | None = None
        self._joint_map: dict[str, float] = {}

    def _ensure_node(self) -> None:
        if self._node is not None:
            return
        require_rclpy("ROS2 robot driver")
        Ros2Context.ensure_init()
        import rclpy
        from rclpy.node import Node
        from sensor_msgs.msg import JointState

        node = Node("physical_ai_robot_driver")

        def joint_cb(msg: JointState) -> None:
            for name, pos in zip(msg.name, msg.position):
                self._joint_map[name] = pos
            ordered = []
            for jn in self.settings.joint_names:
                if jn in self._joint_map:
                    ordered.append(self._joint_map[jn])
            if ordered:
                gripper_open = True
                gj = self.settings.gripper.joint_name
                if gj in self._joint_map:
                    # xArm drive_joint: ~0 rad open, ~0.86 rad closed
                    gripper_open = self._joint_map[gj] < 0.15
                self._joint_state = RobotState(
                    joint_angles_deg=rad_list_to_deg(ordered),
                    gripper_open=gripper_open,
                    ee_position=None,
                )

        node.create_subscription(JointState, self.settings.ros2.joint_states_topic, joint_cb, 10)
        self._node = node
        deadline = time.time() + self.settings.ros2.spin_timeout_s
        while time.time() < deadline and self._joint_state is None:
            rclpy.spin_once(node, timeout_sec=0.2)

    def get_state(self) -> RobotState:
        self._ensure_node()
        import rclpy

        if self._joint_state is None:
            rclpy.spin_once(self._node, timeout_sec=0.5)
        if self._joint_state is None:
            if self.fallback:
                return self.fallback.get_state()
            raise RuntimeError(f"No data on {self.settings.ros2.joint_states_topic}")
        return self._joint_state

    def execute_plan(self, plan: MotionPlan) -> ExecutionResult:
        self._ensure_node()
        require_rclpy("trajectory execution")

        try:
            return self._execute_trajectory(plan)
        except Exception as exc:
            if self.fallback and self.settings.allow_fallback:
                return self.fallback.execute_plan(plan)
            return ExecutionResult(
                success=False,
                final_state=self.get_state(),
                message=f"ROS2 execution failed: {exc}",
            )

    def _execute_trajectory(self, plan: MotionPlan) -> ExecutionResult:
        import rclpy
        from control_msgs.action import FollowJointTrajectory
        from rclpy.action import ActionClient
        from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint

        client = ActionClient(
            self._node,
            FollowJointTrajectory,
            self.settings.ros2.trajectory_action,
        )
        if not client.wait_for_server(timeout_sec=self.settings.ros2.spin_timeout_s):
            raise RuntimeError(f"Action server not available: {self.settings.ros2.trajectory_action}")

        traj = JointTrajectory()
        traj.joint_names = list(self.settings.joint_names)
        dt = plan.duration_s / max(len(plan.waypoints_deg), 1)
        for i, wp in enumerate(plan.waypoints_deg):
            pt = JointTrajectoryPoint()
            pt.positions = deg_list_to_rad(wp)
            pt.time_from_start.sec = int(i * dt)
            pt.time_from_start.nanosec = int((i * dt % 1) * 1e9)
            traj.points.append(pt)

        goal = FollowJointTrajectory.Goal()
        goal.trajectory = traj

        send = client.send_goal_async(goal)
        rclpy.spin_until_future_complete(self._node, send, timeout_sec=plan.duration_s + 5)
        goal_handle = send.result()
        if not goal_handle.accepted:
            raise RuntimeError("Trajectory goal rejected")

        result_future = goal_handle.get_result_async()
        rclpy.spin_until_future_complete(self._node, result_future, timeout_sec=plan.duration_s + 10)

        state = self.get_state()
        return ExecutionResult(
            success=True,
            final_state=state,
            message=f"ROS2 trajectory executed ({len(plan.waypoints_deg)} points)",
        )
