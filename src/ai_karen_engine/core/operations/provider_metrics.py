"""
Provider Metrics and Observability Module.

This module provides structured metrics and observability for provider routing,
including vLLM, Transformers, and other LLM providers.

Metrics tracked:
- Provider selection outcomes
- Provider fallback transitions
- Provider health status changes
- Provider latency and performance
- Provider error rates
- Token usage by provider
"""

import logging
import time
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class ProviderEventType(Enum):
    """Types of provider events for metrics tracking."""
    REQUEST_RECEIVED = "provider_request_received"
    SELECTION_STARTED = "provider_selection_started"
    SELECTED = "provider_selected"
    HEALTH_CHECKED = "provider_health_checked"
    INVOCATION_STARTED = "provider_invocation_started"
    INVOCATION_COMPLETED = "provider_invocation_completed"
    INVOCATION_FAILED = "provider_invocation_failed"
    FALLBACK_TRIGGERED = "provider_fallback_triggered"
    GENERATION_STARTED = "provider_generation_started"
    GENERATION_COMPLETED = "provider_generation_completed"
    GENERATION_FAILED = "provider_generation_failed"
    STREAMING_STARTED = "provider_streaming_started"
    STREAMING_COMPLETED = "provider_streaming_completed"
    STREAMING_FAILED = "provider_streaming_failed"


class ProviderStatus(Enum):
    """Provider health status."""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"
    DISABLED = "disabled"


@dataclass
class ProviderMetrics:
    """Metrics collected for a single provider interaction."""
    provider_id: str
    event_type: ProviderEventType
    timestamp: float = field(default_factory=time.time)
    requested_provider: Optional[str] = None
    requested_model: Optional[str] = None
    actual_provider: Optional[str] = None
    actual_model: Optional[str] = None
    runtime_engine: Optional[str] = None
    response_source: Optional[str] = None
    fallback_level: Optional[int] = None
    degraded_mode: bool = False
    degradation_reason: Optional[str] = None
    latency_ms: Optional[float] = None
    success: bool = True
    error_type: Optional[str] = None
    error_code: Optional[str] = None
    token_usage: Optional[Dict[str, int]] = None
    correlation_id: Optional[str] = None
    request_id: Optional[str] = None
    user_id: Optional[str] = None
    tenant_id: Optional[str] = None
    session_id: Optional[str] = None
    conversation_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary for logging/exporting."""
        return {
            "event_type": self.event_type.value,
            "provider_id": self.provider_id,
            "timestamp": self.timestamp,
            "requested_provider": self.requested_provider,
            "requested_model": self.requested_model,
            "actual_provider": self.actual_provider,
            "actual_model": self.actual_model,
            "runtime_engine": self.runtime_engine,
            "response_source": self.response_source,
            "fallback_level": self.fallback_level,
            "degraded_mode": self.degraded_mode,
            "degradation_reason": self.degradation_reason,
            "latency_ms": self.latency_ms,
            "success": self.success,
            "error_type": self.error_type,
            "error_code": self.error_code,
            "token_usage": self.token_usage,
            "correlation_id": self.correlation_id,
            "request_id": self.request_id,
            "user_id": self.user_id,
            "tenant_id": self.tenant_id,
            "session_id": self.session_id,
            "conversation_id": self.conversation_id,
        }

    def to_prometheus_labels(self) -> Dict[str, str]:
        """Convert metrics to Prometheus label format."""
        return {
            "provider": self.provider_id,
            "runtime_engine": self.runtime_engine or "unknown",
            "success": "true" if self.success else "false",
            "event_type": self.event_type.value,
            "response_source": self.response_source or "unknown",
            "degraded_mode": "true" if self.degraded_mode else "false",
        }


class ProviderMetricsCollector:
    """Collector for provider metrics with structured logging and Prometheus integration."""

    def __init__(self):
        """Initialize the metrics collector."""
        self._metrics_manager = None
        self._counters = {}
        self._histograms = {}
        self._gauges = {}

        # Try to initialize Prometheus metrics
        try:
            from ai_karen_engine.core.operations.metrics_manager import MetricsManager
            self._metrics_manager = MetricsManager()
            self._initialize_prometheus_metrics()
            logger.info("Provider metrics initialized with Prometheus support")
        except Exception as e:
            logger.warning(f"Provider metrics initialized without Prometheus: {e}")

    def _initialize_prometheus_metrics(self):
        """Initialize Prometheus metrics for provider observability."""
        if not self._metrics_manager:
            return

        # Counter for provider selections
        self._counters["provider_selections"] = self._metrics_manager.register_counter(
            name="karen_provider_selections_total",
            description="Total number of provider selections",
            labels=["provider", "event_type", "runtime_engine", "success"]
        )

        # Counter for provider fallbacks
        self._counters["provider_fallbacks"] = self._metrics_manager.register_counter(
            name="karen_provider_fallbacks_total",
            description="Total number of provider fallbacks",
            labels=["from_provider", "to_provider", "reason", "fallback_level"]
        )

        # Counter for provider errors
        self._counters["provider_errors"] = self._metrics_manager.register_counter(
            name="karen_provider_errors_total",
            description="Total number of provider errors",
            labels=["provider", "error_type", "event_type", "runtime_engine"]
        )

        # Histogram for provider latency
        self._histograms["provider_latency_seconds"] = self._metrics_manager.register_histogram(
            name="karen_provider_latency_seconds",
            description="Provider latency in seconds",
            labels=["provider", "event_type", "runtime_engine", "success"],
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0]
        )

        # Histogram for token usage
        self._histograms["provider_tokens"] = self._metrics_manager.register_histogram(
            name="karen_provider_tokens_total",
            description="Total tokens used by provider",
            labels=["provider", "token_type"],  # token_type: prompt, completion, total
            buckets=[10, 50, 100, 500, 1000, 2000, 4000, 8000, 16000]
        )

        # Gauge for provider health
        self._gauges["provider_health"] = self._metrics_manager.register_gauge(
            name="karen_provider_health",
            description="Provider health status (1=healthy, 0=unhealthy)",
            labels=["provider", "runtime_engine"]
        )

        # Gauge for active requests
        self._gauges["provider_active_requests"] = self._metrics_manager.register_gauge(
            name="karen_provider_active_requests",
            description="Number of active requests per provider",
            labels=["provider", "runtime_engine"]
        )

    def record_event(self, metrics: ProviderMetrics):
        """
        Record a provider event with structured logging and Prometheus metrics.

        Args:
            metrics: ProviderMetrics object containing event details
        """
        # Log structured event
        log_level = logging.INFO if metrics.success else logging.WARNING
        logger.log(
            log_level,
            f"Provider event: {metrics.event_type.value}",
            extra={
                "provider_metrics": metrics.to_dict()
            }
        )

        # Update Prometheus metrics
        self._update_prometheus_metrics(metrics)

    def _update_prometheus_metrics(self, metrics: ProviderMetrics):
        """Update Prometheus metrics based on event type."""
        if not self._metrics_manager:
            return

        try:
            # Update selection counter
            if metrics.event_type in [
                ProviderEventType.SELECTED,
                ProviderEventType.FALLBACK_TRIGGERED,
            ]:
                if "provider_selections" in self._counters:
                    self._counters["provider_selections"].labels(
                        provider=metrics.provider_id,
                        event_type=metrics.event_type.value,
                        runtime_engine=metrics.runtime_engine or "unknown",
                        success=str(metrics.success).lower()
                    ).inc()

            # Update error counter
            if not metrics.success and metrics.event_type in [
                ProviderEventType.INVOCATION_FAILED,
                ProviderEventType.GENERATION_FAILED,
                ProviderEventType.STREAMING_FAILED,
            ]:
                if "provider_errors" in self._counters:
                    self._counters["provider_errors"].labels(
                        provider=metrics.provider_id,
                        error_type=metrics.error_type or "unknown",
                        event_type=metrics.event_type.value,
                        runtime_engine=metrics.runtime_engine or "unknown"
                    ).inc()

            # Update latency histogram
            if metrics.latency_ms is not None:
                if "provider_latency_seconds" in self._histograms:
                    self._histograms["provider_latency_seconds"].labels(
                        provider=metrics.provider_id,
                        event_type=metrics.event_type.value,
                        runtime_engine=metrics.runtime_engine or "unknown",
                        success=str(metrics.success).lower()
                    ).observe(metrics.latency_ms / 1000.0)

            # Update token usage histogram
            if metrics.token_usage:
                if "provider_tokens" in self._histograms:
                    for token_type, count in metrics.token_usage.items():
                        if count:
                            self._histograms["provider_tokens"].labels(
                                provider=metrics.provider_id,
                                token_type=token_type
                            ).observe(count)

            # Update health gauge
            if metrics.event_type == ProviderEventType.HEALTH_CHECKED:
                if "provider_health" in self._gauges:
                    health_value = 1.0 if metrics.success else 0.0
                    self._gauges["provider_health"].labels(
                        provider=metrics.provider_id,
                        runtime_engine=metrics.runtime_engine or "unknown"
                    ).set(health_value)

        except Exception as e:
            logger.error(f"Failed to update Prometheus metrics: {e}", exc_info=True)

    def record_fallback(
        self,
        from_provider: str,
        to_provider: str,
        reason: str,
        fallback_level: int,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Record a provider fallback transition.

        Args:
            from_provider: The provider that failed
            to_provider: The fallback provider
            reason: The reason for the fallback
            fallback_level: The fallback chain level
            metadata: Additional metadata about the fallback
        """
        logger.info(
            f"Provider fallback: {from_provider} → {to_provider}",
            extra={
                "from_provider": from_provider,
                "to_provider": to_provider,
                "reason": reason,
                "fallback_level": fallback_level,
                "metadata": metadata or {}
            }
        )

        # Update Prometheus fallback counter
        if self._metrics_manager and "provider_fallbacks" in self._counters:
            try:
                self._counters["provider_fallbacks"].labels(
                    from_provider=from_provider,
                    to_provider=to_provider,
                    reason=reason.replace(" ", "_"),
                    fallback_level=str(fallback_level)
                ).inc()
            except Exception as e:
                logger.error(f"Failed to update fallback counter: {e}")

    def record_provider_health(
        self,
        provider_id: str,
        is_healthy: bool,
        runtime_engine: Optional[str] = None,
        latency_ms: Optional[float] = None
    ):
        """
        Record provider health status.

        Args:
            provider_id: The provider identifier
            is_healthy: Whether the provider is healthy
            runtime_engine: The runtime engine type
            latency_ms: Health check latency in milliseconds
        """
        if self._metrics_manager and "provider_health" in self._gauges:
            try:
                self._gauges["provider_health"].labels(
                    provider=provider_id,
                    runtime_engine=runtime_engine or "unknown"
                ).set(1.0 if is_healthy else 0.0)
            except Exception as e:
                logger.error(f"Failed to update health gauge: {e}")

    def get_metrics_summary(self) -> Dict[str, Any]:
        """
        Get a summary of current metrics.

        Returns:
            Dictionary containing metrics summary
        """
        summary = {
            "prometheus_available": self._metrics_manager is not None,
            "counters": list(self._counters.keys()),
            "histograms": list(self._histograms.keys()),
            "gauges": list(self._gauges.keys()),
        }

        if self._metrics_manager:
            summary["registered_metrics"] = self._metrics_manager._registered_metrics

        return summary


# Global metrics collector instance
_metrics_collector: Optional[ProviderMetricsCollector] = None


def get_provider_metrics_collector() -> ProviderMetricsCollector:
    """Get the global provider metrics collector instance."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = ProviderMetricsCollector()
    return _metrics_collector


def record_provider_event(
    event_type: ProviderEventType,
    provider_id: str,
    **kwargs
) -> ProviderMetrics:
    """
    Convenience function to record a provider event.

    Args:
        event_type: The type of event
        provider_id: The provider identifier
        **kwargs: Additional metrics fields

    Returns:
        The recorded ProviderMetrics object
    """
    collector = get_provider_metrics_collector()
    metrics = ProviderMetrics(
        provider_id=provider_id,
        event_type=event_type,
        **kwargs
    )
    collector.record_event(metrics)
    return metrics


def record_provider_selection(
    provider_id: str,
    requested_provider: Optional[str] = None,
    actual_provider: Optional[str] = None,
    **kwargs
) -> ProviderMetrics:
    """
    Record a provider selection event.

    Args:
        provider_id: The provider identifier
        requested_provider: The provider requested by user
        actual_provider: The provider actually selected
        **kwargs: Additional metrics fields

    Returns:
        The recorded ProviderMetrics object
    """
    return record_provider_event(
        event_type=ProviderEventType.SELECTED,
        provider_id=provider_id,
        requested_provider=requested_provider,
        actual_provider=actual_provider,
        **kwargs
    )


def record_provider_fallback(
    from_provider: str,
    to_provider: str,
    reason: str,
    fallback_level: int,
    **kwargs
) -> None:
    """
    Record a provider fallback transition.

    Args:
        from_provider: The provider that failed
        to_provider: The fallback provider
        reason: The reason for the fallback
        fallback_level: The fallback chain level
        **kwargs: Additional metadata
    """
    collector = get_provider_metrics_collector()
    collector.record_fallback(
        from_provider=from_provider,
        to_provider=to_provider,
        reason=reason,
        fallback_level=fallback_level,
        metadata=kwargs
    )
