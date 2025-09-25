"""
Tests for Response Core API Integration

This module tests the integration of ResponseOrchestrator with existing API endpoints,
ensuring backward compatibility and proper error handling.
"""

import json
import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import FastAPI

from ai_karen_engine.api_routes.response_core_routes import router as response_core_router
from ai_karen_engine.services.auth_utils import get_current_user
from ai_karen_engine.middleware.response_core_integration import (
    ResponseCoreCompatibilityLayer,
    get_compatibility_layer,
    configure_response_core_integration
)


@pytest.fixture
def app():
    """Create test FastAPI app"""
    app = FastAPI()
    
    # Override the auth dependency for testing
    def mock_get_current_user():
        return {
            "id": "test_user_123",
            "user_id": "test_user_123",
            "tenant_id": "test_tenant",
            "is_admin": True
        }
    
    # Override dependencies
    app.dependency_overrides[get_current_user] = mock_get_current_user
    
    app.include_router(response_core_router)
    return app


@pytest.fixture
def client(app):
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def mock_user():
    """Mock authenticated user"""
    return {
        "id": "test_user_123",
        "user_id": "test_user_123",
        "tenant_id": "test_tenant",
        "is_admin": True
    }


@pytest.fixture
def mock_response_orchestrator():
    """Mock ResponseOrchestrator"""
    mock = Mock()
    mock.respond.return_value = "Test response from Response Core"
    mock.diagnostics.return_value = {"status": "healthy"}
    return mock


@pytest.fixture
def mock_chat_orchestrator():
    """Mock ChatOrchestrator"""
    mock = Mock()
    mock_response = Mock()
    mock_response.response = "Test response from Chat Orchestrator"
    mock_response.correlation_id = "test_correlation_123"
    mock_response.processing_time = 0.5
    mock_response.used_fallback = False
    mock_response.context_used = True
    mock_response.metadata = {"test": "metadata"}
    mock.process_message = AsyncMock(return_value=mock_response)
    return mock


class TestResponseCoreRoutes:
    """Test Response Core API routes"""
    
    @patch('ai_karen_engine.api_routes.response_core_routes.get_response_orchestrator')
    def test_chat_with_response_core_success(self, mock_get_orchestrator, client, mock_user, mock_response_orchestrator):
        """Test successful chat with Response Core"""
        mock_get_user.return_value = mock_user
        mock_get_orchestrator.return_value = mock_response_orchestrator
        
        request_data = {
            "message": "Hello, how are you?",
            "user_id": "test_user_123",
            "conversation_id": "test_conv_123",
            "ui_caps": {"copilotkit": True},
            "stream": False
        }
        
        response = client.post("/api/response-core/chat", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "Test response from Response Core"
        assert data["intent"] == "general_assist"
        assert data["persona"] == "assistant"
        assert "correlation_id" in data
        assert "processing_time" in data
        
        # Verify orchestrator was called correctly
        mock_response_orchestrator.respond.assert_called_once()
    
    @patch('ai_karen_engine.api_routes.response_core_routes.get_current_user')
    @patch('ai_karen_engine.api_routes.response_core_routes.get_response_orchestrator')
    def test_chat_with_response_core_error(self, mock_get_orchestrator, mock_get_user, client, mock_user):
        """Test error handling in Response Core chat"""
        mock_get_user.return_value = mock_user
        mock_get_orchestrator.side_effect = Exception("Orchestrator error")
        
        request_data = {
            "message": "Hello, how are you?",
            "user_id": "test_user_123"
        }
        
        response = client.post("/api/response-core/chat", json=request_data)
        
        assert response.status_code == 200  # Should return 200 with error content
        data = response.json()
        assert "error" in data["content"]
        assert data["intent"] == "error"
        assert data["used_fallback"] is True
    
    @patch('ai_karen_engine.api_routes.response_core_routes.get_current_user')
    @patch('ai_karen_engine.api_routes.response_core_routes.get_response_orchestrator')
    @patch('ai_karen_engine.api_routes.response_core_routes.get_chat_orchestrator')
    def test_chat_compatible_success_response_core(self, mock_get_chat, mock_get_response, mock_get_user, client, mock_user, mock_response_orchestrator):
        """Test compatible endpoint with successful Response Core"""
        mock_get_user.return_value = mock_user
        mock_get_response.return_value = mock_response_orchestrator
        
        request_data = {
            "message": "Hello, how are you?",
            "user_id": "test_user_123"
        }
        
        response = client.post("/api/response-core/chat/compatible", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["response"] == "Test response from Response Core"
        assert data["metadata"]["orchestrator"] == "response_core"
        assert data["used_fallback"] is False
    
    @patch('ai_karen_engine.api_routes.response_core_routes.get_current_user')
    @patch('ai_karen_engine.api_routes.response_core_routes.get_response_orchestrator')
    @patch('ai_karen_engine.api_routes.response_core_routes.get_chat_orchestrator')
    def test_chat_compatible_fallback_to_chat_orchestrator(self, mock_get_chat, mock_get_response, mock_get_user, client, mock_user, mock_chat_orchestrator):
        """Test compatible endpoint fallback to ChatOrchestrator"""
        mock_get_user.return_value = mock_user
        mock_get_response.side_effect = Exception("Response Core failed")
        mock_get_chat.return_value = mock_chat_orchestrator
        
        request_data = {
            "message": "Hello, how are you?",
            "user_id": "test_user_123"
        }
        
        response = client.post("/api/response-core/chat/compatible", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["response"] == "Test response from Chat Orchestrator"
        assert data["metadata"]["orchestrator"] == "chat_orchestrator"
        assert data["used_fallback"] is True
        assert "fallback_reason" in data["metadata"]
    
    @patch('ai_karen_engine.api_routes.response_core_routes.get_current_user')
    def test_manage_models_list(self, mock_get_user, client, mock_user):
        """Test model management list operation"""
        mock_get_user.return_value = mock_user
        
        request_data = {
            "operation": "list"
        }
        
        response = client.post("/api/response-core/models", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "system_models" in data["data"]
        assert "huggingface_models" in data["data"]
    
    @patch('ai_karen_engine.api_routes.response_core_routes.get_current_user')
    def test_manage_models_unauthorized(self, mock_get_user, client):
        """Test model management with non-admin user"""
        mock_get_user.return_value = {"id": "user", "is_admin": False}
        
        request_data = {
            "operation": "list"
        }
        
        response = client.post("/api/response-core/models", json=request_data)
        
        assert response.status_code == 403
    
    @patch('ai_karen_engine.api_routes.response_core_routes.get_current_user')
    def test_manage_training_start(self, mock_get_user, client, mock_user):
        """Test training management start operation"""
        mock_get_user.return_value = mock_user
        
        request_data = {
            "operation": "start",
            "model_id": "test_model",
            "config": {"learning_rate": 0.001}
        }
        
        response = client.post("/api/response-core/training", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["status"] == "started"
        assert "job_id" in data
    
    @patch('ai_karen_engine.api_routes.response_core_routes.get_current_user')
    @patch('ai_karen_engine.api_routes.response_core_routes.get_global_orchestrator')
    def test_health_check_success(self, mock_get_orchestrator, mock_get_user, client, mock_response_orchestrator):
        """Test health check endpoint"""
        mock_get_orchestrator.return_value = mock_response_orchestrator
        
        response = client.get("/api/response-core/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["response_core"] == "available"
        assert "diagnostics" in data
    
    @patch('ai_karen_engine.api_routes.response_core_routes.get_current_user')
    def test_get_config(self, mock_get_user, client, mock_user):
        """Test configuration retrieval"""
        mock_get_user.return_value = mock_user
        
        response = client.get("/api/response-core/config")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "config" in data
        assert data["config"]["local_only"] is True
    
    @patch('ai_karen_engine.api_routes.response_core_routes.get_current_user')
    def test_update_config(self, mock_get_user, client, mock_user):
        """Test configuration update"""
        mock_get_user.return_value = mock_user
        
        config_updates = {
            "local_only": False,
            "enable_copilotkit": True
        }
        
        response = client.post("/api/response-core/config", json=config_updates)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["updates"] == config_updates


class TestResponseCoreCompatibilityLayer:
    """Test Response Core compatibility layer"""
    
    def test_compatibility_layer_creation(self):
        """Test compatibility layer creation"""
        layer = ResponseCoreCompatibilityLayer(
            enable_response_core=True,
            fallback_enabled=True
        )
        
        assert layer.enable_response_core is True
        assert layer.fallback_enabled is True
    
    @pytest.mark.asyncio
    @patch('ai_karen_engine.middleware.response_core_integration.get_global_orchestrator')
    async def test_process_chat_request_response_core(self, mock_get_orchestrator, mock_response_orchestrator):
        """Test chat processing with Response Core"""
        mock_get_orchestrator.return_value = mock_response_orchestrator
        
        layer = ResponseCoreCompatibilityLayer(enable_response_core=True)
        
        result = await layer.process_chat_request(
            message="Hello",
            user_id="test_user",
            conversation_id="test_conv",
            use_response_core=True
        )
        
        assert result["success"] is True
        assert result["orchestrator"] == "response_core"
        assert result["local_processing"] is True
        assert "processing_time" in result
    
    @pytest.mark.asyncio
    @patch('ai_karen_engine.middleware.response_core_integration.MemoryProcessor')
    @patch('ai_karen_engine.middleware.response_core_integration.ChatOrchestrator')
    async def test_process_chat_request_chat_orchestrator(self, mock_chat_class, mock_memory_class, mock_chat_orchestrator):
        """Test chat processing with ChatOrchestrator"""
        mock_chat_class.return_value = mock_chat_orchestrator
        
        layer = ResponseCoreCompatibilityLayer(enable_response_core=False)
        
        result = await layer.process_chat_request(
            message="Hello",
            user_id="test_user",
            conversation_id="test_conv",
            use_response_core=False
        )
        
        assert result["success"] is True
        assert result["orchestrator"] == "chat_orchestrator"
        assert result["local_processing"] is False
    
    @pytest.mark.asyncio
    @patch('ai_karen_engine.middleware.response_core_integration.get_global_orchestrator')
    @patch('ai_karen_engine.middleware.response_core_integration.MemoryProcessor')
    @patch('ai_karen_engine.middleware.response_core_integration.ChatOrchestrator')
    async def test_process_chat_request_fallback(self, mock_get_orchestrator, mock_memory_class, mock_chat_class, mock_chat_orchestrator):
        """Test fallback from Response Core to ChatOrchestrator"""
        mock_get_orchestrator.side_effect = Exception("Response Core failed")
        mock_chat_class.return_value = mock_chat_orchestrator
        
        layer = ResponseCoreCompatibilityLayer(
            enable_response_core=True,
            fallback_enabled=True
        )
        
        result = await layer.process_chat_request(
            message="Hello",
            user_id="test_user",
            conversation_id="test_conv",
            use_response_core=True
        )
        
        assert result["success"] is True
        assert result["orchestrator"] == "chat_orchestrator"
        assert result["used_fallback"] is True
        assert "fallback_reason" in result
    
    def test_should_prefer_response_core(self):
        """Test Response Core preference logic"""
        layer = ResponseCoreCompatibilityLayer()
        
        # Test local_only preference
        assert layer._should_prefer_response_core("Hello", local_only=True) is True
        
        # Test keyword-based preference
        assert layer._should_prefer_response_core("Please analyze this code") is True
        assert layer._should_prefer_response_core("Can you explain this?") is True
        assert layer._should_prefer_response_core("Help me with this") is True
        
        # Test persona-related preference
        assert layer._should_prefer_response_core("Change persona to optimizer") is True
        
        # Test default behavior
        assert layer._should_prefer_response_core("Just a regular message") is False
    
    def test_global_compatibility_layer(self):
        """Test global compatibility layer functions"""
        # Test getting default layer
        layer1 = get_compatibility_layer()
        layer2 = get_compatibility_layer()
        assert layer1 is layer2  # Should be same instance
        
        # Test configuring new layer
        layer3 = configure_response_core_integration(
            enable_response_core=False,
            fallback_enabled=False
        )
        assert layer3.enable_response_core is False
        assert layer3.fallback_enabled is False
        
        # Should be new global instance
        layer4 = get_compatibility_layer()
        assert layer3 is layer4


class TestStreamingIntegration:
    """Test streaming integration with Response Core"""
    
    @patch('ai_karen_engine.api_routes.response_core_routes.get_current_user')
    @patch('ai_karen_engine.api_routes.response_core_routes.get_response_orchestrator')
    def test_chat_stream_response_core(self, mock_get_orchestrator, mock_get_user, client, mock_user, mock_response_orchestrator):
        """Test streaming with Response Core"""
        mock_get_user.return_value = mock_user
        mock_get_orchestrator.return_value = mock_response_orchestrator
        
        request_data = {
            "message": "Hello, how are you?",
            "user_id": "test_user_123"
        }
        
        response = client.post("/api/response-core/chat/stream", json=request_data)
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
        
        # Check that response contains streaming data
        content = response.content.decode()
        assert "data:" in content
        assert "type" in content


class TestErrorHandling:
    """Test error handling and edge cases"""
    
    @patch('ai_karen_engine.api_routes.response_core_routes.get_current_user')
    def test_invalid_model_operation(self, mock_get_user, client, mock_user):
        """Test invalid model management operation"""
        mock_get_user.return_value = mock_user
        
        request_data = {
            "operation": "invalid_operation"
        }
        
        response = client.post("/api/response-core/models", json=request_data)
        
        assert response.status_code == 400
    
    @patch('ai_karen_engine.api_routes.response_core_routes.get_current_user')
    def test_invalid_training_operation(self, mock_get_user, client, mock_user):
        """Test invalid training operation"""
        mock_get_user.return_value = mock_user
        
        request_data = {
            "operation": "invalid_operation"
        }
        
        response = client.post("/api/response-core/training", json=request_data)
        
        assert response.status_code == 400
    
    @patch('ai_karen_engine.api_routes.response_core_routes.get_current_user')
    def test_missing_model_id_for_training(self, mock_get_user, client, mock_user):
        """Test training start without model ID"""
        mock_get_user.return_value = mock_user
        
        request_data = {
            "operation": "start"
            # Missing model_id
        }
        
        response = client.post("/api/response-core/training", json=request_data)
        
        assert response.status_code == 400


if __name__ == "__main__":
    pytest.main([__file__])