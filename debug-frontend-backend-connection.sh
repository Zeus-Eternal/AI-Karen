#!/bin/bash

echo "🔍 AI-Karen Frontend-Backend Connection Debug & Fix"
echo "=================================================="

# Check if backend is running
echo "1. Checking backend status..."
if curl -s http://127.0.0.1:8000/health > /dev/null; then
    echo "✅ Backend is running on http://127.0.0.1:8000"
else
    echo "❌ Backend is not responding on http://127.0.0.1:8000"
    echo "   Starting backend..."
    python start.py &
    sleep 5
fi

# Check frontend process
echo "2. Checking frontend processes..."
FRONTEND_PID=$(pgrep -f "next.*dev" | head -1)
if [ -n "$FRONTEND_PID" ]; then
    echo "✅ Frontend is running (PID: $FRONTEND_PID)"
else
    echo "❌ Frontend is not running"
fi

# Check port conflicts
echo "3. Checking for port conflicts..."
echo "Port 8000 (Backend):"
netstat -tlnp | grep :8000 || echo "   No process on port 8000"
echo "Port 3000 (Frontend):"
netstat -tlnp | grep :3000 || echo "   No process on port 3000"
echo "Port 8010 (Problematic):"
netstat -tlnp | grep :8010 || echo "   No process on port 8010"

# Test API endpoints
echo "4. Testing API endpoints..."
echo "Backend health:"
curl -s http://127.0.0.1:8000/health | jq . 2>/dev/null || echo "   Failed to connect"

echo "Models library:"
curl -s http://127.0.0.1:8000/api/models/library | jq . 2>/dev/null || echo "   Failed to connect"

echo "Auth endpoint:"
curl -s http://127.0.0.1:8000/api/auth/me | jq . 2>/dev/null || echo "   Failed to connect (expected without auth)"

# Check environment variables
echo "5. Environment configuration:"
echo "KAREN_BACKEND_URL: ${KAREN_BACKEND_URL:-'Not set'}"
echo "NEXT_PUBLIC_API_BASE_URL: ${NEXT_PUBLIC_API_BASE_URL:-'Not set'}"

echo ""
echo "🔧 Recommended fixes:"
echo "1. Ensure backend is running: python start.py"
echo "2. Update frontend environment to use correct backend URL"
echo "3. Clear browser cache and localStorage"
echo "4. Restart frontend development server"