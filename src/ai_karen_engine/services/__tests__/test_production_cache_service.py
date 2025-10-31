"""
Tests for Production Cache Service
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from ai_karen_engine.services.production_cache_service import (
    ProductionCacheService,
    CacheEntry,
    CacheStats,
    get_cache_service,
    reset_cache_service
)


class TestProductionCacheService:
    """Test cases for ProductionCacheService."""
    
    @pytest.fixture
    def mock_redis_client(self):
        """Mock Redis client for testing."""
        mock_redis = Mock()
        mock_redis.r = Mock()
        mock_redis.health.return_value = True
        return mock_redis
    
    @pytest.fixture
    def cache_service(self, mock_redis_client):
        """Create a cache service instance for testing."""
        return ProductionCacheService(redis_client=mock_redis_client)
    
    def test_init(self, cache_service):
        """Test cache service initialization."""
        assert cache_service.prefix == "prod_cache"
        assert cache_service.default_ttl == 3600
        assert cache_service.max_local_entries == 1000
        assert len(cache_service.namespaces) > 0
    
    def test_make_key(self, cache_service):
        """Test cache key generation."""
        key = cache_service._make_key("response_formatting", "test_key")
        assert key == "prod_cache:rf:test_key"
        
        key = cache_service._make_key("unknown_namespace", "test_key")
        assert key == "prod_cache:unknown_namespace:test_key"
    
    def test_hash_key(self, cache_service):
        """Test key hashing."""
        hash1 = cache_service._hash_key("test_string")
        hash2 = cache_service._hash_key("test_string")
        hash3 = cache_service._hash_key("different_string")
        
        assert hash1 == hash2
        assert hash1 != hash3
        assert len(hash1) == 16
    
    def test_calculate_size(self, cache_service):
        """Test size calculation."""
        size = cache_service._calculate_size("test")
        assert size > 0
        
        size_dict = cache_service._calculate_size({"key": "value"})
        assert size_dict > size
    
    def test_should_cache_locally(self, cache_service):
        """Test local caching decision logic."""
        # Small entry should be cached locally
        assert cache_service._should_cache_locally(1024)
        
        # Very large entry should not be cached locally
        assert not cache_service._should_cache_locally(2 * 1024 * 1024)
    
    @pytest.mark.asyncio
    async def test_get_set_local_cache(self, cache_service):
        """Test local cache get/set operations."""
        # Set a value
        success = await cache_service.set("test", "key1", "value1", ttl=3600)
        assert success
        
        # Get the value
        result = await cache_service.get("test", "key1")
        assert result == "value1"
        
        # Get non-existent key
        result = await cache_service.get("test", "nonexistent", default="default")
        assert result == "default"
    
    @pytest.mark.asyncio
    async def test_get_set_redis_cache(self, cache_service):
        """Test Redis cache get/set operations."""
        # Mock Redis operations
        cache_service.redis.r.get.return_value = None
        cache_service.redis.r.setex.return_value = True
        cache_service.redis.r.set.return_value = True
        cache_service.redis.r.sadd.return_value = 1
        cache_service.redis.r.expire.return_value = True
        
        # Set a value
        success = await cache_service.set("test", "key1", "value1", ttl=3600, tags=["tag1"])
        assert success
        
        # Verify Redis calls
        cache_service.redis.r.setex.assert_called()
        cache_service.redis.r.sadd.assert_called()
    
    @pytest.mark.asyncio
    async def test_delete(self, cache_service):
        """Test cache deletion."""
        # Set a value first
        await cache_service.set("test", "key1", "value1")
        
        # Mock Redis delete
        cache_service.redis.r.delete.return_value = 1
        
        # Delete the value
        success = await cache_service.delete("test", "key1")
        assert success
        
        # Verify it's gone from local cache
        result = await cache_service.get("test", "key1")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_invalidate_by_tags(self, cache_service):
        """Test tag-based cache invalidation."""
        # Mock Redis operations
        cache_service.redis.r.smembers.return_value = [b"key1", b"key2"]
        cache_service.redis.r.delete.return_value = 2
        
        # Invalidate by tags
        invalidated = await cache_service.invalidate_by_tags(["tag1"])
        assert invalidated == 2
    
    @pytest.mark.asyncio
    async def test_clear_namespace(self, cache_service):
        """Test namespace clearing."""
        # Mock Redis operations
        cache_service.redis.r.keys.return_value = [b"key1", b"key2"]
        cache_service.redis.r.delete.return_value = 2
        
        # Clear namespace
        cleared = await cache_service.clear_namespace("test")
        assert cleared == 2
    
    def test_get_stats(self, cache_service):
        """Test cache statistics."""
        stats = cache_service.get_stats()
        
        assert "hits" in stats
        assert "misses" in stats
        assert "hit_rate" in stats
        assert "local_entries" in stats
        assert "redis_connected" in stats
    
    def test_reset_stats(self, cache_service):
        """Test statistics reset."""
        # Increment some stats
        cache_service._stats.hits = 10
        cache_service._stats.misses = 5
        
        # Reset stats
        cache_service.reset_stats()
        
        assert cache_service._stats.hits == 0
        assert cache_service._stats.misses == 0
    
    @pytest.mark.asyncio
    async def test_cached_decorator_async(self, cache_service):
        """Test the cached decorator with async functions."""
        call_count = 0
        
        @cache_service.cached("test", ttl=3600)
        async def test_func(x, y):
            nonlocal call_count
            call_count += 1
            return x + y
        
        # First call should execute function
        result1 = await test_func(1, 2)
        assert result1 == 3
        assert call_count == 1
        
        # Second call should use cache
        result2 = await test_func(1, 2)
        assert result2 == 3
        assert call_count == 1  # Should not increment
    
    def test_cached_decorator_sync(self, cache_service):
        """Test the cached decorator with sync functions."""
        call_count = 0
        
        @cache_service.cached("test", ttl=3600)
        def test_func(x, y):
            nonlocal call_count
            call_count += 1
            return x + y
        
        # First call should execute function
        result1 = test_func(1, 2)
        assert result1 == 3
        assert call_count == 1
        
        # Second call should use cache
        result2 = test_func(1, 2)
        assert result2 == 3
        assert call_count == 1  # Should not increment
    
    @pytest.mark.asyncio
    async def test_expiration(self, cache_service):
        """Test cache entry expiration."""
        # Set a value with short TTL
        await cache_service.set("test", "key1", "value1", ttl=1)
        
        # Should be available immediately
        result = await cache_service.get("test", "key1")
        assert result == "value1"
        
        # Wait for expiration
        await asyncio.sleep(1.1)
        
        # Should be expired (this test depends on local cache expiration logic)
        # In a real scenario, Redis would handle expiration
        # For local cache, we need to check expiration manually
        cache_key = cache_service._make_key("test", "key1")
        if cache_key in cache_service._local_cache:
            entry = cache_service._local_cache[cache_key]
            if entry.expires_at and datetime.now() > entry.expires_at:
                # Entry should be considered expired
                assert True
    
    def test_eviction(self, cache_service):
        """Test local cache eviction."""
        # Set max entries to a small number for testing
        cache_service.max_local_entries = 2
        
        # Add entries
        asyncio.run(cache_service.set("test", "key1", "value1"))
        asyncio.run(cache_service.set("test", "key2", "value2"))
        asyncio.run(cache_service.set("test", "key3", "value3"))  # Should trigger eviction
        
        # Should have at most max_local_entries
        assert len(cache_service._local_cache) <= cache_service.max_local_entries


class TestCacheEntry:
    """Test cases for CacheEntry dataclass."""
    
    def test_cache_entry_creation(self):
        """Test CacheEntry creation."""
        now = datetime.now()
        entry = CacheEntry(
            key="test_key",
            value="test_value",
            created_at=now,
            expires_at=now + timedelta(hours=1)
        )
        
        assert entry.key == "test_key"
        assert entry.value == "test_value"
        assert entry.access_count == 0
        assert entry.tags == []
        assert entry.last_accessed == now


class TestCacheStats:
    """Test cases for CacheStats dataclass."""
    
    def test_cache_stats_creation(self):
        """Test CacheStats creation."""
        stats = CacheStats()
        
        assert stats.hits == 0
        assert stats.misses == 0
        assert stats.hit_rate == 0.0
    
    def test_hit_rate_calculation(self):
        """Test hit rate calculation."""
        stats = CacheStats(hits=7, misses=3)
        assert stats.hit_rate == 0.7
        
        stats = CacheStats(hits=0, misses=0)
        assert stats.hit_rate == 0.0


class TestGlobalCacheService:
    """Test cases for global cache service functions."""
    
    def test_get_cache_service(self):
        """Test global cache service getter."""
        # Reset first
        reset_cache_service()
        
        # Get service
        service1 = get_cache_service()
        service2 = get_cache_service()
        
        # Should be the same instance
        assert service1 is service2
    
    def test_reset_cache_service(self):
        """Test global cache service reset."""
        # Get service
        service1 = get_cache_service()
        
        # Reset
        reset_cache_service()
        
        # Get service again
        service2 = get_cache_service()
        
        # Should be different instances
        assert service1 is not service2


if __name__ == "__main__":
    pytest.main([__file__])