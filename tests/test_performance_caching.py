"""
Performance Tests for Caching Implementation

Tests for token validation caching, error response caching, provider health caching,
and request deduplication to ensure performance improvements are working correctly.
"""

import asyncio
import pytest
import time
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch, AsyncMock

from ai_karen_engine.core.cache import (
    MemoryCache,
    TokenValidationCache,
    IntelligentResponseCache,
    ProviderHealthCache,
    RequestDeduplicator,
    get_token_cache,
    get_response_cache,
    get_provider_cache,
    get_request_deduplicator,
    cleanup_all_caches,
    get_all_cache_stats
)
from ai_karen_engine.auth.tokens import EnhancedTokenManager
from ai_karen_engine.auth.config import JWTConfig
from ai_karen_engine.auth.models import UserData
from ai_karen_engine.services.error_response_service import (
    ErrorResponseService,
    ErrorCategory,
    ErrorSeverity
)


class TestMemoryCache:
    """Test basic memory cache functionality"""
    
    def test_cache_basic_operations(self):
        """Test basic cache set/get operations"""
        cache = MemoryCache(max_size=10, default_ttl=60)
        
        # Test set and get
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"
        
        # Test miss
        assert cache.get("nonexistent") is None
        
        # Test stats
        stats = cache.get_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["size"] == 1
    
    def test_cache_ttl_expiration(self):
        """Test TTL expiration"""
        cache = MemoryCache(max_size=10, default_ttl=1)  # 1 second TTL
        
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"
        
        # Wait for expiration
        time.sleep(1.1)
        assert cache.get("key1") is None
        
        stats = cache.get_stats()
        assert stats["expired_removals"] == 1
    
    def test_cache_lru_eviction(self):
        """Test LRU eviction when cache is full"""
        cache = MemoryCache(max_size=2, default_ttl=60)
        
        # Fill cache
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        
        # Access key1 to make it more recently used
        cache.get("key1")
        
        # Add third item, should evict key2
        cache.set("key3", "value3")
        
        assert cache.get("key1") == "value1"  # Should still exist
        assert cache.get("key2") is None      # Should be evicted
        assert cache.get("key3") == "value3"  # Should exist
        
        stats = cache.get_stats()
        assert stats["evictions"] == 1
    
    def test_cache_cleanup_expired(self):
        """Test cleanup of expired entries"""
        cache = MemoryCache(max_size=10, default_ttl=1)
        
        # Add entries with short TTL
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        
        # Wait for expiration
        time.sleep(1.1)
        
        # Cleanup expired entries
        removed_count = cache.cleanup_expired()
        assert removed_count == 2
        assert cache.get_stats()["size"] == 0


class TestTokenValidationCache:
    """Test token validation caching"""
    
    @pytest.fixture
    def token_cache(self):
        return TokenValidationCache(ttl=60)
    
    @pytest.fixture
    def sample_token(self):
        return "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1c2VyMTIzIiwiZXhwIjoxNjQwOTk1MjAwfQ.test"
    
    def test_token_cache_basic_operations(self, token_cache, sample_token):
        """Test basic token cache operations"""
        validation_result = {
            "valid": True,
            "payload": {"sub": "user123", "exp": 1640995200}
        }
        
        # Cache validation result
        token_cache.cache_validation_result(sample_token, validation_result)
        
        # Retrieve cached result
        cached_result = token_cache.get_validation_result(sample_token)
        assert cached_result == validation_result
        
        # Test cache miss
        assert token_cache.get_validation_result("invalid_token") is None
    
    def test_token_cache_invalidation(self, token_cache, sample_token):
        """Test token cache invalidation"""
        validation_result = {"valid": True, "payload": {"sub": "user123"}}
        
        token_cache.cache_validation_result(sample_token, validation_result)
        assert token_cache.get_validation_result(sample_token) is not None
        
        # Invalidate token
        assert token_cache.invalidate_token(sample_token) is True
        assert token_cache.get_validation_result(sample_token) is None
        
        # Test invalidating non-existent token
        assert token_cache.invalidate_token("nonexistent") is False
    
    def test_token_cache_custom_ttl(self, token_cache, sample_token):
        """Test custom TTL for token cache"""
        validation_result = {"valid": False, "error": "Invalid token"}
        
        # Cache with short TTL
        token_cache.cache_validation_result(sample_token, validation_result, custom_ttl=1)
        assert token_cache.get_validation_result(sample_token) is not None
        
        # Wait for expiration
        time.sleep(1.1)
        assert token_cache.get_validation_result(sample_token) is None


class TestIntelligentResponseCache:
    """Test intelligent error response caching"""
    
    @pytest.fixture
    def response_cache(self):
        return IntelligentResponseCache(ttl=60)
    
    def test_response_cache_basic_operations(self, response_cache):
        """Test basic response cache operations"""
        error_message = "API key not found"
        response_data = {
            "title": "API Key Missing",
            "summary": "The API key is not configured",
            "category": "api_key_missing",
            "next_steps": ["Add API key to .env file"]
        }
        
        # Cache response
        response_cache.cache_response(error_message, response_data)
        
        # Retrieve cached response
        cached_response = response_cache.get_cached_response(error_message)
        assert cached_response == response_data
        
        # Test cache miss
        assert response_cache.get_cached_response("different error") is None
    
    def test_response_cache_with_provider(self, response_cache):
        """Test response cache with provider context"""
        error_message = "Rate limit exceeded"
        provider_name = "openai"
        response_data = {
            "title": "Rate Limit Exceeded",
            "summary": "OpenAI rate limit exceeded",
            "category": "rate_limit"
        }
        
        # Cache with provider context
        response_cache.cache_response(
            error_message, response_data, provider_name=provider_name
        )
        
        # Should hit cache with same provider
        cached = response_cache.get_cached_response(error_message, provider_name=provider_name)
        assert cached == response_data
        
        # Should miss cache with different provider
        cached = response_cache.get_cached_response(error_message, provider_name="anthropic")
        assert cached is None


class TestProviderHealthCache:
    """Test provider health caching"""
    
    @pytest.fixture
    def health_cache(self):
        return ProviderHealthCache(ttl=60)
    
    def test_provider_health_cache_basic_operations(self, health_cache):
        """Test basic provider health cache operations"""
        provider_name = "openai"
        health_data = {
            "name": "openai",
            "status": "healthy",
            "success_rate": 0.95,
            "response_time": 1200,
            "last_check": datetime.utcnow().isoformat()
        }
        
        # Cache health data
        health_cache.cache_provider_health(provider_name, health_data)
        
        # Retrieve cached data
        cached_health = health_cache.get_provider_health(provider_name)
        assert cached_health == health_data
        
        # Test cache miss
        assert health_cache.get_provider_health("nonexistent") is None
    
    def test_provider_health_cache_custom_ttl(self, health_cache):
        """Test custom TTL for unhealthy providers"""
        provider_name = "openai"
        unhealthy_data = {
            "name": "openai",
            "status": "unhealthy",
            "error_message": "Service unavailable"
        }
        
        # Cache unhealthy provider (should use shorter TTL)
        health_cache.cache_provider_health(provider_name, unhealthy_data)
        
        # Should be cached initially
        assert health_cache.get_provider_health(provider_name) is not None
    
    def test_provider_health_cache_invalidation(self, health_cache):
        """Test provider health cache invalidation"""
        provider_name = "openai"
        health_data = {"name": "openai", "status": "healthy"}
        
        health_cache.cache_provider_health(provider_name, health_data)
        assert health_cache.get_provider_health(provider_name) is not None
        
        # Invalidate provider
        assert health_cache.invalidate_provider(provider_name) is True
        assert health_cache.get_provider_health(provider_name) is None


class TestRequestDeduplicator:
    """Test request deduplication"""
    
    @pytest.fixture
    def deduplicator(self):
        return RequestDeduplicator(ttl=30)
    
    @pytest.mark.asyncio
    async def test_request_deduplication(self, deduplicator):
        """Test that identical requests are deduplicated"""
        call_count = 0
        
        async def slow_function(arg1, arg2):
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.1)  # Simulate slow operation
            return f"result_{arg1}_{arg2}"
        
        # Start multiple identical requests simultaneously
        tasks = [
            deduplicator.deduplicate(slow_function, "test", "value"),
            deduplicator.deduplicate(slow_function, "test", "value"),
            deduplicator.deduplicate(slow_function, "test", "value")
        ]
        
        results = await asyncio.gather(*tasks)
        
        # All should return the same result
        assert all(result == "result_test_value" for result in results)
        
        # Function should only be called once due to deduplication
        assert call_count == 1
        
        # Check deduplication stats
        stats = deduplicator.get_stats()
        assert stats["unique_requests"] == 1
        assert stats["deduplicated_requests"] == 2
    
    @pytest.mark.asyncio
    async def test_different_requests_not_deduplicated(self, deduplicator):
        """Test that different requests are not deduplicated"""
        call_count = 0
        
        async def test_function(arg):
            nonlocal call_count
            call_count += 1
            return f"result_{arg}"
        
        # Start different requests
        tasks = [
            deduplicator.deduplicate(test_function, "arg1"),
            deduplicator.deduplicate(test_function, "arg2"),
            deduplicator.deduplicate(test_function, "arg3")
        ]
        
        results = await asyncio.gather(*tasks)
        
        # Should get different results
        assert results == ["result_arg1", "result_arg2", "result_arg3"]
        
        # Function should be called for each unique request
        assert call_count == 3


class TestTokenManagerCaching:
    """Test token manager with caching integration"""
    
    @pytest.fixture
    def jwt_config(self):
        return JWTConfig(
            secret_key="test_secret_key_for_testing_only",
            algorithm="HS256",
            access_token_expire_minutes=15,
            refresh_token_expire_days=7
        )
    
    @pytest.fixture
    def token_manager(self, jwt_config):
        return EnhancedTokenManager(jwt_config)
    
    @pytest.fixture
    def user_data(self):
        return UserData(
            user_id="test_user_123",
            email="test@example.com",
            full_name="Test User",
            tenant_id="test_tenant",
            roles=["user"],
            is_verified=True,
            is_active=True
        )
    
    @pytest.mark.asyncio
    async def test_token_validation_caching(self, token_manager, user_data):
        """Test that token validation results are cached"""
        # Create a token
        token = await token_manager.create_access_token(user_data)
        
        # First validation (should hit the actual validation)
        start_time = time.time()
        payload1 = await token_manager.validate_token(token, "access")
        first_duration = time.time() - start_time
        
        # Second validation (should hit cache)
        start_time = time.time()
        payload2 = await token_manager.validate_token(token, "access")
        second_duration = time.time() - start_time
        
        # Results should be identical
        assert payload1 == payload2
        assert payload1["sub"] == user_data.user_id
        
        # Second call should be faster due to caching
        assert second_duration < first_duration
        
        # Check cache stats
        cache_stats = token_manager._token_cache.get_stats()
        assert cache_stats["hits"] >= 1
    
    @pytest.mark.asyncio
    async def test_token_cache_invalidation_on_revoke(self, token_manager, user_data):
        """Test that token cache is invalidated when token is revoked"""
        # Create and validate token
        token = await token_manager.create_access_token(user_data)
        payload = await token_manager.validate_token(token, "access")
        assert payload is not None
        
        # Revoke token
        revoked = await token_manager.revoke_token(token)
        assert revoked is True
        
        # Validation should now fail
        with pytest.raises(Exception):  # Should raise InvalidTokenError
            await token_manager.validate_token(token, "access")
    
    @pytest.mark.asyncio
    async def test_token_deduplication(self, token_manager, user_data):
        """Test that simultaneous token validations are deduplicated"""
        # Create a token
        token = await token_manager.create_access_token(user_data)
        
        # Start multiple simultaneous validations
        tasks = [
            token_manager.validate_token(token, "access"),
            token_manager.validate_token(token, "access"),
            token_manager.validate_token(token, "access")
        ]
        
        results = await asyncio.gather(*tasks)
        
        # All should return the same result
        assert all(result["sub"] == user_data.user_id for result in results)
        
        # Check deduplication stats
        dedup_stats = token_manager._deduplicator.get_stats()
        assert dedup_stats["unique_requests"] >= 1


class TestErrorResponseServiceCaching:
    """Test error response service with caching"""
    
    @pytest.fixture
    def error_service(self):
        return ErrorResponseService()
    
    def test_error_response_caching(self, error_service):
        """Test that error responses are cached for common errors"""
        error_message = "OPENAI_API_KEY not found"
        
        # First analysis (should perform full analysis)
        start_time = time.time()
        response1 = error_service.analyze_error(
            error_message=error_message,
            use_ai_analysis=False  # Disable AI to make test deterministic
        )
        first_duration = time.time() - start_time
        
        # Second analysis (should hit cache)
        start_time = time.time()
        response2 = error_service.analyze_error(
            error_message=error_message,
            use_ai_analysis=False
        )
        second_duration = time.time() - start_time
        
        # Results should be identical
        assert response1.title == response2.title
        assert response1.category == response2.category
        assert response1.next_steps == response2.next_steps
        
        # Second call should be faster due to caching
        assert second_duration < first_duration
    
    def test_error_response_cache_with_provider_context(self, error_service):
        """Test error response caching with provider context"""
        error_message = "Rate limit exceeded"
        
        # Analyze with different providers
        response1 = error_service.analyze_error(
            error_message=error_message,
            provider_name="openai",
            use_ai_analysis=False
        )
        
        response2 = error_service.analyze_error(
            error_message=error_message,
            provider_name="anthropic",
            use_ai_analysis=False
        )
        
        # Should get similar responses but potentially different provider-specific guidance
        assert response1.category == response2.category
        assert response1.title == response2.title


class TestCacheIntegration:
    """Test cache integration and global functions"""
    
    def test_global_cache_instances(self):
        """Test that global cache instances work correctly"""
        token_cache = get_token_cache()
        response_cache = get_response_cache()
        provider_cache = get_provider_cache()
        deduplicator = get_request_deduplicator()
        
        assert isinstance(token_cache, TokenValidationCache)
        assert isinstance(response_cache, IntelligentResponseCache)
        assert isinstance(provider_cache, ProviderHealthCache)
        assert isinstance(deduplicator, RequestDeduplicator)
        
        # Test that subsequent calls return the same instances
        assert get_token_cache() is token_cache
        assert get_response_cache() is response_cache
        assert get_provider_cache() is provider_cache
        assert get_request_deduplicator() is deduplicator
    
    @pytest.mark.asyncio
    async def test_cleanup_all_caches(self):
        """Test cleanup of all caches"""
        # Add some data to caches
        token_cache = get_token_cache()
        response_cache = get_response_cache()
        provider_cache = get_provider_cache()
        
        token_cache.cache_validation_result("token1", {"valid": True}, custom_ttl=1)
        response_cache.cache_response("error1", {"title": "Error"}, custom_ttl=1)
        provider_cache.cache_provider_health("provider1", {"status": "healthy"}, custom_ttl=1)
        
        # Wait for expiration
        await asyncio.sleep(1.1)
        
        # Cleanup expired entries
        results = await cleanup_all_caches()
        
        assert "token_cache" in results
        assert "response_cache" in results
        assert "provider_cache" in results
        assert all(count >= 0 for count in results.values())
    
    def test_get_all_cache_stats(self):
        """Test getting statistics for all caches"""
        # Use caches to generate some stats
        token_cache = get_token_cache()
        response_cache = get_response_cache()
        provider_cache = get_provider_cache()
        deduplicator = get_request_deduplicator()
        
        token_cache.cache_validation_result("token1", {"valid": True})
        response_cache.cache_response("error1", {"title": "Error"})
        provider_cache.cache_provider_health("provider1", {"status": "healthy"})
        
        # Get all stats
        all_stats = get_all_cache_stats()
        
        assert "token_cache" in all_stats
        assert "response_cache" in all_stats
        assert "provider_cache" in all_stats
        assert "request_deduplicator" in all_stats
        
        # Check that stats contain expected fields
        for cache_name, stats in all_stats.items():
            assert isinstance(stats, dict)
            if cache_name != "request_deduplicator":
                assert "size" in stats
                assert "hit_rate" in stats


class TestPerformanceBenchmarks:
    """Performance benchmarks for caching implementation"""
    
    @pytest.mark.asyncio
    async def test_token_validation_performance(self):
        """Benchmark token validation with and without caching"""
        jwt_config = JWTConfig(
            secret_key="test_secret_key_for_benchmarking",
            algorithm="HS256",
            access_token_expire_minutes=15
        )
        
        token_manager = EnhancedTokenManager(jwt_config)
        user_data = UserData(
            user_id="benchmark_user",
            email="benchmark@example.com",
            tenant_id="benchmark_tenant"
        )
        
        # Create token
        token = await token_manager.create_access_token(user_data)
        
        # Benchmark without cache (first call)
        start_time = time.time()
        await token_manager.validate_token(token, "access")
        uncached_duration = time.time() - start_time
        
        # Benchmark with cache (subsequent calls)
        cached_durations = []
        for _ in range(10):
            start_time = time.time()
            await token_manager.validate_token(token, "access")
            cached_durations.append(time.time() - start_time)
        
        avg_cached_duration = sum(cached_durations) / len(cached_durations)
        
        # Cached calls should be significantly faster
        performance_improvement = uncached_duration / avg_cached_duration
        assert performance_improvement > 2.0  # At least 2x faster
        
        print(f"Token validation performance improvement: {performance_improvement:.2f}x")
    
    def test_error_response_caching_performance(self):
        """Benchmark error response generation with caching"""
        error_service = ErrorResponseService()
        error_message = "OPENAI_API_KEY environment variable not set"
        
        # Benchmark without cache (first call)
        start_time = time.time()
        error_service.analyze_error(error_message, use_ai_analysis=False)
        uncached_duration = time.time() - start_time
        
        # Benchmark with cache (subsequent calls)
        cached_durations = []
        for _ in range(10):
            start_time = time.time()
            error_service.analyze_error(error_message, use_ai_analysis=False)
            cached_durations.append(time.time() - start_time)
        
        avg_cached_duration = sum(cached_durations) / len(cached_durations)
        
        # Cached calls should be faster
        performance_improvement = uncached_duration / avg_cached_duration
        assert performance_improvement > 1.5  # At least 1.5x faster
        
        print(f"Error response caching performance improvement: {performance_improvement:.2f}x")
    
    @pytest.mark.asyncio
    async def test_request_deduplication_performance(self):
        """Benchmark request deduplication effectiveness"""
        deduplicator = RequestDeduplicator()
        
        call_count = 0
        
        async def expensive_operation(arg):
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.1)  # Simulate expensive operation
            return f"result_{arg}"
        
        # Test without deduplication
        start_time = time.time()
        tasks = [expensive_operation("test") for _ in range(10)]
        await asyncio.gather(*tasks)
        without_dedup_duration = time.time() - start_time
        without_dedup_calls = call_count
        
        # Reset counter
        call_count = 0
        
        # Test with deduplication
        start_time = time.time()
        tasks = [deduplicator.deduplicate(expensive_operation, "test") for _ in range(10)]
        await asyncio.gather(*tasks)
        with_dedup_duration = time.time() - start_time
        with_dedup_calls = call_count
        
        # Deduplication should reduce both time and call count
        assert with_dedup_calls == 1  # Only one actual call
        assert without_dedup_calls == 10  # All calls executed
        
        # The key benefit is call reduction, timing may vary due to overhead
        call_reduction_ratio = without_dedup_calls / with_dedup_calls
        assert call_reduction_ratio >= 10  # Should be exactly 10x fewer calls
        
        print(f"Call reduction: {without_dedup_calls} -> {with_dedup_calls} calls ({call_reduction_ratio:.1f}x)")
        print(f"Time without dedup: {without_dedup_duration:.3f}s, with dedup: {with_dedup_duration:.3f}s")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])