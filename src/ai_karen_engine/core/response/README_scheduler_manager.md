# Autonomous Training Scheduler Manager

The Scheduler Manager provides comprehensive cron-based scheduling for autonomous learning cycles in the Response Core orchestrator. It enables automated training schedules with configurable quality thresholds, safety controls, and multi-channel notification systems.

## Overview

The scheduler system consists of several key components:

- **SchedulerManager**: Main orchestrator for managing training schedules
- **NotificationManager**: Handles multi-channel notifications (email, webhook, memory, logs)
- **ResourceMonitor**: Monitors system resources for safety controls
- **Safety Controls**: Configurable limits and thresholds for safe autonomous operation
- **Schedule Persistence**: Automatic saving/loading of schedules across restarts

## Key Features

### 🕒 Cron-Based Scheduling
- Full cron expression support for flexible timing
- Timezone-aware scheduling
- Automatic next-run calculation
- Schedule pause/resume functionality

### 🛡️ Safety Controls
- Resource usage monitoring (memory, CPU)
- Consecutive failure tracking with cooldown periods
- Configurable quality and validation thresholds
- Automatic rollback on model degradation
- Three safety levels: Strict, Moderate, Permissive

### 📢 Multi-Channel Notifications
- **Log**: Structured logging with correlation IDs
- **Email**: SMTP-based email notifications with TLS support
- **Webhook**: HTTP POST notifications to external systems
- **Memory**: Storage in the memory system for UI display

### 💾 Persistence & Recovery
- Automatic schedule persistence to JSON storage
- Recovery of schedules after system restarts
- Schedule history and statistics tracking
- Backup and restore capabilities

## Quick Start

### Basic Usage

```python
from ai_karen_engine.core.response.scheduler_manager import (
    SchedulerManager, AutonomousConfig, NotificationConfig, SafetyControls
)

# Initialize scheduler
scheduler = SchedulerManager(
    autonomous_learner=your_learner,
    memory_service=your_memory_service
)

# Create configuration
config = AutonomousConfig(
    enabled=True,
    training_schedule="0 2 * * *",  # Daily at 2 AM
    min_data_threshold=100,
    quality_threshold=0.7,
    validation_threshold=0.85
)

# Create schedule
schedule_id = scheduler.create_training_schedule(
    tenant_id="your-tenant",
    name="Daily Training",
    cron_expression="0 2 * * *",
    config=config,
    description="Daily autonomous training"
)

# Start scheduler
await scheduler.start_scheduler()
```

### Advanced Configuration

```python
# Advanced safety controls
safety_controls = SafetyControls(
    level=SafetyLevel.STRICT,
    min_data_threshold=500,
    max_data_threshold=10000,
    quality_threshold=0.8,
    max_training_time_minutes=60,
    validation_threshold=0.9,
    rollback_on_degradation=True,
    max_memory_usage_mb=2048,
    max_cpu_usage_percent=75.0,
    max_consecutive_failures=2,
    failure_cooldown_hours=24
)

# Multi-channel notifications
notifications = NotificationConfig(
    enabled=True,
    types=[NotificationType.LOG, NotificationType.EMAIL, NotificationType.WEBHOOK],
    email_smtp_host="smtp.gmail.com",
    email_smtp_port=587,
    email_username="your-email@gmail.com",
    email_password="your-app-password",
    email_recipients=["admin@yourcompany.com"],
    webhook_url="https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
    webhook_headers={"Authorization": "Bearer your-token"}
)

# Complete configuration
config = AutonomousConfig(
    enabled=True,
    training_schedule="0 3 * * 0",  # Weekly on Sunday at 3 AM
    timezone="UTC",
    safety_controls=safety_controls,
    notifications=notifications,
    max_training_time=7200,  # 2 hours
    backup_models=True,
    auto_rollback=True
)
```

## API Integration

### REST Endpoints

The scheduler provides comprehensive REST API endpoints:

```python
# Create schedule
POST /api/scheduler/schedules
{
    "tenant_id": "your-tenant",
    "name": "Production Training",
    "cron_expression": "0 2 * * 6",
    "config": { ... },
    "description": "Weekly production training"
}

# List schedules
GET /api/scheduler/schedules?tenant_id=your-tenant

# Get schedule details
GET /api/scheduler/schedules/{schedule_id}

# Update schedule
PUT /api/scheduler/schedules/{schedule_id}
{
    "name": "Updated Name",
    "cron_expression": "0 3 * * 6"
}

# Pause/Resume schedule
POST /api/scheduler/schedules/{schedule_id}/pause
POST /api/scheduler/schedules/{schedule_id}/resume

# Delete schedule
DELETE /api/scheduler/schedules/{schedule_id}

# Scheduler control
POST /api/scheduler/start
POST /api/scheduler/stop
GET /api/scheduler/status
```

### Schedule Management

```python
# List all schedules
schedules = scheduler.list_schedules()

# Get specific schedule status
status = scheduler.get_schedule_status(schedule_id)
print(f"Status: {status['status']}")
print(f"Next run: {status['next_run']}")
print(f"Success rate: {status['successful_runs']}/{status['total_runs']}")

# Pause schedule
scheduler.pause_schedule(schedule_id)

# Resume schedule
scheduler.resume_schedule(schedule_id)

# Update schedule
scheduler.update_schedule(schedule_id, name="New Name")

# Delete schedule
scheduler.delete_schedule(schedule_id)
```

## Cron Expression Guide

### Format
```
minute hour day_of_month month day_of_week
(0-59) (0-23) (1-31) (1-12) (0-7, 0=Sunday)
```

### Common Examples
```bash
0 2 * * *      # Daily at 2:00 AM
0 */6 * * *    # Every 6 hours
30 14 * * 1    # Every Monday at 2:30 PM
0 9 1 * *      # First day of every month at 9:00 AM
0 0 * * 0      # Every Sunday at midnight
15 10 * * 1-5  # Weekdays at 10:15 AM
0 */4 * * *    # Every 4 hours
```

### Special Characters
- `*` - Any value
- `*/n` - Every n units
- `a-b` - Range from a to b
- `a,b,c` - Specific values

## Safety Controls

### Safety Levels

**Strict Mode**
- High quality thresholds (0.9+)
- Low resource limits
- Immediate failure response
- Extensive validation

**Moderate Mode** (Default)
- Balanced thresholds (0.7-0.85)
- Reasonable resource limits
- Moderate failure tolerance
- Standard validation

**Permissive Mode**
- Lower thresholds (0.5-0.7)
- Higher resource limits
- Higher failure tolerance
- Minimal validation

### Resource Monitoring

```python
# Get current resource usage
usage = await scheduler.resource_monitor.get_current_usage()
print(f"Memory: {usage['memory_mb']} MB ({usage['memory_percent']}%)")
print(f"CPU: {usage['cpu_percent']}%")

# Safety checks are automatic
# Training will be skipped if:
# - Memory usage > max_memory_usage_mb
# - CPU usage > max_cpu_usage_percent
# - Consecutive failures > max_consecutive_failures
# - Within failure cooldown period
```

## Notification System

### Email Notifications

```python
notifications = NotificationConfig(
    enabled=True,
    types=[NotificationType.EMAIL],
    email_smtp_host="smtp.gmail.com",
    email_smtp_port=587,
    email_username="your-email@gmail.com",
    email_password="your-app-password",  # Use app password for Gmail
    email_recipients=["admin@company.com", "ops@company.com"],
    email_use_tls=True
)
```

### Webhook Integration

```python
# Slack webhook example
notifications = NotificationConfig(
    enabled=True,
    types=[NotificationType.WEBHOOK],
    webhook_url="https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX",
    webhook_headers={"Content-Type": "application/json"},
    webhook_timeout=30
)

# Custom webhook with authentication
notifications = NotificationConfig(
    enabled=True,
    types=[NotificationType.WEBHOOK],
    webhook_url="https://api.yourcompany.com/webhooks/training",
    webhook_headers={
        "Authorization": "Bearer your-api-token",
        "Content-Type": "application/json"
    }
)
```

### Memory Storage

```python
notifications = NotificationConfig(
    enabled=True,
    types=[NotificationType.MEMORY],
    memory_tenant_id="your-tenant",
    memory_importance_score=8  # High importance for training events
)
```

## Error Handling & Recovery

### Automatic Recovery
- Failed schedules are automatically retried after cooldown
- Resource constraints prevent training during high usage
- Model rollback on validation failures
- Schedule persistence survives system restarts

### Manual Recovery
```python
# Check failed schedules
schedules = scheduler.list_schedules()
failed_schedules = [s for s in schedules if s['consecutive_failures'] > 0]

# Reset failure count
scheduler.update_schedule(schedule_id, consecutive_failures=0)

# Force immediate training (bypasses some safety checks)
result = await autonomous_learner.trigger_learning_cycle(
    tenant_id="your-tenant",
    force_training=True
)
```

## Monitoring & Observability

### Schedule Statistics
```python
status = scheduler.get_schedule_status(schedule_id)
print(f"Total runs: {status['total_runs']}")
print(f"Success rate: {status['successful_runs']}/{status['total_runs']}")
print(f"Consecutive failures: {status['consecutive_failures']}")
print(f"Last result: {status['last_result']}")
```

### System Status
```python
# Overall scheduler status
system_status = {
    "scheduler_running": scheduler.running,
    "total_schedules": len(scheduler.schedules),
    "active_schedules": sum(1 for s in scheduler.schedules.values() 
                           if s.status == ScheduleStatus.ACTIVE),
    "running_tasks": len(scheduler.running_tasks)
}
```

### Logging
All scheduler operations are logged with structured information:
```python
# Log format includes:
# - Correlation IDs for tracking
# - Schedule IDs and names
# - Training results and metrics
# - Error details and stack traces
# - Resource usage information
```

## Best Practices

### Production Deployment
1. **Use appropriate safety levels** - Start with Strict, relax as needed
2. **Configure notifications** - Set up email and webhook alerts
3. **Monitor resources** - Ensure adequate memory and CPU
4. **Schedule wisely** - Avoid peak usage times
5. **Test configurations** - Use test notifications before production

### Schedule Design
1. **Daily training** - `0 2 * * *` (2 AM daily)
2. **Weekly deep training** - `0 3 * * 0` (Sunday 3 AM)
3. **Monthly comprehensive** - `0 4 1 * *` (1st of month 4 AM)
4. **Development frequent** - `0 */6 * * *` (Every 6 hours)

### Safety Configuration
1. **Development** - Permissive mode, frequent training
2. **Staging** - Moderate mode, daily training
3. **Production** - Strict mode, weekly training
4. **High-availability** - Conservative thresholds, extensive monitoring

## Dependencies

### Required
- `asyncio` - Async operation support
- `json` - Schedule persistence
- `pathlib` - File system operations
- `dataclasses` - Configuration models

### Optional
- `croniter` - Full cron expression support (highly recommended)
- `psutil` - System resource monitoring
- `aiohttp` - Webhook notifications
- `smtplib` - Email notifications (built-in)

### Installation
```bash
# Minimal installation
pip install asyncio

# Recommended installation
pip install croniter psutil aiohttp

# Full installation with all features
pip install croniter psutil aiohttp smtplib
```

## Troubleshooting

### Common Issues

**Cron expressions not working**
```bash
# Install croniter
pip install croniter

# Verify expression
from croniter import croniter
print(croniter.is_valid("0 2 * * *"))  # Should return True
```

**Resource monitoring unavailable**
```bash
# Install psutil
pip install psutil

# Test resource monitoring
import psutil
print(psutil.virtual_memory())
print(psutil.cpu_percent())
```

**Email notifications failing**
- Check SMTP settings and credentials
- Use app passwords for Gmail
- Verify firewall/network access
- Test with simple SMTP client first

**Webhook notifications failing**
- Verify webhook URL is accessible
- Check authentication headers
- Test with curl or Postman first
- Review webhook endpoint logs

### Debug Mode
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Enable detailed logging for scheduler
logger = logging.getLogger('ai_karen_engine.core.response.scheduler_manager')
logger.setLevel(logging.DEBUG)
```

## Examples

See `examples/scheduler_manager_demo.py` for comprehensive usage examples including:
- Basic schedule creation and management
- Advanced safety control configuration
- Multi-channel notification setup
- Cron expression examples
- Error handling and recovery
- Production deployment patterns

## Testing

Run the test suite:
```bash
pytest tests/test_scheduler_manager.py -v
```

The tests cover:
- Schedule creation and management
- Safety control enforcement
- Notification delivery
- Resource monitoring
- Error handling and recovery
- Persistence and recovery
- API endpoint functionality