"""
Integration tests for authentication routes and middleware.

Tests the complete authentication flow using the unified AuthService
including error handling and response formats.
"""

import asyncio
import json
import pytest
from datetime import datetime, timezone
from typing import Dict, Any
from unittest.mock import AsyncMock, patch, MagicMock

try:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from fastapi.responses import JSONResponse
    import httpx
except ImportError:
    pytest.skip("FastAPI not available", allow_module_level=True)

from src.ai_karen_engine.auth.models import UserData, SessionData, AuthEvent, AuthEventType
from src.ai_karen_engine.auth.exceptions import (
    InvalidCredentialsError,
    AccountLockedError,
    SessionExpiredError,
    RateLimitExceededError
)

# Mock the auth service at module level to avoid configuration loading
mock_auth_service_global = AsyncMock()

def mock_get_auth_service():
    return mock_auth_service_global

def mock_get_auth_service_instance():
    return mock_auth_service_global


class TestAuthRoutesIntegration:
    """Integration tests for authentication routes."""

    @pytest.fixture
    def mock_auth_service(self):
        """Mock AuthService for testing."""
        service = AsyncMock()
        
        # Mock user data
        service.sample_user = UserData(
            user_id="test-user-123",
            email="test@example.com",
            roles=["user"],
            tenant_id="default",
            preferences={"theme": "dark"},
            is_verified=True,
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        # Mock session data
        service.sample_session = SessionData(
            session_token="test-session-token",
            access_token="test-access-token",
            refresh_token="test-refresh-token",
            user_data=service.sample_user,
            expires_in=3600,
            created_at=datetime.now(timezone.utc),
            ip_address="127.0.0.1",
            user_agent="test-agent",
            risk_score=0.1
        )
        
        return service

    @pytest.fixture
    def test_app(self, mock_auth_service):
        """Create test FastAPI app with auth routes."""
        app = FastAPI()
        
        # Mock the auth service getter at module level
        with patch('src.ai_karen_engine.api_routes.auth.get_auth_service_instance') as mock_get_service:
            mock_get_service.return_value = mock_auth_service
            from src.ai_karen_engine.api_routes.auth import router
            app.include_router(router, prefix="/api/auth")
        
        return app

    @pytest.fixture
    def client(self, test_app):
        """Create test client."""
        return TestClient(test_app)

    def test_register_success(self, client, mock_auth_service):
        """Test successful user registration."""
        # Setup mock responses
        mock_auth_service.create_user.return_value = mock_auth_service.sample_user
        mock_auth_service.create_session.return_value = mock_auth_service.sample_session
        
        # Test registration
        response = client.post("/api/auth/register", json={
            "email": "test@example.com",
            "password": "StrongPass123!",
            "tenant_id": "default"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response format
        assert "access_token" in data
        assert "refresh_token" in data
        assert "token_type" in data
        assert "expires_in" in data
        assert "user" in data
        assert data["token_type"] == "bearer"
        
        # Verify user data format
        user_data = data["user"]
        assert user_data["user_id"] == "test-user-123"
        assert user_data["email"] == "test@example.com"
        assert user_data["tenant_id"] == "default"
        assert user_data["is_verified"] is True
        
        # Verify cookie is set
        assert "kari_session" in response.cookies

    def test_register_user_creation_failed(self, client, mock_auth_service):
        """Test registration when user creation fails."""
        mock_auth_service.create_user.return_value = None
        
        response = client.post("/api/auth/register", json={
            "email": "test@example.com",
            "password": "StrongPass123!"
        })
        
        assert response.status_code == 400
        assert response.json()["detail"] == "User creation failed"

    def test_register_validation_error(self, client, mock_auth_service):
        """Test registration with validation error."""
        mock_auth_service.create_user.side_effect = ValueError("Invalid email format")
        
        response = client.post("/api/auth/register", json={
            "email": "invalid-email",
            "password": "StrongPass123!"
        })
        
        assert response.status_code == 400
        assert "Invalid email format" in response.json()["detail"]

    def test_register_server_error(self, client, mock_auth_service):
        """Test registration with server error."""
        mock_auth_service.create_user.side_effect = Exception("Database error")
        
        response = client.post("/api/auth/register", json={
            "email": "test@example.com",
            "password": "StrongPass123!"
        })
        
        assert response.status_code == 500
        assert response.json()["detail"] == "Registration failed"

    def test_login_success(self, client, mock_auth_service):
        """Test successful user login."""
        # Setup mock responses
        mock_auth_service.authenticate_user.return_value = mock_auth_service.sample_user
        mock_auth_service.create_session.return_value = mock_auth_service.sample_session
        
        response = client.post("/api/auth/login", json={
            "email": "test@example.com",
            "password": "StrongPass123!"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response format
        assert "access_token" in data
        assert "refresh_token" in data
        assert "token_type" in data
        assert "expires_in" in data
        assert "user" in data
        
        # Verify cookie is set
        assert "kari_session" in response.cookies

    def test_login_invalid_credentials(self, client, mock_auth_service):
        """Test login with invalid credentials."""
        mock_auth_service.authenticate_user.return_value = None
        
        response = client.post("/api/auth/login", json={
            "email": "test@example.com",
            "password": "wrongpassword"
        })
        
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid credentials"

    def test_login_unverified_email(self, client, mock_auth_service):
        """Test login with unverified email."""
        unverified_user = UserData(
            user_id="test-user-123",
            email="test@example.com",
            roles=["user"],
            tenant_id="default",
            preferences={},
            is_verified=False,  # Not verified
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        mock_auth_service.authenticate_user.return_value = unverified_user
        
        response = client.post("/api/auth/login", json={
            "email": "test@example.com",
            "password": "StrongPass123!"
        })
        
        assert response.status_code == 403
        assert response.json()["detail"] == "Email not verified"

    def test_login_server_error(self, client, mock_auth_service):
        """Test login with server error."""
        mock_auth_service.authenticate_user.side_effect = Exception("Database error")
        
        response = client.post("/api/auth/login", json={
            "email": "test@example.com",
            "password": "StrongPass123!"
        })
        
        assert response.status_code == 500
        assert response.json()["detail"] == "Login failed"

    def test_get_current_user_success(self, client, mock_auth_service):
        """Test getting current user information."""
        # Mock the dependency to return user data
        user_data = {
            "user_id": "test-user-123",
            "email": "test@example.com",
            "full_name": None,
            "roles": ["user"],
            "tenant_id": "default",
            "preferences": {"theme": "dark"},
            "two_factor_enabled": False,
            "is_verified": True
        }
        
        with patch('src.ai_karen_engine.api_routes.auth.get_current_user', 
                  return_value=user_data):
            response = client.get("/api/auth/me")
        
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "test-user-123"
        assert data["email"] == "test@example.com"

    def test_update_credentials_success(self, client, mock_auth_service):
        """Test successful credential update."""
        # Setup mocks
        mock_auth_service.authenticate_user.return_value = mock_auth_service.sample_user
        mock_auth_service.update_user_password.return_value = True
        mock_auth_service.update_user_preferences.return_value = True
        mock_auth_service.create_session.return_value = mock_auth_service.sample_session
        
        # Mock session validation
        with patch('src.ai_karen_engine.api_routes.auth.get_session_user') as mock_get_session:
            mock_get_session.return_value = {
                "user_id": "test-user-123",
                "email": "test@example.com",
                "session_token": "old-token"
            }
            
            response = client.post("/api/auth/update_credentials", json={
                "current_password": "OldPass123!",
                "new_password": "NewPass123!",
                "preferences": {"theme": "light"}
            })
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "user" in data

    def test_update_credentials_missing_current_password(self, client, mock_auth_service):
        """Test credential update without current password."""
        with patch('src.ai_karen_engine.api_routes.auth.get_session_user') as mock_get_session:
            mock_get_session.return_value = {
                "user_id": "test-user-123",
                "email": "test@example.com"
            }
            
            response = client.post("/api/auth/update_credentials", json={
                "new_password": "NewPass123!"
            })
        
        assert response.status_code == 400
        assert response.json()["detail"] == "Current password required"

    def test_update_credentials_wrong_current_password(self, client, mock_auth_service):
        """Test credential update with wrong current password."""
        mock_auth_service.authenticate_user.return_value = None  # Wrong password
        
        with patch('src.ai_karen_engine.api_routes.auth.get_session_user') as mock_get_session:
            mock_get_session.return_value = {
                "user_id": "test-user-123",
                "email": "test@example.com"
            }
            
            response = client.post("/api/auth/update_credentials", json={
                "current_password": "WrongPass123!",
                "new_password": "NewPass123!"
            })
        
        assert response.status_code == 400
        assert response.json()["detail"] == "Current password is incorrect"

    def test_logout_success(self, client, mock_auth_service):
        """Test successful logout."""
        mock_auth_service.invalidate_session.return_value = True
        
        with patch('src.ai_karen_engine.api_routes.auth.get_session_user') as mock_get_session:
            mock_get_session.return_value = {
                "user_id": "test-user-123",
                "session_token": "test-token"
            }
            
            response = client.post("/api/auth/logout")
        
        assert response.status_code == 200
        assert response.json()["detail"] == "Logged out successfully"
        
        # Verify session was invalidated
        mock_auth_service.invalidate_session.assert_called_once_with("test-token")

    def test_request_password_reset_success(self, client, mock_auth_service):
        """Test successful password reset request."""
        mock_auth_service.create_password_reset_token.return_value = "reset-token-123"
        
        response = client.post("/api/auth/request_password_reset", json={
            "email": "test@example.com"
        })
        
        assert response.status_code == 200
        assert response.json()["detail"] == "Password reset link sent"

    def test_request_password_reset_user_not_found(self, client, mock_auth_service):
        """Test password reset request for non-existent user."""
        mock_auth_service.create_password_reset_token.return_value = None
        
        response = client.post("/api/auth/request_password_reset", json={
            "email": "nonexistent@example.com"
        })
        
        assert response.status_code == 200
        # Should not reveal if user exists
        assert "If the email exists" in response.json()["detail"]

    def test_reset_password_success(self, client, mock_auth_service):
        """Test successful password reset."""
        mock_auth_service.verify_password_reset_token.return_value = True
        
        response = client.post("/api/auth/reset_password", json={
            "token": "valid-reset-token",
            "new_password": "NewPass123!"
        })
        
        assert response.status_code == 200
        assert response.json()["detail"] == "Password updated successfully"

    def test_reset_password_invalid_token(self, client, mock_auth_service):
        """Test password reset with invalid token."""
        mock_auth_service.verify_password_reset_token.return_value = False
        
        response = client.post("/api/auth/reset_password", json={
            "token": "invalid-token",
            "new_password": "NewPass123!"
        })
        
        assert response.status_code == 400
        assert response.json()["detail"] == "Invalid or expired token"

    def test_health_check(self, client):
        """Test authentication health check."""
        response = client.get("/api/auth/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "auth"
        assert "timestamp" in data


class TestAuthMiddlewareIntegration:
    """Integration tests for authentication middleware."""

    @pytest.fixture
    def mock_auth_service(self):
        """Mock AuthService for middleware testing."""
        service = AsyncMock()
        service.sample_user = UserData(
            user_id="test-user-123",
            email="test@example.com",
            roles=["user"],
            tenant_id="default",
            preferences={},
            is_verified=True,
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        return service

    @pytest.fixture
    def test_app_with_middleware(self, mock_auth_service):
        """Create test app with auth middleware."""
        app = FastAPI()
        
        # Add a protected route for testing
        @app.get("/protected")
        async def protected_route():
            return {"message": "Access granted"}
        
        # Mock the middleware auth service
        with patch('src.ai_karen_engine.middleware.auth.get_auth_service', 
                  return_value=mock_auth_service):
            from src.ai_karen_engine.middleware.auth import auth_middleware
            app.middleware("http")(auth_middleware)
        
        return app

    @pytest.fixture
    def middleware_client(self, test_app_with_middleware):
        """Create test client with middleware."""
        return TestClient(test_app_with_middleware)

    def test_middleware_valid_token(self, middleware_client, mock_auth_service):
        """Test middleware with valid bearer token."""
        # Mock successful validation
        mock_auth_service.validate_session.return_value = mock_auth_service.sample_user
        
        response = middleware_client.get("/protected", 
                                       headers={"Authorization": "Bearer valid-token"})
        
        assert response.status_code == 200
        assert response.json()["message"] == "Access granted"

    def test_middleware_missing_token(self, middleware_client, mock_auth_service):
        """Test middleware without authorization header."""
        response = middleware_client.get("/protected")
        
        assert response.status_code == 401
        assert response.json()["detail"] == "Unauthorized"

    def test_middleware_invalid_token_format(self, middleware_client, mock_auth_service):
        """Test middleware with invalid token format."""
        response = middleware_client.get("/protected", 
                                       headers={"Authorization": "InvalidFormat"})
        
        assert response.status_code == 401
        assert response.json()["detail"] == "Unauthorized"

    def test_middleware_invalid_token(self, middleware_client, mock_auth_service):
        """Test middleware with invalid token."""
        mock_auth_service.validate_session.return_value = None
        
        response = middleware_client.get("/protected", 
                                       headers={"Authorization": "Bearer invalid-token"})
        
        assert response.status_code == 401
        assert response.json()["detail"] == "Unauthorized"

    def test_middleware_validation_exception(self, middleware_client, mock_auth_service):
        """Test middleware when validation raises exception."""
        mock_auth_service.validate_session.side_effect = Exception("Validation error")
        
        response = middleware_client.get("/protected", 
                                       headers={"Authorization": "Bearer error-token"})
        
        assert response.status_code == 401
        assert response.json()["detail"] == "Unauthorized"


class TestAuthErrorHandling:
    """Test consistent error handling across auth routes."""

    @pytest.fixture
    def mock_auth_service(self):
        """Mock AuthService for error testing."""
        return AsyncMock()

    @pytest.fixture
    def test_app(self, mock_auth_service):
        """Create test app for error testing."""
        app = FastAPI()
        
        with patch('src.ai_karen_engine.api_routes.auth.get_auth_service_instance', 
                  return_value=mock_auth_service):
            from src.ai_karen_engine.api_routes.auth import router
            app.include_router(router, prefix="/api/auth")
        
        return app

    @pytest.fixture
    def client(self, test_app):
        """Create test client."""
        return TestClient(test_app)

    def test_rate_limit_error_handling(self, client, mock_auth_service):
        """Test rate limit error handling."""
        mock_auth_service.authenticate_user.side_effect = RateLimitExceededError("Rate limit exceeded")
        
        response = client.post("/api/auth/login", json={
            "email": "test@example.com",
            "password": "password"
        })
        
        assert response.status_code == 500  # Generic error for now
        assert "Login failed" in response.json()["detail"]

    def test_account_locked_error_handling(self, client, mock_auth_service):
        """Test account locked error handling."""
        mock_auth_service.authenticate_user.side_effect = AccountLockedError("Account locked")
        
        response = client.post("/api/auth/login", json={
            "email": "test@example.com",
            "password": "password"
        })
        
        assert response.status_code == 500  # Generic error for now
        assert "Login failed" in response.json()["detail"]

    def test_session_expired_error_handling(self, client, mock_auth_service):
        """Test session expired error handling."""
        mock_auth_service.validate_session.side_effect = SessionExpiredError("Session expired")
        
        with patch('src.ai_karen_engine.api_routes.auth.get_session_user') as mock_get_session:
            mock_get_session.side_effect = Exception("Session validation failed")
            
            response = client.post("/api/auth/logout")
        
        # Should handle gracefully
        assert response.status_code in [401, 500]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])