# Getting Started with AI Karen Database Infrastructure

This guide will walk you through setting up the AI Karen database infrastructure from scratch.

## 🎯 Overview

The AI Karen database infrastructure provides a complete, containerized database stack that includes:
- **PostgreSQL** for relational data
- **DuckDB** for analytics and user profiles
- **Elasticsearch** for full-text search
- **Milvus** for vector similarity search
- **Redis** for caching and sessions

## 📋 Step-by-Step Setup

### Step 1: Prerequisites Check

Before starting, ensure you have:

```bash
# Check Docker version (should be 20.10+)
docker --version

# Check Docker Compose version (should be 2.0+)
docker compose version
# OR
docker-compose --version

# Check available disk space (need at least 10GB)
df -h

# Check available memory (need at least 4GB)
free -h
```

### Step 2: Environment Configuration

1. **Copy the environment template:**
   ```bash
   cd docker/database
   cp .env.template .env
   ```

2. **Edit the `.env` file:**
   ```bash
   nano .env  # or your preferred editor
   ```

3. **Key settings to customize:**
   ```bash
   # Database passwords (CHANGE THESE!)
   POSTGRES_PASSWORD=your_secure_postgres_password
   REDIS_PASSWORD=your_secure_redis_password
   ELASTICSEARCH_PASSWORD=your_secure_elasticsearch_password

   # Resource limits (adjust based on your system)
   POSTGRES_MAX_CONNECTIONS=100
   ELASTICSEARCH_HEAP_SIZE=1g
   REDIS_MEMORY_LIMIT=512m

   # Environment mode
   ENVIRONMENT=development  # or production
   ```

### Step 3: Start the Database Stack

1. **Start all services:**
   ```bash
   ./scripts/start.sh
   ```

2. **Monitor the startup process:**
   ```bash
   # Watch logs in real-time
   docker-compose logs -f

   # Check service status
   docker-compose ps
   ```

3. **Wait for initialization to complete:**
   The startup script will automatically run database initialization. Look for:
   ```
   🎉 AI Karen Database Initialization Complete! 🎉
   ```

### Step 4: Verify Installation

1. **Run health checks:**
   ```bash
   ./scripts/health-check.sh
   ```

2. **Test individual services:**
   ```bash
   # PostgreSQL
   psql -h localhost -U karen_user -d ai_karen -c "SELECT version();"

   # Elasticsearch
   curl http://localhost:9200/_cluster/health

   # Redis
   redis-cli -h localhost ping

   # Milvus (requires Python)
   python3 -c "from pymilvus import connections; connections.connect(); print('Milvus OK')"
   ```

### Step 5: Explore the Services

1. **PostgreSQL:**
   ```bash
   # Connect to PostgreSQL
   psql -h localhost -U karen_user -d ai_karen

   # List tables
   \dt

   # Check sample data
   SELECT * FROM profiles LIMIT 5;
   ```

2. **Elasticsearch:**
   ```bash
   # Check indices
   curl http://localhost:9200/_cat/indices?v

   # Search sample data
   curl http://localhost:9200/ai_karen_memory/_search
   ```

3. **Redis:**
   ```bash
   # Connect to Redis
   redis-cli -h localhost

   # List AI Karen keys
   KEYS ai_karen:*

   # Check configuration
   HGETALL ai_karen:config:system
   ```

## 🔧 Common Configuration Scenarios

### Development Setup (Minimal Resources)

```bash
# In .env file
POSTGRES_MAX_CONNECTIONS=50
ELASTICSEARCH_HEAP_SIZE=512m
REDIS_MEMORY_LIMIT=256m
MILVUS_MEMORY_LIMIT=1g
ENABLE_MONITORING=false
```

### Production Setup (High Performance)

```bash
# In .env file
POSTGRES_MAX_CONNECTIONS=200
ELASTICSEARCH_HEAP_SIZE=4g
REDIS_MEMORY_LIMIT=2g
MILVUS_MEMORY_LIMIT=8g
ENABLE_MONITORING=true
ENABLE_BACKUPS=true
```

### Testing Setup (Ephemeral Data)

```bash
# Start without persistent volumes
docker-compose up --rm
```

## 🚨 Troubleshooting Common Issues

### Issue: Services Won't Start

**Symptoms:**
- Containers exit immediately
- Port binding errors
- Out of memory errors

**Solutions:**
```bash
# Check port conflicts
netstat -tulpn | grep -E ':(5433|9200|19530|6379)'

# Check Docker resources
docker system df
docker system prune  # if needed

# Check logs for specific errors
docker-compose logs [service_name]
```

### Issue: Slow Performance

**Symptoms:**
- Long response times
- High CPU/memory usage
- Timeouts

**Solutions:**
```bash
# Check resource usage
docker stats

# Adjust resource limits in .env
ELASTICSEARCH_HEAP_SIZE=2g
REDIS_MEMORY_LIMIT=1g

# Restart services
./scripts/restart.sh
```

### Issue: Data Corruption

**Symptoms:**
- Query errors
- Missing data
- Inconsistent results

**Solutions:**
```bash
# Create backup first (if possible)
./scripts/backup.sh --name emergency_backup

# Reset and reinitialize
./scripts/reset.sh
./scripts/start.sh
```

## 📊 Monitoring and Maintenance

### Daily Checks

```bash
# Health check
./scripts/health-check.sh

# Check disk usage
df -h

# Check service status
docker-compose ps
```

### Weekly Maintenance

```bash
# Create backup
./scripts/backup.sh --name weekly_$(date +%Y%m%d)

# Clean up old logs
docker-compose logs --tail=0

# Update images (if needed)
docker-compose pull
./scripts/restart.sh
```

### Monthly Tasks

```bash
# Full system backup
./scripts/backup.sh --name monthly_$(date +%Y%m)

# Review resource usage
docker stats --no-stream

# Check for updates
docker images | grep -E "(postgres|elasticsearch|milvus|redis)"
```

## 🔄 Next Steps

Once your database infrastructure is running:

1. **Connect AI Karen Application:**
   - Update AI Karen's database configuration
   - Test application connectivity
   - Run application-specific migrations

2. **Set Up Monitoring:**
   - Configure log aggregation
   - Set up alerting for critical issues
   - Monitor resource usage trends

3. **Implement Backup Strategy:**
   - Schedule automated backups
   - Test restore procedures
   - Document recovery processes

4. **Security Hardening:**
   - Change default passwords
   - Configure network isolation
   - Enable SSL/TLS encryption
   - Set up audit logging

## 📚 Additional Resources

- [Configuration Guide](./CONFIGURATION.md)
- [Migration Guide](./MIGRATIONS.md)
- [Backup and Restore Guide](./BACKUP_RESTORE.md)
- [Troubleshooting Guide](./TROUBLESHOOTING.md)
- [Performance Tuning](./PERFORMANCE.md)
