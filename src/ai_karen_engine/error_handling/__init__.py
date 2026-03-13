"""
Error Handling and Recovery System for CoPilot

This module provides comprehensive error handling, recovery mechanisms, and retry strategies
throughout the CoPilot application with intelligent classification, monitoring, and recovery.
"""

from .error_classifier import ErrorClassifier, ErrorCategory, ErrorSeverity, ErrorType
from .retry_manager import RetryManager, RetryStrategy, RetryConfig
from .circuit_breaker import CircuitBreaker, CircuitBreakerState
from .error_recovery import ErrorRecoveryManager, RecoveryStrategy
from .error_monitoring import ErrorMonitor, ErrorAnalytics, ErrorPattern
from .error_context import ErrorContext, ContextManager
from .error_notifier import ErrorNotifier, NotificationChannel
from .graceful_degradation import DegradationManager, DegradationLevel
from .error_handler import ErrorHandler, GlobalErrorHandler

__all__ = [
    # Core error classification
    "ErrorClassifier",
    "ErrorCategory", 
    "ErrorSeverity",
    "ErrorType",
    
    # Retry mechanisms
    "RetryManager",
    "RetryStrategy",
    "RetryConfig",
    
    # Circuit breaker patterns
    "CircuitBreaker",
    "CircuitBreakerState",
    
    # Recovery strategies
    "ErrorRecoveryManager",
    "RecoveryStrategy",
    
    # Monitoring and analytics
    "ErrorMonitor",
    "ErrorAnalytics", 
    "ErrorPattern",
    
    # Context management
    "ErrorContext",
    "ContextManager",
    
    # Notifications
    "ErrorNotifier",
    "NotificationChannel",
    
    # Graceful degradation
    "DegradationManager",
    "DegradationLevel",
    
    # Main error handler
    "ErrorHandler",
    "GlobalErrorHandler",
]