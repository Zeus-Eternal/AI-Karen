# Troubleshooting Guide

This guide covers common issues and their solutions for the AI Karen database infrastructure.

## 🔍 Diagnostic Tools

### Quick Health Check
```bash
# Run comprehensive health check
./scripts/health-check.sh

# Check specific service
./scripts/health-check.sh --service postgres

# Generate health report
./scripts/health-check.sh --report
```

### Service Status
```bash
# Check all containers
docker-compose ps

# Check specific service logs
docker-compose logs postgres
docker-compose logs elasticsearch
docker-compose logs milvus
docker-compose logs redis

# Follow logs in real-time
docker-compose logs -f [service_name]
```

### Resource Usage
```bash
# Check Docker resource usage
docker stats

# Check disk usage
df -h
du -sh docker/database/data/*

# Check memory usage
free -h
```

## 🚨 Common Issues and Solutions

### 1. Services Won't Start

#### Symptoms:
- Containers exit immediately
- "Port already in use" errors
- "Cannot connect to Docker daemon"

#### Diagnosis:
```bash
# Check if Docker is running
docker info

# Check port conflicts
netstat -tulpn | grep -E ':(5433|9200|19530|6379)'

# Check Docker Compose file syntax
docker-compose config
```

#### Solutions:

**Port Conflicts:**
```bash
# Find process using the port
lsof -i :5433  # Replace with conflicting port

# Kill the process or change port in .env
POSTGRES_PORT=5433
```

**Docker Daemon Issues:**
```bash
# Start Docker service
sudo systemctl start docker

# Add user to docker group
sudo usermod -aG docker $USER
# Then logout and login again
```

**Resource Constraints:**
```bash
# Check available resources
docker system df

# Clean up unused resources
docker system prune -a

# Increase Docker memory limit (Docker Desktop)
# Settings > Resources > Memory > 4GB+
```

### 2. Database Connection Failures

#### Symptoms:
- "Connection refused" errors
- "Authentication failed" errors
- Timeouts when connecting

#### Diagnosis:
```bash
# Test PostgreSQL connection
pg_isready -h localhost -p 5433 -U karen_user

# Test Redis connection
redis-cli -h localhost -p 6379 ping

# Test Elasticsearch
curl http://localhost:9200/_cluster/health
```

#### Solutions:

**PostgreSQL Issues:**
```bash
# Check if PostgreSQL is accepting connections
docker-compose exec postgres pg_isready

# Reset PostgreSQL password
docker-compose exec postgres psql -U postgres -c "ALTER USER karen_user PASSWORD 'new_password';"

# Check PostgreSQL logs
docker-compose logs postgres | grep ERROR
```

**Redis Issues:**
```bash
# Check Redis configuration
docker-compose exec redis redis-cli CONFIG GET "*"

# Reset Redis password
# Edit .env file and restart
./scripts/restart.sh redis
```

**Elasticsearch Issues:**
```bash
# Check cluster health
curl http://localhost:9200/_cluster/health?pretty

# Check node status
curl http://localhost:9200/_nodes/stats?pretty

# Increase heap size if needed
# In .env: ELASTICSEARCH_HEAP_SIZE=2g
```

### 3. Performance Issues

#### Symptoms:
- Slow query responses
- High CPU/memory usage
- Frequent timeouts

#### Diagnosis:
```bash
# Monitor resource usage
docker stats --no-stream

# Check slow queries (PostgreSQL)
docker-compose exec postgres psql -U karen_user -d ai_karen -c "SELECT * FROM pg_stat_activity WHERE state = 'active';"

# Check Elasticsearch performance
curl http://localhost:9200/_nodes/stats/indices?pretty
```

#### Solutions:

**PostgreSQL Performance:**
```bash
# Increase connection limit
# In .env: POSTGRES_MAX_CONNECTIONS=200

# Analyze slow queries
docker-compose exec postgres psql -U karen_user -d ai_karen -c "SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;"

# Vacuum and analyze tables
docker-compose exec postgres psql -U karen_user -d ai_karen -c "VACUUM ANALYZE;"
```

**Elasticsearch Performance:**
```bash
# Increase heap size
# In .env: ELASTICSEARCH_HEAP_SIZE=4g

# Check index health
curl http://localhost:9200/_cat/indices?v&health=yellow

# Optimize indices
curl -X POST "http://localhost:9200/_optimize"
```

**Redis Performance:**
```bash
# Check memory usage
docker-compose exec redis redis-cli INFO memory

# Increase memory limit
# In .env: REDIS_MEMORY_LIMIT=1g

# Check slow log
docker-compose exec redis redis-cli SLOWLOG GET 10
```

### 4. Data Corruption Issues

#### Symptoms:
- Query errors
- Missing or inconsistent data
- Index corruption messages

#### Diagnosis:
```bash
# Check PostgreSQL data integrity
docker-compose exec postgres psql -U karen_user -d ai_karen -c "SELECT * FROM pg_stat_database;"

# Check Elasticsearch index health
curl http://localhost:9200/_cluster/health?level=indices

# Check DuckDB integrity
duckdb ./data/duckdb/kari_duckdb.db -c "PRAGMA integrity_check;"
```

#### Solutions:

**PostgreSQL Corruption:**
```bash
# Create backup first
./scripts/backup.sh --name emergency_backup

# Reindex corrupted indices
docker-compose exec postgres psql -U karen_user -d ai_karen -c "REINDEX DATABASE ai_karen;"

# If severe, restore from backup
./scripts/restore.sh emergency_backup
```

**Elasticsearch Corruption:**
```bash
# Check and fix index issues
curl -X POST "http://localhost:9200/_cluster/reroute?retry_failed=true"

# Recreate corrupted indices
curl -X DELETE "http://localhost:9200/corrupted_index"
# Then restore from backup
```

### 5. Initialization Failures

#### Symptoms:
- "Database initialization failed" messages
- Missing tables or indices
- Bootstrap data not loaded

#### Diagnosis:
```bash
# Check initialization logs
docker-compose logs db-init

# Verify database schemas
docker-compose exec postgres psql -U karen_user -d ai_karen -c "\dt"

# Check migration status
./scripts/migrate.sh status
```

#### Solutions:

**Re-run Initialization:**
```bash
# Stop services
./scripts/stop.sh

# Remove initialization marker
rm -f /tmp/ai_karen_init/init_success

# Start services (will re-run initialization)
./scripts/start.sh
```

**Manual Migration:**
```bash
# Run migrations manually
./scripts/migrate.sh up

# Load bootstrap data
docker/database/init/bootstrap/load-bootstrap-data.sh
```

### 6. Backup and Restore Issues

#### Symptoms:
- Backup creation fails
- Restore process errors
- Incomplete data after restore

#### Diagnosis:
```bash
# Test backup creation
./scripts/backup.sh --quick --name test_backup

# Validate backup integrity
ls -la ./backups/test_backup/
cat ./backups/test_backup/backup_info.json
```

#### Solutions:

**Backup Issues:**
```bash
# Check disk space
df -h

# Create backup with verbose logging
./scripts/backup.sh --name debug_backup 2>&1 | tee backup.log

# Try service-specific backup
./scripts/backup.sh --service postgres --name postgres_only
```

**Restore Issues:**
```bash
# Validate backup before restore
./scripts/restore.sh backup_name --dry-run

# Restore specific service only
./scripts/restore.sh backup_name --service postgres

# Check restore logs
./scripts/restore.sh backup_name 2>&1 | tee restore.log
```

## 🔧 Advanced Troubleshooting

### Container Debugging

```bash
# Enter container shell
docker-compose exec postgres bash
docker-compose exec elasticsearch bash
docker-compose exec redis sh

# Check container processes
docker-compose exec postgres ps aux

# Check container network
docker-compose exec postgres netstat -tulpn
```

### Network Issues

```bash
# Check Docker networks
docker network ls
docker network inspect ai-karen-database-network

# Test inter-container connectivity
docker-compose exec postgres ping elasticsearch
docker-compose exec postgres ping redis
```

### Log Analysis

```bash
# Extract specific error patterns
docker-compose logs postgres 2>&1 | grep ERROR
docker-compose logs elasticsearch 2>&1 | grep -i "exception\|error"

# Save logs for analysis
docker-compose logs > full_logs_$(date +%Y%m%d_%H%M%S).txt
```

## 📞 Getting Help

### Information to Collect

When seeking help, please provide:

1. **System Information:**
   ```bash
   uname -a
   docker --version
   docker-compose --version
   ```

2. **Service Status:**
   ```bash
   docker-compose ps
   ./scripts/health-check.sh --report
   ```

3. **Error Logs:**
   ```bash
   docker-compose logs --tail=100 > error_logs.txt
   ```

4. **Configuration:**
   ```bash
   # Remove sensitive information first
   grep -v -E "(PASSWORD|SECRET|KEY)" .env > config_safe.txt
   ```

### Support Channels

- Check the [GitHub Issues](https://github.com/ai-karen/database-infrastructure/issues)
- Review the [FAQ](./FAQ.md)
- Consult the [Configuration Guide](./CONFIGURATION.md)

## 🔄 Recovery Procedures

### Complete System Recovery

If all else fails, here's the nuclear option:

```bash
# 1. Create emergency backup (if possible)
./scripts/backup.sh --name emergency_$(date +%Y%m%d_%H%M%S)

# 2. Complete reset
./scripts/reset.sh --force

# 3. Fresh start
./scripts/start.sh

# 4. Restore from backup (if available)
./scripts/restore.sh emergency_backup_name
```

### Partial Recovery

For single service issues:

```bash
# Restart specific service
./scripts/restart.sh postgres

# Reset specific service data
docker-compose stop postgres
docker volume rm ai-karen-postgres-data
docker-compose up -d postgres

# Restore specific service from backup
./scripts/restore.sh backup_name --service postgres
```
