"""
Tests for hook middleware integration.

This module tests the hook middleware that integrates with the FastAPI
request/response pipeline to trigger hooks on API events.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

try:
    from fastapi import FastAPI, Request, Response
    from fastapi.testclient import TestClient
    from starlette.responses import JSONResponse
except ImportError:
    # Mock for testing environments without FastAPI
    class FastAPI:
        def __init__(self): pass
        def add_middleware(self, *args, **kwargs): pass
    
    class Request:
        def __init__(self):
            self.method = "GET"
            self.url = MagicMock()
            self.url.path = "/test"
            self.headers = {}
            self.query_params = {}
            self.path_params = {}
            self.client = None
        async def body(self): return b""
    
    class Response:
        def __init__(self):
            self.status_code = 200
            self.headers = {}
    
    class TestClient:
        def __init__(self, app): pass
        def get(self, *args, **kwargs): return MagicMock()
    
    class JSONResponse:
        def __init__(self, content): pass

from ai_karen_engine.api_routes.hook_middleware import HookMiddleware, create_hook_middleware
from ai_karen_engine.hooks import HookTypes, HookExecutionSummary, HookResult


class TestHookMiddleware:
    """Test hook middleware functionality."""
    
    @pytest.fixture
    def mock_hook_manager(self):
        """Create mock hook manager."""
        hook_manager = MagicMock()
        hook_manager.trigger_hooks = AsyncMock()
        hook_manager.get_summary = MagicMock()
        return hook_manager
    
    @pytest.fixture
    def mock_app(self):
        """Create mock FastAPI app."""
        return MagicMock()
    
    @pytest.fixture
    def hook_middleware(self, mock_app):
        """Create hook middleware instance."""
        return HookMiddleware(
            app=mock_app,
            enabled=True,
            hook_timeout=5.0,
            excluded_paths=["/health", "/docs"]
        )
    
    @pytest.fixture
    def mock_request(self):
        """Create mock request."""
        request = MagicMock(spec=Request)
        request.method = "POST"
        request.url.path = "/api/chat"
        request.url = MagicMock()
        request.url.path = "/api/chat"
        request.headers = {
            "content-type": "application/json",
            "user-agent": "test-client",
            "x-user-id": "test_user_123"
        }
        request.query_params = {"conversation_id": "conv_456"}
        request.path_params = {}
        request.client = MagicMock()
        request.client.host = "127.0.0.1"
        request.body = AsyncMock(return_value=b'{"message": "test"}')
        return request
    
    @pytest.fixture
    def mock_response(self):
        """Create mock response."""
        response = MagicMock()
        response.status_code = 200
        response.headers = {"content-type": "application/json"}
        return response
    
    @pytest.fixture
    def mock_hook_summary(self):
        """Create mock hook execution summary."""
        return HookExecutionSummary(
            hook_type=HookTypes.PRE_MESSAGE,
            total_hooks=1,
            successful_hooks=1,
            failed_hooks=0,
            total_execution_time_ms=50.0,
            results=[
                HookResult.success_result("hook_1", {"result": "success"}, 50.0)
            ]
        )
    
    @pytest.mark.asyncio
    async def test_middleware_enabled_processing(self, hook_middleware, mock_request, mock_response, mock_hook_summary):
        """Test middleware processing when enabled."""
        with patch('ai_karen_engine.api_routes.hook_middleware.get_hook_manager') as mock_get_hook_manager:
            mock_hook_manager = AsyncMock()
            mock_hook_manager.trigger_hooks.return_value = mock_hook_summary
            mock_get_hook_manager.return_value = mock_hook_manager
            
            # Mock call_next
            async def mock_call_next(request):
                return mock_response
            
            # Process request through middleware
            response = await hook_middleware.dispatch(mock_request, mock_call_next)
            
            # Verify hooks were triggered
            assert mock_hook_manager.trigger_hooks.call_count >= 1
            
            # Verify response is returned
            assert response == mock_response
    
    @pytest.mark.asyncio
    async def test_middleware_disabled_processing(self, mock_app, mock_request, mock_response):
        """Test middleware processing when disabled."""
        middleware = HookMiddleware(app=mock_app, enabled=False)
        
        # Mock call_next
        async def mock_call_next(request):
            return mock_response
        
        with patch('ai_karen_engine.api_routes.hook_middleware.get_hook_manager') as mock_get_hook_manager:
            mock_hook_manager = AsyncMock()
            mock_get_hook_manager.return_value = mock_hook_manager
            
            # Process request through middleware
            response = await middleware.dispatch(mock_request, mock_call_next)
            
            # Verify no hooks were triggered
            mock_hook_manager.trigger_hooks.assert_not_called()
            
            # Verify response is returned
            assert response == mock_response
    
    @pytest.mark.asyncio
    async def test_excluded_paths_skipped(self, hook_middleware, mock_response):
        """Test that excluded paths are skipped."""
        # Create request for excluded path
        excluded_request = MagicMock(spec=Request)
        excluded_request.url.path = "/health"
        
        # Mock call_next
        async def mock_call_next(request):
            return mock_response
        
        with patch('ai_karen_engine.api_routes.hook_middleware.get_hook_manager') as mock_get_hook_manager:
            mock_hook_manager = AsyncMock()
            mock_get_hook_manager.return_value = mock_hook_manager
            
            # Process request through middleware
            response = await hook_middleware.dispatch(excluded_request, mock_call_next)
            
            # Verify no hooks were triggered
            mock_hook_manager.trigger_hooks.assert_not_called()
            
            # Verify response is returned
            assert response == mock_response
    
    @pytest.mark.asyncio
    async def test_pre_request_hooks_triggered(self, hook_middleware, mock_request, mock_response, mock_hook_summary):
        """Test that pre-request hooks are triggered."""
        with patch('ai_karen_engine.api_routes.hook_middleware.get_hook_manager') as mock_get_hook_manager:
            mock_hook_manager = AsyncMock()
            mock_hook_manager.trigger_hooks.return_value = mock_hook_summary
            mock_get_hook_manager.return_value = mock_hook_manager
            
            # Mock call_next
            async def mock_call_next(request):
                return mock_response
            
            # Process request through middleware
            await hook_middleware.dispatch(mock_request, mock_call_next)
            
            # Verify pre-request hooks were triggered
            assert mock_hook_manager.trigger_hooks.call_count >= 1
            
            # Check first call was for pre-request
            first_call = mock_hook_manager.trigger_hooks.call_args_list[0]
            hook_context = first_call[0][0]
            assert hook_context.data["event_type"] == "pre_request"
            assert hook_context.data["api_endpoint"] == "/api/chat"
            assert hook_context.data["http_method"] == "POST"
    
    @pytest.mark.asyncio
    async def test_post_response_hooks_triggered(self, hook_middleware, mock_request, mock_response, mock_hook_summary):
        """Test that post-response hooks are triggered."""
        with patch('ai_karen_engine.api_routes.hook_middleware.get_hook_manager') as mock_get_hook_manager:
            mock_hook_manager = AsyncMock()
            mock_hook_manager.trigger_hooks.return_value = mock_hook_summary
            mock_get_hook_manager.return_value = mock_hook_manager
            
            # Mock call_next
            async def mock_call_next(request):
                return mock_response
            
            # Process request through middleware
            await hook_middleware.dispatch(mock_request, mock_call_next)
            
            # Verify both pre and post hooks were triggered
            assert mock_hook_manager.trigger_hooks.call_count >= 2
            
            # Check that post-response hooks were called
            calls = mock_hook_manager.trigger_hooks.call_args_list
            post_call_found = False
            for call in calls:
                hook_context = call[0][0]
                if hook_context.data.get("event_type") == "post_response":
                    post_call_found = True
                    assert "response" in hook_context.data
                    assert "processing_time" in hook_context.data["response"]
                    break
            
            assert post_call_found, "Post-response hooks were not triggered"
    
    @pytest.mark.asyncio
    async def test_error_hooks_triggered_on_exception(self, hook_middleware, mock_request, mock_hook_summary):
        """Test that error hooks are triggered when an exception occurs."""
        with patch('ai_karen_engine.api_routes.hook_middleware.get_hook_manager') as mock_get_hook_manager:
            mock_hook_manager = AsyncMock()
            mock_hook_manager.trigger_hooks.return_value = mock_hook_summary
            mock_get_hook_manager.return_value = mock_hook_manager
            
            # Mock call_next to raise exception
            async def mock_call_next(request):
                raise ValueError("Test error")
            
            # Process request through middleware - should re-raise exception
            with pytest.raises(ValueError, match="Test error"):
                await hook_middleware.dispatch(mock_request, mock_call_next)
            
            # Verify error hooks were triggered
            calls = mock_hook_manager.trigger_hooks.call_args_list
            error_call_found = False
            for call in calls:
                hook_context = call[0][0]
                if hook_context.hook_type == HookTypes.SYSTEM_ERROR:
                    error_call_found = True
                    assert hook_context.data["event_type"] == "request_error"
                    assert hook_context.data["error"] == "Test error"
                    break
            
            assert error_call_found, "Error hooks were not triggered"
    
    @pytest.mark.asyncio
    async def test_hook_timeout_handling(self, hook_middleware, mock_request, mock_response):
        """Test that hook timeouts are handled gracefully."""
        with patch('ai_karen_engine.api_routes.hook_middleware.get_hook_manager') as mock_get_hook_manager:
            mock_hook_manager = AsyncMock()
            # Simulate timeout
            mock_hook_manager.trigger_hooks.side_effect = asyncio.TimeoutError("Hook timeout")
            mock_get_hook_manager.return_value = mock_hook_manager
            
            # Mock call_next
            async def mock_call_next(request):
                return mock_response
            
            # Process request through middleware - should not raise exception
            response = await hook_middleware.dispatch(mock_request, mock_call_next)
            
            # Verify response is still returned despite timeout
            assert response == mock_response
    
    def test_determine_hook_type_chat_endpoints(self, hook_middleware):
        """Test hook type determination for chat endpoints."""
        # Test chat endpoint
        hook_type = hook_middleware._determine_hook_type("/api/chat", "pre")
        assert hook_type == HookTypes.PRE_MESSAGE
        
        hook_type = hook_middleware._determine_hook_type("/api/chat", "post")
        assert hook_type == HookTypes.POST_MESSAGE
        
        # Test WebSocket chat endpoint
        hook_type = hook_middleware._determine_hook_type("/api/ws/chat", "pre")
        assert hook_type == HookTypes.PRE_MESSAGE
    
    def test_determine_hook_type_plugin_endpoints(self, hook_middleware):
        """Test hook type determination for plugin endpoints."""
        hook_type = hook_middleware._determine_hook_type("/api/plugins", "pre")
        assert hook_type == HookTypes.PLUGIN_EXECUTION_START
        
        hook_type = hook_middleware._determine_hook_type("/api/plugins", "post")
        assert hook_type == HookTypes.PLUGIN_EXECUTION_END
    
    def test_determine_hook_type_unknown_endpoints(self, hook_middleware):
        """Test hook type determination for unknown endpoints."""
        hook_type = hook_middleware._determine_hook_type("/api/unknown", "pre")
        assert hook_type == "api_request_start"
        
        hook_type = hook_middleware._determine_hook_type("/api/unknown", "post")
        assert hook_type == "api_request_end"
    
    def test_extract_user_context_from_headers(self, hook_middleware):
        """Test user context extraction from request headers."""
        request_info = {
            "headers": {
                "x-user-id": "user_123",
                "x-session-id": "session_456",
                "x-conversation-id": "conv_789",
                "user-agent": "test-client"
            },
            "query_params": {},
            "path_params": {},
            "client_host": "127.0.0.1",
            "request_id": "req_123"
        }
        
        user_context = hook_middleware._extract_user_context(request_info)
        
        assert user_context["user_id"] == "user_123"
        assert user_context["session_id"] == "session_456"
        assert user_context["conversation_id"] == "conv_789"
        assert user_context["user_agent"] == "test-client"
        assert user_context["client_host"] == "127.0.0.1"
        assert user_context["request_id"] == "req_123"
    
    def test_extract_user_context_from_query_params(self, hook_middleware):
        """Test user context extraction from query parameters."""
        request_info = {
            "headers": {},
            "query_params": {
                "user_id": "user_456",
                "session_id": "session_789",
                "conversation_id": "conv_123"
            },
            "path_params": {},
            "client_host": None,
            "user_agent": None,
            "request_id": "req_456"
        }
        
        user_context = hook_middleware._extract_user_context(request_info)
        
        assert user_context["user_id"] == "user_456"
        assert user_context["session_id"] == "session_789"
        assert user_context["conversation_id"] == "conv_123"
    
    def test_extract_user_context_from_path_params(self, hook_middleware):
        """Test user context extraction from path parameters."""
        request_info = {
            "headers": {},
            "query_params": {},
            "path_params": {
                "user_id": "user_789",
                "conversation_id": "conv_456"
            },
            "client_host": None,
            "user_agent": None,
            "request_id": "req_789"
        }
        
        user_context = hook_middleware._extract_user_context(request_info)
        
        assert user_context["user_id"] == "user_789"
        assert user_context["conversation_id"] == "conv_456"
    
    def test_middleware_enable_disable(self, hook_middleware):
        """Test enabling and disabling middleware."""
        # Initially enabled
        assert hook_middleware.is_enabled() is True
        
        # Disable
        hook_middleware.disable()
        assert hook_middleware.is_enabled() is False
        
        # Enable
        hook_middleware.enable()
        assert hook_middleware.is_enabled() is True
    
    def test_excluded_paths_management(self, hook_middleware):
        """Test adding and removing excluded paths."""
        # Add excluded path
        hook_middleware.add_excluded_path("/api/test")
        assert "/api/test" in hook_middleware.excluded_paths
        
        # Remove excluded path
        hook_middleware.remove_excluded_path("/api/test")
        assert "/api/test" not in hook_middleware.excluded_paths
        
        # Try to remove non-existent path (should not raise error)
        hook_middleware.remove_excluded_path("/api/nonexistent")
    
    def test_get_middleware_stats(self, hook_middleware):
        """Test getting middleware statistics."""
        with patch('ai_karen_engine.api_routes.hook_middleware.get_hook_manager') as mock_get_hook_manager:
            mock_hook_manager = MagicMock()
            mock_hook_manager.get_summary.return_value = {
                "enabled": True,
                "total_hooks": 5,
                "hook_types": 3
            }
            mock_get_hook_manager.return_value = mock_hook_manager
            
            stats = hook_middleware.get_stats()
            
            assert stats["enabled"] is True
            assert stats["hook_timeout"] == 5.0
            assert "/health" in stats["excluded_paths"]
            assert "hook_manager_stats" in stats
            assert stats["hook_manager_stats"]["total_hooks"] == 5
    
    def test_create_hook_middleware_function(self, mock_app):
        """Test the create_hook_middleware factory function."""
        middleware = create_hook_middleware(
            app=mock_app,
            enabled=False,
            hook_timeout=10.0,
            excluded_paths=["/custom"]
        )
        
        assert isinstance(middleware, HookMiddleware)
        assert middleware.enabled is False
        assert middleware.hook_timeout == 10.0
        assert "/custom" in middleware.excluded_paths
    
    @pytest.mark.asyncio
    async def test_request_info_extraction_with_body(self, hook_middleware):
        """Test request information extraction including body."""
        mock_request = MagicMock(spec=Request)
        mock_request.method = "POST"
        mock_request.url.path = "/api/chat"
        mock_request.headers = {"content-type": "application/json"}
        mock_request.query_params = {}
        mock_request.path_params = {}
        mock_request.client = MagicMock()
        mock_request.client.host = "127.0.0.1"
        mock_request.body = AsyncMock(return_value=b'{"message": "test"}')
        
        request_info = await hook_middleware._extract_request_info(mock_request, "req_123")
        
        assert request_info["request_id"] == "req_123"
        assert request_info["method"] == "POST"
        assert request_info["path"] == "/api/chat"
        assert request_info["body"] == '{"message": "test"}'
        assert request_info["client_host"] == "127.0.0.1"
        assert "timestamp" in request_info
    
    def test_response_info_extraction(self, hook_middleware, mock_response):
        """Test response information extraction."""
        processing_time = 0.5
        
        response_info = hook_middleware._extract_response_info(mock_response, processing_time)
        
        assert response_info["status_code"] == 200
        assert response_info["processing_time"] == 0.5
        assert "timestamp" in response_info
        assert "headers" in response_info