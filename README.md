# Kari AI

> **Local-first, plugin-driven, self-evolving.**
> Kari turns a single FastAPI service and a desktop Control Room into an autonomous “Ops Mesh” that can route intents, run domain capsules, and refactor its own code—without leaving your machine.

 
Kari is a modular, headless-first AI system built for enterprise deployments.
The stack ships with robust intent detection, a plugin router, and a
Tauri-based desktop control room. Memory and reasoning subsystems are tuned for
production workloads.

---
 

## 1 · Overview

 
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

Kari is a **modular, headless-first AI system** designed for on-prem or air-gapped environments.
The stack ships with:

* an intent engine and role-based plugin router
* a **SelfRefactor Engine** that patches its own code every hour
* dual-tier vector memory (Milvus + Redis) with surprise & recency weighting
* a **Tauri** desktop Control Room (React+Rust) for ops, metrics, and logs

Everything runs locally by default; cloud APIs are optional, opt-in plugins.

---

## 2 · Feature Highlights
 

| Category             | Highlights                                                                    |
| -------------------- | ----------------------------------------------------------------------------- |
| **Intent & Routing** | Regex intent matcher → Prompt-First Router → Capsule Planner                  |
| **Plugins**          | Drop a folder with `manifest.json` & `handler.py`; UI auto-appears            |
| **Memory**           | Milvus (dense vectors) + Redis (hot cache) + TTL pruning                      |
| **LLMs**             | Local LNM & OSIRIS models (ggml / llama.cpp); HF and OpenAI plugins optional  |
| **Self-Improvement** | DeepSeek-powered **SRE** runs in sandbox, merges patches after tests          |
| **Ops Mesh**         | *Hydra-Ops* capsules (DevOps, Finance, Growth, …) with guardrails & event bus |
| **Observability**    | Prometheus metrics, OpenTelemetry tracing, EchoCore immutable logs            |
| **UI**               | Tauri Control Room: dashboards, model manager, plugin config, memory matrix   |

Detailed usage instructions for each feature are in [docs/features_usage.md](docs/features_usage.md).

 
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

---

## 3 · Repository Layout

```text
core/          # dispatcher, embeddings, capsule planner
event_bus/     # Redis-Streams helpers
guardrails/    # YAML validators & rule engine
capsules/      # domain-specific agents (DevOps, Finance, …)
integrations/  # NANDA client, RPA helpers, external bridges
plugins/       # drop-in plugins (manifest + handler + ui)
desktop_ui/    # Tauri Control Room (Rust + React)
fastapi/       # API entrypoints, chat & metrics
pydantic/      # DTOs & schemas
tests/         # pytest suite
docs/          # architecture docs (mesh_arch.md, …)
```

---

## 4 · Quick-Start

```bash
# 1 · Install Python deps
pip install -r requirements.txt

# 2 · Launch backend API
uvicorn main:app --reload

# 3 · Run desktop Control Room (dev mode)
cd desktop_ui
npx tauri dev
 
```

**Full stack (API + Milvus + Redis + Prometheus):**

```bash
docker compose up
```

Build signed desktop binaries:

 
# Launch the Control Room
cd desktop_ui && npx tauri dev

# Launch the mobile web UI
streamlit run mobile_ui/app.py

```bash
cd desktop_ui
npx tauri build          # outputs .app / .exe / .AppImage
```

Run tests:
 

```bash
pytest -q
```

### API Usage

Kari's FastAPI backend exposes a small set of endpoints for headless deployments.
See [docs/api_usage.md](docs/api_usage.md) for the full list and example `curl`
commands.

---

## 5 · Development Cheatsheet

 
# Launch Control Room
cd desktop_ui && npx tauri build

| Task               | Command                                |
| ------------------ | -------------------------------------- |
| Format             | `black .`                              |
| Type-check         | `mypy .`                               |
| Lint               | `ruff .`                               |
| Tests              | `pytest`                               |
| Hot-reload plugins | just save the folder—Kari auto-detects |
### Advanced / Unrestricted Mode

Set `ADVANCED_MODE=true` to enable full SelfRefactor logs and allow plugin UIs marked as untrusted. Use with caution.

 

---

## 6 · Writing a Plugin

1. `mkdir plugins/my_plugin`
2. Add **manifest.json**

```json
{
  "name": "my_plugin",
  "description": "Says hello",
  "plugin_api_version": "0.1.0",
  "required_roles": ["user"]
}
```

3. Add **handler.py**

```python
def run(message, context):
    return "Hello from my_plugin!"
```

4. (Optional) **prompt.txt** for extra context or **ui.py** to extend the Control Room.

Drop the folder—Kari discovers it, registers routes, and injects UI automatically.

---

 
## Control Room

## 7 · Control Room
 

* **Dashboard** – CPU/RAM, capsule health, error feed
* **LLM Manager** – download / switch local models
* **Plugins** – enable, disable, edit manifests live
* **Memory Matrix** – inspect vector hits & decay curves
* **Logs & Trace** – Prometheus charts, OT spans, SRE patch history

Runs as a native Tauri app; all traffic stays on `localhost`.

 
Run the API with `uvicorn main:app` and start the Tauri Control Room for a
full-featured desktop experience.

---
 

## 8 · Deployment Modes

| Mode             | Stack                                                        | Notes                         |
| ---------------- | ------------------------------------------------------------ | ----------------------------- |
| **Local**        | `docker-compose.yml` (FastAPI + Milvus + Redis + Prometheus) | single-host dev or small team |
| **Desktop-only** | Tauri binary spawns embedded FastAPI                         | offline / air-gapped          |
| **Kubernetes**   | Helm chart `charts/kari/`                                    | GKE, EKS, on-prem             |

 
 
* Local: `docker-compose.yml` (FastAPI, Milvus, Redis, Prometheus)
* Cloud: Helm chart for K8s + GKE/EKS

---
 

## 9 · Roadmap & Docs

Detailed architecture diagrams, sprint plans, and Hydra-Ops capsule spec are in **`DEV_SHEET.md`** and **`docs/mesh_arch.md`**.

---

## 10 · License

 
This project contains the production-ready Kari AI stack. It includes:

- A simple intent engine and plugin router.
- Example plugins (hello world, desktop agent, TUI fallback, hf_llm, openai_llm).
- Vector-based memory with embeddings and an in-memory Milvus client.
- Soft reasoning engine with TTL pruning, recency-weighted queries and async support.
- FastAPI service exposing chat, memory store, metadata-aware search, metrics,
  plugin management and health checks.
- Tauri Control Room for chat, dashboard and memory matrix.
- Streamlit mobile UI for API demo.

MIT — fork, modify, unleash chaos. 😈

---
 

### AI-Karen in One Glance

 
See `DEV_SHEET.md` for the complete development specification and sprint plans.
The Hydra-Ops capsule design is further detailed in `docs/mesh_arch.md`.
 

* Intent router, plugin ecosystem, self-patching SRE
* Vector memory with surprise & recency fusion
* FastAPI backend + Tauri Control Room
* Example plugins: hello-world, desktop agent, HF LLM, OpenAI LLM
* Tests: `pytest -q`
* More in `DEV_SHEET.md` — happy hacking!
 
