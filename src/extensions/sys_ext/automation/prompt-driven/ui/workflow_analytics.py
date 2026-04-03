"""Data aggregation utilities for prompt-driven workflow analytics.

The original implementation provided an in-browser dashboard. This refactor keeps
core analytical helpers so that callers can build visualisations in any
frontend without a hard dependency on a specific UI framework.
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta
from typing import Any, Dict, Iterable, List, Optional

import requests


class WorkflowAnalytics:
    """Collect and transform workflow analytics data from the automation API."""

    def __init__(self, api_base_url: str = "http://localhost:8000") -> None:
        self.api_base_url = api_base_url.rstrip("/")
        self.extension_api = f"{self.api_base_url}/api/extensions/prompt-driven-automation"

    def fetch(self) -> Dict[str, Any]:
        """Return raw analytics payloads from the automation service."""
        workflows: List[Dict[str, Any]] = []
        executions: List[Dict[str, Any]] = []
        metrics: Dict[str, Any] = {}

        workflows = self._safe_get("/workflows").get("workflows", [])
        executions = self._safe_get("/execution-history?limit=1000").get("executions", [])
        metrics = self._safe_get("/metrics")

        return {
            "workflows": workflows,
            "executions": executions,
            "metrics": metrics,
        }

    def summarize(self, *, time_range: Optional[str] = None) -> Dict[str, Any]:
        """Provide aggregated analytics suitable for any presentation layer."""
        payload = self.fetch()
        executions = payload["executions"]
        workflows = payload["workflows"]

        filtered = self._apply_time_filter(executions, time_range)

        return {
            "workflow_totals": self._workflow_totals(workflows),
            "execution_stats": self._execution_stats(filtered),
            "recent_executions": filtered[:20],
            "time_range": time_range or "all",
            "raw_metrics": payload["metrics"],
        }

    def _safe_get(self, path: str) -> Dict[str, Any]:
        """Perform a GET request and return an empty payload on failure."""
        try:
            response = requests.get(f"{self.extension_api}{path}", timeout=10)
            response.raise_for_status()
            data = response.json()
            if isinstance(data, dict):
                return data
        except requests.RequestException:
            pass
        return {}

    def _apply_time_filter(self, executions: Iterable[Dict[str, Any]], time_range: Optional[str]) -> List[Dict[str, Any]]:
        if not time_range or time_range.lower() == "all":
            return list(executions)

        now = datetime.utcnow()
        mapping = {
            "24h": now - timedelta(hours=24),
            "7d": now - timedelta(days=7),
            "30d": now - timedelta(days=30),
        }
        cutoff = mapping.get(time_range.lower())
        if cutoff is None:
            return list(executions)

        filtered: List[Dict[str, Any]] = []
        for record in executions:
            start_time = record.get("start_time")
            if not start_time:
                continue
            try:
                started = datetime.fromisoformat(str(start_time).replace("Z", "+00:00"))
            except ValueError:
                continue
            if started >= cutoff:
                filtered.append(record)
        return filtered

    def _workflow_totals(self, workflows: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
        total = 0
        tags: Counter[str] = Counter()
        for workflow in workflows:
            total += 1
            tags.update(workflow.get("tags", []))
        return {"count": total, "top_tags": tags.most_common(10)}

    def _execution_stats(self, executions: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
        total = 0
        success = 0
        failure = 0
        durations: List[float] = []

        for execution in executions:
            total += 1
            status = str(execution.get("status", "")).lower()
            if status == "success":
                success += 1
            elif status == "failed":
                failure += 1

            duration = execution.get("duration_seconds")
            if isinstance(duration, (int, float)):
                durations.append(float(duration))

        average_duration = sum(durations) / len(durations) if durations else 0.0
        max_duration = max(durations) if durations else 0.0
        min_duration = min(durations) if durations else 0.0

        return {
            "total": total,
            "success": success,
            "failed": failure,
            "success_rate": (success / total) * 100 if total else 0.0,
            "average_duration": average_duration,
            "max_duration": max_duration,
            "min_duration": min_duration,
        }


__all__ = ["WorkflowAnalytics"]
