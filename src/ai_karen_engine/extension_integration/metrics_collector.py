"""Extension Metrics Collector - Comprehensive metrics collection and performance monitoring for extensions.

This module provides comprehensive metrics collection including:
- Performance metrics (execution time, memory usage, CPU usage)
- Health metrics (error rates, availability, response times)
- Usage metrics (API calls, data transfer, user interactions)
- Resource metrics (disk usage, network usage, file handles)
- Business metrics (feature usage, user engagement)
- Custom metrics and events
"""

from __future__ import annotations

import asyncio
import logging
import time
import threading
from collections import defaultdict, deque
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union, Callable
import json
import psutil
import statistics

from ai_karen_engine.extension_host.models import ExtensionManifest


class MetricType(Enum):
    """Types of metrics that can be collected."""
    
    COUNTER = "counter"           # Incrementing counter
    GAUGE = "gauge"              # Current value
    HISTOGRAM = "histogram"       # Distribution of values
    TIMER = "timer"              # Duration measurements
    EVENT = "event"              # Discrete events


class MetricUnit(Enum):
    """Units for metrics."""
    
    COUNT = "count"              # Simple count
    SECONDS = "seconds"           # Time in seconds
    MILLISECONDS = "milliseconds"  # Time in milliseconds
    BYTES = "bytes"              # Size in bytes
    PERCENT = "percent"          # Percentage
    REQUESTS_PER_SECOND = "requests_per_second"  # Rate
    ERROR_RATE = "error_rate"     # Error percentage


@dataclass
class MetricDefinition:
    """Definition of a metric."""
    
    name: str
    type: MetricType
    unit: MetricUnit
    description: str
    tags: Dict[str, str] = field(default_factory=dict)
    enabled: bool = True
    aggregation: Optional[str] = None  # "sum", "avg", "min", "max"


@dataclass
class MetricValue:
    """A single metric value with metadata."""
    
    name: str
    value: Union[int, float, str]
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    tags: Dict[str, str] = field(default_factory=dict)
    unit: Optional[MetricUnit] = None


@dataclass
class MetricSnapshot:
    """Snapshot of metrics at a point in time."""
    
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metrics: Dict[str, MetricValue] = field(default_factory=dict)
    extension_id: Optional[str] = None
    component: Optional[str] = None


@dataclass
class PerformanceMetrics:
    """Performance-related metrics."""
    
    execution_time: float = 0.0
    memory_usage: int = 0
    cpu_usage: float = 0.0
    disk_usage: int = 0
    network_io: Dict[str, int] = field(default_factory=dict)
    file_handles: int = 0
    thread_count: int = 0
    process_count: int = 0


@dataclass
class HealthMetrics:
    """Health-related metrics."""
    
    error_count: int = 0
    success_count: int = 0
    total_requests: int = 0
    error_rate: float = 0.0
    availability: float = 100.0
    response_time_avg: float = 0.0
    response_time_p95: float = 0.0
    response_time_p99: float = 0.0
    uptime: float = 0.0
    last_error: Optional[datetime] = None


@dataclass
class UsageMetrics:
    """Usage-related metrics."""
    
    api_calls: int = 0
    data_transfer: int = 0
    user_interactions: int = 0
    feature_usage: Dict[str, int] = field(default_factory=dict)
    active_users: int = 0
    session_duration: float = 0.0
    requests_per_minute: float = 0.0


class ExtensionMetricsCollector:
    """
    Comprehensive metrics collector for extensions.
    
    Provides:
    - Performance metrics collection
    - Health metrics monitoring
    - Usage metrics tracking
    - Resource metrics monitoring
    - Custom metrics support
    - Real-time aggregation
    - Historical data retention
    """
    
    def __init__(
        self,
        collection_interval: int = 60,  # seconds
        retention_period: int = 7 * 24 * 60 * 60,  # 7 days in seconds
        max_samples: int = 10000,
        enable_real_time: bool = True
    ):
        """
        Initialize the metrics collector.
        
        Args:
            collection_interval: Interval between metric collections
            retention_period: How long to retain metrics
            max_samples: Maximum number of samples to keep
            enable_real_time: Whether to enable real-time collection
        """
        self.collection_interval = collection_interval
        self.retention_period = retention_period
        self.max_samples = max_samples
        self.enable_real_time = enable_real_time
        
        # Metric storage
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_samples))
        self.metric_definitions: Dict[str, MetricDefinition] = {}
        
        # Extension-specific metrics
        self.extension_metrics: Dict[str, Dict[str, Any]] = defaultdict(dict)
        
        # Performance tracking
        self.performance_metrics: Dict[str, PerformanceMetrics] = defaultdict(PerformanceMetrics)
        self.health_metrics: Dict[str, HealthMetrics] = defaultdict(HealthMetrics)
        self.usage_metrics: Dict[str, UsageMetrics] = defaultdict(UsageMetrics)
        
        # Collection state
        self.collection_active = False
        self.collection_task: Optional[asyncio.Task] = None
        
        # Metrics callbacks
        self.metric_callbacks: List[Callable[[MetricSnapshot], None]] = []
        
        # Process handle for system metrics
        self.process = psutil.Process()
        
        self.logger = logging.getLogger("extension.metrics_collector")
        
        # Initialize default metrics
        self._initialize_default_metrics()
        
        self.logger.info("Extension metrics collector initialized")
    
    def _initialize_default_metrics(self) -> None:
        """Initialize default metric definitions."""
        try:
            # Performance metrics
            performance_metrics = [
                MetricDefinition(
                    name="execution_time",
                    type=MetricType.TIMER,
                    unit=MetricUnit.MILLISECONDS,
                    description="Extension execution time",
                    aggregation="avg"
                ),
                MetricDefinition(
                    name="memory_usage",
                    type=MetricType.GAUGE,
                    unit=MetricUnit.BYTES,
                    description="Memory usage",
                    aggregation="max"
                ),
                MetricDefinition(
                    name="cpu_usage",
                    type=MetricType.GAUGE,
                    unit=MetricUnit.PERCENT,
                    description="CPU usage",
                    aggregation="avg"
                ),
                MetricDefinition(
                    name="disk_usage",
                    type=MetricType.GAUGE,
                    unit=MetricUnit.BYTES,
                    description="Disk usage",
                    aggregation="max"
                )
            ]
            
            # Health metrics
            health_metrics = [
                MetricDefinition(
                    name="error_count",
                    type=MetricType.COUNTER,
                    unit=MetricUnit.COUNT,
                    description="Error count",
                    aggregation="sum"
                ),
                MetricDefinition(
                    name="success_count",
                    type=MetricType.COUNTER,
                    unit=MetricUnit.COUNT,
                    description="Success count",
                    aggregation="sum"
                ),
                MetricDefinition(
                    name="error_rate",
                    type=MetricType.GAUGE,
                    unit=MetricUnit.PERCENT,
                    description="Error rate",
                    aggregation="avg"
                ),
                MetricDefinition(
                    name="availability",
                    type=MetricType.GAUGE,
                    unit=MetricUnit.PERCENT,
                    description="Availability percentage",
                    aggregation="avg"
                )
            ]
            
            # Usage metrics
            usage_metrics = [
                MetricDefinition(
                    name="api_calls",
                    type=MetricType.COUNTER,
                    unit=MetricUnit.COUNT,
                    description="API call count",
                    aggregation="sum"
                ),
                MetricDefinition(
                    name="data_transfer",
                    type=MetricType.COUNTER,
                    unit=MetricUnit.BYTES,
                    description="Data transfer amount",
                    aggregation="sum"
                ),
                MetricDefinition(
                    name="user_interactions",
                    type=MetricType.COUNTER,
                    unit=MetricUnit.COUNT,
                    description="User interaction count",
                    aggregation="sum"
                ),
                MetricDefinition(
                    name="active_users",
                    type=MetricType.GAUGE,
                    unit=MetricUnit.COUNT,
                    description="Active user count",
                    aggregation="avg"
                )
            ]
            
            # Register all metrics
            all_metrics = performance_metrics + health_metrics + usage_metrics
            for metric_def in all_metrics:
                self.metric_definitions[metric_def.name] = metric_def
            
        except Exception as e:
            self.logger.error(f"Failed to initialize default metrics: {e}")
    
    def register_metric(self, metric_def: MetricDefinition) -> bool:
        """
        Register a new metric definition.
        
        Args:
            metric_def: Metric definition to register
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.metric_definitions[metric_def.name] = metric_def
            self.logger.info(f"Registered metric: {metric_def.name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to register metric {metric_def.name}: {e}")
            return False
    
    def record_metric(
        self,
        name: str,
        value: Union[int, float, str],
        tags: Optional[Dict[str, str]] = None,
        extension_id: Optional[str] = None
    ) -> bool:
        """
        Record a metric value.
        
        Args:
            name: Metric name
            value: Metric value
            tags: Additional tags
            extension_id: Extension ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if name not in self.metric_definitions:
                self.logger.warning(f"Unknown metric: {name}")
                return False
            
            metric_def = self.metric_definitions[name]
            if not metric_def.enabled:
                return False
            
            # Create metric value
            metric_value = MetricValue(
                name=name,
                value=value,
                timestamp=datetime.now(timezone.utc),
                tags=tags or {},
                unit=metric_def.unit
            )
            
            # Store metric
            self.metrics[name].append(metric_value)
            
            # Store extension-specific metric
            if extension_id:
                if "metrics" not in self.extension_metrics[extension_id]:
                    self.extension_metrics[extension_id]["metrics"] = {}
                if name not in self.extension_metrics[extension_id]["metrics"]:
                    self.extension_metrics[extension_id]["metrics"][name] = deque(maxlen=self.max_samples)
                self.extension_metrics[extension_id]["metrics"][name].append(metric_value)
            
            # Trigger callbacks
            if self.metric_callbacks:
                snapshot = MetricSnapshot(
                    metrics={name: metric_value},
                    extension_id=extension_id
                )
                for callback in self.metric_callbacks:
                    try:
                        callback(snapshot)
                    except Exception as e:
                        self.logger.error(f"Metric callback failed: {e}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to record metric {name}: {e}")
            return False
    
    def increment_counter(
        self,
        name: str,
        value: int = 1,
        tags: Optional[Dict[str, str]] = None,
        extension_id: Optional[str] = None
    ) -> bool:
        """
        Increment a counter metric.
        
        Args:
            name: Metric name
            value: Increment value
            tags: Additional tags
            extension_id: Extension ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get current value
            current_value = 0
            if self.metrics[name]:
                last_metric = self.metrics[name][-1]
                if isinstance(last_metric.value, (int, float)):
                    current_value = last_metric.value
            
            # Increment and record
            new_value = current_value + value
            return self.record_metric(name, new_value, tags, extension_id)
            
        except Exception as e:
            self.logger.error(f"Failed to increment counter {name}: {e}")
            return False
    
    def record_timer(
        self,
        name: str,
        duration: float,
        tags: Optional[Dict[str, str]] = None,
        extension_id: Optional[str] = None
    ) -> bool:
        """
        Record a timer metric.
        
        Args:
            name: Metric name
            duration: Duration in seconds
            tags: Additional tags
            extension_id: Extension ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Convert to milliseconds if needed
            metric_def = self.metric_definitions.get(name)
            if metric_def and metric_def.unit == MetricUnit.MILLISECONDS:
                duration = duration * 1000
            
            return self.record_metric(name, duration, tags, extension_id)
            
        except Exception as e:
            self.logger.error(f"Failed to record timer {name}: {e}")
            return False
    
    def collect_performance_metrics(self, extension_id: Optional[str] = None) -> PerformanceMetrics:
        """
        Collect performance metrics.
        
        Args:
            extension_id: Extension ID to collect metrics for
            
        Returns:
            Performance metrics
        """
        try:
            metrics = PerformanceMetrics()
            
            # Get system metrics
            metrics.memory_usage = self.process.memory_info().rss
            metrics.cpu_usage = self.process.cpu_percent()
            metrics.disk_usage = sum(d.stat().st_size for d in Path.cwd().rglob('*') if d.is_file())
            metrics.file_handles = len(self.process.open_files())
            metrics.thread_count = self.process.num_threads()
            
            # Network I/O
            network_io = self.process.io_counters()
            metrics.network_io = {
                "read_bytes": network_io.read_bytes,
                "write_bytes": network_io.write_bytes
            }
            
            # Store metrics
            if extension_id:
                self.performance_metrics[extension_id] = metrics
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Failed to collect performance metrics: {e}")
            return PerformanceMetrics()
    
    def collect_health_metrics(self, extension_id: Optional[str] = None) -> HealthMetrics:
        """
        Collect health metrics.
        
        Args:
            extension_id: Extension ID to collect metrics for
            
        Returns:
            Health metrics
        """
        try:
            metrics = HealthMetrics()
            
            # Calculate error rate
            error_count = 0
            success_count = 0
            
            if "error_count" in self.metrics:
                error_count = sum(m.value for m in self.metrics["error_count"] if isinstance(m.value, (int, float)))
            
            if "success_count" in self.metrics:
                success_count = sum(m.value for m in self.metrics["success_count"] if isinstance(m.value, (int, float)))
            
            metrics.error_count = int(error_count)
            metrics.success_count = int(success_count)
            metrics.total_requests = metrics.error_count + metrics.success_count
            
            if metrics.total_requests > 0:
                metrics.error_rate = (metrics.error_count / metrics.total_requests) * 100
                metrics.availability = ((metrics.total_requests - metrics.error_count) / metrics.total_requests) * 100
            
            # Calculate response time metrics
            if "execution_time" in self.metrics and self.metrics["execution_time"]:
                execution_times = [m.value for m in self.metrics["execution_time"] if isinstance(m.value, (int, float))]
                if execution_times:
                    metrics.response_time_avg = statistics.mean(execution_times)
                    metrics.response_time_p95 = statistics.quantiles(execution_times, n=20)[18]  # 95th percentile
                    metrics.response_time_p99 = statistics.quantiles(execution_times, n=100)[98]  # 99th percentile
            
            # Store metrics
            if extension_id:
                self.health_metrics[extension_id] = metrics
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Failed to collect health metrics: {e}")
            return HealthMetrics()
    
    def collect_usage_metrics(self, extension_id: Optional[str] = None) -> UsageMetrics:
        """
        Collect usage metrics.
        
        Args:
            extension_id: Extension ID to collect metrics for
            
        Returns:
            Usage metrics
        """
        try:
            metrics = UsageMetrics()
            
            # Get API calls
            if "api_calls" in self.metrics and self.metrics["api_calls"]:
                metrics.api_calls = int(self.metrics["api_calls"][-1].value)
            
            # Get data transfer
            if "data_transfer" in self.metrics and self.metrics["data_transfer"]:
                metrics.data_transfer = int(self.metrics["data_transfer"][-1].value)
            
            # Get user interactions
            if "user_interactions" in self.metrics and self.metrics["user_interactions"]:
                metrics.user_interactions = int(self.metrics["user_interactions"][-1].value)
            
            # Get active users
            if "active_users" in self.metrics and self.metrics["active_users"]:
                metrics.active_users = int(self.metrics["active_users"][-1].value)
            
            # Store metrics
            if extension_id:
                self.usage_metrics[extension_id] = metrics
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Failed to collect usage metrics: {e}")
            return UsageMetrics()
    
    def get_metrics(
        self,
        name: Optional[str] = None,
        extension_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> Dict[str, List[MetricValue]]:
        """
        Get metrics with optional filtering.
        
        Args:
            name: Metric name filter
            extension_id: Extension ID filter
            start_time: Start time filter
            end_time: End time filter
            limit: Maximum number of values to return
            
        Returns:
            Dictionary of metric values
        """
        try:
            result = {}
            
            # Determine which metrics to include
            if name:
                metrics_to_check = [name]
            else:
                metrics_to_check = list(self.metrics.keys())
            
            for metric_name in metrics_to_check:
                if metric_name not in self.metrics:
                    continue
                
                # Get metric values
                if extension_id and extension_id in self.extension_metrics:
                    if "metrics" in self.extension_metrics[extension_id] and metric_name in self.extension_metrics[extension_id]["metrics"]:
                        values = list(self.extension_metrics[extension_id]["metrics"][metric_name])
                    else:
                        continue
                else:
                    values = list(self.metrics[metric_name])
                
                # Apply time filters
                if start_time or end_time:
                    filtered_values = []
                    for value in values:
                        if start_time and value.timestamp < start_time:
                            continue
                        if end_time and value.timestamp > end_time:
                            continue
                        filtered_values.append(value)
                    values = filtered_values
                
                # Apply limit
                if limit:
                    values = values[-limit:]
                
                if values:
                    result[metric_name] = values
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to get metrics: {e}")
            return {}
    
    def get_aggregated_metrics(
        self,
        name: str,
        aggregation: str = "avg",
        extension_id: Optional[str] = None,
        time_window: Optional[int] = None  # seconds
    ) -> Optional[float]:
        """
        Get aggregated metric value.
        
        Args:
            name: Metric name
            aggregation: Aggregation function ("avg", "sum", "min", "max", "count")
            extension_id: Extension ID
            time_window: Time window in seconds
            
        Returns:
            Aggregated value or None
        """
        try:
            # Get metric values
            metrics = self.get_metrics(name, extension_id, limit=None)
            if name not in metrics or not metrics[name]:
                return None
            
            values = [v.value for v in metrics[name] if isinstance(v.value, (int, float))]
            if not values:
                return None
            
            # Apply aggregation
            if aggregation == "avg":
                return statistics.mean(values)
            elif aggregation == "sum":
                return sum(values)
            elif aggregation == "min":
                return min(values)
            elif aggregation == "max":
                return max(values)
            elif aggregation == "count":
                return len(values)
            else:
                self.logger.warning(f"Unknown aggregation: {aggregation}")
                return None
            
        except Exception as e:
            self.logger.error(f"Failed to get aggregated metrics: {e}")
            return None
    
    def start_collection(self) -> None:
        """Start automatic metrics collection."""
        try:
            if self.collection_active:
                self.logger.warning("Metrics collection already active")
                return
            
            self.collection_active = True
            self.collection_task = asyncio.create_task(self._collection_loop())
            
            self.logger.info("Started metrics collection")
            
        except Exception as e:
            self.logger.error(f"Failed to start metrics collection: {e}")
    
    def stop_collection(self) -> None:
        """Stop automatic metrics collection."""
        try:
            self.collection_active = False
            
            if self.collection_task:
                self.collection_task.cancel()
                self.collection_task = None
            
            self.logger.info("Stopped metrics collection")
            
        except Exception as e:
            self.logger.error(f"Failed to stop metrics collection: {e}")
    
    async def _collection_loop(self) -> None:
        """Main collection loop."""
        try:
            while self.collection_active:
                # Collect system metrics
                perf_metrics = self.collect_performance_metrics()
                health_metrics = self.collect_health_metrics()
                usage_metrics = self.collect_usage_metrics()
                
                # Record system metrics
                self.record_metric("system_memory_usage", perf_metrics.memory_usage)
                self.record_metric("system_cpu_usage", perf_metrics.cpu_usage)
                self.record_metric("system_disk_usage", perf_metrics.disk_usage)
                self.record_metric("system_file_handles", perf_metrics.file_handles)
                self.record_metric("system_thread_count", perf_metrics.thread_count)
                
                # Wait for next collection
                await asyncio.sleep(self.collection_interval)
                
        except asyncio.CancelledError:
            self.logger.info("Metrics collection cancelled")
        except Exception as e:
            self.logger.error(f"Metrics collection error: {e}")
    
    def add_metric_callback(self, callback: Callable[[MetricSnapshot], None]) -> None:
        """
        Add a callback to be called when metrics are recorded.
        
        Args:
            callback: Callback function
        """
        self.metric_callbacks.append(callback)
    
    def remove_metric_callback(self, callback: Callable[[MetricSnapshot], None]) -> None:
        """
        Remove a metric callback.
        
        Args:
            callback: Callback function to remove
        """
        if callback in self.metric_callbacks:
            self.metric_callbacks.remove(callback)
    
    def export_metrics(
        self,
        format: str = "json",
        extension_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> str:
        """
        Export metrics in various formats.
        
        Args:
            format: Export format ("json", "csv", "prometheus")
            extension_id: Extension ID filter
            start_time: Start time filter
            end_time: End time filter
            
        Returns:
            Exported metrics as string
        """
        try:
            metrics = self.get_metrics(extension_id=extension_id, start_time=start_time, end_time=end_time)
            
            if format == "json":
                return self._export_json(metrics)
            elif format == "csv":
                return self._export_csv(metrics)
            elif format == "prometheus":
                return self._export_prometheus(metrics)
            else:
                raise ValueError(f"Unsupported export format: {format}")
                
        except Exception as e:
            self.logger.error(f"Failed to export metrics: {e}")
            return ""
    
    def _export_json(self, metrics: Dict[str, List[MetricValue]]) -> str:
        """Export metrics as JSON."""
        try:
            export_data = {}
            for name, values in metrics.items():
                export_data[name] = [
                    {
                        "value": v.value,
                        "timestamp": v.timestamp.isoformat(),
                        "tags": v.tags,
                        "unit": v.unit.value if v.unit else None
                    }
                    for v in values
                ]
            return json.dumps(export_data, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to export JSON: {e}")
            return "{}"
    
    def _export_csv(self, metrics: Dict[str, List[MetricValue]]) -> str:
        """Export metrics as CSV."""
        try:
            lines = ["metric_name,value,timestamp,unit,tags"]
            for name, values in metrics.items():
                for v in values:
                    tags_str = json.dumps(v.tags) if v.tags else ""
                    unit_str = v.unit.value if v.unit else ""
                    lines.append(f"{name},{v.value},{v.timestamp.isoformat()},{unit_str},{tags_str}")
            return "\n".join(lines)
        except Exception as e:
            self.logger.error(f"Failed to export CSV: {e}")
            return ""
    
    def _export_prometheus(self, metrics: Dict[str, List[MetricValue]]) -> str:
        """Export metrics in Prometheus format."""
        try:
            lines = []
            for name, values in metrics.items():
                if values:
                    latest = values[-1]
                    tags_str = ""
                    if latest.tags:
                        tags_str = "{" + ",".join([f'{k}="{v}"' for k, v in latest.tags.items()]) + "}"
                    lines.append(f"{name}{tags_str} {latest.value}")
            return "\n".join(lines)
        except Exception as e:
            self.logger.error(f"Failed to export Prometheus: {e}")
            return ""
    
    def cleanup_old_metrics(self) -> None:
        """Clean up metrics older than retention period."""
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(seconds=self.retention_period)
            
            for name, values in self.metrics.items():
                # Filter out old values
                filtered_values = deque(
                    (v for v in values if v.timestamp >= cutoff_time),
                    maxlen=self.max_samples
                )
                self.metrics[name] = filtered_values
            
            self.logger.info("Cleaned up old metrics")
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup old metrics: {e}")


__all__ = [
    "ExtensionMetricsCollector",
    "MetricDefinition",
    "MetricValue",
    "MetricSnapshot",
    "PerformanceMetrics",
    "HealthMetrics",
    "UsageMetrics",
    "MetricType",
    "MetricUnit",
]