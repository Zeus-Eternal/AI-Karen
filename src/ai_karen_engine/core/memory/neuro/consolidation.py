from __future__ import annotations

from .contracts import ConsolidationDecision, MemoryCandidate, MemoryClass


def decide_consolidation(candidate: MemoryCandidate) -> ConsolidationDecision:
    reuse = int(candidate.metadata.get("reuse_count", 0))
    explicit_save = bool(candidate.metadata.get("explicit_save", False))
    judge_approved = bool(candidate.metadata.get("judge_approved", False))
    if candidate.memory_class == MemoryClass.EPISODIC and (reuse >= 3 or explicit_save):
        return ConsolidationDecision(True, MemoryClass.EPISODIC, MemoryClass.SEMANTIC, "reused_or_saved", 0.85)
    if candidate.memory_class == MemoryClass.EPISODIC and candidate.metadata.get("tool_success_count", 0) >= 3:
        return ConsolidationDecision(True, MemoryClass.EPISODIC, MemoryClass.PROCEDURAL, "repeated_success", 0.82)
    if candidate.metadata.get("user_correction"):
        return ConsolidationDecision(True, candidate.memory_class, MemoryClass.LESSON, "correction", 0.9)
    if candidate.confidence < 0.5 and not judge_approved:
        return ConsolidationDecision(False, candidate.memory_class, MemoryClass.QUARANTINE, "low_confidence", 0.7, True)
    return ConsolidationDecision(False, candidate.memory_class, candidate.memory_class, "no_promotion", 0.5)
