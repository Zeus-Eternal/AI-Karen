#!/bin/bash

echo "🔧 AI-Karen Connection Issue Fix Script"
echo "======================================="

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found. Creating one from template..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "✅ Created .env from .env.example"
    else
        echo "❌ No .env.example found. Please create .env manually."
        exit 1
    fi
fi

# Source environment variables
if [ -f ".env" ]; then
    echo "📋 Loading environment variables from .env..."
    export $(grep -v '^#' .env | xargs)
fi

# Check if services are running
echo "1. Checking service status..."
docker compose ps

# Check what's listening on ports
echo -e "\n2. Checking port bindings..."
ss -ltnp | grep -E ':(8000|8001|3000|8020|5433|6379)' || echo "No services found on expected ports"

# Test API health
echo -e "\n3. Testing API connectivity..."
if curl -s -f http://localhost:8000/health > /dev/null; then
    echo "✅ API is responding on port 8000"
else
    echo "❌ API is not responding on port 8000"
fi

# Check for port 8001 (the problematic one)
if curl -s -f http://localhost:8001/health > /dev/null 2>&1; then
    echo "⚠️  Something is responding on port 8001 (unexpected)"
else
    echo "✅ Nothing on port 8001 (as expected)"
fi

# Check environment variables
echo -e "\n4. Checking environment configuration..."
echo "KAREN_BACKEND_URL: ${KAREN_BACKEND_URL:-'Not set'}"
echo "API_BASE_URL: ${API_BASE_URL:-'Not set'}"
echo "NEXT_PUBLIC_API_URL: ${NEXT_PUBLIC_API_URL:-'Not set'}"

# Quick fix steps
echo -e "\n5. Applying quick fixes..."

# Set correct environment variables
export KAREN_BACKEND_URL="http://127.0.0.1:8000"
export API_BASE_URL="http://127.0.0.1:8000"
export NEXT_PUBLIC_API_URL="http://127.0.0.1:8000"

echo "✅ Environment variables set to correct values"

# Restart web UI to pick up changes
echo -e "\n6. Restarting web UI..."
docker compose restart web-ui

echo -e "\n7. Waiting for services to be ready..."
sleep 10

# Final verification
echo -e "\n8. Final verification..."
if curl -s -f http://localhost:8000/health > /dev/null; then
    echo "✅ API health check passed"
else
    echo "❌ API health check failed"
fi

# Check web UI
if curl -s -f http://localhost:8020 > /dev/null 2>&1 || curl -s -f http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ Web UI is accessible"
else
    echo "❌ Web UI is not accessible"
fi

echo -e "\n🎉 Fix script completed!"
echo "If issues persist, try:"
echo "1. docker compose down && docker compose up -d"
echo "2. Clear browser cache and reload"
echo "3. Check the troubleshooting guide: docs/troubleshooting/NETWORK_CONNECTIVITY_GUIDE.md"