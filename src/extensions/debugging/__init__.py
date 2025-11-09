"""
Extension Debugging and Monitoring Module

Provides comprehensive debugging, monitoring, and diagnostic capabilities for extensions.
"""

from .debug_manager import ExtensionDebugManager
from .logger import ExtensionLogger
from .metrics_collector import ExtensionMetricsCollector
from .error_tracker import ExtensionErrorTracker
from .profiler import ExtensionProfiler
from .tracer import ExtensionTracer
from .alerting import ExtensionAlertManager
from .dashboard import ExtensionDebugDashboard

__all__ = [
    'ExtensionDebugManager',
    'ExtensionLogger',
    'ExtensionMetricsCollector',
    'ExtensionErrorTracker',
    'ExtensionProfiler',
    'ExtensionTracer',
    'ExtensionAlertManager',
    'ExtensionDebugDashboard'
]