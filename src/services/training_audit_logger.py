"""Compatibility alias for the training audit logger implementation."""

from services.memory.internal.training_audit_logger import (  # noqa: F401
    TrainingAuditEvent,
    TrainingAuditLogger,
    TrainingEventType,
    get_training_audit_logger,
)

__all__ = [
    "TrainingAuditEvent",
    "TrainingAuditLogger",
    "TrainingEventType",
    "get_training_audit_logger",
]
