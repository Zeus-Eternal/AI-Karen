"""Client library exports."""

from __future__ import annotations

from ai_karen_engine.clients.embedding_manager import (  # type: ignore[import-not-found]
    EmbeddingManager,
)
from ai_karen_engine.clients.extension_api_client import (  # type: ignore[import-not-found]
    ExtensionAPIClient,
)
from ai_karen_engine.clients.nlp_service import (  # type: ignore[import-not-found]
    NLPService,
)

__all__ = ["ExtensionAPIClient", "EmbeddingManager", "NLPService"]
