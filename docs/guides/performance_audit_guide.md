# Performance Audit Engine Guide

The Performance Audit Engine provides comprehensive performance monitoring and analysis capabilities for the AI Karen system. It helps identify bottlenecks, track resource usage, and generate optimization recommendations.

## Features

### 1. Service Discovery
- Automatically discovers running services and processes
- Classifies services by type (essential, optional, background)
- Tracks resource usage per service (CPU, memory, I/O, threads)

### 2. Startup Time Tracking
- Measures initialization time for each service
- Tracks dependency loading during startup
- Identifies slow-starting services and components

### 3. Runtime Performance Monitoring
- Continuous monitoring of system resources
- Real-time metrics collection
- Historical performance data analysis

### 4. Bottleneck Analysis
- Identifies performance bottlenecks automatically
- Categorizes bottlenecks by type (CPU, memory, I/O, startup)
- Calculates severity levels and impact scores

### 5. Optimization Recommendations
- Generates actionable optimization suggestions
- Provides service-specific recommendations
- Suggests architectural improvements

## Quick Start

### Basic Usage

```python
from ai_karen_engine.audit.performance_auditor import (
    get_performance_auditor,
    StartupTimeContext
)
import asyncio

async def main():
    # Get the global auditor instance
    auditor = get_performance_auditor()
    
    # Track service startup time
    with StartupTimeContext('my_service', auditor) as ctx:
        ctx.add_dependency('database')
        ctx.add_dependency('cache')
        # ... service initialization code ...
    
    # Discover running services
    services = await auditor.service_discovery.discover_services()
    print(f"Found {len(services)} services")
    
    # Run startup performance audit
    startup_report = await auditor.audit_startup_performance()
    print(f"Startup time: {startup_report.total_startup_time:.2f}s")
    print(f"Bottlenecks: {len(startup_report.bottlenecks)}")
    
    # Generate optimization recommendations
    recommendations = await auditor.generate_optimization_recommendations()
    for i, rec in enumerate(recommendations[:5], 1):
        print(f"{i}. {rec}")

asyncio.run(main())
```

### Startup Time Tracking

Use the `StartupTimeContext` context manager to track service startup times:

```python
from ai_karen_engine.audit.performance_auditor import StartupTimeContext, get_performance_auditor

auditor = get_performance_auditor()

# Track startup time with context manager
with StartupTimeContext('auth_service', auditor) as ctx:
    # Record dependencies as they're loaded
    ctx.add_dependency('crypto_library')
    ctx.add_dependency('user_database')
    
    # Your service initialization code here
    initialize_auth_service()

# The startup metrics are automatically recorded
metrics = auditor.startup_tracker.startup_times['auth_service']
print(f"Auth service started in {metrics.duration:.2f}s")
```

### Runtime Monitoring

Monitor system performance over time:

```python
async def monitor_performance():
    auditor = get_performance_auditor()
    
    # Run runtime audit for 10 minutes
    runtime_report = await auditor.audit_runtime_performance(duration_minutes=10)
    
    print(f"Monitored {runtime_report.services_monitored} services")
    print(f"Collected {len(runtime_report.runtime_metrics)} metrics")
    
    # Check for runtime bottlenecks
    for bottleneck in runtime_report.bottlenecks:
        print(f"Bottleneck: {bottleneck.service_name} - {bottleneck.description}")
```

### Service Discovery

Discover and analyze running services:

```python
async def analyze_services():
    auditor = get_performance_auditor()
    
    services = await auditor.service_discovery.discover_services()
    
    # Group services by type
    essential = [s for s in services if s.service_type.value == 'essential']
    optional = [s for s in services if s.service_type.value == 'optional']
    background = [s for s in services if s.service_type.value == 'background']
    
    print(f"Essential services: {len(essential)}")
    print(f"Optional services: {len(optional)}")
    print(f"Background services: {len(background)}")
    
    # Show resource usage
    for service in services[:10]:  # Top 10 services
        print(f"{service.name}: {service.memory_usage / (1024*1024):.1f}MB, "
              f"{service.cpu_percent:.1f}% CPU")
```

## Configuration

### Bottleneck Thresholds

You can customize the thresholds used for bottleneck detection:

```python
from ai_karen_engine.audit.performance_auditor import BottleneckAnalyzer

analyzer = BottleneckAnalyzer()

# Customize thresholds
analyzer.thresholds.update({
    'cpu_high': 70.0,        # CPU usage % threshold
    'memory_high': 2 * 1024 * 1024 * 1024,  # 2GB memory threshold
    'startup_slow': 5.0,     # 5 seconds startup threshold
    'io_high': 200 * 1024 * 1024,  # 200MB I/O threshold
})
```

### Audit Log Location

Specify a custom location for audit logs:

```python
from pathlib import Path
from ai_karen_engine.audit.performance_auditor import PerformanceAuditor

# Custom audit log path
audit_path = Path("/var/log/karen/performance_audit.log")
auditor = PerformanceAuditor(audit_log_path=audit_path)
```

## Report Types

### Startup Report

Contains comprehensive startup performance analysis:

- `total_startup_time`: Total time for all services to start
- `services_analyzed`: Number of services analyzed
- `startup_metrics`: Detailed metrics for each service
- `bottlenecks`: Identified startup bottlenecks
- `recommendations`: Optimization suggestions
- `baseline_memory`: Memory usage before startup
- `peak_memory`: Peak memory usage during startup

### Runtime Report

Contains runtime performance analysis:

- `analysis_duration`: How long the monitoring ran
- `services_monitored`: Number of services monitored
- `runtime_metrics`: Collected performance metrics
- `bottlenecks`: Runtime performance bottlenecks
- `resource_trends`: Resource usage trends over time
- `recommendations`: Runtime optimization suggestions

## Bottleneck Types

The auditor identifies several types of bottlenecks:

- **STARTUP_SLOW**: Services that take too long to initialize
- **CPU_INTENSIVE**: Services with high CPU usage
- **MEMORY_LEAK**: Services with excessive memory usage
- **IO_BOUND**: Services with high I/O operations
- **RESOURCE_CONTENTION**: Services competing for resources
- **BLOCKING_OPERATION**: Services blocking the main thread

## Best Practices

### 1. Regular Auditing
Run performance audits regularly to catch regressions:

```python
# Daily startup audit
async def daily_audit():
    auditor = get_performance_auditor()
    report = await auditor.audit_startup_performance()
    
    # Alert if startup time exceeds threshold
    if report.total_startup_time > 30.0:  # 30 seconds
        send_alert(f"Startup time too high: {report.total_startup_time:.2f}s")
```

### 2. Service Classification
Properly classify your services for better optimization:

```python
# In your service initialization
with StartupTimeContext('analytics_service', auditor) as ctx:
    # This should be classified as 'optional' since it's not essential
    ctx.add_dependency('analytics_database')
    initialize_analytics()
```

### 3. Dependency Tracking
Track dependencies to understand startup bottlenecks:

```python
with StartupTimeContext('ml_service', auditor) as ctx:
    ctx.add_dependency('torch')           # Heavy ML framework
    ctx.add_dependency('transformers')    # Large model library
    ctx.add_dependency('model_weights')   # Large model files
    
    # This helps identify which dependencies are slow to load
    load_ml_models()
```

### 4. Monitoring Integration
Integrate with your monitoring system:

```python
async def export_metrics_to_prometheus():
    auditor = get_performance_auditor()
    
    # Get current bottlenecks
    bottlenecks = await auditor.identify_bottlenecks()
    
    # Export to Prometheus/Grafana
    for bottleneck in bottlenecks:
        prometheus_gauge.labels(
            service=bottleneck.service_name,
            type=bottleneck.bottleneck_type.value
        ).set(bottleneck.impact_score)
```

## Troubleshooting

### High Memory Usage
If the auditor detects high memory usage:

1. Check for memory leaks in your services
2. Implement proper cleanup in service destructors
3. Use memory profiling tools like `memory_profiler`
4. Consider implementing memory limits per service

### Slow Startup Times
If services are starting slowly:

1. Implement lazy loading for non-essential components
2. Move heavy initialization to background tasks
3. Cache expensive computations
4. Optimize dependency loading order

### High CPU Usage
If services show high CPU usage:

1. Profile CPU usage to identify hot spots
2. Implement async/await for I/O operations
3. Use multiprocessing for CPU-bound tasks
4. Optimize algorithms and data structures

## Integration with Existing Code

The performance auditor is designed to integrate seamlessly with existing code:

```python
# In your main application startup
from ai_karen_engine.audit.performance_auditor import StartupTimeContext, get_performance_auditor

def main():
    auditor = get_performance_auditor()
    
    # Track overall application startup
    with StartupTimeContext('application', auditor):
        # Track individual service startups
        with StartupTimeContext('database', auditor):
            initialize_database()
        
        with StartupTimeContext('api_server', auditor):
            initialize_api_server()
        
        with StartupTimeContext('background_tasks', auditor):
            initialize_background_tasks()
    
    # Generate startup report
    asyncio.run(generate_startup_report(auditor))

async def generate_startup_report(auditor):
    report = await auditor.audit_startup_performance()
    
    # Log results
    logger.info(f"Application startup completed in {report.total_startup_time:.2f}s")
    
    # Alert on bottlenecks
    for bottleneck in report.bottlenecks:
        if bottleneck.severity in ['HIGH', 'CRITICAL']:
            logger.warning(f"Performance bottleneck: {bottleneck.description}")
```

This guide provides a comprehensive overview of the Performance Audit Engine. For more detailed examples, see the demo scripts in the `examples/` directory.