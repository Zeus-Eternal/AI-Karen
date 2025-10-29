"""
Performance tests for error handling overhead.

Tests the performance impact of error handling and recovery mechanisms
to ensure they don't significantly degrade system performance.
"""

import pytest
import asyncio
import time
import statistics
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import Mock, AsyncMock, patch
import psutil
import gc
from typing import List, Dict, Any

# Import error handling components
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))

from server.extension_error_recovery_manager import ExtensionErrorRecoveryManager
from ui_launchers.web_ui.src.lib.graceful_degradation.enhanced_backend_service import EnhancedBackendService


class TestErrorHandlingPerformance:
    """Performance tests for error handling mechanisms."""

    @pytest.fixture
    def recovery_manager(self):
        """Create recovery manager for performance testing."""
        return ExtensionErrorRecoveryManager()

    @pytest.fixture
    def backend_service(self):
        """Create backend service for performance testing."""
        return EnhancedBackendService("http://localhost:8000")

    def test_error_detection_performance(self, recovery_manager):
        """Test performance of error detection mechanisms."""
        # Setup test errors
        test_errors = [
            {"type": "authentication_error", "message": "Auth failed"},
            {"type": "network_error", "message": "Connection timeout"},
            {"type": "service_unavailable", "message": "Service down"},
        ] * 1000  # Test with 3000 errors
        
        # Measure error detection performance
        start_time = time.time()
        
        for error in test_errors:
            error_type = recovery_manager.detect_error_type(error)
            assert error_type is not None
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Performance assertions
        assert total_time < 1.0  # Should process 3000 errors in under 1 second
        avg_time_per_error = total_time / len(test_errors)
        assert avg_time_per_error < 0.001  # Less than 1ms per error

    def test_recovery_strategy_selection_performance(self, recovery_manager):
        """Test performance of recovery strategy selection."""
        error_types = [
            "authentication_error",
            "network_error", 
            "service_unavailable",
            "configuration_error",
            "resource_exhaustion"
        ]
        
        # Measure strategy selection performance
        iterations = 10000
        start_time = time.time()
        
        for i in range(iterations):
            error_type = error_types[i % len(error_types)]
            strategy = recovery_manager._select_recovery_strategy(error_type)
            assert strategy is not None
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Performance assertions
        assert total_time < 0.5  # Should complete 10k selections in under 0.5 seconds
        avg_time_per_selection = total_time / iterations
        assert avg_time_per_selection < 0.00005  # Less than 0.05ms per selection

    @pytest.mark.asyncio
    async def test_concurrent_error_handling_performance(self, recovery_manager):
        """Test performance of concurrent error handling."""
        # Setup concurrent error scenarios
        error_contexts = [
            {
                "error_type": f"error_{i}",
                "extension_name": f"ext_{i % 10}",
                "timestamp": time.time()
            }
            for i in range(100)
        ]
        
        # Mock recovery execution to be fast
        with patch.object(recovery_manager, '_execute_recovery') as mock_recovery:
            mock_recovery.return_value = {"success": True, "time": 0.001}
            
            # Measure concurrent handling performance
            start_time = time.time()
            
            tasks = [
                recovery_manager.handle_error_async(context)
                for context in error_contexts
            ]
            
            results = await asyncio.gather(*tasks)
            
            end_time = time.time()
            total_time = end_time - start_time
            
            # Performance assertions
            assert len(results) == 100
            assert total_time < 2.0  # Should handle 100 concurrent errors in under 2 seconds
            assert all(result["success"] for result in results)

    def test_memory_usage_during_error_handling(self, recovery_manager):
        """Test memory usage during intensive error handling."""
        # Measure initial memory usage
        gc.collect()
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        # Generate many error contexts
        error_contexts = []
        for i in range(1000):
            context = {
                "error_type": "test_error",
                "extension_name": f"extension_{i}",
                "error_message": f"Test error message {i}" * 10,  # Make it larger
                "metadata": {"data": list(range(100))}  # Add some data
            }
            error_contexts.append(context)
        
        # Process all errors
        for context in error_contexts:
            recovery_manager.process_error_context(context)
        
        # Measure memory after processing
        gc.collect()
        final_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory usage assertions
        assert memory_increase < 50  # Should not increase memory by more than 50MB
        
        # Clean up and verify memory is released
        error_contexts.clear()
        recovery_manager.cleanup()
        gc.collect()
        
        cleanup_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        memory_after_cleanup = cleanup_memory - initial_memory
        assert memory_after_cleanup < 10  # Should release most memory

    def test_error_logging_performance_impact(self, recovery_manager):
        """Test performance impact of error logging."""
        # Test with logging enabled
        with patch('logging.getLogger') as mock_logger:
            mock_logger.return_value.error = Mock()
            mock_logger.return_value.info = Mock()
            
            start_time = time.time()
            
            for i in range(1000):
                recovery_manager.log_error_with_context({
                    "error_type": "test_error",
                    "message": f"Error {i}",
                    "context": {"data": "test"}
                })
            
            end_time = time.time()
            logging_time = end_time - start_time
        
        # Test without logging
        with patch('logging.getLogger') as mock_logger:
            mock_logger.return_value.error = Mock()
            mock_logger.return_value.info = Mock()
            
            # Disable logging
            mock_logger.return_value.disabled = True
            
            start_time = time.time()
            
            for i in range(1000):
                recovery_manager.log_error_with_context({
                    "error_type": "test_error",
                    "message": f"Error {i}",
                    "context": {"data": "test"}
                })
            
            end_time = time.time()
            no_logging_time = end_time - start_time
        
        # Performance impact should be minimal
        logging_overhead = logging_time - no_logging_time
        assert logging_overhead < 0.5  # Logging should add less than 0.5 seconds overhead

    @pytest.mark.asyncio
    async def test_graceful_degradation_performance_impact(self, backend_service):
        """Test performance impact of graceful degradation."""
        # Mock cache manager
        cache_manager = Mock()
        cache_manager.get.return_value = {"cached": "data"}
        
        # Test normal operation performance
        with patch.object(backend_service, '_make_request') as mock_request:
            mock_request.return_value = {"live": "data"}
            
            start_time = time.time()
            
            tasks = [
                backend_service.get_data_with_fallback("test", cache_manager)
                for _ in range(100)
            ]
            
            results = await asyncio.gather(*tasks)
            
            normal_time = time.time() - start_time
        
        # Test degraded operation performance
        with patch.object(backend_service, '_make_request') as mock_request:
            mock_request.side_effect = Exception("Service unavailable")
            
            start_time = time.time()
            
            tasks = [
                backend_service.get_data_with_fallback("test", cache_manager)
                for _ in range(100)
            ]
            
            results = await asyncio.gather(*tasks)
            
            degraded_time = time.time() - start_time
        
        # Degraded operation should not be significantly slower
        performance_ratio = degraded_time / normal_time
        assert performance_ratio < 2.0  # Degraded should be less than 2x slower
        assert degraded_time < 5.0  # Should complete within 5 seconds

    def test_error_recovery_backoff_performance(self, recovery_manager):
        """Test performance of exponential backoff calculations."""
        # Test backoff calculation performance
        start_time = time.time()
        
        backoff_times = []
        for attempt in range(1, 1001):  # Test 1000 calculations
            backoff_time = recovery_manager._calculate_backoff_delay(attempt)
            backoff_times.append(backoff_time)
        
        end_time = time.time()
        calculation_time = end_time - start_time
        
        # Performance assertions
        assert calculation_time < 0.1  # Should calculate 1000 backoffs in under 0.1 seconds
        assert len(backoff_times) == 1000
        assert all(isinstance(t, (int, float)) for t in backoff_times)

    def test_error_context_serialization_performance(self, recovery_manager):
        """Test performance of error context serialization."""
        # Create complex error context
        complex_context = {
            "error_type": "complex_error",
            "extension_name": "test_extension",
            "error_message": "Complex error with lots of data",
            "timestamp": time.time(),
            "metadata": {
                "user_data": {"id": "user123", "preferences": {"theme": "dark"}},
                "request_data": {"headers": {"auth": "token"}, "body": {"data": list(range(100))}},
                "system_data": {"memory": 1024, "cpu": 75.5, "disk": 512}
            },
            "stack_trace": ["line1", "line2", "line3"] * 20,
            "additional_context": {"key" + str(i): "value" + str(i) for i in range(50)}
        }
        
        # Test serialization performance
        start_time = time.time()
        
        for _ in range(100):
            serialized = recovery_manager.serialize_error_context(complex_context)
            deserialized = recovery_manager.deserialize_error_context(serialized)
            assert deserialized["error_type"] == complex_context["error_type"]
        
        end_time = time.time()
        serialization_time = end_time - start_time
        
        # Performance assertions
        assert serialization_time < 1.0  # Should serialize/deserialize 100 contexts in under 1 second

    @pytest.mark.asyncio
    async def test_recovery_timeout_performance(self, recovery_manager):
        """Test performance of recovery timeout handling."""
        # Mock slow recovery operation
        async def slow_recovery(*args, **kwargs):
            await asyncio.sleep(2.0)  # Simulate slow recovery
            return {"success": True}
        
        with patch.object(recovery_manager, '_execute_recovery', side_effect=slow_recovery):
            # Test recovery with timeout
            start_time = time.time()
            
            try:
                result = await recovery_manager.execute_recovery_with_timeout(
                    {"error_type": "test"}, timeout=1.0
                )
            except asyncio.TimeoutError:
                pass  # Expected timeout
            
            end_time = time.time()
            actual_time = end_time - start_time
            
            # Should timeout close to the specified timeout
            assert 0.9 < actual_time < 1.5  # Allow some variance

    def test_error_pattern_matching_performance(self, recovery_manager):
        """Test performance of error pattern matching."""
        # Setup error patterns
        error_patterns = [
            {"pattern": r"authentication.*failed", "type": "auth_error"},
            {"pattern": r"connection.*timeout", "type": "network_error"},
            {"pattern": r"service.*unavailable", "type": "service_error"},
            {"pattern": r"permission.*denied", "type": "permission_error"},
            {"pattern": r"resource.*exhausted", "type": "resource_error"},
        ] * 20  # 100 patterns total
        
        recovery_manager.load_error_patterns(error_patterns)
        
        # Test error messages
        test_messages = [
            "authentication token failed",
            "connection timeout occurred",
            "service temporarily unavailable",
            "permission denied for user",
            "resource exhausted - out of memory"
        ] * 200  # 1000 messages total
        
        # Measure pattern matching performance
        start_time = time.time()
        
        matches = []
        for message in test_messages:
            match = recovery_manager.match_error_pattern(message)
            matches.append(match)
        
        end_time = time.time()
        matching_time = end_time - start_time
        
        # Performance assertions
        assert matching_time < 2.0  # Should match 1000 messages in under 2 seconds
        assert len([m for m in matches if m is not None]) > 0  # Should find some matches


class TestErrorHandlingBenchmarks:
    """Benchmark tests for error handling components."""

    def test_error_handling_throughput_benchmark(self):
        """Benchmark error handling throughput."""
        recovery_manager = ExtensionErrorRecoveryManager()
        
        # Benchmark parameters
        num_errors = 10000
        error_types = ["auth", "network", "service", "config", "resource"]
        
        # Generate test errors
        test_errors = [
            {
                "type": error_types[i % len(error_types)],
                "message": f"Error {i}",
                "timestamp": time.time()
            }
            for i in range(num_errors)
        ]
        
        # Benchmark error processing
        start_time = time.time()
        
        processed_count = 0
        for error in test_errors:
            recovery_manager.process_error(error)
            processed_count += 1
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Calculate throughput
        throughput = processed_count / total_time
        
        # Benchmark assertions
        assert throughput > 5000  # Should process at least 5000 errors per second
        assert total_time < 5.0   # Should complete within 5 seconds
        
        print(f"Error handling throughput: {throughput:.2f} errors/second")
        print(f"Total processing time: {total_time:.3f} seconds")

    def test_recovery_latency_benchmark(self):
        """Benchmark recovery operation latency."""
        recovery_manager = ExtensionErrorRecoveryManager()
        
        # Mock fast recovery operations
        with patch.object(recovery_manager, '_execute_recovery') as mock_recovery:
            mock_recovery.return_value = {"success": True}
            
            # Measure recovery latencies
            latencies = []
            
            for i in range(1000):
                start_time = time.time()
                
                recovery_manager.execute_recovery({
                    "error_type": "test_error",
                    "context": {"attempt": i}
                })
                
                end_time = time.time()
                latency = (end_time - start_time) * 1000  # Convert to milliseconds
                latencies.append(latency)
            
            # Calculate latency statistics
            avg_latency = statistics.mean(latencies)
            p95_latency = statistics.quantiles(latencies, n=20)[18]  # 95th percentile
            p99_latency = statistics.quantiles(latencies, n=100)[98]  # 99th percentile
            
            # Latency assertions
            assert avg_latency < 1.0   # Average latency should be under 1ms
            assert p95_latency < 5.0   # 95th percentile should be under 5ms
            assert p99_latency < 10.0  # 99th percentile should be under 10ms
            
            print(f"Recovery latency - Avg: {avg_latency:.3f}ms, P95: {p95_latency:.3f}ms, P99: {p99_latency:.3f}ms")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])