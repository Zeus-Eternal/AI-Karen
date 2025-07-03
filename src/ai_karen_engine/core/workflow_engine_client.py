class WorkflowEngineClient:
    """Simple stub for triggering n8n workflows."""

    def trigger(self, workflow_slug: str, payload: dict) -> None:
        """Trigger the workflow identified by ``workflow_slug`` with ``payload``."""
        print(f"[WorkflowEngine] Triggered {workflow_slug} with {payload}")

