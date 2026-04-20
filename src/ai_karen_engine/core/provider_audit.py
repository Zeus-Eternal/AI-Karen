"""
Provider Audit System

This module provides comprehensive audit trails for all provider interactions:
- Complete audit trail for all provider interactions
- Performance metrics tracking
- Failure pattern analysis
- Compliance logging
- Security monitoring
"""

import asyncio
import logging
import time
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pathlib import Path

from ..config.config_manager import get_config_manager
from ..core.logging.logger import get_structured_logger
from ..core.metrics_manager import get_metrics_manager

logger = logging.getLogger(__name__)


class AuditEventType(str, Enum):
    """Provider audit event types"""

    PROVIDER_SELECTED = "provider_selected"
    REQUEST_SENT = "request_sent"
    RESPONSE_RECEIVED = "response_received"
    ERROR_OCCURRED = "error_occurred"
    CIRCUIT_BREAKER_OPENED = "circuit_breaker_opened"
    CIRCUIT_BREAKER_CLOSED = "circuit_breaker_closed"
    AUTHENTICATION_CHECK = "authentication_check"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    FALLBACK_ACTIVATED = "fallback_activated"
    HEALTH_CHECK = "health_check"


class AuditEventSeverity(str, Enum):
    """Audit event severity levels"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AuditEventStatus(str, Enum):
    """Audit event status"""

    SUCCESS = "success"
    FAILURE = "failure"
    TIMEOUT = "timeout"
    PENDING = "pending"


@dataclass
class ProviderAuditEvent:
    """Provider audit event data structure"""

    event_id: str
    timestamp: datetime
    event_type: AuditEventType
    provider_name: str
    request_id: Optional[str] = None
    conversation_id: Optional[str] = None
    user_id: Optional[str] = None
    severity: AuditEventSeverity = AuditEventSeverity.LOW
    status: AuditEventStatus = AuditEventStatus.PENDING
    duration_ms: Optional[float] = None
    request_data: Optional[Dict[str, Any]] = None
    response_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    error_type: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert audit event to dictionary"""
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type.value,
            "provider_name": self.provider_name,
            "request_id": self.request_id,
            "conversation_id": self.conversation_id,
            "user_id": self.user_id,
            "severity": self.severity.value,
            "status": self.status.value,
            "duration_ms": self.duration_ms,
            "request_data": self.request_data,
            "response_data": self.response_data,
            "error_message": self.error_message,
            "error_type": self.error_type,
            "metadata": self.metadata,
        }


@dataclass
class ProviderPerformanceMetrics:
    """Provider performance metrics"""

    provider_name: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    timeout_requests: int = 0
    average_response_time_ms: float = 0.0
    p95_response_time_ms: float = 0.0
    p99_response_time_ms: float = 0.0
    error_rate: float = 0.0
    circuit_breaker_trips: int = 0
    fallback_activations: int = 0
    last_updated: datetime = field(default_factory=datetime.utcnow)

    def update_with_event(self, event: ProviderAuditEvent):
        """Update metrics with audit event"""
        self.total_requests += 1
        self.last_updated = datetime.utcnow()

        if event.status == AuditEventStatus.SUCCESS:
            self.successful_requests += 1
        elif event.status == AuditEventStatus.FAILURE:
            self.failed_requests += 1
        elif event.status == AuditEventStatus.TIMEOUT:
            self.timeout_requests += 1

        if event.duration_ms is not None:
            # Update average response time
            current_avg = self.average_response_time_ms
            self.average_response_time_ms = (
                current_avg * (self.total_requests - 1) + event.duration_ms
            ) / self.total_requests

        # Update error rate
        self.error_rate = (
            (self.failed_requests + self.timeout_requests) / self.total_requests
            if self.total_requests > 0
            else 0.0
        )


class ProviderAuditSystem:
    """Comprehensive provider audit system"""

    def __init__(self, max_events: int = 10000, max_metrics_history: int = 1000):
        self.max_events = max_events
        self.max_metrics_history = max_metrics_history

        # Audit storage
        self._audit_events: List[ProviderAuditEvent] = []
        self._provider_metrics: Dict[str, ProviderPerformanceMetrics] = {}

        # Configuration
        self._structured_logger = get_structured_logger()
        self._metrics_manager = get_metrics_manager()
        self._config_manager = get_config_manager()

        # Background tasks
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running = False

        # Event filters
        self._event_filters: Dict[str, Any] = {}

        # Performance tracking
        self._performance_history: List[Dict[str, Any]] = []

    async def initialize(self):
        """Initialize the audit system"""
        if self._running:
            return

        self._running = True

        # Start background cleanup
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())

        logger.info("Provider Audit System initialized")

    async def shutdown(self):
        """Shutdown the audit system"""
        self._running = False

        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        logger.info("Provider Audit System shutdown completed")

    def record_event(self, event: ProviderAuditEvent):
        """Record a provider audit event"""
        try:
            # Apply filters if configured
            if not self._should_record_event(event):
                return

            # Store event
            self._audit_events.append(event)

            # Update provider metrics
            if event.provider_name not in self._provider_metrics:
                self._provider_metrics[event.provider_name] = (
                    ProviderPerformanceMetrics(provider_name=event.provider_name)
                )

            self._provider_metrics[event.provider_name].update_with_event(event)

            # Log structured event
            self._structured_logger.log_event(
                event=f"provider_audit_{event.event_type.value}",
                details=event.to_dict(),
            )

            # Record metrics
            self._record_metrics(event)

            # Enforce size limits
            if len(self._audit_events) > self.max_events:
                self._audit_events = self._audit_events[-self.max_events :]

            if len(self._provider_metrics) > self.max_metrics_history:
                # Keep only providers with recent activity
                cutoff_time = datetime.utcnow() - timedelta(hours=24)
                active_providers = {
                    name: metrics
                    for name, metrics in self._provider_metrics.items()
                    if metrics.last_updated > cutoff_time
                }
                self._provider_metrics = active_providers

        except Exception as e:
            logger.error(f"Error recording audit event: {e}")

    def _should_record_event(self, event: ProviderAuditEvent) -> bool:
        """Check if event should be recorded based on filters"""
        try:
            # Check provider filter
            if "providers" in self._event_filters:
                if event.provider_name not in self._event_filters["providers"]:
                    return False

            # Check event type filter
            if "event_types" in self._event_filters:
                if event.event_type.value not in self._event_filters["event_types"]:
                    return False

            # Check severity filter
            if "severities" in self._event_filters:
                if event.severity.value not in self._event_filters["severities"]:
                    return False

            # Check time range filter
            if "time_range" in self._event_filters:
                time_range = self._event_filters["time_range"]
                start_time = datetime.fromisoformat(time_range["start"])
                end_time = datetime.fromisoformat(time_range["end"])
                if not (start_time <= event.timestamp <= end_time):
                    return False

            return True

        except Exception as e:
            logger.error(f"Error checking event filters: {e}")
            return True

    def _record_metrics(self, event: ProviderAuditEvent):
        """Record metrics for audit event"""
        try:
            # Record event count metrics
            self._metrics_manager.register_counter(
                "provider_audit_events_total", ["provider", "event_type", "status"]
            ).labels(
                provider=event.provider_name,
                event_type=event.event_type.value,
                status=event.status.value,
            ).inc()

            # Record duration metrics
            if event.duration_ms is not None:
                self._metrics_manager.register_histogram(
                    "provider_audit_event_duration_ms",
                    ["provider", "event_type", "status"],
                ).labels(
                    provider=event.provider_name,
                    event_type=event.event_type.value,
                    status=event.status.value,
                ).observe(event.duration_ms)

            # Record severity metrics
            self._metrics_manager.register_counter(
                "provider_audit_events_by_severity", ["provider", "severity"]
            ).labels(provider=event.provider_name, severity=event.severity.value).inc()

        except Exception as e:
            logger.error(f"Error recording audit metrics: {e}")

    def get_audit_events(
        self,
        provider_name: Optional[str] = None,
        event_type: Optional[AuditEventType] = None,
        limit: int = 100,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[ProviderAuditEvent]:
        """Get filtered audit events"""
        try:
            events = self._audit_events

            # Filter by provider
            if provider_name:
                events = [e for e in events if e.provider_name == provider_name]

            # Filter by event type
            if event_type:
                events = [e for e in events if e.event_type == event_type]

            # Filter by time range
            if start_time:
                events = [e for e in events if e.timestamp >= start_time]
            if end_time:
                events = [e for e in events if e.timestamp <= end_time]

            # Sort by timestamp (newest first)
            events.sort(key=lambda e: e.timestamp, reverse=True)

            # Return limited results
            return events[:limit]

        except Exception as e:
            logger.error(f"Error getting audit events: {e}")
            return []

    def get_provider_metrics(
        self, provider_name: Optional[str] = None
    ) -> Dict[str, ProviderPerformanceMetrics]:
        """Get provider performance metrics"""
        try:
            if provider_name:
                return {provider_name: self._provider_metrics.get(provider_name)}
            return dict(self._provider_metrics)

        except Exception as e:
            logger.error(f"Error getting provider metrics: {e}")
            return {}

    def get_system_audit_summary(self) -> Dict[str, Any]:
        """Get comprehensive audit system summary"""
        try:
            total_events = len(self._audit_events)
            total_providers = len(self._provider_metrics)

            # Calculate overall system health
            successful_events = sum(
                1
                for event in self._audit_events
                if event.status == AuditEventStatus.SUCCESS
            )
            failed_events = sum(
                1
                for event in self._audit_events
                if event.status == AuditEventStatus.FAILURE
            )

            success_rate = successful_events / total_events if total_events > 0 else 0.0

            # Get provider health summary
            provider_health = {}
            for provider_name, metrics in self._provider_metrics.items():
                provider_health[provider_name] = {
                    "total_requests": metrics.total_requests,
                    "successful_requests": metrics.successful_requests,
                    "failed_requests": metrics.failed_requests,
                    "error_rate": metrics.error_rate,
                    "average_response_time_ms": metrics.average_response_time_ms,
                    "circuit_breaker_trips": metrics.circuit_breaker_trips,
                    "last_updated": metrics.last_updated.isoformat(),
                }

            # Recent activity
            recent_events = self._audit_events[-10:] if self._audit_events else []

            return {
                "audit_system_status": "active" if self._running else "inactive",
                "total_events": total_events,
                "total_providers": total_providers,
                "success_rate": success_rate,
                "provider_health": provider_health,
                "recent_events": [event.to_dict() for event in recent_events],
                "system_health": "healthy" if success_rate > 0.9 else "degraded",
            }

        except Exception as e:
            logger.error(f"Error getting audit summary: {e}")
            return {"error": str(e)}

    def set_event_filters(self, filters: Dict[str, Any]):
        """Set event filters for audit recording"""
        self._event_filters = filters
        logger.info(f"Audit event filters updated: {filters}")

    def clear_event_filters(self):
        """Clear all event filters"""
        self._event_filters = {}
        logger.info("Audit event filters cleared")

    def analyze_failure_patterns(
        self, provider_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze failure patterns in audit events"""
        try:
            events = self._audit_events

            if provider_name:
                events = [e for e in events if e.provider_name == provider_name]

            # Filter failure events
            failure_events = [e for e in events if e.status == AuditEventStatus.FAILURE]

            if not failure_events:
                return {"no_failures": True}

            # Analyze error types
            error_types = {}
            for event in failure_events:
                error_type = event.error_type or "unknown"
                error_types[error_type] = error_types.get(error_type, 0) + 1

            # Analyze time patterns
            hourly_failures = {}
            for event in failure_events:
                hour = event.timestamp.hour
                hourly_failures[hour] = hourly_failures.get(hour, 0) + 1

            # Analyze severity distribution
            severity_distribution = {}
            for event in failure_events:
                severity = event.severity.value
                severity_distribution[severity] = (
                    severity_distribution.get(severity, 0) + 1
                )

            return {
                "total_failures": len(failure_events),
                "error_types": error_types,
                "hourly_patterns": hourly_failures,
                "severity_distribution": severity_distribution,
                "failure_rate": len(failure_events) / len(events) if events else 0.0,
                "recommendations": self._generate_failure_recommendations(
                    error_types, hourly_failures
                ),
            }

        except Exception as e:
            logger.error(f"Error analyzing failure patterns: {e}")
            return {"error": str(e)}

    def _generate_failure_recommendations(
        self, error_types: Dict[str, int], hourly_failures: Dict[int, int]
    ) -> List[str]:
        """Generate recommendations based on failure patterns"""
        recommendations = []

        # Analyze error types
        if "timeout" in error_types:
            recommendations.append(
                "Consider increasing timeout settings for timeout errors"
            )
        if "rate_limit" in error_types:
            recommendations.append(
                "Implement rate limiting or upgrade subscription for rate limit errors"
            )
        if "authentication" in error_types:
            recommendations.append(
                "Check API credentials and authentication configuration"
            )

        # Analyze time patterns
        peak_hours = [hour for hour, count in hourly_failures.items() if count > 0]
        if peak_hours:
            recommendations.append(
                f"High failure rates during hours: {peak_hours}. Consider scaling during peak times"
            )

        return recommendations

    async def _cleanup_loop(self):
        """Background cleanup loop"""
        while self._running:
            try:
                await asyncio.sleep(3600)  # Run every hour

                # Clean old events (keep last 30 days)
                cutoff_time = datetime.utcnow() - timedelta(days=30)
                self._audit_events = [
                    e for e in self._audit_events if e.timestamp > cutoff_time
                ]

                # Clean old metrics (keep last 7 days)
                cutoff_time = datetime.utcnow() - timedelta(days=7)
                active_providers = {
                    name: metrics
                    for name, metrics in self._provider_metrics.items()
                    if metrics.last_updated > cutoff_time
                }
                self._provider_metrics = active_providers

                logger.info(
                    f"Audit cleanup completed: {len(self._audit_events)} events, {len(self._provider_metrics)} providers"
                )

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in audit cleanup loop: {e}")
                await asyncio.sleep(60)  # Wait longer on error

    def export_audit_data(
        self,
        format: str = "json",
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> str:
        """Export audit data in specified format"""
        try:
            events = self._audit_events

            # Filter by time range
            if start_time:
                events = [e for e in events if e.timestamp >= start_time]
            if end_time:
                events = [e for e in events if e.timestamp <= end_time]

            if format.lower() == "json":
                return json.dumps(
                    [event.to_dict() for event in events], indent=2, default=str
                )
            elif format.lower() == "csv":
                # Simple CSV export
                lines = [
                    "event_id,timestamp,provider_name,event_type,status,duration_ms,error_message"
                ]
                for event in events:
                    lines.append(
                        f"{event.event_id},{event.timestamp.isoformat()},{event.provider_name},{event.event_type.value},{event.status.value},{event.duration_ms or ''},{event.error_message or ''}"
                    )
                return "\n".join(lines)
            else:
                raise ValueError(f"Unsupported export format: {format}")

        except Exception as e:
            logger.error(f"Error exporting audit data: {e}")
            raise


# Global provider audit system instance
_provider_audit_system: Optional[ProviderAuditSystem] = None


async def get_provider_audit_system() -> ProviderAuditSystem:
    """Get global provider audit system instance"""
    global _provider_audit_system
    if _provider_audit_system is None:
        _provider_audit_system = ProviderAuditSystem()
        await _provider_audit_system.initialize()
    return _provider_audit_system
