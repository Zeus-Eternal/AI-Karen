# AI Karen - Monitoring and Maintenance Procedures

This document outlines the monitoring, maintenance, and operational procedures for the production AI Karen system.

## Table of Contents

1. [Monitoring Overview](#monitoring-overview)
2. [Health Monitoring](#health-monitoring)
3. [Performance Monitoring](#performance-monitoring)
4. [Security Monitoring](#security-monitoring)
5. [Log Management](#log-management)
6. [Alerting and Notifications](#alerting-and-notifications)
7. [Maintenance Procedures](#maintenance-procedures)
8. [Backup and Recovery](#backup-and-recovery)
9. [Incident Response](#incident-response)
10. [Capacity Planning](#capacity-planning)

## Monitoring Overview

### Monitoring Stack

- **Application Monitoring**: Custom health checks and metrics
- **System Monitoring**: Prometheus + Grafana
- **Log Aggregation**: ELK Stack (Elasticsearch, Logstash, Kibana)
- **Uptime Monitoring**: External monitoring service
- **Security Monitoring**: Custom security alerts + SIEM

### Key Metrics

#### Application Metrics
- Request rate (requests/second)
- Response time (95th percentile)
- Error rate (4xx/5xx responses)
- Active users
- Chat messages processed
- Model inference time

#### System Metrics
- CPU utilization
- Memory usage
- Disk I/O
- Network I/O
- Database connections
- Cache hit ratio

#### Business Metrics
- User registrations
- Daily/Monthly active users
- Feature usage statistics
- Revenue metrics (if applicable)

## Health Monitoring

### Automated Health Checks

#### Application Health Check Script

```bash
#!/bin/bash
# /opt/ai-karen/scripts/health_monitor.sh

LOG_FILE="/var/log/ai-karen/health_monitor.log"
ALERT_EMAIL="ops@your-domain.com"
SLACK_WEBHOOK="https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"

# Function to log messages
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

# Function to send alert
send_alert() {
    local service=$1
    local status=$2
    local message=$3
    
    # Email alert
    echo "$message" | mail -s "ALERT: $service $status" "$ALERT_EMAIL"
    
    # Slack alert
    curl -X POST -H 'Content-type: application/json' \
        --data "{\"text\":\"🚨 ALERT: $service $status - $message\"}" \
        "$SLACK_WEBHOOK"
    
    log_message "ALERT SENT: $service $status - $message"
}

# Check backend health
check_backend() {
    if curl -f -s http://localhost:8000/api/health > /dev/null; then
        log_message "Backend health check: OK"
        return 0
    else
        send_alert "Backend" "DOWN" "Backend service is not responding"
        return 1
    fi
}

# Check frontend health
check_frontend() {
    if curl -f -s http://localhost:3000 > /dev/null; then
        log_message "Frontend health check: OK"
        return 0
    else
        send_alert "Frontend" "DOWN" "Frontend service is not responding"
        return 1
    fi
}

# Check database connectivity
check_database() {
    if sudo -u ai-karen psql -h localhost -U ai_karen_user -d ai_karen_prod -c "SELECT 1;" > /dev/null 2>&1; then
        log_message "Database health check: OK"
        return 0
    else
        send_alert "Database" "DOWN" "Database is not accessible"
        return 1
    fi
}

# Check Redis connectivity
check_redis() {
    if redis-cli ping | grep -q PONG; then
        log_message "Redis health check: OK"
        return 0
    else
        send_alert "Redis" "DOWN" "Redis is not responding"
        return 1
    fi
}

# Check disk space
check_disk_space() {
    local usage=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
    if [ "$usage" -gt 85 ]; then
        send_alert "Disk Space" "WARNING" "Disk usage is at ${usage}%"
        return 1
    else
        log_message "Disk space check: OK (${usage}%)"
        return 0
    fi
}

# Check memory usage
check_memory() {
    local usage=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')
    if [ "$usage" -gt 90 ]; then
        send_alert "Memory" "WARNING" "Memory usage is at ${usage}%"
        return 1
    else
        log_message "Memory check: OK (${usage}%)"
        return 0
    fi
}

# Main health check routine
main() {
    log_message "Starting health check routine"
    
    local failed_checks=0
    
    check_backend || ((failed_checks++))
    check_frontend || ((failed_checks++))
    check_database || ((failed_checks++))
    check_redis || ((failed_checks++))
    check_disk_space || ((failed_checks++))
    check_memory || ((failed_checks++))
    
    if [ $failed_checks -eq 0 ]; then
        log_message "All health checks passed"
    else
        log_message "Health check completed with $failed_checks failures"
    fi
    
    return $failed_checks
}

# Run main function
main
```

#### Cron Configuration

```bash
# Add to crontab (crontab -e)
# Run health checks every 5 minutes
*/5 * * * * /opt/ai-karen/scripts/health_monitor.sh

# Run detailed health check every hour
0 * * * * /opt/ai-karen/scripts/detailed_health_check.sh

# Daily system health report
0 8 * * * /opt/ai-karen/scripts/daily_health_report.sh
```

### External Monitoring

#### Uptime Monitoring

Configure external uptime monitoring for:
- Main website: `https://your-domain.com`
- API health endpoint: `https://api.your-domain.com/api/health`
- Admin interface: `https://your-domain.com/admin`

#### SSL Certificate Monitoring

```bash
#!/bin/bash
# Check SSL certificate expiration

DOMAIN="your-domain.com"
THRESHOLD_DAYS=30

# Get certificate expiration date
EXPIRY_DATE=$(echo | openssl s_client -servername $DOMAIN -connect $DOMAIN:443 2>/dev/null | \
              openssl x509 -noout -dates | grep notAfter | cut -d= -f2)

# Convert to epoch time
EXPIRY_EPOCH=$(date -d "$EXPIRY_DATE" +%s)
CURRENT_EPOCH=$(date +%s)
DAYS_UNTIL_EXPIRY=$(( (EXPIRY_EPOCH - CURRENT_EPOCH) / 86400 ))

if [ $DAYS_UNTIL_EXPIRY -lt $THRESHOLD_DAYS ]; then
    echo "SSL certificate expires in $DAYS_UNTIL_EXPIRY days" | \
    mail -s "SSL Certificate Expiration Warning" ops@your-domain.com
fi
```

## Performance Monitoring

### Prometheus Configuration

#### Prometheus Config (`/etc/prometheus/prometheus.yml`)

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "ai_karen_rules.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

scrape_configs:
  - job_name: 'ai-karen-backend'
    static_configs:
      - targets: ['localhost:9090']
    scrape_interval: 15s
    metrics_path: /metrics
    
  - job_name: 'node-exporter'
    static_configs:
      - targets: ['localhost:9100']
      
  - job_name: 'postgres-exporter'
    static_configs:
      - targets: ['localhost:9187']
      
  - job_name: 'redis-exporter'
    static_configs:
      - targets: ['localhost:9121']
```

#### Alert Rules (`ai_karen_rules.yml`)

```yaml
groups:
  - name: ai_karen_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} errors per second"
          
      - alert: HighResponseTime
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High response time detected"
          description: "95th percentile response time is {{ $value }} seconds"
          
      - alert: DatabaseConnectionsHigh
        expr: pg_stat_database_numbackends > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High number of database connections"
          description: "Database has {{ $value }} active connections"
          
      - alert: MemoryUsageHigh
        expr: (node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes > 0.9
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High memory usage"
          description: "Memory usage is {{ $value | humanizePercentage }}"
          
      - alert: DiskSpaceHigh
        expr: (node_filesystem_size_bytes - node_filesystem_avail_bytes) / node_filesystem_size_bytes > 0.85
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High disk usage"
          description: "Disk usage is {{ $value | humanizePercentage }}"
```

### Grafana Dashboards

#### System Overview Dashboard

Key panels:
- Request rate and response time
- Error rate by endpoint
- Active users and sessions
- System resource utilization
- Database performance metrics

#### Application Performance Dashboard

Key panels:
- Chat message processing time
- Model inference latency
- Memory operations performance
- Cache hit/miss ratios
- Queue lengths and processing times

## Security Monitoring

### Security Event Monitoring

#### Failed Login Attempts

```bash
#!/bin/bash
# Monitor failed login attempts

LOG_FILE="/var/log/ai-karen/security.log"
THRESHOLD=10
TIME_WINDOW=300  # 5 minutes

# Count failed login attempts in the last 5 minutes
FAILED_ATTEMPTS=$(grep "authentication_failed" "$LOG_FILE" | \
                  awk -v threshold=$(date -d "5 minutes ago" +%s) \
                  '$1 " " $2 > threshold' | wc -l)

if [ $FAILED_ATTEMPTS -gt $THRESHOLD ]; then
    echo "High number of failed login attempts: $FAILED_ATTEMPTS in last 5 minutes" | \
    mail -s "Security Alert: Failed Login Attempts" security@your-domain.com
fi
```

#### Suspicious Activity Detection

```bash
#!/bin/bash
# Detect suspicious activity patterns

# Check for unusual API usage patterns
grep "POST\|PUT\|DELETE" /var/log/nginx/access.log | \
awk '{print $1}' | sort | uniq -c | sort -nr | head -10 | \
while read count ip; do
    if [ $count -gt 100 ]; then
        echo "Suspicious activity from IP $ip: $count requests" | \
        mail -s "Security Alert: Suspicious Activity" security@your-domain.com
    fi
done

# Check for SQL injection attempts
grep -i "union\|select\|drop\|insert" /var/log/nginx/access.log | \
while read line; do
    echo "Potential SQL injection attempt: $line" | \
    mail -s "Security Alert: SQL Injection Attempt" security@your-domain.com
done
```

### Intrusion Detection

#### File Integrity Monitoring

```bash
#!/bin/bash
# Monitor critical files for changes

CRITICAL_FILES=(
    "/opt/ai-karen/app/.env"
    "/etc/nginx/sites-available/ai-karen"
    "/etc/systemd/system/ai-karen-*.service"
    "/etc/ssl/certs/ai-karen.crt"
)

for file in "${CRITICAL_FILES[@]}"; do
    if [ -f "$file" ]; then
        current_hash=$(sha256sum "$file" | cut -d' ' -f1)
        stored_hash_file="/var/lib/ai-karen/hashes/$(basename "$file").hash"
        
        if [ -f "$stored_hash_file" ]; then
            stored_hash=$(cat "$stored_hash_file")
            if [ "$current_hash" != "$stored_hash" ]; then
                echo "File integrity violation: $file has been modified" | \
                mail -s "Security Alert: File Modified" security@your-domain.com
            fi
        fi
        
        # Update stored hash
        mkdir -p "$(dirname "$stored_hash_file")"
        echo "$current_hash" > "$stored_hash_file"
    fi
done
```

## Log Management

### Log Rotation Configuration

```bash
# /etc/logrotate.d/ai-karen
/var/log/ai-karen/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 ai-karen ai-karen
    sharedscripts
    postrotate
        systemctl reload ai-karen-backend ai-karen-frontend
    endscript
}

/var/log/ai-karen/security.log {
    daily
    missingok
    rotate 365  # Keep security logs longer
    compress
    delaycompress
    notifempty
    create 644 ai-karen ai-karen
}
```

### Log Analysis Scripts

#### Error Analysis

```bash
#!/bin/bash
# Analyze error patterns

LOG_FILE="/var/log/ai-karen/error.log"
REPORT_FILE="/tmp/error_analysis_$(date +%Y%m%d).txt"

echo "AI Karen Error Analysis - $(date)" > "$REPORT_FILE"
echo "=================================" >> "$REPORT_FILE"

# Top error types
echo -e "\nTop Error Types:" >> "$REPORT_FILE"
grep -o '"error":"[^"]*"' "$LOG_FILE" | sort | uniq -c | sort -nr | head -10 >> "$REPORT_FILE"

# Errors by hour
echo -e "\nErrors by Hour:" >> "$REPORT_FILE"
grep "$(date +%Y-%m-%d)" "$LOG_FILE" | cut -d' ' -f2 | cut -d':' -f1 | sort | uniq -c >> "$REPORT_FILE"

# Most affected endpoints
echo -e "\nMost Affected Endpoints:" >> "$REPORT_FILE"
grep -o '"endpoint":"[^"]*"' "$LOG_FILE" | sort | uniq -c | sort -nr | head -10 >> "$REPORT_FILE"

# Email report
mail -s "Daily Error Analysis" -a "$REPORT_FILE" ops@your-domain.com < "$REPORT_FILE"
```

## Alerting and Notifications

### Alert Manager Configuration

```yaml
# /etc/alertmanager/alertmanager.yml
global:
  smtp_smarthost: 'smtp.your-domain.com:587'
  smtp_from: 'alerts@your-domain.com'
  smtp_auth_username: 'alerts@your-domain.com'
  smtp_auth_password: 'your_smtp_password'

route:
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'web.hook'
  routes:
    - match:
        severity: critical
      receiver: 'critical-alerts'
    - match:
        severity: warning
      receiver: 'warning-alerts'

receivers:
  - name: 'web.hook'
    webhook_configs:
      - url: 'http://localhost:5001/'
        
  - name: 'critical-alerts'
    email_configs:
      - to: 'ops@your-domain.com'
        subject: 'CRITICAL: {{ .GroupLabels.alertname }}'
        body: |
          {{ range .Alerts }}
          Alert: {{ .Annotations.summary }}
          Description: {{ .Annotations.description }}
          {{ end }}
    slack_configs:
      - api_url: 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK'
        channel: '#alerts'
        title: 'CRITICAL ALERT'
        text: '{{ range .Alerts }}{{ .Annotations.summary }}{{ end }}'
        
  - name: 'warning-alerts'
    email_configs:
      - to: 'ops@your-domain.com'
        subject: 'WARNING: {{ .GroupLabels.alertname }}'
```

### Notification Channels

#### Email Notifications
- **Critical**: Immediate email to on-call engineer
- **Warning**: Email to operations team
- **Info**: Daily digest email

#### Slack Integration
- **#alerts**: Critical and high-priority alerts
- **#monitoring**: All monitoring notifications
- **#ops**: Operational updates and maintenance

#### SMS/Phone Alerts
- Critical system failures
- Security incidents
- Extended outages

## Maintenance Procedures

### Regular Maintenance Schedule

#### Daily Tasks (Automated)
- Health check execution
- Log rotation
- Backup verification
- Security scan
- Performance metrics review

#### Weekly Tasks
- System updates review
- Security patches assessment
- Performance trend analysis
- Capacity utilization review
- Backup integrity testing

#### Monthly Tasks
- Full system backup
- Security audit
- Performance optimization
- Dependency updates
- Documentation updates

#### Quarterly Tasks
- Disaster recovery testing
- Security penetration testing
- Capacity planning review
- Architecture review
- Compliance audit

### Maintenance Scripts

#### System Update Script

```bash
#!/bin/bash
# System maintenance script

LOG_FILE="/var/log/ai-karen/maintenance.log"

log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Create backup before maintenance
create_backup() {
    log_message "Creating pre-maintenance backup"
    /opt/ai-karen/scripts/backup_database.sh
    /opt/ai-karen/scripts/backup_application.sh
}

# Update system packages
update_system() {
    log_message "Updating system packages"
    apt update
    apt list --upgradable
    
    # Only install security updates automatically
    unattended-upgrade -d
}

# Update application dependencies
update_dependencies() {
    log_message "Checking application dependencies"
    cd /opt/ai-karen/app
    source venv/bin/activate
    
    # Check for outdated packages
    pip list --outdated
    
    # Update only patch versions automatically
    pip install --upgrade $(pip list --outdated --format=freeze | grep -v '^\-e' | cut -d = -f 1)
}

# Cleanup old files
cleanup() {
    log_message "Cleaning up old files"
    
    # Remove old log files
    find /var/log/ai-karen/ -name "*.log.*" -mtime +30 -delete
    
    # Remove old backups
    find /opt/ai-karen/backups/ -name "*.tar.gz" -mtime +7 -delete
    find /opt/ai-karen/backups/ -name "*.sql.gz" -mtime +30 -delete
    
    # Clean temporary files
    find /tmp -name "ai-karen-*" -mtime +1 -delete
}

# Restart services if needed
restart_services() {
    log_message "Checking if services need restart"
    
    # Check if any services need restart
    if systemctl is-failed ai-karen-backend ai-karen-frontend; then
        log_message "Restarting failed services"
        systemctl restart ai-karen-backend ai-karen-frontend
    fi
}

# Main maintenance routine
main() {
    log_message "Starting maintenance routine"
    
    create_backup
    update_system
    update_dependencies
    cleanup
    restart_services
    
    log_message "Maintenance routine completed"
}

# Run maintenance
main
```

### Planned Maintenance Procedures

#### Application Updates

1. **Pre-deployment**:
   - Create full system backup
   - Test update in staging environment
   - Schedule maintenance window
   - Notify users of planned downtime

2. **Deployment**:
   - Enable maintenance mode
   - Stop application services
   - Deploy new version
   - Run database migrations
   - Start services
   - Verify functionality

3. **Post-deployment**:
   - Monitor for errors
   - Verify all features working
   - Disable maintenance mode
   - Send completion notification

#### Database Maintenance

```bash
#!/bin/bash
# Database maintenance script

# Vacuum and analyze database
sudo -u postgres psql ai_karen_prod -c "VACUUM ANALYZE;"

# Update table statistics
sudo -u postgres psql ai_karen_prod -c "ANALYZE;"

# Reindex if needed
sudo -u postgres psql ai_karen_prod -c "REINDEX DATABASE ai_karen_prod;"

# Check for unused indexes
sudo -u postgres psql ai_karen_prod -c "
SELECT schemaname, tablename, attname, n_distinct, correlation 
FROM pg_stats 
WHERE schemaname = 'public' 
ORDER BY n_distinct DESC;
"
```

## Backup and Recovery

### Backup Strategy

#### Automated Backups
- **Database**: Daily full backup, hourly incremental
- **Application**: Weekly full backup
- **Configuration**: Daily backup
- **Logs**: Weekly archive

#### Backup Verification

```bash
#!/bin/bash
# Verify backup integrity

BACKUP_DIR="/opt/ai-karen/backups"
LATEST_DB_BACKUP=$(ls -t "$BACKUP_DIR"/db_backup_*.sql.gz | head -1)

# Test database backup
if [ -f "$LATEST_DB_BACKUP" ]; then
    # Create test database
    sudo -u postgres createdb ai_karen_test
    
    # Restore backup to test database
    gunzip -c "$LATEST_DB_BACKUP" | sudo -u postgres psql ai_karen_test
    
    # Verify data integrity
    TABLE_COUNT=$(sudo -u postgres psql ai_karen_test -t -c "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public';")
    
    if [ "$TABLE_COUNT" -gt 0 ]; then
        echo "Backup verification successful: $TABLE_COUNT tables restored"
    else
        echo "Backup verification failed: No tables found"
        exit 1
    fi
    
    # Cleanup test database
    sudo -u postgres dropdb ai_karen_test
else
    echo "No database backup found for verification"
    exit 1
fi
```

### Recovery Procedures

#### Database Recovery

```bash
#!/bin/bash
# Database recovery procedure

BACKUP_FILE="$1"
if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file>"
    exit 1
fi

# Stop application
systemctl stop ai-karen-backend ai-karen-frontend

# Drop and recreate database
sudo -u postgres dropdb ai_karen_prod
sudo -u postgres createdb ai_karen_prod
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE ai_karen_prod TO ai_karen_user;"

# Restore from backup
gunzip -c "$BACKUP_FILE" | sudo -u postgres psql ai_karen_prod

# Start application
systemctl start ai-karen-backend ai-karen-frontend

echo "Database recovery completed"
```

## Incident Response

### Incident Classification

#### Severity Levels

**P0 - Critical**
- Complete system outage
- Data loss or corruption
- Security breach
- Response time: Immediate (< 15 minutes)

**P1 - High**
- Major feature unavailable
- Significant performance degradation
- Authentication issues
- Response time: < 1 hour

**P2 - Medium**
- Minor feature issues
- Moderate performance impact
- Non-critical errors
- Response time: < 4 hours

**P3 - Low**
- Cosmetic issues
- Enhancement requests
- Documentation updates
- Response time: < 24 hours

### Incident Response Playbook

#### Initial Response (First 15 minutes)

1. **Acknowledge**: Confirm incident receipt
2. **Assess**: Determine severity level
3. **Communicate**: Notify stakeholders
4. **Investigate**: Begin root cause analysis
5. **Mitigate**: Implement immediate fixes

#### Investigation Checklist

- [ ] Check system health dashboard
- [ ] Review recent deployments
- [ ] Analyze error logs
- [ ] Check external dependencies
- [ ] Verify infrastructure status
- [ ] Test user-reported scenarios

#### Communication Templates

**Initial Notification:**
```
Subject: [INCIDENT] System Issue Detected - P1

We are currently investigating reports of [issue description].
Status: Investigating
Impact: [affected services/users]
ETA: Updates every 30 minutes

We will provide updates as more information becomes available.
```

**Resolution Notification:**
```
Subject: [RESOLVED] System Issue - P1

The issue affecting [services] has been resolved.
Root Cause: [brief description]
Resolution: [what was done]
Duration: [total downtime]

A full post-mortem will be published within 24 hours.
```

## Capacity Planning

### Resource Monitoring

#### CPU and Memory Trends

```bash
#!/bin/bash
# Generate capacity planning report

REPORT_FILE="/tmp/capacity_report_$(date +%Y%m%d).txt"

echo "AI Karen Capacity Planning Report - $(date)" > "$REPORT_FILE"
echo "=========================================" >> "$REPORT_FILE"

# CPU utilization trends
echo -e "\nCPU Utilization (Last 7 days):" >> "$REPORT_FILE"
sar -u 1 1 | tail -1 >> "$REPORT_FILE"

# Memory utilization
echo -e "\nMemory Utilization:" >> "$REPORT_FILE"
free -h >> "$REPORT_FILE"

# Disk usage trends
echo -e "\nDisk Usage:" >> "$REPORT_FILE"
df -h >> "$REPORT_FILE"

# Database growth
echo -e "\nDatabase Size:" >> "$REPORT_FILE"
sudo -u postgres psql ai_karen_prod -c "
SELECT 
    pg_size_pretty(pg_database_size('ai_karen_prod')) as database_size,
    pg_size_pretty(pg_total_relation_size('users')) as users_table_size,
    pg_size_pretty(pg_total_relation_size('conversations')) as conversations_table_size;
" >> "$REPORT_FILE"

# Send report
mail -s "Weekly Capacity Planning Report" -a "$REPORT_FILE" ops@your-domain.com < "$REPORT_FILE"
```

### Growth Projections

#### User Growth Monitoring

```sql
-- Monthly user growth
SELECT 
    DATE_TRUNC('month', created_at) as month,
    COUNT(*) as new_users,
    SUM(COUNT(*)) OVER (ORDER BY DATE_TRUNC('month', created_at)) as total_users
FROM users 
WHERE created_at >= NOW() - INTERVAL '12 months'
GROUP BY DATE_TRUNC('month', created_at)
ORDER BY month;

-- Daily active users trend
SELECT 
    DATE(last_login) as date,
    COUNT(DISTINCT user_id) as daily_active_users
FROM user_sessions 
WHERE last_login >= NOW() - INTERVAL '30 days'
GROUP BY DATE(last_login)
ORDER BY date;
```

### Scaling Recommendations

#### Horizontal Scaling Triggers
- CPU utilization > 70% for 1 hour
- Memory utilization > 80% for 30 minutes
- Response time > 2 seconds for 15 minutes
- Database connections > 80% of pool size

#### Vertical Scaling Triggers
- Consistent resource utilization > 80%
- Frequent out-of-memory errors
- Database query performance degradation
- Storage utilization > 85%

---

**Document Version**: 1.0
**Last Updated**: 2024-01-01
**Next Review**: 2024-04-01