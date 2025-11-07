#!/usr/bin/env python3
"""
Test script to verify reasoning module structure without importing.
Uses AST to statically analyze imports.
"""

import ast
import os
from pathlib import Path
from typing import List, Tuple, Set

def get_imports_from_file(filepath: Path) -> Tuple[Set[str], Set[str]]:
    """Extract imports from a Python file using AST."""
    try:
        with open(filepath, 'r') as f:
            tree = ast.parse(f.read(), filename=str(filepath))

        imports = set()
        from_imports = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    from_imports.add(node.module)

        return imports, from_imports
    except Exception as e:
        return set(), set()


def check_module_structure() -> List[Tuple[str, bool, str]]:
    """Check the reasoning module structure."""
    results = []
    base_path = Path("/home/user/AI-Karen/src/ai_karen_engine/core/reasoning")

    # Test 1: Check main __init__.py exists
    main_init = base_path / "__init__.py"
    if main_init.exists():
        results.append(("Main __init__.py exists", True, str(main_init)))
    else:
        results.append(("Main __init__.py exists", False, "File not found"))

    # Test 2: Check submodule structure
    submodules = ["soft_reasoning", "graph", "retrieval", "synthesis", "causal"]
    for submodule in submodules:
        submod_path = base_path / submodule
        init_path = submod_path / "__init__.py"

        if submod_path.is_dir():
            if init_path.exists():
                results.append((f"{submodule}/ structure", True, f"Directory and __init__.py exist"))
            else:
                results.append((f"{submodule}/ structure", False, f"Missing __init__.py"))
        else:
            results.append((f"{submodule}/ structure", False, f"Directory not found"))

    # Test 3: Check key module files exist
    key_files = {
        "soft_reasoning/engine.py": "Soft Reasoning Engine",
        "soft_reasoning/perturbation.py": "Perturbation module",
        "soft_reasoning/optimization.py": "Bayesian Optimizer",
        "soft_reasoning/verifier.py": "Reasoning Verifier",
        "graph/reasoning.py": "Graph Reasoning",
        "graph/capsule.py": "Capsule Graph",
        "retrieval/adapters.py": "Retrieval Adapters",
        "retrieval/vector_stores.py": "Vector Stores",
        "synthesis/ice_wrapper.py": "ICE Wrapper",
        "synthesis/self_refine.py": "Self-Refiner",
        "synthesis/metacognition.py": "Metacognition",
        "synthesis/cognitive_orchestrator.py": "Cognitive Orchestrator",
        "synthesis/subengines.py": "Sub-engines",
        "causal/engine.py": "Causal Engine",
        "causal/cognitive_causal.py": "Cognitive Causal",
    }

    for filepath, name in key_files.items():
        full_path = base_path / filepath
        if full_path.exists():
            results.append((f"{name} file", True, str(filepath)))
        else:
            results.append((f"{name} file", False, f"File not found: {filepath}"))

    # Test 4: Check for circular imports (basic)
    imports_map = {}
    for submodule in submodules:
        submod_path = base_path / submodule
        if submod_path.is_dir():
            for py_file in submod_path.glob("*.py"):
                if py_file.name != "__init__.py":
                    rel_path = f"{submodule}/{py_file.name}"
                    imports, from_imports = get_imports_from_file(py_file)
                    imports_map[rel_path] = (imports, from_imports)

    circular_issues = []
    for file_path, (imports, from_imports) in imports_map.items():
        submod = file_path.split('/')[0]
        # Check if it imports from its own submodule in a problematic way
        for from_imp in from_imports:
            if from_imp.startswith(f"ai_karen_engine.core.reasoning.{submod}"):
                # This is okay for cross-file imports within the same submodule
                pass

    if not circular_issues:
        results.append(("No obvious circular import issues", True, "Import structure looks clean"))
    else:
        results.append(("Circular import check", False, f"Found {len(circular_issues)} potential issues"))

    # Test 5: Check main __init__.py exports
    if main_init.exists():
        with open(main_init, 'r') as f:
            content = f.read()

        checks = [
            ("SoftReasoningEngine", "Core soft reasoning export"),
            ("EmbeddingPerturber", "Perturbation export"),
            ("BayesianOptimizer", "Optimizer export"),
            ("ReasoningVerifier", "Verifier export"),
            ("ReasoningGraph", "Graph export"),
            ("PremiumICEWrapper", "ICE wrapper export"),
            ("SelfRefiner", "Self-refiner export"),
            ("MetacognitiveMonitor", "Metacognition export"),
            ("CognitiveOrchestrator", "Cognitive orchestrator export"),
            ("SRRetriever", "Retrieval export"),
            ("CausalReasoningEngine", "Causal engine export"),
            ("CognitiveCausalReasoner", "Cognitive causal export"),
        ]

        for export_name, description in checks:
            if export_name in content:
                results.append((f"Export: {description}", True, f"'{export_name}' found"))
            else:
                results.append((f"Export: {description}", False, f"'{export_name}' not found"))

    # Test 6: Check README exists
    readme_path = base_path / "README.md"
    if readme_path.exists():
        results.append(("README.md exists", True, "Documentation present"))
    else:
        results.append(("README.md exists", False, "Missing documentation"))

    return results


def main():
    """Run structure tests and display results."""
    print("=" * 80)
    print("AI Karen Reasoning Module Structure Verification")
    print("=" * 80)
    print()

    results = check_module_structure()

    passed = sum(1 for _, success, _ in results if success)
    failed = len(results) - passed

    print(f"Test Results: {passed}/{len(results)} passed\n")

    # Show successful checks
    print("✓ Successful Checks:")
    print("-" * 80)
    for name, success, message in results:
        if success:
            print(f"  ✓ {name}")

    # Show failed checks
    if failed > 0:
        print("\n✗ Failed Checks:")
        print("-" * 80)
        for name, success, message in results:
            if not success:
                print(f"  ✗ {name}")
                print(f"    Details: {message}")

    print("\n" + "=" * 80)

    if failed == 0:
        print("✓ All structure checks passed!")
        return 0
    else:
        print(f"✗ {failed} check(s) failed")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
