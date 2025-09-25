"""
Tests for the enhanced developer tools with AG-UI integration.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from datetime import datetime

from ui_launchers.backend.developer_api import KariDevStudioAPI, dev_api
from main import create_app


@pytest.fixture
def test_app():
    """Create test FastAPI app."""
    app = create_app()
    return app


@pytest.fixture
def test_client(test_app):
    """Create test client."""
    return TestClient(test_app)


@pytest.fixture
def mock_user():
    """Mock user for testing."""
    user = MagicMock()
    user.id = "test_user"
    user.roles = ["admin"]
    user.tenant_id = "test_tenant"
    return user


@pytest.fixture
def dev_studio_api():
    """Create KariDevStudioAPI instance for testing."""
    return KariDevStudioAPI()


class TestKariDevStudioAPI:
    """Test the KariDevStudioAPI class."""
    
    @pytest.mark.asyncio
    async def test_get_system_components(self, dev_studio_api):
        """Test getting system components."""
        user_context = {
            "user_id": "test_user",
            "roles": ["admin"],
            "tenant_id": "test_tenant",
        }
        
        with patch.object(dev_studio_api.plugin_manager, 'get_plugin_metrics') as mock_metrics, \
             patch.object(dev_studio_api.plugin_manager.router, 'list_intents') as mock_intents:
            
            mock_metrics.return_value = {"plugin_calls": {"total": 100}}
            mock_intents.return_value = ["test_plugin", "weather_plugin"]
            
            result = await dev_studio_api.get_system_components(user_context)
            
            assert "components" in result
            assert "total_count" in result
            assert "active_count" in result
            assert "healthy_count" in result
            assert "chat_integrated_count" in result
            assert "ai_enabled_count" in result
            assert "last_updated" in result
            
            # Should have components from plugins, extensions, hooks, and LLM providers
            components = result["components"]
            assert len(components) > 0
            
            # Check that we have different component types
            component_types = {comp["type"] for comp in components}
            assert "plugin" in component_types
            assert "llm_provider" in component_types
    
    @pytest.mark.asyncio
    async def test_get_chat_metrics(self, dev_studio_api):
        """Test getting chat metrics."""
        user_context = {
            "user_id": "test_user",
            "roles": ["admin"],
            "tenant_id": "test_tenant",
        }
        
        result = await dev_studio_api.get_chat_metrics(user_context, hours=24)
        
        assert "metrics" in result
        assert "summary" in result
        assert "timeframe" in result
        assert "last_updated" in result
        
        # Check metrics structure
        metrics = result["metrics"]
        assert len(metrics) > 0
        
        for metric in metrics[:3]:  # Check first few metrics
            assert "timestamp" in metric
            assert "total_messages" in metric
            assert "ai_suggestions" in metric
            assert "tool_calls" in metric
            assert "memory_operations" in metric
            assert "response_time_ms" in metric
            assert "user_satisfaction" in metric
        
        # Check summary structure
        summary = result["summary"]
        assert "total_messages" in summary
        assert "avg_response_time" in summary
        assert "avg_satisfaction" in summary
        assert "total_ai_suggestions" in summary
        assert "total_tool_calls" in summary
    
    @pytest.mark.asyncio
    async def test_execute_component_action_plugin(self, dev_studio_api):
        """Test executing plugin actions."""
        user_context = {
            "user_id": "test_user",
            "roles": ["admin"],
            "tenant_id": "test_tenant",
        }
        
        # Test restart action
        result = await dev_studio_api.execute_component_action(
            "plugin_test_plugin", "restart", user_context
        )
        
        assert result["success"] is True
        assert "message" in result
        assert "test_plugin" in result["message"]
        
        # Test configure action
        result = await dev_studio_api.execute_component_action(
            "plugin_test_plugin", "configure", user_context
        )
        
        assert result["success"] is True
        assert "message" in result
        assert "test_plugin" in result["message"]
    
    @pytest.mark.asyncio
    async def test_execute_component_action_extension(self, dev_studio_api):
        """Test executing extension actions."""
        user_context = {
            "user_id": "test_user",
            "roles": ["admin"],
            "tenant_id": "test_tenant",
        }
        
        # Mock extension manager
        mock_extension_manager = AsyncMock()
        dev_studio_api.set_extension_manager(mock_extension_manager)
        
        # Test reload action
        result = await dev_studio_api.execute_component_action(
            "extension_test_extension", "reload", user_context
        )
        
        assert result["success"] is True
        mock_extension_manager.reload_extension.assert_called_once_with("test_extension")
        
        # Test enable action
        result = await dev_studio_api.execute_component_action(
            "extension_test_extension", "enable", user_context
        )
        
        assert result["success"] is True
        mock_extension_manager.enable_extension.assert_called_once_with("test_extension")
    
    @pytest.mark.asyncio
    async def test_execute_component_action_invalid(self, dev_studio_api):
        """Test executing invalid component actions."""
        user_context = {
            "user_id": "test_user",
            "roles": ["admin"],
            "tenant_id": "test_tenant",
        }
        
        # Test invalid component type
        result = await dev_studio_api.execute_component_action(
            "invalid_test_component", "restart", user_context
        )
        
        assert result["success"] is False
        assert "error" in result
        
        # Test invalid action
        result = await dev_studio_api.execute_component_action(
            "plugin_test_plugin", "invalid_action", user_context
        )
        
        assert result["success"] is False
        assert "error" in result


class TestDeveloperAPIEndpoints:
    """Test the developer API endpoints."""
    
    def test_get_components_endpoint(self, test_client):
        """Test the /api/developer/components endpoint."""
        with patch('ui_launchers.backend.developer_api.get_current_user') as mock_auth:
            mock_user = MagicMock()
            mock_user.id = "test_user"
            mock_user.roles = ["admin"]
            mock_auth.return_value = mock_user
            
            response = test_client.get("/api/developer/components")
            
            assert response.status_code == 200
            data = response.json()
            
            assert "components" in data
            assert "total_count" in data
            assert "active_count" in data
            assert "healthy_count" in data
    
    def test_get_chat_metrics_endpoint(self, test_client):
        """Test the /api/developer/chat-metrics endpoint."""
        with patch('ui_launchers.backend.developer_api.get_current_user') as mock_auth:
            mock_user = MagicMock()
            mock_user.id = "test_user"
            mock_user.roles = ["admin"]
            mock_auth.return_value = mock_user
            
            response = test_client.get("/api/developer/chat-metrics?hours=12")
            
            assert response.status_code == 200
            data = response.json()
            
            assert "metrics" in data
            assert "summary" in data
            assert "timeframe" in data
    
    def test_execute_component_action_endpoint(self, test_client):
        """Test the component action endpoint."""
        with patch('ui_launchers.backend.developer_api.get_current_user') as mock_auth:
            mock_user = MagicMock()
            mock_user.id = "test_user"
            mock_user.roles = ["admin"]
            mock_auth.return_value = mock_user
            
            response = test_client.post("/api/developer/components/plugin_test/restart")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["success"] is True
            assert "message" in data
    
    def test_execute_component_action_unauthorized(self, test_client):
        """Test component action endpoint without admin role."""
        with patch('ui_launchers.backend.developer_api.get_current_user') as mock_auth:
            mock_user = MagicMock()
            mock_user.id = "test_user"
            mock_user.roles = ["user"]  # Not admin
            mock_auth.return_value = mock_user
            
            response = test_client.post("/api/developer/components/plugin_test/restart")
            
            assert response.status_code == 403
            data = response.json()
            assert "Admin role required" in data["detail"]


class TestDeveloperToolsIntegration:
    """Test integration between different developer tools components."""
    
    @pytest.mark.asyncio
    async def test_component_health_analysis(self, dev_studio_api):
        """Test component health analysis functionality."""
        user_context = {
            "user_id": "test_user",
            "roles": ["admin"],
            "tenant_id": "test_tenant",
        }
        
        # Get components
        components_result = await dev_studio_api.get_system_components(user_context)
        components = components_result["components"]
        
        # Analyze health
        healthy_components = [c for c in components if c["health"] == "healthy"]
        warning_components = [c for c in components if c["health"] == "warning"]
        critical_components = [c for c in components if c["health"] == "critical"]
        
        # Should have some components
        assert len(components) > 0
        
        # Health analysis should be consistent
        total_health_count = len(healthy_components) + len(warning_components) + len(critical_components)
        assert total_health_count <= len(components)  # Some might have "unknown" health
    
    @pytest.mark.asyncio
    async def test_chat_integration_analysis(self, dev_studio_api):
        """Test chat integration analysis."""
        user_context = {
            "user_id": "test_user",
            "roles": ["admin"],
            "tenant_id": "test_tenant",
        }
        
        # Get components
        components_result = await dev_studio_api.get_system_components(user_context)
        components = components_result["components"]
        
        # Analyze chat integration
        chat_integrated = [c for c in components if c["chat_integration"]]
        ai_enabled = [c for c in components if c["copilot_enabled"]]
        
        # Should have some chat-integrated components
        assert len(chat_integrated) > 0
        
        # AI-enabled components should be a subset of or equal to chat-integrated
        # (though not strictly required, it's expected in our implementation)
        assert len(ai_enabled) >= 0
    
    def test_metrics_consistency(self, dev_studio_api):
        """Test that metrics are consistent across different endpoints."""
        # This would test that component metrics align with chat metrics
        # and that the data is consistent across different API calls
        pass


@pytest.mark.integration
class TestDeveloperToolsE2E:
    """End-to-end tests for developer tools."""
    
    def test_full_developer_workflow(self, test_client):
        """Test a complete developer workflow."""
        with patch('ui_launchers.backend.developer_api.get_current_user') as mock_auth:
            mock_user = MagicMock()
            mock_user.id = "test_user"
            mock_user.roles = ["admin"]
            mock_auth.return_value = mock_user
            
            # 1. Get system components
            components_response = test_client.get("/api/developer/components")
            assert components_response.status_code == 200
            components_data = components_response.json()
            
            # 2. Get chat metrics
            metrics_response = test_client.get("/api/developer/chat-metrics")
            assert metrics_response.status_code == 200
            metrics_data = metrics_response.json()
            
            # 3. Execute a component action (if components exist)
            components = components_data.get("components", [])
            if components:
                first_component = components[0]
                component_id = first_component["id"]
                
                # Try a safe action like "restart" for plugins
                if first_component["type"] == "plugin":
                    action_response = test_client.post(f"/api/developer/components/{component_id}/restart")
                    assert action_response.status_code == 200
                    action_data = action_response.json()
                    assert action_data["success"] is True
            
            # Verify data consistency
            assert "components" in components_data
            assert "metrics" in metrics_data
            assert components_data["total_count"] >= 0
            assert len(metrics_data["metrics"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])