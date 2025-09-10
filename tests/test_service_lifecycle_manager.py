"""
Tests for Service Lifecycle Manager.

This module tests the service lifecycle management functionality including
startup optimization, idle detection, graceful shutdown, and service consolidation.
"""

import asyncio
import pytest
import time
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, List, Any

from src.ai_karen_engine.core.service_lifecycle_manager import (
    ServiceLifecycleManager, StartupMode, ConsolidationStrategy,
    ServiceMetrics, ConsolidationGroup, StartupSequence,
    ConsolidatedServiceWrapper
)
from src.ai_karen_engine.core.service_classification import (
    ServiceConfig, ServiceClassification, ResourceRequirements
)
from src.ai_karen_engine.core.classified_service_registry import (
    ClassifiedServiceRegistry, ServiceLifecycleState, ClassifiedServiceInfo
)
from src.ai_karen_engine.core.lazy_loading_controller import LazyLoadingController


class MockService:
    """Mock service for testing."""
    
    def __init__(self, name: str):
        self.name = name
        self.initialized = False
        self.shutdown_called = False
        self.cleanup_called = False
    
    async def initialize(self):
        self.initialized = True
    
    async def shutdown(self):
        self.shutdown_called = True
    
    async def cleanup(self):
        self.cleanup_called = True


@pytest.fixture
def mock_registry():
    """Create a mock classified service registry."""
    registry = Mock(spec=ClassifiedServiceRegistry)
    
    # Create mock services
    services = {
        "auth_service": ClassifiedServiceInfo(
            config=ServiceConfig(
                name="auth_service",
                classification=ServiceClassification.ESSENTIAL,
                startup_priority=10,
                dependencies=[],
                resource_requirements=ResourceRequirements(memory_mb=64),
                graceful_shutdown_timeout=5
            ),
            lifecycle_state=ServiceLifecycleState.NOT_LOADED
        ),
        "memory_service": ClassifiedServiceInfo(
            config=ServiceConfig(
                name="memory_service",
                classification=ServiceClassification.OPTIONAL,
                startup_priority=50,
                dependencies=["auth_service"],
                resource_requirements=ResourceRequirements(memory_mb=256),
                idle_timeout=300,
                graceful_shutdown_timeout=10
            ),
            lifecycle_state=ServiceLifecycleState.NOT_LOADED
        ),
        "analytics_service": ClassifiedServiceInfo(
            config=ServiceConfig(
                name="analytics_service",
                classification=ServiceClassification.BACKGROUND,
                startup_priority=200,
                dependencies=[],
                resource_requirements=ResourceRequirements(memory_mb=64),
                idle_timeout=1800,
                graceful_shutdown_timeout=5
            ),
            lifecycle_state=ServiceLifecycleState.NOT_LOADED
        )
    }
    
    registry.classified_services = services
    registry._instances = {}
    
    # Mock dependency analyzer
    mock_analyzer = Mock()
    mock_analyzer.get_startup_order.return_value = ["auth_service", "memory_service", "analytics_service"]
    mock_analyzer.get_shutdown_order.return_value = ["analytics_service", "memory_service", "auth_service"]
    mock_analyzer.get_consolidation_groups.return_value = {
        "analytics_group": ["analytics_service", "memory_service"]
    }
    registry.dependency_analyzer = mock_analyzer
    
    # Mock methods
    registry.load_service_on_demand = AsyncMock()
    registry._suspend_service = AsyncMock()
    
    return registry


@pytest.fixture
def mock_lazy_controller():
    """Create a mock lazy loading controller."""
    controller = Mock(spec=LazyLoadingController)
    controller.get_service = AsyncMock()
    controller.usage_patterns = {}
    return controller


@pytest.fixture
def lifecycle_manager(mock_registry, mock_lazy_controller):
    """Create a service lifecycle manager for testing."""
    return ServiceLifecycleManager(
        registry=mock_registry,
        lazy_controller=mock_lazy_controller,
        startup_mode=StartupMode.FAST_START,
        idle_timeout_seconds=300
    )


class TestServiceLifecycleManager:
    """Test cases for ServiceLifecycleManager."""
    
    def test_initialization(self, lifecycle_manager, mock_registry):
        """Test lifecycle manager initialization."""
        assert lifecycle_manager.registry == mock_registry
        assert lifecycle_manager.startup_mode == StartupMode.FAST_START
        assert lifecycle_manager.idle_timeout_seconds == 300
        assert lifecycle_manager.enable_consolidation is True
        
        # Check that service metrics were initialized
        assert "auth_service" in lifecycle_manager.service_metrics
        assert "memory_service" in lifecycle_manager.service_metrics
        assert "analytics_service" in lifecycle_manager.service_metrics
        
        # Check that startup sequences were calculated
        assert StartupMode.ESSENTIAL_ONLY in lifecycle_manager.startup_sequences
        assert StartupMode.FAST_START in lifecycle_manager.startup_sequences
    
    def test_get_services_for_startup_mode(self, lifecycle_manager):
        """Test service filtering by startup mode."""
        # Test essential only mode
        essential_services = lifecycle_manager._get_services_for_startup_mode(StartupMode.ESSENTIAL_ONLY)
        assert "auth_service" in essential_services
        assert "memory_service" not in essential_services
        assert "analytics_service" not in essential_services
        
        # Test fast start mode (essential + high priority optional)
        fast_start_services = lifecycle_manager._get_services_for_startup_mode(StartupMode.FAST_START)
        assert "auth_service" in fast_start_services
        assert "memory_service" in fast_start_services  # Priority 50 <= 50
        assert "analytics_service" not in fast_start_services  # Priority 200 > 50
        
        # Test normal mode (all enabled)
        normal_services = lifecycle_manager._get_services_for_startup_mode(StartupMode.NORMAL)
        assert len(normal_services) == 3  # All services are enabled by default
    
    def test_estimate_service_startup_time(self, lifecycle_manager):
        """Test service startup time estimation."""
        # Test essential service (should be faster)
        auth_time = lifecycle_manager._estimate_service_startup_time("auth_service")
        assert auth_time > 0
        
        # Test optional service (should be slower than essential)
        memory_time = lifecycle_manager._estimate_service_startup_time("memory_service")
        assert memory_time > auth_time  # Optional services take longer
        
        # Test service with dependencies (should take longer)
        assert memory_time > auth_time  # memory_service has dependencies
    
    def test_optimize_startup_sequence(self, lifecycle_manager, mock_registry):
        """Test startup sequence optimization."""
        services = ["auth_service", "memory_service"]
        analyzer = mock_registry.dependency_analyzer
        
        sequence = lifecycle_manager._optimize_startup_sequence(services, analyzer)
        
        assert isinstance(sequence, StartupSequence)
        assert sequence.services == ["auth_service", "memory_service"]
        assert sequence.estimated_time_seconds > 0
        assert len(sequence.parallel_groups) > 0
        assert len(sequence.critical_path) > 0
    
    def test_find_critical_path(self, lifecycle_manager):
        """Test critical path identification."""
        services = ["auth_service", "memory_service"]
        analyzer = Mock()
        
        critical_path = lifecycle_manager._find_critical_path(services, analyzer)
        
        assert isinstance(critical_path, list)
        # Critical path should include services with dependencies
        assert len(critical_path) >= 1
    
    @pytest.mark.asyncio
    async def test_start_essential_services(self, lifecycle_manager, mock_registry):
        """Test starting essential services only."""
        # Mock the service starting
        async def mock_start_service(service_name):
            mock_registry._instances[service_name] = MockService(service_name)
            return "ready"
        
        lifecycle_manager._start_single_service = AsyncMock(side_effect=mock_start_service)
        
        with patch.object(lifecycle_manager, '_start_monitoring_tasks', new_callable=AsyncMock):
            results = await lifecycle_manager.start_essential_services()
        
        # Should only start essential services
        assert "auth_service" in results
        assert results["auth_service"] == "ready"
        
        # Check that startup time was tracked
        assert lifecycle_manager.performance_metrics["startup_time_saved_seconds"] >= 0
    
    @pytest.mark.asyncio
    async def test_start_services_by_mode(self, lifecycle_manager):
        """Test starting services by different modes."""
        lifecycle_manager._start_single_service = AsyncMock(return_value="ready")
        
        with patch.object(lifecycle_manager, '_start_monitoring_tasks', new_callable=AsyncMock):
            # Test fast start mode
            results = await lifecycle_manager.start_services_by_mode(StartupMode.FAST_START)
        
        # Should start essential and high-priority optional services
        assert "auth_service" in results
        assert "memory_service" in results
        assert results["auth_service"] == "ready"
        assert results["memory_service"] == "ready"
    
    @pytest.mark.asyncio
    async def test_start_single_service(self, lifecycle_manager, mock_lazy_controller):
        """Test starting a single service."""
        service_name = "auth_service"
        mock_service = MockService(service_name)
        mock_lazy_controller.get_service.return_value = mock_service
        
        result = await lifecycle_manager._start_single_service(service_name)
        
        assert result == "ready"
        mock_lazy_controller.get_service.assert_called_once_with(service_name)
        
        # Check metrics were updated
        metrics = lifecycle_manager.service_metrics[service_name]
        assert metrics.startup_time > 0
        assert metrics.last_accessed is not None
    
    @pytest.mark.asyncio
    async def test_detect_idle_services(self, lifecycle_manager, mock_registry):
        """Test idle service detection."""
        # Set up services with different access times
        current_time = time.time()
        
        # Make memory_service appear idle
        mock_registry.classified_services["memory_service"].lifecycle_state = ServiceLifecycleState.ACTIVE
        lifecycle_manager.service_metrics["memory_service"].last_accessed = current_time - 400  # 400 seconds ago
        
        # Make auth_service appear active (essential services are skipped anyway)
        mock_registry.classified_services["auth_service"].lifecycle_state = ServiceLifecycleState.ACTIVE
        lifecycle_manager.service_metrics["auth_service"].last_accessed = current_time - 100  # 100 seconds ago
        
        idle_services = await lifecycle_manager.detect_idle_services()
        
        # memory_service should be detected as idle (400s > 300s timeout)
        assert "memory_service" in idle_services
        # auth_service should not be detected (essential service)
        assert "auth_service" not in idle_services
    
    @pytest.mark.asyncio
    async def test_suspend_idle_services(self, lifecycle_manager, mock_registry):
        """Test suspending idle services."""
        # Mock detect_idle_services to return specific services
        lifecycle_manager.detect_idle_services = AsyncMock(return_value=["memory_service"])
        
        suspended_services = await lifecycle_manager.suspend_idle_services()
        
        assert "memory_service" in suspended_services
        mock_registry._suspend_service.assert_called_once_with("memory_service")
        assert lifecycle_manager.performance_metrics["services_suspended"] == 1
    
    @pytest.mark.asyncio
    async def test_shutdown_service_gracefully(self, lifecycle_manager, mock_registry):
        """Test graceful service shutdown."""
        service_name = "memory_service"
        mock_service = MockService(service_name)
        mock_registry._instances[service_name] = mock_service
        
        success = await lifecycle_manager.shutdown_service_gracefully(service_name, timeout_seconds=5)
        
        assert success is True
        assert mock_service.shutdown_called is True
        assert service_name not in mock_registry._instances
        assert lifecycle_manager.performance_metrics["graceful_shutdowns"] == 1
    
    @pytest.mark.asyncio
    async def test_shutdown_service_timeout(self, lifecycle_manager, mock_registry):
        """Test service shutdown with timeout."""
        service_name = "memory_service"
        
        # Create a service that takes too long to shutdown
        class SlowShutdownService:
            async def shutdown(self):
                await asyncio.sleep(10)  # Takes longer than timeout
        
        mock_registry._instances[service_name] = SlowShutdownService()
        
        # Mock force shutdown
        lifecycle_manager._force_shutdown_service = AsyncMock(return_value=True)
        
        success = await lifecycle_manager.shutdown_service_gracefully(service_name, timeout_seconds=1)
        
        assert success is True
        lifecycle_manager._force_shutdown_service.assert_called_once_with(service_name)
    
    def test_identify_consolidation_opportunities(self, lifecycle_manager, mock_registry):
        """Test identification of service consolidation opportunities."""
        opportunities = lifecycle_manager.identify_consolidation_opportunities()
        
        # Should find the consolidation group from the analyzer
        assert "analytics_group" in opportunities
        group = opportunities["analytics_group"]
        assert isinstance(group, ConsolidationGroup)
        assert "analytics_service" in group.services
        assert "memory_service" in group.services
        assert group.estimated_memory_savings_mb > 0
    
    def test_identify_memory_based_consolidation(self, lifecycle_manager):
        """Test memory-based consolidation identification."""
        opportunities = {}
        lifecycle_manager._identify_memory_based_consolidation(opportunities)
        
        # Should create consolidation opportunities based on memory usage
        # (This depends on the specific memory requirements of test services)
        assert isinstance(opportunities, dict)
    
    def test_identify_dependency_based_consolidation(self, lifecycle_manager, mock_lazy_controller):
        """Test dependency-based consolidation identification."""
        # Mock usage patterns
        from src.ai_karen_engine.core.lazy_loading_controller import UsagePattern
        
        mock_lazy_controller.usage_patterns = {
            "memory_service": UsagePattern(
                service_name="memory_service",
                common_co_accessed_services={"analytics_service", "auth_service"}
            )
        }
        
        opportunities = {}
        lifecycle_manager._identify_dependency_based_consolidation(opportunities)
        
        # Should create consolidation opportunities based on co-usage
        assert isinstance(opportunities, dict)
    
    @pytest.mark.asyncio
    async def test_consolidate_services(self, lifecycle_manager):
        """Test service consolidation."""
        group = ConsolidationGroup(
            name="test_group",
            services=["memory_service", "analytics_service"],
            strategy=ConsolidationStrategy.FUNCTIONAL,
            estimated_memory_savings_mb=100.0
        )
        
        # Mock the consolidated wrapper
        with patch('src.ai_karen_engine.core.service_lifecycle_manager.ConsolidatedServiceWrapper') as mock_wrapper:
            mock_instance = AsyncMock()
            mock_wrapper.return_value = mock_instance
            
            success = await lifecycle_manager.consolidate_services(group)
        
        assert success is True
        assert group.active is True
        assert lifecycle_manager.performance_metrics["services_consolidated"] == 2
        assert lifecycle_manager.performance_metrics["memory_saved_mb"] == 100.0
    
    @pytest.mark.asyncio
    async def test_shutdown_all_services(self, lifecycle_manager, mock_registry):
        """Test shutting down all services."""
        # Set up some active services
        mock_registry._instances = {
            "auth_service": MockService("auth_service"),
            "memory_service": MockService("memory_service")
        }
        
        lifecycle_manager.shutdown_service_gracefully = AsyncMock(return_value=True)
        
        results = await lifecycle_manager.shutdown_all_services(timeout_seconds=10)
        
        assert "auth_service" in results
        assert "memory_service" in results
        assert results["auth_service"] is True
        assert results["memory_service"] is True
        assert lifecycle_manager.shutdown_in_progress is True
    
    def test_get_lifecycle_report(self, lifecycle_manager):
        """Test lifecycle report generation."""
        report = lifecycle_manager.get_lifecycle_report()
        
        assert "startup_mode" in report
        assert "total_services" in report
        assert "performance_metrics" in report
        assert "startup_sequences" in report
        assert "service_metrics" in report
        
        assert report["startup_mode"] == StartupMode.FAST_START.value
        assert report["total_services"] == 3
        assert isinstance(report["performance_metrics"], dict)


class TestConsolidatedServiceWrapper:
    """Test cases for ConsolidatedServiceWrapper."""
    
    @pytest.fixture
    def mock_registry(self):
        """Create a mock registry for wrapper testing."""
        registry = Mock()
        registry.load_service_on_demand = AsyncMock()
        return registry
    
    @pytest.fixture
    def wrapper(self, mock_registry):
        """Create a consolidated service wrapper for testing."""
        return ConsolidatedServiceWrapper(
            group_name="test_group",
            service_names=["service1", "service2"],
            registry=mock_registry
        )
    
    def test_wrapper_initialization(self, wrapper):
        """Test wrapper initialization."""
        assert wrapper.group_name == "test_group"
        assert wrapper.service_names == ["service1", "service2"]
        assert wrapper.initialized is False
        assert len(wrapper.service_instances) == 0
    
    @pytest.mark.asyncio
    async def test_wrapper_initialize(self, wrapper, mock_registry):
        """Test wrapper service initialization."""
        # Mock service instances
        mock_service1 = MockService("service1")
        mock_service2 = MockService("service2")
        
        mock_registry.load_service_on_demand.side_effect = [mock_service1, mock_service2]
        
        await wrapper.initialize()
        
        assert wrapper.initialized is True
        assert len(wrapper.service_instances) == 2
        assert wrapper.service_instances["service1"] == mock_service1
        assert wrapper.service_instances["service2"] == mock_service2
    
    def test_wrapper_get_service(self, wrapper):
        """Test getting service from wrapper."""
        # Set up initialized wrapper
        wrapper.initialized = True
        mock_service = MockService("service1")
        wrapper.service_instances["service1"] = mock_service
        
        result = wrapper.get_service("service1")
        assert result == mock_service
        
        # Test error cases
        with pytest.raises(RuntimeError):
            wrapper.initialized = False
            wrapper.get_service("service1")
        
        wrapper.initialized = True
        with pytest.raises(ValueError):
            wrapper.get_service("nonexistent_service")
    
    @pytest.mark.asyncio
    async def test_wrapper_shutdown(self, wrapper):
        """Test wrapper shutdown."""
        # Set up services
        wrapper.initialized = True
        mock_service1 = MockService("service1")
        mock_service2 = MockService("service2")
        wrapper.service_instances = {
            "service1": mock_service1,
            "service2": mock_service2
        }
        
        await wrapper.shutdown()
        
        assert mock_service1.shutdown_called is True
        assert mock_service2.shutdown_called is True
        assert len(wrapper.service_instances) == 0
        assert wrapper.initialized is False


class TestStartupSequence:
    """Test cases for StartupSequence data class."""
    
    def test_startup_sequence_creation(self):
        """Test StartupSequence creation and properties."""
        sequence = StartupSequence(
            services=["service1", "service2"],
            estimated_time_seconds=5.0,
            parallel_groups=[["service1"], ["service2"]],
            critical_path=["service1", "service2"]
        )
        
        assert sequence.services == ["service1", "service2"]
        assert sequence.estimated_time_seconds == 5.0
        assert len(sequence.parallel_groups) == 2
        assert sequence.critical_path == ["service1", "service2"]


class TestServiceMetrics:
    """Test cases for ServiceMetrics data class."""
    
    def test_service_metrics_creation(self):
        """Test ServiceMetrics creation and default values."""
        metrics = ServiceMetrics()
        
        assert metrics.startup_time == 0.0
        assert metrics.memory_usage_mb == 0.0
        assert metrics.cpu_usage_percent == 0.0
        assert metrics.last_accessed is None
        assert metrics.access_count == 0
        assert metrics.idle_time == 0.0
        assert metrics.suspension_count == 0
        assert metrics.consolidation_savings_mb == 0.0
    
    def test_service_metrics_with_values(self):
        """Test ServiceMetrics with custom values."""
        current_time = time.time()
        metrics = ServiceMetrics(
            startup_time=2.5,
            memory_usage_mb=128.0,
            cpu_usage_percent=15.5,
            last_accessed=current_time,
            access_count=10,
            idle_time=300.0,
            suspension_count=2,
            consolidation_savings_mb=64.0
        )
        
        assert metrics.startup_time == 2.5
        assert metrics.memory_usage_mb == 128.0
        assert metrics.cpu_usage_percent == 15.5
        assert metrics.last_accessed == current_time
        assert metrics.access_count == 10
        assert metrics.idle_time == 300.0
        assert metrics.suspension_count == 2
        assert metrics.consolidation_savings_mb == 64.0


if __name__ == "__main__":
    pytest.main([__file__])