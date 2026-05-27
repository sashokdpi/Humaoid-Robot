"""Trained PINN inference for production pipeline."""

from __future__ import annotations

from pathlib import Path

import torch

from brain_ai.pinns.network import PhysicsInformedNet
from brain_ai.pinns.validator import PhysicsValidator, SimulatedPhysicsValidator
from brain_ai.types import DetectedObject, PhysicsVerdict, RLAction, Vector3
from config.ai_models import ModelPaths


class TrainedPINNValidator(PhysicsValidator):
    def __init__(self, model_path: Path, device: str = "cpu") -> None:
        self.device = device
        ckpt = torch.load(model_path, map_location=device, weights_only=False)
        self.model = PhysicsInformedNet()
        self.model.load_state_dict(ckpt["state_dict"])
        self.model.eval()
        self.model.to(device)
        self._fallback = SimulatedPhysicsValidator()

    def validate(self, action: RLAction, target: DetectedObject | None) -> PhysicsVerdict:
        mass = 0.5 if target and target.label == "bottle" else 1.0
        fragile = 1.0 if target and target.label == "bottle" else 0.0
        x = torch.tensor(
            [
                [
                    action.ee_velocity.x,
                    action.ee_velocity.y,
                    action.ee_velocity.z,
                    action.gripper_force,
                    mass,
                    fragile,
                ]
            ],
            dtype=torch.float32,
            device=self.device,
        )
        with torch.no_grad():
            out = self.model(x)[0].cpu().numpy()

        safe_logit, cvx, cvy, cvz, fscale = out
        safe = float(safe_logit) > 0.0

        corrected = RLAction(
            joint_torques=list(action.joint_torques),
            gripper_force=action.gripper_force * max(float(fscale), 0.1),
            ee_velocity=Vector3(float(cvx), float(cvy), float(cvz)),
        )

        if not safe:
            # Blend with rule-based fallback for hard constraints
            fb = self._fallback.validate(action, target)
            return PhysicsVerdict(
                safe=fb.safe,
                corrected_action=fb.corrected_action or corrected,
                reason=f"PINN unsafe → {fb.reason}",
                corrections={"pinn_safe_logit": float(safe_logit), **fb.corrections},
            )

        return PhysicsVerdict(
            safe=True,
            corrected_action=corrected,
            reason="Trained PINN validated action",
            corrections={"pinn_safe_logit": float(safe_logit)},
        )


def build_pinn_validator(simulation: bool) -> PhysicsValidator:
    paths = ModelPaths()
    if paths.pinn_available():
        device = "cuda" if torch.cuda.is_available() else "cpu"
        return TrainedPINNValidator(paths.pinn_torch, device=device)
    return SimulatedPhysicsValidator()
