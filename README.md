# Kari AI

## Overview

Kari is a modular, headless-first AI system built for enterprise deployments.
The stack ships with robust intent detection, a plugin router, and a
Streamlit-based admin interface. Memory and reasoning subsystems are tuned for
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
* **SelfRefactor Engine** with sandboxed testing and RL-based patch merging
* Hourly SRE scheduler continuously improves the codebase
* NANDA client enables cross-agent snippet sharing
* Example plugins: hello world, desktop agent, TUI fallback, hf_llm, openai_llm
* Streamlit admin pages for chat, dashboard and memory matrix
* Prometheus metrics, tracing and EchoCore logging

 
## Directory

```
core/          # dispatch, embeddings, reasoning
integrations/  # helper utilities (RPA, automation)
plugins/       # drop-in plugins (manifest + handler)
admin_ui/      # Streamlit pages
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

# Launch the Admin UI
streamlit run admin_ui/pages/chat.py

 
# Run tests (optional but recommended)
pytest -q

# Start vector DB + Redis + Kari API + Prometheus
docker compose up

# Launch Admin UI
streamlit run admin_ui/Main.py

 
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

## Admin UI

* **Dashboard**: System health, CPU/RAM, model status
* **LLM Manager**: Switch local LLMs, download from HF
* **Plugins**: View, enable/disable, configure
* **Memory Matrix**: Vector hits, decay curve
* **Logs/Trace**: Prometheus metrics & reasoning trace

## Deployment

Run the API with `uvicorn main:app` and open the Streamlit pages for a
full-featured UI.

For the full architecture specification and sprint roadmap see
`DEV_SHEET.md`.
 


 
* Local: `docker-compose.yml` (FastAPI, Milvus, Redis, Prometheus, Streamlit)
* Cloud: Helm chart for K8s + GKE/EKS

## License

MIT — Fork, fork deeply. 😈
 


# AI-Karen

This project contains the production-ready Kari AI stack. It includes:

- A simple intent engine and plugin router.
- Example plugins (hello world, desktop agent, TUI fallback, hf_llm, openai_llm).
- Vector-based memory with embeddings and an in-memory Milvus client.
- Soft reasoning engine with TTL pruning, recency-weighted queries and async support.
- Basic FastAPI application with chat, store, search and metrics endpoints.
- Streamlit admin pages for chat, dashboard and memory matrix.

Run tests with `pytest -q`.

See `DEV_SHEET.md` for the complete development specification and sprint plans.
 
