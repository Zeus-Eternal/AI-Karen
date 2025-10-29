"""
Tests for Extension Error Logging and Monitoring System

This test suite validates the error logging, metrics collection, trend analysis,
and alerting functionality for the extension runtime authentication system.

Requirements tested:
- 10.1: Extension error alerts with relevant details
- 10.2: Metrics collection on response times, error rates, and availability
- 10.3: Authentication issue escalation and alerting
- 10.4: Performance degradation recommendations
- 10.5: Historical data for trend analysis and capacity planning
"""

import pytest
import asyncio
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
import threading
import time

from server.extension_error_logging import (
    ExtensionErrorLogger, ExtensionMetricsCollector, ExtensionErrorTrendAnalyzer,
    ErrorEvent, ErrorCategory, ErrorSeverity, MetricPoint
)
from server.extension_alerting_system import (
    ExtensionAlertManager, AlertRule, NotificationChannel, AlertType, EscalationLevel
)
from server.extension_monitoring_integration import (
    ExtensionMonitoringIntegration, monitor_extension_endpoint, monitor_recovery_operation
)

class TestExtensionErrorLogger:
    """Test the structured error logging system."""

    def setup_method(self):
        """Set up test fixtures."""
        self.logger = ExtensionErrorLogger("test_logger")

    def test_correlation_context_manager(self):
        """Test correlation ID context management."""
        # Test with provided correlation ID
        test_correlation_id = "test-correlation-123"
        
        with self.logger.correlation_context_manager(test_correlation_id) as correlation_id:
            assert correlation_id == test_correlation_id
            assert self.logger.get_correlation_id() == test_correlation_id
        
        # Test with auto-generated correlation ID
        with self.logger.correlation_context_manager() as correlation_id:
            assert correlation_id is not None
            assert len(correlation_id) > 0
            assert self.logger.get_correlation_id() == correlation_id

    def test_log_error_basic(self):
        """Test basic error logging functionality."""
        error_event = self.logger.log_error(
            error_type="TestError",
            error_message="Test error message",
            category=ErrorCategory.AUTHENTICATION,
            severity=ErrorSeverity.HIGH,
            context={"test_key": "test_value"},
            user_id="test_user",
            tenant_id="test_tenant",
            endpoint="/api/test"
        )
        
        assert error_event.error_type == "TestError"
        assert error_event.error_message == "Test error message"
        assert error_event.category == ErrorCategory.AUTHENTICATION
        assert error_event.severity == ErrorSeverity.HIGH
        assert error_event.context["test_key"] == "test_value"
        assert error_event.user_id == "test_user"
        assert error_event.tenant_id == "test_tenant"
        assert error_event.endpoint == "/api/test"
        assert error_event.correlation_id is not None

    def test_log_recovery_attempt(self):
        """Test recovery attempt logging."""
        correlation_id = "test-correlation-456"
        
        # Test successful recovery
        self.logger.log_recovery_attempt(
            correlation_id=correlation_id,
            recovery_strategy="token_refresh",
            success=True,
            duration=1.5,
            details={"attempts": 1}
        )
        
        # Test failed recovery
        self.logger.log_recovery_attempt(
            correlation_id=correlation_id,
            recovery_strategy="service_restart",
            success=False,
            duration=5.0,
            details={"error": "Service not responding"}
        )

    def test_error_event_to_dict(self):
        """Test error event serialization."""
        error_event = ErrorEvent(
            correlation_id="test-123",
            timestamp=datetime.utcnow(),
            error_type="TestError",
            error_message="Test message",
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.MEDIUM,
            context={"key": "value"}
        )
        
        event_dict = error_event.to_dict()
        
        assert event_dict["correlation_id"] == "test-123"
        assert event_dict["error_type"] == "TestError"
        assert event_dict["category"] == "network"
        assert event_dict["severity"] == "medium"
        assert "timestamp" in event_dict

class TestExtensionMetricsCollector:
    """Test the metrics collection system."""

    def setup_method(self):
        """Set up test fixtures."""
        self.collector = ExtensionMetricsCollector(retention_hours=1)

    def test_record_error(self):
        """Test error recording for metrics."""
        error_event = ErrorEvent(
            correlation_id="test-123",
            timestamp=datetime.utcnow(),
            error_type="AuthError",
            error_message="Authentication failed",
            category=ErrorCategory.AUTHENTICATION,
            severity=ErrorSeverity.HIGH,
            context={}
        )
        
        self.collector.record_error(
            error_event=error_event,
            endpoint="/api/extensions/",
            response_time=1500.0
        )
        
        # Verify error was recorded
        assert len(self.collector.metrics['errors']) == 1
        assert len(self.collector.response_times['/api/extensions/']) == 1

    def test_record_success(self):
        """Test successful request recording."""
        self.collector.record_success(
            endpoint="/api/extensions/",
            response_time=500.0,
            extension_name="test_extension"
        )
        
        # Verify success was recorded
        assert len(self.collector.metrics['requests']) == 1
        assert len(self.collector.response_times['/api/extensions/']) == 1

    def test_record_recovery_success(self):
        """Test recovery attempt recording."""
        self.collector.record_recovery_success(
            correlation_id="test-123",
            recovery_strategy="token_refresh",
            duration=2.0,
            success=True
        )
        
        self.collector.record_recovery_success(
            correlation_id="test-456",
            recovery_strategy="service_restart",
            duration=10.0,
            success=False
        )
        
        # Verify recovery attempts were recorded
        assert len(self.collector.metrics['recovery_attempts']) == 2

    def test_get_error_rate(self):
        """Test error rate calculation."""
        # Record some errors and successes
        current_time = datetime.utcnow()
        
        # Create test error event
        error_event = ErrorEvent(
            correlation_id="test-123",
            timestamp=current_time,
            error_type="TestError",
            error_message="Test error",
            category=ErrorCategory.AUTHENTICATION,
            severity=ErrorSeverity.HIGH,
            context={}
        )
        
        # Record 2 errors and 8 successes
        for i in range(2):
            self.collector.record_error(error_event, "/api/test")
        
        for i in range(8):
            self.collector.record_success("/api/test", 500.0)
        
        error_rates = self.collector.get_error_rate(time_window_minutes=60)
        
        # Should have authentication errors
        assert "authentication" in error_rates
        assert error_rates["authentication"] == 0.2  # 2 errors out of 10 total requests

    def test_get_response_time_stats(self):
        """Test response time statistics calculation."""
        endpoint = "/api/test"
        
        # Record various response times
        response_times = [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000]
        
        for rt in response_times:
            self.collector.record_success(endpoint, rt)
        
        stats = self.collector.get_response_time_stats(endpoint=endpoint)
        
        assert stats['count'] == 10
        assert stats['avg'] == 550.0
        assert stats['min'] == 100.0
        assert stats['max'] == 1000.0
        assert stats['p95'] == 950.0  # 95th percentile

    def test_get_availability_stats(self):
        """Test availability statistics calculation."""
        endpoint = "/api/test"
        
        # Record 9 successes and 1 error
        for i in range(9):
            self.collector.record_success(endpoint, 500.0)
        
        error_event = ErrorEvent(
            correlation_id="test-123",
            timestamp=datetime.utcnow(),
            error_type="TestError",
            error_message="Test error",
            category=ErrorCategory.SERVICE_UNAVAILABLE,
            severity=ErrorSeverity.HIGH,
            context={}
        )
        self.collector.record_error(error_event, endpoint)
        
        availability = self.collector.get_availability_stats()
        
        assert endpoint in availability
        assert availability[endpoint] == 0.9  # 9 successes out of 10 total

    def test_get_recovery_success_rate(self):
        """Test recovery success rate calculation."""
        # Record recovery attempts
        self.collector.record_recovery_success("test-1", "token_refresh", 1.0, True)
        self.collector.record_recovery_success("test-2", "token_refresh", 1.5, True)
        self.collector.record_recovery_success("test-3", "token_refresh", 2.0, False)
        self.collector.record_recovery_success("test-4", "service_restart", 5.0, True)
        
        success_rates = self.collector.get_recovery_success_rate()
        
        assert "token_refresh" in success_rates
        assert "service_restart" in success_rates
        assert success_rates["token_refresh"] == 2/3  # 2 successes out of 3 attempts
        assert success_rates["service_restart"] == 1.0  # 1 success out of 1 attempt

    def test_cleanup_old_metrics(self):
        """Test metrics cleanup functionality."""
        # Create collector with very short retention
        collector = ExtensionMetricsCollector(retention_hours=0.001)  # ~3.6 seconds
        
        # Record some metrics
        error_event = ErrorEvent(
            correlation_id="test-123",
            timestamp=datetime.utcnow() - timedelta(hours=1),  # Old timestamp
            error_type="TestError",
            error_message="Test error",
            category=ErrorCategory.AUTHENTICATION,
            severity=ErrorSeverity.HIGH,
            context={}
        )
        
        collector.record_error(error_event, "/api/test")
        collector.record_success("/api/test", 500.0)
        
        # Verify metrics were recorded
        assert len(collector.metrics['errors']) == 1
        assert len(collector.metrics['requests']) == 1
        
        # Clean up old metrics
        collector.cleanup_old_metrics()
        
        # Verify old metrics were removed
        assert len(collector.metrics['errors']) == 0
        assert len(collector.metrics['requests']) == 0

class TestExtensionErrorTrendAnalyzer:
    """Test the error trend analysis system."""

    def setup_method(self):
        """Set up test fixtures."""
        self.collector = ExtensionMetricsCollector()
        self.analyzer = ExtensionErrorTrendAnalyzer(self.collector)

    def test_analyze_error_trends(self):
        """Test error trend analysis."""
        # Create some historical data
        current_time = datetime.utcnow()
        
        for i in range(24):  # 24 hours of data
            timestamp = current_time - timedelta(hours=i)
            
            # Create error event with historical timestamp
            error_event = ErrorEvent(
                correlation_id=f"test-{i}",
                timestamp=timestamp,
                error_type="TestError",
                error_message="Test error",
                category=ErrorCategory.AUTHENTICATION,
                severity=ErrorSeverity.HIGH,
                context={}
            )
            
            # Manually add to metrics with historical timestamp
            metric_point = MetricPoint(
                timestamp=timestamp,
                value=1.0,
                labels={'category': 'authentication', 'severity': 'high'}
            )
            self.collector.metrics['errors'].append(metric_point)
            
            # Add some requests
            request_point = MetricPoint(
                timestamp=timestamp,
                value=1.0,
                labels={'endpoint': '/api/test'}
            )
            self.collector.metrics['requests'].append(request_point)
        
        trends = self.analyzer.analyze_error_trends(time_window_hours=24)
        
        assert 'buckets' in trends
        assert 'trend_direction' in trends
        assert 'current_error_rate' in trends
        assert 'peak_error_rate' in trends
        assert 'average_error_rate' in trends
        assert len(trends['buckets']) <= 24

    def test_get_performance_recommendations(self):
        """Test performance recommendation generation."""
        # Create conditions that should trigger recommendations
        
        # High error rate
        for i in range(10):
            error_event = ErrorEvent(
                correlation_id=f"test-{i}",
                timestamp=datetime.utcnow(),
                error_type="AuthError",
                error_message="Auth failed",
                category=ErrorCategory.AUTHENTICATION,
                severity=ErrorSeverity.HIGH,
                context={}
            )
            self.collector.record_error(error_event, "/api/test")
        
        # High response times
        for i in range(5):
            self.collector.record_success("/api/test", 3000.0)  # 3 second response time
        
        recommendations = self.analyzer.get_performance_recommendations()
        
        assert isinstance(recommendations, list)
        # Should have recommendations for high error rate and high response time
        assert len(recommendations) >= 1
        
        # Check recommendation structure
        if recommendations:
            rec = recommendations[0]
            assert 'type' in rec
            assert 'severity' in rec
            assert 'message' in rec
            assert 'recommendation' in rec

class TestExtensionAlertManager:
    """Test the alerting system."""

    def setup_method(self):
        """Set up test fixtures."""
        self.alert_manager = ExtensionAlertManager()

    @pytest.mark.asyncio
    async def test_alert_rule_management(self):
        """Test alert rule management."""
        rule = AlertRule(
            rule_id="test_rule",
            alert_type=AlertType.ERROR_RATE_THRESHOLD,
            condition={"threshold": 0.1, "time_window_minutes": 15},
            severity=ErrorSeverity.HIGH,
            escalation_level=EscalationLevel.LEVEL_1
        )
        
        self.alert_manager.add_alert_rule(rule)
        
        assert "test_rule" in self.alert_manager.alert_rules
        assert self.alert_manager.alert_rules["test_rule"].rule_id == "test_rule"

    @pytest.mark.asyncio
    async def test_notification_channel_management(self):
        """Test notification channel management."""
        channel = NotificationChannel(
            channel_id="test_channel",
            channel_type="email",
            config={"to_emails": ["test@example.com"]},
            escalation_levels=[EscalationLevel.LEVEL_1]
        )
        
        self.alert_manager.add_notification_channel(channel)
        
        assert "test_channel" in self.alert_manager.notification_channels
        assert self.alert_manager.notification_channels["test_channel"].channel_id == "test_channel"

    @pytest.mark.asyncio
    async def test_alert_acknowledgment_and_resolution(self):
        """Test alert acknowledgment and resolution."""
        # Create a mock alert
        from server.extension_alerting_system import Alert, AlertStatus
        
        alert = Alert(
            alert_id="test_alert_123",
            correlation_id="test-correlation",
            alert_type="test_type",
            severity=ErrorSeverity.HIGH,
            message="Test alert",
            context={},
            created_at=datetime.utcnow()
        )
        
        # Add to active alerts
        self.alert_manager.active_alerts[alert.alert_id] = alert
        
        # Test acknowledgment
        success = self.alert_manager.acknowledge_alert(alert.alert_id, "test_user")
        assert success
        assert alert.status == AlertStatus.ACKNOWLEDGED
        assert alert.acknowledged_at is not None
        
        # Test resolution
        success = self.alert_manager.resolve_alert(alert.alert_id, "test_user")
        assert success
        assert alert.status == AlertStatus.RESOLVED
        assert alert.resolved_at is not None
        assert alert.alert_id not in self.alert_manager.active_alerts

class TestExtensionMonitoringIntegration:
    """Test the monitoring integration system."""

    def setup_method(self):
        """Set up test fixtures."""
        self.integration = ExtensionMonitoringIntegration()

    @pytest.mark.asyncio
    async def test_monitor_request_success(self):
        """Test successful request monitoring."""
        async with self.integration.monitor_request(
            endpoint="/api/test",
            user_id="test_user",
            tenant_id="test_tenant",
            extension_name="test_extension"
        ) as correlation_id:
            assert correlation_id is not None
            # Simulate some work
            await asyncio.sleep(0.01)
        
        # Verify request was tracked
        assert correlation_id not in self.integration.request_tracking

    @pytest.mark.asyncio
    async def test_monitor_request_error(self):
        """Test error request monitoring."""
        with pytest.raises(ValueError):
            async with self.integration.monitor_request(
                endpoint="/api/test",
                user_id="test_user"
            ) as correlation_id:
                # Simulate an error
                raise ValueError("Test error")

    @pytest.mark.asyncio
    async def test_log_authentication_error(self):
        """Test authentication error logging."""
        await self.integration.log_authentication_error(
            error_message="Token expired",
            user_id="test_user",
            tenant_id="test_tenant",
            endpoint="/api/extensions/",
            context={"token_type": "access"}
        )

    @pytest.mark.asyncio
    async def test_log_service_unavailable(self):
        """Test service unavailable error logging."""
        await self.integration.log_service_unavailable(
            service_name="extension_service",
            error_message="Service not responding",
            endpoint="/api/extensions/",
            context={"timeout": 30}
        )

    @pytest.mark.asyncio
    async def test_log_recovery_attempt(self):
        """Test recovery attempt logging."""
        await self.integration.log_recovery_attempt(
            correlation_id="test-correlation",
            recovery_strategy="token_refresh",
            success=True,
            duration=1.5,
            details={"attempts": 1}
        )

    @pytest.mark.asyncio
    async def test_get_monitoring_dashboard_data(self):
        """Test monitoring dashboard data retrieval."""
        dashboard_data = await self.integration.get_monitoring_dashboard_data()
        
        assert 'timestamp' in dashboard_data
        assert 'metrics' in dashboard_data
        assert 'trends' in dashboard_data
        assert 'recommendations' in dashboard_data
        assert 'alerts' in dashboard_data
        assert 'system_health' in dashboard_data

    def test_error_classification(self):
        """Test error classification logic."""
        # Test authentication error
        auth_error = Exception("HTTP 403: Forbidden")
        category, severity = self.integration._classify_error(auth_error)
        assert category == ErrorCategory.AUTHENTICATION
        assert severity == ErrorSeverity.HIGH
        
        # Test service unavailable error
        service_error = Exception("HTTP 503: Service Unavailable")
        category, severity = self.integration._classify_error(service_error)
        assert category == ErrorCategory.SERVICE_UNAVAILABLE
        assert severity == ErrorSeverity.HIGH
        
        # Test network error
        network_error = Exception("Connection refused")
        category, severity = self.integration._classify_error(network_error)
        assert category == ErrorCategory.NETWORK
        assert severity == ErrorSeverity.MEDIUM

    @pytest.mark.asyncio
    async def test_monitor_extension_endpoint_decorator(self):
        """Test the monitoring decorator."""
        
        @monitor_extension_endpoint(
            endpoint_name="test_endpoint",
            extension_name="test_extension"
        )
        async def test_function(user_context=None, correlation_id=None):
            assert correlation_id is not None
            return {"success": True}
        
        result = await test_function(user_context={"user_id": "test_user"})
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_monitor_recovery_operation(self):
        """Test recovery operation monitoring."""
        async with monitor_recovery_operation(
            recovery_strategy="test_strategy",
            correlation_id="test-correlation"
        ) as correlation_id:
            assert correlation_id == "test-correlation"
            # Simulate recovery work
            await asyncio.sleep(0.01)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])