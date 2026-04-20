"""
Service Health Dashboard

Provides comprehensive monitoring and visualization of service health across all
registered providers with real-time status, metrics, and alerting capabilities.
"""

import asyncio
import json
import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union
from pathlib import Path
import threading
import statistics

try:
    import prometheus_client
    from prometheus_client import Counter, Gauge, Histogram, REGISTRY

    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    Counter = Gauge = Histogram = lambda *args, **kwargs: None

try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    psutil = None


logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status levels"""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"
    CRITICAL = "critical"


class ServiceType(Enum):
    """Types of services being monitored"""

    PROVIDER = "provider"
    MODEL = "model"
    API = "api"
    DATABASE = "database"
    CACHE = "cache"
    QUEUE = "queue"
    STORAGE = "storage"


@dataclass
class HealthMetric:
    """Individual health metric"""

    name: str
    value: float
    unit: str
    timestamp: datetime
    labels: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
            "timestamp": self.timestamp.isoformat(),
            "labels": self.labels,
        }


@dataclass
class HealthCheck:
    """Health check result"""

    service_name: str
    service_type: ServiceType
    status: HealthStatus
    timestamp: datetime
    metrics: List[HealthMetric] = field(default_factory=list)
    message: Optional[str] = None
    error_details: Optional[str] = None
    response_time_ms: Optional[float] = None
    uptime_percentage: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "service_name": self.service_name,
            "service_type": self.service_type.value,
            "status": self.status.value,
            "timestamp": self.timestamp.isoformat(),
            "metrics": [metric.to_dict() for metric in self.metrics],
            "message": self.message,
            "error_details": self.error_details,
            "response_time_ms": self.response_time_ms,
            "uptime_percentage": self.uptime_percentage,
        }


@dataclass
class AlertRule:
    """Alert rule configuration"""

    name: str
    service_pattern: str  # regex pattern for service names
    metric_name: str
    condition: str  # "gt", "lt", "eq", "ne"
    threshold: float
    duration_seconds: int  # how long condition must be met
    severity: str  # "info", "warning", "error", "critical"
    enabled: bool = True
    notification_channels: List[str] = field(default_factory=list)

    def matches_service(self, service_name: str) -> bool:
        """Check if rule matches service name"""
        import re

        return bool(re.match(self.service_pattern, service_name))


@dataclass
class Alert:
    """Alert instance"""

    rule_name: str
    service_name: str
    severity: str
    message: str
    timestamp: datetime
    metrics: Dict[str, Any] = field(default_factory=dict)
    acknowledged: bool = False
    resolved: bool = False
    acknowledged_by: Optional[str] = None
    resolved_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_name": self.rule_name,
            "service_name": self.service_name,
            "severity": self.severity,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "metrics": self.metrics,
            "acknowledged": self.acknowledged,
            "resolved": self.resolved,
            "acknowledged_by": self.acknowledged_by,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
        }


class HealthMetricsCollector:
    """Collects and manages health metrics"""

    def __init__(self, max_history_size: int = 1000):
        self.max_history_size = max_history_size
        self._metrics: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=max_history_size)
        )
        self._prometheus_metrics = {}
        self._lock = threading.RLock()

        if PROMETHEUS_AVAILABLE:
            self._initialize_prometheus_metrics()

    def _initialize_prometheus_metrics(self):
        """Initialize Prometheus metrics"""
        # Check if metrics are already registered to avoid duplicates
        try:
            # Check if our metrics already exist
            existing_metrics = list(REGISTRY._collector_to_names.keys())
            metric_names = {
                "health_checks_total",
                "health_check_duration_seconds",
                "service_uptime_percentage",
                "service_response_time_ms",
                "service_error_rate",
            }

            # Only create metrics that don't already exist
            if any(name in existing_metrics for name in metric_names):
                # Get existing metrics from registry
                self._prometheus_metrics = {}
                for name, metric in REGISTRY._collector_to_names.items():
                    if name in metric_names:
                        self._prometheus_metrics[name] = metric
                return
        except (AttributeError, KeyError):
            pass

        # Create new metrics
        self._prometheus_metrics = {
            "health_checks_total": Counter(
                "health_checks_total",
                "Total health checks performed",
                ["service_name", "status"],
            ),
            "health_check_duration_seconds": Histogram(
                "health_check_duration_seconds",
                "Health check execution time",
                ["service_name"],
            ),
            "service_uptime_percentage": Gauge(
                "service_uptime_percentage",
                "Service uptime percentage",
                ["service_name"],
            ),
            "service_response_time_ms": Gauge(
                "service_response_time_ms",
                "Service response time in milliseconds",
                ["service_name"],
            ),
            "service_error_rate": Gauge(
                "service_error_rate", "Service error rate percentage", ["service_name"]
            ),
        }

    def record_metric(self, metric: HealthMetric):
        """Record a health metric"""
        with self._lock:
            key = f"{metric.name}:{metric.service_name if hasattr(metric, 'service_name') else 'global'}"
            self._metrics[key].append(metric)

            # Update Prometheus metrics if available
            if PROMETHEUS_AVAILABLE and hasattr(metric, "service_name"):
                self._update_prometheus_metric(metric)

    def _update_prometheus_metric(self, metric: HealthMetric):
        """Update Prometheus metric"""
        if metric.name == "response_time" and hasattr(metric, "service_name"):
            self._prometheus_metrics["service_response_time_ms"].labels(
                service_name=metric.service_name
            ).set(metric.value)

        elif metric.name == "uptime" and hasattr(metric, "service_name"):
            self._prometheus_metrics["service_uptime_percentage"].labels(
                service_name=metric.service_name
            ).set(metric.value)

        elif metric.name == "error_rate" and hasattr(metric, "service_name"):
            self._prometheus_metrics["service_error_rate"].labels(
                service_name=metric.service_name
            ).set(metric.value)

    def get_metric_history(
        self, metric_name: str, service_name: Optional[str] = None, limit: int = 100
    ) -> List[HealthMetric]:
        """Get metric history"""
        with self._lock:
            if service_name:
                key = f"{metric_name}:{service_name}"
            else:
                key = metric_name

            metrics = list(self._metrics.get(key, []))
            return metrics[-limit:]

    def get_metric_statistics(
        self,
        metric_name: str,
        service_name: Optional[str] = None,
        time_window_minutes: int = 60,
    ) -> Dict[str, float]:
        """Get metric statistics over time window"""
        cutoff_time = datetime.now() - timedelta(minutes=time_window_minutes)

        with self._lock:
            if service_name:
                key = f"{metric_name}:{service_name}"
            else:
                key = metric_name

            metrics = [
                m for m in self._metrics.get(key, []) if m.timestamp >= cutoff_time
            ]

            if not metrics:
                return {}

            values = [m.value for m in metrics]
            return {
                "count": len(values),
                "avg": statistics.mean(values),
                "min": min(values),
                "max": max(values),
                "p95": sorted(values)[int(len(values) * 0.95)] if values else 0,
                "p99": sorted(values)[int(len(values) * 0.99)] if values else 0,
            }


class ServiceHealthDashboard:
    """Main service health dashboard"""

    def __init__(self):
        self.health_checks: Dict[str, HealthCheck] = {}
        self.alert_rules: List[AlertRule] = []
        self.alerts: List[Alert] = []
        self.metrics_collector = HealthMetricsCollector()
        self._alert_state: Dict[
            str, Dict[str, Any]
        ] = {}  # Tracks alert conditions over time
        self._lock = threading.RLock()
        self._running = False
        self._monitoring_task: Optional[asyncio.Task] = None

        # Initialize default alert rules
        self._initialize_default_alert_rules()

    def _initialize_default_alert_rules(self):
        """Initialize default alert rules"""
        default_rules = [
            AlertRule(
                name="high_response_time",
                service_pattern=".*",
                metric_name="response_time",
                condition="gt",
                threshold=5000.0,  # 5 seconds
                duration_seconds=300,  # 5 minutes
                severity="warning",
            ),
            AlertRule(
                name="critical_response_time",
                service_pattern=".*",
                metric_name="response_time",
                condition="gt",
                threshold=30000.0,  # 30 seconds
                duration_seconds=60,  # 1 minute
                severity="critical",
            ),
            AlertRule(
                name="high_error_rate",
                service_pattern=".*",
                metric_name="error_rate",
                condition="gt",
                threshold=10.0,  # 10%
                duration_seconds=600,  # 10 minutes
                severity="error",
            ),
            AlertRule(
                name="service_down",
                service_pattern=".*",
                metric_name="availability",
                condition="lt",
                threshold=90.0,  # 90%
                duration_seconds=120,  # 2 minutes
                severity="critical",
            ),
            AlertRule(
                name="high_cpu_usage",
                service_pattern=".*",
                metric_name="cpu_usage",
                condition="gt",
                threshold=90.0,  # 90%
                duration_seconds=600,  # 10 minutes
                severity="warning",
            ),
            AlertRule(
                name="high_memory_usage",
                service_pattern=".*",
                metric_name="memory_usage",
                condition="gt",
                threshold=85.0,  # 85%
                duration_seconds=600,  # 10 minutes
                severity="warning",
            ),
        ]

        for rule in default_rules:
            self.add_alert_rule(rule)

    def add_alert_rule(self, rule: AlertRule):
        """Add alert rule"""
        with self._lock:
            self.alert_rules.append(rule)
            logger.info(f"Added alert rule: {rule.name}")

    def remove_alert_rule(self, rule_name: str):
        """Remove alert rule"""
        with self._lock:
            self.alert_rules = [r for r in self.alert_rules if r.name != rule_name]
            logger.info(f"Removed alert rule: {rule_name}")

    def record_health_check(self, health_check: HealthCheck):
        """Record a health check result"""
        with self._lock:
            self.health_checks[health_check.service_name] = health_check

            # Record metrics
            for metric in health_check.metrics:
                metric.service_name = health_check.service_name
                self.metrics_collector.record_metric(metric)

            # Update Prometheus metrics
            if PROMETHEUS_AVAILABLE:
                self.metrics_collector._prometheus_metrics[
                    "health_checks_total"
                ].labels(
                    service_name=health_check.service_name,
                    status=health_check.status.value,
                ).inc()

                if health_check.response_time_ms:
                    self.metrics_collector._prometheus_metrics[
                        "health_check_duration_seconds"
                    ].labels(service_name=health_check.service_name).observe(
                        health_check.response_time_ms / 1000.0
                    )

            # Check for alerts
            self._check_alerts(health_check)

            logger.info(
                f"Recorded health check for {health_check.service_name}: {health_check.status.value}"
            )

    def _check_alerts(self, health_check: HealthCheck):
        """Check if any alert rules are triggered"""
        for rule in self.alert_rules:
            if not rule.enabled:
                continue

            if not rule.matches_service(health_check.service_name):
                continue

            # Find the metric
            metric_value = None
            for metric in health_check.metrics:
                if metric.name == rule.metric_name:
                    metric_value = metric.value
                    break

            if metric_value is None:
                continue

            # Check condition
            triggered = False
            if rule.condition == "gt" and metric_value > rule.threshold:
                triggered = True
            elif rule.condition == "lt" and metric_value < rule.threshold:
                triggered = True
            elif rule.condition == "eq" and metric_value == rule.threshold:
                triggered = True
            elif rule.condition == "ne" and metric_value != rule.threshold:
                triggered = True

            if triggered:
                self._handle_alert_triggered(rule, health_check, metric_value)

    def _handle_alert_triggered(
        self, rule: AlertRule, health_check: HealthCheck, metric_value: float
    ):
        """Handle alert being triggered"""
        service_key = f"{rule.name}:{health_check.service_name}"

        # Initialize alert state if not exists
        if service_key not in self._alert_state:
            self._alert_state[service_key] = {
                "triggered_at": datetime.now(),
                "triggered_count": 0,
                "last_metric_value": metric_value,
            }

        state = self._alert_state[service_key]
        state["triggered_count"] += 1
        state["last_metric_value"] = metric_value

        # Check if duration threshold is met
        triggered_duration = (datetime.now() - state["triggered_at"]).total_seconds()

        if triggered_duration >= rule.duration_seconds:
            # Create alert
            alert = Alert(
                rule_name=rule.name,
                service_name=health_check.service_name,
                severity=rule.severity,
                message=f"Alert triggered: {rule.name} - {rule.condition} {rule.threshold} for {triggered_duration:.0f}s",
                timestamp=datetime.now(),
                metrics={rule.metric_name: metric_value},
            )

            self.alerts.append(alert)
            logger.warning(f"Alert triggered: {alert.message}")

    def acknowledge_alert(self, alert_id: str, acknowledged_by: str):
        """Acknowledge an alert"""
        with self._lock:
            for alert in self.alerts:
                if alert.service_name == alert_id and not alert.acknowledged:
                    alert.acknowledged = True
                    alert.acknowledged_by = acknowledged_by
                    logger.info(f"Alert acknowledged: {alert_id} by {acknowledged_by}")
                    break

    def resolve_alert(self, alert_id: str, resolved_by: str):
        """Resolve an alert"""
        with self._lock:
            for alert in self.alerts:
                if alert.service_name == alert_id and not alert.resolved:
                    alert.resolved = True
                    alert.resolved_at = datetime.now()
                    logger.info(f"Alert resolved: {alert_id} by {resolved_by}")
                    break

    def get_service_health(self, service_name: str) -> Optional[HealthCheck]:
        """Get health check for a specific service"""
        return self.health_checks.get(service_name)

    def get_all_services_health(self) -> Dict[str, HealthCheck]:
        """Get health checks for all services"""
        return self.health_checks.copy()

    def get_active_alerts(self, severity: Optional[str] = None) -> List[Alert]:
        """Get active (unresolved) alerts"""
        alerts = [alert for alert in self.alerts if not alert.resolved]
        if severity:
            alerts = [alert for alert in alerts if alert.severity == severity]
        return alerts

    def get_alert_history(self, limit: int = 100) -> List[Alert]:
        """Get alert history"""
        return self.alerts[-limit:]

    def get_dashboard_summary(self) -> Dict[str, Any]:
        """Get dashboard summary"""
        with self._lock:
            # Count services by status
            status_counts = defaultdict(int)
            for health_check in self.health_checks.values():
                status_counts[health_check.status.value] += 1

            # Count alerts by severity
            alert_counts = defaultdict(int)
            for alert in self.alerts:
                if not alert.resolved:
                    alert_counts[alert.severity] += 1

            # Get system metrics
            system_metrics = self._get_system_metrics()

            return {
                "total_services": len(self.health_checks),
                "service_status_counts": dict(status_counts),
                "active_alerts_count": len([a for a in self.alerts if not a.resolved]),
                "alert_counts_by_severity": dict(alert_counts),
                "total_alert_rules": len(self.alert_rules),
                "enabled_alert_rules": len([r for r in self.alert_rules if r.enabled]),
                "system_metrics": system_metrics,
                "last_updated": datetime.now().isoformat(),
            }

    def _get_system_metrics(self) -> Dict[str, Any]:
        """Get system-wide metrics"""
        metrics = {}

        if PSUTIL_AVAILABLE:
            try:
                # CPU metrics
                cpu_percent = psutil.cpu_percent(interval=1)
                metrics["cpu_usage_percent"] = cpu_percent
                metrics["cpu_count"] = psutil.cpu_count()

                # Memory metrics
                memory = psutil.virtual_memory()
                metrics["memory_usage_percent"] = memory.percent
                metrics["memory_total_gb"] = memory.total / (1024**3)
                metrics["memory_available_gb"] = memory.available / (1024**3)

                # Disk metrics
                disk = psutil.disk_usage("/")
                metrics["disk_usage_percent"] = (disk.used / disk.total) * 100
                metrics["disk_total_gb"] = disk.total / (1024**3)
                metrics["disk_free_gb"] = disk.free / (1024**3)

                # Network metrics
                network = psutil.net_io_counters()
                metrics["network_bytes_sent"] = network.bytes_sent
                metrics["network_bytes_recv"] = network.bytes_recv

            except Exception as e:
                logger.error(f"Failed to get system metrics: {e}")

        return metrics

    def get_service_metrics(
        self, service_name: str, metric_name: str, time_window_minutes: int = 60
    ) -> Dict[str, float]:
        """Get metrics for a specific service"""
        return self.metrics_collector.get_metric_statistics(
            metric_name, service_name, time_window_minutes
        )

    def export_health_data(self, output_file: str) -> bool:
        """Export health data to file"""
        try:
            export_data = {
                "export_timestamp": datetime.now().isoformat(),
                "health_checks": {
                    name: check.to_dict() for name, check in self.health_checks.items()
                },
                "alert_rules": [rule.__dict__ for rule in self.alert_rules],
                "alerts": [alert.to_dict() for alert in self.alerts],
                "dashboard_summary": self.get_dashboard_summary(),
                "metrics_samples": {},
            }

            # Export sample metrics
            for metric_name in ["response_time", "error_rate", "availability"]:
                export_data["metrics_samples"][metric_name] = {
                    service_name: [
                        metric.to_dict()
                        for metric in self.metrics_collector.get_metric_history(
                            metric_name, service_name, 10
                        )
                    ]
                    for service_name in self.health_checks.keys()
                }

            with open(output_file, "w") as f:
                json.dump(export_data, f, indent=2, default=str)

            logger.info(f"Health data exported to {output_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to export health data: {e}")
            return False

    async def start_monitoring(self, interval_seconds: int = 30):
        """Start health monitoring"""
        if self._running:
            return

        self._running = True
        self._monitoring_task = asyncio.create_task(
            self._monitoring_loop(interval_seconds)
        )
        logger.info(f"Health monitoring started with {interval_seconds}s interval")

    async def stop_monitoring(self):
        """Stop health monitoring"""
        self._running = False
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        logger.info("Health monitoring stopped")

    async def _monitoring_loop(self, interval_seconds: int):
        """Main monitoring loop"""
        while self._running:
            try:
                # Perform system health check
                await self._perform_system_health_check()

                # Clean up old alerts
                await self._cleanup_old_alerts()

                await asyncio.sleep(interval_seconds)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(5)

    async def _perform_system_health_check(self):
        """Perform system-wide health check"""
        system_metrics = self._get_system_metrics()

        # Determine system health status
        if system_metrics.get("cpu_usage_percent", 0) > 95:
            status = HealthStatus.CRITICAL
            message = "Critical CPU usage detected"
        elif system_metrics.get("memory_usage_percent", 0) > 90:
            status = HealthStatus.DEGRADED
            message = "High memory usage detected"
        elif system_metrics.get("disk_usage_percent", 0) > 95:
            status = HealthStatus.DEGRADED
            message = "High disk usage detected"
        else:
            status = HealthStatus.HEALTHY
            message = "System healthy"

        # Create health check
        health_check = HealthCheck(
            service_name="system",
            service_type=ServiceType.SYSTEM,
            status=status,
            timestamp=datetime.now(),
            message=message,
            metrics=[
                HealthMetric(
                    name="cpu_usage",
                    value=system_metrics.get("cpu_usage_percent", 0),
                    unit="percent",
                    timestamp=datetime.now(),
                ),
                HealthMetric(
                    name="memory_usage",
                    value=system_metrics.get("memory_usage_percent", 0),
                    unit="percent",
                    timestamp=datetime.now(),
                ),
                HealthMetric(
                    name="disk_usage",
                    value=system_metrics.get("disk_usage_percent", 0),
                    unit="percent",
                    timestamp=datetime.now(),
                ),
            ],
        )

        self.record_health_check(health_check)

    async def _cleanup_old_alerts(self):
        """Clean up old resolved alerts"""
        cutoff_time = datetime.now() - timedelta(days=30)

        with self._lock:
            self.alerts = [
                alert
                for alert in self.alerts
                if not alert.resolved or alert.resolved_at > cutoff_time
            ]
