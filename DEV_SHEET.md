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

## Delivery Phases

| Phase | Sprint Goal               | Key PR Gates                      |
| ----- | ------------------------- | --------------------------------- |
| 0     | Skeleton echo             | FastAPI up, /ping returns 200     |
| 1     | Intent + Plugin router    | Drop test plugin; chat works      |
| 2     | Vector memory             | semantic recall e2e; Prom metrics |
| 3     | EchoCore + Self-Reason    | LNM train script; critique loop   |
| 4     | Admin skin + UI injection | Enable/disable plugin UI live     |
| 5     | Enterprise hardening      | Docker-Compose passes load test   |

## Phase 2 – Core Sprint Plan

**Sprint Length:** 2 weeks
**Goal:** deliver complete core memory and embedding layer with live vector recall.

| Day | Milestone |
| --- | --------- |
| 1   | Scaffold core files (`embedding_manager.py`, `milvus_client.py`, `soft_reasoning_engine.py`) |
| 2   | Implement embedding manager with dual embedding methods (MiniLM + BGE) |
| 3   | Write Milvus client: connect, create collection, upsert |
| 4   | Implement similarity search with metadata filters |
| 5   | Write surprise score function and integrate into SoftReasoningEngine |
| 6   | Build `/store` and `/search` API endpoints |
| 7   | Mid-sprint demo: test storing and searching chunks |
| 8   | Hook Prometheus metrics for embedding time, search latency |
| 9   | Build Memory Matrix UI page (basic version) |
| 10  | QA writes tests for embedding and Milvus client |
| 11  | Load test Milvus, adjust index config |
| 12  | Polish SoftReasoningEngine integration |
| 13  | Final tests, code freeze |
| 14  | Demo Day, merge & tag `v0.2.0` |

### Deliverables

- Fully working vector memory
- API tested & metrics exposed
- Memory Matrix visible in Admin UI
- Coverage ≥ 85% on core files

Maintain this cheat-sheet. Any future architectural change must update this file alongside the specification.
