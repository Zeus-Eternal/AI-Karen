#!/bin/bash

echo "🚨 EMERGENCY: Backend Not Running - Quick Fix"
echo "============================================="

# Check if backend is running
if curl -s -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend is actually running - this might be a different issue"
    exit 0
fi

echo "❌ Backend is not running. Applying emergency fix..."

# 1. Stop everything
echo "1. Stopping all services..."
docker compose down

# 2. Check for port conflicts
echo "2. Checking for port conflicts..."
if ss -ltn | grep -q ":8000 "; then
    echo "⚠️  Something else is using port 8000"
    echo "Processes using port 8000:"
    ss -ltnp | grep ":8000 "
    echo "You may need to kill these processes or change the port"
fi

# 3. Start essential services first
echo "3. Starting database services..."
docker compose up -d postgres redis

# Wait for databases
echo "4. Waiting for databases to be ready..."
sleep 10

# 5. Start API
echo "5. Starting API service..."
docker compose up -d api

# 6. Wait and test
echo "6. Waiting for API to start..."
for i in {1..30}; do
    if curl -s -f http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ Backend is now running! (after ${i} seconds)"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ Backend failed to start after 30 seconds"
        echo "Checking logs..."
        docker compose logs api --tail=10
        exit 1
    fi
    sleep 1
done

# 7. Test endpoints
echo "7. Testing endpoints..."
health=$(curl -s http://localhost:8000/health)
echo "Health: $health"

# 8. Start web UI
echo "8. Starting web UI..."
docker compose up -d web-ui

echo ""
echo "🎉 Emergency fix completed!"
echo ""
echo "✅ Backend should now be accessible at: http://localhost:8000"
echo "✅ Try refreshing your browser"
echo ""
echo "If this doesn't work, run: ./diagnose-and-fix-backend.sh"