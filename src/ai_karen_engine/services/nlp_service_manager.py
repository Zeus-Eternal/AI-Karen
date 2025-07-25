"""
Unified NLP service manager for spaCy and DistilBERT integration.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Dict, Any, Optional, List, Union

from .spacy_service import SpacyService, ParsedMessage
from .distilbert_service import DistilBertService, EmbeddingResult
from .nlp_health_monitor import NLPHealthMonitor, NLPSystemHealth
from .nlp_config import NLPConfig, SpacyConfig, DistilBertConfig
from ..config.config_manager import config_manager

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
        self.spacy_service = SpacyService(self.config.spacy)
        self.distilbert_service = DistilBertService(self.config.distilbert)
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
            nlp_config_dict = config_manager.get_config_value("nlp", {})
            
            # Create config objects with defaults
            spacy_config = SpacyConfig(**nlp_config_dict.get("spacy", {}))
            distilbert_config = DistilBertConfig(**nlp_config_dict.get("distilbert", {}))
            
            config = NLPConfig(
                spacy=spacy_config,
                distilbert=distilbert_config,
                **{k: v for k, v in nlp_config_dict.items() if k not in ["spacy", "distilbert"]}
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
    def get_config(self) -> NLPConfig:
        """Get current NLP configuration."""
        return self.config
    
    async def update_config(self, new_config: Dict[str, Any]):
        """Update NLP configuration."""
        try:
            # Update main config
            current_config = config_manager.get_config()
            current_config["nlp"] = new_config
            config_manager.save_config(current_config)
            
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
        logger.info("All NLP service caches cleared")
    
    def reset_all_metrics(self):
        """Reset all service metrics."""
        self.spacy_service.reset_metrics()
        self.distilbert_service.reset_metrics()
        logger.info("All NLP service metrics reset")
    
    # Utility methods
    def is_ready(self) -> bool:
        """Check if NLP services are ready for use."""
        spacy_status = self.spacy_service.get_health_status()
        distilbert_status = self.distilbert_service.get_health_status()
        
        return (spacy_status.is_healthy and distilbert_status.is_healthy) or \
               (spacy_status.fallback_mode and distilbert_status.fallback_mode)
    
    def get_service_info(self) -> Dict[str, Any]:
        """Get information about all NLP services."""
        spacy_status = self.spacy_service.get_health_status()
        distilbert_status = self.distilbert_service.get_health_status()
        
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
            "monitoring_enabled": self.config.enable_monitoring,
            "ready": self.is_ready()
        }


# Global instance
nlp_service_manager = NLPServiceManager()