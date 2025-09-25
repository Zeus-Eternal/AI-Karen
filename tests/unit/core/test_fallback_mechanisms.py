"""
Tests for Fallback Mechanisms

Tests various fallback handlers and the fallback manager for graceful
service degradation when services fail.
"""

import pytest
import asyncio
import json
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import tempfile
import shutil

from src.ai_karen_engine.core.fallback_mechanisms import (
    FallbackManager, FallbackHandler, CacheFallbackHandler, StaticFallbackHandler,
    SimplifiedFallbackHandler, ProxyFallbackHandler, MockFallbackHandler,
    FallbackType, FallbackConfig, get_fallback_manager
)
from src.ai_karen_engine.core.error_recovery_manager import ErrorRecoveryManager


class TestFallbackConfig:
    """Test fallback configuration"""
    
    def test_default_config(self):
        """Test default fallback configuration"""
        config = FallbackConfig(FallbackType.CACHE)
        
        assert config.fallback_type == FallbackType.CACHE
        assert config.priority == 1
        assert config.timeout == 30
        assert config.retry_after == 300
        assert config.config is None
    
    def test_custom_config(self):
        """Test custom fallback configuration"""
        custom_config = {"key": "value"}
        config = FallbackConfig(
            fallback_type=FallbackType.STATIC,
            priority=2,
            timeout=60,
            retry_after=600,
            config=custom_config
        )
        
        assert config.fallback_type == FallbackType.STATIC
        assert config.priority == 2
        assert config.timeout == 60
        assert config.retry_after == 600
        assert config.config == custom_config


class TestCacheFallbackHandler:
    """Test cache-based fallback handler"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for cache files"""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def cache_handler(self, temp_dir):
        """Create cache fallback handler"""
        config = FallbackConfig(FallbackType.CACHE)
        handler = CacheFallbackHandler("test_service", config)
        # Override cache file path to use temp directory
        handler.cache_file = temp_dir / "test_cache.json"
        return handler
    
    @pytest.mark.asyncio
    async def test_cache_activation(self, cache_handler):
        """Test cache fallback activation"""
        assert not cache_handler.active
        
        result = await cache_handler.activate()
        
        assert result == True
        assert cache_handler.active == True
    
    @pytest.mark.asyncio
    async def test_cache_deactivation(self, cache_handler):
        """Test cache fallback deactivation"""
        # Activate first
        await cache_handler.activate()
        cache_handler.cache["test_key"] = "test_value"
        
        result = await cache_handler.deactivate()
        
        assert result == True
        assert cache_handler.active == False
        
        # Cache should be saved to file
        assert cache_handler.cache_file.exists()
        with open(cache_handler.cache_file, 'r') as f:
            saved_cache = json.load(f)
        assert saved_cache["test_key"] == "test_value"
    
    @pytest.mark.asyncio
    async def test_cache_request_handling(self, cache_handler):
        """Test handling requests with cached responses"""
        await cache_handler.activate()
        
        # Cache a response
        cache_handler.cache_response("user_123", {"name": "John", "id": 123})
        
        # Handle request using cache
        response = await cache_handler.handle_request("user_123")
        
        assert response == {"name": "John", "id": 123}
    
    @pytest.mark.asyncio
    async def test_cache_miss(self, cache_handler):
        """Test handling requests with cache miss"""
        await cache_handler.activate()
        
        # Request non-existent key
        with pytest.raises(Exception) as exc_info:
            await cache_handler.handle_request("non_existent_key")
        
        assert "No cached response available" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_cache_persistence(self, cache_handler, temp_dir):
        """Test cache persistence across handler instances"""
        # First handler instance
        await cache_handler.activate()
        cache_handler.cache_response("persistent_key", "persistent_value")
        await cache_handler.deactivate()
        
        # Second handler instance
        config = FallbackConfig(FallbackType.CACHE)
        new_handler = CacheFallbackHandler("test_service", config)
        new_handler.cache_file = temp_dir / "test_cache.json"
        
        await new_handler.activate()
        
        # Should load cached data
        response = await new_handler.handle_request("persistent_key")
        assert response == "persistent_value"


class TestStaticFallbackHandler:
    """Test static response fallback handler"""
    
    @pytest.fixture
    def static_handler(self):
        """Create static fallback handler"""
        config = FallbackConfig(
            FallbackType.STATIC,
            config={
                'static_responses': {
                    'user_info': {'name': 'Default User', 'id': 0},
                    'status': {'status': 'degraded', 'message': 'Service unavailable'}
                },
                'default_response': {'error': 'Service temporarily unavailable'}
            }
        )
        return StaticFallbackHandler("test_service", config)
    
    @pytest.mark.asyncio
    async def test_static_activation(self, static_handler):
        """Test static fallback activation"""
        result = await static_handler.activate()
        
        assert result == True
        assert static_handler.active == True
    
    @pytest.mark.asyncio
    async def test_static_request_handling(self, static_handler):
        """Test handling requests with static responses"""
        await static_handler.activate()
        
        # Request specific static response
        response = await static_handler.handle_request("user_info")
        assert response == {'name': 'Default User', 'id': 0}
        
        # Request another static response
        response = await static_handler.handle_request("status")
        assert response == {'status': 'degraded', 'message': 'Service unavailable'}
    
    @pytest.mark.asyncio
    async def test_static_default_response(self, static_handler):
        """Test default response for unknown request types"""
        await static_handler.activate()
        
        # Request unknown type should return default
        response = await static_handler.handle_request("unknown_type")
        assert response == {'error': 'Service temporarily unavailable'}
    
    @pytest.mark.asyncio
    async def test_static_no_default(self):
        """Test static handler without default response"""
        config = FallbackConfig(
            FallbackType.STATIC,
            config={'static_responses': {'known': 'response'}}
        )
        handler = StaticFallbackHandler("test_service", config)
        await handler.activate()
        
        # Should raise exception for unknown type with no default
        with pytest.raises(Exception) as exc_info:
            await handler.handle_request("unknown")
        
        assert "No static response available" in str(exc_info.value)


class TestSimplifiedFallbackHandler:
    """Test simplified functionality fallback handler"""
    
    @pytest.mark.asyncio
    async def test_simplified_async_handler(self):
        """Test simplified fallback with async handler"""
        async def simplified_func(user_id):
            return {"id": user_id, "name": "Simplified User", "limited": True}
        
        config = FallbackConfig(
            FallbackType.SIMPLIFIED,
            config={'simplified_handler': simplified_func}
        )
        handler = SimplifiedFallbackHandler("test_service", config)
        
        await handler.activate()
        
        response = await handler.handle_request(123)
        assert response == {"id": 123, "name": "Simplified User", "limited": True}
    
    @pytest.mark.asyncio
    async def test_simplified_sync_handler(self):
        """Test simplified fallback with sync handler"""
        def simplified_func(data):
            return {"processed": data, "mode": "simplified"}
        
        config = FallbackConfig(
            FallbackType.SIMPLIFIED,
            config={'simplified_handler': simplified_func}
        )
        handler = SimplifiedFallbackHandler("test_service", config)
        
        await handler.activate()
        
        response = await handler.handle_request("test_data")
        assert response == {"processed": "test_data", "mode": "simplified"}
    
    @pytest.mark.asyncio
    async def test_simplified_no_handler(self):
        """Test simplified fallback without handler function"""
        config = FallbackConfig(FallbackType.SIMPLIFIED)
        handler = SimplifiedFallbackHandler("test_service", config)
        
        # Should fail to activate without handler
        result = await handler.activate()
        assert result == False


class TestProxyFallbackHandler:
    """Test proxy fallback handler"""
    
    @pytest.fixture
    def mock_service_registry(self):
        """Mock service registry"""
        with patch('src.ai_karen_engine.core.fallback_mechanisms.ServiceRegistry') as mock:
            registry_instance = Mock()
            mock.return_value = registry_instance
            yield registry_instance
    
    @pytest.mark.asyncio
    async def test_proxy_to_service(self, mock_service_registry):
        """Test proxying to another service"""
        # Mock proxy service
        mock_service = Mock()
        mock_service.handle_request = AsyncMock(return_value={"proxied": True})
        mock_service_registry.get_service.return_value = mock_service
        
        config = FallbackConfig(
            FallbackType.PROXY,
            config={'proxy_service': 'backup_service'}
        )
        handler = ProxyFallbackHandler("test_service", config)
        
        await handler.activate()
        
        response = await handler.handle_request("test_data", param="value")
        
        assert response == {"proxied": True}
        mock_service.handle_request.assert_called_once_with("test_data", param="value")
    
    @pytest.mark.asyncio
    async def test_proxy_to_http_endpoint(self):
        """Test proxying to HTTP endpoint"""
        with patch('aiohttp.ClientSession') as mock_session:
            # Mock HTTP response
            mock_response = Mock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={"http_proxied": True})
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock(return_value=None)
            
            mock_session_instance = Mock()
            mock_session_instance.post.return_value = mock_response
            mock_session_instance.__aenter__ = AsyncMock(return_value=mock_session_instance)
            mock_session_instance.__aexit__ = AsyncMock(return_value=None)
            mock_session.return_value = mock_session_instance
            
            config = FallbackConfig(
                FallbackType.PROXY,
                config={'proxy_endpoint': 'http://backup.example.com/api'}
            )
            handler = ProxyFallbackHandler("test_service", config)
            
            await handler.activate()
            
            response = await handler.handle_request(data="test")
            
            assert response == {"http_proxied": True}
            mock_session_instance.post.assert_called_once_with(
                'http://backup.example.com/api',
                json={'data': 'test'}
            )
    
    @pytest.mark.asyncio
    async def test_proxy_no_config(self):
        """Test proxy fallback without configuration"""
        config = FallbackConfig(FallbackType.PROXY)
        handler = ProxyFallbackHandler("test_service", config)
        
        # Should fail to activate without proxy configuration
        result = await handler.activate()
        assert result == False


class TestMockFallbackHandler:
    """Test mock response fallback handler"""
    
    @pytest.mark.asyncio
    async def test_mock_with_generator(self):
        """Test mock fallback with generator function"""
        def mock_generator(request_type, **kwargs):
            return {
                "mock": True,
                "request_type": request_type,
                "params": kwargs
            }
        
        config = FallbackConfig(
            FallbackType.MOCK,
            config={'mock_generator': mock_generator}
        )
        handler = MockFallbackHandler("test_service", config)
        
        await handler.activate()
        
        response = await handler.handle_request("user_data", user_id=123)
        
        assert response["mock"] == True
        assert response["request_type"] == "user_data"
        assert response["params"]["user_id"] == 123
    
    @pytest.mark.asyncio
    async def test_mock_with_async_generator(self):
        """Test mock fallback with async generator function"""
        async def async_mock_generator(data):
            await asyncio.sleep(0.01)  # Simulate async work
            return {"async_mock": True, "data": data}
        
        config = FallbackConfig(
            FallbackType.MOCK,
            config={'mock_generator': async_mock_generator}
        )
        handler = MockFallbackHandler("test_service", config)
        
        await handler.activate()
        
        response = await handler.handle_request("test_input")
        
        assert response == {"async_mock": True, "data": "test_input"}
    
    @pytest.mark.asyncio
    async def test_mock_with_data(self):
        """Test mock fallback with static mock data"""
        mock_data = {
            "user": {"id": 0, "name": "Mock User"},
            "status": {"code": 200, "message": "Mock OK"}
        }
        
        config = FallbackConfig(
            FallbackType.MOCK,
            config={'mock_data': mock_data}
        )
        handler = MockFallbackHandler("test_service", config)
        
        await handler.activate()
        
        # Request specific mock data
        response = await handler.handle_request(type="user")
        assert response == {"id": 0, "name": "Mock User"}
        
        # Request default mock data
        response = await handler.handle_request(type="unknown")
        assert response == {"status": "mock_response"}


class TestFallbackManager:
    """Test fallback manager"""
    
    @pytest.fixture
    def mock_error_recovery_manager(self):
        """Mock error recovery manager"""
        manager = Mock(spec=ErrorRecoveryManager)
        manager.register_fallback_handler = Mock()
        manager.register_alert_handler = Mock()
        return manager
    
    @pytest.fixture
    def fallback_manager(self, mock_error_recovery_manager):
        """Create fallback manager with mocked dependencies"""
        with patch('src.ai_karen_engine.core.fallback_mechanisms.get_error_recovery_manager') as mock_get:
            mock_get.return_value = mock_error_recovery_manager
            return FallbackManager()
    
    def test_fallback_registration(self, fallback_manager):
        """Test fallback handler registration"""
        config = FallbackConfig(FallbackType.CACHE, priority=1)
        handler = CacheFallbackHandler("test_service", config)
        
        fallback_manager.register_fallback("test_service", handler)
        
        assert "test_service" in fallback_manager.fallback_handlers
        assert len(fallback_manager.fallback_handlers["test_service"]) == 1
        assert fallback_manager.fallback_handlers["test_service"][0] == handler
    
    def test_fallback_priority_ordering(self, fallback_manager):
        """Test fallback handlers are ordered by priority"""
        # Register handlers with different priorities
        config1 = FallbackConfig(FallbackType.CACHE, priority=3)
        handler1 = CacheFallbackHandler("test_service", config1)
        
        config2 = FallbackConfig(FallbackType.STATIC, priority=1)
        handler2 = StaticFallbackHandler("test_service", config2)
        
        config3 = FallbackConfig(FallbackType.MOCK, priority=2)
        handler3 = MockFallbackHandler("test_service", config3)
        
        fallback_manager.register_fallback("test_service", handler1)
        fallback_manager.register_fallback("test_service", handler2)
        fallback_manager.register_fallback("test_service", handler3)
        
        handlers = fallback_manager.fallback_handlers["test_service"]
        
        # Should be ordered by priority (lower number = higher priority)
        assert handlers[0].config.priority == 1  # Static
        assert handlers[1].config.priority == 2  # Mock
        assert handlers[2].config.priority == 3  # Cache
    
    def test_cache_fallback_registration_helper(self, fallback_manager):
        """Test cache fallback registration helper"""
        handler = fallback_manager.register_cache_fallback("cache_service", priority=2)
        
        assert isinstance(handler, CacheFallbackHandler)
        assert handler.config.fallback_type == FallbackType.CACHE
        assert handler.config.priority == 2
        assert "cache_service" in fallback_manager.fallback_handlers
    
    def test_static_fallback_registration_helper(self, fallback_manager):
        """Test static fallback registration helper"""
        static_responses = {"error": "Service unavailable"}
        default_response = {"status": "degraded"}
        
        handler = fallback_manager.register_static_fallback(
            "static_service",
            static_responses,
            default_response,
            priority=3
        )
        
        assert isinstance(handler, StaticFallbackHandler)
        assert handler.config.fallback_type == FallbackType.STATIC
        assert handler.config.priority == 3
        assert handler.static_responses == static_responses
        assert handler.default_response == default_response
    
    def test_simplified_fallback_registration_helper(self, fallback_manager):
        """Test simplified fallback registration helper"""
        def simplified_handler():
            return {"simplified": True}
        
        handler = fallback_manager.register_simplified_fallback(
            "simplified_service",
            simplified_handler,
            priority=4
        )
        
        assert isinstance(handler, SimplifiedFallbackHandler)
        assert handler.config.fallback_type == FallbackType.SIMPLIFIED
        assert handler.config.priority == 4
        assert handler.simplified_handler == simplified_handler
    
    @pytest.mark.asyncio
    async def test_fallback_activation(self, fallback_manager):
        """Test fallback activation"""
        # Register a mock fallback that always activates successfully
        config = FallbackConfig(FallbackType.MOCK)
        handler = MockFallbackHandler("test_service", config)
        fallback_manager.register_fallback("test_service", handler)
        
        result = await fallback_manager.activate_fallback("test_service")
        
        assert result == True
        assert "test_service" in fallback_manager.active_fallbacks
        assert fallback_manager.active_fallbacks["test_service"] == handler
        assert handler.active == True
    
    @pytest.mark.asyncio
    async def test_fallback_activation_priority(self, fallback_manager):
        """Test fallback activation tries handlers in priority order"""
        # Register handlers with different priorities, first one fails
        config1 = FallbackConfig(FallbackType.CACHE, priority=1)
        handler1 = Mock(spec=FallbackHandler)
        handler1.config = config1
        handler1.activate = AsyncMock(return_value=False)  # Fails
        
        config2 = FallbackConfig(FallbackType.STATIC, priority=2)
        handler2 = Mock(spec=FallbackHandler)
        handler2.config = config2
        handler2.activate = AsyncMock(return_value=True)  # Succeeds
        
        fallback_manager.register_fallback("test_service", handler1)
        fallback_manager.register_fallback("test_service", handler2)
        
        result = await fallback_manager.activate_fallback("test_service")
        
        assert result == True
        assert fallback_manager.active_fallbacks["test_service"] == handler2
        
        # Both should have been tried, in priority order
        handler1.activate.assert_called_once()
        handler2.activate.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_fallback_deactivation(self, fallback_manager):
        """Test fallback deactivation"""
        # Activate a fallback first
        config = FallbackConfig(FallbackType.MOCK)
        handler = MockFallbackHandler("test_service", config)
        fallback_manager.register_fallback("test_service", handler)
        await fallback_manager.activate_fallback("test_service")
        
        # Deactivate
        result = await fallback_manager.deactivate_fallback("test_service")
        
        assert result == True
        assert "test_service" not in fallback_manager.active_fallbacks
        assert handler.active == False
    
    @pytest.mark.asyncio
    async def test_fallback_request_handling(self, fallback_manager):
        """Test handling requests through active fallback"""
        # Setup mock fallback
        config = FallbackConfig(
            FallbackType.MOCK,
            config={'mock_data': {'test': 'mock_response'}}
        )
        handler = MockFallbackHandler("test_service", config)
        fallback_manager.register_fallback("test_service", handler)
        await fallback_manager.activate_fallback("test_service")
        
        # Handle request
        response = await fallback_manager.handle_fallback_request("test_service", type="test")
        
        assert response == "mock_response"
    
    @pytest.mark.asyncio
    async def test_fallback_request_no_active(self, fallback_manager):
        """Test handling requests when no fallback is active"""
        with pytest.raises(Exception) as exc_info:
            await fallback_manager.handle_fallback_request("no_fallback_service")
        
        assert "No active fallback" in str(exc_info.value)
    
    def test_fallback_status_queries(self, fallback_manager):
        """Test fallback status query methods"""
        # Initially no active fallbacks
        assert not fallback_manager.is_fallback_active("test_service")
        assert fallback_manager.get_active_fallback_type("test_service") is None
        
        # Activate a fallback
        config = FallbackConfig(FallbackType.CACHE)
        handler = CacheFallbackHandler("test_service", config)
        fallback_manager.active_fallbacks["test_service"] = handler
        
        assert fallback_manager.is_fallback_active("test_service")
        assert fallback_manager.get_active_fallback_type("test_service") == FallbackType.CACHE
    
    @pytest.mark.asyncio
    async def test_fallback_status_report(self, fallback_manager):
        """Test fallback status reporting"""
        # Register some fallbacks
        cache_handler = fallback_manager.register_cache_fallback("service1", priority=1)
        static_handler = fallback_manager.register_static_fallback("service1", {}, priority=2)
        mock_handler = fallback_manager.register_mock_fallback("service2", priority=1)
        
        # Activate one fallback
        await fallback_manager.activate_fallback("service1")
        
        status = await fallback_manager.get_fallback_status()
        
        assert "active_fallbacks" in status
        assert "registered_fallbacks" in status
        
        # Should show active fallback
        assert "service1" in status["active_fallbacks"]
        active_info = status["active_fallbacks"]["service1"]
        assert active_info["type"] == FallbackType.CACHE.value
        assert active_info["priority"] == 1
        
        # Should show registered fallbacks
        assert "service1" in status["registered_fallbacks"]
        assert "service2" in status["registered_fallbacks"]
        assert len(status["registered_fallbacks"]["service1"]) == 2  # Cache and static
        assert len(status["registered_fallbacks"]["service2"]) == 1  # Mock only
    
    @pytest.mark.asyncio
    async def test_service_failure_alert_handling(self, fallback_manager):
        """Test handling service failure alerts"""
        # Register a fallback
        fallback_manager.register_mock_fallback("failed_service")
        
        # Simulate service failure alert
        alert_data = {
            "message": "Circuit breaker opened for service failed_service",
            "severity": "critical"
        }
        
        await fallback_manager._handle_service_failure_alert(alert_data)
        
        # Should have activated fallback
        assert fallback_manager.is_fallback_active("failed_service")
    
    def test_global_instance(self):
        """Test global instance access"""
        manager1 = get_fallback_manager()
        manager2 = get_fallback_manager()
        
        # Should return same instance
        assert manager1 is manager2


@pytest.mark.asyncio
async def test_integration_with_error_recovery_manager():
    """Test integration between fallback manager and error recovery manager"""
    mock_error_manager = Mock(spec=ErrorRecoveryManager)
    mock_error_manager.register_fallback_handler = Mock()
    mock_error_manager.register_alert_handler = Mock()
    
    with patch('src.ai_karen_engine.core.fallback_mechanisms.get_error_recovery_manager') as mock_get:
        mock_get.return_value = mock_error_manager
        
        fallback_manager = FallbackManager()
        
        # Should register alert handler
        mock_error_manager.register_alert_handler.assert_called_once()
        
        # Register a fallback
        fallback_manager.register_cache_fallback("integration_service")
        
        # Should register fallback handler with error recovery manager
        mock_error_manager.register_fallback_handler.assert_called_once()
        call_args = mock_error_manager.register_fallback_handler.call_args
        assert call_args[0][0] == "integration_service"


@pytest.mark.asyncio
async def test_concurrent_fallback_operations():
    """Test concurrent fallback activation and deactivation"""
    fallback_manager = FallbackManager()
    
    # Register multiple fallbacks
    services = ["service1", "service2", "service3"]
    for service in services:
        fallback_manager.register_mock_fallback(service)
    
    # Activate all fallbacks concurrently
    activation_tasks = [
        fallback_manager.activate_fallback(service)
        for service in services
    ]
    results = await asyncio.gather(*activation_tasks)
    
    # All should succeed
    assert all(results)
    
    # All should be active
    for service in services:
        assert fallback_manager.is_fallback_active(service)
    
    # Deactivate all concurrently
    deactivation_tasks = [
        fallback_manager.deactivate_fallback(service)
        for service in services
    ]
    results = await asyncio.gather(*deactivation_tasks)
    
    # All should succeed
    assert all(results)
    
    # None should be active
    for service in services:
        assert not fallback_manager.is_fallback_active(service)