#!/bin/bash

# Script to test Docker services after fixes

echo "Testing Docker services..."

# Function to check if a service is healthy
check_service_health() {
    local service_name=$1
    local max_attempts=30
    local attempt=1

    echo "Checking health of $service_name..."

    while [ $attempt -le $max_attempts ]; do
        local health_status=$(docker inspect --format='{{.State.Health.Status}}' "$service_name" 2>/dev/null || echo "unknown")
        
        if [ "$health_status" = "healthy" ]; then
            echo "✅ $service_name is healthy"
            return 0
        elif [ "$health_status" = "starting" ]; then
            echo "⏳ $service_name is starting... (attempt $attempt/$max_attempts)"
        elif [ "$health_status" = "unhealthy" ]; then
            echo "❌ $service_name is unhealthy"
            return 1
        else
            echo "⏳ $service_name status: $health_status... (attempt $attempt/$max_attempts)"
        fi

        sleep 5
        attempt=$((attempt + 1))
    done

    echo "❌ $service_name did not become healthy within $max_attempts attempts"
    return 1
}

# Function to check if a container is running
check_container_running() {
    local container_name=$1
    
    if docker ps --format "table {{.Names}}" | grep -q "$container_name"; then
        echo "✅ $container_name is running"
        return 0
    else
        echo "❌ $container_name is not running"
        return 1
    fi
}

# Function to check Redis connection
check_redis_connection() {
    echo "Testing Redis connection..."
    
    if docker exec ai-karen-redis redis-cli ping 2>/dev/null | grep -q "PONG"; then
        echo "✅ Redis connection successful"
        return 0
    else
        echo "❌ Redis connection failed"
        return 1
    fi
}

# Function to check MinIO connection
check_minio_connection() {
    echo "Testing MinIO connection..."
    
    if docker exec ai-karen-milvus-minio curl -f http://localhost:9000/minio/health/live 2>/dev/null | grep -q "ok"; then
        echo "✅ MinIO connection successful"
        return 0
    else
        echo "❌ MinIO connection failed"
        return 1
    fi
}

# Function to check etcd connection
check_etcd_connection() {
    echo "Testing etcd connection..."
    
    if docker exec ai-karen-milvus-etcd etcdctl endpoint health 2>/dev/null | grep -q "is healthy"; then
        echo "✅ etcd connection successful"
        return 0
    else
        echo "❌ etcd connection failed"
        return 1
    fi
}

# Function to check Milvus connection
check_milvus_connection() {
    echo "Testing Milvus connection..."
    
    if docker exec ai-karen-milvus curl -f http://localhost:9091/healthz 2>/dev/null | grep -q "healthy"; then
        echo "✅ Milvus connection successful"
        return 0
    else
        echo "❌ Milvus connection failed"
        return 1
    fi
}

# Main testing function
run_tests() {
    local failed_tests=0

    echo "=========================================="
    echo "Starting Docker services tests"
    echo "=========================================="

    # Check if containers are running
    echo ""
    echo "1. Checking if containers are running..."
    echo "----------------------------------------"
    
    containers=("ai-karen-postgres" "ai-karen-elasticsearch" "ai-karen-milvus-etcd" "ai-karen-milvus-minio" "ai-karen-milvus" "ai-karen-redis" "ai-karen-duckdb-manager")
    
    for container in "${containers[@]}"; do
        if ! check_container_running "$container"; then
            failed_tests=$((failed_tests + 1))
        fi
    done

    # Check service health
    echo ""
    echo "2. Checking service health..."
    echo "----------------------------------------"
    
    services=("ai-karen-postgres" "ai-karen-elasticsearch" "ai-karen-milvus-etcd" "ai-karen-milvus-minio" "ai-karen-milvus" "ai-karen-redis")
    
    for service in "${services[@]}"; do
        if ! check_service_health "$service"; then
            failed_tests=$((failed_tests + 1))
        fi
    done

    # Check connections
    echo ""
    echo "3. Checking service connections..."
    echo "----------------------------------------"
    
    if ! check_redis_connection; then
        failed_tests=$((failed_tests + 1))
    fi
    
    if ! check_minio_connection; then
        failed_tests=$((failed_tests + 1))
    fi
    
    if ! check_etcd_connection; then
        failed_tests=$((failed_tests + 1))
    fi
    
    if ! check_milvus_connection; then
        failed_tests=$((failed_tests + 1))
    fi

    # Summary
    echo ""
    echo "=========================================="
    echo "Test Summary"
    echo "=========================================="
    
    if [ $failed_tests -eq 0 ]; then
        echo "✅ All tests passed! Docker services are running correctly."
        exit 0
    else
        echo "❌ $failed_tests test(s) failed. Please check the logs above for details."
        exit 1
    fi
}

# Run the tests
run_tests