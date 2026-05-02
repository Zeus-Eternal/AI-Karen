import pytest
from ai_karen_engine.core.memory.types import MemoryQuery
from ai_karen_engine.core.memory.retrieval.retrieval_router import get_retrieval_router

@pytest.mark.asyncio
async def test_recall_missing_tenant_is_empty():
    out = await get_retrieval_router().recall(MemoryQuery(text='hello', user_id='u', tenant_id=''))
    assert out == []
