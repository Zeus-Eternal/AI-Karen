from __future__ import annotations

from typing import Dict, List
from .contracts import ProcedureArtifact


class ProceduralMemoryStore:
    def __init__(self) -> None:
        self._store: Dict[str, List[ProcedureArtifact]] = {}

    def put(self, tenant_id: str, artifact: ProcedureArtifact) -> None:
        self._store.setdefault(tenant_id, []).append(artifact)

    def recall(self, tenant_id: str, trigger_text: str, limit: int = 3) -> List[ProcedureArtifact]:
        triggers = trigger_text.lower()
        items = self._store.get(tenant_id, [])
        return [a for a in items if any(p.lower() in triggers for p in a.trigger_patterns)][:limit]
