"""Postgres-backed storage client mirroring DuckDBClient."""

import json
import os
import threading
from datetime import datetime

try:
    import psycopg  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    psycopg = None


class PostgresClient:
    """Simple PostgreSQL client for user profiles and memory."""

    def __init__(
        self,
        host: str | None = None,
        port: int | None = None,
        dbname: str | None = None,
        user: str | None = None,
        password: str | None = None,
    ) -> None:
        if psycopg is None:
            raise ImportError("psycopg is required for PostgresClient")
        self.conn_params = {
            "host": host or os.getenv("POSTGRES_HOST", "localhost"),
            "port": int(port or os.getenv("POSTGRES_PORT", "5432")),
            "dbname": dbname or os.getenv("POSTGRES_DB", "postgres"),
            "user": user or os.getenv("POSTGRES_USER", "postgres"),
            "password": password or os.getenv("POSTGRES_PASSWORD", "postgres"),
        }
        self._lock = threading.Lock()
        self._ensure_tables()

    def _get_conn(self):
        if psycopg is None:
            raise ImportError("psycopg is required for PostgresClient")
        return psycopg.connect(**self.conn_params)

    def _ensure_tables(self) -> None:
        with self._get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS profiles (
                        user_id VARCHAR PRIMARY KEY,
                        profile_json TEXT,
                        last_update TIMESTAMP
                    );
                    """
                )
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS profile_history (
                        id SERIAL PRIMARY KEY,
                        user_id VARCHAR,
                        timestamp DOUBLE PRECISION,
                        field VARCHAR,
                        old TEXT,
                        new TEXT
                    );
                    """
                )
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS long_term_memory (
                        user_id VARCHAR,
                        memory_json TEXT
                    );
                    """
                )
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS user_roles (
                        user_id VARCHAR,
                        role VARCHAR
                    );
                    """
                )
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS memory (
                        user_id VARCHAR,
                        query VARCHAR,
                        result TEXT,
                        timestamp BIGINT
                    );
                    """
                )
                conn.commit()

    # Profile CRUD
    def get_profile(self, user_id: str):
        with self._lock, self._get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT profile_json FROM profiles WHERE user_id=%s", (user_id,))
                res = cur.fetchone()
                return json.loads(res[0]) if res else None

    def update_profile(self, user_id: str, field: str, value):
        with self._lock, self._get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT profile_json FROM profiles WHERE user_id=%s", (user_id,))
                res = cur.fetchone()
                profile = json.loads(res[0]) if res else {}
                profile[field] = value
                profile["last_update"] = datetime.utcnow().timestamp()
                profile_json = json.dumps(profile)
                if res:
                    cur.execute(
                        "UPDATE profiles SET profile_json=%s, last_update=%s WHERE user_id=%s",
                        (profile_json, datetime.utcnow(), user_id),
                    )
                else:
                    cur.execute(
                        "INSERT INTO profiles (user_id, profile_json, last_update) VALUES (%s, %s, %s)",
                        (user_id, profile_json, datetime.utcnow()),
                    )
                conn.commit()

    def create_profile(self, user_id: str, profile: dict) -> None:
        with self._lock, self._get_conn() as conn:
            with conn.cursor() as cur:
                profile["last_update"] = datetime.utcnow().timestamp()
                cur.execute(
                    "INSERT INTO profiles (user_id, profile_json, last_update) VALUES (%s, %s, %s)",
                    (user_id, json.dumps(profile), datetime.utcnow()),
                )
                conn.commit()

    def delete_profile(self, user_id: str) -> None:
        with self._lock, self._get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM profiles WHERE user_id=%s", (user_id,))
                conn.commit()

    # History
    def append_profile_history(self, user_id: str, entry: dict) -> None:
        with self._lock, self._get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO profile_history (user_id, timestamp, field, old, new) VALUES (%s, %s, %s, %s, %s)",
                    (
                        user_id,
                        entry.get("timestamp"),
                        entry.get("field"),
                        json.dumps(entry.get("old")),
                        json.dumps(entry.get("new")),
                    ),
                )
                conn.commit()

    def get_profile_history(self, user_id: str):
        with self._lock, self._get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT timestamp, field, old, new FROM profile_history WHERE user_id=%s ORDER BY timestamp DESC LIMIT 100",
                    (user_id,),
                )
                rows = cur.fetchall()
                return [
                    {
                        "timestamp": ts,
                        "field": f,
                        "old": json.loads(o) if o else None,
                        "new": json.loads(n) if n else None,
                    }
                    for ts, f, o, n in rows
                ]

    def profile_edit_count(self, user_id: str) -> int:
        with self._lock, self._get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM profile_history WHERE user_id=%s", (user_id,))
                res = cur.fetchone()
                return int(res[0]) if res else 0

    # Memory ops
    def delete_long_term_memory(self, user_id: str) -> None:
        with self._lock, self._get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM long_term_memory WHERE user_id=%s", (user_id,))
                conn.commit()

    # Interactions
    def total_interactions(self, user_id: str) -> int:
        with self._lock, self._get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM profile_history WHERE user_id=%s", (user_id,))
                res = cur.fetchone()
                return int(res[0]) if res else 0

    def recent_interactions(self, user_id: str, window_days: int = 7) -> int:
        cutoff = datetime.utcnow().timestamp() - window_days * 86400
        with self._lock, self._get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT COUNT(*) FROM profile_history WHERE user_id=%s AND timestamp >= %s",
                    (user_id, cutoff),
                )
                res = cur.fetchone()
                return int(res[0]) if res else 0

    # Roles
    def get_user_roles(self, user_id: str):
        with self._lock, self._get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT role FROM user_roles WHERE user_id=%s", (user_id,))
                res = cur.fetchall()
                return [r[0] for r in res]

    # Health
    def health(self) -> bool:
        try:
            with self._get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
            return True
        except Exception:
            return False

__all__ = ["PostgresClient"]
