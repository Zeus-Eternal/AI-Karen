# Extension Monitoring and Alerting System

This package provides comprehensive monitoring and alerting capabilities for the extension authentication and service health system.

## Overview

The monitoring system consists of four main components:

1. **Metrics Dashboard** - Collects and displays authentication, service health, and performance metrics
2. **Alerting System** - Advanced alerting with escalation, multiple notification channels, and customizable rules
3. **Performance Monitor** - Detailed API performance monitoring with resource usage tracking
4. **Integration Layer** - Easy integration with existing extension infrastructure

## Features

### Metrics Collection
- Authentication success/failure rates
- Token refresh statistics
- Service health monitoring
- API response times and error rates
- System resource usage (CPU, memory, disk, network)

### Alerting Capabilities
- Customizable alert rules with thresholds
- Multiple notification channels (Email, Slack, Discord, Webhook)
- Alert escalation with configurable levels
- Cooldown periods to prevent alert spam
- Alert history and statistics

### Performance Monitoring
- Request-level performance tracking
- Response time percentiles (P50, P90, P95, P99)
- Endpoint-specific metrics
- Resource usage alerts
- Performance trend analysis

### Dashboard and API
- Real-time monitoring dashboard
- REST API for metrics access
- Prometheus metrics export
- Interactive web interface

## Quick Start

### 1. Initialize Monitoring

```python
from server.monitoring import initialize_monitoring

# Basic initialization
await initialize_monitoring()

# With custom configuration
config = {
    'notifications': {
        'slack': {
            'webhook_url': 'https://hooks.slack.com/...',
            'channel': '#alerts'
        },
        'email': {
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587,
            'username': 'alerts@example.com',
            'password': 'app_password',
            'from_email': 'alerts@example.com',
            'to_emails': ['admin@example.com']
        }
    },
    'monitoring': {
        'dashboard_check_interval': 30,
        'resource_check_interval': 30,
        'alert_check_interval': 15
    }
}

await initialize_monitoring(config)
```

### 2. Record Metrics

```python
from server.monitoring import (
    record_auth_success,
    record_auth_failure,
    record_api_request,
    record_service_health
)

# Record authentication events
record_auth_success(response_time=0.15, user_id="user123")
record_auth_failure(response_time=0.25, error_type="invalid_token", user_id="user456")

# Record API requests
record_api_request("/api/extensions/", "GET", 200, 0.12)
record_api_request("/api/extensions/background-tasks/", "POST", 403, 0.08)

# Record service health
record_service_health("extension_manager", "healthy", response_time=0.05)
record_service_health("database", "degraded", response_time=0.30)
```

### 3. Access Dashboard

The monitoring dashboard is available at `/api/monitoring/dashboard` and provides:

- Real-time metrics visualization
- Active alerts display
- Performance trends
- Service health status

### 4. Configure Alerts

```python
from server.monitoring.alerting_system import extension_alerting, AlertRule, NotificationChannel

# Add custom alert rule
custom_alert = AlertRule(
    id="custom_auth_alert",
    name="Custom Authentication Alert",
    description="Authentication failure rate exceeds 20%",
    condition="auth_failure_rate > 20",
    threshold=20.0,
    severity="error",
    notification_channels=[NotificationChannel.SLACK, NotificationChannel.EMAIL],
    escalation_enabled=True,
    escalation_interval_minutes=5
)

extension_alerting.add_alert_rule(custom_alert)
```

## API Endpoints

### Dashboard Data
- `GET /api/monitoring/dashboard` - Complete dashboard data
- `GET /api/monitoring/authentication/metrics` - Authentication metrics
- `GET /api/monitoring/health/metrics` - Service health metrics
- `GET /api/monitoring/performance/metrics` - API performance metrics

### Alerts
- `GET /api/monitoring/alerts/active` - Active alerts
- `GET /api/monitoring/alerts/history` - Alert history
- `POST /api/monitoring/alerts` - Create alert rule
- `DELETE /api/monitoring/alerts/{alert_id}` - Delete alert rule

### Status and Export
- `GET /api/monitoring/status` - Monitoring system status
- `GET /api/monitoring/export/prometheus` - Prometheus metrics

## Configuration

### Notification Channels

#### Slack
```python
{
    'slack': {
        'webhook_url': 'https://hooks.slack.com/services/...',
        'channel': '#alerts'
    }
}
```

#### Email
```python
{
    'email': {
        'smtp_server': 'smtp.gmail.com',
        'smtp_port': 587,
        'username': 'alerts@example.com',
        'password': 'app_password',
        'from_email': 'alerts@example.com',
        'to_emails': ['admin@example.com', 'team@example.com']
    }
}
```

#### Discord
```python
{
    'discord': {
        'webhook_url': 'https://discord.com/api/webhooks/...'
    }
}
```

#### Webhook
```python
{
    'webhook': {
        'url': 'https://your-webhook-endpoint.com/alerts',
        'headers': {
            'Authorization': 'Bearer your-token',
            'Content-Type': 'application/json'
        }
    }
}
```

### Alert Rules

Alert rules support the following conditions:
- `auth_failure_rate > threshold` - Authentication failure rate percentage
- `service_health_percentage < threshold` - Service health percentage
- `api_error_rate > threshold` - API error rate percentage
- `avg_response_time > threshold` - Average response time in milliseconds

### Performance Thresholds

Default performance thresholds can be customized:
```python
from server.monitoring.performance_monitor import extension_performance_monitor

extension_performance_monitor.response_time_threshold = 3.0  # seconds
extension_performance_monitor.error_rate_threshold = 10.0   # percentage
extension_performance_monitor.cpu_threshold = 90.0          # percentage
extension_performance_monitor.memory_threshold = 90.0       # percentage
```

## Integration with FastAPI

### Add Monitoring Middleware

```python
from fastapi import FastAPI
from server.monitoring.dashboard_api import monitoring_router, MonitoringMiddleware

app = FastAPI()

# Add monitoring middleware
app.add_middleware(MonitoringMiddleware)

# Include monitoring routes
app.include_router(monitoring_router)
```

### Manual Request Tracking

```python
from server.monitoring.performance_monitor import extension_performance_monitor

# Using context manager
async def my_endpoint():
    async with extension_performance_monitor.measure_request("/api/my-endpoint", "GET"):
        # Your endpoint logic here
        return {"status": "success"}

# Manual recording
def record_request_manually():
    start_time = time.time()
    try:
        # Your logic here
        status_code = 200
    except Exception:
        status_code = 500
    finally:
        response_time = time.time() - start_time
        extension_performance_monitor.record_request(
            "/api/my-endpoint", "GET", response_time, status_code
        )
```

## Frontend Integration

The React dashboard component is available at:
`ui_launchers/web_ui/src/components/monitoring/ExtensionMonitoringDashboard.tsx`

```tsx
import ExtensionMonitoringDashboard from '@/components/monitoring/ExtensionMonitoringDashboard';

function MonitoringPage() {
  return (
    <div>
      <h1>Extension Monitoring</h1>
      <ExtensionMonitoringDashboard />
    </div>
  );
}
```

## Troubleshooting

### Common Issues

1. **Monitoring not starting**
   - Check if `initialize_monitoring()` was called
   - Verify configuration is valid
   - Check logs for initialization errors

2. **Alerts not firing**
   - Verify alert rules are enabled
   - Check threshold values
   - Ensure notification channels are configured

3. **Missing metrics**
   - Confirm metrics are being recorded
   - Check if monitoring middleware is installed
   - Verify API endpoints are being called

4. **Performance issues**
   - Adjust retention periods
   - Reduce monitoring intervals
   - Check system resource usage

### Logging

The monitoring system uses Python's logging module. Enable debug logging:

```python
import logging
logging.getLogger('server.monitoring').setLevel(logging.DEBUG)
```

### Health Checks

Check monitoring system health:

```python
from server.monitoring import get_monitoring_status

status = get_monitoring_status()
print(f"Monitoring active: {status['initialized']}")
print(f"Active alerts: {status['alerting']['active_alerts']}")
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend Dashboard                       │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │         React Monitoring Dashboard                      │ │
│  │  - Real-time metrics display                           │ │
│  │  - Alert management                                     │ │
│  │  - Performance charts                                   │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │ HTTP API
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Monitoring API                           │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              FastAPI Routes                             │ │
│  │  - Dashboard endpoints                                  │ │
│  │  - Metrics API                                          │ │
│  │  - Alert management                                     │ │
│  │  - Prometheus export                                    │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  Monitoring Core                            │
│  ┌─────────────────┐  ┌─────────────────┐  ┌───────────────┐ │
│  │ Metrics         │  │ Alerting        │  │ Performance   │ │
│  │ Dashboard       │  │ System          │  │ Monitor       │ │
│  │ - Auth metrics  │  │ - Alert rules   │  │ - API metrics │ │
│  │ - Health data   │  │ - Notifications │  │ - Resources   │ │
│  │ - API stats     │  │ - Escalation    │  │ - Trends      │ │
│  └─────────────────┘  └─────────────────┘  └───────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                 Notification Channels                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │   Email     │  │   Slack     │  │  Webhook/Discord        │ │
│  │ - SMTP      │  │ - Webhooks  │  │  - HTTP POST            │ │
│  │ - Templates │  │ - Channels  │  │  - Custom payloads      │ │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

This monitoring system provides comprehensive visibility into extension authentication, service health, and performance, enabling proactive issue detection and resolution.