"""
Production-ready spaCy service with fallback mechanisms and monitoring.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import os
import time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from cachetools import TTLCache
import threading

try:
    from .nlp_config import SpacyConfig
except ImportError:
    from nlp_config import SpacyConfig

logger = logging.getLogger(__name__)

# Optional dependencies with graceful fallback
try:
    import spacy
    from spacy.cli import download
    SPACY_AVAILABLE = True
except ImportError:
    spacy = None
    download = None
    SPACY_AVAILABLE = False
    logger.warning("spaCy not available, fallback mode will be used")


@dataclass
class ParsedMessage:
    """Structured representation of parsed message."""
    
    tokens: List[str]
    lemmas: List[str]
    entities: List[Tuple[str, str]]  # (text, label)
    pos_tags: List[Tuple[str, str]]  # (token, pos)
    noun_phrases: List[str]
    sentiment: Optional[float] = None
    language: str = "en"
    processing_time: float = 0.0
    used_fallback: bool = False


@dataclass
class SpacyHealthStatus:
    """Health status for spaCy service."""
    
    is_healthy: bool
    model_loaded: bool
    fallback_mode: bool
    cache_size: int
    cache_hit_rate: float
    avg_processing_time: float
    error_count: int
    last_error: Optional[str] = None


class SpacyService:
    """Production-ready spaCy service with fallback and monitoring."""
    
    def __init__(self, config: Optional[SpacyConfig] = None):
        self.config = config or SpacyConfig()
        self.nlp = None
        self.fallback_mode = False
        self.cache = TTLCache(maxsize=self.config.cache_size, ttl=self.config.cache_ttl)
        self.lock = threading.RLock()
        
        # Monitoring metrics
        self._cache_hits = 0
        self._cache_misses = 0
        self._processing_times = []
        self._error_count = 0
        self._last_error = None
        
        # Initialize service
        self._initialize()
    
    def _initialize(self):
        """Initialize spaCy service with model loading and fallback setup."""
        if not SPACY_AVAILABLE:
            logger.warning("spaCy not available, using fallback mode")
            self.fallback_mode = True
            return
        
        try:
            self.nlp = self._load_model()
            if self.nlp is None:
                self.fallback_mode = True
            else:
                logger.info(f"spaCy service initialized with model: {self.config.model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize spaCy service: {e}")
            self._last_error = str(e)
            self._error_count += 1
            if self.config.enable_fallback:
                self.fallback_mode = True
                logger.info("Enabled fallback mode due to initialization failure")
            else:
                raise
    
    def _load_model(self):
        """Load spaCy model with automatic download if needed."""
        try:
            # Try to load the model
            nlp = spacy.load(
                self.config.model_name,
                disable=self.config.disabled_components
            )
            return nlp
        except OSError as e:
            if self.config.download_missing:
                logger.info(f"Model {self.config.model_name} not found, attempting download...")
                try:
                    download(self.config.model_name)
                    nlp = spacy.load(
                        self.config.model_name,
                        disable=self.config.disabled_components
                    )
                    logger.info(f"Successfully downloaded and loaded {self.config.model_name}")
                    return nlp
                except Exception as download_error:
                    logger.error(f"Failed to download model: {download_error}")
                    # Try fallback to en_core_web_sm
                    if self.config.model_name != "en_core_web_sm":
                        logger.info("Attempting fallback to en_core_web_sm")
                        try:
                            nlp = spacy.load("en_core_web_sm", disable=self.config.disabled_components)
                            logger.info("Successfully loaded fallback model en_core_web_sm")
                            return nlp
                        except Exception:
                            logger.error("Fallback model also failed to load")
            
            logger.error(f"Could not load spaCy model: {e}")
            return None
    
    async def parse_message(self, text: str) -> ParsedMessage:
        """Parse message with spaCy or fallback to simple parsing."""
        if not text or not text.strip():
            return ParsedMessage(
                tokens=[],
                lemmas=[],
                entities=[],
                pos_tags=[],
                noun_phrases=[],
                used_fallback=True
            )
        
        # Check cache first
        cache_key = self._get_cache_key(text)
        with self.lock:
            if cache_key in self.cache:
                self._cache_hits += 1
                return self.cache[cache_key]
            self._cache_misses += 1
        
        start_time = time.time()
        
        try:
            if self.fallback_mode or not self.nlp:
                result = await self._fallback_parse(text)
            else:
                result = await self._spacy_parse(text)
            
            processing_time = time.time() - start_time
            result.processing_time = processing_time
            
            # Update monitoring metrics
            with self.lock:
                self._processing_times.append(processing_time)
                if len(self._processing_times) > 1000:  # Keep last 1000 measurements
                    self._processing_times = self._processing_times[-1000:]
                self.cache[cache_key] = result
            
            return result
            
        except Exception as e:
            logger.error(f"Message parsing failed: {e}")
            self._error_count += 1
            self._last_error = str(e)
            
            # Fallback on error
            if not self.fallback_mode and self.config.enable_fallback:
                logger.info("Falling back to simple parsing due to error")
                result = await self._fallback_parse(text)
                result.processing_time = time.time() - start_time
                return result
            
            raise
    
    async def _spacy_parse(self, text: str) -> ParsedMessage:
        """Parse text using spaCy."""
        # Run spaCy processing in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        doc = await loop.run_in_executor(None, self.nlp, text)
        
        return ParsedMessage(
            tokens=[token.text for token in doc],
            lemmas=[token.lemma_ for token in doc],
            entities=[(ent.text, ent.label_) for ent in doc.ents],
            pos_tags=[(token.text, token.pos_) for token in doc],
            noun_phrases=[chunk.text for chunk in doc.noun_chunks],
            language=doc.lang_,
            used_fallback=False
        )
    
    async def _fallback_parse(self, text: str) -> ParsedMessage:
        """Simple fallback parsing when spaCy is unavailable."""
        # Basic tokenization
        tokens = text.split()
        
        # Simple sentence splitting for noun phrases
        sentences = text.replace('!', '.').replace('?', '.').split('.')
        noun_phrases = [s.strip() for s in sentences if s.strip()]
        
        return ParsedMessage(
            tokens=tokens,
            lemmas=tokens,  # No lemmatization in fallback
            entities=[],    # No entity recognition in fallback
            pos_tags=[],    # No POS tagging in fallback
            noun_phrases=noun_phrases,
            used_fallback=True
        )
    
    def _get_cache_key(self, text: str) -> str:
        """Generate cache key for text."""
        return f"spacy:{hashlib.md5(text.encode()).hexdigest()}"
    
    def get_health_status(self) -> SpacyHealthStatus:
        """Get current health status of the service."""
        with self.lock:
            cache_total = self._cache_hits + self._cache_misses
            cache_hit_rate = self._cache_hits / cache_total if cache_total > 0 else 0.0
            
            avg_processing_time = (
                sum(self._processing_times) / len(self._processing_times)
                if self._processing_times else 0.0
            )
            
            return SpacyHealthStatus(
                is_healthy=not self.fallback_mode or self.config.enable_fallback,
                model_loaded=self.nlp is not None,
                fallback_mode=self.fallback_mode,
                cache_size=len(self.cache),
                cache_hit_rate=cache_hit_rate,
                avg_processing_time=avg_processing_time,
                error_count=self._error_count,
                last_error=self._last_error
            )
    
    def clear_cache(self):
        """Clear the parsing cache."""
        with self.lock:
            self.cache.clear()
            logger.info("spaCy service cache cleared")
    
    def reset_metrics(self):
        """Reset monitoring metrics."""
        with self.lock:
            self._cache_hits = 0
            self._cache_misses = 0
            self._processing_times = []
            self._error_count = 0
            self._last_error = None
            logger.info("spaCy service metrics reset")
    
    async def reload_model(self, new_model_name: Optional[str] = None):
        """Reload spaCy model, optionally with a new model name."""
        if new_model_name:
            self.config.model_name = new_model_name
        
        logger.info(f"Reloading spaCy model: {self.config.model_name}")
        
        try:
            old_nlp = self.nlp
            self.nlp = self._load_model()
            
            if self.nlp is not None:
                self.fallback_mode = False
                logger.info("spaCy model reloaded successfully")
                # Clear cache since model changed
                self.clear_cache()
            else:
                # Restore old model if reload failed
                self.nlp = old_nlp
                if self.config.enable_fallback:
                    self.fallback_mode = True
                    logger.warning("Model reload failed, using fallback mode")
                else:
                    raise RuntimeError("Model reload failed and fallback disabled")
                    
        except Exception as e:
            logger.error(f"Model reload failed: {e}")
            self._error_count += 1
            self._last_error = str(e)
            raise