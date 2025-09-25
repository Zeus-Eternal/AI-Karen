#!/bin/bash

echo "🔧 AI-Karen Frontend-Backend Debug Fix"
echo "======================================"

# Step 1: Fix environment configuration
echo "1. Updating frontend environment configuration..."

# Create proper .env.local for frontend
cat > ui_launchers/web_ui/.env.local << 'EOF'
# API Configuration - Fixed for proper connection
NEXT_PUBLIC_API_BASE_URL=http://localhost:3000
NEXT_PUBLIC_KAREN_BACKEND_URL=http://127.0.0.1:8000
KAREN_BACKEND_URL=http://127.0.0.1:8000
API_BASE_URL=http://127.0.0.1:8000

# Environment
NODE_ENV=development
DEBUG=true

# Auth Configuration
AUTH_SECRET_KEY=dev-secret-key-change-in-production
JWT_SECRET=dev-jwt-secret-change-in-production
CSRF_SECRET=dev-csrf-secret-change-in-production

# Feature Flags
NEXT_PUBLIC_ENABLE_PLUGINS=true
NEXT_PUBLIC_ENABLE_MEMORY=true
NEXT_PUBLIC_ENABLE_EXPERIMENTAL=false
NEXT_PUBLIC_ENABLE_DEV_LOGIN=true

# Proxy Configuration - Use Next.js proxy for API calls
NEXT_PUBLIC_USE_PROXY=true
USE_PROXY=true
KAREN_USE_PROXY=true

# CORS and Security
NEXT_PUBLIC_CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://localhost:8000,http://127.0.0.1:8000
EOF

echo "✅ Updated frontend .env.local"

# Step 2: Clear browser cache instructions
echo ""
echo "2. Browser cache clearing instructions:"
echo "   - Open browser developer tools (F12)"
echo "   - Right-click refresh button and select 'Empty Cache and Hard Reload'"
echo "   - Or clear localStorage manually:"
echo "     localStorage.clear(); sessionStorage.clear();"

# Step 3: Test backend connectivity
echo ""
echo "3. Testing backend connectivity..."
if curl -s http://127.0.0.1:8000/health > /dev/null; then
    echo "✅ Backend is responding"
    
    # Test auth endpoint
    echo "Testing auth endpoint..."
    AUTH_RESPONSE=$(curl -s -w "%{http_code}" http://127.0.0.1:8000/api/auth/me)
    if [[ "$AUTH_RESPONSE" == *"401"* ]] || [[ "$AUTH_RESPONSE" == *"Missing authentication token"* ]]; then
        echo "✅ Auth endpoint is working (401 expected without token)"
    else
        echo "⚠️  Auth endpoint response: $AUTH_RESPONSE"
    fi
    
    # Test models endpoint
    echo "Testing models endpoint..."
    MODELS_RESPONSE=$(curl -s http://127.0.0.1:8000/api/models/library | jq -r '.total_count // "error"')
    if [[ "$MODELS_RESPONSE" != "error" ]]; then
        echo "✅ Models endpoint is working ($MODELS_RESPONSE models found)"
    else
        echo "❌ Models endpoint failed"
    fi
else
    echo "❌ Backend is not responding. Starting backend..."
    python start.py &
    sleep 5
fi

# Step 4: Check frontend process
echo ""
echo "4. Checking frontend process..."
FRONTEND_PID=$(pgrep -f "next.*dev" | head -1)
if [ -n "$FRONTEND_PID" ]; then
    echo "✅ Frontend is running (PID: $FRONTEND_PID)"
    echo "   If issues persist, restart with: cd ui_launchers/web_ui && npm run dev"
else
    echo "❌ Frontend is not running"
    echo "   Start with: cd ui_launchers/web_ui && npm run dev"
fi

# Step 5: Port check using ss (more reliable than netstat)
echo ""
echo "5. Port status check:"
if command -v ss > /dev/null; then
    echo "Backend (8000):" $(ss -tlnp | grep :8000 | wc -l) "processes"
    echo "Frontend (3000):" $(ss -tlnp | grep :3000 | wc -l) "processes"
    echo "Port 8010:" $(ss -tlnp | grep :8010 | wc -l) "processes"
    echo "Port 8020:" $(ss -tlnp | grep :8020 | wc -l) "processes"
else
    echo "ss command not available, skipping port check"
fi

echo ""
echo "🎯 Summary of fixes applied:"
echo "1. ✅ Updated frontend environment to use correct backend URL (127.0.0.1:8000)"
echo "2. ✅ Enabled Next.js proxy for API calls"
echo "3. ✅ Fixed CORS configuration"
echo ""
echo "🔄 Next steps:"
echo "1. Clear browser cache and localStorage"
echo "2. Restart frontend if needed: cd ui_launchers/web_ui && npm run dev"
echo "3. Test the application at http://localhost:3000"
echo ""
echo "🐛 If issues persist:"
echo "- Check browser console for specific errors"
echo "- Verify no other services are using conflicting ports"
echo "- Ensure backend is running: python start.py"