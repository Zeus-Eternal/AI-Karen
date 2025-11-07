#!/usr/bin/env python3
"""
Test script to verify all reasoning module imports and integrations.
"""

import sys
from typing import List, Tuple

def test_imports() -> List[Tuple[str, bool, str]]:
    """Test all reasoning module imports."""
    results = []

    # Test 1: Core reasoning module
    try:
        from ai_karen_engine.core import reasoning
        results.append(("Core reasoning module", True, "Success"))
    except Exception as e:
        results.append(("Core reasoning module", False, str(e)))

    # Test 2: Soft Reasoning components
    try:
        from ai_karen_engine.core.reasoning import (
            SoftReasoningEngine,
            RecallConfig,
            WritebackConfig,
            SRHealth,
        )
        results.append(("Soft Reasoning core", True, "Success"))
    except Exception as e:
        results.append(("Soft Reasoning core", False, str(e)))

    # Test 3: Paper-aligned modules (Perturbation)
    try:
        from ai_karen_engine.core.reasoning import (
            EmbeddingPerturber,
            PerturbationStrategy,
            PerturbationConfig,
        )
        results.append(("Perturbation module", True, "Success"))
    except Exception as e:
        results.append(("Perturbation module", False, str(e)))

    # Test 4: Bayesian Optimization
    try:
        from ai_karen_engine.core.reasoning import (
            BayesianOptimizer,
            OptimizationConfig,
            OptimizationResult,
            AcquisitionFunction,
        )
        results.append(("Bayesian Optimizer", True, "Success"))
    except Exception as e:
        results.append(("Bayesian Optimizer", False, str(e)))

    # Test 5: Verifier
    try:
        from ai_karen_engine.core.reasoning import (
            ReasoningVerifier,
            VerifierConfig,
            VerificationResult,
            VerificationCriterion,
        )
        results.append(("Reasoning Verifier", True, "Success"))
    except Exception as e:
        results.append(("Reasoning Verifier", False, str(e)))

    # Test 6: Graph reasoning
    try:
        from ai_karen_engine.core.reasoning import (
            ReasoningGraph,
            CapsuleGraph,
            Node,
            Edge,
        )
        results.append(("Graph reasoning", True, "Success"))
    except Exception as e:
        results.append(("Graph reasoning", False, str(e)))

    # Test 7: Synthesis and ICE
    try:
        from ai_karen_engine.core.reasoning import (
            PremiumICEWrapper,
            KariICEWrapper,
            ICEWritebackPolicy,
            ReasoningTrace,
            RecallStrategy,
            SynthesisMode,
        )
        results.append(("Synthesis and ICE", True, "Success"))
    except Exception as e:
        results.append(("Synthesis and ICE", False, str(e)))

    # Test 8: Sub-engines
    try:
        from ai_karen_engine.core.reasoning import (
            SynthesisSubEngine,
            LangGraphSubEngine,
            DSPySubEngine,
        )
        results.append(("Sub-engines", True, "Success"))
    except Exception as e:
        results.append(("Sub-engines", False, str(e)))

    # Test 9: Self-Refiner
    try:
        from ai_karen_engine.core.reasoning import (
            SelfRefiner,
            RefinementConfig,
            RefinementResult,
            FeedbackPoint,
            RefinementStage,
            create_self_refiner,
        )
        results.append(("Self-Refiner", True, "Success"))
    except Exception as e:
        results.append(("Self-Refiner", False, str(e)))

    # Test 10: Metacognition
    try:
        from ai_karen_engine.core.reasoning import (
            MetacognitiveMonitor,
            MetacognitiveState,
            MetacognitiveConfig,
            CognitiveState,
            ReasoningStrategy,
            PerformanceMetrics,
        )
        results.append(("Metacognition", True, "Success"))
    except Exception as e:
        results.append(("Metacognition", False, str(e)))

    # Test 11: Cognitive Orchestrator
    try:
        from ai_karen_engine.core.reasoning import (
            CognitiveOrchestrator,
            CognitiveConfig,
            CognitiveTask,
            CognitiveResponse,
            CognitiveMode,
            create_cognitive_orchestrator,
        )
        results.append(("Cognitive Orchestrator", True, "Success"))
    except Exception as e:
        results.append(("Cognitive Orchestrator", False, str(e)))

    # Test 12: Retrieval adapters
    try:
        from ai_karen_engine.core.reasoning import (
            SRRetriever,
            SRCompositeRetriever,
            VectorStore,
            Result,
            MilvusClientAdapter,
            LlamaIndexVectorAdapter,
        )
        results.append(("Retrieval adapters", True, "Success"))
    except Exception as e:
        results.append(("Retrieval adapters", False, str(e)))

    # Test 13: Causal reasoning (core)
    try:
        from ai_karen_engine.core.reasoning import (
            CausalReasoningEngine,
            CausalGraph,
            CausalEdge,
            CausalIntervention,
            CounterfactualScenario,
            CausalExplanation,
            CausalRelationType,
            get_causal_engine,
        )
        results.append(("Causal reasoning (core)", True, "Success"))
    except Exception as e:
        results.append(("Causal reasoning (core)", False, str(e)))

    # Test 14: Cognitive Causal Reasoning
    try:
        from ai_karen_engine.core.reasoning import (
            CognitiveCausalReasoner,
            CausalReasoningMode,
            EvidenceQuality,
            CausalHypothesis,
            CausalReasoningState,
            EnhancedCausalExplanation,
            CounterfactualComparison,
            create_cognitive_causal_reasoner,
        )
        results.append(("Cognitive Causal Reasoning", True, "Success"))
    except Exception as e:
        results.append(("Cognitive Causal Reasoning", False, str(e)))

    # Test 15: Direct submodule imports
    try:
        from ai_karen_engine.core.reasoning.soft_reasoning import engine
        from ai_karen_engine.core.reasoning.soft_reasoning import perturbation
        from ai_karen_engine.core.reasoning.soft_reasoning import optimization
        from ai_karen_engine.core.reasoning.soft_reasoning import verifier
        results.append(("Direct soft_reasoning submodule imports", True, "Success"))
    except Exception as e:
        results.append(("Direct soft_reasoning submodule imports", False, str(e)))

    # Test 16: Direct synthesis submodule imports
    try:
        from ai_karen_engine.core.reasoning.synthesis import ice_wrapper
        from ai_karen_engine.core.reasoning.synthesis import self_refine
        from ai_karen_engine.core.reasoning.synthesis import metacognition
        from ai_karen_engine.core.reasoning.synthesis import cognitive_orchestrator
        results.append(("Direct synthesis submodule imports", True, "Success"))
    except Exception as e:
        results.append(("Direct synthesis submodule imports", False, str(e)))

    # Test 17: Direct causal submodule imports
    try:
        from ai_karen_engine.core.reasoning.causal import engine
        from ai_karen_engine.core.reasoning.causal import cognitive_causal
        results.append(("Direct causal submodule imports", True, "Success"))
    except Exception as e:
        results.append(("Direct causal submodule imports", False, str(e)))

    # Test 18: Direct graph submodule imports
    try:
        from ai_karen_engine.core.reasoning.graph import reasoning
        from ai_karen_engine.core.reasoning.graph import capsule
        results.append(("Direct graph submodule imports", True, "Success"))
    except Exception as e:
        results.append(("Direct graph submodule imports", False, str(e)))

    # Test 19: Direct retrieval submodule imports
    try:
        from ai_karen_engine.core.reasoning.retrieval import adapters
        from ai_karen_engine.core.reasoning.retrieval import vector_stores
        results.append(("Direct retrieval submodule imports", True, "Success"))
    except Exception as e:
        results.append(("Direct retrieval submodule imports", False, str(e)))

    return results


def main():
    """Run import tests and display results."""
    print("=" * 80)
    print("AI Karen Reasoning Module Import Verification")
    print("=" * 80)
    print()

    results = test_imports()

    passed = sum(1 for _, success, _ in results if success)
    failed = len(results) - passed

    print(f"Test Results: {passed}/{len(results)} passed\n")

    # Show successful imports
    print("✓ Successful Imports:")
    print("-" * 80)
    for name, success, message in results:
        if success:
            print(f"  ✓ {name}")

    # Show failed imports
    if failed > 0:
        print("\n✗ Failed Imports:")
        print("-" * 80)
        for name, success, message in results:
            if not success:
                print(f"  ✗ {name}")
                print(f"    Error: {message}")

    print("\n" + "=" * 80)

    if failed == 0:
        print("✓ All imports successful!")
        return 0
    else:
        print(f"✗ {failed} import(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
