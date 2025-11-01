# AI Karen Plugin System

The AI Karen Plugin System provides a lightweight framework for building simple, focused functions that extend system capabilities.

## Directory Structure

```
src/plugins/
├── README.md                    # This file - system overview
├── __init__.py                  # Main exports and backward compatibility
├── core/                        # Plugin framework code
│   ├── __init__.py             # Core framework exports
│   ├── manager.py              # PluginManager (to be moved from root)
│   ├── router.py               # PluginRouter (to be moved from root)
│   ├── memory_manager.py       # MemoryManager (from marketplace)
│   ├── sandbox.py              # Plugin sandbox system (to be moved from root)
│   └── tests/                  # Framework tests
├── implementations/            # Plugin implementations by category
│   ├── README.md               # Implementation guide
│   ├── examples/               # Example plugins and templates
│   ├── core/                   # Core system plugins
│   ├── ai/                     # AI and LLM plugins
│   ├── integrations/           # Third-party integrations
│   └── automation/             # Automation and workflow plugins
├── docs/                       # Plugin system documentation
│   ├── README.md               # Documentation overview
│   ├── development-guide.md    # Plugin development guide
│   ├── marketplace-guide.md    # Marketplace integration guide
│   └── troubleshooting-guide.md # Common issues and solutions
└── [current files]             # Current plugin files (to be reorganized)
```

## Plugin vs Extension

**Plugins** are simple, focused functions suitable for:
- Single-purpose utilities
- Quick integrations
- Simple transformations
- Lightweight tools
- External API calls
- Data processing functions

**Extensions** are complex, feature-rich modules suitable for:
- Multi-component features
- Complex business logic
- UI components and interfaces
- Background services
- Database integrations

## Framework Components

### Core Classes
- **PluginManager**: Manages plugin discovery and lifecycle
- **PluginRouter**: Routes plugin requests and handles execution
- **MemoryManager**: Manages plugin memory and state
- **PluginSandbox**: Provides secure execution environment

### Plugin Structure
Each plugin should include:
- `plugin_manifest.json`: Plugin metadata and configuration
- `handler.py`: Main plugin implementation
- `README.md`: Documentation and usage instructions
- `tests/`: Plugin tests (optional)

## Plugin Categories

### Examples (`implementations/examples/`)
- Template plugins for learning
- Best practice demonstrations
- Development starting points

### Core (`implementations/core/`)
- Essential system plugins
- Time and date utilities
- TUI fallback systems

### AI (`implementations/ai/`)
- LLM service integrations
- Model orchestration
- AI utility functions

### Integrations (`implementations/integrations/`)
- Gmail integration
- Weather services
- Search providers
- External APIs

### Automation (`implementations/automation/`)
- Workflow builders
- Task automation
- Process orchestration

## Development Workflow

1. **Choose Category**: Determine the appropriate plugin category
2. **Create Structure**: Set up plugin files and manifest
3. **Implement Handler**: Write the main plugin function
4. **Test**: Verify plugin functionality
5. **Document**: Provide clear usage instructions

## Getting Started

1. Read the documentation in `docs/development-guide.md`
2. Review example plugins in `implementations/examples/`
3. Copy an example as a starting point
4. Implement your plugin logic
5. Test and document your plugin

## Migration Status

This directory structure is part of the extensions consolidation effort:
- ✅ **Task 1**: New directory structure created
- ⏳ **Task 2**: Extension framework will be organized
- ⏳ **Task 3**: Plugin frameworks will be consolidated in `core/`
- ⏳ **Task 4**: Plugin implementations will be moved to `implementations/`
- ⏳ **Task 5**: Discovery systems will be updated

## Support

- Check `docs/troubleshooting-guide.md` for common issues
- Review example plugins for implementation patterns
- Consult the development guide for best practices
- Examine existing plugins for reference implementations