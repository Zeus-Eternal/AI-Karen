import os
import json
from pathlib import Path

from core.response.chat_memory import ChatMemory


def test_store_and_fetch_context(tmp_path):
    meta_file = tmp_path / "meta.json"
    memory = ChatMemory(metadata_path=meta_file)
    conv = "c1"
    memory.store(conv, "hello", "hi")
    memory.store(conv, "how are you", "fine")
    ctx1 = memory.fetch_context(conv)
    assert len(ctx1) == 2
    # subsequent fetch should use cache
    ctx2 = memory.fetch_context(conv)
    assert ctx1 == ctx2
    # ensure metadata persisted
    assert meta_file.exists()
    data = json.loads(meta_file.read_text())
    assert conv in data


def test_recall_promotes_frequent_items(tmp_path):
    meta_file = tmp_path / "meta.json"
    memory = ChatMemory(metadata_path=meta_file)
    conv = "c2"
    memory.store(conv, "a", "1")
    memory.store(conv, "b", "2")
    # access second message multiple times
    for _ in range(3):
        memory.fetch_context(conv)
    # after repeated access, second record should have higher access_count
    records = memory._store[conv]
    assert records[0].access_count <= records[1].access_count


def test_health_status(tmp_path):
    meta_file = tmp_path / "meta.json"
    memory = ChatMemory(metadata_path=meta_file)
    conv = "c3"
    memory.store(conv, "hello", "hi")
    status = memory.health_status()
    assert status["conversations"] == 1
    assert status["records"] == 1
