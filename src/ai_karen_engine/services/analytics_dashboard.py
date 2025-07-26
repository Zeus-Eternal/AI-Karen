"""
Analytics Dashboard Backend Service

Provides data aggregation, processing, and insights generation for analytics dashboards.
Supports real-time metrics, historical reporting, and user behavior analysis.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, Counter
import statistics
from concurrent.futures import ThreadPoolExecutor

from pydantic import BaseModel, Field

from ai_karen_engine.services.analytics_service import (
    AnalyticsService,
    get_analytics_service,
    Metric,
    MetricType,
    Alert,
    AlertLevel,
    HealthStatus,
    UserInteractionEvent,
    PerformanceMetrics
)


class TimeRange(str, Enum):
    """Time range options for analytics queries"""
    LAST_HOUR = "1h"
    LAST_6_HOURS = "6h"
    LAST_24_HOURS = "24h"
    LAST_7_DAYS = "7d"
    LAST_30_DAYS = "30d"
    LAST_90_DAYS = "90d"


class AggregationType(str, Enum):
    """Types of data aggregation"""
    SUM = "sum"
    AVERAGE = "average"
    COUNT = "count"
    MIN = "min"
    MAX = "max"
    PERCENTILE = "percentile"


class ChartType(str, Enum):
    """Chart types for dashboard visualization"""
    LINE = "line"
    BAR = "bar"
    PIE = "pie"
    AREA = "area"
    SCATTER = "scatter"
    HEATMAP = "heatmap"
    GAUGE = "gauge"


@dataclass
class TimeSeriesPoint:
    """Single point in a time series"""
    timestamp: datetime
    value: Union[int, float]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TimeSeriesData:
    """Time series data for charts"""
    name: str
    data_points: List[TimeSeriesPoint]
    chart_type: ChartType = ChartType.LINE
    metadata: Dict[str, Any] = field(default_factory=dict)


class DashboardWidget(BaseModel):
    """Dashboard widget configuration"""
    id: str
    title: str
    description: Optional[str] = None
    chart_type: ChartType
    metric_name: str
    time_range: TimeRange
    aggregation: AggregationType
    filters: Dict[str, Any] = Field(default_factory=dict)
    refresh_interval: int = 30  # seconds
    position: Dict[str, int] = Field(default_factory=dict)  # x, y, width, height


class DashboardConfig(BaseModel):
    """Dashboard configuration"""
    id: str
    name: str
    description: Optional[str] = None
    widgets: List[DashboardWidget]
    layout: Dict[str, Any] = Field(default_factory=dict)
    permissions: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class AnalyticsQuery(BaseModel):
    """Analytics query parameters"""
    metric_name: str
    time_range: TimeRange
    aggregation: AggregationType
    group_by: Optional[List[str]] = None
    filters: Dict[str, Any] = Field(default_factory=dict)
    limit: Optional[int] = None
    percentile: Optional[float] = None  # For percentile aggregation


class AnalyticsResult(BaseModel):
    """Analytics query result"""
    query: AnalyticsQuery
    data: List[TimeSeriesData]
    summary: Dict[str, Any]
    generated_at: datetime = Field(default_factory=datetime.now)
    execution_time_ms: float


class UserBehaviorInsight(BaseModel):
    """User behavior analysis insight"""
    insight_type: str
    title: str
    description: str
    confidence: float  # 0.0 to 1.0
    data: Dict[str, Any]
    recommendations: List[str] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=datetime.now)


class SystemHealthSummary(BaseModel):
    """System health summary for dashboard"""
    overall_status: HealthStatus
    component_statuses: Dict[str, HealthStatus]
    active_alerts: int
    critical_alerts: int
    system_metrics: Dict[str, float]
    performance_summary: Dict[str, Dict[str, float]]
    uptime_percentage: float
    last_updated: datetime = Field(default_factory=datetime.now)


class DataAggregator:
    """Aggregates and processes analytics data"""
    
    def __init__(self, analytics_service: AnalyticsService = None):
        self.analytics_service = analytics_service or get_analytics_service()
        self.logger = logging.getLogger(__name__)
    
    def _get_time_range_delta(self, time_range: TimeRange) -> timedelta:
        """Convert TimeRange enum to timedelta"""
        range_map = {
            TimeRange.LAST_HOUR: timedelta(hours=1),
            TimeRange.LAST_6_HOURS: timedelta(hours=6),
            TimeRange.LAST_24_HOURS: timedelta(hours=24),
            TimeRange.LAST_7_DAYS: timedelta(days=7),
            TimeRange.LAST_30_DAYS: timedelta(days=30),
            TimeRange.LAST_90_DAYS: timedelta(days=90)
        }
        return range_map.get(time_range, timedelta(hours=24))
    
    def _get_time_bucket_size(self, time_range: TimeRange) -> timedelta:
        """Get appropriate time bucket size for aggregation"""
        bucket_map = {
            TimeRange.LAST_HOUR: timedelta(minutes=1),
            TimeRange.LAST_6_HOURS: timedelta(minutes=5),
            TimeRange.LAST_24_HOURS: timedelta(minutes=15),
            TimeRange.LAST_7_DAYS: timedelta(hours=1),
            TimeRange.LAST_30_DAYS: timedelta(hours=6),
            TimeRange.LAST_90_DAYS: timedelta(days=1)
        }
        return bucket_map.get(time_range, timedelta(minutes=15))
    
    def aggregate_metrics(self, query: AnalyticsQuery) -> List[TimeSeriesPoint]:
        """Aggregate metrics based on query parameters"""
        try:
            # Get time range
            time_delta = self._get_time_range_delta(query.time_range)
            start_time = datetime.now() - time_delta
            
            # Get recent metrics
            recent_metrics = self.analytics_service.get_recent_metrics(
                minutes=int(time_delta.total_seconds() / 60)
            )
            
            # Filter metrics by name and filters
            filtered_metrics = []
            for metric in recent_metrics:
                if metric.name == query.metric_name:
                    # Apply filters
                    if self._matches_filters(metric, query.filters):
                        filtered_metrics.append(metric)
            
            if not filtered_metrics:
                return []
            
            # Group by time buckets
            bucket_size = self._get_time_bucket_size(query.time_range)
            time_buckets = defaultdict(list)
            
            for metric in filtered_metrics:
                # Calculate bucket timestamp
                bucket_timestamp = self._get_bucket_timestamp(metric.timestamp, bucket_size)
                time_buckets[bucket_timestamp].append(metric.value)
            
            # Aggregate values in each bucket
            aggregated_points = []
            for timestamp, values in sorted(time_buckets.items()):
                aggregated_value = self._apply_aggregation(values, query.aggregation, query.percentile)
                aggregated_points.append(TimeSeriesPoint(
                    timestamp=timestamp,
                    value=aggregated_value,
                    metadata={"count": len(values)}
                ))
            
            return aggregated_points
            
        except Exception as e:
            self.logger.error(f"Error aggregating metrics: {e}")
            return []
    
    def _matches_filters(self, metric: Metric, filters: Dict[str, Any]) -> bool:
        """Check if metric matches the given filters"""
        for filter_key, filter_value in filters.items():
            if filter_key in metric.tags:
                if metric.tags[filter_key] != filter_value:
                    return False
            elif filter_key in metric.metadata:
                if metric.metadata[filter_key] != filter_value:
                    return False
        return True
    
    def _get_bucket_timestamp(self, timestamp: datetime, bucket_size: timedelta) -> datetime:
        """Get the bucket timestamp for a given timestamp and bucket size"""
        # Round down to the nearest bucket
        total_seconds = int(timestamp.timestamp())
        bucket_seconds = int(bucket_size.total_seconds())
        bucket_timestamp = (total_seconds // bucket_seconds) * bucket_seconds
        return datetime.fromtimestamp(bucket_timestamp)
    
    def _apply_aggregation(self, values: List[float], aggregation: AggregationType, 
                          percentile: Optional[float] = None) -> float:
        """Apply aggregation function to values"""
        if not values:
            return 0.0
        
        if aggregation == AggregationType.SUM:
            return sum(values)
        elif aggregation == AggregationType.AVERAGE:
            return statistics.mean(values)
        elif aggregation == AggregationType.COUNT:
            return len(values)
        elif aggregation == AggregationType.MIN:
            return min(values)
        elif aggregation == AggregationType.MAX:
            return max(values)
        elif aggregation == AggregationType.PERCENTILE:
            if percentile is None:
                percentile = 95.0
            sorted_values = sorted(values)
            index = int((percentile / 100.0) * len(sorted_values))
            return sorted_values[min(index, len(sorted_values) - 1)]
        else:
            return statistics.mean(values)


class UserBehaviorAnalyzer:
    """Analyzes user behavior patterns and generates insights"""
    
    def __init__(self, analytics_service: AnalyticsService = None):
        self.analytics_service = analytics_service or get_analytics_service()
        self.logger = logging.getLogger(__name__)
    
    def analyze_user_patterns(self, time_range: TimeRange = TimeRange.LAST_7_DAYS) -> List[UserBehaviorInsight]:
        """Analyze user behavior patterns and generate insights"""
        insights = []
        
        try:
            # Get popular events
            hours = self._time_range_to_hours(time_range)
            popular_events = self.analytics_service.get_popular_events(hours)
            
            # Analyze event patterns
            insights.extend(self._analyze_event_patterns(popular_events))
            
            # Analyze user activity trends
            insights.extend(self._analyze_activity_trends(hours))
            
            # Analyze session patterns
            insights.extend(self._analyze_session_patterns())
            
        except Exception as e:
            self.logger.error(f"Error analyzing user patterns: {e}")
        
        return insights
    
    def _time_range_to_hours(self, time_range: TimeRange) -> int:
        """Convert TimeRange to hours"""
        range_map = {
            TimeRange.LAST_HOUR: 1,
            TimeRange.LAST_6_HOURS: 6,
            TimeRange.LAST_24_HOURS: 24,
            TimeRange.LAST_7_DAYS: 168,
            TimeRange.LAST_30_DAYS: 720,
            TimeRange.LAST_90_DAYS: 2160
        }
        return range_map.get(time_range, 168)
    
    def _analyze_event_patterns(self, popular_events: Dict[str, int]) -> List[UserBehaviorInsight]:
        """Analyze event patterns and generate insights"""
        insights = []
        
        if not popular_events:
            return insights
        
        total_events = sum(popular_events.values())
        sorted_events = sorted(popular_events.items(), key=lambda x: x[1], reverse=True)
        
        # Most popular event insight
        if sorted_events:
            top_event, top_count = sorted_events[0]
            percentage = (top_count / total_events) * 100
            
            insights.append(UserBehaviorInsight(
                insight_type="popular_event",
                title=f"Most Popular User Action: {top_event}",
                description=f"'{top_event}' accounts for {percentage:.1f}% of all user interactions",
                confidence=0.9,
                data={
                    "event_type": top_event,
                    "count": top_count,
                    "percentage": percentage,
                    "total_events": total_events
                },
                recommendations=[
                    f"Consider optimizing the '{top_event}' experience",
                    "Monitor performance metrics for this popular action"
                ]
            ))
        
        # Event diversity insight
        unique_events = len(popular_events)
        if unique_events > 1:
            # Calculate event distribution entropy
            entropy = self._calculate_entropy(list(popular_events.values()))
            
            if entropy > 2.0:  # High diversity
                insights.append(UserBehaviorInsight(
                    insight_type="event_diversity",
                    title="High User Engagement Diversity",
                    description=f"Users are engaging with {unique_events} different features",
                    confidence=0.8,
                    data={
                        "unique_events": unique_events,
                        "entropy": entropy,
                        "events": popular_events
                    },
                    recommendations=[
                        "Users are exploring multiple features - consider feature discovery improvements",
                        "Monitor which feature combinations are most effective"
                    ]
                ))
        
        return insights
    
    def _analyze_activity_trends(self, hours: int) -> List[UserBehaviorInsight]:
        """Analyze user activity trends"""
        insights = []
        
        try:
            # This would typically analyze user activity over time
            # For now, we'll create a placeholder insight
            insights.append(UserBehaviorInsight(
                insight_type="activity_trend",
                title="User Activity Analysis",
                description=f"Analyzed user activity patterns over the last {hours} hours",
                confidence=0.7,
                data={
                    "analysis_period_hours": hours,
                    "trend": "stable"  # This would be calculated from actual data
                },
                recommendations=[
                    "Continue monitoring user activity patterns",
                    "Consider implementing activity-based notifications"
                ]
            ))
            
        except Exception as e:
            self.logger.error(f"Error analyzing activity trends: {e}")
        
        return insights
    
    def _analyze_session_patterns(self) -> List[UserBehaviorInsight]:
        """Analyze user session patterns"""
        insights = []
        
        try:
            # Get session statistics
            session_count = len(self.analytics_service.user_tracker.user_sessions)
            
            if session_count > 0:
                insights.append(UserBehaviorInsight(
                    insight_type="session_analysis",
                    title="Active User Sessions",
                    description=f"Currently tracking {session_count} active user sessions",
                    confidence=0.9,
                    data={
                        "active_sessions": session_count
                    },
                    recommendations=[
                        "Monitor session duration and engagement",
                        "Consider session-based personalization"
                    ]
                ))
            
        except Exception as e:
            self.logger.error(f"Error analyzing session patterns: {e}")
        
        return insights
    
    def _calculate_entropy(self, values: List[int]) -> float:
        """Calculate Shannon entropy for event distribution"""
        import math
        
        total = sum(values)
        if total == 0:
            return 0.0
        
        entropy = 0.0
        for value in values:
            if value > 0:
                probability = value / total
                entropy -= probability * math.log2(probability)
        
        return entropy


class RealtimeMetricsProcessor:
    """Processes real-time metrics for dashboard updates"""
    
    def __init__(self, analytics_service: AnalyticsService = None):
        self.analytics_service = analytics_service or get_analytics_service()
        self.subscribers: Dict[str, List[callable]] = defaultdict(list)
        self.is_running = False
        self._processor_task = None
        self.logger = logging.getLogger(__name__)
    
    def subscribe(self, metric_name: str, callback: callable):
        """Subscribe to real-time updates for a metric"""
        self.subscribers[metric_name].append(callback)
        self.logger.info(f"Subscribed to real-time updates for {metric_name}")
    
    def unsubscribe(self, metric_name: str, callback: callable):
        """Unsubscribe from real-time updates"""
        if callback in self.subscribers[metric_name]:
            self.subscribers[metric_name].remove(callback)
    
    async def start_processing(self):
        """Start real-time metrics processing"""
        if self.is_running:
            return
        
        self.is_running = True
        self._processor_task = asyncio.create_task(self._process_loop())
        self.logger.info("Started real-time metrics processing")
    
    async def stop_processing(self):
        """Stop real-time metrics processing"""
        self.is_running = False
        if self._processor_task:
            self._processor_task.cancel()
            try:
                await self._processor_task
            except asyncio.CancelledError:
                pass
        self.logger.info("Stopped real-time metrics processing")
    
    async def _process_loop(self):
        """Main processing loop for real-time metrics"""
        last_processed = datetime.now()
        
        while self.is_running:
            try:
                # Get recent metrics since last processing
                current_time = datetime.now()
                minutes_since_last = int((current_time - last_processed).total_seconds() / 60)
                
                if minutes_since_last > 0:
                    recent_metrics = self.analytics_service.get_recent_metrics(minutes_since_last)
                    
                    # Process metrics for subscribers
                    for metric in recent_metrics:
                        if metric.name in self.subscribers:
                            for callback in self.subscribers[metric.name]:
                                try:
                                    if asyncio.iscoroutinefunction(callback):
                                        await callback(metric)
                                    else:
                                        callback(metric)
                                except Exception as e:
                                    self.logger.error(f"Error in metric callback: {e}")
                    
                    last_processed = current_time
                
                # Wait before next processing cycle
                await asyncio.sleep(5)  # Process every 5 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in real-time processing loop: {e}")
                await asyncio.sleep(5)


class AnalyticsDashboard:
    """
    Main Analytics Dashboard Backend Service
    
    Provides comprehensive analytics dashboard functionality including data aggregation,
    real-time metrics, historical reporting, and user behavior insights.
    """
    
    def __init__(self, analytics_service: AnalyticsService = None):
        self.analytics_service = analytics_service or get_analytics_service()
        self.data_aggregator = DataAggregator(self.analytics_service)
        self.behavior_analyzer = UserBehaviorAnalyzer(self.analytics_service)
        self.realtime_processor = RealtimeMetricsProcessor(self.analytics_service)
        
        self.dashboards: Dict[str, DashboardConfig] = {}
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.logger = logging.getLogger(__name__)
        
        self.logger.info("Analytics Dashboard initialized")
    
    # Dashboard Management
    def create_dashboard(self, config: DashboardConfig) -> str:
        """Create a new dashboard"""
        self.dashboards[config.id] = config
        self.logger.info(f"Created dashboard: {config.name}")
        return config.id
    
    def get_dashboard(self, dashboard_id: str) -> Optional[DashboardConfig]:
        """Get dashboard configuration"""
        return self.dashboards.get(dashboard_id)
    
    def update_dashboard(self, dashboard_id: str, config: DashboardConfig) -> bool:
        """Update dashboard configuration"""
        if dashboard_id in self.dashboards:
            config.updated_at = datetime.now()
            self.dashboards[dashboard_id] = config
            self.logger.info(f"Updated dashboard: {dashboard_id}")
            return True
        return False
    
    def delete_dashboard(self, dashboard_id: str) -> bool:
        """Delete a dashboard"""
        if dashboard_id in self.dashboards:
            del self.dashboards[dashboard_id]
            self.logger.info(f"Deleted dashboard: {dashboard_id}")
            return True
        return False
    
    def list_dashboards(self) -> List[DashboardConfig]:
        """List all dashboards"""
        return list(self.dashboards.values())
    
    # Data Query and Aggregation
    async def execute_query(self, query: AnalyticsQuery) -> AnalyticsResult:
        """Execute an analytics query"""
        start_time = datetime.now()
        
        try:
            # Run aggregation in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            aggregated_data = await loop.run_in_executor(
                self.executor,
                self.data_aggregator.aggregate_metrics,
                query
            )
            
            # Create time series data
            time_series = TimeSeriesData(
                name=query.metric_name,
                data_points=aggregated_data,
                chart_type=ChartType.LINE
            )
            
            # Generate summary statistics
            values = [point.value for point in aggregated_data]
            summary = self._generate_summary(values, query)
            
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return AnalyticsResult(
                query=query,
                data=[time_series],
                summary=summary,
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            self.logger.error(f"Error executing query: {e}")
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            return AnalyticsResult(
                query=query,
                data=[],
                summary={"error": str(e)},
                execution_time_ms=execution_time
            )
    
    def _generate_summary(self, values: List[float], query: AnalyticsQuery) -> Dict[str, Any]:
        """Generate summary statistics for query results"""
        if not values:
            return {"count": 0}
        
        return {
            "count": len(values),
            "sum": sum(values),
            "average": statistics.mean(values),
            "min": min(values),
            "max": max(values),
            "median": statistics.median(values),
            "std_dev": statistics.stdev(values) if len(values) > 1 else 0.0
        }
    
    # Widget Data
    async def get_widget_data(self, widget: DashboardWidget) -> AnalyticsResult:
        """Get data for a specific dashboard widget"""
        query = AnalyticsQuery(
            metric_name=widget.metric_name,
            time_range=widget.time_range,
            aggregation=widget.aggregation,
            filters=widget.filters
        )
        return await self.execute_query(query)
    
    async def get_dashboard_data(self, dashboard_id: str) -> Dict[str, AnalyticsResult]:
        """Get data for all widgets in a dashboard"""
        dashboard = self.get_dashboard(dashboard_id)
        if not dashboard:
            return {}
        
        results = {}
        for widget in dashboard.widgets:
            try:
                results[widget.id] = await self.get_widget_data(widget)
            except Exception as e:
                self.logger.error(f"Error getting data for widget {widget.id}: {e}")
                results[widget.id] = AnalyticsResult(
                    query=AnalyticsQuery(
                        metric_name=widget.metric_name,
                        time_range=widget.time_range,
                        aggregation=widget.aggregation
                    ),
                    data=[],
                    summary={"error": str(e)},
                    execution_time_ms=0.0
                )
        
        return results
    
    # System Health Dashboard
    async def get_system_health_summary(self) -> SystemHealthSummary:
        """Get comprehensive system health summary"""
        try:
            # Get health checks
            health_checks = await self.analytics_service.run_all_health_checks()
            overall_status = self.analytics_service.get_overall_health()
            
            component_statuses = {
                name: check.status for name, check in health_checks.items()
            }
            
            # Get alerts
            recent_alerts = self.analytics_service.get_recent_alerts(minutes=60)
            active_alerts = len(recent_alerts)
            critical_alerts = len([a for a in recent_alerts if a.level == AlertLevel.CRITICAL])
            
            # Get system metrics
            system_metrics = self.analytics_service.get_system_metrics()
            system_metrics_dict = {
                "cpu_percent": system_metrics.cpu_percent,
                "memory_percent": system_metrics.memory_percent,
                "disk_usage_percent": system_metrics.disk_usage_percent
            }
            
            # Get performance summary (placeholder)
            performance_summary = {
                "ai_orchestrator": self.analytics_service.get_service_performance("ai_orchestrator", hours=1),
                "memory_service": self.analytics_service.get_service_performance("memory_service", hours=1),
                "plugin_service": self.analytics_service.get_service_performance("plugin_service", hours=1)
            }
            
            # Calculate uptime percentage (placeholder)
            uptime_percentage = 99.5  # This would be calculated from actual uptime data
            
            return SystemHealthSummary(
                overall_status=overall_status,
                component_statuses=component_statuses,
                active_alerts=active_alerts,
                critical_alerts=critical_alerts,
                system_metrics=system_metrics_dict,
                performance_summary=performance_summary,
                uptime_percentage=uptime_percentage
            )
            
        except Exception as e:
            self.logger.error(f"Error getting system health summary: {e}")
            return SystemHealthSummary(
                overall_status=HealthStatus.UNKNOWN,
                component_statuses={},
                active_alerts=0,
                critical_alerts=0,
                system_metrics={},
                performance_summary={},
                uptime_percentage=0.0
            )
    
    # User Behavior Insights
    async def get_user_insights(self, time_range: TimeRange = TimeRange.LAST_7_DAYS) -> List[UserBehaviorInsight]:
        """Get user behavior insights"""
        try:
            loop = asyncio.get_event_loop()
            insights = await loop.run_in_executor(
                self.executor,
                self.behavior_analyzer.analyze_user_patterns,
                time_range
            )
            return insights
        except Exception as e:
            self.logger.error(f"Error getting user insights: {e}")
            return []
    
    # Real-time Updates
    async def start_realtime_updates(self):
        """Start real-time metrics processing"""
        await self.realtime_processor.start_processing()
    
    async def stop_realtime_updates(self):
        """Stop real-time metrics processing"""
        await self.realtime_processor.stop_processing()
    
    def subscribe_to_metric(self, metric_name: str, callback: callable):
        """Subscribe to real-time metric updates"""
        self.realtime_processor.subscribe(metric_name, callback)
    
    def unsubscribe_from_metric(self, metric_name: str, callback: callable):
        """Unsubscribe from real-time metric updates"""
        self.realtime_processor.unsubscribe(metric_name, callback)
    
    # Utility Methods
    def get_available_metrics(self) -> List[str]:
        """Get list of available metrics for dashboard creation"""
        # This would typically query the metrics collector for available metric names
        return [
            "system.cpu.percent",
            "system.memory.percent",
            "system.disk.percent",
            "user.events.login",
            "user.events.logout",
            "service.ai_orchestrator.duration",
            "service.memory_service.duration",
            "service.plugin_service.duration"
        ]
    
    def get_dashboard_templates(self) -> List[DashboardConfig]:
        """Get predefined dashboard templates"""
        templates = []
        
        # System Overview Template
        system_template = DashboardConfig(
            id="system_overview",
            name="System Overview",
            description="Comprehensive system health and performance dashboard",
            widgets=[
                DashboardWidget(
                    id="cpu_usage",
                    title="CPU Usage",
                    chart_type=ChartType.LINE,
                    metric_name="system.cpu.percent",
                    time_range=TimeRange.LAST_24_HOURS,
                    aggregation=AggregationType.AVERAGE,
                    position={"x": 0, "y": 0, "width": 6, "height": 4}
                ),
                DashboardWidget(
                    id="memory_usage",
                    title="Memory Usage",
                    chart_type=ChartType.LINE,
                    metric_name="system.memory.percent",
                    time_range=TimeRange.LAST_24_HOURS,
                    aggregation=AggregationType.AVERAGE,
                    position={"x": 6, "y": 0, "width": 6, "height": 4}
                ),
                DashboardWidget(
                    id="user_events",
                    title="User Events",
                    chart_type=ChartType.BAR,
                    metric_name="user.events.login",
                    time_range=TimeRange.LAST_24_HOURS,
                    aggregation=AggregationType.COUNT,
                    position={"x": 0, "y": 4, "width": 12, "height": 4}
                )
            ]
        )
        templates.append(system_template)
        
        return templates
    
    async def shutdown(self):
        """Shutdown the analytics dashboard"""
        await self.stop_realtime_updates()
        self.executor.shutdown(wait=True)
        self.logger.info("Analytics Dashboard shutdown")


# Global dashboard instance
_analytics_dashboard: Optional[AnalyticsDashboard] = None


def get_analytics_dashboard(analytics_service: AnalyticsService = None) -> AnalyticsDashboard:
    """Get or create the global analytics dashboard instance"""
    global _analytics_dashboard
    if _analytics_dashboard is None:
        _analytics_dashboard = AnalyticsDashboard(analytics_service)
    return _analytics_dashboard


def initialize_analytics_dashboard(analytics_service: AnalyticsService = None) -> AnalyticsDashboard:
    """Initialize the analytics dashboard with configuration"""
    global _analytics_dashboard
    _analytics_dashboard = AnalyticsDashboard(analytics_service)
    return _analytics_dashboard