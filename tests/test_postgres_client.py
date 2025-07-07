import sqlite3
import sys
from types import SimpleNamespace

sys.modules.setdefault("psycopg", SimpleNamespace(connect=lambda **_: None))
from ai_karen_engine.clients.database.postgres_client import PostgresClient
from ai_karen_engine.core.memory import manager as memory_manager


class FakePgCursor:
    def __init__(self, cur):
        self.cur = cur

    def execute(self, query, params=None):
        q = query.replace("%s", "?")
        self.cur.execute(q, params or [])

    def fetchone(self):
        return self.cur.fetchone()

    def fetchall(self):
        return self.cur.fetchall()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        pass


class FakePgConnection:
    def __init__(self):
        self.conn = sqlite3.connect(":memory:")

    def cursor(self):
        return FakePgCursor(self.conn.cursor())

    def commit(self):
        self.conn.commit()

    def close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        pass


def setup_fake_tables(conn):
    cur = conn.cursor()
    cur.execute(
        "CREATE TABLE profiles (user_id TEXT PRIMARY KEY, profile_json TEXT, last_update TIMESTAMP)"
    )
    cur.execute(
        "CREATE TABLE profile_history (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, timestamp REAL, field TEXT, old TEXT, new TEXT)"
    )
    cur.execute(
        "CREATE TABLE long_term_memory (user_id TEXT, memory_json TEXT)"
    )
    cur.execute(
        "CREATE TABLE user_roles (user_id TEXT, role TEXT)"
    )
    cur.execute(
        "CREATE TABLE memory (user_id TEXT, query TEXT, result TEXT, timestamp INTEGER)"
    )
    conn.commit()


def test_postgres_client_profile_crud(monkeypatch):
    conn = FakePgConnection()
    setup_fake_tables(conn)
    monkeypatch.setattr(PostgresClient, "_get_conn", lambda self: conn)
    monkeypatch.setattr(PostgresClient, "_ensure_tables", lambda self: None)
    client = PostgresClient()

    client.create_profile("u1", {"name": "test"})
    prof = client.get_profile("u1")
    assert prof["name"] == "test"

    client.update_profile("u1", "name", "new")
    prof = client.get_profile("u1")
    assert prof["name"] == "new"

    client.delete_profile("u1")
    assert client.get_profile("u1") is None


def test_memory_manager_postgres(monkeypatch):
    conn = FakePgConnection()
    setup_fake_tables(conn)

    class FakePg:
        def connect(self, **_):
            return conn

    monkeypatch.setattr(memory_manager, "psycopg", FakePg())
    monkeypatch.setattr(memory_manager, "duckdb", None)
    monkeypatch.setattr(memory_manager, "redis", None)

    memory_manager.update_memory({"user_id": "u1"}, "q", "r")
    res = memory_manager.recall_context({"user_id": "u1"}, "q", limit=1)
    assert res and res[0]["query"] == "q"


