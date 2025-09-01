"""
Model Orchestrator Error Tracking Integration.

This module provides error tracking capabilities for model orchestrator operations.
"""

from .model_orchestrator_errors import (
    get_model_orchestrator_error_tracker,
    track_model_error,
    ModelOrchestratorErrorTracker,
    ModelError,
    ErrorSeverity,
    ErrorCategory
)

__all__ = [
    "get_model_orchestrator_error_tracker",
    "track_model_error",
    "ModelOrchestratorErrorTracker",
    "ModelError",
    "ErrorSeverity",
    "ErrorCategory"
]