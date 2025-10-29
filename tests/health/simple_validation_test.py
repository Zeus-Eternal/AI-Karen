#!/usr/bin/env python3
"""
Simple validation test that doesn't require pytest.

Tests basic functionality of the health monitoring test infrastructure.
"""

import sys
import os
import asyncio
from pathlib import Path
from unittest.mock import Mock, AsyncMock
from enum import Enum

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class ServiceStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class ExtensionStatus(Enum):
    ACTIVE = "active"
    LOADING = "loading"
    ERROR = "error"
    DISABLED = "disabled"


class MockExtensionServiceMonitor:
    """Mock implementation of ExtensionServiceMonitor for testing."""
    
    def __init__(self, extension_manager):
        self.extension_manager = extension_manager
        self.service_status = {}
        self.last_health_check = {}
        self.failure_counts = {}
        self.monitoring_active = False
    
    async def check_extension_manager_health(self):
        """Check extension manager health."""
        try:
            if self.extension_manager.is_initialized():
                self.service_status['extension_manager'] = ServiceStatus.HEALTHY
                self.failure_counts['extension_manager'] = 0
                return True
            else:
                self.service_status['extension_manager'] = ServiceStatus.UNHEALTHY
                self.failure_counts['extension_manager'] = self.failure_counts.get('extension_manager', 0) + 1
                return False
        except Exception:
            self.service_status['extension_manager'] = ServiceStatus.UNHEALTHY
            self.failure_counts['extension_manager'] = self.failure_counts.get('extension_manager', 0) + 1
            return False
    
    async def check_extension_health(self, name, record):
        """Check individual extension health."""
        try:
            if record.status == ExtensionStatus.ACTIVE:
                health_result = await self.extension_manager.check_extension_health(name)
                if health_result:
                    self.service_status[name] = ServiceStatus.HEALTHY
                    self.failure_counts[name] = 0
                    return True
                else:
                    self.service_status[name] = ServiceStatus.DEGRADED
                    self.failure_counts[name] = self.failure_counts.get(name, 0) + 1
                    return False
            else:
                self.service_status[name] = ServiceStatus.DEGRADED
                return False
        except Exception:
            self.service_status[name] = ServiceStatus.UNHEALTHY
            self.failure_counts[name] = self.failure_counts.get(name, 0) + 1
            return False
    
    async def perform_health_checks(self):
        """Perform complete health check cycle."""
        # Check extension manager
        await self.check_extension_manager_health()
        
        # Check individual extensions
        extensions = self.extension_manager.registry.get_all_extensions()
        for name, record in extensions.items():
            await self.check_extension_health(name, record)
    
    async def attempt_manager_recovery(self):
        """Attempt to recover extension manager."""
        try:
            await self.extension_manager.reinitialize()
            self.failure_counts['extension_manager'] = 0
        except Exception:
            pass
    
    async def attempt_extension_recovery(self, name):
        """Attempt to recover specific extension."""
        try:
            record = await self.extension_manager.reload_extension(name)
            if record and record.status == ExtensionStatus.ACTIVE:
                self.failure_counts[name] = 0
        except Exception:
            pass
    
    def get_service_status(self):
        """Get current service status."""
        return {
            'services': {
                name: {
                    'status': status.value,
                    'failure_count': self.failure_counts.get(name, 0)
                }
                for name, status in self.service_status.items()
            },
            'overall_health': self._calculate_overall_health(),
            'monitoring_active': self.monitoring_active
        }
    
    def _calculate_overall_health(self):
        """Calculate overall system health."""
        if not self.service_status:
            return ServiceStatus.UNKNOWN.value
        
        healthy_count = sum(1 for status in self.service_status.values()
                          if status == ServiceStatus.HEALTHY)
        total_count = len(self.service_status)
        
        if healthy_count == total_count:
            return ServiceStatus.HEALTHY.value
        elif healthy_count > total_count / 2:
            return ServiceStatus.DEGRADED.value
        else:
            return ServiceStatus.UNHEALTHY.value


async def test_basic_health_monitoring():
    """Test basic health monitoring functionality."""
    print("Testing basic health monitoring...")
    
    # Create mock extension manager
    manager = Mock()
    manager.is_initialized.return_value = True
    manager.registry = Mock()
    manager.registry.get_all_extensions.return_value = {
        'test_extension': Mock(
            status=ExtensionStatus.ACTIVE,
            instance=Mock()
        )
    }
    manager.check_extension_health = AsyncMock(return_value=True)
    manager.reload_extension = AsyncMock()
    manager.reinitialize = AsyncMock()
    
    # Create service monitor
    monitor = MockExtensionServiceMonitor(manager)
    
    # Test health checks
    await monitor.perform_health_checks()
    
    # Verify results
    status = monitor.get_service_status()
    assert 'services' in status
    assert 'overall_health' in status
    assert status['overall_health'] == ServiceStatus.HEALTHY.value
    assert 'extension_manager' in status['services']
    assert 'test_extension' in status['services']
    
    print("✅ Basic health monitoring test passed")


async def test_failure_detection():
    """Test failure detection and counting."""
    print("Testing failure detection...")
    
    # Create failing extension manager
    manager = Mock()
    manager.is_initialized.return_value = False  # Simulate failure
    manager.registry = Mock()
    manager.registry.get_all_extensions.return_value = {}
    manager.check_extension_health = AsyncMock(return_value=False)
    
    # Create service monitor
    monitor = MockExtensionServiceMonitor(manager)
    
    # Test failure detection
    result = await monitor.check_extension_manager_health()
    assert result is False
    assert monitor.service_status['extension_manager'] == ServiceStatus.UNHEALTHY
    assert monitor.failure_counts['extension_manager'] == 1
    
    # Test failure count increment
    await monitor.check_extension_manager_health()
    assert monitor.failure_counts['extension_manager'] == 2
    
    print("✅ Failure detection test passed")


async def test_recovery_mechanisms():
    """Test recovery mechanisms."""
    print("Testing recovery mechanisms...")
    
    # Create extension manager with recovery capability
    manager = Mock()
    manager.is_initialized.return_value = True
    manager.registry = Mock()
    manager.registry.get_all_extensions.return_value = {}
    manager.reinitialize = AsyncMock()
    manager.reload_extension = AsyncMock()
    
    # Create service monitor
    monitor = MockExtensionServiceMonitor(manager)
    
    # Test manager recovery
    await monitor.attempt_manager_recovery()
    manager.reinitialize.assert_called_once()
    
    # Test extension recovery
    await monitor.attempt_extension_recovery('test_extension')
    manager.reload_extension.assert_called_once_with('test_extension')
    
    print("✅ Recovery mechanisms test passed")


async def test_status_calculation():
    """Test overall health status calculation."""
    print("Testing status calculation...")
    
    monitor = MockExtensionServiceMonitor(Mock())
    
    # Test healthy scenario
    monitor.service_status = {
        'service1': ServiceStatus.HEALTHY,
        'service2': ServiceStatus.HEALTHY
    }
    assert monitor._calculate_overall_health() == ServiceStatus.HEALTHY.value
    
    # Test degraded scenario
    monitor.service_status = {
        'service1': ServiceStatus.HEALTHY,
        'service2': ServiceStatus.DEGRADED,
        'service3': ServiceStatus.HEALTHY
    }
    assert monitor._calculate_overall_health() == ServiceStatus.DEGRADED.value
    
    # Test unhealthy scenario
    monitor.service_status = {
        'service1': ServiceStatus.UNHEALTHY,
        'service2': ServiceStatus.UNHEALTHY,
        'service3': ServiceStatus.HEALTHY
    }
    assert monitor._calculate_overall_health() == ServiceStatus.UNHEALTHY.value
    
    # Test unknown scenario
    monitor.service_status = {}
    assert monitor._calculate_overall_health() == ServiceStatus.UNKNOWN.value
    
    print("✅ Status calculation test passed")


async def test_concurrent_operations():
    """Test concurrent health check operations."""
    print("Testing concurrent operations...")
    
    # Create extension manager
    manager = Mock()
    manager.is_initialized.return_value = True
    manager.registry = Mock()
    manager.registry.get_all_extensions.return_value = {
        f'extension_{i}': Mock(status=ExtensionStatus.ACTIVE, instance=Mock())
        for i in range(10)
    }
    manager.check_extension_health = AsyncMock(return_value=True)
    
    # Create service monitor
    monitor = MockExtensionServiceMonitor(manager)
    
    # Run concurrent health checks
    tasks = [monitor.perform_health_checks() for _ in range(5)]
    await asyncio.gather(*tasks)
    
    # Verify results
    status = monitor.get_service_status()
    assert len(status['services']) >= 10  # 10 extensions + manager
    
    print("✅ Concurrent operations test passed")


async def run_all_tests():
    """Run all validation tests."""
    print("Health Monitoring Test Infrastructure Validation")
    print("=" * 50)
    
    tests = [
        test_basic_health_monitoring,
        test_failure_detection,
        test_recovery_mechanisms,
        test_status_calculation,
        test_concurrent_operations
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            await test()
            passed += 1
        except Exception as e:
            print(f"❌ {test.__name__} failed: {e}")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All validation tests PASSED!")
        print("\nThe health monitoring test infrastructure is working correctly.")
        print("You can now run the full test suite with pytest when it's available.")
        return True
    else:
        print("💥 Some validation tests FAILED.")
        return False


def main():
    """Main entry point."""
    try:
        success = asyncio.run(run_all_tests())
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
        return 130
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())