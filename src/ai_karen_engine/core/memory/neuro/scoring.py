from __future__ import annotations

from .contracts import MemoryCandidate


def blended_score(candidate: MemoryCandidate) -> float:
    m = candidate.metadata
    semantic = float(m.get("semantic_similarity", 0.0))
    lexical = float(m.get("lexical_match", 0.0))
    freshness = float(candidate.freshness)
    importance = float(candidate.importance)
    confidence = float(candidate.confidence)
    reuse = float(m.get("reuse_count", 0.0))
    class_weight = float(m.get("memory_class_weight", 1.0))
    user_confirmation = float(m.get("user_confirmation", 0.0))
    trust = float(m.get("source_trust", 1.0))
    tenant_match = float(m.get("tenant_match", 1.0))
    procedure_success = float(m.get("procedure_success_rate", 0.0))
    penalty = float(m.get("correction_penalty", 0.0)) + float(m.get("quarantine_penalty", 0.0))
    return max(
        0.0,
        min(
            1.0,
            (semantic * 0.2)
            + (lexical * 0.12)
            + (freshness * 0.1)
            + (importance / 10.0 * 0.08)
            + (confidence * 0.14)
            + (min(1.0, reuse / 10.0) * 0.06)
            + (class_weight * 0.08)
            + (user_confirmation * 0.06)
            + (trust * 0.06)
            + (tenant_match * 0.05)
            + (procedure_success * 0.05)
            - penalty,
        ),
    )
