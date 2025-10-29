#!/usr/bin/env python3
"""
Standalone test script for SmartCacheManager

This script tests the smart caching and computation reuse system
to verify all requirements are met.
"""

import asyncio
import tempfile
import shutil
import json
from datetime import datetime, timedelta
from pathlib import Path

# Add src to path for imports
import sys
sys.path.insert(0, 'src')

from ai_karen_engine.services.smart_cache_manager import (
    SmartCacheManager,
    CacheEntry,
    UsagePattern,
    CacheMetrics
)


async def test_basic_caching():
    """Test basic caching functionality."""
    print("Testing basic caching functionality...")
    
    temp_dir = tempfile.mkdtemp()
    try:
        cache_manager = SmartCacheManager(
            max_memory_mb=5,
            max_entries=50,
            cache_dir=temp_dir
        )
        
        # Test caching a response
        query = "What is machine learning?"
        context = {"user_id": "test_user", "session": "test_session"}
        response = {
            "content": "Machine learning is a subset of artificial intelligence...",
            "confidence": 0.95
        }
        
        await cache_manager.cache_response_components(query, context, response)
        
        # Test cache hit
        cached_response = await cache_manager.check_cache_relevance(query, context)
        assert cached_response is not None
        assert cached_response["content"] == response["content"]
        
        print("✓ Basic caching works correctly")
        
        # Test cache miss
        different_query = "What is deep learning?"
        cached_response = await cache_manager.check_cache_relevance(different_query, context)
        assert cached_response is None
        
        print("✓ Cache miss detection works correctly")
        
        await cache_manager.stop_background_tasks()
        
    finally:
        shutil.rmtree(temp_dir)


async def test_query_similarity_caching():
    """Test query similarity-based caching."""
    print("\nTesting query similarity caching...")
    
    temp_dir = tempfile.mkdtemp()
    try:
        cache_manager = SmartCacheManager(
            max_memory_mb=5,
            similarity_threshold=0.6,
            cache_dir=temp_dir
        )
        
        # Cache original response
        original_query = "How does neural network work?"
        context = {"user_id": "test_user"}
        response = {"content": "Neural networks work by...", "confidence": 0.9}
        
        await cache_manager.cache_response_components(original_query, context, response)
        
        # Mock high similarity for testing
        original_method = cache_manager._calculate_query_similarity
        cache_manager._calculate_query_similarity = lambda q1, q2: 0.8
        
        # Test similar query
        similar_query = "How do neural networks function?"
        cached_response = await cache_manager.check_cache_relevance(similar_query, context)
        
        # Restore original method
        cache_manager._calculate_query_similarity = original_method
        
        assert cached_response is not None
        print("✓ Query similarity caching works correctly")
        
        await cache_manager.stop_background_tasks()
        
    finally:
        shutil.rmtree(temp_dir)


async def test_component_caching():
    """Test component-based caching."""
    print("\nTesting component-based caching...")
    
    temp_dir = tempfile.mkdtemp()
    try:
        cache_manager = SmartCacheManager(cache_dir=temp_dir)
        
        # Cache response with components
        query = "Analyze stock market data"
        context = {"user_id": "trader123"}
        response = {"analysis": "Market is bullish"}
        components = {
            "stock_data": {"AAPL": 150.0, "GOOGL": 2800.0},
            "market_indicators": {"RSI": 65, "MACD": "positive"}
        }
        
        await cache_manager.cache_response_components(query, context, response, components)
        
        # Check component caching
        query_hash = cache_manager._hash_query(query)
        assert query_hash in cache_manager.component_cache
        assert "stock_data" in cache_manager.component_cache[query_hash]
        assert "market_indicators" in cache_manager.component_cache[query_hash]
        
        print("✓ Component caching works correctly")
        
        await cache_manager.stop_background_tasks()
        
    finally:
        shutil.rmtree(temp_dir)


async def test_intelligent_invalidation():
    """Test intelligent cache invalidation."""
    print("\nTesting intelligent cache invalidation...")
    
    temp_dir = tempfile.mkdtemp()
    try:
        cache_manager = SmartCacheManager(cache_dir=temp_dir)
        
        # Create test entries with different characteristics
        current_time = datetime.now()
        
        # Expired entry
        expired_entry = CacheEntry(
            key="expired",
            content="expired content",
            timestamp=current_time - timedelta(hours=2),
            access_count=1,
            last_accessed=current_time - timedelta(hours=2),
            context_hash="ctx1",
            query_hash="q1",
            relevance_score=0.8,
            size_bytes=100,
            expiry_time=current_time - timedelta(hours=1)
        )
        
        # Low relevance entry
        low_relevance_entry = CacheEntry(
            key="low_relevance",
            content="low relevance content",
            timestamp=current_time,
            access_count=1,
            last_accessed=current_time,
            context_hash="ctx2",
            query_hash="q2",
            relevance_score=0.1,
            size_bytes=100
        )
        
        # Good entry
        good_entry = CacheEntry(
            key="good",
            content="good content",
            timestamp=current_time,
            access_count=5,
            last_accessed=current_time,
            context_hash="ctx3",
            query_hash="q3",
            relevance_score=0.9,
            size_bytes=100
        )
        
        cache_manager.cache["expired"] = expired_entry
        cache_manager.cache["low_relevance"] = low_relevance_entry
        cache_manager.cache["good"] = good_entry
        
        # Run invalidation
        invalidated_count = await cache_manager.implement_intelligent_invalidation({
            'min_relevance': 0.3
        })
        
        assert invalidated_count == 2  # expired and low_relevance should be invalidated
        assert "good" in cache_manager.cache
        assert "expired" not in cache_manager.cache
        assert "low_relevance" not in cache_manager.cache
        
        print("✓ Intelligent invalidation works correctly")
        
        await cache_manager.stop_background_tasks()
        
    finally:
        shutil.rmtree(temp_dir)


async def test_cache_warming():
    """Test cache warming based on usage patterns."""
    print("\nTesting cache warming...")
    
    temp_dir = tempfile.mkdtemp()
    try:
        cache_manager = SmartCacheManager(cache_dir=temp_dir)
        
        # Create usage patterns
        current_time = datetime.now().strftime("%H:%M")
        patterns = [
            UsagePattern(
                query_pattern="weather forecast",
                frequency=10,
                time_patterns=[current_time],  # Current time
                context_patterns=["user:morning_user"],
                user_patterns=[],
                prediction_confidence=0.8
            ),
            UsagePattern(
                query_pattern="stock prices",
                frequency=5,
                time_patterns=["23:59"],  # Different time
                context_patterns=[],
                user_patterns=[],
                prediction_confidence=0.9
            )
        ]
        
        # Warm cache
        warmed_count = await cache_manager.warm_cache_based_on_patterns(patterns)
        
        assert warmed_count == 1  # Only first pattern should match current time
        assert len(cache_manager.cache) == 1
        
        # Check that warmed entry has correct tags
        warmed_entry = list(cache_manager.cache.values())[0]
        assert "warmed" in warmed_entry.tags
        assert "predicted" in warmed_entry.tags
        
        print("✓ Cache warming works correctly")
        
        await cache_manager.stop_background_tasks()
        
    finally:
        shutil.rmtree(temp_dir)


async def test_memory_optimization():
    """Test memory optimization functionality."""
    print("\nTesting memory optimization...")
    
    temp_dir = tempfile.mkdtemp()
    try:
        cache_manager = SmartCacheManager(
            max_memory_mb=1,  # Small limit for testing
            max_entries=10,
            cache_dir=temp_dir
        )
        
        # Create entries that exceed memory limit
        large_content = "x" * 50000  # 50KB content
        
        for i in range(5):
            entry = CacheEntry(
                key=f"large_{i}",
                content=large_content,
                timestamp=datetime.now(),
                access_count=i + 1,  # Different access counts
                last_accessed=datetime.now(),
                context_hash=f"ctx{i}",
                query_hash=f"q{i}",
                relevance_score=0.5 + (i * 0.1),  # Different relevance scores
                size_bytes=len(large_content)
            )
            cache_manager.cache[f"large_{i}"] = entry
        
        initial_memory = cache_manager._calculate_memory_usage()
        
        # Run memory optimization
        results = await cache_manager.optimize_cache_memory_usage()
        
        assert 'initial_memory_bytes' in results
        assert 'final_memory_bytes' in results
        assert results['initial_memory_bytes'] == initial_memory
        
        print("✓ Memory optimization works correctly")
        
        await cache_manager.stop_background_tasks()
        
    finally:
        shutil.rmtree(temp_dir)


async def test_usage_pattern_tracking():
    """Test usage pattern tracking and updates."""
    print("\nTesting usage pattern tracking...")
    
    temp_dir = tempfile.mkdtemp()
    try:
        cache_manager = SmartCacheManager(cache_dir=temp_dir)
        
        # Cache multiple similar queries to build patterns
        queries = [
            "What is the weather in New York?",
            "What is the weather in Boston?",
            "What is the weather in Chicago?"
        ]
        
        context = {"user_id": "weather_user", "session_type": "chat"}
        response = {"content": "Weather information"}
        
        for query in queries:
            await cache_manager.cache_response_components(query, context, response)
        
        # Check that usage patterns were created
        assert len(cache_manager.usage_patterns) > 0
        
        # Find weather pattern
        weather_pattern = None
        for pattern in cache_manager.usage_patterns:
            if "weather" in pattern.query_pattern:
                weather_pattern = pattern
                break
        
        assert weather_pattern is not None
        assert weather_pattern.frequency >= 1
        assert len(weather_pattern.time_patterns) >= 1
        assert "user:weather_user" in weather_pattern.context_patterns
        
        print("✓ Usage pattern tracking works correctly")
        
        await cache_manager.stop_background_tasks()
        
    finally:
        shutil.rmtree(temp_dir)


async def test_cache_metrics():
    """Test cache metrics calculation."""
    print("\nTesting cache metrics...")
    
    temp_dir = tempfile.mkdtemp()
    try:
        cache_manager = SmartCacheManager(cache_dir=temp_dir)
        
        # Generate cache activity
        query = "Test query"
        context = {"user_id": "test"}
        response = {"content": "Test response"}
        
        # Cache hit scenario
        await cache_manager.cache_response_components(query, context, response)
        await cache_manager.check_cache_relevance(query, context)  # Hit
        
        # Cache miss scenario
        await cache_manager.check_cache_relevance("Different query", context)  # Miss
        
        # Get metrics
        metrics = await cache_manager.get_cache_metrics()
        
        assert metrics.total_requests == 2
        assert metrics.cache_hits == 1
        assert metrics.cache_misses == 1
        assert metrics.hit_rate == 0.5
        assert metrics.miss_rate == 0.5
        assert metrics.memory_usage_bytes > 0
        
        print("✓ Cache metrics calculation works correctly")
        
        await cache_manager.stop_background_tasks()
        
    finally:
        shutil.rmtree(temp_dir)


async def test_persistent_storage():
    """Test persistent cache storage."""
    print("\nTesting persistent storage...")
    
    temp_dir = tempfile.mkdtemp()
    try:
        # Create cache manager and add data
        cache_manager1 = SmartCacheManager(cache_dir=temp_dir)
        
        query = "Persistent test query"
        context = {"user_id": "persistent_user"}
        response = {"content": "Persistent response"}
        
        await cache_manager1.cache_response_components(query, context, response)
        
        # Save to disk
        success = await cache_manager1.save_cache_to_disk()
        assert success
        
        await cache_manager1.stop_background_tasks()
        
        # Create new cache manager and load data
        cache_manager2 = SmartCacheManager(cache_dir=temp_dir)
        success = await cache_manager2.load_cache_from_disk()
        assert success
        
        # Verify data was loaded
        cached_response = await cache_manager2.check_cache_relevance(query, context)
        assert cached_response is not None
        assert cached_response["content"] == response["content"]
        
        print("✓ Persistent storage works correctly")
        
        await cache_manager2.stop_background_tasks()
        
    finally:
        shutil.rmtree(temp_dir)


async def test_background_tasks():
    """Test background task management."""
    print("\nTesting background tasks...")
    
    temp_dir = tempfile.mkdtemp()
    try:
        cache_manager = SmartCacheManager(cache_dir=temp_dir)
        
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
        
        print("✓ Background task management works correctly")
        
    finally:
        shutil.rmtree(temp_dir)


async def run_performance_test():
    """Run performance test to verify efficiency requirements."""
    print("\nRunning performance tests...")
    
    temp_dir = tempfile.mkdtemp()
    try:
        cache_manager = SmartCacheManager(
            max_memory_mb=50,
            max_entries=1000,
            cache_dir=temp_dir
        )
        
        import time
        
        # Test cache performance with multiple operations
        start_time = time.time()
        
        # Cache 100 different responses
        for i in range(100):
            query = f"Test query {i}"
            context = {"user_id": f"user_{i % 10}", "batch": i // 10}
            response = {"content": f"Response {i}", "data": "x" * 1000}
            
            await cache_manager.cache_response_components(query, context, response)
        
        cache_time = time.time() - start_time
        
        # Test cache retrieval performance
        start_time = time.time()
        
        hits = 0
        for i in range(100):
            query = f"Test query {i}"
            context = {"user_id": f"user_{i % 10}", "batch": i // 10}
            cached_response = await cache_manager.check_cache_relevance(query, context)
            if cached_response:
                hits += 1
        
        retrieval_time = time.time() - start_time
        
        # Get final metrics
        metrics = await cache_manager.get_cache_metrics()
        
        print(f"✓ Performance test completed:")
        print(f"  - Cache time for 100 operations: {cache_time:.3f}s")
        print(f"  - Retrieval time for 100 operations: {retrieval_time:.3f}s")
        print(f"  - Cache hit rate: {metrics.hit_rate:.2%}")
        print(f"  - Memory usage: {metrics.memory_usage_bytes / 1024:.1f} KB")
        
        # Verify performance requirements
        assert cache_time < 5.0  # Should cache 100 items in under 5 seconds
        assert retrieval_time < 1.0  # Should retrieve 100 items in under 1 second
        assert metrics.hit_rate == 1.0  # Should have 100% hit rate for exact matches
        
        await cache_manager.stop_background_tasks()
        
    finally:
        shutil.rmtree(temp_dir)


async def main():
    """Run all tests."""
    print("Starting SmartCacheManager comprehensive tests...\n")
    
    try:
        await test_basic_caching()
        await test_query_similarity_caching()
        await test_component_caching()
        await test_intelligent_invalidation()
        await test_cache_warming()
        await test_memory_optimization()
        await test_usage_pattern_tracking()
        await test_cache_metrics()
        await test_persistent_storage()
        await test_background_tasks()
        await run_performance_test()
        
        print("\n" + "="*60)
        print("✅ ALL SMART CACHE MANAGER TESTS PASSED!")
        print("="*60)
        print("\nSmartCacheManager successfully implements:")
        print("✓ Intelligent caching based on query similarity")
        print("✓ Cache relevance checking with context and freshness")
        print("✓ Component-based caching for reusable response parts")
        print("✓ Intelligent cache invalidation based on content relevance")
        print("✓ Cache warming system based on usage patterns")
        print("✓ Memory optimization system for cached content management")
        print("✓ Performance metrics and monitoring")
        print("✓ Persistent storage capabilities")
        print("✓ Background maintenance tasks")
        print("✓ Efficient computation reuse")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)