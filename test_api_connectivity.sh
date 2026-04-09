#!/bin/bash

# Test API connectivity after configuration fix
echo "🧪 Testing API connectivity..."

# Test backend directly
echo "1. Testing backend health..."
BACKEND_HEALTH=$(curl -s -X GET "http://172.21.0.10:8000/api/auth/health" --connect-timeout 5)
if echo "$BACKEND_HEALTH" | grep -q "healthy"; then
    echo "✅ Backend is healthy at 172.21.0.10:8000"
else
    echo "❌ Backend not responding at 172.21.0.10:8000"
    exit 1
fi

# Test profile update endpoint
echo "2. Testing profile update endpoint..."
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJkZXYtdXNlciIsImlhdCI6MTc3NTQ4NzgzNywiaWF0IjoxNzcwNTQ3ODM3LCJleHAiOjE3NzU0ODk2MzcsImV4cCI6MTc3MDU0OTYzNywiZW1haWwiOiJhZG1pbkBrYXJlbi5haSIsInVzZXJfdHlwZSI6ImFkbWpbZSIsInBlcm1pc3Npb25zIjpbImFkbWluIiwidXNlciJdLCJyb2xlcyI6WyJhZG1pbiIsInVzZXIiXX0.kR63kw_9vXGUB8merQKdnK-TqDaH_ffTNV87Mvrx2Us"

PROFILE_UPDATE=$(curl -s -X PUT "http://172.21.0.10:8000/api/auth/me" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"full_name": "Test User"}' \
  --connect-timeout 5)

if echo "$PROFILE_UPDATE" | grep -q "user_id"; then
    echo "✅ Profile update endpoint working"
    echo "   Updated user: $(echo $PROFILE_UPDATE | jq -r '.full_name')"
else
    echo "❌ Profile update failed:"
    echo "$PROFILE_UPDATE"
    exit 1
fi

echo ""
echo "🎉 API connectivity test passed!"
echo ""
echo "📝 Configuration Summary:"
echo "   - Frontend container: 172.21.0.11:8010"
echo "   - Backend container: 172.21.0.10:8000"
echo "   - API calls now routed correctly"
echo ""
echo "🌐 Next Steps:"
echo "   1. Frontend should now connect to backend properly"
echo "   2. Profile updates should work in the web interface"
echo "   3. All other API calls should function correctly"