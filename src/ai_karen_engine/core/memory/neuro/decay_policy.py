from __future__ import annotations

from .contracts import MemoryCandidate, MemoryClass


def decay_score(candidate: MemoryCandidate) -> float:
    base = candidate.confidence * (0.5 + candidate.importance / 2)
    reuse = float(candidate.metadata.get("reuse_count", 0))
    corrections = float(candidate.metadata.get("correction_count", 0))
    risk = float(candidate.metadata.get("risk_score", 0))
    if candidate.memory_class == MemoryClass.STM:
        factor = 0.4
    elif candidate.memory_class == MemoryClass.EPISODIC:
        factor = 0.6
    elif candidate.memory_class == MemoryClass.SEMANTIC:
        factor = 0.9
    elif candidate.memory_class == MemoryClass.PROCEDURAL:
        factor = 0.85
    elif candidate.memory_class == MemoryClass.LESSON:
        factor = 0.95
    else:
        factor = 0.2
    return max(0.0, min(1.0, base * factor + (reuse * 0.03) - (corrections * 0.05) - (risk * 0.1)))
