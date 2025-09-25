import numpy as np
import pytest

from src.ai_karen_engine.database.memory_manager import MemoryManager


class DummyMilvusClient:
    def __init__(self):
        self.called = False

    async def search(self, *args, **kwargs):
        self.called = True
        return [[type("Result", (), {"distance": 0.9})()]]


class DummyEmbeddingManager:
    pass


class DummyDBClient:
    pass


@pytest.mark.asyncio
async def test_disable_surprise_filter(monkeypatch):
    monkeypatch.setenv("KARI_DISABLE_MEMORY_SURPRISE_FILTER", "true")
    manager = MemoryManager(
        DummyDBClient(), DummyMilvusClient(), DummyEmbeddingManager()
    )
    assert manager.disable_surprise_check is True
    result = await manager._check_surprise("tenant", np.array([0.1, 0.2]))
    assert result is True
    assert not manager.milvus_client.called
