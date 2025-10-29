"""
Configuration and fixtures for health monitoring tests.

Provides shared fixtures and configuration for all health monitoring test suites.
"""

import pytest
import asyncio
import logging
from unittest.mock import Mock, AsyncMock
from datetime import datetime

# Configure logging for tests
logging.basicConfig(level=logging.DEBUG)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_extension_status():
    """Mock ExtensionStatus enum for testing."""
    from enum import Enum
    
    class MockExtensionStatus(Enum):
        ACTIVE = "active"
        LOADING = "loading"
        ERROR = "error"
        DISABLED = "disabled"
    
    return MockExtensionStatus


@pytest.fixture
def basic_extension_manager():
    """Create basic extension manager for testing."""
    manager = Mock()
    manager.is_initialized.return_value = True
    manager.registry = Mock()
    manager.registry.get_all_extensions.return_value = {}
    manager.check_extension_health = AsyncMock(return_value=True)
    manager.reload_extension = AsyncMock()
    manager.reinitialize = AsyncMock()
    return manager


@pytest.fixture
def extension_with_health_check():
    """Create extension record with health check capability."""
    extension = Mock()
    extension.status = Mock()
    extension.status.value = "active"
    extension.instance = Mock()
    extension.manifest = Mock()
    extension.manifest.name = "test_extension"
    extension.loaded_at = datetime.utcnow()
    return extension


@pytest.fixture
def multiple_extensions():
    """Create multiple extension records for testing."""
    extensions = {}
    for i in range(5):
        extension = Mock()
        extension.status = Mock()
        extension.status.value = "active"
        extension.instance = Mock()
        extension.manifest = Mock()
        extension.manifest.name = f"extension_{i}"
        extension.loaded_at = datetime.utcnow()
        extensions[f"extension_{i}"] = extension
    return extensions


@pytest.fixture
def failing_extension_manager():
    """Create extension manager that simulates failures."""
    manager = Mock()
    manager.is_initialized.return_value = False
    manager.registry = Mock()
    manager.registry.get_all_extensions.return_value = {}
    manager.check_extension_health = AsyncMock(return_value=False)
    manager.reload_extension = AsyncMock(side_effect=Exception("Reload failed"))
    manager.reinitialize = AsyncMock(side_effect=Exception("Reinit failed"))
    return manager


@pytest.fixture
def performance_test_config():
    """Configuration for performance tests."""
    return {
        'max_execution_time': 1.0,
        'max_memory_growth_mb': 100,
        'concurrent_requests': 10,
        'load_test_duration': 5.0,
        'extension_count': 100
    }


@pytest.fixture
def chaos_test_config():
    """Configuration for chaos engineering tests."""
    return {
        'failure_rates': [0.1, 0.3, 0.5, 0.7, 0.9],
        'chaos_duration': 3.0,
        'recovery_timeout': 10.0,
        'max_cascading_failures': 5
    }


@pytest.fixture(autouse=True)
def cleanup_after_test():
    """Cleanup fixture that runs after each test."""
    yield
    # Cleanup any global state if needed
    pass


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as a performance test"
    )
    config.addinivalue_line(
        "markers", "chaos: mark test as a chaos engineering test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on file paths."""
    for item in items:
        # Add markers based on test file location
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "performance" in str(item.fspath):
            item.add_marker(pytest.mark.performance)
            item.add_marker(pytest.mark.slow)
        elif "chaos" in str(item.fspath):
            item.add_marker(pytest.mark.chaos)
            item.add_marker(pytest.mark.slow)


# Custom assertions for health monitoring tests
def assert_service_healthy(service_status, service_name):
    """Assert that a service is healthy."""
    assert service_name in service_status['services'], f"Service {service_name} not found in status"
    service_info = service_status['services'][service_name]
    assert service_info['status'] == 'healthy', f"Service {service_name} is not healthy: {service_info['status']}"


def assert_service_degraded(service_status, service_name):
    """Assert that a service is degraded."""
    assert service_name in service_status['services'], f"Service {service_name} not found in status"
    service_info = service_status['services'][service_name]
    assert service_info['status'] == 'degraded', f"Service {service_name} is not degraded: {service_info['status']}"


def assert_service_unhealthy(service_status, service_name):
    """Assert that a service is unhealthy."""
    assert service_name in service_status['services'], f"Service {service_name} not found in status"
    service_info = service_status['services'][service_name]
    assert service_info['status'] == 'unhealthy', f"Service {service_name} is not unhealthy: {service_info['status']}"


def assert_overall_health(service_status, expected_health):
    """Assert overall system health."""
    assert service_status['overall_health'] == expected_health, \
        f"Overall health is {service_status['overall_health']}, expected {expected_health}"


# Make custom assertions available to all tests
pytest.assert_service_healthy = assert_service_healthy
pytest.assert_service_degraded = assert_service_degraded
pytest.assert_service_unhealthy = assert_service_unhealthy
pytest.assert_overall_health = assert_overall_health