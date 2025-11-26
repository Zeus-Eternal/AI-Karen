"""
Unified NLP service manager for spaCy and DistilBERT integration.
"""

from __future__ import annotations

import asyncio
import logging
import os
import threading
from typing import Dict, Any, Optional, List, Union

from src.services.spacy_service import SpacyService, ParsedMessage
from src.services.distilbert_service import DistilBertService
from src.services.small_language_model_service import SmallLanguageModelService, ScaffoldResult, OutlineResult, SummaryResult
from src.services.nlp_health_monitor import NLPHealthMonitor, NLPSystemHealth
from src.services.nlp_config import NLPConfig, SpacyConfig, DistilBertConfig, SmallLanguageModelConfig
from ai_karen_engine.config.config_manager import config_manager

logger = logging.getLogger(__name__)


class NLPServiceManager:
    """Unified manager for NLP services with configuration and health monitoring."""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.config = self._load_config()

        enable_heavy_helpers = (
            os.getenv("KARI_ENABLE_DEGRADED_HELPERS", "").lower()
            in {"1", "true", "yes"}
        )
        if not enable_heavy_helpers:
            os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
            os.environ.setdefault("HF_HUB_OFFLINE", "1")
            logger.info(
                "DistilBERT will run in offline fallback mode. Set "
                "KARI_ENABLE_DEGRADED_HELPERS=1 to allow full model loading."
            )

        # Initialize services based on configuration
        self.spacy_service = SpacyService(self.config.spacy) if self.config.spacy.enabled else None
        self.distilbert_service = DistilBertService(self.config.distilbert) if self.config.distilbert.enabled else None
        self.small_language_model_service = SmallLanguageModelService(self.config.small_language_model) if self.config.small_language_model.enabled else None
        
        # Initialize health monitor with available services
        self.health_monitor = NLPHealthMonitor(
            self.spacy_service,
            self.distilbert_service,
            self.config
        )
        
        self._initialized = True
        logger.info("NLP Service Manager initialized")
    
    def _load_config(self) -> NLPConfig:
        """Load NLP configuration from config manager."""
        try:
            # Get NLP config from main config
            nlp_config_dict = config_manager.get_config_value("nlp", default={})
            
            # Create config objects with defaults
            spacy_config = SpacyConfig(**nlp_config_dict.get("spacy", {}))
            distilbert_config = DistilBertConfig(**nlp_config_dict.get("distilbert", {}))
            small_language_model_config = SmallLanguageModelConfig(**nlp_config_dict.get("small_language_model", {}))
            
            config = NLPConfig(
                spacy=spacy_config,
                distilbert=distilbert_config,
                small_language_model=small_language_model_config,
                **{k: v for k, v in nlp_config_dict.items() if k not in ["spacy", "distilbert", "small_language_model"]}
            )
            
            logger.info("NLP configuration loaded successfully")
            return config
            
        except Exception as e:
            logger.warning(f"Failed to load NLP config: {e}, using defaults")
            return NLPConfig()
    
    async def initialize(self):
        """Initialize all NLP services and start monitoring."""
        try:
            # Start health monitoring if enabled
            if self.config.enable_monitoring:
                await self.health_monitor.start_monitoring()
                logger.info("NLP health monitoring started")
            
            # Run initial health check
            health_status = await self.health_monitor.check_health()
            if health_status.is_healthy:
                logger.info("NLP services initialized successfully")
            else:
                logger.warning(f"NLP services initialized with issues: {health_status.alerts}")
            
        except Exception as e:
            logger.error(f"Failed to initialize NLP services: {e}")
            raise
    
    async def shutdown(self):
        """Shutdown all NLP services."""
        try:
            await self.health_monitor.stop_monitoring()
            logger.info("NLP Service Manager shutdown completed")
        except Exception as e:
            logger.error(f"Error during NLP service shutdown: {e}")
    
    # spaCy service methods
    async def parse_message(self, text: str) -> ParsedMessage:
        """Parse message using spaCy service."""
        return await self.spacy_service.parse_message(text)
    
    # DistilBERT service methods
    async def get_embeddings(
        self,
        texts: Union[str, List[str]],
        normalize: bool = True
    ) -> Union[List[float], List[List[float]]]:
        """Generate embeddings using DistilBERT service."""
        return await self.distilbert_service.get_embeddings(texts, normalize)
    
    async def batch_embeddings(
        self,
        texts: List[str],
        batch_size: Optional[int] = None
    ) -> List[List[float]]:
        """Generate embeddings for multiple texts in batches."""
        return await self.distilbert_service.batch_embeddings(texts, batch_size)
    
    # TinyLlama service methods
    async def generate_scaffold(
        self,
        text: str,
        scaffold_type: str = "reasoning",
        max_tokens: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> ScaffoldResult:
        """Generate scaffolding using Small Language Model service."""
        return await self.small_language_model_service.generate_scaffold(
            text, scaffold_type, max_tokens, context
        )
    
    async def generate_outline(
        self,
        text: str,
        outline_style: str = "bullet",
        max_points: int = 5
    ) -> OutlineResult:
        """Generate outline using Small Language Model service."""
        return await self.small_language_model_service.generate_outline(
            text, outline_style, max_points
        )
    
    async def summarize_context(
        self,
        text: str,
        summary_type: str = "concise",
        max_tokens: Optional[int] = None
    ) -> SummaryResult:
        """Summarize context using Small Language Model service."""
        return await self.small_language_model_service.summarize_context(
            text, summary_type, max_tokens
        )
    
    async def generate_short_fill(
        self,
        context: str,
        prompt: str,
        max_tokens: Optional[int] = None,
        fill_type: str = "continuation"
    ) -> ScaffoldResult:
        """Generate short fill using Small Language Model service."""
        return await self.small_language_model_service.generate_short_fill(
            context, prompt, max_tokens, fill_type
        )
    
    async def augment_response(
        self,
        user_message: str,
        main_response: str,
        augmentation_type: str = "enhancement"
    ) -> Dict[str, Any]:
        """Augment response using Small Language Model service."""
        return await self.small_language_model_service.augment_response(
            user_message, main_response, augmentation_type
        )
    
    # Combined NLP operations
    async def process_message_full(self, text: str) -> Dict[str, Any]:
        """Process message with both spaCy parsing and DistilBERT embeddings."""
        try:
            # Run both operations concurrently
            parse_task = self.parse_message(text)
            embedding_task = self.get_embeddings(text)
            
            parsed_message, embeddings = await asyncio.gather(parse_task, embedding_task)
            
            return {
                "text": text,
                "parsed": {
                    "tokens": parsed_message.tokens,
                    "lemmas": parsed_message.lemmas,
                    "entities": parsed_message.entities,
                    "pos_tags": parsed_message.pos_tags,
                    "noun_phrases": parsed_message.noun_phrases,
                    "sentences": parsed_message.sentences,
                    "dependencies": parsed_message.dependencies,
                    "language": parsed_message.language,
                    "processing_time": parsed_message.processing_time,
                    "used_fallback": parsed_message.used_fallback
                },
                "embeddings": embeddings,
                "embedding_dimension": len(embeddings) if embeddings else 0
            }
            
        except Exception as e:
            logger.error(f"Full message processing failed: {e}")
            raise
    
    async def extract_entities_with_embeddings(self, text: str) -> List[Dict[str, Any]]:
        """Extract entities and generate embeddings for each entity."""
        parsed_message = await self.parse_message(text)
        
        if not parsed_message.entities:
            return []
        
        # Extract entity texts
        entity_texts = [entity[0] for entity in parsed_message.entities]
        
        # Generate embeddings for all entities
        entity_embeddings = await self.batch_embeddings(entity_texts)
        
        # Combine entities with their embeddings
        entities_with_embeddings = []
        for (entity_text, entity_label), embedding in zip(parsed_message.entities, entity_embeddings):
            entities_with_embeddings.append({
                "text": entity_text,
                "label": entity_label,
                "embedding": embedding
            })
        
        return entities_with_embeddings
    
    async def semantic_similarity(self, text1: str, text2: str) -> float:
        """Calculate semantic similarity between two texts using embeddings."""
        embeddings = await self.get_embeddings([text1, text2])
        
        if len(embeddings) != 2:
            raise ValueError("Failed to generate embeddings for both texts")
        
        # Calculate cosine similarity
        import numpy as np
        
        vec1 = np.array(embeddings[0])
        vec2 = np.array(embeddings[1])
        
        # Cosine similarity
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        similarity = dot_product / (norm1 * norm2)
        return float(similarity)
    
    # Health and monitoring methods
    async def get_health_status(self) -> NLPSystemHealth:
        """Get current health status of all NLP services."""
        return await self.health_monitor.check_health()
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get health summary."""
        return self.health_monitor.get_health_summary()
    
    def get_health_trends(self, hours: int = 24) -> Dict[str, Any]:
        """Get health trends over specified time period."""
        return self.health_monitor.get_health_trends(hours)
    
    async def run_diagnostic(self) -> Dict[str, Any]:
        """Run comprehensive diagnostic tests."""
        return await self.health_monitor.run_diagnostic()
    
    # Configuration methods
    def configure_services(
        self,
        enable_spacy: bool = True,
        enable_distilbert: bool = True,
        enable_small_language_model: bool = True
    ):
        """Configure which NLP services should be enabled.
        
        Args:
            enable_spacy: Whether to enable spaCy service
            enable_distilbert: Whether to enable DistilBERT service
            enable_small_language_model: Whether to enable Small Language Model service
        """
        # Update configuration
        self.config.spacy.enabled = enable_spacy
        self.config.distilbert.enabled = enable_distilbert
        self.config.small_language_model.enabled = enable_small_language_model
        
        # Log the configuration
        logger.info(f"NLP services configured: spaCy={enable_spacy}, DistilBERT={enable_distilbert}, Small Language Model={enable_small_language_model}")
    
    def get_config(self) -> NLPConfig:
        """Get current NLP configuration."""
        return self.config
    
    async def update_config(self, new_config: Dict[str, Any]):
        """Update NLP configuration."""
        try:
            # Update main config
            from ai_karen_engine.config.config_manager import save_config
            current_config = config_manager.get_config()
            current_config["nlp"] = new_config
            save_config(current_config)
            
            # Reload configuration
            self.config = self._load_config()
            
            # Reload services with new config
            await self.spacy_service.reload_model()
            await self.distilbert_service.reload_model()
            
            logger.info("NLP configuration updated successfully")
            
        except Exception as e:
            logger.error(f"Failed to update NLP configuration: {e}")
            raise
    
    # Cache management
    def clear_all_caches(self):
        """Clear all service caches."""
        self.spacy_service.clear_cache()
        self.distilbert_service.clear_cache()
        self.small_language_model_service.clear_cache()
        logger.info("All NLP service caches cleared")
    
    def reset_all_metrics(self):
        """Reset all service metrics."""
        self.spacy_service.reset_metrics()
        self.distilbert_service.reset_metrics()
        self.small_language_model_service.reset_metrics()
        logger.info("All NLP service metrics reset")
    
    # Utility methods
    def is_ready(self) -> bool:
        """Check if NLP services are ready for use."""
        spacy_status = self.spacy_service.get_health_status()
        distilbert_status = self.distilbert_service.get_health_status()
        small_language_model_status = self.small_language_model_service.get_health_status()
        
        return (spacy_status.is_healthy and distilbert_status.is_healthy and small_language_model_status.is_healthy) or \
               (spacy_status.fallback_mode and distilbert_status.fallback_mode and small_language_model_status.fallback_mode)
    
    def get_service_info(self) -> Dict[str, Any]:
        """Get information about all NLP services."""
        spacy_status = self.spacy_service.get_health_status()
        distilbert_status = self.distilbert_service.get_health_status()
        small_language_model_status = self.small_language_model_service.get_health_status()
        
        return {
            "spacy": {
                "model_name": self.config.spacy.model_name,
                "model_loaded": spacy_status.model_loaded,
                "fallback_mode": spacy_status.fallback_mode,
                "cache_size": spacy_status.cache_size,
                "disabled_components": self.config.spacy.disabled_components
            },
            "distilbert": {
                "model_name": self.config.distilbert.model_name,
                "model_loaded": distilbert_status.model_loaded,
                "fallback_mode": distilbert_status.fallback_mode,
                "device": distilbert_status.device,
                "cache_size": distilbert_status.cache_size,
                "embedding_dimension": self.config.distilbert.embedding_dimension
            },
            "small_language_model": {
                "model_name": self.config.small_language_model.model_name,
                "model_loaded": small_language_model_status.model_loaded,
                "fallback_mode": small_language_model_status.fallback_mode,
                "cache_size": small_language_model_status.cache_size,
                "max_tokens": self.config.small_language_model.max_tokens,
                "temperature": self.config.small_language_model.temperature
            },
            "monitoring_enabled": self.config.enable_monitoring,
            "ready": self.is_ready()
        }


_nlp_manager_lock = threading.RLock()
_nlp_manager_instance: Optional[NLPServiceManager] = None


def get_nlp_service_manager() -> NLPServiceManager:
    """Return the lazily-created :class:`NLPServiceManager` singleton."""

    global _nlp_manager_instance
    if _nlp_manager_instance is None:
        with _nlp_manager_lock:
            if _nlp_manager_instance is None:
                logger.info("Initializing NLPServiceManager (lazy singleton)")
                _nlp_manager_instance = NLPServiceManager()
    return _nlp_manager_instance


class _LazyNLPServiceManagerProxy:
    """Attribute proxy that lazily instantiates the underlying manager on use."""

    def _resolve(self) -> NLPServiceManager:
        return get_nlp_service_manager()

    def __getattr__(self, item):
        return getattr(self._resolve(), item)

    def __setattr__(self, key, value):
        if key.startswith("_"):
            super().__setattr__(key, value)
        else:
            setattr(self._resolve(), key, value)

    def __repr__(self) -> str:  # pragma: no cover - simple debug helper
        return f"<LazyNLPServiceManagerProxy wrapping {self._resolve()!r}>"

    def __dir__(self):  # pragma: no cover - used for developer ergonomics
        return sorted(set(dir(self._resolve())))


nlp_service_manager = _LazyNLPServiceManagerProxy()


def reset_nlp_service_manager() -> None:
    """Reset the cached manager instance (primarily for tests)."""

    global _nlp_manager_instance
    with _nlp_manager_lock:
        _nlp_manager_instance = None


__all__ = [
    "NLPServiceManager",
    "get_nlp_service_manager",
    "reset_nlp_service_manager",
    "nlp_service_manager",
]
