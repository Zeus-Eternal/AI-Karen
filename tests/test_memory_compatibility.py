import pytest
from datetime import datetime
from unittest.mock import Mock

from ai_karen_engine.models.web_ui_types import WebUIMemoryQuery
from ai_karen_engine.database.memory_manager import MemoryEntry
from ai_karen_engine.services.memory_compatibility import (
    transform_web_ui_memory_query,
    transform_memory_entries_to_web_ui,
    ensure_js_timestamp,
)
from ai_karen_engine.api_routes.memory_routes import MemQuery


@pytest.mark.asyncio
async def test_transform_web_ui_memory_query():
    query = WebUIMemoryQuery(
        text="hello",
        user_id="u1",
        session_id="s1",
        tags=["tag1"],
        top_k=3,
        similarity_threshold=0.8,
    )
    result = await transform_web_ui_memory_query(query)
    assert isinstance(result, MemQuery)
    assert result.query == "hello"
    assert result.user_id == "s1"
    assert result.top_k == 3


@pytest.mark.asyncio
async def test_transform_memory_entries_to_web_ui():
    entry = MemoryEntry(
        id="m1",
        content="c",
        metadata={"a": 1},
        timestamp=123.0,
    )
    entry.tags = ["t1"]
    entry.user_id = "u1"
    entry.session_id = "s1"
    results = await transform_memory_entries_to_web_ui([entry])
    assert len(results) == 1
    m = results[0]
    assert m.id == "m1"
    assert m.content == "c"
    assert m.metadata == {"a": 1}
    assert m.tags == ["t1"]
    assert isinstance(m.timestamp, int)


def test_ensure_js_timestamp():
    dt = datetime(2024, 1, 1)
    ts = ensure_js_timestamp(dt)
    assert isinstance(ts, int)
    ts2 = ensure_js_timestamp(1000)
    assert ts2 == 1000 * 1000
