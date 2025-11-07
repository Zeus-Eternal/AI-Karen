"""
Reasoning Module - CORTEX v2 with Soft Reasoning

Enhanced reasoning capabilities with human-level cognitive functions.

Organization:
- soft_reasoning/: Core Soft Reasoning implementation (paper-aligned)
- graph/: Graph-based reasoning structures
- retrieval/: Vector store and retrieval adapters
- synthesis/: ICE wrapper and synthesis capabilities
- causal/: Causal reasoning and inference

This module implements the Soft Reasoning approach from the research paper:
"Soft Reasoning: Navigating Solution Spaces in Large Language Models
through Controlled Embedding Exploration" (OpenReview ID: 4gWE7CMOlH)
"""

# Core Soft Reasoning (NEW: Paper-aligned implementation)
from ai_karen_engine.core.reasoning.soft_reasoning import (
    SoftReasoningEngine,
    RecallConfig,
    WritebackConfig,
    SRHealth,
    EmbeddingPerturber,
    PerturbationStrategy,
    PerturbationConfig,
    BayesianOptimizer,
    OptimizationConfig,
    OptimizationResult,
    AcquisitionFunction,
    ReasoningVerifier,
    VerifierConfig,
    VerificationResult,
    VerificationCriterion,
)

# Graph-based reasoning
from ai_karen_engine.core.reasoning.graph import (
    ReasoningGraph,
    CapsuleGraph,
    Node,
    Edge,
)

# Synthesis and ICE integration
from ai_karen_engine.core.reasoning.synthesis import (
    PremiumICEWrapper,
    KariICEWrapper,
    ICEWritebackPolicy,
    ReasoningTrace,
    RecallStrategy,
    SynthesisMode,
    ICEPerformanceBaseline,
    ICECircuitBreaker,
    SynthesisSubEngine,
    LangGraphSubEngine,
    DSPySubEngine,
)

# Retrieval adapters
from ai_karen_engine.core.reasoning.retrieval import (
    SRRetriever,
    SRCompositeRetriever,
    VectorStore,
    Result,
    MilvusClientAdapter,
    LlamaIndexVectorAdapter,
)

# Causal reasoning
from ai_karen_engine.core.reasoning.causal import (
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
    # Core Soft Reasoning
    "SoftReasoningEngine",
    "RecallConfig",
    "WritebackConfig",
    "SRHealth",

    # NEW: Paper-aligned modules
    "EmbeddingPerturber",
    "PerturbationStrategy",
    "PerturbationConfig",
    "BayesianOptimizer",
    "OptimizationConfig",
    "OptimizationResult",
    "AcquisitionFunction",
    "ReasoningVerifier",
    "VerifierConfig",
    "VerificationResult",
    "VerificationCriterion",

    # Graph reasoning
    "ReasoningGraph",
    "CapsuleGraph",
    "Node",
    "Edge",

    # Synthesis & ICE
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

    # Retrieval
    "SRRetriever",
    "SRCompositeRetriever",
    "VectorStore",
    "Result",
    "MilvusClientAdapter",
    "LlamaIndexVectorAdapter",

    # Causal reasoning
    "CausalReasoningEngine",
    "CausalGraph",
    "CausalEdge",
    "CausalIntervention",
    "CounterfactualScenario",
    "CausalExplanation",
    "CausalRelationType",
    "get_causal_engine",
]
