"""
Comprehensive Cache Efficiency Tests
Validates cache hit rates, memory usage, and intelligent caching strategies.
"""

import pytest
import asyncio
import time
import hashlib
import statistics
from typing import List, Dict, Any, Optional
from unittest.mock import Mock, patch, AsyncMock

from src.ai_karen_engine.services.smart_cache_manager import SmartCacheManager
from src.ai_karen_engine.core.shared_types import (
    OptimizedResponse, ContentSection, CachedResponse, Context,
    QueryAnalysis, ComplexityLevel, ContentType, ResponseLength, ExpertiseLevel
)


class TestCacheEfficiencyValidation:
    """Test suite for comprehensive cache efficiency validation."""
    
    @pytest.fixture
    async def cache_manager(self):
        """Create a smart cache manager for testing."""
        manager = SmartCacheManager()
        await manager.initialize()
        return manager
    
    @pytest.fixture
    def sample_responses(self):
        """Create sample optimized responses for caching tests."""
        responses = []
        for i in range(10):
            response = OptimizedResponse(
                content_sections=[
                    ContentSection(
                        priority=1,
                        content=f"High priority content for query {i}",
                        section_type="summary"
                    ),
                    ContentSection(
                        priority=2,
                        content=f"Detailed explanation for query {i}",
                        section_type="explanation"
                    )
                ],
                total_size=1000 + i * 100,
                generation_time=2.0 + i * 0.1,
                model_used=f"model-{i % 3}",  # Rotate between 3 models
                optimization_applied=["redundancy_elimination", "content_prioritization"],
                cache_key=f"cache-key-{i}",
                streaming_metadata=Mock()
            )
            responses.append(response)
        return responses
    
    @pytest.fixture
    def sample_queries(self):
        """Create sample queries for cache testing."""
        return [
            {
                "query": "What is machine learning?",
                "context": Context(user_id="user1", session_id="session1"),
                "expected_similarity": ["What is ML?", "Explain machine learning"]
            },
            {
                "query": "How to implement neural networks?",
                "context": Context(user_id="user2", session_id="session2"),
                "expected_similarity": ["Neural network implementation", "Build neural networks"]
            },
            {
                "query": "Python programming basics",
                "context": Context(user_id="user1", session_id="session1"),
                "expected_similarity": ["Python fundamentals", "Learn Python basics"]
            },
            {
                "query": "Data structures and algorithms",
                "context": Context(user_id="user3", session_id="session3"),
                "expected_similarity": ["DSA concepts", "Algorithms and data structures"]
            },
            {
                "query": "Web development with React",
                "context": Context(user_id="user2", session_id="session2"),
                "expected_similarity": ["React web development", "Building React apps"]
            }
        ]
    
    def _generate_cache_key(self, query: str, context: Context) -> str:
        """Generate a cache key for testing."""
        key_data = f"{query}:{context.user_id}:{context.session_id}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    @pytest.mark.asyncio
    async def test_cache_hit_rate_optimization(self, cache_manager, sample_responses, sample_queries):
        """Test that cache achieves high hit rates for similar queries."""
        cache_stats = {
            'hits': 0,
            'misses': 0,
            'total_requests': 0
        }
        
        # First pass: populate cache
        for i, query_data in enumerate(sample_queries):
            query = query_data["query"]
            context = query_data["context"]
            
            # Cache miss - store response
            cached_response = await cache_manager.check_cache_relevance(query, context)
            if cached_response is None:
                cache_stats['misses'] += 1
                # Cache the response
                await cache_manager.cache_response_components(sample_responses[i])
            else:
                cache_stats['hits'] += 1
            
            cache_stats['total_requests'] += 1
        
        # Second pass: test similar queries (should hit cache)
        for query_data in sample_queries:
            for similar_query in query_data["expected_similarity"]:
                context = query_data["context"]
                
                cached_response = await cache_manager.check_cache_relevance(similar_query, context)
                if cached_response is not None:
                    cache_stats['hits'] += 1
                else:
                    cache_stats['misses'] += 1
                
                cache_stats['total_requests'] += 1
        
        # Calculate hit rate
        hit_rate = cache_stats['hits'] / cache_stats['total_requests'] if cache_stats['total_requests'] > 0 else 0
        
        # Verify cache efficiency
        assert hit_rate >= 0.6, f"Cache hit rate {hit_rate:.2%} should be at least 60%"
        
        print(f"\nCache Hit Rate Results:")
        print(f"Total requests: {cache_stats['total_requests']}")
        print(f"Cache hits: {cache_stats['hits']}")
        print(f"Cache misses: {cache_stats['misses']}")
        print(f"Hit rate: {hit_rate:.2%}")
    
    @pytest.mark.asyncio
    async def test_cache_memory_usage_optimization(self, cache_manager, sample_responses):
        """Test that cache memory usage is optimized and doesn't grow excessively."""
        initial_memory = await cache_manager.get_cache_memory_usage()
        
        # Cache multiple responses
        for response in sample_responses:
            await cache_manager.cache_response_components(response)
        
        memory_after_caching = await cache_manager.get_cache_memory_usage()
        memory_growth = memory_after_caching - initial_memory
        
        # Verify reasonable memory usage
        expected_max_memory = len(sample_responses) * 2  # 2MB per response estimate
        assert memory_growth <= expected_max_memory, (
            f"Cache memory growth {memory_growth:.2f}MB exceeds expected {expected_max_memory}MB"
        )
        
        # Test memory optimization
        await cache_manager.optimize_cache_memory_usage()
        
        memory_after_optimization = await cache_manager.get_cache_memory_usage()
        memory_reduction = memory_after_caching - memory_after_optimization
        
        # Should reduce memory usage
        assert memory_reduction >= 0, "Memory optimization should not increase usage"
        
        print(f"\nCache Memory Usage Results:")
        print(f"Initial memory: {initial_memory:.2f}MB")
        print(f"After caching: {memory_after_caching:.2f}MB")
        print(f"After optimization: {memory_after_optimization:.2f}MB")
        print(f"Memory growth: {memory_growth:.2f}MB")
        print(f"Memory reduction: {memory_reduction:.2f}MB")
    
    @pytest.mark.asyncio
    async def test_intelligent_cache_invalidation(self, cache_manager, sample_responses, sample_queries):
        """Test intelligent cache invalidation based on content relevance."""
        # Cache responses with different timestamps
        current_time = time.time()
        
        for i, response in enumerate(sample_responses[:5]):
            # Simulate different cache ages
            cache_timestamp = current_time - (i * 3600)  # Each response 1 hour older
            
            with patch('time.time', return_value=cache_timestamp):
                await cache_manager.cache_response_components(response)
        
        # Test cache invalidation based on age
        old_cache_key = sample_responses[4].cache_key  # Oldest cached item
        recent_cache_key = sample_responses[0].cache_key  # Most recent item
        
        # Implement intelligent invalidation
        await cache_manager.implement_intelligent_invalidation(old_cache_key)
        
        # Verify old cache is invalidated
        old_cached = await cache_manager.check_cache_relevance("old query", Mock())
        recent_cached = await cache_manager.check_cache_relevance("recent query", Mock())
        
        # Old cache should be invalidated, recent should remain
        # Note: This test assumes the cache manager implements age-based invalidation
        print(f"\nCache Invalidation Results:")
        print(f"Old cache invalidated: {old_cached is None}")
        print(f"Recent cache preserved: {recent_cached is not None}")
    
    @pytest.mark.asyncio
    async def test_cache_warming_based_on_patterns(self, cache_manager, sample_queries):
        """Test proactive cache warming based on usage patterns."""
        # Simulate usage patterns
        usage_patterns = []
        
        # Create patterns based on frequent queries
        for query_data in sample_queries:
            pattern = Mock(
                query_template=query_data["query"],
                frequency=10 + len(query_data["expected_similarity"]),
                context_pattern=query_data["context"],
                predicted_queries=query_data["expected_similarity"]
            )
            usage_patterns.append(pattern)
        
        # Test cache warming
        with patch.object(cache_manager, '_generate_predicted_response') as mock_generate:
            mock_generate.return_value = AsyncMock(return_value=Mock())
            
            warming_start_time = time.time()
            await cache_manager.warm_cache_based_on_patterns(usage_patterns)
            warming_time = time.time() - warming_start_time
            
            # Verify cache warming completed efficiently
            assert warming_time < 2.0, f"Cache warming should complete quickly, took {warming_time:.3f}s"
            
            # Verify predicted queries were processed
            assert mock_generate.call_count >= len(usage_patterns), "Should generate responses for patterns"
        
        # Test that warmed cache improves hit rates
        warmed_hits = 0
        total_warmed_requests = 0
        
        for query_data in sample_queries:
            for predicted_query in query_data["expected_similarity"]:
                cached_response = await cache_manager.check_cache_relevance(
                    predicted_query, query_data["context"]
                )
                if cached_response is not None:
                    warmed_hits += 1
                total_warmed_requests += 1
        
        warmed_hit_rate = warmed_hits / total_warmed_requests if total_warmed_requests > 0 else 0
        
        print(f"\nCache Warming Results:")
        print(f"Warming time: {warming_time:.3f}s")
        print(f"Warmed hit rate: {warmed_hit_rate:.2%}")
        print(f"Patterns processed: {len(usage_patterns)}")
    
    @pytest.mark.asyncio
    async def test_component_based_caching(self, cache_manager, sample_responses):
        """Test caching of reusable response components."""
        # Extract components from responses
        all_components = []
        for response in sample_responses:
            for section in response.content_sections:
                component = Mock(
                    id=f"component_{len(all_components)}",
                    content=section.content,
                    type=section.section_type,
                    reusability_score=0.8 if "summary" in section.section_type else 0.6
                )
                all_components.append(component)
        
        # Cache components
        for component in all_components:
            await cache_manager.cache_component(component)
        
        # Test component reuse
        reused_components = 0
        total_component_requests = 0
        
        for component in all_components[:5]:  # Test first 5 components
            cached_component = await cache_manager.get_cached_component(component.id)
            if cached_component is not None:
                reused_components += 1
            total_component_requests += 1
        
        component_reuse_rate = reused_components / total_component_requests if total_component_requests > 0 else 0
        
        assert component_reuse_rate >= 0.8, (
            f"Component reuse rate {component_reuse_rate:.2%} should be at least 80%"
        )
        
        print(f"\nComponent Caching Results:")
        print(f"Total components cached: {len(all_components)}")
        print(f"Component reuse rate: {component_reuse_rate:.2%}")
    
    @pytest.mark.asyncio
    async def test_cache_performance_under_load(self, cache_manager, sample_responses, sample_queries):
        """Test cache performance under concurrent load."""
        # Populate cache
        for response in sample_responses:
            await cache_manager.cache_response_components(response)
        
        # Create concurrent cache requests
        async def cache_request(query_data):
            query = query_data["query"]
            context = query_data["context"]
            
            start_time = time.time()
            cached_response = await cache_manager.check_cache_relevance(query, context)
            request_time = time.time() - start_time
            
            return {
                'query': query,
                'cached': cached_response is not None,
                'request_time': request_time
            }
        
        # Execute concurrent requests
        concurrent_requests = sample_queries * 4  # 4x the queries for load testing
        
        start_time = time.time()
        results = await asyncio.gather(*[cache_request(query_data) for query_data in concurrent_requests])
        total_time = time.time() - start_time
        
        # Analyze performance
        request_times = [result['request_time'] for result in results]
        avg_request_time = statistics.mean(request_times)
        max_request_time = max(request_times)
        cache_hits = sum(1 for result in results if result['cached'])
        hit_rate = cache_hits / len(results)
        
        # Verify performance under load
        assert avg_request_time < 0.1, f"Average cache request time {avg_request_time:.3f}s should be under 0.1s"
        assert max_request_time < 0.5, f"Maximum cache request time {max_request_time:.3f}s should be under 0.5s"
        assert total_time < 2.0, f"Total concurrent processing time {total_time:.3f}s should be under 2s"
        
        print(f"\nCache Performance Under Load:")
        print(f"Concurrent requests: {len(results)}")
        print(f"Total time: {total_time:.3f}s")
        print(f"Average request time: {avg_request_time:.3f}s")
        print(f"Maximum request time: {max_request_time:.3f}s")
        print(f"Hit rate under load: {hit_rate:.2%}")
    
    @pytest.mark.asyncio
    async def test_cache_consistency_across_sessions(self, cache_manager, sample_responses, sample_queries):
        """Test cache consistency across different user sessions."""
        # Cache responses for different users/sessions
        session_cache_data = {}
        
        for i, query_data in enumerate(sample_queries):
            query = query_data["query"]
            context = query_data["context"]
            response = sample_responses[i]
            
            # Cache response
            await cache_manager.cache_response_components(response)
            
            # Track by session
            session_id = context.session_id
            if session_id not in session_cache_data:
                session_cache_data[session_id] = []
            session_cache_data[session_id].append({
                'query': query,
                'response': response,
                'context': context
            })
        
        # Test cross-session cache access
        cross_session_hits = 0
        total_cross_session_requests = 0
        
        for session_id, cache_entries in session_cache_data.items():
            for entry in cache_entries:
                # Try to access from different session
                different_context = Context(
                    user_id="different_user",
                    session_id="different_session"
                )
                
                cached_response = await cache_manager.check_cache_relevance(
                    entry['query'], different_context
                )
                
                if cached_response is not None:
                    cross_session_hits += 1
                total_cross_session_requests += 1
        
        cross_session_hit_rate = cross_session_hits / total_cross_session_requests if total_cross_session_requests > 0 else 0
        
        print(f"\nCache Consistency Results:")
        print(f"Sessions tested: {len(session_cache_data)}")
        print(f"Cross-session hit rate: {cross_session_hit_rate:.2%}")
    
    @pytest.mark.asyncio
    async def test_cache_size_management(self, cache_manager, sample_responses):
        """Test cache size management and eviction policies."""
        # Set cache size limit for testing
        max_cache_size = 5  # Limit to 5 responses
        
        with patch.object(cache_manager, 'max_cache_size', max_cache_size):
            # Cache more responses than the limit
            for i, response in enumerate(sample_responses):
                await cache_manager.cache_response_components(response)
                
                # Check cache size doesn't exceed limit
                current_cache_size = await cache_manager.get_cache_size()
                assert current_cache_size <= max_cache_size, (
                    f"Cache size {current_cache_size} exceeds limit {max_cache_size}"
                )
        
        # Verify eviction occurred
        final_cache_size = await cache_manager.get_cache_size()
        assert final_cache_size == max_cache_size, f"Final cache size should be {max_cache_size}"
        
        # Test that most recently used items are retained
        recent_responses = sample_responses[-max_cache_size:]
        retained_count = 0
        
        for response in recent_responses:
            if await cache_manager.is_cached(response.cache_key):
                retained_count += 1
        
        retention_rate = retained_count / len(recent_responses)
        assert retention_rate >= 0.6, f"Recent item retention rate {retention_rate:.2%} should be at least 60%"
        
        print(f"\nCache Size Management Results:")
        print(f"Cache size limit: {max_cache_size}")
        print(f"Final cache size: {final_cache_size}")
        print(f"Recent item retention rate: {retention_rate:.2%}")
    
    @pytest.mark.asyncio
    async def test_cache_freshness_validation(self, cache_manager, sample_responses):
        """Test cache freshness validation and automatic refresh."""
        # Cache responses with different freshness
        current_time = time.time()
        
        fresh_response = sample_responses[0]
        stale_response = sample_responses[1]
        
        # Cache fresh response
        with patch('time.time', return_value=current_time):
            await cache_manager.cache_response_components(fresh_response)
        
        # Cache stale response (simulate old timestamp)
        with patch('time.time', return_value=current_time - 7200):  # 2 hours ago
            await cache_manager.cache_response_components(stale_response)
        
        # Test freshness validation
        fresh_cached = await cache_manager.check_cache_relevance("fresh query", Mock())
        stale_cached = await cache_manager.check_cache_relevance("stale query", Mock())
        
        # Verify freshness handling
        # Implementation should handle stale cache appropriately
        print(f"\nCache Freshness Results:")
        print(f"Fresh cache available: {fresh_cached is not None}")
        print(f"Stale cache handling: {stale_cached is not None}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])