"""
End-to-End Tests for Session Persistence and Premium Response System

Tests the complete user journey including:
- Login with session persistence
- Page refresh maintaining session
- Token expiry and automatic refresh
- Logout and session cleanup
- Error scenarios with intelligent responses
"""

import pytest
import asyncio
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional
from unittest.mock import patch, AsyncMock, MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import AsyncClient
import jwt

from ai_karen_engine.api_routes.auth_session_routes import router as auth_router
from ai_karen_engine.middleware.session_persistence import SessionPersistenceMiddleware
from ai_karen_engine.auth.models import UserData, SessionData
from ai_karen_engine.auth.config import AuthConfig
from ai_karen_engine.services.error_response_service import ErrorResponseService


@pytest.fixture
def app():
    """Create complete FastAPI app with auth routes and middleware."""
    app = FastAPI()
    
    # Add session persistence middleware
    app.add_middleware(SessionPersistenceMiddleware, enable_intelligent_errors=True)
    
    # Include auth routes
    app.include_router(auth_router)
    
    # Add protected test routes
    @app.get("/api/dashboard")
    async def dashboard():
        return {"message": "Welcome to dashboard", "data": "sensitive_data"}
    
    @app.get("/api/profile")
    async def profile():
        return {"message": "User profile", "settings": {"theme": "dark"}}
    
    @app.get("/api/admin/users")
    async def admin_users():
        return {"users": ["user1", "user2"], "total": 2}
    
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def sample_user():
    """Create sample user data."""
    return UserData(
        user_id="e2e-user-123",
        email="e2e@example.com",
        full_name="E2E Test User",
        tenant_id="default",
        roles=["user"],
        is_verified=True,
        is_active=True,
        preferences={"theme": "dark", "language": "en"}
    )


@pytest.fixture
def auth_config():
    """Create test auth configuration."""
    return AuthConfig.from_env()


class TestCompleteUserJourney:
    """Test complete user authentication journey with session persistence."""

    @pytest.mark.asyncio
    async def test_complete_login_to_logout_journey(self, client, sample_user):
        """Test complete user journey from login to logout."""
        
        with patch('ai_karen_engine.api_routes.auth_session_routes.get_auth_service_instance') as mock_auth_service, \
             patch('ai_karen_engine.api_routes.auth_session_routes.get_token_manager') as mock_token_manager, \
             patch('ai_karen_engine.api_routes.auth_session_routes.get_cookie_manager_instance') as mock_cookie_manager, \
             patch('ai_karen_engine.middleware.session_persistence.AuthConfig'):
            
            # Setup mocks for login
            auth_service_mock = AsyncMock()
            auth_service_mock.authenticate_user.return_value = sample_user
            auth_service_mock.create_session.return_value = SessionData(
                session_token="session-e2e-123",
                access_token="access-e2e-123",
                refresh_token="refresh-e2e-123",
                expires_in=900,
                user_data=sample_user,
                ip_address="127.0.0.1",
                user_agent="test-agent",
                created_at=datetime.now(timezone.utc),
                expires_at=datetime.now(timezone.utc) + timedelta(minutes=15)
            )
            mock_auth_service.return_value = auth_service_mock
            
            token_manager_mock = AsyncMock()
            token_manager_mock.create_access_token.return_value = "access-e2e-123"
            token_manager_mock.create_refresh_token.return_value = "refresh-e2e-123"
            token_manager_mock.validate_access_token.return_value = {
                "sub": "e2e-user-123",
                "email": "e2e@example.com",
                "full_name": "E2E Test User",
                "roles": ["user"],
                "tenant_id": "default",
                "is_verified": True
            }
            mock_token_manager.return_value = token_manager_mock
            
            cookie_manager_mock = MagicMock()
            mock_cookie_manager.return_value = cookie_manager_mock
            
            # Step 1: User logs in
            login_response = client.post("/auth/login", json={
                "email": "e2e@example.com",
                "password": "password123"
            })
            
            assert login_response.status_code == 200
            login_data = login_response.json()
            access_token = login_data["access_token"]
            
            # Verify login response structure
            assert login_data["token_type"] == "bearer"
            assert login_data["expires_in"] == 900
            assert login_data["user"]["email"] == "e2e@example.com"
            assert login_data["user"]["user_id"] == "e2e-user-123"
            
            # Verify cookies were set
            cookie_manager_mock.set_refresh_token_cookie.assert_called_once()
            cookie_manager_mock.set_session_cookie.assert_called_once()
            
            # Step 2: User accesses protected dashboard
            dashboard_response = client.get("/api/dashboard", headers={
                "Authorization": f"Bearer {access_token}"
            })
            
            assert dashboard_response.status_code == 200
            dashboard_data = dashboard_response.json()
            assert dashboard_data["message"] == "Welcome to dashboard"
            assert "sensitive_data" in dashboard_data["data"]
            
            # Step 3: User accesses profile
            profile_response = client.get("/api/profile", headers={
                "Authorization": f"Bearer {access_token}"
            })
            
            assert profile_response.status_code == 200
            profile_data = profile_response.json()
            assert profile_data["message"] == "User profile"
            assert profile_data["settings"]["theme"] == "dark"
            
            # Step 4: User logs out
            cookie_manager_mock.get_refresh_token.return_value = "refresh-e2e-123"
            cookie_manager_mock.get_session_token.return_value = "session-e2e-123"
            token_manager_mock.revoke_token.return_value = True
            auth_service_mock.invalidate_session.return_value = True
            
            logout_response = client.post("/auth/logout")
            
            assert logout_response.status_code == 200
            assert logout_response.json()["detail"] == "Logged out successfully"
            
            # Verify cleanup was called
            token_manager_mock.revoke_token.assert_called_once_with("refresh-e2e-123")
            auth_service_mock.invalidate_session.assert_called_once_with("session-e2e-123", reason="logout")
            cookie_manager_mock.clear_all_auth_cookies.assert_called_once()

    @pytest.mark.asyncio
    async def test_session_persistence_across_page_refresh(self, client, sample_user):
        """Test that session persists across page refresh (simulated by new requests)."""
        
        with patch('ai_karen_engine.api_routes.auth_session_routes.get_auth_service_instance') as mock_auth_service, \
             patch('ai_karen_engine.api_routes.auth_session_routes.get_token_manager') as mock_token_manager, \
             patch('ai_karen_engine.api_routes.auth_session_routes.get_cookie_manager_instance') as mock_cookie_manager, \
             patch('ai_karen_engine.middleware.session_persistence.AuthConfig'):
            
            # Setup initial login
            auth_service_mock = AsyncMock()
            auth_service_mock.authenticate_user.return_value = sample_user
            auth_service_mock.create_session.return_value = SessionData(
                session_token="session-persist-123",
                access_token="access-persist-123",
                refresh_token="refresh-persist-123",
                expires_in=900,
                user_data=sample_user,
                ip_address="127.0.0.1",
                user_agent="test-agent",
                created_at=datetime.now(timezone.utc),
                expires_at=datetime.now(timezone.utc) + timedelta(minutes=15)
            )
            mock_auth_service.return_value = auth_service_mock
            
            token_manager_mock = AsyncMock()
            token_manager_mock.create_access_token.return_value = "access-persist-123"
            token_manager_mock.create_refresh_token.return_value = "refresh-persist-123"
            token_manager_mock.validate_access_token.return_value = {
                "sub": "e2e-user-123",
                "email": "e2e@example.com",
                "full_name": "E2E Test User",
                "roles": ["user"],
                "tenant_id": "default",
                "is_verified": True
            }
            mock_token_manager.return_value = token_manager_mock
            
            cookie_manager_mock = MagicMock()
            mock_cookie_manager.return_value = cookie_manager_mock
            
            # Step 1: Initial login
            login_response = client.post("/auth/login", json={
                "email": "e2e@example.com",
                "password": "password123"
            })
            
            assert login_response.status_code == 200
            access_token = login_response.json()["access_token"]
            
            # Step 2: Access protected resource
            first_access = client.get("/api/dashboard", headers={
                "Authorization": f"Bearer {access_token}"
            })
            assert first_access.status_code == 200
            
            # Step 3: Simulate page refresh - new request with same token
            # In real scenario, frontend would use stored access token
            second_access = client.get("/api/profile", headers={
                "Authorization": f"Bearer {access_token}"
            })
            assert second_access.status_code == 200
            
            # Step 4: Simulate browser restart - access with refresh token only
            # Mock refresh token validation for session rehydration
            cookie_manager_mock.get_refresh_token.return_value = "refresh-persist-123"
            token_manager_mock.validate_refresh_token.return_value = {
                "sub": "e2e-user-123",
                "email": "e2e@example.com",
                "tenant_id": "default",
                "exp": (datetime.now(timezone.utc) + timedelta(days=7)).timestamp(),
                "jti": "refresh-jti-123"
            }
            token_manager_mock.rotate_tokens.return_value = (
                "new-access-persist-123",
                "new-refresh-persist-123",
                datetime.now(timezone.utc) + timedelta(days=7)
            )
            
            refresh_response = client.post("/auth/refresh")
            assert refresh_response.status_code == 200
            
            new_access_token = refresh_response.json()["access_token"]
            assert new_access_token == "new-access-persist-123"
            
            # Step 5: Continue using new access token
            token_manager_mock.validate_access_token.return_value = {
                "sub": "e2e-user-123",
                "email": "e2e@example.com",
                "full_name": "E2E Test User",
                "roles": ["user"],
                "tenant_id": "default",
                "is_verified": True
            }
            
            continued_access = client.get("/api/dashboard", headers={
                "Authorization": f"Bearer {new_access_token}"
            })
            assert continued_access.status_code == 200

    @pytest.mark.asyncio
    async def test_automatic_token_refresh_flow(self, client, sample_user):
        """Test automatic token refresh when access token expires."""
        
        with patch('ai_karen_engine.middleware.session_persistence.AuthConfig'), \
             patch('ai_karen_engine.middleware.session_persistence.EnhancedTokenManager') as mock_token_manager_class, \
             patch('ai_karen_engine.middleware.session_persistence.get_cookie_manager') as mock_cookie_manager_func:
            
            # Setup token manager mock
            token_manager_mock = AsyncMock()
            mock_token_manager_class.return_value = token_manager_mock
            
            # Setup cookie manager mock
            cookie_manager_mock = MagicMock()
            mock_cookie_manager_func.return_value = cookie_manager_mock
            
            # Step 1: First request with expired access token
            token_manager_mock.validate_access_token.side_effect = [
                # First call - token expired
                Exception("Token expired"),
                # Second call after refresh - valid token
                {
                    "sub": "e2e-user-123",
                    "email": "e2e@example.com",
                    "full_name": "E2E Test User",
                    "roles": ["user"],
                    "tenant_id": "default",
                    "is_verified": True
                }
            ]
            
            # Mock successful refresh token validation and rotation
            cookie_manager_mock.get_refresh_token.return_value = "valid-refresh-token"
            token_manager_mock.validate_refresh_token.return_value = {
                "sub": "e2e-user-123",
                "email": "e2e@example.com",
                "tenant_id": "default",
                "exp": (datetime.now(timezone.utc) + timedelta(days=7)).timestamp(),
                "jti": "refresh-jti-123"
            }
            
            new_expires_at = datetime.now(timezone.utc) + timedelta(days=7)
            token_manager_mock.rotate_tokens.return_value = (
                "new-access-token-auto",
                "new-refresh-token-auto",
                new_expires_at
            )
            
            # Make request with expired token
            response = client.get("/api/dashboard", headers={
                "Authorization": "Bearer expired-access-token"
            })
            
            # Should succeed after automatic refresh
            assert response.status_code == 200
            
            # Verify new access token is provided in response header
            assert "X-New-Access-Token" in response.headers
            assert response.headers["X-New-Access-Token"] == "new-access-token-auto"
            
            # Verify token rotation was called
            token_manager_mock.rotate_tokens.assert_called_once()
            cookie_manager_mock.set_refresh_token_cookie.assert_called_once()

    @pytest.mark.asyncio
    async def test_session_expiry_with_intelligent_error(self, client):
        """Test session expiry handling with intelligent error response."""
        
        with patch('ai_karen_engine.middleware.session_persistence.AuthConfig'), \
             patch('ai_karen_engine.middleware.session_persistence.EnhancedTokenManager') as mock_token_manager_class, \
             patch('ai_karen_engine.middleware.session_persistence.get_cookie_manager') as mock_cookie_manager_func, \
             patch('ai_karen_engine.middleware.session_persistence.ErrorResponseService') as mock_error_service_class:
            
            # Setup mocks
            token_manager_mock = AsyncMock()
            mock_token_manager_class.return_value = token_manager_mock
            
            cookie_manager_mock = MagicMock()
            mock_cookie_manager_func.return_value = cookie_manager_mock
            
            error_service_mock = MagicMock()
            mock_error_service_class.return_value = error_service_mock
            
            # Mock expired access token
            token_manager_mock.validate_access_token.side_effect = Exception("Token expired")
            
            # Mock expired refresh token
            cookie_manager_mock.get_refresh_token.return_value = "expired-refresh-token"
            token_manager_mock.validate_refresh_token.side_effect = Exception("Refresh token expired")
            
            # Mock intelligent error response
            mock_response = MagicMock()
            mock_response.summary = "Your session has expired. Please log in again to continue."
            mock_response.title = "Session Expired"
            mock_response.category = "authentication"
            mock_response.severity = "medium"
            mock_response.next_steps = [
                "Click the login button to sign in again",
                "Your work will be saved automatically"
            ]
            mock_response.contact_admin = False
            mock_response.retry_after = None
            mock_response.help_url = "https://docs.example.com/auth-troubleshooting"
            mock_response.provider_health = None
            mock_response.technical_details = None
            error_service_mock.analyze_error.return_value = mock_response
            
            # Make request with expired tokens
            response = client.get("/api/dashboard", headers={
                "Authorization": "Bearer expired-access-token"
            })
            
            assert response.status_code == 401
            data = response.json()
            
            # Verify intelligent error response structure
            assert "error" in data
            assert data["error"]["title"] == "Session Expired"
            assert data["error"]["summary"] == "Your session has expired. Please log in again to continue."
            assert data["error"]["category"] == "authentication"
            assert data["error"]["severity"] == "medium"
            assert len(data["error"]["next_steps"]) == 2
            assert data["error"]["contact_admin"] is False
            assert data["error"]["help_url"] == "https://docs.example.com/auth-troubleshooting"
            
            # Verify expired refresh token was cleared
            cookie_manager_mock.clear_refresh_token_cookie.assert_called_once()

    @pytest.mark.asyncio
    async def test_multiple_concurrent_requests_with_refresh(self, client, sample_user):
        """Test handling of multiple concurrent requests during token refresh."""
        
        with patch('ai_karen_engine.middleware.session_persistence.AuthConfig'), \
             patch('ai_karen_engine.middleware.session_persistence.EnhancedTokenManager') as mock_token_manager_class, \
             patch('ai_karen_engine.middleware.session_persistence.get_cookie_manager') as mock_cookie_manager_func:
            
            # Setup mocks
            token_manager_mock = AsyncMock()
            mock_token_manager_class.return_value = token_manager_mock
            
            cookie_manager_mock = MagicMock()
            mock_cookie_manager_func.return_value = cookie_manager_mock
            
            # Mock expired access token for first few calls, then valid token
            call_count = 0
            def mock_validate_access_token(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                if call_count <= 3:  # First 3 calls fail (expired)
                    raise Exception("Token expired")
                else:  # Subsequent calls succeed (after refresh)
                    return {
                        "sub": "e2e-user-123",
                        "email": "e2e@example.com",
                        "full_name": "E2E Test User",
                        "roles": ["user"],
                        "tenant_id": "default",
                        "is_verified": True
                    }
            
            token_manager_mock.validate_access_token.side_effect = mock_validate_access_token
            
            # Mock successful refresh
            cookie_manager_mock.get_refresh_token.return_value = "valid-refresh-token"
            token_manager_mock.validate_refresh_token.return_value = {
                "sub": "e2e-user-123",
                "email": "e2e@example.com",
                "tenant_id": "default",
                "exp": (datetime.now(timezone.utc) + timedelta(days=7)).timestamp(),
                "jti": "refresh-jti-123"
            }
            
            new_expires_at = datetime.now(timezone.utc) + timedelta(days=7)
            token_manager_mock.rotate_tokens.return_value = (
                "refreshed-access-token",
                "refreshed-refresh-token",
                new_expires_at
            )
            
            # Make multiple concurrent requests (simulated)
            responses = []
            for i in range(3):
                response = client.get(f"/api/dashboard", headers={
                    "Authorization": "Bearer expired-access-token"
                })
                responses.append(response)
            
            # All requests should eventually succeed
            for response in responses:
                assert response.status_code == 200
            
            # Token rotation should have been called (but potentially deduplicated)
            assert token_manager_mock.rotate_tokens.call_count >= 1

    @pytest.mark.asyncio
    async def test_admin_access_with_role_validation(self, client, sample_user):
        """Test admin access with role-based validation."""
        
        # Create admin user
        admin_user = UserData(
            user_id="admin-user-123",
            email="admin@example.com",
            full_name="Admin User",
            tenant_id="default",
            roles=["admin", "user"],
            is_verified=True,
            is_active=True,
            preferences={"theme": "light"}
        )
        
        with patch('ai_karen_engine.api_routes.auth_session_routes.get_auth_service_instance') as mock_auth_service, \
             patch('ai_karen_engine.api_routes.auth_session_routes.get_token_manager') as mock_token_manager, \
             patch('ai_karen_engine.api_routes.auth_session_routes.get_cookie_manager_instance') as mock_cookie_manager, \
             patch('ai_karen_engine.middleware.session_persistence.AuthConfig'):
            
            # Setup admin login
            auth_service_mock = AsyncMock()
            auth_service_mock.authenticate_user.return_value = admin_user
            auth_service_mock.create_session.return_value = SessionData(
                session_token="admin-session-123",
                access_token="admin-access-123",
                refresh_token="admin-refresh-123",
                expires_in=900,
                user_data=admin_user,
                ip_address="127.0.0.1",
                user_agent="test-agent",
                created_at=datetime.now(timezone.utc),
                expires_at=datetime.now(timezone.utc) + timedelta(minutes=15)
            )
            mock_auth_service.return_value = auth_service_mock
            
            token_manager_mock = AsyncMock()
            token_manager_mock.create_access_token.return_value = "admin-access-123"
            token_manager_mock.create_refresh_token.return_value = "admin-refresh-123"
            token_manager_mock.validate_access_token.return_value = {
                "sub": "admin-user-123",
                "email": "admin@example.com",
                "full_name": "Admin User",
                "roles": ["admin", "user"],
                "tenant_id": "default",
                "is_verified": True
            }
            mock_token_manager.return_value = token_manager_mock
            
            cookie_manager_mock = MagicMock()
            mock_cookie_manager.return_value = cookie_manager_mock
            
            # Admin login
            login_response = client.post("/auth/login", json={
                "email": "admin@example.com",
                "password": "admin123"
            })
            
            assert login_response.status_code == 200
            admin_token = login_response.json()["access_token"]
            
            # Access admin endpoint
            admin_response = client.get("/api/admin/users", headers={
                "Authorization": f"Bearer {admin_token}"
            })
            
            assert admin_response.status_code == 200
            admin_data = admin_response.json()
            assert "users" in admin_data
            assert admin_data["total"] == 2


class TestErrorScenarios:
    """Test various error scenarios with intelligent responses."""

    @pytest.mark.asyncio
    async def test_api_key_missing_error_response(self, client):
        """Test intelligent response for missing API key errors."""
        
        with patch('ai_karen_engine.middleware.session_persistence.AuthConfig'), \
             patch('ai_karen_engine.middleware.session_persistence.EnhancedTokenManager') as mock_token_manager_class, \
             patch('ai_karen_engine.middleware.session_persistence.ErrorResponseService') as mock_error_service_class:
            
            # Setup valid authentication
            token_manager_mock = AsyncMock()
            mock_token_manager_class.return_value = token_manager_mock
            token_manager_mock.validate_access_token.return_value = {
                "sub": "user123",
                "email": "test@example.com",
                "roles": ["user"],
                "tenant_id": "default",
                "is_verified": True
            }
            
            # Setup error service
            error_service_mock = MagicMock()
            mock_error_service_class.return_value = error_service_mock
            
            # Create app that simulates API key error
            app = FastAPI()
            app.add_middleware(SessionPersistenceMiddleware, enable_intelligent_errors=True)
            
            @app.get("/api/test/openai")
            async def openai_endpoint():
                raise Exception("OPENAI_API_KEY not set in environment")
            
            test_client = TestClient(app)
            
            # Mock intelligent error response
            mock_response = MagicMock()
            mock_response.summary = "OpenAI API key is missing from your configuration"
            mock_response.title = "OpenAI API Key Missing"
            mock_response.category = "api_key_missing"
            mock_response.severity = "high"
            mock_response.next_steps = [
                "Add OPENAI_API_KEY to your .env file",
                "Get your API key from https://platform.openai.com/api-keys",
                "Restart the application after adding the key"
            ]
            mock_response.contact_admin = False
            mock_response.retry_after = None
            mock_response.help_url = "https://docs.example.com/openai-setup"
            mock_response.provider_health = {"openai": {"status": "unhealthy", "reason": "missing_api_key"}}
            mock_response.technical_details = None
            error_service_mock.analyze_error.return_value = mock_response
            
            # Make request that triggers API key error
            response = test_client.get("/api/test/openai", headers={
                "Authorization": "Bearer valid-token"
            })
            
            assert response.status_code == 500
            data = response.json()
            
            # Verify intelligent error response
            assert data["error"]["title"] == "OpenAI API Key Missing"
            assert data["error"]["category"] == "api_key_missing"
            assert data["error"]["severity"] == "high"
            assert len(data["error"]["next_steps"]) == 3
            assert "Add OPENAI_API_KEY to your .env file" in data["error"]["next_steps"]
            assert data["error"]["help_url"] == "https://docs.example.com/openai-setup"
            assert data["error"]["provider_health"]["openai"]["status"] == "unhealthy"

    @pytest.mark.asyncio
    async def test_rate_limit_error_response(self, client):
        """Test intelligent response for rate limit errors."""
        
        with patch('ai_karen_engine.middleware.session_persistence.AuthConfig'), \
             patch('ai_karen_engine.middleware.session_persistence.EnhancedTokenManager') as mock_token_manager_class, \
             patch('ai_karen_engine.middleware.session_persistence.ErrorResponseService') as mock_error_service_class:
            
            # Setup valid authentication
            token_manager_mock = AsyncMock()
            mock_token_manager_class.return_value = token_manager_mock
            token_manager_mock.validate_access_token.return_value = {
                "sub": "user123",
                "email": "test@example.com",
                "roles": ["user"],
                "tenant_id": "default",
                "is_verified": True
            }
            
            # Setup error service
            error_service_mock = MagicMock()
            mock_error_service_class.return_value = error_service_mock
            
            # Create app that simulates rate limit error
            app = FastAPI()
            app.add_middleware(SessionPersistenceMiddleware, enable_intelligent_errors=True)
            
            from fastapi import HTTPException
            
            @app.get("/api/test/rate-limited")
            async def rate_limited_endpoint():
                raise HTTPException(status_code=429, detail="Rate limit exceeded")
            
            test_client = TestClient(app)
            
            # Mock intelligent error response
            mock_response = MagicMock()
            mock_response.summary = "You've exceeded the rate limit for API requests"
            mock_response.title = "Rate Limit Exceeded"
            mock_response.category = "rate_limit"
            mock_response.severity = "medium"
            mock_response.next_steps = [
                "Wait 5 minutes before trying again",
                "Consider upgrading your plan for higher limits",
                "Reduce the frequency of your requests"
            ]
            mock_response.contact_admin = False
            mock_response.retry_after = 300
            mock_response.help_url = "https://docs.example.com/rate-limits"
            mock_response.provider_health = None
            mock_response.technical_details = None
            error_service_mock.analyze_error.return_value = mock_response
            
            # Make request that triggers rate limit
            response = test_client.get("/api/test/rate-limited", headers={
                "Authorization": "Bearer valid-token"
            })
            
            assert response.status_code == 429
            data = response.json()
            
            # Verify intelligent error response
            assert data["error"]["title"] == "Rate Limit Exceeded"
            assert data["error"]["category"] == "rate_limit"
            assert data["error"]["severity"] == "medium"
            assert data["error"]["retry_after"] == 300
            assert "Wait 5 minutes before trying again" in data["error"]["next_steps"]
            assert data["error"]["help_url"] == "https://docs.example.com/rate-limits"

    @pytest.mark.asyncio
    async def test_database_error_response(self, client):
        """Test intelligent response for database errors."""
        
        with patch('ai_karen_engine.middleware.session_persistence.AuthConfig'), \
             patch('ai_karen_engine.middleware.session_persistence.EnhancedTokenManager') as mock_token_manager_class, \
             patch('ai_karen_engine.middleware.session_persistence.ErrorResponseService') as mock_error_service_class:
            
            # Setup valid authentication
            token_manager_mock = AsyncMock()
            mock_token_manager_class.return_value = token_manager_mock
            token_manager_mock.validate_access_token.return_value = {
                "sub": "user123",
                "email": "test@example.com",
                "roles": ["user"],
                "tenant_id": "default",
                "is_verified": True
            }
            
            # Setup error service
            error_service_mock = MagicMock()
            mock_error_service_class.return_value = error_service_mock
            
            # Create app that simulates database error
            app = FastAPI()
            app.add_middleware(SessionPersistenceMiddleware, enable_intelligent_errors=True)
            
            @app.get("/api/test/database")
            async def database_endpoint():
                raise Exception('relation "users" does not exist')
            
            test_client = TestClient(app)
            
            # Mock intelligent error response
            mock_response = MagicMock()
            mock_response.summary = "The database is not properly initialized"
            mock_response.title = "Database Not Initialized"
            mock_response.category = "database_error"
            mock_response.severity = "critical"
            mock_response.next_steps = [
                "Contact admin to run database migrations",
                "The system needs to be properly set up"
            ]
            mock_response.contact_admin = True
            mock_response.retry_after = None
            mock_response.help_url = "https://docs.example.com/database-setup"
            mock_response.provider_health = None
            mock_response.technical_details = 'relation "users" does not exist'
            error_service_mock.analyze_error.return_value = mock_response
            
            # Make request that triggers database error
            response = test_client.get("/api/test/database", headers={
                "Authorization": "Bearer valid-token"
            })
            
            assert response.status_code == 500
            data = response.json()
            
            # Verify intelligent error response
            assert data["error"]["title"] == "Database Not Initialized"
            assert data["error"]["category"] == "database_error"
            assert data["error"]["severity"] == "critical"
            assert data["error"]["contact_admin"] is True
            assert "Contact admin to run database migrations" in data["error"]["next_steps"]
            assert data["error"]["technical_details"] == 'relation "users" does not exist'


class TestPerformanceAndReliability:
    """Test performance and reliability aspects of the session system."""

    @pytest.mark.asyncio
    async def test_session_performance_under_load(self, client):
        """Test session validation performance under simulated load."""
        
        with patch('ai_karen_engine.middleware.session_persistence.AuthConfig'), \
             patch('ai_karen_engine.middleware.session_persistence.EnhancedTokenManager') as mock_token_manager_class:
            
            # Setup fast token validation
            token_manager_mock = AsyncMock()
            mock_token_manager_class.return_value = token_manager_mock
            token_manager_mock.validate_access_token.return_value = {
                "sub": "perf-user-123",
                "email": "perf@example.com",
                "roles": ["user"],
                "tenant_id": "default",
                "is_verified": True
            }
            
            # Measure performance of multiple requests
            start_time = time.time()
            
            responses = []
            for i in range(10):  # Simulate 10 concurrent requests
                response = client.get("/api/dashboard", headers={
                    "Authorization": "Bearer performance-token"
                })
                responses.append(response)
            
            end_time = time.time()
            total_time = end_time - start_time
            
            # All requests should succeed
            for response in responses:
                assert response.status_code == 200
            
            # Performance should be reasonable (less than 1 second for 10 requests)
            assert total_time < 1.0
            
            # Average response time should be reasonable
            avg_time = total_time / len(responses)
            assert avg_time < 0.1  # Less than 100ms per request

    @pytest.mark.asyncio
    async def test_graceful_degradation_on_service_failure(self, client):
        """Test graceful degradation when auth services fail."""
        
        with patch('ai_karen_engine.middleware.session_persistence.AuthConfig'), \
             patch('ai_karen_engine.middleware.session_persistence.EnhancedTokenManager') as mock_token_manager_class, \
             patch('ai_karen_engine.middleware.session_persistence.ErrorResponseService') as mock_error_service_class:
            
            # Setup token manager to fail
            token_manager_mock = AsyncMock()
            mock_token_manager_class.return_value = token_manager_mock
            token_manager_mock.validate_access_token.side_effect = Exception("Service unavailable")
            
            # Setup error service
            error_service_mock = MagicMock()
            mock_error_service_class.return_value = error_service_mock
            
            # Mock graceful error response
            mock_response = MagicMock()
            mock_response.summary = "Authentication service is temporarily unavailable"
            mock_response.title = "Service Temporarily Unavailable"
            mock_response.category = "service_unavailable"
            mock_response.severity = "high"
            mock_response.next_steps = [
                "Try again in a few minutes",
                "Contact admin if problem persists"
            ]
            mock_response.contact_admin = True
            mock_response.retry_after = 180
            mock_response.help_url = None
            mock_response.provider_health = None
            mock_response.technical_details = None
            error_service_mock.analyze_error.return_value = mock_response
            
            # Make request when service is down
            response = client.get("/api/dashboard", headers={
                "Authorization": "Bearer any-token"
            })
            
            assert response.status_code == 503  # Service Unavailable
            data = response.json()
            
            # Verify graceful error response
            assert data["error"]["title"] == "Service Temporarily Unavailable"
            assert data["error"]["retry_after"] == 180
            assert data["error"]["contact_admin"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])