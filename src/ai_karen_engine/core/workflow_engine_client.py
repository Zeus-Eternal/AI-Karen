import logging


logger = logging.getLogger(__name__)


class WorkflowEngineClient:
    """Simple stub for triggering n8n workflows."""

    def trigger(self, workflow_slug: str, payload: dict) -> None:
        """Trigger the workflow identified by ``workflow_slug`` with ``payload``."""
        logger.info(
            "[WorkflowEngine] Triggered %s with %s", workflow_slug, payload
        )

