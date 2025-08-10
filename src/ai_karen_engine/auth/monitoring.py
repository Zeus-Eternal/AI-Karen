"""
Comprehensive monitoring and metrics collection for the authentication service.

This module provides structured logging, metrics collection, and alerting
capabilities for monitoring authentication system health and security.
"""

import asyncio
import json
import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4

from ai_karen_engine.integrations.llm_utils import PROM_REGISTRY

from .config import AuthConfig
from .models import AuthEvent, AuthEventType

try:  # pragma: no cover - optional dependency
    from prometheus_client import CollectorRegistry, Counter, Histogram
except Exception:  # pragma: no cover

    class _DummyMetric:
        def inc(self, amount: int = 1) -> None:  # pragma: no cover
            pass

        def observe(self, value: float) -> None:  # pragma: no cover
            pass

    Counter = Histogram = _DummyMetric  # type: ignore
    CollectorRegistry = object  # type: ignore

AUTH_SUCCESS = None
AUTH_FAILURE = None
AUTH_PROCESSING_TIME = None


def init_auth_metrics(
    registry: CollectorRegistry | None = PROM_REGISTRY,
    force: bool = False,
):
    """Initialize authentication metrics."""
    global AUTH_SUCCESS, AUTH_FAILURE, AUTH_PROCESSING_TIME
    if not force:
        if AUTH_SUCCESS is not None:
            return AUTH_SUCCESS, AUTH_FAILURE, AUTH_PROCESSING_TIME
        if registry is not None:
            existing = getattr(registry, "_names_to_collectors", {})  # type: ignore[attr-defined]
            auth_success = existing.get("kari_auth_success_total")
            if auth_success is not None:
                AUTH_SUCCESS = auth_success
                AUTH_FAILURE = existing.get("kari_auth_failure_total")
                AUTH_PROCESSING_TIME = existing.get("kari_auth_processing_seconds")
                return AUTH_SUCCESS, AUTH_FAILURE, AUTH_PROCESSING_TIME

    try:
        AUTH_SUCCESS = Counter(
            "kari_auth_success_total",
            "Total successful authentication events",
            registry=registry,
        )
        AUTH_FAILURE = Counter(
            "kari_auth_failure_total",
            "Total failed authentication events",
            registry=registry,
        )
        AUTH_PROCESSING_TIME = Histogram(
            "kari_auth_processing_seconds",
            "Time spent processing authentication events",
            registry=registry,
        )
    except ValueError:
        if registry is not None:
            existing = getattr(registry, "_names_to_collectors", {})  # type: ignore[attr-defined]
            AUTH_SUCCESS = existing.get("kari_auth_success_total")
            AUTH_FAILURE = existing.get("kari_auth_failure_total")
            AUTH_PROCESSING_TIME = existing.get("kari_auth_processing_seconds")
    return AUTH_SUCCESS, AUTH_FAILURE, AUTH_PROCESSING_TIME


# Initialize metrics with default registry at import time
init_auth_metrics()


def metrics_hook(event: str, data: Dict[str, object]) -> None:
    """Forward authentication events to Prometheus metrics."""
    # Support both millisecond and second inputs for processing time
    duration_ms = data.get("processing_time_ms")
    duration = data.get("processing_time")
    if duration_ms is not None:
        try:
            duration = float(duration_ms) / 1000.0
        except Exception:  # pragma: no cover - best effort
            duration = 0.0
    else:
        try:
            duration = float(duration or 0)
        except Exception:  # pragma: no cover - best effort
            duration = 0.0

    # Normalize event names to a consistent set
    normalized = {
        "login_failed": "login_failed",
        "login_success": "login_success",
        "login_blocked": "login_blocked",
        "rate_limit_exceeded": "rate_limit_exceeded",
    }.get(event, event)

    if normalized == "login_success":
        if AUTH_SUCCESS is not None:
            AUTH_SUCCESS.inc()
        if AUTH_PROCESSING_TIME is not None:
            AUTH_PROCESSING_TIME.observe(duration)
    elif normalized in {"login_failed", "login_blocked", "rate_limit_exceeded"}:
        if AUTH_FAILURE is not None:
            AUTH_FAILURE.inc()
        if AUTH_PROCESSING_TIME is not None and duration:
            AUTH_PROCESSING_TIME.observe(duration)


@dataclass
class MetricPoint:
    """A single metric data point."""

    timestamp: datetime
    metric_name: str
    value: float
    tags: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "metric_name": self.metric_name,
            "value": self.value,
            "tags": self.tags,
        }


@dataclass
class Alert:
    """An alert triggered by monitoring conditions."""

    alert_id: str
    alert_type: str
    severity: str  # "low", "medium", "high", "critical"
    message: str
    timestamp: datetime
    details: Dict[str, Any] = field(default_factory=dict)
    resolved: bool = False
    resolved_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "alert_id": self.alert_id,
            "alert_type": self.alert_type,
            "severity": self.severity,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "details": self.details,
            "resolved": self.resolved,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
        }


class MetricsCollector:
    """
    Collects and aggregates authentication metrics for monitoring.

    Provides real-time metrics collection with configurable retention
    and aggregation capabilities.
    """

    def __init__(self, config: AuthConfig):
        self.config = config
        self.monitoring_config = config.monitoring

        # Metrics storage
        self._metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=10000))
        self._counters: Dict[str, int] = defaultdict(int)
        self._gauges: Dict[str, float] = defaultdict(float)
        self._histograms: Dict[str, List[float]] = defaultdict(list)

        # Time-based aggregations
        self._minute_buckets: Dict[str, Dict[int, float]] = defaultdict(dict)
        self._hour_buckets: Dict[str, Dict[int, float]] = defaultdict(dict)

        # Performance tracking
        self._operation_times: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=1000)
        )

        self.logger = logging.getLogger(f"{__name__}.MetricsCollector")

        # Start background cleanup task
        self._cleanup_task = None
        if self.monitoring_config.enable_metrics:
            self._start_cleanup_task()

    def _start_cleanup_task(self) -> None:
        """Start background task for metrics cleanup."""

        async def cleanup_loop():
            while True:
                try:
                    await asyncio.sleep(300)  # 5 minutes
                    await self._cleanup_old_metrics()
                except Exception as e:
                    self.logger.error(f"Error in metrics cleanup: {e}")

        self._cleanup_task = asyncio.create_task(cleanup_loop())

    async def _cleanup_old_metrics(self) -> None:
        """Clean up old metrics data to prevent memory growth."""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)

        for metric_name, points in self._metrics.items():
            # Remove old points
            while points and points[0].timestamp < cutoff_time:
                points.popleft()

        # Clean up time buckets
        current_minute = int(time.time() // 60)
        current_hour = int(time.time() // 3600)

        for metric_name in list(self._minute_buckets.keys()):
            buckets = self._minute_buckets[metric_name]
            for minute in list(buckets.keys()):
                if minute < current_minute - 1440:  # Keep 24 hours
                    del buckets[minute]

        for metric_name in list(self._hour_buckets.keys()):
            buckets = self._hour_buckets[metric_name]
            for hour in list(buckets.keys()):
                if hour < current_hour - 168:  # Keep 7 days
                    del buckets[hour]

    async def record_counter(
        self, metric_name: str, value: int = 1, tags: Optional[Dict[str, str]] = None
    ) -> None:
        """Record a counter metric."""
        if not self.monitoring_config.enable_metrics:
            return

        full_name = self._build_metric_name(metric_name, tags)
        self._counters[full_name] += value

        # Also store as time series
        point = MetricPoint(
            timestamp=datetime.now(timezone.utc),
            metric_name=metric_name,
            value=float(value),
            tags=tags or {},
        )
        self._metrics[metric_name].append(point)

        # Update time buckets
        await self._update_time_buckets(metric_name, float(value))

    async def record_gauge(
        self, metric_name: str, value: float, tags: Optional[Dict[str, str]] = None
    ) -> None:
        """Record a gauge metric."""
        if not self.monitoring_config.enable_metrics:
            return

        full_name = self._build_metric_name(metric_name, tags)
        self._gauges[full_name] = value

        point = MetricPoint(
            timestamp=datetime.now(timezone.utc),
            metric_name=metric_name,
            value=value,
            tags=tags or {},
        )
        self._metrics[metric_name].append(point)

    async def record_histogram(
        self, metric_name: str, value: float, tags: Optional[Dict[str, str]] = None
    ) -> None:
        """Record a histogram metric."""
        if not self.monitoring_config.enable_metrics:
            return

        full_name = self._build_metric_name(metric_name, tags)
        self._histograms[full_name].append(value)

        # Keep only recent values
        if len(self._histograms[full_name]) > 1000:
            self._histograms[full_name] = self._histograms[full_name][-1000:]

        point = MetricPoint(
            timestamp=datetime.now(timezone.utc),
            metric_name=metric_name,
            value=value,
            tags=tags or {},
        )
        self._metrics[metric_name].append(point)

    async def record_timing(
        self, operation: str, duration_ms: float, tags: Optional[Dict[str, str]] = None
    ) -> None:
        """Record operation timing."""
        await self.record_histogram(f"auth.timing.{operation}", duration_ms, tags)
        self._operation_times[operation].append(duration_ms)

    def _build_metric_name(self, base_name: str, tags: Optional[Dict[str, str]]) -> str:
        """Build full metric name with tags."""
        if not tags:
            return base_name

        tag_str = ",".join(f"{k}={v}" for k, v in sorted(tags.items()))
        return f"{base_name}[{tag_str}]"

    async def _update_time_buckets(self, metric_name: str, value: float) -> None:
        """Update time-based aggregation buckets."""
        current_time = time.time()
        current_minute = int(current_time // 60)
        current_hour = int(current_time // 3600)

        # Update minute bucket
        if current_minute not in self._minute_buckets[metric_name]:
            self._minute_buckets[metric_name][current_minute] = 0
        self._minute_buckets[metric_name][current_minute] += value

        # Update hour bucket
        if current_hour not in self._hour_buckets[metric_name]:
            self._hour_buckets[metric_name][current_hour] = 0
        self._hour_buckets[metric_name][current_hour] += value

    def get_counter(
        self, metric_name: str, tags: Optional[Dict[str, str]] = None
    ) -> int:
        """Get current counter value."""
        full_name = self._build_metric_name(metric_name, tags)
        return self._counters.get(full_name, 0)

    def get_gauge(
        self, metric_name: str, tags: Optional[Dict[str, str]] = None
    ) -> float:
        """Get current gauge value."""
        full_name = self._build_metric_name(metric_name, tags)
        return self._gauges.get(full_name, 0.0)

    def get_histogram_stats(
        self, metric_name: str, tags: Optional[Dict[str, str]] = None
    ) -> Dict[str, float]:
        """Get histogram statistics."""
        full_name = self._build_metric_name(metric_name, tags)
        values = self._histograms.get(full_name, [])

        if not values:
            return {
                "count": 0,
                "min": 0,
                "max": 0,
                "avg": 0,
                "p50": 0,
                "p95": 0,
                "p99": 0,
            }

        sorted_values = sorted(values)
        count = len(sorted_values)

        return {
            "count": count,
            "min": sorted_values[0],
            "max": sorted_values[-1],
            "avg": sum(sorted_values) / count,
            "p50": sorted_values[int(count * 0.5)],
            "p95": sorted_values[int(count * 0.95)],
            "p99": sorted_values[int(count * 0.99)],
        }

    def get_rate(self, metric_name: str, minutes: int = 5) -> float:
        """Get rate per minute for a metric over the specified time window."""
        current_minute = int(time.time() // 60)
        total = 0

        for i in range(minutes):
            minute = current_minute - i
            total += self._minute_buckets[metric_name].get(minute, 0)

        return total / minutes if minutes > 0 else 0

    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all current metrics."""
        return {
            "counters": dict(self._counters),
            "gauges": dict(self._gauges),
            "histograms": {
                name: self.get_histogram_stats(name.split("[")[0])
                for name in self._histograms.keys()
            },
            "rates": {
                metric: {
                    "1min": self.get_rate(metric, 1),
                    "5min": self.get_rate(metric, 5),
                    "15min": self.get_rate(metric, 15),
                }
                for metric in self._minute_buckets.keys()
            },
        }


class AlertManager:
    """
    Manages alerts and notifications for authentication monitoring.

    Provides configurable alerting based on metrics thresholds
    and security events.
    """

    def __init__(self, config: AuthConfig, metrics_collector: MetricsCollector):
        self.config = config
        self.monitoring_config = config.monitoring
        self.metrics_collector = metrics_collector

        # Alert storage
        self._active_alerts: Dict[str, Alert] = {}
        self._alert_history: deque = deque(maxlen=1000)

        # Alert rules
        self._alert_rules: List[Dict[str, Any]] = []
        self._setup_default_alert_rules()

        # Alert callbacks
        self._alert_callbacks: List[Callable[[Alert], None]] = []

        self.logger = logging.getLogger(f"{__name__}.AlertManager")

        # Start monitoring task
        self._monitoring_task = None
        if self.monitoring_config.enable_alerting:
            self._start_monitoring_task()

    def _setup_default_alert_rules(self) -> None:
        """Set up default alert rules."""
        self._alert_rules = [
            {
                "name": "high_failed_login_rate",
                "condition": lambda: self.metrics_collector.get_rate(
                    "auth.login.failed", 5
                )
                > 10,
                "severity": "high",
                "message": "High failed login rate detected",
                "cooldown_minutes": 5,
            },
            {
                "name": "authentication_errors",
                "condition": lambda: self.metrics_collector.get_rate("auth.errors", 5)
                > 5,
                "severity": "medium",
                "message": "High authentication error rate",
                "cooldown_minutes": 10,
            },
            {
                "name": "security_blocks",
                "condition": lambda: self.metrics_collector.get_rate(
                    "auth.security.blocked", 5
                )
                > 2,
                "severity": "high",
                "message": "Multiple security blocks detected",
                "cooldown_minutes": 5,
            },
            {
                "name": "slow_authentication",
                "condition": lambda: self.metrics_collector.get_histogram_stats(
                    "auth.timing.authenticate"
                ).get("p95", 0)
                > 5000,
                "severity": "medium",
                "message": "Slow authentication performance",
                "cooldown_minutes": 15,
            },
            {
                "name": "anomaly_detection_rate",
                "condition": lambda: self.metrics_collector.get_rate(
                    "auth.anomaly.detected", 5
                )
                > 1,
                "severity": "high",
                "message": "High anomaly detection rate",
                "cooldown_minutes": 5,
            },
        ]

    def _start_monitoring_task(self) -> None:
        """Start background monitoring task."""

        async def monitoring_loop():
            while True:
                try:
                    await asyncio.sleep(60)  # Check every minute
                    await self._check_alert_rules()
                except Exception as e:
                    self.logger.error(f"Error in alert monitoring: {e}")

        self._monitoring_task = asyncio.create_task(monitoring_loop())

    async def _check_alert_rules(self) -> None:
        """Check all alert rules and trigger alerts if needed."""
        for rule in self._alert_rules:
            try:
                rule_name = rule["name"]

                # Check if alert is in cooldown
                if self._is_in_cooldown(rule_name, rule.get("cooldown_minutes", 5)):
                    continue

                # Evaluate condition
                if rule["condition"]():
                    await self._trigger_alert(
                        alert_type=rule_name,
                        severity=rule["severity"],
                        message=rule["message"],
                        details={"rule": rule_name},
                    )
            except Exception as e:
                self.logger.error(
                    f"Error checking alert rule {rule.get('name', 'unknown')}: {e}"
                )

    def _is_in_cooldown(self, alert_type: str, cooldown_minutes: int) -> bool:
        """Check if an alert type is in cooldown period."""
        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=cooldown_minutes)

        # Check recent alerts of this type
        for alert in reversed(self._alert_history):
            if alert.alert_type == alert_type and alert.timestamp > cutoff_time:
                return True

        return False

    async def trigger_security_alert(
        self, event: AuthEvent, severity: str = "medium"
    ) -> None:
        """Trigger a security-related alert."""
        await self._trigger_alert(
            alert_type="security_event",
            severity=severity,
            message=f"Security event: {event.event_type.value}",
            details={
                "event_id": event.event_id,
                "event_type": event.event_type.value,
                "user_id": event.user_id,
                "email": event.email,
                "ip_address": event.ip_address,
                "risk_score": event.risk_score,
                "security_flags": event.security_flags,
            },
        )

    async def _trigger_alert(
        self,
        alert_type: str,
        severity: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> Alert:
        """Trigger a new alert."""
        alert = Alert(
            alert_id=str(uuid4()),
            alert_type=alert_type,
            severity=severity,
            message=message,
            timestamp=datetime.now(timezone.utc),
            details=details or {},
        )

        # Store alert
        self._active_alerts[alert.alert_id] = alert
        self._alert_history.append(alert)

        # Log alert
        self.logger.warning(
            f"ALERT [{severity.upper()}] {alert_type}: {message}",
            extra={
                "alert_id": alert.alert_id,
                "alert_type": alert_type,
                "severity": severity,
                "details": details,
            },
        )

        # Notify callbacks
        for callback in self._alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                self.logger.error(f"Error in alert callback: {e}")

        return alert

    def add_alert_callback(self, callback: Callable[[Alert], None]) -> None:
        """Add a callback function to be called when alerts are triggered."""
        self._alert_callbacks.append(callback)

    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an active alert."""
        if alert_id in self._active_alerts:
            alert = self._active_alerts[alert_id]
            alert.resolved = True
            alert.resolved_at = datetime.now(timezone.utc)
            del self._active_alerts[alert_id]

            self.logger.info(f"Alert resolved: {alert_id}")
            return True

        return False

    def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts."""
        return list(self._active_alerts.values())

    def get_alert_history(self, limit: int = 100) -> List[Alert]:
        """Get recent alert history."""
        return list(self._alert_history)[-limit:]

    def get_alert_stats(self) -> Dict[str, Any]:
        """Get alert statistics."""
        active_count = len(self._active_alerts)
        total_count = len(self._alert_history)

        # Count by severity
        severity_counts = defaultdict(int)
        for alert in self._alert_history:
            severity_counts[alert.severity] += 1

        # Count by type
        type_counts = defaultdict(int)
        for alert in self._alert_history:
            type_counts[alert.alert_type] += 1

        return {
            "active_alerts": active_count,
            "total_alerts": total_count,
            "alerts_by_severity": dict(severity_counts),
            "alerts_by_type": dict(type_counts),
            "alerting_enabled": self.monitoring_config.enable_alerting,
        }


class AuthMonitor:
    """
    Main monitoring class that coordinates metrics collection and alerting.

    Provides a unified interface for monitoring authentication system
    health, performance, and security.
    """

    def __init__(self, config: AuthConfig):
        self.config = config
        self.monitoring_config = config.monitoring

        # Initialize components
        self.metrics = MetricsCollector(config)
        self.alerts = AlertManager(config, self.metrics)

        # Structured logger for auth events
        self.logger = logging.getLogger(f"{__name__}.AuthMonitor")
        self._setup_structured_logging()

        # Event tracking
        self._recent_events: deque = deque(maxlen=1000)

        self.logger.info("AuthMonitor initialized")

    def _setup_structured_logging(self) -> None:
        """Set up structured logging for authentication events."""

        # Create a custom formatter for structured logs
        class StructuredFormatter(logging.Formatter):
            def format(self, record):
                # Create structured log entry
                log_entry = {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "level": record.levelname,
                    "logger": record.name,
                    "message": record.getMessage(),
                }

                # Add extra fields if present
                if hasattr(record, "auth_event"):
                    log_entry["auth_event"] = record.auth_event
                if hasattr(record, "event_id"):
                    log_entry["event_id"] = record.event_id
                if hasattr(record, "user_id"):
                    log_entry["user_id"] = record.user_id
                if hasattr(record, "ip_address"):
                    log_entry["ip_address"] = record.ip_address

                return json.dumps(log_entry)

        # Add structured handler if not already present
        if not any(
            isinstance(h.formatter, StructuredFormatter) for h in self.logger.handlers
        ):
            handler = logging.StreamHandler()
            handler.setFormatter(StructuredFormatter())
            self.logger.addHandler(handler)
        # Prevent duplicate logs from propagating to root logger
        self.logger.propagate = False

    async def record_auth_event(self, event: AuthEvent) -> None:
        """Record an authentication event for monitoring."""
        if not self.monitoring_config.enable_monitoring:
            return

        # Store event
        self._recent_events.append(event)

        # Record metrics
        await self._record_event_metrics(event)

        # Log event
        await self._log_structured_event(event)

        # Check for security alerts
        if self._should_trigger_security_alert(event):
            severity = self._determine_alert_severity(event)
            await self.alerts.trigger_security_alert(event, severity)

    async def _record_event_metrics(self, event: AuthEvent) -> None:
        """Record metrics for an authentication event."""
        base_tags = {
            "event_type": event.event_type.value,
            "success": str(event.success).lower(),
            "tenant_id": event.tenant_id or "default",
        }

        # Record basic event counter
        await self.metrics.record_counter("auth.events.total", 1, base_tags)

        # Record success/failure counters
        if event.success:
            await self.metrics.record_counter("auth.events.success", 1, base_tags)
        else:
            await self.metrics.record_counter("auth.events.failed", 1, base_tags)

        # Record specific event type counters
        event_type_key = event.event_type.value.replace("_", ".")
        await self.metrics.record_counter(f"auth.{event_type_key}", 1, base_tags)

        # Record processing time if available
        if event.processing_time_ms > 0:
            await self.metrics.record_timing(
                "authenticate" if "login" in event.event_type.value else "general",
                event.processing_time_ms,
                base_tags,
            )

        # Record risk score
        if event.risk_score > 0:
            await self.metrics.record_histogram(
                "auth.risk_score", event.risk_score, base_tags
            )

        # Record security-specific metrics
        if event.blocked_by_security:
            await self.metrics.record_counter("auth.security.blocked", 1, base_tags)

        if event.security_flags:
            for flag in event.security_flags:
                flag_tags = {**base_tags, "flag": flag}
                await self.metrics.record_counter("auth.security.flags", 1, flag_tags)

        # Record error metrics
        if not event.success and event.error_message:
            error_tags = {
                **base_tags,
                "error_type": self._classify_error(event.error_message),
            }
            await self.metrics.record_counter("auth.errors", 1, error_tags)

    async def _log_structured_event(self, event: AuthEvent) -> None:
        """Log authentication event with structured format."""
        log_level = logging.INFO
        if not event.success or event.blocked_by_security:
            log_level = logging.WARNING
        if event.risk_score > 0.7:
            log_level = logging.ERROR

        self.logger.log(
            log_level,
            f"AUTH_EVENT: {event.event_type.value} - {'SUCCESS' if event.success else 'FAILED'}",
            extra={
                "auth_event": event.to_dict(),
                "event_id": event.event_id,
                "user_id": event.user_id,
                "email": event.email,
                "ip_address": event.ip_address,
                "success": event.success,
                "risk_score": event.risk_score,
                "processing_time_ms": event.processing_time_ms,
            },
        )

    def _should_trigger_security_alert(self, event: AuthEvent) -> bool:
        """Determine if an event should trigger a security alert."""
        # High-risk events
        if event.risk_score > 0.8:
            return True

        # Security blocks
        if event.blocked_by_security:
            return True

        # Multiple security flags
        if len(event.security_flags) >= 3:
            return True

        # Specific high-risk event types
        high_risk_events = {
            AuthEventType.LOGIN_BLOCKED,
            AuthEventType.SECURITY_BLOCK,
            AuthEventType.ANOMALY_DETECTED,
            AuthEventType.THREAT_DETECTED,
            AuthEventType.RATE_LIMIT_EXCEEDED,
        }

        return event.event_type in high_risk_events

    def _determine_alert_severity(self, event: AuthEvent) -> str:
        """Determine alert severity based on event characteristics."""
        if event.risk_score > 0.9 or event.event_type == AuthEventType.THREAT_DETECTED:
            return "critical"
        elif event.risk_score > 0.7 or event.event_type in {
            AuthEventType.LOGIN_BLOCKED,
            AuthEventType.SECURITY_BLOCK,
            AuthEventType.ANOMALY_DETECTED,
        }:
            return "high"
        elif event.risk_score > 0.5 or len(event.security_flags) >= 2:
            return "medium"
        else:
            return "low"

    def _classify_error(self, error_message: str) -> str:
        """Classify error message into categories."""
        error_lower = error_message.lower()

        if "credential" in error_lower or "password" in error_lower:
            return "invalid_credentials"
        elif "rate limit" in error_lower:
            return "rate_limit"
        elif "locked" in error_lower:
            return "account_locked"
        elif "expired" in error_lower:
            return "session_expired"
        elif "not found" in error_lower:
            return "user_not_found"
        elif "security" in error_lower or "blocked" in error_lower:
            return "security_block"
        else:
            return "other"

    async def record_performance_metric(
        self,
        operation: str,
        duration_ms: float,
        success: bool = True,
        tags: Optional[Dict[str, str]] = None,
    ) -> None:
        """Record a performance metric."""
        base_tags = {"operation": operation, "success": str(success).lower()}
        if tags:
            base_tags.update(tags)

        await self.metrics.record_timing(operation, duration_ms, base_tags)

        # Record operation counter
        await self.metrics.record_counter(f"auth.operations.{operation}", 1, base_tags)

    async def record_user_activity(
        self, user_id: str, activity_type: str, details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Record user activity for monitoring."""
        tags = {"activity_type": activity_type}
        await self.metrics.record_counter("auth.user.activity", 1, tags)

        # Update user activity gauge
        await self.metrics.record_gauge(
            f"auth.user.last_activity.{user_id}", time.time()
        )

    def get_monitoring_stats(self) -> Dict[str, Any]:
        """Get comprehensive monitoring statistics."""
        return {
            "metrics": self.metrics.get_all_metrics(),
            "alerts": self.alerts.get_alert_stats(),
            "recent_events_count": len(self._recent_events),
            "monitoring_enabled": self.monitoring_config.enable_monitoring,
            "metrics_enabled": self.monitoring_config.enable_metrics,
            "alerting_enabled": self.monitoring_config.enable_alerting,
        }

    def get_recent_events(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent authentication events."""
        return [event.to_dict() for event in list(self._recent_events)[-limit:]]

    def get_health_status(self) -> Dict[str, Any]:
        """Get system health status."""
        # Calculate health metrics
        recent_events = list(self._recent_events)[-100:]  # Last 100 events

        if not recent_events:
            return {"status": "unknown", "reason": "No recent events"}

        # Calculate success rate
        successful_events = sum(1 for event in recent_events if event.success)
        success_rate = successful_events / len(recent_events)

        # Check for active critical alerts
        critical_alerts = [
            alert
            for alert in self.alerts.get_active_alerts()
            if alert.severity == "critical"
        ]

        # Determine overall health
        if critical_alerts:
            status = "critical"
            reason = f"{len(critical_alerts)} critical alerts active"
        elif success_rate < 0.8:
            status = "degraded"
            reason = f"Low success rate: {success_rate:.1%}"
        elif success_rate < 0.95:
            status = "warning"
            reason = f"Reduced success rate: {success_rate:.1%}"
        else:
            status = "healthy"
            reason = f"Success rate: {success_rate:.1%}"

        return {
            "status": status,
            "reason": reason,
            "success_rate": success_rate,
            "active_alerts": len(self.alerts.get_active_alerts()),
            "critical_alerts": len(critical_alerts),
            "recent_events": len(recent_events),
        }

    async def shutdown(self) -> None:
        """Shutdown monitoring components."""
        if self.metrics._cleanup_task:
            self.metrics._cleanup_task.cancel()

        if self.alerts._monitoring_task:
            self.alerts._monitoring_task.cancel()

        self.logger.info("AuthMonitor shutdown completed")
