"""Client utilities for model and embedding access."""

from ai_karen_engine.clients.slm_pool import SLMPool
from ai_karen_engine.clients.embedding import get_embedding

__all__ = ["SLMPool", "get_embedding"]
