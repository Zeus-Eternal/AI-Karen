from __future__ import annotations

from .contracts import MemoryCandidate


def blended_score(candidate: MemoryCandidate) -> float:
    m = candidate.metadata
    semantic = float(m.get("semantic_similarity", 0.0))
    lexical = float(m.get("lexical_match", 0.0))
    freshness = float(candidate.freshness)
    confidence = float(candidate.confidence)
    trust = float(m.get("source_trust", 1.0))
    penalty = float(m.get("correction_penalty", 0.0)) + float(m.get("quarantine_penalty", 0.0))
    return max(0.0, min(1.0, semantic * 0.35 + lexical * 0.2 + freshness * 0.15 + confidence * 0.2 + trust * 0.1 - penalty))
