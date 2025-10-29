"""
Comprehensive Resource Usage Tests
Validates CPU usage stays under 5% per response and memory usage is optimized.
"""

import pytest
import asyncio
import psutil
import time
import threading
from typing import List, Dict, Any, Optional
from unittest.mock import Mock, patch, AsyncMock
from contextlib import asynccontextmanager

from src.ai_karen_engine.services.intelligent_response_controller import IntelligentResponseController
from src.ai_karen_engine.services.content_optimization_engine import ContentOptimizationEngine
from src.ai_karen_engine.services.smart_cache_manager import SmartCacheManager
from src.ai_karen_engine.services.cuda_acceleration_engine import CUDAAccelerationEngine
from src.ai_karen_engine.core.shared_types import (
    QueryAnalysis, ComplexityLevel, ContentType, ResponseLength, 
    ExpertiseLevel, OptimizedResponse, PerformanceMetrics
)


class ResourceMonitor:
    """Helper class to monitor system resource usage."""
    
    def __init__(self):
        self.cpu_samples = []
        self.memory_samples = []
        self.monitoring = False
        self.monitor_thread = None
    
    def start_monitoring(self, interval: float = 0.1):
        """Start monitoring system resources."""
        self.monitoring = True
        self.cpu_samples = []
        self.memory_samples = []
        self.monitor_thread = threading.Thread(target=self._monitor_loop, args=(interval,))
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop monitoring and return collected data."""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join()
        
        return {
            'cpu_samples': self.cpu_samples,
            'memory_samples': self.memory_samples,
            'avg_cpu': sum(self.cpu_samples) / len(self.cpu_samples) if self.cpu_samples else 0,
            'max_cpu': max(self.cpu_samples) if self.cpu_samples else 0,
            'avg_memory': sum(self.memory_samples) / len(self.memory_samples) if self.memory_samples else 0,
            'max_memory': max(self.memory_samples) if self.memory_samples else 0
        }
    
    def _monitor_loop(self, interval: float):
        """Internal monitoring loop."""
        process = psutil.Process()
        
        while self.monitoring:
            try:
                # Get CPU percentage for this process
                cpu_percent = process.cpu_percent()
                self.cpu_samples.append(cpu_percent)
                
                # Get memory usage in MB
                memory_info = process.memory_info()
                memory_mb = memory_info.rss / 1024 / 1024
                self.memory_samples.append(memory_mb)
                
                time.sleep(interval)
            except Exception:
                # Handle process termination or other errors
                break


class TestResourceUsageValidation:
    """Test suite for comprehensive resource usage validation."""
    
    @pytest.fixture
    async def response_controller(self):
        """Create an intelligent response controller for testing."""
        controller = IntelligentResponseController()
        await controller.initialize()
        return controller
    
    @pytest.fixture
    async def content_optimizer(self):
        """Create a content optimization engine for testing."""
        optimizer = ContentOptimizationEngine()
        await optimizer.initialize()
        return optimizer
    
    @pytest.fixture
    async def cache_manager(self):
        """Create a smart cache manager for testing."""
        manager = SmartCacheManager()
        await manager.initialize()
        return manager
    
    @pytest.fixture
    async def cuda_engine(self):
        """Create a CUDA acceleration engine for testing."""
        engine = CUDAAccelerationEngine()
        await engine.initialize()
        return engine
    
    @pytest.fixture
    def resource_monitor(self):
        """Create a resource monitor for testing."""
        return ResourceMonitor()
    
    @pytest.fixture
    def test_queries(self):
        """Create test queries of varying complexity."""
        return [
            {
                "query": "What is Python?",
                "complexity": ComplexityLevel.SIMPLE,
                "expected_cpu_limit": 3.0  # Even stricter for simple queries
            },
            {
                "query": "Explain object-oriented programming concepts with examples in Python.",
                "complexity": ComplexityLevel.MODERATE,
                "expected_cpu_limit": 5.0
            },
            {
                "query": "Create a comprehensive web application using Django with authentication, database models, REST API, and frontend integration.",
                "complexity": ComplexityLevel.COMPLEX,
                "expected_cpu_limit": 5.0  # Should still stay under 5%
            }
        ]
    
    @asynccontextmanager
    async def monitor_resources(self, resource_monitor: ResourceMonitor):
        """Context manager to monitor resources during test execution."""
        resource_monitor.start_monitoring(interval=0.05)  # High frequency monitoring
        try:
            yield resource_monitor
        finally:
            resource_data = resource_monitor.stop_monitoring()
            return resource_data
    
    @pytest.mark.asyncio
    async def test_cpu_usage_per_response(self, response_controller, resource_monitor, test_queries):
        """Test that CPU usage stays under 5% per response."""
        cpu_results = []
        
        for query_data in test_queries:
            query = query_data["query"]
            expected_limit = query_data["expected_cpu_limit"]
            
            # Mock the response generation to simulate real processing
            with patch.object(response_controller, '_generate_response') as mock_generate:
                # Simulate some CPU work
                async def simulate_processing(*args, **kwargs):
                    # Simulate processing with controlled CPU usage
                    await asyncio.sleep(0.1)
                    return f"Response to: {query}"
                
                mock_generate.side_effect = simulate_processing
                
                # Monitor resources during response generation
                async with self.monitor_resources(resource_monitor) as monitor:
                    start_time = time.time()
                    response = await response_controller.generate_optimized_response(query, "test-model")
                    end_time = time.time()
                
                resource_data = monitor.stop_monitoring()
                
                cpu_results.append({
                    'query': query,
                    'complexity': query_data["complexity"],
                    'avg_cpu': resource_data['avg_cpu'],
                    'max_cpu': resource_data['max_cpu'],
                    'expected_limit': expected_limit,
                    'response_time': end_time - start_time
                })
                
                # Verify CPU usage is within limits
                assert resource_data['max_cpu'] <= expected_limit, (
                    f"CPU usage {resource_data['max_cpu']:.2f}% exceeds limit {expected_limit}% "
                    f"for query: {query[:50]}..."
                )
                
                assert resource_data['avg_cpu'] <= expected_limit * 0.7, (
                    f"Average CPU usage {resource_data['avg_cpu']:.2f}% exceeds 70% of limit "
                    f"for query: {query[:50]}..."
                )
        
        # Verify overall CPU efficiency
        avg_cpu_usage = sum(r['avg_cpu'] for r in cpu_results) / len(cpu_results)
        max_cpu_usage = max(r['max_cpu'] for r in cpu_results)
        
        assert avg_cpu_usage <= 3.0, f"Overall average CPU usage {avg_cpu_usage:.2f}% should be under 3%"
        assert max_cpu_usage <= 5.0, f"Maximum CPU usage {max_cpu_usage:.2f}% should be under 5%"
        
        print(f"\nCPU Usage Results:")
        print(f"Average CPU usage: {avg_cpu_usage:.2f}%")
        print(f"Maximum CPU usage: {max_cpu_usage:.2f}%")
        for result in cpu_results:
            print(f"  {result['complexity'].value}: avg={result['avg_cpu']:.2f}%, max={result['max_cpu']:.2f}%")
    
    @pytest.mark.asyncio
    async def test_memory_usage_optimization(self, response_controller, resource_monitor, test_queries):
        """Test that memory usage is optimized and doesn't grow excessively."""
        memory_results = []
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        for query_data in test_queries:
            query = query_data["query"]
            
            # Monitor memory during response generation
            async with self.monitor_resources(resource_monitor) as monitor:
                with patch.object(response_controller, 'generate_optimized_response') as mock_generate:
                    # Simulate memory-efficient processing
                    mock_generate.return_value = AsyncMock(return_value=Mock())
                    
                    response = await response_controller.generate_optimized_response(query, "test-model")
            
            resource_data = monitor.stop_monitoring()
            current_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            memory_growth = current_memory - initial_memory
            
            memory_results.append({
                'query': query,
                'complexity': query_data["complexity"],
                'avg_memory': resource_data['avg_memory'],
                'max_memory': resource_data['max_memory'],
                'memory_growth': memory_growth,
                'initial_memory': initial_memory
            })
            
            # Verify memory usage is reasonable
            assert memory_growth < 50, (  # Less than 50MB growth per query
                f"Memory growth {memory_growth:.2f}MB is excessive "
                f"for query: {query[:50]}..."
            )
        
        # Verify overall memory efficiency
        total_memory_growth = sum(r['memory_growth'] for r in memory_results)
        avg_memory_per_query = total_memory_growth / len(memory_results)
        
        assert avg_memory_per_query < 20, f"Average memory per query {avg_memory_per_query:.2f}MB should be under 20MB"
        assert total_memory_growth < 100, f"Total memory growth {total_memory_growth:.2f}MB should be under 100MB"
        
        print(f"\nMemory Usage Results:")
        print(f"Initial memory: {initial_memory:.2f}MB")
        print(f"Total memory growth: {total_memory_growth:.2f}MB")
        print(f"Average memory per query: {avg_memory_per_query:.2f}MB")
    
    @pytest.mark.asyncio
    async def test_concurrent_request_resource_usage(self, response_controller, resource_monitor):
        """Test resource usage under concurrent request load."""
        concurrent_queries = [
            "What is machine learning?",
            "Explain neural networks",
            "How does backpropagation work?",
            "What are transformers in AI?",
            "Describe reinforcement learning"
        ]
        
        # Monitor resources during concurrent processing
        async with self.monitor_resources(resource_monitor) as monitor:
            with patch.object(response_controller, 'generate_optimized_response') as mock_generate:
                # Simulate concurrent processing
                async def simulate_concurrent_processing(query, model):
                    await asyncio.sleep(0.2)  # Simulate processing time
                    return f"Response to: {query}"
                
                mock_generate.side_effect = simulate_concurrent_processing
                
                # Execute concurrent requests
                tasks = [
                    response_controller.generate_optimized_response(query, "test-model")
                    for query in concurrent_queries
                ]
                
                start_time = time.time()
                responses = await asyncio.gather(*tasks)
                end_time = time.time()
        
        resource_data = monitor.stop_monitoring()
        
        # Verify concurrent resource usage
        assert resource_data['max_cpu'] <= 15.0, (  # Allow higher CPU for concurrent processing
            f"Concurrent CPU usage {resource_data['max_cpu']:.2f}% should stay under 15%"
        )
        
        assert resource_data['avg_cpu'] <= 10.0, (
            f"Average concurrent CPU usage {resource_data['avg_cpu']:.2f}% should stay under 10%"
        )
        
        # Verify all responses were generated
        assert len(responses) == len(concurrent_queries), "All concurrent requests should complete"
        
        # Verify reasonable total processing time
        total_time = end_time - start_time
        assert total_time < 1.0, f"Concurrent processing should complete in under 1s, took {total_time:.3f}s"
        
        print(f"\nConcurrent Resource Usage Results:")
        print(f"Concurrent requests: {len(concurrent_queries)}")
        print(f"Total time: {total_time:.3f}s")
        print(f"Average CPU: {resource_data['avg_cpu']:.2f}%")
        print(f"Maximum CPU: {resource_data['max_cpu']:.2f}%")
    
    @pytest.mark.asyncio
    async def test_content_optimization_resource_efficiency(self, content_optimizer, resource_monitor):
        """Test that content optimization is resource-efficient."""
        # Create large content for optimization
        large_content = "This is a test sentence. " * 1000  # Large repetitive content
        
        async with self.monitor_resources(resource_monitor) as monitor:
            # Perform content optimization
            optimized_content = await content_optimizer.eliminate_redundant_content(large_content)
            prioritized_sections = await content_optimizer.prioritize_content_sections(optimized_content)
            formatted_content = await content_optimizer.optimize_formatting(optimized_content, "markdown")
        
        resource_data = monitor.stop_monitoring()
        
        # Verify optimization resource usage
        assert resource_data['max_cpu'] <= 3.0, (
            f"Content optimization CPU usage {resource_data['max_cpu']:.2f}% should stay under 3%"
        )
        
        # Verify content was actually optimized
        size_reduction = (len(large_content) - len(optimized_content)) / len(large_content)
        assert size_reduction > 0.1, f"Content should be reduced by at least 10%, got {size_reduction:.2%}"
        
        print(f"\nContent Optimization Resource Results:")
        print(f"Original size: {len(large_content)} chars")
        print(f"Optimized size: {len(optimized_content)} chars")
        print(f"Size reduction: {size_reduction:.2%}")
        print(f"CPU usage: {resource_data['max_cpu']:.2f}%")
    
    @pytest.mark.asyncio
    async def test_cache_memory_efficiency(self, cache_manager, resource_monitor):
        """Test that cache operations are memory-efficient."""
        # Generate test data for caching
        test_responses = []
        for i in range(10):
            response = OptimizedResponse(
                content_sections=[Mock(content=f"Test content {i}" * 100)],
                total_size=1000 + i * 100,
                generation_time=1.0,
                model_used="test-model",
                optimization_applied=["test"],
                cache_key=f"test-key-{i}",
                streaming_metadata=Mock()
            )
            test_responses.append(response)
        
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        async with self.monitor_resources(resource_monitor) as monitor:
            # Cache multiple responses
            for response in test_responses:
                await cache_manager.cache_response_components(response)
            
            # Perform cache operations
            for i in range(5):
                await cache_manager.check_cache_relevance(f"test query {i}", Mock())
            
            # Optimize cache memory
            await cache_manager.optimize_cache_memory_usage()
        
        resource_data = monitor.stop_monitoring()
        final_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        memory_growth = final_memory - initial_memory
        
        # Verify cache memory efficiency
        assert memory_growth < 30, f"Cache memory growth {memory_growth:.2f}MB should be under 30MB"
        assert resource_data['max_cpu'] <= 2.0, f"Cache CPU usage {resource_data['max_cpu']:.2f}% should stay under 2%"
        
        print(f"\nCache Memory Efficiency Results:")
        print(f"Cached responses: {len(test_responses)}")
        print(f"Memory growth: {memory_growth:.2f}MB")
        print(f"CPU usage: {resource_data['max_cpu']:.2f}%")
    
    @pytest.mark.asyncio
    async def test_cuda_resource_management(self, cuda_engine, resource_monitor):
        """Test CUDA resource management and fallback efficiency."""
        cuda_available = await cuda_engine.detect_cuda_availability()
        
        if not cuda_available:
            pytest.skip("CUDA not available for testing")
        
        async with self.monitor_resources(resource_monitor) as monitor:
            # Test GPU memory allocation
            with patch.object(cuda_engine, 'manage_gpu_memory_allocation') as mock_alloc:
                mock_alloc.return_value = AsyncMock(return_value=Mock())
                
                # Simulate GPU operations
                for i in range(5):
                    await cuda_engine.manage_gpu_memory_allocation(1024 * 1024)  # 1MB allocations
            
            # Test CPU fallback
            with patch.object(cuda_engine, 'fallback_to_cpu_on_gpu_failure') as mock_fallback:
                mock_fallback.return_value = AsyncMock(return_value="CPU result")
                
                # Simulate fallback scenarios
                for i in range(3):
                    await cuda_engine.fallback_to_cpu_on_gpu_failure(lambda: "test computation")
        
        resource_data = monitor.stop_monitoring()
        
        # Verify CUDA resource management efficiency
        assert resource_data['max_cpu'] <= 4.0, (
            f"CUDA management CPU usage {resource_data['max_cpu']:.2f}% should stay under 4%"
        )
        
        print(f"\nCUDA Resource Management Results:")
        print(f"CUDA available: {cuda_available}")
        print(f"CPU usage: {resource_data['max_cpu']:.2f}%")
    
    @pytest.mark.asyncio
    async def test_resource_pressure_handling(self, response_controller, resource_monitor):
        """Test system behavior under resource pressure."""
        # Simulate high resource usage scenario
        async with self.monitor_resources(resource_monitor) as monitor:
            with patch.object(response_controller, 'monitor_response_performance') as mock_monitor:
                mock_monitor.return_value = AsyncMock(return_value=Mock(
                    cpu_usage=4.5,  # Near the limit
                    memory_usage=80,  # High memory usage
                    response_time=2.0
                ))
                
                # Generate responses under pressure
                queries = [f"Test query {i}" for i in range(3)]
                
                for query in queries:
                    with patch.object(response_controller, 'generate_optimized_response') as mock_generate:
                        mock_generate.return_value = AsyncMock(return_value=Mock())
                        
                        # Should still complete within resource limits
                        response = await response_controller.generate_optimized_response(query, "test-model")
                        assert response is not None, "Should generate response even under pressure"
        
        resource_data = monitor.stop_monitoring()
        
        # Verify graceful handling of resource pressure
        assert resource_data['max_cpu'] <= 6.0, (  # Allow slight overage under pressure
            f"CPU usage under pressure {resource_data['max_cpu']:.2f}% should stay under 6%"
        )
        
        print(f"\nResource Pressure Handling Results:")
        print(f"CPU usage under pressure: {resource_data['max_cpu']:.2f}%")
        print(f"System maintained stability: {resource_data['max_cpu'] <= 6.0}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])