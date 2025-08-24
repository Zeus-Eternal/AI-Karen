"""
Unit tests for service initialization improvements.

Tests the enhanced service registry with graceful dependency handling,
metrics deduplication, and comprehensive health monitoring.
"""

import asyncio
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, Any

from ai_karen_engine.core.service_registry import (
    ServiceRegistry,
    ServiceStatus,
    DependencyStatus,
    DependencyInfo,
    ServiceInfo,
    get_service_registry,
    initialize_services
)
from ai_karen_engine.core.metrics_manager import MetricsManager, get_metrics_manager


class MockService:
    """Mock service for testing."""
    
    def __init__(self, config=None, **kwargs):
        self.config = config
        self.dependencies = kwargs
        self.initialized = False
        self.shutdown_called = False
    
    async def initialize(self):
        self.initialized = True
    
    async def shutdown(self):
        self.shutdown_called = True


class FailingService:
    """Mock service that fails during initialization."""
    
    def __init__(self, config=None, **kwargs):
        raise ValueError("Service initialization failed")


class DependentService:
    """Mock service that requires dependencies."""
    
    def __init__(self, config=None, **kwargs):
        # Check if any dependency was provided
        if not kwargs:
            raise ValueError("Required dependency missing")
        self.config = config
        self.dependencies = kwargs
        self.initialized = False
    
    async def initialize(self):
        self.initialized = True


@pytest.fixture
def service_registry():
    """Create a fresh service registry for testing."""
    return ServiceRegistry()


@pytest.fixture
def metrics_manager():
    """Create a fresh metrics manager for testing."""
    manager = MetricsManager()
    manager.clear_registry()
    return manager


class TestServiceRegistry:
    """Test the enhanced service registry functionality."""
    
    def test_service_registration(self, service_registry):
        """Test basic service registration."""
        service_registry.register_service("test_service", MockService)
        
        assert "test_service" in service_registry._services
        service_info = service_registry._services["test_service"]
        assert service_info.name == "test_service"
        assert service_info.service_type == MockService
        assert service_info.status == ServiceStatus.PENDING
    
    def test_service_registration_with_dependencies(self, service_registry):
        """Test service registration with dependencies."""
        dependencies = {"dep1": True, "dep2": False}  # dep1 required, dep2 optional
        service_registry.register_service("test_service", MockService, dependencies)
        
        service_info = service_registry._services["test_service"]
        assert len(service_info.dependencies) == 2
        
        dep1 = next(d for d in service_info.dependencies if d.name == "dep1")
        dep2 = next(d for d in service_info.dependencies if d.name == "dep2")
        
        assert dep1.required is True
        assert dep2.required is False
    
    @pytest.mark.asyncio
    async def test_simple_service_initialization(self, service_registry):
        """Test initialization of a service without dependencies."""
        service_registry.register_service("test_service", MockService)
        
        instance = await service_registry.get_service("test_service")
        
        assert instance is not None
        assert isinstance(instance, MockService)
        assert instance.initialized is True
        
        service_info = service_registry._services["test_service"]
        assert service_info.status == ServiceStatus.READY
        assert service_info.initialization_time is not None
    
    @pytest.mark.asyncio
    async def test_service_initialization_with_dependencies(self, service_registry):
        """Test initialization of services with dependencies."""
        # Register dependency first
        service_registry.register_service("dependency_service", MockService)
        
        # Register dependent service
        service_registry.register_service(
            "dependent", 
            DependentService, 
            {"dependency_service": True}
        )
        
        # Get dependent service (should initialize dependency first)
        instance = await service_registry.get_service("dependent")
        
        assert instance is not None
        assert isinstance(instance, DependentService)
        assert len(instance.dependencies) > 0
        
        # Check that dependency was also initialized
        dep_instance = await service_registry.get_service("dependency_service")
        assert dep_instance.initialized is True
    
    @pytest.mark.asyncio
    async def test_missing_required_dependency(self, service_registry):
        """Test handling of missing required dependencies."""
        service_registry.register_service(
            "dependent", 
            DependentService, 
            {"missing_dep": True}
        )
        
        # Should fail to initialize due to missing dependency
        with pytest.raises(RuntimeError) as exc_info:
            await service_registry.get_service("dependent")
        
        assert "failed to initialize" in str(exc_info.value).lower()
        
        service_info = service_registry._services["dependent"]
        assert service_info.status == ServiceStatus.ERROR
        assert "missing required dependencies" in service_info.error_message.lower()
    
    @pytest.mark.asyncio
    async def test_optional_dependency_handling(self, service_registry):
        """Test handling of missing optional dependencies."""
        service_registry.register_service(
            "test_service", 
            MockService, 
            {"optional_dep": False}  # Optional dependency
        )
        
        instance = await service_registry.get_service("test_service")
        
        assert instance is not None
        service_info = service_registry._services["test_service"]
        # Should be ready even without optional dependency
        assert service_info.status in [ServiceStatus.READY, ServiceStatus.DEGRADED]
    
    @pytest.mark.asyncio
    async def test_service_initialization_failure(self, service_registry):
        """Test handling of service initialization failures."""
        service_registry.register_service("failing_service", FailingService)
        
        # Should raise RuntimeError due to initialization failure
        with pytest.raises(RuntimeError) as exc_info:
            await service_registry.get_service("failing_service")
        
        assert "failed to initialize" in str(exc_info.value).lower()
        
        service_info = service_registry._services["failing_service"]
        assert service_info.status == ServiceStatus.ERROR
        assert "Failed to create instance" in service_info.error_message
    
    @pytest.mark.asyncio
    async def test_max_initialization_attempts(self, service_registry):
        """Test maximum initialization attempts handling."""
        service_registry.register_service("failing_service", FailingService, max_attempts=2)
        
        # Try to get service multiple times - should raise RuntimeError each time
        for _ in range(3):
            with pytest.raises(RuntimeError):
                await service_registry.get_service("failing_service")
        
        service_info = service_registry._services["failing_service"]
        assert service_info.initialization_attempts == 2  # Should stop at max attempts
        assert service_info.status == ServiceStatus.ERROR
    
    @pytest.mark.asyncio
    async def test_health_check(self, service_registry):
        """Test service health checking."""
        async def mock_health_check(instance):
            return {"status": "healthy", "details": "All good"}
        
        service_registry.register_service(
            "test_service", 
            MockService, 
            health_check=mock_health_check
        )
        
        # Initialize service
        await service_registry.get_service("test_service")
        
        # Perform health check
        health_results = await service_registry.health_check("test_service")
        
        assert "test_service" in health_results
        result = health_results["test_service"]
        assert result["status"] == ServiceStatus.READY.value
        assert result["health_check"]["status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_health_check_failure(self, service_registry):
        """Test handling of health check failures."""
        async def failing_health_check(instance):
            raise Exception("Health check failed")
        
        service_registry.register_service(
            "test_service", 
            MockService, 
            health_check=failing_health_check
        )
        
        # Initialize service
        await service_registry.get_service("test_service")
        
        # Perform health check
        health_results = await service_registry.health_check("test_service")
        
        result = health_results["test_service"]
        assert "error" in result["health_check"]
        assert result["health_status"] == "unhealthy"
    
    def test_initialization_report(self, service_registry):
        """Test initialization report generation."""
        service_registry.register_service("service1", MockService)
        service_registry.register_service("service2", FailingService)
        
        report = service_registry.get_initialization_report()
        
        assert "summary" in report
        assert "services" in report
        assert "dependency_graph" in report
        assert "metrics" in report
        
        summary = report["summary"]
        assert summary["total_services"] == 2
        assert "success_rate" in summary
    
    @pytest.mark.asyncio
    async def test_service_shutdown(self, service_registry):
        """Test graceful service shutdown."""
        service_registry.register_service("test_service", MockService)
        
        # Initialize service
        instance = await service_registry.get_service("test_service")
        
        # Shutdown registry
        await service_registry.shutdown()
        
        # Check that service was shut down
        assert instance.shutdown_called is True
        
        service_info = service_registry._services["test_service"]
        assert service_info.status == ServiceStatus.STOPPED


class TestMetricsManager:
    """Test the metrics manager functionality."""
    
    def test_metrics_manager_initialization(self, metrics_manager):
        """Test metrics manager initialization."""
        assert metrics_manager is not None
        info = metrics_manager.get_metrics_info()
        assert "prometheus_available" in info
        assert "registered_count" in info
    
    def test_counter_registration(self, metrics_manager):
        """Test counter metric registration."""
        counter = metrics_manager.register_counter(
            "test_counter",
            "Test counter metric",
            ["label1", "label2"]
        )
        
        assert counter is not None
        assert metrics_manager.is_registered("test_counter")
    
    def test_histogram_registration(self, metrics_manager):
        """Test histogram metric registration."""
        histogram = metrics_manager.register_histogram(
            "test_histogram",
            "Test histogram metric",
            ["label1"]
        )
        
        assert histogram is not None
        assert metrics_manager.is_registered("test_histogram")
    
    def test_gauge_registration(self, metrics_manager):
        """Test gauge metric registration."""
        gauge = metrics_manager.register_gauge(
            "test_gauge",
            "Test gauge metric"
        )
        
        assert gauge is not None
        assert metrics_manager.is_registered("test_gauge")
    
    def test_duplicate_metric_registration(self, metrics_manager):
        """Test handling of duplicate metric registration."""
        # Register metric first time
        counter1 = metrics_manager.register_counter("test_counter", "Test counter")
        
        # Register same metric again
        counter2 = metrics_manager.register_counter("test_counter", "Test counter")
        
        # Should return existing instance or dummy
        assert counter1 is not None
        assert counter2 is not None
        assert metrics_manager.is_registered("test_counter")
    
    @patch('ai_karen_engine.core.metrics_manager.logger')
    def test_prometheus_import_failure(self, mock_logger, metrics_manager):
        """Test handling when Prometheus is not available."""
        # Create manager without Prometheus
        manager = MetricsManager()
        manager._prometheus_available = False
        manager._setup_dummy_classes()
        
        counter = manager.register_counter("test_counter", "Test counter")
        
        # Should return dummy metric
        assert counter is not None
        # Dummy metric should have required methods
        assert hasattr(counter, 'labels')
        assert hasattr(counter, 'inc')
    
    def test_safe_metrics_context(self, metrics_manager):
        """Test safe metrics context manager."""
        with metrics_manager.safe_metrics_context() as manager:
            counter = manager.register_counter("test_counter", "Test counter")
            assert counter is not None
    
    def test_metrics_info(self, metrics_manager):
        """Test metrics information retrieval."""
        metrics_manager.register_counter("counter1", "Counter 1")
        metrics_manager.register_histogram("histogram1", "Histogram 1")
        
        info = metrics_manager.get_metrics_info()
        
        assert info["registered_count"] == 2
        assert "counter1" in info["registered_metrics"]
        assert "histogram1" in info["registered_metrics"]


class TestServiceInitializationIntegration:
    """Test integration of service initialization improvements."""
    
    @pytest.mark.asyncio
    async def test_initialize_services_function(self):
        """Test the initialize_services function."""
        with patch('ai_karen_engine.core.service_registry.get_service_registry') as mock_get_registry:
            mock_registry = Mock()
            mock_registry.initialize_all_services = AsyncMock(return_value={})
            mock_registry.get_initialization_report = Mock(return_value={
                'summary': {
                    'ready_services': 3,
                    'total_services': 5,
                    'degraded_services': 1,
                    'error_services': 1
                },
                'services': {}
            })
            mock_registry.start_health_monitoring = Mock()
            mock_get_registry.return_value = mock_registry
            
            await initialize_services()
            
            # Verify that services were registered and initialized
            assert mock_registry.register_service.call_count >= 5  # At least 5 services
            mock_registry.initialize_all_services.assert_called_once()
            mock_registry.start_health_monitoring.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_service_registry_singleton(self):
        """Test that service registry is a singleton."""
        registry1 = get_service_registry()
        registry2 = get_service_registry()
        
        assert registry1 is registry2
    
    def test_metrics_manager_singleton(self):
        """Test that metrics manager is a singleton."""
        manager1 = get_metrics_manager()
        manager2 = get_metrics_manager()
        
        assert manager1 is manager2
    
    @pytest.mark.asyncio
    async def test_dependency_resolution_order(self, service_registry):
        """Test that dependencies are resolved in correct order."""
        # Register services with complex dependency chain
        service_registry.register_service("base", MockService)
        service_registry.register_service("middle", MockService, {"base": True})
        service_registry.register_service("top", MockService, {"middle": True})
        
        # Initialize top service (should initialize all dependencies)
        await service_registry.get_service("top")
        
        # Check initialization order
        report = service_registry.get_initialization_report()
        order = report["summary"]["initialization_order"]
        
        # Base should be initialized before middle, middle before top
        base_idx = order.index("base")
        middle_idx = order.index("middle")
        top_idx = order.index("top")
        
        assert base_idx < middle_idx < top_idx
    
    @pytest.mark.asyncio
    async def test_circular_dependency_detection(self, service_registry):
        """Test handling of circular dependencies."""
        # This is a basic test - full circular dependency detection
        # would require more sophisticated dependency graph analysis
        service_registry.register_service("service_a", MockService, {"service_b": True})
        service_registry.register_service("service_b", MockService, {"service_a": True})
        
        # Should handle gracefully without infinite recursion
        try:
            await service_registry.get_service("service_a")
        except Exception as e:
            # Should not cause infinite recursion or stack overflow
            assert "recursion" not in str(e).lower()


if __name__ == "__main__":
    pytest.main([__file__])