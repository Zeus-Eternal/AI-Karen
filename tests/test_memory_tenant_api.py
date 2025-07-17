import types


from ai_karen_engine.core.memory import manager as mm
from tests.test_memory_manager import duckdb_stub


def load_manager(monkeypatch):
    store = []

    class RecordingPostgres:
        def __init__(self):
            self.records = []

        def upsert_memory(self, *args, **kwargs):
            self.records.append((args, kwargs))

        def recall_memory(self, *args, **kwargs):
            return []

    pg = RecordingPostgres()
    monkeypatch.setattr(mm, "postgres", pg)
    monkeypatch.setattr(mm, "pg_syncer", types.SimpleNamespace(postgres_available=True, mark_unavailable=lambda: None))
    monkeypatch.setattr(mm, "redis", None)
    monkeypatch.setattr(mm, "duckdb", duckdb_stub(store))
    monkeypatch.setattr(mm, "store_vector", lambda u, q, r, tenant_id=None: 1)
    return mm


def test_tenant_isolated_calls(monkeypatch):
    manager = load_manager(monkeypatch)
    manager.update_memory({"user_id": "u", "session_id": "s", "tenant_id": "A"}, "q", "r")
    result = manager.recall_context({"user_id": "u", "tenant_id": "B"}, "q")
    assert result is None
