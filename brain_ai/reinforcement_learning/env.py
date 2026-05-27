"""Grasp simulation environment (Isaac Lab–compatible interface; standalone Gymnasium env)."""

from __future__ import annotations

import numpy as np

try:
    import gymnasium as gym
    from gymnasium import spaces
except ImportError:
    gym = None
    spaces = None


class GraspSimEnv:
    """
    State: joint angles (6), object offset (3), gripper open (1)
    Action: joint velocity deltas (6), gripper force command (1)
  Reward: reach + grasp success - collision/force penalty
    """

    metadata = {"render_modes": []}

    def __init__(self, joint_count: int = 6) -> None:
        if gym is None:
            raise ImportError("Install gymnasium: pip install gymnasium")
        self.joint_count = joint_count
        obs_dim = joint_count + 3 + 1
        act_dim = joint_count + 1
        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf, shape=(obs_dim,), dtype=np.float32
        )
        self.action_space = spaces.Box(
            low=-1.0, high=1.0, shape=(act_dim,), dtype=np.float32
        )
        self._reset_internal()

    def _reset_internal(self) -> None:
        self.joints = np.zeros(self.joint_count, dtype=np.float32)
        self.object_pos = np.array([0.45, 0.12, 0.82], dtype=np.float32)
        self.gripper_open = 1.0
        self.steps = 0

    def reset(self, seed=None, options=None):
        if seed is not None:
            np.random.seed(seed)
        self._reset_internal()
        self.object_pos += np.random.uniform(-0.05, 0.05, 3).astype(np.float32)
        return self._obs(), {}

    def _obs(self) -> np.ndarray:
        return np.concatenate([self.joints, self.object_pos, [self.gripper_open]]).astype(
            np.float32
        )

    def step(self, action: np.ndarray):
        self.steps += 1
        j_delta = action[: self.joint_count] * 0.05
        force_cmd = (action[self.joint_count] + 1) / 2 * 25  # 0..25
        self.joints = np.clip(self.joints + j_delta, -3.14, 3.14)

        ee = self._fk_approx()
        dist = float(np.linalg.norm(ee - self.object_pos))

        if force_cmd > 5 and dist < 0.08:
            self.gripper_open = 0.0

        reward = -dist - 0.01 * self.steps
        if dist < 0.05 and self.gripper_open < 0.5:
            reward += 5.0
        if force_cmd > 22:
            reward -= 2.0

        terminated = dist < 0.04 and self.gripper_open < 0.5
        truncated = self.steps >= 200
        return self._obs(), reward, terminated, truncated, {"dist": dist, "force": force_cmd}

    def _fk_approx(self) -> np.ndarray:
        # Rough EE position from first 3 joints
        j = self.joints
        x = 0.3 + 0.15 * np.cos(j[0]) + 0.12 * np.cos(j[1])
        y = 0.15 * np.sin(j[0]) + 0.1 * np.sin(j[1])
        z = 0.5 + 0.1 * j[2]
        return np.array([x, y, z], dtype=np.float32)


if gym is not None:

    class GraspGymEnv(gym.Env):
        def __init__(self):
            super().__init__()
            self._inner = GraspSimEnv()
            self.observation_space = self._inner.observation_space
            self.action_space = self._inner.action_space

        def reset(self, seed=None, options=None):
            return self._inner.reset(seed=seed, options=options)

        def step(self, action):
            return self._inner.step(action)
