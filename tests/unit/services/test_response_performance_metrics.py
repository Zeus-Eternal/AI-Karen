"""
Unit tests for Response Performance Metrics system
"""

import pytest
import asyncio
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from src.ai_karen_engine.services.response_performance_metrics import (
    ResponsePerformanceCollector,
    ResponsePerformanceMetrics,
    OptimizationType,
    MetricType,
    AggregatedMetrics,
    BottleneckAnalysis
)


class TestResponsePerformanceCollector:
    """Test cases for ResponsePerformanceCollector"""
    
    @pytest.fixture
    def collector(self):
        """Create a test collector instance"""
        return ResponsePerformanceCollector(max_metrics_history=100)
    
    def test_start_response_tracking(self, collector):
        """Test starting response tracking"""
        response_id = "test_response_123"
        query = "Test query"
        model_used = "test_model"
        
        collector.start_response_tracking(response_id, query, model_used)
        
        assert response_id in collector.active_responses
        assert collector.active_responses[response_id]['query'] == query
        assert collector.active_responses[response_id]['model_used'] == model_used
        assert collector.current_metrics['active_responses'] == 1
    
    def test_record_optimization_applied(self, collector):
        """Test recording optimization application"""
        response_id = "test_response_123"
        collector.start_response_tracking(response_id, "test", "model")
        
        collector.record_optimization_applied(response_id, OptimizationType.CACHE_OPTIMIZATION)
        
        assert OptimizationType.CACHE_OPTIMIZATION in collector.active_responses[response_id]['optimizations_applied']
    
    def test_record_bottleneck(self, collector):
        """Test recording bottlenecks"""
        response_id = "test_response_123"
        collector.start_response_tracking(response_id, "test", "model")
        
        collector.record_bottleneck(response_id, "model_loading")
        
        assert "model_loading" in collector.active_responses[response_id]['bottlenecks']
    
    def test_record_streaming_chunk(self, collector):
        """Test recording streaming chunks"""
        response_id = "test_response_123"
        collector.start_response_tracking(response_id, "test", "model")
        
        collector.record_streaming_chunk(response_id)
        collector.record_streaming_chunk(response_id)
        
        assert collector.active_responses[response_id]['streaming_chunks'] == 2
    
    def test_record_error(self, collector):
        """Test recording errors"""
        response_id = "test_response_123"
        collector.start_response_tracking(response_id, "test", "model")
        
        collector.record_error(response_id, "timeout")
        
        assert collector.active_responses[response_id]['error_occurred'] is True
        assert collector.active_responses[response_id]['error_type'] == "timeout"
    
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    def test_finish_response_tracking(self, mock_memory, mock_cpu, collector):
        """Test finishing response tracking"""
        # Mock system metrics
        mock_cpu.return_value = 15.0
        mock_memory.return_value.used = 1024 * 1024 * 1024  # 1GB
        
        response_id = "test_response_123"
        collector.start_response_tracking(response_id, "test query", "test_model")
        
        # Simulate some processing time
        time.sleep(0.1)
        
        metrics = collector.finish_response_tracking(
            response_id=response_id,
            response_size=1000,
            cache_hit_rate=75.0,
            model_efficiency=85.0,
            content_relevance_score=90.0
        )
        
        assert metrics is not None
        assert metrics.response_id == response_id
        assert metrics.query == "test query"
        assert metrics.model_used == "test_model"
        assert metrics.response_time > 0
        assert metrics.response_size == 1000
        assert metrics.cache_hit_rate == 75.0
        assert metrics.model_efficiency == 85.0
        assert metrics.content_relevance_score == 90.0
        assert response_id not in collector.active_responses
        assert collector.current_metrics['active_responses'] == 0
    
    def test_get_metrics_history(self, collector):
        """Test getting metrics history"""
        # Add some test metrics
        for i in range(5):
            collector.start_response_tracking(f"response_{i}", f"query_{i}", "model")
            collector.finish_response_tracking(f"response_{i}")
        
        history = collector.get_metrics_history(limit=3)
        assert len(history) == 3
        
        all_history = collector.get_metrics_history()
        assert len(all_history) == 5
    
    def test_get_current_metrics(self, collector):
        """Test getting current metrics"""
        current = collector.get_current_metrics()
        
        assert 'active_responses' in current
        assert 'avg_response_time_1min' in current
        assert 'cpu_usage_current' in current
        assert 'memory_usage_current' in current
        assert 'cache_hit_rate_1min' in current
        assert 'throughput_1min' in current
        assert 'error_rate_1min' in current
    
    def test_get_aggregated_metrics_empty(self, collector):
        """Test getting aggregated metrics with no data"""
        time_period = timedelta(hours=1)
        metrics = collector.get_aggregated_metrics(time_period)
        
        assert metrics.total_responses == 0
        assert metrics.avg_response_time == 0.0
        assert metrics.error_rate == 0.0
    
    def test_get_aggregated_metrics_with_data(self, collector):
        """Test getting aggregated metrics with data"""
        # Add test metrics
        test_metrics = []
        for i in range(10):
            collector.start_response_tracking(f"response_{i}", f"query_{i}", f"model_{i % 3}")
            metrics = collector.finish_response_tracking(
                f"response_{i}",
                response_size=100 + i * 10,
                cache_hit_rate=70.0 + i,
                model_efficiency=80.0 + i
            )
            test_metrics.append(metrics)
        
        time_period = timedelta(hours=1)
        aggregated = collector.get_aggregated_metrics(time_period)
        
        assert aggregated.total_responses == 10
        assert aggregated.avg_response_time > 0
        assert len(aggregated.most_used_models) == 3
        assert aggregated.cache_hit_rate > 70.0
    
    def test_analyze_bottlenecks(self, collector):
        """Test bottleneck analysis"""
        # Add test data with bottlenecks
        for i in range(5):
            collector.start_response_tracking(f"response_{i}", f"query_{i}", "model")
            collector.record_bottleneck(f"response_{i}", "model_loading")
            if i % 2 == 0:
                collector.record_bottleneck(f"response_{i}", "memory_pressure")
            collector.finish_response_tracking(f"response_{i}")
        
        time_period = timedelta(hours=1)
        bottlenecks = collector.analyze_bottlenecks(time_period)
        
        assert len(bottlenecks) > 0
        
        # Find model_loading bottleneck
        model_loading_bottleneck = next(
            (b for b in bottlenecks if b.bottleneck_type == "model_loading"), 
            None
        )
        assert model_loading_bottleneck is not None
        assert model_loading_bottleneck.frequency == 5
        assert len(model_loading_bottleneck.suggested_optimizations) > 0
    
    def test_export_metrics(self, collector, tmp_path):
        """Test exporting metrics to file"""
        # Add test data
        for i in range(3):
            collector.start_response_tracking(f"response_{i}", f"query_{i}", "model")
            collector.finish_response_tracking(f"response_{i}")
        
        export_file = tmp_path / "test_export.json"
        collector.export_metrics(str(export_file))
        
        assert export_file.exists()
        
        # Verify exported data
        import json
        with open(export_file) as f:
            data = json.load(f)
        
        assert len(data) == 3
        assert all('response_id' in item for item in data)
        assert all('timestamp' in item for item in data)
    
    def test_optimization_suggestions(self, collector):
        """Test optimization suggestion generation"""
        suggestions = collector._generate_optimization_suggestions("model_loading", 5.0)
        
        assert len(suggestions) > 0
        assert any("preloading" in s.lower() for s in suggestions)
        
        gpu_suggestions = collector._generate_optimization_suggestions("gpu_memory", 3.0)
        assert any("gpu" in s.lower() for s in gpu_suggestions)
    
    def test_concurrent_tracking(self, collector):
        """Test concurrent response tracking"""
        import threading
        
        def track_response(response_id):
            collector.start_response_tracking(response_id, f"query_{response_id}", "model")
            time.sleep(0.01)  # Simulate processing
            collector.finish_response_tracking(response_id)
        
        threads = []
        for i in range(10):
            thread = threading.Thread(target=track_response, args=(f"response_{i}",))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # All responses should be completed
        assert len(collector.active_responses) == 0
        assert len(collector.metrics_history) == 10


class TestResponsePerformanceMetrics:
    """Test cases for ResponsePerformanceMetrics data class"""
    
    def test_metrics_creation(self):
        """Test creating performance metrics"""
        metrics = ResponsePerformanceMetrics(
            response_id="test_123",
            timestamp=datetime.now(),
            query="test query",
            model_used="test_model",
            response_time=1.5,
            cpu_usage=10.0,
            memory_usage=1024 * 1024,
            cache_hit_rate=80.0
        )
        
        assert metrics.response_id == "test_123"
        assert metrics.query == "test query"
        assert metrics.model_used == "test_model"
        assert metrics.response_time == 1.5
        assert metrics.cpu_usage == 10.0
        assert metrics.memory_usage == 1024 * 1024
        assert metrics.cache_hit_rate == 80.0
        assert metrics.optimizations_applied == []
        assert metrics.bottlenecks == []
    
    def test_metrics_with_optimizations(self):
        """Test metrics with optimizations applied"""
        metrics = ResponsePerformanceMetrics(
            response_id="test_123",
            timestamp=datetime.now(),
            query="test query",
            model_used="test_model",
            response_time=1.5,
            cpu_usage=10.0,
            memory_usage=1024 * 1024,
            optimizations_applied=[OptimizationType.CACHE_OPTIMIZATION, OptimizationType.GPU_ACCELERATION]
        )
        
        assert len(metrics.optimizations_applied) == 2
        assert OptimizationType.CACHE_OPTIMIZATION in metrics.optimizations_applied
        assert OptimizationType.GPU_ACCELERATION in metrics.optimizations_applied


class TestAggregatedMetrics:
    """Test cases for AggregatedMetrics"""
    
    def test_aggregated_metrics_creation(self):
        """Test creating aggregated metrics"""
        start_time = datetime.now() - timedelta(hours=1)
        end_time = datetime.now()
        
        metrics = AggregatedMetrics(
            period_start=start_time,
            period_end=end_time,
            total_responses=100,
            avg_response_time=2.5,
            p95_response_time=5.0,
            p99_response_time=8.0,
            avg_cpu_usage=15.0,
            avg_memory_usage=1024 * 1024 * 512,
            avg_gpu_usage=45.0,
            cache_hit_rate=75.0,
            avg_user_satisfaction=4.2,
            error_rate=2.5,
            throughput=50.0,
            most_used_models={"model_a": 60, "model_b": 40},
            optimization_effectiveness={OptimizationType.CACHE_OPTIMIZATION: 25.0},
            identified_bottlenecks={"model_loading": 5, "memory_pressure": 2}
        )
        
        assert metrics.total_responses == 100
        assert metrics.avg_response_time == 2.5
        assert metrics.cache_hit_rate == 75.0
        assert "model_a" in metrics.most_used_models
        assert OptimizationType.CACHE_OPTIMIZATION in metrics.optimization_effectiveness


class TestBottleneckAnalysis:
    """Test cases for BottleneckAnalysis"""
    
    def test_bottleneck_analysis_creation(self):
        """Test creating bottleneck analysis"""
        analysis = BottleneckAnalysis(
            bottleneck_type="model_loading",
            frequency=10,
            avg_impact=3.5,
            affected_models=["model_a", "model_b"],
            suggested_optimizations=["Enable model preloading", "Use model caching"],
            severity="HIGH"
        )
        
        assert analysis.bottleneck_type == "model_loading"
        assert analysis.frequency == 10
        assert analysis.avg_impact == 3.5
        assert len(analysis.affected_models) == 2
        assert len(analysis.suggested_optimizations) == 2
        assert analysis.severity == "HIGH"


@pytest.mark.asyncio
class TestPerformanceIntegration:
    """Integration tests for performance monitoring"""
    
    async def test_full_response_lifecycle(self):
        """Test complete response lifecycle tracking"""
        collector = ResponsePerformanceCollector(max_metrics_history=10)
        
        response_id = "integration_test_123"
        query = "Integration test query"
        model_used = "integration_model"
        
        # Start tracking
        collector.start_response_tracking(response_id, query, model_used)
        
        # Simulate processing with various events
        collector.record_optimization_applied(response_id, OptimizationType.CACHE_OPTIMIZATION)
        collector.record_streaming_chunk(response_id)
        collector.record_streaming_chunk(response_id)
        collector.record_bottleneck(response_id, "network_latency")
        
        # Finish tracking
        metrics = collector.finish_response_tracking(
            response_id=response_id,
            response_size=2048,
            cache_hit_rate=85.0,
            model_efficiency=92.0,
            content_relevance_score=88.0,
            cuda_acceleration_gain=15.0
        )
        
        # Verify complete metrics
        assert metrics.response_id == response_id
        assert metrics.query == query
        assert metrics.model_used == model_used
        assert metrics.response_size == 2048
        assert metrics.streaming_chunks == 2
        assert OptimizationType.CACHE_OPTIMIZATION in metrics.optimizations_applied
        assert "network_latency" in metrics.bottlenecks
        assert metrics.cuda_acceleration_gain == 15.0
        
        # Verify aggregated metrics
        aggregated = collector.get_aggregated_metrics(timedelta(minutes=1))
        assert aggregated.total_responses == 1
        assert aggregated.avg_response_time > 0
        assert aggregated.cache_hit_rate == 85.0
    
    async def test_performance_monitoring_workflow(self):
        """Test typical performance monitoring workflow"""
        collector = ResponsePerformanceCollector(max_metrics_history=50)
        
        # Simulate multiple responses with different characteristics
        test_scenarios = [
            {"model": "fast_model", "cache_hit": 90.0, "optimizations": [OptimizationType.CACHE_OPTIMIZATION]},
            {"model": "slow_model", "cache_hit": 30.0, "optimizations": [], "bottlenecks": ["model_loading"]},
            {"model": "gpu_model", "cache_hit": 70.0, "optimizations": [OptimizationType.GPU_ACCELERATION]},
            {"model": "fast_model", "cache_hit": 85.0, "optimizations": [OptimizationType.CACHE_OPTIMIZATION]},
            {"model": "error_model", "cache_hit": 0.0, "optimizations": [], "error": "timeout"}
        ]
        
        for i, scenario in enumerate(test_scenarios):
            response_id = f"scenario_{i}"
            collector.start_response_tracking(response_id, f"query_{i}", scenario["model"])
            
            # Apply optimizations
            for opt in scenario.get("optimizations", []):
                collector.record_optimization_applied(response_id, opt)
            
            # Add bottlenecks
            for bottleneck in scenario.get("bottlenecks", []):
                collector.record_bottleneck(response_id, bottleneck)
            
            # Add errors
            if "error" in scenario:
                collector.record_error(response_id, scenario["error"])
            
            # Finish tracking
            collector.finish_response_tracking(
                response_id=response_id,
                cache_hit_rate=scenario["cache_hit"]
            )
        
        # Analyze results
        aggregated = collector.get_aggregated_metrics(timedelta(minutes=1))
        assert aggregated.total_responses == 5
        assert "fast_model" in aggregated.most_used_models
        assert aggregated.error_rate == 20.0  # 1 out of 5 had errors
        
        # Analyze bottlenecks
        bottlenecks = collector.analyze_bottlenecks(timedelta(minutes=1))
        model_loading_bottleneck = next(
            (b for b in bottlenecks if b.bottleneck_type == "model_loading"), 
            None
        )
        assert model_loading_bottleneck is not None
        assert model_loading_bottleneck.frequency == 1