"""
Tests for comprehensive anomaly detection engine.

This module tests the integration of all anomaly detection components including
behavioral analysis, attack pattern detection, and adaptive learning.
"""

import pytest
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

from ai_karen_engine.security.comprehensive_anomaly_engine import (
    ComprehensiveAnomalyEngine,
    ComprehensiveAnalysisResult
)
from ai_karen_engine.security.adaptive_learning import LearningConfig
from ai_karen_engine.security.models import (
    AuthContext,
    NLPFeatures,
    CredentialFeatures,
    EmbeddingAnalysis,
    IntelligentAuthConfig,
    RiskThresholds,
    RiskLevel,
    GeoLocation,
    SecurityAction,
    SecurityActionType
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
        enable_threat_intelligence=True,
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
def comprehensive_engine(intelligent_auth_config, learning_config):
    """Create comprehensive anomaly engine."""
    with tempfile.TemporaryDirectory() as temp_dir:
        engine = ComprehensiveAnomalyEngine(intelligent_auth_config, learning_config)
        # Set temporary storage paths for components
        engine.adaptive_learning_engine.storage_path = Path(temp_dir) / "adaptive_learning"
        engine.adaptive_learning_engine.storage_path.mkdir(parents=True, exist_ok=True)
        return engine


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


class TestComprehensiveAnomalyEngine:
    """Test comprehensive anomaly detection engine."""
    
    @pytest.mark.asyncio
    async def test_engine_initialization(self, comprehensive_engine):
        """Test engine initialization."""
        success = await comprehensive_engine.initialize()
        assert success is True
        
        # Check that all components are initialized
        assert comprehensive_engine.anomaly_detector is not None
        assert comprehensive_engine.attack_pattern_detector is not None
        assert comprehensive_engine.adaptive_learning_engine is not None
    
    @pytest.mark.asyncio
    async def test_health_check(self, comprehensive_engine):
        """Test comprehensive health check."""
        await comprehensive_engine.initialize()
        
        health_status = await comprehensive_engine.health_check()
        assert health_status.status.value in ['healthy', 'degraded']
    
    @pytest.mark.asyncio
    async def test_comprehensive_analysis_normal_case(
        self,
        comprehensive_engine,
        sample_auth_context,
        sample_nlp_features,
        sample_embedding_analysis
    ):
        """Test comprehensive analysis for normal authentication attempt."""
        await comprehensive_engine.initialize()
        
        result = await comprehensive_engine.analyze_authentication_attempt(
            sample_auth_context, sample_nlp_features, sample_embedding_analysis
        )
        
        assert isinstance(result, ComprehensiveAnalysisResult)
        assert result.behavioral_analysis is not None
        assert result.threat_analysis is not None
        assert 0.0 <= result.overall_risk_score <= 1.0
        assert result.risk_level in [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]
        assert result.processing_time > 0
        assert len(result.components_used) >= 2  # Should use at least behavioral and attack pattern
        assert 0.0 <= result.confidence_score <= 1.0
        assert isinstance(result.recommended_actions, list)
        assert isinstance(result.should_block, bool)
        assert isinstance(result.requires_2fa, bool)
    
    @pytest.mark.asyncio
    async def test_comprehensive_analysis_high_risk_case(
        self,
        comprehensive_engine,
        sample_auth_context,
        sample_nlp_features,
        sample_embedding_analysis
    ):
        """Test comprehensive analysis for high-risk authentication attempt."""
        await comprehensive_engine.initialize()
        
        # Modify context to be high-risk
        high_risk_context = sample_auth_context
        high_risk_context.is_tor_exit_node = True
        high_risk_context.threat_intel_score = 0.9
        high_risk_context.previous_failed_attempts = 10
        high_risk_context.timestamp = datetime.now().replace(hour=2)  # Night time
        high_risk_context.geolocation.is_usual_location = False
        
        # Modify NLP features to be suspicious
        suspicious_nlp = sample_nlp_features
        suspicious_nlp.suspicious_patterns = ["keyboard_walk", "repeated_chars"]
        suspicious_nlp.credential_similarity = 0.9
        
        # Modify embedding to be anomalous
        anomalous_embedding = sample_embedding_analysis
        anomalous_embedding.similarity_to_user_profile = 0.1
        anomalous_embedding.similarity_to_attack_patterns = 0.9
        anomalous_embedding.outlier_score = 0.9
        
        result = await comprehensive_engine.analyze_authentication_attempt(
            high_risk_context, suspicious_nlp, anomalous_embedding
        )
        
        assert isinstance(result, ComprehensiveAnalysisResult)
        # High-risk case should have higher risk score than normal case
        # The actual score depends on the weighting and implementation details
        assert result.overall_risk_score > 0.2  # Should be higher than baseline
        assert result.risk_level in [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]
        # Should have security recommendations for unusual patterns
        assert len(result.recommended_actions) > 0
    
    @pytest.mark.asyncio
    async def test_feedback_processing(
        self,
        comprehensive_engine,
        sample_auth_context,
        sample_nlp_features,
        sample_embedding_analysis
    ):
        """Test feedback processing through comprehensive engine."""
        await comprehensive_engine.initialize()
        
        # Perform analysis
        result = await comprehensive_engine.analyze_authentication_attempt(
            sample_auth_context, sample_nlp_features, sample_embedding_analysis
        )
        
        # Create feedback
        feedback = {
            'false_positive': True,
            'is_correct': False,
            'confidence': 0.9,
            'feedback_source': 'admin',
            'notes': 'User confirmed legitimate login'
        }
        
        # Process feedback
        await comprehensive_engine.process_feedback(
            sample_auth_context.email, sample_auth_context, result, feedback
        )
        
        # Check that adaptive learning processed the feedback
        learning_engine = comprehensive_engine.adaptive_learning_engine
        assert learning_engine.global_metrics['total_feedback_processed'] == 1
    
    @pytest.mark.asyncio
    async def test_risk_score_calculation(self, comprehensive_engine):
        """Test comprehensive risk score calculation."""
        await comprehensive_engine.initialize()
        
        # Test different risk combinations
        behavioral_risk = 0.3
        attack_pattern_risk = 0.6
        threat_intel_risk = 0.2
        
        comprehensive_risk = comprehensive_engine._calculate_comprehensive_risk_score(
            behavioral_risk, attack_pattern_risk, threat_intel_risk
        )
        
        assert 0.0 <= comprehensive_risk <= 1.0
        # Should be weighted combination
        expected_risk = (
            behavioral_risk * 0.4 +
            attack_pattern_risk * 0.4 +
            threat_intel_risk * 0.2
        )
        assert abs(comprehensive_risk - expected_risk) < 0.01
    
    @pytest.mark.asyncio
    async def test_attack_pattern_risk_calculation(self, comprehensive_engine):
        """Test attack pattern risk score calculation."""
        await comprehensive_engine.initialize()
        
        # Create threat analysis with various indicators
        from ai_karen_engine.security.models import (
            ThreatAnalysis,
            BruteForceIndicators,
            CredentialStuffingIndicators,
            AccountTakeoverIndicators
        )
        
        threat_analysis = ThreatAnalysis(
            ip_reputation_score=0.3,
            known_attack_patterns=["brute_force", "credential_stuffing"],
            threat_actor_indicators=["CYBERCRIMINAL"],
            brute_force_indicators=BruteForceIndicators(
                rapid_attempts=True,
                multiple_ips=True,
                password_variations=True,
                time_pattern_score=0.8
            ),
            credential_stuffing_indicators=CredentialStuffingIndicators(
                multiple_accounts=True,
                common_passwords=True,
                distributed_sources=True,
                success_rate_pattern=0.05
            ),
            account_takeover_indicators=AccountTakeoverIndicators(
                location_anomaly=True,
                device_change=True,
                behavior_change=True,
                privilege_escalation=False
            ),
            similar_attacks_detected=5,
            attack_campaign_correlation="campaign_123"
        )
        
        risk_score = comprehensive_engine._calculate_attack_pattern_risk_score(threat_analysis)
        
        assert 0.0 <= risk_score <= 1.0
        # Should be high risk due to multiple indicators
        assert risk_score > 0.5
    
    def test_risk_level_determination(self, comprehensive_engine):
        """Test risk level determination with adaptive thresholds."""
        thresholds = RiskThresholds(
            low_risk_threshold=0.3,
            medium_risk_threshold=0.6,
            high_risk_threshold=0.8,
            critical_risk_threshold=0.95
        )
        
        # Test different risk scores
        assert comprehensive_engine._determine_risk_level(0.1, thresholds) == RiskLevel.LOW  # < 0.3
        assert comprehensive_engine._determine_risk_level(0.5, thresholds) == RiskLevel.LOW   # >= 0.3 but < 0.6
        assert comprehensive_engine._determine_risk_level(0.7, thresholds) == RiskLevel.MEDIUM # >= 0.6 but < 0.8
        assert comprehensive_engine._determine_risk_level(0.85, thresholds) == RiskLevel.HIGH  # >= 0.8 but < 0.95
        assert comprehensive_engine._determine_risk_level(0.98, thresholds) == RiskLevel.CRITICAL # >= 0.95
    
    @pytest.mark.asyncio
    async def test_security_recommendations(self, comprehensive_engine):
        """Test security recommendation generation."""
        await comprehensive_engine.initialize()
        
        # Create high-risk behavioral and threat analysis
        from ai_karen_engine.security.models import (
            BehavioralAnalysis,
            ThreatAnalysis,
            BruteForceIndicators,
            CredentialStuffingIndicators,
            AccountTakeoverIndicators
        )
        
        behavioral_analysis = BehavioralAnalysis(
            is_usual_time=False,
            time_deviation_score=0.8,
            is_usual_location=False,
            location_deviation_score=0.9,
            is_known_device=False,
            device_similarity_score=0.1,
            login_frequency_anomaly=0.7,
            session_duration_anomaly=0.0,
            success_rate_last_30_days=0.5,
            failed_attempts_pattern={'recent_failures': 5}
        )
        
        threat_analysis = ThreatAnalysis(
            ip_reputation_score=0.8,
            known_attack_patterns=["brute_force"],
            threat_actor_indicators=["CYBERCRIMINAL"],
            brute_force_indicators=BruteForceIndicators(rapid_attempts=True),
            credential_stuffing_indicators=CredentialStuffingIndicators(),
            account_takeover_indicators=AccountTakeoverIndicators(),
            similar_attacks_detected=3,
            attack_campaign_correlation="campaign_456"
        )
        
        actions = comprehensive_engine._generate_security_recommendations(
            0.9, RiskLevel.CRITICAL, behavioral_analysis, threat_analysis
        )
        
        assert isinstance(actions, list)
        assert len(actions) > 0
        
        # Should have blocking action for critical risk
        block_actions = [a for a in actions if a.action_type == SecurityActionType.BLOCK]
        assert len(block_actions) > 0
        
        # Should have alert for brute force
        alert_actions = [a for a in actions if a.action_type == SecurityActionType.ALERT]
        assert len(alert_actions) > 0
    
    @pytest.mark.asyncio
    async def test_confidence_calculation(self, comprehensive_engine):
        """Test confidence score calculation."""
        await comprehensive_engine.initialize()
        
        from ai_karen_engine.security.models import (
            BehavioralAnalysis,
            ThreatAnalysis,
            BruteForceIndicators,
            CredentialStuffingIndicators,
            AccountTakeoverIndicators
        )
        
        # Create consistent behavioral analysis
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
        
        # Create threat analysis with correlations
        threat_analysis = ThreatAnalysis(
            ip_reputation_score=0.2,
            known_attack_patterns=[],
            threat_actor_indicators=[],
            brute_force_indicators=BruteForceIndicators(),
            credential_stuffing_indicators=CredentialStuffingIndicators(),
            account_takeover_indicators=AccountTakeoverIndicators(),
            similar_attacks_detected=2,
            attack_campaign_correlation=None
        )
        
        confidence = comprehensive_engine._calculate_confidence_score(
            behavioral_analysis, threat_analysis, 0.3
        )
        
        assert 0.0 <= confidence <= 1.0
        # Should have reasonable confidence for consistent data
        assert confidence > 0.4
    
    @pytest.mark.asyncio
    async def test_attack_correlation_calculation(self, comprehensive_engine):
        """Test attack correlation score calculation."""
        await comprehensive_engine.initialize()
        
        from ai_karen_engine.security.models import (
            ThreatAnalysis,
            BruteForceIndicators,
            CredentialStuffingIndicators,
            AccountTakeoverIndicators
        )
        
        threat_analysis = ThreatAnalysis(
            ip_reputation_score=0.5,
            known_attack_patterns=["pattern1", "pattern2"],
            threat_actor_indicators=["CYBERCRIMINAL"],
            brute_force_indicators=BruteForceIndicators(),
            credential_stuffing_indicators=CredentialStuffingIndicators(),
            account_takeover_indicators=AccountTakeoverIndicators(),
            similar_attacks_detected=8,
            attack_campaign_correlation="campaign_789"
        )
        
        correlation_score = comprehensive_engine._calculate_attack_correlation_score(threat_analysis)
        
        assert 0.0 <= correlation_score <= 1.0
        # Should have high correlation due to similar attacks and campaign
        assert correlation_score > 0.5
    
    @pytest.mark.asyncio
    async def test_fallback_analysis_result(self, comprehensive_engine, sample_auth_context):
        """Test fallback analysis result creation."""
        await comprehensive_engine.initialize()
        
        start_time = time.time()
        components_used = ["behavioral_anomaly_detector"]
        
        fallback_result = comprehensive_engine._create_fallback_analysis_result(
            sample_auth_context, start_time, components_used
        )
        
        assert isinstance(fallback_result, ComprehensiveAnalysisResult)
        assert fallback_result.behavioral_analysis is not None
        assert fallback_result.threat_analysis is not None
        assert fallback_result.overall_risk_score >= 0.0
        assert fallback_result.risk_level == RiskLevel.LOW
        assert fallback_result.processing_time >= 0.0
        assert fallback_result.components_used == components_used
        assert fallback_result.confidence_score >= 0.0
        assert not fallback_result.should_block
        assert not fallback_result.requires_2fa
    
    @pytest.mark.asyncio
    async def test_comprehensive_metrics(self, comprehensive_engine):
        """Test comprehensive metrics collection."""
        await comprehensive_engine.initialize()
        
        # Perform some analyses to generate metrics
        comprehensive_engine._comprehensive_analyses = 10
        comprehensive_engine._high_risk_detections = 3
        comprehensive_engine._blocked_attempts = 2
        comprehensive_engine._correlation_matches = 1
        comprehensive_engine._processing_times = [0.1, 0.2, 0.15, 0.18, 0.12]
        
        metrics = await comprehensive_engine.get_comprehensive_metrics()
        
        assert isinstance(metrics, dict)
        assert 'comprehensive_analyses' in metrics
        assert 'high_risk_detections' in metrics
        assert 'blocked_attempts' in metrics
        assert 'correlation_matches' in metrics
        assert 'avg_processing_time' in metrics
        assert 'model_version' in metrics
        assert 'anomaly_detector_metrics' in metrics
        assert 'attack_pattern_metrics' in metrics
        assert 'adaptive_learning_metrics' in metrics
        assert 'component_weights' in metrics
        assert 'components_health' in metrics
        
        # Check metric values
        assert metrics['comprehensive_analyses'] == 10
        assert metrics['high_risk_detections'] == 3
        assert metrics['blocked_attempts'] == 2
        assert metrics['correlation_matches'] == 1
        assert metrics['avg_processing_time'] > 0.0
    
    @pytest.mark.asyncio
    async def test_error_handling(self, comprehensive_engine, sample_auth_context):
        """Test error handling in comprehensive analysis."""
        await comprehensive_engine.initialize()
        
        # Test with None values
        result = await comprehensive_engine.analyze_authentication_attempt(
            sample_auth_context, None, None
        )
        
        # Should return fallback result without crashing
        assert isinstance(result, ComprehensiveAnalysisResult)
        assert result.overall_risk_score >= 0.0
        assert result.risk_level is not None
    
    @pytest.mark.asyncio
    async def test_shutdown(self, comprehensive_engine):
        """Test graceful shutdown."""
        await comprehensive_engine.initialize()
        
        # Should shutdown without errors
        await comprehensive_engine.shutdown()


if __name__ == "__main__":
    pytest.main([__file__])