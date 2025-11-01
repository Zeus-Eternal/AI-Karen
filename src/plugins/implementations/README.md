# Plugin Implementations

This directory contains all plugin implementations organized by category. Plugins are simple, focused functions that extend system capabilities without the complexity of full extensions.

## Directory Structure

### `examples/`
Example plugins that serve as templates and learning resources for plugin development.

### `core/`
Core system plugins that provide essential functionality:
- Time queries
- TUI fallback systems
- System utilities

### `ai/`
AI and LLM-related plugins:
- LLM service integrations (OpenAI, Gemini, DeepSeek, Llama)
- Model orchestration plugins
- AI utility functions

### `integrations/`
Third-party service integrations:
- Gmail integration
- Weather services
- Search providers
- Yelp integration
- Other external APIs

### `automation/`
Automation and workflow plugins:
- Workflow builders
- Task automation
- Process orchestration

## Plugin Structure

Each plugin should follow this structure:

```
plugin-name/
├── plugin_manifest.json    # Plugin metadata and configuration
├── handler.py             # Main plugin implementation
├── README.md              # Documentation and usage
└── tests/                 # Plugin tests (optional)
    └── test_handler.py
```

## Plugin Manifest Format

```json
{
  "name": "plugin-name",
  "version": "1.0.0",
  "display_name": "Plugin Display Name",
  "description": "Brief description of plugin functionality",
  "category": "core|ai|integrations|automation|examples",
  "handler": "handler.py",
  "entry_point": "main_function",
  "dependencies": [],
  "permissions": [],
  "configuration": {}
}
```

## Development Guidelines

1. **Keep it Simple**: Plugins should be focused, single-purpose functions
2. **Clear Documentation**: Each plugin must have clear documentation
3. **Error Handling**: Implement proper error handling and logging
4. **Security**: Follow security best practices for external integrations
5. **Testing**: Include tests for plugin functionality where appropriate

## Migration Notes

This directory will contain plugins migrated from:
- `src/plugins/*/` (existing plugin implementations)
- `src/marketplace/*/` (marketplace plugin implementations)

The migration will preserve all existing functionality while organizing plugins by category for better discoverability and maintenance.