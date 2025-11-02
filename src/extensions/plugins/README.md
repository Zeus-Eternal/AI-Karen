# Consolidated Plugin System

This directory contains the unified plugin system that consolidates the functionality from the previous `src/plugins` and `src/marketplace` plugin frameworks.

## Architecture

The plugin system is organized as follows:

```
src/extensions/plugins/
├── __init__.py                    # Main plugin system exports
├── core/                          # Plugin framework components
│   ├── __init__.py               # Core framework exports
│   ├── manager.py                # PluginManager (from src/plugins)
│   ├── router.py                 # PluginRouter (from src/plugins)
│   ├── sandbox.py                # Sandbox execution (from src/plugins)
│   ├── sandbox_runner.py         # Sandbox runner (from src/plugins)
│   ├── memory_manager.py         # MemoryManager (from src/marketplace)
│   └── tests/                    # Framework tests
├── implementations/              # Plugin implementations (organized by category)
│   ├── examples/                 # Example plugins
│   ├── core/                     # Core system plugins
│   ├── ai/                       # AI/LLM plugins
│   ├── integrations/             # Third-party integrations
│   └── automation/               # Automation plugins
└── docs/                         # Plugin system documentation
```

## Key Components

### PluginManager
- Manages plugin execution with metrics and memory persistence
- Integrates with the unified memory system
- Provides prometheus metrics for monitoring
- Handles plugin lifecycle and error recovery

### PluginRouter
- Discovers and validates plugins from the implementations directory
- Supports categorized plugin structure
- Provides Jinja2-powered prompt rendering
- Enforces RBAC (Role-Based Access Control)
- Handles sandbox execution

### MemoryManager
- Lightweight interface to the unified memory system
- Allows plugins to store and recall information
- Supports tenant isolation

### Sandbox System
- Executes plugins in isolated subprocesses
- Provides CPU and memory limits
- Handles timeouts and error recovery

## Usage

### Basic Plugin Execution

```python
from src.extensions.plugins import PluginManager, PluginRouter

# Create plugin manager
manager = PluginManager()

# Execute a plugin
result, stdout, stderr = await manager.run_plugin(
    name="time-query",
    params={"format": "iso"},
    user_ctx={"user_id": "123", "roles": ["user"]}
)
```

### Plugin Discovery

```python
from src.extensions.plugins import PluginRouter

# Create router and discover plugins
router = PluginRouter()
intents = router.list_intents()

# Get specific plugin
plugin = router.get_plugin("time-query")
```

### Memory Integration

```python
from src.extensions.plugins import MemoryManager

# Create memory manager
memory = MemoryManager(tenant_id="tenant123")

# Store information
memory.write(user_ctx, "weather query", {"location": "NYC", "temp": "72F"})

# Recall information
memories = memory.read(user_ctx, "weather", limit=5)
```

## Backward Compatibility

The system maintains backward compatibility through compatibility layers at:
- `src/ai_karen_engine/plugins/` - Re-exports for existing imports

This allows existing code to continue working while new code can use the consolidated imports.

## Migration from Old System

### Old Imports (still supported)
```python
from ai_karen_engine.plugins.router import PluginRouter
from ai_karen_engine.plugins.manager import PluginManager
```

### New Imports (recommended)
```python
from src.extensions.plugins import PluginRouter, PluginManager
# or
from src.extensions.plugins.core.router import PluginRouter
from src.extensions.plugins.core.manager import PluginManager
```

## Plugin Development

See `implementations/README.md` for detailed information on developing plugins for the consolidated system.

## Testing

Run the framework integration tests:

```bash
python -m pytest src/extensions/plugins/core/tests/
```

## Configuration

The plugin system can be configured through environment variables:

- `KARI_PLUGIN_DIR`: Override the default plugin implementations directory
- `KARI_CPU_LIMIT`: Set CPU limits for sandboxed plugin execution
- `ADVANCED_MODE`: Enable advanced features like trusted UI components

## Security

- Plugins run in sandboxed environments by default
- RBAC controls access to plugins based on user roles
- Memory operations are tenant-isolated
- UI components require explicit trust settings