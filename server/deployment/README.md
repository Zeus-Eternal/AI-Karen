# Authentication System Deployment Tools

This directory contains tools for deploying and managing the extension authentication system with zero downtime and comprehensive monitoring.

## Components

### 1. Database Migrations (`migration_runner.py`)

Handles database schema changes for authentication tables.

**Features:**
- Automatic migration discovery and execution
- Rollback capabilities
- Migration status tracking
- Checksum validation

**Usage:**
```bash
# Run all pending migrations
python migration_runner.py migrate

# Check migration status
python migration_runner.py status

# Rollback specific migration
python migration_runner.py rollback --target 001_create_auth_tables
```

### 2. Configuration Deployment (`config_deployer.py`)

Manages configuration file deployment with backup and rollback.

**Features:**
- Automatic configuration backup
- Environment-specific configuration
- Validation before deployment
- Rollback to previous configurations

**Usage:**
```bash
# Deploy configuration
python config_deployer.py deploy --config-file auth.json --environment production

# List available backups
python config_deployer.py list-backups

# Rollback to previous configuration
python config_deployer.py rollback --backup-id backup_20241027_143022
```

### 3. Zero-Downtime Updates (`zero_downtime_updater.py`)

Orchestrates service updates without interrupting authentication.

**Features:**
- Health check monitoring during updates
- Automatic rollback on failure
- Rolling service restarts
- Graceful shutdown handling

**Usage:**
```python
from zero_downtime_updater import ZeroDowntimeUpdater

updater = ZeroDowntimeUpdater(config)
updater.add_health_check('auth_service', check_auth_health)

async with updater.update_context('config_update'):
    await updater.update_configuration(config_changes)
```

### 4. Authentication Monitoring (`auth_monitoring.py`)

Monitors authentication system health and sends alerts.

**Features:**
- Real-time metrics collection
- Configurable alert thresholds
- Multiple notification channels (email, webhook, Slack)
- Alert management and acknowledgment

**Usage:**
```python
from auth_monitoring import initialize_auth_monitor

monitor = initialize_auth_monitor(config)
await monitor.start_monitoring()

# Record authentication events
monitor.record_auth_event('auth_attempt', success=True, response_time_ms=250)
```

### 5. Main Deployment Script (`deploy_auth_system.py`)

Orchestrates complete authentication system deployment.

**Features:**
- Full system deployment workflow
- Environment-specific configuration
- Automatic rollback on failure
- Deployment status tracking

**Usage:**
```bash
# Deploy to production
python deploy_auth_system.py deploy --environment production

# Check deployment status
python deploy_auth_system.py status

# Rollback deployment
python deploy_auth_system.py rollback --backup-id backup_20241027_143022
```

## Configuration

### Database Configuration

Configure database connection in `deployment_config.json`:

```json
{
  "database": {
    "host": "localhost",
    "port": 5432,
    "user": "postgres",
    "password": "your_password",
    "database": "kari"
  }
}
```

### Monitoring Configuration

Configure monitoring and alerting:

```json
{
  "monitoring": {
    "enabled": true,
    "success_rate_threshold": 0.95,
    "response_time_threshold_ms": 1000,
    "error_rate_threshold": 0.05,
    "email_alerts": {
      "enabled": true,
      "smtp_host": "smtp.gmail.com",
      "smtp_port": 587,
      "from_address": "alerts@example.com",
      "to_addresses": ["admin@example.com"]
    }
  }
}
```

### Environment-Specific Settings

Configure different settings per environment:

```json
{
  "environments": {
    "development": {
      "jwt_secret_key": "dev-secret-key",
      "token_expiry_minutes": 1440,
      "rate_limiting_enabled": false
    },
    "production": {
      "jwt_secret_key": "secure-production-key",
      "token_expiry_minutes": 60,
      "rate_limiting_enabled": true
    }
  }
}
```

## Deployment Workflow

### 1. Pre-Deployment Checks

- Verify database connectivity
- Check configuration validity
- Ensure backup systems are working
- Validate health check endpoints

### 2. Deployment Steps

1. **Database Migrations**: Apply schema changes
2. **Configuration Deployment**: Update configuration files
3. **Service Updates**: Rolling restart of services
4. **Health Verification**: Ensure all systems are healthy
5. **Monitoring Activation**: Start monitoring and alerting

### 3. Post-Deployment

- Monitor system health
- Verify authentication functionality
- Check alert systems
- Document deployment results

## Rollback Procedures

### Automatic Rollback

The system automatically rolls back if:
- Health checks fail repeatedly
- Deployment exceeds time limits
- Critical errors occur during deployment

### Manual Rollback

```bash
# Rollback configuration
python config_deployer.py rollback --backup-id backup_20241027_143022

# Rollback database migration
python migration_runner.py rollback --target 001_create_auth_tables

# Full system rollback
python deploy_auth_system.py rollback --backup-id backup_20241027_143022
```

## Monitoring and Alerts

### Metrics Tracked

- Authentication success rate
- Average response time
- Error rates
- Token refresh rates
- Permission denial rates

### Alert Conditions

- Success rate below 95%
- Response time above 1000ms
- Error rate above 5%
- High permission denial rates

### Notification Channels

- **Email**: SMTP-based email alerts
- **Webhook**: HTTP POST to custom endpoints
- **Slack**: Slack channel notifications

## Security Considerations

### JWT Secret Keys

- Use strong, unique secret keys for each environment
- Rotate keys regularly
- Store keys securely (environment variables, secrets management)

### Database Security

- Use strong database passwords
- Enable SSL/TLS for database connections
- Restrict database access to authorized hosts

### Configuration Security

- Encrypt sensitive configuration values
- Use secure file permissions
- Audit configuration changes

## Troubleshooting

### Common Issues

1. **Migration Failures**
   - Check database connectivity
   - Verify user permissions
   - Review migration logs

2. **Configuration Deployment Failures**
   - Validate configuration syntax
   - Check file permissions
   - Verify backup directory access

3. **Health Check Failures**
   - Check service status
   - Verify endpoint accessibility
   - Review service logs

4. **Alert System Issues**
   - Verify SMTP/webhook configuration
   - Check network connectivity
   - Review alert handler logs

### Log Files

- Migration logs: `migration_runner.log`
- Deployment logs: `deployment_logs/update_log.json`
- Alert logs: `deployment_logs/auth_alerts.json`
- System logs: Check application log files

## Best Practices

### Deployment

1. Always test in staging environment first
2. Schedule deployments during low-traffic periods
3. Have rollback plan ready
4. Monitor system closely after deployment

### Configuration

1. Use environment-specific configurations
2. Validate configurations before deployment
3. Keep configuration changes minimal
4. Document all configuration changes

### Monitoring

1. Set appropriate alert thresholds
2. Test alert systems regularly
3. Have escalation procedures
4. Review metrics regularly

### Security

1. Rotate JWT secret keys regularly
2. Use strong passwords and keys
3. Enable audit logging
4. Review security logs regularly

## Support

For issues or questions:

1. Check the troubleshooting section
2. Review log files for error details
3. Verify configuration settings
4. Test individual components separately

## Version History

- v1.0.0: Initial deployment tools implementation
- Includes database migrations, configuration deployment, zero-downtime updates, and monitoring