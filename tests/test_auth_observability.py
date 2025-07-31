"""
Unit tests for intelligent authentication observability service.

Tests comprehensive metrics collection, alerting, and security insights generation
for the intelligent authentication system.
"""

import asyncio
import json
import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from src.ai_karen_engine.security.observability import (
    AuthObservabilityService,
    AuthEvent,
    AuthEventType,
    AlertSeverity,
    SecurityAlert,
    SecurityInsight,
    PrometheusMetrics,
    MetricsAggregator,
    AlertingEngine,
    SecurityInsightsGenerator,
    create_observability_service,
    PROMETHEUS_AVAILABLE
)
from src.ai_karen_engine.security.models import (
    AuthContext,
    AuthAnalysisResult,
    RiskLevel,
    GeoLocation,
    NLPFeatures,
    CredentialFeatures,
    EmbeddingAnalysis,
    BehavioralAnalysis,
    ThreatAnalysis,
    SecurityAction
)


@pytest.fixture
def sample_auth_context():
    """Create sample authentication context for testing."""
    return AuthContext(
        email="test@example.com",
        password_hash="hashed_password",
        client_ip="192.168.1.100",
        user_agent="Mozilla/5.0 Test Browser",
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
        device_fingerprint="test_device_fingerprint",
        is_tor_exit_node=False,
        is_vpn=False,
        threat_intel_score=0.2,
        previous_failed_attempts=0
    )


@pytest.fixture
def sample_auth_result():
    """Create sample authentication analysis result for testing."""
    return AuthAnalysisResult(
        risk_score=0.3,
        risk_level=RiskLevel.LOW,
        should_block=False,
        requires_2fa=False,
        nlp_features=NLPFeatures(
            email_features=CredentialFeatures(
                token_count=2,
                unique_token_ratio=1.0,
                entropy_score=3.5,
                language="en",
                contains_suspicious_patterns=False
            ),
            password_features=CredentialFeatures(
                token_count=1,
                unique_token_ratio=1.0,
                entropy_score=4.2,
                language="en",
                contains_suspicious_patterns=False
            ),
            credential_similarity=0.1,
            language_consistency=True,
            processing_time=0.05
        ),
        embedding_analysis=EmbeddingAnalysis(
            embedding_vector=[0.1, 0.2, 0.3, 0.4, 0.5],
            similarity_to_user_profile=0.8,
            similarity_to_attack_patterns=0.1,
            outlier_score=0.2,
            processing_time=0.1
        ),
        behavioral_analysis=BehavioralAnalysis(
            is_usual_time=True,
            time_deviation_score=0.1,
            is_usual_location=True,
            location_deviation_score=0.0,
            is_known_device=True,
            device_similarity_score=0.9,
            login_frequency_anomaly=0.1,
            session_duration_anomaly=0.1,
            success_rate_last_30_days=0.95
        ),
        threat_analysis=ThreatAnalysis(
            ip_reputation_score=0.2,
            known_attack_patterns=["pattern1"],
            similar_attacks_detected=0
        ),
        processing_time=0.25,
        confidence_score=0.8
    )


class TestAuthEvent:
    """Test AuthEvent data model."""
    
    def test_auth_event_creation(self, sample_auth_context):
        """Test creating AuthEvent from basic parameters."""
        event = AuthEvent(
            event_type=AuthEventType.LOGIN_ATTEMPT,
            user_id="test@example.com",
            email="test@example.com",
            client_ip="192.168.1.100",
            user_agent="Test Browser",
            timestamp=datetime.now(),
            request_id="test_123"
        )
        
        assert event.event_type == AuthEventType.LOGIN_ATTEMPT
        assert event.user_id == "test@example.com"
        assert event.client_ip == "192.168.1.100"
        assert event.request_id == "test_123"
    
    def test_auth_event_from_context_and_result(self, sample_auth_context, sample_auth_result):
        """Test creating AuthEvent from AuthContext and AuthAnalysisResult."""
        event = AuthEvent.from_auth_context_and_result(
            sample_auth_context,
            sample_auth_result,
            AuthEventType.LOGIN_SUCCESS,
            processing_time_ms=250.0
        )
        
        assert event.event_type == AuthEventType.LOGIN_SUCCESS
        assert event.email == sample_auth_context.email
        assert event.client_ip == sample_auth_context.client_ip
        assert event.risk_score == sample_auth_result.risk_score
        assert event.risk_level == sample_auth_result.risk_level
        assert event.processing_time_ms == 250.0
        assert event.country == "US"
        assert event.is_usual_location is True
    
    def test_auth_event_to_dict(self, sample_auth_context):
        """Test AuthEvent serialization to dictionary."""
        event = AuthEvent.from_auth_context_and_result(
            sample_auth_context,
            event_type=AuthEventType.LOGIN_ATTEMPT
        )
        
        event_dict = event.to_dict()
        
        assert event_dict['event_type'] == 'login_attempt'
        assert event_dict['email'] == sample_auth_context.email
        assert 'timestamp' in event_dict
        assert isinstance(event_dict['timestamp'], str)  # Should be ISO format


class TestSecurityAlert:
    """Test SecurityAlert data model."""
    
    def test_security_alert_creation(self):
        """Test creating SecurityAlert."""
        alert = SecurityAlert(
            alert_id="test_alert_123",
            severity=AlertSeverity.HIGH,
            title="Test Alert",
            description="This is a test alert",
            source="test_source",
            timestamp=datetime.now(),
            user_id="test@example.com",
            client_ip="192.168.1.100"
        )
        
        assert alert.alert_id == "test_alert_123"
        assert alert.severity == AlertSeverity.HIGH
        assert alert.title == "Test Alert"
        assert alert.user_id == "test@example.com"
        assert alert.resolved is False
    
    def test_security_alert_to_dict(self):
        """Test SecurityAlert serialization."""
        alert = SecurityAlert(
            alert_id="test_alert_123",
            severity=AlertSeverity.MEDIUM,
            title="Test Alert",
            description="Test description",
            source="test_source",
            timestamp=datetime.now()
        )
        
        alert_dict = alert.to_dict()
        
        assert alert_dict['severity'] == 'medium'
        assert alert_dict['title'] == 'Test Alert'
        assert 'timestamp' in alert_dict


class TestPrometheusMetrics:
    """Test Prometheus metrics collection."""
    
    def test_prometheus_metrics_initialization(self):
        """Test PrometheusMetrics initialization."""
        metrics = PrometheusMetrics()
        
        # Check that metrics objects are created
        assert hasattr(metrics, 'auth_attempts_total')
        assert hasattr(metrics, 'auth_blocks_total')
        assert hasattr(metrics, 'ml_processing_duration')
        assert hasattr(metrics, 'risk_score_distribution')
        assert hasattr(metrics, 'threat_detections_total')
    
    def test_prometheus_metrics_fallback(self):
        """Test PrometheusMetrics with fallback when prometheus unavailable."""
        # Create a custom registry to avoid conflicts
        if PROMETHEUS_AVAILABLE:
            from prometheus_client import CollectorRegistry
            custom_registry = CollectorRegistry()
            metrics = PrometheusMetrics(registry=custom_registry)
        else:
            metrics = PrometheusMetrics()
        
        # Should not raise errors even when prometheus is unavailable
        metrics.auth_attempts_total.labels(
            event_type='login_attempt',
            risk_level='low',
            country='US',
            outcome='success'
        ).inc()


class TestMetricsAggregator:
    """Test MetricsAggregator functionality."""
    
    def test_metrics_aggregator_initialization(self):
        """Test MetricsAggregator initialization."""
        aggregator = MetricsAggregator(retention_hours=24)
        
        assert aggregator.retention_hours == 24
        assert len(aggregator.events) == 0
        assert len(aggregator.alerts) == 0
    
    def test_add_event(self, sample_auth_context):
        """Test adding events to aggregator."""
        aggregator = MetricsAggregator()
        event = AuthEvent.from_auth_context_and_result(
            sample_auth_context,
            event_type=AuthEventType.LOGIN_SUCCESS
        )
        
        aggregator.add_event(event)
        
        assert len(aggregator.events) == 1
        assert aggregator.events[0] == event
    
    def test_add_alert(self):
        """Test adding alerts to aggregator."""
        aggregator = MetricsAggregator()
        alert = SecurityAlert(
            alert_id="test_123",
            severity=AlertSeverity.HIGH,
            title="Test Alert",
            description="Test",
            source="test",
            timestamp=datetime.now()
        )
        
        aggregator.add_alert(alert)
        
        assert len(aggregator.alerts) == 1
        assert aggregator.alerts[0] == alert
    
    def test_get_events_in_timerange(self, sample_auth_context):
        """Test retrieving events within time range."""
        aggregator = MetricsAggregator()
        
        # Add events with different timestamps
        now = datetime.now()
        old_event = AuthEvent.from_auth_context_and_result(
            sample_auth_context,
            event_type=AuthEventType.LOGIN_ATTEMPT
        )
        old_event.timestamp = now - timedelta(hours=2)
        
        recent_event = AuthEvent.from_auth_context_and_result(
            sample_auth_context,
            event_type=AuthEventType.LOGIN_SUCCESS
        )
        recent_event.timestamp = now - timedelta(minutes=30)
        
        aggregator.add_event(old_event)
        aggregator.add_event(recent_event)
        
        # Get events from last hour
        start_time = now - timedelta(hours=1)
        end_time = now
        events = aggregator.get_events_in_timerange(start_time, end_time)
        
        assert len(events) == 1
        assert events[0] == recent_event
    
    def test_get_hourly_stats(self, sample_auth_context):
        """Test getting hourly statistics."""
        aggregator = MetricsAggregator()
        
        # Add some events
        for i in range(5):
            event = AuthEvent.from_auth_context_and_result(
                sample_auth_context,
                event_type=AuthEventType.LOGIN_SUCCESS
            )
            aggregator.add_event(event)
        
        stats = aggregator.get_hourly_stats(hours_back=1)
        
        # Should have stats for current hour
        assert len(stats) > 0
        current_hour = datetime.now().strftime('%Y-%m-%d-%H')
        assert current_hour in stats
        assert stats[current_hour]['total_events'] == 5


class TestAlertingEngine:
    """Test AlertingEngine functionality."""
    
    def test_alerting_engine_initialization(self):
        """Test AlertingEngine initialization."""
        engine = AlertingEngine()
        
        assert len(engine.alert_handlers) == 0
        assert len(engine.alert_rules) > 0  # Should have default rules
    
    def test_add_alert_handler(self):
        """Test adding alert handler."""
        engine = AlertingEngine()
        handler = Mock()
        
        engine.add_alert_handler(handler)
        
        assert len(engine.alert_handlers) == 1
        assert engine.alert_handlers[0] == handler
    
    def test_add_alert_rule(self):
        """Test adding custom alert rule."""
        engine = AlertingEngine()
        
        rule = {
            'name': 'test_rule',
            'condition': lambda event: event.risk_score and event.risk_score > 0.9,
            'severity': AlertSeverity.CRITICAL,
            'title': 'Test Rule Alert',
            'description': 'Test rule triggered'
        }
        
        engine.add_alert_rule(rule)
        
        # Should have default rules plus our custom rule
        assert len(engine.alert_rules) > 4
        assert rule in engine.alert_rules
    
    def test_process_event_triggers_alert(self, sample_auth_context):
        """Test that high-risk events trigger alerts."""
        engine = AlertingEngine()
        handler = Mock()
        engine.add_alert_handler(handler)
        
        # Create high-risk event
        event = AuthEvent.from_auth_context_and_result(
            sample_auth_context,
            event_type=AuthEventType.LOGIN_ATTEMPT
        )
        event.risk_score = 0.9  # High risk
        
        engine.process_event(event)
        
        # Should have called the handler
        handler.assert_called_once()
        alert = handler.call_args[0][0]
        assert isinstance(alert, SecurityAlert)
        assert alert.severity == AlertSeverity.HIGH
    
    def test_process_event_no_alert_for_low_risk(self, sample_auth_context):
        """Test that low-risk events don't trigger alerts."""
        engine = AlertingEngine()
        handler = Mock()
        engine.add_alert_handler(handler)
        
        # Create low-risk event
        event = AuthEvent.from_auth_context_and_result(
            sample_auth_context,
            event_type=AuthEventType.LOGIN_ATTEMPT
        )
        event.risk_score = 0.2  # Low risk
        
        engine.process_event(event)
        
        # Should not have called the handler
        handler.assert_not_called()


class TestSecurityInsightsGenerator:
    """Test SecurityInsightsGenerator functionality."""
    
    def test_insights_generator_initialization(self):
        """Test SecurityInsightsGenerator initialization."""
        aggregator = MetricsAggregator()
        generator = SecurityInsightsGenerator(aggregator)
        
        assert generator.metrics_aggregator == aggregator
        assert len(generator.insight_generators) > 0
    
    @pytest.mark.asyncio
    async def test_generate_insights_empty_data(self):
        """Test generating insights with no data."""
        aggregator = MetricsAggregator()
        generator = SecurityInsightsGenerator(aggregator)
        
        insights = await generator.generate_insights(hours_back=24)
        
        # Should return empty list or insights with zero counts
        assert isinstance(insights, list)
    
    @pytest.mark.asyncio
    async def test_generate_anomaly_insights(self, sample_auth_context):
        """Test generating anomaly insights."""
        aggregator = MetricsAggregator()
        generator = SecurityInsightsGenerator(aggregator)
        
        # Add multiple high-risk events
        for i in range(15):  # Above threshold of 10
            event = AuthEvent.from_auth_context_and_result(
                sample_auth_context,
                event_type=AuthEventType.LOGIN_ATTEMPT
            )
            event.risk_score = 0.9
            event.user_id = f"user{i}@example.com"
            aggregator.add_event(event)
        
        insights = await generator._generate_anomaly_insights(hours_back=1)
        
        assert len(insights) > 0
        insight = insights[0]
        assert insight.category == "anomaly_detection"
        assert insight.severity == AlertSeverity.HIGH
        assert "high-risk" in insight.title.lower()
    
    @pytest.mark.asyncio
    async def test_generate_threat_intelligence_insights(self, sample_auth_context):
        """Test generating threat intelligence insights."""
        aggregator = MetricsAggregator()
        generator = SecurityInsightsGenerator(aggregator)
        
        # Add multiple threat intelligence hits
        for i in range(8):  # Above threshold of 5
            event = AuthEvent.from_auth_context_and_result(
                sample_auth_context,
                event_type=AuthEventType.LOGIN_ATTEMPT
            )
            event.threat_intel_score = 0.8
            event.client_ip = f"192.168.1.{i}"
            aggregator.add_event(event)
        
        insights = await generator._generate_threat_intelligence_insights(hours_back=1)
        
        assert len(insights) > 0
        insight = insights[0]
        assert insight.category == "threat_intelligence"
        assert insight.severity == AlertSeverity.HIGH


class TestAuthObservabilityService:
    """Test AuthObservabilityService main functionality."""
    
    def test_observability_service_initialization(self):
        """Test AuthObservabilityService initialization."""
        service = AuthObservabilityService()
        
        assert service.prometheus_metrics is not None
        assert service.metrics_aggregator is not None
        assert service.alerting_engine is not None
        assert service.insights_generator is not None
    
    def test_observability_service_with_config(self):
        """Test AuthObservabilityService initialization with config."""
        config = {
            'retention_hours': 48,
            'max_metrics': 5000
        }
        
        service = AuthObservabilityService(config)
        
        assert service.config == config
        assert service.metrics_aggregator.retention_hours == 48
    
    def test_record_auth_event(self, sample_auth_context, sample_auth_result):
        """Test recording authentication event."""
        service = AuthObservabilityService()
        
        service.record_auth_event(
            sample_auth_context,
            sample_auth_result,
            AuthEventType.LOGIN_SUCCESS,
            processing_time_ms=200.0
        )
        
        # Check that event was added to aggregator
        events = service.metrics_aggregator.get_events_in_timerange(
            datetime.now() - timedelta(minutes=1),
            datetime.now()
        )
        
        assert len(events) == 1
        event = events[0]
        assert event.event_type == AuthEventType.LOGIN_SUCCESS
        assert event.processing_time_ms == 200.0
    
    def test_record_ml_processing_metrics(self):
        """Test recording ML processing metrics."""
        service = AuthObservabilityService()
        
        # Should not raise errors
        service.record_ml_processing_metrics(
            component="nlp_analysis",
            duration_ms=50.0,
            success=True
        )
        
        service.record_ml_processing_metrics(
            component="embedding_analysis",
            duration_ms=100.0,
            success=False,
            error_type="timeout"
        )
    
    def test_record_threat_detection(self, sample_auth_context):
        """Test recording threat detection."""
        service = AuthObservabilityService()
        
        service.record_threat_detection(
            threat_type="brute_force",
            severity="high",
            source="anomaly_detector",
            context=sample_auth_context
        )
        
        # Should create alert for high severity
        alerts = service.get_recent_alerts(hours_back=1)
        assert len(alerts) > 0
        alert = alerts[0]
        assert "brute_force" in alert.title.lower()
    
    def test_record_component_health(self):
        """Test recording component health."""
        service = AuthObservabilityService()
        
        # Should not raise errors
        service.record_component_health("nlp_service", True)
        service.record_component_health("embedding_service", False)
    
    def test_get_authentication_statistics(self, sample_auth_context, sample_auth_result):
        """Test getting authentication statistics."""
        service = AuthObservabilityService()
        
        # Add some events
        service.record_auth_event(
            sample_auth_context,
            sample_auth_result,
            AuthEventType.LOGIN_SUCCESS
        )
        
        service.record_auth_event(
            sample_auth_context,
            sample_auth_result,
            AuthEventType.LOGIN_FAILURE
        )
        
        stats = service.get_authentication_statistics(hours_back=1)
        
        assert stats['total_events'] == 2
        assert 'success_rate' in stats
        assert 'failure_rate' in stats
        assert 'unique_users' in stats
        assert 'time_range' in stats
    
    def test_get_threat_intelligence_statistics(self, sample_auth_context):
        """Test getting threat intelligence statistics."""
        service = AuthObservabilityService()
        
        # Add event with threat intelligence data
        event = AuthEvent.from_auth_context_and_result(
            sample_auth_context,
            event_type=AuthEventType.LOGIN_ATTEMPT
        )
        event.threat_intel_score = 0.9  # > 0.8 for high threat
        event.attack_patterns = ["brute_force", "credential_stuffing"]
        
        service.metrics_aggregator.add_event(event)
        
        stats = service.get_threat_intelligence_statistics(hours_back=1)
        
        assert stats['total_threat_hits'] == 1
        assert stats['high_threat_hits'] == 1
        assert 'malicious_ips' in stats
        assert 'attack_patterns' in stats
    
    def test_get_ml_performance_statistics(self, sample_auth_context):
        """Test getting ML performance statistics."""
        service = AuthObservabilityService()
        
        # Add event with ML performance data
        event = AuthEvent.from_auth_context_and_result(
            sample_auth_context,
            event_type=AuthEventType.LOGIN_ATTEMPT
        )
        event.nlp_analysis_success = True
        event.embedding_analysis_success = False
        event.nlp_processing_time_ms = 50.0
        event.embedding_processing_time_ms = 100.0
        
        service.metrics_aggregator.add_event(event)
        
        stats = service.get_ml_performance_statistics(hours_back=1)
        
        assert stats['total_events'] == 1
        assert 'nlp_success_rate' in stats
        assert 'embedding_success_rate' in stats
        assert 'avg_nlp_processing_time_ms' in stats
    
    @pytest.mark.asyncio
    async def test_generate_security_insights(self, sample_auth_context):
        """Test generating security insights."""
        service = AuthObservabilityService()
        
        # Add some high-risk events
        for i in range(12):
            event = AuthEvent.from_auth_context_and_result(
                sample_auth_context,
                event_type=AuthEventType.LOGIN_ATTEMPT
            )
            event.risk_score = 0.9
            service.metrics_aggregator.add_event(event)
        
        insights = await service.generate_security_insights(hours_back=1)
        
        assert isinstance(insights, list)
        # Should generate at least one insight for high-risk events
        if insights:
            assert all(isinstance(insight, SecurityInsight) for insight in insights)
    
    def test_add_alert_handler(self):
        """Test adding custom alert handler."""
        service = AuthObservabilityService()
        handler = Mock()
        
        service.add_alert_handler(handler)
        
        # Handler should be added to alerting engine
        assert handler in service.alerting_engine.alert_handlers
    
    def test_export_prometheus_metrics(self):
        """Test exporting Prometheus metrics."""
        service = AuthObservabilityService()
        
        metrics_data = service.export_prometheus_metrics()
        
        assert isinstance(metrics_data, bytes)
    
    def test_export_events_json(self, sample_auth_context):
        """Test exporting events as JSON."""
        service = AuthObservabilityService()
        
        # Add an event
        service.record_auth_event(
            sample_auth_context,
            event_type=AuthEventType.LOGIN_SUCCESS
        )
        
        json_data = service.export_events_json(hours_back=1)
        
        assert isinstance(json_data, str)
        events = json.loads(json_data)
        assert isinstance(events, list)
        assert len(events) == 1
    
    def test_export_alerts_json(self):
        """Test exporting alerts as JSON."""
        service = AuthObservabilityService()
        
        # Create an alert
        alert = SecurityAlert(
            alert_id="test_123",
            severity=AlertSeverity.HIGH,
            title="Test Alert",
            description="Test",
            source="test",
            timestamp=datetime.now()
        )
        service.metrics_aggregator.add_alert(alert)
        
        json_data = service.export_alerts_json(hours_back=1)
        
        assert isinstance(json_data, str)
        alerts = json.loads(json_data)
        assert isinstance(alerts, list)
        assert len(alerts) == 1
    
    def test_cleanup(self):
        """Test service cleanup."""
        service = AuthObservabilityService()
        
        # Should not raise errors
        service.cleanup()


class TestConvenienceFunctions:
    """Test convenience functions."""
    
    def test_create_observability_service(self):
        """Test create_observability_service function."""
        service = create_observability_service()
        
        assert isinstance(service, AuthObservabilityService)
    
    def test_create_observability_service_with_config(self):
        """Test create_observability_service with config."""
        config = {'retention_hours': 72}
        service = create_observability_service(config)
        
        assert isinstance(service, AuthObservabilityService)
        assert service.config == config


class TestIntegration:
    """Integration tests for observability service."""
    
    @pytest.mark.asyncio
    async def test_full_authentication_flow_observability(self, sample_auth_context, sample_auth_result):
        """Test complete authentication flow with observability."""
        service = AuthObservabilityService()
        
        # Record authentication attempt
        service.record_auth_event(
            sample_auth_context,
            sample_auth_result,
            AuthEventType.LOGIN_ATTEMPT,
            processing_time_ms=150.0
        )
        
        # Record ML processing metrics
        service.record_ml_processing_metrics("nlp_analysis", 50.0, True)
        service.record_ml_processing_metrics("embedding_analysis", 80.0, True)
        service.record_ml_processing_metrics("anomaly_detection", 20.0, True)
        
        # Record successful login
        service.record_auth_event(
            sample_auth_context,
            sample_auth_result,
            AuthEventType.LOGIN_SUCCESS,
            processing_time_ms=200.0
        )
        
        # Get statistics
        auth_stats = service.get_authentication_statistics(hours_back=1)
        ml_stats = service.get_ml_performance_statistics(hours_back=1)
        
        # Generate insights
        insights = await service.generate_security_insights(hours_back=1)
        
        # Verify data was recorded correctly
        assert auth_stats['total_events'] == 2
        assert ml_stats['total_events'] == 2
        assert ml_stats['nlp_success_rate'] == 1.0
        
        # Export data
        events_json = service.export_events_json(hours_back=1)
        prometheus_metrics = service.export_prometheus_metrics()
        
        assert len(json.loads(events_json)) == 2
        assert isinstance(prometheus_metrics, bytes)
    
    def test_high_volume_event_processing(self, sample_auth_context):
        """Test processing high volume of events."""
        service = AuthObservabilityService()
        
        # Process many events
        num_events = 1000
        for i in range(num_events):
            event = AuthEvent.from_auth_context_and_result(
                sample_auth_context,
                event_type=AuthEventType.LOGIN_ATTEMPT
            )
            event.user_id = f"user{i % 100}@example.com"  # 100 unique users
            event.risk_score = 0.1 + (i % 10) * 0.1  # Varying risk scores
            
            service.metrics_aggregator.add_event(event)
        
        # Get statistics
        stats = service.get_authentication_statistics(hours_back=1)
        
        assert stats['total_events'] == num_events
        assert stats['unique_users'] == 100
        assert 0.0 <= stats['avg_risk_score'] <= 1.0
    
    def test_alert_generation_and_handling(self, sample_auth_context):
        """Test alert generation and handling."""
        service = AuthObservabilityService()
        
        # Add alert handler
        alerts_received = []
        def test_handler(alert):
            alerts_received.append(alert)
        
        service.add_alert_handler(test_handler)
        
        # Create high-risk event that should trigger alert
        event = AuthEvent.from_auth_context_and_result(
            sample_auth_context,
            event_type=AuthEventType.LOGIN_ATTEMPT
        )
        event.risk_score = 0.95  # Very high risk
        
        # Process event (should trigger alert)
        service.alerting_engine.process_event(event)
        
        # Verify alert was generated and handled
        assert len(alerts_received) > 0
        alert = alerts_received[0]
        assert alert.severity in [AlertSeverity.HIGH, AlertSeverity.CRITICAL]
        assert "high" in alert.title.lower() or "risk" in alert.title.lower()


if __name__ == "__main__":
    pytest.main([__file__])