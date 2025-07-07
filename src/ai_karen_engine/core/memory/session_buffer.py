from __future__ import annotations

import json
import os
import threading
import time
from typing import Any, Dict, List, Optional

from ai_karen_engine.clients.database.duckdb_client import DuckDBClient
from ai_karen_engine.clients.database.postgres_client import PostgresClient


class SessionBuffer:
    """Buffer chat records in DuckDB until flushed to Postgres."""

    def __init__(
        self,
        duckdb_client: DuckDBClient,
        postgres_client: Optional[PostgresClient] = None,
        flush_size: Optional[int] = None,
    ) -> None:
        self.duckdb = duckdb_client
        self.postgres = postgres_client
        self.flush_size = flush_size or int(os.getenv("SESSION_BUFFER_SIZE", "20"))
        self._pending: Dict[str, List[Dict[str, Any]]] = {}
        self._lock = threading.Lock()
        self._ensure_table()

    def _ensure_table(self) -> None:
        with self.duckdb._get_conn() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS session_buffer (
                    user_id VARCHAR,
                    session_id VARCHAR,
                    query VARCHAR,
                    result VARCHAR,
                    timestamp BIGINT,
                    vector_id BIGINT
                )
                """
            )

    def add_entry(
        self,
        user_id: str,
        session_id: Optional[str],
        query: str,
        result: Any,
        vector_id: Optional[int] = None,
        timestamp: Optional[int] = None,
    ) -> None:
        ts = timestamp or int(time.time())
        entry = {
            "user_id": user_id,
            "session_id": session_id,
            "query": query,
            "result": result,
            "timestamp": ts,
            "vector_id": vector_id if vector_id is not None else -1,
        }
        with self.duckdb._get_conn() as conn:
            conn.execute(
                "INSERT INTO session_buffer (user_id, session_id, query, result, timestamp, vector_id) VALUES (?, ?, ?, ?, ?, ?)",
                [user_id, session_id, query, json.dumps(result), ts, entry["vector_id"]],
            )

        sid = session_id or "default"
        with self._lock:
            self._pending.setdefault(sid, []).append(entry)
            if len(self._pending[sid]) >= self.flush_size:
                self.flush_to_postgres(sid)

    def _load_entries(self, sid: str) -> List[Dict[str, Any]]:
        with self.duckdb._get_conn() as conn:
            rows = conn.execute(
                "SELECT user_id, session_id, query, result, timestamp, vector_id FROM session_buffer WHERE session_id = ?",
                [sid],
            ).fetchall()
        return [
            {
                "user_id": r[0],
                "session_id": r[1],
                "query": r[2],
                "result": json.loads(r[3]),
                "timestamp": r[4],
                "vector_id": r[5],
            }
            for r in rows
        ]

    def flush_to_postgres(self, session_id: Optional[str] = None) -> None:
        if not self.postgres:
            return
        sessions = [session_id] if session_id else list(self._pending.keys())
        for sid in sessions:
            entries = self._load_entries(sid)
            if not entries:
                continue
            try:
                for e in entries:
                    self.postgres.upsert_memory(
                        e.get("vector_id", -1),
                        e["user_id"],
                        e["session_id"],
                        e["query"],
                        e["result"],
                        e["timestamp"],
                    )
                with self.duckdb._get_conn() as conn:
                    conn.execute("DELETE FROM session_buffer WHERE session_id = ?", [sid])
                with self._lock:
                    self._pending[sid] = []
            except Exception:
                # keep entries for later retry
                continue
