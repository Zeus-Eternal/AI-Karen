from ai_karen_engine.clients.database.postgres_client import PostgresClient

def test_upsert_and_recall():
    client = PostgresClient(dsn="sqlite:///:memory:", use_sqlite=True)
    client.upsert_memory(1, "t1", "u1", "s1", "q", "r", timestamp=123)
    rec = client.get_by_vector(1)
    assert rec["user_id"] == "u1"
    assert rec["session_id"] == "s1"
    assert rec["query"] == "q"
    assert rec["result"] == "r"
    assert rec["timestamp"] == 123

    # Overwrite same vector, check update
    client.upsert_memory(1, "t1", "u1", "s1", "q2", "r2", timestamp=124)
    rec2 = client.get_by_vector(1)
    assert rec2["query"] == "q2"
    assert rec2["result"] == "r2"
    assert rec2["timestamp"] == 124

    # Session fetch
    sess = client.get_session_records("s1", tenant_id="t1")
    assert len(sess) == 1
    assert sess[0]["result"] == "r2"

    # Delete logic
    client.delete(1)
    assert client.get_by_vector(1) is None

def test_recall_memory_batch():
    client = PostgresClient(dsn="sqlite:///:memory:", use_sqlite=True)
    for i in range(5):
        client.upsert_memory(i, "t2", "u2", "s2", f"q{i}", f"r{i}", timestamp=100 + i)
    recs = client.recall_memory("u2", limit=3, tenant_id="t2")
    assert len(recs) == 3
    assert recs[0]["query"] == "q4"
    assert recs[1]["query"] == "q3"
    assert recs[2]["query"] == "q2"

    # Ensure cross-tenant isolation
    other = client.recall_memory("u2", limit=1, tenant_id="other")
    assert other == []

def test_health_ok():
    client = PostgresClient(dsn="sqlite:///:memory:", use_sqlite=True)
    assert client.health() is True

def test_sqlite_fallback_without_psycopg(monkeypatch):
    import sys
    sys.modules["psycopg"] = None
    client = PostgresClient(dsn="sqlite:///:memory:", use_sqlite=True)
    client.upsert_memory(2, "t3", "u3", "s3", "test_query", "test_result")
    rec = client.get_by_vector(2)
    assert rec["user_id"] == "u3"
    assert rec["query"] == "test_query"

