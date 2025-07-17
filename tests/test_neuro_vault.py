import importlib

from ai_karen_engine.core.neuro_vault import NeuroVault
from ai_karen_engine.core.embedding_manager import _METRICS


def test_index_and_query():
    nv = NeuroVault()
    nv.index_text("u", "the cat sat on the mat", {"id": 1})
    nv.index_text("u", "dogs play in the park", {"id": 2})
    results = nv.query("u", "cat on mat", top_k=2)
    assert results[0]["metadata"]["id"] == 1
    assert "memory_recall_latency" in _METRICS
    assert "rerank_time" in _METRICS
    assert "recall_hit_rate" in _METRICS
