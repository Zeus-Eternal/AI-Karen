"""
Model Orchestrator Audit Integration.

This module integrates model orchestrator operations with the existing
audit trail system, providing comprehensive audit logging for compliance.
"""

import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from pathlib import Path
from enum import Enum

from ai_karen_engine.security.access_control import audit_logger
from ai_karen_engine.monitoring.model_orchestrator_tracing import TraceContext

logger = logging.getLogger(__name__)


class AuditEventType(Enum):
    """Types of audit events for model operations."""
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
    """Audit event for model operations."""
    timestamp: str
    event_type: str
    user_id: Optional[str]
    model_id: Optional[str]
    library: Optional[str]
    operation: str
    success: bool
    correlation_id: Optional[str]
    trace_id: Optional[str]
    details: Dict[str, Any]
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None
    tenant_id: Optional[str] = None


class ModelOrchestratorAuditor:
    """
    Audit logger for model orchestrator operations.
    
    Integrates with existing audit trail system and provides
    comprehensive audit logging for compliance and security.
    """
    
    def __init__(self, audit_log_path: Optional[Path] = None):
        self.audit_log_path = audit_log_path or Path("logs/model_orchestrator_audit.log")
        self.audit_log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Integration with existing audit logger
        self.system_audit_logger = audit_logger
        
        logger.debug(f"Model orchestrator auditor initialized: {self.audit_log_path}")
    
    def _create_audit_event(
        self,
        event_type: AuditEventType,
        operation: str,
        success: bool,
        user_id: Optional[str] = None,
        model_id: Optional[str] = None,
        library: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        trace_context: Optional[TraceContext] = None,
        request_info: Optional[Dict[str, str]] = None
    ) -> ModelAuditEvent:
        """Create an audit event."""
        return ModelAuditEvent(
            timestamp=datetime.utcnow().isoformat() + "Z",
            event_type=event_type.value,
            user_id=user_id,
            model_id=model_id,
            library=library,
            operation=operation,
            success=success,
            correlation_id=trace_context.correlation_id if trace_context else None,
            trace_id=trace_context.trace_id if trace_context else None,
            details=details or {},
            ip_address=request_info.get("ip_address") if request_info else None,
            user_agent=request_info.get("user_agent") if request_info else None,
            session_id=request_info.get("session_id") if request_info else None,
            tenant_id=request_info.get("tenant_id") if request_info else None
        )
    
    def _write_audit_event(self, event: ModelAuditEvent):
        """Write audit event to log file and integrate with system audit logger."""
        try:
            # Write to model orchestrator audit log
            event_dict = asdict(event)
            with open(self.audit_log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(event_dict, default=str) + '\n')
            
            # Integrate with existing system audit logger for cloud usage tracking
            if event.model_id and event.success:
                # Map model operations to cloud usage for compliance
                provider = self._determine_provider(event.library, event.model_id)
                model_name = self._extract_model_name(event.model_id)
                
                self.system_audit_logger.log_cloud_usage(
                    user_id=event.user_id or "system",
                    provider=provider,
                    model=model_name
                )
            
            logger.debug(f"Audit event recorded: {event.event_type} for {event.model_id}")
            
        except Exception as e:
            logger.error(f"Failed to write audit event: {e}")
    
    def _determine_provider(self, library: Optional[str], model_id: str) -> str:
        """Determine the provider based on library and model ID."""
        if library == "transformers":
            return "huggingface"
        elif library == "llama-cpp":
            return "llamacpp"
        elif library == "spacy":
            return "spacy"
        elif library == "sklearn":
            return "sklearn"
        elif "/" in model_id:
            # Assume HuggingFace format (owner/model)
            return "huggingface"
        else:
            return "unknown"
    
    def _extract_model_name(self, model_id: str) -> str:
        """Extract model name from model ID."""
        if "/" in model_id:
            return model_id.split("/")[-1]
        return model_id
    
    def audit_model_download(
        self,
        model_id: str,
        user_id: str,
        library: str,
        success: bool,
        bytes_downloaded: Optional[int] = None,
        duration_seconds: Optional[float] = None,
        error_message: Optional[str] = None,
        trace_context: Optional[TraceContext] = None,
        request_info: Optional[Dict[str, str]] = None
    ):
        """Audit model download operations."""
        details = {
            "bytes_downloaded": bytes_downloaded,
            "duration_seconds": duration_seconds
        }
        if error_message:
            details["error_message"] = error_message
        
        event = self._create_audit_event(
            event_type=AuditEventType.MODEL_DOWNLOAD,
            operation="download",
            success=success,
            user_id=user_id,
            model_id=model_id,
            library=library,
            details=details,
            trace_context=trace_context,
            request_info=request_info
        )
        self._write_audit_event(event)
    
    def audit_model_removal(
        self,
        model_id: str,
        user_id: str,
        library: str,
        success: bool,
        bytes_freed: Optional[int] = None,
        error_message: Optional[str] = None,
        trace_context: Optional[TraceContext] = None,
        request_info: Optional[Dict[str, str]] = None
    ):
        """Audit model removal operations."""
        details = {
            "bytes_freed": bytes_freed
        }
        if error_message:
            details["error_message"] = error_message
        
        event = self._create_audit_event(
            event_type=AuditEventType.MODEL_REMOVE,
            operation="remove",
            success=success,
            user_id=user_id,
            model_id=model_id,
            library=library,
            details=details,
            trace_context=trace_context,
            request_info=request_info
        )
        self._write_audit_event(event)
    
    def audit_license_acceptance(
        self,
        model_id: str,
        user_id: str,
        license_type: str,
        license_url: Optional[str] = None,
        trace_context: Optional[TraceContext] = None,
        request_info: Optional[Dict[str, str]] = None
    ):
        """Audit license acceptance events."""
        details = {
            "license_type": license_type,
            "license_url": license_url,
            "acceptance_timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        event = self._create_audit_event(
            event_type=AuditEventType.LICENSE_ACCEPTANCE,
            operation="license_acceptance",
            success=True,
            user_id=user_id,
            model_id=model_id,
            details=details,
            trace_context=trace_context,
            request_info=request_info
        )
        self._write_audit_event(event)
    
    def audit_security_validation(
        self,
        model_id: str,
        user_id: str,
        validation_type: str,
        success: bool,
        security_details: Dict[str, Any],
        error_message: Optional[str] = None,
        trace_context: Optional[TraceContext] = None,
        request_info: Optional[Dict[str, str]] = None
    ):
        """Audit security validation events."""
        details = {
            "validation_type": validation_type,
            "security_details": security_details
        }
        if error_message:
            details["error_message"] = error_message
        
        event = self._create_audit_event(
            event_type=AuditEventType.SECURITY_VALIDATION,
            operation=f"security_{validation_type}",
            success=success,
            user_id=user_id,
            model_id=model_id,
            details=details,
            trace_context=trace_context,
            request_info=request_info
        )
        self._write_audit_event(event)
    
    def audit_access_control(
        self,
        operation: str,
        user_id: str,
        model_id: Optional[str],
        permission_required: str,
        access_granted: bool,
        reason: Optional[str] = None,
        trace_context: Optional[TraceContext] = None,
        request_info: Optional[Dict[str, str]] = None
    ):
        """Audit access control decisions."""
        details = {
            "permission_required": permission_required,
            "access_granted": access_granted,
            "reason": reason
        }
        
        event = self._create_audit_event(
            event_type=AuditEventType.ACCESS_CONTROL,
            operation=f"access_control_{operation}",
            success=access_granted,
            user_id=user_id,
            model_id=model_id,
            details=details,
            trace_context=trace_context,
            request_info=request_info
        )
        self._write_audit_event(event)
    
    def audit_registry_operation(
        self,
        operation: str,
        user_id: Optional[str],
        model_id: Optional[str],
        success: bool,
        changes: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
        trace_context: Optional[TraceContext] = None
    ):
        """Audit registry operations."""
        details = {
            "changes": changes or {}
        }
        if error_message:
            details["error_message"] = error_message
        
        event = self._create_audit_event(
            event_type=AuditEventType.REGISTRY_UPDATE,
            operation=f"registry_{operation}",
            success=success,
            user_id=user_id,
            model_id=model_id,
            details=details,
            trace_context=trace_context
        )
        self._write_audit_event(event)
    
    def audit_migration_operation(
        self,
        migration_type: str,
        user_id: str,
        models_processed: int,
        success: bool,
        duration_seconds: Optional[float] = None,
        models_migrated: Optional[List[str]] = None,
        error_message: Optional[str] = None,
        trace_context: Optional[TraceContext] = None,
        request_info: Optional[Dict[str, str]] = None
    ):
        """Audit migration operations."""
        details = {
            "migration_type": migration_type,
            "models_processed": models_processed,
            "duration_seconds": duration_seconds,
            "models_migrated": models_migrated or []
        }
        if error_message:
            details["error_message"] = error_message
        
        event = self._create_audit_event(
            event_type=AuditEventType.MODEL_MIGRATION,
            operation=f"migration_{migration_type}",
            success=success,
            user_id=user_id,
            details=details,
            trace_context=trace_context,
            request_info=request_info
        )
        self._write_audit_event(event)
    
    def audit_garbage_collection(
        self,
        trigger: str,
        user_id: Optional[str],
        models_removed: List[str],
        bytes_freed: int,
        success: bool,
        error_message: Optional[str] = None,
        trace_context: Optional[TraceContext] = None
    ):
        """Audit garbage collection operations."""
        details = {
            "trigger": trigger,
            "models_removed": models_removed,
            "bytes_freed": bytes_freed,
            "models_count": len(models_removed)
        }
        if error_message:
            details["error_message"] = error_message
        
        event = self._create_audit_event(
            event_type=AuditEventType.GARBAGE_COLLECTION,
            operation="garbage_collection",
            success=success,
            user_id=user_id,
            details=details,
            trace_context=trace_context
        )
        self._write_audit_event(event)
    
    def audit_quota_enforcement(
        self,
        user_id: str,
        operation: str,
        quota_bytes: int,
        current_usage_bytes: int,
        requested_bytes: int,
        allowed: bool,
        trace_context: Optional[TraceContext] = None,
        request_info: Optional[Dict[str, str]] = None
    ):
        """Audit quota enforcement decisions."""
        details = {
            "quota_bytes": quota_bytes,
            "current_usage_bytes": current_usage_bytes,
            "requested_bytes": requested_bytes,
            "usage_percent": (current_usage_bytes / quota_bytes) * 100 if quota_bytes > 0 else 0
        }
        
        event = self._create_audit_event(
            event_type=AuditEventType.QUOTA_ENFORCEMENT,
            operation=f"quota_{operation}",
            success=allowed,
            user_id=user_id,
            details=details,
            trace_context=trace_context,
            request_info=request_info
        )
        self._write_audit_event(event)
    
    def audit_compliance_check(
        self,
        check_type: str,
        user_id: Optional[str],
        model_id: Optional[str],
        compliant: bool,
        compliance_details: Dict[str, Any],
        trace_context: Optional[TraceContext] = None
    ):
        """Audit compliance checks."""
        details = {
            "check_type": check_type,
            "compliance_details": compliance_details
        }
        
        event = self._create_audit_event(
            event_type=AuditEventType.COMPLIANCE_CHECK,
            operation=f"compliance_{check_type}",
            success=compliant,
            user_id=user_id,
            model_id=model_id,
            details=details,
            trace_context=trace_context
        )
        self._write_audit_event(event)
    
    def get_audit_summary(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        user_id: Optional[str] = None,
        event_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get audit summary for reporting."""
        try:
            if not self.audit_log_path.exists():
                return {"error": "Audit log file not found"}
            
            events = []
            with open(self.audit_log_path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        event = json.loads(line.strip())
                        
                        # Apply filters
                        event_time = datetime.fromisoformat(event['timestamp'].replace('Z', '+00:00'))
                        
                        if start_date and event_time < start_date:
                            continue
                        if end_date and event_time > end_date:
                            continue
                        if user_id and event.get('user_id') != user_id:
                            continue
                        if event_type and event.get('event_type') != event_type:
                            continue
                        
                        events.append(event)
                        
                    except json.JSONDecodeError:
                        continue
            
            # Generate summary statistics
            total_events = len(events)
            successful_events = sum(1 for e in events if e.get('success', False))
            failed_events = total_events - successful_events
            
            event_types = {}
            users = {}
            models = {}
            
            for event in events:
                # Count by event type
                event_type = event.get('event_type', 'unknown')
                event_types[event_type] = event_types.get(event_type, 0) + 1
                
                # Count by user
                user = event.get('user_id', 'unknown')
                users[user] = users.get(user, 0) + 1
                
                # Count by model
                model = event.get('model_id')
                if model:
                    models[model] = models.get(model, 0) + 1
            
            return {
                "summary": {
                    "total_events": total_events,
                    "successful_events": successful_events,
                    "failed_events": failed_events,
                    "success_rate": (successful_events / total_events) * 100 if total_events > 0 else 0
                },
                "by_event_type": event_types,
                "by_user": users,
                "by_model": models,
                "date_range": {
                    "start": start_date.isoformat() if start_date else None,
                    "end": end_date.isoformat() if end_date else None
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating audit summary: {e}")
            return {"error": str(e)}


# Global auditor instance
_model_orchestrator_auditor: Optional[ModelOrchestratorAuditor] = None


def get_model_orchestrator_auditor() -> ModelOrchestratorAuditor:
    """Get the global model orchestrator auditor instance."""
    global _model_orchestrator_auditor
    if _model_orchestrator_auditor is None:
        _model_orchestrator_auditor = ModelOrchestratorAuditor()
    return _model_orchestrator_auditor