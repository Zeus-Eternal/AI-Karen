"""
Extension API Performance Monitor

Comprehensive performance monitoring for extension APIs including
response times, throughput, error rates, and resource utilization.
"""

import asyncio
import logging
import time
import psutil
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict, deque
from contextlib import asynccontextmanager
import json
import statistics

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """Individual performance metric data point."""
    timestamp: datetime
    endpoint: str
    method: str
    response_time: float
    status_code: int
    request_size: int = 0
    response_size: int = 0
    user_id: Optional[str] = None
    error_type: Optional[str] = None


@dataclass
class ResourceUsage:
    """System resource usage snapshot."""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    disk_io_read_mb: float
    disk_io_write_mb: float
    network_sent_mb: float
    network_recv_mb: float


@dataclass
class EndpointStats:
    """Statistics for a specific endpoint."""
    endpoint: str
    method: str
    total_requests: int = 0
    error_count: int = 0
    total_response_time: float = 0.0
    min_response_time: float = float('inf')
    max_response_time: float = 0.0
    response_times: deque = field(default_factory=lambda: deque(maxlen=1000))
    status_codes: Dict[int, int] = field(default_factory=lambda: defaultdict(int))
    hourly_requests: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    last_request: Optional[datetime] = None

    @property
    def average_response_time(self) -> float:
        return self.total_response_time / self.total_requests if self.total_requests > 0 else 0.0

    @property
    def error_rate(self) -> float:
        return (self.error_count / self.total_requests * 100) if self.total_requests > 0 else 0.0

    @property
    def requests_per_hour(self) -> float:
        current_hour = datetime.utcnow().strftime('%Y-%m-%d-%H')
        return self.hourly_requests.get(current_hour, 0)

    def get_percentiles(self) -> Dict[str, float]:
        """Calculate response time percentiles."""
        if not self.response_times:
            return {'p50': 0, 'p90': 0, 'p95': 0, 'p99': 0}
        
        sorted_times = sorted(self.response_times)
        length = len(sorted_times)
        
        return {
            'p50': sorted_times[int(length * 0.5)] if length > 0 else 0,
            'p90': sorted_times[int(length * 0.9)] if length > 0 else 0,
            'p95': sorted_times[int(length * 0.95)] if length > 0 else 0,
            'p99': sorted_times[int(length * 0.99)] if length > 0 else 0,
        }


class ExtensionPerformanceMonitor:
    """Comprehensive performance monitoring for extension APIs."""

    def __init__(self, retention_hours: int = 24):
        self.retention_hours = retention_hours
        self.metrics: deque = deque(maxlen=100000)  # Store raw metrics
        self.endpoint_stats: Dict[str, EndpointStats] = defaultdict(lambda: EndpointStats("", ""))
        self.resource_usage: deque = deque(maxlen=2880)  # 24 hours at 30-second intervals
        
        # Performance thresholds
        self.response_time_threshold = 2.0  # seconds
        self.error_rate_threshold = 5.0     # percentage
        self.cpu_threshold = 80.0           # percentage
        self.memory_threshold = 85.0        # percentage
        
        # Monitoring state
        self.monitoring_active = False
        self.resource_monitor_task = None
        self.cleanup_task = None
        
        # Performance alerts
        self.performance_alerts: List[Dict[str, Any]] = []
        self.alert_callbacks: List[callable] = []

    async def start_monitoring(self, resource_check_interval: int = 30):
        """Start performance monitoring."""
        if self.monitoring_active:
            logger.warning("Performance monitoring is already active")
            return
        
        self.monitoring_active = True
        logger.info("Starting extension performance monitoring")
        
        # Start resource monitoring
        self.resource_monitor_task = asyncio.create_task(
            self._resource_monitoring_loop(resource_check_interval)
        )
        
        # Start cleanup task
        self.cleanup_task = asyncio.create_task(
            self._cleanup_loop()
        )

    async def stop_monitoring(self):
        """Stop performance monitoring."""
        self.monitoring_active = False
        
        if self.resource_monitor_task:
            self.resource_monitor_task.cancel()
            try:
                await self.resource_monitor_task
            except asyncio.CancelledError:
                pass
        
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Stopped extension performance monitoring")

    def record_request(
        self,
        endpoint: str,
        method: str,
        response_time: float,
        status_code: int,
        request_size: int = 0,
        response_size: int = 0,
        user_id: Optional[str] = None,
        error_type: Optional[str] = None
    ):
        """Record a request performance metric."""
        timestamp = datetime.utcnow()
        
        # Create metric record
        metric = PerformanceMetric(
            timestamp=timestamp,
            endpoint=endpoint,
            method=method,
            response_time=response_time,
            status_code=status_code,
            request_size=request_size,
            response_size=response_size,
            user_id=user_id,
            error_type=error_type
        )
        
        self.metrics.append(metric)
        
        # Update endpoint statistics
        endpoint_key = f"{method}:{endpoint}"
        stats = self.endpoint_stats[endpoint_key]
        
        if not stats.endpoint:  # Initialize if new
            stats.endpoint = endpoint
            stats.method = method
        
        stats.total_requests += 1
        stats.total_response_time += response_time
        stats.response_times.append(response_time)
        stats.status_codes[status_code] += 1
        stats.last_request = timestamp
        
        # Update min/max response times
        stats.min_response_time = min(stats.min_response_time, response_time)
        stats.max_response_time = max(stats.max_response_time, response_time)
        
        # Update hourly request count
        hour_key = timestamp.strftime('%Y-%m-%d-%H')
        stats.hourly_requests[hour_key] += 1
        
        # Count errors
        if status_code >= 400:
            stats.error_count += 1
        
        # Check for performance issues
        asyncio.create_task(self._check_performance_alerts(stats, response_time, status_code))

    async def _resource_monitoring_loop(self, interval: int):
        """Monitor system resource usage."""
        while self.monitoring_active:
            try:
                # Get CPU usage
                cpu_percent = psutil.cpu_percent(interval=1)
                
                # Get memory usage
                memory = psutil.virtual_memory()
                memory_percent = memory.percent
                memory_used_mb = memory.used / (1024 * 1024)
                
                # Get disk I/O
                disk_io = psutil.disk_io_counters()
                disk_read_mb = disk_io.read_bytes / (1024 * 1024) if disk_io else 0
                disk_write_mb = disk_io.write_bytes / (1024 * 1024) if disk_io else 0
                
                # Get network I/O
                network_io = psutil.net_io_counters()
                network_sent_mb = network_io.bytes_sent / (1024 * 1024) if network_io else 0
                network_recv_mb = network_io.bytes_recv / (1024 * 1024) if network_io else 0
                
                # Record resource usage
                resource_usage = ResourceUsage(
                    timestamp=datetime.utcnow(),
                    cpu_percent=cpu_percent,
                    memory_percent=memory_percent,
                    memory_used_mb=memory_used_mb,
                    disk_io_read_mb=disk_read_mb,
                    disk_io_write_mb=disk_write_mb,
                    network_sent_mb=network_sent_mb,
                    network_recv_mb=network_recv_mb
                )
                
                self.resource_usage.append(resource_usage)
                
                # Check resource thresholds
                await self._check_resource_alerts(resource_usage)
                
                await asyncio.sleep(interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in resource monitoring loop: {e}")
                await asyncio.sleep(interval)

    async def _cleanup_loop(self):
        """Cleanup old metrics and data."""
        while self.monitoring_active:
            try:
                await asyncio.sleep(3600)  # Run every hour
                await self._cleanup_old_data()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")

    async def _cleanup_old_data(self):
        """Clean up old performance data."""
        cutoff_time = datetime.utcnow() - timedelta(hours=self.retention_hours)
        
        # Clean up metrics
        while self.metrics and self.metrics[0].timestamp < cutoff_time:
            self.metrics.popleft()
        
        # Clean up resource usage
        while self.resource_usage and self.resource_usage[0].timestamp < cutoff_time:
            self.resource_usage.popleft()
        
        # Clean up hourly request counts
        cutoff_hour = cutoff_time.strftime('%Y-%m-%d-%H')
        for stats in self.endpoint_stats.values():
            old_hours = [hour for hour in stats.hourly_requests.keys() if hour < cutoff_hour]
            for hour in old_hours:
                del stats.hourly_requests[hour]
        
        logger.debug(f"Cleaned up performance data older than {self.retention_hours} hours")

    async def _check_performance_alerts(self, stats: EndpointStats, response_time: float, status_code: int):
        """Check for performance-related alerts."""
        alerts = []
        
        # Check response time threshold
        if response_time > self.response_time_threshold:
            alerts.append({
                'type': 'slow_response',
                'endpoint': f"{stats.method}:{stats.endpoint}",
                'response_time': response_time,
                'threshold': self.response_time_threshold,
                'severity': 'warning' if response_time < self.response_time_threshold * 2 else 'error'
            })
        
        # Check error rate threshold
        if stats.error_rate > self.error_rate_threshold:
            alerts.append({
                'type': 'high_error_rate',
                'endpoint': f"{stats.method}:{stats.endpoint}",
                'error_rate': stats.error_rate,
                'threshold': self.error_rate_threshold,
                'severity': 'warning' if stats.error_rate < self.error_rate_threshold * 2 else 'error'
            })
        
        # Record and notify alerts
        for alert in alerts:
            alert['timestamp'] = datetime.utcnow().isoformat()
            self.performance_alerts.append(alert)
            
            # Notify callbacks
            for callback in self.alert_callbacks:
                try:
                    await callback(alert)
                except Exception as e:
                    logger.error(f"Error in performance alert callback: {e}")

    async def _check_resource_alerts(self, resource_usage: ResourceUsage):
        """Check for resource usage alerts."""
        alerts = []
        
        # Check CPU threshold
        if resource_usage.cpu_percent > self.cpu_threshold:
            alerts.append({
                'type': 'high_cpu_usage',
                'cpu_percent': resource_usage.cpu_percent,
                'threshold': self.cpu_threshold,
                'severity': 'warning' if resource_usage.cpu_percent < self.cpu_threshold * 1.1 else 'error'
            })
        
        # Check memory threshold
        if resource_usage.memory_percent > self.memory_threshold:
            alerts.append({
                'type': 'high_memory_usage',
                'memory_percent': resource_usage.memory_percent,
                'memory_used_mb': resource_usage.memory_used_mb,
                'threshold': self.memory_threshold,
                'severity': 'warning' if resource_usage.memory_percent < self.memory_threshold * 1.05 else 'error'
            })
        
        # Record and notify alerts
        for alert in alerts:
            alert['timestamp'] = datetime.utcnow().isoformat()
            self.performance_alerts.append(alert)
            
            # Notify callbacks
            for callback in self.alert_callbacks:
                try:
                    await callback(alert)
                except Exception as e:
                    logger.error(f"Error in resource alert callback: {e}")

    def add_alert_callback(self, callback: callable):
        """Add a callback for performance alerts."""
        self.alert_callbacks.append(callback)

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get overall performance summary."""
        if not self.endpoint_stats:
            return {
                'total_requests': 0,
                'total_errors': 0,
                'average_response_time': 0,
                'error_rate': 0,
                'endpoints_count': 0,
                'last_updated': datetime.utcnow().isoformat()
            }
        
        total_requests = sum(stats.total_requests for stats in self.endpoint_stats.values())
        total_errors = sum(stats.error_count for stats in self.endpoint_stats.values())
        total_response_time = sum(stats.total_response_time for stats in self.endpoint_stats.values())
        
        return {
            'total_requests': total_requests,
            'total_errors': total_errors,
            'average_response_time': total_response_time / total_requests if total_requests > 0 else 0,
            'error_rate': (total_errors / total_requests * 100) if total_requests > 0 else 0,
            'endpoints_count': len(self.endpoint_stats),
            'monitoring_active': self.monitoring_active,
            'last_updated': datetime.utcnow().isoformat()
        }

    def get_endpoint_performance(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get performance data for top endpoints."""
        sorted_endpoints = sorted(
            self.endpoint_stats.values(),
            key=lambda x: x.total_requests,
            reverse=True
        )[:limit]
        
        return [
            {
                'endpoint': f"{stats.method}:{stats.endpoint}",
                'total_requests': stats.total_requests,
                'error_count': stats.error_count,
                'error_rate': stats.error_rate,
                'average_response_time': stats.average_response_time,
                'min_response_time': stats.min_response_time if stats.min_response_time != float('inf') else 0,
                'max_response_time': stats.max_response_time,
                'requests_per_hour': stats.requests_per_hour,
                'percentiles': stats.get_percentiles(),
                'status_codes': dict(stats.status_codes),
                'last_request': stats.last_request.isoformat() if stats.last_request else None
            }
            for stats in sorted_endpoints
        ]

    def get_resource_usage_summary(self) -> Dict[str, Any]:
        """Get system resource usage summary."""
        if not self.resource_usage:
            return {
                'current_cpu': 0,
                'current_memory': 0,
                'average_cpu': 0,
                'average_memory': 0,
                'peak_cpu': 0,
                'peak_memory': 0,
                'last_updated': datetime.utcnow().isoformat()
            }
        
        recent_usage = list(self.resource_usage)[-60:]  # Last 30 minutes
        
        current = recent_usage[-1] if recent_usage else None
        cpu_values = [usage.cpu_percent for usage in recent_usage]
        memory_values = [usage.memory_percent for usage in recent_usage]
        
        return {
            'current_cpu': current.cpu_percent if current else 0,
            'current_memory': current.memory_percent if current else 0,
            'current_memory_mb': current.memory_used_mb if current else 0,
            'average_cpu': statistics.mean(cpu_values) if cpu_values else 0,
            'average_memory': statistics.mean(memory_values) if memory_values else 0,
            'peak_cpu': max(cpu_values) if cpu_values else 0,
            'peak_memory': max(memory_values) if memory_values else 0,
            'samples_count': len(recent_usage),
            'monitoring_active': self.monitoring_active,
            'last_updated': datetime.utcnow().isoformat()
        }

    def get_performance_trends(self, hours: int = 24) -> Dict[str, Any]:
        """Get performance trends over time."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        recent_metrics = [m for m in self.metrics if m.timestamp >= cutoff_time]
        
        if not recent_metrics:
            return {
                'hourly_requests': [],
                'hourly_errors': [],
                'hourly_avg_response_time': [],
                'period_hours': hours,
                'last_updated': datetime.utcnow().isoformat()
            }
        
        # Group by hour
        hourly_data = defaultdict(lambda: {'requests': 0, 'errors': 0, 'response_times': []})
        
        for metric in recent_metrics:
            hour_key = metric.timestamp.strftime('%Y-%m-%d %H:00')
            hourly_data[hour_key]['requests'] += 1
            hourly_data[hour_key]['response_times'].append(metric.response_time)
            
            if metric.status_code >= 400:
                hourly_data[hour_key]['errors'] += 1
        
        # Convert to time series
        sorted_hours = sorted(hourly_data.keys())
        
        hourly_requests = [{'time': hour, 'value': hourly_data[hour]['requests']} for hour in sorted_hours]
        hourly_errors = [{'time': hour, 'value': hourly_data[hour]['errors']} for hour in sorted_hours]
        hourly_avg_response_time = [
            {
                'time': hour,
                'value': statistics.mean(hourly_data[hour]['response_times']) if hourly_data[hour]['response_times'] else 0
            }
            for hour in sorted_hours
        ]
        
        return {
            'hourly_requests': hourly_requests,
            'hourly_errors': hourly_errors,
            'hourly_avg_response_time': hourly_avg_response_time,
            'period_hours': hours,
            'last_updated': datetime.utcnow().isoformat()
        }

    def get_recent_alerts(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent performance alerts."""
        return self.performance_alerts[-limit:] if self.performance_alerts else []

    @asynccontextmanager
    async def measure_request(self, endpoint: str, method: str, user_id: str = None):
        """Context manager to measure request performance."""
        start_time = time.time()
        status_code = 200
        error_type = None
        
        try:
            yield
        except Exception as e:
            status_code = 500
            error_type = type(e).__name__
            raise
        finally:
            end_time = time.time()
            response_time = end_time - start_time
            
            self.record_request(
                endpoint=endpoint,
                method=method,
                response_time=response_time,
                status_code=status_code,
                user_id=user_id,
                error_type=error_type
            )


# Global performance monitor instance
extension_performance_monitor = ExtensionPerformanceMonitor()