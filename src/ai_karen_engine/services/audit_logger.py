"""
Alias module kept for backward compatibility.

Some routes import ``ai_karen_engine.services.audit_logger`` while others
import ``ai_karen_engine.services.audit_logging``. Both should expose the
same lightweight audit logging shim.
"""

from .audit_logging import (
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
