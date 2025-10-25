"""
Network Conditions Testing

Tests backend connectivity under various network conditions.
"""

import asyncio
import time
import pytest
import pytest_asyncio
import statistics
from .test_backend_connectivity_reliability import (
    NetworkConditionSimulator, 
    AuthenticationPerformanceTracker
)


class TestBackendConnectivity:
    """Test backend connectivity under various network conditions."""
    
    @pytest.mark.asyncio
    async def test_connectivity_under_good_network_conditions(self):
        """Test backend connectivity under good network conditions."""
        network_simulator = NetworkConditionSimulator()
        network_simulator.configure_good_network()
        
        # Simulate multiple connection attempts
        success_count = 0
        total_attempts = 10
        response_times = []
        
        for i in range(total_attempts):
            start_time = time.time()
            
            try:
                # Simulate network delay
                await network_simulator.simulate_network_delay()
                
                # Simulate connection attempt
                if not network_simulator.should_simulate_failure("connection"):
                    # Mock successful response
                    response = {"status": "success", "data": f"response_{i}"}
                    success_count += 1
                else:
                    raise ConnectionError("Simulated connection failure")
                    
                response_time = (time.time() - start_time) * 1000
                response_times.append(response_time)
                
            except ConnectionError:
                response_time = (time.time() - start_time) * 1000
                response_times.append(response_time)
        
        # Analyze connectivity under good conditions
        success_rate = success_count / total_attempts
        avg_response_time = statistics.mean(response_times)
        
        # Under good network conditions, expect high success rate and low latency
        assert success_rate > 0.95  # At least 95% success rate
        assert avg_response_time < 200  # Average response time under 200ms
        assert max(response_times) < 500  # Max response time under 500ms
    
    @pytest.mark.asyncio
    async def test_connectivity_under_poor_network_conditions(self):
        """Test backend connectivity under poor network conditions."""
        network_simulator = NetworkConditionSimulator()
        network_simulator.configure_poor_network()
        
        success_count = 0
        total_attempts = 10
        response_times = []
        timeout_count = 0
        
        for i in range(total_attempts):
            start_time = time.time()
            
            try:
                # Simulate network delay
                await network_simulator.simulate_network_delay()
                
                # Check for simulated failures
                if network_simulator.should_simulate_failure("connection"):
                    raise ConnectionError("Simulated connection failure")
                elif network_simulator.should_simulate_failure("packet_loss"):
                    raise TimeoutError("Simulated packet loss timeout")
                    
                # Mock successful response
                response = {"status": "success", "data": f"response_{i}"}
                success_count += 1
                
            except (ConnectionError, TimeoutError) as e:
                if isinstance(e, TimeoutError):
                    timeout_count += 1
                    
            finally:
                response_time = (time.time() - start_time) * 1000
                response_times.append(response_time)
        
        # Analyze connectivity under poor conditions
        success_rate = success_count / total_attempts
        avg_response_time = statistics.mean(response_times)
        
        # Under poor network conditions, expect degraded performance
        assert success_rate < 0.9  # Success rate should be impacted
        assert avg_response_time > 1000  # Higher response times due to latency
        assert timeout_count > 0  # Should experience some timeouts
    
    @pytest.mark.asyncio
    async def test_connectivity_with_unstable_network(self):
        """Test backend connectivity with unstable network conditions."""
        network_simulator = NetworkConditionSimulator()
        network_simulator.configure_unstable_network()
        
        # Test connectivity over time to see instability
        test_duration = 10  # seconds
        start_time = time.time()
        
        connectivity_samples = []
        
        while time.time() - start_time < test_duration:
            sample_start = time.time()
            
            try:
                await network_simulator.simulate_network_delay()
                
                if network_simulator.should_simulate_failure("connection"):
                    connectivity_samples.append({"success": False, "response_time": 0})
                else:
                    response_time = (time.time() - sample_start) * 1000
                    connectivity_samples.append({"success": True, "response_time": response_time})
                    
            except Exception:
                connectivity_samples.append({"success": False, "response_time": 0})
                
            # Sample every 500ms
            await asyncio.sleep(0.5)
        
        # Analyze network instability
        successful_samples = [s for s in connectivity_samples if s["success"]]
        failed_samples = [s for s in connectivity_samples if not s["success"]]
        
        success_rate = len(successful_samples) / len(connectivity_samples)
        
        # Unstable network should show variability
        assert 0.3 < success_rate < 0.95  # Variable success rate
        assert len(failed_samples) > 0  # Should have some failures
        assert len(successful_samples) > 0  # Should have some successes
        
        # Response times should be variable
        if successful_samples:
            response_times = [s["response_time"] for s in successful_samples]
            response_time_std = statistics.stdev(response_times) if len(response_times) > 1 else 0
            assert response_time_std > 100  # High variability in response times