"""
Unit tests for ExtensionServiceMonitor health monitoring components.

Tests the core health monitoring functionality including:
- Health check execution
- Service status tracking
- Failure detection and counting
- Recovery attempt triggering
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
from enum import Enum

# Import the components we're testing
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))

from server.extension_health_monitor import (
    ExtensionServiceMonitor,
    ServiceStatus,
    ExtensionStatus
)


class TestExtensionServiceMonitor:
    """Test suite for ExtensionServiceMonitor."""

    @pytest.fixture
    def mock_extension_manager(self):
        """Create mock extension manager."""
        manager = Mock()
        manager.is_initialized.return_value = True
        manager.registry = Mock()
        manager.registry.get_all_extensions.return_value = {
            'test_extension': Mock(
                status=ExtensionStatus.ACTIVE,
                instance=Mock(),
                manifest=Mock(name='test_extension')
            )
        }
        manager.check_extension_health = AsyncMock(return_value=True)
        manager.reload_extension = AsyncMock()
        manager.reinitialize = AsyncMock()
        return manager

    @pytest.fixture
    def service_monitor(self, mock_extension_manager):
        """Create ExtensionServiceMonitor instance."""
        return ExtensionServiceMonitor(mock_extension_manager)

    @pytest.mark.asyncio
    async def test_initialization(self, service_monitor, mock_extension_manager):
        """Test service monitor initialization."""
        assert service_monitor.extension_manager == mock_extension_manager
        assert service_monitor.service_status == {}
        assert service_monitor.last_health_check == {}
        assert service_monitor.failure_counts == {}
        assert service_monitor.monitoring_active is False

    @pytest.mark.asyncio
    async def test_extension_manager_health_check_success(self, service_monitor):
        """Test successful extension manager health check."""
        result = await service_monitor.check_extension_manager_health()
        
        assert result is True
        assert service_monitor.service_status['extension_manager'] == ServiceStatus.HEALTHY
        assert 'extension_manager' in service_monitor.last_health_check
        assert service_monitor.failure_counts['extension_manager'] == 0

    @pytest.mark.asyncio
    async def test_extension_manager_health_check_failure(self, service_monitor):
        """Test extension manager health check failure."""
        service_monitor.extension_manager.is_initialized.return_value = False
        
        result = await service_monitor.check_extension_manager_health()
        
        assert result is False
        assert service_monitor.service_status['extension_manager'] == ServiceStatus.UNHEALTHY
        assert service_monitor.failure_counts['extension_manager'] == 1

    @pytest.mark.asyncio
    async def test_extension_health_check_success(self, service_monitor):
        """Test successful extension health check."""
        extension_name = 'test_extension'
        extension_record = Mock(
            status=ExtensionStatus.ACTIVE,
            instance=Mock()
        )
        
        result = await service_monitor.check_extension_health(extension_name, extension_record)
        
        assert result is True
        assert service_monitor.service_status[extension_name] == ServiceStatus.HEALTHY
        assert extension_name in service_monitor.last_health_check
        assert service_monitor.failure_counts[extension_name] == 0

    @pytest.mark.asyncio
    async def test_extension_health_check_degraded(self, service_monitor):
        """Test extension health check with degraded status."""
        extension_name = 'test_extension'
        extension_record = Mock(
            status=ExtensionStatus.LOADING,  # Not ACTIVE
            instance=Mock()
        )
        
        result = await service_monitor.check_extension_health(extension_name, extension_record)
        
        assert result is False
        assert service_monitor.service_status[extension_name] == ServiceStatus.DEGRADED

    @pytest.mark.asyncio
    async def test_extension_health_check_failure(self, service_monitor):
        """Test extension health check failure."""
        extension_name = 'test_extension'
        extension_record = Mock(
            status=ExtensionStatus.ACTIVE,
            instance=Mock()
        )
        
        # Make health check fail
        service_monitor.extension_manager.check_extension_health.return_value = False
        
        result = await service_monitor.check_extension_health(extension_name, extension_record)
        
        assert result is False
        assert service_monitor.service_status[extension_name] == ServiceStatus.DEGRADED
        assert service_monitor.failure_counts[extension_name] == 1

    @pytest.mark.asyncio
    async def test_failure_count_increment(self, service_monitor):
        """Test that failure counts increment correctly."""
        extension_name = 'test_extension'
        extension_record = Mock(
            status=ExtensionStatus.ACTIVE,
            instance=Mock()
        )
        
        # Make health check fail
        service_monitor.extension_manager.check_extension_health.return_value = False
        
        # First failure
        await service_monitor.check_extension_health(extension_name, extension_record)
        assert service_monitor.failure_counts[extension_name] == 1
        
        # Second failure
        await service_monitor.check_extension_health(extension_name, extension_record)
        assert service_monitor.failure_counts[extension_name] == 2

    @pytest.mark.asyncio
    async def test_recovery_attempt_triggered(self, service_monitor):
        """Test that recovery is attempted after threshold failures."""
        extension_name = 'test_extension'
        extension_record = Mock(
            status=ExtensionStatus.ACTIVE,
            instance=Mock()
        )
        
        # Set failure count to threshold - 1
        service_monitor.failure_counts[extension_name] = 2
        
        # Make health check fail (should trigger recovery)
        service_monitor.extension_manager.check_extension_health.return_value = False
        
        with patch.object(service_monitor, 'attempt_extension_recovery') as mock_recovery:
            await service_monitor.check_extension_health(extension_name, extension_record)
            mock_recovery.assert_called_once_with(extension_name)

    @pytest.mark.asyncio
    async def test_manager_recovery_attempt(self, service_monitor):
        """Test extension manager recovery attempt."""
        await service_monitor.attempt_manager_recovery()
        
        # Verify reinitialize was called
        service_monitor.extension_manager.reinitialize.assert_called_once()

    @pytest.mark.asyncio
    async def test_extension_recovery_attempt(self, service_monitor):
        """Test extension recovery attempt."""
        extension_name = 'test_extension'
        
        # Mock successful recovery
        recovered_record = Mock(status=ExtensionStatus.ACTIVE)
        service_monitor.extension_manager.reload_extension.return_value = recovered_record
        
        await service_monitor.attempt_extension_recovery(extension_name)
        
        # Verify reload was called and failure count reset
        service_monitor.extension_manager.reload_extension.assert_called_once_with(extension_name)
        assert service_monitor.failure_counts[extension_name] == 0

    @pytest.mark.asyncio
    async def test_perform_health_checks(self, service_monitor):
        """Test complete health check cycle."""
        await service_monitor.perform_health_checks()
        
        # Verify manager health check was performed
        assert 'extension_manager' in service_monitor.service_status
        
        # Verify extension health checks were performed
        assert 'test_extension' in service_monitor.service_status

    def test_get_service_status(self, service_monitor):
        """Test service status reporting."""
        # Set up some test data
        service_monitor.service_status['test_service'] = ServiceStatus.HEALTHY
        service_monitor.last_health_check['test_service'] = datetime.utcnow()
        service_monitor.failure_counts['test_service'] = 0
        service_monitor.monitoring_active = True
        
        status = service_monitor.get_service_status()
        
        assert 'services' in status
        assert 'overall_health' in status
        assert 'monitoring_active' in status
        assert status['monitoring_active'] is True
        assert 'test_service' in status['services']

    def test_calculate_overall_health_all_healthy(self, service_monitor):
        """Test overall health calculation when all services are healthy."""
        service_monitor.service_status = {
            'service1': ServiceStatus.HEALTHY,
            'service2': ServiceStatus.HEALTHY
        }
        
        overall_health = service_monitor._calculate_overall_health()
        assert overall_health == ServiceStatus.HEALTHY.value

    def test_calculate_overall_health_degraded(self, service_monitor):
        """Test overall health calculation when some services are degraded."""
        service_monitor.service_status = {
            'service1': ServiceStatus.HEALTHY,
            'service2': ServiceStatus.DEGRADED,
            'service3': ServiceStatus.HEALTHY
        }
        
        overall_health = service_monitor._calculate_overall_health()
        assert overall_health == ServiceStatus.DEGRADED.value

    def test_calculate_overall_health_unhealthy(self, service_monitor):
        """Test overall health calculation when most services are unhealthy."""
        service_monitor.service_status = {
            'service1': ServiceStatus.UNHEALTHY,
            'service2': ServiceStatus.UNHEALTHY,
            'service3': ServiceStatus.HEALTHY
        }
        
        overall_health = service_monitor._calculate_overall_health()
        assert overall_health == ServiceStatus.UNHEALTHY.value

    def test_calculate_overall_health_unknown(self, service_monitor):
        """Test overall health calculation when no services are monitored."""
        service_monitor.service_status = {}
        
        overall_health = service_monitor._calculate_overall_health()
        assert overall_health == ServiceStatus.UNKNOWN.value

    @pytest.mark.asyncio
    async def test_monitoring_loop_start_stop(self, service_monitor):
        """Test monitoring loop start and stop."""
        # Start monitoring with very short interval
        monitoring_task = asyncio.create_task(
            service_monitor.start_monitoring(check_interval=0.1)
        )
        
        # Let it run briefly
        await asyncio.sleep(0.2)
        
        # Stop monitoring
        await service_monitor.stop_monitoring()
        
        # Wait for task to complete
        await asyncio.sleep(0.1)
        
        assert service_monitor.monitoring_active is False
        monitoring_task.cancel()

    @pytest.mark.asyncio
    async def test_exception_handling_in_health_checks(self, service_monitor):
        """Test exception handling during health checks."""
        # Make extension manager throw exception
        service_monitor.extension_manager.is_initialized.side_effect = Exception("Test error")
        
        # Should not raise exception
        result = await service_monitor.check_extension_manager_health()
        
        assert result is False
        assert service_monitor.service_status['extension_manager'] == ServiceStatus.UNHEALTHY

    @pytest.mark.asyncio
    async def test_recovery_exception_handling(self, service_monitor):
        """Test exception handling during recovery attempts."""
        # Make recovery throw exception
        service_monitor.extension_manager.reinitialize.side_effect = Exception("Recovery failed")
        
        # Should not raise exception
        await service_monitor.attempt_manager_recovery()
        
        # Failure count should not be reset
        service_monitor.failure_counts['extension_manager'] = 5
        await service_monitor.attempt_manager_recovery()
        assert service_monitor.failure_counts['extension_manager'] == 5


class TestServiceStatusEnum:
    """Test ServiceStatus enum."""

    def test_service_status_values(self):
        """Test ServiceStatus enum values."""
        assert ServiceStatus.HEALTHY.value == "healthy"
        assert ServiceStatus.DEGRADED.value == "degraded"
        assert ServiceStatus.UNHEALTHY.value == "unhealthy"
        assert ServiceStatus.UNKNOWN.value == "unknown"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])