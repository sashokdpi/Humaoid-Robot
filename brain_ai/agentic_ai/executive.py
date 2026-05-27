"""Cognitive layer: task decomposition and module orchestration."""

from __future__ import annotations

import re

from brain_ai.types import DetectedObject, Plan, SubGoal, TaskStatus, Vector3


class AgenticExecutive:
    """Planner / coordinator. Simulation uses rule-based decomposition; swap for LangGraph + LLM later."""

    def plan(self, command: str, perception_objects: list[DetectedObject] | None = None) -> Plan:
        command_lower = command.lower().strip()
        target = self._select_target(command_lower, perception_objects or [])
        place = Vector3.from_list([0.70, 0.40, 0.75])

        sub_goals = [
            SubGoal("scan", "Scan environment", "perception", TaskStatus.PENDING),
            SubGoal("detect", "Detect and localize objects", "perception", TaskStatus.PENDING),
            SubGoal("physics", "Validate grasp with physics model", "pinns", TaskStatus.PENDING),
            SubGoal("grasp", "Generate adaptive grasp policy", "rl", TaskStatus.PENDING),
            SubGoal("motion", "Plan collision-free trajectory", "motion", TaskStatus.PENDING),
            SubGoal("execute", "Execute robot motion", "motion", TaskStatus.PENDING),
            SubGoal("safety", "Verify human / workspace safety", "safety", TaskStatus.PENDING),
        ]

        if "clean" in command_lower or "table" in command_lower:
            sub_goals.insert(
                0,
                SubGoal("decompose", "Decompose table-cleaning workflow", "planner", TaskStatus.SUCCESS),
            )

        return Plan(command=command, sub_goals=sub_goals, target_object=target, place_position=place)

    def _select_target(
        self, command: str, objects: list[DetectedObject]
    ) -> DetectedObject | None:
        if not objects:
            return None

        color_match = re.search(r"\b(red|blue|green|yellow)\b", command)
        label_match = re.search(r"\b(bottle|tool|box)\b", command)

        candidates = objects
        if color_match:
            color = color_match.group(1)
            candidates = [o for o in candidates if o.color and o.color.lower() == color]
        if label_match:
            label = label_match.group(1)
            candidates = [o for o in candidates if o.label.lower() == label]

        if not candidates:
            return objects[0]
        return max(candidates, key=lambda o: o.confidence)
