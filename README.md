# Kari AI

## Overview

Kari is a modular, headless-first AI system. The repository contains a minimal
prototype with intent detection, a plugin router and a Streamlit-based admin
skin. Memory and reasoning are simplified for local testing.

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

This repository is a minimal proof of concept. Run the API with
`uvicorn main:app`, and open the Streamlit pages for a lightweight UI.

For the full architecture specification and sprint roadmap see
`DEV_SHEET.md`.
* Local: `docker-compose.yml` (FastAPI, Milvus, Redis, Prometheus, Streamlit)
* Cloud: Helm chart for K8s + GKE/EKS

## License

MIT — Fork, fork deeply. 😈
