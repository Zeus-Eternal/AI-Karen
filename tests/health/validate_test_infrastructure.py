#!/usr/bin/env python3
"""
Validation script for health monitoring test infrastructure.

Validates that all test components are properly set up and can be imported.
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def validate_imports():
    """Validate that all test modules can be imported."""
    print("Validating test module imports...")
    
    try:
        # Test unit test imports
        from tests.unit.health.test_extension_service_monitor import TestExtensionServiceMonitor
        print("✅ Unit tests import successfully")
        
        # Test integration test imports
        from tests.integration.health.test_service_recovery_mechanisms import TestServiceRecoveryIntegration
        print("✅ Integration tests import successfully")
        
        # Test performance test imports
        from tests.performance.health.test_health_check_performance import TestHealthCheckPerformance
        print("✅ Performance tests import successfully")
        
        # Test chaos test imports
        from tests.chaos.health.test_chaos_engineering_scenarios import TestChaosEngineeringScenarios
        print("✅ Chaos tests import successfully")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def validate_fixtures():
    """Validate that test fixtures are working."""
    print("\nValidating test fixtures...")
    
    try:
        # Import conftest fixtures
        sys.path.insert(0, str(Path(__file__).parent))
        import conftest
        
        # Test basic fixtures
        basic_manager = conftest.basic_extension_manager()
        assert basic_manager is not None
        print("✅ Basic extension manager fixture works")
        
        multiple_exts = conftest.multiple_extensions()
        assert len(multiple_exts) == 5
        print("✅ Multiple extensions fixture works")
        
        perf_config = conftest.performance_test_config()
        assert 'max_execution_time' in perf_config
        print("✅ Performance test config fixture works")
        
        chaos_config = conftest.chaos_test_config()
        assert 'failure_rates' in chaos_config
        print("✅ Chaos test config fixture works")
        
        return True
        
    except Exception as e:
        print(f"❌ Fixture validation error: {e}")
        return False

def validate_test_runner():
    """Validate that the test runner script is functional."""
    print("\nValidating test runner...")
    
    try:
        from tests.health.run_health_monitoring_tests import HealthMonitoringTestRunner
        
        runner = HealthMonitoringTestRunner()
        assert len(runner.test_suites) == 4
        print("✅ Test runner initializes correctly")
        
        # Check test suite configuration
        for suite_name, config in runner.test_suites.items():
            assert 'path' in config
            assert 'description' in config
            assert 'markers' in config
            assert 'timeout' in config
        print("✅ Test suite configurations are valid")
        
        return True
        
    except Exception as e:
        print(f"❌ Test runner validation error: {e}")
        return False

def validate_directory_structure():
    """Validate that all required directories and files exist."""
    print("\nValidating directory structure...")
    
    required_files = [
        'tests/health/conftest.py',
        'tests/health/run_health_monitoring_tests.py',
        'tests/health/README.md',
        'tests/unit/health/test_extension_service_monitor.py',
        'tests/integration/health/test_service_recovery_mechanisms.py',
        'tests/performance/health/test_health_check_performance.py',
        'tests/chaos/health/test_chaos_engineering_scenarios.py'
    ]
    
    missing_files = []
    for file_path in required_files:
        full_path = project_root / file_path
        if not full_path.exists():
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    else:
        print("✅ All required files exist")
        return True

def validate_mock_health_monitor():
    """Validate that we can create a mock health monitor for testing."""
    print("\nValidating mock health monitor creation...")
    
    try:
        # Create a minimal mock health monitor
        from unittest.mock import Mock, AsyncMock
        from enum import Enum
        
        class MockServiceStatus(Enum):
            HEALTHY = "healthy"
            DEGRADED = "degraded"
            UNHEALTHY = "unhealthy"
            UNKNOWN = "unknown"
        
        class MockExtensionStatus(Enum):
            ACTIVE = "active"
            LOADING = "loading"
            ERROR = "error"
        
        # Mock extension manager
        manager = Mock()
        manager.is_initialized.return_value = True
        manager.registry = Mock()
        manager.registry.get_all_extensions.return_value = {}
        manager.check_extension_health = AsyncMock(return_value=True)
        
        # Mock service monitor
        class MockServiceMonitor:
            def __init__(self, extension_manager):
                self.extension_manager = extension_manager
                self.service_status = {}
                self.last_health_check = {}
                self.failure_counts = {}
                self.monitoring_active = False
            
            def get_service_status(self):
                return {
                    'services': self.service_status,
                    'overall_health': MockServiceStatus.HEALTHY.value,
                    'monitoring_active': self.monitoring_active
                }
        
        monitor = MockServiceMonitor(manager)
        status = monitor.get_service_status()
        
        assert 'services' in status
        assert 'overall_health' in status
        assert 'monitoring_active' in status
        
        print("✅ Mock health monitor creation works")
        return True
        
    except Exception as e:
        print(f"❌ Mock health monitor validation error: {e}")
        return False

def main():
    """Run all validations."""
    print("Health Monitoring Test Infrastructure Validation")
    print("=" * 50)
    
    validations = [
        validate_directory_structure,
        validate_imports,
        validate_fixtures,
        validate_test_runner,
        validate_mock_health_monitor
    ]
    
    all_passed = True
    for validation in validations:
        try:
            if not validation():
                all_passed = False
        except Exception as e:
            print(f"❌ Validation failed with exception: {e}")
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 All validations PASSED! Test infrastructure is ready.")
        print("\nNext steps:")
        print("1. Run unit tests: python tests/health/run_health_monitoring_tests.py --suite unit")
        print("2. Run integration tests: python tests/health/run_health_monitoring_tests.py --suite integration")
        print("3. Run all tests: python tests/health/run_health_monitoring_tests.py")
    else:
        print("💥 Some validations FAILED. Please fix the issues above.")
    
    return all_passed

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)