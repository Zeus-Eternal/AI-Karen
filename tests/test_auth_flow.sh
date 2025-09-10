#!/bin/bash

echo "🔐 Testing authentication flow..."
echo

# Step 1: Login and save cookies
echo "1. Logging in..."
LOGIN_RESPONSE=$(curl -s -c auth_cookies.txt -X POST \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"admin123"}' \
  http://localhost:8010/api/auth/login)

if echo "$LOGIN_RESPONSE" | grep -q "access_token"; then
  echo "✅ Login successful!"
  echo "   Response: $(echo "$LOGIN_RESPONSE" | jq -r '.user.email // "Unknown"') logged in"
  
  # Extract access token
  ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.access_token')
  echo "   Access token: ${ACCESS_TOKEN:0:50}..."
else
  echo "❌ Login failed!"
  echo "   Response: $LOGIN_RESPONSE"
  exit 1
fi

echo

# Step 2: Test /api/auth/me with token
echo "2. Testing /api/auth/me with Bearer token..."
ME_RESPONSE=$(curl -s -b auth_cookies.txt \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  http://localhost:8010/api/auth/me)

if echo "$ME_RESPONSE" | grep -q "email"; then
  echo "✅ /api/auth/me successful!"
  echo "   User: $(echo "$ME_RESPONSE" | jq -r '.email // "Unknown"')"
else
  echo "❌ /api/auth/me failed!"
  echo "   Response: $ME_RESPONSE"
fi

echo

# Step 3: Test /api/models/library with token
echo "3. Testing /api/models/library with Bearer token..."
MODELS_RESPONSE=$(curl -s -b auth_cookies.txt \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  http://localhost:8010/api/models/library)

if echo "$MODELS_RESPONSE" | grep -q -v "Authentication required"; then
  echo "✅ /api/models/library successful!"
  if echo "$MODELS_RESPONSE" | jq -e '. | type == "array"' > /dev/null 2>&1; then
    MODEL_COUNT=$(echo "$MODELS_RESPONSE" | jq '. | length')
    echo "   Models available: $MODEL_COUNT"
  else
    echo "   Response: $(echo "$MODELS_RESPONSE" | head -c 100)..."
  fi
else
  echo "❌ /api/models/library failed!"
  echo "   Response: $MODELS_RESPONSE"
fi

echo

# Step 4: Test without token (should fail)
echo "4. Testing /api/models/library without token (should fail)..."
NO_AUTH_RESPONSE=$(curl -s http://localhost:8010/api/models/library)

if echo "$NO_AUTH_RESPONSE" | grep -q "Authentication required"; then
  echo "✅ Correctly rejected request without authentication"
else
  echo "⚠️  Request without auth succeeded (unexpected)"
  echo "   Response: $NO_AUTH_RESPONSE"
fi

echo
echo "🎉 Authentication flow test completed!"

# Cleanup
rm -f auth_cookies.txt