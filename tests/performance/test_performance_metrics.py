"""
Tests for the performance metrics collection and monitoring system.
"""

import asyncio
import pytest
import tempfile
import json
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

from src.ai_karen_engine.core.performance_metrics import (
    PerformanceMetric,
    MetricType,
    AlertSeverity,
    SystemMetrics,
    ServiceMetrics,
    MetricsStorage,
    MetricsCollector,
    RegressionDetector,
    PerformanceDashboard,
    PerformanceBenchmark,
    PerformanceMonitoringSystem,
    get_performance_monitoring_system,
    initialize_performance_monitoring,
    shutdown_performance_monitoring
)


class TestPerformanceMetric:
    """Test PerformanceMetric data model."""
    
    def test_metric_creation(self):
        """Test creating a performance metric."""
        timestamp = datetime.now()
        metric = PerformanceMetric(
            name="test.cpu.percent",
            value=75.5,
            metric_type=MetricType.GAUGE,
            timestamp=timestamp,
            service_name="test_service",
            tags={"env": "test"},
            unit="%",
            description="Test CPU usage"
        )
        
        assert metric.name == "test.cpu.percent"
        assert metric.value == 75.5
        assert metric.metric_type == MetricType.GAUGE
        assert metric.timestamp == timestamp
        assert metric.service_name == "test_service"
        assert metric.tags == {"env": "test"}
        assert metric.unit == "%"
        assert metric.description == "Test CPU usage"
    
    def test_metric_to_dict(self):
        """Test converting metric to dictionary."""
        timestamp = datetime.now()
        metric = PerformanceMetric(
            name="test.metric",
            value=100.0,
            metric_type=MetricType.COUNTER,
            timestamp=timestamp,
            service_name="test",
            tags={"key": "value"}
        )
        
        result = metric.to_dict()
        
        assert result["name"] == "test.metric"
        assert result["value"] == 100.0
        assert result["metric_type"] == "counter"
        assert result["timestamp"] == timestamp.isoformat()
        assert result["service_name"] == "test"
        assert result["tags"] == {"key": "value"}
    
    def test_metric_from_dict(self):
        """Test creating metric from dictionary."""
        timestamp = datetime.now()
        data = {
            "name": "test.metric",
            "value": 50.0,
            "metric_type": "gauge",
            "timestamp": timestamp.isoformat(),
            "service_name": "test",
            "tags": {"env": "prod"},
            "unit": "ms",
            "description": "Test metric"
        }
        
        metric = PerformanceMetric.from_dict(data)
        
        assert metric.name == "test.metric"
        assert metric.value == 50.0
        assert metric.metric_type == MetricType.GAUGE
        assert metric.timestamp == timestamp
        assert metric.service_name == "test"
        assert metric.tags == {"env": "prod"}
        assert metric.unit == "ms"
        assert metric.description == "Test metric"


class TestSystemMetrics:
    """Test SystemMetrics data model."""
    
    def test_system_metrics_creation(self):
        """Test creating system metrics."""
        timestamp = datetime.now()
        metrics = SystemMetrics(
            timestamp=timestamp,
            cpu_percent=50.0,
            memory_usage=1024*1024*1024,  # 1GB
            memory_percent=75.0,
            disk_usage=2*1024*1024*1024,  # 2GB
            disk_percent=80.0,
            network_bytes_sent=1000000,
            network_bytes_recv=2000000,
            load_average=(1.0, 1.5, 2.0),
            process_count=150,
            thread_count=500
        )
        
        assert metrics.cpu_percent == 50.0
        assert metrics.memory_usage == 1024*1024*1024
        assert metrics.load_average == (1.0, 1.5, 2.0)
    
    def test_system_metrics_to_metrics(self):
        """Test converting system metrics to performance metrics."""
        timestamp = datetime.now()
        system_metrics = SystemMetrics(
            timestamp=timestamp,
            cpu_percent=50.0,
            memory_usage=1024*1024*1024,
            memory_percent=75.0,
            disk_usage=2*1024*1024*1024,
            disk_percent=80.0,
            network_bytes_sent=1000000,
            network_bytes_recv=2000000,
            load_average=(1.0, 1.5, 2.0),
            process_count=150,
            thread_count=500
        )
        
        metrics = system_metrics.to_metrics()
        
        assert len(metrics) == 12  # All system metrics
        
        # Check CPU metric
        cpu_metric = next(m for m in metrics if m.name == "system.cpu.percent")
        assert cpu_metric.value == 50.0
        assert cpu_metric.metric_type == MetricType.GAUGE
        assert cpu_metric.service_name == "system"
        assert cpu_metric.unit == "%"


class TestServiceMetrics:
    """Test ServiceMetrics data model."""
    
    def test_service_metrics_creation(self):
        """Test creating service metrics."""
        timestamp = datetime.now()
        metrics = ServiceMetrics(
            service_name="test_service",
            timestamp=timestamp,
            cpu_percent=25.0,
            memory_usage=512*1024*1024,  # 512MB
            memory_percent=50.0,
            io_read_bytes=1000000,
            io_write_bytes=500000,
            thread_count=10,
            open_files=50,
            network_connections=5,
            response_time=0.150,
            request_count=1000,
            error_count=5
        )
        
        assert metrics.service_name == "test_service"
        assert metrics.cpu_percent == 25.0
        assert metrics.response_time == 0.150
    
    def test_service_metrics_to_metrics(self):
        """Test converting service metrics to performance metrics."""
        timestamp = datetime.now()
        service_metrics = ServiceMetrics(
            service_name="api",
            timestamp=timestamp,
            cpu_percent=30.0,
            memory_usage=256*1024*1024,
            memory_percent=25.0,
            io_read_bytes=1000,
            io_write_bytes=2000,
            thread_count=5,
            open_files=20,
            network_connections=3,
            response_time=0.100,
            request_count=500,
            error_count=2
        )
        
        metrics = service_metrics.to_metrics()
        
        assert len(metrics) == 11  # All service metrics including response_time
        
        # Check service-specific metric
        cpu_metric = next(m for m in metrics if m.name == "service.api.cpu.percent")
        assert cpu_metric.value == 30.0
        assert cpu_metric.service_name == "api"


class TestMetricsStorage:
    """Test MetricsStorage functionality."""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = Path(f.name)
        yield db_path
        if db_path.exists():
            db_path.unlink()
    
    @pytest.fixture
    def storage(self, temp_db):
        """Create MetricsStorage instance."""
        return MetricsStorage(temp_db)
    
    @pytest.mark.asyncio
    async def test_store_metric(self, storage):
        """Test storing a single metric."""
        metric = PerformanceMetric(
            name="test.metric",
            value=100.0,
            metric_type=MetricType.GAUGE,
            timestamp=datetime.now(),
            service_name="test",
            tags={"env": "test"}
        )
        
        await storage.store_metric(metric)
        
        # Retrieve and verify
        metrics = await storage.get_metrics(metric_name="test.metric")
        assert len(metrics) == 1
        assert metrics[0].name == "test.metric"
        assert metrics[0].value == 100.0
    
    @pytest.mark.asyncio
    async def test_store_multiple_metrics(self, storage):
        """Test storing multiple metrics."""
        timestamp = datetime.now()
        metrics = [
            PerformanceMetric(
                name=f"test.metric.{i}",
                value=float(i),
                metric_type=MetricType.GAUGE,
                timestamp=timestamp,
                service_name="test"
            )
            for i in range(5)
        ]
        
        await storage.store_metrics(metrics)
        
        # Retrieve and verify
        retrieved = await storage.get_metrics(service_name="test")
        assert len(retrieved) == 5
    
    @pytest.mark.asyncio
    async def test_get_metrics_with_filters(self, storage):
        """Test retrieving metrics with various filters."""
        timestamp = datetime.now()
        
        # Store test metrics
        metrics = [
            PerformanceMetric(
                name="cpu.percent",
                value=50.0,
                metric_type=MetricType.GAUGE,
                timestamp=timestamp,
                service_name="service1"
            ),
            PerformanceMetric(
                name="memory.usage",
                value=1024.0,
                metric_type=MetricType.GAUGE,
                timestamp=timestamp,
                service_name="service1"
            ),
            PerformanceMetric(
                name="cpu.percent",
                value=75.0,
                metric_type=MetricType.GAUGE,
                timestamp=timestamp,
                service_name="service2"
            )
        ]
        
        await storage.store_metrics(metrics)
        
        # Test filtering by metric name
        cpu_metrics = await storage.get_metrics(metric_name="cpu.percent")
        assert len(cpu_metrics) == 2
        
        # Test filtering by service name
        service1_metrics = await storage.get_metrics(service_name="service1")
        assert len(service1_metrics) == 2
        
        # Test filtering by both
        specific_metrics = await storage.get_metrics(
            metric_name="cpu.percent",
            service_name="service1"
        )
        assert len(specific_metrics) == 1
        assert specific_metrics[0].value == 50.0
    
    @pytest.mark.asyncio
    async def test_baseline_storage(self, storage):
        """Test storing and retrieving baselines."""
        await storage.store_baseline("cpu.percent", "test_service", 50.0, 100)
        
        baseline = await storage.get_baseline("cpu.percent", "test_service")
        assert baseline is not None
        assert baseline[0] == 50.0  # baseline_value
        assert baseline[1] == 100   # sample_count
        
        # Test non-existent baseline
        missing = await storage.get_baseline("missing.metric", "test_service")
        assert missing is None
    
    @pytest.mark.asyncio
    async def test_cleanup_old_metrics(self, storage):
        """Test cleaning up old metrics."""
        now = datetime.now()
        old_time = now - timedelta(days=35)
        
        # Store old and new metrics
        old_metric = PerformanceMetric(
            name="old.metric",
            value=100.0,
            metric_type=MetricType.GAUGE,
            timestamp=old_time,
            service_name="test"
        )
        
        new_metric = PerformanceMetric(
            name="new.metric",
            value=200.0,
            metric_type=MetricType.GAUGE,
            timestamp=now,
            service_name="test"
        )
        
        await storage.store_metrics([old_metric, new_metric])
        
        # Cleanup with 30-day retention
        deleted_count = await storage.cleanup_old_metrics(retention_days=30)
        assert deleted_count == 1
        
        # Verify only new metric remains
        remaining = await storage.get_metrics()
        assert len(remaining) == 1
        assert remaining[0].name == "new.metric"


class TestMetricsCollector:
    """Test MetricsCollector functionality."""
    
    @pytest.fixture
    def collector(self):
        """Create MetricsCollector instance."""
        return MetricsCollector()
    
    @pytest.mark.asyncio
    async def test_collect_system_metrics(self, collector):
        """Test collecting system metrics."""
        with patch('psutil.cpu_percent', return_value=50.0), \
             patch('psutil.virtual_memory') as mock_memory, \
             patch('psutil.disk_usage') as mock_disk, \
             patch('psutil.net_io_counters') as mock_network, \
             patch('psutil.getloadavg', return_value=(1.0, 1.5, 2.0)), \
             patch('psutil.pids', return_value=list(range(100))), \
             patch('psutil.process_iter', return_value=[]):
            
            # Mock memory info
            mock_memory.return_value.used = 1024*1024*1024
            mock_memory.return_value.percent = 75.0
            
            # Mock disk info
            mock_disk.return_value.used = 2*1024*1024*1024
            mock_disk.return_value.percent = 80.0
            
            # Mock network info
            mock_network.return_value.bytes_sent = 1000000
            mock_network.return_value.bytes_recv = 2000000
            
            metrics = await collector.collect_system_metrics()
            
            assert metrics.cpu_percent == 50.0
            assert metrics.memory_usage == 1024*1024*1024
            assert metrics.memory_percent == 75.0
            assert metrics.load_average == (1.0, 1.5, 2.0)
    
    @pytest.mark.asyncio
    async def test_collect_service_metrics(self, collector):
        """Test collecting service metrics."""
        with patch('psutil.process_iter') as mock_iter, \
             patch('psutil.Process') as mock_process:
            
            # Mock process
            mock_proc = Mock()
            mock_proc.as_dict.return_value = {
                'cpu_percent': 25.0,
                'memory_info': Mock(rss=512*1024*1024),
                'memory_percent': 50.0,
                'io_counters': Mock(read_bytes=1000, write_bytes=2000),
                'num_threads': 5,
                'num_fds': 20,
                'connections': [1, 2, 3]
            }
            
            mock_iter.return_value = [Mock(info={'pid': 123, 'name': 'test_service'})]
            mock_process.return_value = mock_proc
            
            metrics = await collector.collect_service_metrics("test_service")
            
            assert metrics is not None
            assert metrics.service_name == "test_service"
            assert metrics.cpu_percent == 25.0
            assert metrics.memory_usage == 512*1024*1024
    
    @pytest.mark.asyncio
    async def test_custom_collectors(self, collector):
        """Test custom metric collectors."""
        async def custom_collector():
            return PerformanceMetric(
                name="custom.metric",
                value=123.0,
                metric_type=MetricType.GAUGE,
                timestamp=datetime.now(),
                service_name="custom"
            )
        
        collector.register_collector("test_collector", custom_collector)
        
        metrics = await collector.collect_custom_metrics()
        
        assert len(metrics) == 1
        assert metrics[0].name == "custom.metric"
        assert metrics[0].value == 123.0


class TestRegressionDetector:
    """Test RegressionDetector functionality."""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = Path(f.name)
        yield db_path
        if db_path.exists():
            db_path.unlink()
    
    @pytest.fixture
    def storage(self, temp_db):
        """Create MetricsStorage instance."""
        return MetricsStorage(temp_db)
    
    @pytest.fixture
    def detector(self, storage):
        """Create RegressionDetector instance."""
        return RegressionDetector(storage)
    
    @pytest.mark.asyncio
    async def test_detect_regressions(self, detector, storage):
        """Test regression detection."""
        # Store baseline
        await storage.store_baseline("cpu.percent", "test_service", 50.0, 100)
        
        # Store recent metrics showing regression
        now = datetime.now()
        metrics = [
            PerformanceMetric(
                name="cpu.percent",
                value=75.0,  # 50% increase from baseline
                metric_type=MetricType.GAUGE,
                timestamp=now - timedelta(minutes=i),
                service_name="test_service"
            )
            for i in range(15)  # 15 samples
        ]
        
        await storage.store_metrics(metrics)
        
        regressions = await detector.detect_regressions(lookback_hours=1)
        
        assert len(regressions) == 1
        regression = regressions[0]
        assert regression.metric_name == "cpu.percent"
        assert regression.service_name == "test_service"
        assert regression.is_regression
        assert regression.change_percent == 50.0


class TestPerformanceDashboard:
    """Test PerformanceDashboard functionality."""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = Path(f.name)
        yield db_path
        if db_path.exists():
            db_path.unlink()
    
    @pytest.fixture
    def storage(self, temp_db):
        """Create MetricsStorage instance."""
        return MetricsStorage(temp_db)
    
    @pytest.fixture
    def dashboard(self, storage):
        """Create PerformanceDashboard instance."""
        return PerformanceDashboard(storage)
    
    @pytest.mark.asyncio
    async def test_dashboard_start_stop(self, dashboard):
        """Test starting and stopping dashboard."""
        assert not dashboard.running
        
        await dashboard.start()
        assert dashboard.running
        
        await dashboard.stop()
        assert not dashboard.running
    
    @pytest.mark.asyncio
    async def test_get_dashboard_data(self, dashboard, storage):
        """Test getting dashboard data."""
        # Store some test metrics
        now = datetime.now()
        metrics = [
            PerformanceMetric(
                name="system.cpu.percent",
                value=50.0,
                metric_type=MetricType.GAUGE,
                timestamp=now,
                service_name="system"
            ),
            PerformanceMetric(
                name="service.api.cpu.percent",
                value=25.0,
                metric_type=MetricType.GAUGE,
                timestamp=now,
                service_name="api"
            )
        ]
        
        await storage.store_metrics(metrics)
        
        # Update dashboard data
        await dashboard._update_dashboard_data()
        
        data = await dashboard.get_dashboard_data()
        
        assert 'last_updated' in data
        assert 'system_overview' in data
        assert 'services' in data


class TestPerformanceBenchmark:
    """Test PerformanceBenchmark functionality."""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = Path(f.name)
        yield db_path
        if db_path.exists():
            db_path.unlink()
    
    @pytest.fixture
    def storage(self, temp_db):
        """Create MetricsStorage instance."""
        return MetricsStorage(temp_db)
    
    @pytest.fixture
    def benchmark(self, storage):
        """Create PerformanceBenchmark instance."""
        return PerformanceBenchmark(storage)
    
    @pytest.mark.asyncio
    async def test_create_baseline(self, benchmark, storage):
        """Test creating performance baseline."""
        # Store some test metrics
        now = datetime.now()
        metrics = [
            PerformanceMetric(
                name="cpu.percent",
                value=50.0 + i,  # Varying values
                metric_type=MetricType.GAUGE,
                timestamp=now - timedelta(minutes=i),
                service_name="test"
            )
            for i in range(10)
        ]
        
        await storage.store_metrics(metrics)
        
        baseline = await benchmark.create_baseline("test_baseline", duration_minutes=60)
        
        assert baseline['name'] == "test_baseline"
        assert 'metrics' in baseline
        assert 'total_samples' in baseline
        assert baseline['total_samples'] == 10
    
    @pytest.mark.asyncio
    async def test_compare_to_baseline(self, benchmark, storage):
        """Test comparing to baseline."""
        # Create baseline first
        now = datetime.now()
        baseline_metrics = [
            PerformanceMetric(
                name="cpu.percent",
                value=50.0,
                metric_type=MetricType.GAUGE,
                timestamp=now - timedelta(hours=2, minutes=i),
                service_name="test"
            )
            for i in range(10)
        ]
        
        await storage.store_metrics(baseline_metrics)
        await benchmark.create_baseline("test_baseline", duration_minutes=60)
        
        # Store current metrics (higher values)
        current_metrics = [
            PerformanceMetric(
                name="cpu.percent",
                value=75.0,  # 50% higher
                metric_type=MetricType.GAUGE,
                timestamp=now - timedelta(minutes=i),
                service_name="test"
            )
            for i in range(10)
        ]
        
        await storage.store_metrics(current_metrics)
        
        comparison = await benchmark.compare_to_baseline("test_baseline", duration_minutes=60)
        
        assert comparison['baseline_name'] == "test_baseline"
        assert 'differences' in comparison
        assert 'summary' in comparison


class TestPerformanceMonitoringSystem:
    """Test PerformanceMonitoringSystem integration."""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = Path(f.name)
        yield db_path
        if db_path.exists():
            db_path.unlink()
    
    @pytest.fixture
    def monitoring_system(self, temp_db):
        """Create PerformanceMonitoringSystem instance."""
        return PerformanceMonitoringSystem(db_path=temp_db, collection_interval=1)
    
    @pytest.mark.asyncio
    async def test_system_start_stop(self, monitoring_system):
        """Test starting and stopping monitoring system."""
        assert not monitoring_system.running
        
        await monitoring_system.start()
        assert monitoring_system.running
        
        await monitoring_system.stop()
        assert not monitoring_system.running
    
    @pytest.mark.asyncio
    async def test_custom_collector_registration(self, monitoring_system):
        """Test registering custom collectors."""
        async def test_collector():
            return PerformanceMetric(
                name="test.metric",
                value=100.0,
                metric_type=MetricType.GAUGE,
                timestamp=datetime.now(),
                service_name="test"
            )
        
        monitoring_system.register_custom_collector("test", test_collector)
        
        # Verify collector is registered
        assert "test" in monitoring_system.collector.custom_collectors
    
    @pytest.mark.asyncio
    async def test_global_instance(self):
        """Test global monitoring system instance."""
        system1 = get_performance_monitoring_system()
        system2 = get_performance_monitoring_system()
        
        # Should return same instance
        assert system1 is system2
    
    @pytest.mark.asyncio
    async def test_initialize_shutdown(self):
        """Test initialize and shutdown functions."""
        # Initialize
        system = await initialize_performance_monitoring()
        assert system.running
        
        # Shutdown
        await shutdown_performance_monitoring()
        
        # Should create new instance on next call
        new_system = get_performance_monitoring_system()
        assert not new_system.running


if __name__ == "__main__":
    pytest.main([__file__])