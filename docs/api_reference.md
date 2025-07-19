Hail God Zeus—here’s your **merged, production-grade Kari AI API Reference & Usage Guide**, streamlined for onboarding, devs, and LLMs. Place this in `/docs/api_usage.md` or share with your evil minions. Includes endpoint list, basic/advanced usage, RBAC, and reference to further docs.

---

# 🦹‍♂️ KARI AI — API REFERENCE & USAGE GUIDE (2025 EVIL TWIN RELEASE)

---

**Kari’s FastAPI service exposes a clean, local-first API for intent routing, memory, plugins, self-refactor, LLM switching, and metrics. All endpoints return JSON.**

---

## **Endpoints Summary**

| Method | Path                  | Parameters                         | Description                                                                  |
| ------ | --------------------- | ---------------------------------- | ---------------------------------------------------------------------------- |
| GET    | `/`                   | –                                  | List available routes (root)                                                 |
| GET    | `/ping`               | –                                  | Liveness check                                                               |
| GET    | `/health`             | –                                  | Returns plugin count & health                                                |
| GET    | `/ready`              | –                                  | Readiness probe for orchestrators                                            |
| POST   | `/chat`               | `text`, `role`                     | Route text to intent engine, RBAC via `role`                                 |
| POST   | `/store`              | `text`, `ttl_seconds`, `tag`       | Persist memory with optional TTL/tag                                         |
| POST   | `/search`             | `text`, `top_k`, `metadata_filter` | Query memory vector store                                                    |
| GET    | `/metrics`            | –                                  | Prometheus metrics                                                           |
| GET    | `/plugins`            | –                                  | List available plugin intents                                                |
| POST   | `/plugins/reload`     | –                                  | Reload plugin manifests from disk                                            |
| GET    | `/plugins/{intent}`   | –                                  | Get manifest for a single plugin                                             |
| GET    | `/self_refactor/logs` | `full`                             | Retrieve SelfRefactor patch logs (`?full=true` for raw, ADVANCED\_MODE only) |
| POST   | `/self_refactor/approve` | `review_id`                        | Apply a queued patch set (admin only) |
| GET    | `/models`             | –                                  | List available LLM backends                                                  |
| POST   | `/models/select`      | `model`                            | Switch active LLM                                                            |

**All endpoints run locally (`localhost:8000`) by default. See [docs/api\_usage.md](api_usage.md) for curl examples.**

---

## **Basic Usage Examples**

### 1. Start API

```bash
uvicorn main:app --reload
```

### 2. Send a Chat Message

```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"text": "hello"}' http://localhost:8000/chat
```

### 3. Store a Memory

```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"text": "remember me", "ttl_seconds": 3600, "tag": "test"}' \
  http://localhost:8000/store
```

### 4. Search Memory

```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"text": "retrieve", "top_k": 3}' \
  http://localhost:8000/search
```

### 5. List and Reload Plugins

```bash
curl http://localhost:8000/plugins
curl -X POST http://localhost:8000/plugins/reload
```

### 6. List and Switch LLMs

```bash
curl http://localhost:8000/models
curl -X POST -H "Content-Type: application/json" \
  -d '{"model": "local"}' http://localhost:8000/models/select
```

---

## **Advanced/Unrestricted Mode**

Set `ADVANCED_MODE=true` for extra power:

* Unsanitized SelfRefactor logs
* Untrusted plugin UIs enabled

```bash
ADVANCED_MODE=true uvicorn main:app
curl http://localhost:8000/self_refactor/logs?full=true
```

**Use with caution.**

---

## **Role Enforcement (RBAC)**

* All sensitive/advanced endpoints require `role` input (e.g., `"admin"`, `"user"`, `"evil"`).
* Plugin and model actions are checked against roles defined in their manifests.
* See [docs/security.md](security.md) for RBAC enforcement details.

---

## **More Docs**

* [Features](features_usage.md)
* [Plugin API](plugin_spec.md)
* [Security](security.md)
* [SelfRefactor](self_refactor.md)
* [UI Blueprint](ui_blueprint.md)
* [Mesh & Ops](mesh_arch.md)

---

**Twin out—lightning API domination at your fingertips. 😈⚡**
