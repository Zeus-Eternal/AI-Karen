"""
Extension health debugging interface with detailed monitoring and diagnostics.
Provides comprehensive health information for troubleshooting extension issues.
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import json

logger = logging.getLogger(__name__)

class HealthStatus(Enum):
    """Health status enumeration."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"
    RECOVERING = "recovering"

@dataclass
class HealthMetric:
    """Individual health metric."""
    name: str
    value: Any
    status: HealthStatus
    threshold: Optional[float] = None
    unit: Optional[str] = None
    description: Optional[str] = None
    last_updated: datetime = None

    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = datetime.utcnow()

@dataclass
class ExtensionHealthReport:
    """Comprehensive health report for an extension."""
    extension_name: str
    overall_status: HealthStatus
    metrics: List[HealthMetric]
    error_history: List[Dict[str, Any]]
    performance_stats: Dict[str, Any]
    dependencies: Dict[str, HealthStatus]
    last_check: datetime
    uptime: timedelta
    recovery_info: Optional[Dict[str, Any]] = None

class ExtensionHealthDebugger:
    """Advanced health debugging interface for extensions."""

    def __init__(self, extension_manager=None, health_monitor=None):
        self.extension_manager = extension_manager
        self.health_monitor = health_monitor
        self.health_history: Dict[str, List[HealthMetric]] = {}
        self.performance_baselines: Dict[str, Dict[str, float]] = {}
        self.alert_thresholds: Dict[str, Dict[str, float]] = {}
        self._initialize_thresholds()

    def _initialize_thresholds(self):
        """Initialize default health thresholds."""
        self.alert_thresholds = {
            "response_time": {"warning": 1000, "critical": 5000},  # milliseconds
            "error_rate": {"warning": 0.05, "critical": 0.15},    # percentage
            "memory_usage": {"warning": 0.8, "critical": 0.95},   # percentage
            "cpu_usage": {"warning": 0.7, "critical": 0.9},       # percentage
            "failure_count": {"warning": 3, "critical": 10}       # count
        }

    async def get_comprehensive_health_report(
        self, 
        extension_name: Optional[str] = None
    ) -> Dict[str, ExtensionHealthReport]:
        """Get comprehensive health report for extensions."""
        try:
            reports = {}
            
            if extension_name:
                # Get report for specific extension
                report = await self._generate_extension_health_report(extension_name)
                if report:
                    reports[extension_name] = report
            else:
                # Get reports for all extensions
                if self.extension_manager:
                    extensions = self.extension_manager.registry.get_all_extensions()
                    for name in extensions.keys():
                        report = await self._generate_extension_health_report(name)
                        if report:
                            reports[name] = report
            
            return reports
            
        except Exception as e:
            logger.error(f"Error generating health reports: {e}")
            return {}

    async def _generate_extension_health_report(
        self, 
        extension_name: str
    ) -> Optional[ExtensionHealthReport]:
        """Generate detailed health report for specific extension."""
        try:
            # Collect health metrics
            metrics = await self._collect_health_metrics(extension_name)
            
            # Get error history
            error_history = self._get_error_history(extension_name)
            
            # Calculate performance stats
            performance_stats = await self._calculate_performance_stats(extension_name)
            
            # Check dependencies
            dependencies = await self._check_dependencies(extension_name)
            
            # Determine overall status
            overall_status = self._determine_overall_status(metrics, error_history)
            
            # Calculate uptime
            uptime = self._calculate_uptime(extension_name)
            
            # Get recovery information
            recovery_info = self._get_recovery_info(extension_name)
            
            report = ExtensionHealthReport(
                extension_name=extension_name,
                overall_status=overall_status,
                metrics=metrics,
                error_history=error_history,
                performance_stats=performance_stats,
                dependencies=dependencies,
                last_check=datetime.utcnow(),
                uptime=uptime,
                recovery_info=recovery_info
            )
            
            # Store in history
            self._store_health_history(extension_name, metrics)
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating health report for {extension_name}: {e}")
            return None

    async def _collect_health_metrics(self, extension_name: str) -> List[HealthMetric]:
        """Collect detailed health metrics for extension."""
        metrics = []
        
        try:
            # Response time metric
            response_time = await self._measure_response_time(extension_name)
            metrics.append(HealthMetric(
                name="response_time",
                value=response_time,
                status=self._evaluate_metric_status("response_time", response_time),
                threshold=self.alert_thresholds["response_time"]["warning"],
                unit="ms",
                description="Average API response time"
            ))
            
            # Error rate metric
            error_rate = await self._calculate_error_rate(extension_name)
            metrics.append(HealthMetric(
                name="error_rate",
                value=error_rate,
                status=self._evaluate_metric_status("error_rate", error_rate),
                threshold=self.alert_thresholds["error_rate"]["warning"],
                unit="%",
                description="Error rate over last hour"
            ))
            
            # Memory usage metric
            memory_usage = await self._get_memory_usage(extension_name)
            metrics.append(HealthMetric(
                name="memory_usage",
                value=memory_usage,
                status=self._evaluate_metric_status("memory_usage", memory_usage),
                threshold=self.alert_thresholds["memory_usage"]["warning"],
                unit="%",
                description="Memory usage percentage"
            ))
            
            # Active connections metric
            active_connections = await self._get_active_connections(extension_name)
            metrics.append(HealthMetric(
                name="active_connections",
                value=active_connections,
                status=HealthStatus.HEALTHY if active_connections >= 0 else HealthStatus.UNKNOWN,
                unit="count",
                description="Number of active connections"
            ))
            
            # Background tasks metric
            background_tasks = await self._get_background_task_count(extension_name)
            metrics.append(HealthMetric(
                name="background_tasks",
                value=background_tasks,
                status=HealthStatus.HEALTHY if background_tasks >= 0 else HealthStatus.UNKNOWN,
                unit="count",
                description="Number of active background tasks"
            ))
            
        except Exception as e:
            logger.error(f"Error collecting metrics for {extension_name}: {e}")
            # Add error metric
            metrics.append(HealthMetric(
                name="collection_error",
                value=str(e),
                status=HealthStatus.UNHEALTHY,
                description="Error collecting metrics"
            ))
        
        return metrics

    async def _measure_response_time(self, extension_name: str) -> float:
        """Measure average response time for extension."""
        try:
            # This would integrate with actual extension endpoints
            # For now, return mock data based on health monitor
            if self.health_monitor and hasattr(self.health_monitor, 'get_response_time'):
                return await self.health_monitor.get_response_time(extension_name)
            
            # Mock response time
            import random
            return random.uniform(50, 500)  # 50-500ms
            
        except Exception as e:
            logger.error(f"Error measuring response time for {extension_name}: {e}")
            return -1

    async def _calculate_error_rate(self, extension_name: str) -> float:
        """Calculate error rate for extension."""
        try:
            # This would integrate with actual error tracking
            # For now, return mock data
            if self.health_monitor and hasattr(self.health_monitor, 'get_error_rate'):
                return await self.health_monitor.get_error_rate(extension_name)
            
            # Mock error rate
            import random
            return random.uniform(0, 0.1)  # 0-10% error rate
            
        except Exception as e:
            logger.error(f"Error calculating error rate for {extension_name}: {e}")
            return -1

    async def _get_memory_usage(self, extension_name: str) -> float:
        """Get memory usage for extension."""
        try:
            # This would integrate with actual memory monitoring
            # For now, return mock data
            import random
            return random.uniform(0.3, 0.8)  # 30-80% memory usage
            
        except Exception as e:
            logger.error(f"Error getting memory usage for {extension_name}: {e}")
            return -1

    async def _get_active_connections(self, extension_name: str) -> int:
        """Get number of active connections for extension."""
        try:
            # This would integrate with actual connection monitoring
            # For now, return mock data
            import random
            return random.randint(0, 50)
            
        except Exception as e:
            logger.error(f"Error getting active connections for {extension_name}: {e}")
            return -1

    async def _get_background_task_count(self, extension_name: str) -> int:
        """Get number of background tasks for extension."""
        try:
            # This would integrate with actual task monitoring
            # For now, return mock data
            import random
            return random.randint(0, 10)
            
        except Exception as e:
            logger.error(f"Error getting background task count for {extension_name}: {e}")
            return -1

    def _get_error_history(self, extension_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent error history for extension."""
        try:
            # This would integrate with actual error logging
            # For now, return mock error history
            errors = []
            for i in range(min(limit, 3)):  # Mock 0-3 recent errors
                error = {
                    "timestamp": (datetime.utcnow() - timedelta(hours=i)).isoformat(),
                    "error_type": "AuthenticationError" if i % 2 == 0 else "ServiceUnavailable",
                    "message": f"Mock error {i} for {extension_name}",
                    "severity": "warning" if i % 2 == 0 else "error",
                    "resolved": i > 0
                }
                errors.append(error)
            
            return errors
            
        except Exception as e:
            logger.error(f"Error getting error history for {extension_name}: {e}")
            return []

    async def _calculate_performance_stats(self, extension_name: str) -> Dict[str, Any]:
        """Calculate performance statistics for extension."""
        try:
            # This would integrate with actual performance monitoring
            # For now, return mock performance stats
            import random
            
            stats = {
                "requests_per_minute": random.randint(10, 100),
                "average_response_time": random.uniform(100, 800),
                "p95_response_time": random.uniform(500, 1500),
                "p99_response_time": random.uniform(1000, 3000),
                "success_rate": random.uniform(0.85, 0.99),
                "throughput_mbps": random.uniform(1, 50),
                "concurrent_users": random.randint(1, 25)
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error calculating performance stats for {extension_name}: {e}")
            return {}

    async def _check_dependencies(self, extension_name: str) -> Dict[str, HealthStatus]:
        """Check health status of extension dependencies."""
        try:
            # This would check actual dependencies
            # For now, return mock dependency status
            dependencies = {
                "database": HealthStatus.HEALTHY,
                "redis": HealthStatus.HEALTHY,
                "external_api": HealthStatus.DEGRADED,
                "file_system": HealthStatus.HEALTHY
            }
            
            return dependencies
            
        except Exception as e:
            logger.error(f"Error checking dependencies for {extension_name}: {e}")
            return {}

    def _determine_overall_status(
        self, 
        metrics: List[HealthMetric], 
        error_history: List[Dict[str, Any]]
    ) -> HealthStatus:
        """Determine overall health status based on metrics and errors."""
        try:
            # Count unhealthy metrics
            unhealthy_count = sum(1 for m in metrics if m.status == HealthStatus.UNHEALTHY)
            degraded_count = sum(1 for m in metrics if m.status == HealthStatus.DEGRADED)
            
            # Check recent errors
            recent_errors = [e for e in error_history 
                           if not e.get("resolved", False) and 
                           datetime.fromisoformat(e["timestamp"]) > datetime.utcnow() - timedelta(hours=1)]
            
            # Determine status
            if unhealthy_count > 0 or len(recent_errors) > 2:
                return HealthStatus.UNHEALTHY
            elif degraded_count > 0 or len(recent_errors) > 0:
                return HealthStatus.DEGRADED
            else:
                return HealthStatus.HEALTHY
                
        except Exception as e:
            logger.error(f"Error determining overall status: {e}")
            return HealthStatus.UNKNOWN

    def _calculate_uptime(self, extension_name: str) -> timedelta:
        """Calculate uptime for extension."""
        try:
            # This would track actual uptime
            # For now, return mock uptime
            import random
            hours = random.randint(1, 720)  # 1 hour to 30 days
            return timedelta(hours=hours)
            
        except Exception as e:
            logger.error(f"Error calculating uptime for {extension_name}: {e}")
            return timedelta(0)

    def _get_recovery_info(self, extension_name: str) -> Optional[Dict[str, Any]]:
        """Get recovery information for extension."""
        try:
            # This would integrate with actual recovery tracking
            # For now, return mock recovery info
            return {
                "last_recovery_attempt": (datetime.utcnow() - timedelta(hours=2)).isoformat(),
                "recovery_success_rate": 0.85,
                "automatic_recovery_enabled": True,
                "recovery_strategies": ["restart", "clear_cache", "reset_connections"]
            }
            
        except Exception as e:
            logger.error(f"Error getting recovery info for {extension_name}: {e}")
            return None

    def _evaluate_metric_status(self, metric_name: str, value: float) -> HealthStatus:
        """Evaluate health status based on metric value and thresholds."""
        try:
            if metric_name not in self.alert_thresholds or value < 0:
                return HealthStatus.UNKNOWN
            
            thresholds = self.alert_thresholds[metric_name]
            
            if value >= thresholds["critical"]:
                return HealthStatus.UNHEALTHY
            elif value >= thresholds["warning"]:
                return HealthStatus.DEGRADED
            else:
                return HealthStatus.HEALTHY
                
        except Exception as e:
            logger.error(f"Error evaluating metric status for {metric_name}: {e}")
            return HealthStatus.UNKNOWN

    def _store_health_history(self, extension_name: str, metrics: List[HealthMetric]):
        """Store health metrics in history for trend analysis."""
        try:
            if extension_name not in self.health_history:
                self.health_history[extension_name] = []
            
            # Store metrics with timestamp
            for metric in metrics:
                self.health_history[extension_name].append(metric)
            
            # Keep only last 100 entries per extension
            self.health_history[extension_name] = self.health_history[extension_name][-100:]
            
        except Exception as e:
            logger.error(f"Error storing health history for {extension_name}: {e}")

    def get_health_trends(self, extension_name: str, hours: int = 24) -> Dict[str, List[Dict[str, Any]]]:
        """Get health trends for extension over specified time period."""
        try:
            if extension_name not in self.health_history:
                return {}
            
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            recent_metrics = [
                m for m in self.health_history[extension_name]
                if m.last_updated > cutoff_time
            ]
            
            # Group by metric name
            trends = {}
            for metric in recent_metrics:
                if metric.name not in trends:
                    trends[metric.name] = []
                
                trends[metric.name].append({
                    "timestamp": metric.last_updated.isoformat(),
                    "value": metric.value,
                    "status": metric.status.value
                })
            
            return trends
            
        except Exception as e:
            logger.error(f"Error getting health trends for {extension_name}: {e}")
            return {}

    def export_health_report(self, reports: Dict[str, ExtensionHealthReport]) -> str:
        """Export health reports to JSON format."""
        try:
            export_data = {}
            for name, report in reports.items():
                export_data[name] = {
                    "extension_name": report.extension_name,
                    "overall_status": report.overall_status.value,
                    "metrics": [asdict(m) for m in report.metrics],
                    "error_history": report.error_history,
                    "performance_stats": report.performance_stats,
                    "dependencies": {k: v.value for k, v in report.dependencies.items()},
                    "last_check": report.last_check.isoformat(),
                    "uptime_hours": report.uptime.total_seconds() / 3600,
                    "recovery_info": report.recovery_info
                }
            
            return json.dumps(export_data, indent=2, default=str)
            
        except Exception as e:
            logger.error(f"Error exporting health report: {e}")
            return "{}"