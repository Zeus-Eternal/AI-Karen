#!/bin/bash

# Test script to verify authentication flow
BACKEND_URL="http://127.0.0.1:8000"
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI4YTMyZmQzZC05NGYwLTRmZjgtODE0Yi1lZWYzOTQyYTI3ZDkiLCJlbWFpbCI6ImFkbWluQGV4YW1wbGUuY29tIiwiZnVsbF9uYW1lIjoiQWRtaW4gVXNlciIsInJvbGVzIjpbXSwidGVuYW50X2lkIjoiZmMwY2ExOTQtYTkxYS00NjA1LWE4OWUtMDkzNDQ3ODEyMTM1IiwiaXNfdmVyaWZpZWQiOnRydWUsImlzX2FjdGl2ZSI6dHJ1ZSwiZXhwIjoxNzU2NzQyNDE5LCJpYXQiOjE3NTY3NDE1MTksIm5iZiI6MTc1Njc0MTUxOSwianRpIjoiZTUzNTBkNGE0YzEyYTUyZTQ4ZjY2MzkzOTUxMWVkNDgiLCJ0eXAiOiJhY2Nlc3MifQ.lIeHeeaYxHJtks4-0iL_cNEvf3iUFOUyivc8YaH8lB0"

echo "🚀 Testing Frontend Authentication Flow"
echo "Backend URL: $BACKEND_URL"
echo ""

# Test /api/auth/me
echo "🔍 Testing User Profile..."
response=$(curl -s -w "HTTPSTATUS:%{http_code}" -X GET "$BACKEND_URL/api/auth/me" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json")

http_code=$(echo $response | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
body=$(echo $response | sed -e 's/HTTPSTATUS:.*//g')

if [ "$http_code" -eq 200 ]; then
  echo "   ✅ Success: $http_code"
  echo "   Data: $(echo $body | cut -c1-100)..."
else
  echo "   ❌ Failed: $http_code"
  echo "   Error: $body"
fi

echo ""

# Test /api/plugins/
echo "🔍 Testing Plugins List..."
response=$(curl -s -w "HTTPSTATUS:%{http_code}" -X GET "$BACKEND_URL/api/plugins/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json")

http_code=$(echo $response | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
body=$(echo $response | sed -e 's/HTTPSTATUS:.*//g')

if [ "$http_code" -eq 200 ]; then
  echo "   ✅ Success: $http_code"
  echo "   Data: $(echo $body | cut -c1-100)..."
else
  echo "   ❌ Failed: $http_code"
  echo "   Error: $body"
fi

echo ""

# Test /api/health
echo "🔍 Testing Health Check..."
response=$(curl -s -w "HTTPSTATUS:%{http_code}" -X GET "$BACKEND_URL/api/health" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json")

http_code=$(echo $response | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
body=$(echo $response | sed -e 's/HTTPSTATUS:.*//g')

if [ "$http_code" -eq 200 ]; then
  echo "   ✅ Success: $http_code"
  echo "   Data: $(echo $body | cut -c1-100)..."
else
  echo "   ❌ Failed: $http_code"
  echo "   Error: $body"
fi

echo ""
echo "💡 If all tests pass, the backend authentication is working correctly."
echo "   The issue is likely in the frontend session management."