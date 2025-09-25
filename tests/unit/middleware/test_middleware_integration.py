"""
Integration Tests for Session Persistence and Error Handler Middleware

Tests the integration between session persistence middleware and intelligent
error handler middleware, ensuring they work together correctly.
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, AsyncMock, patch
from fastapi import FastAPI, Request, HTTPException
from fastapi.testclient import TestClient

from ai_karen_engine.middleware.session_persistence import SessionPersistenceMiddleware
from ai_karen_engine.middleware.intelligent_error_handler import IntelligentErrorHandlerMiddleware
from ai_karen_engine.auth.exceptions import TokenExpiredError, InvalidTokenError


@pytest.fixture
def integrated_app():
    """Create test FastAPI app with both middleware integrated."""
    app = FastAPI()
    
    # Add middleware in correct order (error handler first, then session persistence)
    app.add_middleware(
        IntelligentErrorHandlerMiddleware,
        enable_intelligent_responses=True,
        debug_mode=False
    )
    app.add_middleware(
        SessionPersistenceMiddleware,
        enable_intelligent_errors=True
    )
    
    # Add test routes
    @app.get("/api/test/protected")
    async def protected_route(request: Request):
        user_id = getattr(request.state, "user", None)
        return {"message": "success", "user_id": user_id}
    
    @app.get("/api/test/protected_error")
    async def protected_error_route(request: Request):
        # This route requires auth but then throws an error
        raise ValueError("Protected route error")
    
    @app.get("/api/test/public")
    async def public_route():
        return {"message": "public"}
    
    @app.get("/api/auth/login")
    async def auth_route():
        return {"message": "auth route"}
    
    return app


@pytest.fixture
def client(integrated_app):
    """Create test client."""
    return TestClient(integrated_app)


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
def mock_error_service():
    """Mock error response service."""
    with patch("ai_karen_engine.middleware.session_persistence.ErrorResponseService") as session_mock, \
         patch("ai_karen_engine.middleware.intelligent_error_handler.ErrorResponseService") as error_mock:
        
        # Create a single mock instance that both middleware will use
        instance = Mock()
        session_mock.return_value = instance
        error_mock.return_value = instance
        yield instance


class TestMiddlewareIntegration:
    """Test integration between session persistence and error handler middleware."""
    
    def test_public_routes_bypass_both_middleware(self, client):
        """Test that public routes bypass both authentication and error handling."""
        response = client.get("/api/test/public")
        assert response.status_code == 200
        assert response.json() == {"message": "public"}
    
    def test_auth_routes_bypass_session_persistence_only(self, client):
        """Test that auth routes bypass session persistence but still get error handling."""
        response = client.get("/api/auth/login")
        assert response.status_code == 200
        assert response.json() == {"message": "auth route"}
    
    @patch("ai_karen_engine.middleware.session_persistence.AuthConfig")
    def test_successful_authentication_flow(
        self,
        mock_auth_config,
        client,
        mock_token_manager,
        mock_cookie_manager
    ):
        """Test successful authentication flow through both middleware."""
        # Mock valid token
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
        assert data["message"] == "success"
    
    def test_authentication_error_with_intelligent_response(
        self,
        client,
        mock_error_service
    ):
        """Test that authentication errors get intelligent error responses."""
        # Mock error service response for missing auth header
        mock_response = Mock()
        mock_response.summary = "You need to log in to access this resource"
        mock_response.title = "Authentication Required"
        mock_response.category = "authentication"
        mock_response.severity = "medium"
        mock_response.next_steps = ["Click the login button", "Check your session"]
        mock_response.contact_admin = False
        mock_response.retry_after = None
        mock_response.help_url = None
        mock_response.provider_health = None
        mock_response.technical_details = None
        mock_error_service.analyze_error.return_value = mock_response
        
        response = client.get("/api/test/protected")
        assert response.status_code == 401
        
        data = response.json()
        assert data["detail"] == "You need to log in to access this resource"
        assert data["error"]["title"] == "Authentication Required"
        assert data["error"]["category"] == "authentication"
        assert data["error"]["next_steps"] == ["Click the login button", "Check your session"]
    
    @patch("ai_karen_engine.middleware.session_persistence.AuthConfig")
    def test_token_refresh_with_error_handling(
        self,
        mock_auth_config,
        client,
        mock_token_manager,
        mock_cookie_manager,
        mock_error_service
    ):
        """Test token refresh flow with error handling integration."""
        # Mock expired access token
        mock_token_manager.validate_access_token.side_effect = TokenExpiredError("Token expired")
        
        # Mock successful refresh
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
        data = response.json()
        assert data["user_id"] == "user123"
        
        # Verify new access token is provided
        assert "X-New-Access-Token" in response.headers
        assert response.headers["X-New-Access-Token"] == "new_access_token"
    
    @patch("ai_karen_engine.middleware.session_persistence.AuthConfig")
    def test_failed_token_refresh_with_intelligent_error(
        self,
        mock_auth_config,
        client,
        mock_token_manager,
        mock_cookie_manager,
        mock_error_service
    ):
        """Test failed token refresh with intelligent error response."""
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
        mock_response.next_steps = [
            "Click the login button to sign in again",
            "Your work will be saved automatically"
        ]
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
        assert "Your session has expired" in data["detail"]
        
        # Verify expired refresh token cookie was cleared
        mock_cookie_manager.clear_refresh_token_cookie.assert_called_once()
    
    @patch("ai_karen_engine.middleware.session_persistence.AuthConfig")
    def test_authenticated_route_error_with_intelligent_response(
        self,
        mock_auth_config,
        client,
        mock_token_manager,
        mock_cookie_manager,
        mock_error_service
    ):
        """Test that errors in authenticated routes get intelligent responses."""
        # Mock valid token
        mock_token_manager.validate_access_token.return_value = {
            "sub": "user123",
            "email": "test@example.com",
            "roles": ["user"],
            "tenant_id": "default",
            "is_verified": True
        }
        
        # Mock error service response for the ValueError
        mock_response = Mock()
        mock_response.summary = "An unexpected error occurred while processing your request"
        mock_response.title = "Internal Server Error"
        mock_response.category = "system_error"
        mock_response.severity = "high"
        mock_response.next_steps = [
            "Try refreshing the page",
            "Contact admin if the problem persists"
        ]
        mock_response.contact_admin = True
        mock_response.retry_after = None
        mock_response.help_url = None
        mock_response.provider_health = None
        mock_response.technical_details = "ValueError: Protected route error"
        mock_error_service.analyze_error.return_value = mock_response
        
        response = client.get(
            "/api/test/protected_error",
            headers={"Authorization": "Bearer valid_token"}
        )
        
        assert response.status_code == 500
        data = response.json()
        assert data["error"]["title"] == "Internal Server Error"
        assert data["error"]["contact_admin"] is True
        assert "unexpected error occurred" in data["detail"]
    
    def test_middleware_order_matters(self):
        """Test that middleware order affects behavior correctly."""
        # Create app with wrong middleware order (session persistence first)
        wrong_order_app = FastAPI()
        wrong_order_app.add_middleware(SessionPersistenceMiddleware, enable_intelligent_errors=True)
        wrong_order_app.add_middleware(IntelligentErrorHandlerMiddleware, enable_intelligent_responses=True)
        
        @wrong_order_app.get("/api/test/protected")
        async def protected_route():
            return {"message": "success"}
        
        client = TestClient(wrong_order_app)
        
        # Without auth header, session persistence middleware should handle the error
        # But since error handler is added after, it won't catch session persistence errors
        response = client.get("/api/test/protected")
        assert response.status_code == 401
        
        # The response should still be intelligent since session persistence has intelligent errors enabled
        data = response.json()
        assert "error" in data  # Should have intelligent error structure
    
    def test_error_service_shared_between_middleware(self, client, mock_error_service):
        """Test that both middleware can use the same error service instance."""
        # Mock error service to track calls
        call_count = 0
        original_analyze = mock_error_service.analyze_error
        
        def track_calls(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            mock_response = Mock()
            mock_response.summary = f"Error {call_count}"
            mock_response.title = f"Error {call_count}"
            mock_response.category = "system_error"
            mock_response.severity = "medium"
            mock_response.next_steps = ["Try again"]
            mock_response.contact_admin = False
            mock_response.retry_after = None
            mock_response.help_url = None
            mock_response.provider_health = None
            mock_response.technical_details = None
            return mock_response
        
        mock_error_service.analyze_error.side_effect = track_calls
        
        # Make request that triggers session persistence error
        response = client.get("/api/test/protected")
        assert response.status_code == 401
        assert call_count == 1
        
        # Both middleware should be able to use the error service
        data = response.json()
        assert "Error 1" in data["detail"]
    
    def test_request_metadata_preserved_across_middleware(
        self,
        client,
        mock_error_service
    ):
        """Test that request metadata is preserved and passed correctly through both middleware."""
        mock_response = Mock()
        mock_response.summary = "Authentication required"
        mock_response.title = "Auth Required"
        mock_response.category = "authentication"
        mock_response.severity = "medium"
        mock_response.next_steps = ["Log in"]
        mock_response.contact_admin = False
        mock_response.retry_after = None
        mock_response.help_url = None
        mock_response.provider_health = None
        mock_response.technical_details = None
        mock_error_service.analyze_error.return_value = mock_response
        
        response = client.get(
            "/api/test/protected",
            headers={
                "User-Agent": "test-client/1.0",
                "X-Forwarded-For": "192.168.1.100"
            }
        )
        
        assert response.status_code == 401
        
        # Verify error service was called with correct metadata
        mock_error_service.analyze_error.assert_called_once()
        call_args = mock_error_service.analyze_error.call_args
        additional_context = call_args[1]["additional_context"]
        
        assert additional_context["path"] == "/api/test/protected"
        assert additional_context["method"] == "GET"
        assert additional_context["user_agent"] == "test-client/1.0"
        assert additional_context["ip_address"] == "192.168.1.100"


class TestMiddlewareConfiguration:
    """Test different middleware configuration scenarios."""
    
    def test_session_persistence_with_intelligent_errors_disabled(self):
        """Test session persistence middleware with intelligent errors disabled."""
        app = FastAPI()
        app.add_middleware(IntelligentErrorHandlerMiddleware, enable_intelligent_responses=True)
        app.add_middleware(SessionPersistenceMiddleware, enable_intelligent_errors=False)
        
        @app.get("/api/test/protected")
        async def protected_route():
            return {"message": "success"}
        
        client = TestClient(app)
        response = client.get("/api/test/protected")
        
        assert response.status_code == 401
        # Should get simple error from session persistence, but error handler should enhance it
        data = response.json()
        # The exact structure depends on how the middleware interact, but it should be handled
        assert "detail" in data
    
    def test_error_handler_with_intelligent_responses_disabled(self):
        """Test error handler middleware with intelligent responses disabled."""
        app = FastAPI()
        app.add_middleware(IntelligentErrorHandlerMiddleware, enable_intelligent_responses=False)
        app.add_middleware(SessionPersistenceMiddleware, enable_intelligent_errors=True)
        
        @app.get("/api/test/protected")
        async def protected_route():
            return {"message": "success"}
        
        client = TestClient(app)
        response = client.get("/api/test/protected")
        
        assert response.status_code == 401
        # Should get intelligent error from session persistence since error handler is disabled
        data = response.json()
        assert "error" in data  # Should have intelligent error structure from session persistence
    
    def test_both_middleware_with_intelligent_responses_disabled(self):
        """Test both middleware with intelligent responses disabled."""
        app = FastAPI()
        app.add_middleware(IntelligentErrorHandlerMiddleware, enable_intelligent_responses=False)
        app.add_middleware(SessionPersistenceMiddleware, enable_intelligent_errors=False)
        
        @app.get("/api/test/protected")
        async def protected_route():
            return {"message": "success"}
        
        client = TestClient(app)
        response = client.get("/api/test/protected")
        
        assert response.status_code == 401
        # Should get simple error response
        data = response.json()
        assert data == {"detail": "Missing or invalid authorization header"}


if __name__ == "__main__":
    pytest.main([__file__])