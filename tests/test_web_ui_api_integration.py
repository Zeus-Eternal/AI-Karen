"""
Integration tests for Web UI API compatibility endpoints.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch

try:
    from fastapi.testclient import TestClient
    from fastapi import FastAPI
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    TestClient = None
    FastAPI = None

from ai_karen_engine.api_routes.web_api_compatibility import router
from src.ai_karen_engine.models.shared_types import FlowOutput, AiData


# Create a test FastAPI app with just the Web UI API router
if FASTAPI_AVAILABLE:
    test_app = FastAPI()
    test_app.include_router(router)
else:
    test_app = None


@pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI not available")
class TestWebUIAPIIntegration:
    """Test the web UI API compatibility endpoints."""
    
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
            ai_data=AiData(
                keywords=["greeting"],
                confidence=0.95
            ),
            suggested_new_facts=["User initiated conversation"],
            proactive_suggestion="Would you like to know about my capabilities?"
        )
        return mock
    
    @pytest.fixture
    def mock_memory_service(self):
        """Mock memory service."""
        mock = AsyncMock()
        mock.query_memories.return_value = []
        mock.store_web_ui_memory.return_value = "mem-123"
        return mock
    
    @pytest.fixture
    def mock_plugin_service(self):
        """Mock plugin service."""
        mock = AsyncMock()
        mock.list_plugins.return_value = [
            {
                "name": "test-plugin",
                "description": "Test plugin",
                "category": "test",
                "enabled": True,
                "version": "1.0.0"
            }
        ]
        mock.execute_plugin.return_value = {"result": "success"}
        return mock
    
    def test_health_check_endpoint(self, client):
        """Test the health check endpoint."""
        response = client.get("/api/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "services" in data
        assert "timestamp" in data
        assert "uptime" in data
    
    @patch('src.ai_karen_engine.api_routes.web_api_compatibility.get_ai_orchestrator_service')
    def test_chat_process_endpoint(self, mock_get_orchestrator, client, mock_ai_orchestrator):
        """Test the chat process endpoint."""
        mock_get_orchestrator.return_value = mock_ai_orchestrator
        
        request_data = {
            "message": "Hello, how are you?",
            "conversation_history": [],
            "relevant_memories": [],
            "user_settings": {
                "memory_depth": "medium",
                "personality_tone": "friendly"
            },
            "user_id": "test-user",
            "session_id": "test-session"
        }
        
        response = client.post("/api/chat/process", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "finalResponse" in data
        assert data["finalResponse"] == "Hello! How can I help you today?"
        assert "suggested_new_facts" in data
        assert "proactive_suggestion" in data
    
    def test_chat_process_validation_error(self, client):
        """Test chat process endpoint with validation error."""
        request_data = {
            "message": "",  # Empty message should cause validation error
            "conversation_history": [],
            "relevant_memories": [],
            "user_settings": {}
        }
        
        response = client.post("/api/chat/process", json=request_data)
        assert response.status_code == 400
        
        data = response.json()
        assert "error" in data
        assert "type" in data
        assert data["type"] == "VALIDATION_ERROR"
    
    @patch('src.ai_karen_engine.api_routes.web_api_compatibility.get_memory_service')
    def test_memory_query_endpoint(self, mock_get_memory, client, mock_memory_service):
        """Test the memory query endpoint."""
        mock_get_memory.return_value = mock_memory_service
        
        request_data = {
            "text": "coffee preferences",
            "user_id": "test-user",
            "session_id": "test-session",
            "top_k": 5,
            "similarity_threshold": 0.7
        }
        
        response = client.post("/api/memory/query", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "memories" in data
        assert "total_count" in data
        assert "query_time_ms" in data
        assert isinstance(data["memories"], list)
    
    @patch('src.ai_karen_engine.api_routes.web_api_compatibility.get_memory_service')
    def test_memory_store_endpoint(self, mock_get_memory, client, mock_memory_service):
        """Test the memory store endpoint."""
        mock_get_memory.return_value = mock_memory_service
        
        request_data = {
            "content": "User likes coffee",
            "metadata": {"type": "preference"},
            "tags": ["coffee", "preference"],
            "user_id": "test-user",
            "session_id": "test-session"
        }
        
        response = client.post("/api/memory/store", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "success" in data
        assert "memory_id" in data
        assert "message" in data
        assert data["success"] is True
    
    @patch('src.ai_karen_engine.api_routes.web_api_compatibility.get_plugin_service')
    def test_list_plugins_endpoint(self, mock_get_plugin, client, mock_plugin_service):
        """Test the list plugins endpoint."""
        mock_get_plugin.return_value = mock_plugin_service
        
        response = client.get("/api/plugins")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        if len(data) > 0:
            plugin = data[0]
            assert "name" in plugin
            assert "description" in plugin
            assert "category" in plugin
            assert "enabled" in plugin
    
    @patch('src.ai_karen_engine.api_routes.web_api_compatibility.get_plugin_service')
    def test_execute_plugin_endpoint(self, mock_get_plugin, client, mock_plugin_service):
        """Test the execute plugin endpoint."""
        mock_get_plugin.return_value = mock_plugin_service
        
        request_data = {
            "plugin_name": "test-plugin",
            "parameters": {"param1": "value1"},
            "user_id": "test-user",
            "session_id": "test-session"
        }
        
        response = client.post("/api/plugins/execute", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "success" in data
        assert "result" in data
        assert "execution_time_ms" in data
    
    def test_system_metrics_endpoint(self, client):
        """Test the system metrics endpoint."""
        response = client.get("/api/analytics/system")
        assert response.status_code == 200
        
        data = response.json()
        assert "cpu_usage" in data
        assert "memory_usage" in data
        assert "disk_usage" in data
        assert "active_sessions" in data
        assert "total_requests" in data
        assert "error_rate" in data
    
    def test_usage_analytics_endpoint(self, client):
        """Test the usage analytics endpoint."""
        response = client.get("/api/analytics/usage")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_conversations" in data
        assert "total_messages" in data
        assert "average_session_duration" in data
        assert "most_used_features" in data
        assert "user_activity" in data


if __name__ == "__main__":
    pytest.main([__file__])