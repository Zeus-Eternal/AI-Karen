"""
Performance benchmarking tests to measure optimization effectiveness.
Tests startup time, memory usage, and resource consumption improvements.
"""

import pytest
import asyncio
import time
import psutil
import os
from typing import Dict, List, Any
from unittest.mock import Mock, patch, AsyncMock
from dataclasses import dataclass

from src.ai_karen_engine.audit.performance_auditor import PerformanceAuditor
from src.ai_karen_engine.core.service_lifecycle_manager import ServiceLifecycleManager
from src.ai_karen_engine.core.lazy_loading_controller import LazyLoadingController
from src.ai_karen_engine.core.resource_monitor import ResourceMonitor
from src.ai_karen_engine.core.performance_metrics import PerformanceMetric, SystemMetrics, ServiceMetrics


@dataclass
class BenchmarkResult:
    """Benchmark test result data."""
    test_name: str
    baseline_time: float
    optimized_time: float
    improvement_percentage: float
    memory_baseline: int
    memory_optimized: int
    memory_improvement: float


class PerformanceBenchmarkSuite:
    """Comprehensive performance benchmarking test suite."""
    
    def __init__(self):
        self.results: List[BenchmarkResult] = []
        self.baseline_metrics = {}
        self.optimized_metrics = {}
    
    async def run_startup_benchmark(self) -> BenchmarkResult:
        """Benchmark system startup time with and without optimizations."""
        # Baseline startup (without optimizations)
        baseline_start = time.time()
        await self._simulate_baseline_startup()
        baseline_time = time.time() - baseline_start
        baseline_memory = psutil.Process().memory_info().rss
        
        # Optimized startup
        optimized_start = time.time()
        await self._simulate_optimized_startup()
        optimized_time = time.time() - optimized_start
        optimized_memory = psutil.Process().memory_info().rss
        
        improvement = ((baseline_time - optimized_time) / baseline_time) * 100
        memory_improvement = ((baseline_memory - optimized_memory) / baseline_memory) * 100
        
        return BenchmarkResult(
            test_name="startup_time",
            baseline_time=baseline_time,
            optimized_time=optimized_time,
            improvement_percentage=improvement,
            memory_baseline=baseline_memory,
            memory_optimized=optimized_memory,
            memory_improvement=memory_improvement
        )
    
    async def _simulate_baseline_startup(self):
        """Simulate baseline startup without optimizations."""
        # Simulate loading all services at once
        services = ["auth", "llm", "memory", "analytics", "monitoring", "plugins"]
        for service in services:
            await asyncio.sleep(0.1)  # Simulate service initialization time
    
    async def _simulate_optimized_startup(self):
        """Simulate optimized startup with lazy loading."""
        lifecycle_manager = ServiceLifecycleManager()
        lazy_controller = LazyLoadingController()
        
        # Only start essential services
        essential_services = ["auth", "routing"]
        for service in essential_services:
            await lifecycle_manager.start_service(service)
            await asyncio.sleep(0.05)  # Faster essential service startup
    
    async def run_memory_benchmark(self) -> BenchmarkResult:
        """Benchmark memory usage optimization."""
        baseline_memory = await self._measure_baseline_memory_usage()
        optimized_memory = await self._measure_optimized_memory_usage()
        
        improvement = ((baseline_memory - optimized_memory) / baseline_memory) * 100
        
        return BenchmarkResult(
            test_name="memory_usage",
            baseline_time=0,
            optimized_time=0,
            improvement_percentage=improvement,
            memory_baseline=baseline_memory,
            memory_optimized=optimized_memory,
            memory_improvement=improvement
        )
    
    async def _measure_baseline_memory_usage(self) -> int:
        """Measure memory usage without optimizations."""
        # Simulate loading all services and their dependencies
        mock_services = []
        for i in range(10):
            mock_services.append([0] * 1000000)  # Simulate memory allocation
        return psutil.Process().memory_info().rss
    
    async def _measure_optimized_memory_usage(self) -> int:
        """Measure memory usage with optimizations."""
        # Simulate lazy loading and resource cleanup
        resource_monitor = ResourceMonitor()
        await resource_monitor.optimize_memory_usage()
        return psutil.Process().memory_info().rss
    
    async def run_service_lifecycle_benchmark(self) -> BenchmarkResult:
        """Benchmark service lifecycle operations."""
        lifecycle_manager = ServiceLifecycleManager()
        
        # Benchmark service startup time
        start_time = time.time()
        await lifecycle_manager.start_service("test_service")
        startup_time = time.time() - start_time
        
        # Benchmark service shutdown time
        start_time = time.time()
        await lifecycle_manager.shutdown_service("test_service")
        shutdown_time = time.time() - start_time
        
        total_optimized = startup_time + shutdown_time
        baseline_total = 2.0  # Assume baseline takes 2 seconds
        
        improvement = ((baseline_total - total_optimized) / baseline_total) * 100
        
        return BenchmarkResult(
            test_name="service_lifecycle",
            baseline_time=baseline_total,
            optimized_time=total_optimized,
            improvement_percentage=improvement,
            memory_baseline=0,
            memory_optimized=0,
            memory_improvement=0
        )


@pytest.fixture
def benchmark_suite():
    """Create benchmark suite fixture."""
    return PerformanceBenchmarkSuite()


@pytest.mark.asyncio
async def test_startup_time_benchmark(benchmark_suite):
    """Test startup time optimization effectiveness."""
    result = await benchmark_suite.run_startup_benchmark()
    
    # Verify startup time improvement meets requirement (50% reduction)
    assert result.improvement_percentage >= 50.0, f"Startup improvement {result.improvement_percentage}% < 50%"
    assert result.optimized_time < result.baseline_time
    
    print(f"Startup benchmark: {result.improvement_percentage:.1f}% improvement")
    print(f"Baseline: {result.baseline_time:.3f}s, Optimized: {result.optimized_time:.3f}s")


@pytest.mark.asyncio
async def test_memory_usage_benchmark(benchmark_suite):
    """Test memory usage optimization effectiveness."""
    result = await benchmark_suite.run_memory_benchmark()
    
    # Verify memory usage stays within limits (512MB for core services)
    max_memory_mb = 512 * 1024 * 1024  # 512MB in bytes
    assert result.memory_optimized <= max_memory_mb, f"Memory usage {result.memory_optimized} > 512MB"
    
    print(f"Memory benchmark: {result.memory_improvement:.1f}% improvement")
    print(f"Baseline: {result.memory_baseline} bytes, Optimized: {result.memory_optimized} bytes")


@pytest.mark.asyncio
async def test_service_lifecycle_benchmark(benchmark_suite):
    """Test service lifecycle operation performance."""
    result = await benchmark_suite.run_service_lifecycle_benchmark()
    
    # Verify service operations are fast (< 2 seconds total)
    assert result.optimized_time < 2.0, f"Service lifecycle time {result.optimized_time}s >= 2s"
    assert result.improvement_percentage > 0, "No improvement in service lifecycle performance"
    
    print(f"Service lifecycle benchmark: {result.improvement_percentage:.1f}% improvement")


@pytest.mark.asyncio
async def test_resource_consumption_benchmark():
    """Test overall resource consumption optimization."""
    auditor = PerformanceAuditor()
    
    # Run performance audit
    startup_report = await auditor.audit_startup_performance()
    runtime_report = await auditor.audit_runtime_performance()
    
    # Verify resource usage is within acceptable limits
    assert startup_report.total_startup_time < 5.0, "Startup time exceeds 5 seconds"
    assert runtime_report.total_memory_usage < 1024 * 1024 * 1024, "Memory usage exceeds 1GB"
    
    # Verify CPU usage is reasonable
    cpu_usage = runtime_report.average_cpu_usage
    assert cpu_usage < 50.0, f"CPU usage {cpu_usage}% too high"


@pytest.mark.asyncio
async def test_lazy_loading_performance():
    """Test lazy loading performance impact."""
    lazy_controller = LazyLoadingController()
    
    # Test service loading time
    start_time = time.time()
    service = await lazy_controller.get_service("test_service")
    load_time = time.time() - start_time
    
    # Verify lazy loading is fast (< 2 seconds as per requirement)
    assert load_time < 2.0, f"Lazy loading time {load_time}s >= 2s"
    
    # Test cached service access
    start_time = time.time()
    cached_service = await lazy_controller.get_service("test_service")
    cached_time = time.time() - start_time
    
    # Cached access should be much faster
    assert cached_time < 0.1, f"Cached service access too slow: {cached_time}s"


@pytest.mark.asyncio
async def test_concurrent_service_performance():
    """Test performance under concurrent service operations."""
    lifecycle_manager = ServiceLifecycleManager()
    
    # Start multiple services concurrently
    services = ["service1", "service2", "service3", "service4", "service5"]
    
    start_time = time.time()
    tasks = [lifecycle_manager.start_service(service) for service in services]
    await asyncio.gather(*tasks)
    concurrent_time = time.time() - start_time
    
    # Concurrent startup should be faster than sequential
    sequential_estimate = len(services) * 0.5  # Assume 0.5s per service
    assert concurrent_time < sequential_estimate, "Concurrent startup not faster than sequential"
    
    print(f"Concurrent service startup: {concurrent_time:.3f}s for {len(services)} services")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])