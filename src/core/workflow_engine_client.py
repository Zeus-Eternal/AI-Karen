class WorkflowEngineClient:
    """Mock client that would trigger n8n workflows."""

    def trigger(self, workflow_slug: str, payload: dict) -> None:
        # In real implementation this would perform an HTTP request to n8n
        print(f"[WorkflowEngine] Triggered {workflow_slug} with {payload}")
