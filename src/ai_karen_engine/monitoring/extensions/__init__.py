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

from .extension_alerting_system import (
    extension_alert_manager,
    AlertType,
    EscalationLevel as MonitoringEscalationLevel
)

from .extension_error_logging import (
    extension_error_logger,
    extension_metrics_collector,
    extension_trend_analyzer,
    ErrorSeverity,
    ErrorCategory,
    AlertStatus as MonitoringAlertStatus
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
    'extension_alert_manager',
    'NotificationChannel',
    'EscalationLevel',
    'MonitoringEscalationLevel',
    'NotificationConfig',
    'AlertRule',
    'AlertType',
    
    # Error logging
    'extension_error_logger',
    'extension_metrics_collector',
    'extension_trend_analyzer',
    'ErrorSeverity',
    'ErrorCategory',
    'MonitoringAlertStatus',
    
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