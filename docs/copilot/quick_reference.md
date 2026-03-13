# CoPilot Architecture Deployment Quick Reference

This document provides a quick reference for common deployment tasks for the CoPilot Architecture.

## Basic Operations

### Start Services
```bash
# Start all services
./scripts/deploy-copilot.sh

# Or manually
docker-compose -f docker-compose-copilot.yml up -d
```

### Stop Services
```bash
# Graceful stop
./scripts/stop-copilot.sh

# Force stop and remove containers
docker-compose -f docker-compose-copilot.yml down -v
```

### Check Status
```bash
# Check all services
docker-compose -f docker-compose-copilot.yml ps

# Check specific service
docker-compose -f docker-compose-copilot.yml ps api-copilot
```

### View Logs
```bash
# View all logs
docker-compose -f docker-compose-copilot.yml logs -f

# View specific service logs
docker-compose -f docker-compose-copilot.yml logs -f api-copilot

# View recent logs (last hour)
docker-compose -f docker-compose-copilot.yml logs --since 1h
```

## Updates and Maintenance

### Update Deployment
```bash
# Automated update
./scripts/update-copilot.sh

# Manual update
docker-compose -f docker-compose-copilot.yml pull
docker-compose -f docker-compose-copilot.yml up -d --build
```

### Restart Services
```bash
# Restart all services
docker-compose -f docker-compose-copilot.yml restart

# Restart specific service
docker-compose -f docker-compose-copilot.yml restart api-copilot
```

### Scale Services
```bash
# Scale API service
docker-compose -f docker-compose-copilot.yml up -d --scale api-copilot=3

# Scale web service
docker-compose -f docker-compose-copilot.yml up -d --scale web-copilot=2
```

## Backup and Restore

### Create Backup
```bash
# Automated backup
./scripts/backup-copilot.sh

# Manual database backup
docker-compose -f docker-compose-copilot.yml exec -T postgres-copilot pg_dump -U karen_user ai_karen_copilot > backup.sql
```

### Restore Backup
```bash
# Automated restore
./scripts/restore-copilot.sh

# Manual database restore
docker-compose -f docker-compose-copilot.yml exec -T postgres-copilot psql -U karen_user -d ai_karen_copilot < backup.sql
```

## Health Checks

### Check Service Health
```bash
# API health
curl http://localhost:8000/health

# Web health
curl http://localhost:8010

# Prometheus health
curl http://localhost:9090

# Grafana health
curl http://localhost:3001
```

### Check Database Connection
```bash
# PostgreSQL connection
docker-compose -f docker-compose-copilot.yml exec postgres-copilot psql -U karen_user -d ai_karen_copilot -c "SELECT 1"

# Redis connection
docker-compose -f docker-compose-copilot.yml exec redis-copilot redis-cli ping
```

## Troubleshooting

### Common Issues

#### Service Not Starting
```bash
# Check logs
docker-compose -f docker-compose-copilot.yml logs api-copilot

# Check port conflicts
netstat -tulpn | grep :8000
netstat -tulpn | grep :8010
```

#### High Memory Usage
```bash
# Check memory usage
docker stats

# Restart services
docker-compose -f docker-compose-copilot.yml restart
```

#### Database Connection Issues
```bash
# Check database service
docker-compose -f docker-compose-copilot.yml ps postgres-copilot

# Check database logs
docker-compose -f docker-compose-copilot.yml logs postgres-copilot
```

### Debug Mode
```bash
# Enable debug mode
sed -i 's/DEBUG=false/DEBUG=true/' .env
docker-compose -f docker-compose-copilot.yml restart api-copilot web-copilot
```

## Access URLs

| Service | URL | Default Credentials |
|---------|-----|-------------------|
| CoPilot Web UI | http://localhost:8010 | N/A |
| Backend API | http://localhost:8000 | N/A |
| Grafana Dashboard | http://localhost:3001 | admin/admin |
| Prometheus | http://localhost:9090 | N/A |
| MinIO Console | http://localhost:9001 | minioadmin/minioadmin |

## Configuration Files

| File | Purpose |
|------|---------|
| `config/copilot_deployment.yml` | Main deployment configuration |
| `config/copilot_production.env` | Production environment variables |
| `docker-compose-copilot.yml` | Docker Compose configuration |
| `monitoring/prometheus-copilot.yml` | Prometheus configuration |

## Important Directories

| Directory | Purpose |
|----------|---------|
| `logs/` | Application logs |
| `backups/` | Backup files |
| `certs/` | SSL certificates |
| `monitoring/` | Monitoring configuration |
| `scripts/` | Deployment and management scripts |

## Emergency Procedures

### Full System Restart
```bash
# Stop all services
docker-compose -f docker-compose-copilot.yml down

# Wait 10 seconds
sleep 10

# Start all services
docker-compose -f docker-compose-copilot.yml up -d

# Check status
docker-compose -f docker-compose-copilot.yml ps
```

### Emergency Rollback
```bash
# Stop services
./scripts/stop-copilot.sh --remove-containers

# Restore from backup
./scripts/restore-copilot.sh

# Start services
./scripts/deploy-copilot.sh
```

### Clear All Data (Destructive)
```bash
# WARNING: This will permanently delete all data
docker-compose -f docker-compose-copilot.yml down -v
rm -rf data/* logs/* backups/*
```

## Support

- **Documentation**: `docs/copilot/` directory
- **Deployment Guide**: `docs/copilot/deployment_guide.md`
- **Rollback Plan**: `docs/copilot/rollback_plan.md`
- **Issues**: GitHub repository
- **Community**: Community forum