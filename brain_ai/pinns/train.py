"""Train PINN on synthetic physics violations (xArm6 grasp dynamics)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

from brain_ai.pinns.network import PhysicsInformedNet
from config.ai_models import ModelPaths, get_training_settings


def _synthetic_dataset(n: int = 8000, seed: int = 42) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    X = np.zeros((n, 6), dtype=np.float32)
    Y = np.zeros((n, 5), dtype=np.float32)

    for i in range(n):
        vx, vy, vz = rng.uniform(-1.2, 1.2, 3)
        force = rng.uniform(0, 30)
        mass = rng.uniform(0.1, 2.0)
        fragile = rng.choice([0.0, 1.0])
        X[i] = [vx, vy, vz, force, mass, fragile]

        speed = (vx**2 + vy**2 + vz**2) ** 0.5
        safe = 1.0
        scale_v = 1.0
        scale_f = 1.0

        if speed > 0.8:
            safe = 0.0
            scale_v = 0.8 / max(speed, 1e-6)
        if force > 25:
            safe = 0.0
            scale_f = 25.0 / force
        if fragile > 0.5 and force > 15:
            safe = 0.0
            scale_f = min(scale_f, 12.0 / force)

        # Physics residual: F = ma heuristic
        accel_est = speed * 10
        if accel_est > mass * 15:
            safe = 0.0
            scale_v *= 0.9

        Y[i, 0] = safe
        Y[i, 1] = vx * scale_v
        Y[i, 2] = vy * scale_v
        Y[i, 3] = vz * scale_v
        Y[i, 4] = scale_f

    return X, Y


def train_pinn(
    output_path: Path | None = None,
    epochs: int | None = None,
    device: str | None = None,
) -> Path:
    settings = get_training_settings()
    paths = ModelPaths()
    out = output_path or paths.pinn_torch
    out.parent.mkdir(parents=True, exist_ok=True)
    epochs = epochs or settings.pinn_epochs

    if device == "auto" or not device:
        device = "cuda" if torch.cuda.is_available() else "cpu"

    X, Y = _synthetic_dataset()
    ds = TensorDataset(torch.from_numpy(X), torch.from_numpy(Y))
    loader = DataLoader(ds, batch_size=settings.pinn_batch_size, shuffle=True)

    model = PhysicsInformedNet().to(device)
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    bce = nn.BCEWithLogitsLoss()
    mse = nn.MSELoss()

    for epoch in range(epochs):
        total = 0.0
        for xb, yb in loader:
            xb, yb = xb.to(device), yb.to(device)
            pred = model(xb)
            loss_safe = bce(pred[:, 0], yb[:, 0])
            loss_corr = mse(pred[:, 1:], yb[:, 1:])
            loss = loss_safe + 0.5 * loss_corr
            opt.zero_grad()
            loss.backward()
            opt.step()
            total += loss.item()
        if (epoch + 1) % 50 == 0:
            print(f"PINN epoch {epoch + 1}/{epochs} loss={total / len(loader):.4f}")

    torch.save({"state_dict": model.state_dict(), "input_dim": 6}, out)
    print(f"Saved PINN to {out}")
    return out


if __name__ == "__main__":
    train_pinn()
