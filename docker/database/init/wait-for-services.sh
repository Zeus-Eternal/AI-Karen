#!/bin/bash
set -e

# Service Readiness Checker for AI Karen Database Stack
# This script waits for all database services to be ready before proceeding

echo "⏳ Waiting for AI Karen database services to be ready..."

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Function to check PostgreSQL
check_postgres() {
    local host="${POSTGRES_HOST:-postgres}"
    local port="${POSTGRES_PORT:-5432}"
    local user="${POSTGRES_USER:-karen_user}"
    local db="${POSTGRES_DB:-ai_karen}"
    
    log "Checking PostgreSQL at $host:$port..."
    
    if command -v pg_isready > /dev/null 2>&1; then
        pg_isready -h "$host" -p "$port" -U "$user" -d "$db"
    else
        # Fallback using netcat
        nc -z "$host" "$port"
    fi
}

# Function to check Elasticsearch
check_elasticsearch() {
    local host="${ELASTICSEARCH_HOST:-elasticsearch}"
    local port="${ELASTICSEARCH_PORT:-9200}"
    
    log "Checking Elasticsearch at $host:$port..."
    
    if command -v curl > /dev/null 2>&1; then
        curl -s -f "http://$host:$port/_cluster/health" > /dev/null
    else
        nc -z "$host" "$port"
    fi
}

# Function to check Milvus
check_milvus() {
    local host="${MILVUS_HOST:-milvus}"
    local port="${MILVUS_PORT:-19530}"
    
    log "Checking Milvus at $host:$port..."
    nc -z "$host" "$port"
}

# Function to check Redis
check_redis() {
    local host="${REDIS_HOST:-redis}"
    local port="${REDIS_PORT:-6379}"
    local password="${REDIS_PASSWORD:-}"
    
    log "Checking Redis at $host:$port..."
    
    if command -v redis-cli > /dev/null 2>&1; then
        if [ -n "$password" ]; then
            redis-cli -h "$host" -p "$port" -a "$password" ping > /dev/null
        else
            redis-cli -h "$host" -p "$port" ping > /dev/null
        fi
    else
        nc -z "$host" "$port"
    fi
}

# Function to check ETCD (for Milvus)
check_etcd() {
    local host="${ETCD_HOST:-milvus-etcd}"
    local port="${ETCD_PORT:-2379}"
    
    log "Checking ETCD at $host:$port..."
    nc -z "$host" "$port"
}

# Function to check MinIO (for Milvus)
check_minio() {
    local host="${MINIO_HOST:-milvus-minio}"
    local port="${MINIO_PORT:-9000}"
    
    log "Checking MinIO at $host:$port..."
    
    if command -v curl > /dev/null 2>&1; then
        curl -s -f "http://$host:$port/minio/health/live" > /dev/null
    else
        nc -z "$host" "$port"
    fi
}

# Function to wait for a service with retries
wait_for_service() {
    local service_name="$1"
    local check_function="$2"
    local max_attempts="${3:-60}"
    local attempt=1
    
    log "Waiting for $service_name to be ready..."
    
    while [ $attempt -le $max_attempts ]; do
        if $check_function; then
            log "✅ $service_name is ready!"
            return 0
        fi
        
        log "Attempt $attempt/$max_attempts: $service_name not ready, waiting 5 seconds..."
        sleep 5
        attempt=$((attempt + 1))
    done
    
    log "❌ $service_name failed to become ready after $max_attempts attempts"
    return 1
}

# Install required tools
log "Installing required tools..."
apk add --no-cache curl netcat-openbsd postgresql-client redis

# Wait for all services
log "Starting service readiness checks..."

# Core database services
wait_for_service "PostgreSQL" "check_postgres" 30
wait_for_service "Redis" "check_redis" 30
wait_for_service "Elasticsearch" "check_elasticsearch" 60

# Milvus dependencies first
wait_for_service "ETCD" "check_etcd" 30
wait_for_service "MinIO" "check_minio" 30

# Then Milvus itself
wait_for_service "Milvus" "check_milvus" 60

# Additional health checks
log "Performing additional health checks..."

# Check PostgreSQL can accept connections
log "Testing PostgreSQL connection..."
if psql -h "${POSTGRES_HOST:-postgres}" -U "${POSTGRES_USER:-karen_user}" -d "${POSTGRES_DB:-ai_karen}" -c "SELECT 1;" > /dev/null 2>&1; then
    log "✅ PostgreSQL connection test passed"
else
    log "❌ PostgreSQL connection test failed"
    exit 1
fi

# Check Elasticsearch cluster health
log "Testing Elasticsearch cluster health..."
cluster_health=$(curl -s "http://${ELASTICSEARCH_HOST:-elasticsearch}:${ELASTICSEARCH_PORT:-9200}/_cluster/health" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
if [ "$cluster_health" = "green" ] || [ "$cluster_health" = "yellow" ]; then
    log "✅ Elasticsearch cluster health: $cluster_health"
else
    log "❌ Elasticsearch cluster health check failed: $cluster_health"
    exit 1
fi

# Check Redis functionality
log "Testing Redis functionality..."
if redis-cli -h "${REDIS_HOST:-redis}" -p "${REDIS_PORT:-6379}" ${REDIS_PASSWORD:+-a "$REDIS_PASSWORD"} set test_key test_value > /dev/null 2>&1; then
    if redis-cli -h "${REDIS_HOST:-redis}" -p "${REDIS_PORT:-6379}" ${REDIS_PASSWORD:+-a "$REDIS_PASSWORD"} get test_key | grep -q "test_value"; then
        redis-cli -h "${REDIS_HOST:-redis}" -p "${REDIS_PORT:-6379}" ${REDIS_PASSWORD:+-a "$REDIS_PASSWORD"} del test_key > /dev/null 2>&1
        log "✅ Redis functionality test passed"
    else
        log "❌ Redis read test failed"
        exit 1
    fi
else
    log "❌ Redis write test failed"
    exit 1
fi

# Create readiness marker
log "Creating readiness marker..."
mkdir -p /tmp/ai_karen_init
echo "$(date -Iseconds)" > /tmp/ai_karen_init/services_ready
echo "All services are ready for initialization" > /tmp/ai_karen_init/status

log "🎉 All database services are ready!"
log "Services verified:"
log "  - PostgreSQL: ${POSTGRES_HOST:-postgres}:${POSTGRES_PORT:-5432}"
log "  - Elasticsearch: ${ELASTICSEARCH_HOST:-elasticsearch}:${ELASTICSEARCH_PORT:-9200}"
log "  - Milvus: ${MILVUS_HOST:-milvus}:${MILVUS_PORT:-19530}"
log "  - Redis: ${REDIS_HOST:-redis}:${REDIS_PORT:-6379}"
log "  - ETCD: ${ETCD_HOST:-milvus-etcd}:${ETCD_PORT:-2379}"
log "  - MinIO: ${MINIO_HOST:-milvus-minio}:${MINIO_PORT:-9000}"

log "Ready to proceed with database initialization!"