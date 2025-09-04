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
except ImportError as e:
    # Model orchestrator audit not available (missing dependencies)
    _MODEL_ORCHESTRATOR_AVAILABLE = False
    
    # Create dummy classes for compatibility
    class ModelOrchestratorAuditor:
        def __init__(self, *args, **kwargs):
            raise ImportError(f"Model orchestrator audit not available: {e}")
    
    class AuditEventType:
        pass
    
    class ModelAuditEvent:
        pass
    
    def get_model_orchestrator_auditor():
        raise ImportError(f"Model orchestrator audit not available: {e}")

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