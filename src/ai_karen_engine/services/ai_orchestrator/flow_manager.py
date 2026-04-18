"""Flow manager compatibility module."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Dict


class FlowRegistrationError(Exception):
    """Raised when a flow cannot be registered."""


class FlowExecutionError(Exception):
    """Raised when a flow execution fails."""


@dataclass
class FlowStats:
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    average_duration: float = 0.0
    last_execution: float | None = None


class FlowManager:
    """Minimal flow manager used for legacy compatibility and tests."""

    def __init__(self) -> None:
        self._flows: Dict[Any, Callable[[Any], Awaitable[Any]]] = {}
        self._flow_metadata: Dict[Any, Dict[str, Any]] = {}
        self._execution_stats: Dict[Any, Dict[str, Any]] = {}

    def register_flow(self, flow_type: Any, handler: Callable[[Any], Awaitable[Any]], metadata: Dict[str, Any] | None = None) -> None:
        if flow_type in self._flows:
            raise FlowRegistrationError(f"Flow already registered: {flow_type}")
        self._flows[flow_type] = handler
        self._flow_metadata[flow_type] = metadata or {}
        self._execution_stats.setdefault(flow_type, {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "average_duration": 0.0,
            "last_execution": None,
        })

    async def execute_flow(self, flow_type: Any, input_data: Any) -> Any:
        import time

        if flow_type not in self._flows:
            raise FlowExecutionError(f"Flow not registered: {flow_type}")

        start = time.time()
        stats = self._execution_stats.setdefault(flow_type, {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "average_duration": 0.0,
            "last_execution": None,
        })
        stats["total_executions"] += 1
        try:
            result = await self._flows[flow_type](input_data)
            stats["successful_executions"] += 1
            return result
        except Exception as exc:
            stats["failed_executions"] += 1
            raise FlowExecutionError(str(exc)) from exc
        finally:
            duration = time.time() - start
            n = stats["total_executions"]
            stats["average_duration"] = ((stats["average_duration"] * (n - 1)) + duration) / max(n, 1)
            stats["last_execution"] = time.time()

    def get_available_flows(self) -> list[Any]:
        return list(self._flows.keys())

    def get_flow_stats(self, flow_type: Any) -> Dict[str, Any]:
        return self._execution_stats.get(flow_type, {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "average_duration": 0.0,
            "last_execution": None,
        })


__all__ = ["FlowManager", "FlowRegistrationError", "FlowExecutionError", "FlowStats"]
