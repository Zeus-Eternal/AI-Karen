import logging
import os
from pathlib import Path

from ai_karen_engine.core.embedding_manager import EmbeddingManager
from ai_karen_engine.clients.nlp.spacy_client import SpaCyClient
from ai_karen_engine.clients.nlp.basic_classifier import BasicClassifier

embedding_manager: EmbeddingManager | None = None
spacy_client: SpaCyClient | None = None
classifier: BasicClassifier | None = None

logger = logging.getLogger(__name__)

async def load_default_models() -> None:
    """Initialize default models if they haven't been loaded."""
    global embedding_manager, spacy_client, classifier

    eco_mode = os.getenv("KARI_ECO_MODE", "false").lower() in {"1", "true", "yes"}

    if embedding_manager is None:
        embedding_manager = EmbeddingManager()
        if not eco_mode:
            await embedding_manager.initialize()
        logger.info(
            "Default embedding model loaded: %s",
            embedding_manager.model_loaded,
        )

    if not eco_mode and spacy_client is None:
        try:
            spacy_client = SpaCyClient()
            logger.info(
                "SpaCy model loaded: %s",
                SpaCyClient.DEFAULT_MODEL
                if hasattr(SpaCyClient, "DEFAULT_MODEL")
                else "default",
            )
        except Exception as exc:  # pragma: no cover - runtime only
            logger.error("Failed to load spaCy model: %s", exc)
            spacy_client = None

    if not eco_mode and classifier is None:
        try:
            classifier = BasicClassifier(Path("data/default_classifier"))
            logger.info("Basic classifier ready")
        except Exception as exc:  # pragma: no cover - runtime only
            logger.error("Failed to load basic classifier: %s", exc)
            classifier = None


def get_embedding_manager() -> EmbeddingManager:
    if embedding_manager is None:
        raise RuntimeError("Default models not loaded")
    return embedding_manager


def get_spacy_client() -> SpaCyClient | None:
    return spacy_client


def get_classifier() -> BasicClassifier | None:
    return classifier
