# n8n Workflow Integration

Kari can interface with n8n to trigger external workflows. This is useful for complex automations that span multiple services.

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

The default implementation prints the payload. Replace the method with an HTTP request to your n8n API for production use.
