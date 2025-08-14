from __future__ import annotations

"""Client library exports."""

from ai_karen_engine.clients.embedding_manager import EmbeddingManager
from ai_karen_engine.clients.extension_api_client import ExtensionAPIClient
from ai_karen_engine.clients.nlp_service import NLPService

__all__ = ["ExtensionAPIClient", "EmbeddingManager", "NLPService"]
