import numpy as np
import pytest

from ai_karen_engine.database.memory_manager import MemoryManager, MemoryQuery


class DummyDBClient:
    async def get_async_session(self):
        class DummySession:
            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc, tb):
                pass

            async def execute(self, *args, **kwargs):
                pass

            def add(self, *args, **kwargs):
                pass

            async def commit(self):
                pass

        return DummySession()


class DummyEmbeddingManager:
    async def get_embedding(self, text: str):
        return np.zeros(3)


@pytest.mark.asyncio
async def test_query_memories_without_milvus():
    manager = MemoryManager(DummyDBClient(), None, DummyEmbeddingManager())
    query = MemoryQuery(text="hi")
    results = await manager.query_memories("tenant", query)
    assert results == []


@pytest.mark.asyncio
async def test_check_surprise_without_milvus():
    manager = MemoryManager(DummyDBClient(), None, DummyEmbeddingManager())
    embedding = np.zeros(3)
    surprising = await manager._check_surprise("tenant", embedding)
    assert surprising is True
