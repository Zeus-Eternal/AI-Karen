"""
Extension Health Monitoring System

This module extends the existing health monitoring infrastructure to include
comprehensive extension service health checks, integrating with the existing
/health endpoint and database health monitoring patterns.

Requirements: 5.1, 5.2, 5.3, 5.4, 5.5
"""

import asyncio
import logging
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class ExtensionHealthStatus(str, Enum):
    """Extension health status levels"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class ExtensionHealthMetrics:
    """Health metrics for a specific extension"""
    name: str
    status: ExtensionHealthStatus
    response_time_ms: float
    last_check: datetime
    error_count: int = 0
    success_count: int = 0
    uptime_seconds: float = 0
    memory_usage_mb: float = 0
    cpu_usage_percent: float = 0
    background_tasks_active: int = 0
    background_tasks_failed: int = 0
    api_calls_per_minute: float = 0
    error: Optional[str] = None


@dataclass
class ExtensionSystemHealth:
    """Overall extension system health"""
    overall_status: ExtensionHealthStatus
    total_extensions: int
    healthy_extensions: int
    degraded_extensions: int
    unhealthy_extensions: int
    extension_metrics: Dict[str, ExtensionHealthMetrics]
    system_uptime_seconds: float
    authentication_healthy: bool
    database_healthy: bool
    background_tasks_healthy: bool
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class ExtensionHealthMonitor:
    """
    Extension health monitoring system that integrates with existing health infrastructure.
    
    This monitor tracks extension-specific health metrics and integrates with the
    existing health endpoint patterns in server/health_endpoints.py.
    """
    
    def __init__(self, extension_manager=None):
        self.extension_manager = extension_manager
        self._monitoring_active = False
        self._monitoring_task: Optional[asyncio.Task] = None
        self._health_history: List[ExtensionSystemHealth] = []
        self._max_history = 100
        self._start_time = time.time()
        
        # Health check thresholds
        self.thresholds = {
            "response_time_warning_ms": 500,
            "response_time_critical_ms": 2000,
            "error_rate_warning": 0.05,  # 5%
            "error_rate_critical": 0.15,  # 15%
            "memory_warning_mb": 100,
            "memory_critical_mb": 500,
            "cpu_warning_percent": 70,
            "cpu_critical_percent": 90
        }
    
    async def start_monitoring(self, check_interval: int = 30):
        """Start extension health monitoring"""
        self._monitoring_active = True
        self._monitoring_task = asyncio.create_task(self._monitoring_loop(check_interval))
        logger.info("Extension health monitoring started")
    
    async def stop_monitoring(self):
        """Stop extension health monitoring"""
        self._monitoring_active = False
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        logger.info("Extension health monitoring stopped")
    
    async def _monitoring_loop(self, check_interval: int):
        """Main monitoring loop"""
        while self._monitoring_active:
            try:
                health = await self.check_extension_system_health()
                self._add_to_history(health)
                
                # Update Prometheus metrics
                self.update_extension_metrics(health)
                
                # Log warnings for unhealthy extensions
                if health.overall_status != ExtensionHealthStatus.HEALTHY:
                    await self._handle_health_issues(health)
                
                await asyncio.sleep(check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in extension health monitoring loop: {e}")
                await asyncio.sleep(check_interval)
    
    async def check_extension_system_health(self) -> ExtensionSystemHealth:
        """
        Check health of the entire extension system.
        
        This method integrates with existing health check patterns and provides
        comprehensive extension system health information.
        """
        try:
            # Check if extension manager is available
            if not self.extension_manager:
                return ExtensionSystemHealth(
                    overall_status=ExtensionHealthStatus.UNKNOWN,
                    total_extensions=0,
                    healthy_extensions=0,
                    degraded_extensions=0,
                    unhealthy_extensions=0,
                    extension_metrics={},
                    system_uptime_seconds=time.time() - self._start_time,
                    authentication_healthy=False,
                    database_healthy=False,
                    background_tasks_healthy=False
                )
            
            # Get all extensions
            extensions = {}
            extension_metrics = {}
            
            try:
                extensions = self.extension_manager.registry.get_all_extensions()
            except Exception as e:
                logger.warning(f"Failed to get extensions from registry: {e}")
            
            # Check health of each extension
            for name, record in extensions.items():
                try:
                    metrics = await self._check_individual_extension_health(name, record)
                    extension_metrics[name] = metrics
                except Exception as e:
                    logger.error(f"Failed to check health for extension {name}: {e}")
                    extension_metrics[name] = ExtensionHealthMetrics(
                        name=name,
                        status=ExtensionHealthStatus.UNHEALTHY,
                        response_time_ms=0,
                        last_check=datetime.now(timezone.utc),
                        error=str(e)
                    )
            
            # Check supporting services health
            auth_healthy = await self._check_authentication_service_health()
            db_healthy = await self._check_database_health()
            bg_tasks_healthy = await self._check_background_tasks_health()
            
            # Calculate overall statistics
            total_extensions = len(extension_metrics)
            healthy_count = sum(1 for m in extension_metrics.values() 
                              if m.status == ExtensionHealthStatus.HEALTHY)
            degraded_count = sum(1 for m in extension_metrics.values() 
                               if m.status == ExtensionHealthStatus.DEGRADED)
            unhealthy_count = sum(1 for m in extension_metrics.values() 
                                if m.status == ExtensionHealthStatus.UNHEALTHY)
            
            # Determine overall status
            overall_status = self._calculate_overall_status(
                extension_metrics, auth_healthy, db_healthy, bg_tasks_healthy
            )
            
            return ExtensionSystemHealth(
                overall_status=overall_status,
                total_extensions=total_extensions,
                healthy_extensions=healthy_count,
                degraded_extensions=degraded_count,
                unhealthy_extensions=unhealthy_count,
                extension_metrics=extension_metrics,
                system_uptime_seconds=time.time() - self._start_time,
                authentication_healthy=auth_healthy,
                database_healthy=db_healthy,
                background_tasks_healthy=bg_tasks_healthy
            )
            
        except Exception as e:
            logger.error(f"Failed to check extension system health: {e}")
            return ExtensionSystemHealth(
                overall_status=ExtensionHealthStatus.UNHEALTHY,
                total_extensions=0,
                healthy_extensions=0,
                degraded_extensions=0,
                unhealthy_extensions=1,  # System itself is unhealthy
                extension_metrics={},
                system_uptime_seconds=time.time() - self._start_time,
                authentication_healthy=False,
                database_healthy=False,
                background_tasks_healthy=False
            )
    
    async def _check_individual_extension_health(self, name: str, record) -> ExtensionHealthMetrics:
        """Check health of an individual extension"""
        start_time = time.time()
        
        try:
            # Basic status check
            is_active = hasattr(record, 'status') and record.status.value == 'active'
            
            # Check if extension has health check method
            health_result = True
            if hasattr(record, 'instance') and record.instance:
                if hasattr(record.instance, 'health_check'):
                    try:
                        health_result = await record.instance.health_check()
                    except Exception as e:
                        logger.warning(f"Extension {name} health check failed: {e}")
                        health_result = False
            
            # Calculate response time
            response_time = (time.time() - start_time) * 1000
            
            # Get extension metrics if available
            error_count = getattr(record, 'error_count', 0)
            success_count = getattr(record, 'success_count', 0)
            
            # Calculate uptime
            uptime = 0
            if hasattr(record, 'loaded_at') and record.loaded_at:
                uptime = (datetime.now(timezone.utc) - record.loaded_at).total_seconds()
            
            # Get background task metrics
            bg_tasks_active = 0
            bg_tasks_failed = 0
            try:
                if hasattr(self.extension_manager, 'get_extension_background_tasks'):
                    tasks = await self.extension_manager.get_extension_background_tasks(name)
                    bg_tasks_active = len([t for t in tasks if t.get('status') == 'running'])
                    bg_tasks_failed = len([t for t in tasks if t.get('status') == 'failed'])
            except Exception:
                pass
            
            # Determine status based on various factors
            status = self._determine_extension_status(
                is_active, health_result, response_time, error_count, success_count
            )
            
            return ExtensionHealthMetrics(
                name=name,
                status=status,
                response_time_ms=response_time,
                last_check=datetime.now(timezone.utc),
                error_count=error_count,
                success_count=success_count,
                uptime_seconds=uptime,
                background_tasks_active=bg_tasks_active,
                background_tasks_failed=bg_tasks_failed,
                error=getattr(record, 'error', None)
            )
            
        except Exception as e:
            return ExtensionHealthMetrics(
                name=name,
                status=ExtensionHealthStatus.UNHEALTHY,
                response_time_ms=(time.time() - start_time) * 1000,
                last_check=datetime.now(timezone.utc),
                error=str(e)
            )
    
    def _determine_extension_status(
        self, 
        is_active: bool, 
        health_result: bool, 
        response_time: float,
        error_count: int,
        success_count: int
    ) -> ExtensionHealthStatus:
        """Determine extension status based on various health factors"""
        
        # If not active, it's unhealthy
        if not is_active:
            return ExtensionHealthStatus.UNHEALTHY
        
        # If health check failed, it's unhealthy
        if not health_result:
            return ExtensionHealthStatus.UNHEALTHY
        
        # Check response time
        if response_time > self.thresholds["response_time_critical_ms"]:
            return ExtensionHealthStatus.UNHEALTHY
        elif response_time > self.thresholds["response_time_warning_ms"]:
            return ExtensionHealthStatus.DEGRADED
        
        # Check error rate
        total_requests = error_count + success_count
        if total_requests > 0:
            error_rate = error_count / total_requests
            if error_rate > self.thresholds["error_rate_critical"]:
                return ExtensionHealthStatus.UNHEALTHY
            elif error_rate > self.thresholds["error_rate_warning"]:
                return ExtensionHealthStatus.DEGRADED
        
        return ExtensionHealthStatus.HEALTHY
    
    async def _check_authentication_service_health(self) -> bool:
        """Check authentication service health for extension APIs"""
        try:
            # Import here to avoid circular imports
            from server.security import get_extension_auth_manager
            
            auth_manager = get_extension_auth_manager()
            if not auth_manager:
                return False
            
            # Test authentication functionality
            # This is a basic check - in a real implementation, you might
            # test token generation/validation
            return True
            
        except Exception as e:
            logger.warning(f"Authentication service health check failed: {e}")
            return False
    
    async def _check_database_health(self) -> bool:
        """Check database health for extension services"""
        try:
            # Use existing database health check patterns
            from server.enhanced_database_health_monitor import get_enhanced_database_health_monitor
            
            enhanced_monitor = get_enhanced_database_health_monitor()
            if enhanced_monitor:
                health = await enhanced_monitor.get_current_health_with_extension_focus()
                return health.get("extension_service_healthy", False)
            
            # Fallback to basic database health check
            from server.database_config import get_database_config
            db_config = get_database_config()
            if db_config:
                health = await db_config.get_database_health()
                return health.get("healthy", False)
            
            return False
            
        except Exception as e:
            logger.warning(f"Database health check failed: {e}")
            return False
    
    async def _check_background_tasks_health(self) -> bool:
        """Check background tasks health for extensions"""
        try:
            if not self.extension_manager:
                return False
            
            # Check if background task system is operational
            # This would check the task scheduler, queue health, etc.
            # For now, return True if extension manager is available
            return True
            
        except Exception as e:
            logger.warning(f"Background tasks health check failed: {e}")
            return False
    
    def _calculate_overall_status(
        self,
        extension_metrics: Dict[str, ExtensionHealthMetrics],
        auth_healthy: bool,
        db_healthy: bool,
        bg_tasks_healthy: bool
    ) -> ExtensionHealthStatus:
        """Calculate overall extension system status"""
        
        # If critical services are down, system is unhealthy
        if not auth_healthy or not db_healthy:
            return ExtensionHealthStatus.UNHEALTHY
        
        # If no extensions, status depends on supporting services
        if not extension_metrics:
            return ExtensionHealthStatus.DEGRADED if bg_tasks_healthy else ExtensionHealthStatus.UNHEALTHY
        
        # Calculate extension health ratios
        total = len(extension_metrics)
        healthy = sum(1 for m in extension_metrics.values() 
                     if m.status == ExtensionHealthStatus.HEALTHY)
        unhealthy = sum(1 for m in extension_metrics.values() 
                       if m.status == ExtensionHealthStatus.UNHEALTHY)
        
        # Determine overall status based on ratios
        if unhealthy > total * 0.5:  # More than 50% unhealthy
            return ExtensionHealthStatus.UNHEALTHY
        elif healthy < total * 0.7:  # Less than 70% healthy
            return ExtensionHealthStatus.DEGRADED
        elif not bg_tasks_healthy:  # Extensions healthy but background tasks not
            return ExtensionHealthStatus.DEGRADED
        else:
            return ExtensionHealthStatus.HEALTHY
    
    async def _handle_health_issues(self, health: ExtensionSystemHealth):
        """Handle detected health issues"""
        if health.overall_status == ExtensionHealthStatus.UNHEALTHY:
            logger.error(
                f"Extension system is unhealthy: {health.unhealthy_extensions} unhealthy, "
                f"{health.degraded_extensions} degraded out of {health.total_extensions} total"
            )
        elif health.overall_status == ExtensionHealthStatus.DEGRADED:
            logger.warning(
                f"Extension system is degraded: {health.degraded_extensions} degraded, "
                f"{health.unhealthy_extensions} unhealthy out of {health.total_extensions} total"
            )
        
        # Log specific extension issues
        for name, metrics in health.extension_metrics.items():
            if metrics.status != ExtensionHealthStatus.HEALTHY:
                logger.warning(
                    f"Extension {name} is {metrics.status.value}: "
                    f"response_time={metrics.response_time_ms:.1f}ms, "
                    f"errors={metrics.error_count}, "
                    f"error_msg={metrics.error}"
                )
    
    def _add_to_history(self, health: ExtensionSystemHealth):
        """Add health record to history"""
        self._health_history.append(health)
        if len(self._health_history) > self._max_history:
            self._health_history.pop(0)
    
    def get_health_history(self, minutes: int = 60) -> List[ExtensionSystemHealth]:
        """Get health history for the specified number of minutes"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=minutes)
        return [h for h in self._health_history if h.timestamp >= cutoff_time]
    
    async def get_extension_health_for_api(self) -> Dict[str, Any]:
        """
        Get extension health information formatted for API responses.
        
        This method provides health information in a format suitable for
        integration with existing health endpoints.
        """
        health = await self.check_extension_system_health()
        
        return {
            "status": health.overall_status.value,
            "timestamp": health.timestamp.isoformat(),
            "uptime_seconds": health.system_uptime_seconds,
            "extensions": {
                "total": health.total_extensions,
                "healthy": health.healthy_extensions,
                "degraded": health.degraded_extensions,
                "unhealthy": health.unhealthy_extensions,
                "details": {
                    name: {
                        "status": metrics.status.value,
                        "response_time_ms": metrics.response_time_ms,
                        "uptime_seconds": metrics.uptime_seconds,
                        "error_count": metrics.error_count,
                        "success_count": metrics.success_count,
                        "background_tasks_active": metrics.background_tasks_active,
                        "background_tasks_failed": metrics.background_tasks_failed,
                        "last_check": metrics.last_check.isoformat(),
                        "error": metrics.error
                    }
                    for name, metrics in health.extension_metrics.items()
                }
            },
            "supporting_services": {
                "authentication": {
                    "healthy": health.authentication_healthy,
                    "description": "Extension API authentication service"
                },
                "database": {
                    "healthy": health.database_healthy,
                    "description": "Extension database connectivity"
                },
                "background_tasks": {
                    "healthy": health.background_tasks_healthy,
                    "description": "Extension background task system"
                }
            }
        }
    
    def update_extension_metrics(self, health: ExtensionSystemHealth):
        """Update Prometheus metrics with extension health data"""
        try:
            from server.metrics import (
                EXTENSION_HEALTH_STATUS, EXTENSION_RESPONSE_TIME, 
                EXTENSION_BACKGROUND_TASKS, EXTENSION_UPTIME, PROMETHEUS_ENABLED
            )
            
            if not PROMETHEUS_ENABLED:
                return
            
            # Update metrics for each extension
            for name, metrics in health.extension_metrics.items():
                # Health status metric (1=healthy, 0.5=degraded, 0=unhealthy)
                status_value = {
                    ExtensionHealthStatus.HEALTHY: 1.0,
                    ExtensionHealthStatus.DEGRADED: 0.5,
                    ExtensionHealthStatus.UNHEALTHY: 0.0,
                    ExtensionHealthStatus.UNKNOWN: 0.0
                }.get(metrics.status, 0.0)
                
                # Get extension category if available
                extension_category = "unknown"
                try:
                    if self.extension_manager:
                        extensions = self.extension_manager.registry.get_all_extensions()
                        if name in extensions:
                            record = extensions[name]
                            if hasattr(record, 'manifest') and hasattr(record.manifest, 'category'):
                                extension_category = record.manifest.category
                except Exception:
                    pass
                
                EXTENSION_HEALTH_STATUS.labels(
                    extension_name=name,
                    extension_category=extension_category
                ).set(status_value)
                
                # Response time metric
                EXTENSION_RESPONSE_TIME.labels(
                    extension_name=name,
                    operation="health_check"
                ).observe(metrics.response_time_ms / 1000.0)  # Convert to seconds
                
                # Background tasks metrics
                EXTENSION_BACKGROUND_TASKS.labels(
                    extension_name=name,
                    task_status="active"
                ).set(metrics.background_tasks_active)
                
                EXTENSION_BACKGROUND_TASKS.labels(
                    extension_name=name,
                    task_status="failed"
                ).set(metrics.background_tasks_failed)
                
                # Uptime metric
                EXTENSION_UPTIME.labels(extension_name=name).set(metrics.uptime_seconds)
                
        except Exception as e:
            logger.warning(f"Failed to update extension metrics: {e}")
    
    def record_extension_api_call(self, extension_name: str, endpoint: str, status_code: int, response_time_ms: float):
        """Record extension API call metrics"""
        try:
            from server.metrics import (
                EXTENSION_API_CALLS, EXTENSION_RESPONSE_TIME, 
                EXTENSION_ERRORS, PROMETHEUS_ENABLED
            )
            
            if not PROMETHEUS_ENABLED:
                return
            
            # Record API call
            EXTENSION_API_CALLS.labels(
                extension_name=extension_name,
                endpoint=endpoint,
                status_code=str(status_code)
            ).inc()
            
            # Record response time
            EXTENSION_RESPONSE_TIME.labels(
                extension_name=extension_name,
                operation=endpoint
            ).observe(response_time_ms / 1000.0)  # Convert to seconds
            
            # Record errors for non-2xx status codes
            if status_code >= 400:
                error_type = "client_error" if 400 <= status_code < 500 else "server_error"
                EXTENSION_ERRORS.labels(
                    extension_name=extension_name,
                    error_type=error_type
                ).inc()
                
        except Exception as e:
            logger.warning(f"Failed to record extension API call metrics: {e}")
    
    async def get_database_performance_metrics(self) -> Dict[str, Any]:
        """
        Get database performance metrics for extensions.
        
        This method provides detailed database performance information
        for integration with the database health monitor endpoint.
        """
        try:
            health = await self.check_extension_system_health()
            
            # Collect database-related metrics
            database_queries = {}
            connection_usage = {}
            background_task_load = {}
            database_errors = {}
            dependent_extensions_count = 0
            total_operations_per_minute = 0
            
            for name, metrics in health.extension_metrics.items():
                # Check if extension is database-dependent
                is_database_dependent = (
                    metrics.background_tasks_active > 0 or
                    metrics.background_tasks_failed > 0 or
                    (metrics.error and "database" in metrics.error.lower())
                )
                
                if is_database_dependent:
                    dependent_extensions_count += 1
                    
                    # Database query performance (estimated from response times)
                    database_queries[name] = {
                        "avg_response_time_ms": metrics.response_time_ms,
                        "estimated_queries_per_minute": metrics.api_calls_per_minute,
                        "success_rate": (
                            metrics.success_count / max(metrics.success_count + metrics.error_count, 1)
                        ) * 100
                    }
                    
                    # Connection usage estimation
                    connection_usage[name] = {
                        "estimated_connections": max(1, metrics.background_tasks_active),
                        "connection_efficiency": min(100, (metrics.success_count / max(metrics.error_count + 1, 1)) * 10)
                    }
                    
                    # Background task database load
                    background_task_load[name] = {
                        "active_tasks": metrics.background_tasks_active,
                        "failed_tasks": metrics.background_tasks_failed,
                        "task_failure_rate": (
                            metrics.background_tasks_failed / 
                            max(metrics.background_tasks_active + metrics.background_tasks_failed, 1)
                        ) * 100
                    }
                    
                    # Database errors
                    if metrics.error and "database" in metrics.error.lower():
                        database_errors[name] = {
                            "error_count": metrics.error_count,
                            "last_error": metrics.error,
                            "error_rate_per_hour": metrics.error_count  # Simplified calculation
                        }
                    
                    # Add to total operations
                    total_operations_per_minute += metrics.api_calls_per_minute
            
            return {
                "database_queries": database_queries,
                "connection_usage": connection_usage,
                "background_task_load": background_task_load,
                "database_errors": database_errors,
                "dependent_extensions_count": dependent_extensions_count,
                "operations_per_minute": total_operations_per_minute,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "collection_method": "extension_health_monitor"
            }
            
        except Exception as e:
            logger.error(f"Failed to get database performance metrics: {e}")
            return {
                "database_queries": {},
                "connection_usage": {},
                "background_task_load": {},
                "database_errors": {},
                "dependent_extensions_count": 0,
                "operations_per_minute": 0,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error": str(e)
            }

    def record_extension_error(self, extension_name: str, error_type: str):
        """Record extension error metrics"""
        try:
            from server.metrics import EXTENSION_ERRORS, PROMETHEUS_ENABLED
            
            if not PROMETHEUS_ENABLED:
                return
            
            EXTENSION_ERRORS.labels(
                extension_name=extension_name,
                error_type=error_type
            ).inc()
            
        except Exception as e:
            logger.warning(f"Failed to record extension error metrics: {e}")
    
    async def check_specific_extension_health(self, extension_name: str) -> Dict[str, Any]:
        """Check health of a specific extension"""
        if not self.extension_manager:
            return {
                "extension": extension_name,
                "status": "unknown",
                "error": "Extension manager not available"
            }
        
        try:
            extensions = self.extension_manager.registry.get_all_extensions()
            if extension_name not in extensions:
                return {
                    "extension": extension_name,
                    "status": "not_found",
                    "error": "Extension not found"
                }
            
            record = extensions[extension_name]
            metrics = await self._check_individual_extension_health(extension_name, record)
            
            return {
                "extension": extension_name,
                "status": metrics.status.value,
                "response_time_ms": metrics.response_time_ms,
                "uptime_seconds": metrics.uptime_seconds,
                "error_count": metrics.error_count,
                "success_count": metrics.success_count,
                "background_tasks_active": metrics.background_tasks_active,
                "background_tasks_failed": metrics.background_tasks_failed,
                "last_check": metrics.last_check.isoformat(),
                "error": metrics.error,
                "healthy": metrics.status == ExtensionHealthStatus.HEALTHY
            }
            
        except Exception as e:
            logger.error(f"Failed to check health for extension {extension_name}: {e}")
            return {
                "extension": extension_name,
                "status": "error",
                "error": str(e),
                "healthy": False
            }


# Global instance
_extension_health_monitor: Optional[ExtensionHealthMonitor] = None


def get_extension_health_monitor() -> Optional[ExtensionHealthMonitor]:
    """Get the global extension health monitor"""
    return _extension_health_monitor


async def initialize_extension_health_monitor(extension_manager=None) -> ExtensionHealthMonitor:
    """Initialize the extension health monitor"""
    global _extension_health_monitor
    
    _extension_health_monitor = ExtensionHealthMonitor(extension_manager)
    await _extension_health_monitor.start_monitoring()
    
    logger.info("Extension health monitor initialized")
    return _extension_health_monitor


async def shutdown_extension_health_monitor():
    """Shutdown the extension health monitor"""
    global _extension_health_monitor
    
    if _extension_health_monitor:
        await _extension_health_monitor.stop_monitoring()
        _extension_health_monitor = None
    
    logger.info("Extension health monitor shutdown completed")


def record_extension_api_call_global(extension_name: str, endpoint: str, status_code: int, response_time_ms: float):
    """Global function to record extension API call metrics"""
    monitor = get_extension_health_monitor()
    if monitor:
        monitor.record_extension_api_call(extension_name, endpoint, status_code, response_time_ms)


def record_extension_error_global(extension_name: str, error_type: str):
    """Global function to record extension error metrics"""
    monitor = get_extension_health_monitor()
    if monitor:
        monitor.record_extension_error(extension_name, error_type)