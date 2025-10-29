# Extension Performance Optimization System

This module provides comprehensive performance optimization and scaling capabilities for the Kari extension system. It implements caching, lazy loading, resource optimization, horizontal scaling, and performance monitoring to ensure optimal system performance.

## Features

### 🚀 Performance Optimization
- **Extension Caching**: Intelligent caching of extension manifests, classes, and data
- **Lazy Loading**: Multiple loading strategies (eager, lazy, on-demand, background)
- **Resource Optimization**: Memory, CPU, and I/O optimization with automatic cleanup
- **Horizontal Scaling**: Automatic scaling based on metrics and load balancing

### 📊 Monitoring & Analytics
- **Real-time Monitoring**: Continuous performance metrics collection
- **Performance Alerts**: Configurable thresholds with severity levels
- **Performance Scoring**: Automated scoring for performance, reliability, and efficiency
- **Optimization Recommendations**: AI-driven suggestions for performance improvements

### ⚙️ Configuration & Management
- **Flexible Configuration**: JSON-based configuration with environment variable support
- **CLI Tools**: Command-line interface for management and monitoring
- **Integration APIs**: Easy integration with existing extension manager

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                Performance Integration                       │
│              (Unified Interface)                            │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────┬─────────────┬─────────────┬─────────────────────┐
│    Cache    │    Lazy     │  Resource   │     Scaling         │
│   Manager   │   Loader    │ Optimizer   │    Manager          │
└─────────────┴─────────────┴─────────────┴─────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│              Performance Monitor                            │
│           (Metrics & Alerting)                             │
└─────────────────────────────────────────────────────────────┘
```

## Components

### 1. Cache Manager (`cache_manager.py`)

Provides intelligent caching for extension loading and data:

```python
from src.core.extensions.performance import ExtensionCacheManager

cache_manager = ExtensionCacheManager(
    max_size_mb=256,
    max_entries=1000,
    default_ttl=3600
)

await cache_manager.start()

# Cache extension data
await cache_manager.set("extension:manifest", manifest_data)
cached_data = await cache_manager.get("extension:manifest")

# Get cache statistics
stats = await cache_manager.get_stats()
print(f"Hit rate: {stats.hit_rate:.2%}")
```

**Features:**
- LRU eviction policy
- TTL-based expiration
- Size-based limits
- Cache warming
- Performance metrics

### 2. Lazy Loader (`lazy_loader.py`)

Implements multiple loading strategies for optimal startup performance:

```python
from src.core.extensions.performance import ExtensionLazyLoader, LoadingStrategy

lazy_loader = ExtensionLazyLoader(
    extension_root=Path("extensions"),
    cache_manager=cache_manager,
    max_concurrent_loads=5
)

# Configure loading strategy
await lazy_loader.configure_loading_strategy(
    extension_name="analytics",
    strategy=LoadingStrategy.LAZY,
    priority=100,
    dependencies=["auth", "database"]
)

# Load extensions with optimization
loaded_extensions = await lazy_loader.load_extensions(manifests)
```

**Loading Strategies:**
- **Eager**: Load immediately during startup
- **Lazy**: Load on first access (creates proxy)
- **On-Demand**: Load only when explicitly requested
- **Background**: Load in background after startup

### 3. Resource Optimizer (`resource_optimizer.py`)

Monitors and optimizes resource usage:

```python
from src.core.extensions.performance import ExtensionResourceOptimizer, ResourceLimits

optimizer = ExtensionResourceOptimizer(
    monitoring_interval=30.0,
    memory_threshold=0.8,
    cpu_threshold=0.7
)

await optimizer.start()

# Register extension for monitoring
limits = ResourceLimits(max_memory_mb=512, max_cpu_percent=50)
await optimizer.register_extension("my_extension", process_id, limits)

# Optimize extension resources
await optimizer.optimize_extension_memory("my_extension")
await optimizer.optimize_extension_cpu("my_extension")

# Get optimization recommendations
recommendations = await optimizer.get_optimization_recommendations()
```

**Optimization Features:**
- Real-time resource monitoring
- Automatic garbage collection
- CPU priority adjustment
- Resource limit enforcement
- Optimization recommendations

### 4. Scaling Manager (`scaling_manager.py`)

Provides horizontal scaling capabilities:

```python
from src.core.extensions.performance import (
    ExtensionScalingManager, ScalingRule, ScalingTrigger, ScalingStrategy
)

scaling_manager = ExtensionScalingManager(resource_optimizer)
await scaling_manager.start()

# Configure scaling rules
rule = ScalingRule(
    trigger=ScalingTrigger.CPU_USAGE,
    threshold_up=70,
    threshold_down=30,
    min_instances=1,
    max_instances=5,
    scale_up_step=1,
    scale_down_step=1
)

await scaling_manager.configure_scaling(
    extension_name="analytics",
    strategy=ScalingStrategy.AUTO,
    rules=[rule]
)

# Manual scaling
await scaling_manager.scale_extension("analytics", target_instances=3)

# Get instance for load balancing
instance = await scaling_manager.get_instance_for_request("analytics")
```

**Scaling Features:**
- Automatic scaling based on metrics
- Load balancing (round-robin)
- Health monitoring
- Custom scaling rules
- Manual scaling support

### 5. Performance Monitor (`performance_monitor.py`)

Comprehensive performance monitoring and alerting:

```python
from src.core.extensions.performance import ExtensionPerformanceMonitor

monitor = ExtensionPerformanceMonitor(
    cache_manager=cache_manager,
    resource_optimizer=optimizer,
    scaling_manager=scaling_manager
)

await monitor.start()

# Configure performance thresholds
thresholds = {
    'cpu_usage_percent': 80,
    'memory_usage_mb': 512,
    'average_response_time_ms': 1000
}
await monitor.configure_thresholds("my_extension", thresholds)

# Get performance summary
summary = await monitor.get_performance_summary("my_extension", hours=24)
print(f"Performance score: {summary.performance_score}/100")

# Get active alerts
alerts = await monitor.get_active_alerts()
for alert in alerts:
    print(f"[{alert.severity}] {alert.extension_name}: {alert.message}")
```

**Monitoring Features:**
- Real-time metrics collection
- Performance scoring (0-100)
- Configurable alerting
- Historical analysis
- Custom metric collectors
- Performance recommendations

## Configuration

### Basic Configuration

```json
{
  "cache": {
    "max_size_mb": 256,
    "max_entries": 1000,
    "default_ttl": 3600,
    "cleanup_interval": 300
  },
  "lazy_loading": {
    "max_concurrent_loads": 5,
    "default_strategy": "lazy",
    "loading_timeout": 300
  },
  "resource_optimization": {
    "monitoring_interval": 30,
    "optimization_interval": 300,
    "memory_threshold": 0.8,
    "cpu_threshold": 0.7,
    "enable_auto_optimization": true
  },
  "scaling": {
    "enable_scaling": true,
    "metrics_collection_interval": 30,
    "scaling_evaluation_interval": 60,
    "default_min_instances": 1,
    "default_max_instances": 5
  },
  "monitoring": {
    "enable_monitoring": true,
    "monitoring_interval": 30,
    "alert_check_interval": 60,
    "metrics_retention_hours": 168,
    "enable_alerting": true
  }
}
```

### Extension-Specific Configuration

```json
{
  "extensions": {
    "analytics": {
      "loading_strategy": "lazy",
      "loading_priority": 100,
      "max_memory_mb": 1024,
      "max_cpu_percent": 70,
      "enable_scaling": true,
      "scaling_strategy": "auto",
      "min_instances": 1,
      "max_instances": 3,
      "scaling_rules": [
        {
          "trigger": "cpu_usage",
          "threshold_up": 70,
          "threshold_down": 30,
          "cooldown_seconds": 300,
          "scale_up_step": 1,
          "scale_down_step": 1
        }
      ],
      "performance_thresholds": {
        "cpu_usage_percent": 80,
        "memory_usage_mb": 800,
        "average_response_time_ms": 2000
      }
    }
  }
}
```

## Usage Examples

### Basic Integration

```python
from pathlib import Path
from src.core.extensions.performance import PerformanceIntegration

# Create performance integration
integration = PerformanceIntegration(
    extension_root=Path("extensions"),
    cache_size_mb=256,
    enable_scaling=True,
    enable_monitoring=True
)

await integration.start()

# Configure extension performance
await integration.configure_extension_performance(
    extension_name="analytics",
    manifest=analytics_manifest,
    config={
        'loading_strategy': 'lazy',
        'resource_limits': {'max_memory_mb': 512},
        'scaling': {
            'enabled': True,
            'strategy': 'auto',
            'rules': [cpu_scaling_rule]
        }
    }
)

# Load extensions with optimization
loaded_extensions = await integration.load_extensions_optimized(manifests)

# Get performance status
status = await integration.get_performance_status()
print(f"Cache hit rate: {status['cache_stats'].hit_rate:.2%}")
```

### Integration with Extension Manager

```python
from src.core.extensions.performance import integrate_with_extension_manager

# Integrate with existing extension manager
await integrate_with_extension_manager(extension_manager, performance_integration)

# Extension manager now uses optimized loading automatically
```

## CLI Usage

The performance system includes a comprehensive CLI tool:

```bash
# Show cache statistics
python -m src.core.extensions.performance.cli cache stats

# Monitor system resources
python -m src.core.extensions.performance.cli resources monitor

# Scale an extension
python -m src.core.extensions.performance.cli scaling scale analytics 3

# Show performance summary
python -m src.core.extensions.performance.cli monitor summary analytics --hours 24

# Show active alerts
python -m src.core.extensions.performance.cli monitor alerts

# Configure extension performance
python -m src.core.extensions.performance.cli config extension analytics \
  --loading-strategy lazy --max-memory-mb 512 --enable-scaling

# Run performance benchmark
python -m src.core.extensions.performance.cli benchmark /path/to/extensions
```

## Performance Metrics

The system tracks comprehensive performance metrics:

### System Metrics
- CPU usage percentage
- Memory usage (MB and percentage)
- Disk I/O (read/write MB/s)
- Network I/O (sent/received MB/s)
- File handles and thread counts

### Extension Metrics
- Load time and initialization time
- Runtime resource usage
- Request rate and response times
- Error rates and cache performance
- Scaling events and instance counts

### Performance Scores
- **Performance Score** (0-100): Based on resource efficiency
- **Reliability Score** (0-100): Based on error rates and uptime
- **Efficiency Score** (0-100): Based on resource usage vs performance

## Best Practices

### 1. Loading Strategy Selection

- **Security/Auth extensions**: Use `eager` loading
- **UI-heavy extensions**: Use `lazy` loading
- **Background services**: Use `background` loading
- **Optional features**: Use `on_demand` loading

### 2. Resource Limits

Set appropriate resource limits based on extension type:

```python
# Lightweight extension
ResourceLimits(max_memory_mb=128, max_cpu_percent=20)

# Analytics extension
ResourceLimits(max_memory_mb=1024, max_cpu_percent=70)

# Background processing
ResourceLimits(max_memory_mb=512, max_cpu_percent=50, max_threads=10)
```

### 3. Scaling Configuration

Configure scaling based on workload patterns:

```python
# CPU-intensive workload
ScalingRule(
    trigger=ScalingTrigger.CPU_USAGE,
    threshold_up=70,
    threshold_down=30,
    cooldown_seconds=300
)

# Queue-based workload
ScalingRule(
    trigger=ScalingTrigger.QUEUE_LENGTH,
    threshold_up=10,
    threshold_down=2,
    cooldown_seconds=180
)
```

### 4. Monitoring Thresholds

Set appropriate monitoring thresholds:

```python
# Conservative thresholds
thresholds = {
    'cpu_usage_percent': 60,
    'memory_usage_mb': 400,
    'average_response_time_ms': 500,
    'error_rate_percent': 1.0
}

# Performance-focused thresholds
thresholds = {
    'cpu_usage_percent': 80,
    'memory_usage_mb': 800,
    'average_response_time_ms': 1000,
    'error_rate_percent': 5.0
}
```

## Testing

Run the comprehensive test suite:

```bash
# Run all performance tests
python -m pytest src/core/extensions/performance/test_performance.py -v

# Run specific test categories
python -m pytest src/core/extensions/performance/test_performance.py::TestExtensionCacheManager -v
python -m pytest src/core/extensions/performance/test_performance.py::TestExtensionLazyLoader -v
python -m pytest src/core/extensions/performance/test_performance.py::TestExtensionResourceOptimizer -v

# Run integration tests
python -m pytest src/core/extensions/performance/test_performance.py::TestPerformanceIntegrationE2E -v
```

## Troubleshooting

### Common Issues

1. **High Memory Usage**
   - Check cache size configuration
   - Review resource limits
   - Enable automatic optimization
   - Monitor for memory leaks

2. **Slow Extension Loading**
   - Use appropriate loading strategies
   - Enable cache warming
   - Increase concurrent load limit
   - Check dependency chains

3. **Scaling Issues**
   - Verify scaling is enabled
   - Check scaling rules and thresholds
   - Monitor resource usage patterns
   - Review cooldown periods

4. **Performance Alerts**
   - Review threshold configurations
   - Check system resource availability
   - Analyze performance trends
   - Implement recommendations

### Debug Mode

Enable verbose logging for debugging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Or use CLI with verbose flag
python -m src.core.extensions.performance.cli --verbose cache stats
```

## Contributing

When contributing to the performance system:

1. **Add Tests**: Include comprehensive tests for new features
2. **Update Documentation**: Keep README and docstrings current
3. **Performance Impact**: Consider the performance impact of changes
4. **Backward Compatibility**: Maintain API compatibility
5. **Configuration**: Add appropriate configuration options

## License

This performance optimization system is part of the Kari AI platform and follows the same licensing terms.