"""
Unit tests for intelligent authentication base classes and interfaces.

Tests the abstract base classes, service registry, health monitoring,
and dependency injection components.
"""

import asyncio
import pytest
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

from src.ai_karen_engine.security.intelligent_auth_base import (
    ServiceStatus,
    ServiceHealthStatus,
    IntelligentAuthHealthStatus,
    BaseIntelligentAuthService,
    ServiceRegistry,
    HealthMonitor,
    get_service_registry,
    register_service,
    get_service
)
from src.ai_karen_engine.security.models import (
    IntelligentAuthConfig,
    AuthContext,
    AuthAnalysisResult,
    NLPFeatures,
    EmbeddingAnalysis,
    BehavioralAnalysis,
    ThreatAnalysis
)


class TestServiceHealthStatus:
    """Test ServiceHealthStatus data model."""

    def test_valid_health_status(self):
        """Test valid health status creation."""
        now = datetime.now()
        status = ServiceHealthStatus(
            service_name="test_service",
            status=ServiceStatus.HEALTHY,
            last_check=now,
            response_time=0.15,
            metadata={"version": "1.0.0"}
        )
        
        assert status.service_name == "test_service"
        assert status.status == ServiceStatus.HEALTHY
        assert status.response_time == 0.15
        assert status.metadata["version"] == "1.0.0"

    def test_health_status_serialization(self):
        """Test health status serialization."""
        now = datetime.now()
        status = ServiceHealthStatus(
            service_name="test_service",
            status=ServiceStatus.DEGRADED,
            last_check=now,
            response_time=0.25,
            error_message="Service degraded"
        )
        
        data = status.to_dict()
        
        assert data["service_name"] == "test_service"
        assert data["status"] == "degraded"
        assert data["response_time"] == 0.25
        assert data["error_message"] == "Service degraded"
        assert "last_check" in data


class TestIntelligentAuthHealthStatus:
    """Test IntelligentAuthHealthStatus data model."""

    def test_healthy_system_status(self):
        """Test healthy system status."""
        component1 = ServiceHealthStatus(
            service_name="service1",
            status=ServiceStatus.HEALTHY,
            last_check=datetime.now()
        )
        
        component2 = ServiceHealthStatus(
            service_name="service2", 
            status=ServiceStatus.HEALTHY,
            last_check=datetime.now()
        )
        
        health_status = IntelligentAuthHealthStatus(
            overall_status=ServiceStatus.HEALTHY,
            component_statuses={"service1": component1, "service2": component2},
            last_updated=datetime.now()
        )
        
        assert health_status.is_healthy()
        assert len(health_status.get_unhealthy_components()) == 0

    def test_unhealthy_system_status(self):
        """Test unhealthy system status."""
        component1 = ServiceHealthStatus(
            service_name="service1",
            status=ServiceStatus.HEALTHY,
            last_check=datetime.now()
        )
        
        component2 = ServiceHealthStatus(
            service_name="service2",
            status=ServiceStatus.UNHEALTHY,
            last_check=datetime.now(),
            error_message="Service failed"
        )
        
        health_status = IntelligentAuthHealthStatus(
            overall_status=ServiceStatus.UNHEALTHY,
            component_statuses={"service1": component1, "service2": component2},
            last_updated=datetime.now()
        )
        
        assert not health_status.is_healthy()
        unhealthy = health_status.get_unhealthy_components()
        assert len(unhealthy) == 1
        assert "service2" in unhealthy

    def test_health_status_serialization(self):
        """Test health status serialization."""
        component = ServiceHealthStatus(
            service_name="test_service",
            status=ServiceStatus.HEALTHY,
            last_check=datetime.now()
        )
        
        health_status = IntelligentAuthHealthStatus(
            overall_status=ServiceStatus.HEALTHY,
            component_statuses={"test_service": component},
            last_updated=datetime.now(),
            processing_metrics={"avg_response_time": 0.15}
        )
        
        data = health_status.to_dict()
        
        assert data["overall_status"] == "healthy"
        assert "test_service" in data["component_statuses"]
        assert data["processing_metrics"]["avg_response_time"] == 0.15


class MockIntelligentAuthService(BaseIntelligentAuthService):
    """Mock implementation of BaseIntelligentAuthService for testing."""

    def __init__(self, config: IntelligentAuthConfig, should_fail_health_check: bool = False):
        super().__init__(config)
        self.initialized = False
        self.should_fail_health_check = should_fail_health_check

    async def initialize(self) -> bool:
        """Mock initialization."""
        self.initialized = True
        return True

    async def shutdown(self) -> None:
        """Mock shutdown."""
        self.initialized = False

    async def _perform_health_check(self) -> bool:
        """Mock health check."""
        if self.should_fail_health_check:
            raise Exception("Mock health check failure")
        return self.initialized


class TestBaseIntelligentAuthService:
    """Test BaseIntelligentAuthService abstract base class."""

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return IntelligentAuthConfig()

    @pytest.fixture
    def service(self, config):
        """Create test service instance."""
        return MockIntelligentAuthService(config)

    @pytest.mark.asyncio
    async def test_service_initialization(self, service):
        """Test service initialization."""
        assert not service.initialized
        
        result = await service.initialize()
        
        assert result
        assert service.initialized

    @pytest.mark.asyncio
    async def test_service_shutdown(self, service):
        """Test service shutdown."""
        await service.initialize()
        assert service.initialized
        
        await service.shutdown()
        
        assert not service.initialized

    @pytest.mark.asyncio
    async def test_successful_health_check(self, service):
        """Test successful health check."""
        await service.initialize()
        
        status = await service.health_check()
        
        assert status.service_name == "MockIntelligentAuthService"
        assert status.status == ServiceStatus.HEALTHY
        assert status.response_time >= 0
        assert status.error_message is None

    @pytest.mark.asyncio
    async def test_failed_health_check(self, config):
        """Test failed health check."""
        service = MockIntelligentAuthService(config, should_fail_health_check=True)
        await service.initialize()
        
        status = await service.health_check()
        
        assert status.status == ServiceStatus.UNHEALTHY
        assert status.error_message is not None
        assert "Mock health check failure" in status.error_message

    @pytest.mark.asyncio
    async def test_config_update(self, service):
        """Test configuration update."""
        new_config = IntelligentAuthConfig(enable_nlp_analysis=False)
        
        result = await service.update_config(new_config)
        
        assert result
        assert not service.config.enable_nlp_analysis


class TestServiceRegistry:
    """Test ServiceRegistry functionality."""

    @pytest.fixture
    def registry(self):
        """Create test service registry."""
        return ServiceRegistry()

    @pytest.fixture
    def mock_service(self):
        """Create mock service."""
        service = Mock()
        service.initialize = AsyncMock(return_value=True)
        service.shutdown = AsyncMock()
        service.health_check = AsyncMock(return_value=ServiceHealthStatus(
            service_name="mock_service",
            status=ServiceStatus.HEALTHY,
            last_check=datetime.now()
        ))
        return service

    def test_service_registration(self, registry, mock_service):
        """Test service registration."""
        registry.register_service("test_service", mock_service)
        
        assert registry.has_service("test_service")
        assert registry.get_service("test_service") is mock_service
        assert "test_service" in registry.get_service_names()

    def test_service_retrieval(self, registry, mock_service):
        """Test service retrieval."""
        registry.register_service("test_service", mock_service)
        
        retrieved = registry.get_service("test_service")
        assert retrieved is mock_service
        
        # Test non-existent service
        assert registry.get_service("non_existent") is None
        assert not registry.has_service("non_existent")

    @pytest.mark.asyncio
    async def test_initialize_all_services(self, registry, mock_service):
        """Test initializing all services."""
        registry.register_service("test_service", mock_service)
        
        result = await registry.initialize_all()
        
        assert result
        mock_service.initialize.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialize_all_with_failure(self, registry):
        """Test initialization with service failure."""
        failing_service = Mock()
        failing_service.initialize = AsyncMock(return_value=False)
        
        registry.register_service("failing_service", failing_service)
        
        result = await registry.initialize_all()
        
        assert not result

    @pytest.mark.asyncio
    async def test_shutdown_all_services(self, registry, mock_service):
        """Test shutting down all services."""
        registry.register_service("test_service", mock_service)
        
        await registry.shutdown_all()
        
        mock_service.shutdown.assert_called_once()

    @pytest.mark.asyncio
    async def test_health_check_all_services(self, registry, mock_service):
        """Test health checking all services."""
        registry.register_service("test_service", mock_service)
        
        statuses = await registry.health_check_all()
        
        assert "test_service" in statuses
        assert statuses["test_service"].status == ServiceStatus.HEALTHY
        mock_service.health_check.assert_called_once()

    @pytest.mark.asyncio
    async def test_health_check_service_without_health_check(self, registry):
        """Test health check for service without health_check method."""
        service_without_health_check = Mock(spec=[])  # No health_check method
        registry.register_service("no_health_check", service_without_health_check)
        
        statuses = await registry.health_check_all()
        
        assert "no_health_check" in statuses
        assert statuses["no_health_check"].status == ServiceStatus.UNKNOWN

    def test_clear_registry(self, registry, mock_service):
        """Test clearing the registry."""
        registry.register_service("test_service", mock_service)
        assert registry.has_service("test_service")
        
        registry.clear()
        
        assert not registry.has_service("test_service")
        assert len(registry.get_service_names()) == 0


class TestHealthMonitor:
    """Test HealthMonitor functionality."""

    @pytest.fixture
    def registry(self):
        """Create test service registry."""
        return ServiceRegistry()

    @pytest.fixture
    def mock_service(self):
        """Create mock service for health monitoring."""
        service = Mock()
        service.health_check = AsyncMock(return_value=ServiceHealthStatus(
            service_name="mock_service",
            status=ServiceStatus.HEALTHY,
            last_check=datetime.now(),
            response_time=0.1
        ))
        return service

    @pytest.fixture
    def health_monitor(self, registry):
        """Create health monitor instance."""
        return HealthMonitor(registry, check_interval=0.1)  # Fast interval for testing

    @pytest.mark.asyncio
    async def test_start_stop_monitoring(self, health_monitor):
        """Test starting and stopping health monitoring."""
        assert not health_monitor._monitoring
        
        await health_monitor.start_monitoring()
        assert health_monitor._monitoring
        assert health_monitor._monitor_task is not None
        
        await health_monitor.stop_monitoring()
        assert not health_monitor._monitoring

    @pytest.mark.asyncio
    async def test_health_monitoring_loop(self, registry, mock_service, health_monitor):
        """Test health monitoring loop."""
        registry.register_service("test_service", mock_service)
        
        await health_monitor.start_monitoring()
        
        # Wait for at least one health check cycle
        await asyncio.sleep(0.2)
        
        await health_monitor.stop_monitoring()
        
        # Verify health check was called
        mock_service.health_check.assert_called()
        
        # Check health status
        current_status = health_monitor.get_current_health_status()
        assert current_status.overall_status == ServiceStatus.HEALTHY
        assert "test_service" in current_status.component_statuses

    @pytest.mark.asyncio
    async def test_health_history_tracking(self, registry, mock_service, health_monitor):
        """Test health history tracking."""
        registry.register_service("test_service", mock_service)
        
        # Manually perform health checks
        await health_monitor._perform_health_checks()
        await health_monitor._perform_health_checks()
        
        history = health_monitor.get_health_history("test_service")
        assert len(history) == 2
        
        # Test limited history
        limited_history = health_monitor.get_health_history("test_service", limit=1)
        assert len(limited_history) == 1

    @pytest.mark.asyncio
    async def test_unhealthy_service_logging(self, registry, health_monitor):
        """Test logging of unhealthy services."""
        unhealthy_service = Mock()
        unhealthy_service.health_check = AsyncMock(return_value=ServiceHealthStatus(
            service_name="unhealthy_service",
            status=ServiceStatus.UNHEALTHY,
            last_check=datetime.now(),
            error_message="Service is down"
        ))
        
        registry.register_service("unhealthy_service", unhealthy_service)
        
        with patch.object(health_monitor.logger, 'warning') as mock_warning:
            await health_monitor._perform_health_checks()
            
            mock_warning.assert_called()
            args = mock_warning.call_args[0][0]
            assert "unhealthy_service" in args
            assert "is unhealthy" in args


class TestGlobalServiceRegistry:
    """Test global service registry functions."""

    def test_global_registry_access(self):
        """Test global registry access."""
        registry = get_service_registry()
        assert isinstance(registry, ServiceRegistry)
        
        # Should return the same instance
        registry2 = get_service_registry()
        assert registry is registry2

    def test_global_service_registration(self):
        """Test global service registration."""
        mock_service = Mock()
        
        register_service("global_test_service", mock_service)
        
        retrieved = get_service("global_test_service")
        assert retrieved is mock_service
        
        # Clean up
        get_service_registry().clear()

    def test_global_service_retrieval_nonexistent(self):
        """Test retrieving non-existent service from global registry."""
        result = get_service("non_existent_service")
        assert result is None


if __name__ == "__main__":
    pytest.main([__file__])