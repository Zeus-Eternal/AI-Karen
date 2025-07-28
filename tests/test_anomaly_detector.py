"""
Unit tests for the anomaly detection service.

This module tests the comprehensive anomaly detection functionality including
multi-dimensional risk scoring, adaptive thresholds, and feedback learning.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

from ai_karen_engine.security.anomaly_detector import (
    AnomalyDetector,
    RiskFactors,
    UserRiskProfile
)
from ai_karen_engine.security.models import (
    AuthContext,
    NLPFeatures,
    EmbeddingAnalysis,
    BehavioralAnalysis,
    CredentialFeatures,
    IntelligentAuthConfig,
    RiskThresholds,
    RiskLevel,
    GeoLocation
)


@pytest.fixture
def config():
    """Create test configuration."""
    return IntelligentAuthConfig(
        enable_nlp_analysis=True,
        enable_embedding_analysis=True,
        enable_behavioral_analysis=True,
        cache_size=100,
        cache_ttl=300
    )


@pytest.fixture
def anomaly_detector(config):
    """Create anomaly detector instance."""
    return AnomalyDetector(config)


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
    email_features = CredentialFeatures(
        token_count=2,
        unique_token_ratio=1.0,
        entropy_score=3.5,
        language="en",
        contains_suspicious_patterns=False,
        pattern_types=[]
    )
    
    password_features = CredentialFeatures(
        token_count=1,
        unique_token_ratio=1.0,
        entropy_score=4.2,
        language="unknown",
        contains_suspicious_patterns=False,
        pattern_types=[]
    )
    
    return NLPFeatures(
        email_features=email_features,
        password_features=password_features,
        credential_similarity=0.2,
        language_consistency=True,
        suspicious_patterns=[],
        processing_time=0.1,
        used_fallback=False,
        model_version="test_model"
    )


@pytest.fixture
def sample_embedding_analysis():
    """Create sample embedding analysis."""
    return EmbeddingAnalysis(
        embedding_vector=[0.1] * 768,
        similarity_to_user_profile=0.8,
        similarity_to_attack_patterns=0.1,
        cluster_assignment="cluster_1",
        outlier_score=0.2,
        processing_time=0.05,
        model_version="distilbert"
    )


class TestAnomalyDetector:
    """Test cases for AnomalyDetector class."""
    
    @pytest.mark.asyncio
    async def test_initialization(self, config):
        """Test anomaly detector initialization."""
        detector = AnomalyDetector(config)
        
        assert detector.config == config
        assert detector.model_version == "anomaly_detector_v1.0"
        assert len(detector.user_risk_profiles) == 0
        assert detector._detection_count == 0
        
        # Test initialization
        result = await detector.initialize()
        assert result is True
    
    @pytest.mark.asyncio
    async def test_health_check(self, anomaly_detector):
        """Test health check functionality."""
        await anomaly_detector.initialize()
        
        health_status = await anomaly_detector.health_check()
        
        assert health_status.service_name == "AnomalyDetector"
        # Import ServiceStatus from the base module
        from ai_karen_engine.security.intelligent_auth_base import ServiceStatus
        assert health_status.status in [
            ServiceStatus.HEALTHY,
            ServiceStatus.DEGRADED
        ]
        assert health_status.response_time > 0
    
    @pytest.mark.asyncio
    async def test_detect_anomalies_normal_case(
        self,
        anomaly_detector,
        sample_auth_context,
        sample_nlp_features,
        sample_embedding_analysis
    ):
        """Test anomaly detection for normal authentication attempt."""
        await anomaly_detector.initialize()
        
        result = await anomaly_detector.detect_anomalies(
            sample_auth_context,
            sample_nlp_features,
            sample_embedding_analysis
        )
        
        assert isinstance(result, BehavioralAnalysis)
        assert result.is_usual_time is not None
        assert result.is_usual_location is not None
        assert result.is_known_device is not None
        assert 0.0 <= result.time_deviation_score <= 1.0
        assert 0.0 <= result.location_deviation_score <= 1.0
        assert 0.0 <= result.device_similarity_score <= 1.0
        assert 0.0 <= result.login_frequency_anomaly <= 1.0
        assert 0.0 <= result.success_rate_last_30_days <= 1.0
        assert isinstance(result.failed_attempts_pattern, dict)
    
    @pytest.mark.asyncio
    async def test_detect_anomalies_high_risk_case(
        self,
        anomaly_detector,
        sample_auth_context,
        sample_nlp_features,
        sample_embedding_analysis
    ):
        """Test anomaly detection for high-risk authentication attempt."""
        await anomaly_detector.initialize()
        
        # Modify context to be high-risk
        high_risk_context = sample_auth_context
        high_risk_context.is_tor_exit_node = True
        high_risk_context.threat_intel_score = 0.9
        high_risk_context.previous_failed_attempts = 5
        high_risk_context.timestamp = datetime.now().replace(hour=2)  # Night time
        
        # Modify NLP features to be suspicious
        suspicious_nlp = sample_nlp_features
        suspicious_nlp.suspicious_patterns = ["keyboard_walk", "repeated_chars"]
        suspicious_nlp.credential_similarity = 0.9
        
        # Modify embedding to be anomalous
        anomalous_embedding = sample_embedding_analysis
        anomalous_embedding.similarity_to_user_profile = 0.1
        anomalous_embedding.similarity_to_attack_patterns = 0.8
        anomalous_embedding.outlier_score = 0.9
        
        result = await anomaly_detector.detect_anomalies(
            high_risk_context,
            suspicious_nlp,
            anomalous_embedding
        )
        
        assert isinstance(result, BehavioralAnalysis)
        # High-risk case should show more anomalies
        assert result.time_deviation_score > 0.2  # Night time login
        assert result.device_similarity_score < 0.8  # Tor usage
        assert result.login_frequency_anomaly > 0.1  # Failed attempts
    
    @pytest.mark.asyncio
    async def test_calculate_risk_score(
        self,
        anomaly_detector,
        sample_auth_context,
        sample_nlp_features,
        sample_embedding_analysis
    ):
        """Test risk score calculation."""
        await anomaly_detector.initialize()
        
        # Create behavioral analysis
        behavioral_analysis = BehavioralAnalysis(
            is_usual_time=True,
            time_deviation_score=0.1,
            is_usual_location=True,
            location_deviation_score=0.1,
            is_known_device=True,
            device_similarity_score=0.9,
            login_frequency_anomaly=0.1,
            session_duration_anomaly=0.0,
            success_rate_last_30_days=0.95,
            failed_attempts_pattern={}
        )
        
        risk_score = await anomaly_detector.calculate_risk_score(
            sample_auth_context,
            sample_nlp_features,
            sample_embedding_analysis,
            behavioral_analysis
        )
        
        assert isinstance(risk_score, float)
        assert 0.0 <= risk_score <= 1.0
    
    @pytest.mark.asyncio
    async def test_learn_from_feedback_false_positive(self, anomaly_detector, sample_auth_context):
        """Test learning from false positive feedback."""
        await anomaly_detector.initialize()
        
        user_id = "test@example.com"
        feedback = {
            'type': 'false_positive',
            'false_positive': True,
            'false_negative': False,
            'actual_risk_score': 0.1
        }
        
        # Initial state
        assert user_id not in anomaly_detector.user_risk_profiles
        
        await anomaly_detector.learn_from_feedback(user_id, sample_auth_context, feedback)
        
        # Check that user profile was created and updated
        assert user_id in anomaly_detector.user_risk_profiles
        profile = anomaly_detector.user_risk_profiles[user_id]
        assert profile.false_positive_count == 1
        assert profile.false_negative_count == 0
        assert len(profile.risk_history) == 1
        assert profile.risk_history[0] == 0.1
    
    @pytest.mark.asyncio
    async def test_learn_from_feedback_false_negative(self, anomaly_detector, sample_auth_context):
        """Test learning from false negative feedback."""
        await anomaly_detector.initialize()
        
        user_id = "test@example.com"
        feedback = {
            'type': 'false_negative',
            'false_positive': False,
            'false_negative': True,
            'actual_risk_score': 0.9
        }
        
        await anomaly_detector.learn_from_feedback(user_id, sample_auth_context, feedback)
        
        profile = anomaly_detector.user_risk_profiles[user_id]
        assert profile.false_positive_count == 0
        assert profile.false_negative_count == 1
        assert len(profile.risk_history) == 1
        assert profile.risk_history[0] == 0.9
    
    def test_calculate_nlp_risk_normal(self, anomaly_detector, sample_nlp_features):
        """Test NLP risk calculation for normal features."""
        risk_score = anomaly_detector._calculate_nlp_risk(sample_nlp_features)
        
        assert isinstance(risk_score, float)
        assert 0.0 <= risk_score <= 1.0
        # Normal features should have low risk
        assert risk_score < 0.5
    
    def test_calculate_nlp_risk_suspicious(self, anomaly_detector, sample_nlp_features):
        """Test NLP risk calculation for suspicious features."""
        # Modify features to be suspicious
        sample_nlp_features.suspicious_patterns = ["keyboard_walk", "repeated_chars", "common_weak"]
        sample_nlp_features.credential_similarity = 0.9
        sample_nlp_features.language_consistency = False
        sample_nlp_features.email_features.entropy_score = 1.0  # Low entropy
        sample_nlp_features.password_features.contains_suspicious_patterns = True
        
        risk_score = anomaly_detector._calculate_nlp_risk(sample_nlp_features)
        
        assert isinstance(risk_score, float)
        assert 0.0 <= risk_score <= 1.0
        # Suspicious features should have higher risk
        assert risk_score > 0.5
    
    def test_calculate_embedding_risk_normal(self, anomaly_detector, sample_embedding_analysis):
        """Test embedding risk calculation for normal analysis."""
        risk_score = anomaly_detector._calculate_embedding_risk(sample_embedding_analysis)
        
        assert isinstance(risk_score, float)
        assert 0.0 <= risk_score <= 1.0
        # Normal embedding should have low risk
        assert risk_score < 0.5
    
    def test_calculate_embedding_risk_anomalous(self, anomaly_detector, sample_embedding_analysis):
        """Test embedding risk calculation for anomalous analysis."""
        # Modify embedding to be anomalous
        sample_embedding_analysis.similarity_to_user_profile = 0.1  # Low similarity
        sample_embedding_analysis.similarity_to_attack_patterns = 0.9  # High attack similarity
        sample_embedding_analysis.outlier_score = 0.9  # High outlier score
        
        risk_score = anomaly_detector._calculate_embedding_risk(sample_embedding_analysis)
        
        assert isinstance(risk_score, float)
        assert 0.0 <= risk_score <= 1.0
        # Anomalous embedding should have higher risk
        assert risk_score > 0.5
    
    def test_calculate_temporal_risk_normal(self, anomaly_detector, sample_auth_context):
        """Test temporal risk calculation for normal time."""
        # Set normal business hours
        sample_auth_context.timestamp = sample_auth_context.timestamp.replace(hour=14)  # 2 PM
        sample_auth_context.time_since_last_login = timedelta(hours=8)  # Normal interval
        
        risk_score = anomaly_detector._calculate_temporal_risk(sample_auth_context)
        
        assert isinstance(risk_score, float)
        assert 0.0 <= risk_score <= 1.0
        # Normal time should have low risk
        assert risk_score < 0.3
    
    def test_calculate_temporal_risk_unusual(self, anomaly_detector, sample_auth_context):
        """Test temporal risk calculation for unusual time."""
        # Set unusual time (night)
        sample_auth_context.timestamp = sample_auth_context.timestamp.replace(hour=2)  # 2 AM
        sample_auth_context.time_since_last_login = timedelta(seconds=30)  # Very quick
        
        risk_score = anomaly_detector._calculate_temporal_risk(sample_auth_context)
        
        assert isinstance(risk_score, float)
        assert 0.0 <= risk_score <= 1.0
        # Unusual time should have higher risk
        assert risk_score > 0.3
    
    def test_calculate_geolocation_risk_usual(self, anomaly_detector, sample_auth_context):
        """Test geolocation risk calculation for usual location."""
        risk_score = anomaly_detector._calculate_geolocation_risk(sample_auth_context)
        
        assert isinstance(risk_score, float)
        assert 0.0 <= risk_score <= 1.0
        # Usual location should have low risk
        assert risk_score < 0.3
    
    def test_calculate_geolocation_risk_unusual(self, anomaly_detector, sample_auth_context):
        """Test geolocation risk calculation for unusual location."""
        # Modify to unusual location
        sample_auth_context.geolocation.is_usual_location = False
        
        risk_score = anomaly_detector._calculate_geolocation_risk(sample_auth_context)
        
        assert isinstance(risk_score, float)
        assert 0.0 <= risk_score <= 1.0
        # Unusual location should have higher risk
        assert risk_score >= 0.5
    
    def test_calculate_device_risk_normal(self, anomaly_detector, sample_auth_context):
        """Test device risk calculation for normal device."""
        risk_score = anomaly_detector._calculate_device_risk(sample_auth_context)
        
        assert isinstance(risk_score, float)
        assert 0.0 <= risk_score <= 1.0
        # Normal device should have low risk
        assert risk_score < 0.3
    
    def test_calculate_device_risk_suspicious(self, anomaly_detector, sample_auth_context):
        """Test device risk calculation for suspicious device."""
        # Modify to suspicious device
        sample_auth_context.is_tor_exit_node = True
        sample_auth_context.is_vpn = True
        sample_auth_context.device_fingerprint = None
        sample_auth_context.user_agent = "curl/7.68.0"  # Suspicious user agent
        
        risk_score = anomaly_detector._calculate_device_risk(sample_auth_context)
        
        assert isinstance(risk_score, float)
        assert 0.0 <= risk_score <= 1.0
        # Suspicious device should have higher risk
        assert risk_score > 0.5
    
    @pytest.mark.asyncio
    async def test_calculate_frequency_risk_normal(self, anomaly_detector, sample_auth_context):
        """Test frequency risk calculation for normal frequency."""
        await anomaly_detector.initialize()
        
        risk_score = await anomaly_detector._calculate_frequency_risk(sample_auth_context)
        
        assert isinstance(risk_score, float)
        assert 0.0 <= risk_score <= 1.0
        # Normal frequency should have low risk
        assert risk_score < 0.3
    
    @pytest.mark.asyncio
    async def test_calculate_frequency_risk_high_frequency(self, anomaly_detector, sample_auth_context):
        """Test frequency risk calculation for high frequency attempts."""
        await anomaly_detector.initialize()
        
        # Add many recent attempts
        for i in range(15):
            anomaly_detector.recent_attempts.append({
                'context': sample_auth_context,
                'timestamp': datetime.now(),
                'email': sample_auth_context.email,
                'ip': sample_auth_context.client_ip
            })
        
        # Set high failed attempts
        sample_auth_context.previous_failed_attempts = 8
        
        risk_score = await anomaly_detector._calculate_frequency_risk(sample_auth_context)
        
        assert isinstance(risk_score, float)
        assert 0.0 <= risk_score <= 1.0
        # High frequency should have higher risk
        assert risk_score > 0.5
    
    def test_calculate_overall_risk_score(self, anomaly_detector):
        """Test overall risk score calculation."""
        risk_factors = RiskFactors(
            nlp_risk=0.3,
            embedding_risk=0.4,
            behavioral_risk=0.2,
            temporal_risk=0.1,
            geolocation_risk=0.2,
            device_risk=0.1,
            threat_intel_risk=0.3,
            frequency_risk=0.2
        )
        
        overall_score = anomaly_detector._calculate_overall_risk_score(risk_factors)
        
        assert isinstance(overall_score, float)
        assert 0.0 <= overall_score <= 1.0
        # Should be weighted combination
        assert 0.2 < overall_score < 0.4
    
    def test_calculate_overall_risk_score_high_frequency(self, anomaly_detector):
        """Test overall risk score with high frequency multiplier."""
        risk_factors = RiskFactors(
            nlp_risk=0.3,
            embedding_risk=0.4,
            behavioral_risk=0.2,
            temporal_risk=0.1,
            geolocation_risk=0.2,
            device_risk=0.1,
            threat_intel_risk=0.3,
            frequency_risk=0.8  # High frequency
        )
        
        overall_score = anomaly_detector._calculate_overall_risk_score(risk_factors)
        
        assert isinstance(overall_score, float)
        assert 0.0 <= overall_score <= 1.0
        # High frequency should increase score
        assert overall_score > 0.3
    
    def test_determine_risk_level(self, anomaly_detector):
        """Test risk level determination."""
        # Test different risk scores based on default thresholds (0.3, 0.6, 0.8, 0.95)
        # The logic is: score >= critical_threshold -> CRITICAL, score >= high_threshold -> HIGH, etc.
        assert anomaly_detector._determine_risk_level("test@example.com", 0.1) == RiskLevel.LOW
        assert anomaly_detector._determine_risk_level("test@example.com", 0.7) == RiskLevel.MEDIUM  # >= 0.6 but < 0.8
        assert anomaly_detector._determine_risk_level("test@example.com", 0.85) == RiskLevel.HIGH   # >= 0.8 but < 0.95
        assert anomaly_detector._determine_risk_level("test@example.com", 0.95) == RiskLevel.CRITICAL
    
    def test_calculate_confidence_score(self, anomaly_detector):
        """Test confidence score calculation."""
        # Test with multiple significant factors
        risk_factors = RiskFactors(
            nlp_risk=0.5,
            embedding_risk=0.4,
            behavioral_risk=0.3,
            temporal_risk=0.2,
            geolocation_risk=0.1,
            device_risk=0.0,
            threat_intel_risk=0.0,
            frequency_risk=0.0
        )
        
        confidence = anomaly_detector._calculate_confidence_score(risk_factors)
        
        assert isinstance(confidence, float)
        assert 0.1 <= confidence <= 1.0
        # Multiple factors should give reasonable confidence
        assert confidence > 0.3
    
    def test_is_unusual_user_agent(self, anomaly_detector):
        """Test unusual user agent detection."""
        # Normal user agents
        assert not anomaly_detector._is_unusual_user_agent(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        
        # Suspicious user agents
        assert anomaly_detector._is_unusual_user_agent("curl/7.68.0")
        assert anomaly_detector._is_unusual_user_agent("python-requests/2.25.1")
        assert anomaly_detector._is_unusual_user_agent("Bot/1.0")
        assert anomaly_detector._is_unusual_user_agent("automated-script")
    
    @pytest.mark.asyncio
    async def test_user_risk_profile_creation(self, anomaly_detector, sample_auth_context):
        """Test user risk profile creation and updates."""
        await anomaly_detector.initialize()
        
        user_email = "test@example.com"
        risk_score = 0.4
        
        # Initially no profile
        assert user_email not in anomaly_detector.user_risk_profiles
        
        # Update profile
        await anomaly_detector._update_user_risk_profile(user_email, risk_score)
        
        # Profile should be created
        assert user_email in anomaly_detector.user_risk_profiles
        profile = anomaly_detector.user_risk_profiles[user_email]
        assert profile.user_id == user_email
        assert len(profile.risk_history) == 1
        assert profile.risk_history[0] == risk_score
    
    @pytest.mark.asyncio
    async def test_adaptive_thresholds_update(self, anomaly_detector):
        """Test adaptive thresholds update."""
        await anomaly_detector.initialize()
        
        user_email = "test@example.com"
        
        # Create profile with sufficient history
        profile = UserRiskProfile(user_id=user_email)
        profile.risk_history = [0.3, 0.4, 0.2, 0.5, 0.3, 0.4, 0.2, 0.3, 0.4, 0.3, 0.2, 0.4]
        
        anomaly_detector.user_risk_profiles[user_email] = profile
        
        # Update adaptive thresholds
        await anomaly_detector._update_adaptive_thresholds(user_email, profile)
        
        # Should have adaptive thresholds
        assert profile.adaptive_thresholds is not None
        assert profile.adaptive_thresholds.enable_adaptive_thresholds
        assert profile.adaptive_thresholds.user_specific_thresholds
    
    def test_get_metrics(self, anomaly_detector):
        """Test metrics collection."""
        metrics = anomaly_detector.get_metrics()
        
        assert isinstance(metrics, dict)
        assert 'detection_count' in metrics
        assert 'high_risk_detections' in metrics
        assert 'false_positive_feedback' in metrics
        assert 'false_negative_feedback' in metrics
        assert 'cache_hit_rate' in metrics
        assert 'avg_processing_time' in metrics
        assert 'user_profiles_count' in metrics
        assert 'recent_attempts_count' in metrics
        assert 'model_version' in metrics
        
        # Check metric types
        assert isinstance(metrics['detection_count'], int)
        assert isinstance(metrics['high_risk_detections'], int)
        assert isinstance(metrics['cache_hit_rate'], float)
        assert isinstance(metrics['avg_processing_time'], float)
        assert isinstance(metrics['model_version'], str)
    
    @pytest.mark.asyncio
    async def test_caching_functionality(
        self,
        anomaly_detector,
        sample_auth_context,
        sample_nlp_features,
        sample_embedding_analysis
    ):
        """Test risk calculation caching."""
        await anomaly_detector.initialize()
        
        behavioral_analysis = BehavioralAnalysis(
            is_usual_time=True,
            time_deviation_score=0.1,
            is_usual_location=True,
            location_deviation_score=0.1,
            is_known_device=True,
            device_similarity_score=0.9,
            login_frequency_anomaly=0.1,
            session_duration_anomaly=0.0,
            success_rate_last_30_days=0.95,
            failed_attempts_pattern={}
        )
        
        # First call should miss cache
        initial_cache_misses = anomaly_detector._cache_misses
        risk_score1 = await anomaly_detector.calculate_risk_score(
            sample_auth_context,
            sample_nlp_features,
            sample_embedding_analysis,
            behavioral_analysis
        )
        assert anomaly_detector._cache_misses == initial_cache_misses + 1
        
        # Second call with same parameters should hit cache
        initial_cache_hits = anomaly_detector._cache_hits
        risk_score2 = await anomaly_detector.calculate_risk_score(
            sample_auth_context,
            sample_nlp_features,
            sample_embedding_analysis,
            behavioral_analysis
        )
        assert anomaly_detector._cache_hits == initial_cache_hits + 1
        assert risk_score1 == risk_score2
    
    @pytest.mark.asyncio
    async def test_error_handling(self, anomaly_detector, sample_auth_context):
        """Test error handling in anomaly detection."""
        await anomaly_detector.initialize()
        
        # Test with None values
        result = await anomaly_detector.detect_anomalies(
            sample_auth_context,
            None,  # Invalid NLP features
            None   # Invalid embedding analysis
        )
        
        # Should return fallback behavioral analysis
        assert isinstance(result, BehavioralAnalysis)
        assert result.is_usual_time is not None
        assert result.is_usual_location is not None
        assert result.is_known_device is not None


class TestRiskFactors:
    """Test cases for RiskFactors dataclass."""
    
    def test_risk_factors_creation(self):
        """Test RiskFactors creation and serialization."""
        risk_factors = RiskFactors(
            nlp_risk=0.3,
            embedding_risk=0.4,
            behavioral_risk=0.2,
            temporal_risk=0.1,
            geolocation_risk=0.2,
            device_risk=0.1,
            threat_intel_risk=0.3,
            frequency_risk=0.2
        )
        
        assert risk_factors.nlp_risk == 0.3
        assert risk_factors.embedding_risk == 0.4
        assert risk_factors.behavioral_risk == 0.2
        
        # Test serialization
        risk_dict = risk_factors.to_dict()
        assert isinstance(risk_dict, dict)
        assert risk_dict['nlp_risk'] == 0.3
        assert risk_dict['embedding_risk'] == 0.4
        assert len(risk_dict) == 8


class TestUserRiskProfile:
    """Test cases for UserRiskProfile class."""
    
    def test_user_risk_profile_creation(self):
        """Test UserRiskProfile creation."""
        profile = UserRiskProfile(user_id="test@example.com")
        
        assert profile.user_id == "test@example.com"
        assert profile.baseline_risk == 0.5
        assert len(profile.risk_history) == 0
        assert profile.false_positive_count == 0
        assert profile.false_negative_count == 0
        assert profile.adaptive_thresholds is None
    
    def test_update_risk_history(self):
        """Test risk history updates."""
        profile = UserRiskProfile(user_id="test@example.com")
        
        # Add some risk scores
        for i in range(15):
            profile.update_risk_history(0.3 + i * 0.01)
        
        assert len(profile.risk_history) == 15
        assert profile.baseline_risk != 0.5  # Should be updated
        
        # Test max history limit
        for i in range(100):
            profile.update_risk_history(0.4)
        
        assert len(profile.risk_history) == 100  # Should be capped
        
        # Add one more
        profile.update_risk_history(0.5)
        assert len(profile.risk_history) == 100  # Still capped
        assert profile.risk_history[-1] == 0.5  # Latest value


if __name__ == "__main__":
    pytest.main([__file__])