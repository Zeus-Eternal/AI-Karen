"""SQLite-backed Postgres client used in tests.

This lightweight implementation mimics the interface of the production
Postgres client but persists data in an in-memory SQLite database. It is
sufficient for unit tests and avoids heavy dependencies.
"""

from __future__ import annotations

import sqlite3
from typing import Any, Dict, List, Optional


class PostgresClient:
    """Simplified client providing basic CRUD operations."""

    def __init__(self, dsn: str = "", use_sqlite: bool = True) -> None:
        self.use_sqlite = use_sqlite
        self.placeholder = "?" if use_sqlite else "%s"
        self.conn = sqlite3.connect(":memory:")
        self._ensure_tables()

    # ------------------------------------------------------------------
    def _ensure_tables(self) -> None:
        self._execute(
            """
            CREATE TABLE IF NOT EXISTS memory (
                vector_id INTEGER PRIMARY KEY,
                user_id TEXT,
                session_id TEXT,
                query TEXT,
                result TEXT,
                timestamp INTEGER
            )
            """
        )

    def _execute(
        self, sql: str, params: Optional[List[Any]] | None = None, fetch: bool = False
    ) -> List[Any]:
        cur = self.conn.execute(sql, params or [])
        rows = cur.fetchall() if fetch else []
        self.conn.commit()
        return rows

    # ------------------------------------------------------------------
    def upsert_memory(
        self,
        vector_id: int,
        user_id: str,
        session_id: Optional[str],
        query: str,
        result: Any,
        timestamp: int = 0,
    ) -> None:
        ph = self.placeholder
        sql = (
            "REPLACE INTO memory (vector_id, user_id, session_id, query, result, timestamp) "
            f"VALUES ({ph},{ph},{ph},{ph},{ph},{ph})"
        )
        self._execute(
            sql,
            [vector_id, user_id, session_id, query, str(result), timestamp],
        )

    # ------------------------------------------------------------------
    def get_by_vector(self, vector_id: int) -> Optional[Dict[str, Any]]:
        rows = self._execute(
            "SELECT user_id, session_id, query, result, timestamp FROM memory WHERE vector_id=?",
            [vector_id],
            fetch=True,
        )
        if not rows:
            return None
        u, s, q, r, t = rows[0]
        return {"user_id": u, "session_id": s, "query": q, "result": r, "timestamp": t}

    def get_session_records(self, session_id: str) -> List[Dict[str, Any]]:
        rows = self._execute(
            "SELECT user_id, session_id, query, result, timestamp FROM memory WHERE session_id=?",
            [session_id],
            fetch=True,
        )
        return [
            {"user_id": u, "session_id": s, "query": q, "result": r, "timestamp": t}
            for (u, s, q, r, t) in rows
        ]

    def recall_memory(self, user_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        rows = self._execute(
            "SELECT user_id, session_id, query, result, timestamp FROM memory WHERE user_id=? ORDER BY timestamp DESC",
            [user_id],
            fetch=True,
        )
        records = [
            {"user_id": u, "session_id": s, "query": q, "result": r, "timestamp": t}
            for (u, s, q, r, t) in rows
        ]
        return records[:limit]

    def delete(self, vector_id: int) -> None:
        self._execute("DELETE FROM memory WHERE vector_id=?", [vector_id])

    def health(self) -> bool:  # pragma: no cover - trivial
        return True


__all__ = ["PostgresClient"]
