"""
Tests for Performance Auditor functionality.

This module tests the performance audit engine including service discovery,
startup time tracking, resource monitoring, and bottleneck analysis.
"""

import pytest
import asyncio
import time
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from src.ai_karen_engine.audit.performance_auditor import (
    PerformanceAuditor,
    ServiceDiscovery,
    StartupTimeTracker,
    ResourceUsageTracker,
    BottleneckAnalyzer,
    StartupTimeContext,
    ServiceInfo,
    ServiceType,
    BottleneckType,
    StartupMetrics,
    RuntimeMetrics,
    Bottleneck,
    get_performance_auditor
)


class TestServiceDiscovery:
    """Test service discovery functionality."""
    
    @pytest.fixture
    def service_discovery(self):
        return ServiceDiscovery()
    
    @pytest.mark.asyncio
    async def test_discover_services(self, service_discovery):
        """Test basic service discovery."""
        with patch('psutil.Process') as mock_process:
            # Mock current process
            mock_current = Mock()
            mock_current.children.return_value = []
            mock_current.as_dict.return_value = {
                'pid': 1234,
                'name': 'python',
                'memory_info': Mock(rss=100*1024*1024),
                'cpu_percent': 15.5,
                'io_counters': Mock(read_bytes=1000, write_bytes=2000),
                'num_threads': 5,
                'status': 'running',
                'cmdline': ['python', 'main.py']
            }
            mock_process.return_value = mock_current
            
            services = await service_discovery.discover_services()
            
            assert len(services) > 0
            # Should discover at least the Python modules
            service_names = [s.name for s in services]
            assert any('ai_karen_engine' in name for name in service_names)
    
    def test_classify_service_type(self, service_discovery):
        """Test service type classification."""
        # Essential services
        assert service_discovery._classify_service_type('auth_service', {}) == ServiceType.ESSENTIAL
        assert service_discovery._classify_service_type('main_server', {}) == ServiceType.ESSENTIAL
        
        # Background services
        assert service_discovery._classify_service_type('monitor_daemon', {}) == ServiceType.BACKGROUND
        assert service_discovery._classify_service_type('cleanup_scheduler', {}) == ServiceType.BACKGROUND
        
        # Optional services
        assert service_discovery._classify_service_type('plugin_manager', {}) == ServiceType.OPTIONAL
        assert service_discovery._classify_service_type('copilot_extension', {}) == ServiceType.OPTIONAL
        
        # Unknown
        assert service_discovery._classify_service_type('random_service', {}) == ServiceType.UNKNOWN
    
    def test_determine_service_name(self, service_discovery):
        """Test service name determination."""
        # From command line
        proc_info = {
            'name': 'python',
            'cmdline': ['python', '/path/to/main.py', '--arg']
        }
        assert service_discovery._determine_service_name(proc_info) == 'main'
        
        # From process name
        proc_info = {
            'name': 'nginx',
            'cmdline': []
        }
        assert service_discovery._determine_service_name(proc_info) == 'nginx'


class TestStartupTimeTracker:
    """Test startup time tracking functionality."""
    
    @pytest.fixture
    def startup_tracker(self):
        return StartupTimeTracker()
    
    def test_startup_measurement(self, startup_tracker):
        """Test basic startup time measurement."""
        service_name = "test_service"
        
        # Start measurement
        startup_tracker.start_measurement(service_name)
        assert service_name in startup_tracker.active_measurements
        
        # Simulate some work
        time.sleep(0.1)
        
        # End measurement
        metrics = startup_tracker.end_measurement(service_name)
        
        assert metrics is not None
        assert metrics.service_name == service_name
        assert metrics.duration >= 0.1
        assert metrics.memory_delta >= 0  # Memory might increase or decrease
        assert service_name in startup_tracker.startup_times
        assert service_name not in startup_tracker.active_measurements
    
    def test_dependency_tracking(self, startup_tracker):
        """Test dependency loading tracking."""
        service_name = "test_service"
        
        startup_tracker.start_measurement(service_name)
        startup_tracker.add_dependency_loaded(service_name, "dependency1")
        startup_tracker.add_dependency_loaded(service_name, "dependency2")
        
        metrics = startup_tracker.end_measurement(service_name)
        
        assert "dependency1" in metrics.dependencies_loaded
        assert "dependency2" in metrics.dependencies_loaded
        assert len(metrics.dependencies_loaded) == 2
    
    def test_startup_summary(self, startup_tracker):
        """Test startup summary generation."""
        # Add some mock measurements
        for i in range(3):
            service_name = f"service_{i}"
            startup_tracker.start_measurement(service_name)
            time.sleep(0.01)  # Small delay
            startup_tracker.end_measurement(service_name)
        
        summary = startup_tracker.get_startup_summary()
        
        assert summary['services_count'] == 3
        assert summary['total_startup_time'] > 0
        assert len(summary['slowest_services']) <= 5
        assert len(summary['startup_order']) == 3


class TestStartupTimeContext:
    """Test startup time context manager."""
    
    def test_context_manager_success(self):
        """Test context manager for successful startup."""
        auditor = PerformanceAuditor()
        service_name = "test_context_service"
        
        with StartupTimeContext(service_name, auditor) as ctx:
            ctx.add_dependency("test_dependency")
            time.sleep(0.01)
        
        assert service_name in auditor.startup_tracker.startup_times
        metrics = auditor.startup_tracker.startup_times[service_name]
        assert "test_dependency" in metrics.dependencies_loaded
        assert len(metrics.errors) == 0
    
    def test_context_manager_with_error(self):
        """Test context manager with error handling."""
        auditor = PerformanceAuditor()
        service_name = "test_error_service"
        
        try:
            with StartupTimeContext(service_name, auditor):
                raise ValueError("Test error")
        except ValueError:
            pass
        
        assert service_name in auditor.startup_tracker.startup_times
        metrics = auditor.startup_tracker.startup_times[service_name]
        assert len(metrics.errors) == 1
        assert "ValueError: Test error" in metrics.errors


class TestResourceUsageTracker:
    """Test resource usage tracking functionality."""
    
    @pytest.fixture
    def resource_tracker(self):
        return ResourceUsageTracker(history_size=10)
    
    @pytest.fixture
    def mock_service(self):
        return ServiceInfo(
            name="test_service",
            pid=1234,
            service_type=ServiceType.ESSENTIAL,
            startup_time=1.0,
            memory_usage=100*1024*1024,
            cpu_percent=10.0,
            io_read_bytes=1000,
            io_write_bytes=2000,
            thread_count=5,
            status="running",
            dependencies=[],
            last_accessed=None,
            module_path=None
        )
    
    @patch('psutil.Process')
    def test_collect_service_metrics(self, mock_process_class, resource_tracker, mock_service):
        """Test service metrics collection."""
        # Mock process
        mock_process = Mock()
        mock_process.as_dict.return_value = {
            'memory_info': Mock(rss=150*1024*1024),
            'memory_percent': 15.0,
            'cpu_percent': 20.0,
            'io_counters': Mock(read_bytes=2000, write_bytes=3000),
            'num_threads': 6,
            'num_fds': 10,
            'connections': []
        }
        mock_process_class.return_value = mock_process
        
        metrics = resource_tracker._collect_service_metrics(mock_service)
        
        assert metrics is not None
        assert metrics.service_name == "test_service"
        assert metrics.memory_usage == 150*1024*1024
        assert metrics.cpu_percent == 20.0
        assert metrics.thread_count == 6
    
    def test_service_trends(self, resource_tracker):
        """Test service trend analysis."""
        service_name = "test_service"
        
        # Add some mock metrics
        for i in range(5):
            metrics = RuntimeMetrics(
                service_name=service_name,
                timestamp=datetime.now() - timedelta(minutes=i),
                cpu_percent=10.0 + i,
                memory_usage=100*1024*1024 + i*1024*1024,
                memory_percent=10.0 + i,
                io_read_bytes=1000 + i*100,
                io_write_bytes=2000 + i*200,
                thread_count=5 + i,
                open_files=10,
                network_connections=2,
                response_time=None
            )
            resource_tracker.metrics_history[service_name].append(metrics)
        
        trends = resource_tracker.get_service_trends(service_name, duration_minutes=60)
        
        assert 'cpu_percent' in trends
        assert 'memory_usage' in trends
        assert len(trends['cpu_percent']) == 5
        assert trends['cpu_percent'] == [10.0, 11.0, 12.0, 13.0, 14.0]


class TestBottleneckAnalyzer:
    """Test bottleneck analysis functionality."""
    
    @pytest.fixture
    def bottleneck_analyzer(self):
        return BottleneckAnalyzer()
    
    def test_analyze_startup_bottlenecks(self, bottleneck_analyzer):
        """Test startup bottleneck analysis."""
        # Create slow startup metrics
        slow_metrics = StartupMetrics(
            service_name="slow_service",
            start_time=time.time(),
            end_time=time.time() + 15.0,  # 15 seconds - slow
            duration=15.0,
            memory_before=100*1024*1024,
            memory_after=1200*1024*1024,  # 1.2GB - high memory usage
            memory_delta=1100*1024*1024,
            cpu_usage=50.0,
            dependencies_loaded=["dep1", "dep2"],
            errors=[]
        )
        
        bottlenecks = bottleneck_analyzer.analyze_startup_bottlenecks([slow_metrics])
        
        assert len(bottlenecks) >= 1
        
        # Should detect slow startup
        startup_bottlenecks = [b for b in bottlenecks if b.bottleneck_type == BottleneckType.STARTUP_SLOW]
        assert len(startup_bottlenecks) >= 1
        
        slow_bottleneck = startup_bottlenecks[0]
        assert slow_bottleneck.service_name == "slow_service"
        assert slow_bottleneck.impact_score > 0
        assert len(slow_bottleneck.recommendations) > 0
    
    def test_analyze_runtime_bottlenecks(self, bottleneck_analyzer):
        """Test runtime bottleneck analysis."""
        # Create high CPU usage metrics
        high_cpu_metrics = [
            RuntimeMetrics(
                service_name="cpu_intensive_service",
                timestamp=datetime.now(),
                cpu_percent=90.0,  # High CPU usage
                memory_usage=100*1024*1024,
                memory_percent=10.0,
                io_read_bytes=1000,
                io_write_bytes=2000,
                thread_count=5,
                open_files=10,
                network_connections=2,
                response_time=None
            )
            for _ in range(5)
        ]
        
        bottlenecks = bottleneck_analyzer.analyze_runtime_bottlenecks(high_cpu_metrics)
        
        assert len(bottlenecks) >= 1
        
        # Should detect CPU intensive bottleneck
        cpu_bottlenecks = [b for b in bottlenecks if b.bottleneck_type == BottleneckType.CPU_INTENSIVE]
        assert len(cpu_bottlenecks) >= 1
        
        cpu_bottleneck = cpu_bottlenecks[0]
        assert cpu_bottleneck.service_name == "cpu_intensive_service"
        assert cpu_bottleneck.impact_score > 0
        assert "CPU" in cpu_bottleneck.description
    
    def test_severity_calculation(self, bottleneck_analyzer):
        """Test severity level calculation."""
        # Test different severity levels
        assert bottleneck_analyzer._calculate_severity(130, 80, 120) == "CRITICAL"  # >= critical_threshold
        assert bottleneck_analyzer._calculate_severity(125, 80, 200) == "HIGH"      # >= threshold * 1.5 (120)
        assert bottleneck_analyzer._calculate_severity(100, 80, 200) == "MEDIUM"    # >= threshold * 1.2 (96)
        assert bottleneck_analyzer._calculate_severity(85, 80, 200) == "LOW"        # < threshold * 1.2


class TestPerformanceAuditor:
    """Test main performance auditor functionality."""
    
    @pytest.fixture
    def temp_audit_path(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir) / "test_audit.log"
    
    @pytest.fixture
    def performance_auditor(self, temp_audit_path):
        return PerformanceAuditor(audit_log_path=temp_audit_path)
    
    @pytest.mark.asyncio
    async def test_audit_startup_performance(self, performance_auditor):
        """Test startup performance audit."""
        # Add some mock startup data
        performance_auditor.startup_tracker.start_measurement("test_service")
        time.sleep(0.01)
        performance_auditor.startup_tracker.end_measurement("test_service")
        
        with patch.object(performance_auditor.service_discovery, 'discover_services') as mock_discover:
            mock_discover.return_value = [
                ServiceInfo(
                    name="test_service",
                    pid=1234,
                    service_type=ServiceType.ESSENTIAL,
                    startup_time=1.0,
                    memory_usage=100*1024*1024,
                    cpu_percent=10.0,
                    io_read_bytes=1000,
                    io_write_bytes=2000,
                    thread_count=5,
                    status="running",
                    dependencies=[],
                    last_accessed=None,
                    module_path=None
                )
            ]
            
            report = await performance_auditor.audit_startup_performance()
            
            assert report is not None
            assert report.services_analyzed == 1
            assert len(report.startup_metrics) == 1
            assert report.total_startup_time > 0
            assert report.baseline_memory > 0
            assert len(report.recommendations) >= 0
    
    @pytest.mark.asyncio
    async def test_audit_runtime_performance(self, performance_auditor):
        """Test runtime performance audit."""
        with patch.object(performance_auditor.service_discovery, 'discover_services') as mock_discover:
            mock_discover.return_value = [
                ServiceInfo(
                    name="test_service",
                    pid=1234,
                    service_type=ServiceType.ESSENTIAL,
                    startup_time=1.0,
                    memory_usage=100*1024*1024,
                    cpu_percent=10.0,
                    io_read_bytes=1000,
                    io_write_bytes=2000,
                    thread_count=5,
                    status="running",
                    dependencies=[],
                    last_accessed=None,
                    module_path=None
                )
            ]
            
            # Mock the monitoring to avoid long wait
            with patch.object(performance_auditor.resource_tracker, 'start_monitoring'), \
                 patch.object(performance_auditor.resource_tracker, 'stop_monitoring'), \
                 patch('asyncio.sleep'):
                
                # Add some mock metrics
                performance_auditor.resource_tracker.metrics_history["test_service"].append(
                    RuntimeMetrics(
                        service_name="test_service",
                        timestamp=datetime.now(),
                        cpu_percent=15.0,
                        memory_usage=120*1024*1024,
                        memory_percent=12.0,
                        io_read_bytes=1500,
                        io_write_bytes=2500,
                        thread_count=6,
                        open_files=12,
                        network_connections=3,
                        response_time=None
                    )
                )
                
                report = await performance_auditor.audit_runtime_performance(duration_minutes=1)
                
                assert report is not None
                assert report.services_monitored == 1
                assert report.analysis_duration >= 0
                assert len(report.recommendations) >= 0
    
    @pytest.mark.asyncio
    async def test_identify_bottlenecks(self, performance_auditor):
        """Test bottleneck identification."""
        # Add mock startup data with bottleneck
        performance_auditor.startup_tracker.startup_times["slow_service"] = StartupMetrics(
            service_name="slow_service",
            start_time=time.time(),
            end_time=time.time() + 15.0,
            duration=15.0,  # Slow startup
            memory_before=100*1024*1024,
            memory_after=200*1024*1024,
            memory_delta=100*1024*1024,
            cpu_usage=50.0,
            dependencies_loaded=[],
            errors=[]
        )
        
        bottlenecks = await performance_auditor.identify_bottlenecks()
        
        assert len(bottlenecks) >= 1
        assert any(b.bottleneck_type == BottleneckType.STARTUP_SLOW for b in bottlenecks)
    
    @pytest.mark.asyncio
    async def test_generate_optimization_recommendations(self, performance_auditor):
        """Test optimization recommendation generation."""
        # Add mock bottleneck
        performance_auditor.startup_tracker.startup_times["slow_service"] = StartupMetrics(
            service_name="slow_service",
            start_time=time.time(),
            end_time=time.time() + 15.0,
            duration=15.0,
            memory_before=100*1024*1024,
            memory_after=200*1024*1024,
            memory_delta=100*1024*1024,
            cpu_usage=50.0,
            dependencies_loaded=[],
            errors=[]
        )
        
        recommendations = await performance_auditor.generate_optimization_recommendations()
        
        assert len(recommendations) > 0
        assert any("lazy loading" in rec.lower() for rec in recommendations)
    
    def test_save_report(self, performance_auditor, temp_audit_path):
        """Test report saving functionality."""
        # Create a simple report
        from src.ai_karen_engine.audit.performance_auditor import StartupReport
        
        report = StartupReport(
            total_startup_time=5.0,
            services_analyzed=2,
            startup_metrics=[],
            bottlenecks=[],
            recommendations=["Test recommendation"],
            baseline_memory=100*1024*1024,
            peak_memory=150*1024*1024,
            generated_at=datetime.now()
        )
        
        # Save report
        asyncio.run(performance_auditor._save_report(report, "startup"))
        
        # Verify file was created and contains data
        assert temp_audit_path.exists()
        
        with open(temp_audit_path, 'r') as f:
            content = f.read().strip()
            assert content
            
            # Parse JSON
            report_data = json.loads(content)
            assert report_data['type'] == 'startup'
            assert 'report' in report_data
            assert 'timestamp' in report_data


class TestGlobalAuditor:
    """Test global auditor instance functionality."""
    
    def test_get_performance_auditor(self):
        """Test global auditor instance."""
        auditor1 = get_performance_auditor()
        auditor2 = get_performance_auditor()
        
        # Should return the same instance
        assert auditor1 is auditor2
        assert isinstance(auditor1, PerformanceAuditor)


@pytest.mark.integration
class TestPerformanceAuditorIntegration:
    """Integration tests for performance auditor."""
    
    @pytest.mark.asyncio
    async def test_full_audit_cycle(self):
        """Test complete audit cycle."""
        with tempfile.TemporaryDirectory() as temp_dir:
            audit_path = Path(temp_dir) / "integration_audit.log"
            auditor = PerformanceAuditor(audit_log_path=audit_path)
            
            # Simulate service startup
            with StartupTimeContext("integration_service", auditor) as ctx:
                ctx.add_dependency("test_dependency")
                time.sleep(0.05)  # Simulate startup work
            
            # Run startup audit
            startup_report = await auditor.audit_startup_performance()
            
            assert startup_report.services_analyzed > 0
            assert len(startup_report.startup_metrics) > 0
            assert startup_report.total_startup_time > 0
            
            # Verify audit log was created
            assert audit_path.exists()
            
            # Generate recommendations
            recommendations = await auditor.generate_optimization_recommendations()
            assert len(recommendations) >= 0
    
    @pytest.mark.asyncio
    async def test_real_service_discovery(self):
        """Test service discovery with real system processes."""
        auditor = PerformanceAuditor()
        
        services = await auditor.service_discovery.discover_services()
        
        # Should discover at least some services
        assert len(services) > 0
        
        # Should have at least one Python-related service
        python_services = [s for s in services if 'python' in s.name.lower() or 'ai_karen' in s.name]
        assert len(python_services) > 0
        
        # Verify service info structure
        for service in services[:5]:  # Check first 5 services
            assert service.name
            assert isinstance(service.service_type, ServiceType)
            assert service.memory_usage >= 0
            assert service.cpu_percent >= 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])