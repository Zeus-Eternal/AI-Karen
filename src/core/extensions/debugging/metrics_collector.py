"""
Extension Metrics Collector

Collects and aggregates performance metrics from extensions including
resource usage, request metrics, custom metrics, and performance indicators.
"""

import asyncio
import time
import psutil
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Union
from collections import defaultdict, deque
from dataclasses import dataclass
import statistics

from .models import MetricPoint


@dataclass
class MetricThreshold:
    """Defines thresholds for metric alerting."""
    warning: Union[int, float]
    critical: Union[int, float]
    comparison: str = "greater"  # greater, less, equal


@dataclass
class MetricAggregation:
    """Aggregated metric data over a time period."""
    metric_name: str
    count: int
    sum: float
    min: float
    max: float
    avg: float
    median: float
    p95: float
    p99: float
    timestamp: datetime


class MetricBuffer:
    """Thread-safe buffer for storing metric points."""
    
    def __init__(self, max_size: int = 10000):
        self.max_size = max_size
        self.buffer = deque(maxlen=max_size)
        self.lock = threading.Lock()
    
    def add(self, metric: MetricPoint):
        """Add a metric point to the buffer."""
        with self.lock:
            self.buffer.append(metric)
    
    def get_metrics(
        self,
        metric_name: Optional[str] = None,
        since: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[MetricPoint]:
        """Get metrics from buffer with optional filtering."""
        with self.lock:
            metrics = list(self.buffer)
        
        # Filter by metric name
        if metric_name:
            metrics = [m for m in metrics if m.metric_name == metric_name]
        
        # Filter by time
        if since:
            metrics = [m for m in metrics if m.timestamp >= since]
        
        # Apply limit
        if limit:
            metrics = metrics[-limit:]
        
        return metrics
    
    def clear(self):
        """Clear the buffer."""
        with self.lock:
            self.buffer.clear()


class ExtensionMetricsCollector:
    """
    Collects and manages metrics for extensions.
    
    Features:
    - Automatic resource usage collection
    - Custom metric registration
    - Metric aggregation and analysis
    - Threshold monitoring
    - Performance trend analysis
    """
    
    def __init__(
        self,
        extension_id: str,
        extension_name: str,
        collection_interval: float = 30.0,
        buffer_size: int = 10000,
        debug_manager=None
    ):
        self.extension_id = extension_id
        self.extension_name = extension_name
        self.collection_interval = collection_interval
        self.debug_manager = debug_manager
        
        # Metric storage
        self.buffer = MetricBuffer(buffer_size)
        self.custom_collectors: Dict[str, Callable] = {}
        self.thresholds: Dict[str, MetricThreshold] = {}
        
        # Collection state
        self._collecting = False
        self._collection_task: Optional[asyncio.Task] = None
        self._process = psutil.Process()
        
        # Performance tracking
        self._request_times = deque(maxlen=1000)
        self._error_counts = defaultdict(int)
        self._last_collection_time = time.time()
    
    async def start_collection(self):
        """Start automatic metric collection."""
        if self._collecting:
            return
        
        self._collecting = True
        self._collection_task = asyncio.create_task(self._collection_loop())
    
    async def stop_collection(self):
        """Stop automatic metric collection."""
        self._collecting = False
        
        if self._collection_task:
            self._collection_task.cancel()
            try:
                await self._collection_task
            except asyncio.CancelledError:
                pass
    
    def register_custom_collector(self, metric_name: str, collector: Callable[[], Union[int, float]]):
        """Register a custom metric collector function."""
        self.custom_collectors[metric_name] = collector
    
    def set_threshold(self, metric_name: str, threshold: MetricThreshold):
        """Set alerting threshold for a metric."""
        self.thresholds[metric_name] = threshold
    
    def record_metric(
        self,
        metric_name: str,
        value: Union[int, float],
        unit: str = "",
        tags: Optional[Dict[str, str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Record a custom metric value."""
        metric = MetricPoint(
            extension_id=self.extension_id,
            metric_name=metric_name,
            value=value,
            unit=unit,
            timestamp=datetime.utcnow(),
            tags=tags or {},
            metadata=metadata or {}
        )
        
        self.buffer.add(metric)
        
        # Check thresholds
        self._check_threshold(metric)
    
    def record_request_time(self, duration_ms: float):
        """Record request processing time."""
        self._request_times.append(duration_ms)
        self.record_metric("request_duration", duration_ms, "ms")
    
    def record_error(self, error_type: str):
        """Record an error occurrence."""
        self._error_counts[error_type] += 1
        self.record_metric(f"error_count_{error_type}", 1, "count")
    
    def get_metrics(
        self,
        metric_name: Optional[str] = None,
        since: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[MetricPoint]:
        """Get collected metrics with optional filtering."""
        return self.buffer.get_metrics(metric_name, since, limit)
    
    def get_metric_aggregation(
        self,
        metric_name: str,
        time_window: timedelta = timedelta(hours=1)
    ) -> Optional[MetricAggregation]:
        """Get aggregated metrics for a time window."""
        since = datetime.utcnow() - time_window
        metrics = self.get_metrics(metric_name, since)
        
        if not metrics:
            return None
        
        values = [m.value for m in metrics]
        
        return MetricAggregation(
            metric_name=metric_name,
            count=len(values),
            sum=sum(values),
            min=min(values),
            max=max(values),
            avg=statistics.mean(values),
            median=statistics.median(values),
            p95=self._percentile(values, 95),
            p99=self._percentile(values, 99),
            timestamp=datetime.utcnow()
        )
    
    def get_current_resource_usage(self) -> Dict[str, float]:
        """Get current resource usage metrics."""
        try:
            # CPU usage (percentage)
            cpu_percent = self._process.cpu_percent()
            
            # Memory usage
            memory_info = self._process.memory_info()
            memory_mb = memory_info.rss / (1024 * 1024)
            
            # I/O counters
            io_counters = self._process.io_counters()
            
            # Network usage (if available)
            network_connections = len(self._process.connections())
            
            return {
                'cpu_percent': cpu_percent,
                'memory_mb': memory_mb,
                'memory_percent': self._process.memory_percent(),
                'disk_read_mb': io_counters.read_bytes / (1024 * 1024),
                'disk_write_mb': io_counters.write_bytes / (1024 * 1024),
                'network_connections': network_connections,
                'threads': self._process.num_threads(),
                'file_descriptors': self._process.num_fds() if hasattr(self._process, 'num_fds') else 0
            }
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return {}
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary statistics."""
        current_time = time.time()
        time_window = current_time - 3600  # Last hour
        
        # Request metrics
        recent_requests = [t for t in self._request_times if t > time_window * 1000]
        
        request_stats = {}
        if recent_requests:
            request_stats = {
                'count': len(recent_requests),
                'avg_duration_ms': statistics.mean(recent_requests),
                'min_duration_ms': min(recent_requests),
                'max_duration_ms': max(recent_requests),
                'p95_duration_ms': self._percentile(recent_requests, 95),
                'requests_per_second': len(recent_requests) / 3600
            }
        
        # Error metrics
        total_errors = sum(self._error_counts.values())
        error_rate = total_errors / max(len(recent_requests), 1) if recent_requests else 0
        
        # Resource metrics
        resource_usage = self.get_current_resource_usage()
        
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'requests': request_stats,
            'errors': {
                'total_count': total_errors,
                'error_rate': error_rate,
                'by_type': dict(self._error_counts)
            },
            'resources': resource_usage,
            'collection_interval': self.collection_interval,
            'buffer_size': len(self.buffer.buffer)
        }
    
    def export_metrics(self, format: str = "json") -> str:
        """Export metrics in specified format."""
        metrics = self.get_metrics()
        
        if format.lower() == "json":
            import json
            return json.dumps([m.to_dict() for m in metrics], indent=2)
        elif format.lower() == "csv":
            import csv
            import io
            
            output = io.StringIO()
            if metrics:
                fieldnames = ['extension_id', 'metric_name', 'value', 'unit', 'timestamp', 'tags', 'metadata']
                writer = csv.DictWriter(output, fieldnames=fieldnames)
                writer.writeheader()
                
                for metric in metrics:
                    row = metric.to_dict()
                    row['tags'] = str(row['tags'])
                    row['metadata'] = str(row['metadata'])
                    writer.writerow(row)
            
            return output.getvalue()
        elif format.lower() == "prometheus":
            return self._export_prometheus_format(metrics)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    async def _collection_loop(self):
        """Main collection loop."""
        while self._collecting:
            try:
                await self._collect_metrics()
                await asyncio.sleep(self.collection_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                if self.debug_manager:
                    self.debug_manager.record_error(
                        self.extension_id,
                        "MetricsCollectionError",
                        str(e),
                        {"component": "metrics_collector"}
                    )
                await asyncio.sleep(self.collection_interval)
    
    async def _collect_metrics(self):
        """Collect all metrics."""
        current_time = datetime.utcnow()
        
        # Collect resource usage metrics
        resource_usage = self.get_current_resource_usage()
        for metric_name, value in resource_usage.items():
            self.buffer.add(MetricPoint(
                extension_id=self.extension_id,
                metric_name=f"resource_{metric_name}",
                value=value,
                unit=self._get_metric_unit(metric_name),
                timestamp=current_time
            ))
        
        # Collect custom metrics
        for metric_name, collector in self.custom_collectors.items():
            try:
                value = collector()
                if isinstance(value, (int, float)):
                    self.buffer.add(MetricPoint(
                        extension_id=self.extension_id,
                        metric_name=metric_name,
                        value=value,
                        unit="",
                        timestamp=current_time
                    ))
            except Exception as e:
                if self.debug_manager:
                    self.debug_manager.record_error(
                        self.extension_id,
                        "CustomMetricCollectionError",
                        str(e),
                        {"metric_name": metric_name}
                    )
        
        # Collect derived metrics
        self._collect_derived_metrics(current_time)
    
    def _collect_derived_metrics(self, timestamp: datetime):
        """Collect derived metrics from existing data."""
        # Request rate
        recent_requests = len([t for t in self._request_times if t > (time.time() - 60) * 1000])
        self.buffer.add(MetricPoint(
            extension_id=self.extension_id,
            metric_name="requests_per_minute",
            value=recent_requests,
            unit="requests/min",
            timestamp=timestamp
        ))
        
        # Average response time
        if self._request_times:
            avg_response_time = statistics.mean(list(self._request_times)[-100:])  # Last 100 requests
            self.buffer.add(MetricPoint(
                extension_id=self.extension_id,
                metric_name="avg_response_time",
                value=avg_response_time,
                unit="ms",
                timestamp=timestamp
            ))
        
        # Error rate
        total_errors = sum(self._error_counts.values())
        total_requests = len(self._request_times)
        error_rate = (total_errors / max(total_requests, 1)) * 100
        self.buffer.add(MetricPoint(
            extension_id=self.extension_id,
            metric_name="error_rate",
            value=error_rate,
            unit="percent",
            timestamp=timestamp
        ))
    
    def _check_threshold(self, metric: MetricPoint):
        """Check if metric exceeds threshold and generate alert."""
        threshold = self.thresholds.get(metric.metric_name)
        if not threshold:
            return
        
        exceeded = False
        severity = None
        
        if threshold.comparison == "greater":
            if metric.value >= threshold.critical:
                exceeded = True
                severity = "critical"
            elif metric.value >= threshold.warning:
                exceeded = True
                severity = "warning"
        elif threshold.comparison == "less":
            if metric.value <= threshold.critical:
                exceeded = True
                severity = "critical"
            elif metric.value <= threshold.warning:
                exceeded = True
                severity = "warning"
        
        if exceeded and self.debug_manager:
            self.debug_manager.create_alert(
                extension_id=self.extension_id,
                alert_type="threshold_violation",
                severity=severity,
                title=f"{metric.metric_name} threshold exceeded",
                message=f"{metric.metric_name} value {metric.value} exceeds {severity} threshold",
                metric_name=metric.metric_name,
                current_value=metric.value,
                threshold_value=threshold.critical if severity == "critical" else threshold.warning
            )
    
    def _get_metric_unit(self, metric_name: str) -> str:
        """Get appropriate unit for metric."""
        unit_map = {
            'cpu_percent': '%',
            'memory_mb': 'MB',
            'memory_percent': '%',
            'disk_read_mb': 'MB',
            'disk_write_mb': 'MB',
            'network_connections': 'count',
            'threads': 'count',
            'file_descriptors': 'count'
        }
        return unit_map.get(metric_name, '')
    
    def _percentile(self, values: List[float], percentile: int) -> float:
        """Calculate percentile of values."""
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        index = (percentile / 100) * (len(sorted_values) - 1)
        
        if index.is_integer():
            return sorted_values[int(index)]
        else:
            lower = sorted_values[int(index)]
            upper = sorted_values[int(index) + 1]
            return lower + (upper - lower) * (index - int(index))
    
    def _export_prometheus_format(self, metrics: List[MetricPoint]) -> str:
        """Export metrics in Prometheus format."""
        lines = []
        
        # Group metrics by name
        grouped_metrics = defaultdict(list)
        for metric in metrics:
            grouped_metrics[metric.metric_name].append(metric)
        
        for metric_name, metric_list in grouped_metrics.items():
            # Add help and type comments
            lines.append(f"# HELP {metric_name} Extension metric")
            lines.append(f"# TYPE {metric_name} gauge")
            
            # Add metric values
            for metric in metric_list:
                labels = []
                labels.append(f'extension_id="{metric.extension_id}"')
                
                for key, value in metric.tags.items():
                    labels.append(f'{key}="{value}"')
                
                label_str = "{" + ",".join(labels) + "}" if labels else ""
                timestamp = int(metric.timestamp.timestamp() * 1000)
                
                lines.append(f"{metric_name}{label_str} {metric.value} {timestamp}")
        
        return "\n".join(lines)