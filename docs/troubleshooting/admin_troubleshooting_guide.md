# Admin Management System Troubleshooting Guide

This comprehensive guide helps diagnose and resolve common issues with the admin management system.

## Table of Contents

- [Quick Diagnostic Tools](#quick-diagnostic-tools)
- [Authentication Issues](#authentication-issues)
- [Authorization and Permissions](#authorization-and-permissions)
- [User Management Issues](#user-management-issues)
- [System Configuration Problems](#system-configuration-problems)
- [Database Issues](#database-issues)
- [Email and Notifications](#email-and-notifications)
- [Performance Issues](#performance-issues)
- [Security Alerts and Incidents](#security-alerts-and-incidents)
- [API and Integration Issues](#api-and-integration-issues)
- [UI and Frontend Issues](#ui-and-frontend-issues)
- [Monitoring and Logging](#monitoring-and-logging)

## Quick Diagnostic Tools

### System Health Check Script

Create and run this diagnostic script to quickly identify common issues:

```bash
#!/bin/bash
# admin-health-check.sh

echo "=== Admin System Health Check ==="
echo "Timestamp: $(date)"
echo

# Check application status
echo "1. Application Status:"
if pm2 list | grep -q "admin-app.*online"; then
    echo "   ✅ Application is running"
else
    echo "   ❌ Application is not running"
    pm2 status
fi
echo

# Check database connectivity
echo "2. Database Connectivity:"
if psql -h localhost -U $DB_USER -d $DB_NAME -c "SELECT 1;" > /dev/null 2>&1; then
    echo "   ✅ Database connection successful"
else
    echo "   ❌ Database connection failed"
fi
echo

# Check required tables
echo "3. Database Schema:"
TABLES=$(psql -h localhost -U $DB_USER -d $DB_NAME -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_name IN ('users', 'audit_logs', 'system_config');")
if [ "$TABLES" -eq 3 ]; then
    echo "   ✅ All required tables exist"
else
    echo "   ❌ Missing required tables (found $TABLES/3)"
fi
echo

# Check API endpoints
echo "4. API Health:"
if curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/api/health | grep -q "200"; then
    echo "   ✅ API endpoints responding"
else
    echo "   ❌ API endpoints not responding"
fi
echo

# Check logs for errors
echo "5. Recent Errors:"
ERROR_COUNT=$(tail -n 100 /var/log/admin-app/error.log | grep -c "ERROR" 2>/dev/null || echo "0")
if [ "$ERROR_COUNT" -eq 0 ]; then
    echo "   ✅ No recent errors in logs"
else
    echo "   ⚠️  Found $ERROR_COUNT recent errors"
    echo "   Recent errors:"
    tail -n 10 /var/log/admin-app/error.log | grep "ERROR" | tail -n 3
fi
echo

echo "=== Health Check Complete ==="
```

### Log Analysis Commands

```bash
# Check application logs
pm2 logs admin-app --lines 50 --timestamp

# Check error logs
tail -f /var/log/admin-app/error.log

# Check security logs
tail -f /var/log/admin-app/security.log

# Check database logs
sudo tail -f /var/log/postgresql/postgresql-*.log

# Check nginx/apache logs
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log
```

## Authentication Issues

### Issue: Cannot Access Admin Interface

#### Symptoms
- Login page loads but admin sections are not accessible
- "Insufficient permissions" errors
- Redirect loops between login and admin pages

#### Diagnostic Steps
```bash
# Check user role in database
psql -d database_name -c "SELECT id, email, username, role, is_active FROM users WHERE email = 'admin@example.com';"

# Check session data
psql -d database_name -c "SELECT * FROM sessions WHERE user_id = 'user-id-here';"

# Check application logs for authentication errors
pm2 logs admin-app | grep -i "auth\|permission\|role"
```

#### Solutions

**1. User Role Not Set Correctly**
```sql
-- Update user role to admin or super_admin
UPDATE users SET role = 'super_admin' WHERE email = 'admin@example.com';

-- Verify the change
SELECT email, role FROM users WHERE email = 'admin@example.com';
```

**2. Session Issues**
```bash
# Clear user sessions
psql -d database_name -c "DELETE FROM sessions WHERE user_id = 'user-id-here';"

# Or clear all sessions (forces all users to re-login)
psql -d database_name -c "DELETE FROM sessions;"
```

**3. Application Configuration**
```javascript
// Check config/auth.js
module.exports = {
  roles: {
    SUPER_ADMIN: 'super_admin',
    ADMIN: 'admin',
    USER: 'user'
  },
  permissions: {
    MANAGE_USERS: ['super_admin', 'admin'],
    MANAGE_ADMINS: ['super_admin'],
    SYSTEM_CONFIG: ['super_admin']
  }
};
```

### Issue: First-Run Setup Not Working

#### Symptoms
- Setup page not loading
- Cannot create super admin account
- Setup process hangs or errors

#### Diagnostic Steps
```bash
# Check if super admin already exists
psql -d database_name -c "SELECT COUNT(*) FROM users WHERE role = 'super_admin';"

# Check setup API endpoint
curl -X GET http://localhost:3000/api/admin/setup/check-first-run

# Check for setup-related errors
pm2 logs admin-app | grep -i "setup\|first-run"
```

#### Solutions

**1. Super Admin Already Exists**
```sql
-- If you need to reset first-run setup, temporarily remove super admin
UPDATE users SET role = 'admin' WHERE role = 'super_admin';

-- Or delete the super admin (be careful!)
DELETE FROM users WHERE role = 'super_admin' AND email = 'old-admin@example.com';
```

**2. Database Migration Issues**
```bash
# Re-run the admin system migration
psql -d database_name -f data/migrations/postgres/018_admin_management_system.sql

# Check if system_config table exists
psql -d database_name -c "\dt system_config"
```

**3. API Endpoint Issues**
```bash
# Check if setup routes are registered
curl -X GET http://localhost:3000/api/admin/setup/check-first-run -v

# Restart application
pm2 restart admin-app
```

### Issue: Multi-Factor Authentication Problems

#### Symptoms
- MFA setup fails
- Cannot verify MFA codes
- MFA bypass not working

#### Diagnostic Steps
```bash
# Check MFA configuration
psql -d database_name -c "SELECT key, value FROM system_config WHERE key LIKE '%mfa%';"

# Check user MFA status
psql -d database_name -c "SELECT id, email, mfa_enabled, mfa_secret FROM users WHERE email = 'user@example.com';"

# Check MFA-related logs
pm2 logs admin-app | grep -i "mfa\|totp\|2fa"
```

#### Solutions

**1. MFA Secret Issues**
```sql
-- Reset user's MFA secret
UPDATE users SET mfa_secret = NULL, mfa_enabled = false WHERE email = 'user@example.com';
```

**2. Time Synchronization Issues**
```bash
# Check system time
date
timedatectl status

# Sync time if needed
sudo ntpdate -s time.nist.gov
```

**3. MFA Configuration**
```javascript
// Check MFA settings in config
const mfaConfig = {
  issuer: 'Your App Name',
  window: 2, // Allow 2 time steps (60 seconds)
  step: 30   // 30-second time step
};
```

## Authorization and Permissions

### Issue: Admin Cannot Perform Expected Actions

#### Symptoms
- "Access denied" errors for admin users
- Admin interface shows but actions fail
- Inconsistent permission behavior

#### Diagnostic Steps
```bash
# Check user permissions
psql -d database_name -c "SELECT u.email, u.role, p.permission_name FROM users u LEFT JOIN user_permissions up ON u.id = up.user_id LEFT JOIN permissions p ON up.permission_id = p.id WHERE u.email = 'admin@example.com';"

# Check role-based permissions
node -e "
const { hasPermission } = require('./lib/auth/permissions');
console.log('Can manage users:', hasPermission('admin', 'MANAGE_USERS'));
console.log('Can manage admins:', hasPermission('admin', 'MANAGE_ADMINS'));
"

# Check API middleware logs
pm2 logs admin-app | grep -i "permission\|authorize\|forbidden"
```

#### Solutions

**1. Role Hierarchy Issues**
```javascript
// Verify role hierarchy in lib/auth/permissions.js
const ROLE_HIERARCHY = {
  'super_admin': 3,
  'admin': 2,
  'user': 1
};

const hasRole = (userRole, requiredRole) => {
  return ROLE_HIERARCHY[userRole] >= ROLE_HIERARCHY[requiredRole];
};
```

**2. Permission Middleware Issues**
```javascript
// Check middleware in lib/middleware/admin-auth.ts
export const requireRole = (requiredRole: string) => {
  return (req: Request, res: Response, next: NextFunction) => {
    const user = req.user;
    
    if (!user || !hasRole(user.role, requiredRole)) {
      return res.status(403).json({
        error: 'Insufficient permissions',
        required: requiredRole,
        current: user?.role
      });
    }
    
    next();
  };
};
```

**3. Frontend Permission Checks**
```typescript
// Verify frontend permission checks in components
const { user, hasRole } = useAuth();

if (!hasRole('admin')) {
  return <UnauthorizedPage />;
}
```

### Issue: Permission Caching Problems

#### Symptoms
- Permission changes not taking effect immediately
- Inconsistent permission behavior
- Users see old permissions after role changes

#### Solutions

**1. Clear Permission Cache**
```bash
# If using Redis for caching
redis-cli FLUSHDB

# If using in-memory cache, restart application
pm2 restart admin-app
```

**2. Force Session Refresh**
```sql
-- Force users to re-authenticate
DELETE FROM sessions WHERE user_id IN (
  SELECT id FROM users WHERE role IN ('admin', 'super_admin')
);
```

## User Management Issues

### Issue: Cannot Create New Users

#### Symptoms
- User creation form fails
- Validation errors on user creation
- Database errors when creating users

#### Diagnostic Steps
```bash
# Check user creation API
curl -X POST http://localhost:3000/api/admin/users \
  -H "Content-Type: application/json" \
  -H "Cookie: session=your-session-cookie" \
  -d '{"email":"test@example.com","username":"testuser","password":"TestPassword123!"}'

# Check database constraints
psql -d database_name -c "\d users"

# Check for validation errors
pm2 logs admin-app | grep -i "validation\|constraint\|duplicate"
```

#### Solutions

**1. Email/Username Uniqueness Issues**
```sql
-- Check for existing users
SELECT email, username FROM users WHERE email = 'test@example.com' OR username = 'testuser';

-- Remove duplicate if needed
DELETE FROM users WHERE email = 'duplicate@example.com' AND created_at < (SELECT MAX(created_at) FROM users WHERE email = 'duplicate@example.com');
```

**2. Password Validation Issues**
```javascript
// Check password validation in lib/auth/setup-validation.ts
const validatePassword = (password: string) => {
  const minLength = 12;
  const hasUpper = /[A-Z]/.test(password);
  const hasLower = /[a-z]/.test(password);
  const hasNumber = /\d/.test(password);
  const hasSpecial = /[!@#$%^&*(),.?":{}|<>]/.test(password);
  
  return {
    valid: password.length >= minLength && hasUpper && hasLower && hasNumber && hasSpecial,
    errors: [
      password.length < minLength && `Minimum ${minLength} characters required`,
      !hasUpper && 'Uppercase letter required',
      !hasLower && 'Lowercase letter required',
      !hasNumber && 'Number required',
      !hasSpecial && 'Special character required'
    ].filter(Boolean)
  };
};
```

**3. Database Connection Issues**
```bash
# Check database connection pool
psql -d database_name -c "SELECT count(*) as active_connections FROM pg_stat_activity WHERE state = 'active';"

# Check for connection limits
psql -d database_name -c "SHOW max_connections;"
```

### Issue: Bulk Operations Failing

#### Symptoms
- Bulk user operations timeout
- Partial completion of bulk operations
- Memory issues during bulk operations

#### Solutions

**1. Batch Size Optimization**
```javascript
// Reduce batch size in bulk operations
const BATCH_SIZE = 100; // Reduce from larger number

const processBulkOperation = async (userIds, operation) => {
  const batches = chunk(userIds, BATCH_SIZE);
  
  for (const batch of batches) {
    await processBatch(batch, operation);
    // Add delay between batches
    await new Promise(resolve => setTimeout(resolve, 100));
  }
};
```

**2. Database Transaction Optimization**
```sql
-- Use smaller transactions
BEGIN;
UPDATE users SET is_active = false WHERE id IN (SELECT id FROM users LIMIT 100);
COMMIT;
```

**3. Memory Management**
```javascript
// Stream large datasets instead of loading all into memory
const stream = require('stream');
const { pipeline } = require('stream/promises');

const processUsersStream = async () => {
  await pipeline(
    getUsersStream(),
    new stream.Transform({
      objectMode: true,
      transform(user, encoding, callback) {
        // Process individual user
        processUser(user);
        callback();
      }
    })
  );
};
```

## System Configuration Problems

### Issue: Configuration Changes Not Taking Effect

#### Symptoms
- System configuration updates don't apply
- Old configuration values still in use
- Configuration UI shows wrong values

#### Diagnostic Steps
```bash
# Check system configuration in database
psql -d database_name -c "SELECT key, value, category, updated_at FROM system_config ORDER BY category, key;"

# Check configuration cache
node -e "
const config = require('./lib/config/system-config');
console.log('Current config:', config.getAll());
"

# Check configuration loading logs
pm2 logs admin-app | grep -i "config\|setting"
```

#### Solutions

**1. Clear Configuration Cache**
```bash
# Restart application to reload configuration
pm2 restart admin-app

# Or clear specific cache if using Redis
redis-cli DEL "system_config:*"
```

**2. Verify Database Updates**
```sql
-- Check if configuration was actually updated
SELECT key, value, updated_at, updated_by FROM system_config 
WHERE key = 'password_min_length' 
ORDER BY updated_at DESC;

-- Manually update if needed
UPDATE system_config 
SET value = '14', updated_at = NOW(), updated_by = 'admin-user-id' 
WHERE key = 'password_min_length';
```

**3. Configuration Loading Issues**
```javascript
// Check configuration loader in lib/config/system-config.ts
class SystemConfig {
  private cache = new Map();
  private lastRefresh = 0;
  private CACHE_TTL = 5 * 60 * 1000; // 5 minutes
  
  async get(key: string) {
    if (this.shouldRefresh()) {
      await this.refresh();
    }
    return this.cache.get(key);
  }
  
  private shouldRefresh() {
    return Date.now() - this.lastRefresh > this.CACHE_TTL;
  }
}
```

### Issue: Email Configuration Problems

#### Symptoms
- Emails not being sent
- SMTP connection errors
- Email templates not loading

#### Diagnostic Steps
```bash
# Test SMTP connection
node -e "
const nodemailer = require('nodemailer');
const transporter = nodemailer.createTransporter({
  host: process.env.SMTP_HOST,
  port: process.env.SMTP_PORT,
  auth: {
    user: process.env.SMTP_USER,
    pass: process.env.SMTP_PASS
  }
});
transporter.verify((error, success) => {
  console.log(error ? 'SMTP Error:' + error : 'SMTP OK');
});
"

# Check email queue
psql -d database_name -c "SELECT * FROM email_queue WHERE status = 'failed' ORDER BY created_at DESC LIMIT 10;"

# Check email logs
pm2 logs admin-app | grep -i "email\|smtp\|mail"
```

#### Solutions

**1. SMTP Configuration Issues**
```javascript
// Verify SMTP settings in config/email.js
const emailConfig = {
  host: process.env.SMTP_HOST,
  port: parseInt(process.env.SMTP_PORT) || 587,
  secure: process.env.SMTP_PORT === '465',
  auth: {
    user: process.env.SMTP_USER,
    pass: process.env.SMTP_PASS
  },
  tls: {
    rejectUnauthorized: false // Only for development
  }
};
```

**2. Email Template Issues**
```bash
# Check if email templates exist
ls -la ui_launchers/web_ui/src/lib/email/templates/

# Verify template compilation
node -e "
const { compileTemplate } = require('./lib/email/template-engine');
console.log(compileTemplate('welcome', { username: 'test' }));
"
```

**3. Email Queue Processing**
```bash
# Check email queue processor
pm2 list | grep email-queue

# Restart email queue processor if needed
pm2 restart email-queue-processor

# Process failed emails manually
node scripts/process-failed-emails.js
```

## Database Issues

### Issue: Database Connection Problems

#### Symptoms
- "Connection refused" errors
- Timeout errors
- Connection pool exhausted

#### Diagnostic Steps
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Check database connectivity
pg_isready -h localhost -p 5432

# Check connection limits
psql -d database_name -c "SELECT count(*) as connections FROM pg_stat_activity;"
psql -d database_name -c "SHOW max_connections;"

# Check for long-running queries
psql -d database_name -c "SELECT pid, now() - pg_stat_activity.query_start AS duration, query FROM pg_stat_activity WHERE (now() - pg_stat_activity.query_start) > interval '5 minutes';"
```

#### Solutions

**1. Connection Pool Configuration**
```javascript
// Adjust connection pool settings in lib/database/client.ts
const pool = new Pool({
  host: process.env.DB_HOST,
  port: process.env.DB_PORT,
  database: process.env.DB_NAME,
  user: process.env.DB_USER,
  password: process.env.DB_PASSWORD,
  max: 20, // Reduce if hitting connection limits
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,
});
```

**2. Kill Long-Running Queries**
```sql
-- Kill specific query
SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE pid = 12345;

-- Kill all idle connections
SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'idle' AND query_start < now() - interval '1 hour';
```

**3. Database Maintenance**
```sql
-- Vacuum and analyze tables
VACUUM ANALYZE users;
VACUUM ANALYZE audit_logs;
VACUUM ANALYZE system_config;

-- Reindex if needed
REINDEX TABLE users;
```

### Issue: Slow Database Queries

#### Symptoms
- Slow page loading
- API timeouts
- High database CPU usage

#### Diagnostic Steps
```sql
-- Check slow queries
SELECT query, mean_time, calls, total_time 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;

-- Check missing indexes
SELECT schemaname, tablename, attname, n_distinct, correlation 
FROM pg_stats 
WHERE schemaname = 'public' 
AND n_distinct > 100;

-- Check table sizes
SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size 
FROM pg_tables 
WHERE schemaname = 'public' 
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

#### Solutions

**1. Add Missing Indexes**
```sql
-- Add indexes for common queries
CREATE INDEX CONCURRENTLY idx_users_email_role ON users (email, role);
CREATE INDEX CONCURRENTLY idx_audit_logs_user_timestamp ON audit_logs (user_id, timestamp DESC);
CREATE INDEX CONCURRENTLY idx_audit_logs_action_timestamp ON audit_logs (action, timestamp DESC);
```

**2. Query Optimization**
```sql
-- Optimize user list query
EXPLAIN ANALYZE 
SELECT u.id, u.email, u.username, u.role, u.is_active, u.last_login 
FROM users u 
WHERE u.role IN ('user', 'admin') 
ORDER BY u.created_at DESC 
LIMIT 20 OFFSET 0;
```

**3. Partition Large Tables**
```sql
-- Partition audit_logs table by date
CREATE TABLE audit_logs_partitioned (
    LIKE audit_logs INCLUDING ALL
) PARTITION BY RANGE (timestamp);

-- Create monthly partitions
CREATE TABLE audit_logs_2024_01 PARTITION OF audit_logs_partitioned
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
```

## Email and Notifications

### Issue: Emails Not Being Delivered

#### Symptoms
- Users not receiving welcome emails
- Password reset emails not arriving
- Admin notifications missing

#### Diagnostic Steps
```bash
# Check email queue status
psql -d database_name -c "SELECT status, COUNT(*) FROM email_queue GROUP BY status;"

# Check recent email attempts
psql -d database_name -c "SELECT * FROM email_queue WHERE created_at > NOW() - INTERVAL '1 hour' ORDER BY created_at DESC;"

# Test email sending
node scripts/test-email.js admin@example.com "Test Subject" "Test message"

# Check email service logs
pm2 logs email-service
```

#### Solutions

**1. SMTP Authentication Issues**
```javascript
// Test SMTP credentials
const testSMTP = async () => {
  const transporter = nodemailer.createTransporter({
    host: process.env.SMTP_HOST,
    port: process.env.SMTP_PORT,
    secure: process.env.SMTP_PORT === '465',
    auth: {
      user: process.env.SMTP_USER,
      pass: process.env.SMTP_PASS
    }
  });
  
  try {
    await transporter.verify();
    console.log('SMTP connection successful');
  } catch (error) {
    console.error('SMTP connection failed:', error);
  }
};
```

**2. Email Queue Processing**
```bash
# Restart email queue processor
pm2 restart email-queue-processor

# Process stuck emails manually
node -e "
const { processEmailQueue } = require('./lib/email/email-queue');
processEmailQueue().then(() => console.log('Queue processed'));
"
```

**3. Email Template Issues**
```bash
# Check template compilation
node -e "
const { renderTemplate } = require('./lib/email/template-engine');
const html = renderTemplate('welcome', { 
  username: 'Test User',
  loginUrl: 'https://example.com/login'
});
console.log('Template rendered:', html.length > 0);
"
```

### Issue: Email Delivery Delays

#### Symptoms
- Emails arrive hours after being sent
- Email queue backing up
- High email processing times

#### Solutions

**1. Increase Email Processing Concurrency**
```javascript
// Adjust email queue processor
const EMAIL_CONCURRENCY = 5; // Process 5 emails simultaneously

const processEmailQueue = async () => {
  const pendingEmails = await getEmailQueue('pending', EMAIL_CONCURRENCY);
  
  await Promise.all(
    pendingEmails.map(email => processEmail(email))
  );
};
```

**2. Optimize Email Templates**
```javascript
// Cache compiled templates
const templateCache = new Map();

const getCompiledTemplate = (templateName) => {
  if (!templateCache.has(templateName)) {
    const compiled = compileTemplate(templateName);
    templateCache.set(templateName, compiled);
  }
  return templateCache.get(templateName);
};
```

**3. Email Rate Limiting**
```javascript
// Implement rate limiting for email sending
const emailRateLimit = {
  perSecond: 10,
  perMinute: 100,
  perHour: 1000
};

const rateLimiter = new RateLimiter(emailRateLimit);
```

## Performance Issues

### Issue: Slow Admin Interface Loading

#### Symptoms
- Admin pages take long to load
- API responses are slow
- Browser becomes unresponsive

#### Diagnostic Steps
```bash
# Check server response times
curl -w "@curl-format.txt" -o /dev/null -s "http://localhost:3000/api/admin/users"

# Monitor server resources
top -p $(pgrep -f "node.*admin")
iostat 1 5

# Check database query performance
psql -d database_name -c "SELECT query, mean_time, calls FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 5;"

# Profile API endpoints
node --prof app.js
```

#### Solutions

**1. Database Query Optimization**
```sql
-- Add pagination to large queries
SELECT * FROM users 
WHERE role = 'user' 
ORDER BY created_at DESC 
LIMIT 20 OFFSET 0;

-- Use indexes for filtering
CREATE INDEX CONCURRENTLY idx_users_role_active ON users (role, is_active);
```

**2. API Response Caching**
```javascript
// Implement response caching
const cache = new Map();
const CACHE_TTL = 5 * 60 * 1000; // 5 minutes

const getCachedResponse = (key) => {
  const cached = cache.get(key);
  if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
    return cached.data;
  }
  return null;
};
```

**3. Frontend Optimization**
```typescript
// Implement virtual scrolling for large lists
import { FixedSizeList as List } from 'react-window';

const VirtualizedUserList = ({ users }) => (
  <List
    height={600}
    itemCount={users.length}
    itemSize={50}
    itemData={users}
  >
    {UserRow}
  </List>
);
```

### Issue: High Memory Usage

#### Symptoms
- Application crashes with out-of-memory errors
- Server becomes unresponsive
- Memory usage continuously increases

#### Diagnostic Steps
```bash
# Monitor memory usage
ps aux | grep node
free -m
cat /proc/meminfo

# Check for memory leaks
node --inspect app.js
# Then use Chrome DevTools to analyze memory

# Monitor garbage collection
node --trace-gc app.js
```

#### Solutions

**1. Memory Leak Detection**
```javascript
// Add memory monitoring
const monitorMemory = () => {
  const usage = process.memoryUsage();
  console.log('Memory usage:', {
    rss: Math.round(usage.rss / 1024 / 1024) + 'MB',
    heapTotal: Math.round(usage.heapTotal / 1024 / 1024) + 'MB',
    heapUsed: Math.round(usage.heapUsed / 1024 / 1024) + 'MB'
  });
};

setInterval(monitorMemory, 60000); // Every minute
```

**2. Optimize Large Data Processing**
```javascript
// Stream large datasets instead of loading into memory
const processLargeDataset = async () => {
  const stream = getUsersStream();
  
  for await (const user of stream) {
    await processUser(user);
    // Process one at a time to avoid memory buildup
  }
};
```

**3. Garbage Collection Tuning**
```bash
# Start application with optimized GC settings
node --max-old-space-size=4096 --gc-interval=100 app.js
```

## Security Alerts and Incidents

### Issue: Multiple Failed Login Attempts

#### Symptoms
- Security alerts about failed logins
- Accounts being locked out
- Suspicious IP addresses in logs

#### Diagnostic Steps
```bash
# Check failed login attempts
psql -d database_name -c "SELECT ip_address, COUNT(*) as attempts, MAX(timestamp) as last_attempt FROM audit_logs WHERE action = 'login_failed' AND timestamp > NOW() - INTERVAL '1 hour' GROUP BY ip_address ORDER BY attempts DESC;"

# Check locked accounts
psql -d database_name -c "SELECT email, locked_until FROM users WHERE locked_until > NOW();"

# Analyze attack patterns
pm2 logs admin-app | grep "failed_login" | tail -50
```

#### Solutions

**1. IP Blocking**
```bash
# Block suspicious IP addresses
sudo iptables -A INPUT -s 192.168.1.100 -j DROP

# Or use fail2ban
sudo fail2ban-client set admin-app banip 192.168.1.100
```

**2. Increase Security Measures**
```sql
-- Temporarily reduce login attempt limits
UPDATE system_config SET value = '3' WHERE key = 'max_login_attempts';

-- Increase lockout duration
UPDATE system_config SET value = '1800' WHERE key = 'lockout_duration';
```

**3. Enable Additional Monitoring**
```javascript
// Add real-time security monitoring
const securityMonitor = {
  checkFailedLogins: async () => {
    const recentFailures = await getFailedLogins(15 * 60 * 1000); // 15 minutes
    
    if (recentFailures.length > 10) {
      await sendSecurityAlert('High number of failed logins detected');
    }
  }
};

setInterval(securityMonitor.checkFailedLogins, 5 * 60 * 1000); // Every 5 minutes
```

### Issue: Suspicious Admin Activity

#### Symptoms
- Unusual admin actions in audit logs
- Admin accounts accessed from new locations
- Bulk operations at unusual times

#### Diagnostic Steps
```bash
# Check recent admin activity
psql -d database_name -c "SELECT u.email, a.action, a.timestamp, a.ip_address FROM audit_logs a JOIN users u ON a.user_id = u.id WHERE u.role IN ('admin', 'super_admin') AND a.timestamp > NOW() - INTERVAL '24 hours' ORDER BY a.timestamp DESC;"

# Check for unusual patterns
psql -d database_name -c "SELECT action, COUNT(*) as count FROM audit_logs WHERE user_id = 'suspicious-user-id' AND timestamp > NOW() - INTERVAL '1 hour' GROUP BY action ORDER BY count DESC;"

# Check login locations
psql -d database_name -c "SELECT DISTINCT ip_address, user_agent FROM audit_logs WHERE action = 'login_success' AND user_id = 'admin-user-id' ORDER BY timestamp DESC;"
```

#### Solutions

**1. Immediate Security Response**
```sql
-- Suspend suspicious admin account
UPDATE users SET is_active = false WHERE id = 'suspicious-user-id';

-- Force logout of all sessions for the user
DELETE FROM sessions WHERE user_id = 'suspicious-user-id';
```

**2. Enhanced Monitoring**
```javascript
// Implement anomaly detection
const detectAnomalies = async (userId) => {
  const recentActivity = await getRecentActivity(userId, 24 * 60 * 60 * 1000);
  const normalPattern = await getNormalActivityPattern(userId);
  
  const anomalies = [];
  
  // Check for unusual times
  const unusualTimes = recentActivity.filter(activity => 
    isOutsideNormalHours(activity.timestamp, normalPattern.normalHours)
  );
  
  // Check for unusual locations
  const unusualLocations = recentActivity.filter(activity =>
    !normalPattern.normalLocations.includes(activity.ipAddress)
  );
  
  return { unusualTimes, unusualLocations };
};
```

**3. Implement Additional Controls**
```sql
-- Require MFA for all admin accounts
UPDATE users SET mfa_required = true WHERE role IN ('admin', 'super_admin');

-- Reduce session timeout for admin accounts
UPDATE system_config SET value = '900' WHERE key = 'session_timeout_admin'; -- 15 minutes
```

## API and Integration Issues

### Issue: API Endpoints Returning Errors

#### Symptoms
- 500 Internal Server Error responses
- API timeouts
- Malformed JSON responses

#### Diagnostic Steps
```bash
# Test API endpoints
curl -X GET http://localhost:3000/api/admin/users -H "Cookie: session=your-session" -v

# Check API logs
pm2 logs admin-app | grep -E "(GET|POST|PUT|DELETE) /api/admin"

# Check for unhandled errors
pm2 logs admin-app | grep -i "unhandled\|uncaught\|error"

# Test database connectivity from API
curl -X GET http://localhost:3000/api/health/database
```

#### Solutions

**1. Error Handling Middleware**
```javascript
// Add comprehensive error handling
const errorHandler = (err, req, res, next) => {
  console.error('API Error:', err);
  
  if (err.name === 'ValidationError') {
    return res.status(400).json({
      error: 'Validation Error',
      details: err.details
    });
  }
  
  if (err.name === 'DatabaseError') {
    return res.status(500).json({
      error: 'Database Error',
      message: 'Please try again later'
    });
  }
  
  res.status(500).json({
    error: 'Internal Server Error',
    requestId: req.id
  });
};

app.use(errorHandler);
```

**2. API Validation**
```javascript
// Add request validation
const validateUserCreation = (req, res, next) => {
  const { email, username, password } = req.body;
  
  const errors = [];
  
  if (!email || !isValidEmail(email)) {
    errors.push('Valid email is required');
  }
  
  if (!username || username.length < 3) {
    errors.push('Username must be at least 3 characters');
  }
  
  if (!password || !isValidPassword(password)) {
    errors.push('Password does not meet requirements');
  }
  
  if (errors.length > 0) {
    return res.status(400).json({ errors });
  }
  
  next();
};
```

**3. Database Connection Handling**
```javascript
// Add database connection retry logic
const withDatabaseRetry = async (operation, maxRetries = 3) => {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await operation();
    } catch (error) {
      if (attempt === maxRetries) {
        throw error;
      }
      
      console.log(`Database operation failed, attempt ${attempt}/${maxRetries}`);
      await new Promise(resolve => setTimeout(resolve, 1000 * attempt));
    }
  }
};
```

### Issue: CORS and Cross-Origin Problems

#### Symptoms
- Browser console shows CORS errors
- API requests blocked by browser
- Preflight request failures

#### Solutions

**1. Configure CORS Properly**
```javascript
// Configure CORS middleware
const corsOptions = {
  origin: [
    'http://localhost:3000',
    'https://yourdomain.com',
    'https://admin.yourdomain.com'
  ],
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization', 'X-Requested-With']
};

app.use(cors(corsOptions));
```

**2. Handle Preflight Requests**
```javascript
// Handle OPTIONS requests
app.options('*', (req, res) => {
  res.header('Access-Control-Allow-Origin', req.headers.origin);
  res.header('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS');
  res.header('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  res.header('Access-Control-Allow-Credentials', true);
  res.sendStatus(200);
});
```

## UI and Frontend Issues

### Issue: Admin Interface Not Loading

#### Symptoms
- Blank admin pages
- JavaScript errors in browser console
- Components not rendering

#### Diagnostic Steps
```bash
# Check browser console for errors
# Open browser dev tools and check Console tab

# Check if JavaScript bundles are loading
curl -I http://localhost:3000/_next/static/js/[bundle-name].js

# Check Next.js build
npm run build
npm run start

# Check for TypeScript errors
npm run type-check
```

#### Solutions

**1. Fix JavaScript Errors**
```typescript
// Check for undefined variables or functions
const AdminDashboard = () => {
  const { user, loading } = useAuth();
  
  if (loading) {
    return <LoadingSpinner />;
  }
  
  if (!user || !hasRole(user.role, 'admin')) {
    return <UnauthorizedPage />;
  }
  
  return (
    <div>
      {/* Admin dashboard content */}
    </div>
  );
};
```

**2. Fix Build Issues**
```bash
# Clear Next.js cache
rm -rf .next
npm run build

# Check for missing dependencies
npm install

# Fix TypeScript errors
npm run type-check
```

**3. Fix Routing Issues**
```typescript
// Check route configuration
const AdminLayout = () => {
  return (
    <AdminRoute requiredRole="admin">
      <Routes>
        <Route path="/admin" element={<AdminDashboard />} />
        <Route path="/admin/users" element={<UserManagement />} />
        <Route path="/admin/settings" element={<SystemSettings />} />
      </Routes>
    </AdminRoute>
  );
};
```

### Issue: Form Validation Not Working

#### Symptoms
- Forms submit with invalid data
- Validation messages not showing
- Client-side validation bypassed

#### Solutions

**1. Fix Form Validation**
```typescript
// Implement proper form validation
const UserCreationForm = () => {
  const [errors, setErrors] = useState<Record<string, string>>({});
  
  const validateForm = (data: UserFormData) => {
    const newErrors: Record<string, string> = {};
    
    if (!data.email || !isValidEmail(data.email)) {
      newErrors.email = 'Valid email is required';
    }
    
    if (!data.password || !isValidPassword(data.password)) {
      newErrors.password = 'Password does not meet requirements';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };
  
  const handleSubmit = (data: UserFormData) => {
    if (validateForm(data)) {
      // Submit form
    }
  };
};
```

**2. Add Server-Side Validation**
```javascript
// Always validate on server side
app.post('/api/admin/users', validateUserData, async (req, res) => {
  try {
    const user = await createUser(req.body);
    res.json({ success: true, user });
  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});
```

## Monitoring and Logging

### Issue: Missing or Incomplete Logs

#### Symptoms
- Log files not being created
- Missing audit trail entries
- Incomplete error information

#### Solutions

**1. Configure Logging Properly**
```javascript
// Configure Winston logger
const winston = require('winston');

const logger = winston.createLogger({
  level: 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.errors({ stack: true }),
    winston.format.json()
  ),
  transports: [
    new winston.transports.File({ filename: 'logs/error.log', level: 'error' }),
    new winston.transports.File({ filename: 'logs/combined.log' }),
    new winston.transports.Console({
      format: winston.format.simple()
    })
  ]
});
```

**2. Ensure Audit Logging**
```javascript
// Add audit logging to all admin actions
const auditLogger = {
  log: async (userId, action, resourceType, resourceId, details, req) => {
    await db.query(
      'INSERT INTO audit_logs (user_id, action, resource_type, resource_id, details, ip_address, user_agent, timestamp) VALUES ($1, $2, $3, $4, $5, $6, $7, NOW())',
      [userId, action, resourceType, resourceId, JSON.stringify(details), req.ip, req.get('User-Agent')]
    );
  }
};
```

**3. Log Rotation Configuration**
```bash
# Configure logrotate
cat > /etc/logrotate.d/admin-app << EOF
/var/log/admin-app/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 app app
    postrotate
        pm2 reloadLogs
    endscript
}
EOF
```

---

*This troubleshooting guide should be updated regularly as new issues are discovered and resolved. Keep it current with system changes and user feedback.*