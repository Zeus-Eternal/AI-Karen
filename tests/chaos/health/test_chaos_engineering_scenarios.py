"""
Chaos engineering tests for health monitoring failure scenarios.

Tests system resilience under various failure conditions including:
- Random service failures
- Network partitions
- Resource exhaustion
- Cascading failures
- Recovery under stress
"""

import pytest
import asyncio
import random
import time
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
import threading
from concurrent.futures import ThreadPoolExecutor

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))

from server.extension_health_monitor import (
    ExtensionServiceMonitor,
    ServiceStatus,
    ExtensionStatus
)


class ChaosExtensionManager:
    """Extension manager that simulates various chaos scenarios."""
    
    def __init__(self):
        self.is_initialized = Mock(return_value=True)
        self.registry = Mock()
        self.check_extension_health = AsyncMock(return_value=True)
        self.reload_extension = AsyncMock()
        self.reinitialize = AsyncMock()
        
        # Chaos configuration
        self.chaos_config = {
            'failure_rate': 0.0,
            'network_partition': False,
            'resource_exhaustion': False,
            'slow_responses': False,
            'intermittent_failures': False,
            'cascading_failures': False
        }
        
        # State tracking
        self.call_count = 0
        self.failed_services = set()
        self.recovery_attempts = {}
        
        # Create test extensions
        self.extensions = {}
        for i in range(20):
            self.extensions[f'extension_{i}'] = Mock(
                status=ExtensionStatus.ACTIVE,
                instance=Mock(),
                manifest=Mock(name=f'extension_{i}')
            )
        
        self.registry.get_all_extensions.return_value = self.extensions
        
        # Set up chaos behaviors
        self._setup_chaos_behaviors()
    
    def _setup_chaos_behaviors(self):
        """Set up chaotic behaviors for testing."""
        
        def chaotic_is_initialized():
            self.call_count += 1
            
            if self.chaos_config['network_partition']:
                raise ConnectionError("Network partition simulated")
            
            if self.chaos_config['resource_exhaustion']:
                raise MemoryError("Resource exhaustion simulated")
            
            if self.chaos_config['cascading_failures'] and self.call_count > 5:
                return False
            
            return random.random() > self.chaos_config['failure_rate']
        
        async def chaotic_health_check(name):
            self.call_count += 1
            
            if self.chaos_config['slow_responses']:
                await asyncio.sleep(random.uniform(0.1, 1.0))
            
            if self.chaos_config['network_partition']:
                raise ConnectionError(f"Network partition for {name}")
            
            if self.chaos_config['intermittent_failures']:
                # Intermittent failures based on time
                if int(time.time()) % 3 == 0:
                    return False
            
            if name in self.failed_services:
                return False
            
            return random.random() > self.chaos_config['failure_rate']
        
        async def chaotic_reload(name):
            self.recovery_attempts[name] = self.recovery_attempts.get(name, 0) + 1
            
            if self.chaos_config['resource_exhaustion']:
                raise MemoryError("Cannot reload - resource exhaustion")
            
            # Recovery success rate depends on attempts
            success_rate = min(0.8, self.recovery_attempts[name] * 0.3)
            if random.random() < success_rate:
                self.failed_services.discard(name)
                return Mock(status=ExtensionStatus.ACTIVE)
            else:
                return Mock(status=ExtensionStatus.ERROR)
        
        async def chaotic_reinitialize():
            if self.chaos_config['cascading_failures']:
                # Reinitialize might cause more failures
                for ext_name in random.sample(list(self.extensions.keys()), 3):
                    self.failed_services.add(ext_name)
            
            await asyncio.sleep(0.1)  # Simulate reinit time
        
        self.is_initialized.side_effect = chaotic_is_initialized
        self.check_extension_health.side_effect = chaotic_health_check
        self.reload_extension.side_effect = chaotic_reload
        self.reinitialize.side_effect = chaotic_reinitialize
    
    def enable_chaos(self, scenario_config):
        """Enable specific chaos scenario."""
        self.chaos_config.update(scenario_config)
        self.call_count = 0
        self.failed_services.clear()
        self.recovery_attempts.clear()
    
    def inject_failures(self, service_names):
        """Inject failures for specific services."""
        self.failed_services.update(service_names)


class TestChaosEngineeringScenarios:
    """Chaos engineering tests for health monitoring."""

    @pytest.fixture
    def chaos_manager(self):
        """Create chaos-enabled extension manager."""
        return ChaosExtensionManager()

    @pytest.fixture
    def chaos_monitor(self, chaos_manager):
        """Create service monitor with chaos manager."""
        return ExtensionServiceMonitor(chaos_manager)

    @pytest.mark.asyncio
    async def test_random_service_failures(self, chaos_monitor, chaos_manager):
        """Test system behavior under random service failures."""
        monitor = chaos_monitor
        manager = chaos_manager
        
        # Enable random failures
        manager.enable_chaos({'failure_rate': 0.3})  # 30% failure rate
        
        # Run multiple health check cycles
        healthy_cycles = 0
        degraded_cycles = 0
        unhealthy_cycles = 0
        
        for cycle in range(20):
            await monitor.perform_health_checks()
            
            overall_health = monitor._calculate_overall_health()
            if overall_health == ServiceStatus.HEALTHY.value:
                healthy_cycles += 1
            elif overall_health == ServiceStatus.DEGRADED.value:
                degraded_cycles += 1
            else:
                unhealthy_cycles += 1
            
            await asyncio.sleep(0.1)
        
        # System should show resilience
        assert healthy_cycles > 0, "System never recovered to healthy state"
        assert degraded_cycles > 0, "System should show degraded states under failures"
        
        # Most cycles should not be completely unhealthy
        assert unhealthy_cycles < healthy_cycles + degraded_cycles, \
            "System spent too much time in unhealthy state"

    @pytest.mark.asyncio
    async def test_network_partition_scenario(self, chaos_monitor, chaos_manager):
        """Test behavior during network partition."""
        monitor = chaos_monitor
        manager = chaos_manager
        
        # Start with healthy system
        await monitor.perform_health_checks()
        assert monitor._calculate_overall_health() == ServiceStatus.HEALTHY.value
        
        # Simulate network partition
        manager.enable_chaos({'network_partition': True})
        
        # Health checks should handle network errors gracefully
        for _ in range(5):
            await monitor.perform_health_checks()
            # System should detect failures but not crash
            assert len(monitor.service_status) > 0
        
        # Restore network
        manager.enable_chaos({'network_partition': False})
        
        # System should recover
        recovery_attempts = 0
        while recovery_attempts < 10:
            await monitor.perform_health_checks()
            if monitor._calculate_overall_health() == ServiceStatus.HEALTHY.value:
                break
            recovery_attempts += 1
            await asyncio.sleep(0.1)
        
        assert recovery_attempts < 10, "System failed to recover from network partition"

    @pytest.mark.asyncio
    async def test_resource_exhaustion_scenario(self, chaos_monitor, chaos_manager):
        """Test behavior under resource exhaustion."""
        monitor = chaos_monitor
        manager = chaos_manager
        
        # Enable resource exhaustion
        manager.enable_chaos({'resource_exhaustion': True})
        
        # Health checks should handle resource errors
        error_count = 0
        for _ in range(10):
            try:
                await monitor.perform_health_checks()
            except MemoryError:
                error_count += 1
        
        # Some errors are expected, but system should remain functional
        assert error_count < 10, "System completely failed under resource exhaustion"
        
        # Recovery attempts should also handle resource issues
        await monitor.attempt_manager_recovery()
        # Should not crash, even if recovery fails

    @pytest.mark.asyncio
    async def test_slow_response_scenario(self, chaos_monitor, chaos_manager):
        """Test behavior with slow service responses."""
        monitor = chaos_monitor
        manager = chaos_manager
        
        # Enable slow responses
        manager.enable_chaos({'slow_responses': True})
        
        # Measure health check performance under slow conditions
        start_time = time.time()
        await monitor.perform_health_checks()
        execution_time = time.time() - start_time
        
        # Should handle slow responses but still complete
        assert execution_time > 0.5, "Slow responses not simulated properly"
        assert execution_time < 30.0, "Health check took too long under slow conditions"
        
        # System should still function
        assert len(monitor.service_status) > 0

    @pytest.mark.asyncio
    async def test_intermittent_failures_scenario(self, chaos_monitor, chaos_manager):
        """Test behavior with intermittent service failures."""
        monitor = chaos_monitor
        manager = chaos_manager
        
        # Enable intermittent failures
        manager.enable_chaos({'intermittent_failures': True})
        
        # Track status changes over time
        status_history = []
        
        for _ in range(15):  # Run for 15 cycles
            await monitor.perform_health_checks()
            overall_health = monitor._calculate_overall_health()
            status_history.append(overall_health)
            await asyncio.sleep(1.1)  # Wait for intermittent pattern
        
        # Should see status changes due to intermittent failures
        unique_statuses = set(status_history)
        assert len(unique_statuses) > 1, "No status changes detected with intermittent failures"
        
        # Should recover periodically
        healthy_count = status_history.count(ServiceStatus.HEALTHY.value)
        assert healthy_count > 0, "System never recovered during intermittent failures"

    @pytest.mark.asyncio
    async def test_cascading_failures_scenario(self, chaos_monitor, chaos_manager):
        """Test behavior during cascading failures."""
        monitor = chaos_monitor
        manager = chaos_manager
        
        # Start with healthy system
        await monitor.perform_health_checks()
        initial_health = monitor._calculate_overall_health()
        assert initial_health == ServiceStatus.HEALTHY.value
        
        # Enable cascading failures
        manager.enable_chaos({'cascading_failures': True})
        
        # Trigger initial failure that should cascade
        manager.inject_failures(['extension_0'])
        
        # Monitor cascade progression
        failure_progression = []
        
        for cycle in range(10):
            await monitor.perform_health_checks()
            
            # Count failed services
            failed_count = sum(1 for status in monitor.service_status.values()
                             if status in [ServiceStatus.UNHEALTHY, ServiceStatus.DEGRADED])
            failure_progression.append(failed_count)
            
            # Trigger recovery attempts (which might cause more failures)
            if cycle % 3 == 0:
                await monitor.attempt_manager_recovery()
            
            await asyncio.sleep(0.1)
        
        # Should see failure propagation
        max_failures = max(failure_progression)
        assert max_failures > 1, "Cascading failures not properly simulated"
        
        # But system should eventually stabilize
        recent_failures = failure_progression[-3:]
        assert max(recent_failures) - min(recent_failures) <= 2, \
            "System failed to stabilize after cascading failures"

    @pytest.mark.asyncio
    async def test_recovery_under_stress(self, chaos_monitor, chaos_manager):
        """Test recovery mechanisms under high stress."""
        monitor = chaos_monitor
        manager = chaos_manager
        
        # Create high-stress scenario
        manager.enable_chaos({
            'failure_rate': 0.5,
            'slow_responses': True,
            'intermittent_failures': True
        })
        
        # Inject multiple failures
        failed_services = [f'extension_{i}' for i in range(0, 10, 2)]
        manager.inject_failures(failed_services)
        
        # Set high failure counts to trigger recovery
        for service in failed_services:
            monitor.failure_counts[service] = 3
        
        # Attempt concurrent recoveries under stress
        recovery_tasks = []
        for service in failed_services:
            task = asyncio.create_task(monitor.attempt_extension_recovery(service))
            recovery_tasks.append(task)
        
        # Also attempt manager recovery
        manager_recovery_task = asyncio.create_task(monitor.attempt_manager_recovery())
        recovery_tasks.append(manager_recovery_task)
        
        # Wait for all recoveries with timeout
        try:
            await asyncio.wait_for(asyncio.gather(*recovery_tasks), timeout=30.0)
        except asyncio.TimeoutError:
            pytest.fail("Recovery took too long under stress")
        
        # Verify some recovery occurred
        await monitor.perform_health_checks()
        final_health = monitor._calculate_overall_health()
        
        # System should not be completely unhealthy after recovery attempts
        assert final_health != ServiceStatus.UNKNOWN.value, "System status unknown after recovery"

    @pytest.mark.asyncio
    async def test_monitoring_loop_chaos_resilience(self, chaos_monitor, chaos_manager):
        """Test monitoring loop resilience under chaos conditions."""
        monitor = chaos_monitor
        manager = chaos_manager
        
        # Enable multiple chaos conditions
        manager.enable_chaos({
            'failure_rate': 0.4,
            'intermittent_failures': True,
            'slow_responses': True
        })
        
        # Start monitoring loop
        monitoring_task = asyncio.create_task(
            monitor.start_monitoring(check_interval=0.2)
        )
        
        # Let it run under chaos conditions
        chaos_duration = 3.0  # 3 seconds of chaos
        await asyncio.sleep(chaos_duration)
        
        # Monitoring should still be active
        assert monitor.monitoring_active is True, "Monitoring loop stopped under chaos"
        
        # Stop monitoring
        await monitor.stop_monitoring()
        
        # Wait for clean shutdown
        try:
            await asyncio.wait_for(monitoring_task, timeout=5.0)
        except asyncio.TimeoutError:
            monitoring_task.cancel()
            pytest.fail("Monitoring loop failed to stop cleanly")

    @pytest.mark.asyncio
    async def test_concurrent_chaos_scenarios(self, chaos_monitor, chaos_manager):
        """Test multiple concurrent chaos scenarios."""
        monitor = chaos_monitor
        manager = chaos_manager
        
        async def chaos_scenario_1():
            """Random failures scenario."""
            manager.enable_chaos({'failure_rate': 0.3})
            for _ in range(10):
                await monitor.perform_health_checks()
                await asyncio.sleep(0.1)
        
        async def chaos_scenario_2():
            """Recovery stress scenario."""
            for i in range(5):
                service_name = f'extension_{i}'
                monitor.failure_counts[service_name] = 3
                await monitor.attempt_extension_recovery(service_name)
                await asyncio.sleep(0.2)
        
        async def chaos_scenario_3():
            """Status monitoring scenario."""
            for _ in range(15):
                status = monitor.get_service_status()
                assert 'services' in status
                await asyncio.sleep(0.1)
        
        # Run concurrent chaos scenarios
        scenarios = [
            asyncio.create_task(chaos_scenario_1()),
            asyncio.create_task(chaos_scenario_2()),
            asyncio.create_task(chaos_scenario_3())
        ]
        
        # Wait for all scenarios to complete
        await asyncio.gather(*scenarios)
        
        # System should still be functional
        final_status = monitor.get_service_status()
        assert final_status['monitoring_active'] is False  # Not actively monitoring
        assert len(final_status['services']) > 0

    @pytest.mark.asyncio
    async def test_extreme_failure_scenario(self, chaos_monitor, chaos_manager):
        """Test system behavior under extreme failure conditions."""
        monitor = chaos_monitor
        manager = chaos_manager
        
        # Create extreme failure scenario
        manager.enable_chaos({
            'failure_rate': 0.9,  # 90% failure rate
            'network_partition': True,
            'slow_responses': True,
            'cascading_failures': True
        })
        
        # Inject failures in most services
        all_extensions = list(manager.extensions.keys())
        failed_services = all_extensions[:15]  # Fail 15 out of 20 extensions
        manager.inject_failures(failed_services)
        
        # System should handle extreme conditions without crashing
        exception_count = 0
        for _ in range(5):
            try:
                await monitor.perform_health_checks()
            except Exception:
                exception_count += 1
        
        # Some exceptions are expected, but not all attempts should fail
        assert exception_count < 5, "System completely failed under extreme conditions"
        
        # Status reporting should still work
        status = monitor.get_service_status()
        assert 'overall_health' in status
        
        # Overall health should reflect the extreme conditions
        assert status['overall_health'] in [
            ServiceStatus.UNHEALTHY.value,
            ServiceStatus.DEGRADED.value
        ]

    @pytest.mark.asyncio
    async def test_chaos_recovery_patterns(self, chaos_monitor, chaos_manager):
        """Test different recovery patterns under chaos."""
        monitor = chaos_monitor
        manager = chaos_manager
        
        # Test recovery pattern 1: Gradual recovery
        manager.enable_chaos({'failure_rate': 0.8})
        await monitor.perform_health_checks()
        
        # Gradually reduce failure rate
        for failure_rate in [0.6, 0.4, 0.2, 0.0]:
            manager.enable_chaos({'failure_rate': failure_rate})
            await monitor.perform_health_checks()
            await asyncio.sleep(0.1)
        
        # Should show improvement
        final_health = monitor._calculate_overall_health()
        assert final_health in [ServiceStatus.HEALTHY.value, ServiceStatus.DEGRADED.value]
        
        # Test recovery pattern 2: Sudden recovery
        manager.enable_chaos({'failure_rate': 0.9})
        await monitor.perform_health_checks()
        
        # Sudden recovery
        manager.enable_chaos({'failure_rate': 0.0})
        await monitor.perform_health_checks()
        
        # Should recover quickly
        recovery_health = monitor._calculate_overall_health()
        assert recovery_health != ServiceStatus.UNHEALTHY.value


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])