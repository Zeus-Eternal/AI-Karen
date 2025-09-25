import asyncio
from datetime import datetime

from ai_karen_engine.models.ag_ui_types import AGUIMemoryQuery
from ai_karen_engine.services.ag_ui_memory_interface import (
    transform_ag_ui_query,
    transform_web_ui_entries,
)
from ai_karen_engine.services.memory_service import WebUIMemoryEntry


def run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


def test_transform_ag_ui_query():
    now = int(datetime.utcnow().timestamp() * 1000)
    query = AGUIMemoryQuery(
        queryText="hello", sessionId="s1", timeRange=(now - 1000, now)
    )
    web_query = run(transform_ag_ui_query(query))
    assert web_query.text == "hello"
    assert web_query.session_id == "s1"
    assert web_query.top_k == 5
    assert web_query.time_range is not None


def test_transform_web_ui_entries():
    timestamp = datetime.utcnow().timestamp()
    entry = WebUIMemoryEntry(
        id="1",
        content="test",
        timestamp=timestamp,
        tags=["tag"],
        similarity_score=0.9,
        embedding=None,
        metadata={},
        ttl=None,
        user_id="u1",
        session_id="s1",
    )
    ag_entries = transform_web_ui_entries([entry])
    assert ag_entries[0].id == "1"
    assert ag_entries[0].timestamp == int(timestamp * 1000)
    assert ag_entries[0].tags == ["tag"]
