"""
Load testing for health check performance.

Tests the performance characteristics of health monitoring including:
- Health check execution time under load
- Concurrent health check handling
- Memory usage during monitoring
- Scalability with multiple extensions
"""

import pytest
import asyncio
import time
import psutil
import statistics
from unittest.mock import Mock, AsyncMock
from concurrent.futures import ThreadPoolExecutor
import threading

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))

from server.extension_health_monitor import (
    ExtensionServiceMonitor,
    ServiceStatus,
    ExtensionStatus
)


class TestHealthCheckPerformance:
    """Performance tests for health check system."""

    @pytest.fixture
    def performance_extension_manager(self):
        """Create extension manager optimized for performance testing."""
        manager = Mock()
        manager.is_initialized.return_value = True
        manager.registry = Mock()
        manager.check_extension_health = AsyncMock(return_value=True)
        manager.reload_extension = AsyncMock()
        manager.reinitialize = AsyncMock()
        
        # Create multiple extensions for load testing
        extensions = {}
        for i in range(100):  # 100 extensions for load testing
            extensions[f'extension_{i}'] = Mock(
                status=ExtensionStatus.ACTIVE,
                instance=Mock(),
                manifest=Mock(name=f'extension_{i}')
            )
        
        manager.registry.get_all_extensions.return_value = extensions
        return manager

    @pytest.fixture
    def performance_monitor(self, performance_extension_manager):
        """Create service monitor for performance testing."""
        return ExtensionServiceMonitor(performance_extension_manager)

    @pytest.mark.asyncio
    async def test_single_health_check_performance(self, performance_monitor):
        """Test performance of single health check cycle."""
        monitor = performance_monitor
        
        # Warm up
        await monitor.perform_health_checks()
        
        # Measure performance
        start_time = time.time()
        await monitor.perform_health_checks()
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        # Health check should complete within reasonable time
        assert execution_time < 1.0, f"Health check took {execution_time:.3f}s, expected < 1.0s"
        
        # Verify all extensions were checked
        assert len(monitor.service_status) >= 100  # 100 extensions + manager

    @pytest.mark.asyncio
    async def test_concurrent_health_checks_performance(self, performance_monitor):
        """Test performance under concurrent health check load."""
        monitor = performance_monitor
        
        # Create multiple concurrent health check tasks
        num_concurrent = 10
        
        async def run_health_check():
            start_time = time.time()
            await monitor.perform_health_checks()
            return time.time() - start_time
        
        # Execute concurrent health checks
        start_time = time.time()
        tasks = [asyncio.create_task(run_health_check()) for _ in range(num_concurrent)]
        execution_times = await asyncio.gather(*tasks)
        total_time = time.time() - start_time
        
        # Analyze performance
        avg_execution_time = statistics.mean(execution_times)
        max_execution_time = max(execution_times)
        
        # Performance assertions
        assert avg_execution_time < 2.0, f"Average execution time {avg_execution_time:.3f}s too high"
        assert max_execution_time < 5.0, f"Max execution time {max_execution_time:.3f}s too high"
        assert total_time < 10.0, f"Total concurrent execution time {total_time:.3f}s too high"

    @pytest.mark.asyncio
    async def test_memory_usage_during_monitoring(self, performance_monitor):
        """Test memory usage during extended monitoring."""
        monitor = performance_monitor
        
        # Get initial memory usage
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Run extended monitoring
        for i in range(50):  # 50 health check cycles
            await monitor.perform_health_checks()
            
            # Occasionally check memory growth
            if i % 10 == 0:
                current_memory = process.memory_info().rss / 1024 / 1024  # MB
                memory_growth = current_memory - initial_memory
                
                # Memory growth should be reasonable
                assert memory_growth < 100, f"Memory growth {memory_growth:.1f}MB too high after {i} cycles"
        
        # Final memory check
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        total_growth = final_memory - initial_memory
        
        assert total_growth < 200, f"Total memory growth {total_growth:.1f}MB too high"

    @pytest.mark.asyncio
    async def test_scalability_with_extension_count(self, performance_extension_manager):
        """Test how performance scales with number of extensions."""
        manager = performance_extension_manager
        
        # Test with different numbers of extensions
        extension_counts = [10, 50, 100, 200, 500]
        performance_results = []
        
        for count in extension_counts:
            # Create extensions for this test
            extensions = {}
            for i in range(count):
                extensions[f'ext_{i}'] = Mock(
                    status=ExtensionStatus.ACTIVE,
                    instance=Mock(),
                    manifest=Mock(name=f'ext_{i}')
                )
            
            manager.registry.get_all_extensions.return_value = extensions
            monitor = ExtensionServiceMonitor(manager)
            
            # Measure performance
            start_time = time.time()
            await monitor.perform_health_checks()
            execution_time = time.time() - start_time
            
            performance_results.append((count, execution_time))
        
        # Analyze scalability
        for i, (count, exec_time) in enumerate(performance_results):
            # Performance should scale reasonably (not exponentially)
            expected_max_time = 0.01 * count  # 10ms per extension max
            assert exec_time < expected_max_time, \
                f"Health check for {count} extensions took {exec_time:.3f}s, expected < {expected_max_time:.3f}s"

    @pytest.mark.asyncio
    async def test_monitoring_loop_performance(self, performance_monitor):
        """Test performance of continuous monitoring loop."""
        monitor = performance_monitor
        
        # Track performance metrics
        execution_times = []
        memory_samples = []
        
        async def performance_tracking_loop():
            process = psutil.Process()
            
            for _ in range(20):  # 20 monitoring cycles
                start_time = time.time()
                await monitor.perform_health_checks()
                execution_time = time.time() - start_time
                
                execution_times.append(execution_time)
                memory_samples.append(process.memory_info().rss / 1024 / 1024)
                
                await asyncio.sleep(0.1)  # Short interval for testing
        
        # Run performance tracking
        await performance_tracking_loop()
        
        # Analyze results
        avg_execution_time = statistics.mean(execution_times)
        max_execution_time = max(execution_times)
        memory_variance = statistics.variance(memory_samples) if len(memory_samples) > 1 else 0
        
        # Performance assertions
        assert avg_execution_time < 1.0, f"Average monitoring cycle time {avg_execution_time:.3f}s too high"
        assert max_execution_time < 2.0, f"Max monitoring cycle time {max_execution_time:.3f}s too high"
        assert memory_variance < 100, f"Memory variance {memory_variance:.1f} indicates memory leak"

    @pytest.mark.asyncio
    async def test_recovery_performance_under_load(self, performance_monitor):
        """Test recovery performance under high load."""
        monitor = performance_monitor
        manager = monitor.extension_manager
        
        # Simulate failures for multiple extensions
        failed_extensions = [f'extension_{i}' for i in range(0, 50, 5)]  # Every 5th extension
        
        # Set failure counts to trigger recovery
        for ext_name in failed_extensions:
            monitor.failure_counts[ext_name] = 3
        
        # Measure recovery performance
        start_time = time.time()
        
        # Trigger recoveries
        recovery_tasks = []
        for ext_name in failed_extensions:
            task = asyncio.create_task(monitor.attempt_extension_recovery(ext_name))
            recovery_tasks.append(task)
        
        await asyncio.gather(*recovery_tasks)
        
        total_recovery_time = time.time() - start_time
        
        # Recovery should complete in reasonable time
        expected_max_time = len(failed_extensions) * 0.1  # 100ms per recovery max
        assert total_recovery_time < expected_max_time, \
            f"Recovery of {len(failed_extensions)} extensions took {total_recovery_time:.3f}s"

    @pytest.mark.asyncio
    async def test_status_reporting_performance(self, performance_monitor):
        """Test performance of status reporting with large datasets."""
        monitor = performance_monitor
        
        # Populate with status data
        await monitor.perform_health_checks()
        
        # Measure status reporting performance
        start_time = time.time()
        
        # Generate multiple status reports
        for _ in range(100):
            status = monitor.get_service_status()
            assert 'services' in status
            assert 'overall_health' in status
        
        total_time = time.time() - start_time
        avg_time_per_report = total_time / 100
        
        # Status reporting should be fast
        assert avg_time_per_report < 0.01, f"Status reporting too slow: {avg_time_per_report:.4f}s per report"

    @pytest.mark.asyncio
    async def test_thread_safety_performance(self, performance_monitor):
        """Test thread safety and performance under concurrent access."""
        monitor = performance_monitor
        
        # Shared results storage
        results = {'execution_times': [], 'errors': []}
        results_lock = threading.Lock()
        
        def run_health_check_sync():
            """Synchronous wrapper for health check."""
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                start_time = time.time()
                loop.run_until_complete(monitor.perform_health_checks())
                execution_time = time.time() - start_time
                
                with results_lock:
                    results['execution_times'].append(execution_time)
                    
            except Exception as e:
                with results_lock:
                    results['errors'].append(str(e))
            finally:
                loop.close()
        
        # Run concurrent health checks from multiple threads
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(run_health_check_sync) for _ in range(10)]
            
            # Wait for completion
            for future in futures:
                future.result(timeout=30)
        
        # Analyze results
        assert len(results['errors']) == 0, f"Thread safety errors: {results['errors']}"
        assert len(results['execution_times']) == 10, "Not all health checks completed"
        
        avg_execution_time = statistics.mean(results['execution_times'])
        assert avg_execution_time < 2.0, f"Thread concurrent execution too slow: {avg_execution_time:.3f}s"

    @pytest.mark.asyncio
    async def test_failure_detection_performance(self, performance_monitor):
        """Test performance of failure detection under various conditions."""
        monitor = performance_monitor
        manager = monitor.extension_manager
        
        # Test scenarios with different failure rates
        failure_scenarios = [
            (0, "no_failures"),
            (10, "low_failure_rate"),
            (50, "high_failure_rate"),
            (90, "critical_failure_rate")
        ]
        
        performance_results = []
        
        for failure_percentage, scenario_name in failure_scenarios:
            # Configure failure simulation
            def health_check_with_failures(name):
                # Simulate failures based on percentage
                import random
                return random.randint(1, 100) > failure_percentage
            
            manager.check_extension_health.side_effect = health_check_with_failures
            
            # Measure performance
            start_time = time.time()
            await monitor.perform_health_checks()
            execution_time = time.time() - start_time
            
            performance_results.append((scenario_name, failure_percentage, execution_time))
        
        # Analyze performance across scenarios
        for scenario_name, failure_rate, exec_time in performance_results:
            # Performance should remain reasonable even with high failure rates
            max_expected_time = 2.0  # 2 seconds max regardless of failure rate
            assert exec_time < max_expected_time, \
                f"Scenario '{scenario_name}' ({failure_rate}% failures) took {exec_time:.3f}s"


class TestHealthCheckBenchmarks:
    """Benchmark tests for health check system."""

    @pytest.mark.asyncio
    async def test_baseline_performance_benchmark(self):
        """Establish baseline performance metrics."""
        # Create minimal setup for baseline
        manager = Mock()
        manager.is_initialized.return_value = True
        manager.registry = Mock()
        manager.registry.get_all_extensions.return_value = {}
        manager.check_extension_health = AsyncMock(return_value=True)
        
        monitor = ExtensionServiceMonitor(manager)
        
        # Measure baseline performance
        times = []
        for _ in range(100):
            start_time = time.time()
            await monitor.perform_health_checks()
            times.append(time.time() - start_time)
        
        # Calculate statistics
        avg_time = statistics.mean(times)
        median_time = statistics.median(times)
        p95_time = sorted(times)[int(0.95 * len(times))]
        
        # Log benchmark results (these serve as reference points)
        print(f"\nBaseline Performance Benchmark:")
        print(f"Average: {avg_time:.4f}s")
        print(f"Median: {median_time:.4f}s")
        print(f"95th percentile: {p95_time:.4f}s")
        
        # Baseline should be very fast with no extensions
        assert avg_time < 0.01, f"Baseline too slow: {avg_time:.4f}s"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])