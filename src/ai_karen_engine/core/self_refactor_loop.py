"""Utilities to run the SelfRefactorEngine in a single cycle."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from ai_karen_engine.self_refactor import SelfRefactorEngine


def run_self_refactor_cycle(
    repo_root: Path,
    llm: Optional[Any] = None,
    nanda: Optional[Any] = None,
) -> Optional[dict]:
    """Execute one self-healing cycle and return the patch report."""
    engine = SelfRefactorEngine(repo_root=repo_root, llm=llm, nanda=nanda)
    issues = engine.static_analysis()
    if not issues:
        return None
    patches = engine.propose_patches(issues)
    report = engine.test_patches(patches)
    engine.reinforce(report)
    return report
