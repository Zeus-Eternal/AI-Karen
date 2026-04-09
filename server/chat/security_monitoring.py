"""
Security monitoring wrapper for AI-Karen Production Chat System
Provides compatibility layer for modules expecting security_monitoring module
"""

from .monitoring import (
    get_chat_monitoring_service,
    get_chat_monitoring_service as get_security_monitoring_service,
    record_chat_metric,
    start_chat_session,
    update_chat_session,
    end_chat_session,
    MetricType,
    log_security_event,
    SecurityEvent,
    ThreatLevel,
    get_security_monitor,
    ChatMonitoringService,
    SystemMetric,
    ChatSessionMetrics,
    AlertStatus,
    MetricType as SecurityMetricType,
)
