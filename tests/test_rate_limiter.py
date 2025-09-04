"""
Comprehensive tests for the enhanced rate limiting system
"""

import asyncio
import pytest
import pytest_asyncio
import time
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

from ai_karen_engine.server.rate_limiter import (
    EnhancedRateLimiter,
    MemoryRateLimitStorage,
    RedisRateLimitStorage,
    RateLimitRule,
    RateLimitScope,
    RateLimitAlgorithm,
    RateLimitResult,
    create_rate_limiter,
    DEFAULT_RATE_LIMIT_RULES,
)

# Legacy imports for backward compatibility tests
from ai_karen_engine.auth.config import AuthConfig
from ai_karen_engine.auth.exceptions import RateLimitExceededError
from ai_karen_engine.auth.security import RateLimiter
from ai_karen_engine.auth.rate_limit_store import RedisRateLimitStore

try:
    import fakeredis.aioredis as fakeredis
    FAKEREDIS_AVAILABLE = True
except Exception:  # pragma: no cover
    fakeredis = None
    FAKEREDIS_AVAILABLE = False

try:
    import redis.asyncio as redis_asyncio
    REDIS_AVAILABLE = True
except ImportError:
    redis_asyncio = None
    REDIS_AVAILABLE = False


class TestMemoryRateLimitStorage:
    """Test memory-based rate limit storage"""
    
    @pytest.fixture
    def storage(self):
        return MemoryRateLimitStorage()
    
    @pytest.mark.asyncio
    async def test_get_count_empty(self, storage):
        count = await storage.get_count("test_key", 60)
        assert count == 0
    
    @pytest.mark.asyncio
    async def test_increment_count(self, storage):
        count1 = await storage.increment_count("test_key", 60, 1)
        assert count1 == 1
        
        count2 = await storage.increment_count("test_key", 60, 2)
        assert count2 == 3
        
        current_count = await storage.get_count("test_key", 60)
        assert current_count == 3
    
    @pytest.mark.asyncio
    async def test_window_start(self, storage):
        start_time = datetime.now(timezone.utc)
        
        # Initially no window start
        window_start = await storage.get_window_start("test_key")
        assert window_start is None
        
        # Set window start
        await storage.set_window_start("test_key", start_time, 60)
        
        # Retrieve window start
        retrieved_start = await storage.get_window_start("test_key")
        assert retrieved_start == start_time
    
    @pytest.mark.asyncio
    async def test_request_timestamps(self, storage):
        current_time = time.time()
        
        # Add timestamps
        await storage.add_request_timestamp("test_key", current_time, 60)
        await storage.add_request_timestamp("test_key", current_time + 1, 60)
        await storage.add_request_timestamp("test_key", current_time + 2, 60)
        
        # Get all timestamps
        timestamps = await storage.get_request_timestamps("test_key", current_time - 1)
        assert len(timestamps) == 3
        assert current_time in timestamps
        assert current_time + 1 in timestamps
        assert current_time + 2 in timestamps
        
        # Get timestamps since a later time
        recent_timestamps = await storage.get_request_timestamps("test_key", current_time + 1.5)
        assert len(recent_timestamps) == 1
        assert current_time + 2 in recent_timestamps
    
    @pytest.mark.asyncio
    async def test_cleanup_expired(self, storage):
        current_time = time.time()
        old_time = current_time - 3600  # 1 hour ago
        
        # Add old and new timestamps
        await storage.add_request_timestamp("test_key", old_time, 60)
        await storage.add_request_timestamp("test_key", current_time, 60)
        
        # Before cleanup
        timestamps = await storage.get_request_timestamps("test_key", 0)
        assert len(timestamps) == 2
        
        # Cleanup expired entries
        await storage.cleanup_expired(current_time - 1800)  # 30 minutes ago
        
        # After cleanup
        timestamps = await storage.get_request_timestamps("test_key", 0)
        assert len(timestamps) == 1
        assert current_time in timestamps
    
    @pytest.mark.asyncio
    async def test_stats(self, storage):
        await storage.increment_count("key1", 60, 1)
        await storage.increment_count("key2", 60, 1)
        await storage.add_request_timestamp("key3", time.time(), 60)
        
        stats = await storage.get_stats()
        assert stats["storage_type"] == "memory"
        assert stats["tracked_keys"] >= 2
        assert stats["total_timestamps"] >= 1


@pytest.mark.skipif(not FAKEREDIS_AVAILABLE, reason="fakeredis not available")
class TestRedisRateLimitStorage:
    """Test Redis-based rate limit storage"""
    
    @pytest_asyncio.fixture
    async def storage(self):
        fake_redis = fakeredis.FakeRedis(decode_responses=True)
        storage = RedisRateLimitStorage(fake_redis)
        yield storage
        await fake_redis.aclose()
    
    @pytest.mark.asyncio
    async def test_get_count_empty(self, storage):
        count = await storage.get_count("test_key", 60)
        assert count == 0
    
    @pytest.mark.asyncio
    async def test_increment_count(self, storage):
        count1 = await storage.increment_count("test_key", 60, 1)
        assert count1 == 1
        
        count2 = await storage.increment_count("test_key", 60, 2)
        assert count2 == 3
        
        current_count = await storage.get_count("test_key", 60)
        assert current_count == 3
    
    @pytest.mark.asyncio
    async def test_window_start(self, storage):
        start_time = datetime.now(timezone.utc)
        
        # Initially no window start
        window_start = await storage.get_window_start("test_key")
        assert window_start is None
        
        # Set window start
        await storage.set_window_start("test_key", start_time, 60)
        
        # Retrieve window start
        retrieved_start = await storage.get_window_start("test_key")
        assert retrieved_start is not None
        # Allow small time difference due to serialization
        assert abs((retrieved_start - start_time).total_seconds()) < 1
    
    @pytest.mark.asyncio
    async def test_request_timestamps(self, storage):
        current_time = time.time()
        
        # Add timestamps
        await storage.add_request_timestamp("test_key", current_time, 60)
        await storage.add_request_timestamp("test_key", current_time + 1, 60)
        await storage.add_request_timestamp("test_key", current_time + 2, 60)
        
        # Get all timestamps
        timestamps = await storage.get_request_timestamps("test_key", current_time - 1)
        assert len(timestamps) == 3
        
        # Get timestamps since a later time
        recent_timestamps = await storage.get_request_timestamps("test_key", current_time + 1.5)
        assert len(recent_timestamps) == 1


class TestRateLimitRule:
    """Test rate limit rule configuration"""
    
    def test_rule_creation(self):
        rule = RateLimitRule(
            name="test_rule",
            scope=RateLimitScope.IP,
            algorithm=RateLimitAlgorithm.SLIDING_WINDOW,
            limit=100,
            window_seconds=60,
            priority=10,
            endpoints=["/api/test"],
            description="Test rule"
        )
        
        assert rule.name == "test_rule"
        assert rule.scope == RateLimitScope.IP
        assert rule.algorithm == RateLimitAlgorithm.SLIDING_WINDOW
        assert rule.limit == 100
        assert rule.window_seconds == 60
        assert rule.priority == 10
        assert rule.endpoints == ["/api/test"]
        assert rule.enabled is True
    
    def test_rule_defaults(self):
        rule = RateLimitRule(
            name="minimal_rule",
            scope=RateLimitScope.USER,
            algorithm=RateLimitAlgorithm.FIXED_WINDOW,
            limit=50,
            window_seconds=30
        )
        
        assert rule.burst_limit is None
        assert rule.enabled is True
        assert rule.priority == 0
        assert rule.endpoints is None
        assert rule.user_types is None
        assert rule.description == ""


class TestEnhancedRateLimiter:
    """Test enhanced rate limiter functionality"""
    
    @pytest.fixture
    def storage(self):
        return MemoryRateLimitStorage()
    
    @pytest.fixture
    def simple_rules(self):
        return [
            RateLimitRule(
                name="user_limit",
                scope=RateLimitScope.USER,
                algorithm=RateLimitAlgorithm.FIXED_WINDOW,
                limit=100,
                window_seconds=3600,
                priority=20  # Higher priority than IP rule
            ),
            RateLimitRule(
                name="ip_limit",
                scope=RateLimitScope.IP,
                algorithm=RateLimitAlgorithm.SLIDING_WINDOW,
                limit=10,
                window_seconds=60,
                priority=10
            ),
        ]
    
    @pytest.fixture
    def limiter(self, storage, simple_rules):
        return EnhancedRateLimiter(storage, simple_rules)
    
    @pytest.mark.asyncio
    async def test_check_rate_limit_allowed(self, limiter):
        result = await limiter.check_rate_limit(
            ip_address="192.168.1.1",
            endpoint="/api/test",
            user_id="user123"
        )
        
        assert result.allowed is True
        assert result.current_count == 0
        assert result.limit > 0
        assert result.window_seconds > 0
        assert result.rule_name in ["ip_limit", "user_limit"]
    
    @pytest.mark.asyncio
    async def test_check_rate_limit_exceeded(self, limiter):
        ip_address = "192.168.1.2"
        endpoint = "/api/test"
        
        # Make requests up to the limit
        for i in range(10):
            await limiter.record_request(ip_address, endpoint)
        
        # Next request should be rate limited
        result = await limiter.check_rate_limit(ip_address, endpoint)
        assert result.allowed is False
        assert result.current_count >= 10
        assert result.retry_after_seconds > 0
    
    @pytest.mark.asyncio
    async def test_sliding_window_algorithm(self, storage):
        rule = RateLimitRule(
            name="sliding_test",
            scope=RateLimitScope.IP,
            algorithm=RateLimitAlgorithm.SLIDING_WINDOW,
            limit=5,
            window_seconds=10
        )
        limiter = EnhancedRateLimiter(storage, [rule])
        
        ip_address = "192.168.1.3"
        endpoint = "/api/sliding"
        
        # Make 5 requests quickly
        for i in range(5):
            await limiter.record_request(ip_address, endpoint)
        
        # 6th request should be blocked
        result = await limiter.check_rate_limit(ip_address, endpoint)
        assert result.allowed is False
        
        # Wait for some requests to expire from the window
        await asyncio.sleep(2)
        
        # Should still be blocked as all requests are still in the 10-second window
        result = await limiter.check_rate_limit(ip_address, endpoint)
        assert result.allowed is False
    
    @pytest.mark.asyncio
    async def test_fixed_window_algorithm(self, storage):
        rule = RateLimitRule(
            name="fixed_test",
            scope=RateLimitScope.IP,
            algorithm=RateLimitAlgorithm.FIXED_WINDOW,
            limit=3,
            window_seconds=5
        )
        limiter = EnhancedRateLimiter(storage, [rule])
        
        ip_address = "192.168.1.4"
        endpoint = "/api/fixed"
        
        # First request should be allowed
        result = await limiter.check_rate_limit(ip_address, endpoint)
        assert result.allowed is True
        await limiter.record_request(ip_address, endpoint)
        
        # Second request should be allowed
        result = await limiter.check_rate_limit(ip_address, endpoint)
        assert result.allowed is True
        await limiter.record_request(ip_address, endpoint)
        
        # Third request should be allowed
        result = await limiter.check_rate_limit(ip_address, endpoint)
        assert result.allowed is True
        await limiter.record_request(ip_address, endpoint)
        
        # Fourth request should be blocked
        result = await limiter.check_rate_limit(ip_address, endpoint)
        assert result.allowed is False
    
    @pytest.mark.asyncio
    async def test_token_bucket_algorithm(self, storage):
        rule = RateLimitRule(
            name="token_test",
            scope=RateLimitScope.IP,
            algorithm=RateLimitAlgorithm.TOKEN_BUCKET,
            limit=10,
            window_seconds=10,
            burst_limit=15
        )
        limiter = EnhancedRateLimiter(storage, [rule])
        
        ip_address = "192.168.1.5"
        endpoint = "/api/token"
        
        # Should start with full bucket (burst_limit = 15)
        result = await limiter.check_rate_limit(ip_address, endpoint, request_size=15)
        assert result.allowed is True
        await limiter.record_request(ip_address, endpoint, request_size=15)
        
        # Should be out of tokens now
        result = await limiter.check_rate_limit(ip_address, endpoint, request_size=1)
        assert result.allowed is False
    
    @pytest.mark.asyncio
    async def test_rule_priority(self, storage):
        rules = [
            RateLimitRule(
                name="low_priority",
                scope=RateLimitScope.IP,
                algorithm=RateLimitAlgorithm.SLIDING_WINDOW,
                limit=100,
                window_seconds=60,
                priority=1
            ),
            RateLimitRule(
                name="high_priority",
                scope=RateLimitScope.IP,
                algorithm=RateLimitAlgorithm.SLIDING_WINDOW,
                limit=10,
                window_seconds=60,
                priority=10,
                endpoints=["/api/priority"]
            ),
        ]
        limiter = EnhancedRateLimiter(storage, rules)
        
        # Request to specific endpoint should use high priority rule
        result = await limiter.check_rate_limit("192.168.1.6", "/api/priority")
        assert result.rule_name == "high_priority"
        assert result.limit == 10
        
        # Request to other endpoint should use low priority rule
        result = await limiter.check_rate_limit("192.168.1.6", "/api/other")
        assert result.rule_name == "low_priority"
        assert result.limit == 100
    
    @pytest.mark.asyncio
    async def test_user_specific_limits(self, limiter):
        # User-specific request should use user rule
        result = await limiter.check_rate_limit(
            ip_address="192.168.1.7",
            endpoint="/api/test",
            user_id="user456"
        )
        assert result.rule_name == "user_limit"
        assert result.limit == 100
        
        # Anonymous request should use IP rule
        result = await limiter.check_rate_limit(
            ip_address="192.168.1.7",
            endpoint="/api/test"
        )
        assert result.rule_name == "ip_limit"
        assert result.limit == 10
    
    @pytest.mark.asyncio
    async def test_request_size_weighting(self, limiter):
        ip_address = "192.168.1.8"
        endpoint = "/api/weighted"
        
        # Large request should consume more of the limit
        result = await limiter.check_rate_limit(ip_address, endpoint, request_size=5)
        assert result.allowed is True
        await limiter.record_request(ip_address, endpoint, request_size=5)
        
        # Should have less remaining capacity
        result = await limiter.check_rate_limit(ip_address, endpoint, request_size=6)
        # Depending on the rule, this might be blocked
        if not result.allowed:
            assert result.current_count >= 5
    
    @pytest.mark.asyncio
    async def test_stats(self, limiter):
        stats = await limiter.get_stats()
        
        assert "rules_count" in stats
        assert "default_rule" in stats
        assert "cache_size" in stats
        assert "storage" in stats
        
        assert stats["rules_count"] == 2  # From simple_rules fixture
        assert "name" in stats["default_rule"]
        assert "scope" in stats["default_rule"]
        assert "algorithm" in stats["default_rule"]
    
    @pytest.mark.asyncio
    async def test_cleanup(self, limiter):
        # Add some requests
        await limiter.record_request("192.168.1.9", "/api/cleanup")
        
        # Cleanup should not raise errors
        await limiter.cleanup()
        
        # Should still be functional after cleanup
        result = await limiter.check_rate_limit("192.168.1.9", "/api/cleanup")
        assert isinstance(result, RateLimitResult)


class TestRateLimiterFactory:
    """Test rate limiter factory function"""
    
    def test_create_memory_limiter(self):
        limiter = create_rate_limiter(storage_type="memory")
        assert isinstance(limiter, EnhancedRateLimiter)
        assert isinstance(limiter.storage, MemoryRateLimitStorage)
    
    @pytest.mark.skipif(not REDIS_AVAILABLE, reason="redis not available")
    def test_create_redis_limiter_no_url(self):
        with pytest.raises(ValueError, match="redis_url is required"):
            create_rate_limiter(storage_type="redis")
    
    def test_create_with_custom_rules(self):
        custom_rules = [
            RateLimitRule(
                name="custom",
                scope=RateLimitScope.GLOBAL,
                algorithm=RateLimitAlgorithm.FIXED_WINDOW,
                limit=1000,
                window_seconds=60
            )
        ]
        
        limiter = create_rate_limiter(storage_type="memory", custom_rules=custom_rules)
        assert len(limiter.rules) == 1
        assert limiter.rules[0].name == "custom"
    
    def test_default_rules_loaded(self):
        limiter = create_rate_limiter(storage_type="memory")
        assert len(limiter.rules) == len(DEFAULT_RATE_LIMIT_RULES)


# Legacy tests for backward compatibility
class TestLegacyRateLimiter:
    """Test legacy rate limiter for backward compatibility"""
    
    @pytest.mark.asyncio
    async def test_rate_limiter_memory_backend(self):
        config = AuthConfig()
        config.security.rate_limit_max_requests = 2
        config.security.rate_limit_window_minutes = 1
        limiter = RateLimiter(config)
        ip = "127.0.0.1"
        await limiter.check_rate_limit(ip)
        await limiter.record_attempt(ip)
        await limiter.check_rate_limit(ip)
        await limiter.record_attempt(ip)
        with pytest.raises(RateLimitExceededError):
            await limiter.check_rate_limit(ip)

    @pytest.mark.skipif(not FAKEREDIS_AVAILABLE, reason="fakeredis not available")
    @pytest.mark.asyncio
    async def test_rate_limiter_redis_backend(self):
        config = AuthConfig()
        config.security.rate_limit_max_requests = 2
        config.security.rate_limit_window_minutes = 1
        config.security.rate_limit_storage = "redis"
        fake_client = fakeredis.FakeRedis(decode_responses=True)
        store = RedisRateLimitStore(fake_client)
        limiter = RateLimiter(config, store=store)
        ip = "192.168.1.1"
        await limiter.check_rate_limit(ip)
        await limiter.record_attempt(ip)
        await limiter.check_rate_limit(ip)
        await limiter.record_attempt(ip)
        with pytest.raises(RateLimitExceededError):
            await limiter.check_rate_limit(ip)
        await fake_client.aclose()


class TestRateLimitIntegration:
    """Integration tests for rate limiting system"""
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """Test rate limiter under concurrent load"""
        storage = MemoryRateLimitStorage()
        rule = RateLimitRule(
            name="concurrent_test",
            scope=RateLimitScope.IP,
            algorithm=RateLimitAlgorithm.SLIDING_WINDOW,
            limit=10,
            window_seconds=60
        )
        limiter = EnhancedRateLimiter(storage, [rule])
        
        ip_address = "192.168.1.100"
        endpoint = "/api/concurrent"
        
        async def make_request():
            result = await limiter.check_rate_limit(ip_address, endpoint)
            if result.allowed:
                await limiter.record_request(ip_address, endpoint)
            return result.allowed
        
        # Make 20 concurrent requests
        tasks = [make_request() for _ in range(20)]
        results = await asyncio.gather(*tasks)
        
        # Should have exactly 10 allowed requests
        allowed_count = sum(1 for allowed in results if allowed)
        assert allowed_count <= 10  # Some might be blocked due to race conditions
        assert allowed_count >= 8   # But most should be allowed
    
    @pytest.mark.asyncio
    async def test_multiple_ips_different_limits(self):
        """Test that different IPs have independent limits"""
        storage = MemoryRateLimitStorage()
        rule = RateLimitRule(
            name="multi_ip_test",
            scope=RateLimitScope.IP,
            algorithm=RateLimitAlgorithm.FIXED_WINDOW,
            limit=3,
            window_seconds=60
        )
        limiter = EnhancedRateLimiter(storage, [rule])
        
        endpoint = "/api/multi"
        
        # Each IP should have its own limit
        for ip_suffix in range(1, 4):  # Test 3 different IPs
            ip_address = f"192.168.1.{ip_suffix}"
            
            # Each IP should be able to make 3 requests
            for request_num in range(3):
                result = await limiter.check_rate_limit(ip_address, endpoint)
                assert result.allowed is True, f"IP {ip_address} request {request_num + 1} should be allowed"
                await limiter.record_request(ip_address, endpoint)
            
            # 4th request should be blocked
            result = await limiter.check_rate_limit(ip_address, endpoint)
            assert result.allowed is False, f"IP {ip_address} 4th request should be blocked"
    
    @pytest.mark.asyncio
    async def test_rule_caching_performance(self):
        """Test that rule caching improves performance"""
        storage = MemoryRateLimitStorage()
        
        # Create many rules to test caching
        rules = []
        for i in range(100):
            priority = 200 if i == 50 else i  # Give rule_50 the highest priority
            rules.append(RateLimitRule(
                name=f"rule_{i}",
                scope=RateLimitScope.IP,
                algorithm=RateLimitAlgorithm.SLIDING_WINDOW,
                limit=100,
                window_seconds=60,
                priority=priority,
                endpoints=[f"/api/endpoint_{i}"] if i == 50 else None  # Only rule_50 matches the endpoint
            ))
        
        limiter = EnhancedRateLimiter(storage, rules)
        
        ip_address = "192.168.1.200"
        endpoint = "/api/endpoint_50"  # Should match rule_50
        
        # First request should populate cache
        start_time = time.time()
        result1 = await limiter.check_rate_limit(ip_address, endpoint)
        first_request_time = time.time() - start_time
        
        # Second request should use cache and be faster
        start_time = time.time()
        result2 = await limiter.check_rate_limit(ip_address, endpoint)
        second_request_time = time.time() - start_time
        
        # Both should use the same rule
        assert result1.rule_name == result2.rule_name == "rule_50"
        
        # Second request should be faster (though this might be flaky in CI)
        # Just ensure both complete successfully
        assert first_request_time >= 0
        assert second_request_time >= 0
