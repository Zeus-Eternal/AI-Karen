"""Postgres client with optional SQLite fallback."""
from __future__ import annotations

import json
import os
import sqlite3
from typing import Any, Dict, List, Optional

try:
    import psycopg
    _PSYCOPG_AVAILABLE = True
except Exception:  # pragma: no cover - optional dependency
    psycopg = None
    _PSYCOPG_AVAILABLE = False


class PostgresClient:
    """Lightweight Postgres client used for memory persistence."""

    def __init__(self, dsn: str = "", use_sqlite: bool = False) -> None:
        self.dsn = dsn
        self.use_sqlite = use_sqlite or not _PSYCOPG_AVAILABLE
        if self.use_sqlite:
            path = dsn.replace("sqlite://", "") or ":memory:"
            self.conn = sqlite3.connect(path, check_same_thread=False)
        else:
            pg_dsn = dsn or (
                "dbname=%s user=%s password=%s host=%s port=%s"
                % (
                    os.getenv("POSTGRES_DB", "postgres"),
                    os.getenv("POSTGRES_USER", "postgres"),
                    os.getenv("POSTGRES_PASSWORD", "postgres"),
                    os.getenv("POSTGRES_HOST", "localhost"),
                    os.getenv("POSTGRES_PORT", "5432"),
                )
            )
            self.conn = psycopg.connect(pg_dsn, autocommit=True)
        self._ensure_table()

    @property
    def placeholder(self) -> str:
        """Return SQL placeholder appropriate for the backend."""
        return "?" if self.use_sqlite else "%s"

    # ------------------------------------------------------------------
    def _ensure_table(self) -> None:
        create_sql = (
            "CREATE TABLE IF NOT EXISTS memory ("
            "vector_id BIGINT PRIMARY KEY,"
            "tenant_id VARCHAR,"
            "user_id VARCHAR,"
            "session_id VARCHAR,"
            "query TEXT,"
            "result TEXT,"
            "timestamp BIGINT"
            ")"
        )
        cur = self.conn.cursor()
        cur.execute(create_sql)
        self.conn.commit()
        cur.close()

    # ------------------------------------------------------------------
    def _execute(self, sql: str, params: Optional[List[Any]] = None, fetch: bool = False) -> List[tuple]:
        cur = self.conn.cursor()
        cur.execute(sql, params or [])
        rows = cur.fetchall() if fetch else []
        self.conn.commit()
        cur.close()
        return rows

    # ------------------------------------------------------------------
    def upsert_memory(
        self,
        vector_id: int,
        tenant_id: str,
        user_id: str,
        session_id: str,
        query: str,
        result: Any,
        timestamp: int = 0,
    ) -> None:
        data_json = json.dumps(result)
        if self.use_sqlite:
            sql = (
                "INSERT INTO memory (vector_id, tenant_id, user_id, session_id, query, result, timestamp) "
                "VALUES (?, ?, ?, ?, ?, ?, ?) "
                "ON CONFLICT(vector_id) DO UPDATE SET "
                "tenant_id=excluded.tenant_id, user_id=excluded.user_id, session_id=excluded.session_id, "
                "query=excluded.query, result=excluded.result, timestamp=excluded.timestamp"
            )
            self._execute(
                sql, [vector_id, tenant_id, user_id, session_id, query, data_json, timestamp]
            )
        else:
            sql = (
                "INSERT INTO memory (vector_id, tenant_id, user_id, session_id, query, result, timestamp) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s) "
                "ON CONFLICT (vector_id) DO UPDATE SET "
                "tenant_id=EXCLUDED.tenant_id, user_id=EXCLUDED.user_id, session_id=EXCLUDED.session_id, "
                "query=EXCLUDED.query, result=EXCLUDED.result, timestamp=EXCLUDED.timestamp"
            )
            self._execute(
                sql, [vector_id, tenant_id, user_id, session_id, query, data_json, timestamp]
            )

    def get_by_vector(self, vector_id: int) -> Optional[Dict[str, Any]]:
        sql = "SELECT tenant_id, user_id, session_id, query, result, timestamp FROM memory WHERE vector_id = "
        sql += "?" if self.use_sqlite else "%s"
        rows = self._execute(sql, [vector_id], fetch=True)
        if not rows:
            return None
        row = rows[0]
        return {
            "tenant_id": row[0],
            "user_id": row[1],
            "session_id": row[2],
            "query": row[3],
            "result": json.loads(row[4]),
            "timestamp": row[5],
        }

    def get_session_records(self, session_id: str, tenant_id: Optional[str] = None) -> List[Dict[str, Any]]:
        sql = "SELECT vector_id, tenant_id, user_id, session_id, query, result, timestamp FROM memory WHERE session_id = "
        sql += "?" if self.use_sqlite else "%s"
        params = [session_id]
        if tenant_id is not None:
            sql += " AND tenant_id = " + ("?" if self.use_sqlite else "%s")
            params.append(tenant_id)
        rows = self._execute(sql, params, fetch=True)
        return [
            {
                "vector_id": r[0],
                "tenant_id": r[1],
                "user_id": r[2],
                "session_id": r[3],
                "query": r[4],
                "result": json.loads(r[5]),
                "timestamp": r[6],
            }
            for r in rows
        ]

    def recall_memory(
        self, user_id: str, query: Optional[str] = None, limit: int = 5, tenant_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        sql = (
            "SELECT vector_id, tenant_id, user_id, session_id, query, result, timestamp FROM memory "
            "WHERE user_id = "
        )
        sql += "?" if self.use_sqlite else "%s"
        params = [user_id]
        if tenant_id is not None:
            sql += " AND tenant_id = " + ("?" if self.use_sqlite else "%s")
            params.append(tenant_id)
        sql += " ORDER BY timestamp DESC LIMIT "
        sql += "?" if self.use_sqlite else "%s"
        params.append(limit)
        rows = self._execute(sql, params, fetch=True)
        return [
            {
                "vector_id": r[0],
                "tenant_id": r[1],
                "user_id": r[2],
                "session_id": r[3],
                "query": r[4],
                "result": json.loads(r[5]),
                "timestamp": r[6],
            }
            for r in rows
        ]

    def delete(self, vector_id: int) -> None:
        sql = "DELETE FROM memory WHERE vector_id = "
        sql += "?" if self.use_sqlite else "%s"
        self._execute(sql, [vector_id])

    def health(self) -> bool:
        try:
            self._execute("SELECT 1", fetch=True)
            return True
        except Exception:
            return False


__all__ = ["PostgresClient"]
