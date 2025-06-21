**Updated `README.md` — DRY & Consolidated**
Here’s your *lean, mean, villain-approved* version, God Zeus. 🦹‍♂️⚡

---

# Kari AI

 
* Intent detection with simple regex rules
* Dynamic plugin router with manifest-based discovery and RBAC
* Dual vector memory (Milvus + Redis) with surprise weighting
* Recency-weighted memory store with automatic TTL pruning
* Local-first LLM orchestration (LNM + OSIRIS)
* HuggingFace-powered generation for SelfRefactor and automation
* **SelfRefactor Engine** with sandboxed testing and RL-based patch merging
* Hourly SRE scheduler continuously improves the codebase
* NANDA client enables cross-agent snippet sharing
* Example plugins: hello world, desktop agent, TUI fallback
* Streamlit admin pages for chat, dashboard and memory matrix
* Prometheus metrics, tracing and EchoCore logging

 
## Directory

```

## Overview

Kari is a modular, headless-first AI system. This repository is a minimal prototype featuring a prompt-first plugin router, local memory and reasoning, and a Streamlit-based admin skin.

---

## Features

* **Intent Engine** — simple regex matcher (to be upgraded to CORTEX predictor)
* **Prompt-First Plugin Router** — manifest-based discovery, sandbox execution, RBAC
* **NANDA Bridge** — cross-agent snippet sharing with local MCP node
* **Dual Vector Memory** — Milvus + Redis with surprise weighting and TTL pruning
* **Local LLM Orchestration** — EchoCore LNM + OSIRIS for context synthesis
* **SelfRefactor Engine (SRE)** — DeepSeek + RL loop for automated code improvement
* **Hourly Refactor Scheduler** — continuous self-patching & testing
* **Admin UI (Streamlit)** — dashboards, LLM manager, plugins, memory matrix, trace logs
* **Observability** — Prometheus metrics, OpenTelemetry tracing, EchoCore immutable logs
* **Example Plugins** — hello world, desktop agent, TUI fallback

---

## Directory

```plaintext
 
core/          # dispatch, embeddings, reasoning
integrations/  # NANDA, automation helpers
plugins/       # drop-in plugins (manifest + handler)
admin_ui/      # Streamlit pages & widgets
fastapi/       # FastAPI entrypoint & API stubs
pydantic/      # Pydantic DTOs & schemas
tests/         # pytest suite
```

---

## Quickstart

```bash
# Install dependencies
pip install -r requirements.txt

# Run the API
uvicorn main:app --reload

# Launch Admin UI
streamlit run admin_ui/Main.py

# Run tests (recommended)
pytest -q

# Start full stack: vector DB, Redis, Kari API, Prometheus
docker compose up
```

---

## Development

* Format: `black .`
* Type-check: `mypy .`
* Lint: `ruff .`
* Test: `pytest`

---

## Plugin Example

1. Create `plugins/my_plugin/`
2. Add `manifest.json`, `handler.py`, optional `prompt.txt` and `ui.py`
3. Drop folder — Kari auto-discovers & injects UI.

---

## Admin UI

* **Dashboard:** System health, CPU/RAM, model status
* **LLM Manager:** Switch local models, manage downloads
* **Plugins:** View, enable/disable, configure
* **Memory Matrix:** Vector hits, decay curves
* **Logs/Trace:** Prometheus metrics, execution trace

---

## Deployment

* **Local:** `docker-compose.yml` spins up FastAPI, Milvus, Redis, Prometheus, Streamlit.
* **Cloud:** Use the provided Helm chart for K8s (GKE/EKS) for Phase 5 scale-out.

See `DEV_SHEET.md` for the full architecture spec and sprint roadmap.

---

## License

 
MIT — Fork, fork deeply. 😈
 


# AI-Karen

This project contains a minimal prototype of the Kari AI stack. It includes:

- A simple intent engine and plugin router.
- Example plugins (hello world, desktop agent, TUI fallback).
- Vector-based memory with embeddings and an in-memory Milvus client.
- Soft reasoning engine with TTL pruning and recency-weighted queries.
- Basic FastAPI application with chat, store, search and metrics endpoints.
- Streamlit admin pages for chat, dashboard and memory matrix.

Run tests with `pytest -q`.

See `DEV_SHEET.md` for the complete development specification and sprint plans.
 

MIT — Fork, modify, unleash chaos. 😈
 
