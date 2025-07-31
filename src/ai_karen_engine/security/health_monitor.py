"""
Comprehensive Health Monitoring System for Intelligent Authentication.

This module provides advanced health monitoring capabilities for all intelligent
authentication components, including automated alerting, service recovery,
and detailed health analytics.
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Callable, Awaitable
from collections import defaultdict, deque
import threading

from ai_karen_engine.security.intelligent_auth_base import (
    ServiceStatus,
    ServiceHealthStatus,
    IntelligentAuthHealthStatus,
    HealthCheckable,
    ServiceRegistry
)

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertType(Enum):
    """Types of health alerts."""
    SERVICE_DOWN = "service_down"
    SERVICE_DEGRADED = "service_degraded"
    HIGH_ERROR_RATE = "high_error_rate"
    SLOW_RESPONSE = "slow_response"
    MEMORY_USAGE = "memory_usage"
    RECOVERY_SUCCESS = "recovery_success"
    RECOVERY_FAILED = "recovery_failed"


@dataclass
class HealthAlert:
    """Health monitoring alert."""
    alert_id: str
    alert_type: AlertType
    severity: AlertSeverity
    service_name: str
    message: str
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    resolved: bool = False
    resolved_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'alert_id': self.alert_id,
            'alert_type': self.alert_type.value,
            'severity': self.severity.value,
            'service_name': self.service_name,
            'message': self.message,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata,
            'resolved': self.resolved,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None
        }


@dataclass
class HealthMetrics:
    """Health metrics for a service."""
    service_name: str
    uptime_percentage: float
    avg_response_time: float
    error_rate: float
    last_error: Optional[str]
    total_checks: int
    successful_checks: int
    failed_checks: int
    last_check_time: datetime
    response_time_history: List[float] = field(default_factory=list)
    error_history: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'service_name': self.service_name,
            'uptime_percentage': self.uptime_percentage,
            'avg_response_time': self.avg_response_time,
            'error_rate': self.error_rate,
            'last_error': self.last_error,
            'total_checks': self.total_checks,
            'successful_checks': self.successful_checks,
            'failed_checks': self.failed_checks,
            'last_check_time': self.last_check_time.isoformat(),
            'response_time_history': self.response_time_history[-50:],  # Last 50 measurements
            'error_history': self.error_history[-10:]  # Last 10 errors
        }


@dataclass
class RecoveryAction:
    """Recovery action configuration."""
    service_name: str
    action_name: str
    action_function: Callable[[], Awaitable[bool]]
    max_attempts: int = 3
    retry_delay: float = 30.0
    enabled: bool = True


class HealthMonitor:
    """
    Comprehensive health monitoring system for intelligent authentication components.
    
    Features:
    - Continuous health monitoring with configurable intervals
    - Automated alerting based on health status changes
    - Service recovery mechanisms with retry logic
    - Health metrics collection and analysis
    - Historical health data tracking
    """

    def __init__(self, 
                 service_registry: ServiceRegistry,
                 check_interval: float = 60.0,
                 alert_thresholds: Optional[Dict[str, Any]] = None,
                 enable_recovery: bool = True):
        """
        Initialize health monitor.
        
        Args:
            service_registry: Registry of services to monitor
            check_interval: Health check interval in seconds
            alert_thresholds: Custom alert thresholds
            enable_recovery: Whether to enable automatic recovery
        """
        self.service_registry = service_registry
        self.check_interval = check_interval
        self.enable_recovery = enable_recovery
        self.logger = logging.getLogger(f"{__name__}.HealthMonitor")
        
        # Alert thresholds
        self.alert_thresholds = {
            'response_time_warning': 2.0,
            'response_time_critical': 5.0,
            'error_rate_warning': 0.1,
            'error_rate_critical': 0.3,
            'uptime_warning': 0.95,
            'uptime_critical': 0.90,
            **( alert_thresholds or {})
        }
        
        # Monitoring state
        self._monitoring = False
        self._monitor_task: Optional[asyncio.Task] = None
        self._health_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self._metrics: Dict[str, HealthMetrics] = {}
        self._alerts: List[HealthAlert] = []
        self._alert_handlers: List[Callable[[HealthAlert], Awaitable[None]]] = []
        self._recovery_actions: Dict[str, List[RecoveryAction]] = defaultdict(list)
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Statistics
        self._total_checks = 0
        self._total_alerts = 0
        self._recovery_attempts = 0
        self._successful_recoveries = 0

    async def start_monitoring(self) -> None:
        """Start continuous health monitoring."""
        if self._monitoring:
            self.logger.warning("Health monitoring is already running")
            return

        self._monitoring = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        self.logger.info(f"Started health monitoring with {self.check_interval}s interval")

    async def stop_monitoring(self) -> None:
        """Stop health monitoring."""
        self._monitoring = False
        
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
            
        self.logger.info("Stopped health monitoring")

    async def _monitor_loop(self) -> None:
        """Main monitoring loop."""
        while self._monitoring:
            try:
                await self._perform_health_checks()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in health monitoring loop: {e}")
                await asyncio.sleep(self.check_interval)

    async def _perform_health_checks(self) -> None:
        """Perform health checks on all registered services."""
        service_names = self.service_registry.get_service_names()
        
        for service_name in service_names:
            try:
                await self._check_service_health(service_name)
            except Exception as e:
                self.logger.error(f"Error checking health of service {service_name}: {e}")
        
        self._total_checks += 1

    async def _check_service_health(self, service_name: str) -> None:
        """Check health of a specific service."""
        service = self.service_registry.get_service(service_name)
        if not service:
            return

        start_time = time.time()
        health_status = None
        
        try:
            # Perform health check
            if hasattr(service, 'health_check'):
                health_status = await service.health_check()
            else:
                # Create basic health status for services without health check
                health_status = ServiceHealthStatus(
                    service_name=service_name,
                    status=ServiceStatus.UNKNOWN,
                    last_check=datetime.now(),
                    response_time=time.time() - start_time,
                    error_message="Health check not supported"
                )
            
            # Update metrics
            await self._update_service_metrics(service_name, health_status)
            
            # Store health history
            with self._lock:
                self._health_history[service_name].append(health_status)
            
            # Check for alerts
            await self._check_alert_conditions(service_name, health_status)
            
            # Attempt recovery if needed
            if (self.enable_recovery and 
                health_status.status == ServiceStatus.UNHEALTHY):
                await self._attempt_service_recovery(service_name, service)
                
        except Exception as e:
            # Create error health status
            health_status = ServiceHealthStatus(
                service_name=service_name,
                status=ServiceStatus.UNHEALTHY,
                last_check=datetime.now(),
                response_time=time.time() - start_time,
                error_message=str(e)
            )
            
            await self._update_service_metrics(service_name, health_status)
            
            with self._lock:
                self._health_history[service_name].append(health_status)
            
            await self._create_alert(
                AlertType.SERVICE_DOWN,
                AlertSeverity.CRITICAL,
                service_name,
                f"Health check failed: {e}"
            )

    async def _update_service_metrics(self, service_name: str, health_status: ServiceHealthStatus) -> None:
        """Update metrics for a service."""
        with self._lock:
            if service_name not in self._metrics:
                self._metrics[service_name] = HealthMetrics(
                    service_name=service_name,
                    uptime_percentage=0.0,
                    avg_response_time=0.0,
                    error_rate=0.0,
                    last_error=None,
                    total_checks=0,
                    successful_checks=0,
                    failed_checks=0,
                    last_check_time=datetime.now()
                )
            
            metrics = self._metrics[service_name]
            metrics.total_checks += 1
            metrics.last_check_time = health_status.last_check
            
            # Update response time
            metrics.response_time_history.append(health_status.response_time)
            if len(metrics.response_time_history) > 100:
                metrics.response_time_history = metrics.response_time_history[-100:]
            
            metrics.avg_response_time = (
                sum(metrics.response_time_history) / len(metrics.response_time_history)
            )
            
            # Update success/failure counts
            if health_status.status == ServiceStatus.HEALTHY:
                metrics.successful_checks += 1
            else:
                metrics.failed_checks += 1
                if health_status.error_message:
                    metrics.last_error = health_status.error_message
                    metrics.error_history.append(health_status.error_message)
                    if len(metrics.error_history) > 20:
                        metrics.error_history = metrics.error_history[-20:]
            
            # Calculate rates
            metrics.uptime_percentage = (
                metrics.successful_checks / metrics.total_checks
                if metrics.total_checks > 0 else 0.0
            )
            metrics.error_rate = (
                metrics.failed_checks / metrics.total_checks
                if metrics.total_checks > 0 else 0.0
            )

    async def _check_alert_conditions(self, service_name: str, health_status: ServiceHealthStatus) -> None:
        """Check if alert conditions are met."""
        metrics = self._metrics.get(service_name)
        if not metrics:
            return

        # Check service status alerts
        if health_status.status == ServiceStatus.UNHEALTHY:
            await self._create_alert(
                AlertType.SERVICE_DOWN,
                AlertSeverity.CRITICAL,
                service_name,
                f"Service is unhealthy: {health_status.error_message or 'Unknown error'}"
            )
        elif health_status.status == ServiceStatus.DEGRADED:
            await self._create_alert(
                AlertType.SERVICE_DEGRADED,
                AlertSeverity.WARNING,
                service_name,
                "Service is degraded"
            )

        # Check response time alerts
        if health_status.response_time >= self.alert_thresholds['response_time_critical']:
            await self._create_alert(
                AlertType.SLOW_RESPONSE,
                AlertSeverity.CRITICAL,
                service_name,
                f"Critical response time: {health_status.response_time:.2f}s"
            )
        elif health_status.response_time >= self.alert_thresholds['response_time_warning']:
            await self._create_alert(
                AlertType.SLOW_RESPONSE,
                AlertSeverity.WARNING,
                service_name,
                f"Slow response time: {health_status.response_time:.2f}s"
            )

        # Check error rate alerts (only if we have enough data)
        if metrics.total_checks >= 10:
            if metrics.error_rate >= self.alert_thresholds['error_rate_critical']:
                await self._create_alert(
                    AlertType.HIGH_ERROR_RATE,
                    AlertSeverity.CRITICAL,
                    service_name,
                    f"Critical error rate: {metrics.error_rate:.1%}"
                )
            elif metrics.error_rate >= self.alert_thresholds['error_rate_warning']:
                await self._create_alert(
                    AlertType.HIGH_ERROR_RATE,
                    AlertSeverity.WARNING,
                    service_name,
                    f"High error rate: {metrics.error_rate:.1%}"
                )

        # Check uptime alerts (only if we have enough data)
        if metrics.total_checks >= 20:
            if metrics.uptime_percentage <= self.alert_thresholds['uptime_critical']:
                await self._create_alert(
                    AlertType.SERVICE_DOWN,
                    AlertSeverity.CRITICAL,
                    service_name,
                    f"Critical uptime: {metrics.uptime_percentage:.1%}"
                )
            elif metrics.uptime_percentage <= self.alert_thresholds['uptime_warning']:
                await self._create_alert(
                    AlertType.SERVICE_DEGRADED,
                    AlertSeverity.WARNING,
                    service_name,
                    f"Low uptime: {metrics.uptime_percentage:.1%}"
                )

    async def _create_alert(self, 
                          alert_type: AlertType, 
                          severity: AlertSeverity,
                          service_name: str, 
                          message: str,
                          metadata: Optional[Dict[str, Any]] = None) -> None:
        """Create and process a health alert."""
        # Check for duplicate alerts (avoid spam)
        recent_alerts = [
            alert for alert in self._alerts[-10:]  # Check last 10 alerts
            if (alert.alert_type == alert_type and 
                alert.service_name == service_name and
                not alert.resolved and
                (datetime.now() - alert.timestamp).seconds < 300)  # Within 5 minutes
        ]
        
        if recent_alerts:
            return  # Don't create duplicate alert

        alert = HealthAlert(
            alert_id=f"{service_name}_{alert_type.value}_{int(time.time())}",
            alert_type=alert_type,
            severity=severity,
            service_name=service_name,
            message=message,
            timestamp=datetime.now(),
            metadata=metadata or {}
        )
        
        with self._lock:
            self._alerts.append(alert)
            self._total_alerts += 1
        
        # Keep only recent alerts
        if len(self._alerts) > 1000:
            self._alerts = self._alerts[-1000:]
        
        self.logger.warning(f"Health alert: {alert.severity.value.upper()} - {alert.message}")
        
        # Notify alert handlers
        for handler in self._alert_handlers:
            try:
                await handler(alert)
            except Exception as e:
                self.logger.error(f"Error in alert handler: {e}")

    async def _attempt_service_recovery(self, service_name: str, service: Any) -> None:
        """Attempt to recover an unhealthy service."""
        recovery_actions = self._recovery_actions.get(service_name, [])
        
        if not recovery_actions:
            # Try default recovery actions
            recovery_actions = await self._get_default_recovery_actions(service_name, service)
        
        for action in recovery_actions:
            if not action.enabled:
                continue
                
            self.logger.info(f"Attempting recovery action '{action.action_name}' for service {service_name}")
            self._recovery_attempts += 1
            
            success = False
            for attempt in range(action.max_attempts):
                try:
                    success = await action.action_function()
                    if success:
                        break
                    
                    if attempt < action.max_attempts - 1:
                        await asyncio.sleep(action.retry_delay)
                        
                except Exception as e:
                    self.logger.error(f"Recovery action failed (attempt {attempt + 1}): {e}")
                    if attempt < action.max_attempts - 1:
                        await asyncio.sleep(action.retry_delay)
            
            if success:
                self._successful_recoveries += 1
                await self._create_alert(
                    AlertType.RECOVERY_SUCCESS,
                    AlertSeverity.INFO,
                    service_name,
                    f"Recovery action '{action.action_name}' succeeded"
                )
                break
            else:
                await self._create_alert(
                    AlertType.RECOVERY_FAILED,
                    AlertSeverity.ERROR,
                    service_name,
                    f"Recovery action '{action.action_name}' failed after {action.max_attempts} attempts"
                )

    async def _get_default_recovery_actions(self, service_name: str, service: Any) -> List[RecoveryAction]:
        """Get default recovery actions for a service."""
        actions = []
        
        # Try to reinitialize the service
        if hasattr(service, 'initialize'):
            actions.append(RecoveryAction(
                service_name=service_name,
                action_name="reinitialize",
                action_function=lambda: service.initialize(),
                max_attempts=2,
                retry_delay=10.0
            ))
        
        # Try to restart the service
        if hasattr(service, 'restart'):
            actions.append(RecoveryAction(
                service_name=service_name,
                action_name="restart",
                action_function=lambda: service.restart(),
                max_attempts=1,
                retry_delay=30.0
            ))
        
        return actions

    def add_alert_handler(self, handler: Callable[[HealthAlert], Awaitable[None]]) -> None:
        """Add an alert handler function."""
        self._alert_handlers.append(handler)

    def remove_alert_handler(self, handler: Callable[[HealthAlert], Awaitable[None]]) -> None:
        """Remove an alert handler function."""
        if handler in self._alert_handlers:
            self._alert_handlers.remove(handler)

    def add_recovery_action(self, recovery_action: RecoveryAction) -> None:
        """Add a recovery action for a service."""
        self._recovery_actions[recovery_action.service_name].append(recovery_action)

    def remove_recovery_action(self, service_name: str, action_name: str) -> None:
        """Remove a recovery action for a service."""
        actions = self._recovery_actions.get(service_name, [])
        self._recovery_actions[service_name] = [
            action for action in actions 
            if action.action_name != action_name
        ]

    def get_current_health_status(self) -> IntelligentAuthHealthStatus:
        """Get current comprehensive health status."""
        with self._lock:
            # Get latest health status for each service
            component_statuses = {}
            overall_status = ServiceStatus.HEALTHY
            
            for service_name, history in self._health_history.items():
                if history:
                    latest_status = history[-1]
                    component_statuses[service_name] = latest_status
                    
                    # Determine overall status
                    if latest_status.status == ServiceStatus.UNHEALTHY:
                        overall_status = ServiceStatus.UNHEALTHY
                    elif (latest_status.status == ServiceStatus.DEGRADED and 
                          overall_status == ServiceStatus.HEALTHY):
                        overall_status = ServiceStatus.DEGRADED

            # Calculate processing metrics
            processing_metrics = {}
            for service_name, metrics in self._metrics.items():
                processing_metrics.update({
                    f"{service_name}_uptime": metrics.uptime_percentage,
                    f"{service_name}_avg_response_time": metrics.avg_response_time,
                    f"{service_name}_error_rate": metrics.error_rate,
                    f"{service_name}_total_checks": metrics.total_checks
                })

            # Add global metrics
            processing_metrics.update({
                'total_health_checks': self._total_checks,
                'total_alerts': self._total_alerts,
                'recovery_attempts': self._recovery_attempts,
                'successful_recoveries': self._successful_recoveries,
                'recovery_success_rate': (
                    self._successful_recoveries / self._recovery_attempts
                    if self._recovery_attempts > 0 else 0.0
                )
            })

            return IntelligentAuthHealthStatus(
                overall_status=overall_status,
                component_statuses=component_statuses,
                last_updated=datetime.now(),
                processing_metrics=processing_metrics
            )

    def get_service_metrics(self, service_name: str) -> Optional[HealthMetrics]:
        """Get metrics for a specific service."""
        with self._lock:
            return self._metrics.get(service_name)

    def get_all_metrics(self) -> Dict[str, HealthMetrics]:
        """Get metrics for all services."""
        with self._lock:
            return self._metrics.copy()

    def get_health_history(self, service_name: str, limit: int = 100) -> List[ServiceHealthStatus]:
        """Get health history for a specific service."""
        with self._lock:
            history = list(self._health_history.get(service_name, []))
            return history[-limit:] if limit > 0 else history

    def get_recent_alerts(self, limit: int = 50, severity: Optional[AlertSeverity] = None) -> List[HealthAlert]:
        """Get recent alerts, optionally filtered by severity."""
        with self._lock:
            alerts = self._alerts
            
            if severity:
                alerts = [alert for alert in alerts if alert.severity == severity]
            
            return alerts[-limit:] if limit > 0 else alerts

    def get_unresolved_alerts(self) -> List[HealthAlert]:
        """Get all unresolved alerts."""
        with self._lock:
            return [alert for alert in self._alerts if not alert.resolved]

    def resolve_alert(self, alert_id: str) -> bool:
        """Mark an alert as resolved."""
        with self._lock:
            for alert in self._alerts:
                if alert.alert_id == alert_id and not alert.resolved:
                    alert.resolved = True
                    alert.resolved_at = datetime.now()
                    self.logger.info(f"Resolved alert: {alert_id}")
                    return True
            return False

    def get_monitoring_statistics(self) -> Dict[str, Any]:
        """Get comprehensive monitoring statistics."""
        with self._lock:
            return {
                'monitoring_active': self._monitoring,
                'check_interval': self.check_interval,
                'total_health_checks': self._total_checks,
                'total_alerts': self._total_alerts,
                'recovery_attempts': self._recovery_attempts,
                'successful_recoveries': self._successful_recoveries,
                'recovery_success_rate': (
                    self._successful_recoveries / self._recovery_attempts
                    if self._recovery_attempts > 0 else 0.0
                ),
                'services_monitored': len(self._health_history),
                'alert_handlers_registered': len(self._alert_handlers),
                'recovery_actions_registered': sum(
                    len(actions) for actions in self._recovery_actions.values()
                ),
                'alert_thresholds': self.alert_thresholds
            }

    async def force_health_check(self, service_name: Optional[str] = None) -> None:
        """Force an immediate health check for a service or all services."""
        if service_name:
            await self._check_service_health(service_name)
        else:
            await self._perform_health_checks()

    def update_alert_thresholds(self, thresholds: Dict[str, Any]) -> None:
        """Update alert thresholds."""
        self.alert_thresholds.update(thresholds)
        self.logger.info(f"Updated alert thresholds: {thresholds}")

    async def shutdown(self) -> None:
        """Shutdown the health monitor."""
        await self.stop_monitoring()
        
        with self._lock:
            self._health_history.clear()
            self._metrics.clear()
            self._alerts.clear()
            self._alert_handlers.clear()
            self._recovery_actions.clear()
        
        self.logger.info("Health monitor shutdown complete")


# Default alert handlers

async def log_alert_handler(alert: HealthAlert) -> None:
    """Default alert handler that logs alerts."""
    logger = logging.getLogger("health_monitor.alerts")
    
    log_level = {
        AlertSeverity.INFO: logging.INFO,
        AlertSeverity.WARNING: logging.WARNING,
        AlertSeverity.ERROR: logging.ERROR,
        AlertSeverity.CRITICAL: logging.CRITICAL
    }.get(alert.severity, logging.INFO)
    
    logger.log(
        log_level,
        f"[{alert.alert_type.value.upper()}] {alert.service_name}: {alert.message}"
    )


async def console_alert_handler(alert: HealthAlert) -> None:
    """Alert handler that prints alerts to console."""
    timestamp = alert.timestamp.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] HEALTH ALERT - {alert.severity.value.upper()}: {alert.message}")


# Utility functions for creating common recovery actions

def create_reinitialize_action(service_name: str, service: Any) -> RecoveryAction:
    """Create a recovery action that reinitializes a service."""
    async def reinitialize():
        if hasattr(service, 'initialize'):
            return await service.initialize()
        return False
    
    return RecoveryAction(
        service_name=service_name,
        action_name="reinitialize",
        action_function=reinitialize,
        max_attempts=2,
        retry_delay=10.0
    )


def create_restart_action(service_name: str, service: Any) -> RecoveryAction:
    """Create a recovery action that restarts a service."""
    async def restart():
        try:
            if hasattr(service, 'shutdown'):
                await service.shutdown()
            if hasattr(service, 'initialize'):
                return await service.initialize()
        except Exception:
            pass
        return False
    
    return RecoveryAction(
        service_name=service_name,
        action_name="restart",
        action_function=restart,
        max_attempts=1,
        retry_delay=30.0
    )


def create_cache_clear_action(service_name: str, service: Any) -> RecoveryAction:
    """Create a recovery action that clears service cache."""
    async def clear_cache():
        try:
            if hasattr(service, 'clear_cache'):
                await service.clear_cache()
                return True
            elif hasattr(service, 'cache') and hasattr(service.cache, 'clear'):
                service.cache.clear()
                return True
        except Exception:
            pass
        return False
    
    return RecoveryAction(
        service_name=service_name,
        action_name="clear_cache",
        action_function=clear_cache,
        max_attempts=1,
        retry_delay=5.0
    )