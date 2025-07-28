"""
Unit tests for user behavioral profiling service.
"""

import pytest
import asyncio
import json
import tempfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
from typing import List

from src.ai_karen_engine.security.user_behavioral_profiling import (
    UserBehavioralProfilingService,
    UserBehavioralProfilingConfig,
    ProfileSimilarityScore,
    ProfileAnalysisResult
)
from src.ai_karen_engine.security.behavioral_embedding import (
    UserBehavioralProfile,
    BehavioralEmbeddingResult
)
from src.ai_karen_engine.security.models import AuthContext, GeoLocation


@pytest.fixture
def temp_profile_dir():
    """Create temporary directory for profile persistence."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def profiling_config(temp_profile_dir):
    """Create profiling configuration."""
    return UserBehavioralProfilingConfig(
        max_profiles_in_memory=10,
        profile_expiry_days=30,
        min_logins_for_profile=2,
        enable_persistence=True,
        persistence_path=temp_profile_dir,
        similarity_threshold=0.7,
        anomaly_threshold=0.3
    )


@pytest.fixture
def sample_auth_context():
    """Create sample authentication context."""
    return AuthContext(
        email="test@example.com",
        password_hash="hashed_password",
        client_ip="192.168.1.1",
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        timestamp=datetime.now(),
        request_id="test-request-123",
        geolocation=GeoLocation(
            country="US",
            region="CA",
            city="San Francisco",
            latitude=37.7749,
            longitude=-122.4194,
            timezone="America/Los_Angeles",
            is_usual_location=True
        ),
        device_fingerprint="device123",
        is_tor_exit_node=False,
        is_vpn=False,
        threat_intel_score=0.1,
        previous_failed_attempts=0
    )


@pytest.fixture
def sample_embedding_result():
    """Create sample behavioral embedding result."""
    return BehavioralEmbeddingResult(
        embedding_vector=[0.1] * 768,
        context_features={
            'timestamp_hour': 14,
            'country': 'US',
            'is_usual_location': True
        },
        processing_time=0.1,
        used_fallback=False,
        model_version="test-model",
        similarity_scores={'max_similarity_to_profile': 0.8}
    )


@pytest.fixture
def profiling_service(profiling_config):
    """Create user behavioral profiling service."""
    return UserBehavioralProfilingService(config=profiling_config)


@pytest.fixture
def mature_user_profile():
    """Create a mature user profile with sufficient data."""
    profile = UserBehavioralProfile(user_id="test@example.com")
    profile.login_count = 20
    profile.typical_embeddings = [[0.1] * 768 for _ in range(10)]
    profile.typical_login_times = [9, 10, 11, 14, 15, 16] * 3  # Business hours
    profile.typical_locations = [
        {'country': 'US', 'city': 'San Francisco', 'timezone': 'America/Los_Angeles'}
    ] * 5
    profile.typical_devices = ['device123', 'device456']
    profile.success_patterns = [
        {
            'timestamp': datetime.now().isoformat(),
            'hour': 14,
            'day_of_week': 1,
            'context_features': {'country': 'US'},
            'threat_score': 0.1,
            'location': 'US'
        }
    ] * 10
    return profile


class TestUserBehavioralProfilingService:
    """Test cases for UserBehavioralProfilingService."""
    
    def test_service_initialization(self, profiling_service, profiling_config):
        """Test service initialization."""
        assert profiling_service.config == profiling_config
        assert len(profiling_service.profiles) == 0
        assert profiling_service.persistence_path.exists()
    
    @pytest.mark.asyncio
    async def test_analyze_user_behavior_no_profile(
        self,
        profiling_service,
        sample_auth_context,
        sample_embedding_result
    ):
        """Test behavior analysis when no profile exists."""
        # Act
        result = await profiling_service.analyze_user_behavior(
            sample_auth_context,
            sample_embedding_result
        )
        
        # Assert
        assert isinstance(result, ProfileAnalysisResult)
        assert result.user_id == sample_auth_context.email
        assert not result.profile_exists
        assert result.similarity_score is None
        assert "Insufficient historical data" in result.recommendations[0]
        assert result.processing_time > 0
    
    @pytest.mark.asyncio
    async def test_analyze_user_behavior_insufficient_data(
        self,
        profiling_service,
        sample_auth_context,
        sample_embedding_result
    ):
        """Test behavior analysis with insufficient profile data."""
        # Arrange - Create profile with insufficient logins
        profile = UserBehavioralProfile(user_id=sample_auth_context.email)
        profile.login_count = 1  # Below min_logins_for_profile
        profiling_service.profiles[sample_auth_context.email] = profile
        
        # Act
        result = await profiling_service.analyze_user_behavior(
            sample_auth_context,
            sample_embedding_result
        )
        
        # Assert
        assert result.profile_exists
        assert result.similarity_score is None
        assert "Insufficient historical data" in result.recommendations[0]
    
    @pytest.mark.asyncio
    async def test_analyze_user_behavior_with_mature_profile(
        self,
        profiling_service,
        sample_auth_context,
        sample_embedding_result,
        mature_user_profile
    ):
        """Test behavior analysis with mature user profile."""
        # Arrange
        profiling_service.profiles[sample_auth_context.email] = mature_user_profile
        
        # Act
        result = await profiling_service.analyze_user_behavior(
            sample_auth_context,
            sample_embedding_result
        )
        
        # Assert
        assert result.profile_exists
        assert result.similarity_score is not None
        assert isinstance(result.similarity_score, ProfileSimilarityScore)
        assert 0.0 <= result.similarity_score.overall_similarity <= 1.0
        assert 0.0 <= result.similarity_score.confidence_score <= 1.0
        assert result.processing_time > 0
    
    @pytest.mark.asyncio
    async def test_update_user_profile_successful_login(
        self,
        profiling_service,
        sample_auth_context,
        sample_embedding_result
    ):
        """Test user profile update for successful login."""
        # Act
        await profiling_service.update_user_profile(
            sample_auth_context.email,
            sample_auth_context,
            sample_embedding_result,
            login_successful=True
        )
        
        # Wait for async tasks to complete if async updates are enabled
        if profiling_service.config.async_updates:
            await asyncio.sleep(0.1)  # Give async task time to complete
        
        # Assert
        profile = profiling_service.profiles.get(sample_auth_context.email)
        assert profile is not None
        assert profile.user_id == sample_auth_context.email
        assert len(profile.typical_embeddings) == 1
        assert profile.typical_embeddings[0] == sample_embedding_result.embedding_vector
        assert sample_auth_context.timestamp.hour in profile.typical_login_times
        assert profile.login_count == 1
        assert len(profile.typical_locations) == 1
        assert profile.typical_locations[0]['country'] == 'US'
    
    @pytest.mark.asyncio
    async def test_update_user_profile_failed_login(
        self,
        profiling_service,
        sample_auth_context,
        sample_embedding_result
    ):
        """Test that failed logins don't update profile."""
        # Act
        await profiling_service.update_user_profile(
            sample_auth_context.email,
            sample_auth_context,
            sample_embedding_result,
            login_successful=False
        )
        
        # Assert
        profile = profiling_service.profiles.get(sample_auth_context.email)
        assert profile is None  # Profile should not be created for failed logins
    
    def test_calculate_temporal_similarity(
        self,
        profiling_service,
        sample_auth_context,
        mature_user_profile
    ):
        """Test temporal similarity calculation."""
        # Arrange - Set current time to match profile pattern
        sample_auth_context.timestamp = sample_auth_context.timestamp.replace(hour=14)
        
        # Act
        similarity = profiling_service._calculate_temporal_similarity(
            sample_auth_context,
            mature_user_profile
        )
        
        # Assert
        assert 0.0 <= similarity <= 1.0
        assert similarity >= 0.5  # Should be high since hour 14 is in typical times
    
    def test_calculate_temporal_similarity_unusual_time(
        self,
        profiling_service,
        sample_auth_context,
        mature_user_profile
    ):
        """Test temporal similarity for unusual login time."""
        # Arrange - Set unusual time (3 AM)
        sample_auth_context.timestamp = sample_auth_context.timestamp.replace(hour=3)
        
        # Act
        similarity = profiling_service._calculate_temporal_similarity(
            sample_auth_context,
            mature_user_profile
        )
        
        # Assert
        assert 0.0 <= similarity <= 1.0
        assert similarity < 0.3  # Should be low for unusual time
    
    def test_calculate_location_similarity(
        self,
        profiling_service,
        sample_auth_context,
        mature_user_profile
    ):
        """Test location similarity calculation."""
        # Act
        similarity = profiling_service._calculate_location_similarity(
            sample_auth_context,
            mature_user_profile
        )
        
        # Assert
        assert 0.0 <= similarity <= 1.0
        assert similarity > 0.5  # Should be high since location matches profile
    
    def test_calculate_location_similarity_new_location(
        self,
        profiling_service,
        sample_auth_context,
        mature_user_profile
    ):
        """Test location similarity for new location."""
        # Arrange - Change to different location
        sample_auth_context.geolocation.country = "UK"
        sample_auth_context.geolocation.city = "London"
        
        # Act
        similarity = profiling_service._calculate_location_similarity(
            sample_auth_context,
            mature_user_profile
        )
        
        # Assert
        assert 0.0 <= similarity <= 1.0
        assert similarity < 0.3  # Should be low for new location
    
    def test_calculate_device_similarity(
        self,
        profiling_service,
        sample_auth_context,
        mature_user_profile
    ):
        """Test device similarity calculation."""
        # Act
        similarity = profiling_service._calculate_device_similarity(
            sample_auth_context,
            mature_user_profile
        )
        
        # Assert
        assert 0.0 <= similarity <= 1.0
        # Note: This will likely be low since device hash won't match exactly
    
    def test_detect_anomaly_indicators(
        self,
        profiling_service,
        sample_auth_context,
        sample_embedding_result,
        mature_user_profile
    ):
        """Test anomaly indicator detection."""
        # Arrange - Create low similarity score
        similarity_score = ProfileSimilarityScore(
            overall_similarity=0.2,  # Low similarity
            embedding_similarity=0.1,
            temporal_similarity=0.05,  # Very low
            location_similarity=0.1,
            device_similarity=0.1,
            pattern_consistency=0.2,
            confidence_score=0.8
        )
        
        # Act
        indicators = profiling_service._detect_anomaly_indicators(
            sample_auth_context,
            sample_embedding_result,
            mature_user_profile,
            similarity_score
        )
        
        # Assert
        assert isinstance(indicators, list)
        assert len(indicators) > 0
        assert any("Low overall behavioral similarity" in indicator for indicator in indicators)
        assert any("Unusual login time" in indicator for indicator in indicators)
    
    def test_detect_anomaly_indicators_high_threat(
        self,
        profiling_service,
        sample_auth_context,
        sample_embedding_result,
        mature_user_profile
    ):
        """Test anomaly detection with high threat score."""
        # Arrange
        sample_auth_context.threat_intel_score = 0.8  # High threat
        similarity_score = ProfileSimilarityScore(
            overall_similarity=0.8,
            embedding_similarity=0.8,
            temporal_similarity=0.8,
            location_similarity=0.8,
            device_similarity=0.8,
            pattern_consistency=0.8,
            confidence_score=0.8
        )
        
        # Act
        indicators = profiling_service._detect_anomaly_indicators(
            sample_auth_context,
            sample_embedding_result,
            mature_user_profile,
            similarity_score
        )
        
        # Assert
        assert any("High threat intelligence score" in indicator for indicator in indicators)
    
    def test_identify_risk_factors(
        self,
        profiling_service,
        sample_auth_context,
        sample_embedding_result,
        mature_user_profile
    ):
        """Test risk factor identification."""
        # Arrange - Create low confidence score
        similarity_score = ProfileSimilarityScore(
            overall_similarity=0.7,
            embedding_similarity=0.7,
            temporal_similarity=0.7,
            location_similarity=0.7,
            device_similarity=0.7,
            pattern_consistency=0.7,
            confidence_score=0.4  # Low confidence
        )
        
        # Act
        risk_factors = profiling_service._identify_risk_factors(
            sample_auth_context,
            sample_embedding_result,
            mature_user_profile,
            similarity_score
        )
        
        # Assert
        assert isinstance(risk_factors, list)
        assert any("Low confidence in behavioral profile" in factor for factor in risk_factors)
    
    def test_generate_recommendations(self, profiling_service):
        """Test recommendation generation."""
        # Arrange
        similarity_score = ProfileSimilarityScore(
            overall_similarity=0.2,  # Low similarity
            embedding_similarity=0.2,
            temporal_similarity=0.2,
            location_similarity=0.2,
            device_similarity=0.2,
            pattern_consistency=0.2,
            confidence_score=0.8
        )
        anomaly_indicators = ["Low overall behavioral similarity", "Unusual login time", "New location"]
        risk_factors = ["Multiple risk factors detected", "Another risk factor"]
        
        # Act
        recommendations = profiling_service._generate_recommendations(
            similarity_score,
            anomaly_indicators,
            risk_factors
        )
        
        # Assert
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0

        assert any("additional authentication factors" in rec for rec in recommendations)
        assert any("security review" in rec for rec in recommendations)
    
    def test_generate_recommendations_normal_behavior(self, profiling_service):
        """Test recommendations for normal behavior."""
        # Arrange
        similarity_score = ProfileSimilarityScore(
            overall_similarity=0.8,  # High similarity
            embedding_similarity=0.8,
            temporal_similarity=0.8,
            location_similarity=0.8,
            device_similarity=0.8,
            pattern_consistency=0.8,
            confidence_score=0.8
        )
        anomaly_indicators = []
        risk_factors = []
        
        # Act
        recommendations = profiling_service._generate_recommendations(
            similarity_score,
            anomaly_indicators,
            risk_factors
        )
        
        # Assert
        assert any("Normal behavioral pattern" in rec for rec in recommendations)
    
    @pytest.mark.asyncio
    async def test_profile_persistence_save_and_load(
        self,
        profiling_service,
        sample_auth_context,
        sample_embedding_result
    ):
        """Test profile persistence - save and load."""
        # Arrange - Update profile
        await profiling_service.update_user_profile(
            sample_auth_context.email,
            sample_auth_context,
            sample_embedding_result,
            login_successful=True
        )
        
        # Wait for async tasks to complete if async updates are enabled
        if profiling_service.config.async_updates:
            await asyncio.sleep(0.1)  # Give async task time to complete
        
        # Act - Save profile
        profile = profiling_service.profiles[sample_auth_context.email]
        await profiling_service._save_profile_to_disk(sample_auth_context.email, profile)
        
        # Clear memory and load from disk
        profiling_service.profiles.clear()
        loaded_profile = await profiling_service._load_profile_from_disk(sample_auth_context.email)
        
        # Assert
        assert loaded_profile is not None
        assert loaded_profile.user_id == sample_auth_context.email
        assert loaded_profile.login_count == profile.login_count
        assert len(loaded_profile.typical_embeddings) == len(profile.typical_embeddings)
    
    @pytest.mark.asyncio
    async def test_get_user_profile_from_memory(
        self,
        profiling_service,
        sample_auth_context,
        mature_user_profile
    ):
        """Test getting user profile from memory."""
        # Arrange
        profiling_service.profiles[sample_auth_context.email] = mature_user_profile
        
        # Act
        profile = await profiling_service._get_user_profile(sample_auth_context.email)
        
        # Assert
        assert profile is not None
        assert profile.user_id == sample_auth_context.email
        assert profile.login_count == mature_user_profile.login_count
    
    @pytest.mark.asyncio
    async def test_get_user_profile_from_disk(
        self,
        profiling_service,
        sample_auth_context,
        mature_user_profile
    ):
        """Test getting user profile from disk when not in memory."""
        # Arrange - Save profile to disk
        await profiling_service._save_profile_to_disk(sample_auth_context.email, mature_user_profile)
        
        # Act - Get profile (should load from disk)
        profile = await profiling_service._get_user_profile(sample_auth_context.email)
        
        # Assert
        assert profile is not None
        assert profile.user_id == sample_auth_context.email
        assert profile.login_count == mature_user_profile.login_count
        # Should now be in memory cache
        assert sample_auth_context.email in profiling_service.profiles
    
    def test_get_profile_statistics(self, profiling_service, mature_user_profile):
        """Test profile statistics generation."""
        # Arrange
        profiling_service.profiles["user1"] = mature_user_profile
        profiling_service.profiles["user2"] = mature_user_profile
        profiling_service._cache_hits = 10
        profiling_service._cache_misses = 5
        
        # Act
        stats = profiling_service.get_profile_statistics()
        
        # Assert
        assert stats['total_profiles'] == 2
        assert stats['avg_login_count'] == mature_user_profile.login_count
        assert stats['cache_hit_rate'] == 10 / 15  # 10 hits out of 15 total
        assert 'avg_embeddings_per_profile' in stats
    
    def test_get_profile_statistics_empty(self, profiling_service):
        """Test profile statistics with no profiles."""
        # Act
        stats = profiling_service.get_profile_statistics()
        
        # Assert
        assert stats['total_profiles'] == 0
        assert stats['avg_login_count'] == 0
        assert stats['avg_embeddings_per_profile'] == 0
        assert stats['cache_hit_rate'] == 0.0
    
    def test_get_health_status(self, profiling_service):
        """Test health status reporting."""
        # Act
        health = profiling_service.get_health_status()
        
        # Assert
        assert health['is_healthy'] is True
        assert 'profiles_in_memory' in health
        assert 'persistence_enabled' in health
        assert 'persistence_path_exists' in health
        assert 'background_tasks' in health
        assert 'statistics' in health
    
    @pytest.mark.asyncio
    async def test_cleanup(self, profiling_service, sample_auth_context, mature_user_profile):
        """Test service cleanup."""
        # Arrange
        profiling_service.profiles[sample_auth_context.email] = mature_user_profile
        
        # Act
        await profiling_service.cleanup()
        
        # Assert
        assert profiling_service._shutdown_event.is_set()
        # Profile should be saved to disk
        profile_file = profiling_service.persistence_path / f"{sample_auth_context.email}.json"
        assert profile_file.exists()


class TestProfileSimilarityScore:
    """Test cases for ProfileSimilarityScore."""
    
    def test_profile_similarity_score_creation(self):
        """Test profile similarity score creation."""
        # Act
        score = ProfileSimilarityScore(
            overall_similarity=0.8,
            embedding_similarity=0.7,
            temporal_similarity=0.9,
            location_similarity=0.6,
            device_similarity=0.8,
            pattern_consistency=0.7,
            confidence_score=0.9
        )
        
        # Assert
        assert score.overall_similarity == 0.8
        assert score.embedding_similarity == 0.7
        assert score.temporal_similarity == 0.9
        assert score.location_similarity == 0.6
        assert score.device_similarity == 0.8
        assert score.pattern_consistency == 0.7
        assert score.confidence_score == 0.9
    
    def test_profile_similarity_score_serialization(self):
        """Test profile similarity score serialization."""
        # Arrange
        score = ProfileSimilarityScore(
            overall_similarity=0.8,
            embedding_similarity=0.7,
            temporal_similarity=0.9,
            location_similarity=0.6,
            device_similarity=0.8,
            pattern_consistency=0.7,
            confidence_score=0.9
        )
        
        # Act
        score_dict = score.to_dict()
        restored_score = ProfileSimilarityScore.from_dict(score_dict)
        
        # Assert
        assert restored_score.overall_similarity == score.overall_similarity
        assert restored_score.embedding_similarity == score.embedding_similarity
        assert restored_score.temporal_similarity == score.temporal_similarity
        assert restored_score.location_similarity == score.location_similarity
        assert restored_score.device_similarity == score.device_similarity
        assert restored_score.pattern_consistency == score.pattern_consistency
        assert restored_score.confidence_score == score.confidence_score


class TestUserBehavioralProfilingConfig:
    """Test cases for UserBehavioralProfilingConfig."""
    
    def test_config_defaults(self):
        """Test configuration defaults."""
        # Act
        config = UserBehavioralProfilingConfig()
        
        # Assert
        assert config.max_profiles_in_memory == 1000
        assert config.profile_expiry_days == 90
        assert config.min_logins_for_profile == 3
        assert config.enable_persistence is True
        assert config.embedding_weight == 0.4
        assert config.temporal_weight == 0.2
        assert config.location_weight == 0.2
        assert config.device_weight == 0.1
        assert config.pattern_weight == 0.1
        assert config.similarity_threshold == 0.7
        assert config.anomaly_threshold == 0.3
    
    def test_config_custom_values(self):
        """Test configuration with custom values."""
        # Act
        config = UserBehavioralProfilingConfig(
            max_profiles_in_memory=500,
            min_logins_for_profile=5,
            embedding_weight=0.5,
            similarity_threshold=0.8
        )
        
        # Assert
        assert config.max_profiles_in_memory == 500
        assert config.min_logins_for_profile == 5
        assert config.embedding_weight == 0.5
        assert config.similarity_threshold == 0.8
        # Other values should remain default
        assert config.temporal_weight == 0.2
        assert config.anomaly_threshold == 0.3


if __name__ == "__main__":
    pytest.main([__file__])