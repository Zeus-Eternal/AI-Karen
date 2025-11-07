"""
Reasoning utilities and graph support (CORTEX v2)
Enhanced with human-level cognitive capabilities
"""

# Core reasoning foundation
from ai_karen_engine.core.reasoning.graph import ReasoningGraph
from ai_karen_engine.core.reasoning.graph_core import CapsuleGraph
from ai_karen_engine.core.reasoning.soft_reasoning_engine import SoftReasoningEngine
from ai_karen_engine.core.reasoning.ice_integration import (
    ICEWritebackPolicy,
    ReasoningTrace,
    KariICEWrapper,
)

# Advanced causal reasoning
from ai_karen_engine.core.reasoning.causal_reasoning import (
    CausalReasoningEngine,
    CausalGraph,
    CausalEdge,
    CausalIntervention,
    CounterfactualScenario,
    CausalExplanation,
    CausalRelationType,
    get_causal_engine,
)

__all__ = [
    # Core foundation
    "ReasoningGraph",
    "SoftReasoningEngine",
    "KariICEWrapper",
    "ICEWritebackPolicy",
    "ReasoningTrace",
    "CapsuleGraph",

    # Advanced causal reasoning
    "CausalReasoningEngine",
    "CausalGraph",
    "CausalEdge",
    "CausalIntervention",
    "CounterfactualScenario",
    "CausalExplanation",
    "CausalRelationType",
    "get_causal_engine",
]
