"""
Comprehensive Audit Logger for Agent Operations

This module provides comprehensive audit logging for all agent actions,
plan executions, approval workflows, and guardrail violations with
correlation IDs and structured logging.
"""

import asyncio
import logging
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
import os
from pathlib import Path

from ai_karen_engine.agents.planner import Plan, PlanStep
from ai_karen_engine.agents.execution_pipeline import (
    ExecutionContext, 
    ApprovalRequest, 
    GuardrailCheck,
    ExecutionStatus,
    ApprovalStatus
)


class AuditEventType(Enum):
    """Types of audit events."""
    # Plan events
    PLAN_CREATED = "plan.created"
    PLAN_APPROVED = "plan.approved"
    PLAN_REJECTED = "plan.rejected"
    PLAN_STARTED = "plan.started"
    PLAN_COMPLETED = "plan.completed"
    PLAN_FAILED = "plan.failed"
    PLAN_CANCELLED = "plan.cancelled"
    
    # Step events
    STEP_STARTED = "step.started"
    STEP_COMPLETED = "step.completed"
    STEP_FAILED = "step.failed"
    STEP_SKIPPED = "step.skipped"
    
    # Approval events
    APPROVAL_REQUESTED = "approval.requested"
    APPROVAL_GRANTED = "approval.granted"
    APPROVAL_DENIED = "approval.denied"
    APPROVAL_EXPIRED = "approval.expired"
    APPROVAL_AUTO_GRANTED = "approval.auto_granted"
    
    # Guardrail events
    GUARDRAIL_VIOLATION = "guardrail.violation"
    GUARDRAIL_POLICY_APPLIED = "guardrail.policy_applied"
    
    # Rollback events
    ROLLBACK_INITIATED = "rollback.initiated"
    ROLLBACK_COMPLETED = "rollback.completed"
    ROLLBACK_FAILED = "rollback.failed"
    
    # Tool events
    TOOL_EXECUTED = "tool.executed"
    TOOL_FAILED = "tool.failed"
    
    # Security events
    RBAC_VIOLATION = "security.rbac_violation"
    PRIVACY_VIOLATION = "security.privacy_violation"
    CITATION_VIOLATION = "security.citation_violation"
    
    # System events
    CIRCUIT_BREAKER_OPENED = "system.circuit_breaker_opened"
    CIRCUIT_BREAKER_CLOSED = "system.circuit_breaker_closed"
    EXECUTION_LIMIT_REACHED = "system.execution_limit_reached"


class AuditSeverity(Enum):
    """Severity levels for audit events."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AuditEvent:
    """Structured audit event."""
    event_id: str
    event_type: AuditEventType
    timestamp: datetime
    correlation_id: str
    
    # Context
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    plan_id: Optional[str] = None
    step_id: Optional[str] = None
    execution_id: Optional[str] = None
    
    # Event details
    severity: AuditSeverity = AuditSeverity.INFO
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    
    # Performance metrics
    duration_ms: Optional[int] = None
    
    # Security context
    rbac_level: Optional[str] = None
    privacy_level: Optional[str] = None
    
    # Error information
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    stack_trace: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        
        # Convert enums to strings
        data["event_type"] = self.event_type.value
        data["severity"] = self.severity.value
        data["timestamp"] = self.timestamp.isoformat()
        
        # Remove None values
        return {k: v for k, v in data.items() if v is not None}
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


class AuditLogger:
    """
    Comprehensive audit logger for agent operations with structured logging,
    correlation tracking, and multiple output formats.
    """
    
    def __init__(self, log_directory: str = "logs/audit"):
        self.log_directory = Path(log_directory)
        self.log_directory.mkdir(parents=True, exist_ok=True)
        
        self.logger = logging.getLogger(__name__)
        
        # Configuration
        self.enable_file_logging = True
        self.enable_structured_logging = True
        self.enable_metrics_collection = True
        self.log_retention_days = 90
        
        # In-memory storage for recent events (for debugging and metrics)
        self.recent_events: List[AuditEvent] = []
        self.max_recent_events = 1000
        
        # Metrics
        self.audit_metrics = {
            "events_logged": 0,
            "events_by_type": {},
            "events_by_severity": {},
            "events_by_user": {},
            "correlation_chains": {}
        }
        
        # Initialize file handlers
        self._initialize_file_handlers()
    
    def _initialize_file_handlers(self):
        """Initialize file logging handlers."""
        if not self.enable_file_logging:
            return
        
        try:
            # Create daily log file
            today = datetime.now().strftime("%Y-%m-%d")
            log_file = self.log_directory / f"audit_{today}.jsonl"
            
            # Configure file handler
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.INFO)
            
            # JSON formatter for structured logging
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(formatter)
            
            # Add to logger (prevent duplicates)
            audit_file_logger = logging.getLogger("audit_file")
            if not audit_file_logger.handlers:
                audit_file_logger.addHandler(file_handler)
                audit_file_logger.setLevel(logging.INFO)
                audit_file_logger.propagate = False
            
        except Exception as e:
            self.logger.error(f"Failed to initialize file handlers: {e}")
    
    async def log_event(
        self,
        event_type: AuditEventType,
        correlation_id: str,
        message: str = "",
        severity: AuditSeverity = AuditSeverity.INFO,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        plan_id: Optional[str] = None,
        step_id: Optional[str] = None,
        execution_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        duration_ms: Optional[int] = None,
        rbac_level: Optional[str] = None,
        privacy_level: Optional[str] = None,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None,
        stack_trace: Optional[str] = None
    ) -> str:
        """
        Log an audit event with full context.
        
        Args:
            event_type: Type of event
            correlation_id: Correlation ID for tracking related events
            message: Human-readable message
            severity: Event severity level
            user_id: User identifier
            session_id: Session identifier
            plan_id: Plan identifier
            step_id: Step identifier
            execution_id: Execution identifier
            details: Additional event details
            duration_ms: Operation duration in milliseconds
            rbac_level: RBAC level context
            privacy_level: Privacy level context
            error_code: Error code if applicable
            error_message: Error message if applicable
            stack_trace: Stack trace if applicable
            
        Returns:
            Event ID
        """
        event_id = str(uuid.uuid4())
        
        try:
            # Create audit event
            event = AuditEvent(
                event_id=event_id,
                event_type=event_type,
                timestamp=datetime.utcnow(),
                correlation_id=correlation_id,
                user_id=user_id,
                session_id=session_id,
                plan_id=plan_id,
                step_id=step_id,
                execution_id=execution_id,
                severity=severity,
                message=message,
                details=details or {},
                duration_ms=duration_ms,
                rbac_level=rbac_level,
                privacy_level=privacy_level,
                error_code=error_code,
                error_message=error_message,
                stack_trace=stack_trace
            )
            
            # Store in recent events
            self.recent_events.append(event)
            if len(self.recent_events) > self.max_recent_events:
                self.recent_events = self.recent_events[-self.max_recent_events:]
            
            # Update metrics
            await self._update_metrics(event)
            
            # Log to file
            if self.enable_file_logging:
                await self._log_to_file(event)
            
            # Log to standard logger
            log_level = self._severity_to_log_level(severity)
            self.logger.log(
                log_level,
                f"[{event_type.value}] {message}",
                extra={
                    "event_id": event_id,
                    "correlation_id": correlation_id,
                    "user_id": user_id,
                    "plan_id": plan_id,
                    "execution_id": execution_id
                }
            )
            
            return event_id
            
        except Exception as e:
            self.logger.error(f"Failed to log audit event: {e}")
            return event_id
    
    async def _update_metrics(self, event: AuditEvent):
        """Update audit metrics."""
        if not self.enable_metrics_collection:
            return
        
        try:
            self.audit_metrics["events_logged"] += 1
            
            # By type
            event_type = event.event_type.value
            self.audit_metrics["events_by_type"][event_type] = (
                self.audit_metrics["events_by_type"].get(event_type, 0) + 1
            )
            
            # By severity
            severity = event.severity.value
            self.audit_metrics["events_by_severity"][severity] = (
                self.audit_metrics["events_by_severity"].get(severity, 0) + 1
            )
            
            # By user
            if event.user_id:
                self.audit_metrics["events_by_user"][event.user_id] = (
                    self.audit_metrics["events_by_user"].get(event.user_id, 0) + 1
                )
            
            # Correlation chains
            if event.correlation_id not in self.audit_metrics["correlation_chains"]:
                self.audit_metrics["correlation_chains"][event.correlation_id] = []
            self.audit_metrics["correlation_chains"][event.correlation_id].append(event.event_id)
            
        except Exception as e:
            self.logger.error(f"Failed to update audit metrics: {e}")
    
    async def _log_to_file(self, event: AuditEvent):
        """Log event to file in JSON Lines format."""
        if not self.enable_file_logging:
            return
        
        try:
            # Get today's log file
            today = datetime.now().strftime("%Y-%m-%d")
            log_file = self.log_directory / f"audit_{today}.jsonl"
            
            # Append event as JSON line
            with open(log_file, 'a') as f:
                f.write(event.to_json() + '\n')
                
        except Exception as e:
            self.logger.error(f"Failed to write to audit log file: {e}")
    
    def _severity_to_log_level(self, severity: AuditSeverity) -> int:
        """Convert audit severity to logging level."""
        mapping = {
            AuditSeverity.DEBUG: logging.DEBUG,
            AuditSeverity.INFO: logging.INFO,
            AuditSeverity.WARNING: logging.WARNING,
            AuditSeverity.ERROR: logging.ERROR,
            AuditSeverity.CRITICAL: logging.CRITICAL
        }
        return mapping.get(severity, logging.INFO)
    
    # Convenience methods for common events
    
    async def log_plan_created(
        self,
        plan: Plan,
        correlation_id: str,
        user_id: str,
        session_id: str
    ) -> str:
        """Log plan creation event."""
        return await self.log_event(
            event_type=AuditEventType.PLAN_CREATED,
            correlation_id=correlation_id,
            message=f"Plan created: {plan.name}",
            user_id=user_id,
            session_id=session_id,
            plan_id=plan.plan_id,
            details={
                "plan_name": plan.name,
                "step_count": len(plan.steps),
                "requires_approval": plan.requires_approval,
                "confidence_score": plan.confidence_score.value if plan.confidence_score else None,
                "estimated_time": str(plan.total_estimated_time) if plan.total_estimated_time else None
            }
        )
    
    async def log_plan_execution_started(
        self,
        context: ExecutionContext
    ) -> str:
        """Log plan execution start."""
        return await self.log_event(
            event_type=AuditEventType.PLAN_STARTED,
            correlation_id=context.correlation_id,
            message=f"Plan execution started: {context.plan.name}",
            user_id=context.user_id,
            session_id=context.session_id,
            plan_id=context.plan.plan_id,
            execution_id=context.execution_id,
            rbac_level=context.user_rbac_level.value,
            privacy_level=context.privacy_clearance.value,
            details={
                "execution_mode": context.execution_mode.value,
                "timeout_seconds": context.timeout_seconds,
                "enable_rollback": context.enable_rollback,
                "step_count": len(context.plan.steps)
            }
        )
    
    async def log_plan_execution_completed(
        self,
        context: ExecutionContext
    ) -> str:
        """Log plan execution completion."""
        return await self.log_event(
            event_type=AuditEventType.PLAN_COMPLETED,
            correlation_id=context.correlation_id,
            message=f"Plan execution completed: {context.plan.name}",
            user_id=context.user_id,
            session_id=context.session_id,
            plan_id=context.plan.plan_id,
            execution_id=context.execution_id,
            duration_ms=int(context.total_execution_time.total_seconds() * 1000) if context.total_execution_time else None,
            details={
                "status": context.status.value,
                "completed_steps": len(context.completed_steps),
                "failed_steps": len(context.failed_steps),
                "total_steps": len(context.plan.steps),
                "rollback_data_available": len(context.rollback_data) > 0
            }
        )
    
    async def log_step_execution(
        self,
        step: PlanStep,
        context: ExecutionContext,
        success: bool,
        duration_ms: Optional[int] = None,
        error_message: Optional[str] = None
    ) -> str:
        """Log step execution."""
        event_type = AuditEventType.STEP_COMPLETED if success else AuditEventType.STEP_FAILED
        
        return await self.log_event(
            event_type=event_type,
            correlation_id=context.correlation_id,
            message=f"Step {'completed' if success else 'failed'}: {step.name}",
            severity=AuditSeverity.INFO if success else AuditSeverity.ERROR,
            user_id=context.user_id,
            session_id=context.session_id,
            plan_id=context.plan.plan_id,
            step_id=step.step_id,
            execution_id=context.execution_id,
            duration_ms=duration_ms,
            error_message=error_message,
            details={
                "tool_name": step.tool_name,
                "execution_mode": step.execution_mode.value,
                "risk_level": step.risk_assessment.level.name if step.risk_assessment else None,
                "citation_count": len(step.required_citations),
                "can_rollback": step.can_rollback
            }
        )
    
    async def log_approval_request(
        self,
        request: ApprovalRequest,
        correlation_id: str
    ) -> str:
        """Log approval request creation."""
        return await self.log_event(
            event_type=AuditEventType.APPROVAL_REQUESTED,
            correlation_id=correlation_id,
            message=f"Approval requested: {request.operation_description}",
            user_id=request.user_id,
            plan_id=request.plan_id,
            step_id=request.step_id,
            details={
                "request_id": request.request_id,
                "required_approver_level": request.required_approver_level.value,
                "risk_assessment": request.risk_assessment,
                "expires_at": request.expires_at.isoformat() if request.expires_at else None
            }
        )
    
    async def log_approval_decision(
        self,
        request: ApprovalRequest,
        correlation_id: str,
        approved: bool,
        approver_id: Optional[str] = None,
        auto_approved: bool = False
    ) -> str:
        """Log approval decision."""
        if approved:
            event_type = AuditEventType.APPROVAL_AUTO_GRANTED if auto_approved else AuditEventType.APPROVAL_GRANTED
            message = f"Approval {'auto-' if auto_approved else ''}granted: {request.operation_description}"
        else:
            event_type = AuditEventType.APPROVAL_DENIED
            message = f"Approval denied: {request.operation_description}"
        
        return await self.log_event(
            event_type=event_type,
            correlation_id=correlation_id,
            message=message,
            user_id=request.user_id,
            plan_id=request.plan_id,
            step_id=request.step_id,
            details={
                "request_id": request.request_id,
                "approver_id": approver_id,
                "auto_approved": auto_approved,
                "rejection_reason": request.rejection_reason,
                "decision_time": datetime.utcnow().isoformat()
            }
        )
    
    async def log_guardrail_violation(
        self,
        check: GuardrailCheck,
        context: ExecutionContext,
        step: PlanStep
    ) -> str:
        """Log guardrail violation."""
        return await self.log_event(
            event_type=AuditEventType.GUARDRAIL_VIOLATION,
            correlation_id=context.correlation_id,
            message=f"Guardrail violation: {check.message}",
            severity=AuditSeverity.WARNING if check.severity == "warning" else AuditSeverity.ERROR,
            user_id=context.user_id,
            session_id=context.session_id,
            plan_id=context.plan.plan_id,
            step_id=step.step_id,
            execution_id=context.execution_id,
            details={
                "violation_type": check.violation_type.value if check.violation_type else None,
                "severity": check.severity,
                "suggested_action": check.suggested_action,
                "tool_name": step.tool_name,
                "check_details": check.to_dict()
            }
        )
    
    async def log_rollback_operation(
        self,
        execution_id: str,
        correlation_id: str,
        success: bool,
        steps_rolled_back: int,
        error_message: Optional[str] = None
    ) -> str:
        """Log rollback operation."""
        event_type = AuditEventType.ROLLBACK_COMPLETED if success else AuditEventType.ROLLBACK_FAILED
        
        return await self.log_event(
            event_type=event_type,
            correlation_id=correlation_id,
            message=f"Rollback {'completed' if success else 'failed'}: {steps_rolled_back} steps",
            severity=AuditSeverity.INFO if success else AuditSeverity.ERROR,
            execution_id=execution_id,
            error_message=error_message,
            details={
                "steps_rolled_back": steps_rolled_back,
                "rollback_success": success
            }
        )
    
    # Query and analysis methods
    
    def get_events_by_correlation_id(self, correlation_id: str) -> List[AuditEvent]:
        """Get all events for a correlation ID."""
        return [
            event for event in self.recent_events
            if event.correlation_id == correlation_id
        ]
    
    def get_events_by_user(self, user_id: str, limit: int = 100) -> List[AuditEvent]:
        """Get recent events for a user."""
        user_events = [
            event for event in self.recent_events
            if event.user_id == user_id
        ]
        return sorted(user_events, key=lambda x: x.timestamp, reverse=True)[:limit]
    
    def get_events_by_plan(self, plan_id: str) -> List[AuditEvent]:
        """Get all events for a plan."""
        return [
            event for event in self.recent_events
            if event.plan_id == plan_id
        ]
    
    def get_security_events(self, hours: int = 24) -> List[AuditEvent]:
        """Get security-related events from the last N hours."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        security_event_types = {
            AuditEventType.RBAC_VIOLATION,
            AuditEventType.PRIVACY_VIOLATION,
            AuditEventType.CITATION_VIOLATION,
            AuditEventType.GUARDRAIL_VIOLATION
        }
        
        return [
            event for event in self.recent_events
            if (event.timestamp >= cutoff_time and 
                event.event_type in security_event_types)
        ]
    
    def get_audit_metrics(self) -> Dict[str, Any]:
        """Get comprehensive audit metrics."""
        return {
            "metrics": self.audit_metrics.copy(),
            "recent_events_count": len(self.recent_events),
            "log_directory": str(self.log_directory),
            "configuration": {
                "file_logging_enabled": self.enable_file_logging,
                "structured_logging_enabled": self.enable_structured_logging,
                "metrics_collection_enabled": self.enable_metrics_collection,
                "retention_days": self.log_retention_days
            }
        }
    
    async def cleanup_old_logs(self):
        """Clean up old log files based on retention policy."""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.log_retention_days)
            
            for log_file in self.log_directory.glob("audit_*.jsonl"):
                try:
                    # Extract date from filename
                    date_str = log_file.stem.replace("audit_", "")
                    file_date = datetime.strptime(date_str, "%Y-%m-%d")
                    
                    if file_date < cutoff_date:
                        log_file.unlink()
                        self.logger.info(f"Deleted old audit log: {log_file}")
                
                except (ValueError, OSError) as e:
                    self.logger.warning(f"Failed to process log file {log_file}: {e}")
            
        except Exception as e:
            self.logger.error(f"Log cleanup failed: {e}")


# Global audit logger instance
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Get global audit logger instance."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger


async def initialize_audit_logging(log_directory: str = "logs/audit") -> AuditLogger:
    """Initialize audit logging system."""
    global _audit_logger
    _audit_logger = AuditLogger(log_directory)
    return _audit_logger