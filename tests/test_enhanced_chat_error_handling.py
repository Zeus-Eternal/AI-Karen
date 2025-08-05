"""
Tests for enhanced chat processing error handling.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

try:
    from fastapi.testclient import TestClient
    from fastapi import FastAPI
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    TestClient = None
    FastAPI = None

from ai_karen_engine.api_routes.web_api_compatibility import router
from src.ai_karen_engine.models.web_ui_types import WebUIErrorCode
from src.ai_karen_engine.models.shared_types import FlowOutput, AiData


# Create a test FastAPI app with just the Web UI API router
if FASTAPI_AVAILABLE:
    test_app = FastAPI()
    test_app.include_router(router, prefix="/api")
else:
    test_app = None


@pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI not available")
class TestEnhancedChatErrorHandling:
    """Test enhanced error handling for chat processing endpoint."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        if not FASTAPI_AVAILABLE:
            pytest.skip("FastAPI not available")
        return TestClient(test_app)
    
    @pytest.fixture
    def mock_ai_orchestrator(self):
        """Mock AI orchestrator service."""
        mock = AsyncMock()
        mock.conversation_processing_flow.return_value = FlowOutput(
            response="Hello! How can I help you today?",
            ai_data=AiData(keywords=["greeting"], confidence=0.95)
        )
        return mock
    
    def test_empty_message_validation(self, client):
        """Test validation error for empty message."""
        request_data = {
            "message": "",
            "conversation_history": [],
            "relevant_memories": [],
            "user_settings": {}
        }
        
        response = client.post("/api/chat/process", json=request_data)
        assert response.status_code == 400
        
        data = response.json()
        assert data["type"] == "VALIDATION_ERROR"
        assert "validation_errors" in data["details"]
        assert any("message" in error["field"] for error in data["details"]["validation_errors"])
    
    def test_whitespace_only_message_validation(self, client):
        """Test validation error for whitespace-only message."""
        request_data = {
            "message": "   \n\t   ",
            "conversation_history": [],
            "relevant_memories": [],
            "user_settings": {}
        }
        
        response = client.post("/api/chat/process", json=request_data)
        assert response.status_code == 400
        
        data = response.json()
        assert data["type"] == "VALIDATION_ERROR"
        assert "validation_errors" in data["details"]
    
    def test_message_too_long_validation(self, client):
        """Test validation error for message that's too long."""
        request_data = {
            "message": "x" * 10001,  # Exceeds 10,000 character limit
            "conversation_history": [],
            "relevant_memories": [],
            "user_settings": {}
        }
        
        response = client.post("/api/chat/process", json=request_data)
        assert response.status_code == 400
        
        data = response.json()
        assert data["type"] == "VALIDATION_ERROR"
        assert "validation_errors" in data["details"]
        assert any("too long" in error["message"] for error in data["details"]["validation_errors"])
    
    def test_invalid_conversation_history_format(self, client):
        """Test validation error for invalid conversation history format."""
        request_data = {
            "message": "Hello",
            "conversation_history": [
                "invalid_string_instead_of_object",
                {"role": "user"}  # Missing content field
            ],
            "relevant_memories": [],
            "user_settings": {}
        }
        
        response = client.post("/api/chat/process", json=request_data)
        assert response.status_code == 400
        
        data = response.json()
        assert data["type"] == "VALIDATION_ERROR"
        assert "validation_errors" in data["details"]
        validation_errors = data["details"]["validation_errors"]
        
        # Check for both validation errors
        assert any("conversation_history[0]" in error["field"] for error in validation_errors)
        assert any("conversation_history[1]" in error["field"] for error in validation_errors)
    
    def test_invalid_user_settings_format(self, client):
        """Test validation error for invalid user settings format."""
        request_data = {
            "message": "Hello",
            "conversation_history": [],
            "relevant_memories": [],
            "user_settings": "invalid_string_instead_of_object"
        }
        
        response = client.post("/api/chat/process", json=request_data)
        assert response.status_code == 400
        
        data = response.json()
        assert data["type"] == "VALIDATION_ERROR"
        assert "validation_errors" in data["details"]
        assert any("user_settings" in error["field"] for error in data["details"]["validation_errors"])
    
    @patch('src.ai_karen_engine.api_routes.web_api_compatibility.get_ai_orchestrator_service')
    def test_timeout_error_handling(self, mock_get_orchestrator, client):
        """Test timeout error handling with retries."""
        mock_orchestrator = AsyncMock()
        mock_orchestrator.conversation_processing_flow.side_effect = asyncio.TimeoutError()
        mock_get_orchestrator.return_value = mock_orchestrator
        
        request_data = {
            "message": "Hello",
            "conversation_history": [],
            "relevant_memories": [],
            "user_settings": {}
        }
        
        response = client.post("/api/chat/process", json=request_data)
        assert response.status_code == 504
        
        data = response.json()
        assert data["type"] == "SERVICE_UNAVAILABLE"
        assert "timeout" in data["message"].lower()
        assert "retry_count" in data["details"]
    
    @patch('src.ai_karen_engine.api_routes.web_api_compatibility.get_ai_orchestrator_service')
    def test_connection_error_handling(self, mock_get_orchestrator, client):
        """Test connection error handling with retries."""
        mock_orchestrator = AsyncMock()
        mock_orchestrator.conversation_processing_flow.side_effect = ConnectionError("Connection failed")
        mock_get_orchestrator.return_value = mock_orchestrator
        
        request_data = {
            "message": "Hello",
            "conversation_history": [],
            "relevant_memories": [],
            "user_settings": {}
        }
        
        response = client.post("/api/chat/process", json=request_data)
        assert response.status_code == 503
        
        data = response.json()
        assert data["type"] == "SERVICE_UNAVAILABLE"
        assert "connection_error" in data["details"]
        assert "retry_count" in data["details"]
    
    @patch('src.ai_karen_engine.api_routes.web_api_compatibility.get_ai_orchestrator_service')
    def test_rate_limit_error_handling(self, mock_get_orchestrator, client):
        """Test rate limit error handling."""
        mock_orchestrator = AsyncMock()
        mock_orchestrator.conversation_processing_flow.side_effect = Exception("Rate limit exceeded")
        mock_get_orchestrator.return_value = mock_orchestrator
        
        request_data = {
            "message": "Hello",
            "conversation_history": [],
            "relevant_memories": [],
            "user_settings": {}
        }
        
        response = client.post("/api/chat/process", json=request_data)
        assert response.status_code == 429
        
        data = response.json()
        assert data["type"] == "SERVICE_UNAVAILABLE"
        assert "rate limit" in data["message"].lower()
    
    @patch('src.ai_karen_engine.api_routes.web_api_compatibility.get_ai_orchestrator_service')
    def test_authentication_error_handling(self, mock_get_orchestrator, client):
        """Test authentication error handling."""
        mock_orchestrator = AsyncMock()
        mock_orchestrator.conversation_processing_flow.side_effect = Exception("Authentication failed")
        mock_get_orchestrator.return_value = mock_orchestrator
        
        request_data = {
            "message": "Hello",
            "conversation_history": [],
            "relevant_memories": [],
            "user_settings": {}
        }
        
        response = client.post("/api/chat/process", json=request_data)
        assert response.status_code == 401
        
        data = response.json()
        assert data["type"] == "AUTHENTICATION_ERROR"
        assert "authentication" in data["message"].lower()
    
    @patch('src.ai_karen_engine.api_routes.web_api_compatibility.get_ai_orchestrator_service')
    @patch('src.ai_karen_engine.services.web_api_compatibility.WebUITransformationService.transform_chat_request_to_backend')
    def test_transformation_error_handling(self, mock_transform, mock_get_orchestrator, client):
        """Test request transformation error handling."""
        mock_transform.side_effect = ValueError("Invalid request format")
        mock_get_orchestrator.return_value = AsyncMock()
        
        request_data = {
            "message": "Hello",
            "conversation_history": [],
            "relevant_memories": [],
            "user_settings": {}
        }
        
        response = client.post("/api/chat/process", json=request_data)
        assert response.status_code == 400
        
        data = response.json()
        assert data["type"] == "VALIDATION_ERROR"
        assert "transformation_error" in data["details"]
    
    @patch('src.ai_karen_engine.api_routes.web_api_compatibility.get_ai_orchestrator_service')
    @patch('src.ai_karen_engine.services.web_api_compatibility.WebUITransformationService.transform_backend_response_to_chat')
    def test_response_transformation_fallback(self, mock_transform_response, mock_get_orchestrator, client):
        """Test response transformation error with fallback."""
        mock_orchestrator = AsyncMock()
        mock_orchestrator.conversation_processing_flow.return_value = FlowOutput(
            response="Hello! How can I help you today?",
            ai_data=AiData(keywords=["greeting"], confidence=0.95)
        )
        mock_get_orchestrator.return_value = mock_orchestrator
        
        # Make response transformation fail
        mock_transform_response.side_effect = Exception("Response transformation failed")
        
        request_data = {
            "message": "Hello",
            "conversation_history": [],
            "relevant_memories": [],
            "user_settings": {}
        }
        
        response = client.post("/api/chat/process", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "finalResponse" in data
        assert "trouble formatting" in data["finalResponse"]
    
    @patch('src.ai_karen_engine.api_routes.web_api_compatibility.get_ai_orchestrator_service')
    def test_empty_response_fallback(self, mock_get_orchestrator, client):
        """Test fallback for empty AI response."""
        mock_orchestrator = AsyncMock()
        mock_orchestrator.conversation_processing_flow.return_value = FlowOutput(
            response="",  # Empty response
            ai_data=None
        )
        mock_get_orchestrator.return_value = mock_orchestrator
        
        request_data = {
            "message": "Hello",
            "conversation_history": [],
            "relevant_memories": [],
            "user_settings": {}
        }
        
        response = client.post("/api/chat/process", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "finalResponse" in data
        assert "couldn't generate a proper response" in data["finalResponse"]
    
    @patch('src.ai_karen_engine.api_routes.web_api_compatibility.get_ai_orchestrator_service')
    def test_successful_retry_after_failure(self, mock_get_orchestrator, client):
        """Test successful processing after initial failure."""
        mock_orchestrator = AsyncMock()
        
        # First call fails, second succeeds
        mock_orchestrator.conversation_processing_flow.side_effect = [
            ConnectionError("Connection failed"),
            FlowOutput(
                response="Hello! How can I help you today?",
                ai_data=AiData(keywords=["greeting"], confidence=0.95)
            )
        ]
        mock_get_orchestrator.return_value = mock_orchestrator
        
        request_data = {
            "message": "Hello",
            "conversation_history": [],
            "relevant_memories": [],
            "user_settings": {}
        }
        
        response = client.post("/api/chat/process", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "finalResponse" in data
        assert data["finalResponse"] == "Hello! How can I help you today?"
    
    def test_request_id_in_error_responses(self, client):
        """Test that request ID is included in error responses."""
        request_data = {
            "message": "",  # This will cause validation error
            "conversation_history": [],
            "relevant_memories": [],
            "user_settings": {}
        }
        
        response = client.post("/api/chat/process", json=request_data)
        assert response.status_code == 400
        
        data = response.json()
        assert "request_id" in data
        assert data["request_id"] is not None
    
    def test_user_friendly_error_messages(self, client):
        """Test that error responses contain user-friendly messages."""
        request_data = {
            "message": "",
            "conversation_history": [],
            "relevant_memories": [],
            "user_settings": {}
        }
        
        response = client.post("/api/chat/process", json=request_data)
        assert response.status_code == 400
        
        data = response.json()
        assert "error" in data
        assert "Please check your request format" in data["error"]


if __name__ == "__main__":
    pytest.main([__file__])