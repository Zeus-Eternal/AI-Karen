"""
Monitoring integration for response formatting system.

This module provides integration with the existing monitoring and metrics
systems to track response formatting performance and usage.
"""

import logging
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

# Prometheus metrics integration (optional)
try:
    from prometheus_client import Counter, Histogram, Gauge, REGISTRY
    
    # Response formatting metrics
    FORMATTING_REQUESTS_TOTAL = Counter(
        'response_formatting_requests_total',
        'Total number of response formatting requests',
        ['formatter', 'content_type', 'success']
    )
    
    FORMATTING_LATENCY = Histogram(
        'response_formatting_latency_seconds',
        'Response formatting latency in seconds',
        ['formatter', 'content_type']
    )
    
    FORMATTING_CONFIDENCE_SCORE = Histogram(
        'response_formatting_confidence_score',
        'Content type detection confidence scores',
        ['content_type']
    )
    
    ACTIVE_FORMATTERS = Gauge(
        'response_formatting_active_formatters',
        'Number of active response formatters'
    )
    
    PROMETHEUS_ENABLED = True
    logger.info("Prometheus metrics enabled for response formatting")
    
except ImportError:
    PROMETHEUS_ENABLED = False
    logger.debug("Prometheus not available, metrics disabled")


@dataclass
class FormattingMetric:
    """Data structure for formatting metrics."""
    timestamp: float
    formatter_name: str
    content_type: str
    success: bool
    latency_ms: float
    confidence_score: float
    user_query_length: int
    response_length: int
    error_message: Optional[str] = None


class ResponseFormattingMonitor:
    """
    Monitor for response formatting system performance and usage.
    
    This class collects and aggregates metrics about response formatting
    operations and integrates with existing monitoring infrastructure.
    """
    
    def __init__(self, max_metrics_history: int = 1000):
        self.max_metrics_history = max_metrics_history
        self._metrics_history: deque = deque(maxlen=max_metrics_history)
        self._aggregated_metrics = {
            'total_requests': 0,
            'successful_formats': 0,
            'failed_formats': 0,
            'total_latency_ms': 0.0,
            'formatter_usage': defaultdict(int),
            'content_type_distribution': defaultdict(int),
            'error_counts': defaultdict(int),
            'confidence_scores': deque(maxlen=100)  # Keep last 100 scores
        }
        self._start_time = time.time()
        
        logger.info("Response formatting monitor initialized")
    
    def update_active_formatters_count(self, count: int) -> None:
        """Update the count of active formatters."""
        if PROMETHEUS_ENABLED:
            try:
                ACTIVE_FORMATTERS.set(count)
            except Exception as e:
                logger.warning(f"Failed to update active formatters gauge: {e}")
    
    def record_formatting_attempt(
        self,
        formatter_name: str,
        content_type: str,
        success: bool,
        latency_ms: float,
        confidence_score: float,
        user_query_length: int,
        response_length: int,
        error_message: Optional[str] = None
    ) -> None:
        """
        Record a formatting attempt.
        
        Args:
            formatter_name: Name of the formatter used
            content_type: Type of content being formatted
            success: Whether formatting was successful
            latency_ms: Formatting latency in milliseconds
            confidence_score: Confidence score for content type detection
            user_query_length: Length of user query
            response_length: Length of response content
            error_message: Error message if formatting failed
        """
        metric = FormattingMetric(
            timestamp=time.time(),
            formatter_name=formatter_name,
            content_type=content_type,
            success=success,
            latency_ms=latency_ms,
            confidence_score=confidence_score,
            user_query_length=user_query_length,
            response_length=response_length,
            error_message=error_message
        )
        
        self._metrics_history.append(metric)
        self._update_aggregated_metrics(metric)
        
        # Update Prometheus metrics if available
        if PROMETHEUS_ENABLED:
            try:
                # Record request counter
                FORMATTING_REQUESTS_TOTAL.labels(
                    formatter=formatter_name,
                    content_type=content_type,
                    success=str(success).lower()
                ).inc()
                
                # Record latency histogram (convert ms to seconds)
                FORMATTING_LATENCY.labels(
                    formatter=formatter_name,
                    content_type=content_type
                ).observe(latency_ms / 1000.0)
                
                # Record confidence score
                FORMATTING_CONFIDENCE_SCORE.labels(
                    content_type=content_type
                ).observe(confidence_score)
                
            except Exception as e:
                logger.warning(f"Failed to update Prometheus metrics: {e}")
        
        # Log significant events
        if not success:
            logger.warning(
                f"Formatting failed: formatter={formatter_name}, "
                f"content_type={content_type}, error={error_message}"
            )
        elif latency_ms > 1000:  # Log slow formatting
            logger.warning(
                f"Slow formatting: formatter={formatter_name}, "
                f"latency={latency_ms:.1f}ms"
            )
    
    def _update_aggregated_metrics(self, metric: FormattingMetric) -> None:
        """Update aggregated metrics with new data point."""
        self._aggregated_metrics['total_requests'] += 1
        
        if metric.success:
            self._aggregated_metrics['successful_formats'] += 1
        else:
            self._aggregated_metrics['failed_formats'] += 1
            if metric.error_message:
                self._aggregated_metrics['error_counts'][metric.error_message] += 1
        
        self._aggregated_metrics['total_latency_ms'] += metric.latency_ms
        self._aggregated_metrics['formatter_usage'][metric.formatter_name] += 1
        self._aggregated_metrics['content_type_distribution'][metric.content_type] += 1
        self._aggregated_metrics['confidence_scores'].append(metric.confidence_score)
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """
        Get summary of formatting metrics.
        
        Returns:
            Dictionary with aggregated metrics
        """
        total_requests = self._aggregated_metrics['total_requests']
        successful_formats = self._aggregated_metrics['successful_formats']
        total_latency = self._aggregated_metrics['total_latency_ms']
        
        # Calculate rates and averages
        success_rate = successful_formats / max(1, total_requests)
        avg_latency_ms = total_latency / max(1, total_requests)
        
        # Calculate confidence score statistics
        confidence_scores = list(self._aggregated_metrics['confidence_scores'])
        avg_confidence = sum(confidence_scores) / max(1, len(confidence_scores))
        
        # Get recent metrics (last 5 minutes)
        recent_cutoff = time.time() - 300  # 5 minutes
        recent_metrics = [
            m for m in self._metrics_history 
            if m.timestamp > recent_cutoff
        ]
        
        recent_success_rate = 0.0
        recent_avg_latency = 0.0
        if recent_metrics:
            recent_successes = sum(1 for m in recent_metrics if m.success)
            recent_success_rate = recent_successes / len(recent_metrics)
            recent_avg_latency = sum(m.latency_ms for m in recent_metrics) / len(recent_metrics)
        
        return {
            'uptime_seconds': time.time() - self._start_time,
            'total_requests': total_requests,
            'successful_formats': successful_formats,
            'failed_formats': self._aggregated_metrics['failed_formats'],
            'success_rate': success_rate,
            'average_latency_ms': avg_latency_ms,
            'average_confidence_score': avg_confidence,
            'recent_success_rate': recent_success_rate,
            'recent_average_latency_ms': recent_avg_latency,
            'formatter_usage': dict(self._aggregated_metrics['formatter_usage']),
            'content_type_distribution': dict(self._aggregated_metrics['content_type_distribution']),
            'top_errors': dict(list(self._aggregated_metrics['error_counts'].items())[:5]),
            'metrics_history_size': len(self._metrics_history)
        }
    
    def get_prometheus_metrics(self) -> List[str]:
        """
        Get metrics in Prometheus format.
        
        Returns:
            List of Prometheus metric strings
        """
        metrics = []
        summary = self.get_metrics_summary()
        
        # Counter metrics
        metrics.append(f'response_formatting_requests_total {summary["total_requests"]}')
        metrics.append(f'response_formatting_successes_total {summary["successful_formats"]}')
        metrics.append(f'response_formatting_failures_total {summary["failed_formats"]}')
        
        # Gauge metrics
        metrics.append(f'response_formatting_success_rate {summary["success_rate"]:.4f}')
        metrics.append(f'response_formatting_average_latency_ms {summary["average_latency_ms"]:.2f}')
        metrics.append(f'response_formatting_average_confidence {summary["average_confidence_score"]:.4f}')
        metrics.append(f'response_formatting_recent_success_rate {summary["recent_success_rate"]:.4f}')
        metrics.append(f'response_formatting_recent_latency_ms {summary["recent_average_latency_ms"]:.2f}')
        
        # Formatter usage metrics
        for formatter, count in summary['formatter_usage'].items():
            metrics.append(f'response_formatting_formatter_usage{{formatter="{formatter}"}} {count}')
        
        # Content type distribution metrics
        for content_type, count in summary['content_type_distribution'].items():
            metrics.append(f'response_formatting_content_type{{type="{content_type}"}} {count}')
        
        return metrics
    
    def get_health_status(self) -> Dict[str, Any]:
        """
        Get health status of response formatting system.
        
        Returns:
            Dictionary with health information
        """
        summary = self.get_metrics_summary()
        
        # Determine health status
        is_healthy = True
        issues = []
        
        # Check success rate
        if summary['success_rate'] < 0.8:  # Less than 80% success rate
            is_healthy = False
            issues.append(f"Low success rate: {summary['success_rate']:.2%}")
        
        # Check recent performance
        if summary['recent_success_rate'] < 0.7:  # Recent performance degradation
            is_healthy = False
            issues.append(f"Recent performance degradation: {summary['recent_success_rate']:.2%}")
        
        # Check latency
        if summary['average_latency_ms'] > 2000:  # Average latency > 2 seconds
            is_healthy = False
            issues.append(f"High latency: {summary['average_latency_ms']:.0f}ms")
        
        # Check if we have any requests at all
        if summary['total_requests'] == 0:
            is_healthy = False
            issues.append("No formatting requests processed")
        
        return {
            'healthy': is_healthy,
            'status': 'healthy' if is_healthy else 'degraded',
            'issues': issues,
            'uptime_seconds': summary['uptime_seconds'],
            'total_requests': summary['total_requests'],
            'success_rate': summary['success_rate'],
            'average_latency_ms': summary['average_latency_ms']
        }
    
    def get_recent_errors(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent formatting errors.
        
        Args:
            limit: Maximum number of errors to return
            
        Returns:
            List of recent error information
        """
        recent_errors = []
        
        for metric in reversed(list(self._metrics_history)):
            if not metric.success and metric.error_message:
                recent_errors.append({
                    'timestamp': metric.timestamp,
                    'formatter_name': metric.formatter_name,
                    'content_type': metric.content_type,
                    'error_message': metric.error_message,
                    'latency_ms': metric.latency_ms,
                    'confidence_score': metric.confidence_score
                })
                
                if len(recent_errors) >= limit:
                    break
        
        return recent_errors
    
    def reset_metrics(self) -> None:
        """Reset all metrics."""
        self._metrics_history.clear()
        self._aggregated_metrics = {
            'total_requests': 0,
            'successful_formats': 0,
            'failed_formats': 0,
            'total_latency_ms': 0.0,
            'formatter_usage': defaultdict(int),
            'content_type_distribution': defaultdict(int),
            'error_counts': defaultdict(int),
            'confidence_scores': deque(maxlen=100)
        }
        self._start_time = time.time()
        
        logger.info("Response formatting metrics reset")
    
    def export_metrics_data(self) -> List[Dict[str, Any]]:
        """
        Export raw metrics data for analysis.
        
        Returns:
            List of metric data dictionaries
        """
        return [asdict(metric) for metric in self._metrics_history]


# Global monitor instance
_monitor_instance: Optional[ResponseFormattingMonitor] = None


def get_formatting_monitor() -> ResponseFormattingMonitor:
    """
    Get the global response formatting monitor instance.
    
    Returns:
        The global ResponseFormattingMonitor instance
    """
    global _monitor_instance
    
    if _monitor_instance is None:
        _monitor_instance = ResponseFormattingMonitor()
    
    return _monitor_instance


def reset_formatting_monitor() -> None:
    """
    Reset the global monitor instance.
    
    This is primarily used for testing.
    """
    global _monitor_instance
    _monitor_instance = None


def record_formatting_metrics(
    formatter_name: str,
    content_type: str,
    success: bool,
    latency_ms: float,
    confidence_score: float,
    user_query: str,
    response_content: str,
    error_message: Optional[str] = None
) -> None:
    """
    Convenience function to record formatting metrics.
    
    Args:
        formatter_name: Name of the formatter used
        content_type: Type of content being formatted
        success: Whether formatting was successful
        latency_ms: Formatting latency in milliseconds
        confidence_score: Confidence score for content type detection
        user_query: User query text
        response_content: Response content text
        error_message: Error message if formatting failed
    """
    monitor = get_formatting_monitor()
    monitor.record_formatting_attempt(
        formatter_name=formatter_name,
        content_type=content_type,
        success=success,
        latency_ms=latency_ms,
        confidence_score=confidence_score,
        user_query_length=len(user_query),
        response_length=len(response_content),
        error_message=error_message
    )