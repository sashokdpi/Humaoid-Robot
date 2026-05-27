"""LangGraph multi-agent executive: Planner → Vision → Safety → Motion."""

from __future__ import annotations

from typing import Any, TypedDict

from brain_ai.agentic_ai.executive import AgenticExecutive
from brain_ai.agentic_ai.llm import get_chat_model, mock_plan_json, parse_llm_json
from brain_ai.agentic_ai.safety import SafetyAgent
from brain_ai.types import DetectedObject, Plan, SubGoal, TaskStatus, Vector3
from config.ai_models import get_llm_settings

SYSTEM_PROMPT = """You are the executive planner for a Physical AI xArm6 robot with UFACTORY gripper.
Given a user command and detected objects, output JSON only:
{
  "reasoning": "brief explanation",
  "steps": ["step1", "step2", ...],
  "target_hint": {"label": "bottle", "color": "red"},
  "place_position": [x, y, z],
  "safety_notes": "..."
}
Use SI meters. Prefer safe, short plans."""


class AgentState(TypedDict, total=False):
    command: str
    objects: list[DetectedObject]
    llm_plan: dict[str, Any]
    plan: Plan
    safety_ok: bool
    safety_message: str


class LangGraphExecutive:
    """Multi-agent orchestration via LangGraph."""

    def __init__(self) -> None:
        self._fallback = AgenticExecutive()
        self._safety = SafetyAgent()
        self._graph = self._build_graph()

    def plan(self, command: str, perception_objects: list[DetectedObject] | None = None) -> Plan:
        objects = perception_objects or []
        result = self._graph.invoke(
            {"command": command, "objects": objects},
        )
        return result["plan"]

    def _build_graph(self):
        try:
            from langgraph.graph import END, StateGraph
        except ImportError:
            return _MockGraph(self._fallback)

        graph = StateGraph(AgentState)
        graph.add_node("planner", self._node_planner)
        graph.add_node("vision", self._node_vision)
        graph.add_node("safety", self._node_safety)
        graph.add_node("motion", self._node_motion)

        graph.set_entry_point("planner")
        graph.add_edge("planner", "vision")
        graph.add_edge("vision", "safety")
        graph.add_edge("safety", "motion")
        graph.add_edge("motion", END)
        return graph.compile()

    def _node_planner(self, state: AgentState) -> AgentState:
        command = state["command"]
        objects = state.get("objects", [])
        summary = ", ".join(
            f"{o.color or ''} {o.label}@{o.position.as_list()}".strip() for o in objects
        ) or "no detections"

        llm = get_chat_model()
        if llm is None:
            plan_data = mock_plan_json(command, summary)
        else:
            from langchain_core.messages import HumanMessage, SystemMessage

            resp = llm.invoke(
                [
                    SystemMessage(content=SYSTEM_PROMPT),
                    HumanMessage(content=f"Command: {command}\nObjects: {summary}"),
                ]
            )
            plan_data = parse_llm_json(resp.content)

        state["llm_plan"] = plan_data
        return state

    def _node_vision(self, state: AgentState) -> AgentState:
        command = state["command"]
        objects = state.get("objects", [])
        base = self._fallback.plan(command, objects)
        hint = state.get("llm_plan", {}).get("target_hint", {})

        target = base.target_object
        if hint and objects:
            label = hint.get("label")
            color = hint.get("color")
            for o in objects:
                if label and o.label.lower() != str(label).lower():
                    continue
                if color and o.color and o.color.lower() != str(color).lower():
                    continue
                target = o
                break

        place_raw = state.get("llm_plan", {}).get("place_position")
        place = Vector3.from_list(place_raw) if place_raw else base.place_position

        steps_raw = state.get("llm_plan", {}).get("steps", [])
        sub_goals = [
            SubGoal(f"s{i}", desc, "planner", TaskStatus.SUCCESS)
            for i, desc in enumerate(steps_raw[:8])
        ] or base.sub_goals

        state["plan"] = Plan(
            command=command,
            sub_goals=sub_goals,
            target_object=target,
            place_position=place,
        )
        return state

    def _node_safety(self, state: AgentState) -> AgentState:
        plan = state["plan"]
        objects = state.get("objects", [])
        pos = plan.target_object.position if plan.target_object else None
        ok, msg = self._safety.check(objects, pos)
        state["safety_ok"] = ok
        state["safety_message"] = msg
        for sg in plan.sub_goals:
            if sg.module == "safety":
                sg.status = TaskStatus.SUCCESS if ok else TaskStatus.FAILED
        return state

    def _node_motion(self, state: AgentState) -> AgentState:
        plan = state["plan"]
        for sg in plan.sub_goals:
            if sg.module == "motion":
                sg.status = TaskStatus.PENDING
        if not state.get("safety_ok", True):
            plan.sub_goals.append(
                SubGoal("recovery", state.get("safety_message", "unsafe"), "recovery", TaskStatus.FAILED)
            )
        return state


class _MockGraph:
    """Runs fallback when LangGraph not installed."""

    def __init__(self, executive: AgenticExecutive) -> None:
        self._executive = executive

    def invoke(self, state: AgentState) -> AgentState:
        plan = self._executive.plan(state["command"], state.get("objects"))
        state["plan"] = plan
        return state


def build_executive():
    cfg = get_llm_settings()
    if cfg.use_langgraph:
        try:
            return LangGraphExecutive()
        except ImportError:
            pass
    return AgenticExecutive()
