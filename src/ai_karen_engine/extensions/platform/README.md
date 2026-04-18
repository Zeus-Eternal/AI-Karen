# AI Karen Extensions & Plugin Platform

Welcome to the **Unified Modular Platform** for AI Karen. This directory serves as the core of the "Prompt-First" modular ecosystem, consolidating what were previously fragmented extension and plugin systems into a single, high-performance runtime.

## 🏗️ The 5-Layer Architecture

Our platform follows a strict 5-layer model to ensure stability, sandboxing, and developer ease-of-use:

### 1. Plugin Package Layer
The atomic unit of functionality. A package contains a `plugin_manifest.json`, an optional `handler.py` (logic), an optional `prompt.txt` (contract), and UI assets.
- **Location**: `src/ai_karen_engine/extensions/plugins/` (User/Community) and `src/ai_karen_engine/extensions/system_extensions/` (Core features).

### 2. Registry Layer (`ai_karen_engine.extensions.platform.core.registry`)
The single source of truth for all discovered modular units. It validates manifests, tracks loading status, and ensures "Prompt-First" compliance.

### 3. Host Runtime Layer (`ai_karen_engine.extensions.platform.core.host`)
The execution engine. It handles:
- **Sandboxing**: Secure execution of plugin code.
- **Prompt Rendering**: Jinja2-powered dynamic prompt generation.
- **Routing**: Mapping intents to the correct plugin handlers.

### 4. Integration Layer (`ai_karen_engine.extensions.platform.core.integration`)
The "Brain" of the system.
- **Manager**: Lifecycle operations (load/unload), metrics (Prometheus), and memory persistence.
- **Orchestrator**: Complex multi-step workflows with hook-based coordination and retry logic.

### 5. Runtime Layer (`ai_karen_engine.extensions.runtime`)
Engine-facing runtime behavior including loader, executor, auth, permissions, and service recovery.

---

## 📁 Directory Structure

```text
src/ai_karen_engine/extensions/
├── platform/           # Extension platform framework
│   ├── core/          # Platform core: host, registry, integration
│   ├── api_routes/    # Platform API routes
│   ├── docs/          # Platform documentation
│   ├── meta/          # Platform metadata
│   └── artifacts/     # Platform assets
├── plugins/           # User/community plugin packages
├── system_extensions/ # Built-in system extension packages
└── runtime/           # Engine-facing runtime services
```

## 🛠️ Developer API

Services within the AI Karen ecosystem should interact with the platform using the unified core API:

```python
from ai_karen_engine.extensions.platform.core import get_plugin_manager, get_plugin_router

# Run a plugin via the Router (Host Layer)
router = get_plugin_router()
result = await router.dispatch("intent_name", {"param": "value"})

# Manage lifecycle via the Manager (Integration Layer)
manager = get_plugin_manager()
status = manager.get_health_summary()
```

## 🛠️ Developer Tools

### Plugin Validator
We provide a strict validation utility to verify your plugin packages:

```bash
python src/ai_karen_engine/extensions/platform/core/registry/plugin_validator.py src/ai_karen_engine/extensions/plugins/template
```

This checks:
- `plugin_manifest.json` against the official JSON Schema.
- Presence of required assets (`prompt.txt`).
- Basic handler integrity (`handler.py`).

## 🚀 Getting Started
1. **Scaffold**: Copy `src/ai_karen_engine/extensions/plugins/template` to a new folder.
2. **Define**: Update `plugin_manifest.json` with your intent and parameters.
3. **Prompt**: Write your Prompt-First contract in `prompt.txt`.
4. **Log**: (Optional) Add custom logic in `handler.py`.
5. **Auto-Discovery**: Restart the platform; your plugin will be detected automatically.

---
*For documentation on creating plugins, see the [Plugin Development Guide](./docs/PLUGIN_DEV.md) (Stage 2).*

*Kari Modular Platform - Orchestrating Truth.*
