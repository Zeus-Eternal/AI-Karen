# AI Karen - Directory Structure

## Overview

This document describes the clean, DRY organization of AI Karen's extensions and plugins architecture.

## Core Principles

1. **Single Source of Truth** - Framework code lives in one place
2. **Clear Separation** - Extensions vs Plugins are clearly separated
3. **No Duplication** - No duplicate framework files
4. **Production Ready** - All wiring configured for production use

## Directory Structure

```
src/
├── ai_karen_engine/              # 🎯 Core Runtime Framework
│   ├── extensions/               # Extension framework (manager, orchestrator, etc.)
│   ├── plugins/                  # Plugin framework (router, manager, sandbox)
│   └── ...                       # Other core engine components
│
├── extensions/                   # 📦 Extension Implementations
│   ├── security/                 # Security extension
│   ├── debugging/                # Debugging extension
│   ├── performance/              # Performance monitoring extension
│   ├── sdk/                      # Extension development SDK
│   ├── marketplace-extension/    # Marketplace extension
│   ├── community/                # Community features extension
│   ├── onboarding/               # User onboarding extension
│   ├── launch/                   # Launch management extension
│   ├── lifecycle/                # Lifecycle management extension
│   ├── cli/                      # Extension CLI tools
│   ├── docs/                     # Extension documentation
│   ├── tests/                    # Extension tests
│   └── _framework-reference/     # Framework reference (for development)
│
└── plugins/                      # 🔌 Plugin Implementations
    ├── ai/                       # AI & LLM plugins
    │   ├── fine-tune-lnm/
    │   ├── hf-llm/
    │   ├── llm-services/
    │   ├── llm_manager/
    │   └── llm_services/
    ├── automation/               # Automation & workflow plugins
    │   ├── autonomous-task-handler/
    │   └── git-merge-safe/
    ├── integrations/             # Third-party integrations
    │   ├── desktop-agent/
    │   ├── k8s-scale/
    │   ├── gmail_plugin/
    │   ├── search/
    │   ├── searxng/
    │   ├── yelp/
    │   ├── weather_query/
    │   └── ...
    ├── system/                   # Core system plugins
    │   ├── time-query/
    │   └── tui-fallback/
    ├── examples/                 # Example plugins
    │   ├── hello_world/
    │   └── sandbox_fail/
    ├── __meta/                   # Plugin system metadata
    ├── memory_manager.py         # Plugin memory management
    ├── README.md                 # Plugin system documentation
    └── __init__.py               # Plugin exports
```

## Architecture

### Extensions (Complex Features)

**Location:** `src/extensions/`
**Framework:** `src/ai_karen_engine/extensions/`

Extensions are complex, feature-rich modules suitable for:
- Multi-component features
- Complex business logic
- UI components and interfaces
- Background services
- Database integrations
- Multiple API endpoints

**Example Extensions:**
- Security (authentication, authorization, audit logging)
- Debugging (profiler, tracer, error tracker, metrics)
- Performance (caching, optimization, scaling)

### Plugins (Focused Functions)

**Location:** `src/plugins/`
**Framework:** `src/ai_karen_engine/plugins/`

Plugins are simple, focused functions suitable for:
- Single-purpose utilities
- Quick integrations
- Simple transformations
- Lightweight tools
- External API calls
- Data processing functions

**Example Plugins:**
- Time queries
- Weather lookups
- Search integrations
- LLM service connectors

## Framework vs Implementations

### Framework Code (DO NOT MODIFY WITHOUT REVIEW)

Located in `src/ai_karen_engine/`:
- `extensions/manager.py` - Extension lifecycle management
- `extensions/orchestrator.py` - Extension orchestration
- `plugins/router.py` - Plugin routing and discovery
- `plugins/manager.py` - Plugin lifecycle management
- `plugins/sandbox.py` - Plugin sandboxing

### Implementation Code (EXTEND HERE)

Located in `src/extensions/` and `src/plugins/`:
- Add new extensions to `src/extensions/[name]/`
- Add new plugins to `src/plugins/[category]/[name]/`

## Removed Duplicates

The following directories have been removed as part of cleanup:

- ❌ `src/marketplace/` → Merged into `src/plugins/`
- ❌ `src/core/extensions/` → Moved to `src/extensions/`
- ❌ `src/extensions/plugins/` → Merged into `src/plugins/`
- ❌ `src/plugins/manager.py` → Duplicate removed
- ❌ `src/plugins/router.py` → Duplicate removed
- ❌ `src/plugins/sandbox*.py` → Duplicates removed

## Import Paths

### For Extensions

```python
# Framework imports
from ai_karen_engine.extensions import ExtensionManager, ExtensionOrchestrator

# Implementation imports
from extensions.security import SecurityExtension
from extensions.debugging import DebugExtension
```

### For Plugins

```python
# Framework imports
from ai_karen_engine.plugins import PluginRouter, PluginManager

# Implementation imports (via router discovery)
# Plugins are discovered automatically by the PluginRouter
```

## Migration Guide

If you have code referencing old paths:

| Old Path | New Path |
|----------|----------|
| `from src.marketplace.ai.*` | `from plugins.ai.*` |
| `from src.core.extensions.security` | `from extensions.security` |
| `from src.plugins.router` | `from ai_karen_engine.plugins.router` |
| `from src.extensions.core.manager` | `from ai_karen_engine.extensions.manager` |

## Development Workflow

### Creating a New Extension

1. Create directory: `src/extensions/[name]/`
2. Add implementation files
3. Register with extension manager
4. Add tests
5. Update documentation

### Creating a New Plugin

1. Choose category: `ai`, `automation`, `integrations`, `system`, or `examples`
2. Create directory: `src/plugins/[category]/[name]/`
3. Add `plugin_manifest.json`
4. Add `handler.py` with `async def run(params)` function
5. Add `README.md`
6. Plugin auto-discovered by PluginRouter

## Production Wiring

All imports and discovery paths have been updated to reference the new structure:

- ✅ Extension discovery points to `src/extensions/`
- ✅ Plugin discovery points to `src/plugins/`
- ✅ Framework imports reference `src/ai_karen_engine/`
- ✅ No circular dependencies
- ✅ Clear separation of concerns

## Summary

- **Framework:** `src/ai_karen_engine/` (core runtime)
- **Extensions:** `src/extensions/` (complex features)
- **Plugins:** `src/plugins/` (simple functions)
- **No Duplication:** Single source of truth for all code
- **Production Ready:** All wiring configured and tested
