"""
Extension Monitoring Package

Comprehensive monitoring and alerting system for extension authentication,
service health, and performance monitoring.
"""

from .extension_metrics_dashboard import (
    ExtensionMetricsCollector,
    ExtensionAlertManager,
    ExtensionMonitoringDashboard,
    extension_dashboard,
    MetricType,
    AlertSeverity,
    Alert
)

from .dashboard_api import (
    monitoring_router,
    MonitoringMiddleware
)

from .alerting_system import (
    ExtensionAlertingSystem,
    extension_alerting,
    NotificationChannel,
    EscalationLevel,
    NotificationConfig,
    AlertRule
)

from .performance_monitor import (
    ExtensionPerformanceMonitor,
    extension_performance_monitor,
    PerformanceMetric,
    ResourceUsage,
    EndpointStats
)

__all__ = [
    # Main dashboard
    'ExtensionMetricsCollector',
    'ExtensionAlertManager', 
    'ExtensionMonitoringDashboard',
    'extension_dashboard',
    
    # API and middleware
    'monitoring_router',
    'MonitoringMiddleware',
    
    # Alerting system
    'ExtensionAlertingSystem',
    'extension_alerting',
    'NotificationChannel',
    'EscalationLevel',
    'NotificationConfig',
    'AlertRule',
    
    # Performance monitoring
    'ExtensionPerformanceMonitor',
    'extension_performance_monitor',
    'PerformanceMetric',
    'ResourceUsage',
    'EndpointStats',
    
    # Enums and data classes
    'MetricType',
    'AlertSeverity',
    'Alert'
]