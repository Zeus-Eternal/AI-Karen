# Plugin Specification

This document describes how to build plugins for Kari and how they are loaded at runtime.

Plugins live under the `src/ai_karen_engine/plugins/` folder and must contain at least a `plugin_manifest.json` and a `handler.py` file. Optionally a `ui.py` file can expose a widget for the Control Room.

## Manifest Schema

| Field | Type | Description |
| ----- | ---- | ----------- |
| `plugin_api_version` | string | Currently must be `"1.0"`. Plugins with other versions are ignored. |
| `intent` | string or list | Intent names that this plugin handles. |
| `required_roles` | list of strings | Roles allowed to invoke the plugin. |
| `enable_external_workflow` | bool | If `true` the plugin may call an external n8n workflow. |
| `workflow_slug` | string | Optional slug passed to the workflow engine. |
| `trusted_ui` | bool | If `true`, the Control Room will render `ui.py` without requiring `ADVANCED_MODE`. |

The manifest is validated against `config/plugin_schema.json` when `PluginRouter.load_plugins()` scans the directory. Plugins missing required fields are skipped.

## Handler Interface

`handler.py` must export a `run(params: dict) -> dict | str` function. It receives the request parameters and returns a response. Async functions are supported.

```python
# src/ai_karen_engine/plugins/hello_world/handler.py

def run(params: dict) -> dict:
    return {"message": "Hello World from plugin!"}
```

Plugins may also expose optional helper functions, but only `run` is required.

## UI Injection

If a plugin provides `ui.py` with a `render()` function, the Control Room will automatically load it when the plugin is enabled. Untrusted UIs are only loaded when `ADVANCED_MODE=true` or the manifest sets `trusted_ui: true`.

```python
# ui.py
import reacton

def render():
    return reacton.h("div", {}, ["Custom Widget"])
```

Reload plugins via the API:

```bash
curl -X POST http://localhost:8000/plugins/reload
```

See [docs/n8n_integration.md](n8n_integration.md) for workflow usage and [docs/security.md](security.md) for RBAC details.
