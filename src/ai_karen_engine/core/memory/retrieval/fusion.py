from __future__ import annotations

from typing import Dict, Iterable, List

from ..types import MemoryEntry


def reciprocal_rank_fusion(scored_lists: Dict[str, List[MemoryEntry]], k: int = 60) -> List[MemoryEntry]:
    fused: Dict[str, float] = {}
    best: Dict[str, MemoryEntry] = {}
    for _, entries in scored_lists.items():
        for rank, entry in enumerate(entries, start=1):
            fused[entry.id] = fused.get(entry.id, 0.0) + 1.0 / (k + rank)
            if entry.id not in best or entry.relevance > best[entry.id].relevance:
                best[entry.id] = entry
    ranked = sorted(best.values(), key=lambda e: fused.get(e.id, 0.0), reverse=True)
    for entry in ranked:
        entry.relevance = max(entry.relevance, fused.get(entry.id, 0.0))
    return ranked


def dedupe_by_id(entries: Iterable[MemoryEntry]) -> List[MemoryEntry]:
    seen = set()
    out: List[MemoryEntry] = []
    for entry in entries:
        if entry.id in seen:
            continue
        seen.add(entry.id)
        out.append(entry)
    return out
