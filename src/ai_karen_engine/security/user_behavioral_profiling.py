"""
Enhanced user behavioral profiling service for intelligent authentication system.

This module provides advanced user behavioral profiling with persistence layer,
sophisticated similarity scoring, and profile management capabilities.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
import threading
import hashlib

try:
    from ai_karen_engine.security.behavioral_embedding import (
        UserBehavioralProfile, BehavioralEmbeddingResult
    )
    from ai_karen_engine.security.models import AuthContext, IntelligentAuthConfig
except ImportError:
    # Fallback imports for testing
    from behavioral_embedding import UserBehavioralProfile, BehavioralEmbeddingResult
    from models import AuthContext, IntelligentAuthConfig

logger = logging.getLogger(__name__)


@dataclass
class ProfileSimilarityScore:
    """Detailed similarity score breakdown for user behavioral profile."""
    
    overall_similarity: float
    embedding_similarity: float
    temporal_similarity: float
    location_similarity: float
    device_similarity: float
    pattern_consistency: float
    confidence_score: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'overall_similarity': self.overall_similarity,
            'embedding_similarity': self.embedding_similarity,
            'temporal_similarity': self.temporal_similarity,
            'location_similarity': self.location_similarity,
            'device_similarity': self.device_similarity,
            'pattern_consistency': self.pattern_consistency,
            'confidence_score': self.confidence_score
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ProfileSimilarityScore:
        """Create instance from dictionary."""
        return cls(**data)


@dataclass
class ProfileAnalysisResult:
    """Result of behavioral profile analysis."""
    
    user_id: str
    profile_exists: bool
    similarity_score: Optional[ProfileSimilarityScore]
    anomaly_indicators: List[str] = field(default_factory=list)
    risk_factors: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    processing_time: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'user_id': self.user_id,
            'profile_exists': self.profile_exists,
            'similarity_score': self.similarity_score.to_dict() if self.similarity_score else None,
            'anomaly_indicators': self.anomaly_indicators,
            'risk_factors': self.risk_factors,
            'recommendations': self.recommendations,
            'processing_time': self.processing_time
        }


@dataclass
class UserBehavioralProfilingConfig:
    """Configuration for user behavioral profiling service."""
    
    # Profile management
    max_profiles_in_memory: int = 1000
    profile_expiry_days: int = 90
    min_logins_for_profile: int = 3
    
    # Persistence settings
    enable_persistence: bool = True
    persistence_path: str = "data/behavioral_profiles"
    backup_interval_hours: int = 24
    
    # Similarity calculation
    embedding_weight: float = 0.4
    temporal_weight: float = 0.2
    location_weight: float = 0.2
    device_weight: float = 0.1
    pattern_weight: float = 0.1
    
    # Anomaly detection
    similarity_threshold: float = 0.7
    anomaly_threshold: float = 0.3
    confidence_threshold: float = 0.6
    
    # Performance settings
    async_updates: bool = True
    batch_size: int = 10
    max_concurrent_updates: int = 5


class UserBehavioralProfilingService:
    """
    Enhanced user behavioral profiling service with persistence and advanced analysis.
    """
    
    def __init__(self, config: Optional[UserBehavioralProfilingConfig] = None):
        self.config = config or UserBehavioralProfilingConfig()
        self.logger = logger
        
        # In-memory profile storage
        self.profiles: Dict[str, UserBehavioralProfile] = {}
        self.profiles_lock = threading.RLock()
        
        # Profile access tracking for LRU eviction
        self.profile_access_times: Dict[str, datetime] = {}
        self.access_lock = threading.RLock()
        
        # Persistence layer
        self.persistence_path = Path(self.config.persistence_path)
        self.persistence_path.mkdir(parents=True, exist_ok=True)
        
        # Background tasks
        self._background_tasks: List[asyncio.Task] = []
        self._shutdown_event = asyncio.Event()
        
        # Metrics
        self._profile_loads = 0
        self._profile_saves = 0
        self._cache_hits = 0
        self._cache_misses = 0
        self._similarity_calculations = 0
        
        # Initialize service
        self._initialize()
    
    def _initialize(self):
        """Initialize the behavioral profiling service."""
        try:
            # Load existing profiles if persistence is enabled
            if self.config.enable_persistence:
                self._load_profiles_from_disk()
            
            self.logger.info(
                f"UserBehavioralProfilingService initialized with "
                f"{len(self.profiles)} profiles loaded"
            )
            
        except Exception as e:
            self.logger.error(f"Failed to initialize behavioral profiling service: {e}")
            raise
    
    async def analyze_user_behavior(
        self,
        auth_context: AuthContext,
        embedding_result: BehavioralEmbeddingResult
    ) -> ProfileAnalysisResult:
        """
        Analyze user behavior against their behavioral profile.
        
        Args:
            auth_context: Authentication context
            embedding_result: Behavioral embedding result
            
        Returns:
            ProfileAnalysisResult with detailed analysis
        """
        start_time = time.time()
        user_id = auth_context.email
        
        try:
            # Get or create user profile
            profile = await self._get_user_profile(user_id)
            
            if not profile or profile.login_count < self.config.min_logins_for_profile:
                # Insufficient data for analysis
                return ProfileAnalysisResult(
                    user_id=user_id,
                    profile_exists=profile is not None,
                    similarity_score=None,
                    recommendations=["Insufficient historical data for behavioral analysis"],
                    processing_time=time.time() - start_time
                )
            
            # Calculate detailed similarity scores
            similarity_score = await self._calculate_detailed_similarity(
                auth_context, embedding_result, profile
            )
            
            # Detect anomalies and risk factors
            anomaly_indicators = self._detect_anomaly_indicators(
                auth_context, embedding_result, profile, similarity_score
            )
            
            risk_factors = self._identify_risk_factors(
                auth_context, embedding_result, profile, similarity_score
            )
            
            recommendations = self._generate_recommendations(
                similarity_score, anomaly_indicators, risk_factors
            )
            
            self._similarity_calculations += 1
            
            return ProfileAnalysisResult(
                user_id=user_id,
                profile_exists=True,
                similarity_score=similarity_score,
                anomaly_indicators=anomaly_indicators,
                risk_factors=risk_factors,
                recommendations=recommendations,
                processing_time=time.time() - start_time
            )
            
        except Exception as e:
            self.logger.error(f"Failed to analyze user behavior for {user_id}: {e}")
            return ProfileAnalysisResult(
                user_id=user_id,
                profile_exists=False,
                similarity_score=None,
                anomaly_indicators=["Analysis failed"],
                processing_time=time.time() - start_time
            )
    
    async def update_user_profile(
        self,
        user_id: str,
        auth_context: AuthContext,
        embedding_result: BehavioralEmbeddingResult,
        login_successful: bool
    ) -> None:
        """
        Update user's behavioral profile based on login outcome.
        
        Args:
            user_id: User identifier
            auth_context: Authentication context
            embedding_result: Behavioral embedding result
            login_successful: Whether the login was successful
        """
        if not login_successful:
            return  # Only update profile for successful logins
        
        try:
            if self.config.async_updates:
                # Schedule async update
                task = asyncio.create_task(
                    self._async_update_profile(user_id, auth_context, embedding_result)
                )
                self._background_tasks.append(task)
            else:
                # Synchronous update
                await self._update_profile_sync(user_id, auth_context, embedding_result)
                
        except Exception as e:
            self.logger.error(f"Failed to update profile for {user_id}: {e}")
    
    async def _async_update_profile(
        self,
        user_id: str,
        auth_context: AuthContext,
        embedding_result: BehavioralEmbeddingResult
    ) -> None:
        """Asynchronously update user profile."""
        try:
            await self._update_profile_sync(user_id, auth_context, embedding_result)
        except Exception as e:
            self.logger.error(f"Async profile update failed for {user_id}: {e}")
    
    async def _update_profile_sync(
        self,
        user_id: str,
        auth_context: AuthContext,
        embedding_result: BehavioralEmbeddingResult
    ) -> None:
        """Synchronously update user profile."""
        with self.profiles_lock:
            # Get or create profile
            if user_id not in self.profiles:
                self.profiles[user_id] = UserBehavioralProfile(user_id=user_id)
            
            profile = self.profiles[user_id]
            
            # Update embedding history
            profile.typical_embeddings.append(embedding_result.embedding_vector)
            if len(profile.typical_embeddings) > 50:  # Keep last 50 embeddings
                profile.typical_embeddings = profile.typical_embeddings[-50:]
            
            # Update temporal patterns
            login_hour = auth_context.timestamp.hour
            profile.typical_login_times.append(login_hour)
            if len(profile.typical_login_times) > 100:
                profile.typical_login_times = profile.typical_login_times[-100:]
            
            # Update location patterns
            if auth_context.geolocation:
                location_info = {
                    'country': auth_context.geolocation.country,
                    'region': auth_context.geolocation.region,
                    'city': auth_context.geolocation.city,
                    'timezone': auth_context.geolocation.timezone,
                    'timestamp': auth_context.timestamp.isoformat()
                }
                profile.typical_locations.append(location_info)
                if len(profile.typical_locations) > 20:
                    profile.typical_locations = profile.typical_locations[-20:]
            
            # Update device patterns
            device_hash = hashlib.md5(auth_context.user_agent.encode()).hexdigest()[:16]
            if device_hash not in profile.typical_devices:
                profile.typical_devices.append(device_hash)
                if len(profile.typical_devices) > 10:
                    profile.typical_devices = profile.typical_devices[-10:]
            
            # Update success patterns with enhanced context
            success_pattern = {
                'timestamp': auth_context.timestamp.isoformat(),
                'hour': auth_context.timestamp.hour,
                'day_of_week': auth_context.timestamp.weekday(),
                'context_features': embedding_result.context_features,
                'embedding_similarity': embedding_result.similarity_scores.get('max_similarity_to_profile', 0.0),
                'threat_score': auth_context.threat_intel_score,
                'location': auth_context.geolocation.country if auth_context.geolocation else None
            }
            profile.success_patterns.append(success_pattern)
            if len(profile.success_patterns) > 100:
                profile.success_patterns = profile.success_patterns[-100:]
            
            # Update metadata
            profile.last_updated = datetime.now()
            profile.login_count += 1
            
            # Update access time for LRU
            with self.access_lock:
                self.profile_access_times[user_id] = datetime.now()
        
        # Schedule persistence if enabled
        if self.config.enable_persistence:
            await self._schedule_profile_save(user_id)
        
        self.logger.debug(f"Updated behavioral profile for user: {user_id}")
    
    async def _calculate_detailed_similarity(
        self,
        auth_context: AuthContext,
        embedding_result: BehavioralEmbeddingResult,
        profile: UserBehavioralProfile
    ) -> ProfileSimilarityScore:
        """Calculate detailed similarity scores against user profile."""
        
        # Embedding similarity
        embedding_similarities = []
        for typical_embedding in profile.typical_embeddings:
            similarity = self._cosine_similarity(
                embedding_result.embedding_vector, typical_embedding
            )
            embedding_similarities.append(similarity)
        
        embedding_similarity = (
            max(embedding_similarities) if embedding_similarities else 0.0
        )
        
        # Temporal similarity
        temporal_similarity = self._calculate_temporal_similarity(
            auth_context, profile
        )
        
        # Location similarity
        location_similarity = self._calculate_location_similarity(
            auth_context, profile
        )
        
        # Device similarity
        device_similarity = self._calculate_device_similarity(
            auth_context, profile
        )
        
        # Pattern consistency
        pattern_consistency = self._calculate_pattern_consistency(
            auth_context, embedding_result, profile
        )
        
        # Calculate weighted overall similarity
        overall_similarity = (
            self.config.embedding_weight * embedding_similarity +
            self.config.temporal_weight * temporal_similarity +
            self.config.location_weight * location_similarity +
            self.config.device_weight * device_similarity +
            self.config.pattern_weight * pattern_consistency
        )
        
        # Calculate confidence based on profile maturity
        confidence_score = min(1.0, profile.login_count / 20.0)  # Full confidence at 20+ logins
        
        return ProfileSimilarityScore(
            overall_similarity=overall_similarity,
            embedding_similarity=embedding_similarity,
            temporal_similarity=temporal_similarity,
            location_similarity=location_similarity,
            device_similarity=device_similarity,
            pattern_consistency=pattern_consistency,
            confidence_score=confidence_score
        )
    
    def _calculate_temporal_similarity(
        self,
        auth_context: AuthContext,
        profile: UserBehavioralProfile
    ) -> float:
        """Calculate temporal pattern similarity."""
        if not profile.typical_login_times:
            return 0.0
        
        current_hour = auth_context.timestamp.hour
        
        # Calculate hour frequency distribution
        hour_counts = {}
        for hour in profile.typical_login_times:
            hour_counts[hour] = hour_counts.get(hour, 0) + 1
        
        total_logins = len(profile.typical_login_times)
        current_hour_frequency = hour_counts.get(current_hour, 0) / total_logins
        
        # Also consider adjacent hours (±1 hour tolerance)
        adjacent_hours = [(current_hour - 1) % 24, (current_hour + 1) % 24]
        adjacent_frequency = sum(
            hour_counts.get(hour, 0) for hour in adjacent_hours
        ) / total_logins
        
        # Combine current and adjacent hour frequencies
        temporal_similarity = current_hour_frequency + (adjacent_frequency * 0.5)
        
        return min(1.0, temporal_similarity * 2)  # Scale to [0, 1]
    
    def _calculate_location_similarity(
        self,
        auth_context: AuthContext,
        profile: UserBehavioralProfile
    ) -> float:
        """Calculate location pattern similarity."""
        if not auth_context.geolocation or not profile.typical_locations:
            return 0.5  # Neutral score when no location data
        
        current_country = auth_context.geolocation.country
        current_city = auth_context.geolocation.city
        
        # Check country matches
        country_matches = sum(
            1 for loc in profile.typical_locations
            if loc.get('country') == current_country
        )
        country_similarity = country_matches / len(profile.typical_locations)
        
        # Check city matches (more specific)
        city_matches = sum(
            1 for loc in profile.typical_locations
            if loc.get('city') == current_city
        )
        city_similarity = city_matches / len(profile.typical_locations)
        
        # Weighted combination (country: 0.3, city: 0.7)
        location_similarity = 0.3 * country_similarity + 0.7 * city_similarity
        
        return location_similarity
    
    def _calculate_device_similarity(
        self,
        auth_context: AuthContext,
        profile: UserBehavioralProfile
    ) -> float:
        """Calculate device pattern similarity."""
        if not profile.typical_devices:
            return 0.0
        
        current_device_hash = hashlib.md5(auth_context.user_agent.encode()).hexdigest()[:16]
        
        # Exact device match
        if current_device_hash in profile.typical_devices:
            return 1.0
        
        # Partial user agent similarity (for device family detection)
        current_ua_lower = auth_context.user_agent.lower()
        
        similarity_scores = []
        for device_hash in profile.typical_devices:
            # This is a simplified approach - in production, you'd want more sophisticated
            # device fingerprinting and user agent parsing
            similarity_scores.append(0.3)  # Partial similarity for same user
        
        return max(similarity_scores) if similarity_scores else 0.0
    
    def _calculate_pattern_consistency(
        self,
        auth_context: AuthContext,
        embedding_result: BehavioralEmbeddingResult,
        profile: UserBehavioralProfile
    ) -> float:
        """Calculate overall pattern consistency."""
        if not profile.success_patterns:
            return 0.0
        
        consistency_scores = []
        
        for pattern in profile.success_patterns[-10:]:  # Check last 10 patterns
            score = 0.0
            
            # Time consistency
            if abs(pattern['hour'] - auth_context.timestamp.hour) <= 2:
                score += 0.3
            
            # Day of week consistency
            if pattern['day_of_week'] == auth_context.timestamp.weekday():
                score += 0.2
            
            # Threat score consistency
            threat_diff = abs(pattern.get('threat_score', 0.0) - auth_context.threat_intel_score)
            if threat_diff < 0.2:
                score += 0.3
            
            # Location consistency
            if (auth_context.geolocation and 
                pattern.get('location') == auth_context.geolocation.country):
                score += 0.2
            
            consistency_scores.append(score)
        
        return sum(consistency_scores) / len(consistency_scores)
    
    def _detect_anomaly_indicators(
        self,
        auth_context: AuthContext,
        embedding_result: BehavioralEmbeddingResult,
        profile: UserBehavioralProfile,
        similarity_score: ProfileSimilarityScore
    ) -> List[str]:
        """Detect anomaly indicators in user behavior."""
        indicators = []
        
        # Low overall similarity
        if similarity_score.overall_similarity < self.config.anomaly_threshold:
            indicators.append("Low overall behavioral similarity")
        
        # Unusual time
        if similarity_score.temporal_similarity < 0.1:
            indicators.append("Unusual login time")
        
        # New location
        if similarity_score.location_similarity < 0.1:
            indicators.append("New or unusual location")
        
        # New device
        if similarity_score.device_similarity < 0.1:
            indicators.append("New or unusual device")
        
        # High threat intelligence score
        if auth_context.threat_intel_score > 0.7:
            indicators.append("High threat intelligence score")
        
        # Multiple failed attempts
        if auth_context.previous_failed_attempts > 3:
            indicators.append("Multiple recent failed attempts")
        
        # VPN or Tor usage (if unusual for user)
        if auth_context.is_vpn or auth_context.is_tor_exit_node:
            vpn_tor_usage = sum(
                1 for pattern in profile.success_patterns
                if pattern.get('context_features', {}).get('is_vpn') or
                   pattern.get('context_features', {}).get('is_tor')
            )
            if vpn_tor_usage / len(profile.success_patterns) < 0.1:
                indicators.append("Unusual VPN/Tor usage")
        
        return indicators
    
    def _identify_risk_factors(
        self,
        auth_context: AuthContext,
        embedding_result: BehavioralEmbeddingResult,
        profile: UserBehavioralProfile,
        similarity_score: ProfileSimilarityScore
    ) -> List[str]:
        """Identify risk factors in the authentication attempt."""
        risk_factors = []
        
        # Low confidence in profile
        if similarity_score.confidence_score < self.config.confidence_threshold:
            risk_factors.append("Low confidence in behavioral profile")
        
        # Rapid location changes
        if (auth_context.geolocation and profile.typical_locations and
            len(profile.typical_locations) > 1):
            recent_locations = profile.typical_locations[-5:]
            unique_countries = set(loc.get('country') for loc in recent_locations)
            if len(unique_countries) > 2:
                risk_factors.append("Rapid location changes detected")
        
        # Off-hours access
        if auth_context.timestamp.hour < 6 or auth_context.timestamp.hour > 22:
            night_logins = sum(
                1 for hour in profile.typical_login_times
                if hour < 6 or hour > 22
            )
            if night_logins / len(profile.typical_login_times) < 0.2:
                risk_factors.append("Unusual off-hours access")
        
        # Embedding outlier
        if similarity_score.embedding_similarity < 0.3:
            risk_factors.append("Behavioral embedding outlier")
        
        return risk_factors
    
    def _generate_recommendations(
        self,
        similarity_score: ProfileSimilarityScore,
        anomaly_indicators: List[str],
        risk_factors: List[str]
    ) -> List[str]:
        """Generate security recommendations based on analysis."""
        recommendations = []
        
        if similarity_score.overall_similarity < 0.3:
            recommendations.append("Consider requiring additional authentication factors")
        
        if len(anomaly_indicators) > 2:
            recommendations.append("High anomaly count - recommend security review")
        
        if len(risk_factors) > 1:
            recommendations.append("Multiple risk factors - consider blocking or monitoring")
        
        if similarity_score.confidence_score < 0.5:
            recommendations.append("Low profile confidence - collect more behavioral data")
        
        if not anomaly_indicators and not risk_factors:
            recommendations.append("Normal behavioral pattern - allow access")
        
        return recommendations
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        if len(vec1) != len(vec2):
            return 0.0
        
        try:
            import numpy as np
            vec1_np = np.array(vec1)
            vec2_np = np.array(vec2)
            
            dot_product = np.dot(vec1_np, vec2_np)
            norm1 = np.linalg.norm(vec1_np)
            norm2 = np.linalg.norm(vec2_np)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return float(dot_product / (norm1 * norm2))
            
        except ImportError:
            # Fallback without numpy
            dot_product = sum(a * b for a, b in zip(vec1, vec2))
            norm1 = sum(a * a for a in vec1) ** 0.5
            norm2 = sum(b * b for b in vec2) ** 0.5
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return dot_product / (norm1 * norm2)
    
    async def _get_user_profile(self, user_id: str) -> Optional[UserBehavioralProfile]:
        """Get user profile from memory or disk."""
        with self.access_lock:
            self.profile_access_times[user_id] = datetime.now()
        
        # Check memory first
        with self.profiles_lock:
            if user_id in self.profiles:
                self._cache_hits += 1
                return self.profiles[user_id]
        
        self._cache_misses += 1
        
        # Try to load from disk if persistence is enabled
        if self.config.enable_persistence:
            profile = await self._load_profile_from_disk(user_id)
            if profile:
                # Add to memory cache
                with self.profiles_lock:
                    self.profiles[user_id] = profile
                    # Evict old profiles if memory limit exceeded
                    await self._evict_old_profiles()
                return profile
        
        return None
    
    async def _load_profile_from_disk(self, user_id: str) -> Optional[UserBehavioralProfile]:
        """Load user profile from disk storage."""
        try:
            profile_file = self.persistence_path / f"{user_id}.json"
            if profile_file.exists():
                with open(profile_file, 'r') as f:
                    profile_data = json.load(f)
                
                profile = UserBehavioralProfile.from_dict(profile_data)
                self._profile_loads += 1
                return profile
                
        except Exception as e:
            self.logger.error(f"Failed to load profile for {user_id}: {e}")
        
        return None
    
    async def _schedule_profile_save(self, user_id: str) -> None:
        """Schedule profile save to disk."""
        try:
            profile = self.profiles.get(user_id)
            if profile:
                await self._save_profile_to_disk(user_id, profile)
        except Exception as e:
            self.logger.error(f"Failed to save profile for {user_id}: {e}")
    
    async def _save_profile_to_disk(self, user_id: str, profile: UserBehavioralProfile) -> None:
        """Save user profile to disk storage."""
        try:
            profile_file = self.persistence_path / f"{user_id}.json"
            profile_data = profile.to_dict()
            
            # Write atomically
            temp_file = profile_file.with_suffix('.tmp')
            with open(temp_file, 'w') as f:
                json.dump(profile_data, f, indent=2)
            
            temp_file.rename(profile_file)
            self._profile_saves += 1
            
        except Exception as e:
            self.logger.error(f"Failed to save profile for {user_id}: {e}")
    
    def _load_profiles_from_disk(self) -> None:
        """Load all profiles from disk storage."""
        try:
            profile_files = list(self.persistence_path.glob("*.json"))
            loaded_count = 0
            
            for profile_file in profile_files:
                try:
                    user_id = profile_file.stem
                    with open(profile_file, 'r') as f:
                        profile_data = json.load(f)
                    
                    profile = UserBehavioralProfile.from_dict(profile_data)
                    
                    # Check if profile is not expired
                    if (datetime.now() - profile.last_updated).days < self.config.profile_expiry_days:
                        self.profiles[user_id] = profile
                        self.profile_access_times[user_id] = profile.last_updated
                        loaded_count += 1
                    
                except Exception as e:
                    self.logger.error(f"Failed to load profile from {profile_file}: {e}")
            
            self.logger.info(f"Loaded {loaded_count} behavioral profiles from disk")
            
        except Exception as e:
            self.logger.error(f"Failed to load profiles from disk: {e}")
    
    async def _evict_old_profiles(self) -> None:
        """Evict old profiles from memory to maintain size limit."""
        if len(self.profiles) <= self.config.max_profiles_in_memory:
            return
        
        # Sort by access time and remove oldest
        with self.access_lock:
            sorted_profiles = sorted(
                self.profile_access_times.items(),
                key=lambda x: x[1]
            )
            
            profiles_to_remove = len(self.profiles) - self.config.max_profiles_in_memory
            
            for user_id, _ in sorted_profiles[:profiles_to_remove]:
                # Save to disk before removing from memory
                if self.config.enable_persistence and user_id in self.profiles:
                    await self._save_profile_to_disk(user_id, self.profiles[user_id])
                
                # Remove from memory
                with self.profiles_lock:
                    self.profiles.pop(user_id, None)
                self.profile_access_times.pop(user_id, None)
    
    def get_profile_statistics(self) -> Dict[str, Any]:
        """Get statistics about behavioral profiles."""
        with self.profiles_lock:
            profile_count = len(self.profiles)
            
            if profile_count == 0:
                return {
                    'total_profiles': 0,
                    'avg_login_count': 0,
                    'avg_embeddings_per_profile': 0,
                    'cache_hit_rate': 0.0
                }
            
            total_logins = sum(profile.login_count for profile in self.profiles.values())
            total_embeddings = sum(
                len(profile.typical_embeddings) for profile in self.profiles.values()
            )
            
            cache_total = self._cache_hits + self._cache_misses
            cache_hit_rate = self._cache_hits / cache_total if cache_total > 0 else 0.0
            
            return {
                'total_profiles': profile_count,
                'avg_login_count': total_logins / profile_count,
                'avg_embeddings_per_profile': total_embeddings / profile_count,
                'cache_hit_rate': cache_hit_rate,
                'profile_loads': self._profile_loads,
                'profile_saves': self._profile_saves,
                'similarity_calculations': self._similarity_calculations
            }
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of the profiling service."""
        return {
            'is_healthy': True,
            'profiles_in_memory': len(self.profiles),
            'persistence_enabled': self.config.enable_persistence,
            'persistence_path_exists': self.persistence_path.exists(),
            'background_tasks': len(self._background_tasks),
            'statistics': self.get_profile_statistics()
        }
    
    async def cleanup(self) -> None:
        """Cleanup resources and save profiles."""
        self.logger.info("Cleaning up behavioral profiling service...")
        
        # Signal shutdown
        self._shutdown_event.set()
        
        # Wait for background tasks to complete
        if self._background_tasks:
            await asyncio.gather(*self._background_tasks, return_exceptions=True)
        
        # Save all profiles to disk
        if self.config.enable_persistence:
            with self.profiles_lock:
                for user_id, profile in self.profiles.items():
                    await self._save_profile_to_disk(user_id, profile)
        
        self.logger.info("Behavioral profiling service cleanup completed")