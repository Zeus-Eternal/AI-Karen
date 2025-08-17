"""
Health Monitoring Service for LLM Providers and Runtimes

This module provides comprehensive health monitoring capabilities for the LLM system,
including automatic failover, recovery detection, and health-based routing decisions.

Key Features:
- Continuous health monitoring of providers and runtimes
- Automatic failover to healthy alternatives
- Recovery detection and notification
- Health-based routing policies
- Metrics collection and alerting
"""

import asyncio
import logging
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Set

from ai_karen_engine.integrations.registry import get_registry, HealthStatus

logger = logging.getLogger(__name__)

# Optional Prometheus metrics
try:
    from prometheus_client import Counter, Gauge, Histogram
    METRICS_ENABLED = True
except ImportError:
    METRICS_ENABLED = False
    
    class _DummyMetric:
        def labels(self, **kwargs):
            return self
        def inc(self, n: int = 1):
            pass
        def set(self, v: float):
            pass
        def observe(self, v: float):
            pass
    
    Counter = Gauge = Histogram = _DummyMetric

# Metrics
HEALTH_CHECK_TOTAL = Counter(
    "llm_health_checks_total",
    "Total health checks performed",
    ["component", "status"]
) if METRICS_ENABLED else Counter()

COMPONENT_HEALTH_STATUS = Gauge(
    "llm_component_health_status",
    "Current health status of components (1=healthy, 0=unhealthy)",
    ["component", "type"]
) if METRICS_ENABLED else Gauge()

HEALTH_CHECK_DURATION = Histogram(
    "llm_health_check_duration_seconds",
    "Duration of health checks",
    ["component"]
) if METRICS_ENABLED else Histogram()

FAILOVER_EVENTS = Counter(
    "llm_failover_events_total",
    "Total failover events",
    ["from_component", "to_component", "reason"]
) if METRICS_ENABLED else Counter()


@dataclass
class HealthEvent:
    """Represents a health status change event."""
    component: str
    old_status: str
    new_status: str
    timestamp: datetime
    error_message: Optional[str] = None
    response_time: Optional[float] = None


@dataclass
class FailoverEvent:
    """Represents a failover event."""
    from_component: str
    to_component: str
    reason: str
    timestamp: datetime
    success: bool = True


class HealthMonitor:
    """
    Comprehensive health monitoring service for LLM providers and runtimes.
    
    This service continuously monitors the health of all registered components,
    detects failures and recoveries, and provides intelligent failover capabilities.
    """
    
    def __init__(
        self,
        registry=None,
        check_interval: int = 30,
        failure_threshold: int = 3,
        recovery_threshold: int = 2,
        enable_auto_failover: bool = True,
    ):
        self.registry = registry or get_registry()
        self.check_interval = check_interval
        self.failure_threshold = failure_threshold
        self.recovery_threshold = recovery_threshold
        self.enable_auto_failover = enable_auto_failover
        
        # Health tracking
        self.health_history: Dict[str, List[HealthStatus]] = {}
        self.failure_counts: Dict[str, int] = {}
        self.recovery_counts: Dict[str, int] = {}
        self.last_known_good: Dict[str, datetime] = {}
        
        # Event tracking
        self.health_events: List[HealthEvent] = []
        self.failover_events: List[FailoverEvent] = []
        
        # Callbacks
        self.health_change_callbacks: List[Callable[[HealthEvent], None]] = []
        self.failover_callbacks: List[Callable[[FailoverEvent], None]] = []
        
        # Monitoring state
        self.monitoring_active = False
        self.monitor_thread: Optional[threading.Thread] = None
        
        logger.info(f"Health monitor initialized with {check_interval}s interval")
    
    def start_monitoring(self) -> None:
        """Start continuous health monitoring."""
        if self.monitoring_active:
            logger.warning("Health monitoring is already active")
            return
        
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("Started continuous health monitoring")
    
    def stop_monitoring(self) -> None:
        """Stop continuous health monitoring."""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("Stopped health monitoring")
    
    def _monitor_loop(self) -> None:
        """Main monitoring loop."""
        while self.monitoring_active:
            try:
                self.check_all_health()
                time.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
                time.sleep(self.check_interval)
    
    def check_all_health(self) -> Dict[str, HealthStatus]:
        """Check health of all components and process status changes."""
        current_health = self.registry.health_check_all()
        
        for component, status in current_health.items():
            self._process_health_status(component, status)
        
        return current_health
    
    def _process_health_status(self, component: str, status: HealthStatus) -> None:
        """Process a health status update for a component."""
        # Record metrics
        HEALTH_CHECK_TOTAL.labels(component=component, status=status.status).inc()
        if status.response_time:
            HEALTH_CHECK_DURATION.labels(component=component).observe(status.response_time)
        
        # Update health gauge
        health_value = 1.0 if status.status in ["healthy", "unknown"] else 0.0
        component_type = "provider" if component.startswith("provider:") else "runtime"
        COMPONENT_HEALTH_STATUS.labels(component=component, type=component_type).set(health_value)
        
        # Get previous status
        history = self.health_history.setdefault(component, [])
        previous_status = history[-1].status if history else "unknown"
        
        # Add to history
        history.append(status)
        if len(history) > 100:  # Keep last 100 status checks
            history.pop(0)
        
        # Check for status changes
        if status.status != previous_status:
            self._handle_status_change(component, previous_status, status)
        
        # Update failure/recovery tracking
        if status.status in ["unhealthy", "degraded"]:
            self.failure_counts[component] = self.failure_counts.get(component, 0) + 1
            self.recovery_counts[component] = 0
        elif status.status in ["healthy"]:
            self.recovery_counts[component] = self.recovery_counts.get(component, 0) + 1
            if self.recovery_counts[component] >= self.recovery_threshold:
                self.failure_counts[component] = 0
                self.last_known_good[component] = datetime.now()
    
    def _handle_status_change(self, component: str, old_status: str, new_status: HealthStatus) -> None:
        """Handle a health status change."""
        event = HealthEvent(
            component=component,
            old_status=old_status,
            new_status=new_status.status,
            timestamp=datetime.now(),
            error_message=new_status.error_message,
            response_time=new_status.response_time,
        )
        
        self.health_events.append(event)
        if len(self.health_events) > 1000:  # Keep last 1000 events
            self.health_events.pop(0)
        
        logger.info(f"Health status change: {component} {old_status} -> {new_status.status}")
        
        # Notify callbacks
        for callback in self.health_change_callbacks:
            try:
                callback(event)
            except Exception as e:
                logger.error(f"Health change callback error: {e}")
        
        # Handle automatic failover
        if (self.enable_auto_failover and 
            new_status.status in ["unhealthy", "degraded"] and
            self.failure_counts.get(component, 0) >= self.failure_threshold):
            self._attempt_failover(component)
    
    def _attempt_failover(self, failed_component: str) -> None:
        """Attempt to failover from a failed component."""
        logger.warning(f"Attempting failover from failed component: {failed_component}")
        
        # Determine component type
        if failed_component.startswith("provider:"):
            component_type = "provider"
            component_name = failed_component[9:]
            alternatives = self.registry.get_healthy_providers()
        elif failed_component.startswith("runtime:"):
            component_type = "runtime"
            component_name = failed_component[8:]
            alternatives = self.registry.get_healthy_runtimes()
        else:
            logger.error(f"Unknown component type for failover: {failed_component}")
            return
        
        # Find healthy alternatives
        healthy_alternatives = [alt for alt in alternatives if alt != component_name]
        
        if not healthy_alternatives:
            logger.error(f"No healthy alternatives found for {failed_component}")
            return
        
        # Select best alternative (first healthy one for now)
        selected_alternative = healthy_alternatives[0]
        
        # Record failover event
        failover_event = FailoverEvent(
            from_component=failed_component,
            to_component=f"{component_type}:{selected_alternative}",
            reason=f"Health check failures exceeded threshold ({self.failure_threshold})",
            timestamp=datetime.now(),
            success=True,
        )
        
        self.failover_events.append(failover_event)
        if len(self.failover_events) > 100:  # Keep last 100 failover events
            self.failover_events.pop(0)
        
        # Record metrics
        FAILOVER_EVENTS.labels(
            from_component=failed_component,
            to_component=failover_event.to_component,
            reason="health_failure"
        ).inc()
        
        logger.info(f"Failover: {failed_component} -> {failover_event.to_component}")
        
        # Notify callbacks
        for callback in self.failover_callbacks:
            try:
                callback(failover_event)
            except Exception as e:
                logger.error(f"Failover callback error: {e}")
    
    def get_component_health(self, component: str) -> Optional[HealthStatus]:
        """Get current health status of a component."""
        return self.registry.get_health_status(component)
    
    def get_healthy_components(self, component_type: Optional[str] = None) -> List[str]:
        """Get list of healthy components."""
        if component_type == "provider":
            return self.registry.get_healthy_providers()
        elif component_type == "runtime":
            return self.registry.get_healthy_runtimes()
        else:
            # Return all healthy components
            healthy = []
            healthy.extend([f"provider:{p}" for p in self.registry.get_healthy_providers()])
            healthy.extend([f"runtime:{r}" for r in self.registry.get_healthy_runtimes()])
            return healthy
    
    def get_unhealthy_components(self) -> Dict[str, HealthStatus]:
        """Get all unhealthy components."""
        return self.registry.get_unhealthy_components()
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get comprehensive health summary."""
        all_health = self.registry.health_check_all()
        
        summary = {
            "total_components": len(all_health),
            "healthy_components": 0,
            "unhealthy_components": 0,
            "unknown_components": 0,
            "degraded_components": 0,
            "providers": {
                "total": len(self.registry.list_providers()),
                "healthy": len(self.registry.get_healthy_providers()),
            },
            "runtimes": {
                "total": len(self.registry.list_runtimes()),
                "healthy": len(self.registry.get_healthy_runtimes()),
            },
            "recent_events": len([e for e in self.health_events if e.timestamp > datetime.now() - timedelta(hours=1)]),
            "recent_failovers": len([f for f in self.failover_events if f.timestamp > datetime.now() - timedelta(hours=1)]),
        }
        
        # Count by status
        for status in all_health.values():
            if status.status == "healthy":
                summary["healthy_components"] += 1
            elif status.status == "unhealthy":
                summary["unhealthy_components"] += 1
            elif status.status == "degraded":
                summary["degraded_components"] += 1
            else:
                summary["unknown_components"] += 1
        
        return summary
    
    def get_health_history(self, component: str, limit: int = 50) -> List[HealthStatus]:
        """Get health history for a component."""
        history = self.health_history.get(component, [])
        return history[-limit:] if limit else history
    
    def get_recent_events(self, hours: int = 24) -> List[HealthEvent]:
        """Get recent health events."""
        cutoff = datetime.now() - timedelta(hours=hours)
        return [event for event in self.health_events if event.timestamp > cutoff]
    
    def get_recent_failovers(self, hours: int = 24) -> List[FailoverEvent]:
        """Get recent failover events."""
        cutoff = datetime.now() - timedelta(hours=hours)
        return [event for event in self.failover_events if event.timestamp > cutoff]
    
    def add_health_change_callback(self, callback: Callable[[HealthEvent], None]) -> None:
        """Add a callback for health status changes."""
        self.health_change_callbacks.append(callback)
    
    def add_failover_callback(self, callback: Callable[[FailoverEvent], None]) -> None:
        """Add a callback for failover events."""
        self.failover_callbacks.append(callback)
    
    def force_health_check(self, component: str) -> HealthStatus:
        """Force an immediate health check for a specific component."""
        return self.registry.health_check(component)
    
    def reset_failure_count(self, component: str) -> None:
        """Reset failure count for a component (useful for manual recovery)."""
        self.failure_counts[component] = 0
        self.recovery_counts[component] = 0
        logger.info(f"Reset failure count for {component}")
    
    def is_component_healthy(self, component: str) -> bool:
        """Check if a component is currently healthy."""
        status = self.get_component_health(component)
        return status is None or status.status in ["healthy", "unknown"]
    
    def get_best_alternative(self, failed_component: str) -> Optional[str]:
        """Get the best healthy alternative for a failed component."""
        if failed_component.startswith("provider:"):
            alternatives = self.registry.get_healthy_providers()
            component_name = failed_component[9:]
            return next((alt for alt in alternatives if alt != component_name), None)
        elif failed_component.startswith("runtime:"):
            alternatives = self.registry.get_healthy_runtimes()
            component_name = failed_component[8:]
            return next((alt for alt in alternatives if alt != component_name), None)
        else:
            return None


# Global health monitor instance
_global_health_monitor: Optional[HealthMonitor] = None
_health_monitor_lock = threading.RLock()


def get_health_monitor() -> HealthMonitor:
    """Get the global health monitor instance."""
    global _global_health_monitor
    if _global_health_monitor is None:
        with _health_monitor_lock:
            if _global_health_monitor is None:
                _global_health_monitor = HealthMonitor()
    return _global_health_monitor


def initialize_health_monitor(**kwargs) -> HealthMonitor:
    """Initialize a fresh global health monitor."""
    global _global_health_monitor
    with _health_monitor_lock:
        _global_health_monitor = HealthMonitor(**kwargs)
    return _global_health_monitor


# Convenience functions
def start_health_monitoring() -> None:
    """Start global health monitoring."""
    get_health_monitor().start_monitoring()


def stop_health_monitoring() -> None:
    """Stop global health monitoring."""
    if _global_health_monitor:
        _global_health_monitor.stop_monitoring()


def get_health_summary() -> Dict[str, Any]:
    """Get global health summary."""
    return get_health_monitor().get_health_summary()


def is_healthy(component: str) -> bool:
    """Check if a component is healthy."""
    return get_health_monitor().is_component_healthy(component)


__all__ = [
    "HealthEvent",
    "FailoverEvent", 
    "HealthMonitor",
    "get_health_monitor",
    "initialize_health_monitor",
    "start_health_monitoring",
    "stop_health_monitoring",
    "get_health_summary",
    "is_healthy",
]