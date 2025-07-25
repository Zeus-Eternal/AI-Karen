"""Embedding manager providing semantic text embeddings using DistilBERT."""

from __future__ import annotations

import hashlib
import logging
import os
import time
from typing import List, Optional
import numpy as np

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SentenceTransformer = None
    SENTENCE_TRANSFORMERS_AVAILABLE = False

logger = logging.getLogger(__name__)

_METRICS = {}

def record_metric(name: str, value: float) -> None:
    _METRICS.setdefault(name, []).append(value)


class EmbeddingManager:
    """Return semantic embeddings using DistilBERT via sentence-transformers."""

    def __init__(self, model_name: Optional[str] = None, dim: int = 768) -> None:
        self.dim = dim
        
        # Get model name from configuration or fallback to environment/default
        if model_name:
            self.model_name = model_name
        else:
            try:
                from .config_manager import get_config
                config = get_config()
                self.model_name = config.default_embedding_model
            except Exception:
                # Fallback to environment variable or default
                self.model_name = os.getenv(
                    "KARI_EMBED_MODEL", 
                    "sentence-transformers/distilbert-base-nli-stsb-mean-tokens"
                )
        
        self.model: Optional[SentenceTransformer] = None
        self.model_loaded = "hashlib"
        self.fallback_dim = 8  # Smaller dimension for hashlib fallback

    def embed(self, text: str) -> List[float]:
        """Fallback: Embed text using deterministic hashing (only used if sentence-transformers fails)."""
        start = time.time()
        h = hashlib.sha256(text.encode("utf-8")).digest()
        vector = [b / 255 for b in h[:self.fallback_dim]]
        # Pad to expected dimension if needed
        while len(vector) < self.dim:
            vector.extend([0.0] * min(self.fallback_dim, self.dim - len(vector)))
        vector = vector[:self.dim]  # Truncate if too long
        record_metric("embedding_time_seconds", time.time() - start)
        logger.warning("[EmbeddingManager] Using hashlib fallback embeddings - semantic similarity will be poor")
        return vector

    async def initialize(self) -> None:
        """Load sentence-transformers model."""
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            logger.error("[EmbeddingManager] sentence-transformers not installed; using hashlib fallback")
            logger.error("[EmbeddingManager] Install with: pip install sentence-transformers")
            return

        try:
            logger.info(f"[EmbeddingManager] Loading model: {self.model_name}")
            # Load synchronously but wrap for async startup
            self.model = SentenceTransformer(self.model_name)
            self.model_loaded = self.model_name
            
            # Test the model with a sample text to ensure it works
            test_embedding = self.model.encode("test", convert_to_numpy=True)
            self.dim = len(test_embedding)
            
            logger.info(f"[EmbeddingManager] Successfully loaded {self.model_name} (dim={self.dim})")
            
        except Exception as exc:
            logger.error(f"[EmbeddingManager] Failed to load {self.model_name}: {exc}")
            logger.error("[EmbeddingManager] Falling back to hashlib embeddings")
            self.model = None
            self.model_loaded = "hashlib"
    
    async def get_embedding(self, text: str) -> List[float]:
        """Return a semantic embedding for the given text."""
        if not text or not text.strip():
            return [0.0] * self.dim
            
        start = time.time()
        
        if self.model is not None:
            try:
                # Use sentence-transformers for proper semantic embeddings
                vector = self.model.encode(text, convert_to_numpy=True)
                embedding = vector.tolist()
                
                record_metric("embedding_time_seconds", time.time() - start)
                return embedding
                
            except Exception as exc:
                logger.error(f"[EmbeddingManager] Sentence-transformers embedding failed: {exc}")
                # Fall through to hashlib fallback
        
        # Fallback to hashlib if sentence-transformers failed
        return self.embed(text)
    
    def get_model_info(self) -> dict:
        """Get information about the loaded model."""
        return {
            "model_name": self.model_name,
            "model_loaded": self.model_loaded,
            "dimension": self.dim,
            "sentence_transformers_available": SENTENCE_TRANSFORMERS_AVAILABLE,
            "using_fallback": self.model is None
        }
