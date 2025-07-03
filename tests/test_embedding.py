from src.core.embedding_manager import EmbeddingManager, _METRICS


def test_embed_shape():
    manager = EmbeddingManager()
    vec = manager.embed("hello")
    assert len(vec) == manager.dim
    assert "embedding_time_seconds" in _METRICS
