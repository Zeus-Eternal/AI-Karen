import pytest
from ai_karen_engine.core.memory.projections.leangraph_worker import LeanGraphWorker


@pytest.mark.asyncio
async def test_worker_delegates_to_service():
    worker = LeanGraphWorker()
    ok = await worker.project({"event_id": "e1", "tenant_id": "t1", "user_id": "u1", "payload": {}}, None)
    assert ok is True
