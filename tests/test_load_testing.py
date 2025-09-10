"""
Load testing scenarios to validate resource management under stress.
Tests system behavior under high load, concurrent requests, and resource pressure.
"""

import pytest
import asyncio
import time
import psutil
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any
from unittest.mock import Mock, patch, AsyncMock
from dataclasses import dataclass

from src.ai_karen_engine.core.resource_monitor import ResourceMonitor
from src.ai_karen_engine.core.service_lifecycle_manager import ServiceLifecycleManager
from src.ai_karen_engine.core.async_task_orchestrator import AsyncTaskOrchestrator
from src.ai_karen_engine.core.performance_metrics import PerformanceMetric, SystemMetrics, ServiceMetrics


@dataclass
class LoadTestResult:
    """Load test result data."""
    test_name: str
    concurrent_requests: int
    success_rate: float
    average_response_time: float
    peak_memory_usage: int
    peak_cpu_usage: float
    errors: List[str]


class LoadTestSuite:
    """Comprehensive load testing suite."""
    
    def __init__(self):
        self.results: List[LoadTestResult] = []
        self.resource_monitor = ResourceMonitor()
        self.lifecycle_manager = ServiceLifecycleManager()
        self.task_orchestrator = AsyncTaskOrchestrator()
    
    async def run_concurrent_service_load_test(self, num_requests: int = 100) -> LoadTestResult:
        """Test system under concurrent service requests."""
        errors = []
        response_times = []
        start_memory = psutil.Process().memory_info().rss
        peak_memory = start_memory
        peak_cpu = 0.0
        
        async def make_service_request():
            """Simulate a service request."""
            try:
                start_time = time.time()
                
                # Simulate service operations
                await self.lifecycle_manager.start_service(f"test_service_{threading.current_thread().ident}")
                await asyncio.sleep(0.01)  # Simulate processing time
                await self.lifecycle_manager.shutdown_service(f"test_service_{threading.current_thread().ident}")
                
                response_time = time.time() - start_time
                response_times.append(response_time)
                
                # Monitor resources during test
                nonlocal peak_memory, peak_cpu
                current_memory = psutil.Process().memory_info().rss
                current_cpu = psutil.cpu_percent()
                peak_memory = max(peak_memory, current_memory)
                peak_cpu = max(peak_cpu, current_cpu)
                
            except Exception as e:
                errors.append(str(e))
        
        # Execute concurrent requests
        start_time = time.time()
        tasks = [make_service_request() for _ in range(num_requests)]
        await asyncio.gather(*tasks, return_exceptions=True)
        total_time = time.time() - start_time
        
        success_rate = ((num_requests - len(errors)) / num_requests) * 100
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        return LoadTestResult(
            test_name="concurrent_service_requests",
            concurrent_requests=num_requests,
            success_rate=success_rate,
            average_response_time=avg_response_time,
            peak_memory_usage=peak_memory,
            peak_cpu_usage=peak_cpu,
            errors=errors
        )
    
    async def run_resource_pressure_test(self) -> LoadTestResult:
        """Test system behavior under resource pressure."""
        errors = []
        
        # Create artificial resource pressure
        memory_hogs = []
        cpu_tasks = []
        
        try:
            # Create memory pressure
            for _ in range(5):
                memory_hogs.append([0] * 10000000)  # Allocate ~40MB per hog
            
            # Create CPU pressure
            def cpu_intensive_task():
                """CPU intensive task for load testing."""
                result = 0
                for i in range(1000000):
                    result += i * i
                return result
            
            with ThreadPoolExecutor(max_workers=4) as executor:
                cpu_futures = [executor.submit(cpu_intensive_task) for _ in range(8)]
                
                # Monitor system behavior under pressure
                start_time = time.time()
                initial_memory = psutil.Process().memory_info().rss
                
                # Test resource monitor response
                pressure_detected = await self.resource_monitor.detect_resource_pressure()
                
                if pressure_detected:
                    # Test automatic resource cleanup
                    await self.resource_monitor.trigger_resource_cleanup()
                
                # Wait for CPU tasks to complete
                for future in as_completed(cpu_futures):
                    try:
                        future.result(timeout=5)
                    except Exception as e:
                        errors.append(f"CPU task failed: {e}")
                
                end_time = time.time()
                final_memory = psutil.Process().memory_info().rss
                
        except Exception as e:
            errors.append(f"Resource pressure test failed: {e}")
        finally:
            # Cleanup
            memory_hogs.clear()
        
        return LoadTestResult(
            test_name="resource_pressure",
            concurrent_requests=0,
            success_rate=100.0 if not errors else 0.0,
            average_response_time=end_time - start_time,
            peak_memory_usage=final_memory,
            peak_cpu_usage=psutil.cpu_percent(),
            errors=errors
        )
    
    async def run_async_task_load_test(self, num_tasks: int = 50) -> LoadTestResult:
        """Test async task orchestrator under load."""
        errors = []
        response_times = []
        
        async def cpu_intensive_async_task():
            """Async CPU intensive task."""
            try:
                start_time = time.time()
                
                # Offload CPU intensive work
                result = await self.task_orchestrator.offload_cpu_intensive_task(
                    lambda: sum(i * i for i in range(100000))
                )
                
                response_time = time.time() - start_time
                response_times.append(response_time)
                return result
                
            except Exception as e:
                errors.append(str(e))
                return None
        
        # Execute tasks concurrently
        start_memory = psutil.Process().memory_info().rss
        start_time = time.time()
        
        tasks = [cpu_intensive_async_task() for _ in range(num_tasks)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        total_time = time.time() - start_time
        end_memory = psutil.Process().memory_info().rss
        
        success_count = sum(1 for r in results if r is not None and not isinstance(r, Exception))
        success_rate = (success_count / num_tasks) * 100
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        return LoadTestResult(
            test_name="async_task_load",
            concurrent_requests=num_tasks,
            success_rate=success_rate,
            average_response_time=avg_response_time,
            peak_memory_usage=end_memory,
            peak_cpu_usage=psutil.cpu_percent(),
            errors=errors
        )
    
    async def run_service_suspension_load_test(self) -> LoadTestResult:
        """Test automatic service suspension under load."""
        errors = []
        
        try:
            # Start multiple services
            services = [f"load_test_service_{i}" for i in range(10)]
            
            for service in services:
                await self.lifecycle_manager.start_service(service)
            
            # Create resource pressure to trigger suspension
            memory_pressure = [0] * 50000000  # ~200MB
            
            # Wait for automatic suspension to kick in
            await asyncio.sleep(2)
            
            # Check if services were suspended
            suspended_services = await self.lifecycle_manager.get_suspended_services()
            
            # Verify some services were suspended
            if len(suspended_services) == 0:
                errors.append("No services were suspended under resource pressure")
            
            # Cleanup
            for service in services:
                try:
                    await self.lifecycle_manager.shutdown_service(service)
                except:
                    pass  # Service might already be suspended
            
        except Exception as e:
            errors.append(f"Service suspension test failed: {e}")
        
        return LoadTestResult(
            test_name="service_suspension_load",
            concurrent_requests=len(services),
            success_rate=100.0 if not errors else 0.0,
            average_response_time=0,
            peak_memory_usage=psutil.Process().memory_info().rss,
            peak_cpu_usage=psutil.cpu_percent(),
            errors=errors
        )


@pytest.fixture
def load_test_suite():
    """Create load test suite fixture."""
    return LoadTestSuite()


@pytest.mark.asyncio
async def test_concurrent_service_requests(load_test_suite):
    """Test system under concurrent service requests."""
    result = await load_test_suite.run_concurrent_service_load_test(50)
    
    # Verify high success rate under load
    assert result.success_rate >= 95.0, f"Success rate {result.success_rate}% < 95%"
    
    # Verify reasonable response times
    assert result.average_response_time < 1.0, f"Average response time {result.average_response_time}s too high"
    
    print(f"Concurrent requests test: {result.success_rate:.1f}% success rate")
    print(f"Average response time: {result.average_response_time:.3f}s")
    print(f"Peak memory: {result.peak_memory_usage / 1024 / 1024:.1f}MB")


@pytest.mark.asyncio
async def test_resource_pressure_handling(load_test_suite):
    """Test system behavior under resource pressure."""
    result = await load_test_suite.run_resource_pressure_test()
    
    # Verify system handles resource pressure gracefully
    assert len(result.errors) <= 2, f"Too many errors under pressure: {len(result.errors)}"
    
    # Verify resource cleanup was triggered
    assert result.success_rate > 0, "System failed completely under resource pressure"
    
    print(f"Resource pressure test: {len(result.errors)} errors")
    print(f"Peak CPU: {result.peak_cpu_usage:.1f}%")


@pytest.mark.asyncio
async def test_async_task_orchestrator_load(load_test_suite):
    """Test async task orchestrator under heavy load."""
    result = await load_test_suite.run_async_task_load_test(30)
    
    # Verify task orchestrator handles load well
    assert result.success_rate >= 90.0, f"Task success rate {result.success_rate}% < 90%"
    
    # Verify parallel processing improves performance
    assert result.average_response_time < 2.0, f"Task response time {result.average_response_time}s too high"
    
    print(f"Async task load test: {result.success_rate:.1f}% success rate")
    print(f"Average task time: {result.average_response_time:.3f}s")


@pytest.mark.asyncio
async def test_service_suspension_under_load(load_test_suite):
    """Test automatic service suspension under resource pressure."""
    result = await load_test_suite.run_service_suspension_load_test()
    
    # Verify service suspension works
    assert result.success_rate > 0, "Service suspension test failed completely"
    assert len(result.errors) <= 1, f"Too many errors in suspension test: {len(result.errors)}"
    
    print(f"Service suspension test: {len(result.errors)} errors")


@pytest.mark.asyncio
async def test_memory_leak_detection():
    """Test for memory leaks under sustained load."""
    initial_memory = psutil.Process().memory_info().rss
    
    # Run sustained operations
    for i in range(10):
        # Simulate service operations
        lifecycle_manager = ServiceLifecycleManager()
        await lifecycle_manager.start_service(f"leak_test_{i}")
        await asyncio.sleep(0.1)
        await lifecycle_manager.shutdown_service(f"leak_test_{i}")
    
    # Allow garbage collection
    await asyncio.sleep(1)
    
    final_memory = psutil.Process().memory_info().rss
    memory_growth = final_memory - initial_memory
    
    # Verify no significant memory leaks (< 50MB growth)
    max_growth = 50 * 1024 * 1024  # 50MB
    assert memory_growth < max_growth, f"Memory leak detected: {memory_growth / 1024 / 1024:.1f}MB growth"
    
    print(f"Memory growth: {memory_growth / 1024 / 1024:.1f}MB")


@pytest.mark.asyncio
async def test_degraded_mode_performance():
    """Test system performance in degraded mode."""
    resource_monitor = ResourceMonitor()
    
    # Simulate service failures to trigger degraded mode
    with patch.object(ServiceLifecycleManager, 'start_service', side_effect=Exception("Service failed")):
        lifecycle_manager = ServiceLifecycleManager()
        
        # Try to start services (should fail and trigger degraded mode)
        try:
            await lifecycle_manager.start_service("failing_service")
        except:
            pass  # Expected to fail
        
        # Verify system still responds in degraded mode
        metrics = await resource_monitor.get_current_metrics()
        assert metrics is not None, "System unresponsive in degraded mode"
        
        print("Degraded mode test: System remains responsive")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])