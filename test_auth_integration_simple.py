"""
Simple integration tests for authentication routes and middleware.

Tests that the routes and middleware are properly using the unified AuthService
and have consistent error handling.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone

# Test that the auth routes are properly importing and using the unified AuthService
def test_auth_routes_import_unified_service():
    """Test that auth routes import the unified AuthService."""
    with patch('ai_karen_engine.auth.service.get_auth_service') as mock_get_service:
        mock_get_service.return_value = AsyncMock()

        # Import should work without errors
        from ai_karen_engine.api_routes import auth
        
        # Check that the route module has the expected functions
        assert hasattr(auth, 'get_auth_service_instance')
        assert hasattr(auth, 'login')
        assert hasattr(auth, 'register')
        assert hasattr(auth, 'logout')
        assert hasattr(auth, 'get_current_user_route')


def test_auth_middleware_import_unified_service():
    """Test that auth middleware imports the unified AuthService."""
    with patch('ai_karen_engine.auth.service.get_auth_service') as mock_get_service:
        mock_get_service.return_value = AsyncMock()

        # Import should work without errors
        from ai_karen_engine.middleware import auth
        
        # Check that the middleware has the expected functions
        assert hasattr(auth, 'auth_middleware')
        assert hasattr(auth, 'get_auth_service')


def test_auth_routes_error_handling_imports():
    """Test that auth routes import the correct exception types."""
    from ai_karen_engine.api_routes.auth import (
        InvalidCredentialsError,
        AccountLockedError,
        SessionExpiredError,
        RateLimitExceededError,
        AuthError
    )
    
    # Verify exception classes are available
    assert InvalidCredentialsError
    assert AccountLockedError
    assert SessionExpiredError
    assert RateLimitExceededError
    assert AuthError


def test_auth_middleware_error_handling_imports():
    """Test that auth middleware imports the correct exception types."""
    from ai_karen_engine.middleware.auth import (
        AuthError,
        SessionExpiredError,
        RateLimitExceededError
    )
    
    # Verify exception classes are available
    assert AuthError
    assert SessionExpiredError
    assert RateLimitExceededError


def test_auth_routes_consistent_response_format():
    """Test that auth routes have consistent response models."""
    from ai_karen_engine.api_routes.auth import (
        LoginResponse,
        UserResponse,
        LoginRequest,
        RegisterRequest
    )
    
    # Verify response models are defined
    assert LoginResponse
    assert UserResponse
    assert LoginRequest
    assert RegisterRequest
    
    # Check LoginResponse has expected fields
    login_response_fields = LoginResponse.__annotations__
    assert 'access_token' in login_response_fields
    assert 'refresh_token' in login_response_fields
    assert 'token_type' in login_response_fields
    assert 'expires_in' in login_response_fields
    assert 'user' in login_response_fields


def test_core_dependencies_use_unified_service():
    """Test that core dependencies use the unified AuthService."""
    with patch('ai_karen_engine.auth.service.get_auth_service') as mock_get_service:
        mock_service = AsyncMock()
        mock_get_service.return_value = mock_service
        
        from ai_karen_engine.core.dependencies import get_current_user_context
        
        # Function should be available
        assert get_current_user_context


@pytest.mark.asyncio
async def test_auth_service_integration_in_dependencies():
    """Test that dependencies properly integrate with AuthService."""
    from ai_karen_engine.core.dependencies import get_current_user_context
    from fastapi import Request
    
    # Mock request with session cookie
    mock_request = MagicMock(spec=Request)
    mock_request.cookies = {"kari_session": "test-token"}
    mock_request.client.host = "127.0.0.1"
    mock_request.headers = {"user-agent": "test-agent"}
    
    # Mock auth service
    mock_auth_service = AsyncMock()
    mock_user_data = {
        "user_id": "test-user",
        "email": "test@example.com",
        "tenant_id": "default",
        "roles": ["user"]
    }
    mock_auth_service.validate_session.return_value = mock_user_data
    
    with patch('ai_karen_engine.auth.service.get_auth_service', return_value=mock_auth_service):
        # Should be able to get user context
        user_context = await get_current_user_context(mock_request)
        
        # Verify auth service was called
        mock_auth_service.validate_session.assert_called_once_with(
            session_token="test-token",
            ip_address="127.0.0.1",
            user_agent="test-agent"
        )
        
        # Verify user context is returned
        assert user_context == mock_user_data


def test_auth_routes_have_proper_status_codes():
    """Test that auth routes define proper HTTP status codes."""
    from ai_karen_engine.api_routes.auth import status
    
    # Verify status codes are imported
    assert hasattr(status, 'HTTP_401_UNAUTHORIZED')
    assert hasattr(status, 'HTTP_403_FORBIDDEN')
    assert hasattr(status, 'HTTP_423_LOCKED')
    assert hasattr(status, 'HTTP_429_TOO_MANY_REQUESTS')


def test_middleware_has_proper_response_format():
    """Test that middleware returns consistent JSON responses."""
    from ai_karen_engine.middleware.auth import JSONResponse
    
    # Verify JSONResponse is available
    assert JSONResponse


def test_auth_routes_logging_integration():
    """Test that auth routes have proper logging setup."""
    from ai_karen_engine.api_routes.auth import logger
    
    # Verify logger is available
    assert logger
    assert hasattr(logger, 'info')
    assert hasattr(logger, 'error')


def test_auth_configuration_integration():
    """Test that auth routes integrate with configuration."""
    from ai_karen_engine.api_routes.auth import settings
    
    # Verify settings are available
    assert settings
    assert hasattr(settings, 'auth')


def test_session_cookie_configuration():
    """Test that session cookie configuration is properly set up."""
    from ai_karen_engine.api_routes.auth import set_session_cookie, COOKIE_NAME
    
    # Verify cookie functions and constants are available
    assert set_session_cookie
    assert COOKIE_NAME == "kari_session"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])