"""
Tests for Performance Benchmarking System - Task 8.4
Tests continuous performance monitoring with SLO tracking,
automated performance regression testing, and real-time dashboards.
"""

import asyncio
import pytest
import time
from typing import List, Dict, Any
from unittest.mock import Mock, patch, AsyncMock

from src.ai_karen_engine.services.performance_benchmarking import (
    PerformanceBenchmarker, BenchmarkConfig, BenchmarkResult, BenchmarkType,
    LoadProfile
)

class TestPerformanceBenchmarker:
    """Test performance benchmarking functionality"""
    
    @pytest.fixture
    def benchmarker(self):
        """Create performance benchmarker"""
        return PerformanceBenchmarker(max_workers=5)
    
    @pytest.fixture
    def test_config(self):
        """Create test benchmark configuration"""
        return BenchmarkConfig(
            benchmark_type=BenchmarkType.VECTOR_QUERY,
            load_profile=LoadProfile.LIGHT,
            duration_seconds=5,  # Short duration for tests
            target_rps=2.0,
            warmup_seconds=1,
            target_p95_latency_ms=100.0,
            target_error_rate=0.05
        )
    
    @pytest.fixture
    def mock_test_function(self):
        """Create mock test function"""
        async def test_func(data):
            # Simulate some work
            await asyncio.sleep(0.01)  # 10ms latency
            return f"Result for {data}"
        
        return test_func
    
    @pytest.fixture
    def test_data(self):
        """Create test data"""
        return [f"test_data_{i}" for i in range(20)]
    
    def test_benchmarker_initialization(self, benchmarker):
        """Test benchmarker initialization"""
        assert benchmarker.max_workers == 5
        assert len(benchmarker.benchmark_history) == 0
        assert len(benchmarker.active_benchmarks) == 0
        assert len(benchmarker.baselines) == 0
    
    @pytest.mark.asyncio
    async def test_single_request_execution(self, benchmarker, mock_test_function):
        """Test single request execution"""
        result = await benchmarker._execute_single_request(
            mock_test_function, "test_data", "test_benchmark"
        )
        
        assert result["success"] is True
        assert result["latency_ms"] > 0
        assert "Result for test_data" in result["result"]
    
    @pytest.mark.asyncio
    async def test_single_request_error_handling(self, benchmarker):
        """Test single request error handling"""
        async def failing_function(data):
            raise ValueError("Test error")
        
        result = await benchmarker._execute_single_request(
            failing_function, "test_data", "test_benchmark"
        )
        
        assert result["success"] is False
        assert result["latency_ms"] > 0
        assert "Test error" in result["error"]
    
    @pytest.mark.asyncio
    async def test_light_load_benchmark(self, benchmarker, test_config, mock_test_function, test_data):
        """Test light load benchmark execution"""
        # Use very short duration for test
        test_config.duration_seconds = 2
        test_config.warmup_seconds = 0  # Skip warmup for faster test
        
        result = await benchmarker.run_benchmark(
            test_config, mock_test_function, test_data
        )
        
        assert isinstance(result, BenchmarkResult)
        assert result.benchmark_type == BenchmarkType.VECTOR_QUERY
        assert result.load_profile == LoadProfile.LIGHT
        assert result.total_requests > 0
        assert result.successful_requests > 0
        assert result.error_rate == 0.0  # No errors expected
        assert result.avg_latency_ms > 0
        assert result.actual_rps > 0
    
    @pytest.mark.asyncio
    async def test_benchmark_with_warmup(self, benchmarker, test_config, mock_test_function, test_data):
        """Test benchmark with warmup phase"""
        test_config.duration_seconds = 2
        test_config.warmup_seconds = 1
        
        result = await benchmarker.run_benchmark(
            test_config, mock_test_function, test_data
        )
        
        assert result.total_requests > 0
        assert result.successful_requests > 0
        # Warmup requests shouldn't be counted in final results
        assert result.duration_seconds >= 2.0  # Should include warmup time
    
    @pytest.mark.asyncio
    async def test_moderate_load_benchmark(self, benchmarker, mock_test_function, test_data):
        """Test moderate load benchmark"""
        config = BenchmarkConfig(
            benchmark_type=BenchmarkType.LLM_GENERATION,
            load_profile=LoadProfile.MODERATE,
            duration_seconds=2,
            warmup_seconds=0,
            target_p95_latency_ms=50.0
        )
        
        result = await benchmarker.run_benchmark(
            config, mock_test_function, test_data
        )
        
        assert result.load_profile == LoadProfile.MODERATE
        assert result.actual_rps > 2.0  # Should be higher than light load
    
    @pytest.mark.asyncio
    async def test_burst_load_benchmark(self, benchmarker, mock_test_function, test_data):
        """Test burst load benchmark"""
        config = BenchmarkConfig(
            benchmark_type=BenchmarkType.E2E_PIPELINE,
            load_profile=LoadProfile.BURST,
            duration_seconds=10,  # Longer for burst pattern
            warmup_seconds=0,
            target_p95_latency_ms=100.0
        )
        
        result = await benchmarker.run_benchmark(
            config, mock_test_function, test_data
        )
        
        assert result.load_profile == LoadProfile.BURST
        assert result.total_requests > 10  # Should have multiple phases
    
    def test_benchmark_result_calculation(self, benchmarker):
        """Test benchmark result calculation"""
        from datetime import datetime
        
        config = BenchmarkConfig(
            benchmark_type=BenchmarkType.VECTOR_QUERY,
            load_profile=LoadProfile.LIGHT,
            target_p95_latency_ms=100.0,
            target_error_rate=0.05
        )
        
        start_time = datetime.utcnow()
        end_time = datetime.utcnow()
        duration = 10.0
        
        # Mock benchmark data
        benchmark_id = "test_benchmark"
        with benchmarker.lock:
            benchmarker.active_benchmarks[benchmark_id] = {
                "latencies": [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0],
                "requests_completed": 9,
                "requests_failed": 1
            }
        
        result = benchmarker._calculate_benchmark_result(
            benchmark_id, config, start_time, end_time, duration, {}
        )
        
        assert result.total_requests == 10
        assert result.successful_requests == 9
        assert result.failed_requests == 1
        assert result.error_rate == 0.1
        assert result.avg_latency_ms == 55.0  # Average of test data
        assert result.p95_latency_ms == 100.0  # 95th percentile
        assert result.actual_rps == 0.9  # 9 successful / 10 seconds
    
    def test_slo_compliance_checking(self, benchmarker):
        """Test SLO compliance checking"""
        from datetime import datetime
        
        config = BenchmarkConfig(
            benchmark_type=BenchmarkType.VECTOR_QUERY,
            load_profile=LoadProfile.LIGHT,
            target_p95_latency_ms=50.0,  # Strict target
            target_p99_latency_ms=100.0,
            target_error_rate=0.05,
            target_throughput_rps=1.0
        )
        
        start_time = datetime.utcnow()
        end_time = datetime.utcnow()
        duration = 10.0
        
        # Mock benchmark data that violates SLOs
        benchmark_id = "test_benchmark"
        with benchmarker.lock:
            benchmarker.active_benchmarks[benchmark_id] = {
                "latencies": [100.0] * 10,  # All requests take 100ms (violates p95 < 50ms)
                "requests_completed": 8,
                "requests_failed": 2  # 20% error rate (violates < 5%)
            }
        
        result = benchmarker._calculate_benchmark_result(
            benchmark_id, config, start_time, end_time, duration, {}
        )
        
        # Should fail SLO compliance
        assert result.slo_compliance["p95_latency"] is False  # 100ms > 50ms target
        assert result.slo_compliance["error_rate"] is False   # 20% > 5% target
        assert result.slo_compliance["throughput"] is False   # 0.8 RPS < 1.0 target
    
    @pytest.mark.asyncio
    async def test_regression_detection(self, benchmarker, test_config, mock_test_function, test_data):
        """Test performance regression detection"""
        test_config.duration_seconds = 1
        test_config.warmup_seconds = 0
        
        # Run first benchmark to establish baseline
        result1 = await benchmarker.run_benchmark(
            test_config, mock_test_function, test_data
        )
        
        # Verify baseline was established
        assert BenchmarkType.VECTOR_QUERY in benchmarker.baselines
        baseline = benchmarker.baselines[BenchmarkType.VECTOR_QUERY]
        assert baseline["p95_latency_ms"] > 0
        
        # Create a slower mock function to trigger regression
        async def slow_test_function(data):
            await asyncio.sleep(0.1)  # 100ms latency (much slower)
            return f"Slow result for {data}"
        
        # Run second benchmark with slower function
        result2 = await benchmarker.run_benchmark(
            test_config, slow_test_function, test_data
        )
        
        # Should detect regression
        assert len(benchmarker.regression_alerts) > 0
        alert = benchmarker.regression_alerts[-1]
        assert alert["benchmark_type"] == BenchmarkType.VECTOR_QUERY.value
        assert len(alert["regressions"]) > 0
    
    def test_benchmark_history(self, benchmarker):
        """Test benchmark history management"""
        from datetime import datetime
        
        # Add some mock results
        for i in range(5):
            result = BenchmarkResult(
                benchmark_id=f"test_{i}",
                benchmark_type=BenchmarkType.VECTOR_QUERY,
                load_profile=LoadProfile.LIGHT,
                start_time=datetime.utcnow(),
                end_time=datetime.utcnow(),
                duration_seconds=10.0,
                total_requests=100,
                successful_requests=95,
                failed_requests=5,
                error_rate=0.05,
                avg_latency_ms=50.0,
                p50_latency_ms=45.0,
                p95_latency_ms=80.0,
                p99_latency_ms=95.0,
                max_latency_ms=100.0,
                min_latency_ms=10.0,
                actual_rps=9.5,
                peak_rps=10.0,
                slo_compliance={"p95_latency": True, "error_rate": True}
            )
            benchmarker.benchmark_history.append(result)
        
        # Test getting all history
        history = benchmarker.get_benchmark_history()
        assert len(history) == 5
        
        # Test filtering by benchmark type
        vector_history = benchmarker.get_benchmark_history(BenchmarkType.VECTOR_QUERY)
        assert len(vector_history) == 5
        assert all(r.benchmark_type == BenchmarkType.VECTOR_QUERY for r in vector_history)
        
        # Test limiting results
        limited_history = benchmarker.get_benchmark_history(limit=3)
        assert len(limited_history) == 3
    
    def test_performance_dashboard(self, benchmarker):
        """Test performance dashboard generation"""
        from datetime import datetime
        
        # Add some mock results and alerts
        for i in range(3):
            result = BenchmarkResult(
                benchmark_id=f"test_{i}",
                benchmark_type=BenchmarkType.VECTOR_QUERY,
                load_profile=LoadProfile.LIGHT,
                start_time=datetime.utcnow(),
                end_time=datetime.utcnow(),
                duration_seconds=10.0,
                total_requests=100,
                successful_requests=95,
                failed_requests=5,
                error_rate=0.05,
                avg_latency_ms=50.0,
                p50_latency_ms=45.0,
                p95_latency_ms=80.0,
                p99_latency_ms=95.0,
                max_latency_ms=100.0,
                min_latency_ms=10.0,
                actual_rps=9.5,
                peak_rps=10.0,
                slo_compliance={"p95_latency": True, "error_rate": True, "throughput": True}
            )
            benchmarker.benchmark_history.append(result)
        
        # Add a regression alert
        benchmarker.regression_alerts.append({
            "benchmark_id": "test_regression",
            "benchmark_type": BenchmarkType.VECTOR_QUERY.value,
            "timestamp": datetime.utcnow(),
            "regressions": [{"metric": "p95_latency_ms", "degradation_pct": 25.0}]
        })
        
        dashboard = benchmarker.get_performance_dashboard()
        
        assert "summary" in dashboard
        assert "recent_results" in dashboard
        assert "slo_compliance" in dashboard
        assert "regression_alerts" in dashboard
        assert "baselines" in dashboard
        
        # Check summary
        summary = dashboard["summary"]
        assert summary["total_benchmarks"] == 3
        assert summary["recent_regressions"] == 1
        
        # Check recent results
        assert len(dashboard["recent_results"]) == 3
        
        # Check SLO compliance
        if BenchmarkType.VECTOR_QUERY.value in dashboard["slo_compliance"]:
            compliance = dashboard["slo_compliance"][BenchmarkType.VECTOR_QUERY.value]
            assert compliance["compliance_rate"] == 1.0  # All results compliant
            assert compliance["total_runs"] == 3
    
    def test_results_export(self, benchmarker):
        """Test benchmark results export"""
        from datetime import datetime
        import json
        
        # Add a mock result
        result = BenchmarkResult(
            benchmark_id="export_test",
            benchmark_type=BenchmarkType.LLM_GENERATION,
            load_profile=LoadProfile.MODERATE,
            start_time=datetime.utcnow(),
            end_time=datetime.utcnow(),
            duration_seconds=60.0,
            total_requests=300,
            successful_requests=295,
            failed_requests=5,
            error_rate=0.017,
            avg_latency_ms=150.0,
            p50_latency_ms=140.0,
            p95_latency_ms=200.0,
            p99_latency_ms=250.0,
            max_latency_ms=300.0,
            min_latency_ms=50.0,
            actual_rps=4.92,
            peak_rps=5.0,
            slo_compliance={"p95_latency": True, "error_rate": True}
        )
        benchmarker.benchmark_history.append(result)
        
        # Export results
        exported_json = benchmarker.export_results("json")
        
        # Parse and validate
        data = json.loads(exported_json)
        
        assert "export_timestamp" in data
        assert "total_benchmarks" in data
        assert "benchmark_results" in data
        assert data["total_benchmarks"] == 1
        assert len(data["benchmark_results"]) == 1
        
        exported_result = data["benchmark_results"][0]
        assert exported_result["benchmark_id"] == "export_test"
        assert exported_result["benchmark_type"] == BenchmarkType.LLM_GENERATION.value
        assert exported_result["total_requests"] == 300
    
    def test_unsupported_export_format(self, benchmarker):
        """Test unsupported export format handling"""
        with pytest.raises(ValueError, match="Unsupported export format"):
            benchmarker.export_results("xml")

class TestBenchmarkIntegration:
    """Integration tests for benchmarking system"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_benchmark_workflow(self):
        """Test complete benchmark workflow"""
        benchmarker = PerformanceBenchmarker(max_workers=3)
        
        # Create test function that simulates realistic work
        async def realistic_test_function(data):
            # Simulate variable latency
            import random
            latency = random.uniform(0.01, 0.05)  # 10-50ms
            await asyncio.sleep(latency)
            
            # Occasionally fail to test error handling
            if random.random() < 0.05:  # 5% failure rate
                raise Exception("Simulated failure")
            
            return f"Processed {data}"
        
        config = BenchmarkConfig(
            benchmark_type=BenchmarkType.E2E_PIPELINE,
            load_profile=LoadProfile.LIGHT,
            duration_seconds=3,
            warmup_seconds=1,
            target_p95_latency_ms=100.0,
            target_error_rate=0.1,  # Allow 10% errors
            target_throughput_rps=0.8
        )
        
        test_data = [f"item_{i}" for i in range(20)]
        
        # Run benchmark
        result = await benchmarker.run_benchmark(
            config, realistic_test_function, test_data
        )
        
        # Verify results
        assert result.total_requests > 0
        assert result.duration_seconds >= 3.0
        assert result.avg_latency_ms > 0
        assert result.actual_rps > 0
        
        # Check that history was recorded
        history = benchmarker.get_benchmark_history()
        assert len(history) == 1
        assert history[0].benchmark_id == result.benchmark_id
        
        # Check dashboard
        dashboard = benchmarker.get_performance_dashboard()
        assert dashboard["summary"]["total_benchmarks"] == 1
    
    @pytest.mark.asyncio
    async def test_concurrent_benchmarks(self):
        """Test running multiple benchmarks concurrently"""
        benchmarker = PerformanceBenchmarker(max_workers=10)
        
        async def test_function_a(data):
            await asyncio.sleep(0.01)
            return f"A: {data}"
        
        async def test_function_b(data):
            await asyncio.sleep(0.02)
            return f"B: {data}"
        
        config_a = BenchmarkConfig(
            benchmark_type=BenchmarkType.VECTOR_QUERY,
            load_profile=LoadProfile.LIGHT,
            duration_seconds=2,
            warmup_seconds=0
        )
        
        config_b = BenchmarkConfig(
            benchmark_type=BenchmarkType.LLM_GENERATION,
            load_profile=LoadProfile.LIGHT,
            duration_seconds=2,
            warmup_seconds=0
        )
        
        test_data = [f"data_{i}" for i in range(10)]
        
        # Run benchmarks concurrently
        results = await asyncio.gather(
            benchmarker.run_benchmark(config_a, test_function_a, test_data),
            benchmarker.run_benchmark(config_b, test_function_b, test_data)
        )
        
        # Verify both completed successfully
        assert len(results) == 2
        assert results[0].benchmark_type == BenchmarkType.VECTOR_QUERY
        assert results[1].benchmark_type == BenchmarkType.LLM_GENERATION
        
        # Check history contains both
        history = benchmarker.get_benchmark_history()
        assert len(history) == 2

if __name__ == "__main__":
    pytest.main([__file__, "-v"])