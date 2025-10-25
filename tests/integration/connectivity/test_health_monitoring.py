"""
Health Monitoring and Failover Testing

Tests health monitoring and automatic failover functionality.
"""

import asyncio
import time
import pytest
import pytest_asyncio
import statistics
from .test_backend_connectivity_reliability import (
    HealthMonitoringTester,
    AuthenticationPerformanceTracker
)


class TestHealthMonitoringAndFailover:
    """Test health monitoring and automatic failover functionality."""
    
    @pytest.mark.asyncio
    async def test_health_check_monitoring(self):
        """Test basic health check monitoring functionality."""
        health_monitor_tester = HealthMonitoringTester()
        
        # Test health checks for multiple backends
        backends = ["primary", "fallback1", "fallback2"]
        
        # Initially all backends are healthy
        for backend in backends:
            health_result = await health_monitor_tester.simulate_health_check(backend)
            
            assert health_result["backend"] == backend
            assert health_result["healthy"] is True
            assert health_result["response_time_ms"] > 0
            assert health_result["status_code"] == 200
        
        # Make one backend unhealthy
        health_monitor_tester.set_backend_status("primary", False)
        
        # Check health again
        primary_health = await health_monitor_tester.simulate_health_check("primary")
        assert primary_health["healthy"] is False
        assert primary_health["status_code"] == 503
        
        # Other backends should still be healthy
        fallback_health = await health_monitor_tester.simulate_health_check("fallback1")
        assert fallback_health["healthy"] is True
        
        # Get health statistics
        stats = health_monitor_tester.get_health_statistics()
        assert stats["total_checks"] == 4  # 3 initial + 1 recheck
        assert stats["healthy_checks"] == 3
        assert stats["unhealthy_checks"] == 1
        assert 0.7 < stats["health_rate"] < 0.8  # 3/4 = 0.75
    
    @pytest.mark.asyncio
    async def test_automatic_failover_logic(self):
        """Test automatic failover when primary backend fails."""
        health_monitor_tester = HealthMonitoringTester()
        
        # Initially primary is healthy
        primary_health = await health_monitor_tester.simulate_health_check("primary")
        assert primary_health["healthy"] is True
        
        # Primary becomes unhealthy
        health_monitor_tester.set_backend_status("primary", False)
        
        # Detect primary failure
        primary_health = await health_monitor_tester.simulate_health_check("primary")
        assert primary_health["healthy"] is False
        
        # Trigger failover to fallback1
        failover_event = health_monitor_tester.simulate_failover("primary", "fallback1")
        
        assert failover_event["from_backend"] == "primary"
        assert failover_event["to_backend"] == "fallback1"
        assert "unhealthy" in failover_event["reason"]
        
        # Verify fallback1 is healthy
        fallback_health = await health_monitor_tester.simulate_health_check("fallback1")
        assert fallback_health["healthy"] is True
        
        # Get failover statistics
        stats = health_monitor_tester.get_health_statistics()
        assert stats["failover_count"] == 1
        assert len(stats["failover_events"]) == 1
    
    @pytest.mark.asyncio
    async def test_cascading_failover(self):
        """Test cascading failover when multiple backends fail."""
        health_monitor_tester = HealthMonitoringTester()
        
        # Start with all backends healthy
        backends = ["primary", "fallback1", "fallback2"]
        for backend in backends:
            health = await health_monitor_tester.simulate_health_check(backend)
            assert health["healthy"] is True
        
        # Primary fails - failover to fallback1
        health_monitor_tester.set_backend_status("primary", False)
        health_monitor_tester.simulate_failover("primary", "fallback1")
        
        # Fallback1 also fails - failover to fallback2
        health_monitor_tester.set_backend_status("fallback1", False)
        health_monitor_tester.simulate_failover("fallback1", "fallback2")
        
        # Verify final state
        primary_health = await health_monitor_tester.simulate_health_check("primary")
        fallback1_health = await health_monitor_tester.simulate_health_check("fallback1")
        fallback2_health = await health_monitor_tester.simulate_health_check("fallback2")
        
        assert primary_health["healthy"] is False
        assert fallback1_health["healthy"] is False
        assert fallback2_health["healthy"] is True
        
        # Check failover statistics
        stats = health_monitor_tester.get_health_statistics()
        assert stats["failover_count"] == 2
        
        # Verify failover sequence
        failover_events = stats["failover_events"]
        assert failover_events[0]["from_backend"] == "primary"
        assert failover_events[0]["to_backend"] == "fallback1"
        assert failover_events[1]["from_backend"] == "fallback1"
        assert failover_events[1]["to_backend"] == "fallback2"
    
    @pytest.mark.asyncio
    async def test_health_monitoring_under_load(self):
        """Test health monitoring performance under concurrent load."""
        health_monitor_tester = HealthMonitoringTester()
        
        async def concurrent_health_check(backend: str, check_id: int):
            """Perform concurrent health check."""
            return await health_monitor_tester.simulate_health_check(f"{backend}_{check_id}")
        
        # Simulate concurrent health checks
        concurrent_checks = 20
        backends = ["primary", "fallback1", "fallback2"]
        
        tasks = []
        for i in range(concurrent_checks):
            backend = backends[i % len(backends)]
            tasks.append(concurrent_health_check(backend, i))
        
        results = await asyncio.gather(*tasks)
        
        # All health checks should complete
        assert len(results) == concurrent_checks
        
        # All should be successful (since we didn't set any as unhealthy)
        healthy_results = [r for r in results if r["healthy"]]
        assert len(healthy_results) == concurrent_checks
        
        # Response times should be reasonable
        response_times = [r["response_time_ms"] for r in results]
        avg_response_time = statistics.mean(response_times)
        assert avg_response_time < 1000  # Average under 1 second
        
        # Get final statistics
        stats = health_monitor_tester.get_health_statistics()
        assert stats["total_checks"] == concurrent_checks
        assert stats["health_rate"] == 1.0  # All healthy
    
    @pytest.mark.asyncio
    async def test_health_recovery_detection(self):
        """Test detection of backend recovery after failure."""
        health_monitor_tester = HealthMonitoringTester()
        
        # Start with healthy backend
        health = await health_monitor_tester.simulate_health_check("primary")
        assert health["healthy"] is True
        
        # Backend becomes unhealthy
        health_monitor_tester.set_backend_status("primary", False)
        unhealthy_check = await health_monitor_tester.simulate_health_check("primary")
        assert unhealthy_check["healthy"] is False
        
        # Trigger failover
        health_monitor_tester.simulate_failover("primary", "fallback1")
        
        # Backend recovers
        health_monitor_tester.set_backend_status("primary", True)
        recovered_check = await health_monitor_tester.simulate_health_check("primary")
        assert recovered_check["healthy"] is True
        
        # Verify recovery is detected
        stats = health_monitor_tester.get_health_statistics()
        
        # Should have mix of healthy and unhealthy checks
        assert stats["healthy_checks"] >= 2  # Initial + recovery
        assert stats["unhealthy_checks"] >= 1  # Failure period
        assert stats["total_checks"] >= 3