"""LLM backend for agentic planning (Phi-4 / Azure / Ollama / mock)."""

from __future__ import annotations

import json
import os
import re
from typing import Any

from config.ai_models import LLMSettings, get_llm_settings


def get_chat_model():
    """Return LangChain chat model or None for mock mode."""
    cfg = get_llm_settings()
    if cfg.provider == "mock":
        return None

    try:
        if cfg.provider == "azure":
            from langchain_openai import AzureChatOpenAI

            return AzureChatOpenAI(
                azure_endpoint=cfg.azure_endpoint or os.getenv("AZURE_OPENAI_ENDPOINT"),
                azure_deployment=cfg.azure_deployment or cfg.model,
                api_key=cfg.api_key or os.getenv("AZURE_OPENAI_API_KEY"),
                api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview"),
                temperature=cfg.temperature,
            )
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=cfg.model,
            api_key=cfg.api_key or "ollama",
            base_url=cfg.base_url or None,
            temperature=cfg.temperature,
        )
    except ImportError as exc:
        raise ImportError(
            "Install agentic deps: pip install langchain-openai langgraph"
        ) from exc


def mock_plan_json(command: str, objects_summary: str) -> dict[str, Any]:
    """Structured plan when no LLM API is configured."""
    command_lower = command.lower()
    steps = [
        "Scan workspace with vision",
        "Localize target object",
        "Validate physics constraints",
        "Generate RL grasp policy",
        "Plan collision-free trajectory with MoveIt2",
        "Execute on xArm6 with UFACTORY gripper",
    ]
    if "clean" in command_lower:
        steps.insert(0, "Decompose table-cleaning into pick-and-place subtasks")

    target_hint = {}
    for color in ("red", "blue", "green"):
        if color in command_lower:
            target_hint["color"] = color
    for label in ("bottle", "tool", "box"):
        if label in command_lower:
            target_hint["label"] = label

    return {
        "reasoning": f"Rule-based plan for: {command}",
        "steps": steps,
        "target_hint": target_hint,
        "place_position": [0.70, 0.40, 0.75],
        "safety_notes": "Keep human clearance > 0.5m",
    }


def parse_llm_json(text: str) -> dict[str, Any]:
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        return json.loads(match.group())
    return json.loads(text)
