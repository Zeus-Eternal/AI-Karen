from ai_karen_engine.core.memory.retrieval.retrieval_router import HybridRetrievalRouter


def test_graph_query_trigger_detection():
    router = HybridRetrievalRouter()
    class Q: text = "how did this evolve" 
    assert router._is_graph_query(Q()) is True
