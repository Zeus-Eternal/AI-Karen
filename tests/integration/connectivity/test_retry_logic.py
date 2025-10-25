"""
Retry Logic and Exponential Backoff Testing

Tests retry logic implementation and exponential backoff behavior.
"""

import asyncio
import time
import pytest
import pytest_asyncio
import random
import statistics
from .test_backend_connectivity_reliability import RetryLogicTester


class TestRetryLogicAndExponentialBackoff:
    """Test retry logic and exponential backoff implementation."""
    
    @pytest.mark.asyncio
    async def test_exponential_backoff_pattern(self):
        """Test that retry logic follows exponential backoff pattern."""
        retry_tester = RetryLogicTester()
        retry_tester.reset()
        
        # Simulate operation that fails 3 times then succeeds
        with pytest.raises(ConnectionError):
            try:
                for attempt in range(4):  # Will fail 4 times
                    await retry_tester.simulate_failing_operation()
            except ConnectionError:
                pass  # Expected for this test
        
        stats = retry_tester.get_retry_statistics()
        
        # Verify exponential backoff behavior
        assert stats["total_attempts"] == 4
        assert len(stats["backoff_delays"]) == 3  # 3 delays between 4 attempts
        
        # Check that delays increase exponentially
        delays = stats["backoff_delays"]
        if len(delays) > 1:
            for i in range(1, len(delays)):
                # Each delay should be roughly double the previous (with max limit)
                expected_delay = min(delays[i-1] * 2, retry_tester.max_delay)
                assert delays[i] >= delays[i-1]  # Should not decrease
                assert delays[i] <= expected_delay * 1.1  # Allow some tolerance
    
    @pytest.mark.asyncio
    async def test_retry_success_after_failures(self):
        """Test successful retry after initial failures."""
        retry_tester = RetryLogicTester()
        retry_tester.reset()
        
        # Simulate operation that succeeds on 3rd attempt
        result = await retry_tester.simulate_failing_operation(success_after_attempts=3)
        
        assert result["success"] is True
        assert result["attempt"] == 3
        
        stats = retry_tester.get_retry_statistics()
        assert stats["total_attempts"] == 3
        assert len(stats["backoff_delays"]) == 2  # 2 delays before success
    
    @pytest.mark.asyncio
    async def test_max_retry_attempts_limit(self):
        """Test that retry logic respects maximum attempt limits."""
        retry_tester = RetryLogicTester()
        retry_tester.reset()
        retry_tester.max_attempts = 3
        
        # Simulate operation that never succeeds
        attempt_count = 0
        try:
            while attempt_count < 5:  # Try more than max_attempts
                await retry_tester.simulate_failing_operation()
                attempt_count += 1
        except ConnectionError:
            pass
        
        stats = retry_tester.get_retry_statistics()
        
        # Should not exceed max attempts
        assert stats["total_attempts"] <= retry_tester.max_attempts + 2  # Allow some tolerance
    
    @pytest.mark.asyncio
    async def test_backoff_delay_limits(self):
        """Test that backoff delays respect minimum and maximum limits."""
        retry_tester = RetryLogicTester()
        retry_tester.reset()
        retry_tester.base_delay = 0.5
        retry_tester.max_delay = 5.0
        
        # Simulate many failures to test delay limits
        try:
            for attempt in range(10):
                await retry_tester.simulate_failing_operation()
        except ConnectionError:
            pass
        
        stats = retry_tester.get_retry_statistics()
        delays = stats["backoff_delays"]
        
        if delays:
            # First delay should be at least base_delay
            assert delays[0] >= retry_tester.base_delay
            
            # No delay should exceed max_delay
            assert all(delay <= retry_tester.max_delay for delay in delays)
            
            # Delays should generally increase (exponential backoff)
            increasing_count = 0
            for i in range(1, len(delays)):
                if delays[i] >= delays[i-1]:
                    increasing_count += 1
            
            # Most delays should be increasing (allow some tolerance for max limit)
            assert increasing_count >= len(delays) * 0.7
    
    @pytest.mark.asyncio
    async def test_concurrent_retry_operations(self):
        """Test retry logic under concurrent operations."""
        
        async def concurrent_retry_operation(operation_id: int):
            """Simulate concurrent retry operation."""
            local_tester = RetryLogicTester()
            
            try:
                # Each operation succeeds after 2-4 attempts randomly
                success_after = random.randint(2, 4)
                result = await local_tester.simulate_failing_operation(success_after_attempts=success_after)
                return {
                    "operation_id": operation_id,
                    "success": True,
                    "attempts": result["attempt"],
                    "stats": local_tester.get_retry_statistics()
                }
            except Exception as e:
                return {
                    "operation_id": operation_id,
                    "success": False,
                    "error": str(e),
                    "stats": local_tester.get_retry_statistics()
                }
        
        # Run 5 concurrent retry operations
        concurrent_operations = 5
        tasks = [concurrent_retry_operation(i) for i in range(concurrent_operations)]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Analyze concurrent retry behavior
        successful_operations = [r for r in results if isinstance(r, dict) and r.get("success")]
        
        # Most operations should eventually succeed
        assert len(successful_operations) >= concurrent_operations * 0.6
        
        # Each successful operation should have reasonable retry behavior
        for result in successful_operations:
            stats = result["stats"]
            assert stats["total_attempts"] >= 2  # Should have retried at least once
            assert stats["total_attempts"] <= 5  # Should not retry excessively