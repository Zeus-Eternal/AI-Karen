"""
Unified Extension Health Monitor

Consolidates the best features from both platform/core and runtime health monitoring systems.
Provides comprehensive health monitoring with metrics collection, trend analysis, and alert generation.
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
import threading
import psutil

from .database_models import ExtensionModel, ExtensionHealth
from ..platform.core.registry.health_dashboard import HealthDashboard

logger = logging.getLogger(__name__)


class HealthStatus(str, Enum):
    """Health status enumeration."""

    HEALTHY = "healthy"
    WARNING = "warning"
    ERROR = "error"
    UNKNOWN = "unknown"


class HealthSeverity(str, Enum):
    """Health severity levels."""

    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class HealthMetric:
    """Health metric data structure."""

    name: str
    value: float
    unit: str
    timestamp: float
    tags: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class HealthAlert:
    """Health alert data structure."""

    id: str
    extension_id: str
    metric_name: str
    current_value: float
    threshold: float
    severity: HealthSeverity
    status: HealthStatus
    message: str
    timestamp: float
    resolved: bool = False
    resolved_at: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class ExtensionHealthMonitor:
    """Unified extension health monitoring system."""

    def __init__(self, registry=None):
        self.registry = registry
        self.health_data: Dict[str, List[HealthMetric]] = {}
        self.alerts: Dict[str, HealthAlert] = {}
        self.health_status: Dict[str, HealthStatus] = {}
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

        # Configuration
        self.check_interval = 30  # seconds
        self.max_metrics = 1000
        self.alert_thresholds = {
            "cpu_usage": 80.0,
            "memory_usage": 85.0,
            "response_time": 5000.0,  # ms
            "error_rate": 0.05,  # 5%
        }

        # Alert handlers
        self._alert_handlers: List[Callable] = []

        # Health check functions
        self._health_checks: Dict[str, Callable] = {}
        self._setup_default_health_checks()

    async def initialize(self) -> None:
        """Initialize the health monitor."""
        # Load existing health data
        await self._load_health_data()

        # Start monitoring
        self.start_monitoring()

        logger.info("Extension health monitor initialized")

    def start_monitoring(self) -> None:
        """Start health monitoring."""
        if self._monitoring:
            return

        self._monitoring = True
        self._monitor_thread = threading.Thread(target=self._monitoring_loop)
        self._monitor_thread.daemon = True
        self._monitor_thread.start()

        logger.info("Health monitoring started")

    def stop_monitoring(self) -> None:
        """Stop health monitoring."""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join()

        logger.info("Health monitoring stopped")

    def register_health_check(
        self, name: str, check_func: Callable[[], Dict[str, Any]]
    ) -> None:
        """Register a custom health check function."""
        self._health_checks[name] = check_func
        logger.info(f"Registered health check: {name}")

    def register_alert_handler(self, handler: Callable) -> None:
        """Register an alert handler."""
        self._alert_handlers.append(handler)
        logger.info("Registered alert handler")

    async def check_extension_health(self, extension_id: str) -> Dict[str, Any]:
        """Check health of a specific extension."""
        health_data = {}

        # Get extension information
        if self.registry:
            extension = await self.registry.get_extension(extension_id)
            if extension:
                health_data["extension"] = {
                    "id": extension.id,
                    "name": extension.name,
                    "version": extension.version,
                    "state": extension.state.value,
                }

        # Run health checks
        for check_name, check_func in self._health_checks.items():
            try:
                result = check_func()
                health_data[check_name] = result
            except Exception as e:
                logger.error(f"Health check {check_name} failed: {e}")
                health_data[check_name] = {"status": "error", "error": str(e)}

        # Calculate overall health status
        health_data["overall_status"] = self._calculate_overall_status(health_data)

        # Store health metrics
        await self._store_health_metrics(extension_id, health_data)

        return health_data

    async def get_extension_health_history(
        self, extension_id: str, hours: int = 24
    ) -> List[HealthMetric]:
        """Get health history for an extension."""
        with self._lock:
            if extension_id not in self.health_data:
                return []

            cutoff_time = time.time() - (hours * 3600)
            return [
                metric
                for metric in self.health_data[extension_id]
                if metric.timestamp >= cutoff_time
            ]

    async def get_current_health_status(self, extension_id: str) -> HealthStatus:
        """Get current health status for an extension."""
        with self._lock:
            return self.health_status.get(extension_id, HealthStatus.UNKNOWN)

    async def get_all_health_status(self) -> Dict[str, HealthStatus]:
        """Get health status for all extensions."""
        with self._lock:
            return self.health_status.copy()

    async def get_active_alerts(
        self, extension_id: Optional[str] = None
    ) -> List[HealthAlert]:
        """Get active alerts."""
        with self._lock:
            alerts = list(self.alerts.values())

            if extension_id:
                alerts = [
                    alert for alert in alerts if alert.extension_id == extension_id
                ]

            return [alert for alert in alerts if not alert.resolved]

    async def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert."""
        with self._lock:
            if alert_id in self.alerts:
                alert = self.alerts[alert_id]
                alert.resolved = True
                alert.resolved_at = time.time()

                logger.info(f"Resolved alert: {alert_id}")
                return True

            return False

    async def _monitoring_loop(self) -> None:
        """Main monitoring loop."""
        while self._monitoring:
            try:
                # Check health for all extensions
                if self.registry:
                    extensions = await self.registry.list_extensions()
                    for extension in extensions:
                        await self.check_extension_health(extension.id)

                # Check system health
                await self._check_system_health()

                # Check for alerts
                await self._check_alerts()

                # Cleanup old data
                await self._cleanup_old_data()

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")

            # Wait for next check
            time.sleep(self.check_interval)

    async def _check_system_health(self) -> None:
        """Check overall system health."""
        try:
            # Get system metrics
            cpu_usage = psutil.cpu_percent()
            memory_usage = psutil.virtual_memory().percent

            # Store system metrics
            await self._store_health_metrics(
                "system",
                {
                    "cpu_usage": cpu_usage,
                    "memory_usage": memory_usage,
                    "timestamp": time.time(),
                },
            )

        except Exception as e:
            logger.error(f"Error checking system health: {e}")

    async def _check_alerts(self) -> None:
        """Check for and generate alerts."""
        with self._lock:
            for extension_id, metrics in self.health_data.items():
                for metric in metrics:
                    await self._check_metric_alerts(extension_id, metric)

    async def _check_metric_alerts(
        self, extension_id: str, metric: HealthMetric
    ) -> None:
        """Check if a metric triggers any alerts."""
        if metric.name not in self.alert_thresholds:
            return

        threshold = self.alert_thresholds[metric.name]
        if metric.value > threshold:
            # Create alert if not already exists
            alert_id = f"{extension_id}_{metric.name}_{int(time.time())}"

            if alert_id not in self.alerts:
                alert = HealthAlert(
                    id=alert_id,
                    extension_id=extension_id,
                    metric_name=metric.name,
                    current_value=metric.value,
                    threshold=threshold,
                    severity=self._get_alert_severity(
                        metric.name, metric.value, threshold
                    ),
                    status=HealthStatus.ERROR,
                    message=f"{metric.name} is {metric.value:.2f} (threshold: {threshold})",
                    timestamp=time.time(),
                    metadata={"unit": metric.unit},
                )

                self.alerts[alert_id] = alert

                # Notify alert handlers
                await self._notify_alert_handlers(alert)

                logger.warning(f"Alert generated: {alert.message}")

    def _get_alert_severity(
        self, metric_name: str, current_value: float, threshold: float
    ) -> HealthSeverity:
        """Determine alert severity based on metric and threshold."""
        if metric_name == "cpu_usage" or metric_name == "memory_usage":
            if current_value > 95:
                return HealthSeverity.CRITICAL
            elif current_value > 90:
                return HealthSeverity.HIGH
            elif current_value > 80:
                return HealthSeverity.MEDIUM
            else:
                return HealthSeverity.LOW
        elif metric_name == "response_time":
            if current_value > 10000:
                return HealthSeverity.CRITICAL
            elif current_value > 5000:
                return HealthSeverity.HIGH
            elif current_value > 2000:
                return HealthSeverity.MEDIUM
            else:
                return HealthSeverity.LOW
        elif metric_name == "error_rate":
            if current_value > 0.1:
                return HealthSeverity.CRITICAL
            elif current_value > 0.05:
                return HealthSeverity.HIGH
            elif current_value > 0.01:
                return HealthSeverity.MEDIUM
            else:
                return HealthSeverity.LOW

        return HealthSeverity.MEDIUM

    async def _notify_alert_handlers(self, alert: HealthAlert) -> None:
        """Notify all registered alert handlers."""
        for handler in self._alert_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(alert)
                else:
                    handler(alert)
            except Exception as e:
                logger.error(f"Error in alert handler: {e}")

    async def _store_health_metrics(
        self, extension_id: str, health_data: Dict[str, Any]
    ) -> None:
        """Store health metrics."""
        with self._lock:
            if extension_id not in self.health_data:
                self.health_data[extension_id] = []

            # Convert health data to metrics
            timestamp = time.time()

            for key, value in health_data.items():
                if isinstance(value, (int, float)):
                    metric = HealthMetric(
                        name=key,
                        value=float(value),
                        unit="",
                        timestamp=timestamp,
                        tags={"extension_id": extension_id},
                    )
                    self.health_data[extension_id].append(metric)

            # Limit metrics count
            if len(self.health_data[extension_id]) > self.max_metrics:
                self.health_data[extension_id] = self.health_data[extension_id][
                    -self.max_metrics :
                ]

            # Update health status
            overall_status = health_data.get("overall_status", HealthStatus.UNKNOWN)
            self.health_status[extension_id] = overall_status

    def _calculate_overall_status(self, health_data: Dict[str, Any]) -> HealthStatus:
        """Calculate overall health status."""
        if not health_data:
            return HealthStatus.UNKNOWN

        error_count = 0
        warning_count = 0

        for key, value in health_data.items():
            if isinstance(value, dict) and "status" in value:
                status = value["status"]
                if status == "error":
                    error_count += 1
                elif status == "warning":
                    warning_count += 1

        if error_count > 0:
            return HealthStatus.ERROR
        elif warning_count > 0:
            return HealthStatus.WARNING
        else:
            return HealthStatus.HEALTHY

    async def _cleanup_old_data(self) -> None:
        """Clean up old health data."""
        cutoff_time = time.time() - (7 * 24 * 3600)  # 7 days

        with self._lock:
            for extension_id, metrics in self.health_data.items():
                # Remove old metrics
                self.health_data[extension_id] = [
                    metric for metric in metrics if metric.timestamp >= cutoff_time
                ]

            # Remove resolved alerts older than 24 hours
            current_time = time.time()
            for alert_id, alert in list(self.alerts.items()):
                if (
                    alert.resolved
                    and alert.resolved_at
                    and current_time - alert.resolved_at > 24 * 3600
                ):
                    del self.alerts[alert_id]

    async def _load_health_data(self) -> None:
        """Load existing health data from storage."""
        # This would typically load from a database
        # For now, initialize with empty data
        self.health_data = {}
        self.alerts = {}
        self.health_status = {}
        logger.info("Loaded health data from storage")

    def _setup_default_health_checks(self) -> None:
        """Setup default health checks."""

        # Extension process check
        def check_extension_process():
            return {"status": "healthy", "description": "Extension process is running"}

        self.register_health_check("process", check_extension_process)

        # Memory usage check
        def check_memory_usage():
            memory = psutil.virtual_memory()
            return {
                "status": "healthy" if memory.percent < 90 else "warning",
                "memory_percent": memory.percent,
                "available_memory": memory.available,
                "total_memory": memory.total,
            }

        self.register_health_check("memory", check_memory_usage)

        # CPU usage check
        def check_cpu_usage():
            cpu_percent = psutil.cpu_percent(interval=1)
            return {
                "status": "healthy" if cpu_percent < 80 else "warning",
                "cpu_percent": cpu_percent,
            }

        self.register_health_check("cpu", check_cpu_usage)
