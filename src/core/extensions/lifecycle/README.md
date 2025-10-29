# Extension Lifecycle Management

The Extension Lifecycle Management system provides comprehensive lifecycle management for extensions including health monitoring, backup and restore, migration management, and automatic recovery.

## Features

### 🏥 Health Monitoring
- Real-time health monitoring of all extensions
- Configurable health checks (CPU, memory, response time, error rate)
- Custom health check support
- Automatic alerting and recovery triggers
- Health score calculation and trending

### 💾 Backup & Restore
- Full, incremental, and configuration-only backups
- Automated backup scheduling
- Point-in-time snapshots
- Backup integrity verification
- Cross-extension restore capabilities

### 🔄 Migration Management
- Safe extension updates with rollback capabilities
- Pre-migration backup creation
- Step-by-step migration execution
- Automatic rollback on failure
- Migration verification and validation

### 🚑 Recovery Management
- Automatic failure detection and recovery
- Multiple recovery strategies (conservative, auto, aggressive)
- Progressive recovery escalation
- Recovery history tracking
- Manual recovery triggers

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                Extension Lifecycle Manager                  │
│                    (Main Orchestrator)                      │
└─────────────────────────────────────────────────────────────┘
                              │
    ┌─────────────────────────┼─────────────────────────┐
    │                         │                         │
┌───▼────┐              ┌────▼─────┐              ┌────▼─────┐
│ Health │              │ Backup   │              │Migration │
│Monitor │              │ Manager  │              │ Manager  │
└────────┘              └──────────┘              └──────────┘
                              │
                        ┌─────▼──────┐
                        │ Recovery   │
                        │ Manager    │
                        └────────────┘
```

## Components

### ExtensionLifecycleManager
Main orchestrator that coordinates all lifecycle operations.

```python
from src.core.extensions.lifecycle import ExtensionLifecycleManager

# Initialize
lifecycle_manager = ExtensionLifecycleManager(
    extension_manager=extension_manager,
    version_manager=version_manager,
    db_session=db_session,
    backup_root=Path("data/backups"),
    enable_auto_recovery=True
)

# Start lifecycle management
await lifecycle_manager.start()
```

### ExtensionHealthMonitor
Monitors extension health and triggers recovery actions.

```python
# Get health status
health = await lifecycle_manager.get_extension_health("my_extension")
print(f"Status: {health.status}")
print(f"CPU Usage: {health.cpu_usage}%")
print(f"Memory Usage: {health.memory_usage}MB")
print(f"Health Score: {health.health_score}")
```

### ExtensionBackupManager
Handles backup and restore operations.

```python
# Create backup
backup = await lifecycle_manager.create_backup(
    "my_extension",
    backup_type="full",
    description="Pre-update backup"
)

# Restore backup
success = await lifecycle_manager.restore_backup(backup.backup_id)
```

### ExtensionMigrationManager
Manages extension updates and migrations.

```python
# Migrate extension
migration = await lifecycle_manager.migrate_extension(
    "my_extension",
    target_version="2.0.0",
    create_backup=True
)

# Check migration status
status = await lifecycle_manager.get_migration_status("my_extension")
print(f"Migration Status: {status.status}")
```

### ExtensionRecoveryManager
Handles extension recovery operations.

```python
# Recover failed extension
success = await lifecycle_manager.recover_extension(
    "my_extension",
    strategy="auto"
)

# Get recovery history
history = await lifecycle_manager.get_recovery_history("my_extension")
```

## Configuration

### Global Configuration
```python
from src.core.extensions.lifecycle.config import LifecycleConfig

config = LifecycleConfig(
    enabled=True,
    health_check=HealthCheckConfig(
        check_interval_seconds=60,
        cpu_critical_threshold=90.0,
        memory_critical_mb=512.0
    ),
    backup=BackupConfig(
        auto_backup_enabled=True,
        auto_backup_interval_hours=24,
        max_backups_per_extension=10
    ),
    recovery=RecoveryConfig(
        auto_recovery_enabled=True,
        default_strategy="auto",
        max_recovery_attempts=3
    )
)
```

### Extension-Specific Configuration
```python
from src.core.extensions.lifecycle.config import ExtensionSpecificConfig

critical_config = ExtensionSpecificConfig(
    extension_name="critical_extension",
    critical_extension=True,
    health_check=HealthCheckConfig(
        check_interval_seconds=30,  # More frequent checks
        failure_threshold=2         # Lower threshold
    )
)
```

## API Endpoints

### Health Monitoring
- `GET /api/extensions/lifecycle/health` - Get all extension health
- `GET /api/extensions/lifecycle/health/{extension_name}` - Get specific extension health
- `POST /api/extensions/lifecycle/health/{extension_name}/config` - Configure health monitoring

### Backup Management
- `POST /api/extensions/lifecycle/backup` - Create backup
- `POST /api/extensions/lifecycle/backup/restore` - Restore backup
- `GET /api/extensions/lifecycle/backup` - List backups
- `DELETE /api/extensions/lifecycle/backup/{backup_id}` - Delete backup

### Migration Management
- `POST /api/extensions/lifecycle/migration` - Start migration
- `POST /api/extensions/lifecycle/migration/{migration_id}/rollback` - Rollback migration
- `GET /api/extensions/lifecycle/migration/{extension_name}` - Get migration status
- `GET /api/extensions/lifecycle/migration` - List migrations

### Recovery Management
- `POST /api/extensions/lifecycle/recovery` - Trigger recovery
- `GET /api/extensions/lifecycle/recovery/{extension_name}` - Get recovery history

### Overview
- `GET /api/extensions/lifecycle/overview/{extension_name}` - Extension overview
- `GET /api/extensions/lifecycle/overview` - System overview

## CLI Usage

### Health Monitoring
```bash
# Check extension health
kari lifecycle health my_extension

# Get system status
kari lifecycle status
```

### Backup Operations
```bash
# Create backup
kari lifecycle backup my_extension --type full --description "Pre-update backup"

# List backups
kari lifecycle list-backups --extension my_extension

# Restore backup
kari lifecycle restore backup_id_123 --confirm
```

### Migration Operations
```bash
# Migrate extension
kari lifecycle migrate my_extension 2.0.0 --backup --confirm

# Rollback migration
kari lifecycle rollback migration_id_456 --confirm
```

### Recovery Operations
```bash
# Recover extension
kari lifecycle recover my_extension --strategy auto

# View events
kari lifecycle events --extension my_extension --limit 20
```

## Database Schema

The lifecycle management system uses several database tables:

- `extension_health` - Current health status
- `extension_backups` - Backup metadata
- `extension_migrations` - Migration records
- `extension_snapshots` - Lightweight snapshots
- `extension_lifecycle_events` - Event history
- `extension_recovery_actions` - Recovery action definitions
- `extension_health_configs` - Health check configurations

## Recovery Strategies

### Auto Strategy
Progressive recovery with escalating actions:
1. Restart extension
2. Clear cache
3. Restore from backup
4. Rollback to previous version
5. Disable extension

### Conservative Strategy
Minimal intervention:
1. Restart extension
2. Clear cache

### Aggressive Strategy
All available recovery actions:
1. Restart extension
2. Clear cache
3. Restore from backup
4. Rollback to previous version
5. Reinstall extension

## Best Practices

### Health Monitoring
- Set appropriate thresholds for your extensions
- Use custom health checks for business logic validation
- Monitor health trends, not just current status
- Configure alerts for critical extensions

### Backup Management
- Enable automatic backups for production extensions
- Test restore procedures regularly
- Keep multiple backup generations
- Monitor backup storage usage

### Migration Management
- Always create backups before migrations
- Test migrations in staging environments
- Have rollback plans ready
- Monitor extensions after migration

### Recovery Management
- Use conservative strategy for critical extensions
- Monitor recovery patterns to identify systemic issues
- Document custom recovery procedures
- Test recovery procedures regularly

## Monitoring and Alerting

### Health Metrics
- Extension uptime and availability
- Resource usage trends
- Error rates and response times
- Recovery success rates

### Alerts
- Extension health degradation
- Backup failures
- Migration issues
- Recovery failures

### Dashboards
- System-wide health overview
- Extension-specific metrics
- Backup and migration status
- Recovery history and trends

## Troubleshooting

### Common Issues

#### Extension Won't Start After Recovery
1. Check extension logs for errors
2. Verify configuration integrity
3. Check resource availability
4. Try restoring from backup

#### Backup Restore Fails
1. Verify backup integrity
2. Check disk space
3. Ensure extension is stopped
4. Check file permissions

#### Migration Stuck
1. Check migration logs
2. Verify network connectivity
3. Check resource availability
4. Consider manual rollback

#### Health Checks Failing
1. Verify extension is running
2. Check resource thresholds
3. Review custom health checks
4. Check network connectivity

### Debug Mode
Enable debug logging for detailed troubleshooting:

```python
import logging
logging.getLogger('src.core.extensions.lifecycle').setLevel(logging.DEBUG)
```

## Performance Considerations

- Health check frequency vs. system load
- Backup size and compression settings
- Migration timeout settings
- Recovery cooldown periods
- Database query optimization

## Security Considerations

- Backup encryption at rest
- Access control for lifecycle operations
- Audit logging for all operations
- Secure backup storage locations
- Permission validation for destructive operations