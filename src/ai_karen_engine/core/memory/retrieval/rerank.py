from __future__ import annotations

from typing import Iterable, List

from ..neuro.scoring import blended_score
from ..types import MemoryEntry


def rerank_entries(entries: Iterable[MemoryEntry], top_k: int) -> List[MemoryEntry]:
    ranked = sorted(entries, key=lambda e: float(e.relevance), reverse=True)
    return ranked[: max(1, int(top_k or 1))]
