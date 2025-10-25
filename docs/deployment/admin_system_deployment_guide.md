# Admin Management System Deployment Guide

This comprehensive guide covers the deployment process, rollback procedures, and post-deployment verification for the admin management system.

## Table of Contents

- [Pre-Deployment Checklist](#pre-deployment-checklist)
- [Deployment Process](#deployment-process)
- [Database Migration](#database-migration)
- [Configuration Setup](#configuration-setup)
- [Post-Deployment Verification](#post-deployment-verification)
- [Rollback Procedures](#rollback-procedures)
- [Monitoring and Maintenance](#monitoring-and-maintenance)
- [Troubleshooting](#troubleshooting)

## Pre-Deployment Checklist

### Environment Preparation

#### System Requirements
- [ ] **Database**: PostgreSQL 12+ with admin privileges
- [ ] **Node.js**: Version 18+ installed
- [ ] **Memory**: Minimum 4GB RAM available
- [ ] **Storage**: At least 10GB free disk space
- [ ] **Network**: HTTPS certificate configured
- [ ] **Backup**: Current system backup completed

#### Dependencies Verification
- [ ] All npm packages installed and up to date
- [ ] Database connection tested and verified
- [ ] Email service configured and tested
- [ ] SSL/TLS certificates valid and installed
- [ ] Environment variables configured
- [ ] Firewall rules configured for admin endpoints

#### Security Prerequisites
- [ ] Security scanning completed (no critical vulnerabilities)
- [ ] Penetration testing performed (if required)
- [ ] Security policies reviewed and approved
- [ ] Incident response procedures documented
- [ ] Backup and recovery procedures tested

#### Code Quality Checks
- [ ] All tests passing (unit, integration, e2e)
- [ ] Code review completed and approved
- [ ] Performance testing completed
- [ ] Accessibility testing passed
- [ ] Security audit completed

#### Documentation
- [ ] API documentation updated
- [ ] User guides completed
- [ ] Admin procedures documented
- [ ] Troubleshooting guide available
- [ ] Rollback procedures documented

### Stakeholder Approval
- [ ] **Technical Lead**: Code review and architecture approval
- [ ] **Security Team**: Security review and approval
- [ ] **Product Owner**: Feature acceptance and approval
- [ ] **Operations Team**: Deployment readiness confirmation
- [ ] **Legal/Compliance**: Privacy and compliance approval (if required)

## Deployment Process

### Phase 1: Pre-Deployment Setup

#### 1.1 Create Deployment Branch
```bash
# Create deployment branch from main
git checkout main
git pull origin main
git checkout -b deployment/admin-system-v1.0
git push origin deployment/admin-system-v1.0
```

#### 1.2 Environment Configuration
```bash
# Copy environment template
cp .env.example .env.production

# Configure production environment variables
# Edit .env.production with production values
```

**Required Environment Variables:**
```env
# Database Configuration
DATABASE_URL=postgresql://user:password@host:port/database
DATABASE_SSL=true

# Session Configuration
SESSION_SECRET=your-secure-session-secret
SESSION_TIMEOUT_ADMIN=1800
SESSION_TIMEOUT_USER=3600

# Email Configuration
SMTP_HOST=your-smtp-host
SMTP_PORT=587
SMTP_USER=your-smtp-user
SMTP_PASS=your-smtp-password
SMTP_FROM=admin@yourdomain.com

# Security Configuration
MFA_REQUIRED_ADMIN=true
PASSWORD_MIN_LENGTH=14
MAX_LOGIN_ATTEMPTS=5
LOCKOUT_DURATION=900

# Application Configuration
NODE_ENV=production
PORT=3000
BASE_URL=https://yourdomain.com
```

#### 1.3 Build Application
```bash
# Install production dependencies
npm ci --production

# Build application
npm run build

# Verify build
npm run start:prod --dry-run
```

### Phase 2: Database Migration

#### 2.1 Backup Current Database
```bash
# Create database backup
pg_dump -h localhost -U username -d database_name > backup_pre_admin_$(date +%Y%m%d_%H%M%S).sql

# Verify backup integrity
pg_restore --list backup_pre_admin_*.sql
```

#### 2.2 Run Migration Scripts
```bash
# Run main admin system migration
psql -h localhost -U username -d database_name -f data/migrations/postgres/018_admin_management_system.sql

# Run production deployment migration
psql -h localhost -U username -d database_name -f data/migrations/postgres/020_admin_system_production_deployment.sql

# Verify migration success
psql -h localhost -U username -d database_name -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_name IN ('audit_logs', 'system_config');"
```

#### 2.3 Verify Database Schema
```sql
-- Check required tables exist
SELECT table_name FROM information_schema.tables 
WHERE table_name IN ('users', 'audit_logs', 'system_config');

-- Verify role column added to users table
SELECT column_name, data_type FROM information_schema.columns 
WHERE table_name = 'users' AND column_name = 'role';

-- Check indexes created
SELECT indexname FROM pg_indexes 
WHERE tablename IN ('users', 'audit_logs', 'system_config');
```

### Phase 3: Application Deployment

#### 3.1 Deploy Application Code
```bash
# Stop current application (if running)
pm2 stop admin-app || true

# Deploy new code
rsync -av --exclude node_modules --exclude .git . /path/to/production/

# Install dependencies in production
cd /path/to/production/
npm ci --production

# Build application
npm run build
```

#### 3.2 Update Configuration
```bash
# Copy production environment file
cp .env.production /path/to/production/.env

# Set proper file permissions
chmod 600 /path/to/production/.env
chown app:app /path/to/production/.env
```

#### 3.3 Start Application
```bash
# Start application with PM2
pm2 start ecosystem.config.js --env production

# Verify application started
pm2 status
pm2 logs admin-app --lines 50
```

### Phase 4: Configuration Setup

#### 4.1 Initialize System Configuration
```bash
# Run configuration setup script
node scripts/setup-production-config.js

# Verify configuration
curl -k https://localhost:3000/api/admin/setup/check-first-run
```

#### 4.2 Configure Load Balancer/Reverse Proxy
```nginx
# Nginx configuration for admin endpoints
upstream admin_backend {
    server 127.0.0.1:3000;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;
    
    # Admin API routes
    location /api/admin/ {
        proxy_pass http://admin_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Security headers
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";
    }
}
```

#### 4.3 Configure Monitoring
```bash
# Setup log rotation
sudo cp config/logrotate.conf /etc/logrotate.d/admin-app

# Configure monitoring alerts
cp monitoring/admin_alerts.yml /etc/prometheus/alerts/

# Restart monitoring services
sudo systemctl restart prometheus
sudo systemctl restart grafana-server
```

## Database Migration

### Migration Script Execution Order

1. **018_admin_management_system.sql** - Core admin system tables and functions
2. **019_performance_optimization_indexes.sql** - Performance indexes
3. **020_admin_system_production_deployment.sql** - Production-specific configurations

### Migration Verification

#### Post-Migration Checks
```sql
-- Verify all tables created
SELECT COUNT(*) as table_count FROM information_schema.tables 
WHERE table_name IN ('users', 'audit_logs', 'system_config');
-- Expected: 3

-- Check user table has role column
SELECT COUNT(*) as role_column FROM information_schema.columns 
WHERE table_name = 'users' AND column_name = 'role';
-- Expected: 1

-- Verify system configuration defaults
SELECT COUNT(*) as config_count FROM system_config;
-- Expected: 13 (default configuration entries)

-- Check audit log table structure
SELECT column_name FROM information_schema.columns 
WHERE table_name = 'audit_logs' 
ORDER BY ordinal_position;
```

#### Performance Verification
```sql
-- Check indexes created
SELECT schemaname, tablename, indexname 
FROM pg_indexes 
WHERE tablename IN ('users', 'audit_logs', 'system_config');

-- Verify RLS policies
SELECT schemaname, tablename, policyname 
FROM pg_policies 
WHERE tablename IN ('users', 'audit_logs', 'system_config');
```

## Configuration Setup

### System Configuration Values

#### Security Configuration
```sql
-- Update security settings
UPDATE system_config SET value = '14' WHERE key = 'password_min_length';
UPDATE system_config SET value = 'true' WHERE key = 'mfa_required_admin';
UPDATE system_config SET value = '5' WHERE key = 'max_login_attempts';
UPDATE system_config SET value = '1800' WHERE key = 'session_timeout_admin';
```

#### Email Configuration
```sql
-- Configure email settings
UPDATE system_config SET value = 'smtp.yourdomain.com' WHERE key = 'smtp_host';
UPDATE system_config SET value = '587' WHERE key = 'smtp_port';
UPDATE system_config SET value = 'admin@yourdomain.com' WHERE key = 'email_from_address';
UPDATE system_config SET value = 'System Administrator' WHERE key = 'email_from_name';
```

### Application Configuration

#### Environment-Specific Settings
```javascript
// config/production.js
module.exports = {
  database: {
    ssl: true,
    connectionLimit: 20,
    idleTimeoutMillis: 30000
  },
  session: {
    secure: true,
    httpOnly: true,
    sameSite: 'strict',
    maxAge: 1800000 // 30 minutes for admin
  },
  security: {
    rateLimiting: {
      windowMs: 15 * 60 * 1000, // 15 minutes
      max: 100 // limit each IP to 100 requests per windowMs
    },
    helmet: {
      contentSecurityPolicy: {
        directives: {
          defaultSrc: ["'self'"],
          styleSrc: ["'self'", "'unsafe-inline'"],
          scriptSrc: ["'self'"],
          imgSrc: ["'self'", "data:", "https:"]
        }
      }
    }
  }
};
```

## Post-Deployment Verification

### Automated Verification Tests

#### 1. Health Check Tests
```bash
# Run health check script
node scripts/health-check.js

# Expected output:
# ✅ Database connection: OK
# ✅ Admin API endpoints: OK
# ✅ Email service: OK
# ✅ Session management: OK
# ✅ Authentication: OK
```

#### 2. API Endpoint Tests
```bash
# Test first-run setup endpoint
curl -X GET https://yourdomain.com/api/admin/setup/check-first-run
# Expected: {"needsSetup": true}

# Test admin API authentication
curl -X GET https://yourdomain.com/api/admin/users \
  -H "Cookie: session=invalid" \
  -w "%{http_code}"
# Expected: 401
```

#### 3. Database Functionality Tests
```sql
-- Test audit logging
INSERT INTO audit_logs (user_id, action, resource_type, details, ip_address, user_agent, timestamp)
VALUES ('00000000-0000-0000-0000-000000000000', 'test_action', 'test', '{}', '127.0.0.1', 'test', NOW());

-- Verify insert successful
SELECT COUNT(*) FROM audit_logs WHERE action = 'test_action';

-- Clean up test data
DELETE FROM audit_logs WHERE action = 'test_action';
```

### Manual Verification Steps

#### 1. First-Run Setup Process
- [ ] Navigate to application URL
- [ ] Verify redirect to first-run setup page
- [ ] Complete super admin creation process
- [ ] Verify email verification works
- [ ] Confirm automatic login after setup
- [ ] Check super admin dashboard loads correctly

#### 2. Authentication Testing
- [ ] Test super admin login with correct credentials
- [ ] Test login with incorrect credentials (should fail)
- [ ] Verify account lockout after multiple failed attempts
- [ ] Test password reset functionality
- [ ] Verify MFA setup process (if enabled)

#### 3. Admin Functionality Testing
- [ ] Create a new admin user
- [ ] Test admin user login
- [ ] Verify admin can access user management
- [ ] Confirm admin cannot access super admin functions
- [ ] Test user creation by admin
- [ ] Verify audit logging of admin actions

#### 4. Security Feature Testing
- [ ] Test rate limiting on login endpoints
- [ ] Verify session timeout functionality
- [ ] Test HTTPS enforcement
- [ ] Check security headers in responses
- [ ] Verify CSRF protection

### Performance Verification

#### 1. Load Testing
```bash
# Install artillery for load testing
npm install -g artillery

# Run load test
artillery run tests/load/admin-endpoints.yml

# Expected results:
# - Response time p95 < 500ms
# - Error rate < 1%
# - No memory leaks
```

#### 2. Database Performance
```sql
-- Check query performance
EXPLAIN ANALYZE SELECT * FROM users WHERE role = 'admin';
-- Should use index scan, not sequential scan

-- Monitor connection usage
SELECT count(*) as active_connections FROM pg_stat_activity;
-- Should be within configured limits
```

## Rollback Procedures

### Emergency Rollback (Critical Issues)

#### 1. Immediate Application Rollback
```bash
# Stop current application
pm2 stop admin-app

# Restore previous version
cd /path/to/production/
git checkout previous-stable-tag

# Restore dependencies
npm ci --production
npm run build

# Start previous version
pm2 start ecosystem.config.js --env production
```

#### 2. Database Rollback
```bash
# Stop application first
pm2 stop admin-app

# Restore database from backup
pg_restore -h localhost -U username -d database_name backup_pre_admin_*.sql

# Verify restoration
psql -h localhost -U username -d database_name -c "SELECT COUNT(*) FROM users;"
```

### Planned Rollback (Non-Critical Issues)

#### 1. Gradual Rollback Process
```bash
# Create rollback branch
git checkout -b rollback/admin-system-$(date +%Y%m%d)

# Document rollback reason
echo "Rollback reason: [describe issue]" > ROLLBACK_REASON.md
git add ROLLBACK_REASON.md
git commit -m "Document rollback reason"
```

#### 2. Database Schema Rollback
```bash
# Run rollback migration
psql -h localhost -U username -d database_name -f data/migrations/postgres/021_admin_system_rollback.sql

# Verify rollback
psql -h localhost -U username -d database_name -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_name IN ('audit_logs', 'system_config');"
# Expected: 0 (tables should be removed)
```

### Rollback Verification

#### Post-Rollback Checks
- [ ] Application starts successfully
- [ ] Database schema restored to previous state
- [ ] All existing functionality works
- [ ] No data corruption detected
- [ ] Performance metrics within normal ranges
- [ ] Security features still functional

#### Rollback Documentation
```markdown
# Rollback Report

**Date**: [rollback date]
**Time**: [rollback time]
**Duration**: [rollback duration]
**Reason**: [detailed reason for rollback]

## Actions Taken
1. [list all rollback actions]
2. [include timestamps]
3. [note any issues encountered]

## Verification Results
- [ ] Application functionality: OK/ISSUES
- [ ] Database integrity: OK/ISSUES
- [ ] Performance: OK/ISSUES
- [ ] Security: OK/ISSUES

## Next Steps
- [list any required follow-up actions]
- [schedule for retry deployment]
- [additional testing needed]
```

## Monitoring and Maintenance

### Post-Deployment Monitoring

#### 1. Application Monitoring
```bash
# Monitor application logs
pm2 logs admin-app --lines 100 --timestamp

# Monitor system resources
htop
df -h
free -m
```

#### 2. Database Monitoring
```sql
-- Monitor database connections
SELECT count(*) as connections, state 
FROM pg_stat_activity 
GROUP BY state;

-- Check slow queries
SELECT query, mean_time, calls 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;
```

#### 3. Security Monitoring
```bash
# Monitor failed login attempts
tail -f /var/log/admin-app/security.log | grep "failed_login"

# Check audit log entries
psql -d database_name -c "SELECT COUNT(*) FROM audit_logs WHERE timestamp > NOW() - INTERVAL '1 hour';"
```

### Maintenance Tasks

#### Daily Tasks
- [ ] Review application logs for errors
- [ ] Check system resource usage
- [ ] Monitor security alerts
- [ ] Verify backup completion

#### Weekly Tasks
- [ ] Review audit logs for suspicious activity
- [ ] Check database performance metrics
- [ ] Update security configurations if needed
- [ ] Test backup restoration process

#### Monthly Tasks
- [ ] Security vulnerability scan
- [ ] Performance optimization review
- [ ] User access audit
- [ ] Documentation updates

## Troubleshooting

### Common Deployment Issues

#### 1. Database Connection Issues
**Symptoms**: Application fails to start, database connection errors

**Solutions**:
```bash
# Check database connectivity
pg_isready -h localhost -p 5432

# Verify credentials
psql -h localhost -U username -d database_name -c "SELECT 1;"

# Check connection limits
psql -d database_name -c "SHOW max_connections;"
```

#### 2. Migration Failures
**Symptoms**: Migration scripts fail, missing tables/columns

**Solutions**:
```bash
# Check migration status
psql -d database_name -c "SELECT * FROM schema_migrations ORDER BY version;"

# Manually run failed migration
psql -d database_name -f data/migrations/postgres/[failed_migration].sql

# Verify schema state
psql -d database_name -c "\dt"
```

#### 3. Permission Issues
**Symptoms**: 403 errors, access denied messages

**Solutions**:
```bash
# Check file permissions
ls -la /path/to/production/
chmod 755 /path/to/production/
chown -R app:app /path/to/production/

# Verify database permissions
psql -d database_name -c "SELECT * FROM information_schema.role_table_grants WHERE grantee = 'username';"
```

#### 4. Performance Issues
**Symptoms**: Slow response times, high resource usage

**Solutions**:
```bash
# Check system resources
top
iostat 1 5
netstat -an | grep :3000

# Optimize database
psql -d database_name -c "VACUUM ANALYZE;"
psql -d database_name -c "REINDEX DATABASE database_name;"
```

### Emergency Contacts

#### Technical Contacts
- **System Administrator**: [contact information]
- **Database Administrator**: [contact information]
- **Security Team**: [contact information]
- **Development Team Lead**: [contact information]

#### Escalation Procedures
1. **Level 1**: System Administrator (immediate response)
2. **Level 2**: Development Team Lead (within 1 hour)
3. **Level 3**: Security Team (for security issues)
4. **Level 4**: Management (for critical business impact)

---

*This deployment guide should be reviewed and updated with each release to ensure accuracy and completeness.*