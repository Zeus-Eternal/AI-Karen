"""
Health Dashboard Service - Consolidates health data from all plugin system components.

This service:
- Collects health metrics from backend systems
- Aggregates plugin health data
- Tracks system resource usage
- Provides health history and trends
- Generates health reports
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

from ai_karen_engine.extensions.platform.core.registry.plugin_registry import get_registry
from ai_karen_engine.extensions.platform.core.host.lifecycle_manager import get_lifecycle_manager
from ai_karen_engine.extensions.platform.core.registry.state_machine import get_state_machine, ExtensionState
from ai_karen_engine.extensions.platform.core.registry.database_service import get_database_service

logger = logging.getLogger("kari.health_dashboard")


class HealthStatus(Enum):
    """Overall health status."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class SystemMetrics:
    """System resource metrics."""

    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    disk_percent: float = 0.0
    active_plugins: int = 0
    total_plugins: int = 0
    active_hooks: int = 0
    pending_operations: int = 0


@dataclass
class PluginHealthRecord:
    """Health record for a single plugin."""

    plugin_id: str
    name: str
    version: str
    backend_status: str
    frontend_status: str = "unknown"
    state_machine_state: str = "unknown"
    is_validated: bool = False
    has_errors: bool = False
    error_count: int = 0
    last_error: Optional[str] = None
    last_error_time: Optional[datetime] = None
    load_time_ms: Optional[int] = None
    memory_usage_mb: Optional[int] = None
    cpu_usage_percent: Optional[int] = None
    hooks_assigned: int = 0
    last_loaded: Optional[datetime] = None
    uptime_minutes: Optional[float] = None


@dataclass
class HealthSnapshot:
    """Point-in-time health snapshot."""

    timestamp: datetime
    overall_status: HealthStatus
    system_metrics: SystemMetrics
    plugin_health: List[PluginHealthRecord]
    database_status: HealthStatus = HealthStatus.UNKNOWN
    alerts: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class HealthTrend:
    """Health trend data for a time range."""

    period_start: datetime
    period_end: datetime
    snapshots: List[HealthSnapshot]
    avg_plugin_count: float = 0
    avg_active_count: float = 0
    error_count: int = 0
    degradation_events: int = 0


class HealthDashboardService:
    """
    Consolidates and analyzes health data from the plugin ecosystem.

    Features:
    - Real-time health monitoring
    - Historical trend analysis
    - Alert generation
    - Health status reconciliation
    - Resource usage tracking
    """

    def __init__(self):
        self._history: List[HealthSnapshot] = []
        self._max_history = 1000  # Keep last 1000 snapshots
        self._alerts: List[Dict[str, Any]] = []
        self._max_alerts = 100

        logger.info("HealthDashboardService initialized")

    async def collect_health_snapshot(self) -> HealthSnapshot:
        """
        Collect a complete health snapshot from all systems.

        Returns:
            Comprehensive health snapshot
        """
        timestamp = datetime.utcnow()

        # Collect data from all sources in parallel
        try:
            system_metrics, plugin_health, database_status = await asyncio.gather(
                self._collect_system_metrics(),
                self._collect_plugin_health(),
                self._check_database_health(),
            )
        except Exception as e:
            logger.error(f"Error collecting health data: {e}")
            system_metrics = SystemMetrics()
            plugin_health = []
            database_status = HealthStatus.UNKNOWN

        # Determine overall status
        alerts = self._generate_alerts(plugin_health, system_metrics, database_status)
        overall_status = self._determine_overall_status(
            plugin_health, system_metrics, database_status
        )

        snapshot = HealthSnapshot(
            timestamp=timestamp,
            overall_status=overall_status,
            system_metrics=system_metrics,
            plugin_health=plugin_health,
            database_status=database_status,
            alerts=alerts,
        )

        # Store in history
        self._history.append(snapshot)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history :]

        # Update alerts
        self._alerts.extend(alerts)
        if len(self._alerts) > self._max_alerts:
            self._alerts = self._alerts[-self._max_alerts :]

        logger.debug(
            f"Health snapshot collected: {overall_status.value}, "
            f"{len(plugin_health)} plugins, {len(alerts)} alerts"
        )

        return snapshot

    async def _collect_system_metrics(self) -> SystemMetrics:
        """Collect system resource metrics."""
        metrics = SystemMetrics()

        try:
            # Get plugin counts from registry
            registry = get_registry()
            discovered = registry.list_discovered()
            extensions = registry.list_extensions()

            metrics.total_plugins = len(discovered)
            metrics.active_plugins = sum(
                1
                for e in extensions
                if hasattr(e, "status") and e.status.value == "active"
            )

            # Get lifecycle state counts
            try:
                lifecycle = get_lifecycle_manager()
                all_states = lifecycle.get_all_lifecycle_states()

                transient_states = [
                    "installing",
                    "uninstalling",
                    "updating",
                    "restoring",
                    "enabling",
                    "disabling",
                    "downloading",
                    "extracting",
                    "validating",
                    "loading",
                    "unloading",
                ]

                metrics.pending_operations = sum(
                    1 for state in all_states.values() if state in transient_states
                )
            except Exception:
                pass

            # Collect resource usage from plugin health
            plugin_health = await self._collect_plugin_health()
            if plugin_health:
                metrics.cpu_percent = sum(
                    p.cpu_usage_percent or 0 for p in plugin_health
                ) / max(len(plugin_health), 1)

                metrics.memory_percent = (
                    sum(p.memory_usage_mb or 0 for p in plugin_health)
                    / max(len(plugin_health), 1)
                    / 256
                )  # Normalize to percentage

        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")

        return metrics

    async def _collect_plugin_health(self) -> List[PluginHealthRecord]:
        """Collect health data for all plugins."""
        health_records = []

        try:
            registry = get_registry()
            state_machine = get_state_machine()
            discovered = registry.list_discovered()

            for plugin_id in discovered:
                try:
                    # Get metadata
                    metadata = registry.get_metadata(plugin_id)
                    extension = registry.get_extension(plugin_id)

                    # Get state machine state
                    sm_state = state_machine.get_state(plugin_id)
                    sm_state_value = sm_state.value if sm_state else "unknown"

                    # Build health record
                    record = PluginHealthRecord(
                        plugin_id=plugin_id,
                        name=metadata.display_name if metadata else plugin_id,
                        version=metadata.version if metadata else "unknown",
                        backend_status=extension.status.value
                        if extension
                        else "unknown",
                        state_machine_state=sm_state_value,
                        is_validated=metadata.is_valid if metadata else False,
                    )

                    # Get error info from extension if available
                    if extension and hasattr(extension, "error_count"):
                        record.error_count = extension.error_count
                        record.has_errors = extension.error_count > 0
                        record.last_error = extension.error_message
                        record.last_error_time = extension.last_error_at

                    # Get performance metrics
                    if extension and hasattr(extension, "load_time_ms"):
                        record.load_time_ms = extension.load_time_ms

                    if extension and hasattr(extension, "memory_usage_mb"):
                        record.memory_usage_mb = extension.memory_usage_mb

                    if extension and hasattr(extension, "cpu_usage_percent"):
                        record.cpu_usage_percent = extension.cpu_usage_percent

                    if extension and hasattr(extension, "loaded_at"):
                        record.last_loaded = extension.loaded_at
                        if extension.loaded_at:
                            record.uptime_minutes = (
                                datetime.utcnow() - extension.loaded_at
                            ).total_seconds() / 60

                    health_records.append(record)

                except Exception as e:
                    logger.warning(f"Failed to collect health for {plugin_id}: {e}")
                    health_records.append(
                        PluginHealthRecord(
                            plugin_id=plugin_id,
                            name=plugin_id,
                            version="unknown",
                            backend_status="error",
                            has_errors=True,
                            last_error=str(e),
                            last_error_time=datetime.utcnow(),
                        )
                    )

        except Exception as e:
            logger.error(f"Failed to collect plugin health: {e}")

        return health_records

    async def _check_database_health(self) -> HealthStatus:
        """Check database health status."""
        try:
            db_service = get_database_service()

            # Try to get extension stats
            stats = await db_service.get_extension_stats()

            if stats.get("total_extensions", 0) >= 0:
                return HealthStatus.HEALTHY
            else:
                return HealthStatus.DEGRADED

        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return HealthStatus.UNKNOWN

    def _determine_overall_status(
        self,
        plugin_health: List[PluginHealthRecord],
        system_metrics: SystemMetrics,
        database_status: HealthStatus,
    ) -> HealthStatus:
        """Determine overall system health status."""
        # Check for critical conditions
        has_critical_errors = any(
            p.backend_status == "error" and p.has_errors for p in plugin_health
        )

        if has_critical_errors:
            return HealthStatus.UNHEALTHY

        # Check for degraded conditions
        has_degraded = (
            database_status == HealthStatus.DEGRADED
            or database_status == HealthStatus.UNKNOWN
            or any(p.has_errors for p in plugin_health)
            or system_metrics.cpu_percent > 80
            or system_metrics.memory_percent > 80
        )

        if has_degraded:
            return HealthStatus.DEGRADED

        # All checks passed
        return HealthStatus.HEALTHY

    def _generate_alerts(
        self,
        plugin_health: List[PluginHealthRecord],
        system_metrics: SystemMetrics,
        database_status: HealthStatus,
    ) -> List[Dict[str, Any]]:
        """Generate health alerts based on current state."""
        alerts = []

        # Critical alerts
        for plugin in plugin_health:
            if plugin.backend_status == "error" and plugin.has_errors:
                alerts.append(
                    {
                        "severity": "critical",
                        "type": "plugin_error",
                        "plugin_id": plugin.plugin_id,
                        "message": f"Plugin '{plugin.name}' is in error state: {plugin.last_error}",
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                )

        # Warning alerts
        for plugin in plugin_health:
            if plugin.state_machine_state in ["ERROR"]:
                alerts.append(
                    {
                        "severity": "warning",
                        "type": "plugin_state_error",
                        "plugin_id": plugin.plugin_id,
                        "message": f"Plugin '{plugin.name}' state machine is in error state",
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                )

        # Resource alerts
        if system_metrics.cpu_percent > 80:
            alerts.append(
                {
                    "severity": "warning",
                    "type": "high_cpu",
                    "message": f"High CPU usage: {system_metrics.cpu_percent:.1f}%",
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )

        if system_metrics.memory_percent > 80:
            alerts.append(
                {
                    "severity": "warning",
                    "type": "high_memory",
                    "message": f"High memory usage: {system_metrics.memory_percent:.1f}%",
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )

        # Database alerts
        if database_status == HealthStatus.UNKNOWN:
            alerts.append(
                {
                    "severity": "warning",
                    "type": "database_unknown",
                    "message": "Database health status is unknown",
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )

        return alerts

    async def get_health_summary(self) -> Dict[str, Any]:
        """Get a summary of current health status."""
        snapshot = await self.collect_health_snapshot()

        return {
            "status": snapshot.overall_status.value,
            "timestamp": snapshot.timestamp.isoformat(),
            "system": {
                "total_plugins": snapshot.system_metrics.total_plugins,
                "active_plugins": snapshot.system_metrics.active_plugins,
                "pending_operations": snapshot.system_metrics.pending_operations,
                "cpu_percent": round(snapshot.system_metrics.cpu_percent, 1),
                "memory_percent": round(snapshot.system_metrics.memory_percent, 1),
            },
            "plugins": {
                "total": len(snapshot.plugin_health),
                "healthy": sum(1 for p in snapshot.plugin_health if not p.has_errors),
                "unhealthy": sum(1 for p in snapshot.plugin_health if p.has_errors),
                "by_status": self._group_by_field(
                    snapshot.plugin_health, "backend_status"
                ),
                "by_state": self._group_by_field(
                    snapshot.plugin_health, "state_machine_state"
                ),
            },
            "database": {
                "status": snapshot.database_status.value,
            },
            "alerts": {
                "total": len(snapshot.alerts),
                "critical": sum(
                    1 for a in snapshot.alerts if a.get("severity") == "critical"
                ),
                "warnings": sum(
                    1 for a in snapshot.alerts if a.get("severity") == "warning"
                ),
                "recent": snapshot.alerts[-10:],
            },
        }

    def _group_by_field(self, items: List[Any], field: str) -> Dict[str, int]:
        """Group items by a field and count."""
        groups: Dict[str, int] = {}
        for item in items:
            value = getattr(item, field, "unknown")
            groups[value] = groups.get(value, 0) + 1
        return dict(sorted(groups.items(), key=lambda x: x[1], reverse=True))

    async def get_plugin_health_history(
        self, plugin_id: str, hours: int = 24
    ) -> List[Dict[str, Any]]:
        """Get health history for a specific plugin."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)

        history = []
        for snapshot in self._history:
            if snapshot.timestamp < cutoff:
                continue

            plugin_record = next(
                (p for p in snapshot.plugin_health if p.plugin_id == plugin_id),
                None,
            )

            if plugin_record:
                history.append(
                    {
                        "timestamp": snapshot.timestamp.isoformat(),
                        "backend_status": plugin_record.backend_status,
                        "state_machine_state": plugin_record.state_machine_state,
                        "has_errors": plugin_record.has_errors,
                        "error_count": plugin_record.error_count,
                    }
                )

        return history

    async def get_health_trends(
        self, hours: int = 24, interval_minutes: int = 60
    ) -> HealthTrend:
        """Get health trends over time."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)

        # Filter snapshots within time range
        relevant = [s for s in self._history if s.timestamp >= cutoff]

        if not relevant:
            return HealthTrend(
                period_start=cutoff,
                period_end=datetime.utcnow(),
                snapshots=[],
            )

        trend = HealthTrend(
            period_start=relevant[0].timestamp,
            period_end=relevant[-1].timestamp,
            snapshots=relevant,
        )

        # Calculate metrics
        if relevant:
            trend.avg_plugin_count = sum(len(s.plugin_health) for s in relevant) / len(
                relevant
            )

            trend.avg_active_count = sum(
                len([p for p in s.plugin_health if p.backend_status == "active"])
                for s in relevant
            ) / len(relevant)

            trend.error_count = sum(
                sum(1 for p in s.plugin_health if p.has_errors) for s in relevant
            )

            trend.degradation_events = sum(
                1
                for s in relevant
                if s.overall_status in [HealthStatus.DEGRADED, HealthStatus.UNHEALTHY]
            )

        return trend

    def get_active_alerts(
        self, severity: Optional[str] = None, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get active alerts."""
        alerts = self._alerts

        if severity:
            alerts = [a for a in alerts if a.get("severity") == severity]

        return alerts[-limit:]

    def get_recent_snapshots(self, limit: int = 10) -> List[HealthSnapshot]:
        """Get recent health snapshots."""
        return self._history[-limit:]


# Singleton instance
_health_service: Optional[HealthDashboardService] = None


def get_health_service() -> HealthDashboardService:
    """Get the singleton health service instance."""
    global _health_service
    if _health_service is None:
        _health_service = HealthDashboardService()
    return _health_service
