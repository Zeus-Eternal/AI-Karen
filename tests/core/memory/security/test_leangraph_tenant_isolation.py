import pytest
from ai_karen_engine.core.memory.graph.config import LeanGraphConfig
from ai_karen_engine.core.memory.graph.service import LeanGraphService


@pytest.mark.asyncio
async def test_tenant_isolation_blocks_cross_tenant_reads(tmp_path):
    svc = LeanGraphService(LeanGraphConfig(graph_db_path=str(tmp_path)))
    await svc.project_memory_event({"event_id": "e1", "tenant_id": "t1", "user_id": "u1", "payload": {"entities": [{"text": "ProjectX"}]}})
    other = await svc.get_entity_context("t2", "u2", "ProjectX")
    assert other == []
