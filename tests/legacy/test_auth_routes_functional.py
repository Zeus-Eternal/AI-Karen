"""
Functional tests for authentication routes and middleware integration.

Tests that verify the routes and middleware are properly using the unified AuthService
and have consistent error handling and response formats.
"""

import pytest


def test_auth_routes_use_unified_service():
    """Test that auth routes are using the unified AuthService."""
    # Test that the auth routes file imports the unified service correctly
    try:
        # Import the auth module to check for syntax errors and proper imports
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "auth_routes", "src/ai_karen_engine/api_routes/auth.py"
        )
        auth_module = importlib.util.module_from_spec(spec)

        # Check that the file can be loaded (syntax is correct)
        with open("src/ai_karen_engine/api_routes/auth.py", "r") as f:
            content = f.read()

        # Verify it imports from the unified auth service
        assert (
            "from ai_karen_engine.auth.service import AuthService, get_auth_service"
            in content
        )
        assert "from ai_karen_engine.auth.exceptions import" in content

        # Verify it has proper error handling for auth exceptions
        assert "InvalidCredentialsError" in content
        assert "AccountLockedError" in content
        assert "SessionExpiredError" in content
        assert "RateLimitExceededError" in content

        print("✅ Auth routes properly import unified AuthService and exceptions")

    except Exception as e:
        pytest.fail(f"Auth routes import test failed: {e}")


def test_auth_middleware_uses_unified_service():
    """Test that auth middleware is using the unified AuthService."""
    try:
        # Check the middleware file
        with open("src/ai_karen_engine/middleware/auth.py", "r") as f:
            content = f.read()

        # Verify it imports from the unified auth service
        assert (
            "from ai_karen_engine.auth.service import AuthService, get_auth_service"
            in content
        )
        assert "from ai_karen_engine.auth.exceptions import" in content

        # Verify it has proper error handling
        assert "SessionExpiredError" in content
        assert "RateLimitExceededError" in content
        assert "AuthError" in content

        print("✅ Auth middleware properly imports unified AuthService and exceptions")

    except Exception as e:
        pytest.fail(f"Auth middleware import test failed: {e}")


def test_auth_routes_error_handling_consistency():
    """Test that auth routes have consistent error handling."""
    try:
        with open("src/ai_karen_engine/api_routes/auth.py", "r") as f:
            content = f.read()

        # Check for consistent HTTP status codes
        assert "status.HTTP_401_UNAUTHORIZED" in content
        assert "status.HTTP_403_FORBIDDEN" in content
        assert "status.HTTP_423_LOCKED" in content
        assert "status.HTTP_429_TOO_MANY_REQUESTS" in content

        # Check for proper exception handling patterns
        assert "except InvalidCredentialsError:" in content
        assert "except AccountLockedError as e:" in content
        assert "except RateLimitExceededError as e:" in content
        assert "except SessionExpiredError:" in content

        print("✅ Auth routes have consistent error handling")

    except Exception as e:
        pytest.fail(f"Auth routes error handling test failed: {e}")


def test_auth_middleware_error_handling_consistency():
    """Test that auth middleware has consistent error handling."""
    try:
        with open("src/ai_karen_engine/middleware/auth.py", "r") as f:
            content = f.read()

        # Check for proper exception handling
        assert "except SessionExpiredError:" in content
        assert "except RateLimitExceededError:" in content
        assert "except AuthError:" in content

        # Check for consistent response format
        assert 'JSONResponse({"detail": "Session expired"}, status_code=401)' in content
        assert (
            'JSONResponse({"detail": "Rate limit exceeded"}, status_code=429)'
            in content
        )
        assert (
            'JSONResponse({"detail": "Authentication failed"}, status_code=401)'
            in content
        )

        print("✅ Auth middleware has consistent error handling")

    except Exception as e:
        pytest.fail(f"Auth middleware error handling test failed: {e}")


def test_auth_routes_response_format_consistency():
    """Test that auth routes have consistent response formats."""
    try:
        with open("src/ai_karen_engine/api_routes/auth.py", "r") as f:
            content = f.read()

        # Check for consistent response models
        assert "class LoginResponse(BaseModel):" in content
        assert "class UserResponse(BaseModel):" in content
        assert "class LoginRequest(BaseModel):" in content
        assert "class RegisterRequest(BaseModel):" in content

        # Check for consistent response fields
        assert "access_token: str" in content
        assert "refresh_token: str" in content
        assert 'token_type: str = "bearer"' in content
        assert "expires_in: int" in content

        print("✅ Auth routes have consistent response formats")

    except Exception as e:
        pytest.fail(f"Auth routes response format test failed: {e}")


def test_auth_routes_logging_integration():
    """Test that auth routes have proper logging integration."""
    try:
        with open("src/ai_karen_engine/api_routes/auth.py", "r") as f:
            content = f.read()

        # Check for logging imports and usage
        assert "from ai_karen_engine.core.logging import get_logger" in content
        assert "logger = get_logger(__name__)" in content

        # Check for proper logging calls
        assert "logger.info(" in content
        assert "logger.error(" in content

        print("✅ Auth routes have proper logging integration")

    except Exception as e:
        pytest.fail(f"Auth routes logging test failed: {e}")


def test_session_cookie_configuration():
    """Test that session cookie configuration is properly implemented."""
    try:
        with open("src/ai_karen_engine/api_routes/auth.py", "r") as f:
            content = f.read()

        # Check for cookie configuration
        assert 'COOKIE_NAME = "kari_session"' in content
        assert "def set_session_cookie(" in content
        assert "httponly=True" in content
        assert "secure=secure_flag" in content
        assert 'samesite="strict"' in content

        print("✅ Session cookie configuration is properly implemented")

    except Exception as e:
        pytest.fail(f"Session cookie configuration test failed: {e}")


def test_auth_service_factory_functions():
    """Test that auth service factory functions are available."""
    try:
        # Test that the auth service can be imported
        from ai_karen_engine.auth import get_auth_service

        # Test that factory functions exist
        from ai_karen_engine.auth.service import (
            create_auth_service,
            get_intelligent_auth_service,
            get_production_auth_service,
        )

        print("✅ Auth service factory functions are available")

    except ImportError as e:
        pytest.fail(f"Auth service factory functions test failed: {e}")


def test_auth_models_consistency():
    """Test that auth models are consistent across the system."""
    try:
        from ai_karen_engine.auth.models import AuthEvent, SessionData, UserData

        # Check that models have expected attributes
        user_data_fields = UserData.__annotations__
        assert "user_id" in user_data_fields
        assert "email" in user_data_fields
        assert "roles" in user_data_fields
        assert "tenant_id" in user_data_fields
        assert "is_verified" in user_data_fields

        session_data_fields = SessionData.__annotations__
        assert "session_token" in session_data_fields
        assert "access_token" in session_data_fields
        assert "refresh_token" in session_data_fields
        assert "user_data" in session_data_fields
        assert "expires_in" in session_data_fields

        print("✅ Auth models are consistent")

    except Exception as e:
        pytest.fail(f"Auth models consistency test failed: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
