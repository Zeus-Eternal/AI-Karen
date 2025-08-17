"""
Production-ready DistilBERT service with fallback mechanisms and monitoring.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import time
from typing import List, Optional, Union, Any
from dataclasses import dataclass
from cachetools import TTLCache
import threading
import numpy as np

try:
    from ai_karen_engine.services.nlp_config import DistilBertConfig
except ImportError:
    from nlp_config import DistilBertConfig

logger = logging.getLogger(__name__)

# Optional dependencies with graceful fallback
try:
    import torch
    from transformers import AutoTokenizer, AutoModel
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    torch = None
    AutoTokenizer = None
    AutoModel = None
    TRANSFORMERS_AVAILABLE = False
    logger.warning("Transformers not available, fallback mode will be used")


@dataclass
class EmbeddingResult:
    """Result of embedding generation."""
    
    embeddings: List[float]
    processing_time: float
    used_fallback: bool
    model_name: Optional[str] = None
    input_length: int = 0


@dataclass
class DistilBertHealthStatus:
    """Health status for DistilBERT service."""
    
    is_healthy: bool
    model_loaded: bool
    fallback_mode: bool
    device: str
    cache_size: int
    cache_hit_rate: float
    avg_processing_time: float
    error_count: int
    last_error: Optional[str] = None


class DistilBertService:
    """Production-ready DistilBERT service with fallback and monitoring."""
    
    def __init__(self, config: Optional[DistilBertConfig] = None):
        self.config = config or DistilBertConfig()
        self.tokenizer = None
        self.model = None
        self.device = None
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
        """Initialize DistilBERT service with model loading and fallback setup."""
        if not TRANSFORMERS_AVAILABLE:
            logger.warning("Transformers not available, using fallback mode")
            self.fallback_mode = True
            return
        
        try:
            self.device = self._setup_device()
            self.tokenizer, self.model = self._load_model()
            
            if self.tokenizer is None or self.model is None:
                self.fallback_mode = True
            else:
                logger.info(f"DistilBERT service initialized with model: {self.config.model_name}")
                logger.info(f"Using device: {self.device}")
                
        except Exception as e:
            logger.error(f"Failed to initialize DistilBERT service: {e}")
            self._last_error = str(e)
            self._error_count += 1
            if self.config.enable_fallback:
                self.fallback_mode = True
                logger.info("Enabled fallback mode due to initialization failure")
            else:
                raise
    
    def _setup_device(self):
        """Setup compute device (GPU/CPU)."""
        if self.config.enable_gpu:
            if torch.cuda.is_available():
                device = torch.device("cuda")
                logger.info(f"Using GPU: {torch.cuda.get_device_name()}")
            else:
                device = torch.device("cpu")
                logger.info("CUDA unavailable, using CPU for inference")
        else:
            device = torch.device("cpu")
            logger.info("Using CPU for inference")
        return device
    
    def _load_model(self):
        """Load DistilBERT model and tokenizer."""
        try:
            tokenizer = AutoTokenizer.from_pretrained(self.config.model_name)
            model = AutoModel.from_pretrained(self.config.model_name)
            
            # Move model to device and set to eval mode
            model.to(self.device)
            model.eval()
            
            # Disable gradients for inference
            for param in model.parameters():
                param.requires_grad = False
            
            return tokenizer, model
            
        except Exception as e:
            logger.error(f"Failed to load DistilBERT model: {e}")
            return None, None
    
    async def get_embeddings(
        self, 
        texts: Union[str, List[str]], 
        normalize: bool = True
    ) -> Union[List[float], List[List[float]]]:
        """Generate embeddings for text(s) with fallback support."""
        if isinstance(texts, str):
            texts = [texts]
            single_text = True
        else:
            single_text = False
        
        # Filter empty texts
        valid_texts = [text for text in texts if text and text.strip()]
        if not valid_texts:
            empty_embedding = [0.0] * self.config.embedding_dimension
            return empty_embedding if single_text else [empty_embedding] * len(texts)
        
        embeddings = []
        for text in texts:
            if not text or not text.strip():
                embeddings.append([0.0] * self.config.embedding_dimension)
                continue
            
            # Check cache first
            cache_key = self._get_cache_key(text)
            with self.lock:
                if cache_key in self.cache:
                    self._cache_hits += 1
                    cached_result = self.cache[cache_key]
                    embeddings.append(cached_result.embeddings)
                    continue
                self._cache_misses += 1
            
            start_time = time.time()
            
            try:
                if self.fallback_mode or not self.model:
                    embedding = await self._fallback_embedding(text)
                    used_fallback = True
                else:
                    embedding = await self._generate_embedding(text)
                    used_fallback = False
                
                if normalize and not used_fallback:
                    embedding = self._normalize_embedding(embedding)
                
                processing_time = time.time() - start_time
                
                # Cache result
                result = EmbeddingResult(
                    embeddings=embedding,
                    processing_time=processing_time,
                    used_fallback=used_fallback,
                    model_name=self.config.model_name if not used_fallback else "fallback",
                    input_length=len(text)
                )
                
                with self.lock:
                    self._processing_times.append(processing_time)
                    if len(self._processing_times) > 1000:
                        self._processing_times = self._processing_times[-1000:]
                    self.cache[cache_key] = result
                
                embeddings.append(embedding)
                
            except Exception as e:
                logger.error(f"Embedding generation failed for text: {e}")
                self._error_count += 1
                self._last_error = str(e)
                
                # Fallback on error
                if not self.fallback_mode and self.config.enable_fallback:
                    logger.info("Falling back to hash-based embedding due to error")
                    embedding = await self._fallback_embedding(text)
                    embeddings.append(embedding)
                else:
                    raise
        
        return embeddings[0] if single_text else embeddings
    
    async def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding using DistilBERT model."""
        # Tokenize input
        inputs = self.tokenizer(
            text,
            truncation=True,
            padding=True,
            return_tensors="pt",
            max_length=self.config.max_length
        )
        
        # Move inputs to device
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        # Run inference in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        outputs = await loop.run_in_executor(None, self._model_forward, inputs)
        
        # Apply pooling strategy
        if self.config.pooling_strategy == "mean":
            # Mean pooling over sequence length
            embeddings = outputs.last_hidden_state.mean(dim=1).squeeze()
        elif self.config.pooling_strategy == "cls":
            # Use [CLS] token embedding
            embeddings = outputs.last_hidden_state[:, 0, :].squeeze()
        elif self.config.pooling_strategy == "max":
            # Max pooling over sequence length
            embeddings = outputs.last_hidden_state.max(dim=1)[0].squeeze()
        else:
            # Default to mean pooling
            embeddings = outputs.last_hidden_state.mean(dim=1).squeeze()
        
        # Convert to list and move to CPU
        return embeddings.cpu().numpy().tolist()
    
    def _model_forward(self, inputs):
        """Forward pass through the model (runs in thread pool)."""
        if torch is not None:
            with torch.no_grad():
                return self.model(**inputs)
        else:
            return self.model(**inputs)
    
    async def _fallback_embedding(self, text: str) -> List[float]:
        """Generate hash-based fallback embedding when DistilBERT is unavailable."""
        # Use multiple hash functions for better distribution
        hash_functions = [
            lambda x: hashlib.md5(x.encode()).digest(),
            lambda x: hashlib.sha1(x.encode()).digest(),
            lambda x: hashlib.sha256(x.encode()).digest(),
        ]
        
        embedding = []
        
        for hash_func in hash_functions:
            hash_bytes = hash_func(text)
            
            # Convert bytes to float values
            for i in range(0, len(hash_bytes), 4):
                chunk = hash_bytes[i:i+4]
                if len(chunk) == 4:
                    # Convert 4 bytes to signed integer, then normalize
                    value = int.from_bytes(chunk, byteorder='big', signed=True)
                    normalized_value = float(value) / (2**31)  # Normalize to [-1, 1]
                    embedding.append(normalized_value)
        
        # Pad or truncate to target dimension
        target_dim = self.config.embedding_dimension
        while len(embedding) < target_dim:
            # Repeat pattern if needed
            remaining = target_dim - len(embedding)
            to_add = min(remaining, len(embedding))
            embedding.extend(embedding[:to_add])
        
        return embedding[:target_dim]
    
    def _normalize_embedding(self, embedding: List[float]) -> List[float]:
        """Normalize embedding to unit length."""
        embedding_array = np.array(embedding)
        norm = np.linalg.norm(embedding_array)
        if norm > 0:
            return (embedding_array / norm).tolist()
        return embedding
    
    def _get_cache_key(self, text: str) -> str:
        """Generate cache key for text."""
        # Include model name and config in cache key
        config_hash = hashlib.md5(
            f"{self.config.model_name}_{self.config.pooling_strategy}_{self.config.max_length}".encode()
        ).hexdigest()[:8]
        text_hash = hashlib.md5(text.encode()).hexdigest()
        return f"distilbert:{config_hash}:{text_hash}"
    
    def get_health_status(self) -> DistilBertHealthStatus:
        """Get current health status of the service."""
        with self.lock:
            cache_total = self._cache_hits + self._cache_misses
            cache_hit_rate = self._cache_hits / cache_total if cache_total > 0 else 0.0
            
            avg_processing_time = (
                sum(self._processing_times) / len(self._processing_times)
                if self._processing_times else 0.0
            )
            
            return DistilBertHealthStatus(
                is_healthy=not self.fallback_mode or self.config.enable_fallback,
                model_loaded=self.model is not None,
                fallback_mode=self.fallback_mode,
                device=str(self.device) if self.device else "unknown",
                cache_size=len(self.cache),
                cache_hit_rate=cache_hit_rate,
                avg_processing_time=avg_processing_time,
                error_count=self._error_count,
                last_error=self._last_error
            )
    
    def clear_cache(self):
        """Clear the embedding cache."""
        with self.lock:
            self.cache.clear()
            logger.info("DistilBERT service cache cleared")
    
    def reset_metrics(self):
        """Reset monitoring metrics."""
        with self.lock:
            self._cache_hits = 0
            self._cache_misses = 0
            self._processing_times = []
            self._error_count = 0
            self._last_error = None
            logger.info("DistilBERT service metrics reset")
    
    async def reload_model(self, new_model_name: Optional[str] = None):
        """Reload DistilBERT model, optionally with a new model name."""
        if new_model_name:
            self.config.model_name = new_model_name
        
        logger.info(f"Reloading DistilBERT model: {self.config.model_name}")
        
        try:
            old_tokenizer, old_model = self.tokenizer, self.model
            self.tokenizer, self.model = self._load_model()
            
            if self.tokenizer is not None and self.model is not None:
                self.fallback_mode = False
                logger.info("DistilBERT model reloaded successfully")
                # Clear cache since model changed
                self.clear_cache()
            else:
                # Restore old model if reload failed
                self.tokenizer, self.model = old_tokenizer, old_model
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
    
    async def batch_embeddings(
        self, 
        texts: List[str], 
        batch_size: Optional[int] = None
    ) -> List[List[float]]:
        """Generate embeddings for multiple texts in batches for efficiency."""
        if not texts:
            return []
        
        batch_size = batch_size or self.config.batch_size
        embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_embeddings = await self.get_embeddings(batch)
            embeddings.extend(batch_embeddings)
        
        return embeddings