"""Utility helpers for interacting with the Prompt-Driven Automation API.

This module previously rendered a legacy dashboard. The revised version keeps the
public surface area available to extensions while exposing lightweight helper
methods that operate purely through HTTP requests. Callers can use the returned
payloads to build their own interface in any framework.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

import requests


class AutomationStudio:
    """High-level helper for managing prompt-driven automation workflows."""

    def __init__(self, api_base_url: str = "http://localhost:8000") -> None:
        self.api_base_url = api_base_url.rstrip("/")
        self.extension_api = f"{self.api_base_url}/api/extensions/prompt-driven-automation"

    # ------------------------------------------------------------------
    # Workflow lifecycle helpers
    # ------------------------------------------------------------------
    def list_workflows(self) -> List[Dict[str, Any]]:
        """Return the registered workflows."""
        response = requests.get(f"{self.extension_api}/workflows", timeout=10)
        response.raise_for_status()
        return response.json().get("workflows", [])

    def list_templates(self) -> List[Dict[str, Any]]:
        """Fetch available workflow templates."""
        response = requests.get(f"{self.extension_api}/templates", timeout=10)
        response.raise_for_status()
        return response.json().get("templates", [])

    def create_workflow(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Create a workflow using the automation API."""
        response = requests.post(
            f"{self.extension_api}/workflows",
            json=payload,
            timeout=10,
        )
        response.raise_for_status()
        return response.json()

    def execute_workflow(self, workflow_id: str, *, inputs: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a workflow and return the execution metadata."""
        response = requests.post(
            f"{self.extension_api}/workflows/{workflow_id}/execute",
            json={"inputs": inputs or {}},
            timeout=10,
        )
        response.raise_for_status()
        return response.json()

    # ------------------------------------------------------------------
    # Utility helpers
    # ------------------------------------------------------------------
    def export_workflow(self, workflow_id: str) -> str:
        """Download a workflow definition as a JSON string."""
        response = requests.get(
            f"{self.extension_api}/workflows/{workflow_id}",
            timeout=10,
        )
        response.raise_for_status()
        return json.dumps(response.json(), indent=2)

    def summarize(self) -> Dict[str, Any]:
        """Provide a quick summary of workflows, templates, and executions."""
        workflows = self.list_workflows()
        templates = []
        try:
            templates = self.list_templates()
        except requests.HTTPError:
            # Templates endpoint may be optional; ignore if unavailable.
            templates = []

        executions = []
        try:
            response = requests.get(f"{self.extension_api}/execution-history?limit=20", timeout=10)
            response.raise_for_status()
            executions = response.json().get("executions", [])
        except requests.HTTPError:
            executions = []

        return {
            "workflow_count": len(workflows),
            "template_count": len(templates),
            "recent_executions": executions,
            "workflows": workflows,
            "templates": templates,
        }

    def health_check(self) -> Dict[str, Any]:
        """Return health information exposed by the automation extension."""
        response = requests.get(f"{self.extension_api}/health", timeout=10)
        response.raise_for_status()
        return response.json()


__all__ = ["AutomationStudio"]
