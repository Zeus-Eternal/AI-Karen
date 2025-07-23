#!/usr/bin/env python3
"""
Demo script for Analytics Dashboard Backend Service

This script demonstrates the comprehensive analytics and monitoring capabilities
of the AI Karen Analytics Dashboard, including metrics collection, real-time
monitoring, user behavior analysis, and dashboard management.
"""

import asyncio
import time
import random
from datetime import datetime, timedelta

# Run with: PYTHONPATH=src python demo_analytics_dashboard.py

from ai_karen_engine.services.analytics_service import (
    AnalyticsService,
    MetricType,
    AlertLevel,
    UserInteractionEvent
)
from ai_karen_engine.services.analytics_dashboard import (
    AnalyticsDashboard,
    DashboardConfig,
    DashboardWidget,
    ChartType,
    TimeRange,
    AggregationType,
    AnalyticsQuery
)


async def demo_analytics_dashboard():
    """Demonstrate analytics dashboard functionality"""
    print("🚀 AI Karen Analytics Dashboard Demo")
    print("=" * 50)
    
    # Initialize services
    print("\n1. Initializing Analytics Services...")
    analytics_service = AnalyticsService()
    dashboard = AnalyticsDashboard(analytics_service)
    
    print("✅ Analytics Service initialized")
    print("✅ Analytics Dashboard initialized")
    
    # Generate sample metrics
    print("\n2. Generating Sample Metrics...")
    await generate_sample_metrics(analytics_service)
    print("✅ Sample metrics generated")
    
    # Create a sample dashboard
    print("\n3. Creating Sample Dashboard...")
    dashboard_config = create_sample_dashboard()
    dashboard_id = dashboard.create_dashboard(dashboard_config)
    print(f"✅ Dashboard created with ID: {dashboard_id}")
    
    # Execute analytics queries
    print("\n4. Executing Analytics Queries...")
    await demo_analytics_queries(dashboard)
    
    # Demonstrate real-time metrics
    print("\n5. Demonstrating Real-time Metrics...")
    await demo_realtime_metrics(dashboard, analytics_service)
    
    # Generate user behavior insights
    print("\n6. Generating User Behavior Insights...")
    await demo_user_insights(dashboard, analytics_service)
    
    # Show system health summary
    print("\n7. System Health Summary...")
    await demo_system_health(dashboard)
    
    # Dashboard templates
    print("\n8. Available Dashboard Templates...")
    demo_dashboard_templates(dashboard)
    
    # Cleanup
    print("\n9. Cleanup...")
    await dashboard.shutdown()
    analytics_service.shutdown()
    print("✅ Services shutdown complete")
    
    print("\n🎉 Analytics Dashboard Demo Complete!")


async def generate_sample_metrics(analytics_service: AnalyticsService):
    """Generate sample metrics for demonstration"""
    
    # System metrics
    for i in range(20):
        # CPU usage
        cpu_usage = random.uniform(20, 80)
        analytics_service.set_gauge("system.cpu.percent", cpu_usage)
        
        # Memory usage
        memory_usage = random.uniform(40, 90)
        analytics_service.set_gauge("system.memory.percent", memory_usage)
        
        # Disk usage
        disk_usage = random.uniform(30, 70)
        analytics_service.set_gauge("system.disk.percent", disk_usage)
        
        # Request counts
        analytics_service.increment_counter("api.requests.total", random.randint(1, 10))
        analytics_service.increment_counter("api.requests.success", random.randint(1, 8))
        analytics_service.increment_counter("api.requests.error", random.randint(0, 2))
        
        # Response times
        response_time = random.uniform(50, 500)
        analytics_service.record_timer("api.response_time", response_time)
        
        # Performance metrics
        analytics_service.record_performance(
            service_name="ai_orchestrator",
            operation="process_flow",
            duration_ms=random.uniform(100, 1000),
            success=random.choice([True, True, True, False])  # 75% success rate
        )
        
        analytics_service.record_performance(
            service_name="memory_service",
            operation="query_memories",
            duration_ms=random.uniform(50, 300),
            success=random.choice([True, True, True, True, False])  # 80% success rate
        )
        
        # User events
        user_events = ["login", "logout", "page_view", "click", "search", "download"]
        for _ in range(random.randint(1, 5)):
            analytics_service.track_user_event(
                user_id=f"user_{random.randint(1, 100)}",
                event_type=random.choice(user_events),
                event_data={"timestamp": datetime.now().isoformat()},
                session_id=f"session_{random.randint(1, 20)}"
            )
        
        # Small delay to spread metrics over time
        await asyncio.sleep(0.1)
    
    print(f"  📊 Generated metrics for system monitoring")
    print(f"  👥 Generated user interaction events")
    print(f"  ⚡ Generated performance metrics")


def create_sample_dashboard() -> DashboardConfig:
    """Create a sample dashboard configuration"""
    
    widgets = [
        DashboardWidget(
            id="cpu_usage",
            title="CPU Usage",
            description="System CPU utilization over time",
            chart_type=ChartType.LINE,
            metric_name="system.cpu.percent",
            time_range=TimeRange.LAST_HOUR,
            aggregation=AggregationType.AVERAGE,
            position={"x": 0, "y": 0, "width": 6, "height": 4}
        ),
        DashboardWidget(
            id="memory_usage",
            title="Memory Usage",
            description="System memory utilization over time",
            chart_type=ChartType.AREA,
            metric_name="system.memory.percent",
            time_range=TimeRange.LAST_HOUR,
            aggregation=AggregationType.AVERAGE,
            position={"x": 6, "y": 0, "width": 6, "height": 4}
        ),
        DashboardWidget(
            id="api_requests",
            title="API Requests",
            description="Total API requests count",
            chart_type=ChartType.BAR,
            metric_name="api.requests.total",
            time_range=TimeRange.LAST_24_HOURS,
            aggregation=AggregationType.SUM,
            position={"x": 0, "y": 4, "width": 4, "height": 4}
        ),
        DashboardWidget(
            id="response_times",
            title="Response Times",
            description="API response time distribution",
            chart_type=ChartType.LINE,
            metric_name="api.response_time",
            time_range=TimeRange.LAST_HOUR,
            aggregation=AggregationType.PERCENTILE,
            position={"x": 4, "y": 4, "width": 8, "height": 4}
        )
    ]
    
    return DashboardConfig(
        id="demo_dashboard",
        name="Demo System Dashboard",
        description="Comprehensive system monitoring dashboard",
        widgets=widgets,
        layout={"columns": 12, "rows": 8},
        permissions=["admin", "operator"]
    )


async def demo_analytics_queries(dashboard: AnalyticsDashboard):
    """Demonstrate analytics query execution"""
    
    queries = [
        AnalyticsQuery(
            metric_name="system.cpu.percent",
            time_range=TimeRange.LAST_HOUR,
            aggregation=AggregationType.AVERAGE
        ),
        AnalyticsQuery(
            metric_name="api.requests.total",
            time_range=TimeRange.LAST_24_HOURS,
            aggregation=AggregationType.SUM
        ),
        AnalyticsQuery(
            metric_name="api.response_time",
            time_range=TimeRange.LAST_HOUR,
            aggregation=AggregationType.PERCENTILE,
            percentile=95.0
        )
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"  🔍 Executing query {i}: {query.metric_name}")
        result = await dashboard.execute_query(query)
        
        print(f"    ⏱️  Execution time: {result.execution_time_ms:.2f}ms")
        print(f"    📈 Data points: {len(result.data[0].data_points) if result.data else 0}")
        print(f"    📊 Summary: {result.summary}")
        print()


async def demo_realtime_metrics(dashboard: AnalyticsDashboard, analytics_service: AnalyticsService):
    """Demonstrate real-time metrics processing"""
    
    print("  🔄 Starting real-time metrics processing...")
    await dashboard.start_realtime_updates()
    
    # Subscribe to CPU metrics
    cpu_updates = []
    
    def cpu_callback(metric):
        cpu_updates.append(metric.value)
        print(f"    📊 Real-time CPU update: {metric.value:.1f}%")
    
    dashboard.subscribe_to_metric("system.cpu.percent", cpu_callback)
    
    # Generate some real-time metrics
    print("  📡 Generating real-time metrics...")
    for i in range(5):
        cpu_value = random.uniform(30, 70)
        analytics_service.set_gauge("system.cpu.percent", cpu_value)
        await asyncio.sleep(1)
    
    # Wait a bit for processing
    await asyncio.sleep(2)
    
    print(f"  ✅ Received {len(cpu_updates)} real-time updates")
    
    # Cleanup
    dashboard.unsubscribe_from_metric("system.cpu.percent", cpu_callback)
    await dashboard.stop_realtime_updates()


async def demo_user_insights(dashboard: AnalyticsDashboard, analytics_service: AnalyticsService):
    """Demonstrate user behavior insights generation"""
    
    # Generate additional user events for better insights
    user_events = ["login", "logout", "page_view", "click", "search", "download", "upload", "share"]
    
    for _ in range(50):
        analytics_service.track_user_event(
            user_id=f"user_{random.randint(1, 20)}",
            event_type=random.choice(user_events),
            event_data={
                "page": f"/page_{random.randint(1, 10)}",
                "duration": random.randint(10, 300)
            },
            session_id=f"session_{random.randint(1, 10)}"
        )
    
    print("  🧠 Analyzing user behavior patterns...")
    insights = await dashboard.get_user_insights(TimeRange.LAST_24_HOURS)
    
    print(f"  💡 Generated {len(insights)} insights:")
    for insight in insights:
        print(f"    🔍 {insight.insight_type}: {insight.title}")
        print(f"      📝 {insight.description}")
        print(f"      🎯 Confidence: {insight.confidence:.1%}")
        if insight.recommendations:
            print(f"      💡 Recommendations:")
            for rec in insight.recommendations:
                print(f"        • {rec}")
        print()


async def demo_system_health(dashboard: AnalyticsDashboard):
    """Demonstrate system health summary"""
    
    print("  🏥 Generating system health summary...")
    health_summary = await dashboard.get_system_health_summary()
    
    print(f"  🎯 Overall Status: {health_summary.overall_status.value}")
    print(f"  🚨 Active Alerts: {health_summary.active_alerts}")
    print(f"  ⚠️  Critical Alerts: {health_summary.critical_alerts}")
    print(f"  ⏱️  Uptime: {health_summary.uptime_percentage:.1f}%")
    
    print("  📊 System Metrics:")
    for metric, value in health_summary.system_metrics.items():
        print(f"    • {metric}: {value:.1f}%")
    
    print("  🔧 Component Status:")
    for component, status in health_summary.component_statuses.items():
        status_emoji = "✅" if status == "healthy" else "⚠️" if status == "degraded" else "❌"
        print(f"    {status_emoji} {component}: {status.value}")
    
    print("  ⚡ Performance Summary:")
    for service, stats in health_summary.performance_summary.items():
        if stats:
            print(f"    • {service}: {stats.get('total_requests', 0)} requests, "
                  f"{stats.get('success_rate', 0):.1%} success rate")


def demo_dashboard_templates(dashboard: AnalyticsDashboard):
    """Demonstrate dashboard templates"""
    
    print("  📋 Available dashboard templates:")
    templates = dashboard.get_dashboard_templates()
    
    for template in templates:
        print(f"    📊 {template.name}")
        print(f"      📝 {template.description}")
        print(f"      🔧 Widgets: {len(template.widgets)}")
        
        for widget in template.widgets[:2]:  # Show first 2 widgets
            print(f"        • {widget.title} ({widget.chart_type.value})")
        
        if len(template.widgets) > 2:
            print(f"        • ... and {len(template.widgets) - 2} more")
        print()
    
    print("  📈 Available metrics:")
    metrics = dashboard.get_available_metrics()
    for metric in metrics[:5]:  # Show first 5 metrics
        print(f"    • {metric}")
    if len(metrics) > 5:
        print(f"    • ... and {len(metrics) - 5} more")


if __name__ == "__main__":
    # Run the demo
    asyncio.run(demo_analytics_dashboard())