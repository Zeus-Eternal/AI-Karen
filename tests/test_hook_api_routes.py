"""
Tests for hook management API routes.

This module tests the FastAPI endpoints for hook management,
including registration, unregistration, triggering, and monitoring.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

try:
    from fastapi.testclient import TestClient
    from fastapi import FastAPI
except ImportError:
    # Mock for testing environments without FastAPI
    class TestClient:
        def __init__(self, app): pass
        def get(self, *args, **kwargs): return MagicMock()
        def post(self, *args, **kwargs): return MagicMock()
        def delete(self, *args, **kwargs): return MagicMock()
        def put(self, *args, **kwargs): return MagicMock()
    
    class FastAPI:
        def __init__(self): pass

from ai_karen_engine.api_routes.hook_routes import router
from ai_karen_engine.hooks import HookTypes, HookRegistration, HookExecutionSummary, HookResult


class TestHookAPIRoutes:
    """Test hook management API endpoints."""
    
    @pytest.fixture
    def app(self):
        """Create FastAPI app with hook routes."""
        app = FastAPI()
        app.include_router(router, prefix="/api/hooks")
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def mock_hook_manager(self):
        """Create mock hook manager."""
        hook_manager = MagicMock()
        hook_manager.register_hook = AsyncMock()
        hook_manager.unregister_hook = AsyncMock()
        hook_manager.trigger_hooks = AsyncMock()
        hook_manager.get_hook_by_id = MagicMock()
        hook_manager.get_all_hooks = MagicMock()
        hook_manager.get_hooks_by_type = MagicMock()
        hook_manager.get_hooks_by_source = MagicMock()
        hook_manager.get_hook_types = MagicMock()
        hook_manager.get_summary = MagicMock()
        hook_manager.clear_hooks_by_source = AsyncMock()
        hook_manager.enable = MagicMock()
        hook_manager.disable = MagicMock()
        hook_manager.clear_execution_stats = MagicMock()
        return hook_manager
    
    @pytest.fixture
    def sample_hook_registration(self):
        """Create sample hook registration."""
        return HookRegistration(
            id="test_hook_123",
            hook_type=HookTypes.PRE_MESSAGE,
            handler=lambda x: x,
            priority=100,
            conditions={},
            source_type="api",
            source_name="test_source"
        )
    
    def test_register_hook_success(self, client, mock_hook_manager, sample_hook_registration):
        """Test successful hook registration."""
        with patch('ai_karen_engine.api_routes.hook_routes.get_hook_manager', return_value=mock_hook_manager):
            # Setup mock responses
            mock_hook_manager.register_hook.return_value = "test_hook_123"
            mock_hook_manager.get_hook_by_id.return_value = sample_hook_registration
            
            # Make request
            response = client.post("/api/hooks/register", json={
                "hook_type": HookTypes.PRE_MESSAGE,
                "priority": 100,
                "source_type": "api",
                "source_name": "test_source"
            })
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert data["hook_id"] == "test_hook_123"
            assert data["hook_type"] == HookTypes.PRE_MESSAGE
            assert data["source_type"] == "api"
            
            # Verify hook manager was called
            mock_hook_manager.register_hook.assert_called_once()
    
    def test_register_hook_invalid_type_warning(self, client, mock_hook_manager, sample_hook_registration):
        """Test hook registration with non-standard type generates warning."""
        with patch('ai_karen_engine.api_routes.hook_routes.get_hook_manager', return_value=mock_hook_manager):
            mock_hook_manager.register_hook.return_value = "test_hook_123"
            mock_hook_manager.get_hook_by_id.return_value = sample_hook_registration
            
            # Make request with non-standard hook type
            response = client.post("/api/hooks/register", json={
                "hook_type": "custom_hook_type",
                "priority": 100,
                "source_type": "api"
            })
            
            # Should still succeed but log warning
            assert response.status_code == 200
    
    def test_unregister_hook_success(self, client, mock_hook_manager, sample_hook_registration):
        """Test successful hook unregistration."""
        with patch('ai_karen_engine.api_routes.hook_routes.get_hook_manager', return_value=mock_hook_manager):
            # Setup mock responses
            mock_hook_manager.get_hook_by_id.return_value = sample_hook_registration
            mock_hook_manager.unregister_hook.return_value = True
            
            # Make request
            response = client.delete("/api/hooks/unregister/test_hook_123")
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["hook_id"] == "test_hook_123"
            
            # Verify hook manager was called
            mock_hook_manager.unregister_hook.assert_called_once_with("test_hook_123")
    
    def test_unregister_hook_not_found(self, client, mock_hook_manager):
        """Test unregistering non-existent hook."""
        with patch('ai_karen_engine.api_routes.hook_routes.get_hook_manager', return_value=mock_hook_manager):
            # Setup mock to return None (hook not found)
            mock_hook_manager.get_hook_by_id.return_value = None
            
            # Make request
            response = client.delete("/api/hooks/unregister/nonexistent_hook")
            
            # Verify 404 response
            assert response.status_code == 404
    
    def test_trigger_hooks_success(self, client, mock_hook_manager):
        """Test successful hook triggering."""
        with patch('ai_karen_engine.api_routes.hook_routes.get_hook_manager', return_value=mock_hook_manager):
            # Setup mock execution summary
            mock_summary = HookExecutionSummary(
                hook_type=HookTypes.PRE_MESSAGE,
                total_hooks=2,
                successful_hooks=2,
                failed_hooks=0,
                total_execution_time_ms=100.0,
                results=[
                    HookResult.success_result("hook_1", {"result": "success"}, 50.0),
                    HookResult.success_result("hook_2", {"result": "success"}, 50.0)
                ]
            )
            mock_hook_manager.trigger_hooks.return_value = mock_summary
            
            # Make request
            response = client.post("/api/hooks/trigger", json={
                "hook_type": HookTypes.PRE_MESSAGE,
                "data": {"test": "data"},
                "user_context": {"user_id": "test_user"},
                "timeout_seconds": 30.0
            })
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert data["hook_type"] == HookTypes.PRE_MESSAGE
            assert data["total_hooks"] == 2
            assert data["successful_hooks"] == 2
            assert data["failed_hooks"] == 0
            assert len(data["results"]) == 2
    
    def test_list_hooks_all(self, client, mock_hook_manager, sample_hook_registration):
        """Test listing all hooks."""
        with patch('ai_karen_engine.api_routes.hook_routes.get_hook_manager', return_value=mock_hook_manager):
            # Setup mock responses
            mock_hook_manager.get_all_hooks.return_value = [sample_hook_registration]
            mock_hook_manager.get_hook_types.return_value = [HookTypes.PRE_MESSAGE]
            
            # Make request
            response = client.get("/api/hooks/list")
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert data["total_count"] == 1
            assert len(data["hooks"]) == 1
            assert data["hooks"][0]["hook_id"] == "test_hook_123"
            assert HookTypes.PRE_MESSAGE in data["hook_types"]
    
    def test_list_hooks_filtered_by_type(self, client, mock_hook_manager, sample_hook_registration):
        """Test listing hooks filtered by type."""
        with patch('ai_karen_engine.api_routes.hook_routes.get_hook_manager', return_value=mock_hook_manager):
            # Setup mock responses
            mock_hook_manager.get_hooks_by_type.return_value = [sample_hook_registration]
            mock_hook_manager.get_hook_types.return_value = [HookTypes.PRE_MESSAGE]
            
            # Make request with filter
            response = client.get(f"/api/hooks/list?hook_type={HookTypes.PRE_MESSAGE}")
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert data["total_count"] == 1
            
            # Verify correct method was called
            mock_hook_manager.get_hooks_by_type.assert_called_once_with(HookTypes.PRE_MESSAGE)
    
    def test_list_hooks_filtered_by_source(self, client, mock_hook_manager, sample_hook_registration):
        """Test listing hooks filtered by source."""
        with patch('ai_karen_engine.api_routes.hook_routes.get_hook_manager', return_value=mock_hook_manager):
            # Setup mock responses
            mock_hook_manager.get_hooks_by_source.return_value = [sample_hook_registration]
            mock_hook_manager.get_hook_types.return_value = [HookTypes.PRE_MESSAGE]
            
            # Make request with source filter
            response = client.get("/api/hooks/list?source_type=api&source_name=test_source")
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert data["total_count"] == 1
            
            # Verify correct method was called
            mock_hook_manager.get_hooks_by_source.assert_called_once_with("api", "test_source")
    
    def test_get_hook_types(self, client, mock_hook_manager):
        """Test getting available hook types."""
        with patch('ai_karen_engine.api_routes.hook_routes.get_hook_manager', return_value=mock_hook_manager):
            # Setup mock responses
            mock_hook_manager.get_hook_types.return_value = [HookTypes.PRE_MESSAGE, HookTypes.POST_MESSAGE]
            
            # Make request
            response = client.get("/api/hooks/types")
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert "standard_types" in data
            assert "registered_types" in data
            assert "all_types" in data
            assert "lifecycle_hooks" in data
            assert "error_hooks" in data
            
            # Verify standard types are included
            assert HookTypes.PRE_MESSAGE in data["standard_types"]
            assert HookTypes.POST_MESSAGE in data["standard_types"]
    
    def test_get_hook_stats(self, client, mock_hook_manager):
        """Test getting hook system statistics."""
        with patch('ai_karen_engine.api_routes.hook_routes.get_hook_manager', return_value=mock_hook_manager):
            # Setup mock summary
            mock_summary = {
                "enabled": True,
                "total_hooks": 5,
                "hook_types": 3,
                "source_types": ["api", "plugin", "extension"],
                "execution_stats": {"pre_message_success": 10, "post_message_success": 8}
            }
            mock_hook_manager.get_summary.return_value = mock_summary
            
            # Make request
            response = client.get("/api/hooks/stats")
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert data["enabled"] is True
            assert data["total_hooks"] == 5
            assert data["hook_types"] == 3
            assert "api" in data["source_types"]
            assert "pre_message_success" in data["execution_stats"]
    
    def test_get_hook_details(self, client, mock_hook_manager, sample_hook_registration):
        """Test getting detailed hook information."""
        with patch('ai_karen_engine.api_routes.hook_routes.get_hook_manager', return_value=mock_hook_manager):
            # Setup mock response
            mock_hook_manager.get_hook_by_id.return_value = sample_hook_registration
            
            # Make request
            response = client.get("/api/hooks/test_hook_123")
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert data["hook_id"] == "test_hook_123"
            assert data["hook_type"] == HookTypes.PRE_MESSAGE
            assert data["priority"] == 100
            assert data["source_type"] == "api"
            assert "handler_info" in data
    
    def test_get_hook_details_not_found(self, client, mock_hook_manager):
        """Test getting details for non-existent hook."""
        with patch('ai_karen_engine.api_routes.hook_routes.get_hook_manager', return_value=mock_hook_manager):
            # Setup mock to return None
            mock_hook_manager.get_hook_by_id.return_value = None
            
            # Make request
            response = client.get("/api/hooks/nonexistent_hook")
            
            # Verify 404 response
            assert response.status_code == 404
    
    def test_enable_hook(self, client, mock_hook_manager, sample_hook_registration):
        """Test enabling a hook."""
        with patch('ai_karen_engine.api_routes.hook_routes.get_hook_manager', return_value=mock_hook_manager):
            # Setup mock response
            mock_hook_manager.get_hook_by_id.return_value = sample_hook_registration
            
            # Make request
            response = client.put("/api/hooks/test_hook_123/enable")
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["hook_id"] == "test_hook_123"
            
            # Verify hook was enabled
            assert sample_hook_registration.enabled is True
    
    def test_disable_hook(self, client, mock_hook_manager, sample_hook_registration):
        """Test disabling a hook."""
        with patch('ai_karen_engine.api_routes.hook_routes.get_hook_manager', return_value=mock_hook_manager):
            # Setup mock response
            mock_hook_manager.get_hook_by_id.return_value = sample_hook_registration
            
            # Make request
            response = client.put("/api/hooks/test_hook_123/disable")
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["hook_id"] == "test_hook_123"
            
            # Verify hook was disabled
            assert sample_hook_registration.enabled is False
    
    def test_clear_hooks_by_source(self, client, mock_hook_manager):
        """Test clearing hooks by source."""
        with patch('ai_karen_engine.api_routes.hook_routes.get_hook_manager', return_value=mock_hook_manager):
            # Setup mock response
            mock_hook_manager.clear_hooks_by_source.return_value = 3
            
            # Make request
            response = client.delete("/api/hooks/clear/api?source_name=test_source")
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["cleared_count"] == 3
            assert data["source_type"] == "api"
            assert data["source_name"] == "test_source"
            
            # Verify correct method was called
            mock_hook_manager.clear_hooks_by_source.assert_called_once_with("api", "test_source")
    
    def test_enable_hook_system(self, client, mock_hook_manager):
        """Test enabling the hook system."""
        with patch('ai_karen_engine.api_routes.hook_routes.get_hook_manager', return_value=mock_hook_manager):
            # Make request
            response = client.post("/api/hooks/system/enable")
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["enabled"] is True
            
            # Verify hook manager was called
            mock_hook_manager.enable.assert_called_once()
    
    def test_disable_hook_system(self, client, mock_hook_manager):
        """Test disabling the hook system."""
        with patch('ai_karen_engine.api_routes.hook_routes.get_hook_manager', return_value=mock_hook_manager):
            # Make request
            response = client.post("/api/hooks/system/disable")
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["enabled"] is False
            
            # Verify hook manager was called
            mock_hook_manager.disable.assert_called_once()
    
    def test_clear_execution_stats(self, client, mock_hook_manager):
        """Test clearing execution statistics."""
        with patch('ai_karen_engine.api_routes.hook_routes.get_hook_manager', return_value=mock_hook_manager):
            # Make request
            response = client.delete("/api/hooks/system/clear-stats")
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            
            # Verify hook manager was called
            mock_hook_manager.clear_execution_stats.assert_called_once()
    
    def test_hook_system_health_check(self, client, mock_hook_manager):
        """Test hook system health check."""
        with patch('ai_karen_engine.api_routes.hook_routes.get_hook_manager', return_value=mock_hook_manager):
            # Setup mock summary
            mock_summary = {
                "enabled": True,
                "total_hooks": 5,
                "hook_types": 3,
                "source_types": ["api", "plugin"],
                "execution_stats": {"success": 10, "error": 1}
            }
            mock_hook_manager.get_summary.return_value = mock_summary
            
            # Make request
            response = client.get("/api/hooks/health")
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["hook_manager"]["enabled"] is True
            assert data["hook_manager"]["total_hooks"] == 5
            assert "execution_stats" in data
            assert "timestamp" in data
    
    def test_hook_system_health_check_disabled(self, client, mock_hook_manager):
        """Test hook system health check when disabled."""
        with patch('ai_karen_engine.api_routes.hook_routes.get_hook_manager', return_value=mock_hook_manager):
            # Setup mock summary for disabled system
            mock_summary = {
                "enabled": False,
                "total_hooks": 5,
                "hook_types": 3,
                "source_types": ["api", "plugin"],
                "execution_stats": {}
            }
            mock_hook_manager.get_summary.return_value = mock_summary
            
            # Make request
            response = client.get("/api/hooks/health")
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "disabled"
            assert data["hook_manager"]["enabled"] is False
    
    def test_error_handling_in_endpoints(self, client, mock_hook_manager):
        """Test error handling in API endpoints."""
        with patch('ai_karen_engine.api_routes.hook_routes.get_hook_manager', return_value=mock_hook_manager):
            # Setup mock to raise exception
            mock_hook_manager.register_hook.side_effect = Exception("Test error")
            
            # Make request that should fail
            response = client.post("/api/hooks/register", json={
                "hook_type": HookTypes.PRE_MESSAGE,
                "priority": 100,
                "source_type": "api"
            })
            
            # Verify error response
            assert response.status_code == 500
            assert "Failed to register hook" in response.json()["detail"]