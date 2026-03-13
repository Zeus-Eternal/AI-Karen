#!/bin/bash

# Script to deploy database services with fixes

set -e

echo "=========================================="
echo "AI Karen Database Services Deployment"
echo "=========================================="

# Function to print step header
print_step() {
    echo ""
    echo "Step $1: $2"
    echo "----------------------------------------"
}

# Step 1: Fix Redis memory overcommit issue
print_step "1" "Fixing Redis memory overcommit issue"
if [ -x "./fix-redis-memory-overcommit.sh" ]; then
    ./fix-redis-memory-overcommit.sh
else
    echo "❌ fix-redis-memory-overcommit.sh script not found or not executable"
    exit 1
fi

# Step 2: Stop existing containers
print_step "2" "Stopping existing containers"
cd ../database
if [ -f "docker-compose.yml" ]; then
    docker compose down --remove-orphans
    
    # Remove any remaining containers with the same names
    echo "Removing any remaining containers..."
    docker rm -f ai-karen-postgres 2>/dev/null || true
    docker rm -f ai-karen-elasticsearch 2>/dev/null || true
    docker rm -f ai-karen-milvus-etcd 2>/dev/null || true
    docker rm -f ai-karen-milvus-minio 2>/dev/null || true
    docker rm -f ai-karen-milvus 2>/dev/null || true
    docker rm -f ai-karen-redis 2>/dev/null || true
    docker rm -f ai-karen-duckdb-manager 2>/dev/null || true
    
    echo "✅ Existing containers stopped and removed"
else
    echo "❌ docker-compose.yml not found"
    exit 1
fi

# Step 3: Clean up unused volumes and networks
print_step "3" "Cleaning up unused volumes and networks"
docker system prune -f
docker volume prune -f
echo "✅ Cleanup completed"

# Step 4: Start the services
print_step "4" "Starting database services"
docker compose up -d
echo "✅ Services started"

# Step 5: Wait for services to be ready
print_step "5" "Waiting for services to be ready"
echo "This may take a few minutes..."

# Wait for 60 seconds to allow services to start
sleep 60

# Step 6: Test the services
print_step "6" "Testing service connections"
if [ -x "./test-docker-services.sh" ]; then
    ./test-docker-services.sh
else
    echo "❌ test-docker-services.sh script not found or not executable"
    exit 1
fi

# Step 7: Display status
print_step "7" "Displaying service status"
docker-compose ps

echo ""
echo "=========================================="
echo "Deployment completed successfully!"
echo "=========================================="
echo ""
echo "To view logs, run:"
echo "  docker-compose logs -f [service-name]"
echo ""
echo "To stop all services, run:"
echo "  docker compose down"
echo ""
echo "To run the test script again, run:"
echo "  ./scripts/test-docker-services.sh"
echo ""