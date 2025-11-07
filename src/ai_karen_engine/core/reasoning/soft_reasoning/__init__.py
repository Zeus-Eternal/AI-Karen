"""
Soft Reasoning Module

Implements the core Soft Reasoning approach from the research paper:
"Soft Reasoning: Navigating Solution Spaces in Large Language Models
through Controlled Embedding Exploration"

Key components:
- SoftReasoningEngine: Main engine for retrieval and reasoning
- EmbeddingPerturber: Controlled perturbation of embeddings
- BayesianOptimizer: Bayesian optimization for embedding refinement
- ReasoningVerifier: Verifier-guided objectives for quality assessment
"""

from ai_karen_engine.core.reasoning.soft_reasoning.engine import (
    SoftReasoningEngine,
    RecallConfig,
    WritebackConfig,
    SRHealth,
)
from ai_karen_engine.core.reasoning.soft_reasoning.perturbation import (
    EmbeddingPerturber,
    PerturbationStrategy,
    PerturbationConfig,
)
from ai_karen_engine.core.reasoning.soft_reasoning.optimization import (
    BayesianOptimizer,
    OptimizationConfig,
    OptimizationResult,
    AcquisitionFunction,
    optimize_embedding_batch,
)
from ai_karen_engine.core.reasoning.soft_reasoning.verifier import (
    ReasoningVerifier,
    VerifierConfig,
    VerificationResult,
    VerificationCriterion,
)

__all__ = [
    # Core engine
    "SoftReasoningEngine",
    "RecallConfig",
    "WritebackConfig",
    "SRHealth",
    # Perturbation
    "EmbeddingPerturber",
    "PerturbationStrategy",
    "PerturbationConfig",
    # Optimization
    "BayesianOptimizer",
    "OptimizationConfig",
    "OptimizationResult",
    "AcquisitionFunction",
    "optimize_embedding_batch",
    # Verification
    "ReasoningVerifier",
    "VerifierConfig",
    "VerificationResult",
    "VerificationCriterion",
]
