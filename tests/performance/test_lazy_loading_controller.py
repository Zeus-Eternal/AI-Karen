"""
Tests for the Lazy Loading Controller.

This module tests the lazy loading functionality including service registration,
retrieval, caching, preloading strategies, and service proxy patterns.
"""

import asyncio
import pytest
import time
from unittest.mock import Mock, AsyncMock, patch
from typing import Any, Dict, List

from src.ai_karen_engine.core.lazy_loading_controller import (
    LazyLoadingController,
    ServiceLoader,
    CallableServiceLoader,
    RegistryServiceLoader,
    ServiceProxy,
    LoadingStrategy,
    PreloadCondition,
    UsagePattern,
    PreloadRule
)
from src.ai_karen_engine.core.service_classification import ServiceConfig, ServiceClassification
from src.ai_karen_engine.core.classified_service_registry import ClassifiedServiceRegistry


class MockService:
    """Mock service for testing."""
    
    def __init__(self, name: str):
        self.name = name
        self.initialized = True
        self.shutdown_called = False
    
    async def async_method(self, value: str) -> str:
        return f"async_{self.name}_{value}"
    
    def sync_method(self, value: str) -> str:
        return f"sync_{self.name}_{value}"
    
    async def shutdown(self):
        self.shutdown_called = True


class MockServiceLoader(ServiceLoader[MockService]):
    """Mock service loader for testing."""
    
    def __init__(self, service_name: str, dependencies: List[str] = None, fail_load: bool = False):
        self.service_name = service_name
        self.dependencies = dependencies or []
        self.fail_load = fail_load
        self.load_count = 0
        self.unload_count = 0
    
    async def load(self) -> MockService:
        self.load_count += 1
        if self.fail_load:
            raise RuntimeError(f"Failed to load {self.service_name}")
        await asyncio.sleep(0.01)  # Simulate loading time
        return MockService(self.service_name)
    
    async def unload(self, instance: MockService) -> None:
        self.unload_count += 1
        await instance.shutdown()
    
    def get_dependencies(self) -> List[str]:
        return self.dependencies.copy()


@pytest.fixture
def controller():
    """Create a lazy loading controller for testing."""
    return LazyLoadingController(cache_size_limit=5, enable_usage_tracking=True)


@pytest.fixture
def mock_registry():
    """Create a mock classified service registry."""
    registry = Mock(spec=ClassifiedServiceRegistry)
    registry.classified_services = {}
    registry.load_service_on_demand = AsyncMock()
    return registry


class TestLazyLoadingController:
    """Test cases for LazyLoadingController."""
    
    def test_initialization(self, controller):
        """Test controller initialization."""
        assert controller.cache_size_limit == 5
        assert controller.enable_usage_tracking is True
        assert len(controller.service_loaders) == 0
        assert len(controller.cached_instances) == 0
        assert len(controller.usage_patterns) == 0
    
    def test_register_lazy_service_with_loader(self, controller):
        """Test registering a service with a ServiceLoader."""
        loader = MockServiceLoader("test_service")
        controller.register_lazy_service("test_service", loader)
        
        assert "test_service" in controller.service_loaders
        assert controller.service_loaders["test_service"] == loader
        assert "test_service" in controller.usage_patterns
    
    def test_register_lazy_service_with_callable(self, controller):
        """Test registering a service with a callable factory."""
        def factory():
            return MockService("callable_service")
        
        controller.register_lazy_service("callable_service", factory)
        
        assert "callable_service" in controller.service_loaders
        assert isinstance(controller.service_loaders["callable_service"], CallableServiceLoader)
    
    def test_register_lazy_service_invalid_loader(self, controller):
        """Test registering a service with invalid loader."""
        with pytest.raises(ValueError, match="Loader must be a ServiceLoader instance or callable"):
            controller.register_lazy_service("invalid_service", "not_a_loader")
    
    @pytest.mark.asyncio
    async def test_get_service_lazy_loading(self, controller):
        """Test lazy loading of a service."""
        loader = MockServiceLoader("lazy_service")
        controller.register_lazy_service("lazy_service", loader)
        
        # Service should not be loaded yet
        assert loader.load_count == 0
        assert "lazy_service" not in controller.cached_instances
        
        # Get service should trigger loading
        service = await controller.get_service("lazy_service")
        
        assert loader.load_count == 1
        assert "lazy_service" in controller.cached_instances
        assert isinstance(service, ServiceProxy)
    
    @pytest.mark.asyncio
    async def test_get_service_caching(self, controller):
        """Test service caching behavior."""
        loader = MockServiceLoader("cached_service")
        controller.register_lazy_service("cached_service", loader)
        
        # First access should load and cache
        service1 = await controller.get_service("cached_service")
        assert loader.load_count == 1
        assert controller.metrics["cache_misses"] == 1
        
        # Second access should use cache
        service2 = await controller.get_service("cached_service")
        assert loader.load_count == 1  # No additional load
        assert controller.metrics["cache_hits"] == 1
        assert service1 is service2
    
    @pytest.mark.asyncio
    async def test_cache_lru_eviction(self, controller):
        """Test LRU cache eviction."""
        # Fill cache to limit
        for i in range(controller.cache_size_limit + 2):
            loader = MockServiceLoader(f"service_{i}")
            controller.register_lazy_service(f"service_{i}", loader)
            await controller.get_service(f"service_{i}")
        
        # First services should be evicted
        assert len(controller.cached_instances) == controller.cache_size_limit
        assert "service_0" not in controller.cached_instances
        assert "service_1" not in controller.cached_instances
    
    @pytest.mark.asyncio
    async def test_service_proxy_transparent_access(self, controller):
        """Test transparent access through service proxy."""
        loader = MockServiceLoader("proxy_service")
        controller.register_lazy_service("proxy_service", loader)
        
        proxy = await controller.get_service("proxy_service")
        
        # Test async method access
        result = await proxy.async_method("test")
        assert result == "async_proxy_service_test"
        
        # Test sync method access (in async context, we need to await)
        result = await proxy.sync_method("test")
        assert result == "sync_proxy_service_test"
    
    def test_get_service_proxy_without_loading(self, controller):
        """Test getting service proxy without loading."""
        loader = MockServiceLoader("proxy_only_service")
        controller.register_lazy_service("proxy_only_service", loader)
        
        proxy = controller.get_service_proxy("proxy_only_service")
        
        assert isinstance(proxy, ServiceProxy)
        assert loader.load_count == 0  # Should not be loaded yet
        assert "proxy_only_service" not in controller.cached_instances
    
    @pytest.mark.asyncio
    async def test_usage_pattern_tracking(self, controller):
        """Test usage pattern tracking."""
        loader = MockServiceLoader("tracked_service")
        controller.register_lazy_service("tracked_service", loader)
        
        # Access service multiple times
        for _ in range(3):
            await controller.get_service("tracked_service")
            await asyncio.sleep(0.01)
        
        pattern = controller.usage_patterns["tracked_service"]
        # Note: access count might be higher due to internal proxy loading
        assert pattern.access_count >= 3
        assert pattern.last_accessed is not None
        assert len(pattern.peak_usage_hours) > 0
    
    def test_configure_preload_conditions(self, controller):
        """Test configuring preload conditions."""
        loader = MockServiceLoader("preload_service")
        controller.register_lazy_service("preload_service", loader)
        
        conditions = {
            "startup": {
                "services": ["preload_service"],
                "strategy": "preload_critical",
                "priority": 50
            }
        }
        
        controller.configure_preload_conditions(conditions)
        
        assert len(controller.preload_rules) == 1
        assert PreloadCondition.STARTUP in controller.preload_conditions
        assert "preload_service" in controller.preload_conditions[PreloadCondition.STARTUP]
    
    @pytest.mark.asyncio
    async def test_trigger_preload_condition(self, controller):
        """Test triggering preload conditions."""
        loader = MockServiceLoader("preload_trigger_service")
        controller.register_lazy_service("preload_trigger_service", loader)
        
        # Configure preload condition
        conditions = {
            "startup": {
                "services": ["preload_trigger_service"],
                "strategy": "preload_critical"
            }
        }
        controller.configure_preload_conditions(conditions)
        
        # Trigger preload
        preloaded = await controller.trigger_preload_condition(PreloadCondition.STARTUP)
        
        assert "preload_trigger_service" in preloaded
        assert loader.load_count == 1
        assert "preload_trigger_service" in controller.cached_instances
    
    @pytest.mark.asyncio
    async def test_preload_critical_path_services(self, controller):
        """Test preloading critical path services."""
        # Create services with different usage patterns
        for i in range(3):
            loader = MockServiceLoader(f"critical_service_{i}")
            controller.register_lazy_service(f"critical_service_{i}", loader)
            
            # Simulate different access patterns with high scores
            pattern = controller.usage_patterns[f"critical_service_{i}"]
            pattern.access_count = (i + 1) * 10
            pattern.critical_path_score = 0.6 + (i * 0.1)  # Ensure scores > 0.5 threshold
        
        preloaded = await controller.preload_critical_path_services()
        
        # Should preload services with high critical path scores
        assert len(preloaded) > 0
        assert controller.metrics["services_preloaded"] > 0
    
    @pytest.mark.asyncio
    async def test_unload_service(self, controller):
        """Test unloading a service."""
        loader = MockServiceLoader("unload_service")
        controller.register_lazy_service("unload_service", loader)
        
        # Load service first
        await controller.get_service("unload_service")
        assert "unload_service" in controller.cached_instances
        
        # Unload service
        result = await controller.unload_service("unload_service")
        
        assert result is True
        assert "unload_service" not in controller.cached_instances
        assert loader.unload_count == 1
    
    @pytest.mark.asyncio
    async def test_clear_cache(self, controller):
        """Test clearing the entire cache."""
        # Load multiple services
        for i in range(3):
            loader = MockServiceLoader(f"clear_service_{i}")
            controller.register_lazy_service(f"clear_service_{i}", loader)
            await controller.get_service(f"clear_service_{i}")
        
        assert len(controller.cached_instances) == 3
        
        # Clear cache
        count = await controller.clear_cache()
        
        assert count == 3
        assert len(controller.cached_instances) == 0
    
    def test_get_usage_report(self, controller):
        """Test getting usage report."""
        loader = MockServiceLoader("report_service")
        controller.register_lazy_service("report_service", loader)
        
        report = controller.get_usage_report()
        
        assert "metrics" in report
        assert "cache_status" in report
        assert "usage_patterns" in report
        assert "registered_services" in report
        assert report["registered_services"] == 1
    
    def test_get_preload_recommendations(self, controller):
        """Test getting preload recommendations."""
        # Create service with high critical path score
        loader = MockServiceLoader("recommend_service")
        controller.register_lazy_service("recommend_service", loader)
        
        pattern = controller.usage_patterns["recommend_service"]
        pattern.critical_path_score = 0.8
        pattern.access_count = 10  # Add some access count for better recommendations
        
        # Also add co-access tracking
        controller.co_access_tracking["recommend_service"] = {"service1", "service2", "service3"}
        
        recommendations = controller.get_preload_recommendations()
        
        assert len(recommendations) > 0
        assert any(rec["service"] == "recommend_service" for rec in recommendations)
    
    @pytest.mark.asyncio
    async def test_service_loading_failure(self, controller):
        """Test handling of service loading failures."""
        loader = MockServiceLoader("failing_service", fail_load=True)
        controller.register_lazy_service("failing_service", loader)
        
        with pytest.raises(RuntimeError, match="Failed to load failing_service"):
            await controller.get_service("failing_service")
    
    @pytest.mark.asyncio
    async def test_concurrent_service_loading(self, controller):
        """Test concurrent loading of the same service."""
        loader = MockServiceLoader("concurrent_service")
        controller.register_lazy_service("concurrent_service", loader)
        
        # Start multiple concurrent loads
        tasks = [
            controller.get_service("concurrent_service")
            for _ in range(5)
        ]
        
        results = await asyncio.gather(*tasks)
        
        # Should only load once despite concurrent requests
        assert loader.load_count == 1
        assert all(isinstance(result, ServiceProxy) for result in results)
    
    @pytest.mark.asyncio
    async def test_background_tasks(self, controller):
        """Test starting and stopping background tasks."""
        await controller.start_background_tasks()
        
        assert controller.preload_task is not None
        assert controller.cleanup_task is not None
        assert not controller.preload_task.done()
        assert not controller.cleanup_task.done()
        
        await controller.stop_background_tasks()
        
        assert controller.preload_task is None
        assert controller.cleanup_task is None


class TestCallableServiceLoader:
    """Test cases for CallableServiceLoader."""
    
    @pytest.mark.asyncio
    async def test_sync_factory_function(self):
        """Test loading with synchronous factory function."""
        def factory():
            return MockService("sync_factory")
        
        loader = CallableServiceLoader(factory)
        service = await loader.load()
        
        assert isinstance(service, MockService)
        assert service.name == "sync_factory"
    
    @pytest.mark.asyncio
    async def test_async_factory_function(self):
        """Test loading with asynchronous factory function."""
        async def factory():
            await asyncio.sleep(0.01)
            return MockService("async_factory")
        
        loader = CallableServiceLoader(factory)
        service = await loader.load()
        
        assert isinstance(service, MockService)
        assert service.name == "async_factory"
    
    @pytest.mark.asyncio
    async def test_cleanup_function(self):
        """Test service cleanup with cleanup function."""
        cleanup_called = False
        
        def cleanup_func(service):
            nonlocal cleanup_called
            cleanup_called = True
        
        def factory():
            return MockService("cleanup_test")
        
        loader = CallableServiceLoader(factory, cleanup_func=cleanup_func)
        service = await loader.load()
        await loader.unload(service)
        
        assert cleanup_called is True
    
    def test_get_dependencies(self):
        """Test getting service dependencies."""
        def factory():
            return MockService("deps_test")
        
        dependencies = ["dep1", "dep2"]
        loader = CallableServiceLoader(factory, dependencies=dependencies)
        
        assert loader.get_dependencies() == dependencies


class TestRegistryServiceLoader:
    """Test cases for RegistryServiceLoader."""
    
    @pytest.mark.asyncio
    async def test_load_from_registry(self, mock_registry):
        """Test loading service from registry."""
        mock_service = MockService("registry_service")
        mock_registry.load_service_on_demand.return_value = mock_service
        
        loader = RegistryServiceLoader("registry_service", mock_registry)
        service = await loader.load()
        
        assert service is mock_service
        mock_registry.load_service_on_demand.assert_called_once_with("registry_service")
    
    def test_get_dependencies_from_registry(self, mock_registry):
        """Test getting dependencies from registry configuration."""
        config = ServiceConfig(
            name="registry_service",
            classification=ServiceClassification.OPTIONAL,
            dependencies=["dep1", "dep2"]
        )
        
        mock_registry.classified_services = {
            "registry_service": Mock(config=config)
        }
        
        loader = RegistryServiceLoader("registry_service", mock_registry)
        dependencies = loader.get_dependencies()
        
        assert dependencies == ["dep1", "dep2"]
    
    def test_get_dependencies_fallback(self, mock_registry):
        """Test getting dependencies with fallback."""
        mock_registry.classified_services = {}
        
        fallback_deps = ["fallback_dep"]
        loader = RegistryServiceLoader("unknown_service", mock_registry, dependencies=fallback_deps)
        dependencies = loader.get_dependencies()
        
        assert dependencies == fallback_deps


class TestServiceProxy:
    """Test cases for ServiceProxy."""
    
    @pytest.mark.asyncio
    async def test_proxy_lazy_loading(self):
        """Test proxy lazy loading behavior."""
        controller = LazyLoadingController()
        loader = MockServiceLoader("proxy_test")
        proxy = ServiceProxy("proxy_test", loader, controller)
        
        # Service should not be loaded initially
        assert loader.load_count == 0
        
        # Accessing service should trigger loading
        result = await proxy.async_method("test")
        
        assert loader.load_count == 1
        assert result == "async_proxy_test_test"
    
    @pytest.mark.asyncio
    async def test_proxy_caching(self):
        """Test proxy instance caching."""
        controller = LazyLoadingController()
        loader = MockServiceLoader("proxy_cache_test")
        proxy = ServiceProxy("proxy_cache_test", loader, controller)
        
        # Multiple accesses should use same instance
        await proxy.async_method("test1")
        await proxy.sync_method("test2")
        
        assert loader.load_count == 1  # Only loaded once
    
    @pytest.mark.asyncio
    async def test_proxy_concurrent_loading(self):
        """Test proxy handling of concurrent loading."""
        controller = LazyLoadingController()
        loader = MockServiceLoader("proxy_concurrent_test")
        proxy = ServiceProxy("proxy_concurrent_test", loader, controller)
        
        # Start multiple concurrent operations
        tasks = [
            proxy.async_method(f"test_{i}")
            for i in range(5)
        ]
        
        results = await asyncio.gather(*tasks)
        
        # Should only load once despite concurrent access
        assert loader.load_count == 1
        assert len(results) == 5
    
    @pytest.mark.asyncio
    async def test_proxy_unload(self):
        """Test proxy unloading."""
        controller = LazyLoadingController()
        loader = MockServiceLoader("proxy_unload_test")
        proxy = ServiceProxy("proxy_unload_test", loader, controller)
        
        # Load service
        await proxy.async_method("test")
        assert loader.load_count == 1
        
        # Unload service
        await proxy._unload()
        assert loader.unload_count == 1
        
        # Next access should reload
        await proxy.async_method("test2")
        assert loader.load_count == 2


class TestUsagePattern:
    """Test cases for UsagePattern."""
    
    def test_record_access(self):
        """Test recording service access."""
        pattern = UsagePattern("test_service")
        
        # Record first access
        pattern.record_access()
        
        assert pattern.access_count == 1
        assert pattern.last_accessed is not None
        assert len(pattern.peak_usage_hours) == 1
        
        # Record second access
        time.sleep(0.01)
        pattern.record_access()
        
        assert pattern.access_count == 2
        assert pattern.average_access_interval > 0


if __name__ == "__main__":
    pytest.main([__file__])