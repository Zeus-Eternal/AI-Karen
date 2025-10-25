# Admin Management System Backup and Recovery Procedures

This document provides comprehensive procedures for backing up and recovering admin management system data, ensuring business continuity and data protection.

## Table of Contents

- [Backup Strategy Overview](#backup-strategy-overview)
- [Database Backup Procedures](#database-backup-procedures)
- [Application Data Backup](#application-data-backup)
- [Configuration Backup](#configuration-backup)
- [Automated Backup Scripts](#automated-backup-scripts)
- [Recovery Procedures](#recovery-procedures)
- [Disaster Recovery Planning](#disaster-recovery-planning)
- [Testing and Validation](#testing-and-validation)
- [Monitoring and Alerting](#monitoring-and-alerting)

## Backup Strategy Overview

### Backup Types

1. **Full Backup**: Complete system backup including all data and configurations
2. **Incremental Backup**: Only changes since the last backup
3. **Differential Backup**: Changes since the last full backup
4. **Point-in-Time Recovery**: Continuous backup allowing recovery to any specific moment

### Backup Schedule

| Backup Type | Frequency | Retention | Storage Location |
|-------------|-----------|-----------|------------------|
| Full Database | Daily at 2:00 AM | 30 days | Primary + Offsite |
| Incremental Database | Every 4 hours | 7 days | Primary |
| Configuration | Daily at 1:00 AM | 90 days | Primary + Offsite |
| Application Files | Weekly | 12 weeks | Primary + Offsite |
| Audit Logs | Daily at 3:00 AM | 365 days | Primary + Offsite |

### Recovery Time Objectives (RTO) and Recovery Point Objectives (RPO)

| Component | RTO | RPO | Priority |
|-----------|-----|-----|----------|
| Core Admin System | 4 hours | 15 minutes | Critical |
| User Management | 2 hours | 15 minutes | Critical |
| Audit Logs | 8 hours | 1 hour | High |
| System Configuration | 1 hour | 4 hours | High |
| Email Templates | 4 hours | 24 hours | Medium |

## Database Backup Procedures

### Full Database Backup

#### Manual Full Backup

```bash
#!/bin/bash
# full-database-backup.sh

# Configuration
DB_HOST="localhost"
DB_PORT="5432"
DB_NAME="admin_system"
DB_USER="backup_user"
BACKUP_DIR="/backups/database"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="admin_system_full_${DATE}.sql"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Perform full backup
echo "Starting full database backup at $(date)"
pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
    --verbose --clean --if-exists --create \
    --format=custom --compress=9 \
    --file="$BACKUP_DIR/$BACKUP_FILE"

# Check backup success
if [ $? -eq 0 ]; then
    echo "Full backup completed successfully: $BACKUP_FILE"
    
    # Calculate backup size
    BACKUP_SIZE=$(du -h "$BACKUP_DIR/$BACKUP_FILE" | cut -f1)
    echo "Backup size: $BACKUP_SIZE"
    
    # Verify backup integrity
    pg_restore --list "$BACKUP_DIR/$BACKUP_FILE" > /dev/null
    if [ $? -eq 0 ]; then
        echo "Backup integrity verified"
    else
        echo "ERROR: Backup integrity check failed"
        exit 1
    fi
else
    echo "ERROR: Full backup failed"
    exit 1
fi

# Cleanup old backups (keep last 30 days)
find "$BACKUP_DIR" -name "admin_system_full_*.sql" -mtime +30 -delete

echo "Full database backup completed at $(date)"
```

#### Incremental Backup Using WAL-E

```bash
#!/bin/bash
# incremental-backup.sh

# Configuration
WALE_S3_PREFIX="s3://your-backup-bucket/admin-system-wal"
PGDATA="/var/lib/postgresql/data"

# Perform WAL-E backup
echo "Starting incremental backup at $(date)"

# Push WAL files to S3
wal-e wal-push "$PGDATA/pg_wal/$(ls -t $PGDATA/pg_wal/ | head -n1)"

if [ $? -eq 0 ]; then
    echo "Incremental backup completed successfully"
else
    echo "ERROR: Incremental backup failed"
    exit 1
fi

echo "Incremental backup completed at $(date)"
```

### Table-Specific Backups

#### Critical Tables Backup

```bash
#!/bin/bash
# critical-tables-backup.sh

DB_HOST="localhost"
DB_PORT="5432"
DB_NAME="admin_system"
DB_USER="backup_user"
BACKUP_DIR="/backups/tables"
DATE=$(date +%Y%m%d_%H%M%S)

# Critical tables to backup
TABLES=("users" "audit_logs" "system_config" "sessions")

mkdir -p "$BACKUP_DIR"

for table in "${TABLES[@]}"; do
    echo "Backing up table: $table"
    
    pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        --table="$table" --data-only --inserts \
        --file="$BACKUP_DIR/${table}_${DATE}.sql"
    
    if [ $? -eq 0 ]; then
        echo "Table $table backed up successfully"
    else
        echo "ERROR: Failed to backup table $table"
    fi
done

# Create combined backup
cat "$BACKUP_DIR"/*_${DATE}.sql > "$BACKUP_DIR/critical_tables_${DATE}.sql"

echo "Critical tables backup completed"
```

### Point-in-Time Recovery Setup

#### Configure Continuous Archiving

```sql
-- Enable WAL archiving in postgresql.conf
-- wal_level = replica
-- archive_mode = on
-- archive_command = 'wal-e wal-push %p'
-- max_wal_senders = 3
-- wal_keep_segments = 32

-- Create base backup for PITR
SELECT pg_start_backup('admin_system_base_backup');
-- Copy data directory to backup location
SELECT pg_stop_backup();
```

## Application Data Backup

### File System Backup

```bash
#!/bin/bash
# application-backup.sh

# Configuration
APP_DIR="/opt/admin-system"
BACKUP_DIR="/backups/application"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="admin_system_app_${DATE}.tar.gz"

# Directories to backup
BACKUP_PATHS=(
    "$APP_DIR/config"
    "$APP_DIR/data"
    "$APP_DIR/logs"
    "$APP_DIR/uploads"
    "$APP_DIR/.env"
    "$APP_DIR/package.json"
    "$APP_DIR/package-lock.json"
)

mkdir -p "$BACKUP_DIR"

echo "Starting application backup at $(date)"

# Create compressed archive
tar -czf "$BACKUP_DIR/$BACKUP_FILE" "${BACKUP_PATHS[@]}" 2>/dev/null

if [ $? -eq 0 ]; then
    echo "Application backup completed: $BACKUP_FILE"
    
    # Calculate backup size
    BACKUP_SIZE=$(du -h "$BACKUP_DIR/$BACKUP_FILE" | cut -f1)
    echo "Backup size: $BACKUP_SIZE"
else
    echo "ERROR: Application backup failed"
    exit 1
fi

# Cleanup old backups (keep last 12 weeks)
find "$BACKUP_DIR" -name "admin_system_app_*.tar.gz" -mtime +84 -delete

echo "Application backup completed at $(date)"
```

### Email Templates and Assets Backup

```bash
#!/bin/bash
# email-templates-backup.sh

TEMPLATES_DIR="/opt/admin-system/ui_launchers/web_ui/src/lib/email/templates"
ASSETS_DIR="/opt/admin-system/public/assets"
BACKUP_DIR="/backups/templates"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

# Backup email templates
tar -czf "$BACKUP_DIR/email_templates_${DATE}.tar.gz" -C "$TEMPLATES_DIR" .

# Backup assets
tar -czf "$BACKUP_DIR/assets_${DATE}.tar.gz" -C "$ASSETS_DIR" .

echo "Email templates and assets backed up"
```

## Configuration Backup

### System Configuration Backup

```bash
#!/bin/bash
# config-backup.sh

CONFIG_DIRS=(
    "/etc/nginx/sites-available"
    "/etc/ssl/certs"
    "/etc/systemd/system"
    "/etc/logrotate.d"
)

APP_CONFIG_FILES=(
    "/opt/admin-system/.env"
    "/opt/admin-system/config"
    "/opt/admin-system/ecosystem.config.js"
)

BACKUP_DIR="/backups/configuration"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

# Backup system configuration
for dir in "${CONFIG_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        dirname=$(basename "$dir")
        tar -czf "$BACKUP_DIR/system_${dirname}_${DATE}.tar.gz" -C "$dir" .
    fi
done

# Backup application configuration
tar -czf "$BACKUP_DIR/app_config_${DATE}.tar.gz" "${APP_CONFIG_FILES[@]}"

# Backup database configuration
pg_dumpall --globals-only > "$BACKUP_DIR/db_globals_${DATE}.sql"

echo "Configuration backup completed"
```

### Environment Variables Backup

```bash
#!/bin/bash
# env-backup.sh

ENV_FILE="/opt/admin-system/.env"
BACKUP_DIR="/backups/environment"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

# Create encrypted backup of environment file
gpg --symmetric --cipher-algo AES256 --output "$BACKUP_DIR/env_${DATE}.gpg" "$ENV_FILE"

echo "Environment variables backed up (encrypted)"
```

## Automated Backup Scripts

### Master Backup Script

```bash
#!/bin/bash
# master-backup.sh

SCRIPT_DIR="/opt/admin-system/scripts/backup"
LOG_FILE="/var/log/admin-backup.log"
EMAIL_RECIPIENT="admin@example.com"

# Function to log messages
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Function to send notification
send_notification() {
    local subject="$1"
    local message="$2"
    echo "$message" | mail -s "$subject" "$EMAIL_RECIPIENT"
}

log_message "Starting master backup process"

# Run database backup
log_message "Starting database backup"
if "$SCRIPT_DIR/full-database-backup.sh" >> "$LOG_FILE" 2>&1; then
    log_message "Database backup completed successfully"
else
    log_message "ERROR: Database backup failed"
    send_notification "Backup Failed" "Database backup failed. Check logs for details."
    exit 1
fi

# Run application backup
log_message "Starting application backup"
if "$SCRIPT_DIR/application-backup.sh" >> "$LOG_FILE" 2>&1; then
    log_message "Application backup completed successfully"
else
    log_message "ERROR: Application backup failed"
    send_notification "Backup Failed" "Application backup failed. Check logs for details."
    exit 1
fi

# Run configuration backup
log_message "Starting configuration backup"
if "$SCRIPT_DIR/config-backup.sh" >> "$LOG_FILE" 2>&1; then
    log_message "Configuration backup completed successfully"
else
    log_message "ERROR: Configuration backup failed"
    send_notification "Backup Failed" "Configuration backup failed. Check logs for details."
    exit 1
fi

# Sync to offsite storage
log_message "Starting offsite sync"
if rsync -av --delete /backups/ backup-server:/remote/backups/admin-system/; then
    log_message "Offsite sync completed successfully"
else
    log_message "ERROR: Offsite sync failed"
    send_notification "Backup Warning" "Offsite sync failed. Local backups are available."
fi

log_message "Master backup process completed"
send_notification "Backup Success" "All backup operations completed successfully"
```

### Cron Job Configuration

```bash
# Add to crontab (crontab -e)

# Full backup daily at 2:00 AM
0 2 * * * /opt/admin-system/scripts/backup/master-backup.sh

# Incremental backup every 4 hours
0 */4 * * * /opt/admin-system/scripts/backup/incremental-backup.sh

# Configuration backup daily at 1:00 AM
0 1 * * * /opt/admin-system/scripts/backup/config-backup.sh

# Critical tables backup every 2 hours
0 */2 * * * /opt/admin-system/scripts/backup/critical-tables-backup.sh

# Cleanup old backups weekly
0 3 * * 0 /opt/admin-system/scripts/backup/cleanup-old-backups.sh
```

## Recovery Procedures

### Full System Recovery

#### Complete Database Recovery

```bash
#!/bin/bash
# full-database-recovery.sh

# Configuration
DB_HOST="localhost"
DB_PORT="5432"
DB_NAME="admin_system"
DB_USER="postgres"
BACKUP_FILE="$1"

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file>"
    exit 1
fi

if [ ! -f "$BACKUP_FILE" ]; then
    echo "ERROR: Backup file not found: $BACKUP_FILE"
    exit 1
fi

echo "Starting full database recovery from: $BACKUP_FILE"

# Stop application
echo "Stopping application..."
pm2 stop admin-app

# Drop existing database (be careful!)
echo "Dropping existing database..."
dropdb -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" "$DB_NAME"

# Restore from backup
echo "Restoring database from backup..."
pg_restore -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" \
    --create --verbose --clean --if-exists \
    --dbname=postgres "$BACKUP_FILE"

if [ $? -eq 0 ]; then
    echo "Database recovery completed successfully"
    
    # Verify recovery
    echo "Verifying database recovery..."
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        -c "SELECT COUNT(*) FROM users;" > /dev/null
    
    if [ $? -eq 0 ]; then
        echo "Database verification successful"
        
        # Start application
        echo "Starting application..."
        pm2 start admin-app
        
        echo "Full database recovery completed successfully"
    else
        echo "ERROR: Database verification failed"
        exit 1
    fi
else
    echo "ERROR: Database recovery failed"
    exit 1
fi
```

#### Point-in-Time Recovery

```bash
#!/bin/bash
# point-in-time-recovery.sh

RECOVERY_TARGET_TIME="$1"
BASE_BACKUP_DIR="/backups/base"
WAL_ARCHIVE_DIR="/backups/wal"
PGDATA="/var/lib/postgresql/data"

if [ -z "$RECOVERY_TARGET_TIME" ]; then
    echo "Usage: $0 'YYYY-MM-DD HH:MM:SS'"
    exit 1
fi

echo "Starting point-in-time recovery to: $RECOVERY_TARGET_TIME"

# Stop PostgreSQL
systemctl stop postgresql

# Backup current data directory
mv "$PGDATA" "${PGDATA}.backup.$(date +%Y%m%d_%H%M%S)"

# Restore base backup
cp -R "$BASE_BACKUP_DIR/latest" "$PGDATA"

# Create recovery configuration
cat > "$PGDATA/recovery.conf" << EOF
restore_command = 'cp $WAL_ARCHIVE_DIR/%f %p'
recovery_target_time = '$RECOVERY_TARGET_TIME'
recovery_target_action = 'promote'
EOF

# Set permissions
chown -R postgres:postgres "$PGDATA"
chmod 700 "$PGDATA"

# Start PostgreSQL
systemctl start postgresql

echo "Point-in-time recovery initiated. Check PostgreSQL logs for completion."
```

### Selective Recovery

#### Single Table Recovery

```bash
#!/bin/bash
# single-table-recovery.sh

TABLE_NAME="$1"
BACKUP_FILE="$2"
DB_NAME="admin_system"

if [ -z "$TABLE_NAME" ] || [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <table_name> <backup_file>"
    exit 1
fi

echo "Recovering table: $TABLE_NAME from $BACKUP_FILE"

# Create temporary database
createdb temp_recovery_db

# Restore backup to temporary database
pg_restore -d temp_recovery_db "$BACKUP_FILE"

# Backup current table
pg_dump -d "$DB_NAME" -t "$TABLE_NAME" > "${TABLE_NAME}_backup_$(date +%Y%m%d_%H%M%S).sql"

# Drop current table
psql -d "$DB_NAME" -c "DROP TABLE IF EXISTS ${TABLE_NAME} CASCADE;"

# Copy table from temporary database
pg_dump -d temp_recovery_db -t "$TABLE_NAME" | psql -d "$DB_NAME"

# Drop temporary database
dropdb temp_recovery_db

echo "Table recovery completed: $TABLE_NAME"
```

#### Configuration Recovery

```bash
#!/bin/bash
# config-recovery.sh

CONFIG_BACKUP="$1"
RECOVERY_DIR="/opt/admin-system"

if [ -z "$CONFIG_BACKUP" ]; then
    echo "Usage: $0 <config_backup_file>"
    exit 1
fi

echo "Recovering configuration from: $CONFIG_BACKUP"

# Stop application
pm2 stop admin-app

# Backup current configuration
tar -czf "${RECOVERY_DIR}/config_backup_$(date +%Y%m%d_%H%M%S).tar.gz" \
    "${RECOVERY_DIR}/config" "${RECOVERY_DIR}/.env"

# Extract configuration backup
tar -xzf "$CONFIG_BACKUP" -C "$RECOVERY_DIR"

# Set proper permissions
chown -R app:app "${RECOVERY_DIR}/config"
chmod 600 "${RECOVERY_DIR}/.env"

# Start application
pm2 start admin-app

echo "Configuration recovery completed"
```

### Emergency Recovery Procedures

#### Rapid Recovery Script

```bash
#!/bin/bash
# emergency-recovery.sh

EMERGENCY_BACKUP_DIR="/backups/emergency"
LATEST_FULL_BACKUP=$(ls -t $EMERGENCY_BACKUP_DIR/admin_system_full_*.sql | head -n1)
LATEST_CONFIG_BACKUP=$(ls -t $EMERGENCY_BACKUP_DIR/app_config_*.tar.gz | head -n1)

echo "=== EMERGENCY RECOVERY PROCEDURE ==="
echo "Starting emergency recovery at $(date)"

# 1. Stop all services
echo "Stopping services..."
pm2 stop all
systemctl stop nginx

# 2. Recover database
echo "Recovering database from: $LATEST_FULL_BACKUP"
./full-database-recovery.sh "$LATEST_FULL_BACKUP"

# 3. Recover configuration
echo "Recovering configuration from: $LATEST_CONFIG_BACKUP"
./config-recovery.sh "$LATEST_CONFIG_BACKUP"

# 4. Start services
echo "Starting services..."
systemctl start nginx
pm2 start all

# 5. Verify system
echo "Verifying system recovery..."
sleep 10

# Check database
if psql -d admin_system -c "SELECT COUNT(*) FROM users;" > /dev/null 2>&1; then
    echo "✅ Database recovery verified"
else
    echo "❌ Database recovery failed"
    exit 1
fi

# Check application
if curl -s http://localhost:3000/api/health > /dev/null; then
    echo "✅ Application recovery verified"
else
    echo "❌ Application recovery failed"
    exit 1
fi

echo "=== EMERGENCY RECOVERY COMPLETED ==="
echo "Recovery completed at $(date)"
```

## Disaster Recovery Planning

### Disaster Recovery Scenarios

#### Scenario 1: Database Corruption

**Recovery Steps:**
1. Stop application immediately
2. Assess corruption extent
3. Restore from latest full backup
4. Apply incremental backups if available
5. Verify data integrity
6. Restart application

**Estimated Recovery Time:** 2-4 hours

#### Scenario 2: Complete Server Failure

**Recovery Steps:**
1. Provision new server
2. Install required software
3. Restore database from offsite backup
4. Restore application files
5. Restore configuration
6. Update DNS/load balancer
7. Verify functionality

**Estimated Recovery Time:** 4-8 hours

#### Scenario 3: Data Center Outage

**Recovery Steps:**
1. Activate disaster recovery site
2. Restore from offsite backups
3. Update network configuration
4. Redirect traffic to DR site
5. Monitor system performance

**Estimated Recovery Time:** 1-2 hours

### Disaster Recovery Checklist

#### Pre-Disaster Preparation
- [ ] Offsite backups verified and accessible
- [ ] DR site infrastructure ready
- [ ] Network failover procedures tested
- [ ] Contact information updated
- [ ] Recovery procedures documented and tested

#### During Disaster
- [ ] Assess damage and scope
- [ ] Activate disaster recovery team
- [ ] Communicate with stakeholders
- [ ] Execute recovery procedures
- [ ] Monitor recovery progress

#### Post-Disaster
- [ ] Verify system functionality
- [ ] Update stakeholders
- [ ] Document lessons learned
- [ ] Update recovery procedures
- [ ] Plan for return to primary site

## Testing and Validation

### Backup Validation Scripts

#### Backup Integrity Test

```bash
#!/bin/bash
# backup-integrity-test.sh

BACKUP_FILE="$1"
TEST_DB="backup_test_$(date +%s)"

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file>"
    exit 1
fi

echo "Testing backup integrity: $BACKUP_FILE"

# Create test database
createdb "$TEST_DB"

# Restore backup to test database
pg_restore -d "$TEST_DB" "$BACKUP_FILE" > /dev/null 2>&1

if [ $? -eq 0 ]; then
    # Verify critical tables exist
    TABLES=("users" "audit_logs" "system_config")
    
    for table in "${TABLES[@]}"; do
        COUNT=$(psql -d "$TEST_DB" -t -c "SELECT COUNT(*) FROM $table;" 2>/dev/null)
        
        if [ $? -eq 0 ] && [ "$COUNT" -gt 0 ]; then
            echo "✅ Table $table: $COUNT records"
        else
            echo "❌ Table $table: verification failed"
            dropdb "$TEST_DB"
            exit 1
        fi
    done
    
    echo "✅ Backup integrity test passed"
else
    echo "❌ Backup integrity test failed"
    exit 1
fi

# Cleanup
dropdb "$TEST_DB"
```

#### Recovery Test Procedure

```bash
#!/bin/bash
# recovery-test.sh

TEST_ENV="test_recovery"
BACKUP_FILE="$1"

echo "Starting recovery test in $TEST_ENV environment"

# Create isolated test environment
docker-compose -f docker-compose.test.yml up -d

# Wait for services to start
sleep 30

# Perform recovery test
docker exec recovery-test-db pg_restore -d admin_system /backups/test_backup.sql

# Run application tests
docker exec recovery-test-app npm test

# Verify admin functionality
curl -f http://localhost:3001/api/admin/setup/check-first-run

if [ $? -eq 0 ]; then
    echo "✅ Recovery test passed"
else
    echo "❌ Recovery test failed"
fi

# Cleanup test environment
docker-compose -f docker-compose.test.yml down -v
```

### Monthly Recovery Drill

```bash
#!/bin/bash
# monthly-recovery-drill.sh

DRILL_DATE=$(date +%Y%m%d)
DRILL_LOG="/var/log/recovery-drill-${DRILL_DATE}.log"

echo "=== MONTHLY RECOVERY DRILL ===" | tee "$DRILL_LOG"
echo "Date: $(date)" | tee -a "$DRILL_LOG"

# Test 1: Database backup integrity
echo "Testing database backup integrity..." | tee -a "$DRILL_LOG"
if ./backup-integrity-test.sh /backups/database/latest_full_backup.sql >> "$DRILL_LOG" 2>&1; then
    echo "✅ Database backup integrity test passed" | tee -a "$DRILL_LOG"
else
    echo "❌ Database backup integrity test failed" | tee -a "$DRILL_LOG"
fi

# Test 2: Configuration recovery
echo "Testing configuration recovery..." | tee -a "$DRILL_LOG"
if ./config-recovery-test.sh >> "$DRILL_LOG" 2>&1; then
    echo "✅ Configuration recovery test passed" | tee -a "$DRILL_LOG"
else
    echo "❌ Configuration recovery test failed" | tee -a "$DRILL_LOG"
fi

# Test 3: Application recovery
echo "Testing application recovery..." | tee -a "$DRILL_LOG"
if ./recovery-test.sh /backups/database/latest_full_backup.sql >> "$DRILL_LOG" 2>&1; then
    echo "✅ Application recovery test passed" | tee -a "$DRILL_LOG"
else
    echo "❌ Application recovery test failed" | tee -a "$DRILL_LOG"
fi

# Generate report
echo "=== DRILL SUMMARY ===" | tee -a "$DRILL_LOG"
echo "Drill completed at $(date)" | tee -a "$DRILL_LOG"

# Send report
mail -s "Monthly Recovery Drill Report - $DRILL_DATE" admin@example.com < "$DRILL_LOG"
```

## Monitoring and Alerting

### Backup Monitoring Script

```bash
#!/bin/bash
# backup-monitor.sh

BACKUP_DIR="/backups"
ALERT_EMAIL="admin@example.com"
MAX_BACKUP_AGE=86400  # 24 hours in seconds

# Check if recent backups exist
check_backup_freshness() {
    local backup_type="$1"
    local backup_pattern="$2"
    local max_age="$3"
    
    latest_backup=$(find "$BACKUP_DIR" -name "$backup_pattern" -type f -printf '%T@ %p\n' | sort -n | tail -1 | cut -d' ' -f2-)
    
    if [ -z "$latest_backup" ]; then
        echo "❌ No $backup_type backup found"
        return 1
    fi
    
    backup_age=$(($(date +%s) - $(stat -c %Y "$latest_backup")))
    
    if [ $backup_age -gt $max_age ]; then
        echo "❌ $backup_type backup is too old: $(($backup_age / 3600)) hours"
        return 1
    else
        echo "✅ $backup_type backup is current: $(basename "$latest_backup")"
        return 0
    fi
}

# Monitor backup status
echo "=== BACKUP MONITORING REPORT ==="
echo "Date: $(date)"
echo

# Check database backups
check_backup_freshness "Database" "admin_system_full_*.sql" $MAX_BACKUP_AGE
DB_STATUS=$?

# Check application backups
check_backup_freshness "Application" "admin_system_app_*.tar.gz" $((MAX_BACKUP_AGE * 7))  # Weekly
APP_STATUS=$?

# Check configuration backups
check_backup_freshness "Configuration" "app_config_*.tar.gz" $MAX_BACKUP_AGE
CONFIG_STATUS=$?

# Check disk space
DISK_USAGE=$(df "$BACKUP_DIR" | awk 'NR==2 {print $5}' | sed 's/%//')
echo
echo "Backup disk usage: ${DISK_USAGE}%"

if [ $DISK_USAGE -gt 80 ]; then
    echo "⚠️  Warning: Backup disk usage is high"
    DISK_STATUS=1
else
    echo "✅ Backup disk usage is acceptable"
    DISK_STATUS=0
fi

# Send alerts if needed
if [ $DB_STATUS -ne 0 ] || [ $APP_STATUS -ne 0 ] || [ $CONFIG_STATUS -ne 0 ] || [ $DISK_STATUS -ne 0 ]; then
    echo "Sending alert email..."
    {
        echo "Backup monitoring alert for Admin Management System"
        echo
        echo "Issues detected:"
        [ $DB_STATUS -ne 0 ] && echo "- Database backup issue"
        [ $APP_STATUS -ne 0 ] && echo "- Application backup issue"
        [ $CONFIG_STATUS -ne 0 ] && echo "- Configuration backup issue"
        [ $DISK_STATUS -ne 0 ] && echo "- Disk space issue"
        echo
        echo "Please check backup systems immediately."
    } | mail -s "Backup Alert - Admin System" "$ALERT_EMAIL"
fi

echo "=== MONITORING COMPLETE ==="
```

### Backup Health Dashboard

```bash
#!/bin/bash
# backup-health-dashboard.sh

# Generate HTML dashboard
cat > /var/www/html/backup-status.html << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>Admin System Backup Status</title>
    <meta http-equiv="refresh" content="300">
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .status-ok { color: green; }
        .status-warning { color: orange; }
        .status-error { color: red; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
    </style>
</head>
<body>
    <h1>Admin System Backup Status</h1>
    <p>Last updated: $(date)</p>
    
    <table>
        <tr>
            <th>Backup Type</th>
            <th>Last Backup</th>
            <th>Size</th>
            <th>Status</th>
        </tr>
EOF

# Add backup status rows
add_backup_row() {
    local type="$1"
    local pattern="$2"
    local latest_backup=$(find /backups -name "$pattern" -type f -printf '%T@ %p\n' | sort -n | tail -1 | cut -d' ' -f2-)
    
    if [ -n "$latest_backup" ]; then
        local backup_date=$(date -r "$latest_backup" '+%Y-%m-%d %H:%M')
        local backup_size=$(du -h "$latest_backup" | cut -f1)
        local backup_age=$(($(date +%s) - $(stat -c %Y "$latest_backup")))
        
        if [ $backup_age -lt 86400 ]; then
            local status_class="status-ok"
            local status_text="OK"
        elif [ $backup_age -lt 172800 ]; then
            local status_class="status-warning"
            local status_text="Warning"
        else
            local status_class="status-error"
            local status_text="Error"
        fi
    else
        local backup_date="Never"
        local backup_size="N/A"
        local status_class="status-error"
        local status_text="Missing"
    fi
    
    cat >> /var/www/html/backup-status.html << EOF
        <tr>
            <td>$type</td>
            <td>$backup_date</td>
            <td>$backup_size</td>
            <td class="$status_class">$status_text</td>
        </tr>
EOF
}

add_backup_row "Database Full" "admin_system_full_*.sql"
add_backup_row "Application" "admin_system_app_*.tar.gz"
add_backup_row "Configuration" "app_config_*.tar.gz"

cat >> /var/www/html/backup-status.html << 'EOF'
    </table>
</body>
</html>
EOF

echo "Backup status dashboard updated"
```

---

*This backup and recovery documentation should be reviewed and tested regularly to ensure procedures remain current and effective.*