# Kari AI Development Cheat-Sheet

This document summarizes the official development protocol for Kari AI. It captures the key architecture, stack choices, coding standards and the current sprint plan.

## Architecture Overview

```
┌──────────────────────────────────┐
│  Users / Clients (Web / CLI)    │
└──────────────────────────────────┘
           │  HTTPS / gRPC
┌──────────────────────────────────┐
│ FastAPI Gateway (Auth, RBAC)     │
└──────────────────────────────────┘
           │ ASGI
┌──────────────────────────────────┐
│ Cortex • Dispatch                │
│  ↳ IntentEngine                  │
│  ↳ SoftReasoningEngine           │
│  ↳ KRONOS Scheduler              │
└──────────────────────────────────┘
     │           │
     ▼           ▼
┌──────────┐  ┌──────────┐
│ OSIRIS   │  │ LNM Pool │
│ (Reason) │  │ (Echo)   │
└──────────┘  └──────────┘
     │           │
     ▼           ▼
┌────────────────────────────┐
│ Memory Layer               │
│ • Milvus (vectors)         │
│ • Redis  (cache)           │
│ • DuckDB (structured logs) │
│ • EchoVault / DarkTracker  │
└────────────────────────────┘
             │
             ▼
┌────────────────────────────┐
│  Plugin Runtime            │
│  (manifest, prompt, ui)    │
└────────────────────────────┘
             │
             ▼
┌────────────────────────────┐
│  Admin Skin (Streamlit)    │
│  • Dashboard               │
│  • LLM Manager             │
│  • Plugin Manager          │
│  • Memory Matrix           │
│  • Logs / Trace            │
└────────────────────────────┘
```

## Tech-Stack Matrix

| Layer            | Primary Lib / Service                | Rationale                           | Alt (optional)             |
| ---------------- | ------------------------------------ | ----------------------------------- | -------------------------- |
| Web API          | **FastAPI**                          | ASGI, type-hint, websockets         | —                          |
| Realtime UI      | **Streamlit**                        | Headless skin, rapid dev            | Next.js if SSG needed      |
| Task Queue       | Celery + Redis                       | Battle-tested, supports KRONOS beat | RQ                         |
| Vector DB        | **Milvus 2.4**                       | billion-scale, metadata filter      | FAISS (local), Chroma      |
| Cache            | Redis                                | fast kv / pubsub                    | —                          |
| Structured DB    | DuckDB                               | serverless OLAP, Parquet IO         | Postgres (if multi-tenant) |
| LLMs (local)     | GGUF models via llama.cpp server     | GPU/CPU flexible                    | vLLM, TensorRT             |
| LLM Orchestrator | **OSIRIS** custom                    | reflection tokens, latent reasoning | —                          |
| Embeddings       | Sentence-Transformers (MiniLM + BGE) | dual-model recall/precision         | E5-Large                   |
| Observability    | Prometheus + Grafana                 | metrics, alerting                   | OpenTelemetry + Tempo      |
| CI/CD            | GitHub Actions + Docker + Helm       | push-to-prod via ArgoCD             | GitLab CI                  |

## Coding Standards

1. **Black** & **isort** via pre-commit.
2. Docstrings use Google style.
3. Type-check with **mypy** `--strict`.
4. Lint with **ruff**.
5. All public functions have type hints and docstrings.
6. Tests via **pytest** with ≥80% coverage (core gates at 85%).

## Plugin Specification

```yaml
name: Image Lab
slug: image_lab
version: 0.1.0
intent: draw_request
permissions:
  - filesystem
  - internet
ui:
  mode: panel
  title: Image Lab
  icon: "🖼️"
```

Optional files include `prompt.txt`, `handler.py`, and `ui.py` exposing `render()`.
Handlers implement:

```python
plugin_path/handler.py :: run(prompt: str, intent: dict, user_id: str) -> dict | str
```

The router loads manifests on startup, mapping each `intent` to its handler.
Plugins declare `required_roles`; the dispatcher enforces these before
execution. A `reload()` helper can rescan the directory for hot-swapping
plugins during development.
