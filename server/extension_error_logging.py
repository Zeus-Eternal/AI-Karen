"""
Extension Error Logging and Monitoring System

This module provides structured error logging with correlation IDs, metrics collection,
and error trend analysis for the extension runtime authentication system.

Requirements addressed:
- 10.1: Extension error alerts with relevant details
- 10.2: Metrics collection on response times, error rates, and availability
- 10.3: Authentication issue escalation and alerting
- 10.4: Performance degradation recommendations
- 10.5: Historical data for trend analysis and capacity planning
"""

import logging
import json
import uuid
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from enum import Enum
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import asyncio
import threading
from contextlib import contextmanager

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class ErrorSeverity(str, Enum):
    """Error severity levels for classification and alerting."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorCategory(str, Enum):
    """Error categories for classification and analysis."""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    SERVICE_UNAVAILABLE = "service_unavailable"
    NETWORK = "network"
    CONFIGURATION = "configuration"
    PERFORMANCE = "performance"
    UNKNOWN = "unknown"

class AlertStatus(str, Enum):
    """Alert status for tracking alert lifecycle."""
    PENDING = "pending"
    SENT = "sent"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"

@dataclass
class ErrorEvent:
    """Structured error event with correlation tracking."""
    correlation_id: str
    timestamp: datetime
    error_type: str
    error_message: str
    category: ErrorCategory
    severity: ErrorSeverity
    context: Dict[str, Any]
    stack_trace: Optional[str] = None
    user_id: Optional[str] = None
    tenant_id: Optional[str] = None
    extension_name: Optional[str] = None
    endpoint: Optional[str] = None
    request_id: Optional[str] = None
    recovery_attempted: bool = False
    recovery_successful: Optional[bool] = None
    recovery_duration: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert error event to dictionary for logging."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['category'] = self.category.value
        data['severity'] = self.severity.value
        return data

@dataclass
class MetricPoint:
    """Single metric data point."""
    timestamp: datetime
    value: float
    labels: Dict[str, str]

@dataclass
class Alert:
    """Alert for error conditions."""
    alert_id: str
    correlation_id: str
    alert_type: str
    severity: ErrorSeverity
    message: str
    context: Dict[str, Any]
    created_at: datetime
    status: AlertStatus = AlertStatus.PENDING
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None

class ExtensionErrorLogger:
    """Structured error logger with correlation IDs and context tracking."""

    def __init__(self, logger_name: str = "extension_errors"):
        self.logger = logging.getLogger(logger_name)
        self.correlation_context = threading.local()

    @contextmanager
    def correlation_context_manager(self, correlation_id: str = None):
        """Context manager for correlation ID tracking."""
        if correlation_id is None:
            correlation_id = str(uuid.uuid4())
        
        old_correlation_id = getattr(self.correlation_context, 'correlation_id', None)
        self.correlation_context.correlation_id = correlation_id
        
        try:
            yield correlation_id
        finally:
            if old_correlation_id:
                self.correlation_context.correlation_id = old_correlation_id
            else:
                delattr(self.correlation_context, 'correlation_id')

    def get_correlation_id(self) -> str:
        """Get current correlation ID or generate new one."""
        correlation_id = getattr(self.correlation_context, 'correlation_id', None)
        if not correlation_id:
            correlation_id = str(uuid.uuid4())
            self.correlation_context.correlation_id = correlation_id
        return correlation_id

    def log_error(
        self,
        error_type: str,
        error_message: str,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        context: Dict[str, Any] = None,
        stack_trace: str = None,
        user_id: str = None,
        tenant_id: str = None,
        extension_name: str = None,
        endpoint: str = None,
        request_id: str = None
    ) -> ErrorEvent:
        """Log structured error with correlation tracking."""
        
        error_event = ErrorEvent(
            correlation_id=self.get_correlation_id(),
            timestamp=datetime.utcnow(),
            error_type=error_type,
            error_message=error_message,
            category=category,
            severity=severity,
            context=context or {},
            stack_trace=stack_trace,
            user_id=user_id,
            tenant_id=tenant_id,
            extension_name=extension_name,
            endpoint=endpoint,
            request_id=request_id
        )

        # Log structured error
        log_data = error_event.to_dict()
        
        if severity == ErrorSeverity.CRITICAL:
            self.logger.critical(json.dumps(log_data))
        elif severity == ErrorSeverity.HIGH:
            self.logger.error(json.dumps(log_data))
        elif severity == ErrorSeverity.MEDIUM:
            self.logger.warning(json.dumps(log_data))
        else:
            self.logger.info(json.dumps(log_data))

        return error_event

    def log_recovery_attempt(
        self,
        correlation_id: str,
        recovery_strategy: str,
        success: bool,
        duration: float,
        details: Dict[str, Any] = None
    ):
        """Log error recovery attempt."""
        recovery_data = {
            'correlation_id': correlation_id,
            'timestamp': datetime.utcnow().isoformat(),
            'recovery_strategy': recovery_strategy,
            'success': success,
            'duration': duration,
            'details': details or {}
        }

        if success:
            self.logger.info(f"Recovery successful: {json.dumps(recovery_data)}")
        else:
            self.logger.warning(f"Recovery failed: {json.dumps(recovery_data)}")

class ExtensionMetricsCollector:
    """Collects and aggregates extension error and performance metrics."""

    def __init__(self, retention_hours: int = 24):
        self.retention_hours = retention_hours
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque())
        self.error_counts: Dict[str, int] = defaultdict(int)
        self.response_times: Dict[str, deque] = defaultdict(lambda: deque())
        self.availability_stats: Dict[str, Dict[str, Any]] = defaultdict(dict)
        self.lock = threading.Lock()

    def record_error(
        self,
        error_event: ErrorEvent,
        endpoint: str = None,
        response_time: float = None
    ):
        """Record error event for metrics collection."""
        with self.lock:
            timestamp = error_event.timestamp
            
            # Record error count by category and severity
            error_key = f"{error_event.category.value}_{error_event.severity.value}"
            self.error_counts[error_key] += 1
            
            # Record error metric point
            metric_point = MetricPoint(
                timestamp=timestamp,
                value=1.0,
                labels={
                    'category': error_event.category.value,
                    'severity': error_event.severity.value,
                    'extension': error_event.extension_name or 'unknown',
                    'endpoint': endpoint or error_event.endpoint or 'unknown'
                }
            )
            
            self.metrics['errors'].append(metric_point)
            
            # Record response time if provided
            if response_time is not None and endpoint:
                self.response_times[endpoint].append(MetricPoint(
                    timestamp=timestamp,
                    value=response_time,
                    labels={'endpoint': endpoint}
                ))

    def record_success(
        self,
        endpoint: str,
        response_time: float,
        extension_name: str = None
    ):
        """Record successful request for availability calculation."""
        with self.lock:
            timestamp = datetime.utcnow()
            
            # Record success metric
            metric_point = MetricPoint(
                timestamp=timestamp,
                value=1.0,
                labels={
                    'endpoint': endpoint,
                    'extension': extension_name or 'unknown',
                    'status': 'success'
                }
            )
            
            self.metrics['requests'].append(metric_point)
            
            # Record response time
            self.response_times[endpoint].append(MetricPoint(
                timestamp=timestamp,
                value=response_time,
                labels={'endpoint': endpoint}
            ))

    def record_recovery_success(
        self,
        correlation_id: str,
        recovery_strategy: str,
        duration: float,
        success: bool
    ):
        """Record error recovery attempt for success rate tracking."""
        with self.lock:
            timestamp = datetime.utcnow()
            
            metric_point = MetricPoint(
                timestamp=timestamp,
                value=1.0 if success else 0.0,
                labels={
                    'correlation_id': correlation_id,
                    'strategy': recovery_strategy,
                    'success': str(success)
                }
            )
            
            self.metrics['recovery_attempts'].append(metric_point)

    def get_error_rate(self, time_window_minutes: int = 60) -> Dict[str, float]:
        """Calculate error rates by category over time window."""
        with self.lock:
            cutoff_time = datetime.utcnow() - timedelta(minutes=time_window_minutes)
            error_rates = {}
            
            # Count errors by category in time window
            category_counts = defaultdict(int)
            total_requests = 0
            
            for metric_point in self.metrics['errors']:
                if metric_point.timestamp >= cutoff_time:
                    category = metric_point.labels.get('category', 'unknown')
                    category_counts[category] += 1
            
            for metric_point in self.metrics['requests']:
                if metric_point.timestamp >= cutoff_time:
                    total_requests += 1
            
            # Calculate error rates
            for category, count in category_counts.items():
                if total_requests > 0:
                    error_rates[category] = count / total_requests
                else:
                    error_rates[category] = 0.0
            
            return error_rates

    def get_response_time_stats(
        self,
        endpoint: str = None,
        time_window_minutes: int = 60
    ) -> Dict[str, float]:
        """Get response time statistics."""
        with self.lock:
            cutoff_time = datetime.utcnow() - timedelta(minutes=time_window_minutes)
            response_times = []
            
            if endpoint:
                metrics = self.response_times.get(endpoint, deque())
            else:
                # Aggregate all endpoints
                metrics = []
                for endpoint_metrics in self.response_times.values():
                    metrics.extend(endpoint_metrics)
            
            for metric_point in metrics:
                if metric_point.timestamp >= cutoff_time:
                    response_times.append(metric_point.value)
            
            if not response_times:
                return {'count': 0, 'avg': 0.0, 'min': 0.0, 'max': 0.0, 'p95': 0.0}
            
            response_times.sort()
            count = len(response_times)
            avg = sum(response_times) / count
            min_time = min(response_times)
            max_time = max(response_times)
            p95_index = int(0.95 * count)
            p95 = response_times[p95_index] if p95_index < count else max_time
            
            return {
                'count': count,
                'avg': avg,
                'min': min_time,
                'max': max_time,
                'p95': p95
            }

    def get_availability_stats(
        self,
        time_window_minutes: int = 60
    ) -> Dict[str, float]:
        """Calculate availability statistics."""
        with self.lock:
            cutoff_time = datetime.utcnow() - timedelta(minutes=time_window_minutes)
            
            # Count successful requests and errors by endpoint
            endpoint_stats = defaultdict(lambda: {'success': 0, 'errors': 0})
            
            for metric_point in self.metrics['requests']:
                if metric_point.timestamp >= cutoff_time:
                    endpoint = metric_point.labels.get('endpoint', 'unknown')
                    endpoint_stats[endpoint]['success'] += 1
            
            for metric_point in self.metrics['errors']:
                if metric_point.timestamp >= cutoff_time:
                    endpoint = metric_point.labels.get('endpoint', 'unknown')
                    endpoint_stats[endpoint]['errors'] += 1
            
            # Calculate availability percentages
            availability = {}
            for endpoint, stats in endpoint_stats.items():
                total = stats['success'] + stats['errors']
                if total > 0:
                    availability[endpoint] = stats['success'] / total
                else:
                    availability[endpoint] = 1.0  # No requests = 100% available
            
            return availability

    def get_recovery_success_rate(
        self,
        time_window_minutes: int = 60,
        strategy: str = None
    ) -> Dict[str, float]:
        """Calculate error recovery success rates."""
        with self.lock:
            cutoff_time = datetime.utcnow() - timedelta(minutes=time_window_minutes)
            
            strategy_stats = defaultdict(lambda: {'attempts': 0, 'successes': 0})
            
            for metric_point in self.metrics['recovery_attempts']:
                if metric_point.timestamp >= cutoff_time:
                    recovery_strategy = metric_point.labels.get('strategy', 'unknown')
                    
                    if strategy and recovery_strategy != strategy:
                        continue
                    
                    strategy_stats[recovery_strategy]['attempts'] += 1
                    if metric_point.value > 0:
                        strategy_stats[recovery_strategy]['successes'] += 1
            
            # Calculate success rates
            success_rates = {}
            for recovery_strategy, stats in strategy_stats.items():
                if stats['attempts'] > 0:
                    success_rates[recovery_strategy] = stats['successes'] / stats['attempts']
                else:
                    success_rates[recovery_strategy] = 0.0
            
            return success_rates

    def cleanup_old_metrics(self):
        """Remove metrics older than retention period."""
        with self.lock:
            cutoff_time = datetime.utcnow() - timedelta(hours=self.retention_hours)
            
            for metric_name, metric_deque in self.metrics.items():
                while metric_deque and metric_deque[0].timestamp < cutoff_time:
                    metric_deque.popleft()
            
            for endpoint, response_deque in self.response_times.items():
                while response_deque and response_deque[0].timestamp < cutoff_time:
                    response_deque.popleft()

class ExtensionErrorTrendAnalyzer:
    """Analyzes error trends and provides insights for capacity planning."""

    def __init__(self, metrics_collector: ExtensionMetricsCollector):
        self.metrics_collector = metrics_collector

    def analyze_error_trends(
        self,
        time_window_hours: int = 24,
        bucket_size_minutes: int = 60
    ) -> Dict[str, Any]:
        """Analyze error trends over time."""
        
        # Get error rates in time buckets
        buckets = []
        current_time = datetime.utcnow()
        
        for i in range(time_window_hours):
            bucket_start = current_time - timedelta(hours=i+1)
            bucket_end = current_time - timedelta(hours=i)
            
            # Calculate error rates for this bucket
            with self.metrics_collector.lock:
                bucket_errors = defaultdict(int)
                bucket_requests = 0
                
                for metric_point in self.metrics_collector.metrics['errors']:
                    if bucket_start <= metric_point.timestamp < bucket_end:
                        category = metric_point.labels.get('category', 'unknown')
                        bucket_errors[category] += 1
                
                for metric_point in self.metrics_collector.metrics['requests']:
                    if bucket_start <= metric_point.timestamp < bucket_end:
                        bucket_requests += 1
                
                bucket_data = {
                    'timestamp': bucket_start.isoformat(),
                    'total_requests': bucket_requests,
                    'error_counts': dict(bucket_errors),
                    'error_rate': sum(bucket_errors.values()) / max(bucket_requests, 1)
                }
                
                buckets.append(bucket_data)
        
        # Analyze trends
        error_rates = [bucket['error_rate'] for bucket in buckets]
        
        if len(error_rates) >= 2:
            # Calculate trend direction
            recent_count = min(6, len(error_rates))
            older_start = min(6, len(error_rates))
            older_end = min(12, len(error_rates))
            
            if recent_count > 0:
                recent_avg = sum(error_rates[:recent_count]) / recent_count
            else:
                recent_avg = 0.0
            
            if older_end > older_start:
                older_avg = sum(error_rates[older_start:older_end]) / (older_end - older_start)
            else:
                older_avg = 0.0
            
            if older_avg > 0:
                trend_direction = (recent_avg - older_avg) / older_avg
            else:
                trend_direction = 0.0 if recent_avg == 0 else 1.0  # If no older data but recent errors, trend is up
        else:
            trend_direction = 0.0
        
        return {
            'time_window_hours': time_window_hours,
            'buckets': buckets,
            'trend_direction': trend_direction,
            'current_error_rate': error_rates[0] if error_rates else 0.0,
            'peak_error_rate': max(error_rates) if error_rates else 0.0,
            'average_error_rate': sum(error_rates) / len(error_rates) if error_rates else 0.0
        }

    def get_performance_recommendations(self) -> List[Dict[str, Any]]:
        """Generate performance improvement recommendations based on trends."""
        recommendations = []
        
        # Analyze current metrics
        error_rates = self.metrics_collector.get_error_rate(time_window_minutes=60)
        response_stats = self.metrics_collector.get_response_time_stats(time_window_minutes=60)
        availability_stats = self.metrics_collector.get_availability_stats(time_window_minutes=60)
        recovery_rates = self.metrics_collector.get_recovery_success_rate(time_window_minutes=60)
        
        # High error rate recommendation
        total_error_rate = sum(error_rates.values())
        if total_error_rate > 0.05:  # 5% error rate threshold
            recommendations.append({
                'type': 'high_error_rate',
                'severity': 'high',
                'message': f'Error rate is {total_error_rate:.2%}, exceeding 5% threshold',
                'recommendation': 'Investigate authentication and service connectivity issues',
                'metrics': error_rates
            })
        
        # High response time recommendation
        if response_stats['avg'] > 2000:  # 2 second threshold
            recommendations.append({
                'type': 'high_response_time',
                'severity': 'medium',
                'message': f'Average response time is {response_stats["avg"]:.0f}ms',
                'recommendation': 'Consider optimizing database queries and connection pooling',
                'metrics': response_stats
            })
        
        # Low availability recommendation
        low_availability_endpoints = [
            endpoint for endpoint, availability in availability_stats.items()
            if availability < 0.95  # 95% availability threshold
        ]
        
        if low_availability_endpoints:
            recommendations.append({
                'type': 'low_availability',
                'severity': 'high',
                'message': f'Low availability detected for endpoints: {low_availability_endpoints}',
                'recommendation': 'Implement health checks and automatic service recovery',
                'metrics': {ep: availability_stats[ep] for ep in low_availability_endpoints}
            })
        
        # Poor recovery rate recommendation
        poor_recovery_strategies = [
            strategy for strategy, rate in recovery_rates.items()
            if rate < 0.8  # 80% recovery success threshold
        ]
        
        if poor_recovery_strategies:
            recommendations.append({
                'type': 'poor_recovery_rate',
                'severity': 'medium',
                'message': f'Low recovery success rate for strategies: {poor_recovery_strategies}',
                'recommendation': 'Review and improve error recovery mechanisms',
                'metrics': {strategy: recovery_rates[strategy] for strategy in poor_recovery_strategies}
            })
        
        return recommendations

# Global instances
extension_error_logger = ExtensionErrorLogger()
extension_metrics_collector = ExtensionMetricsCollector()
extension_trend_analyzer = ExtensionErrorTrendAnalyzer(extension_metrics_collector)