"""
Integration tests for service recovery mechanisms.

Tests the complete recovery flow including:
- Service failure detection
- Automatic recovery attempts
- Service restoration
- End-to-end recovery scenarios
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))

from server.extension_health_monitor import (
    ExtensionServiceMonitor,
    ServiceStatus,
    ExtensionStatus
)


class TestServiceRecoveryIntegration:
    """Integration tests for service recovery mechanisms."""

    @pytest.fixture
    async def extension_manager_with_failures(self):
        """Create extension manager that simulates failures and recovery."""
        manager = Mock()
        manager.is_initialized = Mock()
        manager.registry = Mock()
        manager.check_extension_health = AsyncMock()
        manager.reload_extension = AsyncMock()
        manager.reinitialize = AsyncMock()
        
        # Simulate failure states
        manager._failure_mode = False
        manager._recovery_attempts = 0
        
        def toggle_failure_mode():
            manager._failure_mode = not manager._failure_mode
            
        def simulate_recovery():
            manager._recovery_attempts += 1
            if manager._recovery_attempts >= 2:  # Recover after 2 attempts
                manager._failure_mode = False
                
        manager.toggle_failure_mode = toggle_failure_mode
        manager.simulate_recovery = simulate_recovery
        
        # Mock methods that respond to failure mode
        def is_initialized_side_effect():
            return not manager._failure_mode
            
        def get_extensions_side_effect():
            if manager._failure_mode:
                return {}
            return {
                'test_extension': Mock(
                    status=ExtensionStatus.ACTIVE,
                    instance=Mock(),
                    manifest=Mock(name='test_extension')
                )
            }
            
        async def check_health_side_effect(name):
            return not manager._failure_mode
            
        async def reload_extension_side_effect(name):
            manager.simulate_recovery()
            if not manager._failure_mode:
                return Mock(status=ExtensionStatus.ACTIVE)
            return Mock(status=ExtensionStatus.ERROR)
            
        async def reinitialize_side_effect():
            manager.simulate_recovery()
            
        manager.is_initialized.side_effect = is_initialized_side_effect
        manager.registry.get_all_extensions.side_effect = get_extensions_side_effect
        manager.check_extension_health.side_effect = check_health_side_effect
        manager.reload_extension.side_effect = reload_extension_side_effect
        manager.reinitialize.side_effect = reinitialize_side_effect
        
        return manager

    @pytest.fixture
    def service_monitor_with_failures(self, extension_manager_with_failures):
        """Create service monitor with failure simulation."""
        return ExtensionServiceMonitor(extension_manager_with_failures)

    @pytest.mark.asyncio
    async def test_complete_failure_and_recovery_cycle(self, service_monitor_with_failures):
        """Test complete failure detection and recovery cycle."""
        monitor = service_monitor_with_failures
        manager = monitor.extension_manager
        
        # Initial healthy state
        await monitor.perform_health_checks()
        assert monitor.service_status['extension_manager'] == ServiceStatus.HEALTHY
        
        # Simulate failure
        manager.toggle_failure_mode()
        
        # First failure detection
        await monitor.perform_health_checks()
        assert monitor.service_status['extension_manager'] == ServiceStatus.UNHEALTHY
        assert monitor.failure_counts['extension_manager'] == 1
        
        # Second failure
        await monitor.perform_health_checks()
        assert monitor.failure_counts['extension_manager'] == 2
        
        # Third failure should trigger recovery
        await monitor.perform_health_checks()
        assert monitor.failure_counts['extension_manager'] == 3
        
        # Verify recovery was attempted
        assert manager._recovery_attempts >= 1
        
        # After recovery, should be healthy again
        await monitor.perform_health_checks()
        assert monitor.service_status['extension_manager'] == ServiceStatus.HEALTHY
        assert monitor.failure_counts['extension_manager'] == 0

    @pytest.mark.asyncio
    async def test_extension_specific_recovery(self, service_monitor_with_failures):
        """Test recovery of specific extension."""
        monitor = service_monitor_with_failures
        manager = monitor.extension_manager
        
        # Set up extension failure
        extension_name = 'test_extension'
        extension_record = Mock(
            status=ExtensionStatus.ACTIVE,
            instance=Mock()
        )
        
        # Simulate extension failure
        manager._failure_mode = True
        
        # Trigger failures until recovery threshold
        for i in range(3):
            await monitor.check_extension_health(extension_name, extension_record)
        
        # Verify recovery was attempted
        assert manager._recovery_attempts >= 1
        
        # Check that extension is recovered
        await monitor.check_extension_health(extension_name, extension_record)
        assert monitor.service_status[extension_name] == ServiceStatus.HEALTHY

    @pytest.mark.asyncio
    async def test_partial_system_recovery(self, service_monitor_with_failures):
        """Test recovery when only some services fail."""
        monitor = service_monitor_with_failures
        manager = monitor.extension_manager
        
        # Add multiple extensions
        def get_multiple_extensions():
            if manager._failure_mode:
                return {
                    'extension1': Mock(status=ExtensionStatus.ERROR),
                    'extension2': Mock(status=ExtensionStatus.ACTIVE),
                    'extension3': Mock(status=ExtensionStatus.ERROR)
                }
            return {
                'extension1': Mock(status=ExtensionStatus.ACTIVE),
                'extension2': Mock(status=ExtensionStatus.ACTIVE),
                'extension3': Mock(status=ExtensionStatus.ACTIVE)
            }
        
        manager.registry.get_all_extensions.side_effect = get_multiple_extensions
        
        # Simulate partial failure
        manager._failure_mode = True
        await monitor.perform_health_checks()
        
        # Check that system is degraded
        overall_health = monitor._calculate_overall_health()
        assert overall_health == ServiceStatus.DEGRADED.value
        
        # Simulate recovery
        manager._failure_mode = False
        await monitor.perform_health_checks()
        
        # Check that system is healthy again
        overall_health = monitor._calculate_overall_health()
        assert overall_health == ServiceStatus.HEALTHY.value

    @pytest.mark.asyncio
    async def test_recovery_timeout_handling(self, service_monitor_with_failures):
        """Test handling of recovery timeouts."""
        monitor = service_monitor_with_failures
        manager = monitor.extension_manager
        
        # Make recovery take a long time
        async def slow_recovery(*args):
            await asyncio.sleep(0.5)  # Simulate slow recovery
            manager.simulate_recovery()
        
        manager.reinitialize.side_effect = slow_recovery
        
        # Trigger failure and recovery
        manager._failure_mode = True
        monitor.failure_counts['extension_manager'] = 3
        
        start_time = time.time()
        await monitor.attempt_manager_recovery()
        end_time = time.time()
        
        # Verify recovery took expected time
        assert end_time - start_time >= 0.5
        
        # Verify recovery completed
        assert manager._recovery_attempts >= 1

    @pytest.mark.asyncio
    async def test_cascading_failure_recovery(self, service_monitor_with_failures):
        """Test recovery from cascading failures."""
        monitor = service_monitor_with_failures
        manager = monitor.extension_manager
        
        # Simulate cascading failure (manager fails, then extensions)
        manager._failure_mode = True
        
        # First, manager fails
        await monitor.check_extension_manager_health()
        assert monitor.service_status['extension_manager'] == ServiceStatus.UNHEALTHY
        
        # Then extensions fail
        extension_record = Mock(status=ExtensionStatus.ACTIVE, instance=Mock())
        await monitor.check_extension_health('test_extension', extension_record)
        assert monitor.service_status['test_extension'] == ServiceStatus.DEGRADED
        
        # Trigger recovery for manager (should fix everything)
        monitor.failure_counts['extension_manager'] = 3
        await monitor.attempt_manager_recovery()
        
        # Verify system recovery
        await monitor.perform_health_checks()
        assert monitor.service_status['extension_manager'] == ServiceStatus.HEALTHY

    @pytest.mark.asyncio
    async def test_recovery_with_monitoring_loop(self, service_monitor_with_failures):
        """Test recovery within the monitoring loop."""
        monitor = service_monitor_with_failures
        manager = monitor.extension_manager
        
        # Start monitoring with short interval
        monitoring_task = asyncio.create_task(
            monitor.start_monitoring(check_interval=0.1)
        )
        
        try:
            # Let it run and establish healthy state
            await asyncio.sleep(0.2)
            assert monitor.service_status.get('extension_manager') == ServiceStatus.HEALTHY
            
            # Introduce failure
            manager.toggle_failure_mode()
            
            # Wait for failure detection and recovery
            await asyncio.sleep(0.5)  # Allow multiple check cycles
            
            # Verify recovery occurred
            assert monitor.service_status.get('extension_manager') == ServiceStatus.HEALTHY
            assert manager._recovery_attempts >= 1
            
        finally:
            await monitor.stop_monitoring()
            monitoring_task.cancel()

    @pytest.mark.asyncio
    async def test_recovery_state_persistence(self, service_monitor_with_failures):
        """Test that recovery state is properly maintained."""
        monitor = service_monitor_with_failures
        manager = monitor.extension_manager
        
        # Simulate failure and partial recovery
        manager._failure_mode = True
        
        # Build up failure count
        for i in range(2):
            await monitor.check_extension_manager_health()
        
        assert monitor.failure_counts['extension_manager'] == 2
        
        # Simulate successful recovery
        manager._failure_mode = False
        await monitor.check_extension_manager_health()
        
        # Verify state was reset
        assert monitor.failure_counts['extension_manager'] == 0
        assert monitor.service_status['extension_manager'] == ServiceStatus.HEALTHY

    @pytest.mark.asyncio
    async def test_multiple_concurrent_recoveries(self, service_monitor_with_failures):
        """Test handling of multiple concurrent recovery attempts."""
        monitor = service_monitor_with_failures
        manager = monitor.extension_manager
        
        # Set up multiple failed services
        monitor.failure_counts['extension_manager'] = 3
        monitor.failure_counts['test_extension'] = 3
        
        # Attempt concurrent recoveries
        recovery_tasks = [
            asyncio.create_task(monitor.attempt_manager_recovery()),
            asyncio.create_task(monitor.attempt_extension_recovery('test_extension'))
        ]
        
        # Wait for all recoveries to complete
        await asyncio.gather(*recovery_tasks)
        
        # Verify both recoveries were attempted
        assert manager._recovery_attempts >= 1

    @pytest.mark.asyncio
    async def test_recovery_failure_handling(self, service_monitor_with_failures):
        """Test handling when recovery attempts fail."""
        monitor = service_monitor_with_failures
        manager = monitor.extension_manager
        
        # Make recovery always fail
        async def failing_recovery(*args):
            raise Exception("Recovery failed")
        
        manager.reinitialize.side_effect = failing_recovery
        
        # Attempt recovery
        await monitor.attempt_manager_recovery()
        
        # Verify failure count wasn't reset (recovery failed)
        monitor.failure_counts['extension_manager'] = 5
        await monitor.attempt_manager_recovery()
        assert monitor.failure_counts['extension_manager'] == 5

    @pytest.mark.asyncio
    async def test_health_status_during_recovery(self, service_monitor_with_failures):
        """Test health status reporting during recovery process."""
        monitor = service_monitor_with_failures
        manager = monitor.extension_manager
        
        # Set up failure state
        manager._failure_mode = True
        await monitor.perform_health_checks()
        
        # Get status during failure
        status_during_failure = monitor.get_service_status()
        assert status_during_failure['overall_health'] == ServiceStatus.UNHEALTHY.value
        
        # Trigger recovery
        manager._failure_mode = False
        await monitor.perform_health_checks()
        
        # Get status after recovery
        status_after_recovery = monitor.get_service_status()
        assert status_after_recovery['overall_health'] == ServiceStatus.HEALTHY.value
        
        # Verify failure counts were reset
        for service_name, service_info in status_after_recovery['services'].items():
            if service_info['status'] == ServiceStatus.HEALTHY.value:
                assert service_info['failure_count'] == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])