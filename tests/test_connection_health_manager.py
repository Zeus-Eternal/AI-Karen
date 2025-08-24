"""
Tests for Connection Health Manager

Tests graceful connection handling, exponential backoff, degraded mode operation,
and connection pool management with proper cleanup.
"""

import asyncio
import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from src.ai_karen_engine.services.connection_health_manager import (
    ConnectionHealthManager,
    ServiceStatus,
    ConnectionType,
    HealthStatus,
    RetryConfig,
    get_connection_health_manager,
    initialize_connection_health_manager,
    shutdown_connection_health_manager,
)


class TestConnectionHealthManager:
    """Test ConnectionHealthManager functionality"""

    @pytest.fixture
    def retry_config(self):
        """Test retry configuration"""
        return RetryConfig(
            max_retries=3,
            base_delay=0.1,
            max_delay=1.0,
            exponential_base=2.0,
            jitter=False,  # Disable jitter for predictable tests
            circuit_breaker_threshold=2,
            circuit_breaker_timeout=5.0,
        )

    @pytest.fixture
    def health_manager(self, retry_config):
        """Create health manager for testing"""
        return ConnectionHealthManager(retry_config)

    @pytest.fixture
    def mock_health_check_success(self):
        """Mock health check that always succeeds"""
        return MagicMock(return_value=True)

    @pytest.fixture
    def mock_health_check_failure(self):
        """Mock health check that always fails"""
        def failing_check():
            raise Exception("Connection failed")
        return failing_check

    @pytest.fixture
    def mock_async_health_check_success(self):
        """Mock async health check that always succeeds"""
        return AsyncMock(return_value={"healthy": True, "response_time": 10.5})

    @pytest.fixture
    def mock_async_health_check_failure(self):
        """Mock async health check that always fails"""
        async def failing_check():
            raise Exception("Async connection failed")
        return failing_check

    def test_service_registration(self, health_manager, mock_health_check_success):
        """Test service registration"""
        # Register service
        health_manager.register_service(
            service_name="test_service",
            connection_type=ConnectionType.DATABASE,
            health_check_func=mock_health_check_success,
        )

        # Verify registration
        assert "test_service" in health_manager.health_status
        status = health_manager.health_status["test_service"]
        assert status.service == "test_service"
        assert status.connection_type == ConnectionType.DATABASE
        assert status.status == ServiceStatus.UNAVAILABLE  # Initial state

    def test_callback_registration(self, health_manager, mock_health_check_success):
        """Test callback registration"""
        degraded_callback = MagicMock()
        recovery_callback = MagicMock()

        health_manager.register_service(
            service_name="test_service",
            connection_type=ConnectionType.REDIS,
            health_check_func=mock_health_check_success,
            degraded_mode_callback=degraded_callback,
            recovery_callback=recovery_callback,
        )

        # Verify callbacks are registered
        assert "test_service" in health_manager.degraded_mode_callbacks
        assert degraded_callback in health_manager.degraded_mode_callbacks["test_service"]
        assert "test_service" in health_manager.recovery_callbacks
        assert recovery_callback in health_manager.recovery_callbacks["test_service"]

    @pytest.mark.asyncio
    async def test_successful_health_check(self, health_manager, mock_health_check_success):
        """Test successful health check"""
        health_manager.register_service(
            service_name="test_service",
            connection_type=ConnectionType.DATABASE,
            health_check_func=mock_health_check_success,
        )

        # Perform health check
        status = await health_manager.check_service_health("test_service")

        # Verify results
        assert status.status == ServiceStatus.HEALTHY
        assert status.error_message is None
        assert status.retry_count == 0
        assert status.response_time_ms is not None
        mock_health_check_success.assert_called_once()

    @pytest.mark.asyncio
    async def test_failed_health_check(self, health_manager, mock_health_check_failure):
        """Test failed health check"""
        health_manager.register_service(
            service_name="test_service",
            connection_type=ConnectionType.DATABASE,
            health_check_func=mock_health_check_failure,
        )

        # Perform health check
        status = await health_manager.check_service_health("test_service")

        # Verify results
        assert status.status == ServiceStatus.UNAVAILABLE
        assert status.error_message == "Connection failed"
        assert status.retry_count == 1
        assert status.next_retry is not None

    @pytest.mark.asyncio
    async def test_async_health_check(self, health_manager, mock_async_health_check_success):
        """Test async health check"""
        health_manager.register_service(
            service_name="test_service",
            connection_type=ConnectionType.REDIS,
            health_check_func=mock_async_health_check_success,
        )

        # Perform health check
        status = await health_manager.check_service_health("test_service")

        # Verify results
        assert status.status == ServiceStatus.HEALTHY
        assert status.metadata["response_time"] == 10.5
        mock_async_health_check_success.assert_called_once()

    @pytest.mark.asyncio
    async def test_retry_connection_success(self, health_manager):
        """Test successful connection retry"""
        call_count = 0
        
        def intermittent_check():
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise Exception("Connection failed")
            return True

        # Use higher circuit breaker threshold to prevent it from opening during test
        health_manager.retry_config.circuit_breaker_threshold = 10

        health_manager.register_service(
            service_name="test_service",
            connection_type=ConnectionType.DATABASE,
            health_check_func=intermittent_check,
        )

        # Retry connection
        success = await health_manager.retry_connection("test_service", max_retries=5)

        # Verify success
        assert success is True
        assert call_count == 3  # Failed twice, succeeded on third attempt

    @pytest.mark.asyncio
    async def test_retry_connection_failure(self, health_manager, mock_health_check_failure):
        """Test failed connection retry"""
        health_manager.register_service(
            service_name="test_service",
            connection_type=ConnectionType.DATABASE,
            health_check_func=mock_health_check_failure,
        )

        # Retry connection
        success = await health_manager.retry_connection("test_service", max_retries=2)

        # Verify failure
        assert success is False

    def test_exponential_backoff_calculation(self, health_manager):
        """Test exponential backoff delay calculation"""
        # Test delay calculation
        delay1 = health_manager._calculate_retry_delay(1)
        delay2 = health_manager._calculate_retry_delay(2)
        delay3 = health_manager._calculate_retry_delay(3)

        # Verify exponential increase
        assert delay1 == 0.2  # base_delay * exponential_base^1 = 0.1 * 2^1
        assert delay2 == 0.4  # base_delay * exponential_base^2 = 0.1 * 2^2
        assert delay3 == 0.8  # base_delay * exponential_base^3 = 0.1 * 2^3

    def test_max_delay_limit(self, health_manager):
        """Test maximum delay limit"""
        # Test with high attempt number
        delay = health_manager._calculate_retry_delay(10)
        
        # Should not exceed max_delay
        assert delay <= health_manager.retry_config.max_delay

    def test_circuit_breaker_logic(self, health_manager, mock_health_check_failure):
        """Test circuit breaker functionality"""
        health_manager.register_service(
            service_name="test_service",
            connection_type=ConnectionType.DATABASE,
            health_check_func=mock_health_check_failure,
        )

        # Record failures to trigger circuit breaker
        health_manager._record_failure("test_service")
        health_manager._record_failure("test_service")

        # Circuit breaker should be open
        assert health_manager._is_circuit_breaker_open("test_service") is True

    def test_circuit_breaker_reset(self, health_manager):
        """Test circuit breaker reset"""
        # Trigger circuit breaker
        health_manager._record_failure("test_service")
        health_manager._record_failure("test_service")
        assert health_manager._is_circuit_breaker_open("test_service") is True

        # Reset circuit breaker
        health_manager._reset_circuit_breaker("test_service")
        assert health_manager._is_circuit_breaker_open("test_service") is False

    def test_degraded_mode_management(self, health_manager):
        """Test degraded mode enable/disable"""
        health_manager.register_service(
            service_name="test_service",
            connection_type=ConnectionType.REDIS,
            health_check_func=MagicMock(),
        )

        # Enable degraded mode
        features = ["caching", "session_persistence"]
        health_manager.enable_degraded_mode("test_service", features)

        status = health_manager.get_service_status("test_service")
        assert status.status == ServiceStatus.DEGRADED
        assert status.degraded_features == features

        # Disable degraded mode
        health_manager.disable_degraded_mode("test_service")
        status = health_manager.get_service_status("test_service")
        assert status.status == ServiceStatus.HEALTHY
        assert status.degraded_features == []

    def test_service_availability_checks(self, health_manager):
        """Test service availability check methods"""
        health_manager.register_service(
            service_name="healthy_service",
            connection_type=ConnectionType.DATABASE,
            health_check_func=MagicMock(),
        )
        health_manager.register_service(
            service_name="degraded_service",
            connection_type=ConnectionType.REDIS,
            health_check_func=MagicMock(),
        )
        health_manager.register_service(
            service_name="unavailable_service",
            connection_type=ConnectionType.MILVUS,
            health_check_func=MagicMock(),
        )

        # Set different statuses
        health_manager.health_status["healthy_service"].status = ServiceStatus.HEALTHY
        health_manager.health_status["degraded_service"].status = ServiceStatus.DEGRADED
        health_manager.health_status["unavailable_service"].status = ServiceStatus.UNAVAILABLE

        # Test is_service_healthy
        assert health_manager.is_service_healthy("healthy_service") is True
        assert health_manager.is_service_healthy("degraded_service") is False
        assert health_manager.is_service_healthy("unavailable_service") is False

        # Test is_service_available
        assert health_manager.is_service_available("healthy_service") is True
        assert health_manager.is_service_available("degraded_service") is True
        assert health_manager.is_service_available("unavailable_service") is False

    def test_degraded_features_mapping(self, health_manager):
        """Test degraded features mapping for different connection types"""
        # Test Redis features
        redis_features = health_manager._get_degraded_features("redis_service")
        health_manager.register_service(
            service_name="redis_service",
            connection_type=ConnectionType.REDIS,
            health_check_func=MagicMock(),
        )
        redis_features = health_manager._get_degraded_features("redis_service")
        expected_redis = ["caching", "session_persistence", "rate_limiting"]
        assert redis_features == expected_redis

        # Test Database features
        health_manager.register_service(
            service_name="db_service",
            connection_type=ConnectionType.DATABASE,
            health_check_func=MagicMock(),
        )
        db_features = health_manager._get_degraded_features("db_service")
        expected_db = ["data_persistence", "user_management", "audit_logging"]
        assert db_features == expected_db

    @pytest.mark.asyncio
    async def test_status_change_callbacks(self, health_manager):
        """Test status change callback execution"""
        degraded_callback = AsyncMock()
        recovery_callback = AsyncMock()

        health_manager.register_service(
            service_name="test_service",
            connection_type=ConnectionType.DATABASE,
            health_check_func=MagicMock(return_value=True),
            degraded_mode_callback=degraded_callback,
            recovery_callback=recovery_callback,
        )

        # Simulate status change from healthy to unavailable
        await health_manager._handle_status_change(
            "test_service", ServiceStatus.HEALTHY, ServiceStatus.UNAVAILABLE
        )
        degraded_callback.assert_called_once_with("test_service")

        # Simulate status change from unavailable to healthy
        await health_manager._handle_status_change(
            "test_service", ServiceStatus.UNAVAILABLE, ServiceStatus.HEALTHY
        )
        recovery_callback.assert_called_once_with("test_service")

    @pytest.mark.asyncio
    async def test_connection_failure_handling(self, health_manager):
        """Test connection failure handling"""
        health_manager.register_service(
            service_name="test_service",
            connection_type=ConnectionType.DATABASE,
            health_check_func=MagicMock(),
        )

        # Handle connection failure
        error = Exception("Database connection lost")
        await health_manager.handle_connection_failure("test_service", error)

        # Verify status update
        status = health_manager.get_service_status("test_service")
        assert status.status == ServiceStatus.UNAVAILABLE
        assert status.error_message == "Database connection lost"
        assert status.retry_count == 1

    @pytest.mark.asyncio
    async def test_monitoring_loop(self, health_manager):
        """Test background monitoring loop"""
        health_check_mock = MagicMock(return_value=True)
        health_manager.register_service(
            service_name="test_service",
            connection_type=ConnectionType.DATABASE,
            health_check_func=health_check_mock,
        )

        # Start monitoring with short interval
        await health_manager.start_monitoring(check_interval=0.1)
        
        # Wait for a few checks
        await asyncio.sleep(0.3)
        
        # Stop monitoring
        await health_manager.stop_monitoring()

        # Verify health checks were called
        assert health_check_mock.call_count >= 2

    def test_get_all_statuses(self, health_manager):
        """Test getting all service statuses"""
        # Register multiple services
        for i in range(3):
            health_manager.register_service(
                service_name=f"service_{i}",
                connection_type=ConnectionType.DATABASE,
                health_check_func=MagicMock(),
            )

        # Get all statuses
        all_statuses = health_manager.get_all_statuses()
        
        # Verify all services are included
        assert len(all_statuses) == 3
        for i in range(3):
            assert f"service_{i}" in all_statuses
            assert isinstance(all_statuses[f"service_{i}"], HealthStatus)

    def test_get_degraded_features(self, health_manager):
        """Test getting degraded features for a service"""
        health_manager.register_service(
            service_name="test_service",
            connection_type=ConnectionType.REDIS,
            health_check_func=MagicMock(),
        )

        # Enable degraded mode with specific features
        features = ["caching", "rate_limiting"]
        health_manager.enable_degraded_mode("test_service", features)

        # Get degraded features
        degraded_features = health_manager.get_degraded_features("test_service")
        assert degraded_features == features

    @pytest.mark.asyncio
    async def test_global_manager_functions(self):
        """Test global manager functions"""
        # Test initialization
        manager = await initialize_connection_health_manager(
            retry_config=RetryConfig(max_retries=2),
            start_monitoring=False,
        )
        assert manager is not None

        # Test getting global instance
        global_manager = get_connection_health_manager()
        assert global_manager is manager

        # Test shutdown
        await shutdown_connection_health_manager()

    def test_error_handling_in_callbacks(self, health_manager):
        """Test error handling in callback execution"""
        def failing_callback(service_name):
            raise Exception("Callback failed")

        health_manager.register_service(
            service_name="test_service",
            connection_type=ConnectionType.DATABASE,
            health_check_func=MagicMock(),
            degraded_mode_callback=failing_callback,
        )

        # This should not raise an exception
        asyncio.run(health_manager._execute_degraded_mode_callbacks("test_service"))

    @pytest.mark.asyncio
    async def test_circuit_breaker_timeout(self, health_manager):
        """Test circuit breaker timeout functionality"""
        # Set very short timeout for testing
        health_manager.retry_config.circuit_breaker_timeout = 0.1

        # Trigger circuit breaker
        health_manager._record_failure("test_service")
        health_manager._record_failure("test_service")
        assert health_manager._is_circuit_breaker_open("test_service") is True

        # Wait for timeout
        await asyncio.sleep(0.2)

        # Circuit breaker should allow attempts again
        assert health_manager._is_circuit_breaker_open("test_service") is False

    def test_next_retry_calculation(self, health_manager):
        """Test next retry time calculation"""
        # Calculate next retry time
        next_retry = health_manager._calculate_next_retry(1)
        
        # Should be in the future
        assert next_retry > datetime.utcnow()
        
        # Should be approximately base_delay * exponential_base seconds from now
        expected_delay = health_manager.retry_config.base_delay * health_manager.retry_config.exponential_base
        expected_time = datetime.utcnow() + timedelta(seconds=expected_delay)
        
        # Allow some tolerance for execution time
        time_diff = abs((next_retry - expected_time).total_seconds())
        assert time_diff < 1.0  # Within 1 second tolerance