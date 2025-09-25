"""
Integration tests for enhanced authentication routes with session persistence.

Tests the complete authentication flow including login, token refresh,
session validation, and logout with secure cookie management.
"""

import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import AsyncClient

from ai_karen_engine.api_routes.auth_session_routes import router
from ai_karen_engine.auth.models import UserData, SessionData
from ai_karen_engine.auth.config import AuthConfig
from ai_karen_engine.auth.tokens import EnhancedTokenManager
from ai_karen_engine.auth.cookie_manager import SessionCookieManager
from ai_karen_engine.auth.exceptions import (
    InvalidCredentialsError,
    TokenExpiredError,
    InvalidTokenError,
    SessionExpiredError,
)


# Test fixtures
@pytest.fixture
def app():
    """Create FastAPI app with auth session routes."""
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def auth_config():
    """Create test auth configuration."""
    return AuthConfig.from_env()


@pytest.fixture
def token_manager(auth_config):
    """Create test token manager."""
    return EnhancedTokenManager(auth_config.jwt)


@pytest.fixture
def cookie_manager(auth_config):
    """Create test cookie manager."""
    return SessionCookieManager(auth_config)


@pytest.fixture
def sample_user():
    """Create sample user data."""
    return UserData(
        user_id="test-user-123",
        email="test@example.com",
        full_name="Test User",
        tenant_id="default",
        roles=["user"],
        is_verified=True,
        is_active=True,
        preferences={"theme": "dark"}
    )


@pytest.fixture
def sample_session_data(sample_user):
    """Create sample session data."""
    return SessionData(
        session_token="session-token-123",
        access_token="access-token-123",
        refresh_token="refresh-token-123",
        expires_in=900,  # 15 minutes
        user_data=sample_user,
        ip_address="127.0.0.1",
        user_agent="test-agent",
        created_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=15)
    )


class TestAuthSessionRoutes:
    """Test class for enhanced authentication routes."""

    @pytest.mark.asyncio
    async def test_register_success(self, client, sample_user):
        """Test successful user registration with session persistence."""
        
        # Mock auth service and token manager
        with patch('ai_karen_engine.api_routes.auth_session_routes.get_auth_service_instance') as mock_auth_service, \
             patch('ai_karen_engine.api_routes.auth_session_routes.get_token_manager') as mock_token_manager, \
             patch('ai_karen_engine.api_routes.auth_session_routes.get_cookie_manager_instance') as mock_cookie_manager:
            
            # Setup mocks
            auth_service_mock = AsyncMock()
            auth_service_mock.create_user.return_value = sample_user
            auth_service_mock.create_session.return_value = SessionData(
                session_token="session-123",
                access_token="access-123",
                refresh_token="refresh-123",
                expires_in=900,
                user_data=sample_user,
                ip_address="127.0.0.1",
                user_agent="test-agent",
                created_at=datetime.now(timezone.utc),
                expires_at=datetime.now(timezone.utc) + timedelta(minutes=15)
            )
            mock_auth_service.return_value = auth_service_mock
            
            token_manager_mock = AsyncMock()
            token_manager_mock.create_access_token.return_value = "access-token-123"
            token_manager_mock.create_refresh_token.return_value = "refresh-token-123"
            mock_token_manager.return_value = token_manager_mock
            
            cookie_manager_mock = MagicMock()
            mock_cookie_manager.return_value = cookie_manager_mock
            
            # Make request
            response = client.post("/auth/register", json={
                "email": "test@example.com",
                "password": "password123",
                "full_name": "Test User",
                "tenant_id": "default"
            })
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert data["access_token"] == "access-token-123"
            assert data["token_type"] == "bearer"
            assert data["expires_in"] == 900
            assert data["user"]["email"] == "test@example.com"
            assert data["user"]["user_id"] == "test-user-123"
            
            # Verify auth service was called
            auth_service_mock.create_user.assert_called_once()
            auth_service_mock.create_session.assert_called_once()
            
            # Verify token manager was called
            token_manager_mock.create_access_token.assert_called_once_with(sample_user)
            token_manager_mock.create_refresh_token.assert_called_once_with(sample_user)
            
            # Verify cookies were set
            cookie_manager_mock.set_refresh_token_cookie.assert_called_once()
            cookie_manager_mock.set_session_cookie.assert_called_once()

    @pytest.mark.asyncio
    async def test_login_success(self, client, sample_user):
        """Test successful user login with session persistence."""
        
        with patch('ai_karen_engine.api_routes.auth_session_routes.get_auth_service_instance') as mock_auth_service, \
             patch('ai_karen_engine.api_routes.auth_session_routes.get_token_manager') as mock_token_manager, \
             patch('ai_karen_engine.api_routes.auth_session_routes.get_cookie_manager_instance') as mock_cookie_manager:
            
            # Setup mocks
            auth_service_mock = AsyncMock()
            auth_service_mock.authenticate_user.return_value = sample_user
            auth_service_mock.create_session.return_value = SessionData(
                session_token="session-123",
                access_token="access-123",
                refresh_token="refresh-123",
                expires_in=900,
                user_data=sample_user,
                ip_address="127.0.0.1",
                user_agent="test-agent",
                created_at=datetime.now(timezone.utc),
                expires_at=datetime.now(timezone.utc) + timedelta(minutes=15)
            )
            mock_auth_service.return_value = auth_service_mock
            
            token_manager_mock = AsyncMock()
            token_manager_mock.create_access_token.return_value = "access-token-123"
            token_manager_mock.create_refresh_token.return_value = "refresh-token-123"
            mock_token_manager.return_value = token_manager_mock
            
            cookie_manager_mock = MagicMock()
            mock_cookie_manager.return_value = cookie_manager_mock
            
            # Make request
            response = client.post("/auth/login", json={
                "email": "test@example.com",
                "password": "password123"
            })
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert data["access_token"] == "access-token-123"
            assert data["token_type"] == "bearer"
            assert data["expires_in"] == 900
            assert data["user"]["email"] == "test@example.com"
            
            # Verify auth service was called
            auth_service_mock.authenticate_user.assert_called_once()
            auth_service_mock.create_session.assert_called_once()

    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials."""
        
        with patch('ai_karen_engine.api_routes.auth_session_routes.get_auth_service_instance') as mock_auth_service:
            
            auth_service_mock = AsyncMock()
            auth_service_mock.authenticate_user.side_effect = InvalidCredentialsError("Invalid credentials")
            mock_auth_service.return_value = auth_service_mock
            
            response = client.post("/auth/login", json={
                "email": "test@example.com",
                "password": "wrongpassword"
            })
            
            assert response.status_code == 401
            assert "Invalid credentials" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_refresh_token_success(self, client, sample_user):
        """Test successful token refresh."""
        
        with patch('ai_karen_engine.api_routes.auth_session_routes.get_token_manager') as mock_token_manager, \
             patch('ai_karen_engine.api_routes.auth_session_routes.get_cookie_manager_instance') as mock_cookie_manager:
            
            # Setup mocks
            token_manager_mock = AsyncMock()
            token_manager_mock.validate_refresh_token.return_value = {
                "sub": "test-user-123",
                "email": "test@example.com",
                "tenant_id": "default",
                "exp": (datetime.now(timezone.utc) + timedelta(days=7)).timestamp(),
                "jti": "refresh-jti-123"
            }
            token_manager_mock.rotate_tokens.return_value = (
                "new-access-token",
                "new-refresh-token", 
                datetime.now(timezone.utc) + timedelta(days=7)
            )
            mock_token_manager.return_value = token_manager_mock
            
            cookie_manager_mock = MagicMock()
            cookie_manager_mock.get_refresh_token.return_value = "refresh-token-123"
            mock_cookie_manager.return_value = cookie_manager_mock
            
            # Make request
            response = client.post("/auth/refresh")
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert data["access_token"] == "new-access-token"
            assert data["token_type"] == "bearer"
            assert data["expires_in"] == 900
            
            # Verify token rotation was called
            token_manager_mock.rotate_tokens.assert_called_once()
            
            # Verify new refresh token cookie was set
            cookie_manager_mock.set_refresh_token_cookie.assert_called_once()

    @pytest.mark.asyncio
    async def test_refresh_token_missing(self, client):
        """Test refresh token when no refresh token cookie is present."""
        
        with patch('ai_karen_engine.api_routes.auth_session_routes.get_cookie_manager_instance') as mock_cookie_manager:
            
            cookie_manager_mock = MagicMock()
            cookie_manager_mock.get_refresh_token.return_value = None
            mock_cookie_manager.return_value = cookie_manager_mock
            
            response = client.post("/auth/refresh")
            
            assert response.status_code == 401
            assert "Refresh token not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_refresh_token_expired(self, client):
        """Test refresh token when refresh token is expired."""
        
        with patch('ai_karen_engine.api_routes.auth_session_routes.get_token_manager') as mock_token_manager, \
             patch('ai_karen_engine.api_routes.auth_session_routes.get_cookie_manager_instance') as mock_cookie_manager:
            
            token_manager_mock = AsyncMock()
            token_manager_mock.validate_refresh_token.side_effect = TokenExpiredError("refresh")
            mock_token_manager.return_value = token_manager_mock
            
            cookie_manager_mock = MagicMock()
            cookie_manager_mock.get_refresh_token.return_value = "expired-refresh-token"
            mock_cookie_manager.return_value = cookie_manager_mock
            
            response = client.post("/auth/refresh")
            
            assert response.status_code == 401
            assert "Refresh token expired" in response.json()["detail"]
            
            # Verify expired cookie was cleared
            cookie_manager_mock.clear_refresh_token_cookie.assert_called_once()

    @pytest.mark.asyncio
    async def test_logout_success(self, client):
        """Test successful logout."""
        
        with patch('ai_karen_engine.api_routes.auth_session_routes.get_token_manager') as mock_token_manager, \
             patch('ai_karen_engine.api_routes.auth_session_routes.get_auth_service_instance') as mock_auth_service, \
             patch('ai_karen_engine.api_routes.auth_session_routes.get_cookie_manager_instance') as mock_cookie_manager:
            
            # Setup mocks
            token_manager_mock = AsyncMock()
            token_manager_mock.revoke_token.return_value = True
            mock_token_manager.return_value = token_manager_mock
            
            auth_service_mock = AsyncMock()
            auth_service_mock.invalidate_session.return_value = True
            mock_auth_service.return_value = auth_service_mock
            
            cookie_manager_mock = MagicMock()
            cookie_manager_mock.get_refresh_token.return_value = "refresh-token-123"
            cookie_manager_mock.get_session_token.return_value = "session-token-123"
            mock_cookie_manager.return_value = cookie_manager_mock
            
            # Make request
            response = client.post("/auth/logout")
            
            # Verify response
            assert response.status_code == 200
            assert response.json()["detail"] == "Logged out successfully"
            
            # Verify tokens were revoked
            token_manager_mock.revoke_token.assert_called_once_with("refresh-token-123")
            auth_service_mock.invalidate_session.assert_called_once_with("session-token-123", reason="logout")
            
            # Verify cookies were cleared
            cookie_manager_mock.clear_all_auth_cookies.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_current_user_success(self, client, sample_user):
        """Test getting current user from access token."""
        
        with patch('ai_karen_engine.api_routes.auth_session_routes.get_token_manager') as mock_token_manager:
            
            token_manager_mock = AsyncMock()
            token_manager_mock.validate_access_token.return_value = {
                "sub": "test-user-123",
                "email": "test@example.com",
                "full_name": "Test User",
                "roles": ["user"],
                "tenant_id": "default",
                "is_verified": True,
                "exp": (datetime.now(timezone.utc) + timedelta(minutes=15)).timestamp()
            }
            mock_token_manager.return_value = token_manager_mock
            
            # Make request with Authorization header
            response = client.get("/auth/me", headers={
                "Authorization": "Bearer access-token-123"
            })
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert data["user_id"] == "test-user-123"
            assert data["email"] == "test@example.com"
            assert data["full_name"] == "Test User"
            assert data["roles"] == ["user"]
            assert data["tenant_id"] == "default"
            assert data["is_verified"] is True

    @pytest.mark.asyncio
    async def test_get_current_user_missing_token(self, client):
        """Test getting current user without access token."""
        
        response = client.get("/auth/me")
        
        assert response.status_code == 401
        assert "Missing or invalid authorization header" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_current_user_expired_token(self, client):
        """Test getting current user with expired access token."""
        
        with patch('ai_karen_engine.api_routes.auth_session_routes.get_token_manager') as mock_token_manager:
            
            token_manager_mock = AsyncMock()
            token_manager_mock.validate_access_token.side_effect = TokenExpiredError("access")
            mock_token_manager.return_value = token_manager_mock
            
            response = client.get("/auth/me", headers={
                "Authorization": "Bearer expired-token"
            })
            
            assert response.status_code == 401
            assert "Access token expired" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_session_validation_middleware_access_token(self, client, sample_user):
        """Test session validation middleware with valid access token."""
        
        with patch('ai_karen_engine.api_routes.auth_session_routes.get_token_manager') as mock_token_manager:
            
            token_manager_mock = AsyncMock()
            token_manager_mock.validate_access_token.return_value = {
                "sub": "test-user-123",
                "email": "test@example.com",
                "full_name": "Test User",
                "roles": ["user"],
                "tenant_id": "default",
                "is_verified": True
            }
            mock_token_manager.return_value = token_manager_mock
            
            # Test with a protected endpoint that uses the middleware
            # Note: This would need to be implemented in the actual router
            # For now, we test the dependency function directly
            from ai_karen_engine.api_routes.auth_session_routes import get_current_user_from_token
            from fastapi import Request
            
            # Mock request
            request = MagicMock()
            request.headers.get.return_value = "Bearer access-token-123"
            
            # Mock request_meta
            request_meta = {"ip_address": "127.0.0.1", "user_agent": "test-agent"}
            
            # Call dependency
            user_data = await get_current_user_from_token(request, request_meta)
            
            assert user_data["user_id"] == "test-user-123"
            assert user_data["email"] == "test@example.com"

    @pytest.mark.asyncio
    async def test_session_validation_middleware_fallback_to_session(self, client, sample_user):
        """Test session validation middleware fallback to session validation."""
        
        with patch('ai_karen_engine.api_routes.auth_session_routes.get_token_manager') as mock_token_manager, \
             patch('ai_karen_engine.api_routes.auth_session_routes.get_auth_service_instance') as mock_auth_service, \
             patch('ai_karen_engine.api_routes.auth_session_routes.get_cookie_manager_instance') as mock_cookie_manager:
            
            # Setup token manager to fail (expired token)
            token_manager_mock = AsyncMock()
            token_manager_mock.validate_access_token.side_effect = TokenExpiredError("access")
            mock_token_manager.return_value = token_manager_mock
            
            # Setup auth service to succeed with session validation
            auth_service_mock = AsyncMock()
            auth_service_mock.validate_session.return_value = sample_user
            mock_auth_service.return_value = auth_service_mock
            
            # Setup cookie manager to return session token
            cookie_manager_mock = MagicMock()
            cookie_manager_mock.get_session_token.return_value = "session-token-123"
            mock_cookie_manager.return_value = cookie_manager_mock
            
            # Test the middleware function directly
            from ai_karen_engine.api_routes.auth_session_routes import validate_session_middleware
            from fastapi import Request
            
            # Mock request
            request = MagicMock()
            request.headers.get.return_value = "Bearer expired-token"
            
            # Mock request_meta
            request_meta = {"ip_address": "127.0.0.1", "user_agent": "test-agent"}
            
            # Call middleware
            user_data = await validate_session_middleware(request, request_meta)
            
            assert user_data["user_id"] == "test-user-123"
            assert user_data["email"] == "test@example.com"
            
            # Verify session validation was called
            auth_service_mock.validate_session.assert_called_once()

    @pytest.mark.asyncio
    async def test_health_check(self, client):
        """Test health check endpoint."""
        
        with patch('ai_karen_engine.api_routes.auth_session_routes.get_token_manager') as mock_token_manager, \
             patch('ai_karen_engine.api_routes.auth_session_routes.get_cookie_manager_instance') as mock_cookie_manager:
            
            # Setup mocks
            token_manager_mock = AsyncMock()
            mock_token_manager.return_value = token_manager_mock
            
            cookie_manager_mock = MagicMock()
            cookie_manager_mock.validate_cookie_security.return_value = {
                "valid": True,
                "issues": [],
                "recommendations": []
            }
            mock_cookie_manager.return_value = cookie_manager_mock
            
            response = client.get("/auth/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["service"] == "auth-session"
            assert data["features"]["token_rotation"] is True
            assert data["features"]["secure_cookies"] is True
            assert data["features"]["session_persistence"] is True


class TestTokenRotationFlow:
    """Test complete token rotation flow."""

    @pytest.mark.asyncio
    async def test_complete_auth_flow_with_refresh(self, client, sample_user):
        """Test complete authentication flow with token refresh."""
        
        with patch('ai_karen_engine.api_routes.auth_session_routes.get_auth_service_instance') as mock_auth_service, \
             patch('ai_karen_engine.api_routes.auth_session_routes.get_token_manager') as mock_token_manager, \
             patch('ai_karen_engine.api_routes.auth_session_routes.get_cookie_manager_instance') as mock_cookie_manager:
            
            # Setup mocks for login
            auth_service_mock = AsyncMock()
            auth_service_mock.authenticate_user.return_value = sample_user
            auth_service_mock.create_session.return_value = SessionData(
                session_token="session-123",
                access_token="access-123",
                refresh_token="refresh-123",
                expires_in=900,
                user_data=sample_user,
                ip_address="127.0.0.1",
                user_agent="test-agent",
                created_at=datetime.now(timezone.utc),
                expires_at=datetime.now(timezone.utc) + timedelta(minutes=15)
            )
            mock_auth_service.return_value = auth_service_mock
            
            token_manager_mock = AsyncMock()
            # First call for login
            token_manager_mock.create_access_token.return_value = "access-token-123"
            token_manager_mock.create_refresh_token.return_value = "refresh-token-123"
            # Second call for refresh
            token_manager_mock.validate_refresh_token.return_value = {
                "sub": "test-user-123",
                "email": "test@example.com",
                "tenant_id": "default",
                "exp": (datetime.now(timezone.utc) + timedelta(days=7)).timestamp(),
                "jti": "refresh-jti-123"
            }
            token_manager_mock.rotate_tokens.return_value = (
                "new-access-token",
                "new-refresh-token",
                datetime.now(timezone.utc) + timedelta(days=7)
            )
            mock_token_manager.return_value = token_manager_mock
            
            cookie_manager_mock = MagicMock()
            # For refresh endpoint
            cookie_manager_mock.get_refresh_token.return_value = "refresh-token-123"
            mock_cookie_manager.return_value = cookie_manager_mock
            
            # Step 1: Login
            login_response = client.post("/auth/login", json={
                "email": "test@example.com",
                "password": "password123"
            })
            
            assert login_response.status_code == 200
            login_data = login_response.json()
            assert login_data["access_token"] == "access-token-123"
            
            # Step 2: Refresh token
            refresh_response = client.post("/auth/refresh")
            
            assert refresh_response.status_code == 200
            refresh_data = refresh_response.json()
            assert refresh_data["access_token"] == "new-access-token"
            
            # Verify token rotation was called
            token_manager_mock.rotate_tokens.assert_called_once()


class TestCookieSecurityIntegration:
    """Test cookie security integration."""

    @pytest.mark.asyncio
    async def test_cookie_security_validation(self, client):
        """Test cookie security validation in health check."""
        
        with patch('ai_karen_engine.api_routes.auth_session_routes.get_token_manager') as mock_token_manager, \
             patch('ai_karen_engine.api_routes.auth_session_routes.get_cookie_manager_instance') as mock_cookie_manager:
            
            token_manager_mock = AsyncMock()
            mock_token_manager.return_value = token_manager_mock
            
            cookie_manager_mock = MagicMock()
            cookie_manager_mock.validate_cookie_security.return_value = {
                "valid": False,
                "issues": ["Secure flag should be True in production"],
                "recommendations": ["Set AUTH_SESSION_COOKIE_SECURE=true"],
                "current_config": {
                    "environment": "production",
                    "secure": False,
                    "httponly": True,
                    "samesite": "strict"
                }
            }
            mock_cookie_manager.return_value = cookie_manager_mock
            
            response = client.get("/auth/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["cookie_security"]["valid"] is False
            assert len(data["cookie_security"]["issues"]) > 0
            assert len(data["cookie_security"]["recommendations"]) > 0


if __name__ == "__main__":
    pytest.main([__file__])