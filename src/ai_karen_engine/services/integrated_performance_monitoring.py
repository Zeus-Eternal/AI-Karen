"""
Integrated Performance Monitoring System

Integrates performance monitoring with existing metrics and logging systems
without changing reasoning flows or disrupting existing functionality.

Requirements addressed:
- 5.1-5.5: Performance monitoring and analytics capabilities
- Integration with existing metrics service
- Preservation of existing logging and monitoring flows
"""

import asyncio
import logging
import threading
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from collections import deque, defaultdict
import json

from ai_karen_engine.services.metrics_service import (
    MetricsService, get_metrics_service
)
from ai_karen_engine.services.response_performance_metrics import (
    ResponsePerformanceMetrics, get_performance_metrics_service
)

logger = logging.getLogger("kari.integrated_performance_monitoring")

@dataclass
class PerformanceIntegrationConfig:
    """Configuration for performance monitoring integration."""
    enable_response_tracking: bool = True
    enable_reasoning_tracking: bool = True
    enable_model_tracking: bool = True
    enable_cache_tracking: bool = True
    metrics_retention_hours: int = 24
    alert_thresholds: Dict[str, float] = field(default_factory=lambda: {
        "response_time_ms": 5000,
        "cpu_usage_percent": 80,
        "memory_usage_mb": 1000,
        "error_rate_percent": 10,
        "cache_hit_rate_percent": 30
    })
    enable_real_time_alerts: bool = True

@dataclass
class IntegratedMetrics:
    """Integrated metrics combining multiple sources."""
    timestamp: datetime
    response_metrics: Dict[str, Any] = field(default_factory=dict)
    reasoning_metrics: Dict[str, Any] = field(default_factory=dict)
    model_metrics: Dict[str, Any] = field(default_factory=dict)
    cache_metrics: Dict[str, Any] = field(default_factory=dict)
    system_metrics: Dict[str, Any] = field(default_factory=dict)

@dataclass
class PerformanceAlert:
    """Performance alert information."""
    alert_id: str
    metric_name: str
    current_value: float
    threshold_value: float
    severity: str  # 'warning', 'critical'
    message: str
    timestamp: datetime
    resolved: bool = False

class IntegratedPerformanceMonitor:
    """
    Integrated performance monitoring that combines optimization metrics
    with existing metrics and logging systems.
    """
    
    def __init__(self, config: Optional[PerformanceIntegrationConfig] = None):
        self.logger = logging.getLogger("kari.integrated_performance_monitor")
        self.config = config or PerformanceIntegrationConfig()
        
        # Core services
        self.metrics_service = get_metrics_service()
        try:
            self.performance_metrics_service = get_performance_metrics_service()
        except Exception as e:
            self.logger.warning(f"Performance metrics service not available: {e}")
            self.performance_metrics_service = None
        
        # Integration state
        self.integrated_metrics: deque = deque(maxlen=10000)  # Keep last 10k metrics
        self.active_alerts: Dict[str, PerformanceAlert] = {}
        self.alert_callbacks: List[Callable] = []
        
        # Performance tracking
        self.component_metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.aggregated_stats: Dict[str, Dict[str, float]] = {}
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Background monitoring
        self._monitoring_task: Optional[asyncio.Task] = None
        self._monitoring_active = False
        
        self.logger.info("Integrated Performance Monitor initialized")
    
    async def start_monitoring(self):
        """Start background performance monitoring."""
        if self._monitoring_active:
            return
        
        self._monitoring_active = True
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        self.logger.info("Performance monitoring started")
    
    async def stop_monitoring(self):
        """Stop background performance monitoring."""
        self._monitoring_active = False
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        self.logger.info("Performance monitoring stopped")
    
    async def _monitoring_loop(self):
        """Background monitoring loop."""
        while self._monitoring_active:
            try:
                await self._collect_integrated_metrics()
                await self._check_alert_conditions()
                await self._update_aggregated_stats()
                await asyncio.sleep(10)  # Collect metrics every 10 seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(30)  # Back off on error
    
    async def _collect_integrated_metrics(self):
        """Collect metrics from all integrated sources."""
        try:
            current_time = datetime.now()
            
            # Collect response metrics
            response_metrics = {}
            if self.performance_metrics_service:
                try:
                    response_stats = await self.performance_metrics_service.get_recent_performance_summary()
                    response_metrics = {
                        "avg_response_time_ms": response_stats.get("avg_response_time_ms", 0),
                        "max_response_time_ms": response_stats.get("max_response_time_ms", 0),
                        "total_responses": response_stats.get("total_responses", 0),
                        "avg_cpu_percent": response_stats.get("avg_cpu_percent", 0),
                        "max_cpu_percent": response_stats.get("max_cpu_percent", 0),
                        "avg_memory_mb": response_stats.get("avg_memory_mb", 0),
                        "resource_pressure_count": response_stats.get("resource_pressure_count", 0)
                    }
                except Exception as e:
                    self.logger.debug(f"Failed to collect response metrics: {e}")
            
            # Collect reasoning metrics (from existing metrics service)
            reasoning_metrics = {}
            try:
                # Get metrics from existing metrics service
                metrics_stats = self.metrics_service.get_stats_summary()
                if isinstance(metrics_stats, dict):
                    reasoning_metrics = {
                        "llm_requests": metrics_stats.get("counters", {}).get("copilot_requests_total", 0),
                        "memory_queries": metrics_stats.get("counters", {}).get("memory_queries_total", 0),
                        "avg_llm_latency_ms": self._extract_histogram_avg(
                            metrics_stats.get("histograms", {}).get("llm_latency_seconds", {})
                        ) * 1000,
                        "avg_vector_latency_ms": self._extract_histogram_avg(
                            metrics_stats.get("histograms", {}).get("vector_latency_seconds", {})
                        ) * 1000
                    }
            except Exception as e:
                self.logger.debug(f"Failed to collect reasoning metrics: {e}")
            
            # Collect model metrics
            model_metrics = {}
            try:
                # This would integrate with model discovery and routing metrics
                model_metrics = {
                    "active_models": 0,  # Would be populated by model discovery
                    "model_switches": 0,  # Would be populated by model router
                    "routing_decisions": 0  # Would be populated by routing system
                }
            except Exception as e:
                self.logger.debug(f"Failed to collect model metrics: {e}")
            
            # Collect cache metrics
            cache_metrics = {}
            try:
                # This would integrate with smart cache manager
                cache_metrics = {
                    "cache_hit_rate": 0.0,  # Would be populated by cache manager
                    "cache_size_mb": 0.0,  # Would be populated by cache manager
                    "cache_operations": 0  # Would be populated by cache manager
                }
            except Exception as e:
                self.logger.debug(f"Failed to collect cache metrics: {e}")
            
            # Collect system metrics
            system_metrics = {}
            try:
                import psutil
                process = psutil.Process()
                system_metrics = {
                    "cpu_percent": process.cpu_percent(),
                    "memory_mb": process.memory_info().rss / 1024 / 1024,
                    "memory_percent": psutil.virtual_memory().percent,
                    "open_files": len(process.open_files()),
                    "threads": process.num_threads()
                }
            except Exception as e:
                self.logger.debug(f"Failed to collect system metrics: {e}")
            
            # Create integrated metrics
            integrated = IntegratedMetrics(
                timestamp=current_time,
                response_metrics=response_metrics,
                reasoning_metrics=reasoning_metrics,
                model_metrics=model_metrics,
                cache_metrics=cache_metrics,
                system_metrics=system_metrics
            )
            
            # Store metrics
            with self._lock:
                self.integrated_metrics.append(integrated)
                
                # Update component metrics
                for component, metrics in [
                    ("response", response_metrics),
                    ("reasoning", reasoning_metrics),
                    ("model", model_metrics),
                    ("cache", cache_metrics),
                    ("system", system_metrics)
                ]:
                    self.component_metrics[component].append({
                        "timestamp": current_time,
                        "metrics": metrics
                    })
            
            # Send to existing metrics service
            await self._send_to_existing_metrics(integrated)
            
        except Exception as e:
            self.logger.error(f"Failed to collect integrated metrics: {e}")
    
    def _extract_histogram_avg(self, histogram_data: Dict[str, Any]) -> float:
        """Extract average from histogram data."""
        try:
            if isinstance(histogram_data, dict):
                return histogram_data.get("avg", 0.0)
            return 0.0
        except Exception:
            return 0.0
    
    async def _send_to_existing_metrics(self, integrated: IntegratedMetrics):
        """Send integrated metrics to existing metrics service."""
        try:
            # Send response metrics
            if integrated.response_metrics:
                if "avg_response_time_ms" in integrated.response_metrics:
                    self.metrics_service.record_total_turn_time(
                        integrated.response_metrics["avg_response_time_ms"] / 1000,
                        "integrated_optimization",
                        "success"
                    )
                
                if "avg_cpu_percent" in integrated.response_metrics:
                    self.metrics_service.update_system_health(
                        memory_usage=int(integrated.system_metrics.get("memory_mb", 0) * 1024 * 1024),
                        service="optimization_system"
                    )
            
            # Send model performance metrics
            if integrated.model_metrics and "routing_decisions" in integrated.model_metrics:
                self.metrics_service.record_model_performance(
                    1.0,  # Default score
                    "integrated_system",
                    "routing"
                )
            
        except Exception as e:
            self.logger.debug(f"Failed to send metrics to existing service: {e}")
    
    async def _check_alert_conditions(self):
        """Check for alert conditions based on thresholds."""
        if not self.config.enable_real_time_alerts:
            return
        
        try:
            if not self.integrated_metrics:
                return
            
            latest_metrics = self.integrated_metrics[-1]
            current_time = datetime.now()
            
            # Check response time threshold
            response_time = latest_metrics.response_metrics.get("avg_response_time_ms", 0)
            if response_time > self.config.alert_thresholds["response_time_ms"]:
                await self._trigger_alert(
                    "response_time_high",
                    "response_time_ms",
                    response_time,
                    self.config.alert_thresholds["response_time_ms"],
                    "warning",
                    f"Average response time ({response_time:.1f}ms) exceeds threshold"
                )
            
            # Check CPU usage threshold
            cpu_usage = latest_metrics.system_metrics.get("cpu_percent", 0)
            if cpu_usage > self.config.alert_thresholds["cpu_usage_percent"]:
                await self._trigger_alert(
                    "cpu_usage_high",
                    "cpu_usage_percent",
                    cpu_usage,
                    self.config.alert_thresholds["cpu_usage_percent"],
                    "critical",
                    f"CPU usage ({cpu_usage:.1f}%) exceeds threshold"
                )
            
            # Check memory usage threshold
            memory_usage = latest_metrics.system_metrics.get("memory_mb", 0)
            if memory_usage > self.config.alert_thresholds["memory_usage_mb"]:
                await self._trigger_alert(
                    "memory_usage_high",
                    "memory_usage_mb",
                    memory_usage,
                    self.config.alert_thresholds["memory_usage_mb"],
                    "warning",
                    f"Memory usage ({memory_usage:.1f}MB) exceeds threshold"
                )
            
            # Check cache hit rate threshold
            cache_hit_rate = latest_metrics.cache_metrics.get("cache_hit_rate", 100) * 100
            if cache_hit_rate < self.config.alert_thresholds["cache_hit_rate_percent"]:
                await self._trigger_alert(
                    "cache_hit_rate_low",
                    "cache_hit_rate_percent",
                    cache_hit_rate,
                    self.config.alert_thresholds["cache_hit_rate_percent"],
                    "warning",
                    f"Cache hit rate ({cache_hit_rate:.1f}%) below threshold"
                )
            
        except Exception as e:
            self.logger.error(f"Alert condition check failed: {e}")
    
    async def _trigger_alert(
        self, 
        alert_id: str, 
        metric_name: str, 
        current_value: float, 
        threshold_value: float,
        severity: str, 
        message: str
    ):
        """Trigger a performance alert."""
        try:
            # Check if alert already exists and is recent
            if alert_id in self.active_alerts:
                existing_alert = self.active_alerts[alert_id]
                if (datetime.now() - existing_alert.timestamp).seconds < 300:  # 5 minutes
                    return  # Don't spam alerts
            
            # Create new alert
            alert = PerformanceAlert(
                alert_id=alert_id,
                metric_name=metric_name,
                current_value=current_value,
                threshold_value=threshold_value,
                severity=severity,
                message=message,
                timestamp=datetime.now()
            )
            
            with self._lock:
                self.active_alerts[alert_id] = alert
            
            # Log alert
            log_level = logging.WARNING if severity == "warning" else logging.ERROR
            self.logger.log(log_level, f"Performance Alert: {message}")
            
            # Notify callbacks
            for callback in self.alert_callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(alert)
                    else:
                        callback(alert)
                except Exception as e:
                    self.logger.error(f"Alert callback failed: {e}")
            
        except Exception as e:
            self.logger.error(f"Failed to trigger alert: {e}")
    
    async def _update_aggregated_stats(self):
        """Update aggregated statistics."""
        try:
            with self._lock:
                if len(self.integrated_metrics) < 2:
                    return
                
                # Calculate stats for last hour
                cutoff_time = datetime.now() - timedelta(hours=1)
                recent_metrics = [
                    m for m in self.integrated_metrics 
                    if m.timestamp >= cutoff_time
                ]
                
                if not recent_metrics:
                    return
                
                # Aggregate response metrics
                response_times = [
                    m.response_metrics.get("avg_response_time_ms", 0) 
                    for m in recent_metrics
                    if m.response_metrics.get("avg_response_time_ms", 0) > 0
                ]
                
                if response_times:
                    self.aggregated_stats["response"] = {
                        "avg_response_time_ms": sum(response_times) / len(response_times),
                        "max_response_time_ms": max(response_times),
                        "min_response_time_ms": min(response_times),
                        "p95_response_time_ms": sorted(response_times)[int(len(response_times) * 0.95)] if len(response_times) > 1 else response_times[0]
                    }
                
                # Aggregate system metrics
                cpu_values = [
                    m.system_metrics.get("cpu_percent", 0) 
                    for m in recent_metrics
                    if m.system_metrics.get("cpu_percent", 0) > 0
                ]
                
                memory_values = [
                    m.system_metrics.get("memory_mb", 0) 
                    for m in recent_metrics
                    if m.system_metrics.get("memory_mb", 0) > 0
                ]
                
                if cpu_values and memory_values:
                    self.aggregated_stats["system"] = {
                        "avg_cpu_percent": sum(cpu_values) / len(cpu_values),
                        "max_cpu_percent": max(cpu_values),
                        "avg_memory_mb": sum(memory_values) / len(memory_values),
                        "max_memory_mb": max(memory_values)
                    }
                
        except Exception as e:
            self.logger.error(f"Failed to update aggregated stats: {e}")
    
    def add_alert_callback(self, callback: Callable):
        """Add callback for performance alerts."""
        self.alert_callbacks.append(callback)
        self.logger.debug("Added performance alert callback")
    
    def remove_alert_callback(self, callback: Callable):
        """Remove alert callback."""
        try:
            self.alert_callbacks.remove(callback)
            self.logger.debug("Removed performance alert callback")
        except ValueError:
            pass
    
    def get_performance_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive performance data for dashboard."""
        try:
            with self._lock:
                current_time = datetime.now()
                
                # Get recent metrics (last hour)
                cutoff_time = current_time - timedelta(hours=1)
                recent_metrics = [
                    m for m in self.integrated_metrics 
                    if m.timestamp >= cutoff_time
                ]
                
                # Prepare dashboard data
                dashboard_data = {
                    "timestamp": current_time.isoformat(),
                    "metrics_count": len(recent_metrics),
                    "aggregated_stats": self.aggregated_stats.copy(),
                    "active_alerts": [
                        {
                            "alert_id": alert.alert_id,
                            "metric_name": alert.metric_name,
                            "current_value": alert.current_value,
                            "threshold_value": alert.threshold_value,
                            "severity": alert.severity,
                            "message": alert.message,
                            "timestamp": alert.timestamp.isoformat(),
                            "resolved": alert.resolved
                        }
                        for alert in self.active_alerts.values()
                        if not alert.resolved
                    ],
                    "component_health": {},
                    "trends": {}
                }
                
                # Calculate component health
                if recent_metrics:
                    latest = recent_metrics[-1]
                    
                    dashboard_data["component_health"] = {
                        "response_system": self._calculate_health_score(
                            latest.response_metrics.get("avg_response_time_ms", 0),
                            self.config.alert_thresholds["response_time_ms"]
                        ),
                        "reasoning_system": self._calculate_health_score(
                            latest.reasoning_metrics.get("avg_llm_latency_ms", 0),
                            1000  # 1 second threshold
                        ),
                        "cache_system": latest.cache_metrics.get("cache_hit_rate", 0.5) * 100,
                        "system_resources": 100 - latest.system_metrics.get("cpu_percent", 0)
                    }
                
                # Calculate trends (last 10 data points)
                if len(recent_metrics) >= 10:
                    trend_metrics = recent_metrics[-10:]
                    
                    response_times = [m.response_metrics.get("avg_response_time_ms", 0) for m in trend_metrics]
                    cpu_usage = [m.system_metrics.get("cpu_percent", 0) for m in trend_metrics]
                    
                    dashboard_data["trends"] = {
                        "response_time_trend": self._calculate_trend(response_times),
                        "cpu_usage_trend": self._calculate_trend(cpu_usage),
                        "memory_usage_trend": self._calculate_trend([
                            m.system_metrics.get("memory_mb", 0) for m in trend_metrics
                        ])
                    }
                
                return dashboard_data
                
        except Exception as e:
            self.logger.error(f"Failed to get dashboard data: {e}")
            return {"error": str(e), "timestamp": datetime.now().isoformat()}
    
    def _calculate_health_score(self, current_value: float, threshold: float) -> float:
        """Calculate health score (0-100) based on current value vs threshold."""
        if threshold == 0:
            return 100.0
        
        ratio = current_value / threshold
        if ratio <= 0.5:
            return 100.0
        elif ratio <= 1.0:
            return 100.0 - (ratio - 0.5) * 100.0
        else:
            return max(0.0, 50.0 - (ratio - 1.0) * 25.0)
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction from list of values."""
        if len(values) < 2:
            return "stable"
        
        # Simple linear trend calculation
        first_half = sum(values[:len(values)//2]) / (len(values)//2)
        second_half = sum(values[len(values)//2:]) / (len(values) - len(values)//2)
        
        change_percent = ((second_half - first_half) / first_half * 100) if first_half > 0 else 0
        
        if change_percent > 10:
            return "increasing"
        elif change_percent < -10:
            return "decreasing"
        else:
            return "stable"
    
    async def resolve_alert(self, alert_id: str):
        """Resolve an active alert."""
        try:
            with self._lock:
                if alert_id in self.active_alerts:
                    self.active_alerts[alert_id].resolved = True
                    self.logger.info(f"Resolved alert: {alert_id}")
        except Exception as e:
            self.logger.error(f"Failed to resolve alert {alert_id}: {e}")
    
    def get_integration_status(self) -> Dict[str, Any]:
        """Get integration status with existing systems."""
        return {
            "monitoring_active": self._monitoring_active,
            "metrics_service_available": self.metrics_service is not None,
            "performance_service_available": self.performance_metrics_service is not None,
            "total_metrics_collected": len(self.integrated_metrics),
            "active_alerts_count": len([a for a in self.active_alerts.values() if not a.resolved]),
            "alert_callbacks_count": len(self.alert_callbacks),
            "component_metrics": {
                component: len(metrics) for component, metrics in self.component_metrics.items()
            },
            "config": {
                "response_tracking": self.config.enable_response_tracking,
                "reasoning_tracking": self.config.enable_reasoning_tracking,
                "model_tracking": self.config.enable_model_tracking,
                "cache_tracking": self.config.enable_cache_tracking,
                "real_time_alerts": self.config.enable_real_time_alerts
            }
        }

# Global instance
_integrated_performance_monitor: Optional[IntegratedPerformanceMonitor] = None
_monitor_lock = threading.RLock()

def get_integrated_performance_monitor(
    config: Optional[PerformanceIntegrationConfig] = None
) -> IntegratedPerformanceMonitor:
    """Get the global integrated performance monitor instance."""
    global _integrated_performance_monitor
    if _integrated_performance_monitor is None:
        with _monitor_lock:
            if _integrated_performance_monitor is None:
                _integrated_performance_monitor = IntegratedPerformanceMonitor(config)
    return _integrated_performance_monitor

async def initialize_integrated_performance_monitoring(
    config: Optional[PerformanceIntegrationConfig] = None
):
    """Initialize the integrated performance monitoring system."""
    monitor = get_integrated_performance_monitor(config)
    await monitor.start_monitoring()
    return monitor