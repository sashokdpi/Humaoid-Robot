"""HTTP API for sending commands to the Physical AI pipeline."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from brain_ai.orchestrator import PhysicalAIOrchestrator
from config.settings import RunMode, get_settings

app = FastAPI(title="Physical AI System", version="0.1.0")
_orchestrator: PhysicalAIOrchestrator | None = None


class CommandRequest(BaseModel):
    command: str = Field(..., examples=["Pick the red bottle"])
    mode: RunMode | None = None


def get_orchestrator() -> PhysicalAIOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = PhysicalAIOrchestrator(get_settings())
    return _orchestrator


@app.get("/health")
def health() -> dict:
    settings = get_settings()
    return {"status": "ok", "mode": settings.mode.value, "robot": settings.robot_name}


@app.post("/command")
def run_command(body: CommandRequest) -> dict:
    settings = get_settings()
    if body.mode:
        settings.mode = body.mode
    orchestrator = PhysicalAIOrchestrator(settings)
    try:
        result = orchestrator.run(body.command)
    except (ValueError, RuntimeError, NotImplementedError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    target = result.plan.target_object
    return {
        "success": result.execution.success,
        "trace_id": result.trace_id,
        "target": {
            "label": target.label if target else None,
            "color": target.color if target else None,
            "position": target.position.as_list() if target else None,
        },
        "physics_reason": result.physics.reason,
        "execution": result.execution.message,
        "trace": orchestrator.trace_summary(),
    }
