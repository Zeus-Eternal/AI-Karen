"""
Unit tests for SmartCacheManager

Tests intelligent caching, query similarity, context awareness,
component caching, and predictive cache warming.
"""

import pytest
import asyncio
import tempfile
import shutil
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path

from src.ai_karen_engine.services.smart_cache_manager import (
    SmartCacheManager,
    CacheEntry,
    QuerySimilarity,
    UsagePattern,
    CacheMetrics
)


class TestSmartCacheManager:
    """Test suite for SmartCacheManager."""
    
    @pytest.fixture
    async def cache_manager(self):
        """Create a SmartCacheManager instance for testing."""
        temp_dir = tempfile.mkdtemp()
        manager = SmartCacheManager(
            max_memory_mb=10,
            max_entries=100,
            default_ttl_hours=1,
            similarity_threshold=0.8,
            cache_dir=temp_dir
        )
        yield manager
        await manager.stop_background_tasks()
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def sample_query(self):
        """Sample query for testing."""
        return "What is the weather like today?"
    
    @pytest.fixture
    def sample_context(self):
        """Sample context for testing."""
        return {
            "user_id": "user123",
            "session_type": "chat",
            "timestamp": datetime.now().isoformat()
        }
    
    @pytest.fixture
    def sample_response(self):
        """Sample response for testing."""
        return {
            "content": "The weather is sunny with a temperature of 75°F",
            "confidence": 0.95,
            "sources": ["weather_api"]
        }

    @pytest.mark.asyncio
    async def test_cache_manager_initialization(self, cache_manager):
        """Test SmartCacheManager initialization."""
        assert cache_manager.max_memory_bytes == 10 * 1024 * 1024
        assert cache_manager.max_entries == 100
        assert cache_manager.similarity_threshold == 0.8
        assert len(cache_manager.cache) == 0
        assert len(cache_manager.usage_patterns) == 0
        assert cache_manager.metrics.total_requests == 0

    @pytest.mark.asyncio
    async def test_cache_response_components(self, cache_manager, sample_query, 
                                           sample_context, sample_response):
        """Test caching response and components."""
        components = {
            "weather_data": {"temperature": 75, "condition": "sunny"},
            "location_info": {"city": "New York", "coordinates": [40.7, -74.0]}
        }
        
        await cache_manager.cache_response_components(
            sample_query, sample_context, sample_response, components
        )
        
        # Check that response was cached
        assert len(cache_manager.cache) == 1
        
        # Check that components were cached
        query_hash = cache_manager._hash_query(sample_query)
        assert query_hash in cache_manager.component_cache
        assert "weather_data" in cache_manager.component_cache[query_hash]
        assert "location_info" in cache_manager.component_cache[query_hash]

    @pytest.mark.asyncio
    async def test_check_cache_relevance_direct_hit(self, cache_manager, sample_query,
                                                   sample_context, sample_response):
        """Test direct cache hit."""
        # Cache the response first
        await cache_manager.cache_response_components(
            sample_query, sample_context, sample_response
        )
        
        # Check for cache hit
        cached_response = await cache_manager.check_cache_relevance(
            sample_query, sample_context
        )
        
        assert cached_response is not None
        assert cached_response == sample_response
        assert cache_manager.metrics.cache_hits == 1
        assert cache_manager.metrics.cache_misses == 0

    @pytest.mark.asyncio
    async def test_check_cache_relevance_miss(self, cache_manager):
        """Test cache miss."""
        cached_response = await cache_manager.check_cache_relevance(
            "What is the capital of France?", {"user_id": "user456"}
        )
        
        assert cached_response is None
        assert cache_manager.metrics.cache_hits == 0
        assert cache_manager.metrics.cache_misses == 1

    @pytest.mark.asyncio
    async def test_similarity_based_cache_hit(self, cache_manager, sample_context, sample_response):
        """Test similarity-based cache hit."""
        # Cache original query
        original_query = "What is the weather today?"
        await cache_manager.cache_response_components(
            original_query, sample_context, sample_response
        )
        
        # Mock similarity calculation to return high similarity
        with patch.object(cache_manager, '_calculate_query_similarity', return_value=0.9):
            with patch.object(cache_manager, '_calculate_context_similarity', return_value=0.8):
                # Try similar query
                similar_query = "How is the weather today?"
                cached_response = await cache_manager.check_cache_relevance(
                    similar_query, sample_context
                )
                
                assert cached_response is not None
                assert cache_manager.metrics.cache_hits == 1

    @pytest.mark.asyncio
    async def test_component_based_cache_hit(self, cache_manager, sample_query, 
                                           sample_context, sample_response):
        """Test component-based cache hit."""
        components = {
            "weather_data": {"temperature": 75, "condition": "sunny"}
        }
        
        # Cache components
        await cache_manager.cache_response_components(
            sample_query, sample_context, sample_response, components
        )
        
        # Mock component validity check
        with patch.object(cache_manager, '_is_component_valid', return_value=True):
            # Check for component cache hit
            cached_components = await cache_manager._find_cached_components(
                sample_query, sample_context
            )
            
            assert cached_components is not None
            assert "weather_data" in cached_components

    @pytest.mark.asyncio
    async def test_intelligent_invalidation_expired_entries(self, cache_manager):
        """Test intelligent invalidation of expired entries."""
        # Create expired cache entry
        expired_entry = CacheEntry(
            key="expired_key",
            content="expired_content",
            timestamp=datetime.now() - timedelta(hours=2),
            access_count=1,
            last_accessed=datetime.now() - timedelta(hours=2),
            context_hash="context123",
            query_hash="query123",
            relevance_score=0.8,
            size_bytes=100,
            expiry_time=datetime.now() - timedelta(hours=1)  # Expired 1 hour ago
        )
        
        cache_manager.cache["expired_key"] = expired_entry
        
        # Run invalidation
        invalidated_count = await cache_manager.implement_intelligent_invalidation({})
        
        assert invalidated_count == 1
        assert "expired_key" not in cache_manager.cache

    @pytest.mark.asyncio
    async def test_intelligent_invalidation_low_relevance(self, cache_manager):
        """Test intelligent invalidation of low relevance entries."""
        # Create low relevance cache entry
        low_relevance_entry = CacheEntry(
            key="low_relevance_key",
            content="low_relevance_content",
            timestamp=datetime.now(),
            access_count=1,
            last_accessed=datetime.now(),
            context_hash="context123",
            query_hash="query123",
            relevance_score=0.1,  # Very low relevance
            size_bytes=100
        )
        
        cache_manager.cache["low_relevance_key"] = low_relevance_entry
        
        # Run invalidation with minimum relevance threshold
        invalidated_count = await cache_manager.implement_intelligent_invalidation({
            'min_relevance': 0.3
        })
        
        assert invalidated_count == 1
        assert "low_relevance_key" not in cache_manager.cache

    @pytest.mark.asyncio
    async def test_intelligent_invalidation_unused_entries(self, cache_manager):
        """Test intelligent invalidation of unused entries."""
        # Create unused cache entry
        unused_entry = CacheEntry(
            key="unused_key",
            content="unused_content",
            timestamp=datetime.now() - timedelta(days=10),
            access_count=1,
            last_accessed=datetime.now() - timedelta(days=10),  # Not accessed for 10 days
            context_hash="context123",
            query_hash="query123",
            relevance_score=0.8,
            size_bytes=100
        )
        
        cache_manager.cache["unused_key"] = unused_entry
        
        # Run invalidation with max unused days
        invalidated_count = await cache_manager.implement_intelligent_invalidation({
            'max_days_unused': 7
        })
        
        assert invalidated_count == 1
        assert "unused_key" not in cache_manager.cache

    @pytest.mark.asyncio
    async def test_warm_cache_based_on_patterns(self, cache_manager):
        """Test cache warming based on usage patterns."""
        # Create usage patterns
        pattern1 = UsagePattern(
            query_pattern="weather [LOCATION]",
            frequency=10,
            time_patterns=[datetime.now().strftime("%H:%M")],  # Current time
            context_patterns=["user:user123"],
            user_patterns=[],
            prediction_confidence=0.8
        )
        
        pattern2 = UsagePattern(
            query_pattern="news [TOPIC]",
            frequency=5,
            time_patterns=["23:59"],  # Different time
            context_patterns=[],
            user_patterns=[],
            prediction_confidence=0.9
        )
        
        cache_manager.usage_patterns = [pattern1, pattern2]
        
        # Mock response generation
        with patch.object(cache_manager, '_generate_predicted_response', 
                         return_value={"predicted": "response"}):
            warmed_count = await cache_manager.warm_cache_based_on_patterns()
            
            # Should warm only pattern1 (matches current time)
            assert warmed_count == 1
            assert len(cache_manager.cache) == 1

    @pytest.mark.asyncio
    async def test_optimize_cache_memory_usage(self, cache_manager):
        """Test cache memory optimization."""
        # Create large cache entries
        for i in range(5):
            large_entry = CacheEntry(
                key=f"large_key_{i}",
                content="x" * 20000,  # 20KB content
                timestamp=datetime.now(),
                access_count=1,
                last_accessed=datetime.now(),
                context_hash=f"context{i}",
                query_hash=f"query{i}",
                relevance_score=0.5,
                size_bytes=20000
            )
            cache_manager.cache[f"large_key_{i}"] = large_entry
        
        initial_memory = cache_manager._calculate_memory_usage()
        
        # Mock compression
        with patch.object(cache_manager, '_compress_large_entries', return_value=3):
            with patch.object(cache_manager, '_intelligent_eviction', return_value=1):
                results = await cache_manager.optimize_cache_memory_usage()
                
                assert results['compressed_entries'] == 3
                assert results['evicted_entries'] == 1
                assert 'memory_saved_bytes' in results

    @pytest.mark.asyncio
    async def test_usage_pattern_tracking(self, cache_manager, sample_query, sample_context):
        """Test usage pattern tracking and updates."""
        # Cache response to trigger pattern tracking
        await cache_manager.cache_response_components(
            sample_query, sample_context, {"response": "data"}
        )
        
        # Check that usage pattern was created
        assert len(cache_manager.usage_patterns) == 1
        
        pattern = cache_manager.usage_patterns[0]
        assert pattern.frequency == 1
        assert len(pattern.time_patterns) == 1
        assert "user:user123" in pattern.context_patterns

    @pytest.mark.asyncio
    async def test_cache_metrics_calculation(self, cache_manager, sample_query, 
                                           sample_context, sample_response):
        """Test cache metrics calculation."""
        # Generate some cache activity
        await cache_manager.cache_response_components(
            sample_query, sample_context, sample_response
        )
        
        # Cache hit
        await cache_manager.check_cache_relevance(sample_query, sample_context)
        
        # Cache miss
        await cache_manager.check_cache_relevance("different query", sample_context)
        
        metrics = await cache_manager.get_cache_metrics()
        
        assert metrics.total_requests == 2
        assert metrics.cache_hits == 1
        assert metrics.cache_misses == 1
        assert metrics.hit_rate == 0.5
        assert metrics.miss_rate == 0.5
        assert metrics.memory_usage_bytes > 0

    @pytest.mark.asyncio
    async def test_background_tasks_lifecycle(self, cache_manager):
        """Test background task lifecycle management."""
        # Start background tasks
        await cache_manager.start_background_tasks()
        
        assert cache_manager._cleanup_task is not None
        assert cache_manager._warming_task is not None
        assert not cache_manager._cleanup_task.done()
        assert not cache_manager._warming_task.done()
        
        # Stop background tasks
        await cache_manager.stop_background_tasks()
        
        assert cache_manager._cleanup_task is None
        assert cache_manager._warming_task is None

    @pytest.mark.asyncio
    async def test_persistent_storage(self, cache_manager, sample_query, 
                                    sample_context, sample_response):
        """Test saving and loading cache from disk."""
        # Add some data to cache
        await cache_manager.cache_response_components(
            sample_query, sample_context, sample_response
        )
        
        # Save to disk
        success = await cache_manager.save_cache_to_disk()
        assert success
        
        # Clear cache
        cache_manager.cache.clear()
        cache_manager.usage_patterns.clear()
        
        # Load from disk
        success = await cache_manager.load_cache_from_disk()
        assert success
        assert len(cache_manager.cache) == 1

    @pytest.mark.asyncio
    async def test_memory_pressure_handling(self, cache_manager):
        """Test memory pressure detection and handling."""
        # Fill cache beyond memory limit
        large_content = "x" * 1000000  # 1MB content
        
        for i in range(15):  # 15MB total, exceeds 10MB limit
            entry = CacheEntry(
                key=f"pressure_key_{i}",
                content=large_content,
                timestamp=datetime.now(),
                access_count=1,
                last_accessed=datetime.now(),
                context_hash=f"context{i}",
                query_hash=f"query{i}",
                relevance_score=0.5,
                size_bytes=len(large_content)
            )
            cache_manager.cache[f"pressure_key_{i}"] = entry
        
        # Mock intelligent eviction
        with patch.object(cache_manager, '_intelligent_eviction', return_value=5) as mock_eviction:
            await cache_manager._check_memory_pressure()
            mock_eviction.assert_called_once()

    @pytest.mark.asyncio
    async def test_query_pattern_extraction(self, cache_manager):
        """Test query pattern extraction for usage tracking."""
        test_cases = [
            ("What is the weather in 12345?", "what is the weather in [NUMBER]?"),
            ("Send email to user@example.com", "send email to [EMAIL]"),
            ("Visit https://example.com", "visit [URL]"),
            ("This is a very long query with many words that should be truncated", 
             "this is a very long query with many words that should")
        ]
        
        for query, expected_pattern in test_cases:
            pattern = cache_manager._extract_query_pattern(query)
            assert pattern == expected_pattern

    @pytest.mark.asyncio
    async def test_eviction_score_calculation(self, cache_manager):
        """Test eviction score calculation."""
        current_time = datetime.now()
        
        # Recent, frequently accessed, high relevance entry
        good_entry = CacheEntry(
            key="good_key",
            content="good_content",
            timestamp=current_time,
            access_count=10,
            last_accessed=current_time,
            context_hash="context123",
            query_hash="query123",
            relevance_score=0.9,
            size_bytes=1000
        )
        
        # Old, rarely accessed, low relevance entry
        bad_entry = CacheEntry(
            key="bad_key",
            content="bad_content",
            timestamp=current_time - timedelta(days=7),
            access_count=1,
            last_accessed=current_time - timedelta(days=7),
            context_hash="context456",
            query_hash="query456",
            relevance_score=0.1,
            size_bytes=100000  # Large size
        )
        
        good_score = cache_manager._calculate_eviction_score(good_entry, current_time)
        bad_score = cache_manager._calculate_eviction_score(bad_entry, current_time)
        
        assert good_score > bad_score

    @pytest.mark.asyncio
    async def test_component_validity_check(self, cache_manager):
        """Test component validity checking."""
        current_time = datetime.now()
        
        # Valid component
        valid_component = {
            'data': {'key': 'value'},
            'timestamp': current_time.isoformat(),
            'relevance_score': 0.8
        }
        
        # Invalid component (old)
        invalid_component = {
            'data': {'key': 'value'},
            'timestamp': (current_time - timedelta(days=2)).isoformat(),
            'relevance_score': 0.8
        }
        
        # Invalid component (low relevance)
        low_relevance_component = {
            'data': {'key': 'value'},
            'timestamp': current_time.isoformat(),
            'relevance_score': 0.3
        }
        
        assert cache_manager._is_component_valid(valid_component, {})
        assert not cache_manager._is_component_valid(invalid_component, {})
        assert not cache_manager._is_component_valid(low_relevance_component, {})

    def test_hash_generation(self, cache_manager):
        """Test query and context hash generation."""
        query1 = "What is the weather?"
        query2 = "WHAT IS THE WEATHER?"  # Different case
        query3 = "What is the temperature?"  # Different query
        
        hash1 = cache_manager._hash_query(query1)
        hash2 = cache_manager._hash_query(query2)
        hash3 = cache_manager._hash_query(query3)
        
        # Same query (different case) should produce same hash
        assert hash1 == hash2
        # Different query should produce different hash
        assert hash1 != hash3
        
        # Test context hashing
        context1 = {"user": "123", "session": "abc"}
        context2 = {"session": "abc", "user": "123"}  # Different order
        context3 = {"user": "456", "session": "abc"}  # Different values
        
        ctx_hash1 = cache_manager._hash_context(context1)
        ctx_hash2 = cache_manager._hash_context(context2)
        ctx_hash3 = cache_manager._hash_context(context3)
        
        # Same context (different order) should produce same hash
        assert ctx_hash1 == ctx_hash2
        # Different context should produce different hash
        assert ctx_hash1 != ctx_hash3


if __name__ == "__main__":
    pytest.main([__file__])