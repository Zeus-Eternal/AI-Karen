"""
Error Handling and Recovery Components for CoPilot Frontend

This module provides comprehensive error handling, recovery mechanisms, and
user-friendly error display components for the CoPilot frontend.
"""

from .types import *
from .ErrorBoundary import *
from .ErrorDisplay import *
from .ErrorNotification import *
from .ErrorRecovery import *
from .ErrorReporting import *
from .index import *

__all__ = [
    # Types
    "ErrorInfo",
    "ErrorSeverity",
    "ErrorCategory",
    "RecoveryAction",
    "NotificationType",
    
    # Components
    "ErrorBoundary",
    "ErrorDisplay",
    "ErrorNotification",
    "ErrorRecovery",
    "ErrorReporting",
    
    # Main export
    "ErrorHandling",
]