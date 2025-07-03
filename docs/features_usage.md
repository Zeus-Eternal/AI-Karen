# ⚙️ Kari Feature Guide

This document explains how to use Kari's core features. It is written for both non-technical users and developers deploying the system in headless environments.

---

## 🧠 1. Chat Hub & Capsule Planner

Kari exposes a `/chat` endpoint managed by the **ChatHub**, which routes messages to the appropriate **capsule** (micro-agent) based on intent detection.

### Key Features:

* **Slash commands**:

  * `/help` — list available commands
  * `/memory` — view recent context snippets
  * `/purge` — clear NeuroVault memory
* **Short-term memory**: via NeuroVault, per session.
* **Role-based access**: Use the `role` field (`user`, `dev`, `admin`) to invoke privileged plugins.

### Example:

```bash
curl -X POST -H "Content-Type: application/json" \
    -d '{"text": "help me deploy"}' http://localhost:8000/chat
```

---

## 🧠 2. Memory Matrix

All interactions can be stored and retrieved using the memory API.

### Endpoints:

* `POST /store` — Add to memory (optional `ttl` in seconds).
* `POST /search` — Search based on semantic embedding.
* **Decay awareness**: Older memories fade unless refreshed.

### Example:

```bash
curl -X POST -H "Content-Type: application/json" \
    -d '{"text": "remember this", "ttl": 3600}' http://localhost:8000/store
```

The **Control Room UI** shows memory records, sorted and filterable by relevance, date, or tag.

---

## 🧩 3. Plugin Manager

Plugins extend Kari with new intents, memory hooks, and optional UI.

### How to use:

1. Drop your plugin in `plugins/<name>/` with `plugin_manifest.json` + `handler.py`.
2. Reload all plugins:

```bash
curl -X POST http://localhost:8000/plugins/reload
```

> 🔐 Note: Plugins with UI components only render if `ADVANCED_MODE=true`.

---

## 🧠 4. LLM Manager

Switch and manage LLM models from the Control Room or API.

### Behind the scenes:

* Fetches from `/models` (powered by `llm_manager` plugin).
* Supports both local and remote engines (if configured).
* Useful for tasks like SelfRefactor or switching to lightweight chat modes.

---

## 🔁 5. SelfRefactor Logs

Kari evolves using a SelfRefactor engine. It evaluates plugin performance, rewrites prompt logic, and tests new routes in a sandbox.

### Logs:

* Available at `/self_refactor/logs`
* With `ADVANCED_MODE=true`, enables full stdout/stderr logs.

```bash
ADVANCED_MODE=true uvicorn main:app
curl http://localhost:8000/self_refactor/logs?full=true
```

---

## 🔒 6. Guardrails & Hydra‑Ops

Guardrails validate plugin inputs using YAML-based schemas.

* Defined in `guardrails/*.yml`
* Enforced before any `Hydra-Ops` event dispatch
* Test/edit via Control Room's **Guardrail Editor**

Protects against malformed input, bad state transitions, or unsafe LLM outputs.

---

## 📊 7. Dashboard & Metrics

Kari ships with native **Prometheus metrics** exposed at `/metrics`.

### Includes:

* CPU & RAM usage
* Capsule execution time
* Plugin failure rates
* Memory hit/miss ratios

Visualized in the Control Room with real-time graphs.

---

## 🧊 8. ICE Wrapper

The **ICE wrapper** provides advanced reasoning capabilities:

* Invoked via `ice.process(text)` or `await ice.aprocess(text)`
* Returns:

  * **Entropy score**
  * **Related memory snippets**
  * **LLM-generated insight block**

Perfect for speculative reasoning, decision analysis, or long-horizon inference.

---

## 🧍‍♂️ 9. Roles & Access Levels

Each API call can optionally include a `role` field. UI panels and plugin access are permission-gated.

| Role    | Permissions                                  |
| ------- | -------------------------------------------- |
| `user`  | Basic chat + memory                          |
| `dev`   | Plugin tools, logs, LLM manager              |
| `admin` | Guardrails, capsule editing, plugin hot-swap |

> 🛡️ Admin roles can also edit memory, override decay policies, and toggle background services.

---

## ⚠️ 10. Advanced Mode

Setting `ADVANCED_MODE=true` unlocks unrestricted behavior:

* Shows all plugin UIs
* Enables full SelfRefactor logs
* Allows plugin test execution
* May expose low-level LLM calls and source code paths

> 🔒 Use only in dev environments or trusted operator sessions.

## 🦾 11. Autonomous Agents

Kari includes a lightweight autonomous agent that decomposes a goal into
subtasks and executes them via the `autonomous_task_handler` plugin. Results may
trigger external workflows when permitted by the plugin manifest.

---

## 📚 Additional Docs

* [api\_usage.md](api_usage.md) – REST endpoints
* [mesh\_arch.md](mesh_arch.md) – Capsule orchestration architecture
* [DEV\_SHEET.md](../DEV_SHEET.md) – Active sprint plans
* [plugin\_spec.md](plugin_spec.md) – How to write plugins
* [memory\_arch.md](memory_arch.md) – NeuroVault & Milvus memory architecture

---
