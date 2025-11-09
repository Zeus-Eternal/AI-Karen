"""
Synthesis and ICE Module

Provides Integrated Cognitive Engine (ICE) wrapper, synthesis capabilities,
and human-like cognitive processing.

Components:
- PremiumICEWrapper / KariICEWrapper: ICE integration with policies
- ICEWritebackPolicy: Writeback policies and configuration
- ReasoningTrace: Trace of reasoning process
- SynthesisSubEngine: Protocol for synthesis sub-engines

Human-Like Cognition (NEW):
- SelfRefiner: Iterative refinement with self-feedback (arXiv:2303.17651)
- MetacognitiveMonitor: Self-monitoring and self-reflection
- CognitiveOrchestrator: Human-like reasoning orchestration
"""

from ai_karen_engine.core.reasoning.synthesis.ice_wrapper import (
    PremiumICEWrapper,
    ICEWritebackPolicy,
    ReasoningTrace,
    RecallStrategy,
    SynthesisMode,
    ICEPerformanceBaseline,
    ICECircuitBreaker,
)
from ai_karen_engine.core.reasoning.synthesis.subengines import (
    SynthesisSubEngine,
    LangGraphSubEngine,
    DSPySubEngine,
)

# Human-Like Cognition modules
from ai_karen_engine.core.reasoning.synthesis.self_refine import (
    SelfRefiner,
    RefinementConfig,
    RefinementResult,
    FeedbackPoint,
    RefinementStage,
    create_self_refiner,
)
from ai_karen_engine.core.reasoning.synthesis.metacognition import (
    MetacognitiveMonitor,
    MetacognitiveState,
    MetacognitiveConfig,
    CognitiveState,
    ReasoningStrategy,
    PerformanceMetrics,
)
from ai_karen_engine.core.reasoning.synthesis.cognitive_orchestrator import (
    CognitiveOrchestrator,
    CognitiveConfig,
    CognitiveTask,
    CognitiveResponse,
    CognitiveMode,
    create_cognitive_orchestrator,
)

# Alias for backward compatibility
KariICEWrapper = PremiumICEWrapper

__all__ = [
    # Core ICE
    "PremiumICEWrapper",
    "KariICEWrapper",
    "ICEWritebackPolicy",
    "ReasoningTrace",
    "RecallStrategy",
    "SynthesisMode",
    "ICEPerformanceBaseline",
    "ICECircuitBreaker",
    "SynthesisSubEngine",
    "LangGraphSubEngine",
    "DSPySubEngine",

    # Human-Like Cognition
    "SelfRefiner",
    "RefinementConfig",
    "RefinementResult",
    "FeedbackPoint",
    "RefinementStage",
    "create_self_refiner",
    "MetacognitiveMonitor",
    "MetacognitiveState",
    "MetacognitiveConfig",
    "CognitiveState",
    "ReasoningStrategy",
    "PerformanceMetrics",
    "CognitiveOrchestrator",
    "CognitiveConfig",
    "CognitiveTask",
    "CognitiveResponse",
    "CognitiveMode",
    "create_cognitive_orchestrator",
]
