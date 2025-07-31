"""
Tests for the comprehensive health monitoring system.

This module tests the health monitoring capabilities for intelligent authentication
components, including alerting, recovery mechanisms, and metrics collection.
"""

import asyncio
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any

from ai_karen_engine.security.health_monitor import (
    HealthMonitor,
    HealthAlert,
    HealthMetrics,
    RecoveryAction,
    AlertType,
    AlertSeverity,
    log_alert_handler,
    console_alert_handler,
    create_reinitialize_action,
    create_restart_action,
    create_cache_clear_action
)
from ai_karen_engine.security.intelligent_auth_base import (
    ServiceRegistry,
    ServiceStatus,
    ServiceHealthStatus
)


class TestHealthMonitor:
    """Test cases for HealthMonitor."""

    @pytest.fixture
    def service_registry(self):
        """Create test service registry."""
        registry = ServiceRegistry()
        
        # Mock services
        healthy_service = Mock()
        healthy_service.health_check = AsyncMock(return_value=ServiceHealthStatus(
            service_name="healthy_service",
            status=ServiceStatus.HEALTHY,
            last_check=datetime.now(),
            response_time=0.1
        ))
        
        unhealthy_service = Mock()
        unhealthy_service.health_check = AsyncMock(return_value=ServiceHealthStatus(
            service_name="unhealthy_service",
            status=ServiceStatus.UNHEALTHY,
            last_check=datetime.now(),
            response_time=2.0,
            error_message="Service unavailable"
        ))
        
        registry.register_service("healthy_service", healthy_service)
        registry.register_service("unhealthy_service", unhealthy_service)
        
        return registry

    @pytest.fixture
    def health_monitor(self, service_registry):
        """Create test health monitor."""
        return HealthMonitor(
            service_registry=service_registry,
            check_interval=0.1,  # Fast interval for testing
            alert_thresholds={
                'response_time_warning': 1.0,
                'response_time_critical': 2.0,
                'error_rate_warning': 0.2,
                'error_rate_critical': 0.5
            }
        )

    @pytest.mark.asyncio
    async def test_health_monitor_initialization(self, service_registry):
        """Test health monitor initialization."""
        monitor = HealthMonitor(service_registry)
        
        assert monitor.service_registry == service_registry
        assert monitor.check_interval == 60.0  # Default
        assert monitor.enable_recovery is True
        assert not monitor._monitoring
        assert monitor._monitor_task is None

    @pytest.mark.asyncio
    async def test_start_stop_monitoring(self, health_monitor):
        """Test starting and stopping monitoring."""
        # Start monitoring
        await health_monitor.start_monitoring()
        assert health_monitor._monitoring is True
        assert health_monitor._monitor_task is not None
        
        # Wait a bit for some checks
        await asyncio.sleep(0.3)
        
        # Stop monitoring
        await health_monitor.stop_monitoring()
        assert health_monitor._monitoring is False

    @pytest.mark.asyncio
    async def test_health_check_execution(self, health_monitor):
        """Test health check execution."""
        # Perform manual health check
        await health_monitor._perform_health_checks()
        
        # Check that metrics were created
        metrics = health_monitor.get_all_metrics()
        assert "healthy_service" in metrics
        assert "unhealthy_service" in metrics
        
        # Check healthy service metrics
        healthy_metrics = metrics["healthy_service"]
        assert healthy_metrics.total_checks == 1
        assert healthy_metrics.successful_checks == 1
        assert healthy_metrics.failed_checks == 0
        assert healthy_metrics.uptime_percentage == 1.0
        
        # Check unhealthy service metrics
        unhealthy_metrics = metrics["unhealthy_service"]
        assert unhealthy_metrics.total_checks == 1
        assert unhealthy_metrics.successful_checks == 0
        assert unhealthy_metrics.failed_checks == 1
        assert unhealthy_metrics.uptime_percentage == 0.0

    @pytest.mark.asyncio
    async def test_alert_generation(self, health_monitor):
        """Test alert generation for unhealthy services."""
        # Perform health check
        await health_monitor._perform_health_checks()
        
        # Check that alerts were generated
        alerts = health_monitor.get_recent_alerts()
        assert len(alerts) > 0
        
        # Should have alerts for unhealthy service
        unhealthy_alerts = [
            alert for alert in alerts 
            if alert.service_name == "unhealthy_service"
        ]
        assert len(unhealthy_alerts) > 0
        
        # Check alert properties
        alert = unhealthy_alerts[0]
        assert alert.alert_type in [AlertType.SERVICE_DOWN, AlertType.SLOW_RESPONSE]
        assert alert.severity in [AlertSeverity.CRITICAL, AlertSeverity.WARNING]
        assert not alert.resolved

    @pytest.mark.asyncio
    async def test_alert_handlers(self, health_monitor):
        """Test alert handler functionality."""
        alerts_received = []
        
        async def test_handler(alert: HealthAlert):
            alerts_received.append(alert)
        
        # Add alert handler
        health_monitor.add_alert_handler(test_handler)
        
        # Perform health check to generate alerts
        await health_monitor._perform_health_checks()
        
        # Wait a bit for alert processing
        await asyncio.sleep(0.1)
        
        # Check that handler received alerts
        assert len(alerts_received) > 0

    @pytest.mark.asyncio
    async def test_recovery_actions(self, health_monitor):
        """Test service recovery functionality."""
        # Create mock service with recovery methods
        mock_service = Mock()
        mock_service.health_check = AsyncMock(return_value=ServiceHealthStatus(
            service_name="recoverable_service",
            status=ServiceStatus.UNHEALTHY,
            last_check=datetime.now(),
            response_time=0.1,
            error_message="Service down"
        ))
        mock_service.initialize = AsyncMock(return_value=True)
        
        # Register service
        health_monitor.service_registry.register_service("recoverable_service", mock_service)
        
        # Add recovery action
        recovery_action = RecoveryAction(
            service_name="recoverable_service",
            action_name="test_recovery",
            action_function=mock_service.initialize,
            max_attempts=1,
            retry_delay=0.1
        )
        health_monitor.add_recovery_action(recovery_action)
        
        # Perform health check (should trigger recovery)
        await health_monitor._check_service_health("recoverable_service")
        
        # Wait for recovery attempt
        await asyncio.sleep(0.2)
        
        # Check that recovery was attempted
        mock_service.initialize.assert_called()

    @pytest.mark.asyncio
    async def test_metrics_calculation(self, health_monitor):
        """Test metrics calculation over multiple checks."""
        # Perform multiple health checks
        for _ in range(5):
            await health_monitor._perform_health_checks()
            await asyncio.sleep(0.05)
        
        # Check metrics
        metrics = health_monitor.get_service_metrics("healthy_service")
        assert metrics is not None
        assert metrics.total_checks == 5
        assert metrics.successful_checks == 5
        assert metrics.uptime_percentage == 1.0
        assert metrics.error_rate == 0.0
        
        unhealthy_metrics = health_monitor.get_service_metrics("unhealthy_service")
        assert unhealthy_metrics is not None
        assert unhealthy_metrics.total_checks == 5
        assert unhealthy_metrics.failed_checks == 5
        assert unhealthy_metrics.uptime_percentage == 0.0
        assert unhealthy_metrics.error_rate == 1.0

    @pytest.mark.asyncio
    async def test_health_status_aggregation(self, health_monitor):
        """Test overall health status aggregation."""
        # Perform health check
        await health_monitor._perform_health_checks()
        
        # Get overall health status
        health_status = health_monitor.get_current_health_status()
        
        # Should be unhealthy due to unhealthy service
        assert health_status.overall_status == ServiceStatus.UNHEALTHY
        assert len(health_status.component_statuses) == 2
        assert "healthy_service" in health_status.component_statuses
        assert "unhealthy_service" in health_status.component_statuses

    @pytest.mark.asyncio
    async def test_alert_resolution(self, health_monitor):
        """Test alert resolution functionality."""
        # Generate alerts
        await health_monitor._perform_health_checks()
        
        # Get unresolved alerts
        unresolved = health_monitor.get_unresolved_alerts()
        assert len(unresolved) > 0
        
        # Resolve an alert
        alert_id = unresolved[0].alert_id
        success = health_monitor.resolve_alert(alert_id)
        assert success is True
        
        # Check that alert is resolved
        new_unresolved = health_monitor.get_unresolved_alerts()
        assert len(new_unresolved) == len(unresolved) - 1

    @pytest.mark.asyncio
    async def test_force_health_check(self, health_monitor):
        """Test forced health check functionality."""
        # Force check on specific service
        await health_monitor.force_health_check("healthy_service")
        
        # Check that metrics were updated
        metrics = health_monitor.get_service_metrics("healthy_service")
        assert metrics is not None
        assert metrics.total_checks == 1

    def test_alert_threshold_updates(self, health_monitor):
        """Test updating alert thresholds."""
        new_thresholds = {
            'response_time_warning': 0.5,
            'error_rate_critical': 0.8
        }
        
        health_monitor.update_alert_thresholds(new_thresholds)
        
        assert health_monitor.alert_thresholds['response_time_warning'] == 0.5
        assert health_monitor.alert_thresholds['error_rate_critical'] == 0.8

    def test_monitoring_statistics(self, health_monitor):
        """Test monitoring statistics collection."""
        stats = health_monitor.get_monitoring_statistics()
        
        assert 'monitoring_active' in stats
        assert 'check_interval' in stats
        assert 'total_health_checks' in stats
        assert 'services_monitored' in stats
        assert stats['check_interval'] == 0.1

    @pytest.mark.asyncio
    async def test_health_history_tracking(self, health_monitor):
        """Test health history tracking."""
        # Perform multiple checks
        for _ in range(3):
            await health_monitor._perform_health_checks()
            await asyncio.sleep(0.05)
        
        # Get health history
        history = health_monitor.get_health_history("healthy_service")
        assert len(history) == 3
        
        # All should be healthy
        for status in history:
            assert status.status == ServiceStatus.HEALTHY

    @pytest.mark.asyncio
    async def test_duplicate_alert_prevention(self, health_monitor):
        """Test that duplicate alerts are not created."""
        # Perform multiple checks quickly
        for _ in range(3):
            await health_monitor._perform_health_checks()
        
        # Should not have many duplicate alerts
        alerts = health_monitor.get_recent_alerts()
        service_down_alerts = [
            alert for alert in alerts 
            if (alert.alert_type == AlertType.SERVICE_DOWN and 
                alert.service_name == "unhealthy_service")
        ]
        
        # Should have limited number of duplicate alerts
        assert len(service_down_alerts) <= 2  # Some duplicates allowed but limited

    @pytest.mark.asyncio
    async def test_recovery_action_utilities(self):
        """Test recovery action utility functions."""
        mock_service = Mock()
        mock_service.initialize = AsyncMock(return_value=True)
        mock_service.shutdown = AsyncMock()
        mock_service.cache = Mock()
        mock_service.cache.clear = Mock()
        
        # Test reinitialize action
        reinit_action = create_reinitialize_action("test_service", mock_service)
        assert reinit_action.service_name == "test_service"
        assert reinit_action.action_name == "reinitialize"
        
        success = await reinit_action.action_function()
        assert success is True
        mock_service.initialize.assert_called_once()
        
        # Test restart action
        restart_action = create_restart_action("test_service", mock_service)
        assert restart_action.action_name == "restart"
        
        success = await restart_action.action_function()
        assert success is True
        mock_service.shutdown.assert_called_once()
        
        # Test cache clear action
        cache_action = create_cache_clear_action("test_service", mock_service)
        assert cache_action.action_name == "clear_cache"
        
        success = await cache_action.action_function()
        assert success is True
        mock_service.cache.clear.assert_called_once()

    @pytest.mark.asyncio
    async def test_default_alert_handlers(self):
        """Test default alert handlers."""
        alert = HealthAlert(
            alert_id="test_alert",
            alert_type=AlertType.SERVICE_DOWN,
            severity=AlertSeverity.CRITICAL,
            service_name="test_service",
            message="Test alert message",
            timestamp=datetime.now()
        )
        
        # Test log alert handler (should not raise exception)
        await log_alert_handler(alert)
        
        # Test console alert handler (should not raise exception)
        with patch('builtins.print') as mock_print:
            await console_alert_handler(alert)
            mock_print.assert_called_once()

    @pytest.mark.asyncio
    async def test_monitor_shutdown(self, health_monitor):
        """Test health monitor shutdown."""
        # Start monitoring
        await health_monitor.start_monitoring()
        
        # Perform some checks
        await asyncio.sleep(0.2)
        
        # Shutdown
        await health_monitor.shutdown()
        
        # Check that monitoring stopped and data cleared
        assert not health_monitor._monitoring
        assert len(health_monitor._health_history) == 0
        assert len(health_monitor._metrics) == 0
        assert len(health_monitor._alerts) == 0


if __name__ == "__main__":
    pytest.main([__file__])