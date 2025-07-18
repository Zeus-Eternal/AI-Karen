# Kari AI Plugin Marketplace

This directory contains plugins for the Kari AI platform. Plugins are organized by category:

- `examples/` - Example plugins for learning and testing
- `core/` - Core functionality plugins
- `automation/` - Automation and workflow plugins  
- `ai/` - AI and machine learning plugins
- `integrations/` - Third-party service integrations

## Plugin Development

Each plugin should have its own directory with:
- `__init__.py` - Plugin entry point
- `handler.py` - Main plugin logic
- `plugin_manifest.json` - Plugin metadata
- `README.md` - Plugin documentation

See the examples directory for reference implementations.

## Plugin Structure

```
plugins/category/plugin-name/
├── __init__.py              # Plugin entry point
├── handler.py               # Main plugin logic
├── plugin_manifest.json     # Plugin metadata
├── README.md               # Plugin documentation
└── ...                     # Additional plugin files
```

## Categories

### Examples
Example plugins that demonstrate plugin development patterns and serve as templates for new plugins.

### Core
Essential functionality plugins that provide basic system capabilities.

### Automation
Plugins that enable automation, workflow management, and task scheduling.

### AI
Plugins that provide AI and machine learning capabilities, including LLM integrations.

### Integrations
Plugins that integrate with external services, APIs, and third-party tools.

## Plugin Discovery

The plugin system automatically discovers plugins in this directory structure. Plugins are loaded based on their category and manifest configuration.

## Development Guidelines

1. Follow the standard plugin structure
2. Include comprehensive documentation
3. Provide clear plugin manifests
4. Test plugins thoroughly
5. Follow security best practices