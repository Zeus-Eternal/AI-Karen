"""
Simple Integration Test for Connection Health Management

A focused test to verify the connection health management system works correctly.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.ai_karen_engine.services.connection_health_manager import (
    ConnectionHealthManager,
    ServiceStatus,
    ConnectionType,
    RetryConfig,
)


class TestConnectionHealthSimpleIntegration:
    """Simple integration tests for connection health management"""

    @pytest.mark.asyncio
    async def test_basic_health_management_flow(self):
        """Test basic health management flow with mock services"""
        # Create health manager
        retry_config = RetryConfig(
            max_retries=2,
            base_delay=0.05,
            circuit_breaker_threshold=3,
        )
        health_manager = ConnectionHealthManager(retry_config)

        # Mock health check functions
        redis_healthy = True
        db_healthy = True

        def redis_health_check():
            if redis_healthy:
                return {"healthy": True, "response_time": 5.0}
            else:
                raise Exception("Redis connection failed")

        async def db_health_check():
            if db_healthy:
                return True
            else:
                raise Exception("Database connection failed")

        # Register services
        health_manager.register_service(
            service_name="redis",
            connection_type=ConnectionType.REDIS,
            health_check_func=redis_health_check,
        )

        health_manager.register_service(
            service_name="database",
            connection_type=ConnectionType.DATABASE,
            health_check_func=db_health_check,
        )

        # Test initial health checks
        redis_status = await health_manager.check_service_health("redis")
        db_status = await health_manager.check_service_health("database")

        assert redis_status.status == ServiceStatus.HEALTHY
        assert db_status.status == ServiceStatus.HEALTHY
        assert redis_status.metadata["response_time"] == 5.0

        # Test service availability
        assert health_manager.is_service_healthy("redis")
        assert health_manager.is_service_healthy("database")
        assert health_manager.is_service_available("redis")
        assert health_manager.is_service_available("database")

        # Simulate Redis failure
        redis_healthy = False
        redis_status = await health_manager.check_service_health("redis")
        assert redis_status.status == ServiceStatus.UNAVAILABLE
        assert "Redis connection failed" in redis_status.error_message

        # Database should still be healthy
        db_status = await health_manager.check_service_health("database")
        assert db_status.status == ServiceStatus.HEALTHY

        # Test service availability after failure
        assert not health_manager.is_service_healthy("redis")
        assert health_manager.is_service_healthy("database")
        assert not health_manager.is_service_available("redis")
        assert health_manager.is_service_available("database")

        # Test degraded features
        redis_features = health_manager.get_degraded_features("redis")
        assert "caching" in redis_features
        assert "session_persistence" in redis_features

        # Test recovery
        redis_healthy = True
        redis_status = await health_manager.check_service_health("redis")
        assert redis_status.status == ServiceStatus.HEALTHY

        # Both services should be healthy again
        assert health_manager.is_service_healthy("redis")
        assert health_manager.is_service_healthy("database")

    @pytest.mark.asyncio
    async def test_retry_with_exponential_backoff(self):
        """Test retry mechanism with exponential backoff"""
        retry_config = RetryConfig(
            max_retries=3,
            base_delay=0.01,  # Very small for testing
            exponential_base=2.0,
            jitter=False,
            circuit_breaker_threshold=10,  # High threshold to avoid interference
        )
        health_manager = ConnectionHealthManager(retry_config)

        # Mock service that fails twice then succeeds
        call_count = 0
        def failing_health_check():
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise Exception("Service temporarily down")
            return True

        health_manager.register_service(
            service_name="test_service",
            connection_type=ConnectionType.DATABASE,
            health_check_func=failing_health_check,
        )

        # Test retry mechanism
        import time
        start_time = time.time()
        success = await health_manager.retry_connection("test_service", max_retries=3)
        end_time = time.time()

        # Should succeed after retries
        assert success is True
        assert call_count == 3

        # Should have taken some time due to exponential backoff
        # Expected delays: 0.02s, 0.04s = ~0.06s total
        assert end_time - start_time >= 0.05

        # Service should be healthy after successful retry
        status = health_manager.get_service_status("test_service")
        assert status.status == ServiceStatus.HEALTHY

    @pytest.mark.asyncio
    async def test_circuit_breaker_behavior(self):
        """Test circuit breaker functionality"""
        retry_config = RetryConfig(
            circuit_breaker_threshold=2,
            circuit_breaker_timeout=0.1,  # Short timeout for testing
        )
        health_manager = ConnectionHealthManager(retry_config)

        # Mock service that always fails
        def always_failing_health_check():
            raise Exception("Service permanently down")

        health_manager.register_service(
            service_name="failing_service",
            connection_type=ConnectionType.REDIS,
            health_check_func=always_failing_health_check,
        )

        # Trigger failures to open circuit breaker
        for _ in range(3):
            status = await health_manager.check_service_health("failing_service")
            assert status.status == ServiceStatus.UNAVAILABLE

        # Circuit breaker should be open
        assert health_manager._is_circuit_breaker_open("failing_service")

        # Health checks should be skipped while circuit breaker is open
        status = await health_manager.check_service_health("failing_service")
        assert status.status == ServiceStatus.UNAVAILABLE

        # Wait for circuit breaker timeout
        await asyncio.sleep(0.15)

        # Circuit breaker should allow attempts again
        assert not health_manager._is_circuit_breaker_open("failing_service")

    @pytest.mark.asyncio
    async def test_degraded_mode_callbacks(self):
        """Test degraded mode and recovery callbacks"""
        health_manager = ConnectionHealthManager()

        # Track callback executions
        degraded_called = False
        recovery_called = False

        def degraded_callback(service_name):
            nonlocal degraded_called
            degraded_called = True
            assert service_name == "test_service"

        async def recovery_callback(service_name):
            nonlocal recovery_called
            recovery_called = True
            assert service_name == "test_service"

        # Mock service
        service_healthy = True
        def health_check():
            return service_healthy

        health_manager.register_service(
            service_name="test_service",
            connection_type=ConnectionType.DATABASE,
            health_check_func=health_check,
            degraded_mode_callback=degraded_callback,
            recovery_callback=recovery_callback,
        )

        # Initial health check - should be healthy
        status = await health_manager.check_service_health("test_service")
        assert status.status == ServiceStatus.HEALTHY

        # Simulate service failure
        service_healthy = False
        status = await health_manager.check_service_health("test_service")
        assert status.status == ServiceStatus.UNAVAILABLE
        assert degraded_called

        # Simulate service recovery
        service_healthy = True
        status = await health_manager.check_service_health("test_service")
        assert status.status == ServiceStatus.HEALTHY
        assert recovery_called

    @pytest.mark.asyncio
    async def test_comprehensive_status_reporting(self):
        """Test comprehensive status reporting"""
        health_manager = ConnectionHealthManager()

        # Register multiple services
        services = ["redis", "database", "milvus"]
        for service in services:
            health_manager.register_service(
                service_name=service,
                connection_type=ConnectionType.REDIS if service == "redis" else ConnectionType.DATABASE,
                health_check_func=lambda: True,
            )

        # Check all services
        for service in services:
            status = await health_manager.check_service_health(service)
            assert status.status == ServiceStatus.HEALTHY

        # Get comprehensive status report
        all_statuses = health_manager.get_all_statuses()
        assert len(all_statuses) == 3

        for service in services:
            assert service in all_statuses
            status = all_statuses[service]
            assert status.service == service
            assert status.status == ServiceStatus.HEALTHY
            assert status.last_check is not None

        # Test individual service queries
        for service in services:
            assert health_manager.is_service_healthy(service)
            assert health_manager.is_service_available(service)
            status = health_manager.get_service_status(service)
            assert status is not None
            assert status.service == service

    @pytest.mark.asyncio
    async def test_error_isolation(self):
        """Test that errors in one service don't affect others"""
        health_manager = ConnectionHealthManager()

        # Register two services - one that fails, one that succeeds
        def failing_health_check():
            raise Exception("Service 1 failed")

        def working_health_check():
            return {"healthy": True, "info": "Service 2 working"}

        health_manager.register_service(
            service_name="failing_service",
            connection_type=ConnectionType.REDIS,
            health_check_func=failing_health_check,
        )

        health_manager.register_service(
            service_name="working_service",
            connection_type=ConnectionType.DATABASE,
            health_check_func=working_health_check,
        )

        # Check both services
        failing_status = await health_manager.check_service_health("failing_service")
        working_status = await health_manager.check_service_health("working_service")

        # Failing service should be unavailable
        assert failing_status.status == ServiceStatus.UNAVAILABLE
        assert "Service 1 failed" in failing_status.error_message

        # Working service should be healthy
        assert working_status.status == ServiceStatus.HEALTHY
        assert working_status.metadata["info"] == "Service 2 working"

        # Verify isolation
        assert not health_manager.is_service_healthy("failing_service")
        assert health_manager.is_service_healthy("working_service")

        # Get degraded features only for failing service
        failing_features = health_manager.get_degraded_features("failing_service")
        working_features = health_manager.get_degraded_features("working_service")

        assert len(failing_features) > 0  # Should have degraded features
        assert len(working_features) == 0  # Should have no degraded features