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
    from ai_karen_engine.services.nlp_config import SpacyConfig
except ImportError:
    from nlp_config import SpacyConfig

try:
    from ai_karen_engine.utils.error_formatter import ErrorFormatter, log_dependency_error
except ImportError:
    # Fallback if error formatter is not available
    ErrorFormatter = None
    log_dependency_error = None

logger = logging.getLogger(__name__)

# Optional dependencies with graceful fallback
try:
    import spacy
    from spacy.cli import download
    SPACY_AVAILABLE = True
except Exception:
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
    sentences: List[str]  # Sentence segmentation
    dependencies: List[Dict[str, Any]]  # Dependency parsing results
    sentiment: Optional[float] = None
    language: str = "en"
    processing_time: float = 0.0
    used_fallback: bool = False


@dataclass
class EntityExtractionResult:
    """Result of enhanced entity extraction."""
    
    entities: List[Dict[str, Any]]  # Enhanced entity information
    processing_time: float
    used_fallback: bool
    confidence_scores: Dict[str, float]
    entity_relationships: List[Dict[str, Any]]


@dataclass
class KeyPhraseResult:
    """Result of key phrase identification."""
    
    key_phrases: List[str]
    phrase_scores: Dict[str, float]
    processing_time: float
    used_fallback: bool
    phrase_types: Dict[str, str]  # phrase -> type mapping


@dataclass
class TextNormalizationResult:
    """Result of text normalization."""
    
    normalized_text: str
    original_text: str
    normalizations_applied: List[str]
    processing_time: float
    used_fallback: bool


@dataclass
class StructuredAnalysisResult:
    """Result of structured text analysis."""
    
    structure: Dict[str, Any]
    key_information: Dict[str, Any]
    relationships: List[Dict[str, Any]]
    processing_time: float
    used_fallback: bool


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
            error_msg = f"❌ spaCy Service Initialization Failed: {e}"
            logger.error(error_msg)
            self._last_error = str(e)
            self._error_count += 1
            if self.config.enable_fallback:
                self.fallback_mode = True
                logger.info("✅ Enabled fallback mode - basic NLP functionality available")
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
            
            # Use enhanced error formatting if available
            if ErrorFormatter and log_dependency_error:
                log_dependency_error(logger, e, "spacy[en_core_web_sm]")
            else:
                # Fallback to enhanced manual formatting
                error_msg = f"❌ spaCy Model Loading Failed: {e}"
                
                if "Can't find model" in str(e) and "en_core_web_sm" in str(e):
                    error_msg += (
                        "\n\n🔧 SOLUTION: Install the missing spaCy model by running:\n"
                        "   python -m spacy download en_core_web_sm\n"
                        "   \n"
                        "   Or activate your virtual environment first:\n"
                        "   source .env_kari/bin/activate\n"
                        "   python -m spacy download en_core_web_sm\n"
                        "\n"
                        "ℹ️  The application will continue using fallback NLP processing."
                    )
                else:
                    error_msg += (
                        "\n\n🔧 POSSIBLE SOLUTIONS:\n"
                        "   1. Install spaCy: pip install spacy\n"
                        "   2. Download language model: python -m spacy download en_core_web_sm\n"
                        "   3. Check your virtual environment is activated\n"
                        "\n"
                        "ℹ️  The application will continue using fallback NLP processing."
                    )
                
                logger.error(error_msg)
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
                sentences=[],
                dependencies=[],
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
        
        # Extract dependency parsing information
        dependencies = []
        for token in doc:
            dep_info = {
                "text": token.text,
                "lemma": token.lemma_,
                "pos": token.pos_,
                "tag": token.tag_,
                "dep": token.dep_,
                "head": token.head.text if token.head != token else "ROOT",
                "head_pos": token.head.pos_ if token.head != token else "ROOT",
                "children": [child.text for child in token.children]
            }
            dependencies.append(dep_info)
        
        return ParsedMessage(
            tokens=[token.text for token in doc],
            lemmas=[token.lemma_ for token in doc],
            entities=[(ent.text, ent.label_) for ent in doc.ents],
            pos_tags=[(token.text, token.pos_) for token in doc],
            noun_phrases=[chunk.text for chunk in doc.noun_chunks],
            sentences=[sent.text.strip() for sent in doc.sents],
            dependencies=dependencies,
            language=doc.lang_,
            used_fallback=False
        )
    
    async def _fallback_parse(self, text: str) -> ParsedMessage:
        """Simple fallback parsing when spaCy is unavailable."""
        # Basic tokenization
        tokens = text.split()
        
        # Simple sentence splitting
        sentences = text.replace('!', '.').replace('?', '.').split('.')
        sentences = [s.strip() for s in sentences if s.strip()]
        noun_phrases = sentences  # Use sentences as noun phrases in fallback
        
        # Basic dependency structure (no real parsing in fallback)
        dependencies = []
        for i, token in enumerate(tokens):
            dep_info = {
                "text": token,
                "lemma": token.lower(),  # Simple lowercasing as lemma
                "pos": "UNKNOWN",
                "tag": "UNKNOWN", 
                "dep": "UNKNOWN",
                "head": "ROOT" if i == 0 else tokens[0],  # First token as head
                "head_pos": "ROOT" if i == 0 else "UNKNOWN",
                "children": []
            }
            dependencies.append(dep_info)
        
        return ParsedMessage(
            tokens=tokens,
            lemmas=[token.lower() for token in tokens],  # Simple lowercasing as lemmatization
            entities=[],    # No entity recognition in fallback
            pos_tags=[],    # No POS tagging in fallback
            noun_phrases=noun_phrases,
            sentences=sentences,
            dependencies=dependencies,
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
    
    async def extract_entities(self, text: str) -> List[Tuple[str, str]]:
        """Extract named entities from text."""
        parsed = await self.parse_message(text)
        return parsed.entities
    
    async def extract_entities_enhanced(self, text: str) -> EntityExtractionResult:
        """
        Enhanced entity extraction with confidence scores and relationships.
        
        Args:
            text: Text to extract entities from
            
        Returns:
            EntityExtractionResult with detailed entity information
        """
        if not text or not text.strip():
            return EntityExtractionResult(
                entities=[],
                processing_time=0.0,
                used_fallback=True,
                confidence_scores={},
                entity_relationships=[]
            )
        
        start_time = time.time()
        
        try:
            if self.fallback_mode or not self.nlp:
                result = await self._fallback_entity_extraction(text)
                used_fallback = True
            else:
                result = await self._spacy_entity_extraction(text)
                used_fallback = False
            
            processing_time = time.time() - start_time
            
            return EntityExtractionResult(
                entities=result["entities"],
                processing_time=processing_time,
                used_fallback=used_fallback,
                confidence_scores=result["confidence_scores"],
                entity_relationships=result["entity_relationships"]
            )
            
        except Exception as e:
            logger.error(f"Enhanced entity extraction failed: {e}")
            self._error_count += 1
            self._last_error = str(e)
            
            # Fallback on error
            if not self.fallback_mode and self.config.enable_fallback:
                result = await self._fallback_entity_extraction(text)
                processing_time = time.time() - start_time
                return EntityExtractionResult(
                    entities=result["entities"],
                    processing_time=processing_time,
                    used_fallback=True,
                    confidence_scores=result["confidence_scores"],
                    entity_relationships=result["entity_relationships"]
                )
            else:
                raise
    
    async def identify_key_phrases(
        self, 
        text: str, 
        max_phrases: int = 10,
        min_phrase_length: int = 2
    ) -> KeyPhraseResult:
        """
        Identify key phrases from text using NLP analysis.
        
        Args:
            text: Text to extract key phrases from
            max_phrases: Maximum number of phrases to return
            min_phrase_length: Minimum length of phrases in tokens
            
        Returns:
            KeyPhraseResult with identified key phrases and scores
        """
        if not text or not text.strip():
            return KeyPhraseResult(
                key_phrases=[],
                phrase_scores={},
                processing_time=0.0,
                used_fallback=True,
                phrase_types={}
            )
        
        start_time = time.time()
        
        try:
            if self.fallback_mode or not self.nlp:
                result = await self._fallback_key_phrase_extraction(text, max_phrases, min_phrase_length)
                used_fallback = True
            else:
                result = await self._spacy_key_phrase_extraction(text, max_phrases, min_phrase_length)
                used_fallback = False
            
            processing_time = time.time() - start_time
            
            return KeyPhraseResult(
                key_phrases=result["key_phrases"],
                phrase_scores=result["phrase_scores"],
                processing_time=processing_time,
                used_fallback=used_fallback,
                phrase_types=result["phrase_types"]
            )
            
        except Exception as e:
            logger.error(f"Key phrase identification failed: {e}")
            self._error_count += 1
            self._last_error = str(e)
            
            # Fallback on error
            if not self.fallback_mode and self.config.enable_fallback:
                result = await self._fallback_key_phrase_extraction(text, max_phrases, min_phrase_length)
                processing_time = time.time() - start_time
                return KeyPhraseResult(
                    key_phrases=result["key_phrases"],
                    phrase_scores=result["phrase_scores"],
                    processing_time=processing_time,
                    used_fallback=True,
                    phrase_types=result["phrase_types"]
                )
            else:
                raise
    
    async def normalize_text(
        self, 
        text: str, 
        normalization_options: Optional[Dict[str, bool]] = None
    ) -> TextNormalizationResult:
        """
        Normalize text using spaCy processing.
        
        Args:
            text: Text to normalize
            normalization_options: Options for normalization (lemmatize, lowercase, remove_punct, etc.)
            
        Returns:
            TextNormalizationResult with normalized text
        """
        if not text or not text.strip():
            return TextNormalizationResult(
                normalized_text="",
                original_text=text,
                normalizations_applied=[],
                processing_time=0.0,
                used_fallback=True
            )
        
        # Default normalization options
        options = normalization_options or {
            "lemmatize": True,
            "lowercase": True,
            "remove_punctuation": False,
            "remove_stopwords": False,
            "remove_whitespace": True
        }
        
        start_time = time.time()
        
        try:
            if self.fallback_mode or not self.nlp:
                result = await self._fallback_text_normalization(text, options)
                used_fallback = True
            else:
                result = await self._spacy_text_normalization(text, options)
                used_fallback = False
            
            processing_time = time.time() - start_time
            
            return TextNormalizationResult(
                normalized_text=result["normalized_text"],
                original_text=text,
                normalizations_applied=result["normalizations_applied"],
                processing_time=processing_time,
                used_fallback=used_fallback
            )
            
        except Exception as e:
            logger.error(f"Text normalization failed: {e}")
            self._error_count += 1
            self._last_error = str(e)
            
            # Fallback on error
            if not self.fallback_mode and self.config.enable_fallback:
                result = await self._fallback_text_normalization(text, options)
                processing_time = time.time() - start_time
                return TextNormalizationResult(
                    normalized_text=result["normalized_text"],
                    original_text=text,
                    normalizations_applied=result["normalizations_applied"],
                    processing_time=processing_time,
                    used_fallback=True
                )
            else:
                raise
    
    async def analyze_structure(self, text: str) -> StructuredAnalysisResult:
        """
        Perform structured text analysis for memory retrieval enhancement.
        
        Args:
            text: Text to analyze structurally
            
        Returns:
            StructuredAnalysisResult with structural information
        """
        if not text or not text.strip():
            return StructuredAnalysisResult(
                structure={},
                key_information={},
                relationships=[],
                processing_time=0.0,
                used_fallback=True
            )
        
        start_time = time.time()
        
        try:
            if self.fallback_mode or not self.nlp:
                result = await self._fallback_structure_analysis(text)
                used_fallback = True
            else:
                result = await self._spacy_structure_analysis(text)
                used_fallback = False
            
            processing_time = time.time() - start_time
            
            return StructuredAnalysisResult(
                structure=result["structure"],
                key_information=result["key_information"],
                relationships=result["relationships"],
                processing_time=processing_time,
                used_fallback=used_fallback
            )
            
        except Exception as e:
            logger.error(f"Structured analysis failed: {e}")
            self._error_count += 1
            self._last_error = str(e)
            
            # Fallback on error
            if not self.fallback_mode and self.config.enable_fallback:
                result = await self._fallback_structure_analysis(text)
                processing_time = time.time() - start_time
                return StructuredAnalysisResult(
                    structure=result["structure"],
                    key_information=result["key_information"],
                    relationships=result["relationships"],
                    processing_time=processing_time,
                    used_fallback=True
                )
            else:
                raise
    
    async def extract_facts(self, text: str) -> List[Dict[str, Any]]:
        """Extract factual information from text using NER and dependency parsing."""
        parsed = await self.parse_message(text)
        
        facts = []
        
        # Extract entity-based facts
        for entity_text, entity_label in parsed.entities:
            facts.append({
                "type": "entity",
                "entity": entity_text,
                "label": entity_label,
                "confidence": "high"  # spaCy entities are generally high confidence
            })
        
        # Extract relationship facts from dependency parsing
        if not parsed.used_fallback:
            for dep in parsed.dependencies:
                if dep["dep"] in ["nsubj", "dobj", "pobj"] and dep["head"] != "ROOT":
                    facts.append({
                        "type": "relationship",
                        "subject": dep["text"],
                        "relation": dep["dep"],
                        "object": dep["head"],
                        "confidence": "medium"
                    })
        
        return facts
    
    async def get_linguistic_features(self, text: str) -> Dict[str, Any]:
        """Extract comprehensive linguistic features from text."""
        parsed = await self.parse_message(text)
        
        # Count different POS types
        pos_counts = {}
        for token, pos in parsed.pos_tags:
            pos_counts[pos] = pos_counts.get(pos, 0) + 1
        
        # Count dependency types
        dep_counts = {}
        for dep in parsed.dependencies:
            dep_type = dep["dep"]
            dep_counts[dep_type] = dep_counts.get(dep_type, 0) + 1
        
        return {
            "token_count": len(parsed.tokens),
            "sentence_count": len(parsed.sentences),
            "entity_count": len(parsed.entities),
            "noun_phrase_count": len(parsed.noun_phrases),
            "pos_distribution": pos_counts,
            "dependency_distribution": dep_counts,
            "avg_sentence_length": len(parsed.tokens) / len(parsed.sentences) if parsed.sentences else 0,
            "language": parsed.language,
            "used_fallback": parsed.used_fallback
        }
    
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
    
    async def _spacy_entity_extraction(self, text: str) -> Dict[str, Any]:
        """Enhanced entity extraction using spaCy."""
        # Run spaCy processing in thread pool
        loop = asyncio.get_event_loop()
        doc = await loop.run_in_executor(None, self.nlp, text)
        
        entities = []
        confidence_scores = {}
        entity_relationships = []
        
        # Extract entities with enhanced information
        for ent in doc.ents:
            entity_info = {
                "text": ent.text,
                "label": ent.label_,
                "start": ent.start_char,
                "end": ent.end_char,
                "description": spacy.explain(ent.label_) if hasattr(spacy, 'explain') else ent.label_
            }
            entities.append(entity_info)
            
            # Simple confidence based on entity length and type
            confidence = 0.8 if len(ent.text) > 2 else 0.6
            if ent.label_ in ["PERSON", "ORG", "GPE"]:  # High confidence entity types
                confidence += 0.1
            confidence_scores[ent.text] = min(confidence, 1.0)
        
        # Find entity relationships based on proximity and dependencies
        for i, ent1 in enumerate(doc.ents):
            for j, ent2 in enumerate(doc.ents):
                if i != j and abs(ent1.start - ent2.end) < 10:  # Nearby entities
                    relationship = {
                        "entity1": ent1.text,
                        "entity2": ent2.text,
                        "relationship_type": "proximity",
                        "confidence": 0.6
                    }
                    entity_relationships.append(relationship)
        
        return {
            "entities": entities,
            "confidence_scores": confidence_scores,
            "entity_relationships": entity_relationships
        }
    
    async def _fallback_entity_extraction(self, text: str) -> Dict[str, Any]:
        """Fallback entity extraction using simple patterns."""
        import re
        
        entities = []
        confidence_scores = {}
        entity_relationships = []
        
        # Simple patterns for common entities
        patterns = {
            "EMAIL": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            "URL": r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',
            "PHONE": r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            "NUMBER": r'\b\d+(?:\.\d+)?\b'
        }
        
        for label, pattern in patterns.items():
            matches = re.finditer(pattern, text)
            for match in matches:
                entity_info = {
                    "text": match.group(),
                    "label": label,
                    "start": match.start(),
                    "end": match.end(),
                    "description": label.lower()
                }
                entities.append(entity_info)
                confidence_scores[match.group()] = 0.8
        
        return {
            "entities": entities,
            "confidence_scores": confidence_scores,
            "entity_relationships": entity_relationships
        }
    
    async def _spacy_key_phrase_extraction(self, text: str, max_phrases: int, min_phrase_length: int) -> Dict[str, Any]:
        """Extract key phrases using spaCy NLP analysis."""
        # Run spaCy processing in thread pool
        loop = asyncio.get_event_loop()
        doc = await loop.run_in_executor(None, self.nlp, text)
        
        key_phrases = []
        phrase_scores = {}
        phrase_types = {}
        
        # Extract noun phrases
        for chunk in doc.noun_chunks:
            if len(chunk.text.split()) >= min_phrase_length:
                phrase = chunk.text.strip()
                if phrase and phrase not in key_phrases:
                    key_phrases.append(phrase)
                    # Score based on length and POS composition
                    score = min(len(phrase.split()) * 0.2, 1.0)
                    phrase_scores[phrase] = score
                    phrase_types[phrase] = "noun_phrase"
        
        # Extract named entities as key phrases
        for ent in doc.ents:
            if len(ent.text.split()) >= min_phrase_length:
                phrase = ent.text.strip()
                if phrase and phrase not in key_phrases:
                    key_phrases.append(phrase)
                    phrase_scores[phrase] = 0.9  # High score for entities
                    phrase_types[phrase] = f"entity_{ent.label_.lower()}"
        
        # Extract important verb phrases
        for token in doc:
            if token.pos_ == "VERB" and not token.is_stop:
                # Look for verb + object patterns
                phrase_tokens = [token]
                for child in token.children:
                    if child.dep_ in ["dobj", "pobj", "acomp"]:
                        phrase_tokens.append(child)
                
                if len(phrase_tokens) >= min_phrase_length:
                    phrase = " ".join([t.text for t in phrase_tokens])
                    if phrase and phrase not in key_phrases:
                        key_phrases.append(phrase)
                        phrase_scores[phrase] = 0.7
                        phrase_types[phrase] = "verb_phrase"
        
        # Sort by score and return top phrases
        sorted_phrases = sorted(key_phrases, key=lambda p: phrase_scores.get(p, 0), reverse=True)
        top_phrases = sorted_phrases[:max_phrases]
        
        return {
            "key_phrases": top_phrases,
            "phrase_scores": {p: phrase_scores.get(p, 0) for p in top_phrases},
            "phrase_types": {p: phrase_types.get(p, "unknown") for p in top_phrases}
        }
    
    async def _fallback_key_phrase_extraction(self, text: str, max_phrases: int, min_phrase_length: int) -> Dict[str, Any]:
        """Fallback key phrase extraction using simple methods."""
        # Simple approach: extract multi-word sequences
        words = text.split()
        key_phrases = []
        phrase_scores = {}
        phrase_types = {}
        
        # Extract n-grams
        for n in range(min_phrase_length, min(5, len(words) + 1)):
            for i in range(len(words) - n + 1):
                phrase = " ".join(words[i:i+n])
                if phrase and len(phrase) > 3:  # Skip very short phrases
                    key_phrases.append(phrase)
                    # Score based on length
                    phrase_scores[phrase] = min(n * 0.2, 1.0)
                    phrase_types[phrase] = f"{n}_gram"
        
        # Remove duplicates and sort
        unique_phrases = list(set(key_phrases))
        sorted_phrases = sorted(unique_phrases, key=lambda p: phrase_scores.get(p, 0), reverse=True)
        top_phrases = sorted_phrases[:max_phrases]
        
        return {
            "key_phrases": top_phrases,
            "phrase_scores": {p: phrase_scores.get(p, 0) for p in top_phrases},
            "phrase_types": {p: phrase_types.get(p, "unknown") for p in top_phrases}
        }
    
    async def _spacy_text_normalization(self, text: str, options: Dict[str, bool]) -> Dict[str, Any]:
        """Normalize text using spaCy processing."""
        # Run spaCy processing in thread pool
        loop = asyncio.get_event_loop()
        doc = await loop.run_in_executor(None, self.nlp, text)
        
        normalized_tokens = []
        normalizations_applied = []
        
        for token in doc:
            normalized_token = token.text
            
            # Apply normalization options
            if options.get("lemmatize", False) and not token.is_punct:
                normalized_token = token.lemma_
                if "lemmatize" not in normalizations_applied:
                    normalizations_applied.append("lemmatize")
            
            if options.get("lowercase", False):
                normalized_token = normalized_token.lower()
                if "lowercase" not in normalizations_applied:
                    normalizations_applied.append("lowercase")
            
            if options.get("remove_punctuation", False) and token.is_punct:
                continue  # Skip punctuation
            
            if options.get("remove_stopwords", False) and token.is_stop:
                continue  # Skip stop words
            
            normalized_tokens.append(normalized_token)
        
        # Join tokens and handle whitespace
        normalized_text = " ".join(normalized_tokens)
        
        if options.get("remove_whitespace", False):
            normalized_text = " ".join(normalized_text.split())
            if "remove_whitespace" not in normalizations_applied:
                normalizations_applied.append("remove_whitespace")
        
        return {
            "normalized_text": normalized_text,
            "normalizations_applied": normalizations_applied
        }
    
    async def _fallback_text_normalization(self, text: str, options: Dict[str, bool]) -> Dict[str, Any]:
        """Fallback text normalization using simple string operations."""
        normalized_text = text
        normalizations_applied = []
        
        if options.get("lowercase", False):
            normalized_text = normalized_text.lower()
            normalizations_applied.append("lowercase")
        
        if options.get("remove_punctuation", False):
            import string
            normalized_text = normalized_text.translate(str.maketrans('', '', string.punctuation))
            normalizations_applied.append("remove_punctuation")
        
        if options.get("remove_whitespace", False):
            normalized_text = " ".join(normalized_text.split())
            normalizations_applied.append("remove_whitespace")
        
        return {
            "normalized_text": normalized_text,
            "normalizations_applied": normalizations_applied
        }
    
    async def _spacy_structure_analysis(self, text: str) -> Dict[str, Any]:
        """Analyze text structure using spaCy."""
        # Run spaCy processing in thread pool
        loop = asyncio.get_event_loop()
        doc = await loop.run_in_executor(None, self.nlp, text)
        
        # Analyze sentence structure
        sentences = [sent.text.strip() for sent in doc.sents]
        
        # Extract key structural elements
        structure = {
            "sentence_count": len(sentences),
            "token_count": len(doc),
            "avg_sentence_length": len(doc) / len(sentences) if sentences else 0,
            "complexity_score": self._calculate_complexity_score(doc)
        }
        
        # Extract key information
        key_information = {
            "main_entities": [ent.text for ent in doc.ents[:5]],  # Top 5 entities
            "main_verbs": [token.lemma_ for token in doc if token.pos_ == "VERB" and not token.is_stop][:5],
            "main_nouns": [token.lemma_ for token in doc if token.pos_ == "NOUN" and not token.is_stop][:5]
        }
        
        # Extract relationships
        relationships = []
        for token in doc:
            if token.dep_ in ["nsubj", "dobj", "pobj"] and token.head.pos_ == "VERB":
                relationship = {
                    "subject": token.text,
                    "predicate": token.head.text,
                    "relationship_type": token.dep_,
                    "confidence": 0.7
                }
                relationships.append(relationship)
        
        return {
            "structure": structure,
            "key_information": key_information,
            "relationships": relationships[:10]  # Limit to top 10
        }
    
    async def _fallback_structure_analysis(self, text: str) -> Dict[str, Any]:
        """Fallback structure analysis using simple methods."""
        sentences = text.split('.')
        sentences = [s.strip() for s in sentences if s.strip()]
        words = text.split()
        
        structure = {
            "sentence_count": len(sentences),
            "token_count": len(words),
            "avg_sentence_length": len(words) / len(sentences) if sentences else 0,
            "complexity_score": min(len(words) / 100, 1.0)  # Simple complexity
        }
        
        # Simple key information extraction
        key_information = {
            "main_entities": [],  # No entity extraction in fallback
            "main_verbs": [],     # No POS tagging in fallback
            "main_nouns": []      # No POS tagging in fallback
        }
        
        relationships = []  # No relationship extraction in fallback
        
        return {
            "structure": structure,
            "key_information": key_information,
            "relationships": relationships
        }
    
    def _calculate_complexity_score(self, doc) -> float:
        """Calculate text complexity score based on various factors."""
        if not doc:
            return 0.0
        
        # Factors for complexity
        avg_word_length = sum(len(token.text) for token in doc if not token.is_punct) / len([t for t in doc if not t.is_punct])
        unique_words = len(set(token.lemma_.lower() for token in doc if not token.is_stop and not token.is_punct))
        total_words = len([t for t in doc if not t.is_stop and not t.is_punct])
        lexical_diversity = unique_words / total_words if total_words > 0 else 0
        
        # Dependency depth (complexity of sentence structure)
        max_depth = 0
        for token in doc:
            depth = 0
            current = token
            while current.head != current:
                depth += 1
                current = current.head
                if depth > 10:  # Prevent infinite loops
                    break
            max_depth = max(max_depth, depth)
        
        # Combine factors
        complexity = (
            (avg_word_length / 10) * 0.3 +  # Word length factor
            lexical_diversity * 0.4 +        # Vocabulary diversity
            (max_depth / 10) * 0.3           # Syntactic complexity
        )
        
        return min(complexity, 1.0)
    
    async def enhance_memory_retrieval(
        self, 
        query_text: str, 
        memory_candidates: List[str]
    ) -> Dict[str, Any]:
        """
        Enhance memory retrieval using spaCy analysis for better matching.
        
        Args:
            query_text: The query text to match against
            memory_candidates: List of memory texts to score
            
        Returns:
            Dictionary with enhanced retrieval scores and analysis
        """
        if not query_text or not memory_candidates:
            return {
                "enhanced_scores": {},
                "analysis": {},
                "processing_time": 0.0,
                "used_fallback": True
            }
        
        start_time = time.time()
        
        try:
            # Analyze query text
            query_analysis = await self.analyze_structure(query_text)
            query_entities = await self.extract_entities_enhanced(query_text)
            query_phrases = await self.identify_key_phrases(query_text, max_phrases=5)
            
            enhanced_scores = {}
            analysis = {
                "query_entities": [e["text"] for e in query_entities.entities],
                "query_phrases": query_phrases.key_phrases,
                "matching_details": {}
            }
            
            # Score each memory candidate
            for i, memory_text in enumerate(memory_candidates):
                memory_id = f"memory_{i}"
                
                # Analyze memory text
                memory_entities = await self.extract_entities_enhanced(memory_text)
                memory_phrases = await self.identify_key_phrases(memory_text, max_phrases=5)
                
                # Calculate various similarity scores
                entity_overlap = len(set(e["text"] for e in query_entities.entities) & 
                                   set(e["text"] for e in memory_entities.entities))
                phrase_overlap = len(set(query_phrases.key_phrases) & 
                                   set(memory_phrases.key_phrases))
                
                # Normalize scores
                entity_score = entity_overlap / max(len(query_entities.entities), 1)
                phrase_score = phrase_overlap / max(len(query_phrases.key_phrases), 1)
                
                # Combined score with weights
                combined_score = (entity_score * 0.6 + phrase_score * 0.4)
                enhanced_scores[memory_id] = combined_score
                
                # Store matching details
                analysis["matching_details"][memory_id] = {
                    "entity_overlap": entity_overlap,
                    "phrase_overlap": phrase_overlap,
                    "entity_score": entity_score,
                    "phrase_score": phrase_score
                }
            
            processing_time = time.time() - start_time
            
            return {
                "enhanced_scores": enhanced_scores,
                "analysis": analysis,
                "processing_time": processing_time,
                "used_fallback": self.fallback_mode
            }
            
        except Exception as e:
            logger.error(f"Memory retrieval enhancement failed: {e}")
            # Return basic scores on error
            processing_time = time.time() - start_time
            return {
                "enhanced_scores": {f"memory_{i}": 0.5 for i in range(len(memory_candidates))},
                "analysis": {"error": str(e)},
                "processing_time": processing_time,
                "used_fallback": True
            }