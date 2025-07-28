"""
Behavioral embedding service for intelligent authentication system.

This module provides behavioral embedding generation using DistilBERT infrastructure
for login context analysis, similarity calculation, and clustering for behavioral analysis.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import time
import json
from typing import List, Optional, Dict, Any, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from cachetools import TTLCache
import threading
import numpy as np

try:
    from ai_karen_engine.services.distilbert_service import DistilBertService
    from ai_karen_engine.services.nlp_config import DistilBertConfig
    from ai_karen_engine.security.models import (
        AuthContext, EmbeddingAnalysis, IntelligentAuthConfig
    )
except ImportError:
    # Fallback imports for testing
    from distilbert_service import DistilBertService
    from nlp_config import DistilBertConfig
    from models import AuthContext, EmbeddingAnalysis, IntelligentAuthConfig

logger = logging.getLogger(__name__)


@dataclass
class BehavioralEmbeddingResult:
    """Result of behavioral embedding generation."""
    
    embedding_vector: List[float]
    context_features: Dict[str, Any]
    processing_time: float
    used_fallback: bool
    model_version: str
    similarity_scores: Dict[str, float] = field(default_factory=dict)
    cluster_info: Optional[Dict[str, Any]] = None


@dataclass
class UserBehavioralProfile:
    """User-specific behavioral profile for similarity analysis."""
    
    user_id: str
    typical_embeddings: List[List[float]] = field(default_factory=list)
    typical_login_times: List[int] = field(default_factory=list)  # Hours of day
    typical_locations: List[Dict[str, Any]] = field(default_factory=list)
    typical_devices: List[str] = field(default_factory=list)
    success_patterns: List[Dict[str, Any]] = field(default_factory=list)
    last_updated: datetime = field(default_factory=datetime.now)
    login_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'user_id': self.user_id,
            'typical_embeddings': self.typical_embeddings,
            'typical_login_times': self.typical_login_times,
            'typical_locations': self.typical_locations,
            'typical_devices': self.typical_devices,
            'success_patterns': self.success_patterns,
            'last_updated': self.last_updated.isoformat(),
            'login_count': self.login_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> UserBehavioralProfile:
        """Create instance from dictionary."""
        return cls(
            user_id=data['user_id'],
            typical_embeddings=data.get('typical_embeddings', []),
            typical_login_times=data.get('typical_login_times', []),
            typical_locations=data.get('typical_locations', []),
            typical_devices=data.get('typical_devices', []),
            success_patterns=data.get('success_patterns', []),
            last_updated=datetime.fromisoformat(data.get('last_updated', datetime.now().isoformat())),
            login_count=data.get('login_count', 0)
        )


@dataclass
class BehavioralEmbeddingConfig:
    """Configuration for behavioral embedding service."""
    
    enable_context_enrichment: bool = True
    enable_temporal_features: bool = True
    enable_geolocation_features: bool = True
    enable_device_features: bool = True
    max_profile_embeddings: int = 50
    profile_update_threshold: float = 0.8
    similarity_threshold: float = 0.7
    outlier_threshold: float = 0.3
    cache_size: int = 5000
    cache_ttl: int = 3600


class BehavioralEmbeddingService:
    """
    Behavioral embedding service that uses DistilBERT infrastructure for
    context-aware embedding generation and similarity analysis.
    """
    
    def __init__(
        self,
        distilbert_service: Optional[DistilBertService] = None,
        config: Optional[BehavioralEmbeddingConfig] = None
    ):
        self.config = config or BehavioralEmbeddingConfig()
        self.distilbert_service = distilbert_service or DistilBertService()
        self.logger = logger
        
        # User behavioral profiles storage (in-memory with fallback)
        self.user_profiles: Dict[str, UserBehavioralProfile] = {}
        self.profiles_lock = threading.RLock()
        
        # Caching for embeddings and similarity calculations
        self.embedding_cache = TTLCache(
            maxsize=self.config.cache_size,
            ttl=self.config.cache_ttl
        )
        self.similarity_cache = TTLCache(
            maxsize=self.config.cache_size // 2,
            ttl=self.config.cache_ttl // 2
        )
        self.cache_lock = threading.RLock()
        
        # Metrics tracking
        self._embedding_count = 0
        self._similarity_calculations = 0
        self._cache_hits = 0
        self._cache_misses = 0
        self._processing_times = []
        
        self.logger.info("BehavioralEmbeddingService initialized")
    
    async def generate_behavioral_embedding(
        self,
        auth_context: AuthContext
    ) -> BehavioralEmbeddingResult:
        """
        Generate behavioral embedding for login context using DistilBERT.
        
        Args:
            auth_context: Authentication context with login details
            
        Returns:
            BehavioralEmbeddingResult with embedding vector and analysis
        """
        start_time = time.time()
        
        try:
            # Extract and enrich context features
            context_features = self._extract_context_features(auth_context)
            
            # Create text representation for embedding
            context_text = self._create_context_text(auth_context, context_features)
            
            # Check cache first
            cache_key = self._get_embedding_cache_key(context_text)
            with self.cache_lock:
                if cache_key in self.embedding_cache:
                    self._cache_hits += 1
                    cached_result = self.embedding_cache[cache_key]
                    self.logger.debug(f"Cache hit for embedding: {cache_key[:16]}...")
                    return cached_result
                self._cache_misses += 1
            
            # Generate embedding using DistilBERT
            embedding_vector = await self.distilbert_service.get_embeddings(
                context_text, normalize=True
            )
            
            # Calculate similarity scores if user profile exists
            similarity_scores = await self._calculate_similarity_scores(
                auth_context.email, embedding_vector
            )
            
            processing_time = time.time() - start_time
            
            # Create result
            result = BehavioralEmbeddingResult(
                embedding_vector=embedding_vector,
                context_features=context_features,
                processing_time=processing_time,
                used_fallback=self.distilbert_service.fallback_mode,
                model_version=self.distilbert_service.config.model_name,
                similarity_scores=similarity_scores
            )
            
            # Cache result
            with self.cache_lock:
                self.embedding_cache[cache_key] = result
            
            # Update metrics
            self._embedding_count += 1
            self._processing_times.append(processing_time)
            if len(self._processing_times) > 1000:
                self._processing_times = self._processing_times[-1000:]
            
            self.logger.debug(
                f"Generated behavioral embedding in {processing_time:.3f}s "
                f"(fallback: {result.used_fallback})"
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to generate behavioral embedding: {e}")
            # Return fallback embedding
            return await self._generate_fallback_embedding(auth_context, start_time)
    
    def _extract_context_features(self, auth_context: AuthContext) -> Dict[str, Any]:
        """Extract and enrich context features from authentication context."""
        features = {
            'timestamp_hour': auth_context.timestamp.hour,
            'timestamp_day_of_week': auth_context.timestamp.weekday(),
            'timestamp_is_weekend': auth_context.timestamp.weekday() >= 5,
        }
        
        if self.config.enable_temporal_features:
            features.update({
                'time_since_last_login_hours': (
                    auth_context.time_since_last_login.total_seconds() / 3600
                    if auth_context.time_since_last_login else 0
                ),
                'is_business_hours': 9 <= auth_context.timestamp.hour <= 17,
                'is_night_time': auth_context.timestamp.hour < 6 or auth_context.timestamp.hour > 22,
            })
        
        if self.config.enable_geolocation_features and auth_context.geolocation:
            features.update({
                'country': auth_context.geolocation.country,
                'timezone': auth_context.geolocation.timezone,
                'is_usual_location': auth_context.geolocation.is_usual_location,
                'latitude_zone': int(auth_context.geolocation.latitude / 10) * 10,  # Rough zone
                'longitude_zone': int(auth_context.geolocation.longitude / 10) * 10,
            })
        
        if self.config.enable_device_features:
            features.update({
                'user_agent_hash': hashlib.md5(auth_context.user_agent.encode()).hexdigest()[:8],
                'has_device_fingerprint': bool(auth_context.device_fingerprint),
                'is_tor': auth_context.is_tor_exit_node,
                'is_vpn': auth_context.is_vpn,
            })
        
        # Security context features
        features.update({
            'threat_intel_score': auth_context.threat_intel_score,
            'previous_failed_attempts': min(auth_context.previous_failed_attempts, 10),  # Cap for embedding
            'ip_hash': hashlib.md5(auth_context.client_ip.encode()).hexdigest()[:8],
        })
        
        return features
    
    def _create_context_text(
        self,
        auth_context: AuthContext,
        context_features: Dict[str, Any]
    ) -> str:
        """Create text representation of authentication context for embedding."""
        text_parts = []
        
        # Email domain for context (without revealing full email)
        email_domain = auth_context.email.split('@')[-1] if '@' in auth_context.email else 'unknown'
        text_parts.append(f"domain:{email_domain}")
        
        # Temporal context
        text_parts.append(f"hour:{context_features['timestamp_hour']}")
        text_parts.append(f"weekday:{context_features['timestamp_day_of_week']}")
        
        if context_features.get('is_business_hours'):
            text_parts.append("business_hours")
        if context_features.get('is_weekend'):
            text_parts.append("weekend")
        if context_features.get('is_night_time'):
            text_parts.append("night_time")
        
        # Location context (if available)
        if self.config.enable_geolocation_features and auth_context.geolocation:
            text_parts.append(f"country:{context_features.get('country', 'unknown')}")
            text_parts.append(f"timezone:{context_features.get('timezone', 'unknown')}")
            if context_features.get('is_usual_location'):
                text_parts.append("usual_location")
        
        # Device context
        if self.config.enable_device_features:
            text_parts.append(f"ua_hash:{context_features.get('user_agent_hash', 'unknown')}")
            if context_features.get('is_tor'):
                text_parts.append("tor_exit")
            if context_features.get('is_vpn'):
                text_parts.append("vpn_connection")
        
        # Security context
        threat_level = "low" if auth_context.threat_intel_score < 0.3 else \
                     "medium" if auth_context.threat_intel_score < 0.7 else "high"
        text_parts.append(f"threat:{threat_level}")
        
        if auth_context.previous_failed_attempts > 0:
            text_parts.append(f"failed_attempts:{min(auth_context.previous_failed_attempts, 5)}")
        
        # Join all parts
        context_text = " ".join(text_parts)
        
        self.logger.debug(f"Created context text: {context_text}")
        return context_text
    
    async def _calculate_similarity_scores(
        self,
        user_email: str,
        embedding_vector: List[float]
    ) -> Dict[str, float]:
        """Calculate similarity scores against user's behavioral profile."""
        similarity_scores = {}
        
        with self.profiles_lock:
            user_profile = self.user_profiles.get(user_email)
            if not user_profile or not user_profile.typical_embeddings:
                return similarity_scores
        
        try:
            # Calculate similarity to typical embeddings
            similarities = []
            for typical_embedding in user_profile.typical_embeddings:
                similarity = self._cosine_similarity(embedding_vector, typical_embedding)
                similarities.append(similarity)
            
            if similarities:
                similarity_scores.update({
                    'max_similarity_to_profile': max(similarities),
                    'avg_similarity_to_profile': sum(similarities) / len(similarities),
                    'min_similarity_to_profile': min(similarities),
                })
            
            self._similarity_calculations += 1
            
        except Exception as e:
            self.logger.error(f"Failed to calculate similarity scores: {e}")
        
        return similarity_scores
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        if len(vec1) != len(vec2):
            return 0.0
        
        try:
            vec1_np = np.array(vec1)
            vec2_np = np.array(vec2)
            
            dot_product = np.dot(vec1_np, vec2_np)
            norm1 = np.linalg.norm(vec1_np)
            norm2 = np.linalg.norm(vec2_np)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return float(dot_product / (norm1 * norm2))
            
        except Exception as e:
            self.logger.error(f"Failed to calculate cosine similarity: {e}")
            return 0.0
    
    async def update_user_behavioral_profile(
        self,
        user_email: str,
        auth_context: AuthContext,
        embedding_result: BehavioralEmbeddingResult,
        login_successful: bool
    ) -> None:
        """Update user's behavioral profile based on login outcome."""
        if not login_successful:
            return  # Only update profile for successful logins
        
        with self.profiles_lock:
            # Get or create user profile
            if user_email not in self.user_profiles:
                self.user_profiles[user_email] = UserBehavioralProfile(user_id=user_email)
            
            profile = self.user_profiles[user_email]
            
            # Update typical embeddings
            profile.typical_embeddings.append(embedding_result.embedding_vector)
            if len(profile.typical_embeddings) > self.config.max_profile_embeddings:
                # Remove oldest embeddings
                profile.typical_embeddings = profile.typical_embeddings[-self.config.max_profile_embeddings:]
            
            # Update typical login times
            login_hour = auth_context.timestamp.hour
            profile.typical_login_times.append(login_hour)
            if len(profile.typical_login_times) > 100:  # Keep last 100 login times
                profile.typical_login_times = profile.typical_login_times[-100:]
            
            # Update typical locations
            if auth_context.geolocation:
                location_info = {
                    'country': auth_context.geolocation.country,
                    'region': auth_context.geolocation.region,
                    'city': auth_context.geolocation.city,
                    'timezone': auth_context.geolocation.timezone,
                }
                profile.typical_locations.append(location_info)
                if len(profile.typical_locations) > 20:  # Keep last 20 locations
                    profile.typical_locations = profile.typical_locations[-20:]
            
            # Update typical devices
            device_hash = hashlib.md5(auth_context.user_agent.encode()).hexdigest()[:16]
            if device_hash not in profile.typical_devices:
                profile.typical_devices.append(device_hash)
                if len(profile.typical_devices) > 10:  # Keep last 10 devices
                    profile.typical_devices = profile.typical_devices[-10:]
            
            # Update success patterns
            success_pattern = {
                'timestamp': auth_context.timestamp.isoformat(),
                'hour': auth_context.timestamp.hour,
                'day_of_week': auth_context.timestamp.weekday(),
                'context_features': embedding_result.context_features,
            }
            profile.success_patterns.append(success_pattern)
            if len(profile.success_patterns) > 50:  # Keep last 50 success patterns
                profile.success_patterns = profile.success_patterns[-50:]
            
            # Update metadata
            profile.last_updated = datetime.now()
            profile.login_count += 1
        
        self.logger.debug(f"Updated behavioral profile for user: {user_email}")
    
    async def analyze_embedding_for_anomalies(
        self,
        auth_context: AuthContext,
        embedding_result: BehavioralEmbeddingResult
    ) -> EmbeddingAnalysis:
        """Analyze embedding for anomalies and create EmbeddingAnalysis result."""
        try:
            # Get similarity scores from embedding result
            similarity_scores = embedding_result.similarity_scores
            
            # Calculate similarity to user profile
            similarity_to_user_profile = similarity_scores.get('max_similarity_to_profile', 0.0)
            
            # Calculate similarity to attack patterns (placeholder - would use known attack embeddings)
            similarity_to_attack_patterns = 0.0  # TODO: Implement with attack pattern database
            
            # Calculate outlier score based on similarity to user profile
            outlier_score = 1.0 - similarity_to_user_profile if similarity_to_user_profile > 0 else 0.5
            
            # Determine cluster assignment (placeholder - would use clustering algorithm)
            cluster_assignment = None  # TODO: Implement clustering
            
            return EmbeddingAnalysis(
                embedding_vector=embedding_result.embedding_vector,
                similarity_to_user_profile=similarity_to_user_profile,
                similarity_to_attack_patterns=similarity_to_attack_patterns,
                cluster_assignment=cluster_assignment,
                outlier_score=outlier_score,
                processing_time=embedding_result.processing_time,
                model_version=embedding_result.model_version
            )
            
        except Exception as e:
            self.logger.error(f"Failed to analyze embedding for anomalies: {e}")
            # Return default analysis
            return EmbeddingAnalysis(
                embedding_vector=embedding_result.embedding_vector,
                similarity_to_user_profile=0.0,
                similarity_to_attack_patterns=0.0,
                outlier_score=0.5,
                processing_time=embedding_result.processing_time,
                model_version=embedding_result.model_version
            )
    
    async def _generate_fallback_embedding(
        self,
        auth_context: AuthContext,
        start_time: float
    ) -> BehavioralEmbeddingResult:
        """Generate fallback embedding when DistilBERT service fails."""
        try:
            # Create simple hash-based embedding
            context_features = self._extract_context_features(auth_context)
            context_text = self._create_context_text(auth_context, context_features)
            
            # Generate hash-based embedding
            embedding_vector = await self._generate_hash_embedding(context_text)
            
            processing_time = time.time() - start_time
            
            return BehavioralEmbeddingResult(
                embedding_vector=embedding_vector,
                context_features=context_features,
                processing_time=processing_time,
                used_fallback=True,
                model_version="hash_fallback",
                similarity_scores={}
            )
            
        except Exception as e:
            self.logger.error(f"Failed to generate fallback embedding: {e}")
            # Return minimal embedding
            return BehavioralEmbeddingResult(
                embedding_vector=[0.0] * 768,  # Default DistilBERT dimension
                context_features={},
                processing_time=time.time() - start_time,
                used_fallback=True,
                model_version="minimal_fallback",
                similarity_scores={}
            )
    
    async def _generate_hash_embedding(self, text: str) -> List[float]:
        """Generate hash-based embedding as fallback."""
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
        
        # Pad or truncate to target dimension (768 for DistilBERT)
        target_dim = 768
        while len(embedding) < target_dim:
            # Repeat pattern if needed
            remaining = target_dim - len(embedding)
            to_add = min(remaining, len(embedding))
            embedding.extend(embedding[:to_add])
        
        return embedding[:target_dim]
    
    def _get_embedding_cache_key(self, context_text: str) -> str:
        """Generate cache key for embedding."""
        text_hash = hashlib.md5(context_text.encode()).hexdigest()
        model_info = f"{self.distilbert_service.config.model_name}_{self.distilbert_service.config.pooling_strategy}"
        model_hash = hashlib.md5(model_info.encode()).hexdigest()[:8]
        return f"behavioral_embedding:{model_hash}:{text_hash}"
    
    def get_user_profile(self, user_email: str) -> Optional[UserBehavioralProfile]:
        """Get user's behavioral profile."""
        with self.profiles_lock:
            return self.user_profiles.get(user_email)
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of the behavioral embedding service."""
        with self.cache_lock:
            cache_total = self._cache_hits + self._cache_misses
            cache_hit_rate = self._cache_hits / cache_total if cache_total > 0 else 0.0
            
            avg_processing_time = (
                sum(self._processing_times) / len(self._processing_times)
                if self._processing_times else 0.0
            )
        
        with self.profiles_lock:
            profile_count = len(self.user_profiles)
        
        distilbert_health = self.distilbert_service.get_health_status()
        
        return {
            'is_healthy': distilbert_health.is_healthy,
            'distilbert_service_healthy': distilbert_health.is_healthy,
            'fallback_mode': distilbert_health.fallback_mode,
            'embedding_count': self._embedding_count,
            'similarity_calculations': self._similarity_calculations,
            'cache_hit_rate': cache_hit_rate,
            'avg_processing_time': avg_processing_time,
            'user_profiles_count': profile_count,
            'cache_size': len(self.embedding_cache),
            'distilbert_model': distilbert_health.model_name if hasattr(distilbert_health, 'model_name') else 'unknown'
        }
    
    def clear_cache(self) -> None:
        """Clear all caches."""
        with self.cache_lock:
            self.embedding_cache.clear()
            self.similarity_cache.clear()
        self.logger.info("Behavioral embedding service caches cleared")
    
    def reset_metrics(self) -> None:
        """Reset all metrics."""
        self._embedding_count = 0
        self._similarity_calculations = 0
        self._cache_hits = 0
        self._cache_misses = 0
        self._processing_times = []
        self.logger.info("Behavioral embedding service metrics reset")
    
    async def batch_generate_embeddings(
        self,
        auth_contexts: List[AuthContext]
    ) -> List[BehavioralEmbeddingResult]:
        """Generate embeddings for multiple authentication contexts."""
        results = []
        
        for auth_context in auth_contexts:
            try:
                result = await self.generate_behavioral_embedding(auth_context)
                results.append(result)
            except Exception as e:
                self.logger.error(f"Failed to generate embedding for context {auth_context.request_id}: {e}")
                # Add fallback result
                fallback_result = await self._generate_fallback_embedding(auth_context, time.time())
                results.append(fallback_result)
        
        return results