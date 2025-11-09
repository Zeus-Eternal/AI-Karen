# Extension Debugging and Monitoring System

A comprehensive debugging and monitoring system for Kari extensions that provides logging, metrics collection, error tracking, performance profiling, distributed tracing, and alerting capabilities.

## Features

### 🔍 Extension-Specific Logging
- Structured logging with metadata
- Correlation ID tracking across requests
- User and tenant context management
- Multiple log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Log filtering and search capabilities
- Export to JSON/CSV formats

### 📊 Metrics Collection
- Automatic resource usage monitoring (CPU, memory, network, disk)
- Custom metric registration and collection
- Real-time performance metrics
- Metric aggregation and analysis
- Threshold-based alerting
- Export to JSON/CSV/Prometheus formats

### 🚨 Error Tracking and Analysis
- Automatic error recording and classification
- Error pattern detection and analysis
- Stack trace analysis and grouping
- Resolution tracking and suggestions
- Error trend analysis
- Integration with alerting system

### ⚡ Performance Profiling
- Function-level performance profiling
- Memory usage tracking
- CPU usage monitoring
- Call stack analysis
- Performance bottleneck detection
- Profile session management

### 🔗 Distributed Tracing
- Request tracing across extension operations
- Span creation and management
- Performance analysis and bottleneck detection
- Jaeger-compatible trace export
- Sampling rate configuration
- Context propagation

### 🚨 Intelligent Alerting
- Rule-based alert generation
- Multiple notification channels (log, webhook, email)
- Alert deduplication and cooldowns
- Severity-based filtering
- Alert resolution tracking
- Performance impact monitoring

### 📈 Real-Time Dashboard
- Comprehensive monitoring dashboard
- Real-time metrics visualization
- Log streaming and filtering
- Error analysis and patterns
- Performance monitoring
- Health status overview

## Quick Start

### Basic Setup

```python
from src.core.extensions.debugging import ExtensionDebugManager, DebugConfiguration

# Create debug configuration
config = DebugConfiguration(
    logging_enabled=True,
    metrics_enabled=True,
    error_tracking_enabled=True,
    profiling_enabled=True,
    tracing_enabled=True,
    alerting_enabled=True
)

# Create debug manager
debug_manager = ExtensionDebugManager(
    extension_id="my-extension",
    extension_name="My Extension",
    configuration=config
)

# Start debugging
await debug_manager.start()
```

### Logging

```python
# Get logger
logger = debug_manager.get_logger()

# Basic logging
logger.info("Extension started", version="1.0.0")
logger.warning("High memory usage detected", memory_mb=512)
logger.error("API request failed", status_code=500, url="https://api.example.com")

# Context management
with logger.correlation_context("req-123"):
    with logger.user_context("user123", "tenant456"):
        logger.info("Processing user request")

# Structured logging
logger.log_api_request("GET", "https://api.example.com", 200, 150.5)
logger.log_database_query("SELECT", "users", 25.0, 10)
logger.log_plugin_execution("weather", "get_forecast", True, 200.0)
```

### Metrics Collection

```python
# Get metrics collector
metrics = debug_manager.get_metrics_collector()

# Record custom metrics
metrics.record_metric("active_users", 150, "count")
metrics.record_metric("response_time", 250.5, "ms")
metrics.record_metric("cache_hit_rate", 0.85, "ratio")

# Register custom collectors
def get_queue_size():
    return len(my_queue)

metrics.register_custom_collector("queue_size", get_queue_size)

# Record request metrics
metrics.record_request_time(125.0)
metrics.record_error("ValidationError")
```

### Error Tracking

```python
# Get error tracker
error_tracker = debug_manager.get_error_tracker()

# Record errors
error_tracker.record_error(
    error_type="ValidationError",
    error_message="Invalid input data",
    stack_trace=traceback.format_exc(),
    context={"input": "invalid_data"}
)

# Record exceptions
try:
    risky_operation()
except Exception as e:
    error_tracker.record_exception(e, {"operation": "risky_operation"})

# Get error analysis
analysis = error_tracker.get_error_analysis()
print(f"Total errors: {analysis.total_errors}")
print(f"Error rate: {analysis.error_rate}/hour")
```

### Performance Profiling

```python
# Get profiler
profiler = debug_manager.get_profiler()

# Profile functions
@profiler.profile_function
def expensive_operation(data):
    # Process data
    return result

# Profile code blocks
with profiler.profile_block("data_processing"):
    process_large_dataset()

# Start profiling session
session_id = profiler.start_session(
    profile_memory=True,
    profile_cpu=True,
    enable_cprofile=True
)

# ... run operations ...

# Stop and get results
session = profiler.stop_session(session_id)
bottlenecks = profiler.get_bottlenecks()
```

### Distributed Tracing

```python
# Get tracer
tracer = debug_manager.get_tracer()

# Start trace
context = tracer.start_trace("user_request")

# Create spans
with tracer.start_span("validate_input") as span:
    span.set_tag("input_type", "json")
    validate_user_input(data)

with tracer.start_span("process_request") as span:
    span.set_tag("user_id", user_id)
    result = process_request(data)

# Finish trace
tracer.finish_trace(context.trace_id)

# Trace functions
@tracer.trace_function("api_call")
def call_external_api(url):
    return requests.get(url)
```

### Alerting

```python
# Get alert manager
alert_manager = debug_manager.get_alert_manager()

# Create alerts
await alert_manager.create_alert(
    alert_type="high_cpu",
    severity=AlertSeverity.HIGH,
    title="High CPU Usage",
    message="CPU usage is 85% which exceeds threshold",
    metric_name="cpu_percent",
    current_value=85.0,
    threshold_value=80.0
)

# Add notification channels
from src.core.extensions.debugging.alerting import WebhookNotificationChannel

webhook_channel = WebhookNotificationChannel(
    channel_id="slack",
    name="Slack Notifications",
    webhook_url="https://hooks.slack.com/services/...",
    headers={"Content-Type": "application/json"}
)
alert_manager.add_notification_channel(webhook_channel)
```

### Debug Sessions

```python
# Start debug session
session_id = debug_manager.start_debug_session(
    configuration={
        "enable_profiling": True,
        "enable_tracing": True,
        "profile_memory": True
    }
)

# ... run operations to debug ...

# Stop session and get data
session = debug_manager.stop_debug_session(session_id)
print(f"Session duration: {session.duration_seconds}s")
print(f"Collected data: {len(session.collected_data)} components")
```

### Dashboard Integration

```python
from src.core.extensions.debugging.dashboard import ExtensionDebugDashboard

# Create dashboard
dashboard = ExtensionDebugDashboard(debug_manager)

# Get dashboard data
dashboard_data = dashboard.get_dashboard_data()

# Get real-time metrics
realtime_metrics = dashboard.get_real_time_metrics([
    "cpu_percent", "memory_mb", "response_time"
])

# Search logs
log_results = dashboard.search_logs(
    query="error",
    level="error",
    since=datetime.utcnow() - timedelta(hours=1)
)
```

## CLI Usage

The debugging system includes a comprehensive CLI for monitoring and debugging:

```bash
# Start debug manager
python -m src.core.extensions.debugging.cli --extension-id my-ext start

# Show status
python -m src.core.extensions.debugging.cli --extension-id my-ext status

# View logs
python -m src.core.extensions.debugging.cli --extension-id my-ext logs show --level error --limit 50

# Follow logs in real-time
python -m src.core.extensions.debugging.cli --extension-id my-ext logs show --follow

# Show metrics
python -m src.core.extensions.debugging.cli --extension-id my-ext metrics show --hours 2

# Show current resource usage
python -m src.core.extensions.debugging.cli --extension-id my-ext metrics current

# View errors
python -m src.core.extensions.debugging.cli --extension-id my-ext errors show --unresolved

# Show error patterns
python -m src.core.extensions.debugging.cli --extension-id my-ext errors patterns

# View alerts
python -m src.core.extensions.debugging.cli --extension-id my-ext alerts show --severity high

# Resolve alert
python -m src.core.extensions.debugging.cli --extension-id my-ext alerts resolve alert-123 --notes "Fixed by restart"

# Run health check
python -m src.core.extensions.debugging.cli --extension-id my-ext health

# Export data
python -m src.core.extensions.debugging.cli --extension-id my-ext export --format json --output debug-data.json
```

## API Endpoints

The debugging system provides REST API endpoints for integration:

### Debug Manager
- `POST /api/extensions/debugging/managers/{extension_id}/start` - Start debug manager
- `POST /api/extensions/debugging/managers/{extension_id}/stop` - Stop debug manager
- `GET /api/extensions/debugging/managers/{extension_id}/status` - Get status
- `GET /api/extensions/debugging/managers` - List all managers

### Dashboard
- `GET /api/extensions/debugging/dashboard/{extension_id}` - Get dashboard data
- `GET /api/extensions/debugging/dashboard/{extension_id}/overview` - Get overview
- `GET /api/extensions/debugging/dashboard/{extension_id}/metrics` - Get metrics
- `GET /api/extensions/debugging/dashboard/{extension_id}/logs` - Get logs
- `GET /api/extensions/debugging/dashboard/{extension_id}/errors` - Get errors
- `GET /api/extensions/debugging/dashboard/{extension_id}/alerts` - Get alerts

### Real-time
- `POST /api/extensions/debugging/dashboard/{extension_id}/metrics/realtime` - Get real-time metrics
- `GET /api/extensions/debugging/dashboard/{extension_id}/logs/stream` - Stream logs
- `POST /api/extensions/debugging/dashboard/{extension_id}/logs/search` - Search logs

### Sessions
- `POST /api/extensions/debugging/sessions/{extension_id}/start` - Start debug session
- `POST /api/extensions/debugging/sessions/{extension_id}/{session_id}/stop` - Stop session
- `GET /api/extensions/debugging/sessions/{extension_id}` - List sessions

### Health
- `POST /api/extensions/debugging/health/{extension_id}/check` - Run health check
- `GET /api/extensions/debugging/health/{extension_id}` - Get health status

### Alerts
- `GET /api/extensions/debugging/alerts/{extension_id}` - Get alerts
- `POST /api/extensions/debugging/alerts/{extension_id}/{alert_id}/resolve` - Resolve alert
- `GET /api/extensions/debugging/alerts/{extension_id}/statistics` - Get statistics

### Export
- `GET /api/extensions/debugging/export/{extension_id}/logs` - Export logs
- `GET /api/extensions/debugging/export/{extension_id}/metrics` - Export metrics
- `GET /api/extensions/debugging/export/{extension_id}/errors` - Export errors
- `GET /api/extensions/debugging/export/{extension_id}/alerts` - Export alerts
- `GET /api/extensions/debugging/export/{extension_id}/all` - Export all data

## Configuration

### Debug Configuration

```python
config = DebugConfiguration(
    # Component toggles
    logging_enabled=True,
    metrics_enabled=True,
    error_tracking_enabled=True,
    profiling_enabled=False,  # Can impact performance
    tracing_enabled=False,    # Can impact performance
    alerting_enabled=True,
    
    # Collection intervals
    metrics_interval=30.0,           # seconds
    health_check_interval=60.0,      # seconds
    
    # Storage limits
    max_log_entries=10000,
    max_metrics=50000,
    max_errors=1000,
    max_traces=1000,
    
    # Performance settings
    sampling_rate=1.0,               # 0.0 to 1.0
    profiling_overhead_limit=5.0     # max 5% overhead
)
```

### Alerting Configuration

```python
from src.core.extensions.debugging.alerting import AlertingConfiguration

alerting_config = AlertingConfiguration(
    enabled=True,
    default_cooldown_minutes=5,
    max_alerts_per_hour=100,
    auto_resolve_after_hours=24,
    notification_channels=["log", "webhook"],
    severity_filters={
        "webhook": [AlertSeverity.HIGH, AlertSeverity.CRITICAL]
    }
)
```

## Performance Considerations

### Overhead Monitoring
The debugging system monitors its own performance impact:
- Tracks debug overhead in milliseconds
- Automatically adjusts sampling rates if overhead exceeds limits
- Provides performance recommendations

### Best Practices
1. **Production Settings**: Disable profiling and tracing in production unless needed
2. **Sampling**: Use sampling rates < 1.0 for high-traffic extensions
3. **Storage Limits**: Configure appropriate limits based on available memory
4. **Alert Thresholds**: Set reasonable thresholds to avoid alert fatigue

### Memory Management
- Automatic cleanup of old data based on retention policies
- Circular buffers for metrics and logs to prevent memory growth
- Configurable storage limits for all components

## Integration with Extension System

The debugging system integrates seamlessly with the extension architecture:

```python
from src.core.extensions.base import BaseExtension
from src.core.extensions.debugging import ExtensionDebugManager

class MyExtension(BaseExtension):
    def __init__(self, manifest, context):
        super().__init__(manifest, context)
        
        # Initialize debugging
        self.debug_manager = ExtensionDebugManager(
            self.manifest.name,
            self.manifest.display_name
        )
        
        # Get components
        self.logger = self.debug_manager.get_logger()
        self.metrics = self.debug_manager.get_metrics_collector()
        self.profiler = self.debug_manager.get_profiler()
    
    async def initialize(self):
        await self.debug_manager.start()
        self.logger.info("Extension initialized")
    
    async def shutdown(self):
        self.logger.info("Extension shutting down")
        await self.debug_manager.stop()
    
    @self.profiler.profile_function
    async def process_request(self, request):
        with self.logger.correlation_context():
            self.logger.info("Processing request", request_id=request.id)
            
            try:
                result = await self._handle_request(request)
                self.metrics.record_request_time(request.processing_time)
                return result
            except Exception as e:
                self.error_tracker.record_exception(e)
                raise
```

## Testing

Run the test suite:

```bash
# Run all tests
python -m pytest src/core/extensions/debugging/test_debugging.py

# Run specific test class
python -m pytest src/core/extensions/debugging/test_debugging.py::TestExtensionLogger

# Run with coverage
python -m pytest src/core/extensions/debugging/test_debugging.py --cov=src.core.extensions.debugging
```

## Contributing

When contributing to the debugging system:

1. **Add Tests**: All new features must include comprehensive tests
2. **Performance**: Consider performance impact of new features
3. **Documentation**: Update this README and add docstrings
4. **Backwards Compatibility**: Maintain API compatibility when possible

## Troubleshooting

### Common Issues

**High Memory Usage**
- Reduce storage limits in configuration
- Increase cleanup intervals
- Check for memory leaks in custom collectors

**Performance Impact**
- Disable profiling and tracing in production
- Reduce sampling rates
- Monitor debug overhead metrics

**Missing Data**
- Check component enablement in configuration
- Verify debug manager is started
- Check for errors in debug manager logs

**Alert Fatigue**
- Adjust alert thresholds
- Implement alert cooldowns
- Use severity-based filtering

### Debug the Debugger

The debugging system includes self-monitoring:

```python
# Check debug manager health
health = await debug_manager.run_diagnostics()
print(f"Debug system health: {health.overall_status}")

# Monitor debug overhead
summary = debug_manager.get_debug_summary()
print(f"Debug overhead: {summary['debug_overhead_ms']}ms")

# Check component status
for component in summary['enabled_components']:
    print(f"{component}: enabled")
```