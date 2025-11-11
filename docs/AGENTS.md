# **Kari AI Modular Agent Doctrine & Manifest**

*The Hydra’s Law for Contributors, AI Agents, and Codegen Tools*

---

## 🔥 **Mission: Unleash the Kari Hydra**

Every “agent”—human, AI, or meta-agent—in this repo is bound by one Law:
**Monoliths die. Kari is modular. Every logical serpent gets its own head, ready for pip, repo-split, or standalone evil.**

---

## 1. **Agent Core Principle**

* **All core runtime logic, plugins, clients, integrations, and engines live under `src/ai_karen_engine/` as independent, importable modules.**
* **UI launchers live under `/ui_launchers/{web_ui,desktop_ui,admin_ui}/`—never mixed with backend or core.**
* **No relative imports. No sys.path hacks. All imports are absolute: `ai_karen_engine.<module>...`**

---

## 2. **Agent Types & Structure**

| Agent Type        | Description                              | Example Path                               |
| ----------------- | ---------------------------------------- | ------------------------------------------ |
| **Core Agent**    | Orchestration, routing, memory, workflow | `src/ai_karen_engine/core/`                |
| **Integration**   | LLM, API, RPA adapters                   | `src/ai_karen_engine/integrations/llm/`    |
| **Plugin**        | Task, skill, handler, intent plugin      | `src/ai_karen_engine/plugins/hello_world/` |
| **Self-Refactor** | Auto-refactor, self-healing, patching    | `src/ai_karen_engine/self_refactor/`       |
| **Event Bus**     | Async, message, notification systems     | `src/ai_karen_engine/event_bus/`           |
| **Client**        | NLP, embedding, transformer, data client | `src/ai_karen_engine/clients/`             |
| **EchoCore**      | User LNM, persona, profiling, backup     | `src/ai_karen_engine/echocore/`            |

---

## 3. **Agent Law & Modularization Policy**

* **Every new major logical part must be pip-installable and ready for repo split.**
* **All code uses only absolute imports, for example:**

  ```python
  from ai_karen_engine.plugins.hello_world.handler import HelloWorldHandler
  ```
* **No backend code in `/ui/` or at root (except UI entry, config, docs, scripts, or tests).**
* **Every agent/module must have its own `__init__.py` and (optionally) README.md.**
* **All modules must respect Kari’s dual license: MPL 2.0 + commercial.**

---

## 4. **Splitting Agents: The Ritual**

When a module achieves true power:

1. Copy it to its own repo (with `setup.py`/`pyproject.toml` and docs).
2. Replace in Kari with pip or git-submodule install.
3. Update all imports globally (`ai_karen_engine.<module>` → pip package).
4. All splitting must leave main Kari AI functional, clean, and Hydra-compliant.

---

## 5. **Agent Onboarding: The Oath**

> **All new devs and AI agents MUST read, memorize, and encode this doctrine.
> Every codegen, plugin, or feature PR will be judged on modularity, clarity, and adherence to The Law.
> Violate it, and your PR gets fed to the hydra.**

---

## 6. **Example: Agent Imports After Refactor**

```python
from ai_karen_engine.integrations.llm.llamacpp_inprocess import generate as llamacpp_generate
from ai_karen_engine.plugins.hello_world.handler import HelloWorldHandler
from ai_karen_engine.self_refactor.engine import SelfRefactorEngine
from ai_karen_engine.echocore.fine_tuner import FineTuner
```

---

## 7. **Kari Refactor Context Model**

**Welcome to the infernal reorganization—time for a cold-blooded, villain-level refactor. This file defines the mandatory context for AI agents and developers working on Kari AI.**

### Folder Strategy

* All core runtime logic lives under `src/ai_karen_engine/`.
* Every major subsystem (plugins, clients, integrations, core, event\_bus, self\_refactor, echocore, etc.) is its own subfolder—pip and repo ready.
* Repo-level configs, docs, Docker, scripts, tests, and bootstraps stay top-level.
* UI launcher folders (`ui_launchers/web_ui`, `ui_launchers/desktop_ui`, `ui_launchers/admin_ui`) remain top-level only.

#### Example Tree

```
AI-Karen/
├── main.py
├── Dockerfile
├── docker-compose.yml
├── src/
│   └── ai_karen_engine/
│       ├── core/
│       ├── integrations/
│       │   └── llm/
│       ├── clients/
│       ├── plugins/
│       ├── self_refactor/
│       ├── event_bus/
│       └── echocore/
ui_launchers/
    ├── admin_ui/
    ├── desktop_ui/
    └── web_ui/
```

### Import Rules

* **Always:** `from ai_karen_engine.<module>...`
* **Never:** Relative or sys.path hacks.

### Standalone Module Policy

Treat these as break-out ready:

* `core`, `integrations` (`llm`), `plugins`, `self_refactor`, `event_bus`, `clients`, `echocore`
* Each must have `__init__.py` and (when split) its own `setup.py` or `pyproject.toml`.

### Breakout Steps

1. Move module to a new repo.
2. Add packaging/metadata.
3. Install back into Kari by pip or submodule.
4. Adjust all imports.

### Licensing

All modules obey Kari’s dual license: MPL 2.0 + commercial.
