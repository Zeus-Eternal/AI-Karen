"""
Audit Integration Module.

This module provides comprehensive audit logging capabilities including
model orchestrator operations and performance auditing.
"""

# Import performance auditor (standalone, no system dependencies)
from .performance_auditor import (
    get_performance_auditor,
    PerformanceAuditor,
    StartupTimeContext,
    ServiceInfo,
    StartupMetrics,
    RuntimeMetrics,
    Bottleneck,
    StartupReport,
    RuntimeReport,
    ServiceType,
    BottleneckType
)

# Try to import model orchestrator audit (has system dependencies)
try:
    from .model_orchestrator_audit import (
        get_model_orchestrator_auditor,
        ModelOrchestratorAuditor,
        AuditEventType,
        ModelAuditEvent
    )
    _MODEL_ORCHESTRATOR_AVAILABLE = True
except ImportError as e:  # pragma: no cover - exercised when optional deps missing
    # Model orchestrator audit not available (missing dependencies).  Provide a
    # lightweight in-repo implementation so downstream callers can still emit
    # structured audit events rather than crashing outright.
    import json
    import logging
    import threading
    from dataclasses import asdict, dataclass, field
    from datetime import datetime
    from enum import Enum
    from pathlib import Path
    from typing import Any, Dict, Optional

    logger = logging.getLogger("ai_karen_engine.audit.fallback")
    _MODEL_ORCHESTRATOR_AVAILABLE = False

    class AuditEventType(str, Enum):
        MODEL_DOWNLOAD = "model_download"
        MODEL_REMOVE = "model_remove"
        MODEL_MIGRATION = "model_migration"
        REGISTRY_UPDATE = "registry_update"
        LICENSE_ACCEPTANCE = "license_acceptance"
        SECURITY_VALIDATION = "security_validation"
        ACCESS_CONTROL = "access_control"
        GARBAGE_COLLECTION = "garbage_collection"
        QUOTA_ENFORCEMENT = "quota_enforcement"
        COMPLIANCE_CHECK = "compliance_check"


    @dataclass
    class ModelAuditEvent:
        timestamp: str
        event_type: str
        user_id: Optional[str]
        model_id: Optional[str]
        library: Optional[str]
        operation: str
        success: bool
        correlation_id: Optional[str]
        trace_id: Optional[str]
        details: Dict[str, Any] = field(default_factory=dict)
        ip_address: Optional[str] = None
        user_agent: Optional[str] = None
        session_id: Optional[str] = None
        tenant_id: Optional[str] = None

        def to_dict(self) -> Dict[str, Any]:
            payload = asdict(self)
            payload["details"] = dict(self.details or {})
            return payload


    class ModelOrchestratorAuditor:
        """Fallback auditor that persists events to a local JSONL file."""

        def __init__(self, audit_log_path: Optional[Path | str] = None) -> None:
            self.audit_log_path = Path(audit_log_path or "logs/model_orchestrator_audit.log")
            self.audit_log_path.parent.mkdir(parents=True, exist_ok=True)
            self._lock = threading.Lock()
            logger.debug(
                "Model orchestrator audit fallback initialised at %s due to: %s",
                self.audit_log_path,
                e,
            )

        def _record_event(
            self,
            event_type: AuditEventType,
            *,
            operation: str,
            success: bool,
            details: Optional[Dict[str, Any]] = None,
            **extra: Any,
        ) -> ModelAuditEvent:
            event = ModelAuditEvent(
                timestamp=datetime.utcnow().isoformat() + "Z",
                event_type=event_type.value,
                operation=operation,
                success=success,
                details=details or {},
                user_id=extra.get("user_id"),
                model_id=extra.get("model_id"),
                library=extra.get("library"),
                correlation_id=extra.get("correlation_id"),
                trace_id=extra.get("trace_id"),
                ip_address=extra.get("ip_address"),
                user_agent=extra.get("user_agent"),
                session_id=extra.get("session_id"),
                tenant_id=extra.get("tenant_id"),
            )

            payload = json.dumps(event.to_dict(), default=str)
            with self._lock:
                with self.audit_log_path.open("a", encoding="utf-8") as handle:
                    handle.write(payload + "\n")

            logger.info(
                "[fallback] %s operation=%s success=%s model=%s user=%s",
                event.event_type,
                event.operation,
                event.success,
                event.model_id,
                event.user_id,
            )
            return event

        def audit_model_download(self, *args, **kwargs) -> ModelAuditEvent:
            return self._record_event(AuditEventType.MODEL_DOWNLOAD, operation="download", **self._split_args(args, kwargs))

        def audit_model_removal(self, *args, **kwargs) -> ModelAuditEvent:
            return self._record_event(AuditEventType.MODEL_REMOVE, operation="remove", **self._split_args(args, kwargs))

        def audit_license_acceptance(self, *args, **kwargs) -> ModelAuditEvent:
            return self._record_event(AuditEventType.LICENSE_ACCEPTANCE, operation="license", **self._split_args(args, kwargs))

        def audit_security_validation(self, *args, **kwargs) -> ModelAuditEvent:
            return self._record_event(AuditEventType.SECURITY_VALIDATION, operation="security", **self._split_args(args, kwargs))

        def audit_access_control(self, *args, **kwargs) -> ModelAuditEvent:
            return self._record_event(AuditEventType.ACCESS_CONTROL, operation="access", **self._split_args(args, kwargs))

        def audit_registry_operation(self, *args, **kwargs) -> ModelAuditEvent:
            return self._record_event(AuditEventType.REGISTRY_UPDATE, operation="registry", **self._split_args(args, kwargs))

        def audit_migration_operation(self, *args, **kwargs) -> ModelAuditEvent:
            return self._record_event(AuditEventType.MODEL_MIGRATION, operation="migration", **self._split_args(args, kwargs))

        def audit_garbage_collection(self, *args, **kwargs) -> ModelAuditEvent:
            return self._record_event(AuditEventType.GARBAGE_COLLECTION, operation="gc", **self._split_args(args, kwargs))

        def audit_quota_enforcement(self, *args, **kwargs) -> ModelAuditEvent:
            return self._record_event(AuditEventType.QUOTA_ENFORCEMENT, operation="quota", **self._split_args(args, kwargs))

        def audit_compliance_check(self, *args, **kwargs) -> ModelAuditEvent:
            return self._record_event(AuditEventType.COMPLIANCE_CHECK, operation="compliance", **self._split_args(args, kwargs))

        @staticmethod
        def _split_args(args: tuple, kwargs: Dict[str, Any]) -> Dict[str, Any]:
            """Normalise positional arguments to match the fallback signature."""

            if args:
                positional_mapping = [
                    "model_id",
                    "user_id",
                    "library",
                    "success",
                ]
                for key, value in zip(positional_mapping, args):
                    kwargs.setdefault(key, value)

            details = kwargs.pop("details", None)
            if details is None:
                details = {
                    k: kwargs.get(k)
                    for k in ("bytes_downloaded", "duration_seconds", "bytes_freed", "message")
                    if k in kwargs
                }
            for transient_key in ("bytes_downloaded", "duration_seconds", "bytes_freed", "message"):
                kwargs.pop(transient_key, None)

            request_info = kwargs.pop("request_info", None)
            if request_info:
                kwargs.setdefault("ip_address", request_info.get("ip_address"))
                kwargs.setdefault("user_agent", request_info.get("user_agent"))
                kwargs.setdefault("session_id", request_info.get("session_id"))
                kwargs.setdefault("tenant_id", request_info.get("tenant_id"))

            trace_context = kwargs.pop("trace_context", None)
            if trace_context:
                kwargs.setdefault("correlation_id", getattr(trace_context, "correlation_id", None))
                kwargs.setdefault("trace_id", getattr(trace_context, "trace_id", None))
            kwargs.setdefault("details", details)
            kwargs.setdefault("success", True)
            return kwargs


    _fallback_singleton: Optional[ModelOrchestratorAuditor] = None

    def get_model_orchestrator_auditor(audit_log_path: Optional[Path | str] = None) -> ModelOrchestratorAuditor:
        """Return a singleton fallback auditor."""

        global _fallback_singleton
        if _fallback_singleton is None:
            _fallback_singleton = ModelOrchestratorAuditor(audit_log_path)
        elif audit_log_path and Path(audit_log_path) != _fallback_singleton.audit_log_path:
            _fallback_singleton = ModelOrchestratorAuditor(audit_log_path)
        return _fallback_singleton

__all__ = [
    # Performance audit (always available)
    "get_performance_auditor",
    "PerformanceAuditor",
    "StartupTimeContext",
    "ServiceInfo",
    "StartupMetrics",
    "RuntimeMetrics",
    "Bottleneck",
    "StartupReport",
    "RuntimeReport",
    "ServiceType",
    "BottleneckType",
    
    # Model orchestrator audit (may not be available)
    "get_model_orchestrator_auditor",
    "ModelOrchestratorAuditor",
    "AuditEventType", 
    "ModelAuditEvent",
]