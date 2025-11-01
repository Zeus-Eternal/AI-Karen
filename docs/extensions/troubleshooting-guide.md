# Extension Troubleshooting Guide

## Overview

This guide helps you diagnose and resolve common issues with Kari extensions. Whether you're a user experiencing problems or a developer debugging your extension, this guide provides systematic approaches to identify and fix issues.

## Quick Diagnostics

### Extension Status Check

Start with basic status information:

```bash
# Check if extension is installed and enabled
kari extension status my-extension

# List all extensions and their status
kari extension list --verbose

# Check system health
kari system health --extensions
```

### Log Analysis

Review extension logs for errors:

```bash
# View recent logs
kari extension logs my-extension --tail 100

# Follow logs in real-time
kari extension logs my-extension --follow

# Filter by log level
kari extension logs my-extension --level ERROR

# Search for specific patterns
kari extension logs my-extension --grep "database"
```

### Resource Usage

Check resource consumption:

```bash
# Monitor extension resource usage
kari extension monitor my-extension

# System resource overview
kari system resources --by-extension

# Performance metrics
kari extension metrics my-extension --last 1h
```

## Common Issues and Solutions

### Installation Problems

#### Extension Won't Install

**Symptoms:**
- Installation fails with error messages
- Package download issues
- Dependency conflicts

**Diagnosis:**
```bash
# Check installation logs
kari extension install my-extension --verbose

# Verify package integrity
kari extension verify my-extension-1.0.0.tar.gz

# Check system requirements
kari extension check-requirements my-extension
```

**Solutions:**

1. **Insufficient Permissions**
```bash
# Run with appropriate permissions
sudo kari extension install my-extension

# Or install in user mode
kari extension install my-extension --user
```

2. **Dependency Conflicts**
```bash
# Check dependency tree
kari extension deps my-extension --tree

# Force install (use with caution)
kari extension install my-extension --force

# Install specific version
kari extension install my-extension==1.2.0
```

3. **Network Issues**
```bash
# Use different mirror
kari extension install my-extension --index-url https://alt-mirror.kari.ai

# Install from local file
kari extension install ./my-extension-1.0.0.tar.gz

# Configure proxy
export HTTPS_PROXY=http://proxy.company.com:8080
kari extension install my-extension
```

#### Corrupted Installation

**Symptoms:**
- Extension partially installed
- Missing files or components
- Inconsistent behavior

**Solutions:**
```bash
# Clean reinstall
kari extension uninstall my-extension --clean
kari extension install my-extension

# Repair installation
kari extension repair my-extension

# Verify installation integrity
kari extension verify my-extension --installed
```

### Runtime Issues

#### Extension Won't Start

**Symptoms:**
- Extension shows as installed but not running
- Startup errors in logs
- Missing functionality

**Diagnosis:**
```bash
# Check startup logs
kari extension logs my-extension --since startup

# Validate configuration
kari extension config my-extension --validate

# Check dependencies
kari extension deps my-extension --check
```

**Solutions:**

1. **Configuration Issues**
```bash
# Reset to default configuration
kari extension config my-extension --reset

# Validate configuration schema
kari extension config my-extension --validate --verbose

# Edit configuration interactively
kari extension config my-extension --edit
```

2. **Missing Dependencies**
```bash
# Install missing dependencies
kari extension deps my-extension --install

# Update dependencies
kari extension deps my-extension --update

# Check Python dependencies
pip install -r extensions/my-extension/requirements.txt
```

3. **Permission Problems**
```bash
# Check extension permissions
kari extension permissions my-extension

# Grant required permissions
kari extension permissions my-extension --grant data.read,data.write

# Review permission conflicts
kari extension permissions --conflicts
```

#### Extension Crashes

**Symptoms:**
- Extension stops unexpectedly
- Error messages in logs
- Functionality becomes unavailable

**Diagnosis:**
```bash
# Check crash logs
kari extension logs my-extension --level ERROR --since "1 hour ago"

# Monitor for crashes
kari extension monitor my-extension --crashes

# Generate crash report
kari extension crash-report my-extension
```

**Solutions:**

1. **Memory Issues**
```bash
# Check memory usage
kari extension monitor my-extension --memory

# Increase memory limit
kari extension config my-extension --set memory_limit=1024MB

# Enable memory profiling
kari extension profile my-extension --memory
```

2. **Resource Exhaustion**
```bash
# Check resource limits
kari extension limits my-extension

# Adjust CPU limits
kari extension limits my-extension --cpu 2.0

# Monitor resource usage
kari extension monitor my-extension --resources
```

3. **Code Issues**
```bash
# Enable debug mode
kari extension debug my-extension --enable

# Run in safe mode
kari extension start my-extension --safe-mode

# Check for code errors
kari extension lint my-extension
```

### Performance Issues

#### Slow Extension Response

**Symptoms:**
- API endpoints respond slowly
- UI components lag
- Background tasks take too long

**Diagnosis:**
```bash
# Profile extension performance
kari extension profile my-extension --duration 5m

# Check database queries
kari extension profile my-extension --database

# Monitor API response times
kari extension monitor my-extension --api-times
```

**Solutions:**

1. **Database Optimization**
```bash
# Analyze slow queries
kari extension db my-extension --slow-queries

# Add database indexes
kari extension db my-extension --optimize

# Check connection pool
kari extension db my-extension --connections
```

2. **Caching Issues**
```bash
# Clear extension cache
kari extension cache my-extension --clear

# Configure cache settings
kari extension config my-extension --set cache.ttl=3600

# Monitor cache hit rates
kari extension cache my-extension --stats
```

3. **Resource Optimization**
```bash
# Enable performance monitoring
kari extension monitor my-extension --performance

# Optimize background tasks
kari extension tasks my-extension --optimize

# Review resource allocation
kari extension resources my-extension --optimize
```

#### High Resource Usage

**Symptoms:**
- Extension consuming excessive CPU/memory
- System slowdown
- Resource limit warnings

**Solutions:**
```bash
# Set resource limits
kari extension limits my-extension --memory 512MB --cpu 1.0

# Enable resource monitoring
kari extension monitor my-extension --resources --alert

# Profile resource usage
kari extension profile my-extension --resources --duration 10m
```

### Configuration Issues

#### Invalid Configuration

**Symptoms:**
- Extension fails to start
- Configuration validation errors
- Missing required settings

**Solutions:**
```bash
# Validate configuration
kari extension config my-extension --validate

# Show configuration schema
kari extension config my-extension --schema

# Reset to defaults
kari extension config my-extension --reset

# Interactive configuration
kari extension config my-extension --wizard
```

#### Configuration Not Applied

**Symptoms:**
- Changes don't take effect
- Extension uses old settings
- Configuration appears correct

**Solutions:**
```bash
# Restart extension
kari extension restart my-extension

# Force configuration reload
kari extension config my-extension --reload

# Check configuration file permissions
ls -la ~/.kari/extensions/my-extension/config.json
```

### API and Integration Issues

#### API Endpoints Not Working

**Symptoms:**
- 404 errors for extension endpoints
- Authentication failures
- CORS issues

**Diagnosis:**
```bash
# List registered endpoints
kari extension endpoints my-extension

# Test endpoint connectivity
curl -X GET http://localhost:8000/api/my-extension/health

# Check API logs
kari extension logs my-extension --api
```

**Solutions:**

1. **Endpoint Registration**
```bash
# Verify endpoint registration
kari extension endpoints my-extension --verify

# Re-register endpoints
kari extension restart my-extension

# Check for conflicts
kari extension endpoints --conflicts
```

2. **Authentication Issues**
```bash
# Check authentication configuration
kari extension auth my-extension --status

# Test with authentication
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/my-extension/data

# Review authentication logs
kari extension logs my-extension --auth
```

3. **CORS Configuration**
```bash
# Configure CORS settings
kari extension config my-extension --set cors.origins="*"

# Check CORS headers
curl -H "Origin: http://localhost:3000" -I http://localhost:8000/api/my-extension/data
```

#### External API Integration Issues

**Symptoms:**
- External API calls failing
- Timeout errors
- Authentication problems with external services

**Solutions:**
```bash
# Test external connectivity
kari extension test my-extension --external-apis

# Check API credentials
kari extension config my-extension --check-credentials

# Monitor external API calls
kari extension monitor my-extension --external-apis
```

### UI Integration Issues

#### UI Components Not Loading

**Symptoms:**
- Extension UI not visible
- JavaScript errors
- Component registration failures

**Diagnosis:**
```bash
# Check UI registration
kari extension ui my-extension --status

# Verify component files
kari extension ui my-extension --verify

# Check browser console for errors
# (Open browser developer tools)
```

**Solutions:**

1. **Component Registration**
```bash
# Re-register UI components
kari extension ui my-extension --register

# Check component manifest
kari extension ui my-extension --manifest

# Verify component permissions
kari extension permissions my-extension --ui
```

2. **Build Issues**
```bash
# Rebuild UI components
cd extensions/my-extension/ui
npm run build

# Check build logs
npm run build --verbose

# Install UI dependencies
npm install
```

3. **Asset Loading**
```bash
# Check asset paths
kari extension ui my-extension --assets

# Verify static file serving
curl http://localhost:8000/extensions/my-extension/static/app.js

# Clear browser cache
# (Use browser developer tools)
```

### Data and Storage Issues

#### Data Not Persisting

**Symptoms:**
- Data disappears after restart
- Save operations appear to succeed but data is lost
- Inconsistent data state

**Diagnosis:**
```bash
# Check data storage status
kari extension data my-extension --status

# Verify database connectivity
kari extension data my-extension --test-connection

# Check data permissions
kari extension data my-extension --permissions
```

**Solutions:**

1. **Database Configuration**
```bash
# Check database configuration
kari extension config my-extension --database

# Test database connection
kari extension data my-extension --ping

# Repair database
kari extension data my-extension --repair
```

2. **Transaction Issues**
```bash
# Check for uncommitted transactions
kari extension data my-extension --transactions

# Force transaction commit
kari extension data my-extension --commit

# Enable transaction logging
kari extension config my-extension --set database.log_transactions=true
```

#### Data Corruption

**Symptoms:**
- Invalid data returned
- Database errors
- Inconsistent query results

**Solutions:**
```bash
# Check data integrity
kari extension data my-extension --integrity-check

# Backup current data
kari extension data my-extension --backup

# Restore from backup
kari extension data my-extension --restore backup-2023-12-01.sql

# Rebuild indexes
kari extension data my-extension --reindex
```

## Advanced Troubleshooting

### Debug Mode

Enable comprehensive debugging:

```bash
# Enable debug mode
kari extension debug my-extension --enable

# Set debug level
kari extension debug my-extension --level verbose

# Enable specific debug categories
kari extension debug my-extension --categories api,database,ui
```

### Performance Profiling

Profile extension performance:

```bash
# CPU profiling
kari extension profile my-extension --cpu --duration 5m

# Memory profiling
kari extension profile my-extension --memory --duration 5m

# Database profiling
kari extension profile my-extension --database --duration 5m

# Generate performance report
kari extension profile my-extension --report
```

### Network Diagnostics

Diagnose network-related issues:

```bash
# Test network connectivity
kari extension network my-extension --test

# Monitor network traffic
kari extension network my-extension --monitor

# Check DNS resolution
kari extension network my-extension --dns

# Test proxy configuration
kari extension network my-extension --proxy
```

### Security Diagnostics

Check for security-related issues:

```bash
# Security scan
kari extension security my-extension --scan

# Check permissions
kari extension security my-extension --permissions

# Audit security events
kari extension security my-extension --audit

# Vulnerability check
kari extension security my-extension --vulnerabilities
```

## Diagnostic Tools

### Built-in Tools

**Extension Inspector**
```bash
# Comprehensive extension analysis
kari extension inspect my-extension

# Generate diagnostic report
kari extension inspect my-extension --report

# Export diagnostic data
kari extension inspect my-extension --export diagnostics.json
```

**Health Checker**
```bash
# Run health checks
kari extension health my-extension

# Continuous health monitoring
kari extension health my-extension --monitor

# Health check configuration
kari extension health my-extension --configure
```

### External Tools

**System Monitoring**
```bash
# Monitor system resources
htop
iotop
nethogs

# Check disk usage
df -h
du -sh ~/.kari/extensions/

# Monitor network connections
netstat -tulpn | grep kari
```

**Database Tools**
```bash
# PostgreSQL diagnostics
psql -h localhost -U kari -d kari_extensions -c "\dt"

# Redis diagnostics
redis-cli info
redis-cli monitor

# SQLite diagnostics
sqlite3 ~/.kari/extensions/my-extension/data.db ".schema"
```

## Recovery Procedures

### Extension Recovery

**Safe Mode Recovery**
```bash
# Start in safe mode
kari extension start my-extension --safe-mode

# Disable problematic features
kari extension config my-extension --disable-features background_tasks,ui

# Minimal configuration
kari extension config my-extension --minimal
```

**Data Recovery**
```bash
# List available backups
kari extension backup my-extension --list

# Restore from backup
kari extension backup my-extension --restore 2023-12-01-10-30

# Partial data recovery
kari extension data my-extension --recover --table users
```

**Configuration Recovery**
```bash
# Backup current configuration
kari extension config my-extension --backup

# Restore default configuration
kari extension config my-extension --restore-defaults

# Restore from backup
kari extension config my-extension --restore config-backup-2023-12-01.json
```

### System Recovery

**Extension System Reset**
```bash
# Stop all extensions
kari extension stop --all

# Clear extension cache
kari extension cache --clear-all

# Restart extension system
kari extension system restart
```

**Database Recovery**
```bash
# Backup all extension data
kari extension backup --all

# Reset extension database
kari extension database --reset

# Restore from backups
kari extension restore --all
```

## Prevention Strategies

### Monitoring Setup

**Automated Monitoring**
```bash
# Enable system monitoring
kari extension monitor --enable-all

# Configure alerts
kari extension alerts --configure

# Set up health checks
kari extension health --schedule "*/5 * * * *"
```

**Log Management**
```bash
# Configure log rotation
kari extension logs --rotate-size 100MB --keep 30

# Enable structured logging
kari extension config --global --set logging.structured=true

# Set up log aggregation
kari extension logs --forward-to syslog://log-server:514
```

### Backup Strategy

**Automated Backups**
```bash
# Schedule daily backups
kari extension backup --schedule "0 2 * * *"

# Configure backup retention
kari extension backup --retention 30d

# Test backup restoration
kari extension backup --test-restore
```

**Configuration Versioning**
```bash
# Enable configuration versioning
kari extension config --versioning enable

# Automatic configuration backups
kari extension config --auto-backup before-change

# Configuration change tracking
kari extension config --track-changes
```

### Update Management

**Staged Updates**
```bash
# Test updates in staging
kari extension update my-extension --staging

# Validate update compatibility
kari extension update my-extension --validate

# Rollback capability
kari extension update my-extension --enable-rollback
```

## Getting Help

### Self-Service Resources

**Documentation**
- Extension Development Guide
- API Reference
- Security Guide
- Best Practices

**Community Resources**
- Community Forums: https://community.kari.ai
- Stack Overflow: Tag `kari-extensions`
- GitHub Discussions: https://github.com/kari-ai/extensions/discussions
- Discord Server: https://discord.gg/kari-ai

### Professional Support

**Support Channels**
- Email: support@kari.ai
- Live Chat: Available in Kari dashboard
- Phone: Enterprise customers only
- Video Call: Scheduled support sessions

**Support Levels**
- **Community**: Free community support
- **Professional**: Priority email support
- **Enterprise**: Dedicated support team
- **Premium**: 24/7 support with SLA

### Bug Reports

**Reporting Issues**
1. Check existing issues: https://github.com/kari-ai/extensions/issues
2. Gather diagnostic information
3. Create detailed bug report
4. Include reproduction steps
5. Attach relevant logs and configurations

**Bug Report Template**
```markdown
## Bug Description
Brief description of the issue

## Environment
- Kari Version: 
- Extension Version: 
- Operating System: 
- Python Version: 

## Steps to Reproduce
1. Step one
2. Step two
3. Step three

## Expected Behavior
What should happen

## Actual Behavior
What actually happens

## Logs and Diagnostics
```
Paste relevant logs here
```

## Additional Context
Any other relevant information
```

---

*This troubleshooting guide is regularly updated. For the latest information and additional resources, visit the [online documentation](https://docs.kari.ai/extensions/troubleshooting).*