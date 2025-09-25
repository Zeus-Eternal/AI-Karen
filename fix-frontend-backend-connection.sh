#!/bin/bash

echo "🔧 AI-Karen Frontend-Backend Connection Fix"
echo "==========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get the current frontend IP from the error logs
FRONTEND_IP="10.96.136.74"
FRONTEND_PORT="8020"
BACKEND_PORT="8000"

echo "🌐 Frontend: http://${FRONTEND_IP}:${FRONTEND_PORT}"
echo "🔧 Backend:  http://localhost:${BACKEND_PORT}"

# Function to check if a service is running
check_service() {
    local service=$1
    local port=$2
    if curl -s -f "http://localhost:${port}/health" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ ${service} is running on port ${port}${NC}"
        return 0
    else
        echo -e "${RED}❌ ${service} is not running on port ${port}${NC}"
        return 1
    fi
}

# 1. Check current service status
echo -e "\n1. Checking service status..."
docker compose ps

# 2. Check if backend is accessible
echo -e "\n2. Testing backend connectivity..."
if check_service "Backend API" "$BACKEND_PORT"; then
    BACKEND_RUNNING=true
else
    BACKEND_RUNNING=false
    echo -e "${YELLOW}⚠️  Backend is not accessible${NC}"
fi

# 3. Update environment configuration
echo -e "\n3. Updating environment configuration..."

# Backup current .env
cp .env .env.backup.$(date +%Y%m%d_%H%M%S)

# Update CORS origins
if grep -q "KARI_CORS_ORIGINS" .env; then
    if grep -q "${FRONTEND_IP}" .env; then
        echo -e "${GREEN}✅ Frontend IP already in CORS origins${NC}"
    else
        # Add frontend IP to existing CORS origins
        sed -i "s|KARI_CORS_ORIGINS=\(.*\)|KARI_CORS_ORIGINS=\1,http://${FRONTEND_IP}:${FRONTEND_PORT},http://${FRONTEND_IP}:3000|" .env
        echo -e "${GREEN}✅ Added frontend IP to CORS origins${NC}"
    fi
else
    echo "KARI_CORS_ORIGINS=http://localhost:3000,http://localhost:8020,http://127.0.0.1:3000,http://127.0.0.1:8020,http://${FRONTEND_IP}:${FRONTEND_PORT},http://${FRONTEND_IP}:3000" >> .env
    echo -e "${GREEN}✅ Added CORS origins to .env${NC}"
fi

# Ensure dev login is enabled
if grep -q "AUTH_ALLOW_DEV_LOGIN" .env; then
    sed -i 's/AUTH_ALLOW_DEV_LOGIN=.*/AUTH_ALLOW_DEV_LOGIN=true/' .env
else
    echo "AUTH_ALLOW_DEV_LOGIN=true" >> .env
fi

# Ensure dev mode is enabled
if grep -q "AUTH_DEV_MODE" .env; then
    sed -i 's/AUTH_DEV_MODE=.*/AUTH_DEV_MODE=true/' .env
else
    echo "AUTH_DEV_MODE=true" >> .env
fi

# Ensure other CORS settings
grep -q "KARI_CORS_METHODS" .env || echo "KARI_CORS_METHODS=*" >> .env
grep -q "KARI_CORS_HEADERS" .env || echo "KARI_CORS_HEADERS=*" >> .env
grep -q "KARI_CORS_CREDENTIALS" .env || echo "KARI_CORS_CREDENTIALS=true" >> .env

echo -e "\n📋 Current configuration:"
echo "CORS Origins: $(grep KARI_CORS_ORIGINS .env | cut -d'=' -f2)"
echo "Dev Login: $(grep AUTH_ALLOW_DEV_LOGIN .env | cut -d'=' -f2)"
echo "Dev Mode: $(grep AUTH_DEV_MODE .env | cut -d'=' -f2)"

# 4. Start/restart services
echo -e "\n4. Starting/restarting services..."

if [ "$BACKEND_RUNNING" = false ]; then
    echo "Starting all services..."
    docker compose up -d
else
    echo "Restarting API service to apply CORS changes..."
    docker compose restart api
fi

# 5. Wait for services to be ready
echo -e "\n5. Waiting for services to be ready..."
for i in {1..30}; do
    if check_service "Backend API" "$BACKEND_PORT" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Backend is ready after ${i} seconds${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}❌ Backend failed to start after 30 seconds${NC}"
        echo "Checking logs..."
        docker compose logs api --tail=20
        exit 1
    fi
    sleep 1
done

# 6. Test CORS configuration
echo -e "\n6. Testing CORS configuration..."

# Test OPTIONS preflight request
echo "Testing CORS preflight..."
CORS_RESPONSE=$(curl -s -I \
    -H "Origin: http://${FRONTEND_IP}:${FRONTEND_PORT}" \
    -H "Access-Control-Request-Method: POST" \
    -H "Access-Control-Request-Headers: Content-Type,Authorization" \
    -X OPTIONS \
    "http://localhost:${BACKEND_PORT}/api/copilot/assist" 2>/dev/null)

if echo "$CORS_RESPONSE" | grep -q "Access-Control-Allow-Origin"; then
    echo -e "${GREEN}✅ CORS preflight successful${NC}"
    echo "$CORS_RESPONSE" | grep "Access-Control" | head -3
else
    echo -e "${RED}❌ CORS preflight failed${NC}"
    echo "Response headers:"
    echo "$CORS_RESPONSE" | head -10
fi

# 7. Test API endpoints
echo -e "\n7. Testing API endpoints..."

# Test health endpoint
echo "Testing health endpoint..."
HEALTH_RESPONSE=$(curl -s -H "Origin: http://${FRONTEND_IP}:${FRONTEND_PORT}" \
    "http://localhost:${BACKEND_PORT}/health" 2>/dev/null)

if echo "$HEALTH_RESPONSE" | grep -q "healthy\|status"; then
    echo -e "${GREEN}✅ Health endpoint working${NC}"
    echo "Response: $HEALTH_RESPONSE"
else
    echo -e "${RED}❌ Health endpoint failed${NC}"
    echo "Response: $HEALTH_RESPONSE"
fi

# Test dev-login endpoint
echo -e "\nTesting dev-login endpoint..."
AUTH_RESPONSE=$(curl -s -X POST \
    -H "Origin: http://${FRONTEND_IP}:${FRONTEND_PORT}" \
    -H "Content-Type: application/json" \
    "http://localhost:${BACKEND_PORT}/api/auth/dev-login" \
    -d '{}' 2>/dev/null)

if echo "$AUTH_RESPONSE" | grep -q "access_token\|token"; then
    echo -e "${GREEN}✅ Dev-login endpoint working${NC}"
    echo "Token received successfully"
else
    echo -e "${RED}❌ Dev-login endpoint failed${NC}"
    echo "Response: $AUTH_RESPONSE"
fi

# Test copilot assist endpoint
echo -e "\nTesting copilot assist endpoint..."
COPILOT_RESPONSE=$(curl -s -X POST \
    -H "Origin: http://${FRONTEND_IP}:${FRONTEND_PORT}" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer test-token" \
    "http://localhost:${BACKEND_PORT}/api/copilot/assist" \
    -d '{"message": "test"}' 2>/dev/null)

if echo "$COPILOT_RESPONSE" | grep -q -v "error\|Error"; then
    echo -e "${GREEN}✅ Copilot assist endpoint accessible${NC}"
else
    echo -e "${YELLOW}⚠️  Copilot assist endpoint may need authentication${NC}"
    echo "Response: $COPILOT_RESPONSE"
fi

# 8. Check Next.js API routes
echo -e "\n8. Checking Next.js API routes..."

# Check if Next.js auth routes exist
if [ -f "ui_launchers/web_ui/src/app/api/auth/login-simple/route.ts" ]; then
    echo -e "${GREEN}✅ Next.js login-simple route exists${NC}"
else
    echo -e "${RED}❌ Next.js login-simple route missing${NC}"
fi

if [ -f "ui_launchers/web_ui/src/app/api/auth/validate-session/route.ts" ]; then
    echo -e "${GREEN}✅ Next.js validate-session route exists${NC}"
else
    echo -e "${RED}❌ Next.js validate-session route missing${NC}"
fi

# 9. Final status and recommendations
echo -e "\n9. Final Status and Recommendations"
echo "=================================="

# Check if CORS is working
if echo "$CORS_RESPONSE" | grep -q "Access-Control-Allow-Origin"; then
    echo -e "${GREEN}✅ CORS Configuration: Working${NC}"
    CORS_OK=true
else
    echo -e "${RED}❌ CORS Configuration: Failed${NC}"
    CORS_OK=false
fi

# Check if backend is accessible
if echo "$HEALTH_RESPONSE" | grep -q "healthy\|status"; then
    echo -e "${GREEN}✅ Backend API: Accessible${NC}"
    BACKEND_OK=true
else
    echo -e "${RED}❌ Backend API: Not accessible${NC}"
    BACKEND_OK=false
fi

# Check if auth is working
if echo "$AUTH_RESPONSE" | grep -q "access_token\|token"; then
    echo -e "${GREEN}✅ Authentication: Working${NC}"
    AUTH_OK=true
else
    echo -e "${RED}❌ Authentication: Failed${NC}"
    AUTH_OK=false
fi

# Overall status
if [ "$CORS_OK" = true ] && [ "$BACKEND_OK" = true ] && [ "$AUTH_OK" = true ]; then
    echo -e "\n${GREEN}🎉 All systems working! Frontend should now connect successfully.${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Refresh your browser (Ctrl+Shift+R or Cmd+Shift+R)"
    echo "2. Clear browser cache if needed"
    echo "3. Try the application again"
else
    echo -e "\n${YELLOW}⚠️  Some issues remain. Additional troubleshooting needed.${NC}"
    echo ""
    echo "Troubleshooting steps:"
    
    if [ "$BACKEND_OK" = false ]; then
        echo "• Backend not accessible:"
        echo "  - Check: docker compose ps"
        echo "  - Check logs: docker compose logs api"
        echo "  - Restart: docker compose restart api"
    fi
    
    if [ "$CORS_OK" = false ]; then
        echo "• CORS not working:"
        echo "  - Verify .env CORS settings: grep KARI_CORS .env"
        echo "  - Restart API: docker compose restart api"
        echo "  - Check API logs: docker compose logs api | grep -i cors"
    fi
    
    if [ "$AUTH_OK" = false ]; then
        echo "• Authentication not working:"
        echo "  - Check dev mode: grep AUTH_DEV_MODE .env"
        echo "  - Check dev login: grep AUTH_ALLOW_DEV_LOGIN .env"
        echo "  - Initialize database: python create_tables.py"
    fi
fi

echo ""
echo "📚 Documentation:"
echo "• CORS Issues: docs/troubleshooting/CORS_ISSUES_FIX.md"
echo "• Connection Issues: docs/quick-fixes/CONNECTION_ISSUES_CHECKLIST.md"
echo "• Environment Setup: docs/quick-fixes/ENVIRONMENT_SETUP_FIX.md"