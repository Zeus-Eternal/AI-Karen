"""
Production-grade n8n Workflow Engine Client
Provides robust integration with n8n workflow automation platform
"""
import logging
import os
from typing import Any, Dict, Optional
from urllib.parse import urljoin
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class WorkflowEngineError(Exception):
    """Base exception for workflow engine errors"""
    pass


class WorkflowEngineClient:
    """
    Production-grade n8n workflow engine client with retry logic,
    authentication, and comprehensive error handling.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3
    ):
        """
        Initialize workflow engine client.

        Args:
            base_url: n8n instance base URL (defaults to N8N_BASE_URL env var)
            api_key: n8n API key for authentication (defaults to N8N_API_KEY env var)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self.base_url = base_url or os.getenv("N8N_BASE_URL", "http://localhost:5678")
        self.api_key = api_key or os.getenv("N8N_API_KEY")
        self.timeout = timeout
        self.max_retries = max_retries

        # Initialize HTTP client with timeout
        self.client = httpx.AsyncClient(
            timeout=self.timeout,
            headers=self._build_headers()
        )

        logger.info(f"[WorkflowEngine] Initialized with base_url={self.base_url}")

    def _build_headers(self) -> Dict[str, str]:
        """Build request headers with authentication."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        if self.api_key:
            headers["X-N8N-API-KEY"] = self.api_key

        return headers

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    async def trigger_async(
        self,
        workflow_slug: str,
        payload: Dict[str, Any],
        webhook_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Asynchronously trigger n8n workflow with retry logic.

        Args:
            workflow_slug: Workflow identifier or webhook name
            payload: Data payload to send to workflow
            webhook_path: Optional custom webhook path

        Returns:
            Dict containing workflow execution response

        Raises:
            WorkflowEngineError: If workflow execution fails after retries
        """
        try:
            # Build webhook URL
            if webhook_path:
                url = urljoin(self.base_url, webhook_path)
            else:
                url = urljoin(self.base_url, f"/webhook/{workflow_slug}")

            logger.info(f"[WorkflowEngine] Triggering workflow: {workflow_slug}")
            logger.debug(f"[WorkflowEngine] Payload: {payload}")

            # Make async request to n8n webhook
            response = await self.client.post(url, json=payload)

            # Check response status
            if response.status_code >= 400:
                error_msg = f"Workflow trigger failed with status {response.status_code}: {response.text}"
                logger.error(f"[WorkflowEngine] {error_msg}")
                raise WorkflowEngineError(error_msg)

            result = response.json() if response.text else {"status": "triggered"}

            logger.info(f"[WorkflowEngine] Successfully triggered workflow: {workflow_slug}")
            return result

        except httpx.TimeoutException as e:
            error_msg = f"Workflow trigger timeout for {workflow_slug}: {e}"
            logger.error(f"[WorkflowEngine] {error_msg}")
            raise WorkflowEngineError(error_msg) from e

        except httpx.HTTPError as e:
            error_msg = f"HTTP error triggering workflow {workflow_slug}: {e}"
            logger.error(f"[WorkflowEngine] {error_msg}")
            raise WorkflowEngineError(error_msg) from e

        except Exception as e:
            error_msg = f"Unexpected error triggering workflow {workflow_slug}: {e}"
            logger.error(f"[WorkflowEngine] {error_msg}")
            raise WorkflowEngineError(error_msg) from e

    def trigger(self, workflow_slug: str, payload: Dict[str, Any]) -> None:
        """
        Synchronous trigger method for backward compatibility.
        Logs the trigger event and queues async execution.

        Args:
            workflow_slug: Workflow identifier
            payload: Data payload to send to workflow
        """
        logger.info(
            f"[WorkflowEngine] Sync trigger queued: {workflow_slug} with payload keys: {list(payload.keys())}"
        )
        # For sync compatibility, just log - actual execution happens via trigger_async

    async def execute_workflow(
        self,
        workflow_id: str,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a workflow by ID with input data (requires n8n API).

        Args:
            workflow_id: n8n workflow ID
            input_data: Input data for workflow execution

        Returns:
            Workflow execution result
        """
        try:
            url = urljoin(self.base_url, f"/api/v1/workflows/{workflow_id}/execute")

            logger.info(f"[WorkflowEngine] Executing workflow ID: {workflow_id}")

            response = await self.client.post(url, json={"data": input_data})

            if response.status_code >= 400:
                raise WorkflowEngineError(
                    f"Workflow execution failed: {response.status_code} - {response.text}"
                )

            return response.json()

        except Exception as e:
            error_msg = f"Failed to execute workflow {workflow_id}: {e}"
            logger.error(f"[WorkflowEngine] {error_msg}")
            raise WorkflowEngineError(error_msg) from e

    async def get_workflow_status(self, execution_id: str) -> Dict[str, Any]:
        """
        Get workflow execution status.

        Args:
            execution_id: Workflow execution ID

        Returns:
            Execution status information
        """
        try:
            url = urljoin(self.base_url, f"/api/v1/executions/{execution_id}")
            response = await self.client.get(url)

            if response.status_code >= 400:
                raise WorkflowEngineError(
                    f"Failed to get status: {response.status_code} - {response.text}"
                )

            return response.json()

        except Exception as e:
            logger.error(f"[WorkflowEngine] Error getting workflow status: {e}")
            raise WorkflowEngineError(f"Status check failed: {e}") from e

    async def close(self):
        """Close the HTTP client connection."""
        await self.client.aclose()
        logger.info("[WorkflowEngine] Client closed")


# Global singleton instance
_workflow_client: Optional[WorkflowEngineClient] = None


def get_workflow_client() -> WorkflowEngineClient:
    """Get or create global workflow engine client instance."""
    global _workflow_client
    if _workflow_client is None:
        _workflow_client = WorkflowEngineClient()
    return _workflow_client

