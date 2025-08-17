"""
Credential analysis service for intelligent authentication system.

This module provides comprehensive credential analysis using NLP techniques,
including linguistic feature extraction, suspicious pattern detection,
and entropy calculation for security assessment.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import math
import re
import string
import time
from collections import Counter
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple, Any
from cachetools import TTLCache
import threading

from ai_karen_engine.security.models import (
    CredentialFeatures,
    NLPFeatures,
    IntelligentAuthConfig
)
from ai_karen_engine.security.intelligent_auth_base import (
    BaseIntelligentAuthService,
    CredentialAnalyzerInterface,
    ServiceHealthStatus,
    ServiceStatus
)
from ai_karen_engine.services.spacy_service import SpacyService, ParsedMessage
from ai_karen_engine.services.nlp_config import SpacyConfig

logger = logging.getLogger(__name__)


@dataclass
class SuspiciousPatternResult:
    """Result of suspicious pattern detection."""
    pattern_name: str
    detected: bool
    confidence: float
    details: Dict[str, Any]


class CredentialAnalyzer(BaseIntelligentAuthService, CredentialAnalyzerInterface):
    """
    Comprehensive credential analysis service using NLP and pattern detection.
    
    This service analyzes email addresses and password hashes to extract
    linguistic features, detect suspicious patterns, and assess credential
    strength using various NLP techniques.
    """

    def __init__(self, config: IntelligentAuthConfig, spacy_service: Optional[SpacyService] = None):
        super().__init__(config)
        self.spacy_service = spacy_service or SpacyService(SpacyConfig())
        
        # Initialize caching
        self.cache = TTLCache(
            maxsize=config.cache_size,
            ttl=config.cache_ttl
        )
        self.cache_lock = threading.RLock()
        
        # Performance metrics
        self._analysis_count = 0
        self._cache_hits = 0
        self._cache_misses = 0
        self._processing_times = []
        self._error_count = 0
        self._last_error = None
        
        # Suspicious pattern definitions
        self._initialize_pattern_detectors()
        
        # Language detection cache
        self._language_cache = TTLCache(maxsize=1000, ttl=7200)  # 2 hour TTL
        
        self.logger.info("CredentialAnalyzer initialized")

    def _initialize_pattern_detectors(self) -> None:
        """Initialize sophisticated suspicious pattern detection rules."""
        # Enhanced keyboard walk patterns (common sequences on QWERTY keyboard)
        self.keyboard_walks = {
            'qwerty_horizontal': ['qwer', 'wert', 'erty', 'rtyu', 'tyui', 'yuio', 'uiop',
                                 'asdf', 'sdfg', 'dfgh', 'fghj', 'ghjk', 'hjkl',
                                 'zxcv', 'xcvb', 'cvbn', 'vbnm'],
            'qwerty_vertical': ['qaz', 'wsx', 'edc', 'rfv', 'tgb', 'yhn', 'ujm', 'ik', 'ol'],
            'qwerty_diagonal': ['qwe', 'asd', 'zxc', 'poi', 'lkj', 'mnb'],
            'qwerty_reverse': ['rewq', 'trew', 'ytre', 'uytr', 'iuyt', 'oiuy', 'poiu',
                              'fdsa', 'gfds', 'hgfd', 'jhgf', 'kjhg', 'lkjh',
                              'vcxz', 'bvcx', 'nbvc', 'mnbv']
        }
        
        # Enhanced common password patterns with attack indicators
        self.common_patterns = {
            'repeated_chars': r'(.)\1{2,}',  # 3+ repeated characters
            'sequential_numbers': r'(012|123|234|345|456|567|678|789|890|987|876|765|654|543|432|321|210)',
            'sequential_letters': r'(abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz|zyx|yxw|xwv|wvu|vut|uts|tsr|srq|rqp|qpo|pon|onm|nml|mlk|lkj|kji|jih|ihg|hgf|gfe|fed|edc|dcb|cba)',
            'year_pattern': r'(19|20)\d{2}',
            'simple_substitution': r'[a@][s\$][e3][t7][o0][i1][l1]',  # Common l33t speak
            'keyboard_shift': r'[!@#$%^&*()_+]',  # Shifted number row
            'common_endings': r'(123|456|789|000|111|222|333|444|555|666|777|888|999)$',
            'common_beginnings': r'^(123|abc|qwe|asd|zxc|password|admin|user|test)',
            'alternating_case': r'([a-z][A-Z]|[A-Z][a-z]){3,}',  # Alternating case patterns
            'phone_pattern': r'\d{3}[-.]?\d{3}[-.]?\d{4}',  # Phone number patterns
            'ssn_pattern': r'\d{3}[-.]?\d{2}[-.]?\d{4}',  # SSN patterns
            'credit_card_pattern': r'\d{4}[-.\s]?\d{4}[-.\s]?\d{4}[-.\s]?\d{4}',  # Credit card patterns
            'base64_pattern': r'[A-Za-z0-9+/]{20,}={0,2}',  # Base64 encoded strings
            'hex_pattern': r'[0-9a-fA-F]{16,}',  # Long hex strings
            'url_pattern': r'https?://[^\s]+',  # URL patterns
            'email_pattern': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',  # Email patterns
        }
        
        # Attack-specific patterns
        self.attack_patterns = {
            'brute_force_indicators': [
                r'(password|pass|pwd)\d+',  # password123, pass456
                r'(admin|root|user)\d+',    # admin123, root456
                r'(test|demo|guest)\d+',    # test123, demo456
                r'(login|auth|access)\d+',  # login123, auth456
            ],
            'credential_stuffing_indicators': [
                r'[a-zA-Z]+\d{4,}',         # Common pattern: word + 4+ digits
                r'\d{4,}[a-zA-Z]+',         # Common pattern: 4+ digits + word
                r'[a-zA-Z]+[!@#$%]\d+',     # word + special char + digits
            ],
            'dictionary_attack_indicators': [
                r'^[a-zA-Z]+$',             # Pure alphabetic (dictionary words)
                r'^[a-zA-Z]+\d{1,3}$',      # Dictionary word + 1-3 digits
                r'^[A-Z][a-z]+\d{1,3}$',   # Capitalized word + digits
            ]
        }
        
        # Language-specific suspicious patterns
        self.language_patterns = {
            'english_weak': [
                'password', 'admin', 'user', 'login', 'guest', 'test', 'demo',
                'welcome', 'secret', 'private', 'confidential', 'secure',
                'master', 'super', 'root', 'system', 'default'
            ],
            'common_names': [
                'john', 'jane', 'mike', 'mary', 'david', 'sarah', 'chris', 'lisa',
                'robert', 'jennifer', 'michael', 'jessica', 'william', 'ashley'
            ],
            'common_words': [
                'love', 'hate', 'life', 'work', 'home', 'family', 'friend',
                'money', 'time', 'world', 'people', 'place', 'thing'
            ]
        }
        
        # Compile regex patterns for performance
        self.compiled_patterns = {
            name: re.compile(pattern, re.IGNORECASE)
            for name, pattern in self.common_patterns.items()
        }
        
        # Compile attack patterns
        self.compiled_attack_patterns = {}
        for attack_type, patterns in self.attack_patterns.items():
            self.compiled_attack_patterns[attack_type] = [
                re.compile(pattern, re.IGNORECASE) for pattern in patterns
            ]

    async def initialize(self) -> bool:
        """Initialize the credential analyzer service."""
        try:
            # Test spaCy service
            test_result = await self.spacy_service.parse_message("test")
            if test_result is None:
                self.logger.warning("spaCy service test failed, using fallback mode")
            
            self.logger.info("CredentialAnalyzer initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize CredentialAnalyzer: {e}")
            self._error_count += 1
            self._last_error = str(e)
            return False

    async def shutdown(self) -> None:
        """Gracefully shutdown the service."""
        with self.cache_lock:
            self.cache.clear()
            self._language_cache.clear()
        self.logger.info("CredentialAnalyzer shutdown complete")

    async def _perform_health_check(self) -> bool:
        """Perform health check for the credential analyzer."""
        try:
            # Test basic functionality
            test_features = await self._analyze_text_features("test@example.com", is_email=True)
            
            # Check spaCy service health
            spacy_health = self.spacy_service.get_health_status()
            
            return (
                test_features is not None and
                (spacy_health.is_healthy or spacy_health.fallback_mode)
            )
            
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False

    async def analyze_credentials_batch(self, credential_pairs: List[Tuple[str, str]]) -> List[NLPFeatures]:
        """
        Analyze multiple credential pairs in batch for improved performance.
        
        Args:
            credential_pairs: List of (email, password_hash) tuples to analyze
            
        Returns:
            List of NLPFeatures for each credential pair
        """
        if not credential_pairs:
            return []
        
        start_time = time.time()
        results = []
        
        try:
            # Process in batches to avoid overwhelming the system
            batch_size = min(self.config.batch_size, len(credential_pairs))
            
            for i in range(0, len(credential_pairs), batch_size):
                batch = credential_pairs[i:i + batch_size]
                
                # Process batch concurrently
                batch_tasks = [
                    self.analyze_credentials(email, password_hash)
                    for email, password_hash in batch
                ]
                
                batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
                
                # Handle any exceptions in batch results
                for j, result in enumerate(batch_results):
                    if isinstance(result, Exception):
                        self.logger.error(f"Batch analysis failed for item {i+j}: {result}")
                        # Create fallback result
                        email, password_hash = batch[j]
                        fallback_result = self._create_fallback_nlp_features(
                            email, password_hash, 0.0
                        )
                        results.append(fallback_result)
                    else:
                        results.append(result)
            
            processing_time = time.time() - start_time
            self.logger.info(f"Batch analysis completed: {len(credential_pairs)} items in {processing_time:.3f}s")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Batch credential analysis failed: {e}")
            self._error_count += 1
            self._last_error = str(e)
            
            # Return fallback results for all items
            return [
                self._create_fallback_nlp_features(email, password_hash, 0.0)
                for email, password_hash in credential_pairs
            ]

    async def analyze_credentials(self, email: str, password_hash: str) -> NLPFeatures:
        """
        Analyze credentials and extract comprehensive NLP features.
        
        Args:
            email: Email address to analyze
            password_hash: Hashed password for pattern analysis (not plaintext)
            
        Returns:
            NLPFeatures containing comprehensive analysis results
        """
        start_time = time.time()
        
        try:
            # Check cache first
            cache_key = self._get_cache_key(email, password_hash)
            with self.cache_lock:
                if cache_key in self.cache:
                    self._cache_hits += 1
                    cached_result = self.cache[cache_key]
                    # Update processing time for cached result
                    cached_result.processing_time = time.time() - start_time
                    return cached_result
                self._cache_misses += 1

            # Analyze email features
            email_features = await self._analyze_text_features(email, is_email=True)
            
            # Analyze password hash features (limited analysis for security)
            password_features = await self._analyze_text_features(password_hash, is_email=False)
            
            # Calculate credential similarity
            credential_similarity = await self._calculate_credential_similarity(email, password_hash)
            
            # Check language consistency
            language_consistency = await self._check_language_consistency(email, password_hash)
            
            # Detect suspicious patterns across both credentials
            suspicious_patterns = await self._detect_combined_suspicious_patterns(email, password_hash)
            
            # Create NLP features result
            processing_time = time.time() - start_time
            spacy_health = self.spacy_service.get_health_status()
            
            result = NLPFeatures(
                email_features=email_features,
                password_features=password_features,
                credential_similarity=credential_similarity,
                language_consistency=language_consistency,
                suspicious_patterns=suspicious_patterns,
                processing_time=processing_time,
                used_fallback=spacy_health.fallback_mode,
                model_version='spacy-model' if not spacy_health.fallback_mode else 'fallback'
            )
            
            # Cache the result
            with self.cache_lock:
                self.cache[cache_key] = result
            
            # Update metrics
            self._analysis_count += 1
            self._processing_times.append(processing_time)
            if len(self._processing_times) > 1000:
                self._processing_times = self._processing_times[-1000:]
            
            return result
            
        except Exception as e:
            self.logger.error(f"Credential analysis failed: {e}")
            self._error_count += 1
            self._last_error = str(e)
            
            # Return fallback result
            processing_time = time.time() - start_time
            return self._create_fallback_nlp_features(email, password_hash, processing_time)

    async def _analyze_text_features(self, text: str, is_email: bool = False) -> CredentialFeatures:
        """
        Analyze linguistic features of text using spaCy and pattern detection.
        
        Args:
            text: Text to analyze
            is_email: Whether the text is an email address
            
        Returns:
            CredentialFeatures with extracted features
        """
        try:
            # Parse with spaCy
            parsed = await self.spacy_service.parse_message(text)
            
            # Extract basic features
            token_count = len(parsed.tokens)
            unique_tokens = set(parsed.tokens)
            unique_token_ratio = len(unique_tokens) / token_count if token_count > 0 else 0.0
            
            # Calculate entropy
            entropy_score = self._calculate_entropy(text)
            
            # Detect language
            language = await self._detect_language(text, parsed)
            
            # Detect suspicious patterns
            suspicious_patterns = await self.detect_suspicious_patterns(text)
            contains_suspicious = len(suspicious_patterns) > 0
            
            return CredentialFeatures(
                token_count=token_count,
                unique_token_ratio=unique_token_ratio,
                entropy_score=entropy_score,
                language=language,
                contains_suspicious_patterns=contains_suspicious,
                pattern_types=suspicious_patterns
            )
            
        except Exception as e:
            self.logger.error(f"Text feature analysis failed: {e}")
            # Return basic fallback features
            return CredentialFeatures(
                token_count=len(text.split()),
                unique_token_ratio=0.5,  # Default assumption
                entropy_score=self._calculate_entropy(text),
                language="unknown",
                contains_suspicious_patterns=False,
                pattern_types=[]
            )

    async def detect_suspicious_patterns(self, text: str) -> List[str]:
        """
        Detect suspicious patterns in credential text using advanced algorithms.
        
        Args:
            text: Text to analyze for suspicious patterns
            
        Returns:
            List of detected pattern names with confidence scores
        """
        detected_patterns = []
        text_lower = text.lower()
        
        try:
            # Check compiled regex patterns
            for pattern_name, compiled_pattern in self.compiled_patterns.items():
                if compiled_pattern.search(text):
                    detected_patterns.append(pattern_name)
            
            # Check keyboard walks with enhanced detection
            keyboard_patterns = self._detect_keyboard_walks(text_lower)
            detected_patterns.extend(keyboard_patterns)
            
            # Check attack-specific patterns
            attack_patterns = self._detect_attack_patterns(text_lower)
            detected_patterns.extend(attack_patterns)
            
            # Check language-specific weak patterns
            language_patterns = self._detect_language_specific_patterns(text_lower)
            detected_patterns.extend(language_patterns)
            
            # Check for common weak patterns
            if self._check_common_weak_patterns(text_lower):
                detected_patterns.append("common_weak_pattern")
            
            # Check for dictionary words (enhanced check)
            if await self._contains_dictionary_words(text_lower):
                detected_patterns.append("dictionary_words")
            
            # Check for personal information patterns
            if self._check_personal_info_patterns(text_lower):
                detected_patterns.append("personal_info")
            
            # Check for statistical anomalies
            statistical_patterns = self._detect_statistical_anomalies(text)
            detected_patterns.extend(statistical_patterns)
            
            # Check for encoding patterns
            encoding_patterns = self._detect_encoding_patterns(text)
            detected_patterns.extend(encoding_patterns)
            
        except Exception as e:
            self.logger.error(f"Pattern detection failed: {e}")
        
        return list(set(detected_patterns))  # Remove duplicates

    def _calculate_entropy(self, text: str) -> float:
        """
        Calculate Shannon entropy of text.
        
        Args:
            text: Text to calculate entropy for
            
        Returns:
            Entropy score (higher = more random)
        """
        if not text:
            return 0.0
        
        # Count character frequencies
        char_counts = Counter(text)
        text_length = len(text)
        
        # Calculate entropy
        entropy = 0.0
        for count in char_counts.values():
            probability = count / text_length
            if probability > 0:
                entropy -= probability * math.log2(probability)
        
        return entropy

    async def _detect_language(self, text: str, parsed: ParsedMessage) -> str:
        """
        Detect language of text using spaCy and caching.
        
        Args:
            text: Text to analyze
            parsed: Parsed message from spaCy
            
        Returns:
            Detected language code
        """
        # Check cache first
        cache_key = hashlib.md5(text.encode()).hexdigest()
        if cache_key in self._language_cache:
            return self._language_cache[cache_key]
        
        try:
            # Use spaCy's language detection if available
            if not parsed.used_fallback and parsed.language:
                language = parsed.language
            else:
                # Fallback language detection
                language = self._fallback_language_detection(text)
            
            # Cache the result
            self._language_cache[cache_key] = language
            return language
            
        except Exception as e:
            self.logger.error(f"Language detection failed: {e}")
            return "unknown"

    def _fallback_language_detection(self, text: str) -> str:
        """
        Simple fallback language detection based on character patterns.
        
        Args:
            text: Text to analyze
            
        Returns:
            Detected language code
        """
        # Simple heuristics for common languages
        if not text:
            return "unknown"
        
        # Check for ASCII-only (likely English)
        if all(ord(char) < 128 for char in text):
            return "en"
        
        # Check for common non-ASCII patterns
        if any(ord(char) > 127 for char in text):
            # Could be various languages, default to multilingual
            return "multi"
        
        return "en"  # Default to English

    async def _calculate_credential_similarity(self, email: str, password_hash: str) -> float:
        """
        Calculate similarity between email and password hash.
        
        Args:
            email: Email address
            password_hash: Password hash
            
        Returns:
            Similarity score (0.0 to 1.0)
        """
        try:
            # Extract username from email
            username = email.split('@')[0] if '@' in email else email
            
            # Simple character-based similarity
            # Note: We're comparing with hash, so this is limited
            common_chars = set(username.lower()) & set(password_hash.lower())
            total_chars = set(username.lower()) | set(password_hash.lower())
            
            if not total_chars:
                return 0.0
            
            similarity = len(common_chars) / len(total_chars)
            
            # Additional checks for obvious patterns
            if username.lower() in password_hash.lower():
                similarity = max(similarity, 0.8)  # High similarity if username in hash
            
            return min(similarity, 1.0)
            
        except Exception as e:
            self.logger.error(f"Similarity calculation failed: {e}")
            return 0.0

    async def _check_language_consistency(self, email: str, password_hash: str) -> bool:
        """
        Check if email and password hash have consistent language patterns.
        
        Args:
            email: Email address
            password_hash: Password hash
            
        Returns:
            True if languages are consistent
        """
        try:
            # Parse both texts
            email_parsed = await self.spacy_service.parse_message(email)
            hash_parsed = await self.spacy_service.parse_message(password_hash)
            
            email_lang = await self._detect_language(email, email_parsed)
            hash_lang = await self._detect_language(password_hash, hash_parsed)
            
            # Consider consistency
            if email_lang == "unknown" or hash_lang == "unknown":
                return True  # Can't determine inconsistency
            
            return email_lang == hash_lang or "multi" in [email_lang, hash_lang]
            
        except Exception as e:
            self.logger.error(f"Language consistency check failed: {e}")
            return True  # Default to consistent on error

    async def _detect_combined_suspicious_patterns(self, email: str, password_hash: str) -> List[str]:
        """
        Detect suspicious patterns across both email and password hash.
        
        Args:
            email: Email address
            password_hash: Password hash
            
        Returns:
            List of detected suspicious patterns
        """
        patterns = []
        
        try:
            # Get individual patterns
            email_patterns = await self.detect_suspicious_patterns(email)
            hash_patterns = await self.detect_suspicious_patterns(password_hash)
            
            # Combine and deduplicate
            all_patterns = set(email_patterns + hash_patterns)
            patterns.extend(all_patterns)
            
            # Check for cross-credential patterns
            if self._check_credential_reuse_patterns(email, password_hash):
                patterns.append("credential_reuse_pattern")
            
            if self._check_weak_combination_patterns(email, password_hash):
                patterns.append("weak_combination")
            
        except Exception as e:
            self.logger.error(f"Combined pattern detection failed: {e}")
        
        return patterns

    def _check_common_weak_patterns(self, text: str) -> bool:
        """Check for common weak password patterns."""
        weak_patterns = [
            'password', 'pass', '123', 'admin', 'user', 'login',
            'welcome', 'qwerty', 'abc', 'test', 'demo'
        ]
        
        return any(pattern in text for pattern in weak_patterns)

    async def _contains_dictionary_words(self, text: str) -> bool:
        """
        Check if text contains common dictionary words.
        
        This is a simplified implementation. In production, you might want
        to use a proper dictionary or word list.
        """
        # Simple check for common English words
        common_words = {
            'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had',
            'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his',
            'how', 'man', 'new', 'now', 'old', 'see', 'two', 'way', 'who', 'boy',
            'did', 'its', 'let', 'put', 'say', 'she', 'too', 'use'
        }
        
        # Check if any common words are in the text
        text_words = set(text.lower().split())
        return len(text_words & common_words) > 0

    def _check_personal_info_patterns(self, text: str) -> bool:
        """Check for patterns that might indicate personal information."""
        # Simple patterns for names, dates, etc.
        personal_patterns = [
            (r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)', re.IGNORECASE),  # Month abbreviations
            (r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', 0),  # Date patterns
            (r'[A-Z][a-z]+', 0),  # Capitalized words (potential names) - no IGNORECASE
        ]
        
        for pattern, flags in personal_patterns:
            if re.search(pattern, text, flags):
                return True
        
        return False

    def _check_credential_reuse_patterns(self, email: str, password_hash: str) -> bool:
        """Check for patterns indicating credential reuse."""
        try:
            username = email.split('@')[0] if '@' in email else email
            
            # Check if username appears in hash (simplified check)
            if len(username) > 3 and username.lower() in password_hash.lower():
                return True
            
            # Check for domain reuse patterns
            if '@' in email:
                domain = email.split('@')[1].split('.')[0]
                if len(domain) > 3 and domain.lower() in password_hash.lower():
                    return True
            
            return False
            
        except Exception:
            return False

    def _check_weak_combination_patterns(self, email: str, password_hash: str) -> bool:
        """Check for weak combinations of email and password."""
        try:
            # Check for very short credentials
            if len(email) < 6 or len(password_hash) < 10:  # Hash should be longer
                return True
            
            # Check for repeated patterns
            if email.count('@') != 1:  # Invalid email format
                return True
            
            return False
            
        except Exception:
            return False

    def _create_fallback_nlp_features(self, email: str, password_hash: str, 
                                    processing_time: float) -> NLPFeatures:
        """Create fallback NLP features when analysis fails."""
        # Create basic features
        email_features = CredentialFeatures(
            token_count=len(email.split()),
            unique_token_ratio=0.8,  # Reasonable default
            entropy_score=self._calculate_entropy(email),
            language="unknown",
            contains_suspicious_patterns=False,
            pattern_types=[]
        )
        
        password_features = CredentialFeatures(
            token_count=len(password_hash),
            unique_token_ratio=0.9,  # Hash should have high uniqueness
            entropy_score=self._calculate_entropy(password_hash),
            language="unknown",
            contains_suspicious_patterns=False,
            pattern_types=[]
        )
        
        return NLPFeatures(
            email_features=email_features,
            password_features=password_features,
            credential_similarity=0.0,
            language_consistency=True,
            suspicious_patterns=[],
            processing_time=processing_time,
            used_fallback=True,
            model_version="fallback"
        )

    def _get_cache_key(self, email: str, password_hash: str) -> str:
        """Generate cache key for credential analysis."""
        combined = f"{email}:{password_hash}"
        return f"cred_analysis:{hashlib.md5(combined.encode()).hexdigest()}"

    def _detect_keyboard_walks(self, text: str) -> List[str]:
        """
        Enhanced keyboard walk detection with confidence scoring.
        
        Args:
            text: Text to analyze for keyboard walks
            
        Returns:
            List of detected keyboard walk patterns
        """
        detected_patterns = []
        
        try:
            # Check all keyboard walk types
            for walk_type, walks in self.keyboard_walks.items():
                for walk in walks:
                    if walk in text:
                        pattern_name = f"keyboard_walk_{walk_type}"
                        if pattern_name not in detected_patterns:
                            detected_patterns.append(pattern_name)
                        break  # Only add each walk type once
            
            # Check for longer keyboard walks (5+ characters)
            for i in range(len(text) - 4):
                substring = text[i:i+5]
                for walk_type, walks in self.keyboard_walks.items():
                    for walk in walks:
                        if len(walk) >= 4 and walk in substring:
                            pattern_name = f"long_keyboard_walk_{walk_type}"
                            if pattern_name not in detected_patterns:
                                detected_patterns.append(pattern_name)
                            break
                            
        except Exception as e:
            self.logger.error(f"Keyboard walk detection failed: {e}")
        
        return detected_patterns

    def _detect_attack_patterns(self, text: str) -> List[str]:
        """
        Detect attack-specific patterns in text.
        
        Args:
            text: Text to analyze for attack patterns
            
        Returns:
            List of detected attack pattern names
        """
        detected_patterns = []
        
        try:
            # Check compiled attack patterns
            for attack_type, compiled_patterns in self.compiled_attack_patterns.items():
                for pattern in compiled_patterns:
                    if pattern.search(text):
                        detected_patterns.append(attack_type)
                        break  # Only add each attack type once
            
            # Additional attack pattern checks
            if self._check_brute_force_patterns(text):
                detected_patterns.append("brute_force_pattern")
            
            if self._check_credential_stuffing_patterns(text):
                detected_patterns.append("credential_stuffing_pattern")
            
            if self._check_dictionary_attack_patterns(text):
                detected_patterns.append("dictionary_attack_pattern")
                
        except Exception as e:
            self.logger.error(f"Attack pattern detection failed: {e}")
        
        return detected_patterns

    def _detect_language_specific_patterns(self, text: str) -> List[str]:
        """
        Detect language-specific suspicious patterns.
        
        Args:
            text: Text to analyze for language-specific patterns
            
        Returns:
            List of detected language-specific pattern names
        """
        detected_patterns = []
        
        try:
            # Check English weak patterns
            for weak_word in self.language_patterns['english_weak']:
                if weak_word in text:
                    detected_patterns.append("english_weak_word")
                    break
            
            # Check common names
            for name in self.language_patterns['common_names']:
                if name in text:
                    detected_patterns.append("common_name")
                    break
            
            # Check common words
            common_word_count = 0
            for word in self.language_patterns['common_words']:
                if word in text:
                    common_word_count += 1
            
            if common_word_count >= 2:  # Multiple common words
                detected_patterns.append("multiple_common_words")
            elif common_word_count == 1:
                detected_patterns.append("common_word")
                
        except Exception as e:
            self.logger.error(f"Language-specific pattern detection failed: {e}")
        
        return detected_patterns

    def _detect_statistical_anomalies(self, text: str) -> List[str]:
        """
        Detect statistical anomalies in text patterns.
        
        Args:
            text: Text to analyze for statistical anomalies
            
        Returns:
            List of detected statistical anomaly patterns
        """
        detected_patterns = []
        
        try:
            if not text:
                return detected_patterns
            
            # Character frequency analysis
            char_freq = Counter(text.lower())
            total_chars = len(text)
            
            # Check for extremely low entropy (repeated characters)
            entropy = self._calculate_entropy(text)
            if entropy < 1.0:  # Very low entropy
                detected_patterns.append("low_entropy")
            elif entropy < 2.0:  # Moderately low entropy
                detected_patterns.append("moderate_low_entropy")
            
            # Check for character distribution anomalies
            if char_freq:
                most_common_char, most_common_count = char_freq.most_common(1)[0]
                if most_common_count / total_chars >= 0.5:  # One character >= 50%
                    detected_patterns.append("character_dominance")
            
            # Check for lack of character diversity
            unique_chars = len(char_freq)
            if unique_chars < 4 and total_chars > 6:  # Few unique chars in long text
                detected_patterns.append("low_character_diversity")
            
            # Check for numeric dominance
            digit_count = sum(1 for c in text if c.isdigit())
            if digit_count / total_chars > 0.7:  # >70% digits
                detected_patterns.append("numeric_dominance")
            
            # Check for alphabetic dominance
            alpha_count = sum(1 for c in text if c.isalpha())
            if alpha_count / total_chars > 0.9:  # >90% letters
                detected_patterns.append("alphabetic_dominance")
            
            # Check for special character patterns
            special_count = sum(1 for c in text if not c.isalnum())
            if special_count / total_chars > 0.3:  # >30% special chars
                detected_patterns.append("high_special_chars")
                
        except Exception as e:
            self.logger.error(f"Statistical anomaly detection failed: {e}")
        
        return detected_patterns

    def _detect_encoding_patterns(self, text: str) -> List[str]:
        """
        Detect encoding-related patterns that might indicate obfuscation.
        
        Args:
            text: Text to analyze for encoding patterns
            
        Returns:
            List of detected encoding pattern names
        """
        detected_patterns = []
        
        try:
            # Check for Base64 patterns
            if re.search(r'^[A-Za-z0-9+/]{16,}={0,2}$', text):
                detected_patterns.append("base64_encoded")
            
            # Check for hexadecimal patterns
            if re.search(r'^[0-9a-fA-F]{16,}$', text):
                detected_patterns.append("hex_encoded")
            
            # Check for URL encoding
            if '%' in text and re.search(r'%[0-9a-fA-F]{2}', text):
                detected_patterns.append("url_encoded")
            
            # Check for Unicode escape sequences
            if re.search(r'\\u[0-9a-fA-F]{4}', text):
                detected_patterns.append("unicode_escaped")
            
            # Check for HTML entity encoding
            if re.search(r'&[a-zA-Z]+;|&#\d+;', text):
                detected_patterns.append("html_encoded")
            
            # Check for ROT13 patterns (simple heuristic)
            if self._check_rot13_pattern(text):
                detected_patterns.append("rot13_pattern")
                
        except Exception as e:
            self.logger.error(f"Encoding pattern detection failed: {e}")
        
        return detected_patterns

    def _check_brute_force_patterns(self, text: str) -> bool:
        """Check for patterns typical of brute force attacks."""
        brute_force_indicators = [
            r'(password|pass|pwd)\d+$',  # password followed by numbers
            r'^(admin|root|user)\d+$',   # admin/root/user followed by numbers
            r'^[a-z]+\d{1,3}$',          # simple word + 1-3 digits
            r'^\d{4,8}$',                # pure numeric (common in brute force)
        ]
        
        for pattern in brute_force_indicators:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        return False

    def _check_credential_stuffing_patterns(self, text: str) -> bool:
        """Check for patterns typical of credential stuffing attacks."""
        stuffing_indicators = [
            r'^[a-zA-Z]{3,8}\d{4,8}$',   # word + 4-8 digits (common pattern)
            r'^\d{4,8}[a-zA-Z]{3,8}$',   # digits + word
            r'^[a-zA-Z]+[!@#$%]\d+$',    # word + special + digits
            r'^[a-zA-Z]+_\d+$',          # word_digits
            r'^[a-zA-Z]+\.\d+$',         # word.digits
        ]
        
        for pattern in stuffing_indicators:
            if re.search(pattern, text):
                return True
        
        return False

    def _check_dictionary_attack_patterns(self, text: str) -> bool:
        """Check for patterns typical of dictionary attacks."""
        dictionary_indicators = [
            r'^[a-zA-Z]{4,10}$',         # Pure alphabetic (dictionary words) - reduced max length
            r'^[a-zA-Z]{4,10}\d{1,3}$',  # Dictionary word + 1-3 digits - reduced max length
            r'^[A-Z][a-z]{3,9}$',        # Capitalized word - reduced max length
            r'^[a-z]{4,10}[!@#$%]$',     # Word + single special char - reduced max length
        ]
        
        for pattern in dictionary_indicators:
            if re.search(pattern, text):
                return True
        
        return False

    def _check_rot13_pattern(self, text: str) -> bool:
        """
        Simple heuristic to detect ROT13 encoding.
        
        Args:
            text: Text to check for ROT13 patterns
            
        Returns:
            True if text might be ROT13 encoded
        """
        try:
            # ROT13 decode
            rot13_decoded = text.translate(str.maketrans(
                'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz',
                'NOPQRSTUVWXYZABCDEFGHIJKLMnopqrstuvwxyzabcdefghijklm'
            ))
            
            # Check if decoded text contains common English words
            common_words = {'password', 'admin', 'user', 'login', 'secret', 'the', 'and', 'for'}
            decoded_lower = rot13_decoded.lower()
            
            return any(word in decoded_lower for word in common_words)
            
        except Exception:
            return False

    async def warm_cache(self, credential_pairs: List[Tuple[str, str]]) -> None:
        """
        Pre-warm the cache with commonly analyzed credential pairs.
        
        Args:
            credential_pairs: List of (email, password_hash) tuples to pre-analyze
        """
        self.logger.info(f"Warming cache with {len(credential_pairs)} credential pairs")
        
        try:
            # Analyze in batches to warm the cache
            await self.analyze_credentials_batch(credential_pairs)
            self.logger.info("Cache warming completed successfully")
            
        except Exception as e:
            self.logger.error(f"Cache warming failed: {e}")

    def optimize_cache_settings(self, hit_rate_threshold: float = 0.8) -> Dict[str, Any]:
        """
        Optimize cache settings based on current performance metrics.
        
        Args:
            hit_rate_threshold: Minimum acceptable cache hit rate
            
        Returns:
            Dictionary with optimization recommendations
        """
        with self.cache_lock:
            cache_total = self._cache_hits + self._cache_misses
            current_hit_rate = self._cache_hits / cache_total if cache_total > 0 else 0.0
            
            recommendations = {
                'current_hit_rate': current_hit_rate,
                'target_hit_rate': hit_rate_threshold,
                'current_cache_size': len(self.cache),
                'max_cache_size': self.cache.maxsize,
                'recommendations': []
            }
            
            if current_hit_rate < hit_rate_threshold:
                if len(self.cache) >= self.cache.maxsize * 0.9:
                    recommendations['recommendations'].append({
                        'action': 'increase_cache_size',
                        'current': self.cache.maxsize,
                        'suggested': int(self.cache.maxsize * 1.5),
                        'reason': 'Cache is near capacity and hit rate is low'
                    })
                
                recommendations['recommendations'].append({
                    'action': 'increase_ttl',
                    'current': self.config.cache_ttl,
                    'suggested': int(self.config.cache_ttl * 1.2),
                    'reason': 'Longer TTL may improve hit rate'
                })
            
            return recommendations

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics for the credential analyzer."""
        with self.cache_lock:
            cache_total = self._cache_hits + self._cache_misses
            cache_hit_rate = self._cache_hits / cache_total if cache_total > 0 else 0.0
            
            avg_processing_time = (
                sum(self._processing_times) / len(self._processing_times)
                if self._processing_times else 0.0
            )
            
            # Calculate percentiles for processing times
            processing_times_sorted = sorted(self._processing_times) if self._processing_times else []
            p50 = processing_times_sorted[len(processing_times_sorted)//2] if processing_times_sorted else 0.0
            p95 = processing_times_sorted[int(len(processing_times_sorted)*0.95)] if processing_times_sorted else 0.0
            p99 = processing_times_sorted[int(len(processing_times_sorted)*0.99)] if processing_times_sorted else 0.0
            
            return {
                'analysis_count': self._analysis_count,
                'cache_hit_rate': cache_hit_rate,
                'cache_hits': self._cache_hits,
                'cache_misses': self._cache_misses,
                'cache_size': len(self.cache),
                'cache_max_size': self.cache.maxsize,
                'language_cache_size': len(self._language_cache),
                'avg_processing_time': avg_processing_time,
                'processing_time_p50': p50,
                'processing_time_p95': p95,
                'processing_time_p99': p99,
                'error_count': self._error_count,
                'error_rate': self._error_count / max(self._analysis_count, 1),
                'last_error': self._last_error,
                'throughput_per_second': self._analysis_count / max(sum(self._processing_times), 1) if self._processing_times else 0.0
            }

    def get_cache_statistics(self) -> Dict[str, Any]:
        """Get detailed cache statistics for monitoring."""
        with self.cache_lock:
            cache_total = self._cache_hits + self._cache_misses
            
            return {
                'main_cache': {
                    'size': len(self.cache),
                    'max_size': self.cache.maxsize,
                    'utilization': len(self.cache) / self.cache.maxsize,
                    'hits': self._cache_hits,
                    'misses': self._cache_misses,
                    'hit_rate': self._cache_hits / cache_total if cache_total > 0 else 0.0,
                    'ttl': self.config.cache_ttl
                },
                'language_cache': {
                    'size': len(self._language_cache),
                    'max_size': self._language_cache.maxsize,
                    'utilization': len(self._language_cache) / self._language_cache.maxsize,
                    'ttl': 7200  # 2 hours
                }
            }

    async def precompute_common_patterns(self, common_texts: List[str]) -> None:
        """
        Precompute pattern detection for commonly analyzed texts.
        
        Args:
            common_texts: List of common text patterns to precompute
        """
        self.logger.info(f"Precomputing patterns for {len(common_texts)} common texts")
        
        try:
            # Precompute pattern detection results
            for text in common_texts:
                await self.detect_suspicious_patterns(text)
            
            self.logger.info("Pattern precomputation completed")
            
        except Exception as e:
            self.logger.error(f"Pattern precomputation failed: {e}")

    def clear_cache(self) -> None:
        """Clear all caches."""
        with self.cache_lock:
            self.cache.clear()
            self._language_cache.clear()
        self.logger.info("CredentialAnalyzer caches cleared")

    def reset_metrics(self) -> None:
        """Reset performance metrics."""
        self._analysis_count = 0
        self._cache_hits = 0
        self._cache_misses = 0
        self._processing_times = []
        self._error_count = 0
        self._last_error = None
        self.logger.info("CredentialAnalyzer metrics reset")
        return f"cred_analysis:{hashlib.md5(combined.encode()).hexdigest()}"

    async def warm_cache(self, credential_pairs: List[Tuple[str, str]]) -> None:
        """
        Pre-warm the cache with commonly analyzed credential pairs.
        
        Args:
            credential_pairs: List of (email, password_hash) tuples to pre-analyze
        """
        self.logger.info(f"Warming cache with {len(credential_pairs)} credential pairs")
        
        try:
            # Analyze in batches to warm the cache
            await self.analyze_credentials_batch(credential_pairs)
            self.logger.info("Cache warming completed successfully")
            
        except Exception as e:
            self.logger.error(f"Cache warming failed: {e}")

    def optimize_cache_settings(self, hit_rate_threshold: float = 0.8) -> Dict[str, Any]:
        """
        Optimize cache settings based on current performance metrics.
        
        Args:
            hit_rate_threshold: Minimum acceptable cache hit rate
            
        Returns:
            Dictionary with optimization recommendations
        """
        with self.cache_lock:
            cache_total = self._cache_hits + self._cache_misses
            current_hit_rate = self._cache_hits / cache_total if cache_total > 0 else 0.0
            
            recommendations = {
                'current_hit_rate': current_hit_rate,
                'target_hit_rate': hit_rate_threshold,
                'current_cache_size': len(self.cache),
                'max_cache_size': self.cache.maxsize,
                'recommendations': []
            }
            
            if current_hit_rate < hit_rate_threshold:
                if len(self.cache) >= self.cache.maxsize * 0.9:
                    recommendations['recommendations'].append({
                        'action': 'increase_cache_size',
                        'current': self.cache.maxsize,
                        'suggested': int(self.cache.maxsize * 1.5),
                        'reason': 'Cache is near capacity and hit rate is low'
                    })
                
                recommendations['recommendations'].append({
                    'action': 'increase_ttl',
                    'current': self.config.cache_ttl,
                    'suggested': int(self.config.cache_ttl * 1.2),
                    'reason': 'Longer TTL may improve hit rate'
                })
            
            return recommendations

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics for the credential analyzer."""
        with self.cache_lock:
            cache_total = self._cache_hits + self._cache_misses
            cache_hit_rate = self._cache_hits / cache_total if cache_total > 0 else 0.0
            
            avg_processing_time = (
                sum(self._processing_times) / len(self._processing_times)
                if self._processing_times else 0.0
            )
            
            # Calculate percentiles for processing times
            processing_times_sorted = sorted(self._processing_times) if self._processing_times else []
            p50 = processing_times_sorted[len(processing_times_sorted)//2] if processing_times_sorted else 0.0
            p95 = processing_times_sorted[int(len(processing_times_sorted)*0.95)] if processing_times_sorted else 0.0
            p99 = processing_times_sorted[int(len(processing_times_sorted)*0.99)] if processing_times_sorted else 0.0
            
            return {
                'analysis_count': self._analysis_count,
                'cache_hit_rate': cache_hit_rate,
                'cache_hits': self._cache_hits,
                'cache_misses': self._cache_misses,
                'cache_size': len(self.cache),
                'cache_max_size': self.cache.maxsize,
                'language_cache_size': len(self._language_cache),
                'avg_processing_time': avg_processing_time,
                'processing_time_p50': p50,
                'processing_time_p95': p95,
                'processing_time_p99': p99,
                'error_count': self._error_count,
                'error_rate': self._error_count / max(self._analysis_count, 1),
                'last_error': self._last_error,
                'throughput_per_second': self._analysis_count / max(sum(self._processing_times), 1) if self._processing_times else 0.0
            }

    def get_cache_statistics(self) -> Dict[str, Any]:
        """Get detailed cache statistics for monitoring."""
        with self.cache_lock:
            cache_total = self._cache_hits + self._cache_misses
            
            return {
                'main_cache': {
                    'size': len(self.cache),
                    'max_size': self.cache.maxsize,
                    'utilization': len(self.cache) / self.cache.maxsize,
                    'hits': self._cache_hits,
                    'misses': self._cache_misses,
                    'hit_rate': self._cache_hits / cache_total if cache_total > 0 else 0.0,
                    'ttl': self.config.cache_ttl
                },
                'language_cache': {
                    'size': len(self._language_cache),
                    'max_size': self._language_cache.maxsize,
                    'utilization': len(self._language_cache) / self._language_cache.maxsize,
                    'ttl': 7200  # 2 hours
                }
            }

    async def precompute_common_patterns(self, common_texts: List[str]) -> None:
        """
        Precompute pattern detection for commonly analyzed texts.
        
        Args:
            common_texts: List of common text patterns to precompute
        """
        self.logger.info(f"Precomputing patterns for {len(common_texts)} common texts")
        
        try:
            # Precompute pattern detection results
            for text in common_texts:
                await self.detect_suspicious_patterns(text)
            
            self.logger.info("Pattern precomputation completed")
            
        except Exception as e:
            self.logger.error(f"Pattern precomputation failed: {e}")

    def clear_cache(self) -> None:
        """Clear all caches."""
        with self.cache_lock:
            self.cache.clear()
            self._language_cache.clear()
        self.logger.info("CredentialAnalyzer caches cleared")

    def reset_metrics(self) -> None:
        """Reset performance metrics."""
        self._analysis_count = 0
        self._cache_hits = 0
        self._cache_misses = 0
        self._processing_times = []
        self._error_count = 0
        self._last_error = None
        self.logger.info("CredentialAnalyzer metrics reset")

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for the credential analyzer."""
        with self.cache_lock:
            cache_total = self._cache_hits + self._cache_misses
            cache_hit_rate = self._cache_hits / cache_total if cache_total > 0 else 0.0
            
            avg_processing_time = (
                sum(self._processing_times) / len(self._processing_times)
                if self._processing_times else 0.0
            )
            
            return {
                'analysis_count': self._analysis_count,
                'cache_hit_rate': cache_hit_rate,
                'cache_size': len(self.cache),
                'avg_processing_time': avg_processing_time,
                'error_count': self._error_count,
                'last_error': self._last_error
            }

    def clear_cache(self) -> None:
        """Clear all caches."""
        with self.cache_lock:
            self.cache.clear()
            self._language_cache.clear()
        self.logger.info("CredentialAnalyzer caches cleared")

    def _detect_keyboard_walks(self, text: str) -> List[str]:
        """
        Enhanced keyboard walk detection with confidence scoring.
        
        Args:
            text: Text to analyze for keyboard walks
            
        Returns:
            List of detected keyboard walk patterns
        """
        detected_patterns = []
        
        try:
            # Check all keyboard walk types
            for walk_type, walks in self.keyboard_walks.items():
                for walk in walks:
                    if walk in text:
                        pattern_name = f"keyboard_walk_{walk_type}"
                        if pattern_name not in detected_patterns:
                            detected_patterns.append(pattern_name)
                        break  # Only add each walk type once
            
            # Check for longer keyboard walks (5+ characters)
            for i in range(len(text) - 4):
                substring = text[i:i+5]
                for walk_type, walks in self.keyboard_walks.items():
                    for walk in walks:
                        if len(walk) >= 4 and walk in substring:
                            pattern_name = f"long_keyboard_walk_{walk_type}"
                            if pattern_name not in detected_patterns:
                                detected_patterns.append(pattern_name)
                            break
                            
        except Exception as e:
            self.logger.error(f"Keyboard walk detection failed: {e}")
        
        return detected_patterns

    def _detect_attack_patterns(self, text: str) -> List[str]:
        """
        Detect attack-specific patterns in text.
        
        Args:
            text: Text to analyze for attack patterns
            
        Returns:
            List of detected attack pattern names
        """
        detected_patterns = []
        
        try:
            # Check compiled attack patterns
            for attack_type, compiled_patterns in self.compiled_attack_patterns.items():
                for pattern in compiled_patterns:
                    if pattern.search(text):
                        detected_patterns.append(attack_type)
                        break  # Only add each attack type once
            
            # Additional attack pattern checks
            if self._check_brute_force_patterns(text):
                detected_patterns.append("brute_force_pattern")
            
            if self._check_credential_stuffing_patterns(text):
                detected_patterns.append("credential_stuffing_pattern")
            
            if self._check_dictionary_attack_patterns(text):
                detected_patterns.append("dictionary_attack_pattern")
                
        except Exception as e:
            self.logger.error(f"Attack pattern detection failed: {e}")
        
        return detected_patterns

    def _detect_language_specific_patterns(self, text: str) -> List[str]:
        """
        Detect language-specific suspicious patterns.
        
        Args:
            text: Text to analyze for language-specific patterns
            
        Returns:
            List of detected language-specific pattern names
        """
        detected_patterns = []
        
        try:
            # Check English weak patterns
            for weak_word in self.language_patterns['english_weak']:
                if weak_word in text:
                    detected_patterns.append("english_weak_word")
                    break
            
            # Check common names
            for name in self.language_patterns['common_names']:
                if name in text:
                    detected_patterns.append("common_name")
                    break
            
            # Check common words
            common_word_count = 0
            for word in self.language_patterns['common_words']:
                if word in text:
                    common_word_count += 1
            
            if common_word_count >= 2:  # Multiple common words
                detected_patterns.append("multiple_common_words")
            elif common_word_count == 1:
                detected_patterns.append("common_word")
                
        except Exception as e:
            self.logger.error(f"Language-specific pattern detection failed: {e}")
        
        return detected_patterns

    def _detect_statistical_anomalies(self, text: str) -> List[str]:
        """
        Detect statistical anomalies in text patterns.
        
        Args:
            text: Text to analyze for statistical anomalies
            
        Returns:
            List of detected statistical anomaly patterns
        """
        detected_patterns = []
        
        try:
            if not text:
                return detected_patterns
            
            # Character frequency analysis
            char_freq = Counter(text.lower())
            total_chars = len(text)
            
            # Check for extremely low entropy (repeated characters)
            entropy = self._calculate_entropy(text)
            if entropy < 1.0:  # Very low entropy
                detected_patterns.append("low_entropy")
            elif entropy < 2.0:  # Moderately low entropy
                detected_patterns.append("moderate_low_entropy")
            
            # Check for character distribution anomalies
            if char_freq:
                most_common_char, most_common_count = char_freq.most_common(1)[0]
                if most_common_count / total_chars >= 0.5:  # One character >= 50%
                    detected_patterns.append("character_dominance")
            
            # Check for lack of character diversity
            unique_chars = len(char_freq)
            if unique_chars < 4 and total_chars > 6:  # Few unique chars in long text
                detected_patterns.append("low_character_diversity")
            
            # Check for numeric dominance
            digit_count = sum(1 for c in text if c.isdigit())
            if digit_count / total_chars > 0.7:  # >70% digits
                detected_patterns.append("numeric_dominance")
            
            # Check for alphabetic dominance
            alpha_count = sum(1 for c in text if c.isalpha())
            if alpha_count / total_chars > 0.9:  # >90% letters
                detected_patterns.append("alphabetic_dominance")
            
            # Check for special character patterns
            special_count = sum(1 for c in text if not c.isalnum())
            if special_count / total_chars > 0.3:  # >30% special chars
                detected_patterns.append("high_special_chars")
                
        except Exception as e:
            self.logger.error(f"Statistical anomaly detection failed: {e}")
        
        return detected_patterns

    def _detect_encoding_patterns(self, text: str) -> List[str]:
        """
        Detect encoding-related patterns that might indicate obfuscation.
        
        Args:
            text: Text to analyze for encoding patterns
            
        Returns:
            List of detected encoding pattern names
        """
        detected_patterns = []
        
        try:
            # Check for Base64 patterns
            if re.search(r'^[A-Za-z0-9+/]{16,}={0,2}$', text):
                detected_patterns.append("base64_encoded")
            
            # Check for hexadecimal patterns
            if re.search(r'^[0-9a-fA-F]{16,}$', text):
                detected_patterns.append("hex_encoded")
            
            # Check for URL encoding
            if '%' in text and re.search(r'%[0-9a-fA-F]{2}', text):
                detected_patterns.append("url_encoded")
            
            # Check for Unicode escape sequences
            if re.search(r'\\u[0-9a-fA-F]{4}', text):
                detected_patterns.append("unicode_escaped")
            
            # Check for HTML entity encoding
            if re.search(r'&[a-zA-Z]+;|&#\d+;', text):
                detected_patterns.append("html_encoded")
            
            # Check for ROT13 patterns (simple heuristic)
            if self._check_rot13_pattern(text):
                detected_patterns.append("rot13_pattern")
                
        except Exception as e:
            self.logger.error(f"Encoding pattern detection failed: {e}")
        
        return detected_patterns

    def _check_brute_force_patterns(self, text: str) -> bool:
        """Check for patterns typical of brute force attacks."""
        brute_force_indicators = [
            r'(password|pass|pwd)\d+$',  # password followed by numbers
            r'^(admin|root|user)\d+$',   # admin/root/user followed by numbers
            r'^[a-z]+\d{1,3}$',          # simple word + 1-3 digits
            r'^\d{4,8}$',                # pure numeric (common in brute force)
        ]
        
        for pattern in brute_force_indicators:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        return False

    def _check_credential_stuffing_patterns(self, text: str) -> bool:
        """Check for patterns typical of credential stuffing attacks."""
        stuffing_indicators = [
            r'^[a-zA-Z]{3,8}\d{4,8}$',   # word + 4-8 digits (common pattern)
            r'^\d{4,8}[a-zA-Z]{3,8}$',   # digits + word
            r'^[a-zA-Z]+[!@#$%]\d+$',    # word + special + digits
            r'^[a-zA-Z]+_\d+$',          # word_digits
            r'^[a-zA-Z]+\.\d+$',         # word.digits
        ]
        
        for pattern in stuffing_indicators:
            if re.search(pattern, text):
                return True
        
        return False

    def _check_dictionary_attack_patterns(self, text: str) -> bool:
        """Check for patterns typical of dictionary attacks."""
        dictionary_indicators = [
            r'^[a-zA-Z]{4,10}$',         # Pure alphabetic (dictionary words) - reduced max length
            r'^[a-zA-Z]{4,10}\d{1,3}$',  # Dictionary word + 1-3 digits - reduced max length
            r'^[A-Z][a-z]{3,9}$',        # Capitalized word - reduced max length
            r'^[a-z]{4,10}[!@#$%]$',     # Word + single special char - reduced max length
        ]
        
        for pattern in dictionary_indicators:
            if re.search(pattern, text):
                return True
        
        return False

    def _check_rot13_pattern(self, text: str) -> bool:
        """
        Simple heuristic to detect ROT13 encoding.
        
        Args:
            text: Text to check for ROT13 patterns
            
        Returns:
            True if text might be ROT13 encoded
        """
        try:
            # ROT13 decode
            rot13_decoded = text.translate(str.maketrans(
                'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz',
                'NOPQRSTUVWXYZABCDEFGHIJKLMnopqrstuvwxyzabcdefghijklm'
            ))
            
            # Check if decoded text contains common English words
            common_words = {'password', 'admin', 'user', 'login', 'secret', 'the', 'and', 'for'}
            decoded_lower = rot13_decoded.lower()
            
            return any(word in decoded_lower for word in common_words)
            
        except Exception:
            return False

    def reset_metrics(self) -> None:
        """Reset performance metrics."""
        self._analysis_count = 0
        self._cache_hits = 0
        self._cache_misses = 0
        self._processing_times = []
        self._error_count = 0
        self._last_error = None
        self.logger.info("CredentialAnalyzer metrics reset")

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics for the credential analyzer."""
        with self.cache_lock:
            cache_total = self._cache_hits + self._cache_misses
            cache_hit_rate = self._cache_hits / cache_total if cache_total > 0 else 0.0
            
            avg_processing_time = (
                sum(self._processing_times) / len(self._processing_times)
                if self._processing_times else 0.0
            )
            
            # Calculate percentiles for processing times
            processing_times_sorted = sorted(self._processing_times) if self._processing_times else []
            p50 = processing_times_sorted[len(processing_times_sorted)//2] if processing_times_sorted else 0.0
            p95 = processing_times_sorted[int(len(processing_times_sorted)*0.95)] if processing_times_sorted else 0.0
            p99 = processing_times_sorted[int(len(processing_times_sorted)*0.99)] if processing_times_sorted else 0.0
            
            return {
                'analysis_count': self._analysis_count,
                'cache_hit_rate': cache_hit_rate,
                'cache_hits': self._cache_hits,
                'cache_misses': self._cache_misses,
                'cache_size': len(self.cache),
                'cache_max_size': self.cache.maxsize,
                'language_cache_size': len(self._language_cache),
                'avg_processing_time': avg_processing_time,
                'processing_time_p50': p50,
                'processing_time_p95': p95,
                'processing_time_p99': p99,
                'error_count': self._error_count,
                'error_rate': self._error_count / max(self._analysis_count, 1),
                'last_error': self._last_error,
                'throughput_per_second': self._analysis_count / max(sum(self._processing_times), 1) if self._processing_times else 0.0
            }

    def get_cache_statistics(self) -> Dict[str, Any]:
        """Get detailed cache statistics for monitoring."""
        with self.cache_lock:
            cache_total = self._cache_hits + self._cache_misses
            
            return {
                'main_cache': {
                    'size': len(self.cache),
                    'max_size': self.cache.maxsize,
                    'utilization': len(self.cache) / self.cache.maxsize,
                    'hits': self._cache_hits,
                    'misses': self._cache_misses,
                    'hit_rate': self._cache_hits / cache_total if cache_total > 0 else 0.0,
                    'ttl': self.config.cache_ttl
                },
                'language_cache': {
                    'size': len(self._language_cache),
                    'max_size': self._language_cache.maxsize,
                    'utilization': len(self._language_cache) / self._language_cache.maxsize,
                    'ttl': 7200  # 2 hours
                }
            }

    async def precompute_common_patterns(self, common_texts: List[str]) -> None:
        """
        Precompute pattern detection for commonly analyzed texts.
        
        Args:
            common_texts: List of common text patterns to precompute
        """
        self.logger.info(f"Precomputing patterns for {len(common_texts)} common texts")
        
        try:
            # Precompute pattern detection results
            for text in common_texts:
                await self.detect_suspicious_patterns(text)
            
            self.logger.info("Pattern precomputation completed")
            
        except Exception as e:
            self.logger.error(f"Pattern precomputation failed: {e}")

    def clear_cache(self) -> None:
        """Clear all caches."""
        with self.cache_lock:
            self.cache.clear()
            self._language_cache.clear()
        self.logger.info("CredentialAnalyzer caches cleared")

    def reset_metrics(self) -> None:
        """Reset performance metrics."""
        self._analysis_count = 0
        self._cache_hits = 0
        self._cache_misses = 0
        self._processing_times = []
        self._error_count = 0
        self._last_error = None
        self.logger.info("CredentialAnalyzer metrics reset")