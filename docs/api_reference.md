# API Reference

This reference lists all FastAPI routes defined in `main.py`.

| Method | Path | Parameters | Description |
| ------ | ---- | ---------- | ----------- |
| GET | `/ping` | – | Liveness check |
| GET | `/health` | – | Return plugin count |
| GET | `/ready` | – | Readiness probe |
| POST | `/chat` | `text`, `role` | Route text to intent engine |
| POST | `/store` | `text`, `ttl_seconds`, `tag` | Persist memory |
| POST | `/search` | `text`, `top_k`, `metadata_filter` | Query memory store |
| GET | `/metrics` | – | Prometheus metrics |
| GET | `/plugins` | – | List available intents |
| POST | `/plugins/reload` | – | Reload plugin manifests |
| GET | `/plugins/{intent}` | – | Return one manifest |
| GET | `/self_refactor/logs` | `full` | Retrieve patch logs |
 
| GET | `/models` | – | List available LLM backends |
| POST | `/models/select` | `model` | Switch active LLM |


All responses are JSON. See [docs/api_usage.md](api_usage.md) for `curl` examples and [docs/security.md](security.md) for role enforcement.
