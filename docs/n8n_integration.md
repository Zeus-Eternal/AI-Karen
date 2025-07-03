# n8n Workflow Integration

Kari includes a proprietary bridge to n8n for orchestrating external workflows. Use it to chain our local agents with your existing automation pipelines.

## Setup

1. Configure an n8n instance reachable from the Kari host.
2. In a plugin's `plugin_manifest.json`, set:
   ```json
   {
     "enable_external_workflow": true,
     "workflow_slug": "support_ticket"
   }
   ```
3. In your plugin code, call `WorkflowEngineClient.trigger()` with the desired slug and payload.

```python
from src.core.workflow_engine_client import WorkflowEngineClient

wf = WorkflowEngineClient()
wf.trigger("support_ticket", {"issue": "printer jam"})
```

The open-source implementation prints the payload. The production build uses our custom HTTP layer to communicate securely with n8n.
