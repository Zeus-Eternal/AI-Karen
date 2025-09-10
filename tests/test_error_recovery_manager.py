"""
Tests for Error Recovery Manager

Tests the circuit breaker pattern, fallback mechanisms, and automatic recovery
functionality of the error recovery manager.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

from src.ai_karen_engine.core.error_recovery_manager import (
    ErrorRecoveryManager, ServiceStatus, CircuitState, ServiceHealth,
    CircuitBreakerConfig, get_error_recovery_manager
)
from src.ai_karen_engine.config.performance_config import PerformanceConfig


class TestErrorRecoveryManager:
    """Test cases for ErrorRecoveryManager"""
    
    @pytest.fixture
    def config(self):
        """Create test configuration"""
        return PerformanceConfig()
    
    @pytest.fixture
    def error_manager(self, config):
        """Create error recovery manager instance"""
        return ErrorRecoveryManager(config)
    
    @pytest.fixture
    def mock_service_registry(self):
        """Mock service registry"""
        with patch('src.ai_karen_engine.core.error_recovery_manager.ServiceRegistry') as mock:
            registry_instance = Mock()
            mock.return_value = registry_instance
            yield registry_instance
    
    @pytest.fixture
    def mock_lifecycle_manager(self):
        """Mock service lifecycle manager"""
        with patch('src.ai_karen_engine.core.error_recovery_manager.ServiceLifecycleManager') as mock:
            manager_instance = Mock()
            manager_instance.restart_service = AsyncMock(return_value=True)
            mock.return_value = manager_instance
            yield manager_instance
    
    def test_service_registration(self, error_manager):
        """Test service registration for monitoring"""
        # Register essential service
        error_manager.register_service("auth_service", is_essential=True, fallback_available=True)
        
        assert "auth_service" in error_manager.service_health
        assert error_manager.service_health["auth_service"].is_essential
        assert error_manager.service_health["auth_service"].fallback_available
        assert "auth_service" in error_manager.essential_services
    
    def test_fallback_handler_registration(self, error_manager):
        """Test fallback handler registration"""
        async def mock_fallback():
            return {"status": "fallback_active"}
        
        error_manager.register_service("test_service")
        error_manager.register_fallback_handler("test_service", mock_fallback)
        
        assert "test_service" in error_manager.fallback_handlers
        assert error_manager.service_health["test_service"].fallback_available
    
    @pytest.mark.asyncio
    async def test_service_failure_handling(self, error_manager):
        """Test handling of service failures"""
        error_manager.register_service("test_service", is_essential=False)
        
        # Simulate service failure
        result = await error_manager.handle_service_failure(
            "test_service", 
            Exception("Service connection failed")
        )
        
        health = error_manager.service_health["test_service"]
        assert health.failure_count == 1
        assert health.last_failure is not None
        assert len(health.error_messages) == 1
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_opening(self, error_manager):
        """Test circuit breaker opening after threshold failures"""
        error_manager.register_service("test_service")
        
        # Simulate multiple failures to trigger circuit breaker
        for i in range(error_manager.circuit_config.failure_threshold):
            await error_manager.handle_service_failure(
                "test_service", 
                Exception(f"Failure {i+1}")
            )
        
        health = error_manager.service_health["test_service"]
        assert health.circuit_state == CircuitState.OPEN
        assert health.status == ServiceStatus.CIRCUIT_OPEN
        assert health.circuit_opened_at is not None
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_check(self, error_manager):
        """Test circuit breaker request filtering"""
        error_manager.register_service("test_service")
        
        # Initially should allow requests
        assert await error_manager.check_circuit_breaker("test_service") == True
        
        # Open circuit breaker
        health = error_manager.service_health["test_service"]
        health.circuit_state = CircuitState.OPEN
        health.circuit_opened_at = datetime.now()
        
        # Should block requests when circuit is open
        assert await error_manager.check_circuit_breaker("test_service") == False
    
    @pytest.mark.asyncio
    async def test_service_success_recording(self, error_manager):
        """Test recording of successful service calls"""
        error_manager.register_service("test_service")
        
        # Record some failures first
        health = error_manager.service_health["test_service"]
        health.failure_count = 3
        
        # Record success
        await error_manager.record_service_success("test_service")
        
        assert health.last_success is not None
        assert health.failure_count == 2  # Should decrease
    
    @pytest.mark.asyncio
    async def test_essential_service_recovery(self, error_manager, mock_lifecycle_manager, mock_service_registry):
        """Test automatic recovery attempts for essential services"""
        error_manager.register_service("auth_service", is_essential=True)
        
        # Mock service health check
        mock_service = Mock()
        mock_service.health_check = AsyncMock(return_value=True)
        mock_service_registry.get_service.return_value = mock_service
        
        # Simulate failure of essential service
        result = await error_manager.handle_service_failure(
            "auth_service", 
            Exception("Auth service down")
        )
        
        # Should attempt recovery for essential services
        assert result == True  # Should keep trying
        
        # Verify recovery attempt was made
        mock_lifecycle_manager.restart_service.assert_called_with("auth_service")
    
    @pytest.mark.asyncio
    async def test_optional_service_fallback(self, error_manager):
        """Test fallback activation for optional services"""
        async def mock_fallback():
            return {"status": "using_fallback"}
        
        error_manager.register_service("optional_service", is_essential=False, fallback_available=True)
        error_manager.register_fallback_handler("optional_service", mock_fallback)
        
        # Simulate failure
        result = await error_manager.handle_service_failure(
            "optional_service", 
            Exception("Service unavailable")
        )
        
        health = error_manager.service_health["optional_service"]
        assert health.status == ServiceStatus.DEGRADED
        assert result == True  # Should continue with fallback
    
    @pytest.mark.asyncio
    async def test_monitoring_lifecycle(self, error_manager):
        """Test monitoring start and stop"""
        assert not error_manager.monitoring_active
        
        # Start monitoring
        await error_manager.start_monitoring()
        assert error_manager.monitoring_active
        assert error_manager.monitoring_task is not None
        
        # Stop monitoring
        await error_manager.stop_monitoring()
        assert not error_manager.monitoring_active
    
    @pytest.mark.asyncio
    async def test_health_report_export(self, error_manager):
        """Test health report generation"""
        # Register and fail some services
        error_manager.register_service("service1", is_essential=True)
        error_manager.register_service("service2", is_essential=False)
        
        await error_manager.handle_service_failure("service1", Exception("Test failure"))
        
        # Export report
        report = await error_manager.export_health_report()
        
        assert "timestamp" in report
        assert "total_services" in report
        assert "essential_services" in report
        assert "services" in report
        assert "service1" in report["services"]
        assert "service2" in report["services"]
        
        service1_data = report["services"]["service1"]
        assert service1_data["status"] == ServiceStatus.FAILED.value
        assert service1_data["is_essential"] == True
        assert service1_data["failure_count"] == 1
    
    @pytest.mark.asyncio
    async def test_alert_handling(self, error_manager):
        """Test alert generation and handling"""
        alerts_received = []
        
        async def mock_alert_handler(alert_data):
            alerts_received.append(alert_data)
        
        error_manager.register_alert_handler(mock_alert_handler)
        
        # Trigger alert by opening circuit breaker
        error_manager.register_service("test_service", is_essential=True)
        
        # Cause multiple failures to open circuit
        for i in range(error_manager.circuit_config.failure_threshold):
            await error_manager.handle_service_failure(
                "test_service", 
                Exception(f"Failure {i+1}")
            )
        
        # Should have received alert
        assert len(alerts_received) > 0
        alert = alerts_received[-1]
        assert "Circuit breaker opened" in alert["message"]
        assert alert["severity"] == "critical"  # Essential service
    
    @pytest.mark.asyncio
    async def test_recovery_scheduling(self, error_manager):
        """Test automatic recovery scheduling"""
        error_manager.register_service("test_service")
        
        # Set short recovery timeout for testing
        error_manager.circuit_config.recovery_timeout = 1
        
        # Open circuit breaker
        health = error_manager.service_health["test_service"]
        health.circuit_state = CircuitState.OPEN
        health.circuit_opened_at = datetime.now()
        
        # Start recovery scheduling
        task = asyncio.create_task(error_manager._schedule_recovery_attempt("test_service"))
        
        # Wait for recovery timeout
        await asyncio.sleep(1.5)
        
        # Should transition to half-open
        assert health.circuit_state == CircuitState.HALF_OPEN
        assert health.status == ServiceStatus.RECOVERING
        
        # Clean up
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
    
    def test_global_instance(self):
        """Test global instance access"""
        manager1 = get_error_recovery_manager()
        manager2 = get_error_recovery_manager()
        
        # Should return same instance
        assert manager1 is manager2


class TestCircuitBreakerConfig:
    """Test circuit breaker configuration"""
    
    def test_default_config(self):
        """Test default circuit breaker configuration"""
        config = CircuitBreakerConfig()
        
        assert config.failure_threshold == 5
        assert config.recovery_timeout == 60
        assert config.half_open_max_calls == 3
        assert config.success_threshold == 2
    
    def test_custom_config(self):
        """Test custom circuit breaker configuration"""
        config = CircuitBreakerConfig(
            failure_threshold=3,
            recovery_timeout=30,
            half_open_max_calls=2,
            success_threshold=1
        )
        
        assert config.failure_threshold == 3
        assert config.recovery_timeout == 30
        assert config.half_open_max_calls == 2
        assert config.success_threshold == 1


class TestServiceHealth:
    """Test service health data structure"""
    
    def test_service_health_creation(self):
        """Test service health object creation"""
        health = ServiceHealth(
            service_name="test_service",
            is_essential=True,
            fallback_available=True
        )
        
        assert health.service_name == "test_service"
        assert health.status == ServiceStatus.HEALTHY
        assert health.failure_count == 0
        assert health.is_essential == True
        assert health.fallback_available == True
        assert health.circuit_state == CircuitState.CLOSED
    
    def test_error_message_tracking(self):
        """Test error message tracking in service health"""
        health = ServiceHealth("test_service")
        
        # Add error messages
        for i in range(15):  # More than the 10 message limit
            health.error_messages.append(f"Error {i+1}")
        
        # Should keep only last 10 messages when manually managed
        # (The actual truncation happens in ErrorRecoveryManager)
        assert len(health.error_messages) == 15  # Before truncation


@pytest.mark.asyncio
async def test_integration_with_performance_config():
    """Test integration with performance configuration"""
    config = PerformanceConfig()
    error_manager = ErrorRecoveryManager(config)
    
    # Should use config settings
    assert error_manager.config is config
    
    # Test service registration with config
    error_manager.register_service("configured_service")
    assert "configured_service" in error_manager.service_health


@pytest.mark.asyncio
async def test_concurrent_failure_handling():
    """Test handling of concurrent service failures"""
    error_manager = ErrorRecoveryManager()
    
    # Register multiple services
    services = ["service1", "service2", "service3"]
    for service in services:
        error_manager.register_service(service)
    
    # Simulate concurrent failures
    tasks = []
    for service in services:
        task = asyncio.create_task(
            error_manager.handle_service_failure(service, Exception(f"{service} failed"))
        )
        tasks.append(task)
    
    # Wait for all failures to be handled
    await asyncio.gather(*tasks)
    
    # All services should be marked as failed
    for service in services:
        health = error_manager.service_health[service]
        assert health.failure_count == 1
        assert health.last_failure is not None