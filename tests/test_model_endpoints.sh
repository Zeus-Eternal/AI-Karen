#!/bin/bash

echo "🔧 Testing model library endpoints after fixes..."
echo

# Test 1: Test /api/models/stats (should work without auth now)
echo "1. Testing /api/models/stats (no auth required)..."
STATS_RESPONSE=$(timeout 10 curl -s http://localhost:8010/api/models/stats)
if echo "$STATS_RESPONSE" | grep -q "total_models"; then
  echo "✅ /api/models/stats successful!"
  echo "   Total models: $(echo "$STATS_RESPONSE" | jq -r '.total_models // "Unknown"')"
else
  echo "❌ /api/models/stats failed!"
  echo "   Response: $STATS_RESPONSE"
fi

echo

# Test 2: Test /api/models/library (should work without auth now)
echo "2. Testing /api/models/library (no auth required)..."
LIBRARY_RESPONSE=$(timeout 10 curl -s http://localhost:8010/api/models/library)
if echo "$LIBRARY_RESPONSE" | grep -q "models"; then
  echo "✅ /api/models/library successful!"
  if echo "$LIBRARY_RESPONSE" | jq -e '.models | type == "array"' > /dev/null 2>&1; then
    MODEL_COUNT=$(echo "$LIBRARY_RESPONSE" | jq '.models | length')
    echo "   Models available: $MODEL_COUNT"
  else
    echo "   Response: $(echo "$LIBRARY_RESPONSE" | head -c 100)..."
  fi
else
  echo "❌ /api/models/library failed!"
  echo "   Response: $LIBRARY_RESPONSE"
fi

echo

# Test 3: Test with authentication (should also work)
echo "3. Testing with authentication..."
LOGIN_RESPONSE=$(curl -s -X POST \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"admin123"}' \
  http://localhost:8010/api/auth/login)

if echo "$LOGIN_RESPONSE" | grep -q "access_token"; then
  ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.access_token')
  echo "✅ Login successful, testing authenticated requests..."
  
  # Test authenticated stats request
  AUTH_STATS_RESPONSE=$(timeout 10 curl -s \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    http://localhost:8010/api/models/stats)
  
  if echo "$AUTH_STATS_RESPONSE" | grep -q "total_models"; then
    echo "✅ Authenticated /api/models/stats successful!"
  else
    echo "❌ Authenticated /api/models/stats failed!"
    echo "   Response: $AUTH_STATS_RESPONSE"
  fi
else
  echo "❌ Login failed, skipping authenticated tests"
  echo "   Response: $LOGIN_RESPONSE"
fi

echo
echo "🎉 Model endpoints test completed!"