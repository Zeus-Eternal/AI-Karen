"""
Tests for Web UI compatibility layer.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, AsyncMock

from src.ai_karen_engine.models.web_ui_types import (
    ChatProcessRequest,
    ChatProcessResponse,
    WebUIMemoryQuery,
    WebUIMemoryEntry,
    WebUIMemoryQueryResponse,
    WebUIErrorCode,
    create_web_ui_error_response
)
from src.ai_karen_engine.services.web_ui_compatibility import WebUITransformationService
from src.ai_karen_engine.models.shared_types import FlowOutput, AiData


class TestWebUITransformationService:
    """Test the web UI transformation service."""
    
    def test_create_web_ui_error_response(self):
        """Test creating web UI error responses."""
        error_response = create_web_ui_error_response(
            error_code=WebUIErrorCode.VALIDATION_ERROR,
            message="Test error message",
            details={"field": "test_field"},
            user_message="User friendly message"
        )
        
        assert error_response.error == "User friendly message"
        assert error_response.message == "Test error message"
        assert error_response.type == WebUIErrorCode.VALIDATION_ERROR
        assert error_response.details == {"field": "test_field"}
        assert error_response.timestamp is not None
    
    def test_transform_chat_request_to_backend(self):
        """Test transforming chat request from web UI to backend format."""
        web_ui_request = ChatProcessRequest(
            message="Hello, how are you?",
            conversation_history=[
                {"role": "user", "content": "Previous message"}
            ],
            relevant_memories=[
                {"content": "User likes coffee", "similarity_score": 0.8}
            ],
            user_settings={"memory_depth": "medium"},
            user_id="test-user",
            session_id="test-session"
        )
        
        backend_request, flow_input = WebUITransformationService.transform_chat_request_to_backend(web_ui_request)
        
        assert backend_request.prompt == "Hello, how are you?"
        assert backend_request.conversation_history == [{"role": "user", "content": "Previous message"}]
        assert backend_request.user_settings == {"memory_depth": "medium"}
        assert backend_request.session_id == "test-session"
        assert backend_request.include_memories is True
        assert backend_request.include_insights is True
        
        assert flow_input.prompt == "Hello, how are you?"
        assert flow_input.user_id == "test-user"
        assert flow_input.session_id == "test-session"
    
    def test_transform_backend_response_to_chat(self):
        """Test transforming backend response to web UI chat format."""
        ai_data = AiData(
            keywords=["greeting", "conversation"],
            confidence=0.95,
            reasoning="User is greeting the assistant"
        )
        
        backend_response = FlowOutput(
            response="Hello! I'm doing well, thank you for asking.",
            ai_data=ai_data,
            suggested_new_facts=["User is polite"],
            proactive_suggestion="Would you like to know about the weather?"
        )
        
        web_ui_response = WebUITransformationService.transform_backend_response_to_chat(backend_response)
        
        assert web_ui_response.finalResponse == "Hello! I'm doing well, thank you for asking."
        assert web_ui_response.suggested_new_facts == ["User is polite"]
        assert web_ui_response.proactive_suggestion == "Would you like to know about the weather?"
        assert web_ui_response.ai_data_for_final_response is not None
    
    def test_transform_web_ui_memory_query(self):
        """Test transforming web UI memory query to backend format."""
        web_ui_query = WebUIMemoryQuery(
            text="coffee preferences",
            user_id="test-user",
            session_id="test-session",
            tags=["preferences", "food"],
            top_k=10,
            similarity_threshold=0.8
        )
        
        backend_query = WebUITransformationService.transform_web_ui_memory_query(web_ui_query)
        
        assert backend_query.text == "coffee preferences"
        assert backend_query.session_id == "test-session"
        assert backend_query.tags == ["preferences", "food"]
        assert backend_query.top_k == 10
        assert backend_query.similarity_threshold == 0.8
    
    def test_transform_memory_entries_to_web_ui(self):
        """Test transforming backend memory entries to web UI format."""
        # Mock backend memory response
        backend_memories = [
            Mock(
                id="mem-1",
                content="User likes coffee",
                metadata={"type": "preference"},
                timestamp=1234567890.0,
                similarity_score=0.9,
                tags=["coffee", "preference"],
                user_id="test-user",
                session_id="test-session"
            )
        ]
        
        web_ui_response = WebUITransformationService.transform_memory_entries_to_web_ui(
            backend_memories, 
            query_time_ms=150.5
        )
        
        assert len(web_ui_response.memories) == 1
        assert web_ui_response.total_count == 1
        assert web_ui_response.query_time_ms == 150.5
        
        memory = web_ui_response.memories[0]
        assert memory.id == "mem-1"
        assert memory.content == "User likes coffee"
        assert memory.metadata == {"type": "preference"}
        assert memory.timestamp == 1234567890
        assert memory.similarity_score == 0.9
        assert memory.tags == ["coffee", "preference"]
    
    def test_convert_timestamp_to_js_compatible(self):
        """Test timestamp conversion to JavaScript compatible format."""
        dt = datetime(2024, 1, 15, 12, 30, 45)
        js_timestamp = WebUITransformationService.convert_timestamp_to_js_compatible(dt)
        
        assert isinstance(js_timestamp, int)
        assert js_timestamp > 0
    
    def test_convert_js_timestamp_to_datetime(self):
        """Test converting JavaScript timestamp to Python datetime."""
        js_timestamp = 1705320645  # January 15, 2024
        dt = WebUITransformationService.convert_js_timestamp_to_datetime(js_timestamp)
        
        assert isinstance(dt, datetime)
        assert dt.year == 2024
        assert dt.month == 1
        assert dt.day == 15
    
    def test_sanitize_error_response(self):
        """Test error response sanitization."""
        error_details = {
            "error": "Test error",
            "message": "Test message",
            "type": "VALIDATION_ERROR",
            "password": "secret123",  # Should be removed
            "api_key": "key123",      # Should be removed
            "details": {
                "field": "username",
                "invalid_value": "test",
                "secret_data": "hidden"  # Should be removed
            }
        }
        
        sanitized = WebUITransformationService.sanitize_error_response(error_details)
        
        assert "error" in sanitized
        assert "message" in sanitized
        assert "type" in sanitized
        assert "password" not in sanitized
        assert "api_key" not in sanitized
        assert "details" in sanitized
        assert "field" in sanitized["details"]
        assert "invalid_value" in sanitized["details"]
        assert "secret_data" not in sanitized["details"]


if __name__ == "__main__":
    pytest.main([__file__])