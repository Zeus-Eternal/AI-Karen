# Extension Developer Guide

This guide summarizes best practices for building extensions that integrate smoothly with the AI Karen platform.

## Project Layout

```
my-extension/
├── extension.json         # Manifest
├── __init__.py           # Extension class
├── ui/                   # Optional React components
├── plugins/              # Reused or custom plugins
└── tests/                # Unit tests
```

## Key Interfaces

Extensions subclass `ai_karen_engine.extensions.BaseExtension` and may override these hooks:

- `initialize()` – prepare resources and register plugins or UI components.
- `activate()` – start background tasks or services.
- `deactivate()` – gracefully shut down and release resources.

Use `ExtensionDataManager` for storing data and `PluginOrchestrator` to run plugins in workflows.

## Example

```python
from ai_karen_engine.extensions import BaseExtension

class TaskManagerExtension(BaseExtension):
    async def initialize(self):
        await self.register_plugins(["task-db", "reminder"])

    async def activate(self):
        await self.start_background_tasks()
```

## Testing

Run `pytest` inside the extension directory. Include tests for manifest validation and any background tasks.

## Distribution

Package the extension directory as a zip file and upload it to the marketplace. The manifest version field controls update checks.

