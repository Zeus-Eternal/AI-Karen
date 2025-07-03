from __future__ import annotations

from typing import Any

from ai_karen_engine.integrations.llm_registry import registry


def route_input(model: Any, text: str) -> Any:
    """Encode ``text`` according to model metadata."""
    tokenizer_type = getattr(model, "tokenizer_type", "bpe")
    if tokenizer_type == "byte":
        return text.encode("utf-8")
    if hasattr(model, "tokenizer") and model.tokenizer is not None:
        return model.tokenizer.encode(text)
    return text.split()
