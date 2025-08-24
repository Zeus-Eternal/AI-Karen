"""
Tests for Redis Connection Manager

Tests Redis connection handling with graceful degradation, memory cache fallback,
connection pooling, and health monitoring integration.
"""

import asyncio
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from src.ai_karen_engine.services.redis_connection_manager import (
    RedisConnectionManager,
    get_redis_manager,
    initialize_redis_manager,
    shutdown_redis_manager,
)


class TestRedisConnectionManager:
    """Test RedisConnectionManager functionality"""

    @pytest.fixture
    def mock_redis_available(self):
        """Mock Redis library availability"""
        with patch('src.ai_karen_engine.services.redis_connection_manager.REDIS_AVAILABLE', True):
            yield

    @pytest.fixture
    def mock_redis_unavailable(self):
        """Mock Redis library unavailability"""
        with patch('src.ai_karen_engine.services.redis_connection_manager.REDIS_AVAILABLE', False):
            yield

    @pytest.fixture
    def mock_connection_pool(self):
        """Mock Redis connection pool"""
        pool = MagicMock()
        pool.created_connections = 5
        pool._available_connections = [MagicMock() for _ in range(3)]
        pool._in_use_connections = [MagicMock() for _ in range(2)]
        return pool

    @pytest.fixture
    def mock_redis_client(self):
        """Mock Redis client"""
        client = AsyncMock()
        client.ping = AsyncMock(return_value=True)
        client.get = AsyncMock(return_value="test_value")
        client.set = AsyncMock(return_value=True)
        client.delete = AsyncMock(return_value=1)
        client.exists = AsyncMock(return_value=1)
        client.expire = AsyncMock(return_value=True)
        client.hget = AsyncMock(return_value="hash_value")
        client.hset = AsyncMock(return_value=1)
        client.close = AsyncMock()
        return client

    @pytest.fixture
    def redis_manager(self, mock_redis_available):
        """Create Redis manager for testing"""
        return RedisConnectionManager(
            redis_url="redis://localhost:6379/0",
            max_connections=5,
            health_check_interval=10,
        )

    @pytest.mark.asyncio
    async def test_initialization_success(self, redis_manager, mock_connection_pool, mock_redis_client):
        """Test successful Redis initialization"""
        with patch.object(redis_manager, '_create_connection_pool') as mock_create_pool, \
             patch.object(redis_manager, '_create_client') as mock_create_client, \
             patch.object(redis_manager, '_test_connection', return_value=True) as mock_test:
            
            redis_manager._pool = mock_connection_pool
            redis_manager._client = mock_redis_client

            result = await redis_manager.initialize()

            assert result is True
            assert redis_manager._degraded_mode is False
            assert redis_manager._connection_failures == 0
            mock_create_pool.assert_called_once()
            mock_create_client.assert_called_once()
            mock_test.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialization_failure(self, redis_manager):
        """Test Redis initialization failure"""
        with patch.object(redis_manager, '_create_connection_pool', side_effect=Exception("Connection failed")):
            result = await redis_manager.initialize()

            assert result is False
            assert redis_manager._degraded_mode is True

    @pytest.mark.asyncio
    async def test_initialization_without_redis_library(self, mock_redis_unavailable):
        """Test initialization when Redis library is not available"""
        manager = RedisConnectionManager()
        result = await manager.initialize()

        assert result is False
        assert manager._degraded_mode is True

    @pytest.mark.asyncio
    async def test_health_check_success(self, redis_manager, mock_redis_client):
        """Test successful health check"""
        redis_manager._client = mock_redis_client
        redis_manager._degraded_mode = False

        result = await redis_manager._health_check()

        assert result["healthy"] is True
        assert "response_time_ms" in result
        assert result["degraded_mode"] is False
        mock_redis_client.ping.assert_called_once()

    @pytest.mark.asyncio
    async def test_health_check_failure(self, redis_manager, mock_redis_client):
        """Test failed health check"""
        mock_redis_client.ping.side_effect = Exception("Connection lost")
        redis_manager._client = mock_redis_client
        redis_manager._degraded_mode = False

        result = await redis_manager._health_check()

        assert result["healthy"] is False
        assert "error" in result
        assert result["connection_failures"] > 0

    @pytest.mark.asyncio
    async def test_health_check_degraded_mode(self, redis_manager):
        """Test health check in degraded mode"""
        redis_manager._degraded_mode = True

        result = await redis_manager._health_check()

        assert result["healthy"] is False
        assert result["degraded_mode"] is True

    @pytest.mark.asyncio
    async def test_get_operation_success(self, redis_manager, mock_redis_client):
        """Test successful GET operation"""
        redis_manager._client = mock_redis_client
        redis_manager._degraded_mode = False

        result = await redis_manager.get("test_key")

        assert result == "test_value"
        mock_redis_client.get.assert_called_once_with("test_key")

    @pytest.mark.asyncio
    async def test_get_operation_fallback(self, redis_manager, mock_redis_client):
        """Test GET operation fallback to memory cache"""
        mock_redis_client.get.side_effect = Exception("Redis unavailable")
        redis_manager._client = mock_redis_client
        redis_manager._degraded_mode = False

        # Pre-populate memory cache
        redis_manager._set_in_memory_cache("test_key", "cached_value")

        result = await redis_manager.get("test_key")

        assert result == "cached_value"

    @pytest.mark.asyncio
    async def test_get_operation_degraded_mode(self, redis_manager):
        """Test GET operation in degraded mode"""
        redis_manager._degraded_mode = True
        redis_manager._set_in_memory_cache("test_key", "memory_value")

        result = await redis_manager.get("test_key")

        assert result == "memory_value"

    @pytest.mark.asyncio
    async def test_set_operation_success(self, redis_manager, mock_redis_client):
        """Test successful SET operation"""
        redis_manager._client = mock_redis_client
        redis_manager._degraded_mode = False

        result = await redis_manager.set("test_key", "test_value", ex=300)

        assert result is True
        mock_redis_client.set.assert_called_once_with("test_key", "test_value", ex=300, px=None, nx=False, xx=False)

    @pytest.mark.asyncio
    async def test_set_operation_fallback(self, redis_manager, mock_redis_client):
        """Test SET operation fallback to memory cache"""
        mock_redis_client.set.side_effect = Exception("Redis unavailable")
        redis_manager._client = mock_redis_client
        redis_manager._degraded_mode = False

        result = await redis_manager.set("test_key", "test_value", ex=300)

        assert result is True
        # Verify it's stored in memory cache
        cached_value = redis_manager._get_from_memory_cache("test_key")
        assert cached_value == "test_value"

    @pytest.mark.asyncio
    async def test_delete_operation_success(self, redis_manager, mock_redis_client):
        """Test successful DELETE operation"""
        redis_manager._client = mock_redis_client
        redis_manager._degraded_mode = False

        result = await redis_manager.delete("key1", "key2")

        assert result == 1
        mock_redis_client.delete.assert_called_once_with("key1", "key2")

    @pytest.mark.asyncio
    async def test_exists_operation_success(self, redis_manager, mock_redis_client):
        """Test successful EXISTS operation"""
        redis_manager._client = mock_redis_client
        redis_manager._degraded_mode = False

        result = await redis_manager.exists("test_key")

        assert result == 1
        mock_redis_client.exists.assert_called_once_with("test_key")

    @pytest.mark.asyncio
    async def test_expire_operation_success(self, redis_manager, mock_redis_client):
        """Test successful EXPIRE operation"""
        redis_manager._client = mock_redis_client
        redis_manager._degraded_mode = False

        result = await redis_manager.expire("test_key", 300)

        assert result is True
        mock_redis_client.expire.assert_called_once_with("test_key", 300)

    @pytest.mark.asyncio
    async def test_hash_operations_success(self, redis_manager, mock_redis_client):
        """Test successful hash operations"""
        redis_manager._client = mock_redis_client
        redis_manager._degraded_mode = False

        # Test HSET
        set_result = await redis_manager.hset("hash_name", "field", "value")
        assert set_result == 1
        mock_redis_client.hset.assert_called_once_with("hash_name", "field", "value")

        # Test HGET
        get_result = await redis_manager.hget("hash_name", "field")
        assert get_result == "hash_value"
        mock_redis_client.hget.assert_called_once_with("hash_name", "field")

    @pytest.mark.asyncio
    async def test_hash_operations_fallback(self, redis_manager, mock_redis_client):
        """Test hash operations fallback to memory cache"""
        mock_redis_client.hset.side_effect = Exception("Redis unavailable")
        mock_redis_client.hget.side_effect = Exception("Redis unavailable")
        redis_manager._client = mock_redis_client
        redis_manager._degraded_mode = False

        # Test HSET fallback
        set_result = await redis_manager.hset("hash_name", "field", "value")
        assert set_result == 1

        # Test HGET fallback
        get_result = await redis_manager.hget("hash_name", "field")
        assert get_result == "value"

    def test_memory_cache_operations(self, redis_manager):
        """Test memory cache operations"""
        # Test set and get
        result = redis_manager._set_in_memory_cache("key1", "value1", ex=300)
        assert result is True

        cached_value = redis_manager._get_from_memory_cache("key1")
        assert cached_value == "value1"

        # Test delete
        deleted = redis_manager._delete_from_memory_cache("key1")
        assert deleted == 1

        cached_value = redis_manager._get_from_memory_cache("key1")
        assert cached_value is None

    def test_memory_cache_expiration(self, redis_manager):
        """Test memory cache expiration"""
        # Set with very short expiration
        redis_manager._set_in_memory_cache("expire_key", "expire_value", ex=0)
        
        # Should be expired immediately
        redis_manager._cleanup_expired_cache()
        cached_value = redis_manager._get_from_memory_cache("expire_key")
        assert cached_value is None

    def test_memory_cache_size_limit(self, redis_manager):
        """Test memory cache size limit enforcement"""
        # Set a small cache size limit
        redis_manager._max_memory_cache_size = 5

        # Fill cache beyond limit
        for i in range(10):
            redis_manager._set_in_memory_cache(f"key_{i}", f"value_{i}")

        # Cache should not exceed limit
        assert len(redis_manager._memory_cache) <= redis_manager._max_memory_cache_size

    def test_memory_cache_hash_operations(self, redis_manager):
        """Test memory cache hash operations"""
        # Test HSET
        result = redis_manager._hset_in_memory_cache("hash_name", "field1", "value1")
        assert result == 1  # New field

        result = redis_manager._hset_in_memory_cache("hash_name", "field1", "value2")
        assert result == 0  # Existing field

        # Test HGET
        value = redis_manager._hget_from_memory_cache("hash_name", "field1")
        assert value == "value2"

        # Test non-existent field
        value = redis_manager._hget_from_memory_cache("hash_name", "field2")
        assert value is None

    @pytest.mark.asyncio
    async def test_connection_error_handling(self, redis_manager):
        """Test connection error handling"""
        error = Exception("Connection lost")
        
        with patch.object(redis_manager._health_manager, 'handle_connection_failure') as mock_handle:
            await redis_manager._handle_connection_error(error)

            assert redis_manager._connection_failures > 0
            assert redis_manager._last_connection_attempt is not None
            mock_handle.assert_called_once_with("redis", error)

    @pytest.mark.asyncio
    async def test_degraded_mode_callbacks(self, redis_manager):
        """Test degraded mode callbacks"""
        # Test degraded mode callback
        await redis_manager._on_degraded_mode("redis")
        assert redis_manager._degraded_mode is True

        # Test recovery callback
        await redis_manager._on_recovery("redis")
        assert redis_manager._degraded_mode is False
        assert redis_manager._connection_failures == 0

    def test_is_degraded(self, redis_manager):
        """Test degraded mode check"""
        assert redis_manager.is_degraded() is False

        redis_manager._degraded_mode = True
        assert redis_manager.is_degraded() is True

    def test_get_connection_info(self, redis_manager, mock_connection_pool):
        """Test getting connection information"""
        redis_manager._pool = mock_connection_pool
        redis_manager._connection_failures = 3
        redis_manager._last_connection_attempt = datetime.utcnow()

        info = redis_manager.get_connection_info()

        assert info["redis_url"] == redis_manager.redis_url
        assert info["degraded_mode"] == redis_manager._degraded_mode
        assert info["connection_failures"] == 3
        assert info["memory_cache_size"] == len(redis_manager._memory_cache)
        assert "pool_created_connections" in info

    @pytest.mark.asyncio
    async def test_close_cleanup(self, redis_manager, mock_redis_client, mock_connection_pool):
        """Test proper cleanup on close"""
        redis_manager._client = mock_redis_client
        redis_manager._pool = mock_connection_pool
        redis_manager._memory_cache = {"key": "value"}

        await redis_manager.close()

        mock_redis_client.close.assert_called_once()
        assert redis_manager._client is None
        assert redis_manager._pool is None
        assert len(redis_manager._memory_cache) == 0

    @pytest.mark.asyncio
    async def test_close_with_errors(self, redis_manager, mock_redis_client, mock_connection_pool):
        """Test close with errors during cleanup"""
        mock_redis_client.close.side_effect = Exception("Close error")
        mock_connection_pool.disconnect = AsyncMock(side_effect=Exception("Disconnect error"))
        
        redis_manager._client = mock_redis_client
        redis_manager._pool = mock_connection_pool

        # Should not raise exception
        await redis_manager.close()

        assert redis_manager._client is None
        assert redis_manager._pool is None

    @pytest.mark.asyncio
    async def test_global_manager_functions(self, mock_redis_available):
        """Test global manager functions"""
        # Test initialization
        with patch('src.ai_karen_engine.services.redis_connection_manager.RedisConnectionManager') as MockManager:
            mock_instance = AsyncMock()
            mock_instance.initialize = AsyncMock(return_value=True)
            MockManager.return_value = mock_instance

            manager = await initialize_redis_manager(
                redis_url="redis://test:6379/0",
                max_connections=5,
            )
            
            assert manager is not None
            mock_instance.initialize.assert_called_once()

        # Test getting global instance
        global_manager = get_redis_manager()
        assert global_manager is not None

        # Test shutdown
        with patch.object(global_manager, 'close') as mock_close:
            await shutdown_redis_manager()
            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_connection_pool_creation(self, redis_manager):
        """Test connection pool creation"""
        with patch('src.ai_karen_engine.services.redis_connection_manager.ConnectionPool') as MockPool:
            mock_pool = MagicMock()
            MockPool.from_url.return_value = mock_pool

            await redis_manager._create_connection_pool()

            MockPool.from_url.assert_called_once_with(
                redis_manager.redis_url,
                max_connections=redis_manager.max_connections,
                retry_on_timeout=redis_manager.retry_on_timeout,
                socket_keepalive=redis_manager.socket_keepalive,
                socket_keepalive_options=redis_manager.socket_keepalive_options,
                decode_responses=True,
            )
            assert redis_manager._pool == mock_pool

    @pytest.mark.asyncio
    async def test_client_creation(self, redis_manager, mock_connection_pool):
        """Test Redis client creation"""
        redis_manager._pool = mock_connection_pool

        with patch('src.ai_karen_engine.services.redis_connection_manager.Redis') as MockRedis:
            mock_client = MagicMock()
            MockRedis.return_value = mock_client

            await redis_manager._create_client()

            MockRedis.assert_called_once_with(connection_pool=mock_connection_pool)
            assert redis_manager._client == mock_client

    @pytest.mark.asyncio
    async def test_connection_test(self, redis_manager, mock_redis_client):
        """Test connection testing"""
        redis_manager._client = mock_redis_client

        # Test successful connection
        result = await redis_manager._test_connection()
        assert result is True
        mock_redis_client.ping.assert_called_once()

        # Test failed connection
        mock_redis_client.ping.side_effect = Exception("Ping failed")
        result = await redis_manager._test_connection()
        assert result is False

    def test_memory_cache_exists_operation(self, redis_manager):
        """Test memory cache EXISTS operation"""
        # Set some keys
        redis_manager._set_in_memory_cache("key1", "value1")
        redis_manager._set_in_memory_cache("key2", "value2")

        # Test exists
        result = redis_manager._exists_in_memory_cache("key1", "key2", "key3")
        assert result == 2  # Only key1 and key2 exist

    def test_memory_cache_expire_operation(self, redis_manager):
        """Test memory cache EXPIRE operation"""
        # Set a key
        redis_manager._set_in_memory_cache("key1", "value1")

        # Set expiration
        result = redis_manager._expire_in_memory_cache("key1", 300)
        assert result is True

        # Try to expire non-existent key
        result = redis_manager._expire_in_memory_cache("key2", 300)
        assert result is False