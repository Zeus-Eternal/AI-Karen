"""
Compatibility shim namespace so legacy imports keep working while the implementation
now lives under ``services.audit_logging``.
"""

from ai_karen_engine.audit_logging import (
    AuditEvent,
    AuditEventType,
    AuditLogger,
    AuditSeverity,
    get_audit_logger,
)

__all__ = [
    "AuditEvent",
    "AuditEventType",
    "AuditLogger",
    "AuditSeverity",
    "get_audit_logger",
]
