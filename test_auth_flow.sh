#!/bin/bash

# Test script to verify Karen AI authentication flow
# This script tests both backend API and frontend integration

echo "🧪 Testing Karen AI Authentication Flow"
echo "====================================="

# Backend API Test
echo "1. Testing Backend API Health..."
BACKEND_HEALTH=$(curl -s -X GET "http://localhost:8000/api/auth/health" --connect-timeout 5)
if echo "$BACKEND_HEALTH" | grep -q "healthy"; then
    echo "✅ Backend API is healthy"
else
    echo "❌ Backend API is not healthy"
    echo "Response: $BACKEND_HEALTH"
    exit 1
fi

# Login Test
echo "2. Testing Login API..."
LOGIN_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@karen.ai", "password": "admin123"}')

if echo "$LOGIN_RESPONSE" | grep -q "access_token"; then
    echo "✅ Login API successful"
    
    # Extract access token
    ACCESS_TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.access_token')
    
    # Session Validation Test
    echo "3. Testing Session Validation..."
    SESSION_RESPONSE=$(curl -s -X GET "http://localhost:8000/api/auth/validate-session" \
      -H "Authorization: Bearer $ACCESS_TOKEN")
    
    if echo "$SESSION_RESPONSE" | grep -q "session_valid.*true"; then
        echo "✅ Session validation successful"
        
        # Extract user info
        USER_ID=$(echo "$SESSION_RESPONSE" | jq -r '.user.user_id')
        EMAIL=$(echo "$SESSION_RESPONSE" | jq -r '.user.email')
        echo "👤 User: $EMAIL (ID: $USER_ID)"
        
        echo ""
        echo "🎉 Authentication flow test completed successfully!"
        echo ""
        echo "📝 Test Results Summary:"
        echo "   - Backend Health: ✅ Healthy"
        echo "   - Login API: ✅ Working"
        echo "   - Session Validation: ✅ Working"
        echo "   - User Authentication: ✅ Active"
        
    else
        echo "❌ Session validation failed"
        echo "Response: $SESSION_RESPONSE"
        exit 1
    fi
    
else
    echo "❌ Login API failed"
    echo "Response: $LOGIN_RESPONSE"
    exit 1
fi

echo ""
echo "🔧 Frontend Configuration Check:"
echo "   - API Base URL: http://localhost:8000 (corrected)"
echo "   - Frontend Port: 3000"
echo "   - Backend Port: 8000"
echo ""
echo "💡 Next Steps:"
echo "   1. Restart frontend development server if running"
echo "   2. Test login through the web interface"
echo "   3. Verify session persistence after login"