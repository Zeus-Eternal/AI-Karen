"""
Configuration and fixtures for HTTP Request Validation Integration Tests

This module provides shared configuration, fixtures, and utilities for all
HTTP request validation integration tests.
"""

import asyncio
import logging
import pytest
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional
from unittest.mock import Mock

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import validation system components
from src.ai_karen_engine.server.http_validator import (
    HTTPRequestValidator,
    ValidationConfig
)
from src.ai_karen_engine.server.security_analyzer import SecurityAnalyzer
from src.ai_karen_engine.server.rate_limiter import (
    EnhancedRateLimiter,
    MemoryRateLimitStorage,
    RateLimitRule,
    RateLimitScope,
    RateLimitAlgorithm
)
from src.ai_karen_engine.server.enhanced_logger import EnhancedLogger


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_directory():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def test_validation_config():
    """Create a test validation configuration."""
    return ValidationConfig(
        max_content_length=1024 * 1024,  # 1MB for testing
        allowed_methods={"GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"},
        max_header_size=4096,
        max_headers_count=50,
        rate_limit_requests_per_minute=60,
        enable_security_analysis=True,
        log_invalid_requests=True,
        blocked_user_agents={"sqlmap", "nikto", "malicious-bot"},
        suspicious_headers={"x-forwarded-host", "x-cluster-client-ip"}
    )


@pytest.fixture
def test_rate_limit_rules():
    """Create test rate limiting rules."""
    return [
        RateLimitRule(
            name="auth_test",
            scope=RateLimitScope.IP_ENDPOINT,
            algorithm=RateLimitAlgorithm.SLIDING_WINDOW,
            limit=5,
            window_seconds=60,
            priority=100,
            endpoints=["/auth/login", "/auth/register"],
            description="Test auth rate limiting"
        ),
        RateLimitRule(
            name="api_test",
            scope=RateLimitScope.IP,
            algorithm=RateLimitAlgorithm.SLIDING_WINDOW,
            limit=30,
            window_seconds=60,
            priority=50,
            description="Test API rate limiting"
        ),
        RateLimitRule(
            name="global_test",
            scope=RateLimitScope.GLOBAL,
            algorithm=RateLimitAlgorithm.FIXED_WINDOW,
            limit=1000,
            window_seconds=60,
            priority=1,
            description="Test global rate limiting"
        )
    ]


@pytest.fixture
def test_validator(test_validation_config):
    """Create a test HTTP validator."""
    return HTTPRequestValidator(test_validation_config)


@pytest.fixture
def test_security_analyzer(temp_directory):
    """Create a test security analyzer."""
    threat_file = temp_directory / "test_threat_intelligence.json"
    return SecurityAnalyzer(threat_intelligence_file=str(threat_file))


@pytest.fixture
def test_rate_limiter(test_rate_limit_rules):
    """Create a test rate limiter."""
    storage = MemoryRateLimitStorage()
    return EnhancedRateLimiter(storage, test_rate_limit_rules)


@pytest.fixture
def test_enhanced_logger():
    """Create a test enhanced logger."""
    return EnhancedLogger()


@pytest.fixture
def validation_test_system(
    test_validator,
    test_security_analyzer,
    test_rate_limiter,
    test_enhanced_logger,
    test_validation_config
):
    """Create a complete validation test system."""
    return {
        'validator': test_validator,
        'security_analyzer': test_security_analyzer,
        'rate_limiter': test_rate_limiter,
        'enhanced_logger': test_enhanced_logger,
        'config': test_validation_config
    }


def create_mock_request(
    method: str = "GET",
    path: str = "/",
    headers: Dict[str, str] = None,
    query_params: Dict[str, str] = None,
    client_ip: str = "127.0.0.1",
    body: bytes = b""
):
    """Create a mock FastAPI Request object for testing."""
    request = Mock()
    request.method = method
    request.url = Mock()
    request.url.path = path
    request.url.query = "&".join([f"{k}={v}" for k, v in (query_params or {}).items()])
    request.headers = headers or {}
    request.query_params = query_params or {}
    request.client = Mock()
    request.client.host = client_ip
    
    # Mock body reading
    async def read_body():
        return body
    request.body = read_body
    
    return request


@pytest.fixture
def mock_request_factory():
    """Factory fixture for creating mock requests."""
    return create_mock_request


# Test data fixtures
@pytest.fixture
def valid_test_requests():
    """Create a set of valid test requests."""
    return [
        create_mock_request(
            method="GET",
            path="/api/users",
            headers={"user-agent": "test-client/1.0"},
            query_params={"page": "1", "limit": "10"},
            client_ip="192.168.1.100"
        ),
        create_mock_request(
            method="POST",
            path="/api/products",
            headers={"content-type": "application/json", "user-agent": "app/2.0"},
            client_ip="192.168.1.101"
        ),
        create_mock_request(
            method="PUT",
            path="/api/orders/123",
            headers={"authorization": "Bearer token", "content-type": "application/json"},
            client_ip="192.168.1.102"
        )
    ]


@pytest.fixture
def invalid_test_requests():
    """Create a set of invalid test requests."""
    return [
        # Invalid method
        create_mock_request(
            method="INVALID",
            path="/api/test",
            client_ip="192.168.1.200"
        ),
        # Too many headers
        create_mock_request(
            method="GET",
            path="/api/test",
            headers={f"header-{i}": f"value-{i}" for i in range(60)},
            client_ip="192.168.1.201"
        ),
        # Blocked user agent
        create_mock_request(
            method="GET",
            path="/api/test",
            headers={"user-agent": "sqlmap/1.0"},
            client_ip="192.168.1.202"
        ),
        # Content too large
        create_mock_request(
            method="POST",
            path="/api/upload",
            headers={"content-length": str(10 * 1024 * 1024)},  # 10MB
            client_ip="192.168.1.203"
        )
    ]


@pytest.fixture
def attack_test_requests():
    """Create a set of attack test requests."""
    return [
        # SQL injection
        create_mock_request(
            method="GET",
            path="/api/users",
            query_params={"id": "1' UNION SELECT * FROM users--"},
            client_ip="10.0.0.100"
        ),
        # XSS attack
        create_mock_request(
            method="GET",
            path="/search",
            query_params={"q": "<script>alert('xss')</script>"},
            client_ip="10.0.0.101"
        ),
        # Path traversal
        create_mock_request(
            method="GET",
            path="/files/../../../etc/passwd",
            client_ip="10.0.0.102"
        ),
        # Command injection
        create_mock_request(
            method="GET",
            path="/api/exec",
            query_params={"cmd": "ls; cat /etc/passwd"},
            client_ip="10.0.0.103"
        ),
        # Header injection
        create_mock_request(
            method="GET",
            path="/api/test",
            headers={"x-custom": "value\r\nSet-Cookie: malicious=true"},
            client_ip="10.0.0.104"
        )
    ]


# Performance testing utilities
class PerformanceTracker:
    """Utility class for tracking performance metrics during tests."""
    
    def __init__(self):
        self.metrics = {
            'request_count': 0,
            'total_time': 0.0,
            'min_time': float('inf'),
            'max_time': 0.0,
            'processing_times': []
        }
    
    def record_request(self, processing_time: float):
        """Record a request processing time."""
        self.metrics['request_count'] += 1
        self.metrics['total_time'] += processing_time
        self.metrics['min_time'] = min(self.metrics['min_time'], processing_time)
        self.metrics['max_time'] = max(self.metrics['max_time'], processing_time)
        self.metrics['processing_times'].append(processing_time)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        if self.metrics['request_count'] == 0:
            return self.metrics
        
        avg_time = self.metrics['total_time'] / self.metrics['request_count']
        throughput = self.metrics['request_count'] / self.metrics['total_time'] if self.metrics['total_time'] > 0 else 0
        
        return {
            **self.metrics,
            'avg_time': avg_time,
            'throughput': throughput
        }


@pytest.fixture
def performance_tracker():
    """Create a performance tracker for tests."""
    return PerformanceTracker()


# Test markers
pytest_plugins = []

# Custom markers for test categorization
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as performance test"
    )
    config.addinivalue_line(
        "markers", "security: mark test as security test"
    )
    config.addinivalue_line(
        "markers", "error_handling: mark test as error handling test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )


# Test collection hooks
def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test names."""
    for item in items:
        # Add markers based on test file names
        if "performance" in item.nodeid:
            item.add_marker(pytest.mark.performance)
        if "security" in item.nodeid:
            item.add_marker(pytest.mark.security)
        if "error_handling" in item.nodeid:
            item.add_marker(pytest.mark.error_handling)
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        
        # Add slow marker for tests that might take longer
        if any(keyword in item.nodeid for keyword in ["load", "stress", "concurrent", "comprehensive"]):
            item.add_marker(pytest.mark.slow)


# Cleanup fixtures
@pytest.fixture(autouse=True)
def cleanup_after_test():
    """Cleanup after each test."""
    yield
    # Perform any necessary cleanup
    # This runs after each test
    pass


@pytest.fixture(scope="session", autouse=True)
def cleanup_after_session():
    """Cleanup after the entire test session."""
    yield
    # Perform any necessary session-level cleanup
    # This runs after all tests are complete
    pass