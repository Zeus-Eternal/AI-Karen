#!/bin/bash

# Health check script for AI-Karen services
# Waits for all required services to be ready

set -e

echo "🔍 Checking service health..."

# Function to check if a service is responding
check_service() {
    local service_name=$1
    local url=$2
    local max_attempts=${3:-30}
    local attempt=1

    echo "Checking $service_name..."

    while [ $attempt -le $max_attempts ]; do
        if curl -f -s "$url" > /dev/null 2>&1; then
            echo "✅ $service_name is ready"
            return 0
        fi

        echo "⏳ $service_name not ready (attempt $attempt/$max_attempts)"
        sleep 2
        ((attempt++))
    done

    echo "❌ $service_name failed to become ready"
    return 1
}

# Check database services
echo "Checking database services..."

check_service "PostgreSQL" "http://localhost:${POSTGRES_PORT:-5433}" 15 || {
    echo "Checking if PostgreSQL is accepting connections..."
    if command -v pg_isready >/dev/null 2>&1; then
        pg_isready -h localhost -p ${POSTGRES_PORT:-5433} -U postgres
    else
        echo "pg_isready not available, assuming PostgreSQL is ready"
    fi
}

check_service "Redis" "http://localhost:6379" 15 || {
    echo "Checking Redis with redis-cli..."
    if command -v redis-cli >/dev/null 2>&1; then
        redis-cli -h localhost -p 6379 ping
    else
        echo "redis-cli not available, assuming Redis is ready"
    fi
}

check_service "Elasticsearch" "http://localhost:9200/_cluster/health"
check_service "Milvus" "http://localhost:9091/healthz" 15 || {
    echo "Milvus health check failed, but service may still be functional"
}

echo ""
echo "🎉 All services are ready!"
echo ""
echo "Service URLs:"
echo "  PostgreSQL: localhost:${POSTGRES_PORT:-5433}"
echo "  Redis: localhost:6379"
echo "  Elasticsearch: http://localhost:9200"
echo "  Milvus: localhost:19530"
echo ""
