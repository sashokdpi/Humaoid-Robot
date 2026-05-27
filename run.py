#!/usr/bin/env python3
"""CLI entry for Physical AI simulation pipeline."""

from __future__ import annotations

import argparse
import json
import sys

from brain_ai.orchestrator import PhysicalAIOrchestrator
from config.settings import PerceptionBackend, RunMode, get_settings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Physical AI — simulation-first control pipeline")
    parser.add_argument(
        "command",
        nargs="?",
        default="Pick the red bottle and place it in the recycle bin",
        help="High-level task command",
    )
    parser.add_argument(
        "--mode",
        choices=["simulation", "hybrid", "hardware"],
        default=None,
        help="simulation | hybrid (real camera, sim arm) | hardware (ROS2)",
    )
    parser.add_argument(
        "--perception",
        choices=["sim", "realsense_yolo", "ros2"],
        default=None,
        help="Override PHYSICAL_AI_PERCEPTION",
    )
    parser.add_argument("--json", action="store_true", help="Print machine-readable result")
    args = parser.parse_args(argv)

    settings = get_settings()
    if args.mode:
        settings.mode = RunMode(args.mode)
    if args.perception:
        settings.perception_backend = PerceptionBackend(args.perception)

    if settings.mode == RunMode.HARDWARE:
        print("Warning: hardware mode selected; ensure ROS2, MoveIt2, and Jetson policies are configured.")

    orchestrator = PhysicalAIOrchestrator(settings)

    try:
        result = orchestrator.run(args.command)
    except (ValueError, RuntimeError, NotImplementedError) as exc:
        print(f"Pipeline failed: {exc}", file=sys.stderr)
        if args.json:
            print(json.dumps({"success": False, "error": str(exc), "trace": orchestrator.trace_summary()}))
        return 1

    payload = {
        "success": result.execution.success,
        "command": result.command,
        "trace_id": result.trace_id,
        "target": {
            "label": result.plan.target_object.label if result.plan.target_object else None,
            "color": result.plan.target_object.color if result.plan.target_object else None,
            "position": result.plan.target_object.position.as_list() if result.plan.target_object else None,
        },
        "physics": {
            "safe": result.physics.safe,
            "reason": result.physics.reason,
            "corrections": result.physics.corrections,
        },
        "motion": {
            "waypoints": len(result.motion.waypoints_deg),
            "duration_s": result.motion.duration_s,
        },
        "execution": result.execution.message,
        "perception_summary": result.perception.scene_summary,
        "trace": orchestrator.trace_summary(),
    }

    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"Command: {result.command}")
        print(f"Robot: {settings.robot_name} ({settings.arm_variant})")
        print(f"Mode: {settings.mode.value}")
        print(f"Trace ID: {result.trace_id}")
        if result.plan.target_object:
            t = result.plan.target_object
            print(f"Target: {t.color} {t.label} @ {t.position.as_list()} (conf={t.confidence:.0%})")
        print(f"Physics: {result.physics.reason}")
        print(f"Motion: {len(result.motion.waypoints_deg)} waypoints, {result.motion.duration_s}s")
        print(f"Execution: {result.execution.message}")
        print("\nTrace:")
        for step in orchestrator.trace_summary():
            print(f"  - {step['name']}: {step.get('duration_ms', 0):.1f} ms [{step['status']}]")

    return 0 if result.execution.success else 1


if __name__ == "__main__":
    raise SystemExit(main())
