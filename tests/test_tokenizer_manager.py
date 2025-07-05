from ..src.ai_karen_engine.core.tokenizer_manager import TokenizerManager


def test_byte_encoding():
    manager = TokenizerManager({"tokenizer_type": "byte"})
    assert manager.encode("hi") == b"hi"


def test_bpe_fallback():
    manager = TokenizerManager({"tokenizer_type": "bpe", "model_name": "dummy"})
    tokens = manager.encode("hello world")
    assert tokens
