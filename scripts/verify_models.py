#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config.ai_models import ModelPaths, get_llm_settings


def main() -> int:
    paths = ModelPaths()
    llm = get_llm_settings()
    print("Model status:")
    print(f"  RL torch:  {paths.rl_torch}  ({'OK' if paths.rl_torch.exists() else 'MISSING'})")
    print(f"  RL onnx:   {paths.rl_onnx}   ({'OK' if paths.rl_onnx.exists() else 'MISSING'})")
    print(f"  PINN:      {paths.pinn_torch} ({'OK' if paths.pinn_available() else 'MISSING'})")
    print(f"  LLM:       provider={llm.provider} model={llm.model} langgraph={llm.use_langgraph}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
