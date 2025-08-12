# mypy: ignore-errors
"""
Health Monitoring System for AI Karen Engine Integration.

This module provides comprehensive health monitoring and service discovery
for all integrated backend services.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union

logger = logging.getLogger(__name__)

try:
    from prometheus_client import Counter, Gauge, Histogram

    from ai_karen_engine.integrations.llm_utils import PROM_REGISTRY

    _PROM_ENABLED = True
except Exception:  # pragma: no cover - optional dependency

    class _DummyMetric:
        def labels(self, **_kwargs):  # type: ignore[override]
            return self

        def inc(self, *_args, **_kwargs) -> None:  # type: ignore[override]
            pass

        def observe(self, *_args, **_kwargs) -> None:  # type: ignore[override]
            pass

        def set(self, *_args, **_kwargs) -> None:  # type: ignore[override]
            pass

    Counter = Gauge = Histogram = _DummyMetric  # type: ignore
    PROM_REGISTRY = None  # type: ignore
    _PROM_ENABLED = False


class HealthStatus(str, Enum):
    """Health status enumeration."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthCheck:
    """Health check definition."""

    name: str
    check_function: Callable
    interval: int = 30  # seconds
    timeout: int = 5  # seconds
    retries: int = 3
    critical: bool = True
    tags: List[str] = field(default_factory=list)


@dataclass
class HealthResult:
    """Health check result."""

    name: str
    status: HealthStatus
    message: str
    timestamp: datetime
    response_time: float
    details: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


@dataclass
class ServiceHealth:
    """Service health information."""

    service_name: str
    status: HealthStatus
    last_check: datetime
    checks: List[HealthResult] = field(default_factory=list)
    uptime: float = 0.0
    error_count: int = 0
    success_count: int = 0


class HealthMonitor:
    """
    Comprehensive health monitoring system for AI Karen services.

    Monitors service health, performs periodic checks, and provides
    alerting and reporting capabilities.
    """

    def __init__(self):
        self._checks: Dict[str, HealthCheck] = {}
        self._results: Dict[str, List[HealthResult]] = {}
        self._service_health: Dict[str, ServiceHealth] = {}
        self._monitoring_tasks: Dict[str, asyncio.Task] = {}
        self._is_monitoring = False
        self._alert_callbacks: List[Callable] = []
        self._metrics = {
            "total_checks": 0,
            "successful_checks": 0,
            "failed_checks": 0,
            "average_response_time": 0.0,
            "services_healthy": 0,
            "services_degraded": 0,
            "services_unhealthy": 0,
        }
        # Per-check metrics for latency and availability
        self._check_metrics: Dict[str, Dict[str, float]] = {}

        if _PROM_ENABLED:
            self._latency_metric = Histogram(
                "health_check_latency_seconds",
                "Latency of health checks",
                ["check"],
                registry=PROM_REGISTRY,
            )
            self._availability_metric = Gauge(
                "health_check_availability",
                "Availability percentage for health checks",
                ["check"],
                registry=PROM_REGISTRY,
            )
            self._status_metric = Counter(
                "health_check_status_total",
                "Health check results by status",
                ["check", "status"],
                registry=PROM_REGISTRY,
            )
        else:
            dummy = Counter()
            self._latency_metric = dummy  # type: ignore[assignment]
            self._availability_metric = dummy  # type: ignore[assignment]
            self._status_metric = dummy  # type: ignore[assignment]

    def register_health_check(
        self,
        name: str,
        check_function: Callable,
        interval: int = 30,
        timeout: int = 5,
        retries: int = 3,
        critical: bool = True,
        tags: Optional[List[str]] = None,
    ) -> None:
        """Register a health check."""
        self._checks[name] = HealthCheck(
            name=name,
            check_function=check_function,
            interval=interval,
            timeout=timeout,
            retries=retries,
            critical=critical,
            tags=tags or [],
        )

        # Initialize results list
        if name not in self._results:
            self._results[name] = []

        if name not in self._check_metrics:
            self._check_metrics[name] = {
                "total": 0,
                "success": 0,
                "failure": 0,
                "avg_latency": 0.0,
                "availability": 0.0,
            }

        logger.info(f"Registered health check: {name}")

    async def perform_health_check(self, name: str) -> HealthResult:
        """Perform a single health check."""
        if name not in self._checks:
            raise ValueError(f"Health check {name} not registered")

        check = self._checks[name]
        start_time = time.time()

        for attempt in range(check.retries):
            try:
                # Perform the health check with timeout
                result = await asyncio.wait_for(
                    check.check_function(), timeout=check.timeout
                )

                response_time = time.time() - start_time

                # Determine status based on result
                if isinstance(result, dict):
                    status = HealthStatus(result.get("status", HealthStatus.HEALTHY))
                    message = result.get("message", "Health check passed")
                    details = result.get("details", {})
                elif isinstance(result, bool):
                    status = HealthStatus.HEALTHY if result else HealthStatus.UNHEALTHY
                    message = "Health check passed" if result else "Health check failed"
                    details = {}
                else:
                    status = HealthStatus.HEALTHY
                    message = str(result)
                    details = {}

                health_result = HealthResult(
                    name=name,
                    status=status,
                    message=message,
                    timestamp=datetime.utcnow(),
                    response_time=response_time,
                    details=details,
                )

                # Update metrics
                self._metrics["total_checks"] += 1
                if status == HealthStatus.HEALTHY:
                    self._metrics["successful_checks"] += 1
                else:
                    self._metrics["failed_checks"] += 1

                # Update average response time
                total_checks = self._metrics["total_checks"]
                current_avg = self._metrics["average_response_time"]
                self._metrics["average_response_time"] = (
                    current_avg * (total_checks - 1) + response_time
                ) / total_checks

                # Per-check metrics
                cm = self._check_metrics[name]
                cm["total"] += 1
                if status == HealthStatus.HEALTHY:
                    cm["success"] += 1
                else:
                    cm["failure"] += 1
                cm["avg_latency"] = (
                    cm["avg_latency"] * (cm["total"] - 1) + response_time
                ) / cm["total"]

                # Prometheus metrics
                self._latency_metric.labels(check=name).observe(response_time)
                self._status_metric.labels(check=name, status=status.value).inc()

                return health_result

            except asyncio.TimeoutError:
                if attempt == check.retries - 1:
                    return HealthResult(
                        name=name,
                        status=HealthStatus.UNHEALTHY,
                        message=f"Health check timed out after {check.timeout}s",
                        timestamp=datetime.utcnow(),
                        response_time=time.time() - start_time,
                        error="Timeout",
                    )
                continue

            except Exception as e:
                if attempt == check.retries - 1:
                    return HealthResult(
                        name=name,
                        status=HealthStatus.UNHEALTHY,
                        message=f"Health check failed: {str(e)}",
                        timestamp=datetime.utcnow(),
                        response_time=time.time() - start_time,
                        error=str(e),
                    )
                continue

        # This should not be reached, but just in case
        return HealthResult(
            name=name,
            status=HealthStatus.UNKNOWN,
            message="Unknown health check result",
            timestamp=datetime.utcnow(),
            response_time=time.time() - start_time,
            error="Unknown error",
        )

    async def check_all_services(self) -> Dict[str, HealthResult]:
        """Perform health checks on all registered services."""
        results = {}

        # Perform all checks concurrently
        tasks = []
        for name in self._checks:
            task = asyncio.create_task(self.perform_health_check(name))
            tasks.append((name, task))

        # Wait for all checks to complete
        for name, task in tasks:
            try:
                result = await task
                results[name] = result

                # Store result
                self._results[name].append(result)

                # Keep only last 100 results per check
                if len(self._results[name]) > 100:
                    self._results[name] = self._results[name][-100:]

                # Update service health
                self._update_service_health(name, result)

            except Exception as e:
                logger.error(f"Error performing health check {name}: {e}")
                results[name] = HealthResult(
                    name=name,
                    status=HealthStatus.UNHEALTHY,
                    message=f"Health check error: {str(e)}",
                    timestamp=datetime.utcnow(),
                    response_time=0.0,
                    error=str(e),
                )

        # Update overall metrics
        self._update_overall_metrics()

        # Check for alerts
        await self._check_alerts(results)

        return results

    def _update_service_health(self, name: str, result: HealthResult) -> None:
        """Update service health information."""
        if name not in self._service_health:
            self._service_health[name] = ServiceHealth(
                service_name=name, status=result.status, last_check=result.timestamp
            )

        service_health = self._service_health[name]
        service_health.status = result.status
        service_health.last_check = result.timestamp
        service_health.checks.append(result)

        # Keep only last 50 checks
        if len(service_health.checks) > 50:
            service_health.checks = service_health.checks[-50:]

        # Update counters
        if result.status == HealthStatus.HEALTHY:
            service_health.success_count += 1
        else:
            service_health.error_count += 1

        # Calculate uptime (percentage of successful checks in last 24 hours)
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        recent_checks = [
            check for check in service_health.checks if check.timestamp > cutoff_time
        ]

        if recent_checks:
            successful_checks = sum(
                1 for check in recent_checks if check.status == HealthStatus.HEALTHY
            )
            service_health.uptime = (successful_checks / len(recent_checks)) * 100
            self._check_metrics[name]["availability"] = service_health.uptime
            self._availability_metric.labels(check=name).set(service_health.uptime)

    def _update_overall_metrics(self) -> None:
        """Update overall health metrics."""
        healthy_count = 0
        degraded_count = 0
        unhealthy_count = 0

        for service_health in self._service_health.values():
            if service_health.status == HealthStatus.HEALTHY:
                healthy_count += 1
            elif service_health.status == HealthStatus.DEGRADED:
                degraded_count += 1
            else:
                unhealthy_count += 1

        self._metrics["services_healthy"] = healthy_count
        self._metrics["services_degraded"] = degraded_count
        self._metrics["services_unhealthy"] = unhealthy_count

    async def _check_alerts(self, results: Dict[str, HealthResult]) -> None:
        """Check for alert conditions and notify callbacks."""
        alerts = []

        for name, result in results.items():
            check = self._checks[name]

            # Critical service is unhealthy
            if check.critical and result.status == HealthStatus.UNHEALTHY:
                alerts.append(
                    {
                        "type": "critical_service_down",
                        "service": name,
                        "message": f"Critical service {name} is unhealthy: {result.message}",
                        "timestamp": result.timestamp,
                        "details": result.details,
                    }
                )

            # Service has been degraded for too long
            service_health = self._service_health.get(name)
            if service_health and service_health.uptime < 90:  # Less than 90% uptime
                alerts.append(
                    {
                        "type": "low_uptime",
                        "service": name,
                        "message": f"Service {name} has low uptime: {service_health.uptime:.1f}%",
                        "timestamp": datetime.utcnow(),
                        "uptime": service_health.uptime,
                    }
                )

        # Notify alert callbacks
        for alert in alerts:
            for callback in self._alert_callbacks:
                try:
                    await callback(alert)
                except Exception as e:
                    logger.error(f"Alert callback error: {e}")

    def start_monitoring(self) -> None:
        """Start continuous health monitoring."""
        if self._is_monitoring:
            logger.warning("Health monitoring already running")
            return

        self._is_monitoring = True

        # Start monitoring tasks for each check
        for name, check in self._checks.items():
            task = asyncio.create_task(self._monitoring_loop(name, check))
            self._monitoring_tasks[name] = task

        logger.info(f"Started health monitoring for {len(self._checks)} services")

    async def _monitoring_loop(self, name: str, check: HealthCheck) -> None:
        """Continuous monitoring loop for a specific health check."""
        while self._is_monitoring:
            try:
                await self.perform_health_check(name)
                await asyncio.sleep(check.interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop for {name}: {e}")
                await asyncio.sleep(check.interval)

    def stop_monitoring(self) -> None:
        """Stop continuous health monitoring."""
        if not self._is_monitoring:
            return

        self._is_monitoring = False

        # Cancel all monitoring tasks
        for task in self._monitoring_tasks.values():
            task.cancel()

        self._monitoring_tasks.clear()
        logger.info("Stopped health monitoring")

    def add_alert_callback(self, callback: Callable) -> None:
        """Add an alert callback function."""
        self._alert_callbacks.append(callback)

    def remove_alert_callback(self, callback: Callable) -> None:
        """Remove an alert callback function."""
        if callback in self._alert_callbacks:
            self._alert_callbacks.remove(callback)

    def get_service_health(
        self, service_name: Optional[str] = None
    ) -> Union[ServiceHealth, Dict[str, ServiceHealth]]:
        """Get health information for a service or all services."""
        if service_name:
            return self._service_health.get(service_name)
        return self._service_health.copy()

    def get_health_summary(self) -> Dict[str, Any]:
        """Get overall health summary."""
        total_services = len(self._service_health)
        healthy_services = sum(
            1
            for health in self._service_health.values()
            if health.status == HealthStatus.HEALTHY
        )

        overall_status = HealthStatus.HEALTHY
        if healthy_services == 0:
            overall_status = HealthStatus.UNHEALTHY
        elif healthy_services < total_services:
            overall_status = HealthStatus.DEGRADED

        return {
            "overall_status": overall_status.value,
            "total_services": total_services,
            "healthy_services": healthy_services,
            "degraded_services": self._metrics["services_degraded"],
            "unhealthy_services": self._metrics["services_unhealthy"],
            "average_uptime": sum(
                health.uptime for health in self._service_health.values()
            )
            / total_services
            if total_services > 0
            else 0,
            "last_check": max(
                (health.last_check for health in self._service_health.values()),
                default=datetime.utcnow(),
            ).isoformat(),
            "metrics": self._metrics,
        }

    def get_health_history(
        self, service_name: str, hours: int = 24
    ) -> List[HealthResult]:
        """Get health check history for a service."""
        if service_name not in self._results:
            return []

        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        return [
            result
            for result in self._results[service_name]
            if result.timestamp > cutoff_time
        ]

    def get_metrics(self) -> Dict[str, Any]:
        """Get health monitoring metrics."""
        metrics = self._metrics.copy()
        metrics["checks"] = {
            name: data.copy() for name, data in self._check_metrics.items()
        }
        return metrics


# Global health monitor instance
_health_monitor: Optional[HealthMonitor] = None


def get_health_monitor() -> HealthMonitor:
    """Get the global health monitor instance."""
    global _health_monitor
    if _health_monitor is None:
        _health_monitor = HealthMonitor()
    return _health_monitor


async def setup_default_health_checks() -> None:
    """Set up default health checks for AI Karen services."""
    monitor = get_health_monitor()

    # Database health check
    async def check_database():
        try:
            from ai_karen_engine.database.client import get_db_client

            client = get_db_client()
            # Simple query to check database connectivity
            await client.execute("SELECT 1")
            return {"status": "healthy", "message": "Database connection OK"}
        except Exception as e:
            return {"status": "unhealthy", "message": f"Database error: {str(e)}"}

    # Redis health check
    async def check_redis():
        try:
            from ai_karen_engine.clients.database.redis_client import get_redis_client

            client = get_redis_client()
            await client.ping()
            return {"status": "healthy", "message": "Redis connection OK"}
        except Exception as e:
            return {"status": "unhealthy", "message": f"Redis error: {str(e)}"}

    # Vector database health check
    async def check_vector_db():
        try:
            from ai_karen_engine.clients.database.milvus_client import get_milvus_client

            client = get_milvus_client()
            # Check if client is connected
            if client.is_connected():
                return {"status": "healthy", "message": "Vector DB connection OK"}
            else:
                return {"status": "unhealthy", "message": "Vector DB not connected"}
        except Exception as e:
            return {"status": "unhealthy", "message": f"Vector DB error: {str(e)}"}

    # Service health checks
    async def check_ai_orchestrator():
        try:
            from ai_karen_engine.core.service_registry import get_ai_orchestrator

            service = await get_ai_orchestrator()
            if hasattr(service, "health_check"):
                return await service.health_check()
            return {"status": "healthy", "message": "AI Orchestrator OK"}
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"AI Orchestrator error: {str(e)}",
            }

    async def check_memory_service():
        try:
            from ai_karen_engine.core.service_registry import get_memory_service

            service = await get_memory_service()
            if hasattr(service, "health_check"):
                return await service.health_check()
            return {"status": "healthy", "message": "Memory Service OK"}
        except Exception as e:
            return {"status": "unhealthy", "message": f"Memory Service error: {str(e)}"}

    async def check_extensions():
        try:
            from ai_karen_engine.extensions import get_extension_manager

            manager = get_extension_manager()
            if not manager:
                return {
                    "status": "unhealthy",
                    "message": "Extension manager not initialized",
                }
            summary = manager.get_health_summary()
            return {
                "status": summary.get("overall_status", "healthy"),
                "message": "Extension system health",
                "details": summary,
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"Extension system error: {str(e)}",
            }

    # Register health checks
    monitor.register_health_check(
        "database", check_database, interval=30, critical=True
    )
    monitor.register_health_check("redis", check_redis, interval=30, critical=True)
    monitor.register_health_check(
        "vector_db", check_vector_db, interval=60, critical=True
    )
    monitor.register_health_check(
        "ai_orchestrator", check_ai_orchestrator, interval=30, critical=True
    )
    monitor.register_health_check(
        "memory_service", check_memory_service, interval=30, critical=True
    )
    monitor.register_health_check(
        "extensions", check_extensions, interval=30, critical=False
    )

    logger.info("Default health checks configured")
