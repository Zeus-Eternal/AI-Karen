"""
Zvec Metrics & Monitoring - Phase 4

Comprehensive monitoring system for Zvec integration including:
- Real-time metrics collection
- Performance monitoring (latency, throughput)
- Health checks
- Alerting infrastructure
- Dashboard integration
"""

import time
import asyncio
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
import psutil
import os


class MetricType(Enum):
    """Types of metrics we track"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class MetricPoint:
    """A single metric data point"""
    timestamp: float
    value: float
    tags: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "timestamp": self.timestamp,
            "value": self.value,
            "tags": self.tags
        }


@dataclass
class Alert:
    """An alert that was triggered"""
    severity: AlertSeverity
    metric_name: str
    message: str
    current_value: float
    threshold: float
    timestamp: float = field(default_factory=time.time)
    resolved: bool = False
    
    def to_dict(self) -> Dict:
        return {
            "severity": self.severity.value,
            "metric_name": self.metric_name,
            "message": self.message,
            "current_value": self.current_value,
            "threshold": self.threshold,
            "timestamp": self.timestamp,
            "resolved": self.resolved
        }


class ZvecMetricsCollector:
    """
    Collects and aggregates metrics for Zvec integration.
    
    Tracks:
    - RAG latency (p50, p95, p99)
    - Sync performance
    - User concurrency
    - Offline mode usage
    - Memory usage
    - Database performance
    """
    
    def __init__(self, 
                 retention_seconds: int = 3600,
                 histogram_bins: int = 100):
        self.retention_seconds = retention_seconds
        self.histogram_bins = histogram_bins
        
        # Metric storage
        self._counters: Dict[str, float] = defaultdict(float)
        self._gauges: Dict[str, float] = {}
        self._histograms: Dict[str, deque] = defaultdict(lambda: deque(maxlen=histogram_bins))
        self._timers: Dict[str, deque] = defaultdict(lambda: deque(maxlen=histogram_bins))
        
        # Alerting
        self._thresholds: Dict[str, Dict] = {}
        self._active_alerts: Dict[str, Alert] = {}
        self._alert_callbacks: List[Callable] = []
        
        # Lock for thread safety
        self._lock = threading.Lock()
        
        # Start cleanup thread
        self._cleanup_thread = threading.Thread(target=self._cleanup_old_metrics, daemon=True)
        self._cleanup_thread.start()
    
    def increment(self, name: str, value: float = 1.0, tags: Dict[str, str] = None):
        """Increment a counter metric"""
        with self._lock:
            key = self._make_key(name, tags)
            self._counters[key] += value
            self._check_thresholds(name, self._counters[key], tags)
    
    def set_gauge(self, name: str, value: float, tags: Dict[str, str] = None):
        """Set a gauge metric"""
        with self._lock:
            key = self._make_key(name, tags)
            self._gauges[key] = value
            self._check_thresholds(name, value, tags)
    
    def record_histogram(self, name: str, value: float, tags: Dict[str, str] = None):
        """Record a value in a histogram"""
        with self._lock:
            key = self._make_key(name, tags)
            self._histograms[key].append(MetricPoint(time.time(), value, tags or {}))
    
    def record_timer(self, name: str, duration_ms: float, tags: Dict[str, str] = None):
        """Record a timer value"""
        with self._lock:
            key = self._make_key(name, tags)
            self._timers[key].append(MetricPoint(time.time(), duration_ms, tags or {}))
            self._check_thresholds(name, duration_ms, tags)
    
    def start_timer(self, name: str, tags: Dict[str, str] = None) -> "Timer":
        """Start a timer and return a Timer object"""
        return Timer(self, name, tags)
    
    def set_threshold(self, 
                     metric_name: str,
                     threshold: float,
                     severity: AlertSeverity = AlertSeverity.WARNING,
                     operator: str = "gt"):
        """Set a threshold for alerting"""
        self._thresholds[metric_name] = {
            "threshold": threshold,
            "severity": severity,
            "operator": operator
        }
    
    def register_alert_callback(self, callback: Callable[[Alert], None]):
        """Register a callback to be called when an alert is triggered"""
        self._alert_callbacks.append(callback)
    
    def _make_key(self, name: str, tags: Dict[str, str] = None) -> str:
        """Create a unique key for a metric with tags"""
        if not tags:
            return name
        tag_str = ",".join(f"{k}={v}" for k, v in sorted(tags.items()))
        return f"{name}@{tag_str}"
    
    def _check_thresholds(self, name: str, value: float, tags: Dict[str, str] = None):
        """Check if any thresholds are breached"""
        if name not in self._thresholds:
            return
        
        threshold_config = self._thresholds[name]
        threshold = threshold_config["threshold"]
        operator = threshold_config["operator"]
        
        triggered = False
        if operator == "gt" and value > threshold:
            triggered = True
        elif operator == "lt" and value < threshold:
            triggered = True
        elif operator == "eq" and value == threshold:
            triggered = True
        elif operator == "gte" and value >= threshold:
            triggered = True
        elif operator == "lte" and value <= threshold:
            triggered = True
        
        if triggered:
            alert_key = self._make_key(name, tags)
            if alert_key not in self._active_alerts:
                alert = Alert(
                    severity=threshold_config["severity"],
                    metric_name=name,
                    message=f"Metric {name} exceeded threshold: {value} {operator} {threshold}",
                    current_value=value,
                    threshold=threshold
                )
                self._active_alerts[alert_key] = alert
                # Trigger callbacks
                for callback in self._alert_callbacks:
                    try:
                        callback(alert)
                    except Exception as e:
                        print(f"Error in alert callback: {e}")
        else:
            # Clear alert if value returns to normal
            alert_key = self._make_key(name, tags)
            if alert_key in self._active_alerts:
                self._active_alerts[alert_key].resolved = True
                del self._active_alerts[alert_key]
    
    def _cleanup_old_metrics(self):
        """Periodically cleanup old metrics"""
        while True:
            try:
                time.sleep(300)  # Cleanup every 5 minutes
                cutoff_time = time.time() - self.retention_seconds
                
                with self._lock:
                    # Cleanup histograms
                    for key in list(self._histograms.keys()):
                        self._histograms[key] = deque(
                            [p for p in self._histograms[key] if p.timestamp > cutoff_time],
                            maxlen=self.histogram_bins
                        )
                    
                    # Cleanup timers
                    for key in list(self._timers.keys()):
                        self._timers[key] = deque(
                            [p for p in self._timers[key] if p.timestamp > cutoff_time],
                            maxlen=self.histogram_bins
                        )
            except Exception as e:
                print(f"Error in cleanup thread: {e}")
    
    def get_metric(self, name: str, tags: Dict[str, str] = None) -> Optional[float]:
        """Get the current value of a metric"""
        key = self._make_key(name, tags)
        
        if key in self._counters:
            return self._counters[key]
        elif key in self._gauges:
            return self._gauges[key]
        elif key in self._histograms and self._histograms[key]:
            return sum(p.value for p in self._histograms[key]) / len(self._histograms[key])
        return None
    
    def get_histogram_stats(self, name: str, tags: Dict[str, str] = None) -> Dict[str, float]:
        """Get histogram statistics (min, max, mean, p50, p95, p99)"""
        key = self._make_key(name, tags)
        if key not in self._timers or not self._timers[key]:
            return {}
        
        values = [p.value for p in self._timers[key]]
        if not values:
            return {}
        
        values.sort()
        n = len(values)
        
        return {
            "count": n,
            "min": values[0],
            "max": values[-1],
            "mean": sum(values) / n,
            "p50": values[n // 2],
            "p95": values[int(n * 0.95)],
            "p99": values[int(n * 0.99)]
        }
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all metrics as a dictionary"""
        with self._lock:
            metrics = {
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
                "histograms": {
                    key: len(values) for key, values in self._histograms.items()
                },
                "active_alerts": {
                    key: alert.to_dict() for key, alert in self._active_alerts.items()
                }
            }
            return metrics
    
    def reset(self):
        """Reset all metrics (useful for testing)"""
        with self._lock:
            self._counters.clear()
            self._gauges.clear()
            self._histograms.clear()
            self._timers.clear()
            self._active_alerts.clear()


class Timer:
    """Context manager for timing operations"""
    
    def __init__(self, collector: ZvecMetricsCollector, name: str, tags: Dict[str, str] = None):
        self.collector = collector
        self.name = name
        self.tags = tags
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time is not None:
            duration_ms = (self.time() - self.start_time) * 1000
            self.collector.record_timer(self.name, duration_ms, self.tags)


class ZvecMonitoringService:
    """
    Main monitoring service for Zvec integration.
    
    Provides:
    - Metrics collection
    - Health checks
    - Performance monitoring
    - Alerting
    - Dashboard data
    """
    
    def __init__(self, metrics_collector: ZvecMetricsCollector = None):
        self.metrics = metrics_collector or ZvecMetricsCollector()
        self._process = psutil.Process(os.getpid())
        self._start_time = time.time()
        
        # Setup default thresholds
        self._setup_default_thresholds()
    
    def _setup_default_thresholds(self):
        """Setup default alerting thresholds"""
        # RAG latency thresholds
        self.metrics.set_threshold("rag_latency_p95", 100.0, AlertSeverity.WARNING, "gt")
        self.metrics.set_threshold("rag_latency_p95", 1000.0, AlertSeverity.ERROR, "gt")
        
        # Sync failure rate
        self.metrics.set_threshold("sync_failure_rate", 5.0, AlertSeverity.WARNING, "gt")
        self.metrics.set_threshold("sync_failure_rate", 10.0, AlertSeverity.ERROR, "gt")
        
        # Memory usage
        self.metrics.set_threshold("memory_usage_percent", 80.0, AlertSeverity.WARNING, "gt")
        self.metrics.set_threshold("memory_usage_percent", 95.0, AlertSeverity.CRITICAL, "gt")
        
        # Database connections
        self.metrics.set_threshold("active_users", 900.0, AlertSeverity.INFO, "gt")
        self.metrics.set_threshold("active_users", 950.0, AlertSeverity.WARNING, "gt")
        
        # Conflict rate
        self.metrics.set_threshold("conflict_rate", 1.0, AlertSeverity.WARNING, "gt")
    
    def record_rag_query(self, 
                        latency_ms: float,
                        user_id: str = None,
                        query_type: str = "hybrid"):
        """Record a RAG query"""
        tags = {"query_type": query_type}
        if user_id:
            tags["user_id"] = user_id
        
        self.metrics.record_timer("rag_latency", latency_ms, tags)
        self.metrics.increment("rag_queries_total", 1.0, tags)
    
    def record_sync_operation(self,
                            synced_count: int,
                            failed_count: int,
                            duration_ms: float,
                            direction: str = "zvec_to_milvus"):
        """Record a sync operation"""
        tags = {"direction": direction}
        
        self.metrics.record_timer("sync_latency", duration_ms, tags)
        self.metrics.increment("sync_operations_total", 1.0, tags)
        self.metrics.increment("sync_vectors_synced", float(synced_count), tags)
        
        if failed_count > 0:
            self.metrics.increment("sync_failures_total", float(failed_count), tags)
        
        # Update sync success rate
        total = synced_count + failed_count
        if total > 0:
            success_rate = (synced_count / total) * 100
            self.metrics.set_gauge("sync_success_rate", success_rate, tags)
            failure_rate = (failed_count / total) * 100
            self.metrics.set_gauge("sync_failure_rate", failure_rate, tags)
    
    def record_conflict(self,
                       conflict_type: str,
                       resolution_strategy: str):
        """Record a conflict resolution"""
        tags = {
            "type": conflict_type,
            "resolution": resolution_strategy
        }
        self.metrics.increment("conflicts_total", 1.0, tags)
        self.metrics.increment(f"conflicts_{resolution_strategy}", 1.0, tags)
    
    def record_offline_mode(self, is_offline: bool, user_id: str = None):
        """Record offline mode transition"""
        tags = {"state": "offline" if is_offline else "online"}
        if user_id:
            tags["user_id"] = user_id
        
        self.metrics.increment("offline_transitions", 1.0, tags)
        self.metrics.set_gauge("is_offline", 1.0 if is_offline else 0.0, tags)
    
    def record_user_activity(self, user_id: str, active_connections: int):
        """Record user activity for concurrency monitoring"""
        self.metrics.set_gauge("user_active_connections", float(active_connections), {"user_id": user_id})
        self.metrics.set_gauge("active_users", float(active_connections))
    
    def get_rag_performance(self) -> Dict[str, Any]:
        """Get RAG performance metrics"""
        stats = self.metrics.get_histogram_stats("rag_latency")
        
        return {
            "latency": stats,
            "total_queries": self.metrics.get_metric("rag_queries_total") or 0,
            "queries_per_second": self._calculate_rate("rag_queries_total")
        }
    
    def get_sync_performance(self) -> Dict[str, Any]:
        """Get sync performance metrics"""
        stats = self.metrics.get_histogram_stats("sync_latency")
        
        return {
            "latency": stats,
            "total_syncs": self.metrics.get_metric("sync_operations_total") or 0,
            "syncs_per_minute": self._calculate_rate("sync_operations_total", 60),
            "vectors_synced": self.metrics.get_metric("sync_vectors_synced") or 0,
            "success_rate": self.metrics.get_metric("sync_success_rate") or 0.0,
            "failure_rate": self.metrics.get_metric("sync_failure_rate") or 0.0
        }
    
    def get_concurrency_metrics(self) -> Dict[str, Any]:
        """Get concurrency metrics"""
        return {
            "active_users": self.metrics.get_metric("active_users") or 0,
            "total_connections": self.metrics.get_metric("total_connections") or 0,
            "conflicts_total": self.metrics.get_metric("conflicts_total") or 0
        }
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get system resource metrics"""
        # Memory info
        memory_info = self._process.memory_info()
        memory_percent = self._process.memory_percent()
        
        self.metrics.set_gauge("memory_usage_bytes", float(memory_info.rss))
        self.metrics.set_gauge("memory_usage_percent", float(memory_percent))
        
        # CPU info
        cpu_percent = self._process.cpu_percent()
        self.metrics.set_gauge("cpu_usage_percent", float(cpu_percent))
        
        # Uptime
        uptime_seconds = time.time() - self._start_time
        self.metrics.set_gauge("uptime_seconds", uptime_seconds)
        
        return {
            "memory": {
                "rss_bytes": memory_info.rss,
                "percent": memory_percent
            },
            "cpu": {
                "percent": cpu_percent
            },
            "uptime_seconds": uptime_seconds
        }
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get overall health status"""
        metrics = self.metrics.get_all_metrics()
        
        # Check for critical alerts
        active_alerts = list(metrics["active_alerts"].values())
        critical_alerts = [a for a in active_alerts if a["severity"] == "critical"]
        error_alerts = [a for a in active_alerts if a["severity"] == "error"]
        
        if critical_alerts:
            overall_status = "critical"
        elif error_alerts:
            overall_status = "error"
        elif active_alerts:
            overall_status = "warning"
        else:
            overall_status = "healthy"
        
        return {
            "overall_status": overall_status,
            "active_alerts": active_alerts,
            "alert_count": len(active_alerts),
            "uptime_seconds": time.time() - self._start_time
        }
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get data for monitoring dashboard"""
        return {
            "rag": self.get_rag_performance(),
            "sync": self.get_sync_performance(),
            "concurrency": self.get_concurrency_metrics(),
            "system": self.get_system_metrics(),
            "health": self.get_health_status(),
            "timestamp": time.time()
        }
    
    def _calculate_rate(self, metric_name: str, window_seconds: int = 1) -> float:
        """Calculate rate per time window"""
        # This is a simplified version - in production, use a proper rate calculation
        current_value = self.metrics.get_metric(metric_name) or 0
        uptime_seconds = time.time() - self._start_time
        if uptime_seconds > 0:
            return (current_value / uptime_seconds) * window_seconds
        return 0.0


# Global monitoring service instance
_monitoring_service: Optional[ZvecMonitoringService] = None


def get_monitoring_service() -> ZvecMonitoringService:
    """Get the global monitoring service instance"""
    global _monitoring_service
    if _monitoring_service is None:
        _monitoring_service = ZvecMonitoringService()
    return _monitoring_service


def record_rag_query(latency_ms: float, user_id: str = None, query_type: str = "hybrid"):
    """Convenience function to record a RAG query"""
    service = get_monitoring_service()
    service.record_rag_query(latency_ms, user_id, query_type)


def record_sync_operation(synced_count: int, failed_count: int, duration_ms: float, direction: str = "zvec_to_milvus"):
    """Convenience function to record a sync operation"""
    service = get_monitoring_service()
    service.record_sync_operation(synced_count, failed_count, duration_ms, direction)


def record_conflict(conflict_type: str, resolution_strategy: str):
    """Convenience function to record a conflict"""
    service = get_monitoring_service()
    service.record_conflict(conflict_type, resolution_strategy)
