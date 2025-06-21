# Kari AI

## Overview

Kari is a modular, headless-first AI system built for enterprise deployments.
The stack ships with robust intent detection, a plugin router, and a
Tauri-based desktop control room. Memory and reasoning subsystems are tuned for
production workloads.

## Features

* Intent detection engine with runtime-configurable regex rules
* Robust plugin router with manifest validation and RBAC dispatch
* Dual vector memory (Milvus + Redis) with surprise weighting
* Thread-safe Milvus client supporting TTL and metadata filters
* Recency-weighted memory store with automatic TTL pruning and async queries
* Local-first LLM orchestration (LNM + OSIRIS)
* HuggingFace-powered generation for SelfRefactor and automation
* HuggingFace LLM plugin with auto-download helper
* Optional OpenAI plugin for hosted inference
* **SelfRefactor Engine** with sandboxed testing, RL-based patch merging, and
  dynamic LLM backend selection (HF, DeepSeek or OpenAI)
* Configurable SRE scheduler (default weekly) continuously improves the codebase
* NANDA client enables cross-agent snippet sharing
* **Hydra-Ops Mesh** with capsule planner, event bus and guardrails
* Example plugins: hello world, desktop agent, TUI fallback, hf_llm, openai_llm
* Tauri desktop Control Room for chat, dashboard and memory matrix
* Streamlit mobile UI for API demo
* Prometheus metrics, tracing and EchoCore logging

 
## Directory

```
core/          # dispatch, embeddings, reasoning
event_bus/     # in-memory event streams
guardrails/    # YAML validators
capsules/      # domain-specific micro agents
integrations/  # helper utilities (RPA, automation)
plugins/       # drop-in plugins (manifest + handler)
desktop_ui/    # Tauri Control Room
mobile_ui/     # Streamlit mobile interface
fastapi/       # lightweight stubs for tests
pydantic/      # lightweight stubs for tests
tests/         # pytest suite
```

## Quickstart

```bash
# Install dependencies
pip install -r requirements.txt

# Run the API
uvicorn main:app --reload

# Launch the Control Room
cd desktop_ui && npx tauri dev

# Launch the mobile web UI
streamlit run mobile_ui/app.py

 
# Run tests (optional but recommended)
pytest -q

# Start vector DB + Redis + Kari API + Prometheus
docker compose up

# Launch Control Room
cd desktop_ui && npx tauri build

 
```

## Development

* Format: `black .`
* Type-check: `mypy .`
* Lint: `ruff .`
* Test: `pytest`

## Plugin Example

1. Create `plugins/my_plugin/`
2. Add `manifest.json`, `handler.py`, `prompt.txt` (optional)
3. Optionally add `ui.py` with `render()`
4. Drop folder — Kari auto-discovers & injects UI.

## Control Room

* **Dashboard**: System health, CPU/RAM, model status
* **LLM Manager**: Switch local LLMs, download from HF
* **Plugins**: View, enable/disable, configure
* **Memory Matrix**: Vector hits, decay curve
* **Logs/Trace**: Prometheus metrics & reasoning trace

## Deployment

Run the API with `uvicorn main:app` and start the Tauri Control Room for a
full-featured desktop experience.

For the full architecture specification and sprint roadmap see
`DEV_SHEET.md`.
 


 
* Local: `docker-compose.yml` (FastAPI, Milvus, Redis, Prometheus)
* Cloud: Helm chart for K8s + GKE/EKS

## License

MIT — Fork, fork deeply. 😈
 


# AI-Karen

This project contains the production-ready Kari AI stack. It includes:

- A simple intent engine and plugin router.
- Example plugins (hello world, desktop agent, TUI fallback, hf_llm, openai_llm).
- Vector-based memory with embeddings and an in-memory Milvus client.
- Soft reasoning engine with TTL pruning, recency-weighted queries and async support.
- FastAPI service exposing chat, memory store, metadata-aware search, metrics,
  plugin management and health checks.
- Tauri Control Room for chat, dashboard and memory matrix.
- Streamlit mobile UI for API demo.

Run tests with `pytest -q`.

See `DEV_SHEET.md` for the complete development specification and sprint plans.
The Hydra-Ops capsule design is further detailed in `docs/mesh_arch.md`.
 
