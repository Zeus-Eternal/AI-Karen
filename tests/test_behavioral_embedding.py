"""
Unit tests for behavioral embedding service.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from typing import List

from src.ai_karen_engine.security.behavioral_embedding import (
    BehavioralEmbeddingService,
    BehavioralEmbeddingConfig,
    BehavioralEmbeddingResult,
    UserBehavioralProfile
)
from src.ai_karen_engine.security.models import AuthContext, GeoLocation, EmbeddingAnalysis
from src.ai_karen_engine.services.distilbert_service import DistilBertService


@pytest.fixture
def mock_distilbert_service():
    """Create mock DistilBERT service."""
    service = Mock(spec=DistilBertService)
    service.get_embeddings = AsyncMock(return_value=[0.1] * 768)
    service.fallback_mode = False
    service.config = Mock()
    service.config.model_name = "distilbert-base-uncased"
    service.get_health_status = Mock()
    service.get_health_status.return_value = Mock(is_healthy=True, fallback_mode=False)
    return service


@pytest.fixture
def behavioral_embedding_config():
    """Create behavioral embedding configuration."""
    return BehavioralEmbeddingConfig(
        enable_context_enrichment=True,
        enable_temporal_features=True,
        enable_geolocation_features=True,
        enable_device_features=True,
        max_profile_embeddings=10,
        cache_size=100,
        cache_ttl=300
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
def behavioral_embedding_service(mock_distilbert_service, behavioral_embedding_config):
    """Create behavioral embedding service with mocked dependencies."""
    return BehavioralEmbeddingService(
        distilbert_service=mock_distilbert_service,
        config=behavioral_embedding_config
    )


class TestBehavioralEmbeddingService:
    """Test cases for BehavioralEmbeddingService."""
    
    @pytest.mark.asyncio
    async def test_generate_behavioral_embedding_success(
        self,
        behavioral_embedding_service,
        sample_auth_context,
        mock_distilbert_service
    ):
        """Test successful behavioral embedding generation."""
        # Arrange
        expected_embedding = [0.1] * 768
        mock_distilbert_service.get_embeddings.return_value = expected_embedding
        
        # Act
        result = await behavioral_embedding_service.generate_behavioral_embedding(sample_auth_context)
        
        # Assert
        assert isinstance(result, BehavioralEmbeddingResult)
        assert result.embedding_vector == expected_embedding
        assert result.processing_time > 0
        assert not result.used_fallback
        assert result.model_version == "distilbert-base-uncased"
        assert isinstance(result.context_features, dict)
        
        # Verify DistilBERT service was called
        mock_distilbert_service.get_embeddings.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_behavioral_embedding_with_caching(
        self,
        behavioral_embedding_service,
        sample_auth_context,
        mock_distilbert_service
    ):
        """Test that embedding generation uses caching."""
        # Arrange
        expected_embedding = [0.2] * 768
        mock_distilbert_service.get_embeddings.return_value = expected_embedding
        
        # Act - First call
        result1 = await behavioral_embedding_service.generate_behavioral_embedding(sample_auth_context)
        
        # Act - Second call with same context
        result2 = await behavioral_embedding_service.generate_behavioral_embedding(sample_auth_context)
        
        # Assert
        assert result1.embedding_vector == result2.embedding_vector
        # DistilBERT service should only be called once due to caching
        mock_distilbert_service.get_embeddings.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_behavioral_embedding_fallback(
        self,
        behavioral_embedding_service,
        sample_auth_context,
        mock_distilbert_service
    ):
        """Test fallback behavior when DistilBERT service fails."""
        # Arrange
        mock_distilbert_service.get_embeddings.side_effect = Exception("Service unavailable")
        
        # Act
        result = await behavioral_embedding_service.generate_behavioral_embedding(sample_auth_context)
        
        # Assert
        assert isinstance(result, BehavioralEmbeddingResult)
        assert len(result.embedding_vector) == 768  # Should have correct dimension
        assert result.used_fallback
        assert result.model_version == "hash_fallback"
        assert result.processing_time > 0
    
    def test_extract_context_features(self, behavioral_embedding_service, sample_auth_context):
        """Test context feature extraction."""
        # Act
        features = behavioral_embedding_service._extract_context_features(sample_auth_context)
        
        # Assert
        assert isinstance(features, dict)
        assert 'timestamp_hour' in features
        assert 'timestamp_day_of_week' in features
        assert 'timestamp_is_weekend' in features
        assert 'country' in features
        assert 'timezone' in features
        assert 'is_usual_location' in features
        assert 'user_agent_hash' in features
        assert 'threat_intel_score' in features
        assert 'previous_failed_attempts' in features
        
        # Verify values
        assert features['timestamp_hour'] == sample_auth_context.timestamp.hour
        assert features['country'] == "US"
        assert features['is_usual_location'] is True
        assert features['threat_intel_score'] == 0.1
    
    def test_create_context_text(self, behavioral_embedding_service, sample_auth_context):
        """Test context text creation."""
        # Arrange
        features = behavioral_embedding_service._extract_context_features(sample_auth_context)
        
        # Act
        context_text = behavioral_embedding_service._create_context_text(sample_auth_context, features)
        
        # Assert
        assert isinstance(context_text, str)
        assert "domain:example.com" in context_text
        assert f"hour:{sample_auth_context.timestamp.hour}" in context_text
        assert "country:US" in context_text
        assert "timezone:America/Los_Angeles" in context_text
        assert "usual_location" in context_text
        assert "threat:low" in context_text
    
    def test_cosine_similarity(self, behavioral_embedding_service):
        """Test cosine similarity calculation."""
        # Arrange
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [0.0, 1.0, 0.0]
        vec3 = [1.0, 0.0, 0.0]
        
        # Act
        similarity_orthogonal = behavioral_embedding_service._cosine_similarity(vec1, vec2)
        similarity_identical = behavioral_embedding_service._cosine_similarity(vec1, vec3)
        
        # Assert
        assert abs(similarity_orthogonal - 0.0) < 1e-6  # Should be 0 for orthogonal vectors
        assert abs(similarity_identical - 1.0) < 1e-6   # Should be 1 for identical vectors
    
    def test_cosine_similarity_edge_cases(self, behavioral_embedding_service):
        """Test cosine similarity with edge cases."""
        # Test with different length vectors
        vec1 = [1.0, 0.0]
        vec2 = [1.0, 0.0, 0.0]
        similarity = behavioral_embedding_service._cosine_similarity(vec1, vec2)
        assert similarity == 0.0
        
        # Test with zero vectors
        vec_zero = [0.0, 0.0, 0.0]
        vec_normal = [1.0, 1.0, 1.0]
        similarity = behavioral_embedding_service._cosine_similarity(vec_zero, vec_normal)
        assert similarity == 0.0
    
    @pytest.mark.asyncio
    async def test_update_user_behavioral_profile(
        self,
        behavioral_embedding_service,
        sample_auth_context,
        mock_distilbert_service
    ):
        """Test user behavioral profile updates."""
        # Arrange
        embedding_result = BehavioralEmbeddingResult(
            embedding_vector=[0.1] * 768,
            context_features={'test': 'feature'},
            processing_time=0.1,
            used_fallback=False,
            model_version="test-model"
        )
        
        # Act
        await behavioral_embedding_service.update_user_behavioral_profile(
            sample_auth_context.email,
            sample_auth_context,
            embedding_result,
            login_successful=True
        )
        
        # Assert
        profile = behavioral_embedding_service.get_user_profile(sample_auth_context.email)
        assert profile is not None
        assert profile.user_id == sample_auth_context.email
        assert len(profile.typical_embeddings) == 1
        assert profile.typical_embeddings[0] == embedding_result.embedding_vector
        assert sample_auth_context.timestamp.hour in profile.typical_login_times
        assert profile.login_count == 1
        assert len(profile.typical_locations) == 1
        assert profile.typical_locations[0]['country'] == 'US'
    
    @pytest.mark.asyncio
    async def test_update_user_behavioral_profile_failed_login(
        self,
        behavioral_embedding_service,
        sample_auth_context,
        mock_distilbert_service
    ):
        """Test that failed logins don't update behavioral profile."""
        # Arrange
        embedding_result = BehavioralEmbeddingResult(
            embedding_vector=[0.1] * 768,
            context_features={'test': 'feature'},
            processing_time=0.1,
            used_fallback=False,
            model_version="test-model"
        )
        
        # Act
        await behavioral_embedding_service.update_user_behavioral_profile(
            sample_auth_context.email,
            sample_auth_context,
            embedding_result,
            login_successful=False
        )
        
        # Assert
        profile = behavioral_embedding_service.get_user_profile(sample_auth_context.email)
        assert profile is None  # Profile should not be created for failed logins
    
    @pytest.mark.asyncio
    async def test_analyze_embedding_for_anomalies(
        self,
        behavioral_embedding_service,
        sample_auth_context,
        mock_distilbert_service
    ):
        """Test embedding anomaly analysis."""
        # Arrange
        embedding_result = BehavioralEmbeddingResult(
            embedding_vector=[0.1] * 768,
            context_features={'test': 'feature'},
            processing_time=0.1,
            used_fallback=False,
            model_version="test-model",
            similarity_scores={'max_similarity_to_profile': 0.8}
        )
        
        # Act
        analysis = await behavioral_embedding_service.analyze_embedding_for_anomalies(
            sample_auth_context,
            embedding_result
        )
        
        # Assert
        assert analysis is not None
        assert hasattr(analysis, 'embedding_vector')
        assert hasattr(analysis, 'similarity_to_user_profile')
        assert analysis.embedding_vector == embedding_result.embedding_vector
        assert analysis.similarity_to_user_profile == 0.8
        assert analysis.similarity_to_attack_patterns == 0.0  # Placeholder value
        assert abs(analysis.outlier_score - 0.2) < 1e-10  # 1.0 - 0.8 with floating point tolerance
        assert analysis.processing_time == 0.1
        assert analysis.model_version == "test-model"
    
    @pytest.mark.asyncio
    async def test_calculate_similarity_scores_no_profile(
        self,
        behavioral_embedding_service,
        mock_distilbert_service
    ):
        """Test similarity calculation when no user profile exists."""
        # Arrange
        embedding_vector = [0.1] * 768
        
        # Act
        similarity_scores = await behavioral_embedding_service._calculate_similarity_scores(
            "nonexistent@example.com",
            embedding_vector
        )
        
        # Assert
        assert similarity_scores == {}  # Should return empty dict when no profile exists
    
    @pytest.mark.asyncio
    async def test_calculate_similarity_scores_with_profile(
        self,
        behavioral_embedding_service,
        sample_auth_context,
        mock_distilbert_service
    ):
        """Test similarity calculation with existing user profile."""
        # Arrange
        # First create a profile
        embedding_result = BehavioralEmbeddingResult(
            embedding_vector=[0.5] * 768,
            context_features={'test': 'feature'},
            processing_time=0.1,
            used_fallback=False,
            model_version="test-model"
        )
        
        await behavioral_embedding_service.update_user_behavioral_profile(
            sample_auth_context.email,
            sample_auth_context,
            embedding_result,
            login_successful=True
        )
        
        # Act
        new_embedding = [0.6] * 768  # Similar to profile embedding
        similarity_scores = await behavioral_embedding_service._calculate_similarity_scores(
            sample_auth_context.email,
            new_embedding
        )
        
        # Assert
        assert 'max_similarity_to_profile' in similarity_scores
        assert 'avg_similarity_to_profile' in similarity_scores
        assert 'min_similarity_to_profile' in similarity_scores
        # Allow for small floating point precision errors
        for key, score in similarity_scores.items():
            assert -1e-10 <= score <= 1.0 + 1e-10, f"Score {key}={score} is out of range [0.0, 1.0]"
    
    @pytest.mark.asyncio
    async def test_batch_generate_embeddings(
        self,
        behavioral_embedding_service,
        sample_auth_context,
        mock_distilbert_service
    ):
        """Test batch embedding generation."""
        # Arrange
        auth_contexts = [sample_auth_context] * 3
        mock_distilbert_service.get_embeddings.return_value = [0.1] * 768
        
        # Act
        results = await behavioral_embedding_service.batch_generate_embeddings(auth_contexts)
        
        # Assert
        assert len(results) == 3
        assert all(isinstance(result, BehavioralEmbeddingResult) for result in results)
        assert all(result.embedding_vector == [0.1] * 768 for result in results)
    
    def test_get_health_status(self, behavioral_embedding_service, mock_distilbert_service):
        """Test health status reporting."""
        # Act
        health_status = behavioral_embedding_service.get_health_status()
        
        # Assert
        assert isinstance(health_status, dict)
        assert 'is_healthy' in health_status
        assert 'distilbert_service_healthy' in health_status
        assert 'fallback_mode' in health_status
        assert 'embedding_count' in health_status
        assert 'similarity_calculations' in health_status
        assert 'cache_hit_rate' in health_status
        assert 'avg_processing_time' in health_status
        assert 'user_profiles_count' in health_status
        assert 'cache_size' in health_status
    
    def test_clear_cache(self, behavioral_embedding_service):
        """Test cache clearing."""
        # Arrange - Add something to cache first
        behavioral_embedding_service.embedding_cache['test_key'] = 'test_value'
        behavioral_embedding_service.similarity_cache['test_key'] = 'test_value'
        
        # Act
        behavioral_embedding_service.clear_cache()
        
        # Assert
        assert len(behavioral_embedding_service.embedding_cache) == 0
        assert len(behavioral_embedding_service.similarity_cache) == 0
    
    def test_reset_metrics(self, behavioral_embedding_service):
        """Test metrics reset."""
        # Arrange - Set some metrics
        behavioral_embedding_service._embedding_count = 10
        behavioral_embedding_service._similarity_calculations = 5
        behavioral_embedding_service._cache_hits = 3
        behavioral_embedding_service._cache_misses = 2
        behavioral_embedding_service._processing_times = [0.1, 0.2, 0.3]
        
        # Act
        behavioral_embedding_service.reset_metrics()
        
        # Assert
        assert behavioral_embedding_service._embedding_count == 0
        assert behavioral_embedding_service._similarity_calculations == 0
        assert behavioral_embedding_service._cache_hits == 0
        assert behavioral_embedding_service._cache_misses == 0
        assert behavioral_embedding_service._processing_times == []


class TestUserBehavioralProfile:
    """Test cases for UserBehavioralProfile."""
    
    def test_user_behavioral_profile_creation(self):
        """Test user behavioral profile creation."""
        # Act
        profile = UserBehavioralProfile(user_id="test@example.com")
        
        # Assert
        assert profile.user_id == "test@example.com"
        assert profile.typical_embeddings == []
        assert profile.typical_login_times == []
        assert profile.typical_locations == []
        assert profile.typical_devices == []
        assert profile.success_patterns == []
        assert profile.login_count == 0
        assert isinstance(profile.last_updated, datetime)
    
    def test_user_behavioral_profile_serialization(self):
        """Test user behavioral profile serialization."""
        # Arrange
        profile = UserBehavioralProfile(
            user_id="test@example.com",
            typical_embeddings=[[0.1, 0.2, 0.3]],
            typical_login_times=[9, 10, 11],
            login_count=5
        )
        
        # Act
        profile_dict = profile.to_dict()
        restored_profile = UserBehavioralProfile.from_dict(profile_dict)
        
        # Assert
        assert restored_profile.user_id == profile.user_id
        assert restored_profile.typical_embeddings == profile.typical_embeddings
        assert restored_profile.typical_login_times == profile.typical_login_times
        assert restored_profile.login_count == profile.login_count


class TestBehavioralEmbeddingConfig:
    """Test cases for BehavioralEmbeddingConfig."""
    
    def test_behavioral_embedding_config_defaults(self):
        """Test behavioral embedding configuration defaults."""
        # Act
        config = BehavioralEmbeddingConfig()
        
        # Assert
        assert config.enable_context_enrichment is True
        assert config.enable_temporal_features is True
        assert config.enable_geolocation_features is True
        assert config.enable_device_features is True
        assert config.max_profile_embeddings == 50
        assert config.profile_update_threshold == 0.8
        assert config.similarity_threshold == 0.7
        assert config.outlier_threshold == 0.3
        assert config.cache_size == 5000
        assert config.cache_ttl == 3600
    
    def test_behavioral_embedding_config_custom_values(self):
        """Test behavioral embedding configuration with custom values."""
        # Act
        config = BehavioralEmbeddingConfig(
            enable_context_enrichment=False,
            max_profile_embeddings=100,
            cache_size=1000
        )
        
        # Assert
        assert config.enable_context_enrichment is False
        assert config.max_profile_embeddings == 100
        assert config.cache_size == 1000
        # Other values should remain default
        assert config.enable_temporal_features is True
        assert config.similarity_threshold == 0.7


if __name__ == "__main__":
    pytest.main([__file__])