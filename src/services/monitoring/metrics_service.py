"""
Metrics Service

This service collects and aggregates metrics for the system.
"""

import logging
import time
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from collections import defaultdict, deque
import threading

from .internal.metrics_adapters import MetricsBackend


@dataclass
class Metric:
    """A metric data point."""
    name: str
    value: float
    timestamp: float
    tags: Dict[str, str] = None
    metadata: Dict[str, Any] = None


@dataclass
class MetricConfig:
    """Configuration for metrics collection."""
    retention_period: int = 86400  # 24 hours in seconds
    aggregation_interval: int = 60  # 1 minute in seconds
    max_metrics_per_name: int = 10000


class MetricsService:
    """
    Metrics Service collects and aggregates metrics for the system.
    
    This service provides metric collection, aggregation,
    and querying capabilities.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Metrics Service.
        
        Args:
            config: Configuration for metrics
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Metrics configuration
        self.metrics_config = MetricConfig(**config.get("metrics", {}))
        
        # Metrics storage
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(
            maxlen=self.metrics_config.max_metrics_per_name
        ))
        
        # Aggregated metrics
        self.aggregated_metrics: Dict[str, Dict[str, float]] = {}
        
        # Metrics backends
        self.backends: List[MetricsBackend] = []
        
        # Lock for thread safety
        self.lock = threading.Lock()
        
        # Initialize backends
        self._initialize_backends()
        
        # Start aggregation task
        self._start_aggregation_task()
    
    def _initialize_backends(self):
        """Initialize metrics backends."""
        # Implementation would initialize actual metrics backends
        # (e.g., Prometheus, Graphite, etc.)
        self.logger.info("Initialized metrics backends")
    
    def _start_aggregation_task(self):
        """Start the background aggregation task."""
        import threading
        self.aggregation_thread = threading.Thread(
            target=self._aggregation_loop,
            daemon=True
        )
        self.aggregation_thread.start()
    
    def _aggregation_loop(self):
        """Background loop to aggregate metrics."""
        while True:
            try:
                time.sleep(self.metrics_config.aggregation_interval)
                self._aggregate_metrics()
                self._cleanup_old_metrics()
            except Exception as e:
                self.logger.error(f"Error in aggregation loop: {e}")
    
    def _aggregate_metrics(self):
        """Aggregate metrics for the current interval."""
        with self.lock:
            current_time = time.time()
            cutoff_time = current_time - self.metrics_config.aggregation_interval
            
            # Group metrics by name and tags
            groups = defaultdict(list)
            for name, metric_queue in self.metrics.items():
                for metric in list(metric_queue):
                    if metric.timestamp >= cutoff_time:
                        groups[(name, str(metric.tags))].append(metric)
            
            # Calculate aggregates
            for (name, tags_str), metric_list in groups.items():
                if not metric_list:
                    continue
                
                values = [m.value for m in metric_list]
                
                # Calculate statistics
                stats = {
                    "count": len(values),
                    "sum": sum(values),
                    "min": min(values),
                    "max": max(values),
                    "avg": sum(values) / len(values)
                }
                
                # Calculate percentiles
                sorted_values = sorted(values)
                stats["p50"] = sorted_values[int(len(values) * 0.5)]
                stats["p90"] = sorted_values[int(len(values) * 0.9)]
                stats["p95"] = sorted_values[int(len(values) * 0.95)]
                stats["p99"] = sorted_values[int(len(values) * 0.99)]
                
                # Store aggregated metrics
                key = f"{name}_{tags_str}"
                self.aggregated_metrics[key] = stats
    
    def _cleanup_old_metrics(self):
        """Clean up old metrics based on retention policy."""
        with self.lock:
            cutoff_time = time.time() - self.metrics_config.retention_period
            
            for name, metric_queue in self.metrics.items():
                # Remove old metrics
                while metric_queue and metric_queue[0].timestamp < cutoff_time:
                    metric_queue.popleft()
    
    def record(
        self,
        name: str,
        value: float,
        tags: Optional[Dict[str, str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Record a metric.
        
        Args:
            name: The metric name
            value: The metric value
            tags: Optional metric tags
            metadata: Optional metadata
        """
        metric = Metric(
            name=name,
            value=value,
            timestamp=time.time(),
            tags=tags or {},
            metadata=metadata or {}
        )
        
        with self.lock:
            self.metrics[name].append(metric)
        
        # Send to backends
        for backend in self.backends:
            try:
                backend.record(metric)
            except Exception as e:
                self.logger.error(f"Error recording metric to backend: {e}")
    
    def increment(
        self,
        name: str,
        value: float = 1.0,
        tags: Optional[Dict[str, str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Increment a counter metric.
        
        Args:
            name: The metric name
            value: The value to increment by
            tags: Optional metric tags
            metadata: Optional metadata
        """
        # Get current value if it exists
        current_value = 0.0
        with self.lock:
            if self.metrics[name]:
                # Get most recent value
                current_value = self.metrics[name][-1].value
        
        # Record new value
        self.record(name, current_value + value, tags, metadata)
    
    def gauge(
        self,
        name: str,
        value: float,
        tags: Optional[Dict[str, str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Record a gauge metric.
        
        Args:
            name: The metric name
            value: The gauge value
            tags: Optional metric tags
            metadata: Optional metadata
        """
        self.record(name, value, tags, metadata)
    
    def timing(
        self,
        name: str,
        value: float,
        tags: Optional[Dict[str, str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Record a timing metric.
        
        Args:
            name: The metric name
            value: The timing value in milliseconds
            tags: Optional metric tags
            metadata: Optional metadata
        """
        self.record(name, value, tags, metadata)
    
    def get_metrics(
        self,
        name: str,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        tags: Optional[Dict[str, str]] = None
    ) -> List[Metric]:
        """
        Get metrics for a name.
        
        Args:
            name: The metric name
            start_time: Optional start time
            end_time: Optional end time
            tags: Optional tags to filter by
            
        Returns:
            List of matching metrics
        """
        with self.lock:
            metric_queue = self.metrics.get(name, deque())
        
        # Filter by time
        result = []
        for metric in metric_queue:
            if start_time and metric.timestamp < start_time:
                continue
            if end_time and metric.timestamp > end_time:
                continue
            
            # Filter by tags
            if tags:
                match = True
                for key, value in tags.items():
                    if metric.tags.get(key) != value:
                        match = False
                        break
                if not match:
                    continue
            
            result.append(metric)
        
        return result
    
    def get_aggregated_metrics(
        self,
        name: str,
        tags: Optional[Dict[str, str]] = None
    ) -> Optional[Dict[str, float]]:
        """
        Get aggregated metrics for a name.
        
        Args:
            name: The metric name
            tags: Optional tags
            
        Returns:
            Aggregated metrics if found, None otherwise
        """
        tags_str = str(tags or {})
        key = f"{name}_{tags_str}"
        
        with self.lock:
            return self.aggregated_metrics.get(key)
    
    def get_metric_names(self) -> List[str]:
        """
        Get all metric names.
        
        Returns:
            List of metric names
        """
        with self.lock:
            return list(self.metrics.keys())
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get metrics service statistics.
        
        Returns:
            Dictionary of statistics
        """
        with self.lock:
            total_metrics = sum(len(queue) for queue in self.metrics.values())
            total_aggregated = len(self.aggregated_metrics)
            
            return {
                "total_metrics": total_metrics,
                "total_aggregated_metrics": total_aggregated,
                "metric_names_count": len(self.metrics),
                "backend_count": len(self.backends),
                "config": {
                    "retention_period": self.metrics_config.retention_period,
                    "aggregation_interval": self.metrics_config.aggregation_interval,
                    "max_metrics_per_name": self.metrics_config.max_metrics_per_name
                }
            }
    
    def add_backend(self, backend: MetricsBackend):
        """
        Add a metrics backend.
        
        Args:
            backend: The metrics backend to add
        """
        self.backends.append(backend)
        self.logger.info(f"Added metrics backend: {type(backend).__name__}")
    
    def close(self):
        """Close the metrics service."""
        # Stop aggregation thread
        if hasattr(self, "aggregation_thread"):
            # Thread will stop on its own as it's a daemon
            pass
        
        # Close backends
        for backend in self.backends:
            try:
                backend.close()
            except Exception as e:
                self.logger.error(f"Error closing metrics backend: {e}")
