# Automation Features

Kari includes a lightweight automation layer for chaining tasks and local RPA actions. These helpers are designed for on-prem deployments where network access may be limited.

## 1. Automation Manager

The `AutomationManager` collects asynchronous tasks and executes them sequentially. Plugins can enqueue coroutines that interact with external systems or local scripts.

```python
from integrations.automation_manager import AutomationManager

auto = AutomationManager()
auto.add_task(some_async_task())
results = await auto.run_all()
```

## 2. Local RPA Client

`LocalRPAClient` wraps **PyAutoGUI** for desktop automation. It can click, type, and take screenshots.

```python
from integrations.local_rpa_client import LocalRPAClient

rpa = LocalRPAClient()
rpa.click(100, 200)
rpa.type_text("hello world")
rpa.screenshot("/tmp/snap.png")
```

Use this only on trusted machines because it controls the local keyboard and mouse.

## 3. Workflow Engine Integration

`WorkflowEngineClient` is a simple bridge to trigger n8n workflows. Set `workflow_slug` in a plugin manifest and call `trigger()` with a payload.

```python
from src.core.workflow_engine_client import WorkflowEngineClient

wf = WorkflowEngineClient()
wf.trigger("onboarding", {"user_id": 123})
```

In production you would implement real HTTP calls to your n8n instance. The current stub simply prints to the console.

## Basic vs Advanced

- **Basic usage** uses only the local AutomationManager and RPA client.
- **Advanced usage** combines RPA tasks with external workflow triggers via n8n when enabled by the plugin manifest.

