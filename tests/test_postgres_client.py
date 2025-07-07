import time
from ai_karen_engine.clients.database.postgres_client import PostgresClient


def test_upsert_and_recall():
    client = PostgresClient(dsn="sqlite:///:memory:", use_sqlite=True)
    client.upsert_memory(1, "u1", "s1", "q", "r", timestamp=123)
    rec = client.get_by_vector(1)
    assert rec["user_id"] == "u1"
    assert rec["session_id"] == "s1"
    client.upsert_memory(1, "u1", "s1", "q2", "r2", timestamp=124)
    rec2 = client.get_by_vector(1)
    assert rec2["query"] == "q2"
    sess = client.get_session_records("s1")
    assert len(sess) == 1
    assert sess[0]["result"] == "r2"
    client.delete(1)
    assert client.get_by_vector(1) is None
