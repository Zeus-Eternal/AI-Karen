# Kari AI

> **Local-first, plugin-driven, self-evolving.**
> Kari turns a single FastAPI service and a desktop Control Room into an autonomous “Ops Mesh” that can route intents, run domain capsules, and refactor its own code—without leaving your machine.

---

## 1 · Overview

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

```bash
cd desktop_ui
npx tauri build          # outputs .app / .exe / .AppImage
```

Run tests:

```bash
pytest -q
```

---

## 5 · Development Cheatsheet

| Task               | Command                                |
| ------------------ | -------------------------------------- |
| Format             | `black .`                              |
| Type-check         | `mypy .`                               |
| Lint               | `ruff .`                               |
| Tests              | `pytest`                               |
| Hot-reload plugins | just save the folder—Kari auto-detects |

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

## 7 · Control Room

* **Dashboard** – CPU/RAM, capsule health, error feed
* **LLM Manager** – download / switch local models
* **Plugins** – enable, disable, edit manifests live
* **Memory Matrix** – inspect vector hits & decay curves
* **Logs & Trace** – Prometheus charts, OT spans, SRE patch history

Runs as a native Tauri app; all traffic stays on `localhost`.

---

## 8 · Deployment Modes

| Mode             | Stack                                                        | Notes                         |
| ---------------- | ------------------------------------------------------------ | ----------------------------- |
| **Local**        | `docker-compose.yml` (FastAPI + Milvus + Redis + Prometheus) | single-host dev or small team |
| **Desktop-only** | Tauri binary spawns embedded FastAPI                         | offline / air-gapped          |
| **Kubernetes**   | Helm chart `charts/kari/`                                    | GKE, EKS, on-prem             |

---

## 9 · Roadmap & Docs

Detailed architecture diagrams, sprint plans, and Hydra-Ops capsule spec are in **`DEV_SHEET.md`** and **`docs/mesh_arch.md`**.

---

## 10 · License

MIT — fork, modify, unleash chaos. 😈

---

### AI-Karen in One Glance

* Intent router, plugin ecosystem, self-patching SRE
* Vector memory with surprise & recency fusion
* FastAPI backend + Tauri Control Room
* Example plugins: hello-world, desktop agent, HF LLM, OpenAI LLM
* Tests: `pytest -q`
* More in `DEV_SHEET.md` — happy hacking!
