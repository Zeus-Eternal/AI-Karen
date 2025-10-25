"""
Comprehensive Integration Tests

Integration tests combining multiple connectivity components.
"""

import asyncio
import time
import pytest
import pytest_asyncio
from .test_backend_connectivity_reliability import (
    NetworkConditionSimulator,
    RetryLogicTester,
    HealthMonitoringTester,
    AuthenticationPerformanceTracker
)


@pytest.mark.integration
class TestConnectivityIntegration:
    """Integration tests combining multiple connectivity components."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_connectivity_with_retry_and_failover(self):
        """Test complete connectivity flow with retry logic and failover."""
        network_simulator = NetworkConditionSimulator()
        retry_tester = RetryLogicTester()
        health_monitor_tester = HealthMonitoringTester()
        
        # Configure unstable network
        network_simulator.configure_unstable_network()
        
        # Set up backends with primary failing
        health_monitor_tester.set_backend_status("primary", False)
        health_monitor_tester.set_backend_status("fallback1", True)
        
        async def attempt_connection_with_retry_and_failover():
            """Simulate connection attempt with retry and failover."""
            backends = ["primary", "fallback1", "fallback2"]
            
            for backend in backends:
                retry_tester.reset()
                
                # Check backend health
                health = await health_monitor_tester.simulate_health_check(backend)
                
                if not health["healthy"]:
                    # Try next backend
                    continue
                
                # Attempt connection with retry
                for attempt in range(3):  # Max 3 retries
                    try:
                        # Simulate network conditions
                        await network_simulator.simulate_network_delay()
                        
                        if network_simulator.should_simulate_failure("connection"):
                            await retry_tester.simulate_failing_operation()
                        
                        # Success
                        return {
                            "success": True,
                            "backend": backend,
                            "attempts": attempt + 1,
                            "retry_stats": retry_tester.get_retry_statistics()
                        }
                        
                    except Exception:
                        if attempt < 2:  # Not last attempt
                            await asyncio.sleep(0.1 * (2 ** attempt))  # Exponential backoff
                        continue
                
                # All retries failed for this backend, try next
                continue
            
            # All backends failed
            return {"success": False, "error": "All backends failed"}
        
        # Test the complete flow
        result = await attempt_connection_with_retry_and_failover()
        
        # Should succeed with fallback1 (since primary is unhealthy)
        assert result["success"] is True
        assert result["backend"] == "fallback1"
        
        # Should have attempted retries
        retry_stats = result["retry_stats"]
        assert retry_stats["total_attempts"] >= 1
    
    @pytest.mark.asyncio
    async def test_connectivity_performance_under_various_conditions(self):
        """Test connectivity performance under various network conditions."""
        network_simulator = NetworkConditionSimulator()
        
        # Test different network conditions
        conditions = [
            ("good", network_simulator.configure_good_network),
            ("unstable", network_simulator.configure_unstable_network),
            ("poor", network_simulator.configure_poor_network),
        ]
        
        results = {}
        
        for condition_name, configure_func in conditions:
            configure_func()
            
            # Reset performance tracker
            performance_tracker = AuthenticationPerformanceTracker()
            
            # Run connectivity tests
            attempts = 10
            for i in range(attempts):
                start_time = performance_tracker.start_attempt()
                success = False
                
                try:
                    await network_simulator.simulate_network_delay()
                    
                    if not network_simulator.should_simulate_failure("connection"):
                        success = True
                        
                except Exception:
                    pass
                
                finally:
                    performance_tracker.end_attempt(start_time, success)
            
            # Store results for this condition
            results[condition_name] = performance_tracker.get_statistics()
        
        # Analyze performance across conditions
        good_stats = results["good"]
        unstable_stats = results["unstable"]
        poor_stats = results["poor"]
        
        # Good network should have best performance
        assert good_stats["success_rate"] > unstable_stats["success_rate"]
        assert good_stats["success_rate"] > poor_stats["success_rate"]
        assert good_stats["avg_response_time"] < poor_stats["avg_response_time"]
        
        # Poor network should have worst performance
        assert poor_stats["success_rate"] < good_stats["success_rate"]
        assert poor_stats["avg_response_time"] > good_stats["avg_response_time"]
        
        # All conditions should complete tests
        for condition, stats in results.items():
            assert stats["total_attempts"] == attempts
            assert stats["avg_response_time"] > 0


# Performance test configuration
@pytest.mark.performance
class TestConnectivityLoadTesting:
    """Dedicated load testing for connectivity system."""
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_sustained_connectivity_load(self):
        """Test sustained connectivity load over time."""
        network_simulator = NetworkConditionSimulator()
        performance_tracker = AuthenticationPerformanceTracker()
        
        # Configure good network for sustained testing
        network_simulator.configure_good_network()
        
        # Run connectivity attempts for 30 seconds
        test_duration = 30.0  # seconds
        start_time = time.time()
        operation_count = 0
        
        async def sustained_connectivity_worker():
            """Worker for sustained connectivity testing."""
            nonlocal operation_count
            
            while time.time() - start_time < test_duration:
                worker_start = performance_tracker.start_attempt()
                success = False
                
                try:
                    await network_simulator.simulate_network_delay()
                    
                    if not network_simulator.should_simulate_failure("connection"):
                        success = True
                        operation_count += 1
                    
                    # Small delay to prevent overwhelming
                    await asyncio.sleep(0.1)
                    
                except Exception:
                    pass
                    
                finally:
                    performance_tracker.end_attempt(worker_start, success)
        
        # Run 5 concurrent workers
        workers = 5
        worker_tasks = [sustained_connectivity_worker() for _ in range(workers)]
        
        await asyncio.gather(*worker_tasks)
        
        # Analyze sustained load performance
        stats = performance_tracker.get_statistics()
        
        # Should have completed many operations
        assert stats["total_attempts"] > 50  # At least 50 operations in 30 seconds
        
        # Performance should remain stable under sustained load
        assert stats["success_rate"] > 0.8  # At least 80% success rate
        assert stats["avg_response_time"] < 5.0  # Average under 5 seconds
        
        # Calculate throughput
        throughput = stats["total_attempts"] / test_duration
        assert throughput > 1.0  # At least 1 operation per second