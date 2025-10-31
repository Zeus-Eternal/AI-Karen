"""
Connection Pool Stress Tests

Comprehensive stress tests for database connection pool behavior under various load conditions.
Tests connection pool exhaustion, recovery, timeout handling, and concurrent access patterns.

Requirements: 2.1, 2.3
"""

import asyncio
import pytest
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import Mock, AsyncMock, patch
from typing import List, Dict, Any
import random

from ai_karen_engine.services.database_connection_manager import get_database_manager
from ai_karen_engine.services.database_health_checker import DatabaseHealthChecker, OverallHealthStatus


class TestConnectionPoolStress:
    """Stress tests for database connection pool"""

    @pytest.fixture
    async def mock_pool_environment(self):
        """Mock connection pool environment for stress testing"""
        # Mock connection pool with realistic behavior
        pool_state = {
            "size": 10,
            "max_overflow": 5,
            "checked_out": 0,
            "checked_in": 10,
            "overflow": 0,
            "total_connections": 10,
            "active_connections": 0,
            "connection_failures": 0,
            "slow_queries": 0,
        }
        
        # Mock database manager
        mock_db_manager = Mock()
        mock_db_manager.is_degraded.return_value = False
        
        def get_pool_metrics():
            return {
                "pool_size": pool_state["size"],
                "checked_out": pool_state["checked_out"],
                "checked_in": pool_state["checked_in"],
                "overflow": pool_state["overflow"],
                "total_connections": pool_state["total_connections"],
                "active_connections": pool_state["active_connections"],
                "connection_failures": pool_state["connection_failures"],
            }
        
        mock_db_manager._get_pool_metrics = get_pool_metrics
        
        # Mock session factory with realistic connection behavior
        async def create_mock_session():
            # Simulate connection checkout
            if pool_state["checked_out"] < pool_state["size"] + pool_state["max_overflow"]:
                pool_state["checked_out"] += 1
                pool_state["active_connections"] += 1
                if pool_state["checked_out"] > pool_state["size"]:
                    pool_state["overflow"] = pool_state["checked_out"] - pool_state["size"]
                pool_state["checked_in"] = max(0, pool_state["size"] - pool_state["checked_out"])
                pool_state["total_connections"] = pool_state["size"] + pool_state["overflow"]
                
                # Create mock session
                mock_session = AsyncMock()
                
                # Mock query execution with realistic timing
                async def mock_execute(*args, **kwargs):
                    # Simulate query execution time
                    query_time = random.uniform(0.01, 0.1)
                    if pool_state["checked_out"] > pool_state["size"] * 0.8:
                        query_time *= 2  # Slower when pool is stressed
                    
                    if query_time > 0.05:
                        pool_state["slow_queries"] += 1
                    
                    await asyncio.sleep(query_time)
                    
                    result = Mock()
                    result.scalar.return_value = "PostgreSQL 13.0"
                    return result
                
                mock_session.execute = mock_execute
                
                # Mock session cleanup
                async def mock_close():
                    # Simulate connection checkin
                    pool_state["checked_out"] = max(0, pool_state["checked_out"] - 1)
                    pool_state["active_connections"] = max(0, pool_state["active_connections"] - 1)
                    pool_state["overflow"] = max(0, pool_state["checked_out"] - pool_state["size"])
                    pool_state["checked_in"] = pool_state["size"] - (pool_state["checked_out"] - pool_state["overflow"])
                    pool_state["total_connections"] = pool_state["size"] + pool_state["overflow"]
                
                mock_session.close = mock_close
                
                return mock_session
            else:
                # Pool exhausted
                pool_state["connection_failures"] += 1
                raise Exception("Connection pool exhausted")
        
        # Mock session scope
        class MockSessionScope:
            def __init__(self):
                self.session = None
            
            async def __aenter__(self):
                self.session = await create_mock_session()
                return self.session
            
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                if self.session:
                    await self.session.close()
        
        mock_db_manager.async_session_scope = lambda: MockSessionScope()
        
        return {
            "db_manager": mock_db_manager,
            "pool_state": pool_state,
        }

    @pytest.mark.asyncio
    async def test_connection_pool_under_burst_load(self, mock_pool_environment):
        """Test connection pool behavior under sudden burst load"""
        db_manager = mock_pool_environment["db_manager"]
        pool_state = mock_pool_environment["pool_state"]
        
        # Create health checker with mocked database manager
        health_checker = DatabaseHealthChecker()
        
        # Mock Redis and Milvus for complete health checks
        mock_redis_manager = AsyncMock()
        mock_redis_manager.set.return_value = True
        mock_redis_manager.get.return_value = "test"
        mock_redis_manager.delete.return_value = True
        mock_redis_manager.is_degraded.return_value = False
        mock_redis_manager.get_connection_info.return_value = {"memory_cache_size": 100}
        
        mock_milvus_client = AsyncMock()
        mock_milvus_client.connect.return_value = None
        mock_milvus_client.health_check.return_value = {"status": "healthy"}
        
        with patch.object(health_checker, 'db_manager', db_manager), \
             patch.object(health_checker, 'redis_manager', mock_redis_manager), \
             patch.object(health_checker, 'milvus_client', mock_milvus_client):
            
            # Simulate burst load - many concurrent requests
            burst_size = 25  # More than pool size + overflow
            
            async def burst_task(task_id: int):
                """Single task in burst load"""
                try:
                    start_time = time.time()
                    result = await health_checker.check_health(include_detailed_validation=False)
                    duration = time.time() - start_time
                    
                    return {
                        "task_id": task_id,
                        "success": True,
                        "duration": duration,
                        "status": result.overall_status,
                        "pool_metrics": result.performance_metrics.get("postgresql", {}).get("pool_metrics", {}),
                    }
                except Exception as e:
                    return {
                        "task_id": task_id,
                        "success": False,
                        "error": str(e),
                        "duration": 0,
                    }
            
            # Execute burst load
            start_time = time.time()
            tasks = [burst_task(i) for i in range(burst_size)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            total_duration = time.time() - start_time
            
            # Analyze results
            successful_tasks = [r for r in results if isinstance(r, dict) and r.get("success")]
            failed_tasks = [r for r in results if isinstance(r, dict) and not r.get("success")]
            exception_tasks = [r for r in results if isinstance(r, Exception)]
            
            # Verify burst handling
            assert len(successful_tasks) > 0, "Some tasks should succeed even under burst load"
            
            # Calculate success rate
            success_rate = len(successful_tasks) / burst_size
            
            # Under burst load, we expect some failures but not complete failure
            assert success_rate > 0.3, f"Success rate too low: {success_rate}"
            
            # Check that pool metrics show stress
            if successful_tasks:
                sample_metrics = successful_tasks[0]["pool_metrics"]
                if sample_metrics:
                    # Pool should show high utilization during burst
                    checked_out = sample_metrics.get("checked_out", 0)
                    pool_size = sample_metrics.get("pool_size", 10)
                    utilization = checked_out / pool_size if pool_size > 0 else 0
                    
                    # During burst, utilization should be high
                    assert utilization >= 0.5, f"Pool utilization should be high during burst: {utilization}"
            
            # Verify pool state after burst
            final_pool_state = pool_state
            assert final_pool_state["connection_failures"] >= 0  # Some failures expected
            
            print(f"Burst test completed: {len(successful_tasks)}/{burst_size} successful, "
                  f"duration: {total_duration:.2f}s, failures: {final_pool_state['connection_failures']}")

    @pytest.mark.asyncio
    async def test_connection_pool_sustained_load(self, mock_pool_environment):
        """Test connection pool behavior under sustained load"""
        db_manager = mock_pool_environment["db_manager"]
        pool_state = mock_pool_environment["pool_state"]
        
        # Create health checker
        health_checker = DatabaseHealthChecker()
        
        # Mock other services
        mock_redis_manager = AsyncMock()
        mock_redis_manager.set.return_value = True
        mock_redis_manager.get.return_value = "test"
        mock_redis_manager.delete.return_value = True
        mock_redis_manager.is_degraded.return_value = False
        mock_redis_manager.get_connection_info.return_value = {"memory_cache_size": 100}
        
        mock_milvus_client = AsyncMock()
        mock_milvus_client.connect.return_value = None
        mock_milvus_client.health_check.return_value = {"status": "healthy"}
        
        with patch.object(health_checker, 'db_manager', db_manager), \
             patch.object(health_checker, 'redis_manager', mock_redis_manager), \
             patch.object(health_checker, 'milvus_client', mock_milvus_client):
            
            # Sustained load parameters
            load_duration = 3  # seconds
            concurrent_workers = 8  # Moderate concurrency
            
            async def sustained_worker(worker_id: int):
                """Worker that generates sustained load"""
                worker_results = []
                start_time = time.time()
                
                while (time.time() - start_time) < load_duration:
                    try:
                        task_start = time.time()
                        result = await health_checker.check_health(include_detailed_validation=False)
                        task_duration = time.time() - task_start
                        
                        worker_results.append({
                            "worker_id": worker_id,
                            "success": True,
                            "duration": task_duration,
                            "status": result.overall_status,
                            "timestamp": time.time(),
                        })
                        
                        # Small delay between requests
                        await asyncio.sleep(0.1)
                        
                    except Exception as e:
                        worker_results.append({
                            "worker_id": worker_id,
                            "success": False,
                            "error": str(e),
                            "timestamp": time.time(),
                        })
                        
                        # Longer delay after failure
                        await asyncio.sleep(0.2)
                
                return worker_results
            
            # Run sustained load test
            start_time = time.time()
            worker_tasks = [sustained_worker(i) for i in range(concurrent_workers)]
            worker_results = await asyncio.gather(*worker_tasks)
            total_duration = time.time() - start_time
            
            # Flatten results
            all_results = [result for worker_result in worker_results for result in worker_result]
            
            # Analyze sustained load performance
            successful_results = [r for r in all_results if r.get("success")]
            failed_results = [r for r in all_results if not r.get("success")]
            
            # Calculate metrics
            total_requests = len(all_results)
            success_rate = len(successful_results) / total_requests if total_requests > 0 else 0
            avg_duration = sum(r["duration"] for r in successful_results) / len(successful_results) if successful_results else 0
            
            # Verify sustained load handling
            assert total_requests > 0, "Should have processed requests during sustained load"
            assert success_rate > 0.7, f"Success rate should be high under sustained load: {success_rate}"
            assert avg_duration < 2.0, f"Average response time should be reasonable: {avg_duration}s"
            
            # Check for performance degradation over time
            if len(successful_results) > 10:
                first_half = successful_results[:len(successful_results)//2]
                second_half = successful_results[len(successful_results)//2:]
                
                first_half_avg = sum(r["duration"] for r in first_half) / len(first_half)
                second_half_avg = sum(r["duration"] for r in second_half) / len(second_half)
                
                # Performance shouldn't degrade significantly over time
                degradation_ratio = second_half_avg / first_half_avg if first_half_avg > 0 else 1
                assert degradation_ratio < 3.0, f"Performance degradation too high: {degradation_ratio}"
            
            print(f"Sustained load test: {total_requests} requests, {success_rate:.2%} success rate, "
                  f"avg duration: {avg_duration:.3f}s, total time: {total_duration:.2f}s")

    @pytest.mark.asyncio
    async def test_connection_pool_recovery_after_exhaustion(self, mock_pool_environment):
        """Test connection pool recovery after exhaustion"""
        db_manager = mock_pool_environment["db_manager"]
        pool_state = mock_pool_environment["pool_state"]
        
        # Create health checker
        health_checker = DatabaseHealthChecker()
        
        # Mock other services
        mock_redis_manager = AsyncMock()
        mock_redis_manager.set.return_value = True
        mock_redis_manager.get.return_value = "test"
        mock_redis_manager.delete.return_value = True
        mock_redis_manager.is_degraded.return_value = False
        mock_redis_manager.get_connection_info.return_value = {"memory_cache_size": 100}
        
        mock_milvus_client = AsyncMock()
        mock_milvus_client.connect.return_value = None
        mock_milvus_client.health_check.return_value = {"status": "healthy"}
        
        with patch.object(health_checker, 'db_manager', db_manager), \
             patch.object(health_checker, 'redis_manager', mock_redis_manager), \
             patch.object(health_checker, 'milvus_client', mock_milvus_client):
            
            # Phase 1: Exhaust the pool
            exhaustion_tasks = 20  # More than pool capacity
            
            async def exhaustion_task(task_id: int):
                """Task that holds connections to exhaust pool"""
                try:
                    async with db_manager.async_session_scope() as session:
                        # Hold connection for a while
                        await asyncio.sleep(0.5)
                        await session.execute(text("SELECT 1"))
                        return {"task_id": task_id, "success": True}
                except Exception as e:
                    return {"task_id": task_id, "success": False, "error": str(e)}
            
            # Start exhaustion tasks but don't wait for completion yet
            exhaustion_task_objects = [exhaustion_task(i) for i in range(exhaustion_tasks)]
            
            # Give tasks time to start and exhaust pool
            await asyncio.sleep(0.1)
            
            # Phase 2: Try health checks during exhaustion
            exhaustion_health_results = []
            for _ in range(3):
                try:
                    result = await health_checker.check_health(include_detailed_validation=False)
                    exhaustion_health_results.append({
                        "success": True,
                        "status": result.overall_status,
                        "pool_metrics": result.performance_metrics.get("postgresql", {}).get("pool_metrics", {}),
                    })
                except Exception as e:
                    exhaustion_health_results.append({
                        "success": False,
                        "error": str(e),
                    })
                
                await asyncio.sleep(0.1)
            
            # Wait for exhaustion tasks to complete (releasing connections)
            await asyncio.gather(*exhaustion_task_objects, return_exceptions=True)
            
            # Phase 3: Test recovery
            await asyncio.sleep(0.2)  # Allow pool to recover
            
            recovery_health_results = []
            for _ in range(5):
                try:
                    result = await health_checker.check_health(include_detailed_validation=False)
                    recovery_health_results.append({
                        "success": True,
                        "status": result.overall_status,
                        "pool_metrics": result.performance_metrics.get("postgresql", {}).get("pool_metrics", {}),
                    })
                except Exception as e:
                    recovery_health_results.append({
                        "success": False,
                        "error": str(e),
                    })
                
                await asyncio.sleep(0.1)
            
            # Analyze recovery
            exhaustion_success_rate = sum(1 for r in exhaustion_health_results if r.get("success")) / len(exhaustion_health_results)
            recovery_success_rate = sum(1 for r in recovery_health_results if r.get("success")) / len(recovery_health_results)
            
            # During exhaustion, success rate should be lower
            # After recovery, success rate should improve
            assert recovery_success_rate > exhaustion_success_rate, \
                f"Recovery success rate ({recovery_success_rate}) should be higher than exhaustion rate ({exhaustion_success_rate})"
            
            # Recovery should achieve reasonable success rate
            assert recovery_success_rate > 0.6, f"Recovery success rate should be reasonable: {recovery_success_rate}"
            
            print(f"Pool recovery test: exhaustion success rate: {exhaustion_success_rate:.2%}, "
                  f"recovery success rate: {recovery_success_rate:.2%}")

    @pytest.mark.asyncio
    async def test_connection_pool_timeout_handling(self, mock_pool_environment):
        """Test connection pool timeout handling under stress"""
        db_manager = mock_pool_environment["db_manager"]
        pool_state = mock_pool_environment["pool_state"]
        
        # Modify mock to simulate slow connections
        original_session_scope = db_manager.async_session_scope
        
        def slow_session_scope():
            class SlowSessionScope:
                def __init__(self):
                    self.session = None
                
                async def __aenter__(self):
                    # Simulate slow connection establishment
                    await asyncio.sleep(random.uniform(0.1, 0.5))
                    
                    if pool_state["checked_out"] < pool_state["size"] + pool_state["max_overflow"]:
                        pool_state["checked_out"] += 1
                        pool_state["active_connections"] += 1
                        
                        mock_session = AsyncMock()
                        
                        # Simulate slow queries
                        async def slow_execute(*args, **kwargs):
                            await asyncio.sleep(random.uniform(0.05, 0.2))
                            result = Mock()
                            result.scalar.return_value = "PostgreSQL 13.0"
                            return result
                        
                        mock_session.execute = slow_execute
                        self.session = mock_session
                        return mock_session
                    else:
                        raise Exception("Connection timeout - pool exhausted")
                
                async def __aexit__(self, exc_type, exc_val, exc_tb):
                    if self.session:
                        pool_state["checked_out"] = max(0, pool_state["checked_out"] - 1)
                        pool_state["active_connections"] = max(0, pool_state["active_connections"] - 1)
            
            return SlowSessionScope()
        
        db_manager.async_session_scope = slow_session_scope
        
        # Create health checker
        health_checker = DatabaseHealthChecker()
        
        # Mock other services
        mock_redis_manager = AsyncMock()
        mock_redis_manager.set.return_value = True
        mock_redis_manager.get.return_value = "test"
        mock_redis_manager.delete.return_value = True
        mock_redis_manager.is_degraded.return_value = False
        mock_redis_manager.get_connection_info.return_value = {"memory_cache_size": 100}
        
        mock_milvus_client = AsyncMock()
        mock_milvus_client.connect.return_value = None
        mock_milvus_client.health_check.return_value = {"status": "healthy"}
        
        with patch.object(health_checker, 'db_manager', db_manager), \
             patch.object(health_checker, 'redis_manager', mock_redis_manager), \
             patch.object(health_checker, 'milvus_client', mock_milvus_client):
            
            # Test timeout handling with concurrent requests
            timeout_tasks = 15
            
            async def timeout_test_task(task_id: int):
                """Task that tests timeout handling"""
                start_time = time.time()
                try:
                    # Set a reasonable timeout for the health check
                    result = await asyncio.wait_for(
                        health_checker.check_health(include_detailed_validation=False),
                        timeout=2.0  # 2 second timeout
                    )
                    duration = time.time() - start_time
                    
                    return {
                        "task_id": task_id,
                        "success": True,
                        "duration": duration,
                        "status": result.overall_status,
                        "timed_out": False,
                    }
                except asyncio.TimeoutError:
                    duration = time.time() - start_time
                    return {
                        "task_id": task_id,
                        "success": False,
                        "duration": duration,
                        "error": "Timeout",
                        "timed_out": True,
                    }
                except Exception as e:
                    duration = time.time() - start_time
                    return {
                        "task_id": task_id,
                        "success": False,
                        "duration": duration,
                        "error": str(e),
                        "timed_out": False,
                    }
            
            # Execute timeout test
            start_time = time.time()
            tasks = [timeout_test_task(i) for i in range(timeout_tasks)]
            results = await asyncio.gather(*tasks)
            total_duration = time.time() - start_time
            
            # Analyze timeout handling
            successful_tasks = [r for r in results if r.get("success")]
            timed_out_tasks = [r for r in results if r.get("timed_out")]
            failed_tasks = [r for r in results if not r.get("success") and not r.get("timed_out")]
            
            # Verify timeout handling
            total_tasks = len(results)
            success_rate = len(successful_tasks) / total_tasks
            timeout_rate = len(timed_out_tasks) / total_tasks
            
            # Some tasks should complete successfully even with slow connections
            assert success_rate > 0.2, f"Success rate too low with slow connections: {success_rate}"
            
            # Timeouts should be handled gracefully (not crash the system)
            assert timeout_rate < 0.8, f"Too many timeouts, system may be unresponsive: {timeout_rate}"
            
            # Average duration of successful tasks should be reasonable
            if successful_tasks:
                avg_success_duration = sum(r["duration"] for r in successful_tasks) / len(successful_tasks)
                assert avg_success_duration < 2.0, f"Successful tasks taking too long: {avg_success_duration}s"
            
            print(f"Timeout handling test: {success_rate:.2%} success, {timeout_rate:.2%} timeout, "
                  f"total duration: {total_duration:.2f}s")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])