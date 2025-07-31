"""
Tests for the unified intelligent authentication service.

This module tests the main orchestration service that coordinates all ML components
for intelligent authentication, including error handling, fallback mechanisms,
and performance monitoring.
"""

import asyncio
import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any

from ai_karen_engine.security.intelligent_auth_service import IntelligentAuthService, ProcessingMetrics
from ai_karen_engine.security.models import (
    AuthContext,
    AuthAnalysisResult,
    IntelligentAuthConfig,
    RiskLevel,
    GeoLocation,
    NLPFeatures,
    EmbeddingAnalysis,
    BehavioralAnalysis,
    ThreatAnalysis,
    CredentialFeatures,
    SecurityAction,
    SecurityActionType,
    BruteForceIndicators,
    CredentialStuffingIndicators,
    AccountTakeoverIndicators
)
from ai_karen_engine.security.intelligent_auth_base import ServiceStatus, ServiceHealthStatus


class TestIntelligentAuthService:
    """Test cases for IntelligentAuthService."""

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return IntelligentAuthConfig(
            enable_nlp_analysis=True,
            enable_embedding_analysis=True,
            enable_behavioral_analysis=True,
            enable_threat_intelligence=True,
            max_processing_time=5.0,
            cache_size=100,
            cache_ttl=300
        )

    @pytest.fixture
    def auth_context(self):
        """Create test authentication context."""
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
    def mock_spacy_service(self):
        """Create mock SpaCy service."""
        mock = Mock()
        mock.analyze_text = AsyncMock()
        return mock

    @pytest.fixture
    def mock_distilbert_service(self):
        """Create mock DistilBERT service."""
        mock = Mock()
        mock.get_embeddings = AsyncMock()
        return mock

    @pytest_asyncio.fixture
    async def service(self, config, mock_spacy_service, mock_distilbert_service):
        """Create test service instance."""
        service = IntelligentAuthService(
            config=config,
            spacy_service=mock_spacy_service,
            distilbert_service=mock_distilbert_service
        )
        
        # Mock the component initialization to avoid actual ML model loading
        with patch.object(service, '_initialize_components', new_callable=AsyncMock):
            await service.initialize()
        
        return service

    @pytest.mark.asyncio
    async def test_service_initialization(self, config, mock_spacy_service, mock_distilbert_service):
        """Test service initialization."""
        service = IntelligentAuthService(
            config=config,
            spacy_service=mock_spacy_service,
            distilbert_service=mock_distilbert_service
        )
        
        # Mock component initialization
        with patch.object(service, '_initialize_components', new_callable=AsyncMock) as mock_init:
            result = await service.initialize()
            
            assert result is True
            assert service._initialized is True
            mock_init.assert_called_once()

    @pytest.mark.asyncio
    async def test_analyze_login_attempt_success(self, service, auth_context):
        """Test successful login attempt analysis."""
        # Mock all component methods
        mock_nlp_features = NLPFeatures(
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
            processing_time=0.1,
            used_fallback=False,
            model_version="1.0"
        )

        mock_embedding_analysis = EmbeddingAnalysis(
            embedding_vector=[0.1] * 768,
            similarity_to_user_profile=0.8,
            similarity_to_attack_patterns=0.1,
            cluster_assignment="normal_users",
            outlier_score=0.2,
            processing_time=0.2,
            model_version="1.0"
        )

        mock_behavioral_analysis = BehavioralAnalysis(
            is_usual_time=True,
            time_deviation_score=0.1,
            is_usual_location=True,
            location_deviation_score=0.0,
            is_known_device=True,
            device_similarity_score=0.9,
            login_frequency_anomaly=0.1,
            session_duration_anomaly=0.0,
            success_rate_last_30_days=0.95,
            failed_attempts_pattern={}
        )

        mock_threat_analysis = ThreatAnalysis(
            ip_reputation_score=0.1,
            known_attack_patterns=[],
            threat_actor_indicators=[],
            brute_force_indicators=BruteForceIndicators(),
            credential_stuffing_indicators=CredentialStuffingIndicators(),
            account_takeover_indicators=AccountTakeoverIndicators(),
            similar_attacks_detected=0,
            attack_campaign_correlation=None
        )

        # Mock the analysis methods
        service._analyze_credentials_with_fallback = AsyncMock(return_value=mock_nlp_features)
        service._generate_embedding_with_fallback = AsyncMock(return_value=mock_embedding_analysis)
        service._detect_anomalies_with_fallback = AsyncMock(return_value=mock_behavioral_analysis)
        service._analyze_threats_with_fallback = AsyncMock(return_value=mock_threat_analysis)
        service._calculate_comprehensive_risk_score = AsyncMock(return_value=0.2)

        # Perform analysis
        result = await service.analyze_login_attempt(auth_context)

        # Verify result
        assert isinstance(result, AuthAnalysisResult)
        assert result.risk_score == 0.2
        assert result.risk_level == RiskLevel.LOW
        assert result.should_block is False
        assert result.requires_2fa is False
        assert result.processing_time > 0
        assert result.nlp_features == mock_nlp_features
        assert result.embedding_analysis == mock_embedding_analysis
        assert result.behavioral_analysis == mock_behavioral_analysis
        assert result.threat_analysis == mock_threat_analysis

    @pytest.mark.asyncio
    async def test_analyze_login_attempt_high_risk(self, service, auth_context):
        """Test high-risk login attempt analysis."""
        # Mock high-risk scenario
        service._analyze_credentials_with_fallback = AsyncMock(return_value=service._create_fallback_nlp_features())
        service._generate_embedding_with_fallback = AsyncMock(return_value=service._create_fallback_embedding_analysis())
        service._detect_anomalies_with_fallback = AsyncMock(return_value=service._create_fallback_behavioral_analysis())
        service._analyze_threats_with_fallback = AsyncMock(return_value=service._create_fallback_threat_analysis())
        service._calculate_comprehensive_risk_score = AsyncMock(return_value=0.85)  # High risk

        result = await service.analyze_login_attempt(auth_context)

        assert result.risk_score == 0.85
        assert result.risk_level == RiskLevel.HIGH
        assert result.should_block is False
        assert result.requires_2fa is True
        assert len(result.recommended_actions) > 0
        assert any(action.action_type == SecurityActionType.REQUIRE_2FA.value for action in result.recommended_actions)

    @pytest.mark.asyncio
    async def test_analyze_login_attempt_critical_risk(self, service, auth_context):
        """Test critical-risk login attempt analysis."""
        # Mock critical-risk scenario
        service._analyze_credentials_with_fallback = AsyncMock(return_value=service._create_fallback_nlp_features())
        service._generate_embedding_with_fallback = AsyncMock(return_value=service._create_fallback_embedding_analysis())
        service._detect_anomalies_with_fallback = AsyncMock(return_value=service._create_fallback_behavioral_analysis())
        service._analyze_threats_with_fallback = AsyncMock(return_value=service._create_fallback_threat_analysis())
        service._calculate_comprehensive_risk_score = AsyncMock(return_value=0.98)  # Critical risk

        result = await service.analyze_login_attempt(auth_context)

        assert result.risk_score == 0.98
        assert result.risk_level == RiskLevel.CRITICAL
        assert result.should_block is True
        assert result.requires_2fa is False  # Blocked, so no 2FA needed
        assert len(result.recommended_actions) > 0
        assert any(action.action_type == SecurityActionType.BLOCK.value for action in result.recommended_actions)

    @pytest.mark.asyncio
    async def test_analyze_login_attempt_with_error(self, service, auth_context):
        """Test login attempt analysis with component errors."""
        # Mock component failure
        service._analyze_credentials_with_fallback = AsyncMock(side_effect=Exception("NLP service failed"))
        service._generate_embedding_with_fallback = AsyncMock(return_value=service._create_fallback_embedding_analysis())
        service._detect_anomalies_with_fallback = AsyncMock(return_value=service._create_fallback_behavioral_analysis())
        service._analyze_threats_with_fallback = AsyncMock(return_value=service._create_fallback_threat_analysis())

        result = await service.analyze_login_attempt(auth_context)

        # Should return fallback result
        assert isinstance(result, AuthAnalysisResult)
        assert result.risk_score == service.config.fallback_config.fallback_risk_score
        assert result.risk_level == RiskLevel.LOW
        assert len(result.recommended_actions) > 0
        assert result.user_feedback_required is True

    @pytest.mark.asyncio
    async def test_caching_functionality(self, service, auth_context):
        """Test caching of analysis results."""
        # Mock analysis methods
        service._analyze_credentials_with_fallback = AsyncMock(return_value=service._create_fallback_nlp_features())
        service._generate_embedding_with_fallback = AsyncMock(return_value=service._create_fallback_embedding_analysis())
        service._detect_anomalies_with_fallback = AsyncMock(return_value=service._create_fallback_behavioral_analysis())
        service._analyze_threats_with_fallback = AsyncMock(return_value=service._create_fallback_threat_analysis())
        service._calculate_comprehensive_risk_score = AsyncMock(return_value=0.3)

        # First call should perform analysis
        result1 = await service.analyze_login_attempt(auth_context)
        
        # Second call with same context should use cache
        result2 = await service.analyze_login_attempt(auth_context)

        # Results should be identical (cached)
        assert result1.risk_score == result2.risk_score
        assert result1.analysis_timestamp == result2.analysis_timestamp

        # Analysis methods should only be called once (first time)
        service._analyze_credentials_with_fallback.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_user_behavioral_profile(self, service, auth_context):
        """Test updating user behavioral profile."""
        user_id = "test_user_123"
        
        # Mock component methods
        service.behavioral_embedding = Mock()
        service.behavioral_embedding.update_user_profile = AsyncMock()
        service.anomaly_engine = Mock()
        service.anomaly_engine.update_user_profile = AsyncMock()
        service.adaptive_learning = Mock()
        service.adaptive_learning.process_feedback = AsyncMock()

        await service.update_user_behavioral_profile(user_id, auth_context, success=True)

        # Verify all components were called
        service.behavioral_embedding.update_user_profile.assert_called_once()
        service.anomaly_engine.update_user_profile.assert_called_once()
        service.adaptive_learning.process_feedback.assert_called_once()

    @pytest.mark.asyncio
    async def test_provide_feedback(self, service, auth_context):
        """Test providing feedback to ML models."""
        user_id = "test_user_123"
        feedback = {"correct_prediction": True, "user_satisfaction": 5}
        
        # Mock adaptive learning component
        service.adaptive_learning = Mock()
        service.adaptive_learning.process_feedback = AsyncMock()

        await service.provide_feedback(user_id, auth_context, feedback)

        service.adaptive_learning.process_feedback.assert_called_once()

    def test_get_health_status(self, service):
        """Test getting health status."""
        # Mock component health statuses
        service.component_health = {
            "credential_analyzer": ServiceHealthStatus(
                service_name="credential_analyzer",
                status=ServiceStatus.HEALTHY,
                last_check=datetime.now(),
                response_time=0.1
            ),
            "behavioral_embedding": ServiceHealthStatus(
                service_name="behavioral_embedding",
                status=ServiceStatus.HEALTHY,
                last_check=datetime.now(),
                response_time=0.2
            )
        }

        health_status = service.get_health_status()

        assert health_status.overall_status == ServiceStatus.HEALTHY
        assert len(health_status.component_statuses) == 2
        assert "credential_analyzer" in health_status.component_statuses
        assert "behavioral_embedding" in health_status.component_statuses

    def test_get_health_status_with_unhealthy_component(self, service):
        """Test getting health status with unhealthy component."""
        # Mock one unhealthy component
        service.component_health = {
            "credential_analyzer": ServiceHealthStatus(
                service_name="credential_analyzer",
                status=ServiceStatus.UNHEALTHY,
                last_check=datetime.now(),
                response_time=0.1,
                error_message="Service unavailable"
            ),
            "behavioral_embedding": ServiceHealthStatus(
                service_name="behavioral_embedding",
                status=ServiceStatus.HEALTHY,
                last_check=datetime.now(),
                response_time=0.2
            )
        }

        health_status = service.get_health_status()

        assert health_status.overall_status == ServiceStatus.UNHEALTHY
        assert len(health_status.get_unhealthy_components()) == 1
        assert "credential_analyzer" in health_status.get_unhealthy_components()

    def test_processing_metrics(self, service):
        """Test processing metrics tracking."""
        # Simulate some processing
        service._update_metrics(0.5, success=True)
        service._update_metrics(0.3, success=True)
        service._update_metrics(1.0, success=False)

        metrics = service.get_processing_metrics()

        assert metrics.total_requests == 3
        assert metrics.successful_requests == 2
        assert metrics.failed_requests == 1
        assert metrics.error_rate == 1/3
        assert metrics.avg_processing_time > 0

    def test_fallback_risk_calculation(self, service):
        """Test fallback risk score calculation."""
        # Create test analysis components
        nlp_features = NLPFeatures(
            email_features=CredentialFeatures(
                token_count=2, unique_token_ratio=1.0, entropy_score=3.5,
                language="en", contains_suspicious_patterns=False, pattern_types=[]
            ),
            password_features=CredentialFeatures(
                token_count=1, unique_token_ratio=1.0, entropy_score=4.2,
                language="en", contains_suspicious_patterns=False, pattern_types=[]
            ),
            credential_similarity=0.9,  # High similarity (suspicious)
            language_consistency=True,
            suspicious_patterns=["repeated_chars"],  # Suspicious pattern
            processing_time=0.1,
            used_fallback=False,
            model_version="1.0"
        )

        embedding_analysis = EmbeddingAnalysis(
            embedding_vector=[0.1] * 768,
            similarity_to_user_profile=0.3,
            similarity_to_attack_patterns=0.8,  # High attack similarity
            outlier_score=0.8,  # High outlier score
            processing_time=0.2,
            model_version="1.0"
        )

        behavioral_analysis = BehavioralAnalysis(
            is_usual_time=False,  # Unusual time
            time_deviation_score=0.8,
            is_usual_location=False,  # Unusual location
            location_deviation_score=0.7,
            is_known_device=True,
            device_similarity_score=0.9,
            login_frequency_anomaly=0.8,  # High frequency anomaly
            session_duration_anomaly=0.2,
            success_rate_last_30_days=0.95,
            failed_attempts_pattern={}
        )

        threat_analysis = ThreatAnalysis(
            ip_reputation_score=0.8,  # High threat score
            known_attack_patterns=["brute_force"],  # Known attack patterns
            threat_actor_indicators=[],
            brute_force_indicators=BruteForceIndicators(),
            credential_stuffing_indicators=CredentialStuffingIndicators(),
            account_takeover_indicators=AccountTakeoverIndicators(),
            similar_attacks_detected=0,
            attack_campaign_correlation=None
        )

        risk_score = service._calculate_fallback_risk_score(
            nlp_features, embedding_analysis, behavioral_analysis, threat_analysis
        )

        # Should be high risk due to multiple suspicious factors
        assert risk_score > 0.5
        assert risk_score <= 1.0

    def test_risk_level_determination(self, service):
        """Test risk level determination from scores."""
        assert service._determine_risk_level(0.1) == RiskLevel.LOW
        assert service._determine_risk_level(0.4) == RiskLevel.MEDIUM
        assert service._determine_risk_level(0.7) == RiskLevel.HIGH
        assert service._determine_risk_level(0.98) == RiskLevel.CRITICAL

    def test_security_actions_determination(self, service):
        """Test security actions determination."""
        # Low risk
        should_block, requires_2fa = service._determine_security_actions(0.2, RiskLevel.LOW)
        assert should_block is False
        assert requires_2fa is False

        # High risk
        should_block, requires_2fa = service._determine_security_actions(0.7, RiskLevel.HIGH)
        assert should_block is False
        assert requires_2fa is True

        # Critical risk
        should_block, requires_2fa = service._determine_security_actions(0.98, RiskLevel.CRITICAL)
        assert should_block is True
        assert requires_2fa is False

    def test_confidence_score_calculation(self, service):
        """Test confidence score calculation."""
        # High confidence scenario
        nlp_features = service._create_fallback_nlp_features()
        nlp_features.used_fallback = False  # Not using fallback

        embedding_analysis = service._create_fallback_embedding_analysis()
        behavioral_analysis = service._create_fallback_behavioral_analysis()
        behavioral_analysis.success_rate_last_30_days = 0.9  # Good historical data

        threat_analysis = service._create_fallback_threat_analysis()
        threat_analysis.ip_reputation_score = 0.1  # Some threat intel data

        confidence = service._calculate_confidence_score(
            nlp_features, embedding_analysis, behavioral_analysis, threat_analysis
        )

        assert 0.0 <= confidence <= 1.0
        assert confidence > 0.5  # Should be reasonably confident

    def test_feedback_request_determination(self, service):
        """Test feedback request determination."""
        # Borderline medium risk - should request feedback
        assert service._should_request_feedback(0.55, RiskLevel.MEDIUM) is True
        
        # Borderline high risk - should request feedback
        assert service._should_request_feedback(0.75, RiskLevel.HIGH) is True
        
        # Clear low risk - no feedback needed
        assert service._should_request_feedback(0.1, RiskLevel.LOW) is False
        
        # Clear critical risk - no feedback needed
        assert service._should_request_feedback(0.98, RiskLevel.CRITICAL) is False

    @pytest.mark.asyncio
    async def test_service_shutdown(self, service):
        """Test service shutdown."""
        # Mock components with shutdown methods
        service.credential_analyzer = Mock()
        service.credential_analyzer.shutdown = AsyncMock()
        service.behavioral_embedding = Mock()
        service.behavioral_embedding.shutdown = AsyncMock()

        await service.shutdown()

        assert service._initialized is False
        service.credential_analyzer.shutdown.assert_called_once()
        service.behavioral_embedding.shutdown.assert_called_once()

    def test_error_recording(self, service, auth_context):
        """Test error recording functionality."""
        error = Exception("Test error")
        
        service._record_error(error, auth_context)

        assert len(service.error_history) == 1
        error_record = service.error_history[0]
        assert error_record['error_type'] == 'Exception'
        assert error_record['error_message'] == 'Test error'
        assert error_record['request_id'] == auth_context.request_id

    def test_cache_key_generation(self, service, auth_context):
        """Test cache key generation."""
        key1 = service._generate_cache_key(auth_context)
        key2 = service._generate_cache_key(auth_context)
        
        # Same context should generate same key
        assert key1 == key2
        assert len(key1) == 16  # SHA256 hash truncated to 16 chars

        # Different context should generate different key
        auth_context.email = "different@example.com"
        key3 = service._generate_cache_key(auth_context)
        assert key1 != key3


if __name__ == "__main__":
    pytest.main([__file__])