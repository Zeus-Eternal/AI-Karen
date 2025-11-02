# Plugin Implementations

This directory contains plugin implementations organized by category. Plugins are simple, focused functions that can be executed in a sandboxed environment with proper security controls.

## Directory Structure

```
implementations/
├── examples/           # Example plugins for learning and testing
├── core/              # Core system plugins (time, system utilities)
├── ai/                # AI/LLM related plugins
├── integrations/      # Third-party service integrations
└── automation/        # Automation and workflow plugins
```

## Plugin Structure

Each plugin should be in its own directory with the following structure:

```
plugin-name/
├── plugin_manifest.json  # Plugin metadata and configuration
├── handler.py            # Main plugin logic
├── README.md            # Plugin documentation
└── ui.py               # Optional UI components (if trusted_ui is true)
```

## Plugin Manifest

The `plugin_manifest.json` file contains metadata about the plugin:

```json
{
  "plugin_api_version": "1.0",
  "intent": ["plugin-name"],
  "required_roles": [],
  "trusted_ui": false,
  "sandbox": true,
  "description": "Plugin description",
  "author": "Author name",
  "version": "1.0.0"
}
```

## Handler Implementation

The `handler.py` file must contain a `run` function:

```python
async def run(params):
    """Plugin main logic."""
    # Your plugin implementation here
    return {"result": "success"}
```

## Security

- Plugins run in a sandboxed environment by default
- Set `sandbox: false` in manifest only if absolutely necessary
- Use `required_roles` to restrict access to specific user roles
- Set `trusted_ui: true` only for plugins that need UI components

## Development

1. Create a new directory under the appropriate category
2. Add the required files (manifest, handler, README)
3. Test your plugin using the plugin router
4. Document any dependencies or special requirements

For more information, see the plugin development guide in the docs directory.