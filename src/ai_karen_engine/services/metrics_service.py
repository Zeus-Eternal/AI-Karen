"""AI-Karen metrics service.

Provides production-ready metrics for turn health, memory quality, and model
performance. Integrates with Prometheus when available while offering graceful
fallbacks so the service can operate without the optional dependency.
"""

import logging
import time
from collections import defaultdict, deque
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, Optional, Union

logger = logging.getLogger(__name__)

# Graceful imports with fallback mechanisms
if TYPE_CHECKING:  # pragma: no cover - type check only
    from prometheus_client import (
        CollectorRegistry,
        Counter,
        Gauge,
        Histogram,
        Info,
        Summary,
    )

try:
    from prometheus_client import (
        CONTENT_TYPE_LATEST,
        CollectorRegistry,
        Counter,
        Gauge,
        Histogram,
        Info,
        Summary,
        generate_latest,
    )

    PROMETHEUS_AVAILABLE = True
except Exception:  # pragma: no cover - optional dependency
    logger.warning("Prometheus client not available, using fallback metrics")
    # Define lightweight fallbacks to avoid import-time NameError when
    # Prometheus isn't installed. These stubs satisfy type annotations and
    # allow the service to operate in a degraded mode without the optional
    # dependency.
    CollectorRegistry = Any  # type: ignore[assignment]
    Counter = Histogram = Gauge = Summary = Info = None  # type: ignore[assignment]

    def generate_latest(*_args, **_kwargs) -> bytes:  # type: ignore[override]
        return b""

    CONTENT_TYPE_LATEST = "text/plain; charset=utf-8"
    PROMETHEUS_AVAILABLE = False


@dataclass
class MetricValue:
    """Individual metric value with metadata"""

    value: Union[int, float]
    timestamp: datetime
    labels: Dict[str, str] = field(default_factory=dict)
    correlation_id: Optional[str] = None


@dataclass
class MemoryQualityMetrics:
    """Memory quality tracking metrics"""

    context_usage_rate: float = 0.0
    ignored_top_hit_rate: float = 0.0
    used_shard_rate: float = 0.0
    avg_relevance_score: float = 0.0
    total_queries: int = 0
    total_hits: int = 0


class FallbackMetricsCollector:
    """Fallback metrics collector when Prometheus is not available"""

    def __init__(self):
        self.counters = defaultdict(int)
        self.histograms = defaultdict(list)
        self.gauges = defaultdict(float)
        self.memory_quality = MemoryQualityMetrics()
        self.recent_values = defaultdict(lambda: deque(maxlen=1000))

    def inc_counter(self, name: str, labels: Dict[str, str] = None, value: float = 1):
        """Increment counter metric"""
        key = f"{name}_{self._labels_to_key(labels or {})}"
        self.counters[key] += value
        self.recent_values[name].append(
            MetricValue(value=value, timestamp=datetime.utcnow(), labels=labels or {})
        )

    def observe_histogram(self, name: str, value: float, labels: Dict[str, str] = None):
        """Observe histogram metric"""
        key = f"{name}_{self._labels_to_key(labels or {})}"
        self.histograms[key].append(value)
        self.recent_values[name].append(
            MetricValue(value=value, timestamp=datetime.utcnow(), labels=labels or {})
        )

    def set_gauge(self, name: str, value: float, labels: Dict[str, str] = None):
        """Set gauge metric"""
        key = f"{name}_{self._labels_to_key(labels or {})}"
        self.gauges[key] = value
        self.recent_values[name].append(
            MetricValue(value=value, timestamp=datetime.utcnow(), labels=labels or {})
        )

    def update_memory_quality(self, **kwargs):
        """Update memory quality metrics"""
        for key, value in kwargs.items():
            if hasattr(self.memory_quality, key):
                setattr(self.memory_quality, key, value)

    def get_stats(self) -> Dict[str, Any]:
        """Get current metrics statistics"""
        return {
            "counters": dict(self.counters),
            "histograms": {
                k: {
                    "count": len(v),
                    "sum": sum(v),
                    "avg": sum(v) / len(v) if v else 0,
                    "min": min(v) if v else 0,
                    "max": max(v) if v else 0,
                    "p95": sorted(v)[int(len(v) * 0.95)] if v else 0,
                }
                for k, v in self.histograms.items()
            },
            "gauges": dict(self.gauges),
            "memory_quality": self.memory_quality.__dict__,
        }

    def _labels_to_key(self, labels: Dict[str, str]) -> str:
        """Convert labels dict to string key"""
        return "_".join(f"{k}={v}" for k, v in sorted(labels.items()))


class MetricsService:
    """Comprehensive metrics collection service"""

    def __init__(self, registry: Optional[CollectorRegistry] = None):
        self.registry = registry
        self.fallback_collector = FallbackMetricsCollector()
        self.slo_monitor = None  # Will be set by SLO monitor integration

        if PROMETHEUS_AVAILABLE:
            self._init_prometheus_metrics()
        else:
            logger.info("Using fallback metrics collector")

    def _init_prometheus_metrics(self):
        """Initialize Prometheus metrics"""
        # Request counters with proper labeling
        self.copilot_requests = Counter(
            "copilot_requests_total",
            "Total copilot requests",
            ["status", "user_id", "org_id"],
            registry=self.registry,
        )

        self.memory_queries = Counter(
            "memory_queries_total",
            "Total memory queries",
            ["operation", "status", "user_id", "org_id"],
            registry=self.registry,
        )

        self.memory_commits = Counter(
            "memory_commits_total",
            "Total memory commits",
            ["status", "decay_tier", "user_id", "org_id"],
            registry=self.registry,
        )

        # Timing metrics for latency tracking
        self.llm_latency = Histogram(
            "llm_latency_seconds",
            "LLM generation latency",
            ["provider", "model", "status"],
            registry=self.registry,
            buckets=[0.1, 0.25, 0.5, 1.0, 1.2, 2.0, 5.0, 10.0],
        )

        self.vec_latency = Histogram(
            "vector_latency_seconds",
            "Vector search latency",
            ["operation", "status"],
            registry=self.registry,
            buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
        )

        self.total_turn_time = Histogram(
            "total_turn_time_seconds",
            "Total turn processing time",
            ["endpoint", "status"],
            registry=self.registry,
            buckets=[0.5, 1.0, 2.0, 3.0, 5.0, 10.0, 30.0],
        )

        # Memory quality metrics
        self.context_usage_rate = Gauge(
            "memory_context_usage_rate",
            "Rate of context usage in responses",
            ["user_id", "org_id"],
            registry=self.registry,
        )

        self.ignored_top_hit_rate = Gauge(
            "memory_ignored_top_hit_rate",
            "Rate of ignored top hits",
            ["user_id", "org_id"],
            registry=self.registry,
        )

        self.used_shard_rate = Gauge(
            "memory_used_shard_rate",
            "Rate of used memory shards",
            ["user_id", "org_id"],
            registry=self.registry,
        )

        self.avg_relevance_score = Gauge(
            "memory_avg_relevance_score",
            "Average relevance score of retrieved memories",
            ["user_id", "org_id"],
            registry=self.registry,
        )

        # Model performance metrics
        self.model_performance = Summary(
            "model_performance_score",
            "Model performance score",
            ["model", "task_type"],
            registry=self.registry,
        )

        # System health metrics
        self.active_connections = Gauge(
            "active_connections_total",
            "Number of active connections",
            ["service"],
            registry=self.registry,
        )

        self.memory_usage = Gauge(
            "memory_usage_bytes",
            "Memory usage in bytes",
            ["service", "type"],
            registry=self.registry,
        )

        # Turn health metrics
        self.turn_success_rate = Gauge(
            "turn_success_rate",
            "Success rate of turns",
            ["endpoint", "time_window"],
            registry=self.registry,
        )

        self.turn_error_rate = Gauge(
            "turn_error_rate",
            "Error rate of turns",
            ["endpoint", "error_type", "time_window"],
            registry=self.registry,
        )

    def record_copilot_request(
        self,
        status: str,
        user_id: str = "",
        org_id: str = "",
        correlation_id: Optional[str] = None,
    ):
        """Record copilot request metrics"""
        labels = {"status": status, "user_id": user_id, "org_id": org_id}

        if PROMETHEUS_AVAILABLE:
            self.copilot_requests.labels(**labels).inc()
        else:
            self.fallback_collector.inc_counter("copilot_requests_total", labels)

        # Record for SLO monitoring
        self._record_for_slo_monitoring("requests_" + status, 1)

        logger.debug(
            f"Recorded copilot request: {labels}",
            extra={"correlation_id": correlation_id, "metric_type": "counter"},
        )

    def record_memory_query(
        self,
        operation: str,
        status: str,
        user_id: str = "",
        org_id: str = "",
        correlation_id: Optional[str] = None,
    ):
        """Record memory query metrics"""
        labels = {
            "operation": operation,
            "status": status,
            "user_id": user_id,
            "org_id": org_id,
        }

        if PROMETHEUS_AVAILABLE:
            self.memory_queries.labels(**labels).inc()
        else:
            self.fallback_collector.inc_counter("memory_queries_total", labels)

        logger.debug(
            f"Recorded memory query: {labels}",
            extra={"correlation_id": correlation_id, "metric_type": "counter"},
        )

    def record_memory_commit(
        self,
        status: str,
        decay_tier: str = "",
        user_id: str = "",
        org_id: str = "",
        correlation_id: Optional[str] = None,
    ):
        """Record memory commit metrics"""
        labels = {
            "status": status,
            "decay_tier": decay_tier,
            "user_id": user_id,
            "org_id": org_id,
        }

        if PROMETHEUS_AVAILABLE:
            self.memory_commits.labels(**labels).inc()
        else:
            self.fallback_collector.inc_counter("memory_commits_total", labels)

        logger.debug(
            f"Recorded memory commit: {labels}",
            extra={"correlation_id": correlation_id, "metric_type": "counter"},
        )

    def record_llm_latency(
        self,
        duration: float,
        provider: str = "",
        model: str = "",
        status: str = "success",
        correlation_id: Optional[str] = None,
    ):
        """Record LLM generation latency"""
        labels = {"provider": provider, "model": model, "status": status}

        if PROMETHEUS_AVAILABLE:
            self.llm_latency.labels(**labels).observe(duration)
        else:
            self.fallback_collector.observe_histogram(
                "llm_latency_seconds", duration, labels
            )

        # Record for SLO monitoring
        self._record_for_slo_monitoring("llm_latency_seconds", duration)

        logger.debug(
            f"Recorded LLM latency: {duration:.3f}s {labels}",
            extra={"correlation_id": correlation_id, "metric_type": "histogram"},
        )

    def record_vector_latency(
        self,
        duration: float,
        operation: str = "search",
        status: str = "success",
        correlation_id: Optional[str] = None,
    ):
        """Record vector search latency"""
        labels = {"operation": operation, "status": status}

        if PROMETHEUS_AVAILABLE:
            self.vec_latency.labels(**labels).observe(duration)
        else:
            self.fallback_collector.observe_histogram(
                "vector_latency_seconds", duration, labels
            )

        # Record for SLO monitoring
        self._record_for_slo_monitoring("vector_latency_seconds", duration)

        logger.debug(
            f"Recorded vector latency: {duration:.3f}s {labels}",
            extra={"correlation_id": correlation_id, "metric_type": "histogram"},
        )

    def record_total_turn_time(
        self,
        duration: float,
        endpoint: str,
        status: str = "success",
        correlation_id: Optional[str] = None,
    ):
        """Record total turn processing time"""
        labels = {"endpoint": endpoint, "status": status}

        if PROMETHEUS_AVAILABLE:
            self.total_turn_time.labels(**labels).observe(duration)
        else:
            self.fallback_collector.observe_histogram(
                "total_turn_time_seconds", duration, labels
            )

        # Record for SLO monitoring
        self._record_for_slo_monitoring("total_turn_time_seconds", duration)

        logger.debug(
            f"Recorded total turn time: {duration:.3f}s {labels}",
            extra={"correlation_id": correlation_id, "metric_type": "histogram"},
        )

    def update_memory_quality_metrics(
        self,
        context_usage_rate: Optional[float] = None,
        ignored_top_hit_rate: Optional[float] = None,
        used_shard_rate: Optional[float] = None,
        avg_relevance_score: Optional[float] = None,
        user_id: str = "",
        org_id: str = "",
        correlation_id: Optional[str] = None,
    ):
        """Update memory quality metrics"""
        labels = {"user_id": user_id, "org_id": org_id}

        if PROMETHEUS_AVAILABLE:
            if context_usage_rate is not None:
                self.context_usage_rate.labels(**labels).set(context_usage_rate)
            if ignored_top_hit_rate is not None:
                self.ignored_top_hit_rate.labels(**labels).set(ignored_top_hit_rate)
            if used_shard_rate is not None:
                self.used_shard_rate.labels(**labels).set(used_shard_rate)
            if avg_relevance_score is not None:
                self.avg_relevance_score.labels(**labels).set(avg_relevance_score)
        else:
            updates = {}
            if context_usage_rate is not None:
                updates["context_usage_rate"] = context_usage_rate
                self.fallback_collector.set_gauge(
                    "memory_context_usage_rate", context_usage_rate, labels
                )
            if ignored_top_hit_rate is not None:
                updates["ignored_top_hit_rate"] = ignored_top_hit_rate
                self.fallback_collector.set_gauge(
                    "memory_ignored_top_hit_rate", ignored_top_hit_rate, labels
                )
            if used_shard_rate is not None:
                updates["used_shard_rate"] = used_shard_rate
                self.fallback_collector.set_gauge(
                    "memory_used_shard_rate", used_shard_rate, labels
                )
            if avg_relevance_score is not None:
                updates["avg_relevance_score"] = avg_relevance_score
                self.fallback_collector.set_gauge(
                    "memory_avg_relevance_score", avg_relevance_score, labels
                )

            self.fallback_collector.update_memory_quality(**updates)

        logger.debug(
            f"Updated memory quality metrics: {labels}",
            extra={"correlation_id": correlation_id, "metric_type": "gauge"},
        )

    def record_model_performance(
        self,
        score: float,
        model: str,
        task_type: str,
        correlation_id: Optional[str] = None,
    ):
        """Record model performance score"""
        labels = {"model": model, "task_type": task_type}

        if PROMETHEUS_AVAILABLE:
            self.model_performance.labels(**labels).observe(score)
        else:
            self.fallback_collector.observe_histogram(
                "model_performance_score", score, labels
            )

        logger.debug(
            f"Recorded model performance: {score:.3f} {labels}",
            extra={"correlation_id": correlation_id, "metric_type": "summary"},
        )

    def update_system_health(
        self,
        active_connections: Optional[int] = None,
        memory_usage: Optional[int] = None,
        service: str = "api",
        memory_type: str = "heap",
        correlation_id: Optional[str] = None,
    ):
        """Update system health metrics"""
        if PROMETHEUS_AVAILABLE:
            if active_connections is not None:
                self.active_connections.labels(service=service).set(active_connections)
            if memory_usage is not None:
                self.memory_usage.labels(service=service, type=memory_type).set(
                    memory_usage
                )
        else:
            if active_connections is not None:
                self.fallback_collector.set_gauge(
                    "active_connections_total", active_connections, {"service": service}
                )
            if memory_usage is not None:
                self.fallback_collector.set_gauge(
                    "memory_usage_bytes",
                    memory_usage,
                    {"service": service, "type": memory_type},
                )

        logger.debug(
            f"Updated system health: service={service}",
            extra={"correlation_id": correlation_id, "metric_type": "gauge"},
        )

    def update_turn_health(
        self,
        success_rate: Optional[float] = None,
        error_rate: Optional[float] = None,
        endpoint: str = "",
        error_type: str = "",
        time_window: str = "5m",
        correlation_id: Optional[str] = None,
    ):
        """Update turn health metrics"""
        if PROMETHEUS_AVAILABLE:
            if success_rate is not None:
                self.turn_success_rate.labels(
                    endpoint=endpoint, time_window=time_window
                ).set(success_rate)
            if error_rate is not None:
                self.turn_error_rate.labels(
                    endpoint=endpoint, error_type=error_type, time_window=time_window
                ).set(error_rate)
        else:
            if success_rate is not None:
                self.fallback_collector.set_gauge(
                    "turn_success_rate",
                    success_rate,
                    {"endpoint": endpoint, "time_window": time_window},
                )
            if error_rate is not None:
                self.fallback_collector.set_gauge(
                    "turn_error_rate",
                    error_rate,
                    {
                        "endpoint": endpoint,
                        "error_type": error_type,
                        "time_window": time_window,
                    },
                )

        logger.debug(
            f"Updated turn health: endpoint={endpoint}",
            extra={"correlation_id": correlation_id, "metric_type": "gauge"},
        )

    def _record_for_slo_monitoring(self, metric_name: str, value: float):
        """Record metric for SLO monitoring"""
        if self.slo_monitor:
            try:
                self.slo_monitor.record_metric(metric_name, value)
            except Exception as e:
                logger.warning(f"Failed to record SLO metric {metric_name}: {e}")

    def set_slo_monitor(self, slo_monitor):
        """Set SLO monitor for integration"""
        self.slo_monitor = slo_monitor

    @contextmanager
    def time_operation(
        self,
        operation_name: str,
        labels: Dict[str, str] = None,
        correlation_id: Optional[str] = None,
    ):
        """Context manager for timing operations"""
        start_time = time.time()
        labels = labels or {}

        try:
            yield
            duration = time.time() - start_time

            # Record based on operation type
            if "llm" in operation_name.lower():
                self.record_llm_latency(
                    duration, correlation_id=correlation_id, **labels
                )
            elif (
                "vector" in operation_name.lower() or "search" in operation_name.lower()
            ):
                self.record_vector_latency(
                    duration, correlation_id=correlation_id, **labels
                )
            elif "turn" in operation_name.lower():
                self.record_total_turn_time(
                    duration, correlation_id=correlation_id, **labels
                )

        except Exception:
            duration = time.time() - start_time
            labels["status"] = "error"

            if "llm" in operation_name.lower():
                self.record_llm_latency(
                    duration, correlation_id=correlation_id, **labels
                )
            elif (
                "vector" in operation_name.lower() or "search" in operation_name.lower()
            ):
                self.record_vector_latency(
                    duration, correlation_id=correlation_id, **labels
                )
            elif "turn" in operation_name.lower():
                self.record_total_turn_time(
                    duration, correlation_id=correlation_id, **labels
                )

            raise

    def get_metrics_export(self) -> str:
        """Export metrics in Prometheus format"""
        if PROMETHEUS_AVAILABLE and self.registry:
            return generate_latest(self.registry)
        else:
            # Return fallback metrics in simple text format
            stats = self.fallback_collector.get_stats()
            lines = []

            # Export counters
            for name, value in stats["counters"].items():
                lines.append(f"# TYPE {name} counter")
                lines.append(f"{name} {value}")

            # Export histograms
            for name, hist_stats in stats["histograms"].items():
                lines.append(f"# TYPE {name} histogram")
                for stat_name, stat_value in hist_stats.items():
                    lines.append(f"{name}_{stat_name} {stat_value}")

            # Export gauges
            for name, value in stats["gauges"].items():
                lines.append(f"# TYPE {name} gauge")
                lines.append(f"{name} {value}")

            return "\n".join(lines)

    def get_content_type(self) -> str:
        """Get content type for metrics export"""
        if PROMETHEUS_AVAILABLE:
            return CONTENT_TYPE_LATEST
        else:
            return "text/plain; charset=utf-8"

    def get_stats_summary(self) -> Dict[str, Any]:
        """Get comprehensive metrics summary"""
        if PROMETHEUS_AVAILABLE:
            # For Prometheus, we'd need to query the registry
            # For now, return basic info
            return {
                "metrics_backend": "prometheus",
                "registry_available": True,
                "timestamp": datetime.utcnow().isoformat(),
            }
        else:
            stats = self.fallback_collector.get_stats()
            stats["metrics_backend"] = "fallback"
            stats["timestamp"] = datetime.utcnow().isoformat()
            return stats


# Global metrics service instance
_metrics_service: Optional[MetricsService] = None


def get_metrics_service() -> MetricsService:
    """Get global metrics service instance"""
    global _metrics_service
    if _metrics_service is None:
        _metrics_service = MetricsService()
    return _metrics_service


def init_metrics_service(
    registry: Optional[CollectorRegistry] = None,
) -> MetricsService:
    """Initialize global metrics service with custom registry"""
    global _metrics_service
    _metrics_service = MetricsService(registry)
    return _metrics_service


# Export main classes and functions
__all__ = [
    "MetricsService",
    "MetricValue",
    "MemoryQualityMetrics",
    "FallbackMetricsCollector",
    "get_metrics_service",
    "init_metrics_service",
]
