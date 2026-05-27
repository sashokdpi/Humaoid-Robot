#!/usr/bin/env python3
"""Train PINN + RL grasp policies for Physical AI."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rl-steps", type=int, default=None)
    parser.add_argument("--pinn-epochs", type=int, default=None)
    parser.add_argument("--skip-onnx", action="store_true")
    args = parser.parse_args()

    from brain_ai.pinns.train import train_pinn
    from brain_ai.reinforcement_learning.train import train_grasp_ppo

    print("=== Training PINN ===")
    train_pinn(epochs=args.pinn_epochs)

    print("=== Training RL (PPO) ===")
    train_grasp_ppo(timesteps=args.rl_steps)

    if not args.skip_onnx:
        print("=== Exporting RL to ONNX (Jetson) ===")
        from brain_ai.reinforcement_learning.onnx_policy import export_rl_onnx

        export_rl_onnx()

    print("Done. Models in models/rl and models/pinn")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
