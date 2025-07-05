from ..src.ai_karen_engine.clients.embedding.embedding_client import get_embedding


def test_get_embedding_byte_and_default():
    default_vec = get_embedding("hello")
    byte_vec = get_embedding("hello", model_type="byte")
    assert len(default_vec) == len(byte_vec)

