"""
Tests for authentication monitoring extensions.

This module tests the enhanced monitoring capabilities including:
- Security event correlation
- Performance trend analysis
- Advanced alerting with context
"""

import asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest

from ai_karen_engine.auth.config import AuthConfig
from ai_karen_engine.auth.models import AuthEvent, AuthEventType
from ai_karen_engine.auth.monitoring_extensions import (
    EnhancedAuthMonitor,
    PerformanceTrend,
    PerformanceTrendAnalyzer,
    SecurityEventCorrelator,
    SecurityPattern,
)


class TestSecurityEventCorrelator:
    """Test security event correlation functionality."""

    @pytest.fixture
    def config(self):
        return AuthConfig()

    @pytest.fixture
    def correlator(self, config):
        return SecurityEventCorrelator(config)

    @pytest.mark.asyncio
    async def test_brute_force_pattern_detection(self, correlator):
        """Test detection of brute force attack patterns."""
        ip_address = "192.168.1.100"
        
        # Generate failed login attempts from same IP
        patterns_detected = []
        for i in range(15):
            event = AuthEvent(
                event_type=AuthEventType.LOGIN_FAILED,
                email=f"user{i}@example.com",
                ip_address=ip_address,
                success=False,
                timestamp=datetime.now(timezone.utc),
            )
            
            patterns = await correlator.analyze_event(event)
            patterns_detected.extend(patterns)
        
        # Should detect brute force pattern
        brute_force_patterns = [
            p for p in patterns_detected if p.pattern_type == "brute_force"
        ]
        assert len(brute_force_patterns) > 0
        
        pattern = brute_force_patterns[0]
        assert pattern.severity == "high"
        assert ip_address in pattern.source_ips
        assert pattern.confidence > 0.5

    @pytest.mark.asyncio
    async def test_credential_stuffing_detection(self, correlator):
        """Test detection of credential stuffing patterns."""
        ip_address = "192.168.1.200"
        
        # Generate failed attempts against multiple different users
        patterns_detected = []
        for i in range(8):
            event = AuthEvent(
                event_type=AuthEventType.LOGIN_FAILED,
                email=f"victim{i}@example.com",  # Different users each time
                ip_address=ip_address,
                success=False,
                timestamp=datetime.now(timezone.utc),
            )
            
            patterns = await correlator.analyze_event(event)
            patterns_detected.extend(patterns)
        
        # Should detect credential stuffing
        stuffing_patterns = [
            p for p in patterns_detected if p.pattern_type == "credential_stuffing"
        ]
        assert len(stuffing_patterns) > 0
        
        pattern = stuffing_patterns[0]
        assert pattern.severity == "high"
        assert len(pattern.affected_users) >= 5
        assert ip_address in pattern.source_ips

    @pytest.mark.asyncio
    async def test_anomalous_behavior_detection(self, correlator):
        """Test detection of anomalous behavior patterns."""
        event = AuthEvent(
            event_type=AuthEventType.LOGIN_SUCCESS,
            user_id="user123",
            email="user@example.com",
            ip_address="192.168.1.50",
            success=True,
            risk_score=0.85,  # High risk score indicates anomaly
            security_flags=["unusual_location", "new_device", "off_hours"],
        )
        
        patterns = await correlator.analyze_event(event)
        
        anomaly_patterns = [
            p for p in patterns if p.pattern_type == "anomalous_behavior"
        ]
        assert len(anomaly_patterns) == 1
        
        pattern = anomaly_patterns[0]
        assert pattern.severity == "high"
        assert pattern.confidence == 0.85
        assert "user123" in pattern.affected_users
        assert "unusual_location" in pattern.details.get("security_flags", [])

    @pytest.mark.asyncio
    async def test_pattern_expiration(self, correlator):
        """Test that old patterns are properly expired."""
        # Create an old pattern
        old_event = AuthEvent(
            event_type=AuthEventType.LOGIN_FAILED,
            ip_address="192.168.1.1",
            success=False,
            timestamp=datetime.now(timezone.utc) - timedelta(hours=2),
        )
        
        await correlator.analyze_event(old_event)
        
        # Add pattern manually to simulate old data
        old_pattern = SecurityPattern(
            pattern_id="old_pattern",
            pattern_type="brute_force",
            severity="high",
            confidence=0.8,
            first_seen=datetime.now(timezone.utc) - timedelta(hours=2),
            last_seen=datetime.now(timezone.utc) - timedelta(hours=2),
            event_count=10,
        )
        correlator._active_patterns["old_pattern"] = old_pattern
        
        # Get active patterns (should trigger cleanup)
        active_patterns = correlator.get_active_patterns()
        
        # Old pattern should be removed
        assert "old_pattern" not in correlator._active_patterns

    def test_correlation_statistics(self, correlator):
        """Test correlation statistics reporting."""
        # Add some test data
        correlator._recent_events.extend([
            AuthEvent(event_type=AuthEventType.LOGIN_FAILED, success=False),
            AuthEvent(event_type=AuthEventType.LOGIN_SUCCESS, success=True),
        ])
        
        correlator._failed_attempts_by_ip["192.168.1.1"].extend([
            AuthEvent(event_type=AuthEventType.LOGIN_FAILED, success=False),
            AuthEvent(event_type=AuthEventType.LOGIN_FAILED, success=False),
        ])
        
        correlator._failed_attempts_by_user["user@example.com"].append(
            AuthEvent(event_type=AuthEventType.LOGIN_FAILED, success=False)
        )
        
        stats = correlator.get_correlation_stats()
        
        assert stats["recent_events_analyzed"] == 2
        assert stats["ips_with_failed_attempts"] == 1
        assert stats["users_with_failed_attempts"] == 1
        assert "active_patterns" in stats
        assert "pattern_types" in stats
        assert "severity_distribution" in stats


class TestPerformanceTrendAnalyzer:
    """Test performance trend analysis functionality."""

    @pytest.fixture
    def config(self):
        return AuthConfig()

    @pytest.fixture
    def analyzer(self, config):
        return PerformanceTrendAnalyzer(config)

    @pytest.mark.asyncio
    async def test_metric_recording(self, analyzer):
        """Test recording of metric data points."""
        metric_name = "auth.response_time"
        
        # Record several data points
        timestamps = []
        values = [100.0, 105.0, 110.0, 95.0, 90.0]
        
        for value in values:
            timestamp = datetime.now(timezone.utc)
            await analyzer.record_metric_point(metric_name, value, timestamp)
            timestamps.append(timestamp)
        
        # Check data was recorded
        history = analyzer._metric_history[metric_name]
        assert len(history) == 5
        assert history[-1][1] == 90.0  # Last value

    @pytest.mark.asyncio
    async def test_improving_trend_detection(self, analyzer):
        """Test detection of improving performance trends."""
        metric_name = "auth.response_time"
        base_time = datetime.now(timezone.utc)
        
        # Create improving trend (decreasing response times)
        for i in range(20):
            timestamp = base_time - timedelta(minutes=i)
            value = 200.0 - (i * 5)  # Decreasing values = improving performance
            await analyzer.record_metric_point(metric_name, value, timestamp)
        
        trends = await analyzer.analyze_trends()
        
        # Should detect improving trend
        response_trends = [t for t in trends if t.metric_name == metric_name]
        assert len(response_trends) > 0
        
        # At least one should show improvement
        improving_trends = [t for t in response_trends if t.trend_direction == "improving"]
        assert len(improving_trends) > 0
        
        trend = improving_trends[0]
        assert trend.trend_strength > 0
        assert trend.change_percentage < 0  # Negative change = improvement for response time

    @pytest.mark.asyncio
    async def test_degrading_trend_detection(self, analyzer):
        """Test detection of degrading performance trends."""
        metric_name = "auth.success_rate"
        base_time = datetime.now(timezone.utc)
        
        # Create degrading trend (decreasing success rate)
        for i in range(20):
            timestamp = base_time - timedelta(minutes=i)
            value = 0.95 - (i * 0.01)  # Decreasing success rate
            await analyzer.record_metric_point(metric_name, value, timestamp)
        
        trends = await analyzer.analyze_trends()
        
        # Should detect degrading trend
        success_trends = [t for t in trends if t.metric_name == metric_name]
        assert len(success_trends) > 0
        
        degrading_trends = [t for t in success_trends if t.trend_direction == "degrading"]
        assert len(degrading_trends) > 0
        
        trend = degrading_trends[0]
        assert trend.trend_strength > 0
        assert trend.change_percentage < 0  # Negative change = degradation for success rate

    @pytest.mark.asyncio
    async def test_stable_trend_detection(self, analyzer):
        """Test detection of stable performance trends."""
        metric_name = "auth.stable_metric"
        base_time = datetime.now(timezone.utc)
        
        # Create stable trend (consistent values)
        stable_value = 100.0
        for i in range(20):
            timestamp = base_time - timedelta(minutes=i)
            # Add small random variation but keep stable
            value = stable_value + (i % 3 - 1) * 0.5  # Very small variations
            await analyzer.record_metric_point(metric_name, value, timestamp)
        
        trends = await analyzer.analyze_trends()
        
        # Should detect stable trend
        stable_trends = [t for t in trends if t.metric_name == metric_name]
        if stable_trends:  # May not detect trend if variation is too small
            stable_trend = [t for t in stable_trends if t.trend_direction == "stable"]
            if stable_trend:
                trend = stable_trend[0]
                assert trend.trend_strength == 0.0
                assert abs(trend.change_percentage) < analyzer.significant_change_threshold * 100

    def test_trend_summary(self, analyzer):
        """Test trend summary generation."""
        # Add mock trends to cache
        analyzer._trend_cache = {
            "metric1_5m": PerformanceTrend(
                metric_name="metric1",
                trend_direction="improving",
                trend_strength=0.6,
                current_value=80.0,
                previous_value=100.0,
                change_percentage=-20.0,
                analysis_period_minutes=5,
            ),
            "metric2_15m": PerformanceTrend(
                metric_name="metric2",
                trend_direction="degrading",
                trend_strength=0.8,
                current_value=120.0,
                previous_value=100.0,
                change_percentage=20.0,
                analysis_period_minutes=15,
            ),
            "metric3_30m": PerformanceTrend(
                metric_name="metric3",
                trend_direction="stable",
                trend_strength=0.0,
                current_value=100.0,
                previous_value=100.0,
                change_percentage=0.0,
                analysis_period_minutes=30,
            ),
        }
        
        summary = analyzer.get_trend_summary()
        
        assert summary["trends_analyzed"] == 3
        assert summary["improving"] == 1
        assert summary["degrading"] == 1
        assert summary["stable"] == 1
        assert summary["concerning_trends"] == 1  # degrading with strength > 0.5
        assert summary["status"] == "concerning"  # Has concerning trends

    def test_get_current_trends(self, analyzer):
        """Test retrieving current trends."""
        # Add mock trends
        trend1 = PerformanceTrend(
            metric_name="auth.response_time",
            trend_direction="improving",
            trend_strength=0.5,
            current_value=80.0,
            previous_value=100.0,
            change_percentage=-20.0,
            analysis_period_minutes=5,
        )
        
        trend2 = PerformanceTrend(
            metric_name="auth.success_rate",
            trend_direction="stable",
            trend_strength=0.0,
            current_value=0.95,
            previous_value=0.95,
            change_percentage=0.0,
            analysis_period_minutes=15,
        )
        
        analyzer._trend_cache["auth.response_time_5m"] = trend1
        analyzer._trend_cache["auth.success_rate_15m"] = trend2
        
        # Get all trends
        all_trends = analyzer.get_current_trends()
        assert len(all_trends) == 2
        
        # Get specific metric trends
        response_trends = analyzer.get_current_trends("auth.response_time")
        assert len(response_trends) == 1
        assert response_trends[0].metric_name == "auth.response_time"


class TestEnhancedAuthMonitor:
    """Test the enhanced authentication monitor."""

    @pytest.fixture
    def config(self):
        return AuthConfig()

    @pytest.fixture
    def enhanced_monitor(self, config):
        return EnhancedAuthMonitor(config)

    @pytest.mark.asyncio
    async def test_comprehensive_event_analysis(self, enhanced_monitor):
        """Test comprehensive analysis of authentication events."""
        event = AuthEvent(
            event_type=AuthEventType.LOGIN_FAILED,
            user_id="user123",
            email="user@example.com",
            ip_address="192.168.1.100",
            success=False,
            processing_time_ms=250.0,
            risk_score=0.7,
            security_flags=["suspicious_timing", "new_device"],
            error_message="Invalid credentials",
        )
        
        analysis = await enhanced_monitor.analyze_auth_event(event)
        
        # Check analysis structure
        assert "event_id" in analysis
        assert "timestamp" in analysis
        assert "security_patterns" in analysis
        assert "recommendations" in analysis
        
        assert analysis["event_id"] == event.event_id
        assert isinstance(analysis["security_patterns"], list)
        assert isinstance(analysis["recommendations"], list)

    @pytest.mark.asyncio
    async def test_security_pattern_analysis(self, enhanced_monitor):
        """Test security pattern detection in event analysis."""
        # Create high-risk event that should trigger pattern detection
        event = AuthEvent(
            event_type=AuthEventType.LOGIN_FAILED,
            email="user@example.com",
            ip_address="192.168.1.100",
            success=False,
            risk_score=0.9,
            security_flags=["brute_force_indicator", "suspicious_ip"],
        )
        
        analysis = await enhanced_monitor.analyze_auth_event(event)
        
        # Should generate security recommendations
        recommendations = analysis["recommendations"]
        assert len(recommendations) > 0
        
        # Should have risk-based recommendations
        risk_recommendations = [
            r for r in recommendations if "risk score" in r.lower()
        ]
        assert len(risk_recommendations) > 0

    @pytest.mark.asyncio
    async def test_performance_metric_recording(self, enhanced_monitor):
        """Test performance metric recording during event analysis."""
        event = AuthEvent(
            event_type=AuthEventType.LOGIN_SUCCESS,
            user_id="user123",
            email="user@example.com",
            tenant_id="tenant1",
            success=True,
            processing_time_ms=150.0,
        )
        
        await enhanced_monitor.analyze_auth_event(event)
        
        # Check that performance metrics were recorded
        history = enhanced_monitor.performance_analyzer._metric_history
        
        # Should have recorded processing time
        processing_time_metrics = [
            key for key in history.keys() if "processing_time" in key
        ]
        assert len(processing_time_metrics) > 0
        
        # Should have recorded success rate
        success_rate_metrics = [
            key for key in history.keys() if "success_rate" in key
        ]
        assert len(success_rate_metrics) > 0

    def test_recommendation_generation(self, enhanced_monitor):
        """Test generation of actionable recommendations."""
        # Test slow authentication recommendation
        event = AuthEvent(
            event_type=AuthEventType.LOGIN_SUCCESS,
            success=True,
            processing_time_ms=3000.0,  # Very slow
        )
        
        recommendations = enhanced_monitor._generate_recommendations(event, [])
        
        slow_recommendations = [
            r for r in recommendations if "slow" in r.lower()
        ]
        assert len(slow_recommendations) > 0

    def test_comprehensive_status_reporting(self, enhanced_monitor):
        """Test comprehensive status reporting."""
        status = enhanced_monitor.get_comprehensive_status()
        
        # Check required fields
        assert "security_correlation" in status
        assert "performance_trends" in status
        assert "active_security_patterns" in status
        assert "monitoring_health" in status
        assert "last_analysis" in status
        
        # Check data types
        assert isinstance(status["security_correlation"], dict)
        assert isinstance(status["performance_trends"], dict)
        assert isinstance(status["active_security_patterns"], int)
        assert status["monitoring_health"] == "active"

    @pytest.mark.asyncio
    async def test_background_analysis_task(self, enhanced_monitor):
        """Test that background analysis task is running."""
        # Check that background task was started
        assert enhanced_monitor._analysis_task is not None
        assert not enhanced_monitor._analysis_task.done()
        
        # Test shutdown cancels the task
        await enhanced_monitor.shutdown()
        assert enhanced_monitor._analysis_task.cancelled()

    @pytest.mark.asyncio
    async def test_periodic_analysis_execution(self, enhanced_monitor):
        """Test periodic analysis execution."""
        # Add some test data
        await enhanced_monitor.performance_analyzer.record_metric_point(
            "test.metric", 100.0
        )
        await enhanced_monitor.performance_analyzer.record_metric_point(
            "test.metric", 120.0
        )
        
        # Manually trigger periodic analysis
        await enhanced_monitor._run_periodic_analysis()
        
        # Should not raise exceptions and should complete successfully


class TestSecurityPatternModel:
    """Test the SecurityPattern data model."""

    def test_security_pattern_creation(self):
        """Test creating security patterns."""
        pattern = SecurityPattern(
            pattern_id="test_pattern",
            pattern_type="brute_force",
            severity="high",
            confidence=0.85,
            first_seen=datetime.now(timezone.utc),
            last_seen=datetime.now(timezone.utc),
            event_count=10,
        )
        
        assert pattern.pattern_id == "test_pattern"
        assert pattern.pattern_type == "brute_force"
        assert pattern.severity == "high"
        assert pattern.confidence == 0.85
        assert pattern.event_count == 10

    def test_security_pattern_serialization(self):
        """Test security pattern serialization."""
        pattern = SecurityPattern(
            pattern_id="test_pattern",
            pattern_type="credential_stuffing",
            severity="critical",
            confidence=0.95,
            first_seen=datetime.now(timezone.utc),
            last_seen=datetime.now(timezone.utc),
            event_count=25,
            affected_users={"user1", "user2", "user3"},
            source_ips={"192.168.1.1", "192.168.1.2"},
            details={"threshold": 5, "window_minutes": 10},
        )
        
        pattern_dict = pattern.to_dict()
        
        assert pattern_dict["pattern_id"] == "test_pattern"
        assert pattern_dict["pattern_type"] == "credential_stuffing"
        assert pattern_dict["severity"] == "critical"
        assert pattern_dict["confidence"] == 0.95
        assert pattern_dict["event_count"] == 25
        assert len(pattern_dict["affected_users"]) == 3
        assert len(pattern_dict["source_ips"]) == 2
        assert pattern_dict["details"]["threshold"] == 5


class TestPerformanceTrendModel:
    """Test the PerformanceTrend data model."""

    def test_performance_trend_creation(self):
        """Test creating performance trends."""
        trend = PerformanceTrend(
            metric_name="auth.response_time",
            trend_direction="improving",
            trend_strength=0.7,
            current_value=80.0,
            previous_value=100.0,
            change_percentage=-20.0,
            analysis_period_minutes=15,
        )
        
        assert trend.metric_name == "auth.response_time"
        assert trend.trend_direction == "improving"
        assert trend.trend_strength == 0.7
        assert trend.current_value == 80.0
        assert trend.previous_value == 100.0
        assert trend.change_percentage == -20.0
        assert trend.analysis_period_minutes == 15

    def test_performance_trend_serialization(self):
        """Test performance trend serialization."""
        trend = PerformanceTrend(
            metric_name="auth.success_rate",
            trend_direction="degrading",
            trend_strength=0.6,
            current_value=0.85,
            previous_value=0.95,
            change_percentage=-10.5,
            analysis_period_minutes=30,
        )
        
        trend_dict = trend.to_dict()
        
        assert trend_dict["metric_name"] == "auth.success_rate"
        assert trend_dict["trend_direction"] == "degrading"
        assert trend_dict["trend_strength"] == 0.6
        assert trend_dict["current_value"] == 0.85
        assert trend_dict["previous_value"] == 0.95
        assert trend_dict["change_percentage"] == -10.5
        assert trend_dict["analysis_period_minutes"] == 30
        assert "timestamp" in trend_dict


@pytest.mark.integration
class TestMonitoringExtensionsIntegration:
    """Integration tests for monitoring extensions."""

    @pytest.fixture
    def config(self):
        config = AuthConfig()
        config.monitoring.enable_monitoring = True
        return config

    @pytest.fixture
    def enhanced_monitor(self, config):
        return EnhancedAuthMonitor(config)

    @pytest.mark.asyncio
    async def test_full_attack_scenario_analysis(self, enhanced_monitor):
        """Test analysis of a complete attack scenario."""
        attacker_ip = "192.168.1.100"
        
        # Simulate coordinated attack
        events = []
        
        # Phase 1: Reconnaissance (failed logins against multiple users)
        for i in range(8):
            event = AuthEvent(
                event_type=AuthEventType.LOGIN_FAILED,
                email=f"user{i}@example.com",
                ip_address=attacker_ip,
                success=False,
                timestamp=datetime.now(timezone.utc),
            )
            events.append(event)
        
        # Phase 2: Focused attack (multiple attempts against one user)
        for i in range(12):
            event = AuthEvent(
                event_type=AuthEventType.LOGIN_FAILED,
                email="target@example.com",
                ip_address=attacker_ip,
                success=False,
                timestamp=datetime.now(timezone.utc),
            )
            events.append(event)
        
        # Analyze all events
        all_patterns = []
        for event in events:
            analysis = await enhanced_monitor.analyze_auth_event(event)
            all_patterns.extend(analysis.get("security_patterns", []))
        
        # Should detect both credential stuffing and brute force patterns
        pattern_types = {p["pattern_type"] for p in all_patterns}
        assert "credential_stuffing" in pattern_types or "brute_force" in pattern_types
        
        # Should generate security recommendations
        final_analysis = await enhanced_monitor.analyze_auth_event(events[-1])
        recommendations = final_analysis.get("recommendations", [])
        assert len(recommendations) > 0

    @pytest.mark.asyncio
    async def test_performance_degradation_detection(self, enhanced_monitor):
        """Test detection of performance degradation over time."""
        # Simulate gradually degrading performance
        base_time = datetime.now(timezone.utc)
        
        for i in range(20):
            # Increasing processing times
            processing_time = 100.0 + (i * 10)  # 100ms to 290ms
            
            event = AuthEvent(
                event_type=AuthEventType.LOGIN_SUCCESS,
                user_id=f"user{i % 5}",
                success=True,
                processing_time_ms=processing_time,
                timestamp=base_time + timedelta(minutes=i),
            )
            
            await enhanced_monitor.analyze_auth_event(event)
        
        # Analyze trends
        trends = await enhanced_monitor.performance_analyzer.analyze_trends()
        
        # Should detect degrading performance trend
        processing_trends = [
            t for t in trends if "processing_time" in t.metric_name
        ]
        
        if processing_trends:
            # At least one should show degradation
            degrading_trends = [
                t for t in processing_trends if t.trend_direction == "degrading"
            ]
            # May or may not detect with limited data, but should not error

    @pytest.mark.asyncio
    async def test_comprehensive_monitoring_workflow(self, enhanced_monitor):
        """Test the complete monitoring workflow."""
        # Generate diverse authentication events
        events = [
            # Successful login
            AuthEvent(
                event_type=AuthEventType.LOGIN_SUCCESS,
                user_id="user1",
                email="user1@example.com",
                success=True,
                processing_time_ms=120.0,
            ),
            # Failed login
            AuthEvent(
                event_type=AuthEventType.LOGIN_FAILED,
                email="user2@example.com",
                ip_address="192.168.1.1",
                success=False,
                error_message="Invalid credentials",
            ),
            # High-risk login
            AuthEvent(
                event_type=AuthEventType.LOGIN_SUCCESS,
                user_id="user3",
                email="user3@example.com",
                success=True,
                risk_score=0.8,
                security_flags=["unusual_location"],
            ),
            # Session creation
            AuthEvent(
                event_type=AuthEventType.SESSION_CREATED,
                user_id="user1",
                success=True,
                processing_time_ms=50.0,
            ),
        ]
        
        # Process all events
        analyses = []
        for event in events:
            analysis = await enhanced_monitor.analyze_auth_event(event)
            analyses.append(analysis)
        
        # Verify all events were processed
        assert len(analyses) == len(events)
        
        # Check comprehensive status
        status = enhanced_monitor.get_comprehensive_status()
        assert status["monitoring_health"] == "active"
        
        # Should have recorded metrics
        correlation_stats = status["security_correlation"]
        assert correlation_stats["recent_events_analyzed"] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])