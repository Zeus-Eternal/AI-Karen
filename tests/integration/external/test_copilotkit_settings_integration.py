"""
Integration tests for CopilotKit settings API endpoints.

This module tests the CopilotKit settings API endpoints to ensure they work correctly
and are properly separated from LLM provider settings.
"""

import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI

# Import the CopilotKit settings router
from src.ai_karen_engine.api_routes.copilotkit_settings_routes import (
    router as copilotkit_router,
    CopilotKitConfig,
    CopilotKitFeatures,
    CopilotKitAdvanced
)


@pytest.fixture
def test_app():
    """Create a test FastAPI app with CopilotKit settings routes."""
    app = FastAPI()
    app.include_router(copilotkit_router)
    return app


@pytest.fixture
def client(test_app):
    """Create a test client."""
    return TestClient(test_app)


class TestCopilotKitSettingsAPI:
    """Test CopilotKit settings API endpoints."""
    
    def test_get_copilotkit_settings(self, client):
        """Test getting CopilotKit settings."""
        response = client.get("/api/copilot/settings")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify default configuration structure
        assert "enabled" in data
        assert "api_base_url" in data
        assert "timeout" in data
        assert "features" in data
        assert "advanced" in data
        
        # Verify features structure
        features = data["features"]
        assert "code_suggestions" in features
        assert "ui_assistance" in features
        assert "development_tools" in features
        assert "memory_integration" in features
        
        # Verify advanced settings structure
        advanced = data["advanced"]
        assert "max_suggestions" in advanced
        assert "suggestion_delay" in advanced
        assert "auto_complete" in advanced
        assert "context_awareness" in advanced
    
    def test_update_copilotkit_settings(self, client):
        """Test updating CopilotKit settings."""
        new_config = {
            "enabled": False,
            "api_base_url": "http://test.example.com/api/copilot",
            "timeout": 60,
            "features": {
                "code_suggestions": False,
                "ui_assistance": True,
                "development_tools": True,
                "memory_integration": True
            },
            "advanced": {
                "max_suggestions": 10,
                "suggestion_delay": 1000,
                "auto_complete": False,
                "context_awareness": False
            }
        }
        
        response = client.post("/api/copilot/settings", json=new_config)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify the settings were updated
        assert data["enabled"] == False
        assert data["api_base_url"] == "http://test.example.com/api/copilot"
        assert data["timeout"] == 60
        assert data["features"]["code_suggestions"] == False
        assert data["features"]["memory_integration"] == True
        assert data["advanced"]["max_suggestions"] == 10
        assert data["advanced"]["auto_complete"] == False
    
    def test_get_copilotkit_status(self, client):
        """Test getting CopilotKit status."""
        response = client.get("/api/copilot/status")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify status structure
        assert "status" in data
        assert "message" in data
        assert "last_check" in data
        
        # Status should be one of the expected values
        assert data["status"] in ["healthy", "unhealthy", "unknown"]
    
    def test_test_copilotkit_connection(self, client):
        """Test CopilotKit connection testing."""
        test_request = {
            "api_base_url": "http://localhost:8000/api/copilot",
            "timeout": 30
        }
        
        response = client.post("/api/copilot/test", json=test_request)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify connection test response structure
        assert "success" in data
        assert "message" in data
        assert isinstance(data["success"], bool)
        assert isinstance(data["message"], str)
    
    def test_get_copilotkit_features(self, client):
        """Test getting CopilotKit features."""
        response = client.get("/api/copilot/features")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify features structure
        expected_features = ["code_suggestions", "ui_assistance", "development_tools", "memory_integration"]
        for feature in expected_features:
            assert feature in data
            assert isinstance(data[feature], bool)
    
    def test_update_copilotkit_features(self, client):
        """Test updating CopilotKit features."""
        new_features = {
            "code_suggestions": False,
            "ui_assistance": True,
            "development_tools": False,
            "memory_integration": True
        }
        
        response = client.post("/api/copilot/features", json=new_features)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify features were updated
        assert data["code_suggestions"] == False
        assert data["ui_assistance"] == True
        assert data["development_tools"] == False
        assert data["memory_integration"] == True
    
    def test_toggle_copilotkit_feature(self, client):
        """Test toggling individual CopilotKit features."""
        # Test enabling a feature
        response = client.post("/api/copilot/features/code_suggestions/toggle?enabled=true")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["feature"] == "code_suggestions"
        assert data["enabled"] == True
        assert "message" in data
        
        # Test disabling a feature
        response = client.post("/api/copilot/features/ui_assistance/toggle?enabled=false")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["feature"] == "ui_assistance"
        assert data["enabled"] == False
    
    def test_toggle_invalid_feature(self, client):
        """Test toggling an invalid feature returns 404."""
        response = client.post("/api/copilot/features/invalid_feature/toggle?enabled=true")
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()
    
    def test_get_copilotkit_info(self, client):
        """Test getting CopilotKit information."""
        response = client.get("/api/copilot/info")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify info structure
        assert data["name"] == "CopilotKit"
        assert data["category"] == "UI_FRAMEWORK"
        assert data["is_llm_provider"] == False
        assert data["provider_type"] == "ui_framework"
        
        # Verify capabilities
        assert "capabilities" in data
        expected_capabilities = ["ui_assistance", "code_suggestions", "development_tools", "memory_integration"]
        for capability in expected_capabilities:
            assert capability in data["capabilities"]
        
        # Verify documentation links
        assert "documentation_url" in data
        assert "github_url" in data
        
        # Verify configuration summary
        assert "configuration" in data
        config = data["configuration"]
        assert "enabled" in config
        assert "features_enabled" in config
        assert "total_features" in config


class TestCopilotKitSettingsValidation:
    """Test CopilotKit settings validation."""
    
    def test_invalid_timeout_value(self, client):
        """Test that invalid timeout values are rejected."""
        invalid_config = {
            "enabled": True,
            "api_base_url": "http://localhost:8000/api/copilot",
            "timeout": 500,  # Too high (max is 300)
            "features": {
                "code_suggestions": True,
                "ui_assistance": True,
                "development_tools": True,
                "memory_integration": False
            },
            "advanced": {
                "max_suggestions": 5,
                "suggestion_delay": 500,
                "auto_complete": True,
                "context_awareness": True
            }
        }
        
        response = client.post("/api/copilot/settings", json=invalid_config)
        
        # Should return validation error
        assert response.status_code == 422
    
    def test_invalid_max_suggestions_value(self, client):
        """Test that invalid max_suggestions values are rejected."""
        invalid_config = {
            "enabled": True,
            "api_base_url": "http://localhost:8000/api/copilot",
            "timeout": 30,
            "features": {
                "code_suggestions": True,
                "ui_assistance": True,
                "development_tools": True,
                "memory_integration": False
            },
            "advanced": {
                "max_suggestions": 25,  # Too high (max is 20)
                "suggestion_delay": 500,
                "auto_complete": True,
                "context_awareness": True
            }
        }
        
        response = client.post("/api/copilot/settings", json=invalid_config)
        
        # Should return validation error
        assert response.status_code == 422


if __name__ == "__main__":
    pytest.main([__file__])