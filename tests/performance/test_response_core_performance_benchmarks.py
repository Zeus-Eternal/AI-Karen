"""
Performance benchmarks for Response Core local vs cloud routing.

This module implements detailed performance benchmarking to measure
the effectiveness of local-first routing with cloud acceleration.
"""

import pytest
import asyncio
import time
import statistics
from typing import Dict, List, Any, Optional, Tuple
from unittest.mock import Mock, patch
from dataclasses import dataclass

from src.ai_karen_engine.core.response import (
    ResponseOrchestrator,
    PipelineConfig,
)
from src.ai_karen_engine.core.response.protocols import Analyzer, Memory, LLMClient


@dataclass
class BenchmarkResult:
    """Benchmark result data structure."""
    test_name: str
    local_avg_time: float
    local_min_time: float
    local_max_time: float
    local_p95_time: float
    cloud_avg_time: float
    cloud_min_time: float
    cloud_max_time: float
    cloud_p95_time: float
    local_advantage_percent: float
    local_success_rate: float
    cloud_success_rate: float
    local_throughput: float
    cloud_throughput: float
    context_size_tested: int
    iterations: int


class BenchmarkAnalyzer:
    """High-performance analyzer for benchmarking."""
    
    def __init__(self, processing_time: float = 0.005):
        self.processing_time = processing_time
    
    def detect_intent(self, text: str) -> str:
        time.sleep(self.processing_time)
        
        if "optimize" in text.lower():
            return "optimize_code"
        elif "debug" in text.lower():
            return "debug_error"
        elif "explain" in text.lower():
            return "documentation"
        else:
            return "general_assist"
    
    def sentiment(self, text: str) -> str:
        time.sleep(self.processing_time)
        return "neutral"
    
    def entities(self, text: str) -> Dict[str, Any]:
        time.sleep(self.processing_time)
        return {}


class BenchmarkMemory:
    """High-performance memory for benchmarking."""
    
    def __init__(self, processing_time: float = 0.01):
        self.processing_time = processing_time
    
    def recall(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        time.sleep(self.processing_time)
        return [
            {
                "text": f"Benchmark context for: {query[:30]}",
                "relevance_score": 0.9,
                "timestamp": time.time(),
                "source": "memory"
            }
        ]
    
    def save_turn(self, user_msg: str, assistant_msg: str, meta: Dict[str, Any]) -> None:
        pass  # No-op for benchmarking


class LocalLLMClient:
    """Simulates fast local LLM client."""
    
    def __init__(self, response_time: float = 0.05, context_penalty: float = 0.0001):
        self.response_time = response_time
        self.context_penalty = context_penalty
        self.generation_count = 0
    
    def generate(self, messages: List[Dict[str, str]], **kwargs) -> str:
        self.generation_count += 1
        
        # Calculate context size
        context_size = sum(len(msg.get("content", "")) for msg in messages)
        
        # Simulate processing time with context penalty
        processing_time = self.response_time + (context_size * self.context_penalty)
        time.sleep(processing_time)
        
        return f"Local LLM response {self.generation_count}: Optimized for speed and privacy."


class CloudLLMClient:
    """Simulates cloud LLM client with network latency."""
    
    def __init__(self, response_time: float = 0.2, network_latency: float = 0.05):
        self.response_time = response_time
        self.network_latency = network_latency
        self.generation_count = 0
    
    def generate(self, messages: List[Dict[str, str]], **kwargs) -> str:
        self.generation_count += 1
        
        # Simulate network latency (both ways)
        time.sleep(self.network_latency * 2)
        
        # Simulate cloud processing time
        time.sleep(self.response_time)
        
        return f"Cloud LLM response {self.generation_count}: High-quality response with advanced capabilities."


class ResponseCorePerformanceBenchmarks:
    """Comprehensive performance benchmarking suite."""
    
    def __init__(self):
        self.benchmark_results: List[BenchmarkResult] = []
    
    def create_local_orchestrator(self) -> ResponseOrchestrator:
        """Create orchestrator optimized for local processing."""
        config = PipelineConfig(
            local_only=True,
            enable_metrics=False,
            enable_memory_persistence=False,
            local_model_preference="local:tinyllama-1.1b"
        )
        
        return ResponseOrchestrator(
            analyzer=BenchmarkAnalyzer(processing_time=0.005),
            memory=BenchmarkMemory(processing_time=0.01),
            llm_client=LocalLLMClient(response_time=0.05),
            config=config
        )
    
    def create_cloud_orchestrator(self) -> ResponseOrchestrator:
        """Create orchestrator configured for cloud processing."""
        config = PipelineConfig(
            local_only=False,
            cloud_routing_threshold=0,  # Always use cloud
            enable_metrics=False,
            enable_memory_persistence=False
        )
        
        return ResponseOrchestrator(
            analyzer=BenchmarkAnalyzer(processing_time=0.005),
            memory=BenchmarkMemory(processing_time=0.01),
            llm_client=CloudLLMClient(response_time=0.2, network_latency=0.05),
            config=config
        )
    
    def benchmark_response_time_comparison(
        self,
        iterations: int = 20,
        context_size: int = 1000
    ) -> BenchmarkResult:
        """Benchmark response time comparison between local and cloud."""
        local_orchestrator = self.create_local_orchestrator()
        cloud_orchestrator = self.create_cloud_orchestrator()
        
        # Generate test content with specified context size
        test_content = self._generate_test_content(context_size)
        
        # Benchmark local processing
        local_times = []
        local_successes = 0
        
        for i in range(iterations):
            try:
                start_time = time.time()
                response = local_orchestrator.respond(f"Local test {i}: {test_content}")
                local_times.append(time.time() - start_time)
                local_successes += 1
            except Exception as e:
                print(f"Local benchmark iteration {i} failed: {e}")
        
        # Benchmark cloud processing
        cloud_times = []
        cloud_successes = 0
        
        for i in range(iterations):
            try:
                start_time = time.time()
                response = cloud_orchestrator.respond(f"Cloud test {i}: {test_content}")
                cloud_times.append(time.time() - start_time)
                cloud_successes += 1
            except Exception as e:
                print(f"Cloud benchmark iteration {i} failed: {e}")
        
        # Calculate statistics
        local_stats = self._calculate_time_statistics(local_times)
        cloud_stats = self._calculate_time_statistics(cloud_times)
        
        # Calculate advantage
        local_advantage = 0
        if cloud_stats["avg"] > 0:
            local_advantage = ((cloud_stats["avg"] - local_stats["avg"]) / cloud_stats["avg"]) * 100
        
        # Calculate throughput (requests per second)
        local_throughput = local_successes / sum(local_times) if local_times else 0
        cloud_throughput = cloud_successes / sum(cloud_times) if cloud_times else 0
        
        return BenchmarkResult(
            test_name=f"response_time_comparison_ctx{context_size}",
            local_avg_time=local_stats["avg"],
            local_min_time=local_stats["min"],
            local_max_time=local_stats["max"],
            local_p95_time=local_stats["p95"],
            cloud_avg_time=cloud_stats["avg"],
            cloud_min_time=cloud_stats["min"],
            cloud_max_time=cloud_stats["max"],
            cloud_p95_time=cloud_stats["p95"],
            local_advantage_percent=local_advantage,
            local_success_rate=(local_successes / iterations) * 100,
            cloud_success_rate=(cloud_successes / iterations) * 100,
            local_throughput=local_throughput,
            cloud_throughput=cloud_throughput,
            context_size_tested=context_size,
            iterations=iterations
        )
    
    def benchmark_context_size_scaling(self) -> List[BenchmarkResult]:
        """Benchmark how performance scales with context size."""
        context_sizes = [500, 1000, 2000, 4000, 8000]
        results = []
        
        for context_size in context_sizes:
            result = self.benchmark_response_time_comparison(
                iterations=10,
                context_size=context_size
            )
            results.append(result)
            self.benchmark_results.append(result)
        
        return results
    
    def benchmark_concurrent_performance(
        self,
        concurrent_requests: int = 10,
        iterations_per_request: int = 3
    ) -> Tuple[BenchmarkResult, BenchmarkResult]:
        """Benchmark concurrent performance for local vs cloud."""
        import threading
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        local_orchestrator = self.create_local_orchestrator()
        cloud_orchestrator = self.create_cloud_orchestrator()
        
        def run_local_requests():
            times = []
            successes = 0
            
            def local_request(request_id: int):
                try:
                    start_time = time.time()
                    response = local_orchestrator.respond(f"Concurrent local request {request_id}")
                    return time.time() - start_time, True
                except Exception:
                    return 0, False
            
            with ThreadPoolExecutor(max_workers=concurrent_requests) as executor:
                futures = [
                    executor.submit(local_request, i)
                    for i in range(concurrent_requests * iterations_per_request)
                ]
                
                for future in as_completed(futures):
                    duration, success = future.result()
                    if success:
                        times.append(duration)
                        successes += 1
            
            return times, successes
        
        def run_cloud_requests():
            times = []
            successes = 0
            
            def cloud_request(request_id: int):
                try:
                    start_time = time.time()
                    response = cloud_orchestrator.respond(f"Concurrent cloud request {request_id}")
                    return time.time() - start_time, True
                except Exception:
                    return 0, False
            
            with ThreadPoolExecutor(max_workers=concurrent_requests) as executor:
                futures = [
                    executor.submit(cloud_request, i)
                    for i in range(concurrent_requests * iterations_per_request)
                ]
                
                for future in as_completed(futures):
                    duration, success = future.result()
                    if success:
                        times.append(duration)
                        successes += 1
            
            return times, successes
        
        # Run concurrent benchmarks
        start_time = time.time()
        local_times, local_successes = run_local_requests()
        local_total_time = time.time() - start_time
        
        start_time = time.time()
        cloud_times, cloud_successes = run_cloud_requests()
        cloud_total_time = time.time() - start_time
        
        # Calculate statistics
        local_stats = self._calculate_time_statistics(local_times)
        cloud_stats = self._calculate_time_statistics(cloud_times)
        
        total_requests = concurrent_requests * iterations_per_request
        
        local_result = BenchmarkResult(
            test_name=f"concurrent_local_{concurrent_requests}x{iterations_per_request}",
            local_avg_time=local_stats["avg"],
            local_min_time=local_stats["min"],
            local_max_time=local_stats["max"],
            local_p95_time=local_stats["p95"],
            cloud_avg_time=0,
            cloud_min_time=0,
            cloud_max_time=0,
            cloud_p95_time=0,
            local_advantage_percent=0,
            local_success_rate=(local_successes / total_requests) * 100,
            cloud_success_rate=0,
            local_throughput=local_successes / local_total_time if local_total_time > 0 else 0,
            cloud_throughput=0,
            context_size_tested=1000,
            iterations=total_requests
        )
        
        cloud_result = BenchmarkResult(
            test_name=f"concurrent_cloud_{concurrent_requests}x{iterations_per_request}",
            local_avg_time=0,
            local_min_time=0,
            local_max_time=0,
            local_p95_time=0,
            cloud_avg_time=cloud_stats["avg"],
            cloud_min_time=cloud_stats["min"],
            cloud_max_time=cloud_stats["max"],
            cloud_p95_time=cloud_stats["p95"],
            local_advantage_percent=0,
            local_success_rate=0,
            cloud_success_rate=(cloud_successes / total_requests) * 100,
            local_throughput=0,
            cloud_throughput=cloud_successes / cloud_total_time if cloud_total_time > 0 else 0,
            context_size_tested=1000,
            iterations=total_requests
        )
        
        return local_result, cloud_result
    
    def benchmark_routing_decision_overhead(self) -> BenchmarkResult:
        """Benchmark the overhead of routing decisions."""
        # Create orchestrator with routing logic
        config = PipelineConfig(
            local_only=False,
            cloud_routing_threshold=2000,
            enable_metrics=False
        )
        
        routing_orchestrator = ResponseOrchestrator(
            analyzer=BenchmarkAnalyzer(processing_time=0.005),
            memory=BenchmarkMemory(processing_time=0.01),
            llm_client=LocalLLMClient(response_time=0.05),
            config=config
        )
        
        # Test with different context sizes to trigger different routing decisions
        test_cases = [
            ("small_context", "Short request", 1000),  # Should route to local
            ("large_context", "X" * 3000, 3000),      # Should route to cloud (but use local client)
        ]
        
        routing_times = []
        routing_successes = 0
        
        for case_name, content, expected_size in test_cases:
            for i in range(10):
                try:
                    start_time = time.time()
                    response = routing_orchestrator.respond(f"{case_name} {i}: {content}")
                    routing_times.append(time.time() - start_time)
                    routing_successes += 1
                except Exception as e:
                    print(f"Routing benchmark {case_name} {i} failed: {e}")
        
        # Compare with simple local-only orchestrator
        local_orchestrator = self.create_local_orchestrator()
        local_times = []
        local_successes = 0
        
        for case_name, content, expected_size in test_cases:
            for i in range(10):
                try:
                    start_time = time.time()
                    response = local_orchestrator.respond(f"{case_name} {i}: {content}")
                    local_times.append(time.time() - start_time)
                    local_successes += 1
                except Exception as e:
                    print(f"Local benchmark {case_name} {i} failed: {e}")
        
        # Calculate overhead
        routing_stats = self._calculate_time_statistics(routing_times)
        local_stats = self._calculate_time_statistics(local_times)
        
        overhead_percent = 0
        if local_stats["avg"] > 0:
            overhead_percent = ((routing_stats["avg"] - local_stats["avg"]) / local_stats["avg"]) * 100
        
        return BenchmarkResult(
            test_name="routing_decision_overhead",
            local_avg_time=local_stats["avg"],
            local_min_time=local_stats["min"],
            local_max_time=local_stats["max"],
            local_p95_time=local_stats["p95"],
            cloud_avg_time=routing_stats["avg"],
            cloud_min_time=routing_stats["min"],
            cloud_max_time=routing_stats["max"],
            cloud_p95_time=routing_stats["p95"],
            local_advantage_percent=-overhead_percent,  # Negative because routing is slower
            local_success_rate=(local_successes / 20) * 100,
            cloud_success_rate=(routing_successes / 20) * 100,
            local_throughput=local_successes / sum(local_times) if local_times else 0,
            cloud_throughput=routing_successes / sum(routing_times) if routing_times else 0,
            context_size_tested=2000,
            iterations=20
        )
    
    def _calculate_time_statistics(self, times: List[float]) -> Dict[str, float]:
        """Calculate time statistics from a list of times."""
        if not times:
            return {"avg": 0, "min": 0, "max": 0, "p95": 0}
        
        times_sorted = sorted(times)
        p95_index = int(len(times_sorted) * 0.95)
        
        return {
            "avg": statistics.mean(times),
            "min": min(times),
            "max": max(times),
            "p95": times_sorted[p95_index] if p95_index < len(times_sorted) else max(times)
        }
    
    def _generate_test_content(self, target_size: int) -> str:
        """Generate test content of approximately target size."""
        base_content = "Optimize this code for better performance and maintainability. "
        repetitions = max(1, target_size // len(base_content))
        return base_content * repetitions


# Pytest fixtures and test functions

@pytest.fixture
def benchmark_suite():
    """Create benchmark suite fixture."""
    return ResponseCorePerformanceBenchmarks()


@pytest.mark.asyncio
async def test_basic_response_time_benchmark(benchmark_suite):
    """Test basic response time comparison between local and cloud."""
    result = benchmark_suite.benchmark_response_time_comparison(iterations=15)
    
    # Validate local is faster
    assert result.local_avg_time < result.cloud_avg_time, "Local should be faster than cloud"
    assert result.local_advantage_percent > 0, "Local should have performance advantage"
    
    # Validate success rates
    assert result.local_success_rate >= 95.0, f"Local success rate {result.local_success_rate}% too low"
    assert result.cloud_success_rate >= 95.0, f"Cloud success rate {result.cloud_success_rate}% too low"
    
    # Validate performance requirements
    assert result.local_avg_time < 0.5, f"Local average time {result.local_avg_time:.3f}s too high"
    assert result.local_p95_time < 1.0, f"Local P95 time {result.local_p95_time:.3f}s too high"
    
    print(f"Response time benchmark: Local {result.local_avg_time:.3f}s, "
          f"Cloud {result.cloud_avg_time:.3f}s, Advantage {result.local_advantage_percent:.1f}%")


@pytest.mark.asyncio
async def test_context_size_scaling_benchmark(benchmark_suite):
    """Test how performance scales with context size."""
    results = benchmark_suite.benchmark_context_size_scaling()
    
    assert len(results) >= 5, "Should test multiple context sizes"
    
    # Validate that local maintains advantage across context sizes
    for result in results:
        assert result.local_advantage_percent > 0, \
            f"Local should be faster at context size {result.context_size_tested}"
        assert result.local_avg_time < 1.0, \
            f"Local time {result.local_avg_time:.3f}s too high at context size {result.context_size_tested}"
    
    # Validate scaling behavior
    local_times = [r.local_avg_time for r in results]
    context_sizes = [r.context_size_tested for r in results]
    
    # Local times should scale reasonably with context size
    max_local_time = max(local_times)
    min_local_time = min(local_times)
    scaling_factor = max_local_time / min_local_time if min_local_time > 0 else 1
    
    assert scaling_factor < 5.0, f"Local scaling factor {scaling_factor:.1f} too high"
    
    print(f"Context scaling: {len(results)} sizes tested, "
          f"scaling factor {scaling_factor:.1f}, max time {max_local_time:.3f}s")


@pytest.mark.asyncio
async def test_concurrent_performance_benchmark(benchmark_suite):
    """Test concurrent performance for local vs cloud."""
    local_result, cloud_result = benchmark_suite.benchmark_concurrent_performance(
        concurrent_requests=8,
        iterations_per_request=2
    )
    
    # Validate concurrent performance
    assert local_result.local_success_rate >= 90.0, \
        f"Local concurrent success rate {local_result.local_success_rate}% too low"
    assert cloud_result.cloud_success_rate >= 90.0, \
        f"Cloud concurrent success rate {cloud_result.cloud_success_rate}% too low"
    
    # Validate throughput
    assert local_result.local_throughput > 5.0, \
        f"Local throughput {local_result.local_throughput:.1f} req/s too low"
    assert local_result.local_throughput > cloud_result.cloud_throughput, \
        "Local should have higher throughput than cloud"
    
    # Validate response times under concurrency
    assert local_result.local_p95_time < 2.0, \
        f"Local P95 time {local_result.local_p95_time:.3f}s too high under concurrency"
    
    print(f"Concurrent performance: Local {local_result.local_throughput:.1f} req/s, "
          f"Cloud {cloud_result.cloud_throughput:.1f} req/s")


@pytest.mark.asyncio
async def test_routing_decision_overhead_benchmark(benchmark_suite):
    """Test the overhead of routing decisions."""
    result = benchmark_suite.benchmark_routing_decision_overhead()
    
    # Routing overhead should be minimal
    overhead_percent = abs(result.local_advantage_percent)
    assert overhead_percent < 10.0, f"Routing overhead {overhead_percent:.1f}% too high"
    
    # Both configurations should have high success rates
    assert result.local_success_rate >= 95.0, "Local-only success rate too low"
    assert result.cloud_success_rate >= 95.0, "Routing success rate too low"
    
    # Response times should still be reasonable
    assert result.cloud_avg_time < 0.5, f"Routing average time {result.cloud_avg_time:.3f}s too high"
    
    print(f"Routing overhead: {overhead_percent:.1f}%, "
          f"Local {result.local_avg_time:.3f}s, Routing {result.cloud_avg_time:.3f}s")


@pytest.mark.asyncio
async def test_performance_requirements_validation(benchmark_suite):
    """Validate that all performance requirements are met."""
    # Run comprehensive benchmarks
    basic_result = benchmark_suite.benchmark_response_time_comparison(iterations=20)
    scaling_results = benchmark_suite.benchmark_context_size_scaling()
    local_concurrent, cloud_concurrent = benchmark_suite.benchmark_concurrent_performance()
    routing_result = benchmark_suite.benchmark_routing_decision_overhead()
    
    # Requirement 1.1: Local-first operation should be faster
    assert basic_result.local_advantage_percent > 20.0, \
        f"Local advantage {basic_result.local_advantage_percent:.1f}% < 20%"
    
    # Requirement 2.1: Response times should be reasonable
    assert basic_result.local_avg_time < 0.5, "Local response time requirement not met"
    assert basic_result.local_p95_time < 1.0, "Local P95 response time requirement not met"
    
    # Requirement 5.1: Concurrent handling should scale
    assert local_concurrent.local_throughput > 10.0, "Throughput requirement not met"
    assert local_concurrent.local_success_rate >= 95.0, "Concurrent success rate requirement not met"
    
    # Requirement 5.2: Context scaling should be reasonable
    max_scaling_time = max(r.local_avg_time for r in scaling_results)
    assert max_scaling_time < 1.0, "Context scaling requirement not met"
    
    # Requirement 5.3: Routing overhead should be minimal
    routing_overhead = abs(routing_result.local_advantage_percent)
    assert routing_overhead < 15.0, "Routing overhead requirement not met"
    
    print(f"Performance requirements validation: All requirements met")
    print(f"  Local advantage: {basic_result.local_advantage_percent:.1f}%")
    print(f"  Local response time: {basic_result.local_avg_time:.3f}s")
    print(f"  Concurrent throughput: {local_concurrent.local_throughput:.1f} req/s")
    print(f"  Max scaling time: {max_scaling_time:.3f}s")
    print(f"  Routing overhead: {routing_overhead:.1f}%")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])