"""
Tests for Analytics Dashboard Backend Service

Tests the analytics dashboard functionality including data aggregation,
real-time metrics, historical reporting, and user behavior insights.
"""

import pytest
import asyncio
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from src.ai_karen_engine.services.analytics_dashboard import (
    AnalyticsDashboard,
    DataAggregator,
    UserBehaviorAnalyzer,
    RealtimeMetricsProcessor,
    TimeRange,
    AggregationType,
    ChartType,
    DashboardWidget,
    DashboardConfig,
    AnalyticsQuery,
    AnalyticsResult,
    UserBehaviorInsight,
    SystemHealthSummary,
    TimeSeriesPoint,
    TimeSeriesData,
    get_analytics_dashboard,
    initialize_analytics_dashboard
)

from src.ai_karen_engine.services.analytics_service import (
    AnalyticsService,
    Metric,
    MetricType,
    Alert,
    AlertLevel,
    HealthStatus,
    UserInteractionEvent
)


class TestDataAggregator:
    """Test DataAggregator functionality"""
    
    def test_time_range_conversion(self):
        aggregator = DataAggregator()
        
        # Test time range to timedelta conversion
        delta_1h = aggregator._get_time_range_delta(TimeRange.LAST_HOUR)
        assert delta_1h == timedelta(hours=1)
        
        delta_24h = aggregator._get_time_range_delta(TimeRange.LAST_24_HOURS)
        assert delta_24h == timedelta(hours=24)
        
        delta_7d = aggregator._get_time_range_delta(TimeRange.LAST_7_DAYS)
        assert delta_7d == timedelta(days=7)
    
    def test_bucket_size_calculation(self):
        aggregator = DataAggregator()
        
        # Test bucket size calculation
        bucket_1h = aggregator._get_time_bucket_size(TimeRange.LAST_HOUR)
        assert bucket_1h == timedelta(minutes=1)
        
        bucket_24h = aggregator._get_time_bucket_size(TimeRange.LAST_24_HOURS)
        assert bucket_24h == timedelta(minutes=15)
    
    def test_aggregation_functions(self):
        aggregator = DataAggregator()
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        
        # Test different aggregation types
        assert aggregator._apply_aggregation(values, AggregationType.SUM) == 15.0
        assert aggregator._apply_aggregation(values, AggregationType.AVERAGE) == 3.0
        assert aggregator._apply_aggregation(values, AggregationType.COUNT) == 5
        assert aggregator._apply_aggregation(values, AggregationType.MIN) == 1.0
        assert aggregator._apply_aggregation(values, AggregationType.MAX) == 5.0
        
        # Test percentile
        p95 = aggregator._apply_aggregation(values, AggregationType.PERCENTILE, 95.0)
        assert p95 == 5.0  # 95th percentile of [1,2,3,4,5]
    
    def test_filter_matching(self):
        aggregator = DataAggregator()
        
        metric = Metric(
            name="test.metric",
            value=10.0,
            metric_type=MetricType.GAUGE,
            tags={"service": "test", "env": "prod"},
            metadata={"region": "us-east-1"}
        )
        
        # Test matching filters
        assert aggregator._matches_filters(metric, {"service": "test"}) == True
        assert aggregator._matches_filters(metric, {"env": "prod"}) == True
        assert aggregator._matches_filters(metric, {"region": "us-east-1"}) == True
        
        # Test non-matching filters
        assert aggregator._matches_filters(metric, {"service": "other"}) == False
        assert aggregator._matches_filters(metric, {"env": "dev"}) == False
        
        # Test empty filters
        assert aggregator._matches_filters(metric, {}) == True
    
    @patch('src.ai_karen_engine.services.analytics_service.get_analytics_service')
    def test_aggregate_metrics(self, mock_get_service):
        # Mock analytics service
        mock_service = Mock()
        mock_service.get_recent_metrics.return_value = [
            Metric("test.metric", 10.0, MetricType.GAUGE, timestamp=datetime.now()),
            Metric("test.metric", 20.0, MetricType.GAUGE, timestamp=datetime.now()),
            Metric("test.metric", 30.0, MetricType.GAUGE, timestamp=datetime.now())
        ]
        mock_get_service.return_value = mock_service
        
        aggregator = DataAggregator(mock_service)
        
        query = AnalyticsQuery(
            metric_name="test.metric",
            time_range=TimeRange.LAST_HOUR,
            aggregation=AggregationType.AVERAGE
        )
        
        result = aggregator.aggregate_metrics(query)
        
        # Should have aggregated the metrics
        assert len(result) > 0
        assert all(isinstance(point, TimeSeriesPoint) for point in result)


class TestUserBehaviorAnalyzer:
    """Test UserBehaviorAnalyzer functionality"""
    
    @patch('src.ai_karen_engine.services.analytics_service.get_analytics_service')
    def test_analyze_event_patterns(self, mock_get_service):
        # Mock analytics service
        mock_service = Mock()
        mock_service.get_popular_events.return_value = {
            "login": 100,
            "page_view": 80,
            "click": 60,
            "logout": 40
        }
        mock_get_service.return_value = mock_service
        
        analyzer = UserBehaviorAnalyzer(mock_service)
        insights = analyzer._analyze_event_patterns(mock_service.get_popular_events.return_value)
        
        # Should generate insights about popular events
        assert len(insights) > 0
        
        # Check for popular event insight
        popular_insight = next((i for i in insights if i.insight_type == "popular_event"), None)
        assert popular_insight is not None
        assert popular_insight.title.startswith("Most Popular User Action")
        assert popular_insight.data["event_type"] == "login"
        assert popular_insight.data["count"] == 100
    
    def test_entropy_calculation(self):
        analyzer = UserBehaviorAnalyzer()
        
        # Test entropy calculation
        # Equal distribution should have high entropy
        equal_values = [25, 25, 25, 25]
        entropy_equal = analyzer._calculate_entropy(equal_values)
        
        # Skewed distribution should have lower entropy
        skewed_values = [90, 5, 3, 2]
        entropy_skewed = analyzer._calculate_entropy(skewed_values)
        
        assert entropy_equal > entropy_skewed
        
        # Single value should have zero entropy
        single_value = [100]
        entropy_single = analyzer._calculate_entropy(single_value)
        assert entropy_single == 0.0
    
    @patch('src.ai_karen_engine.services.analytics_service.get_analytics_service')
    @pytest.mark.asyncio
    async def test_analyze_user_patterns(self, mock_get_service):
        # Mock analytics service
        mock_service = Mock()
        mock_service.get_popular_events.return_value = {"login": 50, "logout": 30}
        mock_service.user_tracker.user_sessions = {"session1": {}, "session2": {}}
        mock_get_service.return_value = mock_service
        
        analyzer = UserBehaviorAnalyzer(mock_service)
        insights = analyzer.analyze_user_patterns(TimeRange.LAST_24_HOURS)
        
        # Should generate multiple types of insights
        assert len(insights) > 0
        
        insight_types = [insight.insight_type for insight in insights]
        assert "popular_event" in insight_types


class TestRealtimeMetricsProcessor:
    """Test RealtimeMetricsProcessor functionality"""
    
    @pytest.mark.asyncio
    async def test_subscription_management(self):
        processor = RealtimeMetricsProcessor()
        
        callback_called = False
        
        def test_callback(metric):
            nonlocal callback_called
            callback_called = True
        
        # Test subscription
        processor.subscribe("test.metric", test_callback)
        assert "test.metric" in processor.subscribers
        assert test_callback in processor.subscribers["test.metric"]
        
        # Test unsubscription
        processor.unsubscribe("test.metric", test_callback)
        assert test_callback not in processor.subscribers["test.metric"]
    
    @pytest.mark.asyncio
    async def test_start_stop_processing(self):
        processor = RealtimeMetricsProcessor()
        
        # Test start
        await processor.start_processing()
        assert processor.is_running == True
        assert processor._processor_task is not None
        
        # Test stop
        await processor.stop_processing()
        assert processor.is_running == False


class TestAnalyticsDashboard:
    """Test main AnalyticsDashboard functionality"""
    
    def test_initialization(self):
        dashboard = AnalyticsDashboard()
        
        assert dashboard.analytics_service is not None
        assert dashboard.data_aggregator is not None
        assert dashboard.behavior_analyzer is not None
        assert dashboard.realtime_processor is not None
        assert dashboard.dashboards == {}
    
    def test_dashboard_management(self):
        dashboard = AnalyticsDashboard()
        
        # Create dashboard config
        config = DashboardConfig(
            id="test_dashboard",
            name="Test Dashboard",
            description="A test dashboard",
            widgets=[]
        )
        
        # Test create
        dashboard_id = dashboard.create_dashboard(config)
        assert dashboard_id == "test_dashboard"
        assert "test_dashboard" in dashboard.dashboards
        
        # Test get
        retrieved_config = dashboard.get_dashboard("test_dashboard")
        assert retrieved_config is not None
        assert retrieved_config.name == "Test Dashboard"
        
        # Test update
        config.name = "Updated Dashboard"
        success = dashboard.update_dashboard("test_dashboard", config)
        assert success == True
        
        updated_config = dashboard.get_dashboard("test_dashboard")
        assert updated_config.name == "Updated Dashboard"
        
        # Test list
        dashboards = dashboard.list_dashboards()
        assert len(dashboards) == 1
        assert dashboards[0].name == "Updated Dashboard"
        
        # Test delete
        success = dashboard.delete_dashboard("test_dashboard")
        assert success == True
        assert "test_dashboard" not in dashboard.dashboards
    
    @pytest.mark.asyncio
    async def test_query_execution(self):
        dashboard = AnalyticsDashboard()
        
        query = AnalyticsQuery(
            metric_name="test.metric",
            time_range=TimeRange.LAST_HOUR,
            aggregation=AggregationType.AVERAGE
        )
        
        # Mock the data aggregator
        with patch.object(dashboard.data_aggregator, 'aggregate_metrics') as mock_aggregate:
            mock_aggregate.return_value = [
                TimeSeriesPoint(datetime.now(), 10.0),
                TimeSeriesPoint(datetime.now(), 20.0)
            ]
            
            result = await dashboard.execute_query(query)
            
            assert isinstance(result, AnalyticsResult)
            assert result.query == query
            assert len(result.data) == 1
            assert len(result.data[0].data_points) == 2
            assert result.execution_time_ms > 0
            assert "count" in result.summary
            assert result.summary["count"] == 2
    
    @pytest.mark.asyncio
    async def test_widget_data(self):
        dashboard = AnalyticsDashboard()
        
        widget = DashboardWidget(
            id="test_widget",
            title="Test Widget",
            chart_type=ChartType.LINE,
            metric_name="test.metric",
            time_range=TimeRange.LAST_HOUR,
            aggregation=AggregationType.AVERAGE
        )
        
        # Mock the execute_query method
        with patch.object(dashboard, 'execute_query') as mock_execute:
            mock_result = AnalyticsResult(
                query=AnalyticsQuery(
                    metric_name="test.metric",
                    time_range=TimeRange.LAST_HOUR,
                    aggregation=AggregationType.AVERAGE
                ),
                data=[],
                summary={},
                execution_time_ms=100.0
            )
            mock_execute.return_value = mock_result
            
            result = await dashboard.get_widget_data(widget)
            
            assert result == mock_result
            mock_execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_dashboard_data(self):
        dashboard = AnalyticsDashboard()
        
        # Create dashboard with widgets
        widget1 = DashboardWidget(
            id="widget1",
            title="Widget 1",
            chart_type=ChartType.LINE,
            metric_name="metric1",
            time_range=TimeRange.LAST_HOUR,
            aggregation=AggregationType.AVERAGE
        )
        
        widget2 = DashboardWidget(
            id="widget2",
            title="Widget 2",
            chart_type=ChartType.BAR,
            metric_name="metric2",
            time_range=TimeRange.LAST_24_HOURS,
            aggregation=AggregationType.COUNT
        )
        
        config = DashboardConfig(
            id="test_dashboard",
            name="Test Dashboard",
            widgets=[widget1, widget2]
        )
        
        dashboard.create_dashboard(config)
        
        # Mock get_widget_data
        with patch.object(dashboard, 'get_widget_data') as mock_get_widget:
            mock_result = AnalyticsResult(
                query=AnalyticsQuery(
                    metric_name="test",
                    time_range=TimeRange.LAST_HOUR,
                    aggregation=AggregationType.AVERAGE
                ),
                data=[],
                summary={},
                execution_time_ms=100.0
            )
            mock_get_widget.return_value = mock_result
            
            results = await dashboard.get_dashboard_data("test_dashboard")
            
            assert len(results) == 2
            assert "widget1" in results
            assert "widget2" in results
            assert mock_get_widget.call_count == 2
    
    @pytest.mark.asyncio
    async def test_system_health_summary(self):
        dashboard = AnalyticsDashboard()
        
        # Mock analytics service methods
        with patch.object(dashboard.analytics_service, 'run_all_health_checks') as mock_health, \
             patch.object(dashboard.analytics_service, 'get_overall_health') as mock_overall, \
             patch.object(dashboard.analytics_service, 'get_recent_alerts') as mock_alerts, \
             patch.object(dashboard.analytics_service, 'get_system_metrics') as mock_metrics, \
             patch.object(dashboard.analytics_service, 'get_service_performance') as mock_perf:
            
            # Setup mocks
            mock_health.return_value = {
                "database": Mock(status=HealthStatus.HEALTHY),
                "memory_service": Mock(status=HealthStatus.HEALTHY)
            }
            mock_overall.return_value = HealthStatus.HEALTHY
            mock_alerts.return_value = [
                Mock(level=AlertLevel.WARNING),
                Mock(level=AlertLevel.CRITICAL)
            ]
            mock_metrics.return_value = Mock(
                cpu_percent=25.0,
                memory_percent=60.0,
                disk_usage_percent=45.0
            )
            mock_perf.return_value = {"total_requests": 100, "success_rate": 0.95}
            
            summary = await dashboard.get_system_health_summary()
            
            assert isinstance(summary, SystemHealthSummary)
            assert summary.overall_status == HealthStatus.HEALTHY
            assert len(summary.component_statuses) == 2
            assert summary.active_alerts == 2
            assert summary.critical_alerts == 1
            assert summary.system_metrics["cpu_percent"] == 25.0
    
    @pytest.mark.asyncio
    async def test_user_insights(self):
        dashboard = AnalyticsDashboard()
        
        # Mock behavior analyzer
        with patch.object(dashboard.behavior_analyzer, 'analyze_user_patterns') as mock_analyze:
            mock_insights = [
                UserBehaviorInsight(
                    insight_type="test",
                    title="Test Insight",
                    description="A test insight",
                    confidence=0.8,
                    data={}
                )
            ]
            mock_analyze.return_value = mock_insights
            
            insights = await dashboard.get_user_insights(TimeRange.LAST_7_DAYS)
            
            assert len(insights) == 1
            assert insights[0].title == "Test Insight"
            mock_analyze.assert_called_once_with(TimeRange.LAST_7_DAYS)
    
    def test_available_metrics(self):
        dashboard = AnalyticsDashboard()
        
        metrics = dashboard.get_available_metrics()
        
        assert isinstance(metrics, list)
        assert len(metrics) > 0
        assert "system.cpu.percent" in metrics
        assert "system.memory.percent" in metrics
    
    def test_dashboard_templates(self):
        dashboard = AnalyticsDashboard()
        
        templates = dashboard.get_dashboard_templates()
        
        assert isinstance(templates, list)
        assert len(templates) > 0
        
        # Check system overview template
        system_template = next((t for t in templates if t.id == "system_overview"), None)
        assert system_template is not None
        assert system_template.name == "System Overview"
        assert len(system_template.widgets) > 0
    
    @pytest.mark.asyncio
    async def test_realtime_updates(self):
        dashboard = AnalyticsDashboard()
        
        # Test start/stop
        await dashboard.start_realtime_updates()
        assert dashboard.realtime_processor.is_running == True
        
        await dashboard.stop_realtime_updates()
        assert dashboard.realtime_processor.is_running == False
        
        # Test subscription
        callback_called = False
        
        def test_callback(metric):
            nonlocal callback_called
            callback_called = True
        
        dashboard.subscribe_to_metric("test.metric", test_callback)
        assert "test.metric" in dashboard.realtime_processor.subscribers
        
        dashboard.unsubscribe_from_metric("test.metric", test_callback)
        assert test_callback not in dashboard.realtime_processor.subscribers["test.metric"]
    
    @pytest.mark.asyncio
    async def test_shutdown(self):
        dashboard = AnalyticsDashboard()
        
        # Start some processes
        await dashboard.start_realtime_updates()
        
        # Shutdown should not raise exception
        await dashboard.shutdown()
        
        assert dashboard.realtime_processor.is_running == False


class TestGlobalDashboardManagement:
    """Test global dashboard instance management"""
    
    def test_get_analytics_dashboard(self):
        # Reset global instance
        import src.ai_karen_engine.services.analytics_dashboard as dashboard_module
        dashboard_module._analytics_dashboard = None
        
        dashboard1 = get_analytics_dashboard()
        dashboard2 = get_analytics_dashboard()
        
        assert dashboard1 is dashboard2  # Should be same instance
    
    def test_initialize_analytics_dashboard(self):
        mock_service = Mock()
        dashboard = initialize_analytics_dashboard(mock_service)
        
        assert dashboard.analytics_service == mock_service


if __name__ == "__main__":
    pytest.main([__file__])