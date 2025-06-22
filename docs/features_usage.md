# Kari Feature Guide

This document explains how to use Kari's core features. It is written for both non-technical users and developers deploying the system in headless environments.

## 1. Chat & Capsule Planner

Kari exposes a `/chat` endpoint that routes messages to the appropriate capsule (micro‑agent) based on intent detection. Users simply send plain text; Kari returns structured responses. Developers can supply a `role` field in the request to trigger privileged plugins when authorized.

Example request:

```bash
curl -X POST -H "Content-Type: application/json" \
    -d '{"text": "help me deploy"}' http://localhost:8000/chat
```

## 2. Memory Matrix

All interactions can be stored and searched through the memory API (`/store` and `/search`). The desktop Control Room presents these records in a sortable table so you can review past exchanges and see how recall decay works over time. For headless use, POST to `/store` with `text` and optional `ttl` seconds.

```bash
curl -X POST -H "Content-Type: application/json" \
    -d '{"text": "remember this", "ttl": 3600}' http://localhost:8000/store
```

## 3. Plugin Manager

Plugins extend Kari with new intents and optional UI panels. Drop a folder with `plugin_manifest.json` and a `handler.py` file under `plugins/`. Reload via:

```bash
curl -X POST http://localhost:8000/plugins/reload
```

In the Control Room, admins and developers can enable or disable plugins and view any UI components they expose. Untrusted UIs only render when `ADVANCED_MODE=true`.

## 4. LLM Manager

The LLM Manager page allows you to download or switch local models. Behind the scenes this calls `/models` endpoints to fetch available engines and select one as active. Use it when you need different model sizes for SelfRefactor or chat.

## 5. SelfRefactor Logs

Kari continuously improves itself using the SelfRefactor engine. Sanitized patch logs are available from `/self_refactor/logs`. Set `ADVANCED_MODE=true` for full details including stdout/stderr from the test sandbox. Use with care as this may reveal sensitive code.

```bash
ADVANCED_MODE=true uvicorn main:app
curl http://localhost:8000/self_refactor/logs?full=true
```

## 6. Guardrails & Hydra‑Ops

Guardrails are YAML rules that validate plugin input parameters. When a capsule publishes an event to the Hydra‑Ops bus, guardrails ensure it conforms to policy before tasks execute. Admins can edit these rules in the Guardrail Editor (or via `guardrails/*.yml` files) and test them against sample payloads.

## 7. Dashboard & Metrics

Prometheus metrics are available from `/metrics` and visualized in the Control Room dashboard. CPU/RAM usage, capsule health and error rates update in real time. Point your Prometheus server at `/metrics` or run the Control Room to view graphs locally.

## 8. Roles & Access

- **User** – basic chat and memory search.
- **Dev** – plugin manager, log viewer, LLM manager, capsule preview.
- **Admin** – full system dashboard, guardrail editor, hot-swap capsules.

Endpoints enforce role checks based on the `role` value passed to `/chat` or the API key used. UIs will hide panels if your role lacks access.

## 9. Advanced Mode

Setting `ADVANCED_MODE=true` enables unrestricted plugin UIs and full SelfRefactor log output. Only enable this for trusted operators, as plugins may execute unreviewed code and log entries may expose repository details.

---

 
For a list of raw REST endpoints see [api_usage.md](api_usage.md). Architectural notes live in [mesh_arch.md](mesh_arch.md) and the sprint plans in [DEV_SHEET.md](../DEV_SHEET.md). See [plugin_spec.md](plugin_spec.md) for writing new plugins and [memory_arch.md](memory_arch.md) for details on the vector store.

For a list of raw REST endpoints see [api_usage.md](api_usage.md). For architectural details check [mesh_arch.md](mesh_arch.md) and the sprint plans in [DEV_SHEET.md](DEV_SHEET.md).
 
