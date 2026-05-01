import pytest

from ai_karen_engine.core.memory.graph.config import LeanGraphConfig
from ai_karen_engine.core.memory.graph.service import LeanGraphService


@pytest.mark.asyncio
async def test_projection_creates_mentions_and_supersedes_edges(tmp_path):
    cfg = LeanGraphConfig(graph_db_path=str(tmp_path), graph_backend="kuzu")
    svc = LeanGraphService(cfg)
    ok = await svc.project_memory_event(
        {"event_id": "e1", "tenant_id": "t1", "user_id": "u1", "supersedes": "e0", "payload": {"entities": [{"text": "Detroit"}]}}
    )
    assert ok is True
    ctx = await svc.get_entity_context("t1", "u1", "Detroit")
    assert any(row["event_id"] == "e1" for row in ctx)


@pytest.mark.asyncio
async def test_circuit_breaker_opens_after_repeated_failures(tmp_path):
    cfg = LeanGraphConfig(graph_db_path=str(tmp_path), graph_backend="kuzu")
    svc = LeanGraphService(cfg)
    svc._failure_threshold = 1
    svc.adapter.upsert_memory_event = lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("boom"))  # type: ignore[method-assign]
    ok = await svc.project_memory_event({"event_id": "e1", "tenant_id": "t1", "user_id": "u1", "payload": {}})
    assert ok is False
    # second call should short-circuit while circuit is open
    skipped = await svc.project_memory_event({"event_id": "e2", "tenant_id": "t1", "user_id": "u1", "payload": {}})
    assert skipped is False
