"""
Tests for Session Persistence Middleware

Tests the session persistence middleware functionality including:
- Access token validation
- Automatic token refresh for expired tokens
- Intelligent error responses
- Integration with existing auth system
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from fastapi import FastAPI, Request, HTTPException
from fastapi.testclient import TestClient
from fastapi.responses import JSONResponse

from ai_karen_engine.middleware.session_persistence import SessionPersistenceMiddleware
from ai_karen_engine.auth.exceptions import TokenExpiredError, InvalidTokenError
from ai_karen_engine.auth.models import UserData


@pytest.fixture
def app():
    """Create test FastAPI app with session persistence middleware."""
    app = FastAPI()
    
    # Add middleware
    app.add_middleware(SessionPersistenceMiddleware, enable_intelligent_errors=True)
    
    # Add test routes
    @app.get("/api/test/protected")
    async def protected_route(request: Request):
        user_id = getattr(request.state, "user", None)
        user_data = getattr(request.state, "user_data", None)
        return {
            "message": "success",
            "user_id": user_id,
            "user_data": user_data
        }
    
    @app.get("/api/test/public")
    async def public_route():
        return {"message": "public"}
    
    @app.get("/api/auth/login")
    async def auth_route():
        return {"message": "auth route"}
    
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_token_manager():
    """Mock token manager."""
    with patch("ai_karen_engine.middleware.session_persistence.EnhancedTokenManager") as mock:
        instance = Mock()
        mock.return_value = instance
        yield instance


@pytest.fixture
def mock_cookie_manager():
    """Mock cookie manager."""
    with patch("ai_karen_engine.middleware.session_persistence.get_cookie_manager") as mock:
        instance = Mock()
        mock.return_value = instance
        yield instance


@pytest.fixture
def mock_auth_service():
    """Mock auth service."""
    with patch("ai_karen_engine.middleware.session_persistence.get_auth_service") as mock:
        instance = AsyncMock()
        mock.return_value = instance
        yield instance


@pytest.fixture
def mock_error_service():
    """Mock error response service."""
    with patch("ai_karen_engine.middleware.session_persistence.ErrorResponseService") as mock:
        instance = Mock()
        mock.return_value = instance
        yield instance


class TestSessionPersistenceMiddleware:
    """Test session persistence middleware functionality."""
    
    def test_public_routes_skip_auth(self, client):
        """Test that public routes skip authentication."""
        response = client.get("/api/test/public")
        assert response.status_code == 200
        assert response.json() == {"message": "public"}
    
    def test_auth_routes_skip_session_persistence(self, client):
        """Test that auth routes skip session persistence middleware."""
        response = client.get("/api/auth/login")
        assert response.status_code == 200
        assert response.json() == {"message": "auth route"}
    
    def test_missing_auth_header(self, client, mock_error_service):
        """Test handling of missing authorization header."""
        # Mock error service response
        mock_response = Mock()
        mock_response.summary = "Missing authorization header"
        mock_response.title = "Authentication Required"
        mock_response.category = "authentication"
        mock_response.severity = "medium"
        mock_response.next_steps = ["Please log in to access this resource"]
        mock_response.contact_admin = False
        mock_response.retry_after = None
        mock_response.help_url = None
        mock_response.provider_health = None
        mock_response.technical_details = None
        mock_error_service.analyze_error.return_value = mock_response
        
        response = client.get("/api/test/protected")
        assert response.status_code == 401
        
        data = response.json()
        assert "detail" in data
        assert "error" in data
        assert data["error"]["title"] == "Authentication Required"
    
    def test_invalid_auth_header_format(self, client, mock_error_service):
        """Test handling of invalid authorization header format."""
        # Mock error service response
        mock_response = Mock()
        mock_response.summary = "Invalid authorization header format"
        mock_response.title = "Authentication Required"
        mock_response.category = "authentication"
        mock_response.severity = "medium"
        mock_response.next_steps = ["Please provide a valid Bearer token"]
        mock_response.contact_admin = False
        mock_response.retry_after = None
        mock_response.help_url = None
        mock_response.provider_health = None
        mock_response.technical_details = None
        mock_error_service.analyze_error.return_value = mock_response
        
        response = client.get(
            "/api/test/protected",
            headers={"Authorization": "Invalid token"}
        )
        assert response.status_code == 401
    
    @patch("ai_karen_engine.middleware.session_persistence.AuthConfig")
    def test_valid_access_token(
        self, 
        mock_auth_config,
        client, 
        mock_token_manager, 
        mock_cookie_manager,
        mock_auth_service
    ):
        """Test successful validation of valid access token."""
        # Mock token validation
        mock_token_manager.validate_access_token.return_value = {
            "sub": "user123",
            "email": "test@example.com",
            "roles": ["user"],
            "tenant_id": "default",
            "is_verified": True
        }
        
        response = client.get(
            "/api/test/protected",
            headers={"Authorization": "Bearer valid_token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "user123"
        assert data["user_data"]["email"] == "test@example.com"
    
    @patch("ai_karen_engine.middleware.session_persistence.AuthConfig")
    def test_expired_token_with_successful_refresh(
        self,
        mock_auth_config,
        client,
        mock_token_manager,
        mock_cookie_manager,
        mock_auth_service
    ):
        """Test automatic token refresh when access token is expired."""
        # Mock expired access token
        mock_token_manager.validate_access_token.side_effect = TokenExpiredError("Token expired")
        
        # Mock successful refresh token validation
        mock_cookie_manager.get_refresh_token.return_value = "refresh_token"
        mock_token_manager.validate_refresh_token.return_value = {
            "sub": "user123",
            "email": "test@example.com",
            "tenant_id": "default"
        }
        
        # Mock token rotation
        new_expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        mock_token_manager.rotate_tokens.return_value = (
            "new_access_token",
            "new_refresh_token", 
            new_expires_at
        )
        
        response = client.get(
            "/api/test/protected",
            headers={"Authorization": "Bearer expired_token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "user123"
        
        # Verify token refresh was called
        mock_token_manager.rotate_tokens.assert_called_once()
        mock_cookie_manager.set_refresh_token_cookie.assert_called_once()
        
        # Verify new access token is in response headers
        assert "X-New-Access-Token" in response.headers
        assert response.headers["X-New-Access-Token"] == "new_access_token"
    
    @patch("ai_karen_engine.middleware.session_persistence.AuthConfig")
    def test_expired_token_with_failed_refresh(
        self,
        mock_auth_config,
        client,
        mock_token_manager,
        mock_cookie_manager,
        mock_error_service
    ):
        """Test handling when both access token and refresh token are expired."""
        # Mock expired access token
        mock_token_manager.validate_access_token.side_effect = TokenExpiredError("Token expired")
        
        # Mock expired refresh token
        mock_cookie_manager.get_refresh_token.return_value = "expired_refresh_token"
        mock_token_manager.validate_refresh_token.side_effect = TokenExpiredError("Refresh token expired")
        
        # Mock error service response
        mock_response = Mock()
        mock_response.summary = "Your session has expired. Please log in again."
        mock_response.title = "Session Expired"
        mock_response.category = "authentication"
        mock_response.severity = "medium"
        mock_response.next_steps = ["Click the login button to sign in again"]
        mock_response.contact_admin = False
        mock_response.retry_after = None
        mock_response.help_url = None
        mock_response.provider_health = None
        mock_response.technical_details = None
        mock_error_service.analyze_error.return_value = mock_response
        
        response = client.get(
            "/api/test/protected",
            headers={"Authorization": "Bearer expired_token"}
        )
        
        assert response.status_code == 401
        data = response.json()
        assert data["error"]["title"] == "Session Expired"
        
        # Verify expired refresh token cookie was cleared
        mock_cookie_manager.clear_refresh_token_cookie.assert_called_once()
    
    @patch("ai_karen_engine.middleware.session_persistence.AuthConfig")
    def test_invalid_access_token(
        self,
        mock_auth_config,
        client,
        mock_token_manager,
        mock_error_service
    ):
        """Test handling of invalid access token."""
        # Mock invalid access token
        mock_token_manager.validate_access_token.side_effect = InvalidTokenError("Invalid token")
        
        response = client.get(
            "/api/test/protected",
            headers={"Authorization": "Bearer invalid_token"}
        )
        
        assert response.status_code == 401
    
    @patch("ai_karen_engine.middleware.session_persistence.AuthConfig")
    def test_no_refresh_token_available(
        self,
        mock_auth_config,
        client,
        mock_token_manager,
        mock_cookie_manager,
        mock_error_service
    ):
        """Test handling when no refresh token is available for expired access token."""
        # Mock expired access token
        mock_token_manager.validate_access_token.side_effect = TokenExpiredError("Token expired")
        
        # Mock no refresh token in cookies
        mock_cookie_manager.get_refresh_token.return_value = None
        
        # Mock error service response
        mock_response = Mock()
        mock_response.summary = "Access token expired and no refresh token available"
        mock_response.title = "Session Expired"
        mock_response.category = "authentication"
        mock_response.severity = "medium"
        mock_response.next_steps = ["Please log in again"]
        mock_response.contact_admin = False
        mock_response.retry_after = None
        mock_response.help_url = None
        mock_response.provider_health = None
        mock_response.technical_details = None
        mock_error_service.analyze_error.return_value = mock_response
        
        response = client.get(
            "/api/test/protected",
            headers={"Authorization": "Bearer expired_token"}
        )
        
        assert response.status_code == 401
        data = response.json()
        assert data["error"]["title"] == "Session Expired"
    
    def test_error_service_disabled(self, client):
        """Test middleware behavior when error service is disabled."""
        # Create app with error service disabled
        app = FastAPI()
        app.add_middleware(SessionPersistenceMiddleware, enable_intelligent_errors=False)
        
        @app.get("/api/test/protected")
        async def protected_route():
            return {"message": "success"}
        
        test_client = TestClient(app)
        
        response = test_client.get("/api/test/protected")
        assert response.status_code == 401
        
        # Should get simple error response
        data = response.json()
        assert "detail" in data
        assert "error" not in data  # No intelligent error structure
    
    @patch("ai_karen_engine.middleware.session_persistence.AuthConfig")
    def test_http_exception_handling(
        self,
        mock_auth_config,
        client,
        mock_token_manager,
        mock_error_service
    ):
        """Test handling of HTTP exceptions raised by downstream handlers."""
        # Mock valid token
        mock_token_manager.validate_access_token.return_value = {
            "sub": "user123",
            "email": "test@example.com",
            "roles": ["user"],
            "tenant_id": "default",
            "is_verified": True
        }
        
        # Create app that raises HTTP exception
        app = FastAPI()
        app.add_middleware(SessionPersistenceMiddleware, enable_intelligent_errors=True)
        
        @app.get("/api/test/error")
        async def error_route():
            raise HTTPException(status_code=403, detail="Forbidden")
        
        test_client = TestClient(app)
        
        # Mock error service response
        mock_response = Mock()
        mock_response.summary = "You don't have permission to access this resource"
        mock_response.title = "Access Denied"
        mock_response.category = "authorization"
        mock_response.severity = "medium"
        mock_response.next_steps = ["Contact admin for access"]
        mock_response.contact_admin = True
        mock_response.retry_after = None
        mock_response.help_url = None
        mock_response.provider_health = None
        mock_response.technical_details = None
        mock_error_service.analyze_error.return_value = mock_response
        
        response = test_client.get(
            "/api/test/error",
            headers={"Authorization": "Bearer valid_token"}
        )
        
        assert response.status_code == 403
        data = response.json()
        assert data["error"]["title"] == "Access Denied"
        assert data["error"]["contact_admin"] is True
    
    @patch("ai_karen_engine.middleware.session_persistence.AuthConfig")
    def test_unhandled_exception_handling(
        self,
        mock_auth_config,
        client,
        mock_token_manager,
        mock_error_service
    ):
        """Test handling of unhandled exceptions raised by downstream handlers."""
        # Mock valid token
        mock_token_manager.validate_access_token.return_value = {
            "sub": "user123",
            "email": "test@example.com",
            "roles": ["user"],
            "tenant_id": "default",
            "is_verified": True
        }
        
        # Create app that raises unhandled exception
        app = FastAPI()
        app.add_middleware(SessionPersistenceMiddleware, enable_intelligent_errors=True)
        
        @app.get("/api/test/crash")
        async def crash_route():
            raise ValueError("Something went wrong")
        
        test_client = TestClient(app)
        
        # Mock error service response
        mock_response = Mock()
        mock_response.summary = "An unexpected error occurred"
        mock_response.title = "Internal Server Error"
        mock_response.category = "system_error"
        mock_response.severity = "high"
        mock_response.next_steps = ["Try again later", "Contact admin if problem persists"]
        mock_response.contact_admin = True
        mock_response.retry_after = None
        mock_response.help_url = None
        mock_response.provider_health = None
        mock_response.technical_details = None
        mock_error_service.analyze_error.return_value = mock_response
        
        response = test_client.get(
            "/api/test/crash",
            headers={"Authorization": "Bearer valid_token"}
        )
        
        assert response.status_code == 500
        data = response.json()
        assert data["error"]["title"] == "Internal Server Error"
        assert data["error"]["contact_admin"] is True
    
    def test_request_state_population(self, client, mock_token_manager, mock_cookie_manager):
        """Test that request state is properly populated with user data."""
        with patch("ai_karen_engine.middleware.session_persistence.AuthConfig"):
            # Mock valid token
            mock_token_manager.validate_access_token.return_value = {
                "sub": "user123",
                "email": "test@example.com",
                "roles": ["admin", "user"],
                "tenant_id": "tenant456",
                "is_verified": True
            }
            
            response = client.get(
                "/api/test/protected",
                headers={"Authorization": "Bearer valid_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify user data is properly set
            assert data["user_id"] == "user123"
            assert data["user_data"]["email"] == "test@example.com"
            assert data["user_data"]["roles"] == ["admin", "user"]
            assert data["user_data"]["tenant_id"] == "tenant456"


class TestMiddlewareIntegration:
    """Test middleware integration scenarios."""
    
    def test_middleware_order_with_other_middleware(self):
        """Test that session persistence middleware works correctly with other middleware."""
        app = FastAPI()
        
        # Add multiple middleware in order
        app.add_middleware(SessionPersistenceMiddleware, enable_intelligent_errors=True)
        
        # Add a simple middleware that adds a header
        @app.middleware("http")
        async def add_header_middleware(request: Request, call_next):
            response = await call_next(request)
            response.headers["X-Custom-Header"] = "test"
            return response
        
        @app.get("/api/test/public")
        async def public_route():
            return {"message": "public"}
        
        client = TestClient(app)
        response = client.get("/api/test/public")
        
        assert response.status_code == 200
        assert response.headers["X-Custom-Header"] == "test"
    
    def test_cookie_updates_merged_correctly(self, mock_token_manager, mock_cookie_manager):
        """Test that cookie updates from token refresh are properly merged into response."""
        with patch("ai_karen_engine.middleware.session_persistence.AuthConfig"):
            app = FastAPI()
            app.add_middleware(SessionPersistenceMiddleware, enable_intelligent_errors=True)
            
            @app.get("/api/test/protected")
            async def protected_route():
                return {"message": "success"}
            
            client = TestClient(app)
            
            # Mock expired access token that gets refreshed
            mock_token_manager.validate_access_token.side_effect = TokenExpiredError("Token expired")
            mock_cookie_manager.get_refresh_token.return_value = "refresh_token"
            mock_token_manager.validate_refresh_token.return_value = {
                "sub": "user123",
                "email": "test@example.com",
                "tenant_id": "default"
            }
            
            new_expires_at = datetime.now(timezone.utc) + timedelta(days=7)
            mock_token_manager.rotate_tokens.return_value = (
                "new_access_token",
                "new_refresh_token",
                new_expires_at
            )
            
            response = client.get(
                "/api/test/protected",
                headers={"Authorization": "Bearer expired_token"}
            )
            
            assert response.status_code == 200
            assert "X-New-Access-Token" in response.headers
            assert response.headers["X-New-Access-Token"] == "new_access_token"


if __name__ == "__main__":
    pytest.main([__file__])