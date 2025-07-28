"""
Unit tests for adaptive learning engine.

Tests the adaptive learning functionality including feedback processing,
threshold adjustments, model versioning, and rollback capabilities.
"""

import asyncio
import json
import pytest
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

from ai_karen_engine.security.adaptive_learning import (
    AdaptiveLearningEngine,
    AuthFeedback,
    ModelVersion,
    UserAdaptiveProfile,
    LearningConfig
)
from ai_karen_engine.security.models import (
    AuthContext,
    IntelligentAuthConfig,
    RiskThresholds,
    GeoLocation
)
from ai_karen_engine.security.intelligent_auth_base import (
    ServiceStatus
)


@pytest.fixture
def learning_config():
    """Create test learning configuration."""
    return LearningConfig(
        learning_rate=0.05,
        adaptation_window=50,
        min_samples_for_adaptation=5,
        threshold_adjustment_step=0.1,
        max_threshold_adjustment=0.2,
        feedback_confidence_threshold=0.8
    )


@pytest.fixture
def intelligent_auth_config():
    """Create test intelligent auth configuration."""
    return IntelligentAuthConfig(
        enable_nlp_analysis=True,
        enable_embedding_analysis=True,
        enable_behavioral_analysis=True,
        risk_thresholds=RiskThresholds(
            low_risk_threshold=0.3,
            medium_risk_threshold=0.6,
            high_risk_threshold=0.8,
            critical_risk_threshold=0.95
        ),
        max_processing_time=5.0,
        cache_size=1000,
        cache_ttl=3600
    )


@pytest.fixture
def adaptive_learning_engine(intelligent_auth_config, learning_config):
    """Create test adaptive learning engine."""
    with tempfile.TemporaryDirectory() as temp_dir:
        engine = AdaptiveLearningEngine(intelligent_auth_config, learning_config)
        engine.storage_path = Path(temp_dir) / "adaptive_learning"
        engine.storage_path.mkdir(parents=True, exist_ok=True)
        return engine


@pytest.fixture
def sample_auth_context():
    """Create sample authentication context."""
    return AuthContext(
        email="test@example.com",
        password_hash="hashed_password",
        client_ip="192.168.1.100",
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        timestamp=datetime.now(),
        request_id="test_request_123",
        geolocation=GeoLocation(
            country="US",
            region="CA",
            city="San Francisco",
            latitude=37.7749,
            longitude=-122.4194,
            timezone="America/Los_Angeles",
            is_usual_location=True
        ),
        device_fingerprint="device_123",
        is_tor_exit_node=False,
        is_vpn=False,
        threat_intel_score=0.1,
        previous_failed_attempts=0
    )


@pytest.fixture
def sample_feedback():
    """Create sample authentication feedback."""
    return AuthFeedback(
        user_id="test_user",
        request_id="test_request_123",
        timestamp=datetime.now(),
        original_risk_score=0.7,
        original_decision="block",
        is_false_positive=True,
        is_correct=False,
        confidence=0.9,
        feedback_source="admin"
    )


class TestAuthFeedback:
    """Test AuthFeedback data model."""
    
    def test_feedback_creation(self, sample_feedback):
        """Test feedback creation and validation."""
        assert sample_feedback.user_id == "test_user"
        assert sample_feedback.is_false_positive is True
        assert sample_feedback.confidence == 0.9
        assert sample_feedback.feedback_source == "admin"
    
    def test_feedback_serialization(self, sample_feedback):
        """Test feedback serialization and deserialization."""
        # Test to_dict
        feedback_dict = sample_feedback.to_dict()
        assert isinstance(feedback_dict['timestamp'], str)
        assert feedback_dict['user_id'] == "test_user"
        assert feedback_dict['is_false_positive'] is True
        
        # Test from_dict
        restored_feedback = AuthFeedback.from_dict(feedback_dict)
        assert restored_feedback.user_id == sample_feedback.user_id
        assert restored_feedback.is_false_positive == sample_feedback.is_false_positive
        assert isinstance(restored_feedback.timestamp, datetime)


class TestModelVersion:
    """Test ModelVersion data model."""
    
    def test_model_version_creation(self):
        """Test model version creation."""
        model_data = {"threshold": 0.5, "weights": [0.1, 0.2, 0.3]}
        performance_metrics = {"accuracy": 0.85, "precision": 0.80}
        
        version = ModelVersion(
            version_id="test_v1",
            created_at=datetime.now(),
            model_type="thresholds",
            model_data=model_data,
            performance_metrics=performance_metrics,
            is_active=True
        )
        
        assert version.version_id == "test_v1"
        assert version.model_type == "thresholds"
        assert version.is_active is True
        assert version.performance_metrics["accuracy"] == 0.85
    
    def test_model_version_serialization(self):
        """Test model version serialization."""
        model_data = {"threshold": 0.5}
        version = ModelVersion(
            version_id="test_v1",
            created_at=datetime.now(),
            model_type="thresholds",
            model_data=model_data,
            is_active=True
        )
        
        # Test to_dict
        version_dict = version.to_dict()
        assert isinstance(version_dict['created_at'], str)
        assert version_dict['model_type'] == "thresholds"
        
        # Test from_dict
        restored_version = ModelVersion.from_dict(version_dict)
        assert restored_version.version_id == version.version_id
        assert isinstance(restored_version.created_at, datetime)


class TestUserAdaptiveProfile:
    """Test UserAdaptiveProfile data model."""
    
    def test_profile_creation(self):
        """Test user profile creation."""
        profile = UserAdaptiveProfile(user_id="test_user")
        
        assert profile.user_id == "test_user"
        assert profile.false_positive_count == 0
        assert profile.false_negative_count == 0
        assert profile.baseline_risk == 0.5
        assert len(profile.feedback_history) == 0
    
    def test_feedback_update(self, sample_feedback):
        """Test profile update with feedback."""
        profile = UserAdaptiveProfile(user_id="test_user")
        
        # Add false positive feedback
        profile.update_feedback(sample_feedback)
        
        assert profile.false_positive_count == 1
        assert len(profile.feedback_history) == 1
        assert profile.feedback_history[0] == sample_feedback
    
    def test_risk_history_update(self):
        """Test risk score history update."""
        profile = UserAdaptiveProfile(user_id="test_user")
        
        # Add risk scores
        risk_scores = [0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.2, 0.3, 0.4, 0.5]
        for score in risk_scores:
            profile.update_risk_history(score)
        
        assert len(profile.risk_score_history) == len(risk_scores)
        assert profile.baseline_risk != 0.5  # Should be updated
    
    def test_performance_metrics_calculation(self):
        """Test performance metrics calculation."""
        profile = UserAdaptiveProfile(user_id="test_user")
        
        # Add various feedback types
        feedbacks = [
            AuthFeedback("test_user", "req1", datetime.now(), 0.8, "block", is_correct=True),
            AuthFeedback("test_user", "req2", datetime.now(), 0.3, "allow", is_correct=True),
            AuthFeedback("test_user", "req3", datetime.now(), 0.9, "block", is_false_positive=True),
            AuthFeedback("test_user", "req4", datetime.now(), 0.2, "allow", is_false_negative=True),
        ]
        
        for feedback in feedbacks:
            profile.update_feedback(feedback)
        
        profile.calculate_performance_metrics()
        
        assert 0.0 <= profile.accuracy <= 1.0
        assert 0.0 <= profile.precision <= 1.0
        assert 0.0 <= profile.recall <= 1.0
        assert 0.0 <= profile.f1_score <= 1.0
    
    def test_profile_serialization(self):
        """Test profile serialization and deserialization."""
        profile = UserAdaptiveProfile(user_id="test_user")
        profile.typical_login_hours = [9, 10, 11, 14, 15]
        profile.typical_locations = ["US:San Francisco", "US:New York"]
        
        # Test to_dict
        profile_dict = profile.to_dict()
        assert isinstance(profile_dict['created_at'], str)
        assert profile_dict['user_id'] == "test_user"
        
        # Test from_dict
        restored_profile = UserAdaptiveProfile.from_dict(profile_dict)
        assert restored_profile.user_id == profile.user_id
        assert restored_profile.typical_login_hours == profile.typical_login_hours


class TestLearningConfig:
    """Test LearningConfig data model."""
    
    def test_config_creation(self, learning_config):
        """Test learning config creation."""
        assert learning_config.learning_rate == 0.05
        assert learning_config.threshold_adjustment_step == 0.1
        assert learning_config.feedback_confidence_threshold == 0.8
    
    def test_config_serialization(self, learning_config):
        """Test config serialization."""
        # Test to_dict
        config_dict = learning_config.to_dict()
        assert isinstance(config_dict['time_adjustment_window'], float)
        
        # Test from_dict
        restored_config = LearningConfig.from_dict(config_dict)
        assert restored_config.learning_rate == learning_config.learning_rate
        assert isinstance(restored_config.time_adjustment_window, timedelta)


class TestAdaptiveLearningEngine:
    """Test AdaptiveLearningEngine functionality."""
    
    @pytest.mark.asyncio
    async def test_engine_initialization(self, adaptive_learning_engine):
        """Test engine initialization."""
        success = await adaptive_learning_engine.initialize()
        assert success is True
        assert adaptive_learning_engine.global_metrics['total_feedback_processed'] == 0
    
    @pytest.mark.asyncio
    async def test_health_check(self, adaptive_learning_engine):
        """Test health check functionality."""
        await adaptive_learning_engine.initialize()
        
        health_status = await adaptive_learning_engine.health_check()
        assert health_status.status in [ServiceStatus.HEALTHY, ServiceStatus.DEGRADED]
    
    @pytest.mark.asyncio
    async def test_feedback_processing(self, adaptive_learning_engine, sample_feedback):
        """Test feedback processing."""
        await adaptive_learning_engine.initialize()
        
        # Process feedback
        await adaptive_learning_engine.process_feedback(sample_feedback)
        
        # Check that feedback was processed
        assert adaptive_learning_engine.global_metrics['total_feedback_processed'] == 1
        
        # Check user profile was updated
        assert sample_feedback.user_id in adaptive_learning_engine.user_profiles
        profile = adaptive_learning_engine.user_profiles[sample_feedback.user_id]
        assert profile.false_positive_count == 1
    
    @pytest.mark.asyncio
    async def test_adaptive_thresholds(self, adaptive_learning_engine, sample_feedback):
        """Test adaptive threshold retrieval."""
        await adaptive_learning_engine.initialize()
        
        # Get default thresholds
        thresholds = await adaptive_learning_engine.get_adaptive_thresholds("new_user")
        assert thresholds.low_risk_threshold == 0.3
        
        # Process feedback to create user-specific thresholds
        await adaptive_learning_engine.process_feedback(sample_feedback)
        
        # Get user-specific thresholds
        user_thresholds = await adaptive_learning_engine.get_adaptive_thresholds(sample_feedback.user_id)
        # Should be adjusted due to false positive
        assert user_thresholds.low_risk_threshold > 0.3
    
    @pytest.mark.asyncio
    async def test_behavioral_model_update(self, adaptive_learning_engine, sample_auth_context):
        """Test behavioral model update."""
        await adaptive_learning_engine.initialize()
        
        # Update behavioral model
        await adaptive_learning_engine.update_user_behavioral_model(
            "test_user", sample_auth_context, success=True
        )
        
        # Check profile was created and updated
        assert "test_user" in adaptive_learning_engine.user_profiles
        profile = adaptive_learning_engine.user_profiles["test_user"]
        
        # Check behavioral patterns were recorded
        login_hour = sample_auth_context.timestamp.hour
        assert login_hour in profile.typical_login_hours
        
        if sample_auth_context.geolocation:
            location_key = f"{sample_auth_context.geolocation.country}:{sample_auth_context.geolocation.city}"
            assert location_key in profile.typical_locations
    
    @pytest.mark.asyncio
    async def test_model_versioning(self, adaptive_learning_engine):
        """Test model version creation and management."""
        await adaptive_learning_engine.initialize()
        
        # Create model version
        model_data = {"threshold": 0.5, "weights": [0.1, 0.2, 0.3]}
        performance_metrics = {"accuracy": 0.85, "f1_score": 0.80}
        
        version_id = await adaptive_learning_engine.create_model_version(
            "test_model", model_data, performance_metrics
        )
        
        assert version_id != ""
        assert "test_model" in adaptive_learning_engine.model_versions
        assert "test_model" in adaptive_learning_engine.active_models
        
        # Check version was stored correctly
        versions = adaptive_learning_engine.model_versions["test_model"]
        assert len(versions) == 1
        assert versions[0].version_id == version_id
        assert versions[0].is_active is True
    
    @pytest.mark.asyncio
    async def test_model_rollback(self, adaptive_learning_engine):
        """Test model rollback functionality."""
        await adaptive_learning_engine.initialize()
        
        # Create two model versions
        model_data_v1 = {"threshold": 0.5}
        model_data_v2 = {"threshold": 0.7}
        
        version_id_v1 = await adaptive_learning_engine.create_model_version(
            "test_model", model_data_v1, {"f1_score": 0.85}
        )
        version_id_v2 = await adaptive_learning_engine.create_model_version(
            "test_model", model_data_v2, {"f1_score": 0.90}
        )
        
        # Rollback to v1
        success = await adaptive_learning_engine.rollback_model(
            "test_model", version_id_v1, "test_rollback"
        )
        
        assert success is True
        assert adaptive_learning_engine.active_models["test_model"].version_id == version_id_v1
        assert adaptive_learning_engine.global_metrics['model_rollbacks'] == 1
    
    @pytest.mark.asyncio
    async def test_performance_metrics(self, adaptive_learning_engine, sample_feedback):
        """Test performance metrics retrieval."""
        await adaptive_learning_engine.initialize()
        
        # Process some feedback
        await adaptive_learning_engine.process_feedback(sample_feedback)
        
        # Create a model version
        await adaptive_learning_engine.create_model_version(
            "test_model", {"threshold": 0.5}, {"accuracy": 0.85}
        )
        
        # Get performance metrics
        metrics = await adaptive_learning_engine.get_model_performance_metrics()
        
        assert 'global_metrics' in metrics
        assert 'user_metrics' in metrics
        assert 'model_versions' in metrics
        assert 'learning_config' in metrics
        
        assert metrics['global_metrics']['total_feedback_processed'] == 1
        assert sample_feedback.user_id in metrics['user_metrics']
        assert 'test_model' in metrics['model_versions']
    
    @pytest.mark.asyncio
    async def test_threshold_adjustment_false_positive(self, adaptive_learning_engine):
        """Test threshold adjustment for false positive feedback."""
        await adaptive_learning_engine.initialize()
        
        # Create false positive feedback
        feedback = AuthFeedback(
            user_id="test_user",
            request_id="test_request",
            timestamp=datetime.now(),
            original_risk_score=0.6,
            original_decision="block",
            is_false_positive=True,
            confidence=0.9
        )
        
        # Process feedback
        await adaptive_learning_engine.process_feedback(feedback)
        
        # Get adjusted thresholds
        thresholds = await adaptive_learning_engine.get_adaptive_thresholds("test_user")
        
        # Thresholds should be increased (less sensitive)
        assert thresholds.low_risk_threshold > 0.3
        assert thresholds.medium_risk_threshold > 0.6
        assert thresholds.high_risk_threshold > 0.8
    
    @pytest.mark.asyncio
    async def test_threshold_adjustment_false_negative(self, adaptive_learning_engine):
        """Test threshold adjustment for false negative feedback."""
        await adaptive_learning_engine.initialize()
        
        # Create false negative feedback
        feedback = AuthFeedback(
            user_id="test_user",
            request_id="test_request",
            timestamp=datetime.now(),
            original_risk_score=0.4,
            original_decision="allow",
            is_false_negative=True,
            confidence=0.9
        )
        
        # Process feedback
        await adaptive_learning_engine.process_feedback(feedback)
        
        # Get adjusted thresholds
        thresholds = await adaptive_learning_engine.get_adaptive_thresholds("test_user")
        
        # Thresholds should be decreased (more sensitive)
        assert thresholds.low_risk_threshold < 0.3
        assert thresholds.medium_risk_threshold < 0.6
        assert thresholds.high_risk_threshold < 0.8
    
    @pytest.mark.asyncio
    async def test_feedback_validation(self, adaptive_learning_engine):
        """Test feedback validation."""
        await adaptive_learning_engine.initialize()
        
        # Valid feedback
        valid_feedback = AuthFeedback(
            user_id="test_user",
            request_id="test_request",
            timestamp=datetime.now(),
            original_risk_score=0.5,
            original_decision="allow",
            confidence=0.8
        )
        
        assert adaptive_learning_engine._validate_feedback(valid_feedback) is True
        
        # Invalid feedback (missing user_id)
        invalid_feedback = AuthFeedback(
            user_id="",
            request_id="test_request",
            timestamp=datetime.now(),
            original_risk_score=0.5,
            original_decision="allow",
            confidence=0.8
        )
        
        assert adaptive_learning_engine._validate_feedback(invalid_feedback) is False
    
    @pytest.mark.asyncio
    async def test_storage_persistence(self, adaptive_learning_engine, sample_feedback):
        """Test storage and loading of user profiles and model versions."""
        await adaptive_learning_engine.initialize()
        
        # Process feedback and create model version
        await adaptive_learning_engine.process_feedback(sample_feedback)
        await adaptive_learning_engine.create_model_version(
            "test_model", {"threshold": 0.5}, {"accuracy": 0.85}
        )
        
        # Save data
        await adaptive_learning_engine._save_user_profiles()
        await adaptive_learning_engine._save_model_versions()
        
        # Create new engine and load data
        new_engine = AdaptiveLearningEngine(
            adaptive_learning_engine.config,
            adaptive_learning_engine.learning_config
        )
        new_engine.storage_path = adaptive_learning_engine.storage_path
        
        await new_engine._load_user_profiles()
        await new_engine._load_model_versions()
        
        # Verify data was loaded correctly
        assert sample_feedback.user_id in new_engine.user_profiles
        assert "test_model" in new_engine.model_versions
        assert "test_model" in new_engine.active_models
    
    @pytest.mark.asyncio
    async def test_concurrent_feedback_processing(self, adaptive_learning_engine):
        """Test concurrent feedback processing."""
        await adaptive_learning_engine.initialize()
        
        # Create multiple feedback items
        feedbacks = []
        for i in range(10):
            feedback = AuthFeedback(
                user_id=f"user_{i}",
                request_id=f"request_{i}",
                timestamp=datetime.now(),
                original_risk_score=0.5 + (i * 0.05),
                original_decision="allow",
                confidence=0.9
            )
            feedbacks.append(feedback)
        
        # Process feedback concurrently
        tasks = [adaptive_learning_engine.process_feedback(f) for f in feedbacks]
        await asyncio.gather(*tasks)
        
        # Verify all feedback was processed
        assert adaptive_learning_engine.global_metrics['total_feedback_processed'] == 10
        assert len(adaptive_learning_engine.user_profiles) == 10
    
    @pytest.mark.asyncio
    async def test_shutdown_cleanup(self, adaptive_learning_engine, sample_feedback):
        """Test proper cleanup during shutdown."""
        await adaptive_learning_engine.initialize()
        
        # Add some data
        await adaptive_learning_engine.process_feedback(sample_feedback)
        await adaptive_learning_engine.create_model_version(
            "test_model", {"threshold": 0.5}
        )
        
        # Shutdown
        await adaptive_learning_engine.shutdown()
        
        # Verify cleanup (caches should be cleared)
        assert len(adaptive_learning_engine.adaptation_cache) == 0


if __name__ == "__main__":
    pytest.main([__file__])