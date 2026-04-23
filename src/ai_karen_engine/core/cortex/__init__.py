from __future__ import annotations

"""CORTEX package exports.

Keep this module side-effect light. Importing contracts should not force the
dispatch layer, RBAC checks, or unrelated filesystem-backed services to
initialize at import time.
"""

from importlib import import_module

from ai_karen_engine.core.cortex.contracts import (
    CorrelationIdFactory,
    CortexOutput,
    ExecutionMode,
    IntentEngine,
    IntentSignal,
    KROOrchestrator,
    KireEngine,
    KireSignal,
    LangGraphRuntime,
    OrchestrationInput,
    OrchestrationResult,
    PredictorEngine,
    PredictorSignal,
    ReasoningDepth,
    ReasoningRequest,
    ReasoningResult,
    RbacValidator,
    RouteFamily,
    RoutingDecision,
    RoutingEngine,
    RuntimeRequest,
    UserContext,
)

_DISPATCH_EXPORTS = {
    "build_orchestration_input",
    "build_reasoning_request",
    "dispatch",
    "evaluate_cortex",
    "CortexDispatchError",
}


def __getattr__(name: str):
    if name in _DISPATCH_EXPORTS:
        dispatch_module = import_module("ai_karen_engine.core.cortex.dispatch")
        return getattr(dispatch_module, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "CorrelationIdFactory",
    "CortexDispatchError",
    "CortexOutput",
    "ExecutionMode",
    "IntentEngine",
    "IntentSignal",
    "KROOrchestrator",
    "KireEngine",
    "KireSignal",
    "LangGraphRuntime",
    "OrchestrationInput",
    "OrchestrationResult",
    "PredictorEngine",
    "PredictorSignal",
    "ReasoningDepth",
    "ReasoningRequest",
    "ReasoningResult",
    "RbacValidator",
    "RouteFamily",
    "RoutingDecision",
    "RoutingEngine",
    "RuntimeRequest",
    "UserContext",
    "build_orchestration_input",
    "build_reasoning_request",
    "dispatch",
    "evaluate_cortex",
]
