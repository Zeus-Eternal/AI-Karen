# AI-Karen Comprehensive Troubleshooting Guide

## Overview

This guide provides systematic troubleshooting procedures for common issues in AI-Karen deployments, from development to production environments.

## Quick Diagnostic Commands

### System Health Check
```bash
# Overall system status
curl -s http://localhost:8000/api/health/summary | jq '.'

# Service-specific health
curl -s http://localhost:8000/api/services/postgres/health | jq '.'
curl -s http://localhost:8000/api/services/redis/health | jq '.'
curl -s http://localhost:8000/api/services/milvus/health | jq '.'

# Check running services
docker compose ps
ss -ltnp | grep -E ':(8000|8020|5433|6379|19530|9200)'
```

### Log Analysis
```bash
# API logs
docker compose logs api --tail=100 -f

# Database logs
docker compose logs postgres --tail=50

# Web UI logs
docker compose logs web-ui --tail=50

# System logs
journalctl -u docker -f
```

## Connection and Network Issues

### Issue: "Connection Refused" Errors

**Symptoms:**
- `ERR_CONNECTION_REFUSED` in browser console
- `Connection refused` in API logs
- Services not responding to health checks

**Diagnostic Steps:**
```bash
# 1. Check if services are running
docker compose ps

# 2. Check port bindings
docker compose port api 8000
docker compose port web-ui 3000

# 3. Test local connectivity
curl -v http://localhost:8000/health
telnet localhost 8000

# 4. Check firewall rules
sudo ufw status
iptables -L -n

# 5. Verify network configuration
docker network ls
docker network inspect ai-karen_default
```

**Solutions:**

1. **Service Not Running:**
   ```bash
   # Restart specific service
   docker compose restart api
   
   # Full restart
   docker compose down && docker compose up -d
   ```

2. **Port Conflicts:**
   ```bash
   # Check what's using the port
   lsof -i :8000
   
   # Change port in docker-compose.yml
   ports:
     - "8001:8000"  # Use different external port
   ```

3. **Network Issues:**
   ```bash
   # Recreate network
   docker compose down
   docker network prune
   docker compose up -d
   ```

### Issue: CORS Errors

**Symptoms:**
- Browser console shows CORS policy errors
- Preflight OPTIONS requests failing
- Cross-origin requests blocked

**Diagnostic Steps:**
```bash
# Check CORS configuration
echo $KARI_CORS_ORIGINS
echo $KARI_CORS_METHODS
echo $KARI_CORS_HEADERS

# Test CORS headers
curl -H "Origin: http://localhost:3000" \
     -H "Access-Control-Request-Method: POST" \
     -H "Access-Control-Request-Headers: Content-Type" \
     -X OPTIONS \
     http://localhost:8000/api/auth/login
```

**Solutions:**

1. **Update CORS Configuration:**
   ```bash
   # In .env file
   KARI_CORS_ORIGINS=http://localhost:3000,http://localhost:8020,https://your-domain.com
   KARI_CORS_METHODS=GET,POST,PUT,DELETE,OPTIONS
   KARI_CORS_HEADERS=*
   KARI_CORS_CREDENTIALS=true
   
   # Restart API
   docker compose restart api
   ```

2. **Development Proxy Setup:**
   ```bash
   # Enable proxy in web UI
   NEXT_PUBLIC_USE_PROXY=true
   ```

## Authentication Issues

### Issue: Login Failures

**Symptoms:**
- Login requests hanging or timing out
- "Authentication failed" errors
- Invalid token responses

**Diagnostic Steps:**
```bash
# 1. Test authentication endpoint
curl -X POST http://localhost:8000/api/auth/dev-login \
     -H "Content-Type: application/json" \
     -d '{}'

# 2. Check JWT configuration
echo $JWT_SECRET_KEY
echo $JWT_ALGORITHM

# 3. Verify database connection
docker compose exec postgres psql -U karen_user -d ai_karen -c "\dt"

# 4. Check auth service logs
docker compose logs api | grep -i auth
```

**Solutions:**

1. **Reset Authentication:**
   ```bash
   # Recreate admin user
   docker compose exec api python create_admin_user.py
   
   # Clear auth cache
   docker compose exec redis redis-cli FLUSHDB
   ```

2. **Fix JWT Configuration:**
   ```bash
   # Generate new JWT secret
   JWT_SECRET_KEY=$(openssl rand -base64 32)
   echo "JWT_SECRET_KEY=$JWT_SECRET_KEY" >> .env
   
   # Restart API
   docker compose restart api
   ```

3. **Database Issues:**
   ```bash
   # Recreate auth tables
   docker compose exec api python create_tables.py
   ```

### Issue: Session Persistence Problems

**Symptoms:**
- Users logged out unexpectedly
- Session validation failures
- Token refresh errors

**Diagnostic Steps:**
```bash
# Check session storage
docker compose exec redis redis-cli KEYS "session:*"

# Validate token
curl -X POST http://localhost:8000/api/auth/validate-session \
     -H "Authorization: Bearer <token>"

# Check token expiration
echo "<jwt_token>" | base64 -d | jq '.exp'
```

**Solutions:**

1. **Session Configuration:**
   ```bash
   # Increase session timeout
   SESSION_TIMEOUT=86400  # 24 hours
   JWT_EXPIRATION=3600    # 1 hour
   JWT_REFRESH_EXPIRATION=604800  # 1 week
   ```

2. **Redis Issues:**
   ```bash
   # Clear sessions
   docker compose exec redis redis-cli FLUSHALL
   
   # Check Redis memory
   docker compose exec redis redis-cli INFO memory
   ```

## Database Issues

### Issue: PostgreSQL Connection Problems

**Symptoms:**
- "Connection to database failed" errors
- Slow database queries
- Connection pool exhaustion

**Diagnostic Steps:**
```bash
# 1. Check PostgreSQL status
docker compose exec postgres pg_isready -U karen_user -d ai_karen

# 2. Check connections
docker compose exec postgres psql -U karen_user -d ai_karen -c "SELECT count(*) FROM pg_stat_activity;"

# 3. Check database size
docker compose exec postgres psql -U karen_user -d ai_karen -c "SELECT pg_size_pretty(pg_database_size('ai_karen'));"

# 4. Check slow queries
docker compose exec postgres psql -U karen_user -d ai_karen -c "SELECT query, mean_time, calls FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"
```

**Solutions:**

1. **Connection Pool Tuning:**
   ```python
   # In database configuration
   SQLALCHEMY_POOL_SIZE = 20
   SQLALCHEMY_MAX_OVERFLOW = 30
   SQLALCHEMY_POOL_TIMEOUT = 30
   SQLALCHEMY_POOL_RECYCLE = 3600
   ```

2. **PostgreSQL Performance:**
   ```sql
   -- Optimize PostgreSQL settings
   ALTER SYSTEM SET shared_buffers = '256MB';
   ALTER SYSTEM SET effective_cache_size = '1GB';
   ALTER SYSTEM SET maintenance_work_mem = '64MB';
   SELECT pg_reload_conf();
   ```

3. **Database Maintenance:**
   ```bash
   # Vacuum and analyze
   docker compose exec postgres psql -U karen_user -d ai_karen -c "VACUUM ANALYZE;"
   
   # Reindex
   docker compose exec postgres psql -U karen_user -d ai_karen -c "REINDEX DATABASE ai_karen;"
   ```

### Issue: Redis Memory Issues

**Symptoms:**
- Redis out of memory errors
- Cache misses increasing
- Slow response times

**Diagnostic Steps:**
```bash
# Check Redis memory usage
docker compose exec redis redis-cli INFO memory

# Check key count
docker compose exec redis redis-cli DBSIZE

# Check largest keys
docker compose exec redis redis-cli --bigkeys
```

**Solutions:**

1. **Memory Configuration:**
   ```bash
   # Update Redis configuration
   docker compose exec redis redis-cli CONFIG SET maxmemory 512mb
   docker compose exec redis redis-cli CONFIG SET maxmemory-policy allkeys-lru
   ```

2. **Clear Cache:**
   ```bash
   # Clear all cache
   docker compose exec redis redis-cli FLUSHALL
   
   # Clear specific patterns
   docker compose exec redis redis-cli --scan --pattern "session:*" | xargs docker compose exec redis redis-cli DEL
   ```

## AI Model Issues

### Issue: Model Loading Failures

**Symptoms:**
- "Model not found" errors
- Long model loading times
- Out of memory during model loading

**Diagnostic Steps:**
```bash
# 1. Check model files
ls -la models/llama-cpp/
du -sh models/llama-cpp/*

# 2. Check model configuration
cat llm_settings.json

# 3. Check available memory
free -h
docker stats

# 4. Check model loading logs
docker compose logs api | grep -i "model\|llama"
```

**Solutions:**

1. **Model File Issues:**
   ```bash
   # Download missing models
   cd models/llama-cpp/
   wget https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf/resolve/main/Phi-3-mini-4k-instruct-q4.gguf
   
   # Verify file integrity
   sha256sum Phi-3-mini-4k-instruct-q4.gguf
   ```

2. **Memory Optimization:**
   ```bash
   # Reduce model memory usage
   LLAMA_MLOCK=false
   LLAMA_THREADS=2
   
   # Use smaller model
   # Update llm_settings.json to point to smaller model
   ```

3. **Model Configuration:**
   ```json
   {
     "model_path": "models/llama-cpp/Phi-3-mini-4k-instruct-q4.gguf",
     "n_ctx": 2048,
     "n_gpu_layers": 0,
     "n_threads": 4,
     "verbose": false
   }
   ```

### Issue: Slow AI Responses

**Symptoms:**
- Long response times from AI endpoints
- Timeouts on chat completions
- High CPU usage during inference

**Diagnostic Steps:**
```bash
# Check CPU usage
top -p $(pgrep -f "python.*start")

# Check model performance
curl -w "@curl-format.txt" -X POST http://localhost:8000/api/chat/completions \
     -H "Content-Type: application/json" \
     -d '{"message": "Hello"}'

# Monitor resource usage
docker stats karen-api
```

**Solutions:**

1. **Performance Optimization:**
   ```bash
   # Enable performance profile
   PROFILE=runtime-perf
   
   # Optimize threads
   LLAMA_THREADS=$(nproc)
   
   # Enable memory locking
   LLAMA_MLOCK=true
   ```

2. **Model Optimization:**
   ```bash
   # Use quantized model
   # Switch to Q4 or Q8 quantization for better performance
   
   # Reduce context size
   n_ctx=1024  # Smaller context window
   ```

## Web UI Issues

### Issue: Frontend Build Failures

**Symptoms:**
- Build errors during Docker build
- Missing dependencies
- TypeScript compilation errors

**Diagnostic Steps:**
```bash
# Check Node.js version
node --version
npm --version

# Check build logs
docker compose logs web-ui

# Manual build test
cd ui_launchers/web_ui
npm install
npm run build
```

**Solutions:**

1. **Dependency Issues:**
   ```bash
   # Clear node modules
   cd ui_launchers/web_ui
   rm -rf node_modules package-lock.json
   npm install
   
   # Update dependencies
   npm update
   ```

2. **TypeScript Errors:**
   ```bash
   # Check TypeScript configuration
   npx tsc --noEmit
   
   # Fix type issues
   npm run type-check
   ```

3. **Build Configuration:**
   ```javascript
   // next.config.js
   module.exports = {
     output: 'standalone',
     experimental: {
       outputFileTracingRoot: path.join(__dirname, '../../'),
     },
   }
   ```

### Issue: API Client Connection Problems

**Symptoms:**
- API requests failing from frontend
- Network diagnostics showing connection issues
- Endpoint fallback not working

**Diagnostic Steps:**
```bash
# Check API client configuration
grep -r "KAREN_BACKEND_URL\|API_BASE_URL" ui_launchers/web_ui/

# Test endpoint connectivity
curl -v http://localhost:8000/health

# Check network diagnostics
# Open browser dev tools and check network tab
```

**Solutions:**

1. **API Configuration:**
   ```bash
   # Update environment variables
   KAREN_BACKEND_URL=http://127.0.0.1:8000
   NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
   ```

2. **Proxy Configuration:**
   ```bash
   # Enable proxy mode
   NEXT_PUBLIC_USE_PROXY=true
   
   # Update proxy routes in Next.js
   ```

## Performance Issues

### Issue: High Memory Usage

**Symptoms:**
- System running out of memory
- Docker containers being killed (OOMKilled)
- Slow performance

**Diagnostic Steps:**
```bash
# Check system memory
free -h
cat /proc/meminfo

# Check Docker memory usage
docker stats

# Check process memory
ps aux --sort=-%mem | head -10

# Check memory limits
docker inspect karen-api | grep -i memory
```

**Solutions:**

1. **Memory Optimization:**
   ```bash
   # Enable optimized startup
   KARI_ULTRA_MINIMAL=true
   KARI_LAZY_LOADING=true
   KARI_RESOURCE_MONITORING=true
   
   # Restart with optimized mode
   python start_optimized.py
   ```

2. **Container Limits:**
   ```yaml
   # docker-compose.yml
   services:
     api:
       deploy:
         resources:
           limits:
             memory: 4G
           reservations:
             memory: 2G
   ```

3. **System Tuning:**
   ```bash
   # Increase swap
   sudo fallocate -l 2G /swapfile
   sudo chmod 600 /swapfile
   sudo mkswap /swapfile
   sudo swapon /swapfile
   ```

### Issue: High CPU Usage

**Symptoms:**
- CPU usage consistently high
- System becoming unresponsive
- Slow API responses

**Diagnostic Steps:**
```bash
# Check CPU usage
top -c
htop

# Check process CPU usage
ps aux --sort=-%cpu | head -10

# Monitor API performance
curl -w "@curl-format.txt" http://localhost:8000/health
```

**Solutions:**

1. **CPU Optimization:**
   ```bash
   # Limit CPU usage
   docker update --cpus="2.0" karen-api
   
   # Optimize thread count
   LLAMA_THREADS=4  # Don't exceed available cores
   ```

2. **Process Optimization:**
   ```bash
   # Use nice/ionice for background processes
   nice -n 10 python background_task.py
   ```

## Docker Issues

### Issue: Docker Build Failures

**Symptoms:**
- Build context too large
- Dependency installation failures
- Layer caching issues

**Diagnostic Steps:**
```bash
# Check build context size
du -sh .

# Check .dockerignore
cat .dockerignore

# Build with verbose output
docker build --no-cache --progress=plain .
```

**Solutions:**

1. **Optimize Build Context:**
   ```bash
   # Update .dockerignore
   echo "node_modules" >> .dockerignore
   echo "*.log" >> .dockerignore
   echo ".git" >> .dockerignore
   echo "__pycache__" >> .dockerignore
   ```

2. **Multi-stage Build:**
   ```dockerfile
   # Use multi-stage builds
   FROM python:3.11-slim as builder
   # Build dependencies
   
   FROM python:3.11-slim as runtime
   # Copy only necessary files
   ```

### Issue: Container Startup Failures

**Symptoms:**
- Containers exiting immediately
- Health check failures
- Service dependencies not ready

**Diagnostic Steps:**
```bash
# Check container logs
docker compose logs api

# Check exit codes
docker compose ps

# Test container manually
docker run -it --rm karen-api /bin/bash
```

**Solutions:**

1. **Dependency Management:**
   ```yaml
   # docker-compose.yml
   services:
     api:
       depends_on:
         postgres:
           condition: service_healthy
         redis:
           condition: service_healthy
   ```

2. **Health Checks:**
   ```yaml
   healthcheck:
     test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
     interval: 30s
     timeout: 10s
     retries: 3
     start_period: 40s
   ```

## Monitoring and Debugging

### Enable Debug Mode

```bash
# Enable debug logging
LOG_LEVEL=DEBUG

# Enable verbose output
VERBOSE=true

# Enable development mode
ENVIRONMENT=development
```

### Performance Profiling

```bash
# Profile Python application
pip install py-spy
py-spy record -o profile.svg -d 60 -p $(pgrep -f "python.*start")

# Profile memory usage
pip install memory-profiler
python -m memory_profiler start.py
```

### Network Debugging

```bash
# Capture network traffic
sudo tcpdump -i any -w capture.pcap port 8000

# Analyze with Wireshark
wireshark capture.pcap

# Test connectivity
nmap -p 8000 localhost
telnet localhost 8000
```

## Recovery Procedures

### Emergency Recovery

```bash
# 1. Stop all services
docker compose down

# 2. Clean up resources
docker system prune -f
docker volume prune -f

# 3. Reset to known good state
git checkout main
git pull origin main

# 4. Rebuild and restart
docker compose build --no-cache
docker compose up -d

# 5. Verify health
curl http://localhost:8000/health
```

### Data Recovery

```bash
# Restore from backup
gunzip -c backup_latest.sql.gz | docker compose exec -T postgres psql -U karen_user -d ai_karen

# Restore models
tar -xzf models_backup.tar.gz -C models/

# Restore configuration
cp config_backup/* config/
```

## Prevention and Maintenance

### Regular Health Checks

```bash
#!/bin/bash
# health-check.sh
set -e

echo "Checking AI-Karen health..."

# API health
curl -f http://localhost:8000/health || exit 1

# Database health
docker compose exec postgres pg_isready -U karen_user -d ai_karen || exit 1

# Redis health
docker compose exec redis redis-cli ping || exit 1

# Disk space
DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 80 ]; then
    echo "Warning: Disk usage is ${DISK_USAGE}%"
fi

echo "All systems healthy!"
```

### Automated Monitoring

```bash
# Set up cron job for health checks
echo "*/5 * * * * /path/to/health-check.sh" | crontab -

# Log rotation
echo "/var/log/ai-karen/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 root root
}" > /etc/logrotate.d/ai-karen
```

This comprehensive troubleshooting guide covers the most common issues and their solutions. For additional support, check the system logs and health endpoints for specific error messages.