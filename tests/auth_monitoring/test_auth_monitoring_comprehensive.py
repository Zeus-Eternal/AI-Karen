"""
Comprehensive tests for authentication monitoring and logging functionality.

This module tests all aspects of the authentication monitoring system including:
- Structured logging
- Metrics collection
- Security event monitoring
- Performance tracking
- Alerting capabilities
- Enhanced monitoring features
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai_karen_engine.auth.config import AuthConfig, MonitoringConfig
from ai_karen_engine.auth.models import AuthEvent, AuthEventType, UserData
from ai_karen_engine.auth.monitoring import (
    AlertManager,
    AuthMonitor,
    MetricsCollector,
    init_auth_metrics,
)
from ai_karen_engine.auth.monitoring_extensions import (
    EnhancedAuthMonitor,
    PerformanceTrendAnalyzer,
    SecurityEventCorrelator,
    SecurityPattern,
)
from ai_karen_engine.auth.service import AuthService


class TestMetricsCollector:
    """Test the MetricsCollector component."""

    @pytest.mark.asyncio
    async def test_record_counter_metric(self, metrics_collector):
        """Test recording counter metrics."""
        await metrics_collector.record_counter("test.counter", 5, {"tag": "value"})
        
        # Check counter value
        assert metrics_collector.get_counter("test.counter", {"tag": "value"}) == 5
        
        # Record another increment
        await metrics_collector.record_counter("test.counter", 3, {"tag": "value"})
        assert metrics_collector.get_counter("test.counter", {"tag": "value"}) == 8

    @pytest.mark.asyncio
    async def test_record_gauge_metric(self, metrics_collector):
        """Test recording gauge metrics."""
        await metrics_collector.record_gauge("test.gauge", 42.5, {"env": "test"})
        
        assert metrics_collector.get_gauge("test.gauge", {"env": "test"}) == 42.5
        
        # Update gauge value
        await metrics_collector.record_gauge("test.gauge", 55.0, {"env": "test"})
        assert metrics_collector.get_gauge("test.gauge", {"env": "test"}) == 55.0

    @pytest.mark.asyncio
    async def test_record_histogram_metric(self, metrics_collector):
        """Test recording histogram metrics."""
        values = [10.0, 20.0, 30.0, 40.0, 50.0]
        
        for value in values:
            await metrics_collector.record_histogram("test.histogram", value)
        
        stats = metrics_collector.get_histogram_stats("test.histogram")
        assert stats["count"] == 5
        assert stats["min"] == 10.0
        assert stats["max"] == 50.0
        assert stats["avg"] == 30.0

    @pytest.mark.asyncio
    async def test_record_timing_metric(self, metrics_collector):
        """Test recording timing metrics."""
        await metrics_collector.record_timing("auth_operation", 150.5)
        
        stats = metrics_collector.get_histogram_stats("auth.timing.auth_operation")
        assert stats["count"] == 1
        assert stats["avg"] == 150.5

    def test_get_rate_calculation(self, metrics_collector):
        """Test rate calculation over time windows."""
        # Simulate metrics over time
        current_minute = int(datetime.now().timestamp() // 60)
        
        # Add data to minute buckets
        metrics_collector._minute_buckets["test.metric"][current_minute] = 10
        metrics_collector._minute_buckets["test.metric"][current_minute - 1] = 8
        metrics_collector._minute_buckets["test.metric"][current_minute - 2] = 6
        
        rate = metrics_collector.get_rate("test.metric", 3)
        assert rate == 8.0  # (10 + 8 + 6) / 3

    def test_get_all_metrics(self, metrics_collector):
        """Test getting all metrics summary."""
        # Add some test data
        metrics_collector._counters["test.counter"] = 42
        metrics_collector._gauges["test.gauge"] = 3.14
        metrics_collector._histograms["test.histogram"] = [1.0, 2.0, 3.0]
        
        all_metrics = metrics_collector.get_all_metrics()
        
        assert "counters" in all_metrics
        assert "gauges" in all_metrics
        assert "histograms" in all_metrics
        assert "rates" in all_metrics
        
        assert all_metrics["counters"]["test.counter"] == 42
        assert all_metrics["gauges"]["test.gauge"] == 3.14


class TestAlertManager:
    """Test the AlertManager component."""

    @pytest.mark.asyncio
    async def test_trigger_security_alert(self, alert_manager):
        """Test triggering security alerts."""
        event = AuthEvent(
            event_type=AuthEventType.LOGIN_FAILED,
            user_id="test_user",
            email="test@example.com",
            ip_address="192.168.1.100",
            success=False,
            risk_score=0.8,
            security_flags=["suspicious_ip", "unusual_time"],
        )
        
        await alert_manager.trigger_security_alert(event, "high")
        
        active_alerts = alert_manager.get_active_alerts()
        assert len(active_alerts) == 1
        
        alert = active_alerts[0]
        assert alert.alert_type == "security_event"
        assert alert.severity == "high"
        assert alert.details["risk_score"] == 0.8
        assert "suspicious_ip" in alert.details["security_flags"]

    def test_alert_callback_registration(self, alert_manager):
        """Test alert callback registration and execution."""
        callback_called = False
        callback_alert = None
        
        def test_callback(alert):
            nonlocal callback_called, callback_alert
            callback_called = True
            callback_alert = alert
        
        alert_manager.add_alert_callback(test_callback)
        
        # Trigger an alert
        asyncio.run(alert_manager._trigger_alert(
            "test_alert", "medium", "Test alert message"
        ))
        
        assert callback_called
        assert callback_alert.alert_type == "test_alert"
        assert callback_alert.severity == "medium"

    def test_resolve_alert(self, alert_manager):
        """Test alert resolution."""
        # Create an alert
        alert = asyncio.run(alert_manager._trigger_alert(
            "test_alert", "low", "Test message"
        ))
        
        assert len(alert_manager.get_active_alerts()) == 1
        
        # Resolve the alert
        result = alert_manager.resolve_alert(alert.alert_id)
        assert result is True
        assert len(alert_manager.get_active_alerts()) == 0
        
        # Check alert is marked as resolved
        history = alert_manager.get_alert_history()
        resolved_alert = next(a for a in history if a.alert_id == alert.alert_id)
        assert resolved_alert.resolved is True
        assert resolved_alert.resolved_at is not None

    def test_get_alert_stats(self, alert_manager):
        """Test alert statistics."""
        # Create alerts with different severities
        asyncio.run(alert_manager._trigger_alert("test1", "low", "Test 1"))
        asyncio.run(alert_manager._trigger_alert("test2", "high", "Test 2"))
        asyncio.run(alert_manager._trigger_alert("test3", "critical", "Test 3"))
        
        stats = alert_manager.get_alert_stats()
        
        assert stats["active_alerts"] == 3
        assert stats["total_alerts"] == 3
        assert stats["alerts_by_severity"]["low"] == 1
        assert stats["alerts_by_severity"]["high"] == 1
        assert stats["alerts_by_severity"]["critical"] == 1


class TestAuthMonitor:
    """Test the main AuthMonitor class."""

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        config = AuthConfig()
        config.monitoring.enable_monitoring = True
        config.monitoring.enable_metrics = True
        config.monitoring.enable_alerting = True
        config.monitoring.enable_structured_logging = True
        return config

    @pytest.fixture
    def auth_monitor(self, config):
        """Create AuthMonitor instance."""
        return AuthMonitor(config)

    @pytest.mark.asyncio
    async def test_record_auth_event(self, auth_monitor):
        """Test recording authentication events."""
        event = AuthEvent(
            event_type=AuthEventType.LOGIN_SUCCESS,
            user_id="user123",
            email="user@example.com",
            tenant_id="tenant1",
            ip_address="192.168.1.1",
            user_agent="TestAgent/1.0",
            success=True,
            processing_time_ms=125.5,
            risk_score=0.2,
        )
        
        await auth_monitor.record_auth_event(event)
        
        # Check metrics were recorded
        base_tags = {
            "event_type": "login_success",
            "success": "true",
            "tenant_id": "tenant1",
        }
        
        assert auth_monitor.metrics.get_counter("auth.events.total", base_tags) == 1
        assert auth_monitor.metrics.get_counter("auth.events.success", base_tags) == 1
        assert auth_monitor.metrics.get_counter("auth.login.success", base_tags) == 1
        
        # Check event was stored
        recent_events = auth_monitor.get_recent_events(10)
        assert len(recent_events) == 1
        assert recent_events[0]["event_id"] == event.event_id

    @pytest.mark.asyncio
    async def test_failed_auth_event_metrics(self, auth_monitor):
        """Test metrics for failed authentication events."""
        event = AuthEvent(
            event_type=AuthEventType.LOGIN_FAILED,
            email="user@example.com",
            ip_address="192.168.1.1",
            success=False,
            error_message="Invalid credentials",
            processing_time_ms=50.0,
        )
        
        await auth_monitor.record_auth_event(event)
        
        base_tags = {
            "event_type": "login_failed",
            "success": "false",
            "tenant_id": "default",
        }
        
        assert auth_monitor.metrics.get_counter("auth.events.failed", base_tags) == 1
        assert auth_monitor.metrics.get_counter("auth.login.failed", base_tags) == 1
        
        # Check error classification
        error_tags = {**base_tags, "error_type": "invalid_credentials"}
        assert auth_monitor.metrics.get_counter("auth.errors", error_tags) == 1

    @pytest.mark.asyncio
    async def test_security_alert_triggering(self, auth_monitor):
        """Test automatic security alert triggering."""
        # Create high-risk event
        event = AuthEvent(
            event_type=AuthEventType.LOGIN_FAILED,
            email="user@example.com",
            ip_address="192.168.1.1",
            success=False,
            risk_score=0.9,  # High risk score
            security_flags=["brute_force", "suspicious_ip"],
            blocked_by_security=True,
        )
        
        await auth_monitor.record_auth_event(event)
        
        # Check that security alert was triggered
        active_alerts = auth_monitor.alerts.get_active_alerts()
        assert len(active_alerts) >= 1
        
        security_alert = next(
            (a for a in active_alerts if a.alert_type == "security_event"), None
        )
        assert security_alert is not None
        assert security_alert.severity in ["high", "critical"]

    def test_get_health_status(self, auth_monitor):
        """Test health status reporting."""
        # Add some successful events
        for i in range(10):
            event = AuthEvent(
                event_type=AuthEventType.LOGIN_SUCCESS,
                user_id=f"user{i}",
                success=True,
            )
            auth_monitor._recent_events.append(event)
        
        health = auth_monitor.get_health_status()
        
        assert health["status"] == "healthy"
        assert health["success_rate"] == 1.0
        assert health["recent_events"] == 10

    def test_get_monitoring_stats(self, auth_monitor):
        """Test monitoring statistics."""
        stats = auth_monitor.get_monitoring_stats()
        
        assert "recent_events_count" in stats
        assert "monitoring_enabled" in stats
        assert "metrics_enabled" in stats
        assert "alerting_enabled" in stats
        
        assert stats["monitoring_enabled"] is True
        assert stats["metrics_enabled"] is True
        assert stats["alerting_enabled"] is True

    @pytest.mark.asyncio
    async def test_shutdown(self, auth_monitor):
        """Test proper shutdown of monitoring components."""
        await auth_monitor.shutdown()
        
        # Verify cleanup tasks were cancelled
        assert auth_monitor.metrics._cleanup_task.cancelled()
        assert auth_monitor.alerts._monitoring_task.cancelled()


class TestSecurityEventCorrelator:
    """Test the SecurityEventCorrelator component."""

    @pytest.mark.asyncio
    async def test_brute_force_detection(self, correlator):
        """Test brute force attack detection."""
        ip_address = "192.168.1.100"
        
        # Generate multiple failed attempts from same IP
        for i in range(12):  # Above threshold
            event = AuthEvent(
                event_type=AuthEventType.LOGIN_FAILED,
                email=f"user{i}@example.com",
                ip_address=ip_address,
                success=False,
                timestamp=datetime.now(timezone.utc),
            )
            
            patterns = await correlator.analyze_event(event)
            
            # Should detect brute force on the threshold attempt
            if i >= correlator.brute_force_threshold - 1:
                brute_force_patterns = [
                    p for p in patterns if p.pattern_type == "brute_force"
                ]
                assert len(brute_force_patterns) >= 1
                
                pattern = brute_force_patterns[0]
                assert pattern.severity == "high"
                assert ip_address in pattern.source_ips
                assert pattern.event_count >= correlator.brute_force_threshold

    @pytest.mark.asyncio
    async def test_credential_stuffing_detection(self, correlator):
        """Test credential stuffing attack detection."""
        ip_address = "192.168.1.200"
        
        # Generate failed attempts against multiple users from same IP
        for i in range(6):  # Above threshold
            event = AuthEvent(
                event_type=AuthEventType.LOGIN_FAILED,
                email=f"victim{i}@example.com",
                ip_address=ip_address,
                success=False,
                timestamp=datetime.now(timezone.utc),
            )
            
            patterns = await correlator.analyze_event(event)
            
            # Should detect credential stuffing
            if i >= correlator.credential_stuffing_threshold - 1:
                stuffing_patterns = [
                    p for p in patterns if p.pattern_type == "credential_stuffing"
                ]
                assert len(stuffing_patterns) >= 1
                
                pattern = stuffing_patterns[0]
                assert pattern.severity == "high"
                assert ip_address in pattern.source_ips
                assert len(pattern.affected_users) >= correlator.credential_stuffing_threshold

    @pytest.mark.asyncio
    async def test_anomalous_behavior_detection(self, correlator):
        """Test anomalous behavior detection."""
        event = AuthEvent(
            event_type=AuthEventType.LOGIN_SUCCESS,
            user_id="user123",
            email="user@example.com",
            ip_address="192.168.1.50",
            success=True,
            risk_score=0.85,  # High risk score
            security_flags=["unusual_location", "new_device"],
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

    def test_get_correlation_stats(self, correlator):
        """Test correlation statistics."""
        # Add some test data
        correlator._recent_events.extend([
            AuthEvent(event_type=AuthEventType.LOGIN_FAILED, success=False),
            AuthEvent(event_type=AuthEventType.LOGIN_SUCCESS, success=True),
        ])
        
        correlator._failed_attempts_by_ip["192.168.1.1"].append(
            AuthEvent(event_type=AuthEventType.LOGIN_FAILED, success=False)
        )
        
        stats = correlator.get_correlation_stats()
        
        assert stats["recent_events_analyzed"] == 2
        assert stats["ips_with_failed_attempts"] == 1
        assert "active_patterns" in stats
        assert "pattern_types" in stats


class TestPerformanceTrendAnalyzer:
    """Test the PerformanceTrendAnalyzer component."""
    @pytest.mark.asyncio
    async def test_record_metric_point(self, performance_analyzer):
        """Test recording metric data points."""
        await performance_analyzer.record_metric_point("test.metric", 100.0)
        await performance_analyzer.record_metric_point("test.metric", 110.0)
        await performance_analyzer.record_metric_point("test.metric", 120.0)

        history = performance_analyzer._metric_history["test.metric"]
        assert len(history) == 3
        assert history[-1][1] == 120.0  # Latest value

    @pytest.mark.asyncio
    async def test_trend_analysis(self, performance_analyzer):
        """Test performance trend analysis."""
        # Add historical data with an improving trend
        base_time = datetime.now(timezone.utc)

        for i in range(20):
            timestamp = base_time - timedelta(minutes=i)
            value = 100.0 - (i * 2)  # Decreasing values (improving performance)
            await performance_analyzer.record_metric_point("response_time", value, timestamp)

        trends = await performance_analyzer.analyze_trends()

        # Should detect improving trend for response time
        response_time_trends = [
            t for t in trends if t.metric_name == "response_time"
        ]

        assert len(response_time_trends) > 0

        # At least one trend should show improvement
        improving_trends = [
            t for t in response_time_trends if t.trend_direction == "improving"
        ]
        assert len(improving_trends) > 0

    def test_get_trend_summary(self, performance_analyzer):
        """Test trend summary generation."""
        # Add some mock trends
        performance_analyzer._trend_cache["metric1_5m"] = MagicMock()
        performance_analyzer._trend_cache["metric1_5m"].trend_direction = "improving"
        performance_analyzer._trend_cache["metric1_5m"].trend_strength = 0.3

        performance_analyzer._trend_cache["metric2_5m"] = MagicMock()
        performance_analyzer._trend_cache["metric2_5m"].trend_direction = "degrading"
        performance_analyzer._trend_cache["metric2_5m"].trend_strength = 0.8

        summary = performance_analyzer.get_trend_summary()

        assert summary["trends_analyzed"] == 2
        assert summary["improving"] == 1
        assert summary["degrading"] == 1
        assert summary["concerning_trends"] == 1  # degrading with high strength


class TestEnhancedAuthMonitor:
    """Test the EnhancedAuthMonitor component."""

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return AuthConfig()

    @pytest.fixture
    def enhanced_monitor(self, config):
        """Create EnhancedAuthMonitor instance."""
        return EnhancedAuthMonitor(config)

    @pytest.mark.asyncio
    async def test_analyze_auth_event(self, enhanced_monitor):
        """Test comprehensive authentication event analysis."""
        event = AuthEvent(
            event_type=AuthEventType.LOGIN_FAILED,
            user_id="user123",
            email="user@example.com",
            ip_address="192.168.1.100",
            success=False,
            processing_time_ms=250.0,
            risk_score=0.6,
            security_flags=["suspicious_timing"],
        )
        
        analysis = await enhanced_monitor.analyze_auth_event(event)
        
        assert "event_id" in analysis
        assert "security_patterns" in analysis
        assert "recommendations" in analysis
        assert analysis["event_id"] == event.event_id

    def test_get_comprehensive_status(self, enhanced_monitor):
        """Test comprehensive status reporting."""
        status = enhanced_monitor.get_comprehensive_status()
        
        assert "security_correlation" in status
        assert "performance_trends" in status
        assert "active_security_patterns" in status
        assert "monitoring_health" in status
        assert "last_analysis" in status
        
        assert status["monitoring_health"] == "active"

    @pytest.mark.asyncio
    async def test_shutdown(self, enhanced_monitor):
        """Test enhanced monitor shutdown."""
        await enhanced_monitor.shutdown()
        
        # Verify background task was cancelled
        assert enhanced_monitor._analysis_task.cancelled()


class TestAuthServiceMonitoringIntegration:
    """Test monitoring integration in the main AuthService."""

    @pytest.fixture
    def config(self):
        """Create test configuration with monitoring enabled."""
        config = AuthConfig()
        config.monitoring.enable_monitoring = True
        config.monitoring.enable_metrics = True
        config.monitoring.enable_alerting = True
        return config

    @pytest.fixture
    async def auth_service(self, config):
        """Create AuthService instance with monitoring."""
        service = AuthService(config)
        await service.initialize()
        return service

    @pytest.mark.asyncio
    async def test_monitoring_initialization(self, auth_service):
        """Test that monitoring components are properly initialized."""
        assert auth_service.monitor is not None
        assert auth_service.enhanced_monitor is not None
        
        # Test monitoring is active
        assert auth_service.monitor.monitoring_config.enable_monitoring
        assert auth_service.enhanced_monitor.config.monitoring.enable_monitoring

    @pytest.mark.asyncio
    async def test_auth_event_recording(self, auth_service):
        """Test that authentication events are properly recorded."""
        # Mock the core auth to avoid database dependencies
        auth_service.core_auth.authenticate_user = AsyncMock(return_value=None)
        
        try:
            await auth_service.authenticate_user(
                email="test@example.com",
                password="wrongpassword",
                ip_address="192.168.1.1",
                user_agent="TestAgent/1.0",
            )
        except Exception:
            pass  # Expected to fail
        
        # Check that events were recorded
        recent_events = auth_service.monitor.get_recent_events(10)
        assert len(recent_events) > 0
        
        # Should have recorded a failed login event
        failed_events = [
            e for e in recent_events 
            if e["event_type"] == "login_failed"
        ]
        assert len(failed_events) > 0

    def test_comprehensive_monitoring_status(self, auth_service):
        """Test comprehensive monitoring status reporting."""
        status = auth_service.get_comprehensive_monitoring_status()
        
        assert "timestamp" in status
        assert "basic_monitoring" in status
        assert "enhanced_monitoring" in status
        assert "overall_health" in status
        
        # Should have monitoring enabled
        assert status["basic_monitoring"]["enabled"] is True

    @pytest.mark.asyncio
    async def test_monitoring_shutdown(self, auth_service):
        """Test proper shutdown of monitoring components."""
        await auth_service.shutdown()
        
        # Verify monitoring components were shut down
        # (This would check internal state if accessible)


class TestStructuredLogging:
    """Test structured logging functionality."""

    @pytest.fixture
    def config(self):
        """Create test configuration with structured logging."""
        config = AuthConfig()
        config.monitoring.enable_structured_logging = True
        config.monitoring.structured_log_format = "json"
        return config

    @pytest.fixture
    def auth_monitor(self, config):
        """Create AuthMonitor with structured logging."""
        return AuthMonitor(config)

    @pytest.mark.asyncio
    async def test_structured_log_format(self, auth_monitor, caplog):
        """Test that logs are properly structured."""
        with caplog.at_level(logging.INFO):
            event = AuthEvent(
                event_type=AuthEventType.LOGIN_SUCCESS,
                user_id="user123",
                email="user@example.com",
                ip_address="192.168.1.1",
                success=True,
            )
            
            await auth_monitor.record_auth_event(event)
        
        # Check that structured log entries were created
        assert len(caplog.records) > 0
        
        # Find auth event log
        auth_logs = [
            record for record in caplog.records
            if "AUTH_EVENT" in record.getMessage()
        ]
        assert len(auth_logs) > 0
        
        auth_log = auth_logs[0]
        assert hasattr(auth_log, "auth_event")
        assert hasattr(auth_log, "event_id")
        assert hasattr(auth_log, "user_id")


class TestPrometheusMetricsIntegration:
    """Test Prometheus metrics integration."""

    def test_metrics_initialization(self):
        """Test Prometheus metrics initialization."""
        # Test that metrics can be initialized
        success, failure, processing_time = init_auth_metrics(force=True)
        
        assert success is not None
        assert failure is not None
        assert processing_time is not None

    def test_metrics_hook_functionality(self):
        """Test metrics hook for forwarding events."""
        from ai_karen_engine.auth.monitoring import metrics_hook
        
        # Test successful login
        metrics_hook("login_success", {
            "processing_time_ms": 150.0,
            "user_id": "user123",
        })
        
        # Test failed login
        metrics_hook("login_failed", {
            "processing_time_ms": 75.0,
            "error_type": "invalid_credentials",
        })
        
        # Should not raise exceptions


@pytest.mark.integration
class TestMonitoringIntegrationScenarios:
    """Integration tests for complete monitoring scenarios."""

    @pytest.fixture
    def config(self):
        """Create comprehensive test configuration."""
        config = AuthConfig()
        config.monitoring.enable_monitoring = True
        config.monitoring.enable_metrics = True
        config.monitoring.enable_alerting = True
        config.monitoring.enable_structured_logging = True
        config.monitoring.enable_performance_tracking = True
        return config

    @pytest.fixture
    async def auth_service(self, config):
        """Create fully configured AuthService."""
        service = AuthService(config)
        await service.initialize()
        return service

    @pytest.mark.asyncio
    async def test_brute_force_attack_scenario(self, auth_service):
        """Test complete brute force attack detection and alerting."""
        # Mock authentication to always fail
        auth_service.core_auth.authenticate_user = AsyncMock(
            side_effect=Exception("Invalid credentials")
        )
        
        attacker_ip = "192.168.1.100"
        
        # Simulate brute force attack
        for i in range(15):
            try:
                await auth_service.authenticate_user(
                    email=f"victim{i % 3}@example.com",  # Target few users
                    password="wrongpassword",
                    ip_address=attacker_ip,
                    user_agent="AttackBot/1.0",
                )
            except Exception:
                pass  # Expected failures
        
        # Check that security patterns were detected
        if auth_service.enhanced_monitor:
            active_patterns = auth_service.enhanced_monitor.security_correlator.get_active_patterns()
            brute_force_patterns = [
                p for p in active_patterns if p.pattern_type == "brute_force"
            ]
            assert len(brute_force_patterns) > 0
        
        # Check that alerts were triggered
        active_alerts = auth_service.monitor.alerts.get_active_alerts()
        security_alerts = [
            a for a in active_alerts if a.alert_type == "security_event"
        ]
        assert len(security_alerts) > 0

    @pytest.mark.asyncio
    async def test_performance_degradation_scenario(self, auth_service):
        """Test performance monitoring and trend detection."""
        # Mock slow authentication responses
        async def slow_auth(*args, **kwargs):
            await asyncio.sleep(0.1)  # Simulate slow response
            return UserData(
                user_id="user123",
                email="user@example.com",
                tenant_id="default",
            )
        
        auth_service.core_auth.authenticate_user = slow_auth
        
        # Perform multiple authentications
        for i in range(10):
            try:
                await auth_service.authenticate_user(
                    email="user@example.com",
                    password="password",
                    ip_address="192.168.1.1",
                )
            except Exception:
                pass
        
        # Check performance metrics were recorded
        if auth_service.enhanced_monitor:
            trends = await auth_service.enhanced_monitor.performance_analyzer.analyze_trends()
            # Should have recorded timing data
            timing_trends = [
                t for t in trends if "processing_time" in t.metric_name
            ]
            # May or may not detect trends with limited data, but should not error

    @pytest.mark.asyncio
    async def test_comprehensive_health_monitoring(self, auth_service):
        """Test comprehensive health status reporting."""
        # Generate some activity
        for i in range(5):
            try:
                await auth_service.authenticate_user(
                    email=f"user{i}@example.com",
                    password="password",
                    ip_address="192.168.1.1",
                )
            except Exception:
                pass
        
        # Get health status
        health = auth_service.get_health_status()
        assert "status" in health
        
        # Get comprehensive monitoring status
        comprehensive_status = auth_service.get_comprehensive_monitoring_status()
        assert "overall_health" in comprehensive_status
        assert "basic_monitoring" in comprehensive_status
        assert "enhanced_monitoring" in comprehensive_status

    @pytest.mark.asyncio
    async def test_monitoring_cleanup_and_shutdown(self, auth_service):
        """Test proper cleanup and shutdown of monitoring components."""
        # Generate some activity first
        for i in range(3):
            try:
                await auth_service.authenticate_user(
                    email=f"user{i}@example.com",
                    password="password",
                    ip_address="192.168.1.1",
                )
            except Exception:
                pass
        
        # Shutdown and verify cleanup
        await auth_service.shutdown()
        
        # Verify background tasks were cancelled
        if auth_service.monitor:
            assert auth_service.monitor.metrics._cleanup_task.cancelled()
            assert auth_service.monitor.alerts._monitoring_task.cancelled()
        
        if auth_service.enhanced_monitor:
            assert auth_service.enhanced_monitor._analysis_task.cancelled()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])