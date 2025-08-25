# Plugin Specification

This document describes how to build plugins for Kari and how they are loaded at runtime.

Plugins live under the `src/ai_karen_engine/plugins/` folder and must contain at least a `plugin_manifest.json` and a `handler.py` file. Optionally a `ui.py` file can expose a widget for the Control Room.

## Manifest Schema

| Field | Type | Description |
| ----- | ---- | ----------- |
| `name` | string | Human readable plugin name. |
| `version` | string | Semantic version of the plugin. |
| `description` | string | Short summary shown in the UI. |
| `author` | string | Plugin author or maintainer. |
| `license` | string | License string, defaults to `"MIT"`. |
| `plugin_api_version` | string | Plugin API version, must be `"1.0"` or `"1.1"`. |
| `plugin_type` | string | Plugin type such as `custom` or `integration`. |
| `module` | string | Python module path to the plugin handler. |
| `entry_point` | string | Function inside `module` used to run the plugin. |
| `required_roles` | list of strings | Roles allowed to invoke the plugin. |
| `trusted_ui` | bool | Load `ui.py` without ADVANCED_MODE when `true`. |
| `enable_external_workflow` | bool | Allow calls to external workflows. |
| `sandbox_required` | bool | Run the plugin in a sandbox if `true`. |
| `dependencies` | list | Dependency specifications for other plugins. |
| `compatibility` | object | Version and platform compatibility info. |
| `tags` | list of strings | Extra search tags. |
| `category` | string | Plugin category grouping. |
| `intent` | string | Intent handled by this plugin. |

Plugin discovery reads this file into `PluginManifest`. Extra keys are allowed, but omitting a required field like `name` or `module` will cause discovery errors.

Example `plugin_manifest.json`:

```json
{
  "name": "hello-world",
  "version": "1.0.0",
  "description": "Simple example plugin",
  "author": "ACME",
  "plugin_type": "custom",
  "module": "ai_karen_engine.plugins.hello_world.handler",
  "entry_point": "run",
  "plugin_api_version": "1.0",
  "intent": "hello_world",
  "required_roles": ["user"],
  "trusted_ui": false,
  "enable_external_workflow": false,
  "sandbox_required": true,
  "tags": ["example"],
  "category": "utility",
  "dependencies": [],
  "compatibility": {}
}
```

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
