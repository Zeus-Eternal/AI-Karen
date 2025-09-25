import importlib
import duckdb
from ai_karen_engine.core.memory import manager as mm


class FakePostgres:
    def __init__(self):
        self.records = []
        self.fail = True

    def upsert_memory(self, *args, **kwargs):
        if self.fail:
            raise Exception("down")
        self.records.append(args)

    def health(self):
        return not self.fail


def test_flush_after_reconnect(tmp_path, monkeypatch):
    db_path = tmp_path / "mem.duckdb"
    monkeypatch.setenv("DUCKDB_PATH", str(db_path))
    importlib.reload(mm)
    fake = FakePostgres()
    monkeypatch.setattr(mm, "postgres", fake)
    if getattr(mm, "pg_syncer", None):
        mm.pg_syncer.stop()
    mm.pg_syncer = mm.PostgresSyncer(fake, str(db_path), interval=0.01)
    mm.pg_syncer.postgres_available = False

    mm.update_memory({"user_id": "u1", "session_id": "s1", "tenant_id": "t1"}, "q1", "r1")
    with duckdb.connect(str(db_path)) as con:
        count = con.execute("SELECT COUNT(*) FROM memory WHERE synced=FALSE").fetchone()[0]
    assert count == 1
    assert len(fake.records) == 0

    fake.fail = False
    mm.pg_syncer.run_once()
    with duckdb.connect(str(db_path)) as con:
        count = con.execute("SELECT COUNT(*) FROM memory WHERE synced=FALSE").fetchone()[0]
    assert count == 0
    assert len(fake.records) == 1
