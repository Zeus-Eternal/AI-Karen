import pytest

from src.ai_karen_engine.services.memory_service import (
    MemoryType,
    UISource,
    WebUIMemoryQuery,
    WebUIMemoryService,
)


@pytest.mark.asyncio
async def test_null_memory_manager_graceful():
    service = WebUIMemoryService(None)

    # Store should gracefully return None
    result = await service.store_web_ui_memory(
        tenant_id="tenant",
        content="hello",
        user_id="user",
        ui_source=UISource.API,
        memory_type=MemoryType.GENERAL,
    )
    assert result is None

    # Query should gracefully return empty list
    memories = await service.query_memories(
        "tenant",
        WebUIMemoryQuery(text="hi"),
    )
    assert memories == []
