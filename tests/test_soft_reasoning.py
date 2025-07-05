import time
 
import asyncio

 
import asyncio

 
 
from ..src.ai_karen_engine.core.soft_reasoning_engine import SoftReasoningEngine


def test_ingest_and_query():
    engine = SoftReasoningEngine(ttl_seconds=0.1)
    engine.ingest("hello world")
    results = engine.query("hello", top_k=1)
    assert results
    assert results[0]["payload"]["text"] == "hello world"


def test_prune():
    engine = SoftReasoningEngine(ttl_seconds=0.1)
    engine.ingest("old memory")
    time.sleep(0.2)
    engine.ingest("new memory")
    results = engine.query("memory", top_k=3)
    texts = [r["payload"]["text"] for r in results]
    assert "new memory" in texts
    assert "old memory" not in texts


def test_recency_weighting():
    engine = SoftReasoningEngine(ttl_seconds=1.0)
    engine.ingest("hello world")
    time.sleep(0.3)
    engine.ingest("hello world again")
    results = engine.query("hello", top_k=2)
    assert results[0]["payload"]["text"] == "hello world again"


def test_async_query():
    engine = SoftReasoningEngine(ttl_seconds=0.1)
    engine.ingest("hello async")
    out = asyncio.run(engine.aquery("hello", top_k=1))
    assert out and out[0]["payload"]["text"] == "hello async"
