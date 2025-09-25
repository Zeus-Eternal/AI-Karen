"""
Tests for End-to-End Optimization - Task 8.3
Tests complete turn pipeline optimization to ensure p95 latency < 3 seconds
with caching strategies, connection pooling, and resource optimization.
"""

import asyncio
import pytest
import time
from typing import List, Dict, Any, AsyncIterator
from unittest.mock import Mock, patch, AsyncMock

from src.ai_karen_engine.services.e2e_optimization import (
    E2EOptimizationService, E2ERequest, E2EResponse, E2EMetrics,
    ConnectionPool, HotQueryCache, CacheType, OptimizationLevel
)

class MockMemoryService:
    """Mock memory service for testing"""
    
    def __init__(self, latency_ms: float = 30.0):
        self.latency_ms = latency_ms
        self.call_count = 0
    
    async def query(self, tenant_id, request, correlation_id=None):
        """Mock memory query"""
        self.call_count += 1
        
        # Simulate latency
        await asyncio.sleep(self.latency_ms / 1000.0)
        
        # Return mock response
        from src.ai_karen_engine.services.unified_memory_service import MemorySearchResponse, ContextHit
        from datetime import datetime
        
        hits = [
            ContextHit(
                id=f"memory_{i}",
                text=f"Memory content {i} related to: {request.query}",
                score=0.9 - i * 0.1,
                tags=[f"tag_{i}"],
                recency="today",
                meta={},
                importance=8 - i,
                decay_tier="short",
                created_at=datetime.utcnow(),
                user_id=request.user_id,
                org_id=request.org_id
            )
            for i in range(min(request.top_k, 5))
        ]
        
        return MemorySearchResponse(
            hits=hits,
            total_found=len(hits),
            query_time_ms=self.latency_ms,
            correlation_id=correlation_id or "test"
        )

class MockLLMService:
    """Mock LLM service for testing"""
    
    def __init__(self, latency_ms: float = 200.0):
        self.latency_ms = latency_ms
        self.call_count = 0
    
    async def generate_optimized(self, prompt: str, stream: bool = True, **kwargs) -> AsyncIterator[str]:
        """Mock LLM generation"""
        self.call_count += 1
        
        # Simulate first token latency
        await asyncio.sleep(self.latency_ms / 1000.0)
        
        if stream:
            # Stream response in chunks
            response = f"This is a response to: {prompt[:50]}..."
            words = response.split()
            
            for word in words:
                yield word + " "
                await asyncio.sleep(0.01)  # Small delay between tokens
        else:
            # Non-streaming response
            yield f"Complete response to: {prompt[:50]}..."

class TestConnectionPool:
    """Test connection pool functionality"""
    
    @pytest.fixture
    def connection_pool(self):
        """Create connection pool"""
        return ConnectionPool(max_connections=5, timeout_seconds=1.0)
    
    @pytest.mark.asyncio
    async def test_acquire_and_release(self, connection_pool):
        """Test basic acquire and release operations"""
        # Should be able to acquire connection
        assert await connection_pool.acquire("test_1") is True
        assert connection_pool.active_connections == 1
        
        # Release connection
        connection_pool.release("test_1")
        assert connection_pool.active_connections == 0
    
    @pytest.mark.asyncio
    async def test_connection_limit(self, connection_pool):
        """Test connection pool limits"""
        # Acquire all connections
        for i in range(5):
            assert await connection_pool.acquire(f"test_{i}") is True
        
        assert connection_pool.active_connections == 5
        
        # Next acquisition should timeout
        assert await connection_pool.acquire("test_overflow") is False
        assert connection_pool.active_connections == 5
    
    @pytest.mark.asyncio
    async def test_concurrent_access(self, connection_pool):
        """Test concurrent connection access"""
        async def acquire_and_release(conn_id: str):
            if await connection_pool.acquire(conn_id):
                await asyncio.sleep(0.1)  # Hold connection briefly
                connection_pool.release(conn_id)
                return True
            return False
        
        # Run multiple concurrent tasks
        tasks = [acquire_and_release(f"conn_{i}") for i in range(10)]
        results = await asyncio.gather(*tasks)
        
        # Some should succeed, some might timeout
        successful = sum(results)
        assert successful > 0
        assert connection_pool.active_connections == 0  # All released
    
    def test_connection_stats(self, connection_pool):
        """Test connection pool statistics"""
        stats = connection_pool.get_stats()
        
        assert "max_connections" in stats
        assert "active_connections" in stats
        assert "utilization" in stats
        assert "metrics" in stats
        
        assert stats["max_connections"] == 5
        assert stats["active_connections"] == 0
        assert stats["utilization"] == 0.0

class TestHotQueryCache:
    """Test hot query cache functionality"""
    
    @pytest.fixture
    def cache(self):
        """Create hot query cache"""
        return HotQueryCache(max_size=10, ttl_seconds=60)
    
    def test_cache_put_and_get(self, cache):
        """Test basic cache operations"""
        # Cache should be empty initially
        result = cache.get(CacheType.MEMORY, user_id="user1", query="test query")
        assert result is None
        
        # Put value in cache
        test_data = [{"id": "mem1", "text": "test memory"}]
        cache.put(CacheType.MEMORY, test_data, user_id="user1", query="test query")
        
        # Should retrieve cached value
        cached_result = cache.get(CacheType.MEMORY, user_id="user1", query="test query")
        assert cached_result == test_data
    
    def test_cache_expiry(self, cache):
        """Test cache expiry"""
        # Set very short TTL
        cache.ttl_seconds = 0.1
        
        test_data = [{"id": "mem1", "text": "test memory"}]
        cache.put(CacheType.MEMORY, test_data, user_id="user1", query="test query")
        
        # Should get value immediately
        assert cache.get(CacheType.MEMORY, user_id="user1", query="test query") == test_data
        
        # Wait for expiry
        time.sleep(0.2)
        
        # Should be expired
        assert cache.get(CacheType.MEMORY, user_id="user1", query="test query") is None
    
    def test_cache_eviction(self, cache):
        """Test cache eviction when full"""
        # Fill cache to capacity
        for i in range(cache.max_size):
            cache.put(CacheType.MEMORY, f"data_{i}", user_id="user1", query=f"query_{i}")
        
        assert cache.stats[CacheType.MEMORY.value]["size"] == cache.max_size
        
        # Add one more item (should evict oldest)
        cache.put(CacheType.MEMORY, "new_data", user_id="user1", query="new_query")
        
        # Cache should still be at max size
        assert cache.stats[CacheType.MEMORY.value]["size"] == cache.max_size
        
        # New item should be in cache
        assert cache.get(CacheType.MEMORY, user_id="user1", query="new_query") == "new_data"
    
    def test_cache_stats(self, cache):
        """Test cache statistics"""
        # Add some data and access it
        cache.put(CacheType.MEMORY, "data1", user_id="user1", query="query1")
        cache.put(CacheType.LLM_RESPONSE, "response1", model="gpt-4", prompt="prompt1")
        
        # Access data (hits)
        cache.get(CacheType.MEMORY, user_id="user1", query="query1")
        cache.get(CacheType.MEMORY, user_id="user1", query="query1")
        
        # Access non-existent data (misses)
        cache.get(CacheType.MEMORY, user_id="user1", query="nonexistent")
        
        stats = cache.get_stats()
        
        assert "total_size" in stats
        assert "by_type" in stats
        assert CacheType.MEMORY.value in stats["by_type"]
        
        memory_stats = stats["by_type"][CacheType.MEMORY.value]
        assert memory_stats["hits"] == 2
        assert memory_stats["misses"] == 1
        assert memory_stats["hit_rate"] == 2/3

class TestE2EOptimizationService:
    """Test end-to-end optimization service"""
    
    @pytest.fixture
    def e2e_service(self):
        """Create E2E optimization service"""
        service = E2EOptimizationService(
            optimization_level=OptimizationLevel.BALANCED,
            max_connections=5,
            cache_size=100,
            cache_ttl_seconds=300
        )
        # Don't start background tasks in tests
        return service
    
    @pytest.fixture
    def mock_services(self):
        """Create mock services"""
        memory_service = MockMemoryService(latency_ms=20.0)
        llm_service = MockLLMService(latency_ms=100.0)
        return memory_service, llm_service
    
    def test_service_initialization(self, e2e_service):
        """Test service initialization"""
        assert e2e_service.optimization_level == OptimizationLevel.BALANCED
        assert e2e_service.connection_pool is not None
        assert e2e_service.hot_cache is not None
        assert len(e2e_service.performance_targets) > 0
    
    def test_set_services(self, e2e_service, mock_services):
        """Test service dependency injection"""
        memory_service, llm_service = mock_services
        
        e2e_service.set_services(
            memory_service=memory_service,
            llm_service=llm_service
        )
        
        assert e2e_service.memory_service == memory_service
        assert e2e_service.llm_service == llm_service
    
    @pytest.mark.asyncio
    async def test_optimized_memory_query(self, e2e_service, mock_services):
        """Test optimized memory query with caching"""
        memory_service, _ = mock_services
        e2e_service.set_services(memory_service=memory_service)
        
        request = E2ERequest(
            user_id="test_user",
            query="test query"
        )
        
        # First call should hit the service
        results1, cache_hit1 = await e2e_service._optimized_memory_query(
            request, "test_tenant", "test_correlation"
        )
        
        assert len(results1) > 0
        assert cache_hit1 is False  # First call is not a cache hit
        assert memory_service.call_count == 1
        
        # Second call should hit the cache
        results2, cache_hit2 = await e2e_service._optimized_memory_query(
            request, "test_tenant", "test_correlation"
        )
        
        assert results2 == results1  # Same results
        assert cache_hit2 is True   # Second call is a cache hit
        assert memory_service.call_count == 1  # Service not called again
    
    @pytest.mark.asyncio
    async def test_optimized_context_building(self, e2e_service):
        """Test optimized context building with caching"""
        request = E2ERequest(
            user_id="test_user",
            query="test query"
        )
        
        memory_results = [
            {"id": "mem1", "text": "Memory 1", "score": 0.9},
            {"id": "mem2", "text": "Memory 2", "score": 0.8}
        ]
        
        # First call should build context
        context1, cache_hit1 = await e2e_service._optimized_context_building(
            request, memory_results, "test_correlation"
        )
        
        assert "query" in context1
        assert "memories" in context1
        assert len(context1["memories"]) > 0
        assert cache_hit1 is False
        
        # Second call should hit cache
        context2, cache_hit2 = await e2e_service._optimized_context_building(
            request, memory_results, "test_correlation"
        )
        
        assert context2 == context1
        assert cache_hit2 is True
    
    @pytest.mark.asyncio
    async def test_process_e2e_request(self, e2e_service, mock_services):
        """Test complete E2E request processing"""
        memory_service, llm_service = mock_services
        e2e_service.set_services(
            memory_service=memory_service,
            llm_service=llm_service
        )
        
        request = E2ERequest(
            user_id="test_user",
            query="What is the weather like?",
            stream=True
        )
        
        # Process request
        response_parts = []
        start_time = time.time()
        
        async for chunk in e2e_service.process_e2e_request(request, "test_tenant"):
            response_parts.append(chunk)
        
        total_time = (time.time() - start_time) * 1000
        
        # Verify response
        assert len(response_parts) > 0
        assert total_time < 3000  # Should meet 3 second SLO
        
        # Verify services were called
        assert memory_service.call_count == 1
        assert llm_service.call_count == 1
        
        # Verify metrics were recorded
        assert len(e2e_service.metrics_history) > 0
        
        latest_metrics = e2e_service.metrics_history[-1]
        assert latest_metrics.total_latency_ms > 0
        assert latest_metrics.memory_query_latency_ms > 0
        assert latest_metrics.llm_generation_latency_ms > 0
    
    @pytest.mark.asyncio
    async def test_e2e_performance_targets(self, e2e_service, mock_services):
        """Test that E2E performance meets targets"""
        # Use fast mock services
        memory_service = MockMemoryService(latency_ms=10.0)  # Very fast
        llm_service = MockLLMService(latency_ms=50.0)        # Fast
        
        e2e_service.set_services(
            memory_service=memory_service,
            llm_service=llm_service
        )
        
        # Process multiple requests to get statistical data
        latencies = []
        
        for i in range(10):
            request = E2ERequest(
                user_id="test_user",
                query=f"Test query {i}",
                stream=True
            )
            
            start_time = time.time()
            
            response_parts = []
            async for chunk in e2e_service.process_e2e_request(request, "test_tenant"):
                response_parts.append(chunk)
            
            total_time = (time.time() - start_time) * 1000
            latencies.append(total_time)
        
        # Calculate p95 latency
        sorted_latencies = sorted(latencies)
        p95_latency = sorted_latencies[int(len(sorted_latencies) * 0.95)]
        
        # Should meet SLO target of < 3000ms
        assert p95_latency < 3000.0, f"P95 E2E latency {p95_latency:.2f}ms exceeds 3000ms target"
        
        # Should also be reasonable for fast services
        assert p95_latency < 1000.0, f"P95 latency {p95_latency:.2f}ms is too high for fast services"
    
    def test_performance_report(self, e2e_service):
        """Test performance report generation"""
        # Add some test metrics
        from src.ai_karen_engine.services.e2e_optimization import E2EMetrics
        from datetime import datetime
        
        for i in range(10):
            metrics = E2EMetrics(
                correlation_id=f"test_{i}",
                total_latency_ms=1000.0 + i * 100,
                memory_query_latency_ms=30.0 + i * 2,
                context_build_latency_ms=10.0 + i,
                llm_generation_latency_ms=800.0 + i * 80,
                first_token_latency_ms=200.0 + i * 20,
                tokens_generated=50 + i * 5,
                cache_hits={"memory": i % 3 == 0, "context": i % 4 == 0},
                memory_results_count=5,
                context_tokens_estimate=200
            )
            e2e_service._record_e2e_metrics(metrics)
        
        report = e2e_service.get_performance_report()
        
        assert "summary" in report
        assert "latency_metrics" in report
        assert "slo_compliance" in report
        assert "cache_stats" in report
        assert "connection_pool_stats" in report
        
        # Check summary statistics
        summary = report["summary"]
        assert summary["total_requests"] == 10
        assert 0 <= summary["memory_cache_hit_rate"] <= 1
        assert summary["error_rate"] == 0  # No errors in test data
        
        # Check latency metrics
        if "total" in report["latency_metrics"]:
            total_metrics = report["latency_metrics"]["total"]
            assert "avg_ms" in total_metrics
            assert "p95_ms" in total_metrics
            assert total_metrics["p95_ms"] > total_metrics["avg_ms"]
        
        # Check SLO compliance
        if "total_latency" in report["slo_compliance"]:
            slo_compliance = report["slo_compliance"]["total_latency"]
            assert "target_ms" in slo_compliance
            assert "actual_p95_ms" in slo_compliance
            assert "is_met" in slo_compliance
    
    @pytest.mark.asyncio
    async def test_benchmark_e2e_performance(self, e2e_service, mock_services):
        """Test E2E performance benchmarking"""
        memory_service, llm_service = mock_services
        e2e_service.set_services(
            memory_service=memory_service,
            llm_service=llm_service
        )
        
        # Create test requests
        test_requests = [
            E2ERequest(
                user_id="test_user",
                query=f"Benchmark query {i}",
                stream=False  # Use non-streaming for simpler testing
            )
            for i in range(5)
        ]
        
        # Run benchmark
        results = await e2e_service.benchmark_e2e_performance(test_requests, "test_tenant")
        
        assert "test_requests" in results
        assert "results" in results
        assert "summary" in results
        
        assert results["test_requests"] == 5
        assert len(results["results"]) == 5
        
        # Check that all requests succeeded
        successful_results = [r for r in results["results"] if r["success"]]
        assert len(successful_results) == 5
        
        # Check summary statistics
        summary = results["summary"]
        assert summary["success_rate"] == 1.0
        assert summary["avg_latency_ms"] > 0
        assert summary["p95_latency_ms"] >= summary["avg_latency_ms"]
        assert "slo_compliance" in summary

class TestIntegration:
    """Integration tests for E2E optimization"""
    
    @pytest.mark.asyncio
    async def test_caching_reduces_latency(self):
        """Test that caching reduces subsequent request latency"""
        # Create service with caching enabled
        service = E2EOptimizationService(
            optimization_level=OptimizationLevel.AGGRESSIVE,
            cache_size=1000,
            cache_ttl_seconds=300
        )
        
        # Set up mock services with some latency
        memory_service = MockMemoryService(latency_ms=50.0)
        llm_service = MockLLMService(latency_ms=200.0)
        service.set_services(memory_service=memory_service, llm_service=llm_service)
        
        request = E2ERequest(
            user_id="test_user",
            query="What is machine learning?",
            stream=False
        )
        
        # First request (cold)
        start_time = time.time()
        response_parts_1 = []
        async for chunk in service.process_e2e_request(request, "test_tenant"):
            response_parts_1.append(chunk)
        first_request_time = (time.time() - start_time) * 1000
        
        # Second request (should hit cache)
        start_time = time.time()
        response_parts_2 = []
        async for chunk in service.process_e2e_request(request, "test_tenant"):
            response_parts_2.append(chunk)
        second_request_time = (time.time() - start_time) * 1000
        
        # Second request should be faster due to caching
        # (though LLM generation will still take time)
        assert second_request_time <= first_request_time
        
        # Memory service should only be called once due to caching
        assert memory_service.call_count == 1
    
    @pytest.mark.asyncio
    async def test_connection_pool_prevents_overload(self):
        """Test that connection pool prevents system overload"""
        # Create service with small connection pool
        service = E2EOptimizationService(
            max_connections=2,  # Very small pool
            cache_size=10
        )
        
        # Set up mock services
        memory_service = MockMemoryService(latency_ms=100.0)  # Slower service
        llm_service = MockLLMService(latency_ms=200.0)
        service.set_services(memory_service=memory_service, llm_service=llm_service)
        
        # Create multiple concurrent requests
        async def make_request(request_id: int):
            request = E2ERequest(
                user_id="test_user",
                query=f"Concurrent query {request_id}",
                stream=False
            )
            
            try:
                response_parts = []
                async for chunk in service.process_e2e_request(request, "test_tenant"):
                    response_parts.append(chunk)
                return {"success": True, "response_length": len("".join(response_parts))}
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        # Run concurrent requests (more than connection pool size)
        tasks = [make_request(i) for i in range(5)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Some requests should succeed, some might fail due to connection limits
        successful_results = [r for r in results if isinstance(r, dict) and r.get("success")]
        
        # At least some should succeed
        assert len(successful_results) > 0
        
        # Connection pool should not be overloaded
        pool_stats = service.connection_pool.get_stats()
        assert pool_stats["active_connections"] == 0  # All connections released

if __name__ == "__main__":
    pytest.main([__file__, "-v"])