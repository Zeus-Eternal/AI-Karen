#!/bin/bash

echo "🚀 Quick Port Conflict Fix"
echo "========================="

# Stop everything first
echo "1. Stopping all containers..."
docker compose down

# Update ports to avoid conflicts
echo "2. Using alternative ports..."
echo "   PostgreSQL: 5434 (instead of 5433)"
echo "   Redis: 6381 (instead of 6380)"

# Start services
echo "3. Starting services with new ports..."
docker compose up -d

# Wait and test
echo "4. Waiting for services..."
sleep 20

echo "5. Testing..."
if curl -s http://localhost:8000/health; then
    echo "✅ Success! Backend is running"
else
    echo "❌ Still having issues. Check: docker compose logs api"
fi