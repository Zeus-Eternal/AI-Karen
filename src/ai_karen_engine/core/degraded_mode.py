from __future__ import annotations

"""Helper-driven degraded mode pipeline."""

import logging
from typing import Any, Dict

from ai_karen_engine.clients.embedding_manager import EmbeddingManager
from ai_karen_engine.clients.nlp_service import NLPService
from ai_karen_engine.core.response_envelope import build_response_envelope

logger = logging.getLogger(__name__)


class TinyLlamaHelper:
    """Very small helper placeholder for TinyLlama generation."""

    def generate_scaffold(self, text: str, max_tokens: int = 100) -> str:
        return text[:max_tokens]


def generate_degraded_mode_response(user_input: str, **_kwargs: Any) -> Dict[str, Any]:
    """Generate a response using helper models only."""
    tiny = TinyLlamaHelper()
    emb = EmbeddingManager()
    nlp = NLPService()

    scaffold = tiny.generate_scaffold(user_input)
    # Simple intent and sentiment placeholders using embeddings
    intent = "general"
    sentiment = "neutral"
    try:
        _ = emb.get_embeddings(user_input)
    except Exception as exc:  # pragma: no cover - defensive
        logger.debug("Embedding failed in degraded mode: %s", exc)
    entities = nlp.extract_entities(user_input)

    combined = (
        f"{scaffold}\nIntent: {intent}; Sentiment: {sentiment}; Entities: {entities}"
    )
    meta = {
        "annotations": ["Degraded Mode"],
        "confidence": 0.6,
        "provider": "HelpersOnly",
    }
    return build_response_envelope(combined, "HelpersOnly", "helpers", metadata=meta)
