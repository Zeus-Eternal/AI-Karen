"""
Agent system for Kari's copilot integration.

This package implements the agent planning and orchestration system with
human-like cognitive architecture, soft reasoning, and comprehensive
execution pipelines with guardrails.
"""

from .planner import (
    AgentPlanner,
    SoftReasoningEngine,
    Plan,
    PlanStep,
    CognitionTrail,
    ConfidenceScore,
    RiskAssessment,
    EmotionalContext,
    ConfidenceLevel,
    RiskLevel,
    ReasoningType
)

from .execution_pipeline import (
    ExecutionPipeline,
    ExecutionContext,
    GuardrailEngine,
    ApprovalWorkflow,
    ApprovalRequest,
    GuardrailCheck,
    ExecutionStatus,
    ApprovalStatus,
    GuardrailViolation,
    CircuitBreaker
)

from .audit_logger import (
    AuditLogger,
    AuditEvent,
    AuditEventType,
    AuditSeverity,
    get_audit_logger,
    initialize_audit_logging
)

__all__ = [
    # Planner components
    "AgentPlanner",
    "SoftReasoningEngine", 
    "Plan",
    "PlanStep",
    "CognitionTrail",
    "ConfidenceScore",
    "RiskAssessment",
    "EmotionalContext",
    "ConfidenceLevel",
    "RiskLevel",
    "ReasoningType",
    
    # Execution pipeline components
    "ExecutionPipeline",
    "ExecutionContext",
    "GuardrailEngine",
    "ApprovalWorkflow",
    "ApprovalRequest",
    "GuardrailCheck",
    "ExecutionStatus",
    "ApprovalStatus",
    "GuardrailViolation",
    "CircuitBreaker",
    
    # Audit logging components
    "AuditLogger",
    "AuditEvent",
    "AuditEventType",
    "AuditSeverity",
    "get_audit_logger",
    "initialize_audit_logging"
]