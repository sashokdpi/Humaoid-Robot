"""
Closed-loop Physical AI pipeline:
Human Command -> Agentic -> Perception -> World Model -> Twin -> PINN -> RL -> Motion -> Execute -> Learn
"""

from __future__ import annotations

from brain_ai.agentic_ai.graph import build_executive
from brain_ai.agentic_ai.safety import SafetyAgent
from brain_ai.perception.vision import build_vision_system
from brain_ai.pinns.validator import build_physics_validator
from brain_ai.reinforcement_learning.policy import build_grasp_policy
from brain_ai.types import PipelineResult, SubGoal, TaskStatus
from brain_ai.world_model.model import WorldModel
from config.settings import Settings, get_settings
from digital_twin.twin import build_digital_twin
from hardware.gripper import build_gripper, is_pick_command, is_place_command
from hardware.simulator import build_robot_driver
from observability.tracer import Tracer
from robotics.motion_planner import build_motion_planner
from robotics.robot_state import initial_robot_state


class PhysicalAIOrchestrator:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.tracer = Tracer(enabled=self.settings.trace_enabled)
        self.executive = build_executive()
        self.vision = build_vision_system(self.settings)
        self.world_model = WorldModel()
        self.physics = build_physics_validator(self.settings.is_simulation)
        self.rl_policy = build_grasp_policy(self.settings)
        self.motion = build_motion_planner(self.settings)
        self.twin = build_digital_twin(self.settings)
        self.safety = SafetyAgent()
        self.robot = build_robot_driver(self.settings)
        self.gripper = build_gripper(self.settings)

    def run(self, command: str) -> PipelineResult:
        span_user = self.tracer.start_span("user_command", command=command)

        # Step 1: Perception
        span_perc = self.tracer.start_span(
            "perception", backend=self.settings.perception_backend.value
        )
        perception = self.vision.perceive()
        self.tracer.end_span(span_perc, objects=len(perception.objects))

        robot_state = self.robot.get_state()
        world = self.world_model.update_from_perception(perception, robot_state)

        # Step 2: Cognitive planning
        span_plan = self.tracer.start_span(
            "agentic_planning",
            engine=type(self.executive).__name__,
        )
        plan = self.executive.plan(command, perception.objects)
        if plan.target_object is None and perception.objects:
            plan.target_object = perception.objects[0]
        self.tracer.end_span(span_plan, sub_goals=len(plan.sub_goals))

        target = plan.target_object
        if target is None:
            self.tracer.end_span(span_user, status="failed", reason="no_target")
            raise ValueError("No target object found for command")

        # Step 3: Digital twin sync + validation
        span_twin = self.tracer.start_span("digital_twin_sync")
        self.twin.sync(robot_state, world)
        self.tracer.end_span(span_twin)

        # Step 4: RL proposes grasp
        span_rl = self.tracer.start_span("rl_policy")
        rl_action = self.rl_policy.propose_grasp(target, robot_state)
        self._mark_subgoal(plan, "grasp", TaskStatus.SUCCESS)
        self.tracer.end_span(span_rl, gripper_force=rl_action.gripper_force)

        # Step 5: PINN validation
        span_pinn = self.tracer.start_span("pinn_validation")
        physics = self.physics.validate(rl_action, target)
        self._mark_subgoal(plan, "physics", TaskStatus.SUCCESS if physics.safe else TaskStatus.FAILED)
        self.tracer.end_span(span_pinn, safe=physics.safe, reason=physics.reason)

        if not physics.safe:
            self.tracer.end_span(span_user, status="failed", reason="physics_unsafe")
            raise RuntimeError(f"Unsafe action blocked: {physics.reason}")

        # Step 6: Motion planning
        span_motion = self.tracer.start_span("motion_planning")
        motion_plan = self.motion.plan_to_pose(robot_state, target.position, plan.place_position)
        twin_ok = self.twin.validate_motion(motion_plan)
        self._mark_subgoal(plan, "motion", TaskStatus.SUCCESS if twin_ok else TaskStatus.FAILED)
        self.tracer.end_span(span_motion, collision_free=motion_plan.collision_free, twin_ok=twin_ok)

        if not twin_ok:
            self.tracer.end_span(span_user, status="failed", reason="twin_rejected")
            raise RuntimeError("Digital twin rejected motion plan")

        # Step 7: Safety
        span_safety = self.tracer.start_span("safety_check")
        safe, safety_msg = self.safety.check(perception.objects, target.position)
        self._mark_subgoal(plan, "safety", TaskStatus.SUCCESS if safe else TaskStatus.FAILED)
        self.tracer.end_span(span_safety, safe=safe, message=safety_msg)

        if not safe:
            self.tracer.end_span(span_user, status="failed", reason="safety")
            raise RuntimeError(f"Safety agent blocked execution: {safety_msg}")

        # Step 8: Execute on robot (sim or hardware) + gripper
        span_exec = self.tracer.start_span("robot_execution", mode=self.settings.mode.value)
        if self.gripper and is_pick_command(command):
            span_grip_pre = self.tracer.start_span("gripper_open")
            self.gripper.open()
            self.tracer.end_span(span_grip_pre)

        execution = self.robot.execute_plan(motion_plan)
        self._mark_subgoal(plan, "execute", TaskStatus.SUCCESS if execution.success else TaskStatus.FAILED)

        if execution.success and self.gripper:
            if is_pick_command(command):
                span_grip = self.tracer.start_span("gripper_close", force=rl_action.gripper_force)
                self.gripper.close(rl_action.gripper_force)
                self.tracer.end_span(span_grip)
            elif is_place_command(command):
                span_grip = self.tracer.start_span("gripper_release")
                self.gripper.open()
                self.tracer.end_span(span_grip)

        self.tracer.end_span(span_exec, success=execution.success, gripper=bool(self.gripper))

        # Step 9: Continuous learning hook (log only in scaffold)
        span_learn = self.tracer.start_span("continuous_learning", action="log_feedback")
        self.tracer.end_span(span_learn, reward=1.0 if execution.success else -1.0)

        self.tracer.end_span(span_user, status="ok" if execution.success else "failed")

        return PipelineResult(
            command=command,
            plan=plan,
            perception=perception,
            physics=physics,
            motion=motion_plan,
            execution=execution,
            trace_id=self.tracer.trace_id,
        )

    def trace_summary(self) -> list[dict]:
        return self.tracer.summary()

    @staticmethod
    def _mark_subgoal(plan, goal_id: str, status: TaskStatus) -> None:
        for sg in plan.sub_goals:
            if sg.id == goal_id:
                sg.status = status
                break
