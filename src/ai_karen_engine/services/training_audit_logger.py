"""
Enhanced Audit Logging for Training and Model Management Operations

This module provides specialized audit logging for Response Core Orchestrator
training operations, model management, and administrative activities with
comprehensive security monitoring and compliance tracking.

Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6
"""

import json
import logging
import time
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field, asdict

from ai_karen_engine.services.audit_logging import get_audit_logger, AuditEventType, AuditSeverity
# Simple auth - using dict instead of UserData model
from ai_karen_engine.core.logging import get_logger

logger = get_logger(__name__)


class TrainingEventType(str, Enum):
    """Types of training-related audit events."""
    # Training operations
    TRAINING_STARTED = "training_started"
    TRAINING_COMPLETED = "training_completed"
    TRAINING_FAILED = "training_failed"
    TRAINING_CANCELLED = "training_cancelled"
    TRAINING_PAUSED = "training_paused"
    TRAINING_RESUMED = "training_resumed"
    
    # Model operations
    MODEL_CREATED = "model_created"
    MODEL_UPDATED = "model_updated"
    MODEL_DELETED = "model_deleted"
    MODEL_DEPLOYED = "model_deployed"
    MODEL_ARCHIVED = "model_archived"
    MODEL_RESTORED = "model_restored"
    MODEL_ACCESSED = "model_accessed"
    MODEL_EXPORTED = "model_exported"
    MODEL_IMPORTED = "model_imported"
    
    # Data operations
    TRAINING_DATA_UPLOADED = "training_data_uploaded"
    TRAINING_DATA_MODIFIED = "training_data_modified"
    TRAINING_DATA_DELETED = "training_data_deleted"
    TRAINING_DATA_EXPORTED = "training_data_exported"
    TRAINING_DATA_VALIDATED = "training_data_validated"
    
    # Scheduler operations
    SCHEDULE_CREATED = "schedule_created"
    SCHEDULE_UPDATED = "schedule_updated"
    SCHEDULE_DELETED = "schedule_deleted"
    SCHEDULE_EXECUTED = "schedule_executed"
    AUTONOMOUS_LEARNING_TRIGGERED = "autonomous_learning_triggered"
    
    # Configuration changes
    CONFIG_UPDATED = "config_updated"
    HYPERPARAMETERS_CHANGED = "hyperparameters_changed"
    SAFETY_CONTROLS_MODIFIED = "safety_controls_modified"
    
    # Security events
    UNAUTHORIZED_ACCESS_ATTEMPT = "unauthorized_access_attempt"
    PERMISSION_DENIED = "permission_denied"
    SECURITY_VIOLATION = "security_violation"
    MODEL_INTEGRITY_CHECK_FAILED = "model_integrity_check_failed"
    
    # System events
    SYSTEM_BACKUP_CREATED = "system_backup_created"
    SYSTEM_RESTORED = "system_restored"
    MAINTENANCE_MODE_ENABLED = "maintenance_mode_enabled"
    MAINTENANCE_MODE_DISABLED = "maintenance_mode_disabled"


@dataclass
class TrainingAuditEvent:
    """Specialized audit event for training operations."""
    event_type: TrainingEventType
    severity: AuditSeverity
    message: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    # User context
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    user_roles: List[str] = field(default_factory=list)
    tenant_id: str = "default"
    
    # Request context
    ip_address: str = "unknown"
    user_agent: str = ""
    session_id: Optional[str] = None
    correlation_id: Optional[str] = None
    
    # Training context
    training_job_id: Optional[str] = None
    model_id: Optional[str] = None
    dataset_id: Optional[str] = None
    schedule_id: Optional[str] = None
    
    # Operation details
    operation_type: str = ""
    resource_type: str = ""
    resource_id: Optional[str] = None
    
    # Performance metrics
    duration_ms: Optional[float] = None
    memory_usage_mb: Optional[float] = None
    cpu_usage_percent: Optional[float] = None
    
    # Results and metadata
    success: bool = True
    error_message: Optional[str] = None
    result_summary: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Security context
    permission_required: Optional[str] = None
    permission_granted: bool = True
    security_flags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['event_type'] = self.event_type.value
        data['severity'] = self.severity.value
        return data


class TrainingAuditLogger:
    """Specialized audit logger for training and model management operations."""
    
    def __init__(self):
        """Initialize training audit logger."""
        self.base_audit_logger = get_audit_logger()
        self.training_logger = get_logger("training_audit")
        
        # Event counters for metrics
        self._event_counts: Dict[str, int] = {}
        self._security_events: List[TrainingAuditEvent] = []
    
    def _log_event(self, event: TrainingAuditEvent) -> None:
        """Log a training audit event."""
        try:
            # Convert to dict and log
            event_dict = event.to_dict()
            
            # Update event counters
            event_type = event.event_type.value
            self._event_counts[event_type] = self._event_counts.get(event_type, 0) + 1
            
            # Store security events for analysis
            if event.event_type in [
                TrainingEventType.UNAUTHORIZED_ACCESS_ATTEMPT,
                TrainingEventType.PERMISSION_DENIED,
                TrainingEventType.SECURITY_VIOLATION,
                TrainingEventType.MODEL_INTEGRITY_CHECK_FAILED
            ]:
                self._security_events.append(event)
                # Keep only last 1000 security events
                self._security_events = self._security_events[-1000:]
            
            # Log to appropriate logger based on severity
            extra = {
                "training_audit_event": event_dict,
                "correlation_id": event.correlation_id,
                "user_id": event.user_id,
                "tenant_id": event.tenant_id,
                "training_job_id": event.training_job_id,
                "model_id": event.model_id,
                "dataset_id": event.dataset_id,
                "operation_type": event.operation_type,
                "resource_type": event.resource_type,
                "success": event.success
            }
            
            if event.severity == AuditSeverity.CRITICAL:
                self.training_logger.critical(event.message, **extra)
            elif event.severity == AuditSeverity.ERROR:
                self.training_logger.error(event.message, **extra)
            elif event.severity == AuditSeverity.WARNING:
                self.training_logger.warning(event.message, **extra)
            else:
                self.training_logger.info(event.message, **extra)
            
            # Also log to base audit system for centralized tracking
            self.base_audit_logger.log_audit_event({
                "event_type": "training_operation",
                "severity": event.severity.value,
                "message": event.message,
                "user_id": event.user_id,
                "tenant_id": event.tenant_id,
                "ip_address": event.ip_address,
                "correlation_id": event.correlation_id,
                "metadata": {
                    "training_event_type": event.event_type.value,
                    "training_job_id": event.training_job_id,
                    "model_id": event.model_id,
                    "dataset_id": event.dataset_id,
                    "operation_type": event.operation_type,
                    "resource_type": event.resource_type,
                    "success": event.success,
                    "duration_ms": event.duration_ms,
                    **event.metadata
                }
            })
            
        except Exception as e:
            logger.error(f"Failed to log training audit event: {e}")
    
    # Training Operation Logging
    
    def log_training_started(
        self,
        user: dict,
        training_job_id: str,
        model_id: Optional[str] = None,
        dataset_id: Optional[str] = None,
        training_config: Optional[Dict[str, Any]] = None,
        ip_address: str = "unknown",
        correlation_id: Optional[str] = None,
        **metadata
    ) -> None:
        """Log training job start."""
        event = TrainingAuditEvent(
            event_type=TrainingEventType.TRAINING_STARTED,
            severity=AuditSeverity.INFO,
            message=f"Training job {training_job_id} started",
            user_id=user.get("user_id"),
            user_email=user.get("email"),
            user_roles=user.get("roles", []),
            tenant_id=user.tenant_id,
            ip_address=ip_address,
            correlation_id=correlation_id,
            training_job_id=training_job_id,
            model_id=model_id,
            dataset_id=dataset_id,
            operation_type="training",
            resource_type="training_job",
            resource_id=training_job_id,
            metadata={
                "training_config": training_config,
                **metadata
            }
        )
        self._log_event(event)
    
    def log_training_completed(
        self,
        user: dict,
        training_job_id: str,
        model_id: Optional[str] = None,
        duration_ms: Optional[float] = None,
        performance_metrics: Optional[Dict[str, float]] = None,
        correlation_id: Optional[str] = None,
        **metadata
    ) -> None:
        """Log training job completion."""
        event = TrainingAuditEvent(
            event_type=TrainingEventType.TRAINING_COMPLETED,
            severity=AuditSeverity.INFO,
            message=f"Training job {training_job_id} completed successfully",
            user_id=user.get("user_id"),
            user_email=user.get("email"),
            user_roles=user.get("roles", []),
            tenant_id=user.tenant_id,
            correlation_id=correlation_id,
            training_job_id=training_job_id,
            model_id=model_id,
            operation_type="training",
            resource_type="training_job",
            resource_id=training_job_id,
            duration_ms=duration_ms,
            success=True,
            result_summary="Training completed successfully",
            metadata={
                "performance_metrics": performance_metrics,
                **metadata
            }
        )
        self._log_event(event)
    
    def log_training_failed(
        self,
        user: dict,
        training_job_id: str,
        error_message: str,
        model_id: Optional[str] = None,
        duration_ms: Optional[float] = None,
        correlation_id: Optional[str] = None,
        **metadata
    ) -> None:
        """Log training job failure."""
        event = TrainingAuditEvent(
            event_type=TrainingEventType.TRAINING_FAILED,
            severity=AuditSeverity.ERROR,
            message=f"Training job {training_job_id} failed: {error_message}",
            user_id=user.get("user_id"),
            user_email=user.get("email"),
            user_roles=user.get("roles", []),
            tenant_id=user.tenant_id,
            correlation_id=correlation_id,
            training_job_id=training_job_id,
            model_id=model_id,
            operation_type="training",
            resource_type="training_job",
            resource_id=training_job_id,
            duration_ms=duration_ms,
            success=False,
            error_message=error_message,
            metadata=metadata
        )
        self._log_event(event)
    
    # Model Operation Logging
    
    def log_model_created(
        self,
        user: dict,
        model_id: str,
        model_name: str,
        model_type: str,
        file_size: Optional[int] = None,
        encrypted: bool = False,
        ip_address: str = "unknown",
        correlation_id: Optional[str] = None,
        **metadata
    ) -> None:
        """Log model creation."""
        event = TrainingAuditEvent(
            event_type=TrainingEventType.MODEL_CREATED,
            severity=AuditSeverity.INFO,
            message=f"Model {model_name} created",
            user_id=user.get("user_id"),
            user_email=user.get("email"),
            user_roles=user.get("roles", []),
            tenant_id=user.tenant_id,
            ip_address=ip_address,
            correlation_id=correlation_id,
            model_id=model_id,
            operation_type="create",
            resource_type="model",
            resource_id=model_id,
            metadata={
                "model_name": model_name,
                "model_type": model_type,
                "file_size": file_size,
                "encrypted": encrypted,
                **metadata
            }
        )
        self._log_event(event)
    
    def log_model_accessed(
        self,
        user: dict,
        model_id: str,
        model_name: str,
        access_type: str = "read",
        ip_address: str = "unknown",
        correlation_id: Optional[str] = None,
        **metadata
    ) -> None:
        """Log model access."""
        event = TrainingAuditEvent(
            event_type=TrainingEventType.MODEL_ACCESSED,
            severity=AuditSeverity.INFO,
            message=f"Model {model_name} accessed ({access_type})",
            user_id=user.get("user_id"),
            user_email=user.get("email"),
            user_roles=user.get("roles", []),
            tenant_id=user.tenant_id,
            ip_address=ip_address,
            correlation_id=correlation_id,
            model_id=model_id,
            operation_type=access_type,
            resource_type="model",
            resource_id=model_id,
            metadata={
                "model_name": model_name,
                "access_type": access_type,
                **metadata
            }
        )
        self._log_event(event)
    
    def log_model_deleted(
        self,
        user: dict,
        model_id: str,
        model_name: str,
        ip_address: str = "unknown",
        correlation_id: Optional[str] = None,
        **metadata
    ) -> None:
        """Log model deletion."""
        event = TrainingAuditEvent(
            event_type=TrainingEventType.MODEL_DELETED,
            severity=AuditSeverity.WARNING,
            message=f"Model {model_name} deleted",
            user_id=user.get("user_id"),
            user_email=user.get("email"),
            user_roles=user.get("roles", []),
            tenant_id=user.tenant_id,
            ip_address=ip_address,
            correlation_id=correlation_id,
            model_id=model_id,
            operation_type="delete",
            resource_type="model",
            resource_id=model_id,
            metadata={
                "model_name": model_name,
                **metadata
            }
        )
        self._log_event(event)
    
    # Data Operation Logging
    
    def log_training_data_uploaded(
        self,
        user: dict,
        dataset_id: str,
        dataset_name: str,
        record_count: int,
        file_size: int,
        data_format: str,
        ip_address: str = "unknown",
        correlation_id: Optional[str] = None,
        **metadata
    ) -> None:
        """Log training data upload."""
        event = TrainingAuditEvent(
            event_type=TrainingEventType.TRAINING_DATA_UPLOADED,
            severity=AuditSeverity.INFO,
            message=f"Training data uploaded to dataset {dataset_name}",
            user_id=user.get("user_id"),
            user_email=user.get("email"),
            user_roles=user.get("roles", []),
            tenant_id=user.tenant_id,
            ip_address=ip_address,
            correlation_id=correlation_id,
            dataset_id=dataset_id,
            operation_type="upload",
            resource_type="dataset",
            resource_id=dataset_id,
            metadata={
                "dataset_name": dataset_name,
                "record_count": record_count,
                "file_size": file_size,
                "data_format": data_format,
                **metadata
            }
        )
        self._log_event(event)
    
    # Security Event Logging
    
    def log_unauthorized_access_attempt(
        self,
        user: Optional[dict],
        resource_type: str,
        resource_id: str,
        permission_required: str,
        ip_address: str = "unknown",
        user_agent: str = "",
        correlation_id: Optional[str] = None,
        **metadata
    ) -> None:
        """Log unauthorized access attempt."""
        event = TrainingAuditEvent(
            event_type=TrainingEventType.UNAUTHORIZED_ACCESS_ATTEMPT,
            severity=AuditSeverity.ERROR,
            message=f"Unauthorized access attempt to {resource_type} {resource_id}",
            user_id=user.get("user_id") if user else None,
            user_email=user.get("email") if user else None,
            user_roles=user.get("roles", []) if user else [],
            tenant_id=user.tenant_id if user else "unknown",
            ip_address=ip_address,
            user_agent=user_agent,
            correlation_id=correlation_id,
            operation_type="access",
            resource_type=resource_type,
            resource_id=resource_id,
            permission_required=permission_required,
            permission_granted=False,
            success=False,
            security_flags=["unauthorized_access"],
            metadata=metadata
        )
        self._log_event(event)
    
    def log_permission_denied(
        self,
        user: dict,
        resource_type: str,
        resource_id: str,
        permission_required: str,
        ip_address: str = "unknown",
        correlation_id: Optional[str] = None,
        **metadata
    ) -> None:
        """Log permission denied event."""
        event = TrainingAuditEvent(
            event_type=TrainingEventType.PERMISSION_DENIED,
            severity=AuditSeverity.WARNING,
            message=f"Permission denied for {permission_required} on {resource_type} {resource_id}",
            user_id=user.get("user_id"),
            user_email=user.get("email"),
            user_roles=user.get("roles", []),
            tenant_id=user.tenant_id,
            ip_address=ip_address,
            correlation_id=correlation_id,
            operation_type="access",
            resource_type=resource_type,
            resource_id=resource_id,
            permission_required=permission_required,
            permission_granted=False,
            success=False,
            security_flags=["permission_denied"],
            metadata=metadata
        )
        self._log_event(event)
    
    def log_model_integrity_check_failed(
        self,
        user: dict,
        model_id: str,
        model_name: str,
        expected_checksum: str,
        actual_checksum: str,
        correlation_id: Optional[str] = None,
        **metadata
    ) -> None:
        """Log model integrity check failure."""
        event = TrainingAuditEvent(
            event_type=TrainingEventType.MODEL_INTEGRITY_CHECK_FAILED,
            severity=AuditSeverity.CRITICAL,
            message=f"Model integrity check failed for {model_name}",
            user_id=user.get("user_id"),
            user_email=user.get("email"),
            user_roles=user.get("roles", []),
            tenant_id=user.tenant_id,
            correlation_id=correlation_id,
            model_id=model_id,
            operation_type="integrity_check",
            resource_type="model",
            resource_id=model_id,
            success=False,
            error_message="Checksum mismatch detected",
            security_flags=["integrity_violation"],
            metadata={
                "model_name": model_name,
                "expected_checksum": expected_checksum,
                "actual_checksum": actual_checksum,
                **metadata
            }
        )
        self._log_event(event)
    
    # Configuration Change Logging
    
    def log_config_updated(
        self,
        user: dict,
        config_type: str,
        config_changes: Dict[str, Any],
        ip_address: str = "unknown",
        correlation_id: Optional[str] = None,
        **metadata
    ) -> None:
        """Log configuration changes."""
        event = TrainingAuditEvent(
            event_type=TrainingEventType.CONFIG_UPDATED,
            severity=AuditSeverity.INFO,
            message=f"Configuration updated: {config_type}",
            user_id=user.get("user_id"),
            user_email=user.get("email"),
            user_roles=user.get("roles", []),
            tenant_id=user.tenant_id,
            ip_address=ip_address,
            correlation_id=correlation_id,
            operation_type="update",
            resource_type="configuration",
            resource_id=config_type,
            metadata={
                "config_type": config_type,
                "changes": config_changes,
                **metadata
            }
        )
        self._log_event(event)
    
    # Analytics and Reporting
    
    def get_event_counts(self, hours: int = 24) -> Dict[str, int]:
        """Get event counts for the specified time period."""
        return self._event_counts.copy()
    
    def get_security_events(self, hours: int = 24) -> List[TrainingAuditEvent]:
        """Get recent security events."""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        return [
            event for event in self._security_events
            if event.timestamp > cutoff_time
        ]
    
    def get_user_activity_summary(self, user_id: str, hours: int = 24) -> Dict[str, Any]:
        """Get activity summary for a specific user."""
        # This would typically query a database in a production system
        # For now, return a placeholder
        return {
            "user_id": user_id,
            "period_hours": hours,
            "total_events": 0,
            "event_types": {},
            "resources_accessed": [],
            "security_events": 0
        }


# Global training audit logger instance
_training_audit_logger: Optional[TrainingAuditLogger] = None


def get_training_audit_logger() -> TrainingAuditLogger:
    """Get or create global training audit logger instance."""
    global _training_audit_logger
    if _training_audit_logger is None:
        _training_audit_logger = TrainingAuditLogger()
    return _training_audit_logger