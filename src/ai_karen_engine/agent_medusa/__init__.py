"""
AgentMedusa - Multi-Agent Runtime System

AgentMedusa is a multi-agent runtime system that provides coordination,
arbitration, and execution capabilities for AI agents.
"""

from .contracts import (
    RuntimeRequest,
    RuntimeResponse,
    ExecutionAction,
    MedusaRuntimePolicy,
    ArbitrationRequest,
    ArbitrationDecision,
    SubagentContract,
    DeepExecutionPlan,
)
from .coordinator import MedusaCoordinator
from .arbitration import MedusaArbitrator
from .planning import MedusaPlanner
from .execution import ExecutionEngine, ExecutionPolicy
from .telemetry import RuntimeTelemetry
from .adapters import (
    AuthContextAdapter,
    ExtensionRuntimeAdapter,
    MemoryRuntimeAdapter,
    PersistenceAdapter,
)

__version__ = "0.1.0"
__author__ = "AI-Karen Team"

__all__ = [
    # Contracts
    "RuntimeRequest",
    "RuntimeResponse",
    "ExecutionAction",
    "MedusaRuntimePolicy",
    "ArbitrationRequest",
    "ArbitrationDecision",
    "SubagentContract",
    "DeepExecutionPlan",
    # Core Components
    "MedusaCoordinator",
    "MedusaArbitrator",
    "MedusaPlanner",
    # Execution
    "ExecutionEngine",
    "ExecutionPolicy",
    # Telemetry
    "RuntimeTelemetry",
    # Adapters
    "AuthContextAdapter",
    "ExtensionRuntimeAdapter",
    "MemoryRuntimeAdapter",
    "PersistenceAdapter",
]
