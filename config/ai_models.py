"""Paths and settings for trained RL / PINN / LLM models."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ModelPaths:
    root: Path = field(default_factory=lambda: Path(__file__).resolve().parents[1] / "models")
    rl_torch: Path = field(init=False)
    rl_onnx: Path = field(init=False)
    pinn_torch: Path = field(init=False)

    def __post_init__(self) -> None:
        self.rl_torch = self.root / "rl" / "grasp_policy.pt"
        self.rl_onnx = self.root / "rl" / "grasp_policy.onnx"
        self.pinn_torch = self.root / "pinn" / "physics_validator.pt"

    def rl_available(self) -> bool:
        return self.rl_onnx.exists() or self.rl_torch.exists()

    def pinn_available(self) -> bool:
        return self.pinn_torch.exists()


@dataclass
class LLMSettings:
    provider: str = "mock"  # mock | ollama | openai | azure
    model: str = "phi4"  # e.g. phi-4, gpt-4o-mini, llama3.2
    api_key: str = ""
    base_url: str = ""  # Ollama: http://localhost:11434/v1
    azure_endpoint: str = ""
    azure_deployment: str = ""
    temperature: float = 0.1
    use_langgraph: bool = True


@dataclass
class TrainingSettings:
    rl_timesteps: int = 50_000
    rl_learning_rate: float = 3e-4
    pinn_epochs: int = 200
    pinn_batch_size: int = 64
    device: str = "auto"


def get_model_paths() -> ModelPaths:
    root = Path(os.getenv("PHYSICAL_AI_MODELS_DIR", ModelPaths().root))
    paths = ModelPaths(root=root)
    return paths


def get_llm_settings() -> LLMSettings:
    return LLMSettings(
        provider=os.getenv("PHYSICAL_AI_LLM_PROVIDER", "mock"),
        model=os.getenv("PHYSICAL_AI_LLM_MODEL", "phi4"),
        api_key=os.getenv("PHYSICAL_AI_LLM_API_KEY", os.getenv("OPENAI_API_KEY", "")),
        base_url=os.getenv("PHYSICAL_AI_LLM_BASE_URL", "http://localhost:11434/v1"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", ""),
        azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT", ""),
        temperature=float(os.getenv("PHYSICAL_AI_LLM_TEMPERATURE", "0.1")),
        use_langgraph=os.getenv("PHYSICAL_AI_USE_LANGGRAPH", "1") == "1",
    )


def get_training_settings() -> TrainingSettings:
    return TrainingSettings(
        rl_timesteps=int(os.getenv("PHYSICAL_AI_RL_TIMESTEPS", "50000")),
        pinn_epochs=int(os.getenv("PHYSICAL_AI_PINN_EPOCHS", "200")),
        device=os.getenv("PHYSICAL_AI_TRAIN_DEVICE", "auto"),
    )
