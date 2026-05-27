# Trained AI — RL, PINNs, Agentic

## Quick start

```bash
pip install -r requirements-physical-ai.txt
python scripts/train_all.py          # trains PINN + RL, exports ONNX
python scripts/verify_models.py
python run.py "Pick the red bottle"
```

## Reinforcement learning (PPO)

| File | Purpose |
|------|---------|
| `brain_ai/reinforcement_learning/env.py` | Grasp sim env (Gymnasium) |
| `brain_ai/reinforcement_learning/train.py` | PPO training |
| `models/rl/grasp_policy.pt` | PyTorch checkpoint |
| `models/rl/grasp_policy.onnx` | Jetson inference |

**Isaac Lab:** Replace `GraspSimEnv` with Isaac Lab xArm6 task; keep same export path.

```bash
export PHYSICAL_AI_RL_TIMESTEPS=200000
python scripts/train_all.py
```

## PINNs

| File | Purpose |
|------|---------|
| `brain_ai/pinns/network.py` | Physics-informed MLP |
| `brain_ai/pinns/train.py` | Synthetic physics + residual training |
| `models/pinn/physics_validator.pt` | Deployed validator |

Pipeline uses **Trained PINN** when checkpoint exists; else rule-based fallback.

## Agentic AI (LangGraph)

| File | Purpose |
|------|---------|
| `brain_ai/agentic_ai/graph.py` | Planner → Vision → Safety → Motion |
| `brain_ai/agentic_ai/llm.py` | Phi-4 / Azure / Ollama / mock |

### LLM providers

```bash
# Mock (no API key) — structured rule plan + LangGraph flow
export PHYSICAL_AI_LLM_PROVIDER=mock

# Ollama + Phi / Llama
export PHYSICAL_AI_LLM_PROVIDER=ollama
export PHYSICAL_AI_LLM_MODEL=phi4
export PHYSICAL_AI_LLM_BASE_URL=http://localhost:11434/v1

# Azure OpenAI (Phi-4)
export PHYSICAL_AI_LLM_PROVIDER=azure
export AZURE_OPENAI_ENDPOINT=https://YOUR.openai.azure.com/
export AZURE_OPENAI_DEPLOYMENT=phi-4
export AZURE_OPENAI_API_KEY=...
```

```bash
export PHYSICAL_AI_USE_LANGGRAPH=1
python run.py "Clean the table and pick the red bottle"
```

Trace shows `agentic_planning` engine: `LangGraphExecutive`.
