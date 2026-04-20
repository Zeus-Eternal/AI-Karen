"""
Runtime Telemetry Module

Provides telemetry and monitoring capabilities for AgentMedusa runtime.
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from collections import defaultdict, deque
import threading

from ..contracts.runtime_request import RuntimeRequest
from ..contracts.runtime_response import RuntimeResponse

logger = logging.getLogger(__name__)


@dataclass
class TelemetryMetric:
    """Telemetry metric data structure."""

    name: str
    value: float
    timestamp: float
    tags: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceSnapshot:
    """Performance snapshot of runtime state."""

    timestamp: float
    active_requests: int
    completed_requests: int
    failed_requests: int
    average_response_time: float
    memory_usage: float
    cpu_usage: float
    error_rate: float
    throughput: float


class RuntimeTelemetry:
    """Runtime telemetry and monitoring system."""

    def __init__(self, max_metrics: int = 10000):
        self.max_metrics = max_metrics
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_metrics))
        self.performance_data: Dict[str, List[PerformanceSnapshot]] = defaultdict(list)
        self._lock = threading.RLock()

        # Request tracking
        self.active_requests: Dict[str, RuntimeRequest] = {}
        self.completed_requests: Dict[str, RuntimeResponse] = {}
        self.request_start_times: Dict[str, float] = {}

        # Event handlers
        self._event_handlers: Dict[str, List[Callable]] = defaultdict(list)

        # Performance counters
        self.counters = {
            "requests_total": 0,
            "requests_success": 0,
            "requests_failed": 0,
            "errors_total": 0,
        }

    def record_metric(
        self,
        name: str,
        value: float,
        tags: Optional[Dict[str, str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record a telemetry metric."""
        with self._lock:
            metric = TelemetryMetric(
                name=name,
                value=value,
                timestamp=time.time(),
                tags=tags or {},
                metadata=metadata or {},
            )
            self.metrics[name].append(metric)

            # Emit metric event
            self._emit_event("metric", metric)

    def record_request_start(self, request_id: str, request: RuntimeRequest) -> None:
        """Record the start of a request."""
        with self._lock:
            self.active_requests[request_id] = request
            self.request_start_times[request_id] = time.time()
            self.counters["requests_total"] += 1

            # Record request metric
            self.record_metric(
                "requests.active", len(self.active_requests), {"type": "active"}
            )

    def record_request_complete(
        self, request_id: str, response: RuntimeResponse
    ) -> None:
        """Record the completion of a request."""
        with self._lock:
            if request_id in self.active_requests:
                # Calculate duration
                start_time = self.request_start_times.pop(request_id)
                duration = time.time() - start_time

                # Update counters
                if response.status == RuntimeStatus.SUCCESS:
                    self.counters["requests_success"] += 1
                else:
                    self.counters["requests_failed"] += 1

                # Store completed request
                self.completed_requests[request_id] = response

                # Remove from active requests
                del self.active_requests[request_id]

                # Record metrics
                self.record_metric(
                    "requests.duration", duration, {"status": response.status.value}
                )

                self.record_metric(
                    "requests.active", len(self.active_requests), {"type": "active"}
                )

                # Record performance snapshot
                self._record_performance_snapshot(duration)

                # Emit completion event
                self._emit_event(
                    "request_complete",
                    {
                        "request_id": request_id,
                        "response": response,
                        "duration": duration,
                    },
                )

    def record_error(
        self,
        error_type: str,
        error_message: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record an error occurrence."""
        with self._lock:
            self.counters["errors_total"] += 1

            self.record_metric("errors.total", 1, {"type": error_type})

            self.record_metric("errors." + error_type, 1)

            # Emit error event
            self._emit_event(
                "error",
                {
                    "type": error_type,
                    "message": error_message,
                    "context": context or {},
                },
            )

    def get_metrics(
        self,
        name: Optional[str] = None,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        tags: Optional[Dict[str, str]] = None,
    ) -> List[TelemetryMetric]:
        """Get metrics with optional filtering."""
        with self._lock:
            if name:
                metrics = list(self.metrics.get(name, []))
            else:
                # Return all metrics
                metrics = []
                for metric_queue in self.metrics.values():
                    metrics.extend(metric_queue)

            # Filter by time range
            if start_time or end_time:
                filtered = []
                for metric in metrics:
                    if start_time and metric.timestamp < start_time:
                        continue
                    if end_time and metric.timestamp > end_time:
                        continue
                    filtered.append(metric)
                metrics = filtered

            # Filter by tags
            if tags:
                filtered = []
                for metric in metrics:
                    match = True
                    for key, value in tags.items():
                        if key not in metric.tags or metric.tags[key] != value:
                            match = False
                            break
                    if match:
                        filtered.append(metric)
                metrics = filtered

            return metrics

    def get_performance_summary(
        self,
        time_window: float = 300.0,  # 5 minutes
    ) -> PerformanceSnapshot:
        """Get current performance summary."""
        with self._lock:
            current_time = time.time()
            start_time = current_time - time_window

            # Get recent performance data
            recent_snapshots = [
                snapshot
                for snapshot in self.performance_data.get("performance", [])
                if snapshot.timestamp >= start_time
            ]

            if not recent_snapshots:
                return PerformanceSnapshot(
                    timestamp=current_time,
                    active_requests=len(self.active_requests),
                    completed_requests=self.counters["requests_success"],
                    failed_requests=self.counters["requests_failed"],
                    average_response_time=0.0,
                    memory_usage=0.0,
                    cpu_usage=0.0,
                    error_rate=0.0,
                    throughput=0.0,
                )

            # Calculate aggregates
            total_requests = self.counters["requests_total"]
            completed_requests = self.counters["requests_success"]
            failed_requests = self.counters["requests_failed"]

            avg_response_time = sum(
                s.average_response_time for s in recent_snapshots
            ) / len(recent_snapshots)
            error_rate = (
                (failed_requests / total_requests * 100) if total_requests > 0 else 0.0
            )
            throughput = completed_requests / time_window if time_window > 0 else 0.0

            return PerformanceSnapshot(
                timestamp=current_time,
                active_requests=len(self.active_requests),
                completed_requests=completed_requests,
                failed_requests=failed_requests,
                average_response_time=avg_response_time,
                memory_usage=self._get_memory_usage(),
                cpu_usage=self._get_cpu_usage(),
                error_rate=error_rate,
                throughput=throughput,
            )

    def _record_performance_snapshot(self, duration: float) -> None:
        """Record a performance snapshot."""
        snapshot = PerformanceSnapshot(
            timestamp=time.time(),
            active_requests=len(self.active_requests),
            completed_requests=self.counters["requests_success"],
            failed_requests=self.counters["requests_failed"],
            average_response_time=duration,
            memory_usage=self._get_memory_usage(),
            cpu_usage=self._get_cpu_usage(),
            error_rate=(
                self.counters["requests_failed"] / self.counters["requests_total"] * 100
            )
            if self.counters["requests_total"] > 0
            else 0.0,
            throughput=self.counters["requests_success"]
            / (
                time.time()
                - (
                    self.request_start_times.get(
                        next(iter(self.request_start_times)), time.time()
                    )
                )
            ),
        )

        with self._lock:
            self.performance_data["performance"].append(snapshot)

            # Keep only recent snapshots
            if len(self.performance_data["performance"]) > 1000:
                self.performance_data["performance"] = self.performance_data[
                    "performance"
                ][-1000:]

    def _get_memory_usage(self) -> float:
        """Get current memory usage (placeholder)."""
        # This should be implemented with actual memory monitoring
        return 0.0

    def _get_cpu_usage(self) -> float:
        """Get current CPU usage (placeholder)."""
        # This should be implemented with actual CPU monitoring
        return 0.0

    def add_event_handler(self, event_type: str, handler: Callable) -> None:
        """Add an event handler for telemetry events."""
        self._event_handlers[event_type].append(handler)

    def remove_event_handler(self, event_type: str, handler: Callable) -> None:
        """Remove an event handler."""
        if event_type in self._event_handlers:
            try:
                self._event_handlers[event_type].remove(handler)
            except ValueError:
                pass

    def _emit_event(self, event_type: str, data: Any) -> None:
        """Emit a telemetry event."""
        for handler in self._event_handlers.get(event_type, []):
            try:
                if asyncio.iscoroutinefunction(handler):
                    asyncio.create_task(handler(data))
                else:
                    handler(data)
            except Exception as e:
                logger.error(f"Error in telemetry event handler: {e}")

    def get_health_status(self) -> Dict[str, Any]:
        """Get overall health status."""
        with self._lock:
            performance = self.get_performance_summary()

            return {
                "status": "healthy",
                "timestamp": performance.timestamp,
                "active_requests": performance.active_requests,
                "error_rate": performance.error_rate,
                "average_response_time": performance.average_response_time,
                "throughput": performance.throughput,
                "counters": self.counters.copy(),
                "metrics_count": sum(len(metrics) for metrics in self.metrics.values()),
            }


# Global telemetry instance
runtime_telemetry = RuntimeTelemetry()
