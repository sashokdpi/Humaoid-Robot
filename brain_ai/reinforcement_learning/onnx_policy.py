"""Load trained RL policy (PyTorch or ONNX) for grasp execution."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from brain_ai.reinforcement_learning.policy import GraspPolicy, SimulatedGraspPolicy
from brain_ai.types import DetectedObject, RLAction, RobotState, Vector3
from config.ai_models import ModelPaths
from config.settings import Settings


class TorchGraspPolicy(GraspPolicy):
    def __init__(self, model_path: Path, settings: Settings) -> None:
        import torch

        from brain_ai.reinforcement_learning.ppo_policy import ActorCritic

        self.settings = settings
        ckpt = torch.load(model_path, map_location="cpu", weights_only=False)
        self.obs_dim = int(ckpt["obs_dim"])
        self.act_dim = int(ckpt["act_dim"])
        self.policy = ActorCritic(self.obs_dim, self.act_dim)
        self.policy.load_state_dict(ckpt["policy_state_dict"])
        self.policy.eval()
        self._torch = torch

    def propose_grasp(self, target: DetectedObject, robot: RobotState) -> RLAction:
        obs = self._build_obs(target, robot)
        with self._torch.no_grad():
            mean = self.policy.actor(
                self._torch.tensor(obs, dtype=self._torch.float32).unsqueeze(0)
            )[0].numpy()
        return self._action_to_rl(mean, target)

    def _build_obs(self, target: DetectedObject, robot: RobotState) -> np.ndarray:
        joints = np.array(robot.joint_angles_deg, dtype=np.float32)[:6]
        if len(joints) < 6:
            joints = np.pad(joints, (0, 6 - len(joints)))
        joints = np.deg2rad(joints)
        obj = np.array(target.position.as_list(), dtype=np.float32)
        grip = np.array([1.0 if robot.gripper_open else 0.0], dtype=np.float32)
        obs = np.concatenate([joints, obj, grip])
        if obs.shape[0] < self.obs_dim:
            obs = np.pad(obs, (0, self.obs_dim - obs.shape[0]))
        return obs[: self.obs_dim]

    def _action_to_rl(self, action: np.ndarray, target: DetectedObject) -> RLAction:
        n = self.settings.joint_count
        j_delta = action[:n]
        force = float((action[n] + 1) / 2 * 25) if len(action) > n else 15.0
        return RLAction(
            joint_torques=(j_delta * 3.0).tolist(),
            gripper_force=force,
            ee_velocity=Vector3(0.3, 0.1, 0.05),
        )


class OnnxGraspPolicy(GraspPolicy):
    def __init__(self, onnx_path: Path, settings: Settings) -> None:
        import onnxruntime as ort

        self.settings = settings
        providers = ort.get_available_providers()
        preferred = []
        if "CUDAExecutionProvider" in providers:
            preferred.append("CUDAExecutionProvider")
        if "TensorrtExecutionProvider" in providers:
            preferred.append("TensorrtExecutionProvider")
        preferred.append("CPUExecutionProvider")
        self.session = ort.InferenceSession(str(onnx_path), providers=preferred)
        self.input_name = self.session.get_inputs()[0].name
        self._torch_policy: TorchGraspPolicy | None = None
        paths = ModelPaths()
        if paths.rl_torch.exists():
            self._torch_policy = TorchGraspPolicy(paths.rl_torch, settings)

    def propose_grasp(self, target: DetectedObject, robot: RobotState) -> RLAction:
        if self._torch_policy:
            obs = self._torch_policy._build_obs(target, robot)
        else:
            obs = np.zeros(10, dtype=np.float32)
        out = self.session.run(None, {self.input_name: obs.astype(np.float32)[None, :]})[0][0]
        if self._torch_policy:
            return self._torch_policy._action_to_rl(out, target)
        n = self.settings.joint_count
        return RLAction(
            joint_torques=(out[:n] * 3).tolist(),
            gripper_force=float((out[n] + 1) / 2 * 25) if len(out) > n else 15.0,
            ee_velocity=Vector3(0.3, 0.1, 0.05),
        )


def export_rl_onnx(torch_path: Path | None = None, onnx_path: Path | None = None) -> Path:
    import torch

    paths = ModelPaths()
    torch_path = torch_path or paths.rl_torch
    onnx_path = onnx_path or paths.rl_onnx
    onnx_path.parent.mkdir(parents=True, exist_ok=True)

    ckpt = torch.load(torch_path, map_location="cpu", weights_only=False)
    from brain_ai.reinforcement_learning.ppo_policy import ActorCritic

    policy = ActorCritic(int(ckpt["obs_dim"]), int(ckpt["act_dim"]))
    policy.load_state_dict(ckpt["policy_state_dict"])
    policy.eval()

    dummy = torch.zeros(1, int(ckpt["obs_dim"]))
    policy.eval()
    traced = torch.jit.trace(policy.actor, dummy)
    export_kwargs = dict(
        input_names=["observation"],
        output_names=["action"],
        dynamic_axes={"observation": {0: "batch"}, "action": {0: "batch"}},
        opset_version=18,
    )
    try:
        torch.onnx.export(traced, dummy, str(onnx_path), dynamo=False, **export_kwargs)
    except TypeError:
        torch.onnx.export(traced, dummy, str(onnx_path), **export_kwargs)
    print(f"Exported ONNX to {onnx_path}")
    return onnx_path
