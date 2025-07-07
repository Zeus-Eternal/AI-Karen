"""PostgresClient: persistent store for user and session metadata.

This client wraps psycopg for real Postgres usage but can fall back to
an in-memory SQLite database for tests or local development.
"""

from __future__ import annotations

import threading
import time
from typing import Any, Dict, List, Optional

try:
    import psycopg
except Exception:  # pragma: no cover - library optional
    psycopg = None

import sqlite3


class PostgresClient:
    def __init__(
        self,
        dsn: str = "postgresql://localhost/kari",
        use_sqlite: bool = False,
    ) -> None:
        self.dsn = dsn
        self.use_sqlite = use_sqlite or dsn.startswith("sqlite://") or psycopg is None
        self._lock = threading.Lock()
        self._connect()
        self._ensure_tables()

    # --- connection helpers -------------------------------------------------
    def _connect(self) -> None:
        if self.use_sqlite:
            path = self.dsn.replace("sqlite://", "") if self.dsn else ":memory:"
            self.conn = sqlite3.connect(path, check_same_thread=False)
            self.placeholder = "?"
        else:
            self.conn = psycopg.connect(self.dsn)
            self.placeholder = "%s"
        self.conn.execute("PRAGMA journal_mode=WAL" if self.use_sqlite else "")

    def _execute(self, sql: str, params: Optional[List[Any]] = None, fetch: bool = False):
        with self._lock:
            cur = self.conn.cursor()
            cur.execute(sql, params or [])
            res = cur.fetchall() if fetch else None
            self.conn.commit()
            cur.close()
        return res

    def _ensure_tables(self) -> None:
        ph = self.placeholder
        if self.use_sqlite:
            sql = (
                "CREATE TABLE IF NOT EXISTS memory ("
                "vector_id INTEGER PRIMARY KEY,"
                "user_id TEXT,"
                "session_id TEXT,"
                "query TEXT,"
                "result TEXT,"
                "timestamp INTEGER"
                ")"
            )
        else:
            sql = (
                "CREATE TABLE IF NOT EXISTS memory ("
                "vector_id INTEGER PRIMARY KEY,"
                "user_id VARCHAR,"
                "session_id VARCHAR,"
                "query TEXT,"
                "result TEXT,"
                "timestamp BIGINT"
                ")"
            )
        self._execute(sql)

    # --- CRUD ---------------------------------------------------------------
    def upsert_memory(
        self,
        vector_id: int,
        user_id: str,
        session_id: Optional[str],
        query: str,
        result: Any,
        timestamp: Optional[int] = None,
    ) -> None:
        timestamp = timestamp or int(time.time())
        ph = self.placeholder
        if self.use_sqlite:
            sql = (
                f"INSERT INTO memory (vector_id, user_id, session_id, query, result, timestamp)"
                f" VALUES ({ph},{ph},{ph},{ph},{ph},{ph})"
                f" ON CONFLICT(vector_id) DO UPDATE SET user_id=excluded.user_id,"
                " session_id=excluded.session_id, query=excluded.query,"
                " result=excluded.result, timestamp=excluded.timestamp"
            )
        else:
            sql = (
                f"INSERT INTO memory (vector_id, user_id, session_id, query, result, timestamp)"
                f" VALUES ({ph},{ph},{ph},{ph},{ph},{ph})"
                f" ON CONFLICT (vector_id) DO UPDATE SET user_id=EXCLUDED.user_id,"
                " session_id=EXCLUDED.session_id, query=EXCLUDED.query,"
                " result=EXCLUDED.result, timestamp=EXCLUDED.timestamp"
            )
        self._execute(sql, [vector_id, user_id, session_id, query, str(result), timestamp])

    def get_by_vector(self, vector_id: int) -> Optional[Dict[str, Any]]:
        ph = self.placeholder
        sql = f"SELECT vector_id, user_id, session_id, query, result, timestamp FROM memory WHERE vector_id={ph}"
        rows = self._execute(sql, [vector_id], fetch=True)
        if not rows:
            return None
        v_id, user_id, sess, q, res, ts = rows[0]
        return {
            "vector_id": v_id,
            "user_id": user_id,
            "session_id": sess,
            "query": q,
            "result": res,
            "timestamp": ts,
        }

    def get_session_records(self, session_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        ph = self.placeholder
        sql = (
            f"SELECT vector_id, user_id, session_id, query, result, timestamp FROM memory"
            f" WHERE session_id={ph} ORDER BY timestamp DESC LIMIT {ph}"
        )
        rows = self._execute(sql, [session_id, limit], fetch=True)
        return [
            {
                "vector_id": r[0],
                "user_id": r[1],
                "session_id": r[2],
                "query": r[3],
                "result": r[4],
                "timestamp": r[5],
            }
            for r in rows
        ]

    def delete(self, vector_id: int) -> None:
        ph = self.placeholder
        sql = f"DELETE FROM memory WHERE vector_id={ph}"
        self._execute(sql, [vector_id])

    # --- Health -------------------------------------------------------------
    def health(self) -> bool:
        try:
            self._execute("SELECT 1", fetch=True)
            return True
        except Exception:
            return False

__all__ = ["PostgresClient"]
