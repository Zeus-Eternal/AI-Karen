#!/usr/bin/env python3
# mypy: ignore-errors
"""
Minimal unit tests for the modular Kari server.
Tests app factory, config validation, and basic functionality.
"""

import os
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Test imports
from server.config import Settings
from server.app import create_app
from fastapi.testclient import TestClient


class TestConfig:
    """Test configuration loading and validation"""
    
    def test_settings_creation(self):
        """Test that Settings can be created"""
        settings = Settings()
        assert settings is not None
        assert hasattr(settings, 'environment')
        assert hasattr(settings, 'secret_key')
    
    def test_environment_loading(self):
        """Test environment loading function"""
        # Test that settings can load environment variables
        settings = Settings()
        # Should have a valid environment
        assert settings.environment is not None
    
    def test_required_settings(self):
        """Test that required settings have defaults"""
        settings = Settings()
        assert settings.environment in ['development', 'production', 'testing']
        assert settings.secret_key is not None
        assert len(settings.secret_key) > 0


class TestAppFactory:
    """Test FastAPI app creation"""
    
    def test_create_app(self):
        """Test that create_app returns a FastAPI instance"""
        app = create_app()
        assert app is not None
        assert hasattr(app, 'routes')
        assert hasattr(app, 'title')
        assert app.title == "Kari AI Assistant API"
    
    def test_app_has_routes(self):
        """Test that the app has expected routes"""
        app = create_app()
        route_paths = [route.path for route in app.routes if hasattr(route, 'path')]
        
        # Check for key endpoints
        assert "/health" in route_paths
        assert "/ping" in route_paths
        assert "/api/ping" in route_paths
        assert "/metrics" in route_paths
    
    def test_app_middleware_configured(self):
        """Test that middleware is configured"""
        app = create_app()
        # Should have middleware stack configured
        assert len(app.user_middleware) > 0


class TestHealthEndpoints:
    """Test health and status endpoints"""
    
    def test_ping_endpoint(self, client):
        """Test ping endpoint"""
        response = client.get("/ping")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "timestamp" in data
    
    def test_api_ping_endpoint(self, client):
        """Test API ping endpoint"""
        response = client.get("/api/ping")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "timestamp" in data
    
    def test_health_endpoint(self, client):
        """Test health endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        # Health endpoint should return status info
        data = response.json()
        assert "status" in data


def run_tests():
    """Run the tests"""
    print("Running minimal server tests...")
    
    # Test config
    try:
        test_config = TestConfig()
        test_config.test_settings_creation()
        test_config.test_environment_loading()
        test_config.test_required_settings()
        print("✅ Config tests passed")
    except Exception as e:
        print(f"❌ Config tests failed: {e}")
        return False
    
    # Test app factory
    try:
        test_app = TestAppFactory()
        test_app.test_create_app()
        test_app.test_app_has_routes()
        test_app.test_app_middleware_configured()
        print("✅ App factory tests passed")
    except Exception as e:
        print(f"❌ App factory tests failed: {e}")
        return False
    
    # Test health endpoints
    try:
        test_health = TestHealthEndpoints()
        app = create_app()
        client = TestClient(app)
        test_health.test_ping_endpoint(client)
        test_health.test_api_ping_endpoint(client)
        test_health.test_health_endpoint(client)
        print("✅ Health endpoint tests passed")
    except Exception as e:
        print(f"❌ Health endpoint tests failed: {e}")
        return False
    
    print("🎉 All tests passed!")
    return True


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
