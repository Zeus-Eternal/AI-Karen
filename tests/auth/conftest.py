"""
Configuration and fixtures for authentication tests.
"""

import pytest
import os
import sys
from unittest.mock import Mock, patch
from datetime import datetime, timedelta, timezone

# Add server directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'server'))

from server.security import ExtensionAuthManager


@pytest.fixture(scope="session")
def test_auth_config():
    """Standard authentication configuration for testing."""
    return {
        "secret_key": "test-secret-key-for-authentication-testing-123456789",
        "algorithm": "HS256",
        "enabled": True,
        "auth_mode": "testing",
        "dev_bypass_enabled": True,
        "require_https": False,
        "access_token_expire_minutes": 60,
        "service_token_expire_minutes": 30,
        "refresh_token_expire_days": 7,
        "api_key": "test-api-key-for-authentication-testing",
        "default_permissions": ["extension:read", "extension:write"],
        "development_mode": False
    }


@pytest.fixture(scope="session")
def test_auth_manager(test_auth_config):
    """Standard authentication manager for testing."""
    return ExtensionAuthManager(test_auth_config)


@pytest.fixture
def mock_request():
    """Mock FastAPI request object."""
    request = Mock()
    request.url.path = "/api/extensions/"
    request.headers = {}
    request.client = Mock()
    request.client.host = "192.168.1.100"
    return request


@pytest.fixture
def mock_extension_manager():
    """Mock extension manager for testing."""
    manager = Mock()
    manager.registry.get_all_extensions.return_value = {
        "test-extension": {
            "name": "test-extension",
            "version": "1.0.0",
            "display_name": "Test Extension",
            "description": "A test extension",
            "status": "active",
            "capabilities": ["read", "write"]
        }
    }
    manager.is_initialized.return_value = True
    return manager


@pytest.fixture
def valid_user_context():
    """Standard valid user context for testing."""
    return {
        "user_id": "test-user",
        "tenant_id": "test-tenant",
        "roles": ["user"],
        "permissions": ["extension:read", "extension:write"],
        "token_type": "access"
    }


@pytest.fixture
def admin_user_context():
    """Admin user context for testing."""
    return {
        "user_id": "admin-user",
        "tenant_id": "admin-tenant",
        "roles": ["admin"],
        "permissions": ["extension:*"],
        "token_type": "access"
    }


@pytest.fixture
def service_user_context():
    """Service user context for testing."""
    return {
        "user_id": "service:test-service",
        "tenant_id": "system",
        "roles": ["service"],
        "permissions": ["extension:background_tasks", "extension:execute"],
        "token_type": "service",
        "service_name": "test-service"
    }


@pytest.fixture
def development_user_context():
    """Development user context for testing."""
    return {
        "user_id": "dev-user",
        "tenant_id": "dev-tenant",
        "roles": ["admin", "user"],
        "permissions": ["extension:read", "extension:write", "extension:admin"],
        "token_type": "development"
    }


@pytest.fixture
def expired_token_payload():
    """Expired token payload for testing."""
    return {
        "user_id": "test-user",
        "tenant_id": "test-tenant",
        "roles": ["user"],
        "permissions": ["extension:read"],
        "token_type": "access",
        "exp": datetime.now(timezone.utc) - timedelta(minutes=1),  # Expired
        "iat": datetime.now(timezone.utc) - timedelta(hours=1),
        "iss": "kari-extension-system"
    }


@pytest.fixture
def future_token_payload():
    """Future token payload for testing."""
    return {
        "user_id": "test-user",
        "tenant_id": "test-tenant",
        "roles": ["user"],
        "permissions": ["extension:read"],
        "token_type": "access",
        "nbf": datetime.now(timezone.utc) + timedelta(minutes=5),  # Not yet valid
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        "iat": datetime.now(timezone.utc),
        "iss": "kari-extension-system"
    }


@pytest.fixture
def patch_extension_auth_manager():
    """Patch the global extension auth manager for testing."""
    def _patch_manager(auth_manager):
        return patch('server.security.get_extension_auth_manager', return_value=auth_manager)
    return _patch_manager


@pytest.fixture
def patch_token_manager():
    """Patch token manager for testing."""
    def _patch_token_manager(token_manager=None):
        if token_manager is None:
            token_manager = Mock()
            token_manager.generate_access_token.return_value = ("test-token", "test-refresh-token")
            token_manager.validate_and_extract_user_context.return_value = {
                "user_id": "test-user",
                "tenant_id": "test-tenant",
                "roles": ["user"],
                "permissions": ["extension:read"]
            }
        
        return patch('server.token_manager.create_token_manager', return_value=token_manager)
    return _patch_token_manager


# Test data constants
TEST_EXTENSIONS = {
    "basic-extension": {
        "name": "basic-extension",
        "version": "1.0.0",
        "display_name": "Basic Extension",
        "description": "A basic test extension",
        "status": "active",
        "capabilities": ["read"]
    },
    "advanced-extension": {
        "name": "advanced-extension",
        "version": "2.0.0",
        "display_name": "Advanced Extension",
        "description": "An advanced test extension",
        "status": "active",
        "capabilities": ["read", "write", "admin"]
    },
    "disabled-extension": {
        "name": "disabled-extension",
        "version": "1.0.0",
        "display_name": "Disabled Extension",
        "description": "A disabled test extension",
        "status": "disabled",
        "capabilities": ["read"]
    }
}

TEST_USERS = {
    "regular_user": {
        "user_id": "regular_user",
        "tenant_id": "tenant1",
        "roles": ["user"],
        "permissions": ["extension:read", "extension:write"]
    },
    "admin_user": {
        "user_id": "admin_user",
        "tenant_id": "tenant1",
        "roles": ["admin"],
        "permissions": ["extension:*"]
    },
    "limited_user": {
        "user_id": "limited_user",
        "tenant_id": "tenant2",
        "roles": ["user"],
        "permissions": ["extension:read"]
    },
    "service_user": {
        "user_id": "service:background_service",
        "tenant_id": "system",
        "roles": ["service"],
        "permissions": ["extension:background_tasks", "extension:execute"]
    }
}


# Utility functions for tests
def create_test_token(auth_manager, user_data, expires_delta=None):
    """Create a test token for a user."""
    return auth_manager.create_access_token(
        user_id=user_data["user_id"],
        tenant_id=user_data["tenant_id"],
        roles=user_data["roles"],
        permissions=user_data["permissions"],
        expires_delta=expires_delta
    )


def create_test_service_token(auth_manager, service_name, permissions=None, expires_delta=None):
    """Create a test service token."""
    return auth_manager.create_service_token(
        service_name=service_name,
        permissions=permissions or ["extension:background_tasks"],
        expires_delta=expires_delta
    )


def assert_user_context_matches(actual_context, expected_user_data):
    """Assert that user context matches expected user data."""
    assert actual_context["user_id"] == expected_user_data["user_id"]
    assert actual_context["tenant_id"] == expected_user_data["tenant_id"]
    assert actual_context["roles"] == expected_user_data["roles"]
    assert set(actual_context["permissions"]) == set(expected_user_data["permissions"])


def assert_http_exception(exception, expected_status_code, expected_detail_contains=None):
    """Assert that HTTPException has expected properties."""
    assert exception.status_code == expected_status_code
    if expected_detail_contains:
        assert expected_detail_contains.lower() in exception.detail.lower()


# Pytest configuration
def pytest_configure(config):
    """Configure pytest for authentication tests."""
    # Add custom markers
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "e2e: mark test as an end-to-end test"
    )
    config.addinivalue_line(
        "markers", "security: mark test as a security test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "requires_network: mark test as requiring network access"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically."""
    for item in items:
        # Add markers based on file path
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)
        elif "security" in str(item.fspath):
            item.add_marker(pytest.mark.security)
        
        # Add slow marker for tests that might be slow
        if any(keyword in item.name.lower() for keyword in ["performance", "load", "concurrent", "timeout"]):
            item.add_marker(pytest.mark.slow)
        
        # Add network marker for tests that require network
        if any(keyword in item.name.lower() for keyword in ["network", "http", "api", "request"]):
            item.add_marker(pytest.mark.requires_network)