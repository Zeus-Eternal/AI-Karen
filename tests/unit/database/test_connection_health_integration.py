"""
Integration Tests for Connection Health Management

Tests the complete connection health management system including:
- ConnectionHealthManager coordinating multiple services
- Redis and Database connection managers working together
- Graceful degradation and recovery scenarios
- End-to-end health monitoring and fallback behavior
"""

import asyncio
import pytest
import pytest_asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch

from src.ai_karen_engine.services.connection_health_manager import (
    ConnectionHealthManager,
    ServiceStatus,
    ConnectionType,
    RetryConfig,
    initialize_connection_health_manager,
    shutdown_connection_health_manager,
)
from src.ai_karen_engine.services.redis_connection_manager import (
    RedisConnectionManager,
    initialize_redis_manager,
    shutdown_redis_manager,
)
from src.ai_karen_engine.services.database_connection_manager import (
    DatabaseConnectionManager,
    initialize_database_manager,
    shutdown_database_manager,
)


class TestConnectionHealthIntegration:
    """Integration tests for connection health management system"""

    @pytest.fixture
    def retry_config(self):
        """Fast retry configuration for testing"""
        return RetryConfig(
            max_retries=2,
            base_delay=0.05,
            max_delay=0.2,
            exponential_base=2.0,
            jitter=False,
            circuit_breaker_threshold=2,
            circuit_breaker_timeout=1.0,
        )

    @pytest_asyncio.fixture
    async def health_manager(self, retry_config):
        """Initialize health manager for testing"""
        manager = await initialize_connection_health_manager(
            retry_config=retry_config,
            start_monitoring=False,  # Don't start background monitoring for tests
        )
        yield manager
        await shutdown_connection_health_manager()

    @pytest.fixture
    def mock_redis_available(self):
        """Mock Redis library availability"""
        with patch('src.ai_karen_engine.services.redis_connection_manager.REDIS_AVAILABLE', True):
            yield

    @pytest.fixture
    def mock_settings(self):
        """Mock database settings"""
        with patch('src.ai_karen_engine.services.database_connection_manager.settings') as mock:
            mock.database_url = "postgresql://test:test@localhost:5432/test_db"
            yield mock

    @pytest.mark.asyncio
    async def test_redis_manager_integration(self, health_manager, mock_redis_available):
        """Test Redis manager integration with health manager"""
        # Mock Redis components
        with patch('src.ai_karen_engine.services.redis_connection_manager.ConnectionPool') as MockPool, \
             patch('src.ai_karen_engine.services.redis_connection_manager.Redis') as MockRedis:
            
            mock_pool = MagicMock()
            mock_client = AsyncMock()
            mock_client.ping = AsyncMock(return_value=True)
            mock_client.get = AsyncMock(return_value="test_value")
            mock_client.set = AsyncMock(return_value=True)
            mock_client.close = AsyncMock()
            
            MockPool.from_url.return_value = mock_pool
            MockRedis.return_value = mock_client

            # Initialize Redis manager
            redis_manager = await initialize_redis_manager(
                redis_url="redis://localhost:6379/0",
                max_connections=5,
            )

            try:
                # Verify Redis service is registered with health manager
                assert "redis" in health_manager.health_status
                
                # Check initial health
                health_status = await health_manager.check_service_health("redis")
                assert health_status.status == ServiceStatus.HEALTHY

                # Test Redis operations work
                result = await redis_manager.get("test_key")
                assert result == "test_value"

                # Test degraded mode fallback
                mock_client.get.side_effect = Exception("Redis connection lost")
                result = await redis_manager.get("test_key")
                # Should fallback to memory cache (returns None for non-cached keys)
                assert result is None

                # Verify health manager detects the failure
                health_status = await health_manager.check_service_health("redis")
                assert health_status.status == ServiceStatus.UNAVAILABLE

            finally:
                await shutdown_redis_manager()

    @pytest.mark.asyncio
    async def test_database_manager_integration(self, health_manager, mock_settings):
        """Test Database manager integration with health manager"""
        # Mock SQLAlchemy components
        with patch('src.ai_karen_engine.services.database_connection_manager.create_engine') as mock_create_engine, \
             patch('src.ai_karen_engine.services.database_connection_manager.create_async_engine') as mock_create_async_engine, \
             patch('src.ai_karen_engine.services.database_connection_manager.sessionmaker') as mock_sessionmaker, \
             patch('src.ai_karen_engine.services.database_connection_manager.async_sessionmaker') as mock_async_sessionmaker:
            
            mock_engine = MagicMock()
            mock_async_engine = AsyncMock()
            mock_session_factory = MagicMock()
            mock_async_session_factory = MagicMock()
            mock_session = MagicMock()
            mock_async_session = AsyncMock()

            mock_create_engine.return_value = mock_engine
            mock_create_async_engine.return_value = mock_async_engine
            mock_sessionmaker.return_value = mock_session_factory
            mock_async_sessionmaker.return_value = mock_async_session_factory
            mock_session_factory.return_value = mock_session
            mock_async_session_factory.return_value.__aenter__ = AsyncMock(return_value=mock_async_session)
            mock_async_session_factory.return_value.__aexit__ = AsyncMock(return_value=None)

            # Initialize Database manager
            db_manager = await initialize_database_manager(
                database_url="postgresql://test:test@localhost:5432/test_db",
                pool_size=5,
            )

            try:
                # Verify Database service is registered with health manager
                assert "database" in health_manager.health_status
                
                # Check initial health
                health_status = await health_manager.check_service_health("database")
                assert health_status.status == ServiceStatus.HEALTHY

                # Test database operations work
                with db_manager.session_scope() as session:
                    session.execute("SELECT 1")

                # Test degraded mode fallback
                mock_session.execute.side_effect = Exception("Database connection lost")
                
                # Should still work in degraded mode (returns mock session)
                with db_manager.session_scope() as session:
                    # Mock session should handle operations gracefully
                    session.execute("SELECT 1")

            finally:
                await shutdown_database_manager()

    @pytest.mark.asyncio
    async def test_multiple_services_coordination(self, health_manager, mock_redis_available, mock_settings):
        """Test coordination of multiple services through health manager"""
        # Mock components for both services
        with patch('src.ai_karen_engine.services.redis_connection_manager.ConnectionPool') as MockRedisPool, \
             patch('src.ai_karen_engine.services.redis_connection_manager.Redis') as MockRedis, \
             patch('src.ai_karen_engine.services.database_connection_manager.create_engine') as mock_create_engine, \
             patch('src.ai_karen_engine.services.database_connection_manager.create_async_engine') as mock_create_async_engine, \
             patch('src.ai_karen_engine.services.database_connection_manager.sessionmaker') as mock_sessionmaker, \
             patch('src.ai_karen_engine.services.database_connection_manager.async_sessionmaker') as mock_async_sessionmaker:
            
            # Setup Redis mocks
            mock_redis_pool = MagicMock()
            mock_redis_client = AsyncMock()
            mock_redis_client.ping = AsyncMock(return_value=True)
            MockRedisPool.from_url.return_value = mock_redis_pool
            MockRedis.return_value = mock_redis_client

            # Setup Database mocks
            mock_engine = MagicMock()
            mock_async_engine = AsyncMock()
            mock_session_factory = MagicMock()
            mock_async_session_factory = MagicMock()
            mock_session = MagicMock()
            mock_async_session = AsyncMock()

            mock_create_engine.return_value = mock_engine
            mock_create_async_engine.return_value = mock_async_engine
            mock_sessionmaker.return_value = mock_session_factory
            mock_async_sessionmaker.return_value = mock_async_session_factory
            mock_session_factory.return_value = mock_session
            mock_async_session_factory.return_value.__aenter__ = AsyncMock(return_value=mock_async_session)
            mock_async_session_factory.return_value.__aexit__ = AsyncMock(return_value=None)

            # Initialize both managers
            redis_manager = await initialize_redis_manager()
            db_manager = await initialize_database_manager()

            try:
                # Wait a moment for registration to complete
                await asyncio.sleep(0.1)
                
                # Verify both services are registered
                all_statuses = health_manager.get_all_statuses()
                assert "redis" in all_statuses
                assert "database" in all_statuses

                # Check both services are healthy
                assert health_manager.is_service_healthy("redis")
                assert health_manager.is_service_healthy("database")

                # Simulate Redis failure
                mock_redis_client.ping.side_effect = Exception("Redis down")
                
                # Check Redis health - should fail
                redis_health = await health_manager.check_service_health("redis")
                assert redis_health.status == ServiceStatus.UNAVAILABLE

                # Database should still be healthy
                db_health = await health_manager.check_service_health("database")
                assert db_health.status == ServiceStatus.HEALTHY

                # Test service availability checks
                assert not health_manager.is_service_healthy("redis")
                assert health_manager.is_service_healthy("database")

                # Test degraded features
                redis_features = health_manager.get_degraded_features("redis")
                assert "caching" in redis_features
                assert "session_persistence" in redis_features

            finally:
                await shutdown_redis_manager()
                await shutdown_database_manager()

    @pytest.mark.asyncio
    async def test_circuit_breaker_behavior(self, health_manager, mock_redis_available):
        """Test circuit breaker behavior across service failures"""
        with patch('src.ai_karen_engine.services.redis_connection_manager.ConnectionPool') as MockPool, \
             patch('src.ai_karen_engine.services.redis_connection_manager.Redis') as MockRedis:
            
            mock_pool = MagicMock()
            mock_client = AsyncMock()
            # Make ping always fail to trigger circuit breaker
            mock_client.ping = AsyncMock(side_effect=Exception("Connection failed"))
            
            MockPool.from_url.return_value = mock_pool
            MockRedis.return_value = mock_client

            redis_manager = await initialize_redis_manager()

            try:
                # Trigger multiple failures to open circuit breaker
                for _ in range(3):
                    health_status = await health_manager.check_service_health("redis")
                    assert health_status.status == ServiceStatus.UNAVAILABLE

                # Circuit breaker should be open
                assert health_manager._is_circuit_breaker_open("redis")

                # Health checks should be skipped while circuit breaker is open
                health_status = await health_manager.check_service_health("redis")
                # Should return previous status without calling ping
                assert health_status.status == ServiceStatus.UNAVAILABLE

                # Wait for circuit breaker timeout
                await asyncio.sleep(1.1)  # Slightly longer than timeout

                # Circuit breaker should allow attempts again
                assert not health_manager._is_circuit_breaker_open("redis")

            finally:
                await shutdown_redis_manager()

    @pytest.mark.asyncio
    async def test_retry_with_exponential_backoff(self, health_manager, mock_redis_available):
        """Test retry behavior with exponential backoff"""
        with patch('src.ai_karen_engine.services.redis_connection_manager.ConnectionPool') as MockPool, \
             patch('src.ai_karen_engine.services.redis_connection_manager.Redis') as MockRedis:
            
            mock_pool = MagicMock()
            mock_client = AsyncMock()
            
            # Fail first two attempts, succeed on third
            call_count = 0
            def ping_side_effect():
                nonlocal call_count
                call_count += 1
                if call_count <= 2:
                    raise Exception("Connection failed")
                return True
            
            mock_client.ping = AsyncMock(side_effect=ping_side_effect)
            MockPool.from_url.return_value = mock_pool
            MockRedis.return_value = mock_client

            redis_manager = await initialize_redis_manager()

            try:
                # Test retry connection
                start_time = time.time()
                success = await health_manager.retry_connection("redis", max_retries=3)
                end_time = time.time()

                # Should succeed after retries
                assert success is True
                assert call_count == 3

                # Should have taken some time due to exponential backoff
                # With base_delay=0.05 and exponential_base=2.0:
                # Delay 1: 0.1s, Delay 2: 0.2s, Total: ~0.3s
                assert end_time - start_time >= 0.25  # Allow some tolerance

                # Service should be healthy after successful retry
                health_status = health_manager.get_service_status("redis")
                assert health_status.status == ServiceStatus.HEALTHY

            finally:
                await shutdown_redis_manager()

    @pytest.mark.asyncio
    async def test_degraded_mode_recovery_cycle(self, health_manager, mock_redis_available):
        """Test complete degraded mode and recovery cycle"""
        degraded_callback_called = False
        recovery_callback_called = False

        def degraded_callback(service_name):
            nonlocal degraded_callback_called
            degraded_callback_called = True

        def recovery_callback(service_name):
            nonlocal recovery_callback_called
            recovery_callback_called = True

        with patch('src.ai_karen_engine.services.redis_connection_manager.ConnectionPool') as MockPool, \
             patch('src.ai_karen_engine.services.redis_connection_manager.Redis') as MockRedis:
            
            mock_pool = MagicMock()
            mock_client = AsyncMock()
            mock_client.ping = AsyncMock(return_value=True)
            
            MockPool.from_url.return_value = mock_pool
            MockRedis.return_value = mock_client

            # Register additional callbacks
            health_manager.register_degraded_mode_callback("redis", degraded_callback)
            health_manager.register_recovery_callback("redis", recovery_callback)

            redis_manager = await initialize_redis_manager()

            try:
                # Initial state should be healthy
                assert health_manager.is_service_healthy("redis")
                assert not redis_manager.is_degraded()

                # Simulate service failure
                mock_client.ping.side_effect = Exception("Service down")
                
                # Check health - should trigger degraded mode
                health_status = await health_manager.check_service_health("redis")
                assert health_status.status == ServiceStatus.UNAVAILABLE
                assert degraded_callback_called

                # Redis manager should be in degraded mode
                assert redis_manager.is_degraded()

                # Test operations in degraded mode
                # SET should work (fallback to memory)
                result = await redis_manager.set("test_key", "test_value")
                assert result is True

                # GET should work (from memory cache)
                result = await redis_manager.get("test_key")
                assert result == "test_value"

                # Simulate service recovery
                mock_client.ping = AsyncMock(return_value=True)
                mock_client.ping.side_effect = None

                # Check health - should trigger recovery
                health_status = await health_manager.check_service_health("redis")
                assert health_status.status == ServiceStatus.HEALTHY
                assert recovery_callback_called

                # Redis manager should exit degraded mode
                assert not redis_manager.is_degraded()

            finally:
                await shutdown_redis_manager()

    @pytest.mark.asyncio
    async def test_background_monitoring(self, retry_config, mock_redis_available):
        """Test background health monitoring"""
        # Initialize health manager with monitoring enabled
        health_manager = await initialize_connection_health_manager(
            retry_config=retry_config,
            start_monitoring=True,
            check_interval=0.1,  # Very fast for testing
        )

        try:
            with patch('src.ai_karen_engine.services.redis_connection_manager.ConnectionPool') as MockPool, \
                 patch('src.ai_karen_engine.services.redis_connection_manager.Redis') as MockRedis:
                
                mock_pool = MagicMock()
                mock_client = AsyncMock()
                mock_client.ping = AsyncMock(return_value=True)
                
                MockPool.from_url.return_value = mock_pool
                MockRedis.return_value = mock_client

                redis_manager = await initialize_redis_manager()

                try:
                    # Wait for a few monitoring cycles
                    await asyncio.sleep(0.3)

                    # Verify monitoring is working (ping should be called multiple times)
                    assert mock_client.ping.call_count >= 2

                    # Simulate failure during monitoring
                    mock_client.ping.side_effect = Exception("Monitoring detected failure")

                    # Wait for monitoring to detect failure
                    await asyncio.sleep(0.2)

                    # Service should be marked as unavailable
                    health_status = health_manager.get_service_status("redis")
                    assert health_status.status == ServiceStatus.UNAVAILABLE

                finally:
                    await shutdown_redis_manager()

        finally:
            await shutdown_connection_health_manager()

    @pytest.mark.asyncio
    async def test_service_status_reporting(self, health_manager, mock_redis_available, mock_settings):
        """Test comprehensive service status reporting"""
        with patch('src.ai_karen_engine.services.redis_connection_manager.ConnectionPool') as MockRedisPool, \
             patch('src.ai_karen_engine.services.redis_connection_manager.Redis') as MockRedis, \
             patch('src.ai_karen_engine.services.database_connection_manager.create_engine') as mock_create_engine, \
             patch('src.ai_karen_engine.services.database_connection_manager.create_async_engine') as mock_create_async_engine, \
             patch('src.ai_karen_engine.services.database_connection_manager.sessionmaker') as mock_sessionmaker, \
             patch('src.ai_karen_engine.services.database_connection_manager.async_sessionmaker') as mock_async_sessionmaker:
            
            # Setup mocks
            mock_redis_pool = MagicMock()
            mock_redis_client = AsyncMock()
            mock_redis_client.ping = AsyncMock(return_value=True)
            MockRedisPool.from_url.return_value = mock_redis_pool
            MockRedis.return_value = mock_redis_client

            mock_engine = MagicMock()
            mock_async_engine = AsyncMock()
            mock_session_factory = MagicMock()
            mock_async_session_factory = MagicMock()
            mock_session = MagicMock()
            mock_async_session = AsyncMock()

            mock_create_engine.return_value = mock_engine
            mock_create_async_engine.return_value = mock_async_engine
            mock_sessionmaker.return_value = mock_session_factory
            mock_async_sessionmaker.return_value = mock_async_session_factory
            mock_session_factory.return_value = mock_session
            mock_async_session_factory.return_value.__aenter__ = AsyncMock(return_value=mock_async_session)
            mock_async_session_factory.return_value.__aexit__ = AsyncMock(return_value=None)

            # Initialize both services
            redis_manager = await initialize_redis_manager()
            db_manager = await initialize_database_manager()

            try:
                # Get comprehensive status report
                all_statuses = health_manager.get_all_statuses()
                
                # Verify both services are included
                assert len(all_statuses) == 2
                assert "redis" in all_statuses
                assert "database" in all_statuses

                # Check Redis status details
                redis_status = all_statuses["redis"]
                assert redis_status.service == "redis"
                assert redis_status.connection_type == ConnectionType.REDIS
                assert redis_status.status == ServiceStatus.HEALTHY

                # Check Database status details
                db_status = all_statuses["database"]
                assert db_status.service == "database"
                assert db_status.connection_type == ConnectionType.DATABASE
                assert db_status.status == ServiceStatus.HEALTHY

                # Test individual service info
                redis_info = redis_manager.get_connection_info()
                assert redis_info["redis_url"] == redis_manager.redis_url
                assert redis_info["degraded_mode"] is False

                db_info = db_manager.get_status_info()
                assert db_info["degraded_mode"] is False
                assert "pool_metrics" in db_info

            finally:
                await shutdown_redis_manager()
                await shutdown_database_manager()

    @pytest.mark.asyncio
    async def test_error_isolation(self, health_manager, mock_redis_available, mock_settings):
        """Test that errors in one service don't affect others"""
        with patch('src.ai_karen_engine.services.redis_connection_manager.ConnectionPool') as MockRedisPool, \
             patch('src.ai_karen_engine.services.redis_connection_manager.Redis') as MockRedis, \
             patch('src.ai_karen_engine.services.database_connection_manager.create_engine') as mock_create_engine, \
             patch('src.ai_karen_engine.services.database_connection_manager.create_async_engine') as mock_create_async_engine, \
             patch('src.ai_karen_engine.services.database_connection_manager.sessionmaker') as mock_sessionmaker, \
             patch('src.ai_karen_engine.services.database_connection_manager.async_sessionmaker') as mock_async_sessionmaker:
            
            # Setup Redis to fail
            mock_redis_pool = MagicMock()
            mock_redis_client = AsyncMock()
            mock_redis_client.ping = AsyncMock(side_effect=Exception("Redis completely down"))
            MockRedisPool.from_url.return_value = mock_redis_pool
            MockRedis.return_value = mock_redis_client

            # Setup Database to succeed
            mock_engine = MagicMock()
            mock_async_engine = AsyncMock()
            mock_session_factory = MagicMock()
            mock_async_session_factory = MagicMock()
            mock_session = MagicMock()
            mock_async_session = AsyncMock()

            mock_create_engine.return_value = mock_engine
            mock_create_async_engine.return_value = mock_async_engine
            mock_sessionmaker.return_value = mock_session_factory
            mock_async_sessionmaker.return_value = mock_async_session_factory
            mock_session_factory.return_value = mock_session
            mock_async_session_factory.return_value.__aenter__ = AsyncMock(return_value=mock_async_session)
            mock_async_session_factory.return_value.__aexit__ = AsyncMock(return_value=None)

            # Initialize both services
            redis_manager = await initialize_redis_manager()
            db_manager = await initialize_database_manager()

            try:
                # Check health of both services
                redis_health = await health_manager.check_service_health("redis")
                db_health = await health_manager.check_service_health("database")

                # Redis should fail, Database should succeed
                assert redis_health.status == ServiceStatus.UNAVAILABLE
                assert db_health.status == ServiceStatus.HEALTHY

                # Verify Redis is in degraded mode but Database is not
                assert redis_manager.is_degraded()
                assert not db_manager.is_degraded()

                # Database operations should still work normally
                with db_manager.session_scope() as session:
                    session.execute("SELECT 1")

                # Redis operations should fallback to memory cache
                result = await redis_manager.set("test", "value")
                assert result is True  # Should succeed via memory cache

                result = await redis_manager.get("test")
                assert result == "value"  # Should get from memory cache

            finally:
                await shutdown_redis_manager()
                await shutdown_database_manager()