"""Physics-informed validation before motor execution."""

from __future__ import annotations

from abc import ABC, abstractmethod

from brain_ai.types import DetectedObject, PhysicsVerdict, RLAction, Vector3


class PhysicsValidator(ABC):
    @abstractmethod
    def validate(self, action: RLAction, target: DetectedObject | None) -> PhysicsVerdict:
        raise NotImplementedError


class SimulatedPhysicsValidator(PhysicsValidator):
    """
    Simplified dynamics checks (centripetal / force / stability).
    Replace with trained PINN when available.
    """

    MAX_GRIPPER_FORCE = 25.0
    MAX_EE_SPEED = 0.8  # m/s

    def validate(self, action: RLAction, target: DetectedObject | None) -> PhysicsVerdict:
        speed = (action.ee_velocity.x**2 + action.ee_velocity.y**2 + action.ee_velocity.z**2) ** 0.5
        corrections: dict[str, float] = {}

        if action.gripper_force > self.MAX_GRIPPER_FORCE:
            scale = self.MAX_GRIPPER_FORCE / action.gripper_force
            corrections["gripper_force_scale"] = scale
            action = RLAction(
                joint_torques=action.joint_torques,
                gripper_force=action.gripper_force * scale,
                ee_velocity=action.ee_velocity,
            )

        if speed > self.MAX_EE_SPEED:
            scale = self.MAX_EE_SPEED / speed
            corrections["ee_speed_scale"] = scale
            action = RLAction(
                joint_torques=[t * scale for t in action.joint_torques],
                gripper_force=action.gripper_force,
                ee_velocity=Vector3(
                    action.ee_velocity.x * scale,
                    action.ee_velocity.y * scale,
                    action.ee_velocity.z * scale,
                ),
            )
            reason = f"Reduced EE speed by {(1 - scale) * 100:.0f}% (centrifugal / stability limit)"
            return PhysicsVerdict(safe=True, corrected_action=action, reason=reason, corrections=corrections)

        if target and target.label == "bottle" and action.gripper_force > 18:
            action = RLAction(
                joint_torques=action.joint_torques,
                gripper_force=12.0,
                ee_velocity=action.ee_velocity,
            )
            corrections["gripper_force_scale"] = 12.0 / action.gripper_force
            return PhysicsVerdict(
                safe=True,
                corrected_action=action,
                reason="Reduced grip force for fragile bottle",
                corrections=corrections,
            )

        return PhysicsVerdict(safe=True, corrected_action=action, reason="Action within physics constraints")


class HardwarePhysicsValidator(PhysicsValidator):
    def validate(self, action: RLAction, target: DetectedObject | None) -> PhysicsVerdict:
        raise NotImplementedError("Deploy PINN model on Jetson for hardware validation")


def build_physics_validator(simulation: bool) -> PhysicsValidator:
    from brain_ai.pinns.inference import build_pinn_validator

    return build_pinn_validator(simulation)
