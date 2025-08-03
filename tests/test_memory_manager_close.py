import sys
import types
import pytest

# Stub out heavy Milvus client dependency before importing manager
milvus_stub = types.ModuleType("ai_karen_engine.clients.database.milvus_client")
milvus_stub.recall_vectors = None
milvus_stub.store_vector = None
sys.modules.setdefault("ai_karen_engine.clients.database.milvus_client", milvus_stub)

import ai_karen_engine.core.memory.manager as manager


@pytest.mark.asyncio
async def test_close_cleans_resources(monkeypatch):
    stopped = False
    pg_closed = False
    redis_closed = False
    disconnected = False

    class FakePgSyncer:
        def stop(self):
            nonlocal stopped
            stopped = True

    class FakeConn:
        def close(self):
            nonlocal pg_closed
            pg_closed = True

    class FakePostgres:
        conn = FakeConn()

    class FakeRedis:
        def close(self):
            nonlocal redis_closed
            redis_closed = True

    class FakeIndex:
        async def disconnect(self):
            nonlocal disconnected
            disconnected = True

    monkeypatch.setattr(manager, "pg_syncer", FakePgSyncer())
    monkeypatch.setattr(manager, "postgres", FakePostgres())
    monkeypatch.setattr(manager, "redis_client", FakeRedis())
    monkeypatch.setattr(manager, "neuro_vault", types.SimpleNamespace(index=FakeIndex()))

    await manager.close()

    assert stopped
    assert pg_closed
    assert redis_closed
    assert disconnected
