"""
Tests for Analytics Service

Tests the comprehensive analytics, monitoring, and health checking capabilities
of the AI Karen Analytics Service.
"""

import pytest
import asyncio
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from src.ai_karen_engine.services.analytics_service import (
    AnalyticsService,
    MetricsCollector,
    SystemMonitor,
    HealthChecker,
    AlertManager,
    UserInteractionTracker,
    PerformanceTracker,
    Metric,
    MetricType,
    Alert,
    AlertLevel,
    HealthCheck,
    HealthStatus,
    UserInteractionEvent,
    PerformanceMetrics,
    SystemResourceMetrics,
    PerformanceTimer,
    track_performance,
    get_analytics_service,
    initialize_analytics_service
)


class TestMetricsCollector:
    """Test MetricsCollector functionality"""
    
    def test_record_counter_metric(self):
        collector = MetricsCollector()
        metric = Metric("test.counter", 5, MetricType.COUNTER)
        
        collector.record_metric(metric)
        
        assert collector.get_counter("test.counter") == 5
        assert len(collector.metrics) == 1
    
    def test_record_gauge_metric(self):
        collector = MetricsCollector()
        metric = Metric("test.gauge", 42.5, MetricType.GAUGE)
        
        collector.record_metric(metric)
        
        assert collector.get_gauge("test.gauge") == 42.5
    
    def test_record_histogram_metric(self):
        collector = MetricsCollector()
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        
        for value in values:
            metric = Metric("test.histogram", value, MetricType.HISTOGRAM)
            collector.record_metric(metric)
        
        stats = collector.get_histogram_stats("test.histogram")
        assert stats["count"] == 5
        assert stats["min"] == 1.0
        assert stats["max"] == 5.0
        assert stats["mean"] == 3.0
    
    def test_get_recent_metrics(self):
        collector = MetricsCollector()
        
        # Add old metric
        old_metric = Metric("old.metric", 1, MetricType.COUNTER)
        old_metric.timestamp = datetime.now() - timedelta(minutes=10)
        collector.record_metric(old_metric)
        
        # Add recent metric
        recent_metric = Metric("recent.metric", 2, MetricType.COUNTER)
        collector.record_metric(recent_metric)
        
        recent_metrics = collector.get_recent_metrics(minutes=5)
        assert len(recent_metrics) == 1
        assert recent_metrics[0].name == "recent.metric"


class TestSystemMonitor:
    """Test SystemMonitor functionality"""
    
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    @patch('psutil.net_io_counters')
    def test_get_system_metrics(self, mock_net, mock_disk, mock_memory, mock_cpu):
        # Mock system data
        mock_cpu.return_value = 25.5
        mock_memory.return_value = Mock(
            percent=60.0,
            used=1024*1024*1024,  # 1GB
            available=2048*1024*1024  # 2GB
        )
        mock_disk.return_value = Mock(
            used=50*1024*1024*1024,  # 50GB
            total=100*1024*1024*1024,  # 100GB
            free=50*1024*1024*1024   # 50GB
        )
        mock_net.return_value = Mock(
            bytes_sent=1000000,
            bytes_recv=2000000
        )
        
        monitor = SystemMonitor()
        metrics = monitor.get_system_metrics()
        
        assert metrics.cpu_percent == 25.5
        assert metrics.memory_percent == 60.0
        assert metrics.memory_used_mb == 1024.0
        assert metrics.memory_available_mb == 2048.0
        assert metrics.disk_usage_percent == 50.0
        assert metrics.disk_free_gb == 50.0
        assert metrics.network_bytes_sent == 1000000
        assert metrics.network_bytes_recv == 2000000
    
    def test_start_stop_monitoring(self):
        monitor = SystemMonitor(collection_interval=1)
        
        assert not monitor.is_running
        
        monitor.start_monitoring()
        assert monitor.is_running
        
        time.sleep(0.1)  # Let it start
        
        monitor.stop_monitoring()
        assert not monitor.is_running


class TestHealthChecker:
    """Test HealthChecker functionality"""
    
    @pytest.mark.asyncio
    async def test_register_and_run_health_check(self):
        checker = HealthChecker()
        
        async def test_check():
            return HealthCheck(
                name="test",
                status=HealthStatus.HEALTHY,
                message="All good"
            )
        
        checker.register_health_check("test", test_check)
        result = await checker.run_health_check("test")
        
        assert result.name == "test"
        assert result.status == HealthStatus.HEALTHY
        assert result.message == "All good"
        assert result.response_time is not None
    
    @pytest.mark.asyncio
    async def test_health_check_failure(self):
        checker = HealthChecker()
        
        async def failing_check():
            raise Exception("Something went wrong")
        
        checker.register_health_check("failing", failing_check)
        result = await checker.run_health_check("failing")
        
        assert result.name == "failing"
        assert result.status == HealthStatus.UNHEALTHY
        assert "Something went wrong" in result.message
    
    @pytest.mark.asyncio
    async def test_run_all_health_checks(self):
        checker = HealthChecker()
        
        async def check1():
            return HealthCheck("check1", HealthStatus.HEALTHY, "OK")
        
        async def check2():
            return HealthCheck("check2", HealthStatus.DEGRADED, "Slow")
        
        checker.register_health_check("check1", check1)
        checker.register_health_check("check2", check2)
        
        results = await checker.run_all_health_checks()
        
        assert len(results) == 2
        assert results["check1"].status == HealthStatus.HEALTHY
        assert results["check2"].status == HealthStatus.DEGRADED
    
    def test_get_overall_health(self):
        checker = HealthChecker()
        
        # No checks
        assert checker.get_overall_health() == HealthStatus.UNKNOWN
        
        # Add healthy check
        checker.health_checks["test1"] = HealthCheck("test1", HealthStatus.HEALTHY, "OK")
        assert checker.get_overall_health() == HealthStatus.HEALTHY
        
        # Add degraded check
        checker.health_checks["test2"] = HealthCheck("test2", HealthStatus.DEGRADED, "Slow")
        assert checker.get_overall_health() == HealthStatus.DEGRADED
        
        # Add unhealthy check
        checker.health_checks["test3"] = HealthCheck("test3", HealthStatus.UNHEALTHY, "Failed")
        assert checker.get_overall_health() == HealthStatus.UNHEALTHY


class TestAlertManager:
    """Test AlertManager functionality"""
    
    def test_create_alert(self):
        manager = AlertManager()
        handler_called = False
        
        def test_handler(alert):
            nonlocal handler_called
            handler_called = True
            assert alert.level == AlertLevel.WARNING
            assert alert.message == "Test alert"
        
        manager.add_alert_handler(test_handler)
        alert = manager.create_alert(AlertLevel.WARNING, "Test alert", "test")
        
        assert alert.level == AlertLevel.WARNING
        assert alert.message == "Test alert"
        assert alert.source == "test"
        assert handler_called
    
    def test_threshold_checking(self):
        manager = AlertManager()
        alerts_created = []
        
        def capture_alert(alert):
            alerts_created.append(alert)
        
        manager.add_alert_handler(capture_alert)
        manager.set_threshold("cpu.percent", 80.0, AlertLevel.WARNING, "greater_than")
        
        # Should not trigger alert
        metric = Metric("cpu.percent", 70.0, MetricType.GAUGE)
        manager.check_metric_thresholds(metric)
        assert len(alerts_created) == 0
        
        # Should trigger alert
        metric = Metric("cpu.percent", 85.0, MetricType.GAUGE)
        manager.check_metric_thresholds(metric)
        assert len(alerts_created) == 1
        assert alerts_created[0].level == AlertLevel.WARNING
    
    def test_get_recent_alerts(self):
        manager = AlertManager()
        
        # Create old alert
        old_alert = Alert("1", AlertLevel.INFO, "Old alert", "test")
        old_alert.timestamp = datetime.now() - timedelta(hours=2)
        manager.alerts.append(old_alert)
        
        # Create recent alert
        recent_alert = manager.create_alert(AlertLevel.WARNING, "Recent alert", "test")
        
        recent_alerts = manager.get_recent_alerts(minutes=60)
        assert len(recent_alerts) == 1
        assert recent_alerts[0].message == "Recent alert"


class TestUserInteractionTracker:
    """Test UserInteractionTracker functionality"""
    
    def test_track_event(self):
        tracker = UserInteractionTracker()
        
        event = UserInteractionEvent(
            user_id="user123",
            session_id="session456",
            event_type="page_view",
            event_data={"page": "/dashboard"}
        )
        
        tracker.track_event(event)
        
        assert len(tracker.events) == 1
        assert "session456" in tracker.user_sessions
        
        session = tracker.user_sessions["session456"]
        assert session["user_id"] == "user123"
        assert session["event_count"] == 1
    
    def test_get_user_activity(self):
        tracker = UserInteractionTracker()
        
        # Add old event
        old_event = UserInteractionEvent(
            user_id="user123",
            event_type="old_event"
        )
        old_event.timestamp = datetime.now() - timedelta(hours=25)
        tracker.track_event(old_event)
        
        # Add recent event
        recent_event = UserInteractionEvent(
            user_id="user123",
            event_type="recent_event"
        )
        tracker.track_event(recent_event)
        
        activity = tracker.get_user_activity("user123", hours=24)
        assert len(activity) == 1
        assert activity[0].event_type == "recent_event"
    
    def test_get_popular_events(self):
        tracker = UserInteractionTracker()
        
        # Add multiple events
        for i in range(3):
            tracker.track_event(UserInteractionEvent(
                user_id=f"user{i}",
                event_type="click"
            ))
        
        for i in range(2):
            tracker.track_event(UserInteractionEvent(
                user_id=f"user{i}",
                event_type="view"
            ))
        
        popular = tracker.get_popular_events(hours=24)
        assert popular["click"] == 3
        assert popular["view"] == 2


class TestPerformanceTracker:
    """Test PerformanceTracker functionality"""
    
    def test_record_performance(self):
        tracker = PerformanceTracker()
        
        metric = PerformanceMetrics(
            service_name="test_service",
            operation="test_op",
            duration_ms=150.5,
            success=True
        )
        
        tracker.record_performance(metric)
        assert len(tracker.metrics) == 1
    
    def test_get_service_stats(self):
        tracker = PerformanceTracker()
        
        # Add multiple metrics
        durations = [100.0, 200.0, 150.0, 300.0, 250.0]
        for duration in durations:
            metric = PerformanceMetrics(
                service_name="test_service",
                operation="test_op",
                duration_ms=duration,
                success=True
            )
            tracker.record_performance(metric)
        
        stats = tracker.get_service_stats("test_service")
        
        assert stats["total_requests"] == 5
        assert stats["success_rate"] == 1.0
        assert stats["avg_duration_ms"] == 200.0
        assert stats["min_duration_ms"] == 100.0
        assert stats["max_duration_ms"] == 300.0


class TestAnalyticsService:
    """Test main AnalyticsService functionality"""
    
    def test_initialization(self):
        service = AnalyticsService()
        
        assert service.metrics_collector is not None
        assert service.system_monitor is not None
        assert service.health_checker is not None
        assert service.alert_manager is not None
        assert service.user_tracker is not None
        assert service.performance_tracker is not None
    
    def test_record_metrics(self):
        service = AnalyticsService()
        
        service.increment_counter("test.counter", 5)
        service.set_gauge("test.gauge", 42.5)
        service.record_histogram("test.histogram", 100.0)
        service.record_timer("test.timer", 250.0)
        
        assert service.metrics_collector.get_counter("test.counter") == 5
        assert service.metrics_collector.get_gauge("test.gauge") == 42.5
    
    def test_performance_tracking(self):
        service = AnalyticsService()
        
        service.record_performance(
            service_name="test_service",
            operation="test_op",
            duration_ms=150.0,
            success=True
        )
        
        stats = service.get_service_performance("test_service")
        assert stats["total_requests"] == 1
        assert stats["success_rate"] == 1.0
        assert stats["avg_duration_ms"] == 150.0
    
    def test_user_tracking(self):
        service = AnalyticsService()
        
        service.track_user_event(
            user_id="user123",
            event_type="login",
            event_data={"method": "oauth"},
            session_id="session456"
        )
        
        activity = service.get_user_activity("user123")
        assert len(activity) == 1
        assert activity[0].event_type == "login"
        
        session_stats = service.get_session_stats("session456")
        assert session_stats["user_id"] == "user123"
        assert session_stats["event_count"] == 1
    
    @pytest.mark.asyncio
    async def test_health_checks(self):
        service = AnalyticsService()
        
        # Test individual health check
        result = await service.run_health_check("database")
        assert result.name == "database"
        assert isinstance(result.status, HealthStatus)
        
        # Test all health checks
        results = await service.run_all_health_checks()
        assert len(results) >= 3  # Default health checks
        
        # Test overall health
        overall = service.get_overall_health()
        assert isinstance(overall, HealthStatus)
    
    def test_alert_management(self):
        service = AnalyticsService()
        alerts_received = []
        
        def capture_alert(alert):
            alerts_received.append(alert)
        
        service.add_alert_handler(capture_alert)
        
        alert = service.create_alert(
            AlertLevel.WARNING,
            "Test alert",
            "test_source"
        )
        
        assert alert.level == AlertLevel.WARNING
        assert len(alerts_received) == 1
        
        recent_alerts = service.get_recent_alerts(minutes=5)
        assert len(recent_alerts) == 1
    
    def test_analytics_summary(self):
        service = AnalyticsService()
        
        # Add some data
        service.increment_counter("test.counter")
        service.track_user_event("user123", "test_event")
        service.create_alert(AlertLevel.INFO, "Test", "test")
        
        summary = service.get_analytics_summary()
        
        assert "system_health" in summary
        assert "system_metrics" in summary
        assert "recent_alerts" in summary
        assert "popular_events" in summary
        assert "total_metrics" in summary
        assert summary["total_metrics"] > 0
    
    def test_shutdown(self):
        service = AnalyticsService()
        service.shutdown()  # Should not raise exception


class TestPerformanceTimer:
    """Test PerformanceTimer context manager"""
    
    def test_successful_operation(self):
        service = AnalyticsService()
        
        with PerformanceTimer("test_service", "test_op", service):
            time.sleep(0.01)  # Simulate work
        
        stats = service.get_service_performance("test_service")
        assert stats["total_requests"] == 1
        assert stats["success_rate"] == 1.0
        assert stats["avg_duration_ms"] > 0
    
    def test_failed_operation(self):
        service = AnalyticsService()
        
        try:
            with PerformanceTimer("test_service", "test_op", service):
                raise ValueError("Test error")
        except ValueError:
            pass
        
        stats = service.get_service_performance("test_service")
        assert stats["total_requests"] == 1
        assert stats["success_rate"] == 0.0
    
    def test_manual_failure_marking(self):
        service = AnalyticsService()
        
        with PerformanceTimer("test_service", "test_op", service) as timer:
            timer.mark_failure("Manual failure")
        
        stats = service.get_service_performance("test_service")
        assert stats["success_rate"] == 0.0


class TestPerformanceDecorator:
    """Test performance tracking decorator"""
    
    def test_sync_function_tracking(self):
        service = AnalyticsService()
        
        @track_performance("test_service", "decorated_op")
        def test_function():
            time.sleep(0.01)
            return "success"
        
        # Patch the global service
        with patch('src.ai_karen_engine.services.analytics_service.get_analytics_service', return_value=service):
            result = test_function()
        
        assert result == "success"
        stats = service.get_service_performance("test_service")
        assert stats["total_requests"] == 1
        assert stats["success_rate"] == 1.0
    
    @pytest.mark.asyncio
    async def test_async_function_tracking(self):
        service = AnalyticsService()
        
        @track_performance("test_service", "async_op")
        async def async_test_function():
            await asyncio.sleep(0.01)
            return "async_success"
        
        # Patch the global service
        with patch('src.ai_karen_engine.services.analytics_service.get_analytics_service', return_value=service):
            result = await async_test_function()
        
        assert result == "async_success"
        stats = service.get_service_performance("test_service")
        assert stats["total_requests"] == 1
        assert stats["success_rate"] == 1.0


class TestGlobalServiceManagement:
    """Test global service instance management"""
    
    def test_get_analytics_service(self):
        # Reset global instance
        import src.ai_karen_engine.services.analytics_service as analytics_module
        analytics_module._analytics_service = None
        
        service1 = get_analytics_service()
        service2 = get_analytics_service()
        
        assert service1 is service2  # Should be same instance
    
    def test_initialize_analytics_service(self):
        config = {"max_metrics": 5000}
        service = initialize_analytics_service(config)
        
        assert service.config == config
        assert service.metrics_collector.metrics.maxlen == 5000


if __name__ == "__main__":
    pytest.main([__file__])