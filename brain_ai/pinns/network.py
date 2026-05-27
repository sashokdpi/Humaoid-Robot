"""Physics-informed neural network for action validation."""

from __future__ import annotations

import torch
import torch.nn as nn


class PhysicsInformedNet(nn.Module):
    """
    Input: [ee_vx, ee_vy, ee_vz, gripper_force, target_mass_est, target_fragile]
    Output: [safety_logit, corr_vx, corr_vy, corr_vz, corr_force_scale]
    """

    INPUT_DIM = 6
    OUTPUT_DIM = 5

    def __init__(self, hidden: int = 64) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(self.INPUT_DIM, hidden),
            nn.Tanh(),
            nn.Linear(hidden, hidden),
            nn.Tanh(),
            nn.Linear(hidden, self.OUTPUT_DIM),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)
