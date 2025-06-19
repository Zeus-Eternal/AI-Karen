from core.soft_reasoning_engine import SoftReasoningEngine


def test_ingest_and_query():
    engine = SoftReasoningEngine()
    engine.ingest("hello world")
    results = engine.query("hello", top_k=1)
    assert results
    assert results[0]["payload"]["text"] == "hello world"
