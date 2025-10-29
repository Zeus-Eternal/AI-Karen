"""
Test suite for Extension Monitoring and Alerting System

Comprehensive tests for all monitoring components.
"""

import pytest
import asyncio
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

from server.monitoring.extension_metrics_dashboard import (
    ExtensionMetricsCollector,
    ExtensionAlertManager,
    ExtensionMonitoringDashboard,
    MetricType,
    AlertSeverity,
    Alert
)

from server.monitoring.alerting_system import (
    ExtensionAlertingSystem,
    NotificationChannel,
    EscalationLevel,
    AlertRule
)

from server.monitoring.performance_monitor import (
    ExtensionPerformanceMonitor,
    PerformanceMetric,
    EndpointStats
)

from server.monitoring.integration import (
    ExtensionMonitoringIntegration,
    monitoring_integration
)


class TestExtensionMetricsCollector:
    """Test the metrics collector component."""

    def setup_method(self):
        """Setup test fixtures."""
        self.collector = ExtensionMetricsCollector()

    def test_record_auth_success(self):
        """Test recording authentication success."""
        self.collector.record_auth_success(0.15, "user123")
        
        assert self.collector.auth_success_count == 1
        assert len(self.collector.auth_response_times) == 1
        assert self.collector.auth_response_times[0] == 0.15

    def test_record_auth_failure(self):
        """Test recording authentication failure."""
        self.collector.record_auth_failure(0.25, "invalid_token", "user456")
        
        assert self.collector.auth_failure_count == 1
        assert len(self.collector.auth_response_times) == 1
        assert self.collector.auth_response_times[0] == 0.25

    def test_record_token_refresh(self):
        """Test recording token refresh."""
        self.collector.record_token_refresh(0.1, True)
        
        assert self.collector.token_refresh_count == 1

    def test_record_service_health(self):
        """Test recording service health."""
        self.collector.record_service_health("test_service", "healthy", 0.05)
        
        assert self.collector.service_status["test_service"] == "healthy"
        assert len(self.collector.service_response_times["test_service"]) == 1

    def test_record_api_request(self):
        """Test recording API request."""
        self.collector.record_api_request("/api/test", "GET", 200, 0.12)
        
        assert self.collector.api_request_count == 1
        assert len(self.collector.api_response_times) == 1
        assert self.collector.endpoint_metrics["GET:/api/test"]["request_count"] == 1

    def test_get_auth_metrics(self):
        """Test getting authentication metrics."""
        # Record some test data
        self.collector.record_auth_success(0.1, "user1")
        self.collector.record_auth_success(0.15, "user2")
        self.collector.record_auth_failure(0.2, "invalid_token", "user3")
        
        metrics = self.collector.get_auth_metrics()
        
        assert metrics["total_requests"] == 3
        assert metrics["success_count"] == 2
        assert metrics["failure_count"] == 1
        assert metrics["success_rate"] == 66.67  # 2/3 * 100, rounded

    def test_get_service_health_metrics(self):
        """Test getting service health metrics."""
        self.collector.record_service_health("service1", "healthy", 0.05)
        self.collector.record_service_health("service2", "degraded", 0.15)
        
        metrics = self.collector.get_service_health_metrics()
        
        assert metrics["healthy_services"] == 1
        assert metrics["total_services"] == 2
        assert metrics["health_percentage"] == 50.0

    def test_get_api_performance_metrics(self):
        """Test getting API performance metrics."""
        self.collector.record_api_request("/api/test1", "GET", 200, 0.1)
        self.collector.record_api_request("/api/test2", "POST", 201, 0.15)
        self.collector.record_api_request("/api/test3", "GET", 500, 0.2)
        
        metrics = self.collector.get_api_performance_metrics()
        
        assert metrics["total_requests"] == 3
        assert metrics["error_count"] == 1
        assert metrics["error_rate"] == 33.33  # 1/3 * 100, rounded


class TestExtensionAlertManager:
    """Test the alert manager component."""

    def setup_method(self):
        """Setup test fixtures."""
        self.collector = ExtensionMetricsCollector()
        self.alert_manager = ExtensionAlertManager(self.collector)

    def test_add_alert(self):
        """Test adding an alert rule."""
        alert = Alert(
            id="test_alert",
            name="Test Alert",
            description="Test alert description",
            severity=AlertSeverity.WARNING,
            condition="test_condition > 10",
            threshold=10.0
        )
        
        self.alert_manager.add_alert(alert)
        
        assert "test_alert" in self.alert_manager.alerts
        assert self.alert_manager.alerts["test_alert"].name == "Test Alert"

    def test_remove_alert(self):
        """Test removing an alert rule."""
        alert = Alert(
            id="test_alert",
            name="Test Alert",
            description="Test alert description",
            severity=AlertSeverity.WARNING,
            condition="test_condition > 10",
            threshold=10.0
        )
        
        self.alert_manager.add_alert(alert)
        self.alert_manager.remove_alert("test_alert")
        
        assert "test_alert" not in self.alert_manager.alerts

    @pytest.mark.asyncio
    async def test_check_alerts_trigger(self):
        """Test alert triggering."""
        # Setup test data to trigger alert
        self.collector.record_auth_failure(0.1, "error", "user1")
        self.collector.record_auth_failure(0.1, "error", "user2")
        self.collector.record_auth_success(0.1, "user3")
        
        # Check alerts
        await self.alert_manager.check_alerts()
        
        # Should trigger auth_failure_rate_high alert (failure rate > 10%)
        active_alerts = self.alert_manager.get_active_alerts()
        assert len(active_alerts) > 0

    def test_get_active_alerts(self):
        """Test getting active alerts."""
        active_alerts = self.alert_manager.get_active_alerts()
        assert isinstance(active_alerts, list)

    def test_get_alert_history(self):
        """Test getting alert history."""
        history = self.alert_manager.get_alert_history()
        assert isinstance(history, list)


class TestExtensionAlertingSystem:
    """Test the advanced alerting system."""

    def setup_method(self):
        """Setup test fixtures."""
        self.alerting_system = ExtensionAlertingSystem()

    def test_add_alert_rule(self):
        """Test adding alert rule."""
        rule = AlertRule(
            id="test_rule",
            name="Test Rule",
            description="Test rule description",
            condition="test_metric > 50",
            threshold=50.0,
            severity="warning"
        )
        
        self.alerting_system.add_alert_rule(rule)
        
        assert "test_rule" in self.alerting_system.alert_rules

    def test_remove_alert_rule(self):
        """Test removing alert rule."""
        rule = AlertRule(
            id="test_rule",
            name="Test Rule",
            description="Test rule description",
            condition="test_metric > 50",
            threshold=50.0,
            severity="warning"
        )
        
        self.alerting_system.add_alert_rule(rule)
        self.alerting_system.remove_alert_rule("test_rule")
        
        assert "test_rule" not in self.alerting_system.alert_rules

    def test_configure_notification_channel(self):
        """Test configuring notification channel."""
        config = {
            'enabled': True,
            'webhook_url': 'https://example.com/webhook'
        }
        
        self.alerting_system.configure_notification_channel(
            NotificationChannel.WEBHOOK,
            config
        )
        
        assert NotificationChannel.WEBHOOK in self.alerting_system.notification_configs
        assert self.alerting_system.notification_configs[NotificationChannel.WEBHOOK].enabled

    @pytest.mark.asyncio
    async def test_evaluate_alerts(self):
        """Test alert evaluation."""
        metrics = {
            'auth_failure_rate': 30.0,  # Should trigger critical alert
            'service_health_percentage': 90.0,
            'api_error_rate': 2.0,
            'avg_response_time': 1000.0
        }
        
        await self.alerting_system.evaluate_alerts(metrics)
        
        # Check if critical auth failure alert was triggered
        stats = self.alerting_system.get_alert_statistics()
        assert stats['active_alerts'] > 0

    def test_get_alert_statistics(self):
        """Test getting alert statistics."""
        stats = self.alerting_system.get_alert_statistics()
        
        assert 'active_alerts' in stats
        assert 'total_rules' in stats
        assert 'configured_channels' in stats


class TestExtensionPerformanceMonitor:
    """Test the performance monitor component."""

    def setup_method(self):
        """Setup test fixtures."""
        self.monitor = ExtensionPerformanceMonitor()

    def test_record_request(self):
        """Test recording request performance."""
        self.monitor.record_request("/api/test", "GET", 0.15, 200)
        
        assert len(self.monitor.metrics) == 1
        assert "GET:/api/test" in self.monitor.endpoint_stats
        
        stats = self.monitor.endpoint_stats["GET:/api/test"]
        assert stats.total_requests == 1
        assert stats.average_response_time == 0.15

    def test_endpoint_stats_calculation(self):
        """Test endpoint statistics calculation."""
        # Record multiple requests
        self.monitor.record_request("/api/test", "GET", 0.1, 200)
        self.monitor.record_request("/api/test", "GET", 0.2, 200)
        self.monitor.record_request("/api/test", "GET", 0.3, 500)  # Error
        
        stats = self.monitor.endpoint_stats["GET:/api/test"]
        
        assert stats.total_requests == 3
        assert stats.error_count == 1
        assert stats.error_rate == 33.33  # 1/3 * 100, rounded
        assert stats.average_response_time == 0.2  # (0.1 + 0.2 + 0.3) / 3

    def test_get_performance_summary(self):
        """Test getting performance summary."""
        self.monitor.record_request("/api/test1", "GET", 0.1, 200)
        self.monitor.record_request("/api/test2", "POST", 0.2, 201)
        self.monitor.record_request("/api/test3", "GET", 0.3, 500)
        
        summary = self.monitor.get_performance_summary()
        
        assert summary["total_requests"] == 3
        assert summary["total_errors"] == 1
        assert summary["endpoints_count"] == 3

    def test_get_endpoint_performance(self):
        """Test getting endpoint performance data."""
        self.monitor.record_request("/api/popular", "GET", 0.1, 200)
        self.monitor.record_request("/api/popular", "GET", 0.15, 200)
        self.monitor.record_request("/api/rare", "POST", 0.2, 201)
        
        performance_data = self.monitor.get_endpoint_performance(limit=10)
        
        assert len(performance_data) == 2
        # Should be sorted by request count (popular first)
        assert performance_data[0]["endpoint"] == "GET:/api/popular"
        assert performance_data[0]["total_requests"] == 2

    @pytest.mark.asyncio
    async def test_start_stop_monitoring(self):
        """Test starting and stopping monitoring."""
        await self.monitor.start_monitoring(resource_check_interval=1)
        assert self.monitor.monitoring_active
        
        await asyncio.sleep(0.1)  # Let it run briefly
        
        await self.monitor.stop_monitoring()
        assert not self.monitor.monitoring_active

    @pytest.mark.asyncio
    async def test_measure_request_context_manager(self):
        """Test the request measurement context manager."""
        async with self.monitor.measure_request("/api/test", "GET", "user123"):
            await asyncio.sleep(0.01)  # Simulate work
        
        assert len(self.monitor.metrics) == 1
        metric = self.monitor.metrics[0]
        assert metric.endpoint == "/api/test"
        assert metric.method == "GET"
        assert metric.user_id == "user123"
        assert metric.response_time > 0


class TestExtensionMonitoringIntegration:
    """Test the monitoring integration component."""

    def setup_method(self):
        """Setup test fixtures."""
        self.integration = ExtensionMonitoringIntegration()

    @pytest.mark.asyncio
    async def test_initialize_and_shutdown(self):
        """Test initialization and shutdown."""
        config = {
            'notifications': {
                'log': {'enabled': True, 'level': 'info'}
            },
            'monitoring': {
                'dashboard_check_interval': 60,
                'resource_check_interval': 60,
                'alert_check_interval': 30
            }
        }
        
        await self.integration.initialize(config)
        assert self.integration.initialized
        
        await self.integration.shutdown()
        assert not self.integration.initialized

    def test_record_metrics_methods(self):
        """Test metric recording methods."""
        # These should work even when not initialized (graceful degradation)
        self.integration.record_auth_success(0.1, "user1")
        self.integration.record_auth_failure(0.2, "error", "user2")
        self.integration.record_api_request("/api/test", "GET", 200, 0.15)
        
        # No exceptions should be raised

    def test_get_monitoring_status(self):
        """Test getting monitoring status."""
        status = self.integration.get_monitoring_status()
        
        assert 'initialized' in status
        assert 'status' in status


class TestMonitoringSystemIntegration:
    """Integration tests for the complete monitoring system."""

    @pytest.mark.asyncio
    async def test_end_to_end_monitoring_flow(self):
        """Test complete monitoring flow from metrics to alerts."""
        # Initialize monitoring
        integration = ExtensionMonitoringIntegration()
        config = {
            'notifications': {
                'log': {'enabled': True, 'level': 'warning'}
            },
            'monitoring': {
                'dashboard_check_interval': 1,
                'resource_check_interval': 5,
                'alert_check_interval': 1
            }
        }
        
        try:
            await integration.initialize(config)
            
            # Record metrics that should trigger alerts
            for i in range(10):
                integration.record_auth_failure(0.1, "invalid_token", f"user{i}")
            
            integration.record_auth_success(0.1, "user_success")
            
            # Wait for alert evaluation
            await asyncio.sleep(2)
            
            # Check that alerts were triggered
            status = integration.get_monitoring_status()
            assert status['initialized']
            
            # The auth failure rate should be high enough to trigger alerts
            dashboard_data = status['dashboard']
            assert dashboard_data['auth_success_rate'] < 50  # Should be low due to failures
            
        finally:
            await integration.shutdown()

    @pytest.mark.asyncio
    async def test_performance_monitoring_integration(self):
        """Test performance monitoring integration."""
        monitor = ExtensionPerformanceMonitor()
        
        try:
            await monitor.start_monitoring(resource_check_interval=1)
            
            # Record various performance metrics
            monitor.record_request("/api/fast", "GET", 0.05, 200)
            monitor.record_request("/api/slow", "POST", 2.5, 200)  # Should trigger alert
            monitor.record_request("/api/error", "GET", 0.1, 500)
            
            # Wait for monitoring to process
            await asyncio.sleep(1.5)
            
            # Check performance summary
            summary = monitor.get_performance_summary()
            assert summary['total_requests'] == 3
            assert summary['total_errors'] == 1
            
            # Check endpoint performance
            endpoint_perf = monitor.get_endpoint_performance()
            assert len(endpoint_perf) == 3
            
        finally:
            await monitor.stop_monitoring()

    def test_configuration_validation(self):
        """Test configuration validation."""
        from server.monitoring.config_example import validate_config
        
        # Valid configuration
        valid_config = {
            'notifications': {
                'log': {'enabled': True, 'level': 'info'}
            },
            'monitoring': {
                'dashboard_check_interval': 30,
                'resource_check_interval': 30,
                'alert_check_interval': 15
            }
        }
        
        assert validate_config(valid_config)
        
        # Invalid configuration (missing monitoring section)
        invalid_config = {
            'notifications': {
                'log': {'enabled': True, 'level': 'info'}
            }
        }
        
        with pytest.raises(ValueError):
            validate_config(invalid_config)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])