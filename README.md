# Kari AI

## Overview

Kari is a modular, headless-first AI system combining custom memory layers (Milvus, Redis, EchoVault), advanced self-reasoning (OSIRIS, KRONOS), a dynamic plugin ecosystem, and a Streamlit Admin skin.

## Features

* Intent detection & dispatch
* Dual vector memory with surprise weighting
* Local-first LLM orchestration (LNM + OSIRIS)
* Dynamic plugin system (manifest + auto UI injection)
* EchoCore for immutable truths and dark profiling
* Prometheus observability + live tracing
* Admin UI with drag-drop plugins, model manager, and logs
* ICE wrapper for deep reasoning and memory recall

## Directory

```
core/           # Cortex, dispatch, embeddings, EchoCore
memory/         # MilvusClient, EchoVault, DarkTracker
plugins/        # Drop-in plugins (manifest, handler, ui)
admin_ui/       # Streamlit skin + panels
config/         # YAML settings
models/         # Local LLMs
```

## Quickstart

```bash
# Install dependencies
pip install -r requirements.txt

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

* Local: `docker-compose.yml` (FastAPI, Milvus, Redis, Prometheus, Streamlit)
* Cloud: Helm chart for K8s + GKE/EKS

## License

MIT — Fork, fork deeply. 😈

# AI-Karen

This project contains a minimal prototype of the Kari AI stack. It includes:

- A simple intent engine and plugin router.
- Example plugins (hello world, desktop agent, TUI fallback).
- Vector-based memory with embeddings and an in-memory Milvus client.
- Soft reasoning engine storing and querying memories.
- Basic FastAPI application with chat, store, search and metrics endpoints.
- Streamlit admin pages for chat, dashboard and memory matrix.

Run tests with `pytest -q`.

See `DEV_SHEET.md` for the complete development specification and sprint plans.