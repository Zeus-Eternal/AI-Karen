"""
Unit tests for intelligent authentication data models.

Tests validation, serialization, and deserialization of all data models
used by the intelligent authentication system.
"""

import json
import pytest
from datetime import datetime, timedelta
from pathlib import Path
import tempfile

from src.ai_karen_engine.security.models import (
    AuthContext,
    AuthAnalysisResult,
    GeoLocation,
    CredentialFeatures,
    NLPFeatures,
    EmbeddingAnalysis,
    BehavioralAnalysis,
    ThreatAnalysis,
    BruteForceIndicators,
    CredentialStuffingIndicators,
    AccountTakeoverIndicators,
    SecurityAction,
    RiskLevel,
    SecurityActionType,
    RiskThresholds,
    FeatureFlags,
    FallbackConfig,
    IntelligentAuthConfig
)


class TestGeoLocation:
    """Test GeoLocation data model."""

    def test_valid_geolocation(self):
        """Test valid geolocation creation and validation."""
        geo = GeoLocation(
            country="US",
            region="CA",
            city="San Francisco",
            latitude=37.7749,
            longitude=-122.4194,
            timezone="America/Los_Angeles",
            is_usual_location=True
        )
        
        assert geo.validate()
        assert geo.country == "US"
        assert geo.is_usual_location

    def test_invalid_coordinates(self):
        """Test validation with invalid coordinates."""
        geo = GeoLocation(
            country="US",
            region="CA", 
            city="San Francisco",
            latitude=91.0,  # Invalid latitude
            longitude=-122.4194,
            timezone="America/Los_Angeles"
        )
        
        assert not geo.validate()

    def test_serialization(self):
        """Test serialization and deserialization."""
        geo = GeoLocation(
            country="US",
            region="CA",
            city="San Francisco", 
            latitude=37.7749,
            longitude=-122.4194,
            timezone="America/Los_Angeles"
        )
        
        data = geo.to_dict()
        geo_restored = GeoLocation.from_dict(data)
        
        assert geo_restored.country == geo.country
        assert geo_restored.latitude == geo.latitude
        assert geo_restored.longitude == geo.longitude


class TestAuthContext:
    """Test AuthContext data model."""

    def test_valid_auth_context(self):
        """Test valid authentication context creation."""
        now = datetime.now()
        geo = GeoLocation(
            country="US",
            region="CA",
            city="San Francisco",
            latitude=37.7749,
            longitude=-122.4194,
            timezone="America/Los_Angeles"
        )
        
        context = AuthContext(
            email="test@example.com",
            password_hash="hashed_password",
            client_ip="192.168.1.1",
            user_agent="Mozilla/5.0",
            timestamp=now,
            request_id="req_123",
            geolocation=geo,
            device_fingerprint="device_123",
            time_since_last_login=timedelta(hours=2),
            threat_intel_score=0.2,
            previous_failed_attempts=1
        )
        
        assert context.validate()
        assert context.email == "test@example.com"
        assert context.threat_intel_score == 0.2

    def test_invalid_threat_score(self):
        """Test validation with invalid threat intelligence score."""
        context = AuthContext(
            email="test@example.com",
            password_hash="hashed_password",
            client_ip="192.168.1.1",
            user_agent="Mozilla/5.0",
            timestamp=datetime.now(),
            request_id="req_123",
            threat_intel_score=1.5  # Invalid score > 1.0
        )
        
        assert not context.validate()

    def test_serialization_with_datetime(self):
        """Test serialization with datetime objects."""
        now = datetime.now()
        context = AuthContext(
            email="test@example.com",
            password_hash="hashed_password",
            client_ip="192.168.1.1",
            user_agent="Mozilla/5.0",
            timestamp=now,
            request_id="req_123",
            time_since_last_login=timedelta(hours=2)
        )
        
        data = context.to_dict()
        context_restored = AuthContext.from_dict(data)
        
        assert context_restored.email == context.email
        assert context_restored.timestamp == context.timestamp
        assert context_restored.time_since_last_login == context.time_since_last_login


class TestCredentialFeatures:
    """Test CredentialFeatures data model."""

    def test_valid_credential_features(self):
        """Test valid credential features creation."""
        features = CredentialFeatures(
            token_count=5,
            unique_token_ratio=0.8,
            entropy_score=3.2,
            language="en",
            contains_suspicious_patterns=False,
            pattern_types=["normal"]
        )
        
        assert features.validate()
        assert features.token_count == 5
        assert features.unique_token_ratio == 0.8

    def test_invalid_unique_token_ratio(self):
        """Test validation with invalid unique token ratio."""
        features = CredentialFeatures(
            token_count=5,
            unique_token_ratio=1.5,  # Invalid ratio > 1.0
            entropy_score=3.2,
            language="en",
            contains_suspicious_patterns=False
        )
        
        assert not features.validate()

    def test_serialization(self):
        """Test serialization and deserialization."""
        features = CredentialFeatures(
            token_count=5,
            unique_token_ratio=0.8,
            entropy_score=3.2,
            language="en",
            contains_suspicious_patterns=True,
            pattern_types=["repeated_chars", "keyboard_walk"]
        )
        
        data = features.to_dict()
        features_restored = CredentialFeatures.from_dict(data)
        
        assert features_restored.token_count == features.token_count
        assert features_restored.pattern_types == features.pattern_types


class TestNLPFeatures:
    """Test NLPFeatures data model."""

    def test_valid_nlp_features(self):
        """Test valid NLP features creation."""
        email_features = CredentialFeatures(
            token_count=3,
            unique_token_ratio=1.0,
            entropy_score=2.5,
            language="en",
            contains_suspicious_patterns=False
        )
        
        password_features = CredentialFeatures(
            token_count=1,
            unique_token_ratio=1.0,
            entropy_score=4.2,
            language="en",
            contains_suspicious_patterns=False
        )
        
        nlp_features = NLPFeatures(
            email_features=email_features,
            password_features=password_features,
            credential_similarity=0.3,
            language_consistency=True,
            suspicious_patterns=[],
            processing_time=0.15,
            model_version="spacy-3.4.0"
        )
        
        assert nlp_features.validate()
        assert nlp_features.credential_similarity == 0.3
        assert nlp_features.language_consistency

    def test_invalid_similarity_score(self):
        """Test validation with invalid similarity score."""
        email_features = CredentialFeatures(
            token_count=3,
            unique_token_ratio=1.0,
            entropy_score=2.5,
            language="en",
            contains_suspicious_patterns=False
        )
        
        password_features = CredentialFeatures(
            token_count=1,
            unique_token_ratio=1.0,
            entropy_score=4.2,
            language="en",
            contains_suspicious_patterns=False
        )
        
        nlp_features = NLPFeatures(
            email_features=email_features,
            password_features=password_features,
            credential_similarity=1.5,  # Invalid similarity > 1.0
            language_consistency=True
        )
        
        assert not nlp_features.validate()

    def test_serialization(self):
        """Test serialization and deserialization."""
        email_features = CredentialFeatures(
            token_count=3,
            unique_token_ratio=1.0,
            entropy_score=2.5,
            language="en",
            contains_suspicious_patterns=False
        )
        
        password_features = CredentialFeatures(
            token_count=1,
            unique_token_ratio=1.0,
            entropy_score=4.2,
            language="en",
            contains_suspicious_patterns=False
        )
        
        nlp_features = NLPFeatures(
            email_features=email_features,
            password_features=password_features,
            credential_similarity=0.3,
            language_consistency=True,
            suspicious_patterns=["pattern1"],
            processing_time=0.15
        )
        
        data = nlp_features.to_dict()
        nlp_restored = NLPFeatures.from_dict(data)
        
        assert nlp_restored.credential_similarity == nlp_features.credential_similarity
        assert nlp_restored.email_features.token_count == nlp_features.email_features.token_count
        assert nlp_restored.suspicious_patterns == nlp_features.suspicious_patterns


class TestEmbeddingAnalysis:
    """Test EmbeddingAnalysis data model."""

    def test_valid_embedding_analysis(self):
        """Test valid embedding analysis creation."""
        analysis = EmbeddingAnalysis(
            embedding_vector=[0.1, 0.2, 0.3, 0.4],
            similarity_to_user_profile=0.8,
            similarity_to_attack_patterns=0.1,
            cluster_assignment="cluster_1",
            outlier_score=0.2,
            processing_time=0.05,
            model_version="distilbert-base"
        )
        
        assert analysis.validate()
        assert len(analysis.embedding_vector) == 4
        assert analysis.similarity_to_user_profile == 0.8

    def test_empty_embedding_vector(self):
        """Test validation with empty embedding vector."""
        analysis = EmbeddingAnalysis(
            embedding_vector=[],  # Empty vector
            similarity_to_user_profile=0.8,
            similarity_to_attack_patterns=0.1
        )
        
        assert not analysis.validate()

    def test_invalid_similarity_scores(self):
        """Test validation with invalid similarity scores."""
        analysis = EmbeddingAnalysis(
            embedding_vector=[0.1, 0.2, 0.3],
            similarity_to_user_profile=1.5,  # Invalid > 1.0
            similarity_to_attack_patterns=0.1
        )
        
        assert not analysis.validate()


class TestBehavioralAnalysis:
    """Test BehavioralAnalysis data model."""

    def test_valid_behavioral_analysis(self):
        """Test valid behavioral analysis creation."""
        analysis = BehavioralAnalysis(
            is_usual_time=True,
            time_deviation_score=0.2,
            is_usual_location=True,
            location_deviation_score=0.1,
            is_known_device=True,
            device_similarity_score=0.9,
            login_frequency_anomaly=0.1,
            session_duration_anomaly=0.05,
            success_rate_last_30_days=0.95,
            failed_attempts_pattern={"recent": 2, "total": 5}
        )
        
        assert analysis.validate()
        assert analysis.is_usual_time
        assert analysis.success_rate_last_30_days == 0.95

    def test_invalid_scores(self):
        """Test validation with invalid scores."""
        analysis = BehavioralAnalysis(
            is_usual_time=True,
            time_deviation_score=1.5,  # Invalid > 1.0
            is_usual_location=True,
            location_deviation_score=0.1,
            is_known_device=True,
            device_similarity_score=0.9,
            login_frequency_anomaly=0.1,
            session_duration_anomaly=0.05,
            success_rate_last_30_days=0.95
        )
        
        assert not analysis.validate()


class TestThreatAnalysis:
    """Test ThreatAnalysis data model."""

    def test_valid_threat_analysis(self):
        """Test valid threat analysis creation."""
        analysis = ThreatAnalysis(
            ip_reputation_score=0.3,
            known_attack_patterns=["brute_force", "credential_stuffing"],
            threat_actor_indicators=["apt_group_1"],
            similar_attacks_detected=5,
            attack_campaign_correlation="campaign_123"
        )
        
        assert analysis.validate()
        assert analysis.ip_reputation_score == 0.3
        assert len(analysis.known_attack_patterns) == 2

    def test_invalid_ip_reputation_score(self):
        """Test validation with invalid IP reputation score."""
        analysis = ThreatAnalysis(
            ip_reputation_score=1.5,  # Invalid > 1.0
            similar_attacks_detected=5
        )
        
        assert not analysis.validate()

    def test_serialization_with_indicators(self):
        """Test serialization with attack indicators."""
        brute_force = BruteForceIndicators(
            rapid_attempts=True,
            multiple_ips=False,
            time_pattern_score=0.8
        )
        
        analysis = ThreatAnalysis(
            ip_reputation_score=0.3,
            brute_force_indicators=brute_force,
            similar_attacks_detected=3
        )
        
        data = analysis.to_dict()
        analysis_restored = ThreatAnalysis.from_dict(data)
        
        assert analysis_restored.ip_reputation_score == analysis.ip_reputation_score
        assert analysis_restored.brute_force_indicators.rapid_attempts == brute_force.rapid_attempts


class TestSecurityAction:
    """Test SecurityAction data model."""

    def test_valid_security_action(self):
        """Test valid security action creation."""
        action = SecurityAction(
            action_type="block",
            priority=1,
            description="Block high-risk login attempt",
            automated=True,
            requires_human_review=False
        )
        
        assert action.validate()
        assert action.action_type == "block"
        assert action.priority == 1

    def test_invalid_priority(self):
        """Test validation with invalid priority."""
        action = SecurityAction(
            action_type="block",
            priority=0,  # Invalid priority <= 0
            description="Block high-risk login attempt",
            automated=True,
            requires_human_review=False
        )
        
        assert not action.validate()


class TestAuthAnalysisResult:
    """Test AuthAnalysisResult data model."""

    def test_valid_analysis_result(self):
        """Test valid analysis result creation."""
        # Create required components
        email_features = CredentialFeatures(
            token_count=3, unique_token_ratio=1.0, entropy_score=2.5,
            language="en", contains_suspicious_patterns=False
        )
        password_features = CredentialFeatures(
            token_count=1, unique_token_ratio=1.0, entropy_score=4.2,
            language="en", contains_suspicious_patterns=False
        )
        nlp_features = NLPFeatures(
            email_features=email_features,
            password_features=password_features,
            credential_similarity=0.3,
            language_consistency=True
        )
        
        embedding_analysis = EmbeddingAnalysis(
            embedding_vector=[0.1, 0.2, 0.3],
            similarity_to_user_profile=0.8,
            similarity_to_attack_patterns=0.1
        )
        
        behavioral_analysis = BehavioralAnalysis(
            is_usual_time=True, time_deviation_score=0.2,
            is_usual_location=True, location_deviation_score=0.1,
            is_known_device=True, device_similarity_score=0.9,
            login_frequency_anomaly=0.1, session_duration_anomaly=0.05,
            success_rate_last_30_days=0.95
        )
        
        threat_analysis = ThreatAnalysis(
            ip_reputation_score=0.3,
            similar_attacks_detected=2
        )
        
        action = SecurityAction(
            action_type="allow", priority=3, description="Allow normal login",
            automated=True, requires_human_review=False
        )
        
        result = AuthAnalysisResult(
            risk_score=0.2,
            risk_level=RiskLevel.LOW,
            should_block=False,
            requires_2fa=False,
            nlp_features=nlp_features,
            embedding_analysis=embedding_analysis,
            behavioral_analysis=behavioral_analysis,
            threat_analysis=threat_analysis,
            processing_time=0.25,
            confidence_score=0.9,
            recommended_actions=[action]
        )
        
        assert result.validate()
        assert result.risk_score == 0.2
        assert result.risk_level == RiskLevel.LOW
        assert not result.should_block

    def test_invalid_risk_score(self):
        """Test validation with invalid risk score."""
        # Create minimal required components
        email_features = CredentialFeatures(
            token_count=3, unique_token_ratio=1.0, entropy_score=2.5,
            language="en", contains_suspicious_patterns=False
        )
        password_features = CredentialFeatures(
            token_count=1, unique_token_ratio=1.0, entropy_score=4.2,
            language="en", contains_suspicious_patterns=False
        )
        nlp_features = NLPFeatures(
            email_features=email_features,
            password_features=password_features,
            credential_similarity=0.3,
            language_consistency=True
        )
        
        embedding_analysis = EmbeddingAnalysis(
            embedding_vector=[0.1, 0.2, 0.3],
            similarity_to_user_profile=0.8,
            similarity_to_attack_patterns=0.1
        )
        
        behavioral_analysis = BehavioralAnalysis(
            is_usual_time=True, time_deviation_score=0.2,
            is_usual_location=True, location_deviation_score=0.1,
            is_known_device=True, device_similarity_score=0.9,
            login_frequency_anomaly=0.1, session_duration_anomaly=0.05,
            success_rate_last_30_days=0.95
        )
        
        threat_analysis = ThreatAnalysis(
            ip_reputation_score=0.3,
            similar_attacks_detected=2
        )
        
        result = AuthAnalysisResult(
            risk_score=1.5,  # Invalid risk score > 1.0
            risk_level=RiskLevel.LOW,
            should_block=False,
            requires_2fa=False,
            nlp_features=nlp_features,
            embedding_analysis=embedding_analysis,
            behavioral_analysis=behavioral_analysis,
            threat_analysis=threat_analysis,
            processing_time=0.25
        )
        
        assert not result.validate()


class TestRiskThresholds:
    """Test RiskThresholds configuration model."""

    def test_valid_risk_thresholds(self):
        """Test valid risk thresholds creation."""
        thresholds = RiskThresholds(
            low_risk_threshold=0.2,
            medium_risk_threshold=0.5,
            high_risk_threshold=0.8,
            critical_risk_threshold=0.95
        )
        
        assert thresholds.validate()
        assert thresholds.low_risk_threshold == 0.2

    def test_invalid_threshold_order(self):
        """Test validation with invalid threshold ordering."""
        thresholds = RiskThresholds(
            low_risk_threshold=0.8,  # Higher than medium
            medium_risk_threshold=0.5,
            high_risk_threshold=0.9,
            critical_risk_threshold=0.95
        )
        
        assert not thresholds.validate()


class TestIntelligentAuthConfig:
    """Test IntelligentAuthConfig configuration model."""

    def test_valid_config(self):
        """Test valid configuration creation."""
        config = IntelligentAuthConfig(
            enable_nlp_analysis=True,
            enable_embedding_analysis=True,
            max_processing_time=3.0,
            cache_size=5000,
            cache_ttl=1800,
            batch_size=16
        )
        
        assert config.validate()
        assert config.enable_nlp_analysis
        assert config.max_processing_time == 3.0

    def test_invalid_config_values(self):
        """Test validation with invalid configuration values."""
        config = IntelligentAuthConfig(
            max_processing_time=-1.0,  # Invalid negative time
            cache_size=0,  # Invalid zero cache size
            batch_size=0   # Invalid zero batch size
        )
        
        assert not config.validate()

    def test_config_serialization(self):
        """Test configuration serialization and deserialization."""
        config = IntelligentAuthConfig(
            enable_nlp_analysis=True,
            enable_embedding_analysis=False,
            max_processing_time=2.5,
            cache_size=8000
        )
        
        data = config.to_dict()
        config_restored = IntelligentAuthConfig.from_dict(data)
        
        assert config_restored.enable_nlp_analysis == config.enable_nlp_analysis
        assert config_restored.enable_embedding_analysis == config.enable_embedding_analysis
        assert config_restored.max_processing_time == config.max_processing_time
        assert config_restored.cache_size == config.cache_size

    def test_config_file_operations(self):
        """Test saving and loading configuration from file."""
        config = IntelligentAuthConfig(
            enable_nlp_analysis=True,
            max_processing_time=4.0,
            cache_size=12000
        )
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            config.save_to_file(temp_path)
            config_loaded = IntelligentAuthConfig.load_from_file(temp_path)
            
            assert config_loaded.enable_nlp_analysis == config.enable_nlp_analysis
            assert config_loaded.max_processing_time == config.max_processing_time
            assert config_loaded.cache_size == config.cache_size
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_config_from_env(self, monkeypatch):
        """Test configuration creation from environment variables."""
        monkeypatch.setenv('INTELLIGENT_AUTH_ENABLE_NLP', 'false')
        monkeypatch.setenv('INTELLIGENT_AUTH_MAX_PROCESSING_TIME', '2.0')
        monkeypatch.setenv('INTELLIGENT_AUTH_CACHE_SIZE', '15000')
        
        config = IntelligentAuthConfig.from_env()
        
        assert not config.enable_nlp_analysis
        assert config.max_processing_time == 2.0
        assert config.cache_size == 15000


class TestFeatureFlags:
    """Test FeatureFlags configuration model."""

    def test_default_feature_flags(self):
        """Test default feature flags creation."""
        flags = FeatureFlags()
        
        assert flags.enable_geolocation_analysis
        assert flags.enable_device_fingerprinting
        assert flags.enable_threat_intelligence

    def test_feature_flags_serialization(self):
        """Test feature flags serialization."""
        flags = FeatureFlags(
            enable_geolocation_analysis=False,
            enable_threat_intelligence=True
        )
        
        data = flags.to_dict()
        flags_restored = FeatureFlags.from_dict(data)
        
        assert not flags_restored.enable_geolocation_analysis
        assert flags_restored.enable_threat_intelligence


class TestFallbackConfig:
    """Test FallbackConfig configuration model."""

    def test_valid_fallback_config(self):
        """Test valid fallback configuration."""
        config = FallbackConfig(
            block_on_nlp_failure=True,
            max_processing_timeout=3.0,
            fallback_risk_score=0.5
        )
        
        assert config.validate()
        assert config.block_on_nlp_failure
        assert config.max_processing_timeout == 3.0

    def test_invalid_fallback_config(self):
        """Test invalid fallback configuration."""
        config = FallbackConfig(
            max_processing_timeout=-1.0,  # Invalid negative timeout
            fallback_risk_score=1.5  # Invalid risk score > 1.0
        )
        
        assert not config.validate()


if __name__ == "__main__":
    pytest.main([__file__])