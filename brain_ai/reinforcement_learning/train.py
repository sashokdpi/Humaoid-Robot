"""PPO training for xArm6 grasp (standalone sim; export for Isaac Lab later)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import torch
import torch.nn as nn

from brain_ai.reinforcement_learning.env import GraspSimEnv
from brain_ai.reinforcement_learning.ppo_policy import ActorCritic
from config.ai_models import ModelPaths, get_training_settings


def train_grasp_ppo(
    output_path: Path | None = None,
    timesteps: int | None = None,
    device: str | None = None,
) -> Path:
    settings = get_training_settings()
    paths = ModelPaths()
    out = output_path or paths.rl_torch
    out.parent.mkdir(parents=True, exist_ok=True)
    timesteps = timesteps or settings.rl_timesteps

    if device == "auto" or not device:
        device = "cuda" if torch.cuda.is_available() else "cpu"

    env = GraspSimEnv()
    obs_dim = env.observation_space.shape[0]
    act_dim = env.action_space.shape[0]

    policy = ActorCritic(obs_dim, act_dim).to(device)
    opt = torch.optim.Adam(policy.parameters(), lr=settings.rl_learning_rate)

    gamma, gae_lambda = 0.99, 0.95
    clip_eps = 0.2
    rollout_steps = 512
    n_epochs = 4

    obs, _ = env.reset()
    global_step = 0

    while global_step < timesteps:
        obs_buf, act_buf, rew_buf, logp_buf, val_buf, done_buf = [], [], [], [], [], []

        for _ in range(rollout_steps):
            o_t = torch.tensor(obs, dtype=torch.float32, device=device).unsqueeze(0)
            with torch.no_grad():
                action, logp, value = policy.act(o_t)
            action_np = action.cpu().numpy()[0]
            next_obs, reward, term, trunc, _ = env.step(action_np)
            done = term or trunc

            obs_buf.append(obs)
            act_buf.append(action_np)
            rew_buf.append(reward)
            logp_buf.append(logp.item())
            val_buf.append(value.item())
            done_buf.append(float(done))

            obs = next_obs
            global_step += 1
            if done:
                obs, _ = env.reset()
            if global_step >= timesteps:
                break

        # GAE
        advantages = []
        gae = 0.0
        values = val_buf + [0.0]
        for t in reversed(range(len(rew_buf))):
            delta = rew_buf[t] + gamma * values[t + 1] * (1 - done_buf[t]) - values[t]
            gae = delta + gamma * gae_lambda * (1 - done_buf[t]) * gae
            advantages.insert(0, gae)
        returns = [a + v for a, v in zip(advantages, val_buf)]

        obs_t = torch.tensor(np.array(obs_buf), dtype=torch.float32, device=device)
        act_t = torch.tensor(np.array(act_buf), dtype=torch.float32, device=device)
        logp_old = torch.tensor(logp_buf, dtype=torch.float32, device=device)
        adv_t = torch.tensor(advantages, dtype=torch.float32, device=device)
        ret_t = torch.tensor(returns, dtype=torch.float32, device=device)
        adv_t = (adv_t - adv_t.mean()) / (adv_t.std() + 1e-8)

        for _ in range(n_epochs):
            logp, entropy, value = policy.evaluate(obs_t, act_t)
            ratio = (logp - logp_old).exp()
            surr1 = ratio * adv_t
            surr2 = torch.clamp(ratio, 1 - clip_eps, 1 + clip_eps) * adv_t
            actor_loss = -torch.min(surr1, surr2).mean()
            critic_loss = nn.functional.mse_loss(value, ret_t)
            loss = actor_loss + 0.5 * critic_loss - 0.01 * entropy.mean()

            opt.zero_grad()
            loss.backward()
            opt.step()

        if global_step % 5000 < rollout_steps:
            print(f"RL step {global_step}/{timesteps} last_reward={rew_buf[-1]:.2f}")

    torch.save(
        {
            "policy_state_dict": policy.state_dict(),
            "obs_dim": obs_dim,
            "act_dim": act_dim,
        },
        out,
    )
    print(f"Saved RL policy to {out}")
    return out


if __name__ == "__main__":
    train_grasp_ppo()
