"""
Unit tests for the intelligence layer components.

This module tests the IntelligenceEngine, AnomalyDetector, BehavioralAnalyzer,
and RiskScorer components with mock data.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from typing import List, Dict, Any

from ai_karen_engine.auth.intelligence import (
    IntelligenceEngine,
    AnomalyDetector,
    BehavioralAnalyzer,
    RiskScorer,
    LoginAttempt,
    BehavioralPattern,
    AnomalyResult,
    IntelligenceResult,
)
from ai_karen_engine.auth.config import AuthConfig, IntelligenceConfig
from ai_karen_engine.auth.models import UserData, AuthEvent, AuthEventType


@pytest.fixture
def mock_config():
    """Create a mock authentication configuration."""
    config = AuthConfig()
    config.intelligence = IntelligenceConfig(
        enable_intelligent_auth=True,
        enable_anomaly_detection=True,
        enable_behavioral_analysis=True,
        risk_threshold_low=0.3,
        risk_threshold_medium=0.6,
        risk_threshold_high=0.8,
        min_training_samples=10,
        location_sensitivity=0.5,
        time_sensitivity=0.3,
        device_sensitivity=0.7,
    )
    return config


@pytest.fixture
def sample_user_data():
    """Create sample user data for testing."""
    return UserData(
        user_id="test-user-123",
        email="test@example.com",
        full_name="Test User",
        roles=["user"],
        tenant_id="default",
        is_verified=True,
        is_active=True,
        failed_login_attempts=0,
        created_at=datetime.utcnow() - timedelta(days=30),
        updated_at=datetime.utcnow(),
    )


@pytest.fixture
def sample_login_attempt():
    """Create sample login attempt for testing."""
    return LoginAttempt(
        user_id="test-user-123",
        email="test@example.com",
        ip_address="192.168.1.100",
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        timestamp=datetime.utcnow(),
        device_fingerprint="device-123",
        geolocation={"latitude": 40.7128, "longitude": -74.0060, "city": "New York"},
    )


@pytest.fixture
def sample_behavioral_pattern():
    """Create sample behavioral pattern for testing."""
    return BehavioralPattern(
        user_id="test-user-123",
        typical_login_hours=[9, 10, 11, 14, 15, 16],  # Business hours
        typical_locations=[
            {"latitude": 40.7128, "longitude": -74.0060, "city": "New York"},
            {"latitude": 40.7589, "longitude": -73.9851, "city": "New York Office"},
        ],
        typical_devices=["device-123", "device-456"],
        login_frequency={
            "monday": 5,
            "tuesday": 4,
            "wednesday": 6,
            "thursday": 5,
            "friday": 3,
            "saturday": 1,
            "sunday": 0,
        },
        average_session_duration=3600.0,  # 1 hour
        last_updated=datetime.utcnow(),
    )


@pytest.fixture
def sample_auth_events():
    """Create sample authentication events for testing."""
    base_time = datetime.utcnow() - timedelta(days=30)
    events = []
    
    # Create 20 successful login events over the past month
    for i in range(20):
        event_time = base_time + timedelta(days=i, hours=9 + (i % 8))  # Vary hours
        events.append(
            AuthEvent(
                event_type=AuthEventType.LOGIN_SUCCESS,
                timestamp=event_time,
                user_id="test-user-123",
                email="test@example.com",
                ip_address=f"192.168.1.{100 + (i % 10)}",
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                success=True,
                details={
                    "device_fingerprint": f"device-{123 + (i % 3)}",
                    "geolocation": {
                        "latitude": 40.7128 + (i % 3) * 0.01,
                        "longitude": -74.0060 + (i % 3) * 0.01,
                        "city": "New York"
                    }
                }
            )
        )
    
    return events


class TestAnomalyDetector:
    """Test cases for the AnomalyDetector class."""
    
    def test_init(self, mock_config):
        """Test AnomalyDetector initialization."""
        detector = AnomalyDetector(mock_config)
        assert detector.config == mock_config
        assert detector.logger is not None
    
    @pytest.mark.asyncio
    async def test_detect_anomalies_no_pattern(self, mock_config, sample_login_attempt):
        """Test anomaly detection with no behavioral pattern."""
        detector = AnomalyDetector(mock_config)
        result = await detector.detect_anomalies(sample_login_attempt)
        
        assert isinstance(result, AnomalyResult)
        assert not result.is_anomaly  # No pattern means no anomalies
        assert result.anomaly_score == 0.0
        assert len(result.anomaly_types) == 0
    
    @pytest.mark.asyncio
    async def test_detect_time_anomaly(self, mock_config, sample_login_attempt, sample_behavioral_pattern):
        """Test time-based anomaly detection."""
        detector = AnomalyDetector(mock_config)
        
        # Create attempt at unusual time (3 AM)
        unusual_attempt = LoginAttempt(
            user_id=sample_login_attempt.user_id,
            email=sample_login_attempt.email,
            ip_address=sample_login_attempt.ip_address,
            user_agent=sample_login_attempt.user_agent,
            timestamp=datetime.utcnow().replace(hour=3, minute=0, second=0, microsecond=0),
        )
        
        result = await detector.detect_anomalies(unusual_attempt, sample_behavioral_pattern)
        
        assert isinstance(result, AnomalyResult)
        # Should detect time anomaly since 3 AM is not in typical hours (9-16)
        assert "unusual_time" in result.anomaly_types
        assert result.anomaly_score > 0
    
    @pytest.mark.asyncio
    async def test_detect_location_anomaly(self, mock_config, sample_login_attempt, sample_behavioral_pattern):
        """Test location-based anomaly detection."""
        detector = AnomalyDetector(mock_config)
        
        # Create attempt from distant location (Los Angeles)
        distant_attempt = LoginAttempt(
            user_id=sample_login_attempt.user_id,
            email=sample_login_attempt.email,
            ip_address=sample_login_attempt.ip_address,
            user_agent=sample_login_attempt.user_agent,
            timestamp=sample_login_attempt.timestamp,
            geolocation={"latitude": 34.0522, "longitude": -118.2437, "city": "Los Angeles"},
        )
        
        result = await detector.detect_anomalies(distant_attempt, sample_behavioral_pattern)
        
        assert isinstance(result, AnomalyResult)
        # Should detect location anomaly since LA is far from NYC
        assert "unusual_location" in result.anomaly_types
        assert result.anomaly_score > 0
    
    @pytest.mark.asyncio
    async def test_detect_device_anomaly(self, mock_config, sample_login_attempt, sample_behavioral_pattern):
        """Test device-based anomaly detection."""
        detector = AnomalyDetector(mock_config)
        
        # Create attempt from unknown device
        unknown_device_attempt = LoginAttempt(
            user_id=sample_login_attempt.user_id,
            email=sample_login_attempt.email,
            ip_address=sample_login_attempt.ip_address,
            user_agent=sample_login_attempt.user_agent,
            timestamp=sample_login_attempt.timestamp,
            device_fingerprint="unknown-device-999",
        )
        
        result = await detector.detect_anomalies(unknown_device_attempt, sample_behavioral_pattern)
        
        assert isinstance(result, AnomalyResult)
        # Should detect device anomaly since device-999 is not in typical devices
        assert "unusual_device" in result.anomaly_types
        assert result.anomaly_score > 0
    
    @pytest.mark.asyncio
    async def test_detect_frequency_anomaly(self, mock_config, sample_behavioral_pattern):
        """Test frequency-based anomaly detection."""
        detector = AnomalyDetector(mock_config)
        
        # Create attempt on Sunday (user typically doesn't login on Sunday)
        # Find next Sunday
        now = datetime.utcnow()
        days_ahead = 6 - now.weekday()  # Sunday is 6
        if days_ahead <= 0:  # Target day already happened this week
            days_ahead += 7
        sunday_date = now + timedelta(days=days_ahead)
        
        sunday_attempt = LoginAttempt(
            user_id="test-user-123",
            email="test@example.com",
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0",
            timestamp=sunday_date.replace(hour=10),
        )
        
        result = await detector.detect_anomalies(sunday_attempt, sample_behavioral_pattern)
        
        assert isinstance(result, AnomalyResult)
        # Should detect frequency anomaly since user doesn't typically login on Sunday
        assert "unusual_frequency" in result.anomaly_types
        assert result.anomaly_score > 0
    
    def test_calculate_distance(self, mock_config):
        """Test distance calculation between coordinates."""
        detector = AnomalyDetector(mock_config)
        
        # Distance between NYC and LA (approximately 3944 km)
        nyc_lat, nyc_lon = 40.7128, -74.0060
        la_lat, la_lon = 34.0522, -118.2437
        
        distance = detector._calculate_distance(nyc_lat, nyc_lon, la_lat, la_lon)
        
        # Should be approximately 3944 km (allow 10% tolerance)
        assert 3500 < distance < 4400
    
    @pytest.mark.asyncio
    async def test_detect_anomalies_error_handling(self, mock_config, sample_login_attempt):
        """Test error handling in anomaly detection."""
        detector = AnomalyDetector(mock_config)
        
        # Create a malformed behavioral pattern that will cause errors
        bad_pattern = BehavioralPattern(user_id="test")
        bad_pattern.typical_login_hours = "invalid"  # Should be a list
        
        result = await detector.detect_anomalies(sample_login_attempt, bad_pattern)
        
        assert isinstance(result, AnomalyResult)
        assert not result.is_anomaly
        assert result.anomaly_score == 0.0
        assert "error" in result.details


class TestBehavioralAnalyzer:
    """Test cases for the BehavioralAnalyzer class."""
    
    def test_init(self, mock_config):
        """Test BehavioralAnalyzer initialization."""
        analyzer = BehavioralAnalyzer(mock_config)
        assert analyzer.config == mock_config
        assert analyzer.logger is not None
    
    @pytest.mark.asyncio
    async def test_analyze_behavior_insufficient_data(self, mock_config, sample_login_attempt):
        """Test behavioral analysis with insufficient data."""
        analyzer = BehavioralAnalyzer(mock_config)
        
        result = await analyzer.analyze_behavior(sample_login_attempt)
        
        assert result["status"] == "insufficient_data"
        assert result["analysis"] == {}
    
    @pytest.mark.asyncio
    async def test_analyze_behavior_success(self, mock_config, sample_login_attempt, sample_user_data, sample_auth_events):
        """Test successful behavioral analysis."""
        analyzer = BehavioralAnalyzer(mock_config)
        
        result = await analyzer.analyze_behavior(sample_login_attempt, sample_user_data, sample_auth_events)
        
        assert result["status"] == "success"
        assert "analysis" in result
        assert "pattern" in result
        
        analysis = result["analysis"]
        assert "time_analysis" in analysis
        assert "location_analysis" in analysis
        assert "device_analysis" in analysis
        assert "frequency_analysis" in analysis
        assert "pattern_summary" in analysis
    
    @pytest.mark.asyncio
    async def test_build_behavioral_pattern(self, mock_config, sample_auth_events):
        """Test building behavioral pattern from historical events."""
        analyzer = BehavioralAnalyzer(mock_config)
        
        pattern = await analyzer._build_behavioral_pattern("test-user-123", sample_auth_events)
        
        assert isinstance(pattern, BehavioralPattern)
        assert pattern.user_id == "test-user-123"
        assert len(pattern.typical_login_hours) > 0
        assert len(pattern.login_frequency) > 0
        assert len(pattern.typical_locations) > 0
        assert len(pattern.typical_devices) > 0
    
    def test_analyze_time_pattern(self, mock_config, sample_login_attempt, sample_behavioral_pattern):
        """Test time pattern analysis."""
        analyzer = BehavioralAnalyzer(mock_config)
        
        # Test with typical hour
        typical_attempt = LoginAttempt(
            user_id=sample_login_attempt.user_id,
            email=sample_login_attempt.email,
            ip_address=sample_login_attempt.ip_address,
            user_agent=sample_login_attempt.user_agent,
            timestamp=datetime.utcnow().replace(hour=10),  # 10 AM is typical
        )
        
        result = analyzer._analyze_time_pattern(typical_attempt, sample_behavioral_pattern)
        
        assert result["current_hour"] == 10
        assert result["is_typical_hour"] is True
        assert 10 in result["typical_hours"]
        assert result["hour_deviation"] == 0.0
    
    def test_analyze_location_pattern(self, mock_config, sample_login_attempt, sample_behavioral_pattern):
        """Test location pattern analysis."""
        analyzer = BehavioralAnalyzer(mock_config)
        
        result = analyzer._analyze_location_pattern(sample_login_attempt, sample_behavioral_pattern)
        
        assert "current_location" in result
        assert "is_typical_location" in result
        assert "typical_locations_count" in result
        assert result["typical_locations_count"] == len(sample_behavioral_pattern.typical_locations)
    
    def test_analyze_device_pattern(self, mock_config, sample_login_attempt, sample_behavioral_pattern):
        """Test device pattern analysis."""
        analyzer = BehavioralAnalyzer(mock_config)
        
        result = analyzer._analyze_device_pattern(sample_login_attempt, sample_behavioral_pattern)
        
        assert "device_fingerprint" in result
        assert "is_known_device" in result
        assert "known_devices_count" in result
        assert result["device_fingerprint"] == sample_login_attempt.device_fingerprint
        assert result["is_known_device"] is True  # device-123 is in typical devices
    
    def test_analyze_frequency_pattern(self, mock_config, sample_login_attempt, sample_behavioral_pattern):
        """Test frequency pattern analysis."""
        analyzer = BehavioralAnalyzer(mock_config)
        
        # Create a Monday attempt (weekday 0)
        monday_date = datetime.utcnow()
        while monday_date.weekday() != 0:  # Find next Monday
            monday_date += timedelta(days=1)
        
        monday_attempt = LoginAttempt(
            user_id=sample_login_attempt.user_id,
            email=sample_login_attempt.email,
            ip_address=sample_login_attempt.ip_address,
            user_agent=sample_login_attempt.user_agent,
            timestamp=monday_date,
        )
        
        result = analyzer._analyze_frequency_pattern(monday_attempt, sample_behavioral_pattern)
        
        assert "day_of_week" in result
        assert "typical_frequency" in result
        assert "frequency_ratio" in result
        assert "is_typical_day" in result
        assert result["day_of_week"] == "monday"
        assert result["is_typical_day"] is True  # Monday has frequency > 0
    
    def test_cluster_locations(self, mock_config):
        """Test location clustering."""
        analyzer = BehavioralAnalyzer(mock_config)
        
        locations = [
            {"latitude": 40.7128, "longitude": -74.0060},  # NYC
            {"latitude": 40.7589, "longitude": -73.9851},  # NYC nearby (< 10km)
            {"latitude": 34.0522, "longitude": -118.2437}, # LA (far away)
        ]
        
        clusters = analyzer._cluster_locations(locations)
        
        # Should have 2 clusters: NYC area and LA
        assert len(clusters) == 2
    
    def test_calculate_hour_deviation(self, mock_config):
        """Test hour deviation calculation."""
        analyzer = BehavioralAnalyzer(mock_config)
        
        typical_hours = [9, 10, 11, 14, 15, 16]
        
        # Test exact match
        deviation = analyzer._calculate_hour_deviation(10, typical_hours)
        assert deviation == 0.0
        
        # Test nearby hour
        deviation = analyzer._calculate_hour_deviation(12, typical_hours)
        assert deviation == 1.0  # 1 hour from 11
        
        # Test distant hour
        deviation = analyzer._calculate_hour_deviation(3, typical_hours)
        assert deviation == 6.0  # 6 hours from 9
    
    @pytest.mark.asyncio
    async def test_analyze_behavior_error_handling(self, mock_config, sample_login_attempt, sample_user_data):
        """Test error handling in behavioral analysis."""
        analyzer = BehavioralAnalyzer(mock_config)
        
        # Pass invalid events that will cause errors
        invalid_events = ["not_an_event"]
        
        result = await analyzer.analyze_behavior(sample_login_attempt, sample_user_data, invalid_events)
        
        assert result["status"] == "error"
        assert "error" in result


class TestRiskScorer:
    """Test cases for the RiskScorer class."""
    
    def test_init(self, mock_config):
        """Test RiskScorer initialization."""
        scorer = RiskScorer(mock_config)
        assert scorer.config == mock_config
        assert scorer.logger is not None
    
    def test_calculate_risk_score_low_risk(self, mock_config, sample_login_attempt, sample_user_data):
        """Test risk score calculation for low-risk scenario."""
        scorer = RiskScorer(mock_config)
        
        # Create low-risk scenario
        anomaly_result = AnomalyResult(is_anomaly=False, anomaly_score=0.0)
        behavioral_analysis = {"status": "success", "analysis": {}}
        
        risk_score, risk_level = scorer.calculate_risk_score(
            sample_login_attempt, anomaly_result, behavioral_analysis, sample_user_data
        )
        
        assert 0.0 <= risk_score <= 1.0
        assert risk_level in ["low", "medium", "high", "critical"]
        assert risk_score < mock_config.intelligence.risk_threshold_low
        assert risk_level == "low"
    
    def test_calculate_risk_score_high_risk(self, mock_config, sample_login_attempt):
        """Test risk score calculation for high-risk scenario."""
        scorer = RiskScorer(mock_config)
        
        # Create high-risk user data
        high_risk_user = UserData(
            user_id="test-user-123",
            email="test@example.com",
            is_active=False,  # Inactive account
            failed_login_attempts=5,  # Many failed attempts
            is_verified=False,  # Unverified account
        )
        
        # Create high-risk anomaly result
        anomaly_result = AnomalyResult(
            is_anomaly=True,
            anomaly_score=0.9,
            anomaly_types=["unusual_location", "unusual_device", "unusual_time"],
            confidence=0.95
        )
        
        behavioral_analysis = {
            "status": "success",
            "analysis": {
                "time_analysis": {"is_typical_hour": False, "hour_deviation": 8},
                "location_analysis": {"is_typical_location": False, "min_distance_km": 5000},
                "device_analysis": {"is_known_device": False},
                "frequency_analysis": {"is_typical_day": False},
            }
        }
        
        risk_score, risk_level = scorer.calculate_risk_score(
            sample_login_attempt, anomaly_result, behavioral_analysis, high_risk_user
        )
        
        assert 0.0 <= risk_score <= 1.0
        assert risk_score > mock_config.intelligence.risk_threshold_medium
        assert risk_level in ["high", "critical"]
    
    def test_calculate_behavioral_risk(self, mock_config):
        """Test behavioral risk calculation."""
        scorer = RiskScorer(mock_config)
        
        # High-risk behavioral analysis
        high_risk_analysis = {
            "time_analysis": {"is_typical_hour": False, "hour_deviation": 10},
            "location_analysis": {"is_typical_location": False, "min_distance_km": 1000},
            "device_analysis": {"is_known_device": False},
            "frequency_analysis": {"is_typical_day": False},
        }
        
        risk = scorer._calculate_behavioral_risk(high_risk_analysis)
        assert 0.0 <= risk <= 1.0
        assert risk > 0.0  # Should have some risk
        
        # Low-risk behavioral analysis
        low_risk_analysis = {
            "time_analysis": {"is_typical_hour": True, "hour_deviation": 0},
            "location_analysis": {"is_typical_location": True},
            "device_analysis": {"is_known_device": True},
            "frequency_analysis": {"is_typical_day": True},
        }
        
        risk = scorer._calculate_behavioral_risk(low_risk_analysis)
        assert risk == 0.0  # Should have no risk
    
    def test_calculate_history_risk(self, mock_config, sample_user_data):
        """Test history-based risk calculation."""
        scorer = RiskScorer(mock_config)
        
        # Low-risk user
        risk = scorer._calculate_history_risk(sample_user_data)
        assert risk == 0.0  # Clean user should have no risk
        
        # High-risk user
        high_risk_user = UserData(
            user_id="test-user-123",
            email="test@example.com",
            is_active=False,
            failed_login_attempts=10,
            is_verified=False,
            locked_until=datetime.utcnow() + timedelta(hours=1),
        )
        
        risk = scorer._calculate_history_risk(high_risk_user)
        assert risk > 0.5  # Should have high risk
        assert risk <= 1.0
    
    def test_calculate_context_risk(self, mock_config, sample_login_attempt):
        """Test context-based risk calculation."""
        scorer = RiskScorer(mock_config)
        
        # Normal context
        risk = scorer._calculate_context_risk(sample_login_attempt)
        assert 0.0 <= risk <= 1.0
        
        # Suspicious context
        suspicious_attempt = LoginAttempt(
            user_id="test-user-123",
            email="test@example.com",
            ip_address="127.0.0.1",  # Suspicious IP
            user_agent="curl/7.68.0",  # Bot user agent
            timestamp=datetime.utcnow().replace(hour=2),  # Late night
        )
        
        risk = scorer._calculate_context_risk(suspicious_attempt)
        assert risk > 0.0  # Should have some risk
    
    def test_is_suspicious_ip(self, mock_config):
        """Test suspicious IP detection."""
        scorer = RiskScorer(mock_config)
        
        assert scorer._is_suspicious_ip("127.0.0.1") is True
        assert scorer._is_suspicious_ip("0.0.0.0") is True
        assert scorer._is_suspicious_ip("192.168.1.100") is False
    
    def test_is_suspicious_user_agent(self, mock_config):
        """Test suspicious user agent detection."""
        scorer = RiskScorer(mock_config)
        
        assert scorer._is_suspicious_user_agent("") is True
        assert scorer._is_suspicious_user_agent("curl/7.68.0") is True
        assert scorer._is_suspicious_user_agent("Googlebot/2.1") is True
        assert scorer._is_suspicious_user_agent("Mozilla/5.0 (Windows NT 10.0; Win64; x64)") is False
    
    def test_calculate_risk_score_error_handling(self, mock_config, sample_login_attempt):
        """Test error handling in risk score calculation."""
        scorer = RiskScorer(mock_config)
        
        # Pass invalid data that will cause errors
        invalid_anomaly = "not_an_anomaly_result"
        
        risk_score, risk_level = scorer.calculate_risk_score(
            sample_login_attempt, invalid_anomaly, None, None
        )
        
        # Should return default values on error
        assert risk_score == 0.5
        assert risk_level == "medium"


class TestIntelligenceEngine:
    """Test cases for the IntelligenceEngine class."""
    
    def test_init(self, mock_config):
        """Test IntelligenceEngine initialization."""
        engine = IntelligenceEngine(mock_config)
        assert engine.config == mock_config
        assert isinstance(engine.anomaly_detector, AnomalyDetector)
        assert isinstance(engine.behavioral_analyzer, BehavioralAnalyzer)
        assert isinstance(engine.risk_scorer, RiskScorer)
        assert not engine._initialized
    
    @pytest.mark.asyncio
    async def test_initialize(self, mock_config):
        """Test intelligence engine initialization."""
        engine = IntelligenceEngine(mock_config)
        
        await engine.initialize()
        
        assert engine._initialized is True
        
        # Should not reinitialize
        await engine.initialize()
        assert engine._initialized is True
    
    @pytest.mark.asyncio
    async def test_analyze_login_attempt_success(self, mock_config, sample_login_attempt, sample_user_data, sample_auth_events):
        """Test successful login attempt analysis."""
        engine = IntelligenceEngine(mock_config)
        
        result = await engine.analyze_login_attempt(sample_login_attempt, sample_user_data, sample_auth_events)
        
        assert isinstance(result, IntelligenceResult)
        assert 0.0 <= result.risk_score <= 1.0
        assert result.risk_level in ["low", "medium", "high", "critical"]
        assert isinstance(result.should_block, bool)
        assert isinstance(result.recommendations, list)
        assert result.processing_time_ms > 0
    
    @pytest.mark.asyncio
    async def test_analyze_login_attempt_no_data(self, mock_config, sample_login_attempt):
        """Test login attempt analysis with no historical data."""
        engine = IntelligenceEngine(mock_config)
        
        result = await engine.analyze_login_attempt(sample_login_attempt)
        
        assert isinstance(result, IntelligenceResult)
        assert 0.0 <= result.risk_score <= 1.0
        assert result.risk_level in ["low", "medium", "high", "critical"]
        assert isinstance(result.should_block, bool)
    
    @pytest.mark.asyncio
    async def test_calculate_risk_score(self, mock_config, sample_user_data):
        """Test risk score calculation."""
        engine = IntelligenceEngine(mock_config)
        
        context = {
            "ip_address": "192.168.1.100",
            "user_agent": "Mozilla/5.0",
            "device_fingerprint": "device-123",
            "geolocation": {"latitude": 40.7128, "longitude": -74.0060},
        }
        
        risk_score = await engine.calculate_risk_score(sample_user_data, context)
        
        assert 0.0 <= risk_score <= 1.0
    
    def test_should_block_attempt_high_risk(self, mock_config):
        """Test blocking decision for high-risk attempts."""
        engine = IntelligenceEngine(mock_config)
        
        # High risk score should block
        should_block = engine._should_block_attempt(0.9, "critical", None)
        assert should_block is True
        
        # Multiple high-confidence anomalies should block
        anomaly_result = AnomalyResult(
            is_anomaly=True,
            anomaly_score=0.7,
            anomaly_types=["unusual_location", "unusual_device"],
            confidence=0.9
        )
        should_block = engine._should_block_attempt(0.5, "medium", anomaly_result)
        assert should_block is True
    
    def test_should_block_attempt_low_risk(self, mock_config):
        """Test blocking decision for low-risk attempts."""
        engine = IntelligenceEngine(mock_config)
        
        # Low risk score should not block
        should_block = engine._should_block_attempt(0.2, "low", None)
        assert should_block is False
        
        # Single low-confidence anomaly should not block
        anomaly_result = AnomalyResult(
            is_anomaly=True,
            anomaly_score=0.3,
            anomaly_types=["unusual_time"],
            confidence=0.4
        )
        should_block = engine._should_block_attempt(0.3, "low", anomaly_result)
        assert should_block is False
    
    def test_generate_recommendations(self, mock_config):
        """Test recommendation generation."""
        engine = IntelligenceEngine(mock_config)
        
        # Critical risk recommendations
        recommendations = engine._generate_recommendations("critical", "critical", None, None)
        assert len(recommendations) > 0
        assert any("Block" in rec for rec in recommendations)
        
        # Anomaly-based recommendations
        anomaly_result = AnomalyResult(
            is_anomaly=True,
            anomaly_score=0.7,
            anomaly_types=["unusual_location", "unusual_device"],
            confidence=0.8
        )
        recommendations = engine._generate_recommendations("medium", "medium", anomaly_result, None)
        assert len(recommendations) > 0
        assert any("location" in rec.lower() for rec in recommendations)
        assert any("device" in rec.lower() for rec in recommendations)
    
    @pytest.mark.asyncio
    async def test_analyze_login_attempt_error_handling(self, mock_config):
        """Test error handling in login attempt analysis."""
        engine = IntelligenceEngine(mock_config)
        
        # Create invalid login attempt that will cause errors
        invalid_attempt = "not_a_login_attempt"
        
        with patch.object(engine.behavioral_analyzer, 'analyze_behavior', side_effect=Exception("Test error")):
            result = await engine.analyze_login_attempt(invalid_attempt)
        
        assert isinstance(result, IntelligenceResult)
        assert result.risk_score == 0.5  # Default risk score on error
        assert result.risk_level == "medium"
        assert not result.should_block
        assert len(result.recommendations) > 0
        assert "failed" in result.recommendations[0].lower()
    
    @pytest.mark.asyncio
    async def test_calculate_risk_score_error_handling(self, mock_config, sample_user_data):
        """Test error handling in risk score calculation."""
        engine = IntelligenceEngine(mock_config)
        
        # Create invalid context that will cause errors
        invalid_context = "not_a_context"
        
        risk_score = await engine.calculate_risk_score(sample_user_data, invalid_context)
        
        # Should return default risk score on error
        assert risk_score == 0.5


class TestDataModels:
    """Test cases for intelligence data models."""
    
    def test_login_attempt_to_dict(self, sample_login_attempt):
        """Test LoginAttempt serialization."""
        data = sample_login_attempt.to_dict()
        
        assert isinstance(data, dict)
        assert data["user_id"] == sample_login_attempt.user_id
        assert data["email"] == sample_login_attempt.email
        assert data["ip_address"] == sample_login_attempt.ip_address
        assert data["timestamp"] == sample_login_attempt.timestamp.isoformat()
    
    def test_behavioral_pattern_to_dict(self, sample_behavioral_pattern):
        """Test BehavioralPattern serialization."""
        data = sample_behavioral_pattern.to_dict()
        
        assert isinstance(data, dict)
        assert data["user_id"] == sample_behavioral_pattern.user_id
        assert data["typical_login_hours"] == sample_behavioral_pattern.typical_login_hours
        assert data["last_updated"] == sample_behavioral_pattern.last_updated.isoformat()
    
    def test_anomaly_result_to_dict(self):
        """Test AnomalyResult serialization."""
        result = AnomalyResult(
            is_anomaly=True,
            anomaly_score=0.7,
            anomaly_types=["unusual_location"],
            confidence=0.8,
            details={"test": "data"}
        )
        
        data = result.to_dict()
        
        assert isinstance(data, dict)
        assert data["is_anomaly"] is True
        assert data["anomaly_score"] == 0.7
        assert data["anomaly_types"] == ["unusual_location"]
        assert data["confidence"] == 0.8
        assert data["details"] == {"test": "data"}
    
    def test_intelligence_result_to_dict(self):
        """Test IntelligenceResult serialization."""
        anomaly_result = AnomalyResult(is_anomaly=False, anomaly_score=0.0)
        
        result = IntelligenceResult(
            risk_score=0.3,
            risk_level="low",
            should_block=False,
            anomaly_result=anomaly_result,
            behavioral_analysis={"test": "data"},
            recommendations=["test recommendation"],
            processing_time_ms=100.5
        )
        
        data = result.to_dict()
        
        assert isinstance(data, dict)
        assert data["risk_score"] == 0.3
        assert data["risk_level"] == "low"
        assert data["should_block"] is False
        assert data["anomaly_result"] is not None
        assert data["behavioral_analysis"] == {"test": "data"}
        assert data["recommendations"] == ["test recommendation"]
        assert data["processing_time_ms"] == 100.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])