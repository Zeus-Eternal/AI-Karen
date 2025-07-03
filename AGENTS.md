# Kari Refactor Context Model

**Welcome to the infernal reorganization—time for a cold-blooded, villain-level refactor.**
This file defines the mandatory context for AI agents and developers working on Kari AI.

## Folder Strategy

- Everything core to running Kari AI goes under `src/`.
- Standalone modules (plugins, clients, integrations, core, event bus, self refactor, etc.) live in `src/ai_karen_engine/`.
- Repository-level configs, docs, Docker files, scripts, tests, and bootstraps stay in the repo root.
- UI folders (`ui/mobile_ui`, `ui/desktop_ui`, `ui/admin_ui`) remain top-level for now.

## Final Tree Highlights

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
│       ├── echocore/
│       └── ui/
└── ui/
    ├── admin_ui/
    ├── desktop_ui/
    └── mobile_ui/
```

## Import Rules

- Always import using the `ai_karen_engine` package path.
- Example:

```python
from ai_karen_engine.integrations.llm.ollama_inprocess import OllamaRunner
```

- Eliminate `sys.path` hacks or relative paths outside of `src`.

## Standalone Module Policy

Treat these folders as ready candidates for their own packages or repositories:

- `core`
- `integrations` (`integrations/llm` in particular)
- `plugins`
- `self_refactor`
- `event_bus`
- `clients`
- `echocore`

Each must contain `__init__.py` and can include packaging files when split out.

## Breakout Steps

1. Move the module to its own repository.
2. Add `setup.py` or `pyproject.toml` with versioning.
3. Install back into Kari via pip or as a submodule.
4. Adjust imports accordingly.

## Licensing

All modules obey Kari’s dual license: MPL 2.0 plus the commercial license.

---

**“The Monolith Must Die, and Modular Serpents Shall Rise!”**
Use this document as the guiding context for development, code generation, and future refactors.
