"""
Production-ready DistilBERT service with fallback mechanisms and monitoring.
"""

from __future__ import annotations

import asyncio
import importlib
import os
import hashlib
import logging
import time
from typing import List, Optional, Union, Any
from dataclasses import dataclass
from cachetools import TTLCache
import threading
import numpy as np

try:
    from src.services.nlp_config import DistilBertConfig
except ImportError:
    from nlp_config import DistilBertConfig

logger = logging.getLogger(__name__)

torch = None  # type: ignore[assignment]
AutoTokenizer = None  # type: ignore[assignment]
AutoModel = None  # type: ignore[assignment]
_TRANSFORMERS_STACK_STATUS: Optional[bool] = None


def _ensure_transformers_stack() -> bool:
    """Lazily import torch/transformers to avoid expensive startup costs."""
    global torch, AutoTokenizer, AutoModel, _TRANSFORMERS_STACK_STATUS

    if _TRANSFORMERS_STACK_STATUS is not None:
        return _TRANSFORMERS_STACK_STATUS

    try:
        torch = importlib.import_module("torch")  # type: ignore[assignment]
        transformers_module = importlib.import_module("transformers")
        AutoTokenizer = getattr(transformers_module, "AutoTokenizer")  # type: ignore[assignment]
        AutoModel = getattr(transformers_module, "AutoModel")  # type: ignore[assignment]
        _TRANSFORMERS_STACK_STATUS = True
    except Exception as exc:  # pragma: no cover - depends on optional deps
        torch = None  # type: ignore[assignment]
        AutoTokenizer = None  # type: ignore[assignment]
        AutoModel = None  # type: ignore[assignment]
        _TRANSFORMERS_STACK_STATUS = False
        logger.info(
            "Transformers stack unavailable; DistilBERT service will use fallback mode (%s)",
            exc,
        )

    return _TRANSFORMERS_STACK_STATUS


@dataclass
class EmbeddingResult:
    """Result of embedding generation."""
    
    embeddings: List[float]
    processing_time: float
    used_fallback: bool
    model_name: Optional[str] = None
    input_length: int = 0


@dataclass
class ClassificationResult:
    """Result of text classification."""
    
    classification: str
    confidence: float
    processing_time: float
    used_fallback: bool
    model_name: Optional[str] = None
    input_length: int = 0
    details: Optional[Dict[str, Any]] = None


@dataclass
class IntentResult:
    """Result of intent detection."""
    
    intent: str
    confidence: float
    entities: List[Dict[str, Any]]
    processing_time: float
    used_fallback: bool
    model_name: Optional[str] = None
    input_length: int = 0


@dataclass
class SentimentResult:
    """Result of sentiment analysis."""
    
    sentiment: str  # positive, negative, neutral
    score: float  # -1.0 to 1.0
    confidence: float
    processing_time: float
    used_fallback: bool
    model_name: Optional[str] = None
    input_length: int = 0


@dataclass
class TopicResult:
    """Result of topic tagging."""
    
    topics: List[str]
    topic_scores: Dict[str, float]
    processing_time: float
    used_fallback: bool
    model_name: Optional[str] = None
    input_length: int = 0


@dataclass
class SafetyResult:
    """Result of safety filtering."""
    
    is_safe: bool
    safety_score: float  # 0.0 to 1.0, higher is safer
    flagged_categories: List[str]
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
        if not _ensure_transformers_stack():
            logger.info("DistilBERT service running in lightweight fallback mode")
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
        if torch is None:
            logger.info("PyTorch not available; defaulting to CPU mode")
            return "cpu"

        # Check for CUDA availability with error handling
        try:
            if self.config.enable_gpu and torch.cuda.is_available():
                device = torch.device("cuda")
                logger.info(f"Using GPU: {torch.cuda.get_device_name()}")
                return device
        except Exception as e:
            logger.warning(f"CUDA initialization failed: {e}")
            logger.info("Falling back to CPU due to CUDA issues")

        device = torch.device("cpu")
        logger.info("Using CPU for inference")
        return device

    def _load_model(self):
        """Load DistilBERT model and tokenizer."""
        try:
            # Check for offline mode environment variables
            offline = (
                os.getenv("TRANSFORMERS_OFFLINE", "").lower() in ("1", "true", "yes") or
                os.getenv("HF_HUB_OFFLINE", "").lower() in ("1", "true", "yes")
            )
            
            if AutoTokenizer is None or AutoModel is None:
                raise RuntimeError("Transformers library is unavailable")

            # Try offline first, then fallback to online if needed
            try:
                logger.info(f"Loading model {self.config.model_name} in offline mode")
                tokenizer = AutoTokenizer.from_pretrained(
                    self.config.model_name,
                    local_files_only=True,
                )
                model = AutoModel.from_pretrained(
                    self.config.model_name,
                    local_files_only=True,
                )
                logger.info("✓ Model loaded successfully from local cache")
            except Exception as e:
                if offline:
                    logger.error(f"Failed to load model in offline mode: {e}")
                    raise
                else:
                    logger.warning(f"Failed to load from cache, trying online: {e}")
                    tokenizer = AutoTokenizer.from_pretrained(
                        self.config.model_name,
                        local_files_only=False,
                    )
                    model = AutoModel.from_pretrained(
                        self.config.model_name,
                        local_files_only=False,
                    )
            
            # Move model to device and set to eval mode
            model.to(self.device)
            model.eval()
            
            # Disable gradients for inference
            for param in model.parameters():
                param.requires_grad = False
            
            return tokenizer, model
            
        except Exception as e:
            logger.error(f"Failed to load DistilBERT model: {e}")
            logger.error(f"Model name: {self.config.model_name}")
            logger.error(f"Offline mode: {offline}")
            logger.error(f"TRANSFORMERS_OFFLINE: {os.getenv('TRANSFORMERS_OFFLINE', 'not set')}")
            logger.error(f"HF_HUB_OFFLINE: {os.getenv('HF_HUB_OFFLINE', 'not set')}")
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
    
    async def classify_text(
        self, 
        text: str, 
        classification_type: str = "general"
    ) -> ClassificationResult:
        """
        Classify text using DistilBERT embeddings and rule-based classification.
        
        Args:
            text: Text to classify
            classification_type: Type of classification ("general", "task", "domain", "complexity")
            
        Returns:
            ClassificationResult with classification and confidence
        """
        if not text or not text.strip():
            return ClassificationResult(
                classification="unknown",
                confidence=0.0,
                processing_time=0.0,
                used_fallback=True,
                input_length=0
            )
        
        start_time = time.time()
        
        try:
            if self.fallback_mode or not self.model:
                result = await self._fallback_classification(text, classification_type)
                used_fallback = True
            else:
                result = await self._embedding_based_classification(text, classification_type)
                used_fallback = False
            
            processing_time = time.time() - start_time
            
            return ClassificationResult(
                classification=result["classification"],
                confidence=result["confidence"],
                processing_time=processing_time,
                used_fallback=used_fallback,
                model_name=self.config.model_name if not used_fallback else "fallback",
                input_length=len(text),
                details=result.get("details")
            )
            
        except Exception as e:
            logger.error(f"Text classification failed: {e}")
            self._error_count += 1
            self._last_error = str(e)
            
            # Fallback on error
            if not self.fallback_mode and self.config.enable_fallback:
                result = await self._fallback_classification(text, classification_type)
                processing_time = time.time() - start_time
                return ClassificationResult(
                    classification=result["classification"],
                    confidence=result["confidence"],
                    processing_time=processing_time,
                    used_fallback=True,
                    model_name="fallback",
                    input_length=len(text),
                    details=result.get("details")
                )
            else:
                raise
    
    async def detect_intent(self, text: str) -> IntentResult:
        """
        Detect user intent from text.
        
        Args:
            text: Text to analyze for intent
            
        Returns:
            IntentResult with detected intent and entities
        """
        if not text or not text.strip():
            return IntentResult(
                intent="unknown",
                confidence=0.0,
                entities=[],
                processing_time=0.0,
                used_fallback=True,
                input_length=0
            )
        
        start_time = time.time()
        
        try:
            if self.fallback_mode or not self.model:
                result = await self._fallback_intent_detection(text)
                used_fallback = True
            else:
                result = await self._embedding_based_intent_detection(text)
                used_fallback = False
            
            processing_time = time.time() - start_time
            
            return IntentResult(
                intent=result["intent"],
                confidence=result["confidence"],
                entities=result["entities"],
                processing_time=processing_time,
                used_fallback=used_fallback,
                model_name=self.config.model_name if not used_fallback else "fallback",
                input_length=len(text)
            )
            
        except Exception as e:
            logger.error(f"Intent detection failed: {e}")
            self._error_count += 1
            self._last_error = str(e)
            
            # Fallback on error
            if not self.fallback_mode and self.config.enable_fallback:
                result = await self._fallback_intent_detection(text)
                processing_time = time.time() - start_time
                return IntentResult(
                    intent=result["intent"],
                    confidence=result["confidence"],
                    entities=result["entities"],
                    processing_time=processing_time,
                    used_fallback=True,
                    model_name="fallback",
                    input_length=len(text)
                )
            else:
                raise
    
    async def analyze_sentiment(self, text: str) -> SentimentResult:
        """
        Analyze sentiment of text.
        
        Args:
            text: Text to analyze for sentiment
            
        Returns:
            SentimentResult with sentiment classification and score
        """
        if not text or not text.strip():
            return SentimentResult(
                sentiment="neutral",
                score=0.0,
                confidence=0.0,
                processing_time=0.0,
                used_fallback=True,
                input_length=0
            )
        
        start_time = time.time()
        
        try:
            if self.fallback_mode or not self.model:
                result = await self._fallback_sentiment_analysis(text)
                used_fallback = True
            else:
                result = await self._embedding_based_sentiment_analysis(text)
                used_fallback = False
            
            processing_time = time.time() - start_time
            
            return SentimentResult(
                sentiment=result["sentiment"],
                score=result["score"],
                confidence=result["confidence"],
                processing_time=processing_time,
                used_fallback=used_fallback,
                model_name=self.config.model_name if not used_fallback else "fallback",
                input_length=len(text)
            )
            
        except Exception as e:
            logger.error(f"Sentiment analysis failed: {e}")
            self._error_count += 1
            self._last_error = str(e)
            
            # Fallback on error
            if not self.fallback_mode and self.config.enable_fallback:
                result = await self._fallback_sentiment_analysis(text)
                processing_time = time.time() - start_time
                return SentimentResult(
                    sentiment=result["sentiment"],
                    score=result["score"],
                    confidence=result["confidence"],
                    processing_time=processing_time,
                    used_fallback=True,
                    model_name="fallback",
                    input_length=len(text)
                )
            else:
                raise
    
    async def tag_topics(self, text: str, max_topics: int = 5) -> TopicResult:
        """
        Tag topics in text.
        
        Args:
            text: Text to analyze for topics
            max_topics: Maximum number of topics to return
            
        Returns:
            TopicResult with identified topics and scores
        """
        if not text or not text.strip():
            return TopicResult(
                topics=[],
                topic_scores={},
                processing_time=0.0,
                used_fallback=True,
                input_length=0
            )
        
        start_time = time.time()
        
        try:
            if self.fallback_mode or not self.model:
                result = await self._fallback_topic_tagging(text, max_topics)
                used_fallback = True
            else:
                result = await self._embedding_based_topic_tagging(text, max_topics)
                used_fallback = False
            
            processing_time = time.time() - start_time
            
            return TopicResult(
                topics=result["topics"],
                topic_scores=result["topic_scores"],
                processing_time=processing_time,
                used_fallback=used_fallback,
                model_name=self.config.model_name if not used_fallback else "fallback",
                input_length=len(text)
            )
            
        except Exception as e:
            logger.error(f"Topic tagging failed: {e}")
            self._error_count += 1
            self._last_error = str(e)
            
            # Fallback on error
            if not self.fallback_mode and self.config.enable_fallback:
                result = await self._fallback_topic_tagging(text, max_topics)
                processing_time = time.time() - start_time
                return TopicResult(
                    topics=result["topics"],
                    topic_scores=result["topic_scores"],
                    processing_time=processing_time,
                    used_fallback=True,
                    model_name="fallback",
                    input_length=len(text)
                )
            else:
                raise
    
    async def filter_safety(self, text: str) -> SafetyResult:
        """
        Perform safety filtering on text.
        
        Args:
            text: Text to check for safety
            
        Returns:
            SafetyResult with safety assessment
        """
        if not text or not text.strip():
            return SafetyResult(
                is_safe=True,
                safety_score=1.0,
                flagged_categories=[],
                processing_time=0.0,
                used_fallback=True,
                input_length=0
            )
        
        start_time = time.time()
        
        try:
            if self.fallback_mode or not self.model:
                result = await self._fallback_safety_filtering(text)
                used_fallback = True
            else:
                result = await self._embedding_based_safety_filtering(text)
                used_fallback = False
            
            processing_time = time.time() - start_time
            
            return SafetyResult(
                is_safe=result["is_safe"],
                safety_score=result["safety_score"],
                flagged_categories=result["flagged_categories"],
                processing_time=processing_time,
                used_fallback=used_fallback,
                model_name=self.config.model_name if not used_fallback else "fallback",
                input_length=len(text)
            )
            
        except Exception as e:
            logger.error(f"Safety filtering failed: {e}")
            self._error_count += 1
            self._last_error = str(e)
            
            # Fallback on error
            if not self.fallback_mode and self.config.enable_fallback:
                result = await self._fallback_safety_filtering(text)
                processing_time = time.time() - start_time
                return SafetyResult(
                    is_safe=result["is_safe"],
                    safety_score=result["safety_score"],
                    flagged_categories=result["flagged_categories"],
                    processing_time=processing_time,
                    used_fallback=True,
                    model_name="fallback",
                    input_length=len(text)
                )
            else:
                raise
    
    async def _embedding_based_classification(self, text: str, classification_type: str) -> Dict[str, Any]:
        """Classify text using DistilBERT embeddings and similarity matching."""
        # Get embeddings for the input text
        embeddings = await self.get_embeddings(text)
        
        # Define classification templates based on type
        if classification_type == "general":
            templates = {
                "question": "This is a question asking for information or clarification",
                "request": "This is a request for action or assistance", 
                "statement": "This is a statement providing information or opinion",
                "greeting": "This is a greeting or social interaction",
                "complaint": "This is a complaint or expression of dissatisfaction"
            }
        elif classification_type == "task":
            templates = {
                "coding": "This is about programming, software development, or technical implementation",
                "analysis": "This is about analyzing, evaluating, or understanding something",
                "creation": "This is about creating, building, or generating something new",
                "explanation": "This is asking for explanation or clarification of concepts",
                "troubleshooting": "This is about solving problems or fixing issues"
            }
        elif classification_type == "domain":
            templates = {
                "technology": "This is about technology, computers, software, or digital topics",
                "business": "This is about business, finance, management, or commercial topics",
                "science": "This is about scientific concepts, research, or academic topics",
                "personal": "This is about personal matters, relationships, or individual concerns",
                "creative": "This is about creative work, art, writing, or artistic expression"
            }
        else:  # complexity
            templates = {
                "simple": "This is a simple, straightforward question or request",
                "moderate": "This is a moderately complex topic requiring some analysis",
                "complex": "This is a complex topic requiring deep analysis and expertise"
            }
        
        # Calculate similarity with each template
        best_match = "unknown"
        best_score = 0.0
        
        for category, template in templates.items():
            template_embeddings = await self.get_embeddings(template)
            similarity = self._calculate_cosine_similarity(embeddings, template_embeddings)
            if similarity > best_score:
                best_score = similarity
                best_match = category
        
        # Adjust confidence based on score
        confidence = min(best_score * 1.2, 1.0)  # Boost confidence slightly
        
        return {
            "classification": best_match,
            "confidence": confidence,
            "details": {"similarity_score": best_score}
        }
    
    async def _embedding_based_intent_detection(self, text: str) -> Dict[str, Any]:
        """Detect intent using DistilBERT embeddings."""
        # Get embeddings for the input text
        embeddings = await self.get_embeddings(text)
        
        # Define intent templates
        intent_templates = {
            "information_seeking": "I want to learn about or understand something",
            "task_completion": "I need help completing a specific task or action",
            "problem_solving": "I have a problem that needs to be solved or fixed",
            "creative_assistance": "I need help with creative work or generating ideas",
            "decision_making": "I need help making a choice or decision",
            "social_interaction": "I want to have a conversation or social interaction"
        }
        
        # Calculate similarity with each intent template
        best_intent = "unknown"
        best_score = 0.0
        
        for intent, template in intent_templates.items():
            template_embeddings = await self.get_embeddings(template)
            similarity = self._calculate_cosine_similarity(embeddings, template_embeddings)
            if similarity > best_score:
                best_score = similarity
                best_intent = intent
        
        # Extract simple entities (placeholder - could be enhanced)
        entities = self._extract_simple_entities(text)
        
        return {
            "intent": best_intent,
            "confidence": min(best_score * 1.1, 1.0),
            "entities": entities
        }
    
    async def _embedding_based_sentiment_analysis(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment using DistilBERT embeddings."""
        # Get embeddings for the input text
        embeddings = await self.get_embeddings(text)
        
        # Define sentiment templates
        sentiment_templates = {
            "positive": "This expresses happiness, satisfaction, joy, or positive emotions",
            "negative": "This expresses sadness, anger, frustration, or negative emotions", 
            "neutral": "This is factual, objective, or emotionally neutral"
        }
        
        # Calculate similarity with each sentiment template
        sentiment_scores = {}
        for sentiment, template in sentiment_templates.items():
            template_embeddings = await self.get_embeddings(template)
            similarity = self._calculate_cosine_similarity(embeddings, template_embeddings)
            sentiment_scores[sentiment] = similarity
        
        # Determine best sentiment
        best_sentiment = max(sentiment_scores, key=sentiment_scores.get)
        confidence = sentiment_scores[best_sentiment]
        
        # Calculate sentiment score (-1 to 1)
        pos_score = sentiment_scores.get("positive", 0.0)
        neg_score = sentiment_scores.get("negative", 0.0)
        sentiment_score = pos_score - neg_score
        
        return {
            "sentiment": best_sentiment,
            "score": sentiment_score,
            "confidence": confidence
        }
    
    async def _embedding_based_topic_tagging(self, text: str, max_topics: int) -> Dict[str, Any]:
        """Tag topics using DistilBERT embeddings."""
        # Get embeddings for the input text
        embeddings = await self.get_embeddings(text)
        
        # Define topic templates
        topic_templates = {
            "technology": "technology, computers, software, programming, digital, internet",
            "business": "business, finance, money, management, company, market, sales",
            "science": "science, research, study, experiment, theory, analysis, data",
            "education": "learning, teaching, school, university, knowledge, training",
            "health": "health, medical, wellness, fitness, disease, treatment, care",
            "entertainment": "entertainment, movies, music, games, fun, leisure, hobby",
            "travel": "travel, vacation, trip, journey, destination, tourism, adventure",
            "food": "food, cooking, recipe, restaurant, meal, cuisine, nutrition",
            "sports": "sports, exercise, fitness, competition, team, game, athletic",
            "politics": "politics, government, policy, election, law, society, public"
        }
        
        # Calculate similarity with each topic template
        topic_scores = {}
        for topic, template in topic_templates.items():
            template_embeddings = await self.get_embeddings(template)
            similarity = self._calculate_cosine_similarity(embeddings, template_embeddings)
            topic_scores[topic] = similarity
        
        # Sort topics by score and return top ones
        sorted_topics = sorted(topic_scores.items(), key=lambda x: x[1], reverse=True)
        top_topics = sorted_topics[:max_topics]
        
        topics = [topic for topic, score in top_topics if score > 0.3]  # Threshold
        topic_scores_dict = {topic: score for topic, score in top_topics if score > 0.3}
        
        return {
            "topics": topics,
            "topic_scores": topic_scores_dict
        }
    
    async def _embedding_based_safety_filtering(self, text: str) -> Dict[str, Any]:
        """Perform safety filtering using DistilBERT embeddings."""
        # Get embeddings for the input text
        embeddings = await self.get_embeddings(text)
        
        # Define safety concern templates
        safety_templates = {
            "harmful_content": "harmful, dangerous, violent, threatening, abusive content",
            "inappropriate": "inappropriate, offensive, explicit, adult, sexual content",
            "misinformation": "false information, conspiracy, misleading, unverified claims",
            "spam": "spam, promotional, advertising, unsolicited, repetitive content",
            "personal_info": "personal information, private data, confidential, sensitive details"
        }
        
        # Calculate similarity with safety concern templates
        flagged_categories = []
        max_concern_score = 0.0
        
        for category, template in safety_templates.items():
            template_embeddings = await self.get_embeddings(template)
            similarity = self._calculate_cosine_similarity(embeddings, template_embeddings)
            if similarity > 0.6:  # Threshold for flagging
                flagged_categories.append(category)
            max_concern_score = max(max_concern_score, similarity)
        
        # Calculate safety score (inverse of concern)
        safety_score = 1.0 - max_concern_score
        is_safe = len(flagged_categories) == 0 and safety_score > 0.5
        
        return {
            "is_safe": is_safe,
            "safety_score": safety_score,
            "flagged_categories": flagged_categories
        }
    
    def _calculate_cosine_similarity(self, embeddings1: List[float], embeddings2: List[float]) -> float:
        """Calculate cosine similarity between two embedding vectors."""
        if not embeddings1 or not embeddings2:
            return 0.0
        
        # Convert to numpy arrays for calculation
        vec1 = np.array(embeddings1)
        vec2 = np.array(embeddings2)
        
        # Calculate cosine similarity
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        similarity = dot_product / (norm1 * norm2)
        return float(similarity)
    
    def _extract_simple_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extract simple entities from text using basic patterns."""
        entities = []
        
        # Simple patterns for common entities
        import re
        
        # Email addresses
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        for email in emails:
            entities.append({"text": email, "type": "email", "confidence": 0.9})
        
        # URLs
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        urls = re.findall(url_pattern, text)
        for url in urls:
            entities.append({"text": url, "type": "url", "confidence": 0.9})
        
        # Numbers
        number_pattern = r'\b\d+(?:\.\d+)?\b'
        numbers = re.findall(number_pattern, text)
        for number in numbers:
            entities.append({"text": number, "type": "number", "confidence": 0.7})
        
        return entities
    
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
    
    async def _fallback_classification(self, text: str, classification_type: str) -> Dict[str, Any]:
        """Fallback classification using simple rule-based approach."""
        text_lower = text.lower()
        
        if classification_type == "general":
            if "?" in text:
                return {"classification": "question", "confidence": 0.8}
            elif any(word in text_lower for word in ["please", "can you", "help", "need"]):
                return {"classification": "request", "confidence": 0.7}
            elif any(word in text_lower for word in ["hello", "hi", "hey", "good morning"]):
                return {"classification": "greeting", "confidence": 0.9}
            elif any(word in text_lower for word in ["problem", "issue", "wrong", "error", "broken"]):
                return {"classification": "complaint", "confidence": 0.6}
            else:
                return {"classification": "statement", "confidence": 0.5}
        
        elif classification_type == "task":
            if any(word in text_lower for word in ["code", "program", "debug", "function", "script"]):
                return {"classification": "coding", "confidence": 0.8}
            elif any(word in text_lower for word in ["analyze", "compare", "evaluate", "assess"]):
                return {"classification": "analysis", "confidence": 0.7}
            elif any(word in text_lower for word in ["create", "build", "make", "generate", "design"]):
                return {"classification": "creation", "confidence": 0.7}
            elif any(word in text_lower for word in ["explain", "what is", "how does", "why"]):
                return {"classification": "explanation", "confidence": 0.8}
            elif any(word in text_lower for word in ["fix", "solve", "troubleshoot", "debug"]):
                return {"classification": "troubleshooting", "confidence": 0.7}
            else:
                return {"classification": "general", "confidence": 0.4}
        
        else:
            return {"classification": "unknown", "confidence": 0.3}
    
    async def _fallback_intent_detection(self, text: str) -> Dict[str, Any]:
        """Fallback intent detection using simple patterns."""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ["what", "how", "why", "when", "where", "explain"]):
            intent = "information_seeking"
            confidence = 0.8
        elif any(word in text_lower for word in ["help me", "can you", "please", "need to"]):
            intent = "task_completion"
            confidence = 0.7
        elif any(word in text_lower for word in ["problem", "issue", "error", "fix", "broken"]):
            intent = "problem_solving"
            confidence = 0.8
        elif any(word in text_lower for word in ["create", "generate", "write", "design", "make"]):
            intent = "creative_assistance"
            confidence = 0.7
        elif any(word in text_lower for word in ["should i", "which", "better", "choose", "decide"]):
            intent = "decision_making"
            confidence = 0.6
        else:
            intent = "social_interaction"
            confidence = 0.4
        
        # Extract simple entities
        entities = self._extract_simple_entities(text)
        
        return {
            "intent": intent,
            "confidence": confidence,
            "entities": entities
        }
    
    async def _fallback_sentiment_analysis(self, text: str) -> Dict[str, Any]:
        """Fallback sentiment analysis using simple word matching."""
        text_lower = text.lower()
        
        positive_words = ["good", "great", "excellent", "amazing", "wonderful", "love", "like", "happy", "pleased", "satisfied"]
        negative_words = ["bad", "terrible", "awful", "hate", "dislike", "angry", "frustrated", "disappointed", "sad", "upset"]
        
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            sentiment = "positive"
            score = min(positive_count * 0.3, 1.0)
            confidence = 0.6
        elif negative_count > positive_count:
            sentiment = "negative"
            score = -min(negative_count * 0.3, 1.0)
            confidence = 0.6
        else:
            sentiment = "neutral"
            score = 0.0
            confidence = 0.5
        
        return {
            "sentiment": sentiment,
            "score": score,
            "confidence": confidence
        }
    
    async def _fallback_topic_tagging(self, text: str, max_topics: int) -> Dict[str, Any]:
        """Fallback topic tagging using keyword matching."""
        text_lower = text.lower()
        
        topic_keywords = {
            "technology": ["computer", "software", "code", "program", "digital", "internet", "tech", "app", "website"],
            "business": ["business", "company", "money", "finance", "market", "sales", "profit", "customer"],
            "science": ["research", "study", "experiment", "data", "analysis", "theory", "scientific", "method"],
            "education": ["learn", "teach", "school", "university", "student", "knowledge", "training", "course"],
            "health": ["health", "medical", "doctor", "medicine", "fitness", "wellness", "disease", "treatment"],
            "entertainment": ["movie", "music", "game", "fun", "entertainment", "show", "video", "play"],
            "travel": ["travel", "trip", "vacation", "journey", "destination", "tourism", "visit", "explore"],
            "food": ["food", "cook", "recipe", "restaurant", "meal", "eat", "cuisine", "nutrition"],
            "sports": ["sport", "game", "team", "player", "competition", "exercise", "fitness", "athletic"],
            "politics": ["politics", "government", "policy", "election", "law", "society", "public", "political"]
        }
        
        topic_scores = {}
        for topic, keywords in topic_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_lower) / len(keywords)
            if score > 0:
                topic_scores[topic] = score
        
        # Sort and return top topics
        sorted_topics = sorted(topic_scores.items(), key=lambda x: x[1], reverse=True)
        top_topics = sorted_topics[:max_topics]
        
        topics = [topic for topic, score in top_topics]
        topic_scores_dict = dict(top_topics)
        
        return {
            "topics": topics,
            "topic_scores": topic_scores_dict
        }
    
    async def _fallback_safety_filtering(self, text: str) -> Dict[str, Any]:
        """Fallback safety filtering using simple keyword matching."""
        text_lower = text.lower()
        
        safety_keywords = {
            "harmful_content": ["violence", "harm", "hurt", "kill", "weapon", "dangerous", "threat"],
            "inappropriate": ["explicit", "sexual", "adult", "inappropriate", "offensive", "vulgar"],
            "misinformation": ["conspiracy", "fake", "false", "lie", "misinformation", "hoax"],
            "spam": ["buy now", "click here", "free money", "guaranteed", "limited time", "act now"],
            "personal_info": ["ssn", "social security", "credit card", "password", "private", "confidential"]
        }
        
        flagged_categories = []
        max_concern_score = 0.0
        
        for category, keywords in safety_keywords.items():
            matches = sum(1 for keyword in keywords if keyword in text_lower)
            if matches > 0:
                concern_score = min(matches * 0.3, 1.0)
                max_concern_score = max(max_concern_score, concern_score)
                if concern_score > 0.5:
                    flagged_categories.append(category)
        
        safety_score = 1.0 - max_concern_score
        is_safe = len(flagged_categories) == 0 and safety_score > 0.7
        
        return {
            "is_safe": is_safe,
            "safety_score": safety_score,
            "flagged_categories": flagged_categories
        }
    
    async def route_task(self, text: str) -> Dict[str, Any]:
        """
        Determine optimal task routing based on DistilBERT classification.
        
        Args:
            text: Input text to analyze for routing
            
        Returns:
            Dictionary with routing recommendation and confidence
        """
        # Perform multiple classifications to determine routing
        task_classification = await self.classify_text(text, "task")
        intent_result = await self.detect_intent(text)
        safety_result = await self.filter_safety(text)
        
        # Determine routing based on classifications
        routing_decision = {
            "recommended_handler": "main_llm",  # Default
            "confidence": 0.5,
            "reasoning": "Default routing to main LLM",
            "safety_check": safety_result.is_safe,
            "classifications": {
                "task": task_classification.classification,
                "intent": intent_result.intent,
                "safety_score": safety_result.safety_score
            }
        }
        
        # Safety check first
        if not safety_result.is_safe:
            routing_decision.update({
                "recommended_handler": "safety_filter",
                "confidence": 0.9,
                "reasoning": f"Content flagged for safety concerns: {', '.join(safety_result.flagged_categories)}"
            })
            return routing_decision
        
        # Route based on task classification
        if task_classification.classification == "coding" and task_classification.confidence > 0.7:
            routing_decision.update({
                "recommended_handler": "code_specialist",
                "confidence": task_classification.confidence,
                "reasoning": "High confidence coding task detected"
            })
        elif intent_result.intent == "information_seeking" and intent_result.confidence > 0.8:
            routing_decision.update({
                "recommended_handler": "knowledge_retrieval",
                "confidence": intent_result.confidence,
                "reasoning": "Clear information seeking intent detected"
            })
        elif task_classification.classification in ["analysis", "explanation"] and task_classification.confidence > 0.6:
            routing_decision.update({
                "recommended_handler": "analytical_llm",
                "confidence": task_classification.confidence,
                "reasoning": f"Analytical task ({task_classification.classification}) detected"
            })
        elif intent_result.intent == "creative_assistance" and intent_result.confidence > 0.7:
            routing_decision.update({
                "recommended_handler": "creative_llm",
                "confidence": intent_result.confidence,
                "reasoning": "Creative assistance request detected"
            })
        
        return routing_decision
    
    async def enhance_context_understanding(
        self, 
        text: str, 
        conversation_history: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Enhance context understanding using DistilBERT analysis.
        
        Args:
            text: Current text to analyze
            conversation_history: Previous conversation turns for context
            
        Returns:
            Dictionary with enhanced context insights
        """
        # Analyze current text
        sentiment_result = await self.analyze_sentiment(text)
        topic_result = await self.tag_topics(text, max_topics=3)
        intent_result = await self.detect_intent(text)
        
        context_insights = {
            "current_sentiment": sentiment_result.sentiment,
            "sentiment_score": sentiment_result.score,
            "main_topics": topic_result.topics,
            "user_intent": intent_result.intent,
            "entities": intent_result.entities,
            "context_continuity": 0.5  # Default
        }
        
        # Analyze conversation continuity if history is available
        if conversation_history and len(conversation_history) > 0:
            try:
                # Get embeddings for current text and recent history
                current_embeddings = await self.get_embeddings(text)
                recent_text = " ".join(conversation_history[-2:])  # Last 2 turns
                history_embeddings = await self.get_embeddings(recent_text)
                
                # Calculate continuity score
                continuity_score = self._calculate_cosine_similarity(current_embeddings, history_embeddings)
                context_insights["context_continuity"] = continuity_score
                
                # Analyze topic evolution
                if len(conversation_history) >= 2:
                    prev_topics = await self.tag_topics(conversation_history[-1], max_topics=3)
                    topic_overlap = len(set(topic_result.topics) & set(prev_topics.topics))
                    context_insights["topic_consistency"] = topic_overlap / max(len(topic_result.topics), 1)
                
            except Exception as e:
                logger.debug(f"Context continuity analysis failed: {e}")
        
        return context_insights
