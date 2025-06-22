# Automation Features

Kari ships with a **proprietary automation layer** for chaining tasks and local RPA actions. It's built for secure on‑prem deployments where network access may be restricted.

## 1. Automation Manager

Our `AutomationManager` orchestrates asynchronous tasks using a custom queue. Plugins can enqueue coroutines that interact with local scripts or trigger n8n workflows.

```python
from integrations.automation_manager import AutomationManager

auto = AutomationManager()
auto.add_task(some_async_task())
results = await auto.run_all()
```

## 2. Local RPA Client

The `LocalRPAClient` is Kari's locked‑down wrapper around **PyAutoGUI** for desktop automation. It can click, type, and take screenshots.

```python
from integrations.local_rpa_client import LocalRPAClient

rpa = LocalRPAClient()
rpa.click(100, 200)
rpa.type_text("hello world")
rpa.screenshot("/tmp/snap.png")
```

Use this only on trusted machines because it controls the local keyboard and mouse.

## 3. Workflow Engine Integration

The `WorkflowEngineClient` provides a proprietary bridge to n8n. Set `workflow_slug` in a plugin manifest and call `trigger()` with a payload.

```python
from core.workflow_engine_client import WorkflowEngineClient

wf = WorkflowEngineClient()
wf.trigger("onboarding", {"user_id": 123})
```

Our production build uses a custom HTTP client to contact your n8n instance. The open‑source stub simply prints the payload.

## Basic vs Advanced

- **Basic usage** uses only the local AutomationManager and RPA client.
- **Advanced usage** combines RPA tasks with external workflow triggers via n8n when enabled by the plugin manifest.

