# Directory Structure Analysis

## Current State Analysis

### Plugin System Files (Need Reorganization)

#### System Code (Currently Mixed Locations)
```
src/ai_karen_engine/
├── plugin_manager.py          # Plugin system - NEEDS MOVE
├── plugin_router.py           # Plugin system - NEEDS MOVE  
└── plugins/
    ├── sandbox.py             # Plugin system - NEEDS MOVE
    ├── sandbox_runner.py      # Plugin system - NEEDS MOVE
    └── __init__.py            # Plugin system - NEEDS UPDATE
```

#### Individual Plugins (Currently in System Directory)
```
src/ai_karen_engine/plugins/
├── hello_world/               # Individual plugin - NEEDS MOVE
├── time_query/                # Individual plugin - NEEDS MOVE
├── autonomous_task_handler/   # Individual plugin - NEEDS MOVE
├── desktop_agent/             # Individual plugin - NEEDS MOVE
├── fine_tune_lnm/             # Individual plugin - NEEDS MOVE
├── git_merge_safe/            # Individual plugin - NEEDS MOVE
├── hf_llm/                    # Individual plugin - NEEDS MOVE
├── k8s_scale/                 # Individual plugin - NEEDS MOVE
├── llm_manager/               # Individual plugin - NEEDS MOVE
├── llm_services/              # Individual plugin category - NEEDS MOVE
├── sandbox_fail/              # Individual plugin - NEEDS MOVE
├── tui_fallback/              # Individual plugin - NEEDS MOVE
└── __meta/                    # Plugin metadata - NEEDS MOVE
```

### Extension System Files (Already Well Organized)
```
extensions/                    # Extension development - GOOD
├── examples/
├── automation/
└── ...

src/ai_karen_engine/extensions/ # Extension system code - GOOD
├── manager.py
├── base.py
├── orchestrator.py
└── ...
```

## Import Dependencies Analysis

### Current Import Patterns

#### Plugin System Imports (Need Updates)
```python
# Current problematic imports:
from ai_karen_engine.plugin_manager import PluginManager
from ai_karen_engine.plugin_router import PluginRouter
from ai_karen_engine.plugins.sandbox import PluginSandbox

# Individual plugin imports:
from ai_karen_engine.plugins.hello_world.handler import run
from ai_karen_engine.plugins.time_query.handler import run
```

#### Files Using Plugin System Imports
1. `src/ai_karen_engine/extensions/orchestrator.py` - imports PluginRouter
2. `src/ai_karen_engine/extensions/manager.py` - imports PluginRouter
3. `src/ai_karen_engine/__init__.py` - lazy imports plugin components
4. `src/ai_karen_engine/fastapi.py` - imports get_plugin_router
5. `src/ai_karen_engine/core/cortex/dispatch.py` - imports get_plugin_manager
6. `main.py` - imports get_plugin_router
7. `cli.py` - imports get_plugin_router
8. Multiple test files import plugin components

#### Files Using Individual Plugin Imports
1. `tests/test_llm_manager.py` - imports plugin handler
2. Internal plugin cross-references (plugins importing other plugins)
3. Documentation examples in `AGENTS.md`

## Target Structure Mapping

### Plugin System Reorganization

#### New Plugin System Structure
```
src/ai_karen_engine/plugins/   # Plugin system code
├── __init__.py                # Clean exports
├── manager.py                 # From plugin_manager.py
├── router.py                  # From plugin_router.py
├── registry.py                # New plugin registry
├── sandbox.py                 # From plugins/sandbox.py
└── sandbox_runner.py          # From plugins/sandbox_runner.py
```

#### New Plugin Marketplace Structure
```
plugins/                       # Plugin development/marketplace
├── README.md                  # Plugin development guide
├── examples/                  # Example plugins
│   ├── hello-world/          # From src/.../plugins/hello_world/
│   └── sandbox-fail/         # From src/.../plugins/sandbox_fail/
├── core/                     # Core functionality plugins
│   ├── time-query/           # From src/.../plugins/time_query/
│   └── tui-fallback/         # From src/.../plugins/tui_fallback/
├── automation/               # Automation plugins
│   ├── autonomous-task-handler/ # From src/.../plugins/autonomous_task_handler/
│   └── git-merge-safe/       # From src/.../plugins/git_merge_safe/
├── ai/                       # AI/ML plugins
│   ├── hf-llm/               # From src/.../plugins/hf_llm/
│   ├── fine-tune-lnm/        # From src/.../plugins/fine_tune_lnm/
│   └── llm-services/         # From src/.../plugins/llm_services/
├── integrations/             # Integration plugins
│   ├── desktop-agent/        # From src/.../plugins/desktop_agent/
│   ├── k8s-scale/            # From src/.../plugins/k8s_scale/
│   └── llm-manager/          # From src/.../plugins/llm_manager/
└── __meta/                   # Plugin metadata
    └── command_manifest.json # From src/.../plugins/__meta/
```

### Import Path Mappings

#### Plugin System Import Mappings
```python
# Old -> New mappings
PLUGIN_SYSTEM_MAPPINGS = {
    "ai_karen_engine.plugin_manager": "ai_karen_engine.plugins.manager",
    "ai_karen_engine.plugin_router": "ai_karen_engine.plugins.router",
    "ai_karen_engine.plugins.sandbox": "ai_karen_engine.plugins.sandbox",
    "ai_karen_engine.plugins.sandbox_runner": "ai_karen_engine.plugins.sandbox_runner",
}
```

#### Individual Plugin Import Mappings
```python
# Old -> New mappings for individual plugins
PLUGIN_MAPPINGS = {
    "ai_karen_engine.plugins.hello_world": "plugins.examples.hello_world",
    "ai_karen_engine.plugins.time_query": "plugins.core.time_query",
    "ai_karen_engine.plugins.autonomous_task_handler": "plugins.automation.autonomous_task_handler",
    "ai_karen_engine.plugins.desktop_agent": "plugins.integrations.desktop_agent",
    "ai_karen_engine.plugins.fine_tune_lnm": "plugins.ai.fine_tune_lnm",
    "ai_karen_engine.plugins.git_merge_safe": "plugins.automation.git_merge_safe",
    "ai_karen_engine.plugins.hf_llm": "plugins.ai.hf_llm",
    "ai_karen_engine.plugins.k8s_scale": "plugins.integrations.k8s_scale",
    "ai_karen_engine.plugins.llm_manager": "plugins.integrations.llm_manager",
    "ai_karen_engine.plugins.llm_services": "plugins.ai.llm_services",
    "ai_karen_engine.plugins.sandbox_fail": "plugins.examples.sandbox_fail",
    "ai_karen_engine.plugins.tui_fallback": "plugins.core.tui_fallback",
}
```

## Migration Complexity Assessment

### High-Risk Areas

1. **Plugin Discovery Logic**: Current plugin discovery scans `src/ai_karen_engine/plugins/` for individual plugins
2. **Dynamic Imports**: Plugin router uses dynamic imports that depend on current paths
3. **Extension-Plugin Integration**: Extensions use plugin orchestrator which imports plugin system
4. **Test Dependencies**: Many tests import specific plugins directly
5. **External Documentation**: AGENTS.md and other docs reference current paths

### Medium-Risk Areas

1. **API Routes**: Some API routes may import plugin components
2. **Configuration**: Plugin configuration may reference current paths
3. **Logging**: Log messages may reference current plugin paths
4. **Metrics**: Plugin metrics collection may use current paths

### Low-Risk Areas

1. **Extension System**: Already well-organized, minimal changes needed
2. **Core System**: Most core components don't directly import individual plugins
3. **UI Components**: UI components typically use plugin system through APIs

## Migration Strategy

### Phase 1: Plugin System Code Reorganization
1. Create new `src/ai_karen_engine/plugins/` structure for system code
2. Move `plugin_manager.py` -> `src/ai_karen_engine/plugins/manager.py`
3. Move `plugin_router.py` -> `src/ai_karen_engine/plugins/router.py`
4. Move `plugins/sandbox.py` -> `src/ai_karen_engine/plugins/sandbox.py`
5. Move `plugins/sandbox_runner.py` -> `src/ai_karen_engine/plugins/sandbox_runner.py`
6. Create clean `__init__.py` with proper exports

### Phase 2: Plugin Marketplace Creation
1. Create root `plugins/` directory with category structure
2. Move individual plugins to appropriate categories
3. Update plugin manifests and metadata
4. Create plugin development documentation

### Phase 3: Import Path Updates
1. Update all internal imports to use new plugin system paths
2. Update plugin discovery logic to scan new marketplace directory
3. Create compatibility layer for external code
4. Update tests and documentation

### Phase 4: Validation and Cleanup
1. Comprehensive testing of new structure
2. Performance validation
3. Documentation updates
4. Gradual removal of compatibility layer

## Files Requiring Updates

### Core System Files
- `src/ai_karen_engine/__init__.py` - Update lazy imports
- `src/ai_karen_engine/fastapi.py` - Update plugin router import
- `src/ai_karen_engine/extensions/orchestrator.py` - Update plugin router import
- `src/ai_karen_engine/extensions/manager.py` - Update plugin router import
- `src/ai_karen_engine/core/cortex/dispatch.py` - Update plugin manager import
- `main.py` - Update plugin router import
- `cli.py` - Update plugin router import

### Test Files
- `tests/test_plugin_router.py` - Update imports
- `tests/test_sandbox.py` - Update imports
- `tests/test_workflow_rpa.py` - Update imports
- `tests/test_imports.py` - Update import tests
- `tests/test_llm_manager.py` - Update plugin import

### Documentation Files
- `AGENTS.md` - Update plugin import examples
- Various README files - Update plugin references

### Configuration Files
- Plugin discovery configuration
- API route registration
- Test configuration

This analysis provides the foundation for implementing the directory structure reorganization systematically and safely.