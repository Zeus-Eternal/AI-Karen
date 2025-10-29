"""
Configuration and fixtures for error recovery tests.

Provides shared fixtures and configuration for all error recovery test modules.
"""

import pytest
import asyncio
import tempfile
import shutil
from unittest.mock import Mock, AsyncMock, MagicMock
from datetime import datetime
import os
import sys

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_directory():
    """Create a temporary directory for test files."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_extension_manager():
    """Create a mock extension manager for testing."""
    manager = Mock()
    manager.registry = Mock()
    manager.registry.get_all_extensions.return_value = {
        "test_extension": Mock(
            name="test_extension",
            status="active",
            version="1.0.0"
        )
    }
    manager.is_initialized.return_value = True
    manager.reload_extension = AsyncMock()
    manager.restart_extension = AsyncMock()
    manager.check_extension_health = AsyncMock(return_value=True)
    return manager


@pytest.fixture
def mock_auth_service():
    """Create a mock authentication service for testing."""
    auth_service = Mock()
    auth_service.refresh_token = Mock(return_value="new_token")
    auth_service.validate_token = Mock(return_value=True)
    auth_service.get_user_context = Mock(return_value={
        "user_id": "test_user",
        "tenant_id": "test_tenant",
        "roles": ["user"]
    })
    return auth_service


@pytest.fixture
def mock_cache_manager():
    """Create a mock cache manager for testing."""
    cache_manager = Mock()
    cache_data = {}
    
    def mock_get(key, default=None):
        return cache_data.get(key, default)
    
    def mock_set(key, value, ttl=None):
        cache_data[key] = value
        return True
    
    def mock_clear(key=None):
        if key:
            cache_data.pop(key, None)
        else:
            cache_data.clear()
        return True
    
    cache_manager.get.side_effect = mock_get
    cache_manager.set.side_effect = mock_set
    cache_manager.clear.side_effect = mock_clear
    
    return cache_manager


@pytest.fixture
def mock_feature_flags():
    """Create a mock feature flags manager for testing."""
    feature_flags = Mock()
    flags = {}
    
    def mock_get_flag(flag_name, default=False):
        return flags.get(flag_name, default)
    
    def mock_set_flag(flag_name, value):
        flags[flag_name] = value
        return True
    
    def mock_is_enabled(flag_name):
        return flags.get(flag_name, False)
    
    feature_flags.get_flag.side_effect = mock_get_flag
    feature_flags.set_flag.side_effect = mock_set_flag
    feature_flags.is_enabled.side_effect = mock_is_enabled
    
    return feature_flags


@pytest.fixture
def sample_error_contexts():
    """Provide sample error contexts for testing."""
    return [
        {
            "error_type": "authentication_error",
            "extension_name": "test_extension",
            "error_message": "Authentication failed",
            "timestamp": datetime.utcnow(),
            "attempt_count": 1,
            "metadata": {"user_id": "test_user"}
        },
        {
            "error_type": "network_error",
            "extension_name": "network_extension",
            "error_message": "Connection timeout",
            "timestamp": datetime.utcnow(),
            "attempt_count": 2,
            "metadata": {"endpoint": "/api/test"}
        },
        {
            "error_type": "service_unavailable",
            "extension_name": "service_extension",
            "error_message": "Service temporarily unavailable",
            "timestamp": datetime.utcnow(),
            "attempt_count": 1,
            "metadata": {"service": "background_tasks"}
        }
    ]


@pytest.fixture
def mock_metrics_collector():
    """Create a mock metrics collector for testing."""
    metrics = Mock()
    metrics.record_recovery_attempt = Mock()
    metrics.record_recovery_result = Mock()
    metrics.record_error_count = Mock()
    metrics.record_response_time = Mock()
    metrics.get_metrics = Mock(return_value={
        "recovery_attempts": 0,
        "successful_recoveries": 0,
        "failed_recoveries": 0,
        "average_recovery_time": 0.0
    })
    return metrics


@pytest.fixture
def mock_logger():
    """Create a mock logger for testing."""
    logger = Mock()
    logger.debug = Mock()
    logger.info = Mock()
    logger.warning = Mock()
    logger.error = Mock()
    logger.critical = Mock()
    return logger


@pytest.fixture
def error_recovery_config():
    """Provide error recovery configuration for testing."""
    return {
        "max_retry_attempts": 3,
        "base_backoff_delay": 1.0,
        "max_backoff_delay": 30.0,
        "timeout_seconds": 10.0,
        "enable_metrics": True,
        "enable_persistence": True,
        "recovery_strategies": {
            "authentication_error": "refresh_credentials",
            "network_error": "reset_connection",
            "service_unavailable": "restart_service",
            "configuration_error": "reload_config"
        }
    }


@pytest.fixture
def performance_test_config():
    """Provide configuration for performance tests."""
    return {
        "max_response_time_ms": 100,
        "max_memory_usage_mb": 50,
        "min_throughput_ops_per_sec": 1000,
        "max_cpu_usage_percent": 80,
        "test_duration_seconds": 30
    }


@pytest.fixture
def reliability_test_config():
    """Provide configuration for reliability tests."""
    return {
        "min_success_rate": 0.95,
        "max_failure_rate": 0.05,
        "chaos_injection_rate": 0.1,
        "concurrent_operations": 100,
        "test_iterations": 1000
    }


# Pytest configuration
def pytest_configure(config):
    """Configure pytest for error recovery tests."""
    # Add custom markers
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
        "markers", "reliability: mark test as a reliability test"
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
        elif "reliability" in str(item.fspath):
            item.add_marker(pytest.mark.reliability)
            item.add_marker(pytest.mark.slow)


# Test utilities
class TestErrorRecoveryUtils:
    """Utility class for error recovery testing."""
    
    @staticmethod
    def create_error_context(error_type="test_error", **kwargs):
        """Create a test error context."""
        default_context = {
            "error_type": error_type,
            "extension_name": "test_extension",
            "error_message": f"Test {error_type}",
            "timestamp": datetime.utcnow(),
            "attempt_count": 1,
            "metadata": {}
        }
        default_context.update(kwargs)
        return default_context
    
    @staticmethod
    def create_recovery_result(success=True, **kwargs):
        """Create a test recovery result."""
        default_result = {
            "success": success,
            "strategy": "test_strategy",
            "message": "Test recovery result",
            "timestamp": datetime.utcnow(),
            "recovery_time": 0.1
        }
        default_result.update(kwargs)
        return default_result
    
    @staticmethod
    async def wait_for_condition(condition_func, timeout=5.0, interval=0.1):
        """Wait for a condition to become true."""
        start_time = asyncio.get_event_loop().time()
        
        while asyncio.get_event_loop().time() - start_time < timeout:
            if await condition_func() if asyncio.iscoroutinefunction(condition_func) else condition_func():
                return True
            await asyncio.sleep(interval)
        
        return False
    
    @staticmethod
    def assert_recovery_metrics(metrics, expected_attempts=None, expected_successes=None):
        """Assert recovery metrics match expectations."""
        if expected_attempts is not None:
            assert metrics.get("recovery_attempts", 0) >= expected_attempts
        
        if expected_successes is not None:
            assert metrics.get("successful_recoveries", 0) >= expected_successes
        
        # Success rate should be reasonable
        attempts = metrics.get("recovery_attempts", 0)
        successes = metrics.get("successful_recoveries", 0)
        
        if attempts > 0:
            success_rate = successes / attempts
            assert success_rate >= 0.8  # At least 80% success rate


# Make utilities available to all tests
@pytest.fixture
def test_utils():
    """Provide test utilities."""
    return TestErrorRecoveryUtils