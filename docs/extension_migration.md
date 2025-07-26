# Migrating from Plugins to Extensions

This guide outlines the steps required to move existing plugins to the hierarchical **Extensions System**.

## 1. Review Plugin Functionality

Identify the features provided by each plugin. Extensions can compose multiple plugins so you may merge related functionality under a single extension.

## 2. Create an Extension Manifest

Each extension requires an `extension.json` manifest describing metadata, capabilities and dependencies. See `extensions/README.md` for the manifest schema.

```bash
mkdir -p extensions/my-extension
cat > extensions/my-extension/extension.json <<'MANIFEST'
{
  "name": "my-extension",
  "version": "1.0.0",
  "description": "Migrated example from plugin system",
  "category": "custom",
  "dependencies": {"plugins": ["my-plugin"]}
}
MANIFEST
```

## 3. Implement the Extension Class

Create `__init__.py` implementing a subclass of `BaseExtension` and register any existing plugins through the `PluginOrchestrator`.

```python
from ai_karen_engine.extensions import BaseExtension

class MyExtension(BaseExtension):
    async def initialize(self):
        await self.register_plugins(["my-plugin"])  # reuse existing plugin
```

## 4. Register UI Components

Extensions can provide React components for the Web UI. Add any previous plugin pages under the extension and register them in `initialize()` using the UI manager.

## 5. Update Configuration

Replace old plugin configuration entries with extension names. The extension manager resolves dependencies and handles lifecycle events.

## 6. Validate and Test

Run `pytest tests/test_extension_loading.py` to ensure the extension loads correctly. Existing plugin tests should continue to work when called via the extension interface.

