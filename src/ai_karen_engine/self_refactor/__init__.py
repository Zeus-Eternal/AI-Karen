"""Expose the self-refactoring engine within the core namespace."""

from src.self_refactor import SelfRefactorEngine, PatchReport, SREScheduler

__all__ = ["SelfRefactorEngine", "PatchReport", "SREScheduler"]
