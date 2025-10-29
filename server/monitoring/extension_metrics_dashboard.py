"""
Extension Authentication and Service Metrics Dashboard

This module provides comprehensive monitoring and metrics collection for extension
authentication, service health, and performance monitoring.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import json
import time
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


class MetricType(Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


class AlertSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class MetricPoint:
    """Individual metric data point."""
    timestamp: datetime
    value: float
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class Alert:
    """Alert definition and state."""
    id: str
    name: str
    description: str
    severity: AlertSeverity
    condition: str
    threshold: float
    triggered_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    is_active: bool = False
    trigger_count: int = 0


class ExtensionMetricsCollector:
    """Collects and stores extension-related metrics."""

    def __init__(self, retention_hours: int = 24):
        self.retention_hours = retention_hours
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=10000))
        self.counters: Dict[str, float] = defaultdict(float)
        self.gauges: Dict[str, float] = defaultdict(float)
        self.histograms: Dict[str, List[float]] = defaultdict(list)
        self.timers: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        
        # Authentication metrics
        self.auth_success_count = 0
        self.auth_failure_count = 0
        self.token_refresh_count = 0
        self.auth_response_times = deque(maxlen=1000)
        
        # Service health metrics
        self.service_status: Dict[str, str] = {}
        self.service_response_times: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.service_error_counts: Dict[str, int] = defaultdict(int)
        
        # Extension API metrics
        self.api_request_count = 0
        self.api_error_count = 0
        self.api_response_times = deque(maxlen=1000)
        self.endpoint_metrics: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            'request_count': 0,
            'error_count': 0,
            'response_times': deque(maxlen=100),
            'last_request': None
        })

    def record_auth_success(self, response_time: float, user_id: str = None):
        """Record successful authentication."""
        self.auth_success_count += 1
        self.auth_response_times.append(response_time)
        
        self.record_metric(
            'auth_success_total',
            MetricType.COUNTER,
            1,
            {'user_id': user_id or 'unknown'}
        )
        
        self.record_metric(
            'auth_response_time',
            MetricType.TIMER,
            response_time,
            {'result': 'success'}
        )

    def record_auth_failure(self, response_time: float, error_type: str, user_id: str = None):
        """Record authentication failure."""
        self.auth_failure_count += 1
        self.auth_response_times.append(response_time)
        
        self.record_metric(
            'auth_failure_total',
            MetricType.COUNTER,
            1,
            {'error_type': error_type, 'user_id': user_id or 'unknown'}
        )
        
        self.record_metric(
            'auth_response_time',
            MetricType.TIMER,
            response_time,
            {'result': 'failure'}
        )

    def record_token_refresh(self, response_time: float, success: bool):
        """Record token refresh attempt."""
        self.token_refresh_count += 1
        
        self.record_metric(
            'token_refresh_total',
            MetricType.COUNTER,
            1,
            {'success': str(success)}
        )
        
        self.record_metric(
            'token_refresh_time',
            MetricType.TIMER,
            response_time,
            {'success': str(success)}
        )

    def record_service_health(self, service_name: str, status: str, response_time: float = None):
        """Record service health status."""
        self.service_status[service_name] = status
        
        if response_time is not None:
            self.service_response_times[service_name].append(response_time)
        
        self.record_metric(
            'service_health_status',
            MetricType.GAUGE,
            1 if status == 'healthy' else 0,
            {'service': service_name, 'status': status}
        )

    def record_service_error(self, service_name: str, error_type: str):
        """Record service error."""
        self.service_error_counts[service_name] += 1
        
        self.record_metric(
            'service_error_total',
            MetricType.COUNTER,
            1,
            {'service': service_name, 'error_type': error_type}
        )

    def record_api_request(self, endpoint: str, method: str, status_code: int, response_time: float):
        """Record API request metrics."""
        self.api_request_count += 1
        self.api_response_times.append(response_time)
        
        # Update endpoint-specific metrics
        endpoint_key = f"{method}:{endpoint}"
        self.endpoint_metrics[endpoint_key]['request_count'] += 1
        self.endpoint_metrics[endpoint_key]['response_times'].append(response_time)
        self.endpoint_metrics[endpoint_key]['last_request'] = datetime.utcnow()
        
        if status_code >= 400:
            self.api_error_count += 1
            self.endpoint_metrics[endpoint_key]['error_count'] += 1
        
        self.record_metric(
            'api_request_total',
            MetricType.COUNTER,
            1,
            {'endpoint': endpoint, 'method': method, 'status': str(status_code)}
        )
        
        self.record_metric(
            'api_response_time',
            MetricType.TIMER,
            response_time,
            {'endpoint': endpoint, 'method': method}
        )

    def record_metric(self, name: str, metric_type: MetricType, value: float, labels: Dict[str, str] = None):
        """Record a generic metric."""
        labels = labels or {}
        metric_point = MetricPoint(
            timestamp=datetime.utcnow(),
            value=value,
            labels=labels
        )
        
        self.metrics[name].append(metric_point)
        
        # Update type-specific storage
        if metric_type == MetricType.COUNTER:
            self.counters[name] += value
        elif metric_type == MetricType.GAUGE:
            self.gauges[name] = value
        elif metric_type == MetricType.HISTOGRAM:
            self.histograms[name].append(value)
        elif metric_type == MetricType.TIMER:
            self.timers[name].append(value)

    def get_auth_metrics(self) -> Dict[str, Any]:
        """Get authentication metrics summary."""
        total_requests = self.auth_success_count + self.auth_failure_count
        success_rate = (self.auth_success_count / total_requests * 100) if total_requests > 0 else 0
        
        avg_response_time = (
            sum(self.auth_response_times) / len(self.auth_response_times)
            if self.auth_response_times else 0
        )
        
        return {
            'total_requests': total_requests,
            'success_count': self.auth_success_count,
            'failure_count': self.auth_failure_count,
            'success_rate': round(success_rate, 2),
            'token_refresh_count': self.token_refresh_count,
            'average_response_time': round(avg_response_time, 3),
            'last_updated': datetime.utcnow().isoformat()
        }

    def get_service_health_metrics(self) -> Dict[str, Any]:
        """Get service health metrics summary."""
        healthy_services = sum(1 for status in self.service_status.values() if status == 'healthy')
        total_services = len(self.service_status)
        
        service_details = {}
        for service, status in self.service_status.items():
            response_times = list(self.service_response_times[service])
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
            
            service_details[service] = {
                'status': status,
                'error_count': self.service_error_counts[service],
                'average_response_time': round(avg_response_time, 3),
                'last_check': datetime.utcnow().isoformat()
            }
        
        return {
            'healthy_services': healthy_services,
            'total_services': total_services,
            'health_percentage': round((healthy_services / total_services * 100) if total_services > 0 else 0, 2),
            'services': service_details,
            'last_updated': datetime.utcnow().isoformat()
        }

    def get_api_performance_metrics(self) -> Dict[str, Any]:
        """Get API performance metrics summary."""
        total_requests = self.api_request_count
        error_rate = (self.api_error_count / total_requests * 100) if total_requests > 0 else 0
        
        avg_response_time = (
            sum(self.api_response_times) / len(self.api_response_times)
            if self.api_response_times else 0
        )
        
        # Calculate percentiles
        sorted_times = sorted(self.api_response_times)
        p50 = sorted_times[len(sorted_times) // 2] if sorted_times else 0
        p95 = sorted_times[int(len(sorted_times) * 0.95)] if sorted_times else 0
        p99 = sorted_times[int(len(sorted_times) * 0.99)] if sorted_times else 0
        
        # Endpoint breakdown
        endpoint_summary = {}
        for endpoint, metrics in self.endpoint_metrics.items():
            response_times = list(metrics['response_times'])
            avg_time = sum(response_times) / len(response_times) if response_times else 0
            error_rate_endpoint = (
                metrics['error_count'] / metrics['request_count'] * 100
                if metrics['request_count'] > 0 else 0
            )
            
            endpoint_summary[endpoint] = {
                'request_count': metrics['request_count'],
                'error_count': metrics['error_count'],
                'error_rate': round(error_rate_endpoint, 2),
                'average_response_time': round(avg_time, 3),
                'last_request': metrics['last_request'].isoformat() if metrics['last_request'] else None
            }
        
        return {
            'total_requests': total_requests,
            'error_count': self.api_error_count,
            'error_rate': round(error_rate, 2),
            'average_response_time': round(avg_response_time, 3),
            'percentiles': {
                'p50': round(p50, 3),
                'p95': round(p95, 3),
                'p99': round(p99, 3)
            },
            'endpoints': endpoint_summary,
            'last_updated': datetime.utcnow().isoformat()
        }

    def cleanup_old_metrics(self):
        """Clean up old metric data points."""
        cutoff_time = datetime.utcnow() - timedelta(hours=self.retention_hours)
        
        for metric_name, points in self.metrics.items():
            # Remove old points
            while points and points[0].timestamp < cutoff_time:
                points.popleft()


class ExtensionAlertManager:
    """Manages alerts for extension authentication and service health."""

    def __init__(self, metrics_collector: ExtensionMetricsCollector):
        self.metrics_collector = metrics_collector
        self.alerts: Dict[str, Alert] = {}
        self.alert_history: List[Dict[str, Any]] = []
        self.notification_callbacks: List[callable] = []
        
        # Initialize default alerts
        self._setup_default_alerts()

    def _setup_default_alerts(self):
        """Set up default alert rules."""
        
        # Authentication failure rate alert
        self.add_alert(Alert(
            id="auth_failure_rate_high",
            name="High Authentication Failure Rate",
            description="Authentication failure rate exceeds 10%",
            severity=AlertSeverity.WARNING,
            condition="auth_failure_rate > 10",
            threshold=10.0
        ))
        
        # Service health alert
        self.add_alert(Alert(
            id="service_health_low",
            name="Low Service Health",
            description="Service health percentage below 80%",
            severity=AlertSeverity.ERROR,
            condition="service_health_percentage < 80",
            threshold=80.0
        ))
        
        # API error rate alert
        self.add_alert(Alert(
            id="api_error_rate_high",
            name="High API Error Rate",
            description="API error rate exceeds 5%",
            severity=AlertSeverity.WARNING,
            condition="api_error_rate > 5",
            threshold=5.0
        ))
        
        # Response time alert
        self.add_alert(Alert(
            id="api_response_time_high",
            name="High API Response Time",
            description="Average API response time exceeds 2 seconds",
            severity=AlertSeverity.WARNING,
            condition="api_avg_response_time > 2000",
            threshold=2000.0
        ))

    def add_alert(self, alert: Alert):
        """Add a new alert rule."""
        self.alerts[alert.id] = alert
        logger.info(f"Added alert rule: {alert.name}")

    def remove_alert(self, alert_id: str):
        """Remove an alert rule."""
        if alert_id in self.alerts:
            del self.alerts[alert_id]
            logger.info(f"Removed alert rule: {alert_id}")

    def add_notification_callback(self, callback: callable):
        """Add a notification callback function."""
        self.notification_callbacks.append(callback)

    async def check_alerts(self):
        """Check all alert conditions and trigger notifications."""
        auth_metrics = self.metrics_collector.get_auth_metrics()
        health_metrics = self.metrics_collector.get_service_health_metrics()
        api_metrics = self.metrics_collector.get_api_performance_metrics()
        
        current_values = {
            'auth_failure_rate': (
                auth_metrics['failure_count'] / auth_metrics['total_requests'] * 100
                if auth_metrics['total_requests'] > 0 else 0
            ),
            'service_health_percentage': health_metrics['health_percentage'],
            'api_error_rate': api_metrics['error_rate'],
            'api_avg_response_time': api_metrics['average_response_time'] * 1000  # Convert to ms
        }
        
        for alert_id, alert in self.alerts.items():
            await self._evaluate_alert(alert, current_values)

    async def _evaluate_alert(self, alert: Alert, current_values: Dict[str, float]):
        """Evaluate a single alert condition."""
        try:
            # Simple condition evaluation (can be enhanced with more complex logic)
            condition_met = False
            
            if "auth_failure_rate" in alert.condition:
                condition_met = current_values.get('auth_failure_rate', 0) > alert.threshold
            elif "service_health_percentage" in alert.condition:
                condition_met = current_values.get('service_health_percentage', 100) < alert.threshold
            elif "api_error_rate" in alert.condition:
                condition_met = current_values.get('api_error_rate', 0) > alert.threshold
            elif "api_avg_response_time" in alert.condition:
                condition_met = current_values.get('api_avg_response_time', 0) > alert.threshold
            
            if condition_met and not alert.is_active:
                # Trigger alert
                await self._trigger_alert(alert, current_values)
            elif not condition_met and alert.is_active:
                # Resolve alert
                await self._resolve_alert(alert, current_values)
                
        except Exception as e:
            logger.error(f"Error evaluating alert {alert.id}: {e}")

    async def _trigger_alert(self, alert: Alert, current_values: Dict[str, float]):
        """Trigger an alert."""
        alert.is_active = True
        alert.triggered_at = datetime.utcnow()
        alert.trigger_count += 1
        
        alert_data = {
            'alert_id': alert.id,
            'name': alert.name,
            'description': alert.description,
            'severity': alert.severity.value,
            'triggered_at': alert.triggered_at.isoformat(),
            'current_values': current_values,
            'threshold': alert.threshold
        }
        
        self.alert_history.append({
            **alert_data,
            'action': 'triggered'
        })
        
        logger.warning(f"Alert triggered: {alert.name} - {alert.description}")
        
        # Send notifications
        for callback in self.notification_callbacks:
            try:
                await callback(alert_data)
            except Exception as e:
                logger.error(f"Error sending alert notification: {e}")

    async def _resolve_alert(self, alert: Alert, current_values: Dict[str, float]):
        """Resolve an alert."""
        alert.is_active = False
        alert.resolved_at = datetime.utcnow()
        
        alert_data = {
            'alert_id': alert.id,
            'name': alert.name,
            'description': alert.description,
            'severity': alert.severity.value,
            'resolved_at': alert.resolved_at.isoformat(),
            'current_values': current_values,
            'duration': (alert.resolved_at - alert.triggered_at).total_seconds()
        }
        
        self.alert_history.append({
            **alert_data,
            'action': 'resolved'
        })
        
        logger.info(f"Alert resolved: {alert.name}")
        
        # Send resolution notifications
        for callback in self.notification_callbacks:
            try:
                await callback(alert_data)
            except Exception as e:
                logger.error(f"Error sending alert resolution notification: {e}")

    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get all currently active alerts."""
        active_alerts = []
        for alert in self.alerts.values():
            if alert.is_active:
                active_alerts.append({
                    'id': alert.id,
                    'name': alert.name,
                    'description': alert.description,
                    'severity': alert.severity.value,
                    'triggered_at': alert.triggered_at.isoformat() if alert.triggered_at else None,
                    'trigger_count': alert.trigger_count
                })
        return active_alerts

    def get_alert_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get alert history."""
        return self.alert_history[-limit:]


class ExtensionMonitoringDashboard:
    """Main dashboard for extension monitoring and alerting."""

    def __init__(self):
        self.metrics_collector = ExtensionMetricsCollector()
        self.alert_manager = ExtensionAlertManager(self.metrics_collector)
        self.monitoring_active = False
        self.monitoring_task = None
        
        # Setup default notification handlers
        self.alert_manager.add_notification_callback(self._log_alert_notification)

    async def start_monitoring(self, check_interval: int = 30):
        """Start the monitoring system."""
        if self.monitoring_active:
            logger.warning("Monitoring is already active")
            return
        
        self.monitoring_active = True
        logger.info("Starting extension monitoring dashboard")
        
        # Start monitoring loop
        self.monitoring_task = asyncio.create_task(self._monitoring_loop(check_interval))

    async def stop_monitoring(self):
        """Stop the monitoring system."""
        self.monitoring_active = False
        
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Stopped extension monitoring dashboard")

    async def _monitoring_loop(self, check_interval: int):
        """Main monitoring loop."""
        while self.monitoring_active:
            try:
                # Check alerts
                await self.alert_manager.check_alerts()
                
                # Cleanup old metrics
                self.metrics_collector.cleanup_old_metrics()
                
                # Wait for next check
                await asyncio.sleep(check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(check_interval)

    async def _log_alert_notification(self, alert_data: Dict[str, Any]):
        """Default alert notification handler that logs alerts."""
        action = alert_data.get('action', 'unknown')
        severity = alert_data.get('severity', 'unknown')
        name = alert_data.get('name', 'Unknown Alert')
        
        if action == 'triggered':
            logger.warning(f"ALERT TRIGGERED [{severity.upper()}]: {name}")
        elif action == 'resolved':
            duration = alert_data.get('duration', 0)
            logger.info(f"ALERT RESOLVED: {name} (duration: {duration:.1f}s)")

    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get complete dashboard data."""
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'monitoring_active': self.monitoring_active,
            'authentication': self.metrics_collector.get_auth_metrics(),
            'service_health': self.metrics_collector.get_service_health_metrics(),
            'api_performance': self.metrics_collector.get_api_performance_metrics(),
            'active_alerts': self.alert_manager.get_active_alerts(),
            'alert_history': self.alert_manager.get_alert_history(50)
        }

    # Convenience methods for recording metrics
    def record_auth_success(self, response_time: float, user_id: str = None):
        """Record successful authentication."""
        self.metrics_collector.record_auth_success(response_time, user_id)

    def record_auth_failure(self, response_time: float, error_type: str, user_id: str = None):
        """Record authentication failure."""
        self.metrics_collector.record_auth_failure(response_time, error_type, user_id)

    def record_token_refresh(self, response_time: float, success: bool):
        """Record token refresh attempt."""
        self.metrics_collector.record_token_refresh(response_time, success)

    def record_service_health(self, service_name: str, status: str, response_time: float = None):
        """Record service health status."""
        self.metrics_collector.record_service_health(service_name, status, response_time)

    def record_api_request(self, endpoint: str, method: str, status_code: int, response_time: float):
        """Record API request metrics."""
        self.metrics_collector.record_api_request(endpoint, method, status_code, response_time)


# Global dashboard instance
extension_dashboard = ExtensionMonitoringDashboard()