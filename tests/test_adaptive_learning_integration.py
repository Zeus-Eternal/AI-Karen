"""
Integration tests for adaptive learning engine with anomaly detector.

Tests the integration between the AdaptiveLearningEngine and AnomalyDetector
to ensure they work together correctly for continuous model improvement.
"""

import pytest
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

from ai_karen_engine.security.adaptive_learning import (
    AdaptiveLearningEngine,
    AuthFeedback,
    LearningConfig
)
from ai_karen_engine.security.anomaly_detector import AnomalyDetector
from ai_karen_engine.security.models import (
    AuthContext,
    IntelligentAuthConfig,
    RiskThresholds,
    GeoLocation,
    NLPFeatures,
    CredentialFeatures,
    EmbeddingAnalysis
)


@pytest.fixture
def learning_config():
    """Create test learning configuration."""
    return LearningConfig(
        learning_rate=0.1,
        adaptation_window=20,
        min_samples_for_adaptation=3,
        threshold_adjustment_step=0.1,
        feedback_confidence_threshold=0.7
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
        cache_size=100,
        cache_ttl=300
    )


@pytest.fixture
def anomaly_detector_with_learning(intelligent_auth_config, learning_config):
    """Create anomaly detector with adaptive learning."""
    with tempfile.TemporaryDirectory() as temp_dir:
        detector = AnomalyDetector(intelligent_auth_config, learning_config)
        detector.adaptive_learning_engine.storage_path = Path(temp_dir) / "adaptive_learning"
        detector.adaptive_learning_engine.storage_path.mkdir(parents=True, exist_ok=True)
        return detector


@pytest.fixture
def sample_auth_context():
    """Create sample authentication context."""
    return AuthContext(
        email="test@example.com",
        password_hash="hashed_password_123",
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
def sample_nlp_features():
    """Create sample NLP features."""
    return NLPFeatures(
        email_features=CredentialFeatures(
            token_count=2,
            unique_token_ratio=1.0,
            entropy_score=3.5,
            language="en",
            contains_suspicious_patterns=False,
            pattern_types=[]
        ),
        password_features=CredentialFeatures(
            token_count=1,
            unique_token_ratio=1.0,
            entropy_score=4.2,
            language="en",
            contains_suspicious_patterns=False,
            pattern_types=[]
        ),
        credential_similarity=0.2,
        language_consistency=True,
        suspicious_patterns=[],
        processing_time=0.05,
        used_fallback=False,
        model_version="spacy_v1.0"
    )


@pytest.fixture
def sample_embedding_analysis():
    """Create sample embedding analysis."""
    return EmbeddingAnalysis(
        embedding_vector=[0.1, 0.2, 0.3, 0.4, 0.5],
        similarity_to_user_profile=0.8,
        similarity_to_attack_patterns=0.1,
        cluster_assignment="normal_cluster",
        outlier_score=0.1,
        processing_time=0.03,
        model_version="distilbert_v1.0"
    )


class TestAdaptiveLearningIntegration:
    """Test integration between adaptive learning engine and anomaly detector."""
    
    @pytest.mark.asyncio
    async def test_anomaly_detector_initialization_with_learning(self, anomaly_detector_with_learning):
        """Test that anomaly detector initializes correctly with adaptive learning."""
        success = await anomaly_detector_with_learning.initialize()
        assert success is True
        
        # Check that adaptive learning engine is initialized
        assert anomaly_detector_with_learning.adaptive_learning_engine is not None
        
        # Check health status
        health_status = await anomaly_detector_with_learning.health_check()
        assert health_status.status.value in ['healthy', 'degraded']
    
    @pytest.mark.asyncio
    async def test_feedback_processing_integration(
        self, 
        anomaly_detector_with_learning, 
        sample_auth_context,
        sample_nlp_features,
        sample_embedding_analysis
    ):
        """Test feedback processing through both systems."""
        await anomaly_detector_with_learning.initialize()
        
        # First, perform anomaly detection
        behavioral_analysis = await anomaly_detector_with_learning.detect_anomalies(
            sample_auth_context, sample_nlp_features, sample_embedding_analysis
        )
        
        # Calculate risk score
        risk_score = await anomaly_detector_with_learning.calculate_risk_score(
            sample_auth_context, sample_nlp_features, sample_embedding_analysis, behavioral_analysis
        )
        
        # Create feedback indicating false positive
        feedback = {
            'type': 'false_positive',
            'false_positive': True,
            'false_negative': False,
            'original_risk_score': risk_score,
            'original_decision': 'block' if risk_score > 0.8 else 'allow',
            'confidence': 0.9,
            'feedback_source': 'admin'
        }
        
        # Process feedback
        await anomaly_detector_with_learning.learn_from_feedback(
            sample_auth_context.email, sample_auth_context, feedback
        )
        
        # Check that adaptive learning engine processed the feedback
        learning_engine = anomaly_detector_with_learning.adaptive_learning_engine
        assert learning_engine.global_metrics['total_feedback_processed'] == 1
        
        # Check that user profile was created
        assert sample_auth_context.email in learning_engine.user_profiles
        profile = learning_engine.user_profiles[sample_auth_context.email]
        assert profile.false_positive_count == 1
    
    @pytest.mark.asyncio
    async def test_adaptive_threshold_adjustment(
        self, 
        anomaly_detector_with_learning, 
        sample_auth_context,
        sample_nlp_features,
        sample_embedding_analysis
    ):
        """Test that thresholds are adjusted based on feedback."""
        await anomaly_detector_with_learning.initialize()
        
        learning_engine = anomaly_detector_with_learning.adaptive_learning_engine
        
        # Get initial thresholds
        initial_thresholds = await learning_engine.get_adaptive_thresholds(sample_auth_context.email)
        initial_high_threshold = initial_thresholds.high_risk_threshold
        
        # Create false positive feedback
        feedback = {
            'type': 'false_positive',
            'false_positive': True,
            'original_risk_score': 0.85,
            'original_decision': 'block',
            'confidence': 0.9
        }
        
        # Process feedback
        await anomaly_detector_with_learning.learn_from_feedback(
            sample_auth_context.email, sample_auth_context, feedback
        )
        
        # Get adjusted thresholds
        adjusted_thresholds = await learning_engine.get_adaptive_thresholds(sample_auth_context.email)
        adjusted_high_threshold = adjusted_thresholds.high_risk_threshold
        
        # Threshold should be increased (less sensitive) due to false positive
        assert adjusted_high_threshold > initial_high_threshold
    
    @pytest.mark.asyncio
    async def test_behavioral_model_update_integration(
        self, 
        anomaly_detector_with_learning, 
        sample_auth_context
    ):
        """Test behavioral model updates through the integration."""
        await anomaly_detector_with_learning.initialize()
        
        learning_engine = anomaly_detector_with_learning.adaptive_learning_engine
        
        # Create feedback for successful login
        feedback = {
            'type': 'correct_prediction',
            'is_correct': True,
            'original_risk_score': 0.3,
            'original_decision': 'allow',
            'confidence': 0.8
        }
        
        # Process feedback
        await anomaly_detector_with_learning.learn_from_feedback(
            sample_auth_context.email, sample_auth_context, feedback
        )
        
        # Check that behavioral model was updated
        assert sample_auth_context.email in learning_engine.user_profiles
        profile = learning_engine.user_profiles[sample_auth_context.email]
        
        # Check that behavioral patterns were recorded
        login_hour = sample_auth_context.timestamp.hour
        assert login_hour in profile.typical_login_hours
        
        if sample_auth_context.geolocation:
            location_key = f"{sample_auth_context.geolocation.country}:{sample_auth_context.geolocation.city}"
            assert location_key in profile.typical_locations
    
    @pytest.mark.asyncio
    async def test_model_versioning_integration(self, anomaly_detector_with_learning):
        """Test model versioning through the integration."""
        await anomaly_detector_with_learning.initialize()
        
        learning_engine = anomaly_detector_with_learning.adaptive_learning_engine
        
        # Create a model version
        model_data = {"risk_weights": anomaly_detector_with_learning.risk_weights}
        performance_metrics = {"accuracy": 0.85, "f1_score": 0.80}
        
        version_id = await learning_engine.create_model_version(
            "risk_weights", model_data, performance_metrics
        )
        
        assert version_id != ""
        assert "risk_weights" in learning_engine.model_versions
        assert "risk_weights" in learning_engine.active_models
    
    @pytest.mark.asyncio
    async def test_performance_metrics_integration(
        self, 
        anomaly_detector_with_learning, 
        sample_auth_context
    ):
        """Test performance metrics collection through integration."""
        await anomaly_detector_with_learning.initialize()
        
        learning_engine = anomaly_detector_with_learning.adaptive_learning_engine
        
        # Process multiple feedback items
        feedbacks = [
            {'type': 'correct', 'is_correct': True, 'original_risk_score': 0.2, 'original_decision': 'allow'},
            {'type': 'false_positive', 'false_positive': True, 'original_risk_score': 0.9, 'original_decision': 'block'},
            {'type': 'false_negative', 'false_negative': True, 'original_risk_score': 0.3, 'original_decision': 'allow'},
        ]
        
        for i, feedback in enumerate(feedbacks):
            feedback['confidence'] = 0.9
            context = AuthContext(
                email=f"user_{i}@example.com",
                password_hash="hash",
                client_ip="192.168.1.1",
                user_agent="Mozilla/5.0",
                timestamp=datetime.now(),
                request_id=f"req_{i}"
            )
            
            await anomaly_detector_with_learning.learn_from_feedback(
                context.email, context, feedback
            )
        
        # Get performance metrics
        metrics = await learning_engine.get_model_performance_metrics()
        
        assert 'global_metrics' in metrics
        assert 'user_metrics' in metrics
        assert metrics['global_metrics']['total_feedback_processed'] == 3
        assert metrics['global_metrics']['false_positives_reduced'] == 1
        assert metrics['global_metrics']['false_negatives_reduced'] == 1
    
    @pytest.mark.asyncio
    async def test_shutdown_integration(self, anomaly_detector_with_learning):
        """Test proper shutdown of integrated systems."""
        await anomaly_detector_with_learning.initialize()
        
        # Add some data
        learning_engine = anomaly_detector_with_learning.adaptive_learning_engine
        await learning_engine.create_model_version("test_model", {"data": "test"})
        
        # Shutdown
        await anomaly_detector_with_learning.shutdown()
        
        # Verify cleanup
        assert len(learning_engine.adaptation_cache) == 0
    
    @pytest.mark.asyncio
    async def test_concurrent_feedback_processing_integration(
        self, 
        anomaly_detector_with_learning
    ):
        """Test concurrent feedback processing through integration."""
        await anomaly_detector_with_learning.initialize()
        
        import asyncio
        
        # Create multiple concurrent feedback processing tasks
        tasks = []
        for i in range(5):
            context = AuthContext(
                email=f"concurrent_user_{i}@example.com",
                password_hash="hash",
                client_ip=f"192.168.1.{i+1}",
                user_agent="Mozilla/5.0",
                timestamp=datetime.now(),
                request_id=f"concurrent_req_{i}"
            )
            
            feedback = {
                'type': 'correct',
                'is_correct': True,
                'original_risk_score': 0.3,
                'original_decision': 'allow',
                'confidence': 0.8
            }
            
            task = anomaly_detector_with_learning.learn_from_feedback(
                context.email, context, feedback
            )
            tasks.append(task)
        
        # Execute all tasks concurrently
        await asyncio.gather(*tasks)
        
        # Verify all feedback was processed
        learning_engine = anomaly_detector_with_learning.adaptive_learning_engine
        assert learning_engine.global_metrics['total_feedback_processed'] == 5
        assert len(learning_engine.user_profiles) == 5


if __name__ == "__main__":
    pytest.main([__file__])