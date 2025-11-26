"""
Metrics Service Facade
Provides metrics collection and reporting for the entire system.
"""

import time
import threading
from collections import defaultdict, deque
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field

@dataclass
class MetricPoint:
    """Single metric data point"""
    timestamp: float
    value: Union[int, float]
    tags: Dict[str, str] = field(default_factory=dict)

@dataclass
class MetricSummary:
    """Summary statistics for a metric"""
    count: int = 0
    sum: float = 0.0
    min: float = float('inf')
    max: float = float('-inf')
    avg: float = 0.0
    p50: float = 0.0
    p95: float = 0.0
    p99: float = 0.0

class MetricsService:
    """
    Metrics service facade.
    Provides centralized metrics collection and reporting.
    """
    
    def __init__(self, max_points: int = 1000):
        """
        Initialize the metrics service
        
        Args:
            max_points: Maximum number of points to keep per metric
        """
        self.max_points = max_points
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_points))
        self.counters: Dict[str, int] = defaultdict(int)
        self.gauges: Dict[str, float] = defaultdict(float)
        self._lock = threading.Lock()
        
    def record_timing(self, metric_name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """
        Record a timing metric
        
        Args:
            metric_name: Name of the metric
            value: Timing value in milliseconds
            tags: Optional tags for the metric
        """
        with self._lock:
            self.metrics[metric_name].append(
                MetricPoint(
                    timestamp=time.time(),
                    value=value,
                    tags=tags or {}
                )
            )
    
    def increment_counter(self, metric_name: str, value: int = 1, tags: Optional[Dict[str, str]] = None) -> None:
        """
        Increment a counter metric
        
        Args:
            metric_name: Name of the metric
            value: Value to increment by
            tags: Optional tags for the metric
        """
        with self._lock:
            self.counters[metric_name] += value
            
            # Also record as a point for time series analysis
            self.metrics[metric_name].append(
                MetricPoint(
                    timestamp=time.time(),
                    value=self.counters[metric_name],
                    tags=tags or {}
                )
            )
    
    def set_gauge(self, metric_name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """
        Set a gauge metric
        
        Args:
            metric_name: Name of the metric
            value: Value to set
            tags: Optional tags for the metric
        """
        with self._lock:
            self.gauges[metric_name] = value
            
            # Also record as a point for time series analysis
            self.metrics[metric_name].append(
                MetricPoint(
                    timestamp=time.time(),
                    value=value,
                    tags=tags or {}
                )
            )
    
    def get_metric_summary(self, metric_name: str) -> Optional[MetricSummary]:
        """
        Get summary statistics for a metric
        
        Args:
            metric_name: Name of the metric
            
        Returns:
            Summary statistics or None if metric doesn't exist
        """
        with self._lock:
            points = list(self.metrics.get(metric_name, []))
            
        if not points:
            return None
            
        values = [p.value for p in points]
        values.sort()
        
        count = len(values)
        sum_val = sum(values)
        min_val = min(values)
        max_val = max(values)
        avg_val = sum_val / count if count > 0 else 0.0
        
        # Calculate percentiles
        p50_idx = int(count * 0.5)
        p95_idx = int(count * 0.95)
        p99_idx = int(count * 0.99)
        
        p50 = values[p50_idx] if p50_idx < count else 0.0
        p95 = values[p95_idx] if p95_idx < count else 0.0
        p99 = values[p99_idx] if p99_idx < count else 0.0
        
        return MetricSummary(
            count=count,
            sum=sum_val,
            min=min_val,
            max=max_val,
            avg=avg_val,
            p50=p50,
            p95=p95,
            p99=p99
        )
    
    def get_metric_points(self, metric_name: str, since: Optional[float] = None) -> List[MetricPoint]:
        """
        Get raw metric points
        
        Args:
            metric_name: Name of the metric
            since: Optional timestamp to filter points from
            
        Returns:
            List of metric points
        """
        with self._lock:
            points = list(self.metrics.get(metric_name, []))
            
        if since is not None:
            points = [p for p in points if p.timestamp >= since]
            
        return points
    
    def get_counter_value(self, metric_name: str) -> int:
        """
        Get the current value of a counter
        
        Args:
            metric_name: Name of the counter
            
        Returns:
            Current counter value
        """
        with self._lock:
            return self.counters.get(metric_name, 0)
    
    def get_gauge_value(self, metric_name: str) -> float:
        """
        Get the current value of a gauge
        
        Args:
            metric_name: Name of the gauge
            
        Returns:
            Current gauge value
        """
        with self._lock:
            return self.gauges.get(metric_name, 0.0)
    
    def record_memory_commit(
        self,
        status: str,
        decay_tier: str,
        user_id: str = "",
        org_id: str = "",
        correlation_id: Optional[str] = None
    ) -> None:
        """
        Record memory commit metrics
        
        Args:
            status: Status of the commit (success, error, etc.)
            decay_tier: Decay tier of the memory
            user_id: User ID
            org_id: Organization ID
            correlation_id: Correlation ID
        """
        tags = {
            "status": status,
            "decay_tier": decay_tier,
            "user_id": user_id,
            "org_id": org_id,
        }
        
        if correlation_id:
            tags["correlation_id"] = correlation_id
            
        self.increment_counter("memory_commits", tags=tags)
    
    def record_memory_query(
        self,
        operation: str,
        status: str,
        user_id: str = "",
        org_id: str = "",
        correlation_id: Optional[str] = None
    ) -> None:
        """
        Record memory query metrics
        
        Args:
            operation: Operation type (search, etc.)
            status: Status of the query (success, error, etc.)
            user_id: User ID
            org_id: Organization ID
            correlation_id: Correlation ID
        """
        tags = {
            "operation": operation,
            "status": status,
            "user_id": user_id,
            "org_id": org_id,
        }
        
        if correlation_id:
            tags["correlation_id"] = correlation_id
            
        self.increment_counter("memory_queries", tags=tags)
    
    def record_model_execution(
        self,
        model_name: str,
        provider: str,
        duration_ms: float,
        token_count: int,
        status: str = "success"
    ) -> None:
        """
        Record model execution metrics
        
        Args:
            model_name: Name of the model
            provider: Model provider
            duration_ms: Execution duration in milliseconds
            token_count: Number of tokens processed
            status: Execution status
        """
        tags = {
            "model_name": model_name,
            "provider": provider,
            "status": status,
        }
        
        self.record_timing("model_execution_duration", duration_ms, tags=tags)
        self.increment_counter("model_execution_tokens", token_count, tags=tags)
        self.increment_counter("model_execution_count", tags=tags)
    
    def record_api_request(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        duration_ms: float
    ) -> None:
        """
        Record API request metrics
        
        Args:
            endpoint: API endpoint
            method: HTTP method
            status_code: HTTP status code
            duration_ms: Request duration in milliseconds
        """
        tags = {
            "endpoint": endpoint,
            "method": method,
            "status_code": str(status_code),
        }
        
        self.record_timing("api_request_duration", duration_ms, tags=tags)
        self.increment_counter("api_request_count", tags=tags)

# Global instance
_metrics_service: Optional[MetricsService] = None

def get_metrics_service() -> MetricsService:
    """Get the global metrics service instance"""
    global _metrics_service
    if _metrics_service is None:
        _metrics_service = MetricsService()
    return _metrics_service