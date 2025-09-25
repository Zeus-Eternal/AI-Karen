#!/bin/bash

echo "🔧 AI-Karen CORS Issue Fix Script"
echo "================================="

# Get the current frontend IP from the error logs
FRONTEND_IP="10.96.136.74"
FRONTEND_PORT="8020"

echo "🌐 Detected frontend running on: http://${FRONTEND_IP}:${FRONTEND_PORT}"

# 1. Update CORS configuration in .env
echo "1. Updating CORS configuration..."

# Backup current .env
cp .env .env.backup

# Update CORS origins to include the frontend IP
if grep -q "KARI_CORS_ORIGINS" .env; then
    # Check if IP is already in CORS origins
    if grep -q "${FRONTEND_IP}" .env; then
        echo "✅ Frontend IP already in CORS origins"
    else
        # Add frontend IP to existing CORS origins
        sed -i "s|KARI_CORS_ORIGINS=\(.*\)|KARI_CORS_ORIGINS=\1,http://${FRONTEND_IP}:${FRONTEND_PORT},http://${FRONTEND_IP}:3000|" .env
        echo "✅ Added frontend IP to CORS origins"
    fi
else
    # Add CORS origins if not present
    echo "KARI_CORS_ORIGINS=http://localhost:3000,http://localhost:8020,http://127.0.0.1:3000,http://127.0.0.1:8020,http://${FRONTEND_IP}:${FRONTEND_PORT},http://${FRONTEND_IP}:3000" >> .env
    echo "✅ Added CORS origins to .env"
fi

# Ensure other CORS settings are present
grep -q "KARI_CORS_METHODS" .env || echo "KARI_CORS_METHODS=*" >> .env
grep -q "KARI_CORS_HEADERS" .env || echo "KARI_CORS_HEADERS=*" >> .env
grep -q "KARI_CORS_CREDENTIALS" .env || echo "KARI_CORS_CREDENTIALS=true" >> .env

# 2. Show current CORS configuration
echo -e "\n2. Current CORS configuration:"
grep "KARI_CORS" .env

# 3. Restart backend to apply CORS changes
echo -e "\n3. Restarting backend services..."
docker compose restart api

# 4. Wait for backend to be ready
echo "4. Waiting for backend to restart..."
sleep 15

# 5. Test CORS configuration
echo -e "\n5. Testing CORS configuration..."

# Test OPTIONS preflight request
echo "Testing CORS preflight request..."
CORS_TEST=$(curl -s -I -H "Origin: http://${FRONTEND_IP}:${FRONTEND_PORT}" \
     -H "Access-Control-Request-Method: POST" \
     -H "Access-Control-Request-Headers: Content-Type,Authorization" \
     -X OPTIONS \
     http://localhost:8000/api/health 2>/dev/null)

if echo "$CORS_TEST" | grep -q "Access-Control-Allow-Origin"; then
    echo "✅ CORS preflight request successful"
    echo "$CORS_TEST" | grep "Access-Control"
else
    echo "❌ CORS preflight request failed"
    echo "Response headers:"
    echo "$CORS_TEST"
fi

# Test actual API request
echo -e "\nTesting API health endpoint..."
API_TEST=$(curl -s -H "Origin: http://${FRONTEND_IP}:${FRONTEND_PORT}" \
     http://localhost:8000/health 2>/dev/null)

if echo "$API_TEST" | grep -q "healthy\|status"; then
    echo "✅ API health check successful"
    echo "Response: $API_TEST"
else
    echo "❌ API health check failed"
    echo "Response: $API_TEST"
fi

# 6. Test authentication endpoint
echo -e "\n6. Testing authentication endpoint..."
AUTH_TEST=$(curl -s -X POST \
     -H "Origin: http://${FRONTEND_IP}:${FRONTEND_PORT}" \
     -H "Content-Type: application/json" \
     http://localhost:8000/api/auth/dev-login \
     -d '{}' 2>/dev/null)

if echo "$AUTH_TEST" | grep -q "access_token\|token"; then
    echo "✅ Authentication endpoint working"
else
    echo "❌ Authentication endpoint failed"
    echo "Response: $AUTH_TEST"
fi

# 7. Check if backend is accessible from frontend IP
echo -e "\n7. Network connectivity check..."
if curl -s -f http://localhost:8000/health > /dev/null; then
    echo "✅ Backend is accessible on localhost:8000"
else
    echo "❌ Backend is not accessible on localhost:8000"
fi

# 8. Final recommendations
echo -e "\n8. Final recommendations:"
echo "✅ CORS configuration updated"
echo "✅ Backend restarted"

if echo "$CORS_TEST" | grep -q "Access-Control-Allow-Origin"; then
    echo "✅ CORS is working - frontend should now be able to connect"
    echo ""
    echo "🎉 Fix completed successfully!"
    echo ""
    echo "Next steps:"
    echo "1. Refresh your browser (Ctrl+Shift+R or Cmd+Shift+R)"
    echo "2. Clear browser cache if needed"
    echo "3. Try logging in again"
else
    echo "❌ CORS may still have issues"
    echo ""
    echo "Additional troubleshooting:"
    echo "1. Check if backend is running: docker compose ps"
    echo "2. Check backend logs: docker compose logs api"
    echo "3. Verify .env file: grep KARI_CORS .env"
    echo "4. Try restarting all services: docker compose down && docker compose up -d"
fi

echo ""
echo "📚 For more help, see: docs/troubleshooting/CORS_ISSUES_FIX.md"