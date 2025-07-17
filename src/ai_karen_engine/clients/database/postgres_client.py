"""In-memory fallback Postgres client."""
from __future__ import annotations

from typing import Any, Dict, List


class PostgresClient:
    """Simple in-memory Postgres replacement used for tests and fallback."""

    def __init__(self, dsn: str = "", use_sqlite: bool = True) -> None:
        self._store: Dict[int, Dict[str, Any]] = {}
        self.dsn = dsn
        self.use_sqlite = use_sqlite

    # ------------------------------------------------------------------
    def upsert_memory(
        self,
        vector_id: int,
        user_id: str,
        session_id: str,
        query: str,
        result: Any,
        timestamp: int = 0,
    ) -> None:
        self._store[vector_id] = {
            "user_id": user_id,
            "session_id": session_id,
            "query": query,
            "result": result,
            "timestamp": timestamp,
        }

    def get_by_vector(self, vector_id: int) -> Dict[str, Any] | None:
        return self._store.get(vector_id)

    def get_session_records(self, session_id: str) -> List[Dict[str, Any]]:
        return [v for v in self._store.values() if v["session_id"] == session_id]

    def recall_memory(self, user_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        recs = [v for v in self._store.values() if v["user_id"] == user_id]
        recs.sort(key=lambda r: r["timestamp"], reverse=True)
        return recs[:limit]

    def delete(self, vector_id: int) -> None:
        self._store.pop(vector_id, None)

    def health(self) -> bool:
        return True


__all__ = ["PostgresClient"]
