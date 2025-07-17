from ai_karen_engine.core.memory.session_buffer import SessionBuffer
from ai_karen_engine.clients.database.duckdb_client import DuckDBClient
from ai_karen_engine.clients.database.postgres_client import PostgresClient


class FailPostgres:
    def upsert_memory(self, *args, **kwargs):
        raise RuntimeError("down")


def test_duckdb_persists_when_postgres_down(tmp_path):
    db_path = tmp_path / "buf.db"
    duck = DuckDBClient(db_path=str(db_path))
    buf = SessionBuffer(duck, FailPostgres(), flush_size=1)
    buf.add_entry("u1", "tbuf", "s1", "q", "r", vector_id=1, timestamp=1)
    buf.flush_to_postgres("s1")
    with duck._get_conn() as con:
        count = con.execute("SELECT COUNT(*) FROM session_buffer").fetchone()[0]
    assert count == 1


def test_flushing_moves_data(tmp_path):
    db_path = tmp_path / "buf2.db"
    duck = DuckDBClient(db_path=str(db_path))
    pg = PostgresClient(dsn="sqlite:///:memory:", use_sqlite=True)
    buf = SessionBuffer(duck, pg, flush_size=1)
    buf.add_entry("u2", "tbuf", "s2", "q2", "r2", vector_id=2, timestamp=2)
    buf.flush_to_postgres("s2")
    with duck._get_conn() as con:
        count = con.execute("SELECT COUNT(*) FROM session_buffer").fetchone()[0]
    assert count == 0
    recs = pg.recall_memory("u2", limit=1, tenant_id="tbuf")
    assert recs[0]["query"] == "q2"
    assert buf._pending.get("s2") == []
