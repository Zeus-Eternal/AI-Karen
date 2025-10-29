"""
Tests for Extension Debugging and Monitoring System
"""

import pytest
import asyncio
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from .debug_manager import ExtensionDebugManager, DebugConfiguration
from .logger import ExtensionLogger
from .metrics_collector import ExtensionMetricsCollector
from .error_tracker import ExtensionErrorTracker
from .profiler import ExtensionProfiler
from .tracer import ExtensionTracer
from .alerting import ExtensionAlertManager, AlertSeverity
from .dashboard import ExtensionDebugDashboard
from .models import LogLevel, MetricPoint, ErrorRecord


class TestExtensionLogger:
    """Test extension logging functionality."""
    
    def test_logger_creation(self):
        """Test logger creation and basic functionality."""
        logger = ExtensionLogger("test-ext", "Test Extension")
        
        assert logger.extension_id == "test-ext"
        assert logger.extension_name == "Test Extension"
        assert logger.logger is not None
        assert logger.handler is not None
    
    def test_logging_methods(self):
        """Test different logging methods."""
        logger = ExtensionLogger("test-ext", "Test Extension")
        
        logger.debug("Debug message", key="value")
        logger.info("Info message", count=42)
        logger.warning("Warning message")
        logger.error("Error message", error_code=500)
        logger.critical("Critical message")
        
        logs = logger.get_logs()
        assert len(logs) == 5
        
        # Check log levels
        levels = [log.level for log in logs]
        assert LogLevel.DEBUG in levels
        assert LogLevel.INFO in levels
        assert LogLevel.WARNING in levels
        assert LogLevel.ERROR in levels
        assert LogLevel.CRITICAL in levels
    
    def test_correlation_context(self):
        """Test correlation ID context management."""
        logger = ExtensionLogger("test-ext", "Test Extension")
        
        with logger.correlation_context("test-correlation-123") as correlation_id:
            logger.info("Message with correlation")
            assert correlation_id == "test-correlation-123"
        
        logs = logger.get_logs()
        assert len(logs) == 1
        assert logs[0].correlation_id == "test-correlation-123"
    
    def test_user_context(self):
        """Test user context management."""
        logger = ExtensionLogger("test-ext", "Test Extension")
        
        with logger.user_context("user123", "tenant456"):
            logger.info("Message with user context")
        
        logs = logger.get_logs()
        assert len(logs) == 1
        assert logs[0].user_id == "user123"
        assert logs[0].tenant_id == "tenant456"


class TestExtensionMetricsCollector:
    """Test extension metrics collection."""
    
    @pytest.fixture
    def metrics_collector(self):
        """Create metrics collector for testing."""
        return ExtensionMetricsCollector("test-ext", "Test Extension", collection_interval=0.1)
    
    def test_metrics_collector_creation(self, metrics_collector):
        """Test metrics collector creation."""
        assert metrics_collector.extension_id == "test-ext"
        assert metrics_collector.extension_name == "Test Extension"
        assert not metrics_collector._collecting
    
    def test_record_metric(self, metrics_collector):
        """Test recording custom metrics."""
        metrics_collector.record_metric("test_metric", 42.5, "units", {"tag": "value"})
        
        metrics = metrics_collector.get_metrics()
        assert len(metrics) == 1
        
        metric = metrics[0]
        assert metric.metric_name == "test_metric"
        assert metric.value == 42.5
        assert metric.unit == "units"
        assert metric.tags["tag"] == "value"
    
    def test_custom_collector_registration(self, metrics_collector):
        """Test custom metric collector registration."""
        call_count = 0
        
        def custom_collector():
            nonlocal call_count
            call_count += 1
            return call_count * 10
        
        metrics_collector.register_custom_collector("custom_metric", custom_collector)
        
        # Manually trigger collection
        asyncio.run(metrics_collector._collect_metrics())
        
        metrics = metrics_collector.get_metrics("custom_metric")
        assert len(metrics) == 1
        assert metrics[0].value == 10
    
    def test_performance_summary(self, metrics_collector):
        """Test performance summary generation."""
        # Record some test data
        metrics_collector.record_request_time(100.0)
        metrics_collector.record_request_time(200.0)
        metrics_collector.record_error("TestError")
        
        summary = metrics_collector.get_performance_summary()
        
        assert "timestamp" in summary
        assert "requests" in summary
        assert "errors" in summary
        assert "resources" in summary


class TestExtensionErrorTracker:
    """Test extension error tracking."""
    
    @pytest.fixture
    def error_tracker(self):
        """Create error tracker for testing."""
        return ExtensionErrorTracker("test-ext", "Test Extension")
    
    def test_error_tracker_creation(self, error_tracker):
        """Test error tracker creation."""
        assert error_tracker.extension_id == "test-ext"
        assert error_tracker.extension_name == "Test Extension"
        assert len(error_tracker.errors) == 0
    
    def test_record_error(self, error_tracker):
        """Test error recording."""
        error_record = error_tracker.record_error(
            error_type="TestError",
            error_message="Test error message",
            stack_trace="Stack trace here",
            context={"key": "value"}
        )
        
        assert error_record.error_type == "TestError"
        assert error_record.error_message == "Test error message"
        assert error_record.context["key"] == "value"
        assert not error_record.resolved
        
        errors = error_tracker.get_errors()
        assert len(errors) == 1
        assert errors[0] == error_record
    
    def test_record_exception(self, error_tracker):
        """Test exception recording."""
        try:
            raise ValueError("Test exception")
        except ValueError as e:
            error_record = error_tracker.record_exception(e, {"context": "test"})
        
        assert error_record.error_type == "ValueError"
        assert error_record.error_message == "Test exception"
        assert "Traceback" in error_record.stack_trace
    
    def test_error_pattern_detection(self, error_tracker):
        """Test error pattern detection."""
        # Record similar errors to trigger pattern detection
        for i in range(5):
            error_tracker.record_error(
                error_type="NetworkError",
                error_message=f"Connection failed to server {i}",
                stack_trace="Same stack trace"
            )
        
        patterns = error_tracker.get_error_patterns()
        assert len(patterns) >= 1
        
        pattern = patterns[0]
        assert pattern.error_type == "NetworkError"
        assert pattern.occurrences >= 3
    
    def test_error_analysis(self, error_tracker):
        """Test error analysis."""
        # Record various errors
        error_tracker.record_error("Error1", "Message 1", "Stack 1")
        error_tracker.record_error("Error2", "Message 2", "Stack 2")
        error_tracker.record_error("Error1", "Message 3", "Stack 1")
        
        analysis = error_tracker.get_error_analysis()
        
        assert analysis.total_errors == 3
        assert analysis.unique_errors == 2
        assert analysis.error_rate > 0
        assert len(analysis.top_error_types) > 0


class TestExtensionProfiler:
    """Test extension profiling."""
    
    @pytest.fixture
    def profiler(self):
        """Create profiler for testing."""
        return ExtensionProfiler("test-ext", "Test Extension")
    
    def test_profiler_creation(self, profiler):
        """Test profiler creation."""
        assert profiler.extension_id == "test-ext"
        assert profiler.extension_name == "Test Extension"
        assert len(profiler.function_profiles) == 0
    
    def test_function_profiling(self, profiler):
        """Test function profiling decorator."""
        @profiler.profile_function
        def test_function(x, y):
            time.sleep(0.01)  # Small delay for timing
            return x + y
        
        result = test_function(1, 2)
        assert result == 3
        
        # Check profiling data
        profiles = profiler.function_profiles
        assert len(profiles) == 1
        
        profile_key = list(profiles.keys())[0]
        profile = profiles[profile_key]
        assert profile.function_name == "test_function"
        assert profile.call_count == 1
        assert profile.total_time > 0
    
    def test_profile_block(self, profiler):
        """Test profile block context manager."""
        with profiler.profile_block("test_block"):
            time.sleep(0.01)
        
        profiles = profiler.function_profiles
        assert len(profiles) == 1
        
        profile = list(profiles.values())[0]
        assert profile.function_name == "test_block"
        assert profile.call_count == 1
    
    def test_performance_summary(self, profiler):
        """Test performance summary generation."""
        # Profile some functions
        @profiler.profile_function
        def fast_function():
            pass
        
        @profiler.profile_function
        def slow_function():
            time.sleep(0.01)
        
        fast_function()
        slow_function()
        
        summary = profiler.get_performance_summary()
        
        assert summary["total_functions"] == 2
        assert summary["total_calls"] == 2
        assert len(summary["functions"]) == 2


class TestExtensionTracer:
    """Test extension tracing."""
    
    @pytest.fixture
    def tracer(self):
        """Create tracer for testing."""
        return ExtensionTracer("test-ext", "Test Extension", sampling_rate=1.0)
    
    def test_tracer_creation(self, tracer):
        """Test tracer creation."""
        assert tracer.extension_id == "test-ext"
        assert tracer.extension_name == "Test Extension"
        assert tracer.sampling_rate == 1.0
    
    def test_trace_creation(self, tracer):
        """Test trace creation and management."""
        context = tracer.start_trace("test_operation")
        
        assert context.trace_id is not None
        assert context.parent_span_id is not None
        assert len(tracer.active_traces) == 1
        
        tracer.finish_trace(context.trace_id)
        
        assert len(tracer.active_traces) == 0
        assert len(tracer.completed_traces) == 1
    
    def test_span_creation(self, tracer):
        """Test span creation within traces."""
        context = tracer.start_trace("test_operation")
        
        with tracer.start_span("sub_operation") as span:
            span.set_tag("test_tag", "test_value")
            span.log("Test log message", key="value")
            time.sleep(0.01)
        
        tracer.finish_trace(context.trace_id)
        
        completed_traces = tracer.get_completed_traces()
        assert len(completed_traces) == 1
        
        trace = completed_traces[0]
        assert len(trace.spans) == 2  # Root span + sub span
    
    def test_function_tracing(self, tracer):
        """Test function tracing decorator."""
        @tracer.trace_function("traced_function")
        def test_function(x):
            return x * 2
        
        context = tracer.start_trace("test_trace")
        result = test_function(5)
        tracer.finish_trace(context.trace_id)
        
        assert result == 10
        
        completed_traces = tracer.get_completed_traces()
        assert len(completed_traces) == 1


class TestExtensionAlertManager:
    """Test extension alerting."""
    
    @pytest.fixture
    def alert_manager(self):
        """Create alert manager for testing."""
        return ExtensionAlertManager("test-ext", "Test Extension")
    
    @pytest.mark.asyncio
    async def test_alert_manager_creation(self, alert_manager):
        """Test alert manager creation."""
        assert alert_manager.extension_id == "test-ext"
        assert alert_manager.extension_name == "Test Extension"
        assert len(alert_manager.active_alerts) == 0
    
    @pytest.mark.asyncio
    async def test_create_alert(self, alert_manager):
        """Test alert creation."""
        await alert_manager.start()
        
        alert = await alert_manager.create_alert(
            alert_type="test_alert",
            severity=AlertSeverity.HIGH,
            title="Test Alert",
            message="This is a test alert",
            metric_name="test_metric",
            current_value=100.0,
            threshold_value=80.0
        )
        
        assert alert is not None
        assert alert.alert_type == "test_alert"
        assert alert.severity == AlertSeverity.HIGH
        assert alert.title == "Test Alert"
        
        active_alerts = alert_manager.get_active_alerts()
        assert len(active_alerts) == 1
        assert active_alerts[0] == alert
        
        await alert_manager.stop()
    
    @pytest.mark.asyncio
    async def test_resolve_alert(self, alert_manager):
        """Test alert resolution."""
        await alert_manager.start()
        
        alert = await alert_manager.create_alert(
            alert_type="test_alert",
            severity=AlertSeverity.MEDIUM,
            title="Test Alert",
            message="Test message"
        )
        
        await alert_manager.resolve_alert(alert.id, "Resolved by test")
        
        active_alerts = alert_manager.get_active_alerts()
        assert len(active_alerts) == 0
        
        resolved_alerts = alert_manager.get_resolved_alerts()
        assert len(resolved_alerts) == 1
        assert resolved_alerts[0].resolved
        assert resolved_alerts[0].resolution_notes == "Resolved by test"
        
        await alert_manager.stop()


class TestExtensionDebugManager:
    """Test extension debug manager."""
    
    @pytest.fixture
    def debug_manager(self):
        """Create debug manager for testing."""
        config = DebugConfiguration(
            logging_enabled=True,
            metrics_enabled=True,
            error_tracking_enabled=True,
            profiling_enabled=True,
            tracing_enabled=True,
            alerting_enabled=True
        )
        return ExtensionDebugManager("test-ext", "Test Extension", config)
    
    def test_debug_manager_creation(self, debug_manager):
        """Test debug manager creation."""
        assert debug_manager.extension_id == "test-ext"
        assert debug_manager.extension_name == "Test Extension"
        assert debug_manager.logger is not None
        assert debug_manager.metrics_collector is not None
        assert debug_manager.error_tracker is not None
        assert debug_manager.profiler is not None
        assert debug_manager.tracer is not None
        assert debug_manager.alert_manager is not None
    
    @pytest.mark.asyncio
    async def test_debug_manager_lifecycle(self, debug_manager):
        """Test debug manager start/stop lifecycle."""
        assert not debug_manager._running
        
        await debug_manager.start()
        assert debug_manager._running
        
        await debug_manager.stop()
        assert not debug_manager._running
    
    def test_debug_session_management(self, debug_manager):
        """Test debug session management."""
        session_id = debug_manager.start_debug_session(
            configuration={"enable_profiling": True}
        )
        
        assert session_id in debug_manager.active_sessions
        session = debug_manager.active_sessions[session_id]
        assert session.configuration["enable_profiling"] is True
        
        completed_session = debug_manager.stop_debug_session(session_id)
        assert completed_session is not None
        assert completed_session.status == "completed"
        assert session_id not in debug_manager.active_sessions
    
    def test_debug_summary(self, debug_manager):
        """Test debug summary generation."""
        summary = debug_manager.get_debug_summary()
        
        assert summary["extension_id"] == "test-ext"
        assert summary["extension_name"] == "Test Extension"
        assert "enabled_components" in summary
        assert "logging" in summary["enabled_components"]
        assert "metrics" in summary["enabled_components"]
    
    @pytest.mark.asyncio
    async def test_health_diagnostics(self, debug_manager):
        """Test health diagnostics."""
        await debug_manager.start()
        
        health_status = await debug_manager.run_diagnostics()
        
        assert health_status.extension_id == "test-ext"
        assert health_status.overall_status in ["healthy", "degraded", "unhealthy"]
        assert len(health_status.diagnostics) > 0
        
        await debug_manager.stop()


class TestExtensionDebugDashboard:
    """Test extension debug dashboard."""
    
    @pytest.fixture
    def dashboard(self):
        """Create dashboard for testing."""
        config = DebugConfiguration(
            logging_enabled=True,
            metrics_enabled=True,
            error_tracking_enabled=True
        )
        debug_manager = ExtensionDebugManager("test-ext", "Test Extension", config)
        return ExtensionDebugDashboard(debug_manager)
    
    def test_dashboard_creation(self, dashboard):
        """Test dashboard creation."""
        assert dashboard.extension_id == "test-ext"
        assert dashboard.extension_name == "Test Extension"
        assert dashboard.debug_manager is not None
    
    def test_overview_data(self, dashboard):
        """Test overview data generation."""
        overview = dashboard.get_overview_data()
        
        assert overview["extension_id"] == "test-ext"
        assert overview["extension_name"] == "Test Extension"
        assert "status" in overview
        assert "enabled_components" in overview
    
    def test_dashboard_data(self, dashboard):
        """Test comprehensive dashboard data."""
        # Add some test data
        dashboard.debug_manager.logger.info("Test log message")
        dashboard.debug_manager.metrics_collector.record_metric("test_metric", 42.0)
        dashboard.debug_manager.error_tracker.record_error("TestError", "Test error", "Stack trace")
        
        dashboard_data = dashboard.get_dashboard_data()
        
        assert "overview" in dashboard_data
        assert "metrics" in dashboard_data
        assert "logs" in dashboard_data
        assert "errors" in dashboard_data
        assert "alerts" in dashboard_data
        assert "performance" in dashboard_data
        assert "health" in dashboard_data
        assert "sessions" in dashboard_data


if __name__ == "__main__":
    pytest.main([__file__])