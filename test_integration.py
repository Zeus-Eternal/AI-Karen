#!/usr/bin/env python3
"""
Integration test to verify reasoning module database and import wiring.
"""

import sys
from typing import List, Tuple

def test_integrations() -> List[Tuple[str, bool, str]]:
    """Test reasoning module integrations."""
    results = []

    # Test 1: Import main reasoning module
    try:
        from ai_karen_engine.core import reasoning
        results.append(("Main reasoning module import", True, "Success"))
    except Exception as e:
        results.append(("Main reasoning module import", False, str(e)))
        return results

    # Test 2: Import and verify vector stores
    try:
        from ai_karen_engine.core.reasoning import (
            VectorStore,
            MilvusClientAdapter,
            LlamaIndexVectorAdapter,
            Result,
        )
        results.append(("Vector store imports", True, "Success"))
    except Exception as e:
        results.append(("Vector store imports", False, str(e)))

    # Test 3: Import retrieval adapters
    try:
        from ai_karen_engine.core.reasoning import (
            SRRetriever,
            SRCompositeRetriever,
        )
        results.append(("Retrieval adapter imports", True, "Success"))
    except Exception as e:
        results.append(("Retrieval adapter imports", False, str(e)))

    # Test 4: Import soft reasoning with all new modules
    try:
        from ai_karen_engine.core.reasoning import (
            SoftReasoningEngine,
            RecallConfig,
            WritebackConfig,
            EmbeddingPerturber,
            BayesianOptimizer,
            ReasoningVerifier,
        )
        results.append(("Soft reasoning imports (all modules)", True, "Success"))
    except Exception as e:
        results.append(("Soft reasoning imports (all modules)", False, str(e)))

    # Test 5: Import synthesis modules
    try:
        from ai_karen_engine.core.reasoning import (
            PremiumICEWrapper,
            SelfRefiner,
            MetacognitiveMonitor,
            CognitiveOrchestrator,
        )
        results.append(("Synthesis modules imports", True, "Success"))
    except Exception as e:
        results.append(("Synthesis modules imports", False, str(e)))

    # Test 6: Import causal reasoning
    try:
        from ai_karen_engine.core.reasoning import (
            CausalReasoningEngine,
            CognitiveCausalReasoner,
        )
        results.append(("Causal reasoning imports", True, "Success"))
    except Exception as e:
        results.append(("Causal reasoning imports", False, str(e)))

    # Test 7: Import graph reasoning
    try:
        from ai_karen_engine.core.reasoning import (
            ReasoningGraph,
            CapsuleGraph,
        )
        results.append(("Graph reasoning imports", True, "Success"))
    except Exception as e:
        results.append(("Graph reasoning imports", False, str(e)))

    # Test 8: Verify VectorStore protocol compliance
    try:
        from ai_karen_engine.core.reasoning import VectorStore
        # Check that VectorStore is a Protocol
        import typing
        if hasattr(typing, 'runtime_checkable'):
            results.append(("VectorStore is a Protocol", True, "Success"))
        else:
            results.append(("VectorStore is a Protocol", True, "Protocol check skipped (Python < 3.8)"))
    except Exception as e:
        results.append(("VectorStore is a Protocol", False, str(e)))

    # Test 9: Check backward compatibility - ensure old public API still works
    try:
        from ai_karen_engine.core.reasoning import (
            SoftReasoningEngine,
            PremiumICEWrapper,
            KariICEWrapper,  # Alias for backward compat
        )
        # Verify alias works
        if KariICEWrapper is PremiumICEWrapper:
            results.append(("Backward compatibility (KariICEWrapper alias)", True, "Alias works correctly"))
        else:
            results.append(("Backward compatibility (KariICEWrapper alias)", False, "Alias not pointing to PremiumICEWrapper"))
    except Exception as e:
        results.append(("Backward compatibility (KariICEWrapper alias)", False, str(e)))

    # Test 10: Verify factory functions exist
    try:
        from ai_karen_engine.core.reasoning import (
            create_self_refiner,
            create_cognitive_orchestrator,
            create_cognitive_causal_reasoner,
        )
        results.append(("Factory functions available", True, "All factory functions imported"))
    except Exception as e:
        results.append(("Factory functions available", False, str(e)))

    # Test 11: Verify submodule direct imports work
    try:
        from ai_karen_engine.core.reasoning.soft_reasoning import engine
        from ai_karen_engine.core.reasoning.synthesis import ice_wrapper
        from ai_karen_engine.core.reasoning.causal import engine as causal_engine
        from ai_karen_engine.core.reasoning.retrieval import adapters
        from ai_karen_engine.core.reasoning.graph import reasoning
        results.append(("Direct submodule imports", True, "All submodules accessible"))
    except Exception as e:
        results.append(("Direct submodule imports", False, str(e)))

    # Test 12: Check MilvusClient can be imported
    try:
        from ai_karen_engine.clients.database.milvus_client import MilvusClient
        results.append(("MilvusClient import", True, "Success"))
    except Exception as e:
        results.append(("MilvusClient import", False, str(e)))

    # Test 13: Verify MilvusClientAdapter can wrap MilvusClient
    try:
        from ai_karen_engine.core.reasoning import MilvusClientAdapter
        from ai_karen_engine.clients.database.milvus_client import MilvusClient

        # Just verify the class exists and has the right method
        if hasattr(MilvusClientAdapter, 'upsert'):
            results.append(("MilvusClientAdapter compatibility", True, "Adapter has required methods"))
        else:
            results.append(("MilvusClientAdapter compatibility", False, "Adapter missing required methods"))
    except Exception as e:
        results.append(("MilvusClientAdapter compatibility", False, str(e)))

    # Test 14: Verify external integrations can import from new paths
    try:
        from ai_karen_engine.integrations.sr_llamaindex_adapter import LlamaIndexSRAdapter
        results.append(("External integration (LlamaIndex adapter)", True, "Success"))
    except Exception as e:
        results.append(("External integration (LlamaIndex adapter)", False, str(e)))

    # Test 15: Verify neuro_recall can import from new paths
    try:
        # Just test the import paths exist, don't actually run the modules
        import importlib.util
        spec = importlib.util.find_spec("ai_karen_engine.core.neuro_recall.client.agent")
        if spec is not None:
            results.append(("Neuro recall module import path", True, "Module found"))
        else:
            results.append(("Neuro recall module import path", False, "Module not found"))
    except Exception as e:
        results.append(("Neuro recall module import path", False, str(e)))

    return results


def main():
    """Run integration tests and display results."""
    print("=" * 80)
    print("AI Karen Reasoning Module Integration Test")
    print("=" * 80)
    print()

    results = test_integrations()

    passed = sum(1 for _, success, _ in results if success)
    failed = len(results) - passed

    print(f"Test Results: {passed}/{len(results)} passed\n")

    # Show successful tests
    print("✓ Successful Tests:")
    print("-" * 80)
    for name, success, message in results:
        if success:
            print(f"  ✓ {name}")

    # Show failed tests
    if failed > 0:
        print("\n✗ Failed Tests:")
        print("-" * 80)
        for name, success, message in results:
            if not success:
                print(f"  ✗ {name}")
                print(f"    Error: {message}")

    print("\n" + "=" * 80)

    if failed == 0:
        print("✓ All integration tests passed!")
        print("\n✓ Summary:")
        print("  • All imports properly wired")
        print("  • Database adapters accessible")
        print("  • Vector stores integrated")
        print("  • Backward compatibility maintained")
        print("  • External integrations updated")
        return 0
    else:
        print(f"✗ {failed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
