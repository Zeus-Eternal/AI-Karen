from __future__ import annotations

from typing import Dict, List
from .contracts import LessonArtifact


class LessonMemoryStore:
    def __init__(self) -> None:
        self._store: Dict[str, List[LessonArtifact]] = {}

    def put(self, tenant_id: str, artifact: LessonArtifact) -> None:
        self._store.setdefault(tenant_id, []).append(artifact)

    def recall(self, tenant_id: str, scope: str, limit: int = 5) -> List[LessonArtifact]:
        items = self._store.get(tenant_id, [])
        scope_l = scope.lower()
        return [a for a in items if scope_l in a.failure_signature.lower() or any(scope_l in x.lower() for x in a.applies_to)][:limit]
