# AI Karen - Production Troubleshooting Guide

This guide provides solutions to common issues encountered in production deployment and operation of AI Karen.

## Table of Contents

1. [General Troubleshooting](#general-troubleshooting)
2. [Deployment Issues](#deployment-issues)
3. [Authentication Problems](#authentication-problems)
4. [Database Issues](#database-issues)
5. [Performance Problems](#performance-problems)
6. [SSL/TLS Issues](#ssltls-issues)
7. [Monitoring and Logging](#monitoring-and-logging)
8. [Emergency Procedures](#emergency-procedures)

## General Troubleshooting

### Quick Diagnostic Commands

```bash
# Check service status
sudo systemctl status ai-karen-backend ai-karen-frontend nginx postgresql redis

# Check logs
sudo journalctl -u ai-karen-backend -f
sudo journalctl -u ai-karen-frontend -f
tail -f /var/log/ai-karen/app.log

# Check system resources
htop
df -h
free -h

# Check network connectivity
curl -I https://your-domain.com/api/health
netstat -tlnp | grep -E "(8000|3000|80|443)"
```

### Log Locations

- **Application Logs**: `/var/log/ai-karen/`
- **System Logs**: `/var/log/syslog`
- **Nginx Logs**: `/var/log/nginx/`
- **PostgreSQL Logs**: `/var/log/postgresql/`
- **Redis Logs**: `/var/log/redis/`

## Deployment Issues

### Issue: Service Won't Start

**Symptoms:**
- `systemctl start ai-karen-backend` fails
- Service shows "failed" status

**Diagnosis:**
```bash
# Check detailed error
sudo journalctl -u ai-karen-backend --no-pager -l

# Check configuration
sudo systemctl cat ai-karen-backend

# Verify file permissions
ls -la /opt/ai-karen/app/
```

**Solutions:**

1. **Permission Issues:**
```bash
sudo chown -R ai-karen:ai-karen /opt/ai-karen/
sudo chmod +x /opt/ai-karen/app/start.py
```

2. **Python Environment Issues:**
```bash
cd /opt/ai-karen/app
source venv/bin/activate
python -c "import sys; print(sys.path)"
pip install -r requirements.txt
```

3. **Configuration Issues:**
```bash
# Validate environment file
python scripts/validate_production_config.py

# Check for syntax errors
python -m py_compile start.py
```

### Issue: Port Already in Use

**Symptoms:**
- "Address already in use" error
- Service fails to bind to port

**Diagnosis:**
```bash
# Check what's using the port
sudo netstat -tlnp | grep :8000
sudo lsof -i :8000
```

**Solutions:**

1. **Kill conflicting process:**
```bash
sudo kill -9 <PID>
```

2. **Change port in configuration:**
```bash
# Edit .env file
nano .env
# Change KAREN_BACKEND_PORT=8001
```

3. **Check for zombie processes:**
```bash
ps aux | grep python
sudo pkill -f "python.*start.py"
```

### Issue: Database Connection Failed

**Symptoms:**
- "Connection refused" errors
- Database timeout errors

**Diagnosis:**
```bash
# Test database connection
psql -h localhost -U ai_karen_user -d ai_karen_prod

# Check PostgreSQL status
sudo systemctl status postgresql

# Check database logs
sudo tail -f /var/log/postgresql/postgresql-*.log
```

**Solutions:**

1. **Start PostgreSQL:**
```bash
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

2. **Fix connection string:**
```bash
# Verify database URL in .env
grep AUTH_DATABASE_URL .env

# Test connection manually
python -c "
import asyncpg
import asyncio
async def test():
    conn = await asyncpg.connect('postgresql://ai_karen_user:password@localhost/ai_karen_prod')
    await conn.close()
asyncio.run(test())
"
```

3. **Reset database password:**
```bash
sudo -u postgres psql
ALTER USER ai_karen_user WITH PASSWORD 'new_password';
\q
```

## Authentication Problems

### Issue: Admin Login Fails

**Symptoms:**
- Cannot login with admin@example.com:adminadmin
- "Invalid credentials" error

**Diagnosis:**
```bash
# Check if admin user exists
cd /opt/ai-karen/app
source venv/bin/activate
python -c "
from src.services.auth.auth_service import AuthService
import asyncio
async def check():
    auth = AuthService()
    user = await auth.get_user_by_email('admin@example.com')
    print(f'User exists: {user is not None}')
asyncio.run(check())
"
```

**Solutions:**

1. **Create admin user:**
```bash
python scripts/create_admin_user.py
```

2. **Reset admin password:**
```bash
python scripts/reset_admin_password.py
```

3. **Check authentication configuration:**
```bash
grep -E "(AUTH_|JWT_)" .env
```

### Issue: Session Expires Immediately

**Symptoms:**
- User gets logged out immediately after login
- Session cookies not set

**Diagnosis:**
```bash
# Check session configuration
grep SESSION .env

# Test cookie settings
curl -I https://your-domain.com/api/auth/login
```

**Solutions:**

1. **Fix cookie security settings:**
```bash
# In .env file
AUTH_SESSION_COOKIE_SECURE=true  # Only for HTTPS
AUTH_SESSION_COOKIE_HTTPONLY=true
AUTH_SESSION_COOKIE_SAMESITE=strict
```

2. **Check domain configuration:**
```bash
# Ensure domain matches
grep DOMAIN .env
```

### Issue: JWT Token Invalid

**Symptoms:**
- "Invalid token" errors
- Authentication randomly fails

**Solutions:**

1. **Regenerate JWT secret:**
```bash
# Generate new secret
python -c "import secrets; print(secrets.token_urlsafe(64))"

# Update .env
AUTH_SECRET_KEY=new_generated_secret
JWT_SECRET_KEY=new_generated_secret
```

2. **Check token expiration:**
```bash
grep TOKEN_TIMEOUT .env
```

## Database Issues

### Issue: Database Connection Pool Exhausted

**Symptoms:**
- "Connection pool exhausted" errors
- Slow database responses

**Diagnosis:**
```bash
# Check active connections
sudo -u postgres psql -c "SELECT count(*) FROM pg_stat_activity WHERE datname='ai_karen_prod';"

# Check pool configuration
grep POOL .env
```

**Solutions:**

1. **Increase pool size:**
```bash
# In .env file
AUTH_DB_POOL_SIZE=30
AUTH_DB_POOL_MAX_OVERFLOW=50
```

2. **Check for connection leaks:**
```bash
# Monitor connections over time
watch "sudo -u postgres psql -c \"SELECT count(*) FROM pg_stat_activity WHERE datname='ai_karen_prod';\""
```

3. **Restart services:**
```bash
sudo systemctl restart ai-karen-backend
```

### Issue: Database Migration Fails

**Symptoms:**
- Migration errors during deployment
- Database schema out of sync

**Diagnosis:**
```bash
# Check migration status
cd /opt/ai-karen/app
source venv/bin/activate
python -m alembic current
python -m alembic history
```

**Solutions:**

1. **Run migrations manually:**
```bash
python -m alembic upgrade head
```

2. **Fix migration conflicts:**
```bash
# Check for conflicts
python -m alembic show head

# Resolve conflicts
python -m alembic merge heads
python -m alembic upgrade head
```

3. **Rollback and retry:**
```bash
python -m alembic downgrade -1
python -m alembic upgrade head
```

### Issue: Milvus Connection Failed

**Symptoms:**
- Vector database connection errors
- Memory/embedding operations fail

**Diagnosis:**
```bash
# Check Milvus status
docker ps | grep milvus

# Test connection
python -c "
from pymilvus import connections
connections.connect('default', host='localhost', port='19530')
print('Milvus connection successful')
"
```

**Solutions:**

1. **Start Milvus:**
```bash
cd /opt/ai-karen/milvus
docker-compose up -d
```

2. **Check Milvus configuration:**
```bash
grep MILVUS .env
```

3. **Reset Milvus data:**
```bash
docker-compose down
docker volume prune
docker-compose up -d
```

## Performance Problems

### Issue: High CPU Usage

**Symptoms:**
- Server becomes unresponsive
- High load average

**Diagnosis:**
```bash
# Check CPU usage
htop
top -p $(pgrep -f "python.*start.py")

# Check for CPU-intensive processes
ps aux --sort=-%cpu | head -10
```

**Solutions:**

1. **Optimize worker processes:**
```bash
# In systemd service file
ExecStart=/opt/ai-karen/app/venv/bin/python start.py --workers 4
```

2. **Enable caching:**
```bash
# In .env file
RESPONSE_CACHE_ENABLE=true
DB_QUERY_CACHE_ENABLE=true
```

3. **Check for infinite loops:**
```bash
# Profile the application
python -m cProfile start.py
```

### Issue: High Memory Usage

**Symptoms:**
- Out of memory errors
- System becomes slow

**Diagnosis:**
```bash
# Check memory usage
free -h
ps aux --sort=-%mem | head -10

# Check for memory leaks
valgrind --tool=memcheck python start.py
```

**Solutions:**

1. **Increase system memory:**
```bash
# Add swap space
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

2. **Optimize memory settings:**
```bash
# In .env file
MAX_MEMORY_USAGE_MB=1024
DB_POOL_SIZE=10  # Reduce if too high
```

3. **Restart services periodically:**
```bash
# Add to crontab
0 4 * * * systemctl restart ai-karen-backend
```

### Issue: Slow Response Times

**Symptoms:**
- API responses take too long
- Frontend loads slowly

**Diagnosis:**
```bash
# Test response times
curl -w "@curl-format.txt" -o /dev/null -s https://your-domain.com/api/health

# Check database query performance
sudo -u postgres psql ai_karen_prod -c "SELECT query, mean_time, calls FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"
```

**Solutions:**

1. **Enable caching:**
```bash
# In .env file
RESPONSE_CACHE_ENABLE=true
RESPONSE_CACHE_DEFAULT_TTL=300000
```

2. **Optimize database queries:**
```bash
# Add database indexes
sudo -u postgres psql ai_karen_prod -c "CREATE INDEX CONCURRENTLY idx_users_email ON users(email);"
```

3. **Use CDN for static files:**
```bash
# Configure Nginx for static file caching
location /static/ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

## SSL/TLS Issues

### Issue: SSL Certificate Invalid

**Symptoms:**
- Browser shows "Not Secure" warning
- SSL certificate errors

**Diagnosis:**
```bash
# Check certificate validity
openssl x509 -in /etc/letsencrypt/live/your-domain.com/fullchain.pem -text -noout

# Test SSL configuration
curl -I https://your-domain.com/
```

**Solutions:**

1. **Renew Let's Encrypt certificate:**
```bash
sudo certbot renew
sudo systemctl reload nginx
```

2. **Check certificate chain:**
```bash
openssl s_client -connect your-domain.com:443 -servername your-domain.com
```

3. **Update Nginx configuration:**
```bash
sudo nginx -t
sudo systemctl reload nginx
```

### Issue: Mixed Content Warnings

**Symptoms:**
- Browser console shows mixed content errors
- Some resources load over HTTP

**Solutions:**

1. **Update all URLs to HTTPS:**
```bash
# Check for HTTP URLs in code
grep -r "http://" /opt/ai-karen/app/ --exclude-dir=venv
```

2. **Add Content Security Policy:**
```nginx
add_header Content-Security-Policy "upgrade-insecure-requests;" always;
```

## Monitoring and Logging

### Issue: Logs Not Being Written

**Symptoms:**
- Log files are empty or not updating
- Missing log entries

**Diagnosis:**
```bash
# Check log file permissions
ls -la /var/log/ai-karen/

# Check logging configuration
grep -A 10 -B 10 "logging" /opt/ai-karen/app/.env
```

**Solutions:**

1. **Fix permissions:**
```bash
sudo chown -R ai-karen:ai-karen /var/log/ai-karen/
sudo chmod 755 /var/log/ai-karen/
sudo chmod 644 /var/log/ai-karen/*.log
```

2. **Create log directories:**
```bash
sudo mkdir -p /var/log/ai-karen
sudo chown ai-karen:ai-karen /var/log/ai-karen
```

3. **Check logging configuration:**
```bash
python -c "
import logging.config
import yaml
with open('config/logging_production.yml') as f:
    config = yaml.safe_load(f)
    logging.config.dictConfig(config)
    logging.info('Test log message')
"
```

### Issue: Disk Space Full

**Symptoms:**
- "No space left on device" errors
- Log rotation fails

**Diagnosis:**
```bash
# Check disk usage
df -h
du -sh /var/log/ai-karen/*
```

**Solutions:**

1. **Clean old logs:**
```bash
# Remove old log files
find /var/log/ai-karen/ -name "*.log.*" -mtime +30 -delete

# Compress current logs
gzip /var/log/ai-karen/*.log
```

2. **Configure log rotation:**
```bash
# Check logrotate configuration
sudo logrotate -d /etc/logrotate.d/ai-karen

# Force log rotation
sudo logrotate -f /etc/logrotate.d/ai-karen
```

3. **Move logs to different partition:**
```bash
# Create new log directory on different partition
sudo mkdir /mnt/logs/ai-karen
sudo chown ai-karen:ai-karen /mnt/logs/ai-karen

# Update logging configuration
sed -i 's|/var/log/ai-karen|/mnt/logs/ai-karen|g' config/logging_production.yml
```

## Emergency Procedures

### Service Recovery

**Complete Service Failure:**

1. **Check system status:**
```bash
sudo systemctl status ai-karen-backend ai-karen-frontend nginx postgresql redis
```

2. **Restart all services:**
```bash
sudo systemctl restart postgresql redis
sudo systemctl restart ai-karen-backend ai-karen-frontend
sudo systemctl restart nginx
```

3. **Check logs for errors:**
```bash
sudo journalctl -u ai-karen-backend --since "10 minutes ago"
```

### Database Recovery

**Database Corruption:**

1. **Stop application:**
```bash
sudo systemctl stop ai-karen-backend ai-karen-frontend
```

2. **Restore from backup:**
```bash
# Find latest backup
ls -la /opt/ai-karen/backups/db_backup_*.sql.gz

# Restore database
gunzip -c /opt/ai-karen/backups/db_backup_YYYYMMDD_HHMMSS.sql.gz | \
sudo -u postgres psql ai_karen_prod
```

3. **Restart services:**
```bash
sudo systemctl start ai-karen-backend ai-karen-frontend
```

### Security Incident Response

**Suspected Security Breach:**

1. **Immediate actions:**
```bash
# Block suspicious IPs
sudo ufw deny from <suspicious_ip>

# Check active sessions
sudo -u postgres psql ai_karen_prod -c "SELECT * FROM user_sessions WHERE active = true;"

# Review access logs
sudo tail -100 /var/log/nginx/access.log | grep -E "(POST|PUT|DELETE)"
```

2. **Investigation:**
```bash
# Check authentication logs
sudo grep "authentication" /var/log/ai-karen/security.log

# Review system logs
sudo grep -i "failed\|error\|unauthorized" /var/log/syslog
```

3. **Recovery:**
```bash
# Force password reset for all users
python scripts/force_password_reset.py

# Regenerate JWT secrets
python scripts/regenerate_secrets.py

# Restart all services
sudo systemctl restart ai-karen-backend ai-karen-frontend
```

### Rollback Procedure

**Failed Deployment:**

1. **Stop current services:**
```bash
sudo systemctl stop ai-karen-backend ai-karen-frontend
```

2. **Restore previous version:**
```bash
# Restore application backup
cd /opt/ai-karen
tar -xzf backups/app_backup_YYYYMMDD_HHMMSS.tar.gz

# Restore database backup
gunzip -c backups/db_backup_YYYYMMDD_HHMMSS.sql.gz | \
sudo -u postgres psql ai_karen_prod
```

3. **Start services:**
```bash
sudo systemctl start ai-karen-backend ai-karen-frontend
```

### Contact Information

**Emergency Contacts:**
- System Administrator: admin@your-domain.com
- Security Team: security@your-domain.com
- On-call Engineer: +1-XXX-XXX-XXXX

**External Support:**
- Hosting Provider Support
- SSL Certificate Provider
- Database Administrator

---

**Remember**: Always test solutions in a staging environment before applying to production when possible.