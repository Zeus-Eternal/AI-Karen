from ai_karen_engine.doc_store import DocumentStore
from ai_karen_engine.core.embedding_manager import _METRICS


def test_ingest_and_query(monkeypatch, tmp_path):
    store = DocumentStore()

    sample_text = "INTRO\nThis is a test.\nSECOND\nAnother section."
    monkeypatch.setattr(store, "_extract_text", lambda p: sample_text)

    count = store.ingest("dummy.pdf", doc_id="doc1")
    assert count == 2
    assert "doc_chunks_indexed" in _METRICS

    results = store.query("test", metadata_filter={"doc_id": "doc1"})
    assert results
    assert results[0]["payload"]["doc_id"] == "doc1"
    assert "doc_search_latency" in _METRICS
    assert "metadata_hit_rate" in _METRICS
