#!/usr/bin/env python3
"""Test RealSense + YOLO without full pipeline (requires camera + deps)."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config.settings import PerceptionBackend, get_settings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--frames", type=int, default=1)
    args = parser.parse_args()

    settings = get_settings()
    settings.perception_backend = PerceptionBackend.REALSENSE_YOLO
    settings.allow_fallback = False

    from brain_ai.perception.realsense_yolo import RealSenseYoloPerceptor

    perc = RealSenseYoloPerceptor(settings)
    try:
        for i in range(args.frames):
            result = perc.perceive()
            print(f"Frame {i + 1}: {result.scene_summary}")
            for obj in result.objects:
                print(
                    f"  - {obj.color or '?'} {obj.label} @ {obj.position.as_list()} "
                    f"({obj.confidence:.0%})"
                )
    finally:
        perc.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
