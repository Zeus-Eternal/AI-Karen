# Kari API Usage

This document explains how to interact with Kari's FastAPI service. All endpoints run locally by default.

## Endpoints

| Method | Path | Description |
| ------ | ---- | ----------- |
| `GET`  | `/ping` | Simple liveness check. |
| `GET`  | `/health` | Returns plugin count and health info. |
| `GET`  | `/ready` | Readiness check for orchestration. |
| `POST` | `/chat` | Route text to the intent engine. `role` field controls RBAC. |
| `POST` | `/store` | Persist text in memory with optional TTL and tag. |
| `POST` | `/search` | Query memory store with optional metadata filter. |
| `GET`  | `/metrics` | Aggregate Prometheus metrics. |
| `GET`  | `/plugins` | List available plugin intents. |
| `POST` | `/plugins/reload` | Reload plugin manifests from disk. |
| `GET`  | `/plugins/{intent}` | Return the manifest for a single plugin. |
| `GET`  | `/self_refactor/logs` | Retrieve SelfRefactor logs. Use `?full=true` with `ADVANCED_MODE=true` for unsanitized output. |
| `GET`  | `/models` | List LLM backends. |
| `POST` | `/models/select` | Select the active LLM. |

## Basic Example

Start the API:

```bash
uvicorn main:app
```

Send a chat message:

```bash
curl -X POST -H "Content-Type: application/json" \
    -d '{"text": "hello"}' http://localhost:8000/chat
```

Reload plugins:

```bash
curl -X POST http://localhost:8000/plugins/reload
```

List available models and switch the active one:

```bash
curl http://localhost:8000/models
curl -X POST -H "Content-Type: application/json" \
    -d '{"model": "local"}' http://localhost:8000/models/select
```

## Advanced Mode

Set `ADVANCED_MODE=true` to enable full SelfRefactor logs and allow plugin UIs marked as untrusted. Example:

```bash
ADVANCED_MODE=true uvicorn main:app
curl http://localhost:8000/self_refactor/logs?full=true
```

Use this mode with caution as it exposes detailed patch data and renders untrusted plugin interfaces.
