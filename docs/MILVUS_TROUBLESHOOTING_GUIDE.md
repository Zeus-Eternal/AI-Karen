# Milvus Troubleshooting Guide

## Node ID Mismatch Error Resolution

### Problem Description
The error "expectedNodeID=15473, actualNodeID=15474: node not match" indicates that Milvus components are having coordination issues, typically after restarts or upgrades.

### Current Status
✅ **RESOLVED** - No recent node ID mismatch errors detected  
✅ Milvus is running normally with node ID synchronization restored

## Preventive Measures

### 1. Graceful Shutdown Procedure
When stopping the system, follow this order:
```bash
# Stop dependent services first
docker compose stop api

# Stop Milvus gracefully
docker compose stop milvus

# Stop Milvus dependencies
docker compose stop milvus-etcd milvus-minio
```

### 2. Restart Procedure (if issues occur)
```bash
# Clean restart of Milvus stack
docker compose down milvus milvus-etcd milvus-minio
docker compose up -d milvus-etcd milvus-minio
sleep 10
docker compose up -d milvus
```

### 3. Data Corruption Recovery
If persistent issues occur:
```bash
# CAUTION: This will reset Milvus data
docker compose down milvus milvus-etcd milvus-minio
docker volume rm ai-karen_milvus_data ai-karen_etcd_data
docker compose up -d milvus-etcd milvus-minio milvus
```

## Monitoring Commands

### Check Milvus Health
```bash
# HTTP health check
curl -s http://localhost:9091/health

# gRPC connectivity test
timeout 3 bash -c '</dev/tcp/localhost/19530'

# Check for recent errors
docker logs ai-karen-milvus --since 5m | grep -i error
```

### Check Node Coordination
```bash
# Monitor node IDs in logs
docker logs ai-karen-milvus | grep -i "nodeID\|node not match"

# Check etcd health
docker logs ai-karen-milvus-etcd --tail 10
```

## Configuration Optimizations

The current Milvus configuration includes:
- **Standalone mode** for simplified deployment
- **Proper dependency ordering** with health checks
- **Extended health check timeouts** (300s start period)
- **Volume persistence** for data durability

## When to Take Action

**Immediate action needed if:**
- Health checks consistently fail for >5 minutes
- gRPC port 19530 becomes inaccessible
- Backend API memory/vector operations fail

**Normal operational messages (no action needed):**
- Periodic GC tune messages
- Channel balancer reallocation logs
- Rocksmq statistics

## Integration with AI-Karen Backend

The backend connects to Milvus via:
- **Host:** `milvus` (internal Docker network)
- **Port:** `19530` (gRPC)
- **Configuration:** Environment variables in docker-compose.yml

Monitor backend logs for Milvus connection issues:
```bash
docker logs ai-karen-api | grep -i milvus
```
