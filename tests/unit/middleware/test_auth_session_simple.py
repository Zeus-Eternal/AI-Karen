"""
Simple integration tests for enhanced authentication routes.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient

from ai_karen_engine.api_routes.auth_session_routes import router
from ai_karen_engine.auth.models import UserData, SessionData
from datetime import datetime, timezone, timedelta


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


def test_health_check(client):
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


def test_login_missing_credentials(client):
    """Test login without credentials."""
    
    response = client.post("/auth/login", json={})
    
    # Should get validation error for missing required fields
    assert response.status_code == 422


def test_refresh_token_missing(client):
    """Test refresh token when no refresh token cookie is present."""
    
    with patch('ai_karen_engine.api_routes.auth_session_routes.get_cookie_manager_instance') as mock_cookie_manager:
        
        cookie_manager_mock = MagicMock()
        cookie_manager_mock.get_refresh_token.return_value = None
        mock_cookie_manager.return_value = cookie_manager_mock
        
        response = client.post("/auth/refresh")
        
        assert response.status_code == 401
        assert "Refresh token not found" in response.json()["detail"]


def test_get_current_user_missing_token(client):
    """Test getting current user without access token."""
    
    response = client.get("/auth/me")
    
    assert response.status_code == 401
    assert "Missing or invalid authorization header" in response.json()["detail"]


if __name__ == "__main__":
    pytest.main([__file__])