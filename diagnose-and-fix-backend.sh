#!/bin/bash

echo "🔍 AI-Karen Backend Diagnosis and Fix"
echo "====================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print status
print_status() {
    local status=$1
    local message=$2
    if [ "$status" = "ok" ]; then
        echo -e "${GREEN}✅ ${message}${NC}"
    elif [ "$status" = "warn" ]; then
        echo -e "${YELLOW}⚠️  ${message}${NC}"
    else
        echo -e "${RED}❌ ${message}${NC}"
    fi
}

# Function to check if a port is listening
check_port() {
    local port=$1
    if ss -ltn | grep -q ":${port} "; then
        return 0
    else
        return 1
    fi
}

echo -e "${BLUE}1. Checking Docker Services${NC}"
echo "=========================="

# Check Docker daemon
if ! docker info > /dev/null 2>&1; then
    print_status "error" "Docker daemon is not running"
    echo "Please start Docker and try again"
    exit 1
else
    print_status "ok" "Docker daemon is running"
fi

# Check Docker Compose services
echo -e "\nDocker Compose Status:"
docker compose ps

# Check individual service status
services=("postgres" "redis" "api" "web-ui")
for service in "${services[@]}"; do
    status=$(docker compose ps --format "table {{.Service}}\t{{.State}}" | grep "^${service}" | awk '{print $2}')
    if [ "$status" = "running" ]; then
        print_status "ok" "${service} is running"
    elif [ -n "$status" ]; then
        print_status "error" "${service} is ${status}"
    else
        print_status "error" "${service} is not found"
    fi
done

echo -e "\n${BLUE}2. Checking Port Availability${NC}"
echo "============================="

# Check critical ports
ports=("5433:PostgreSQL" "6380:Redis" "8000:API" "8020:Web-UI")
for port_info in "${ports[@]}"; do
    port=$(echo $port_info | cut -d':' -f1)
    service=$(echo $port_info | cut -d':' -f2)
    
    if check_port $port; then
        print_status "ok" "Port $port ($service) is listening"
    else
        print_status "error" "Port $port ($service) is not listening"
    fi
done

echo -e "\n${BLUE}3. Testing Backend Connectivity${NC}"
echo "==============================="

# Test backend health endpoint
echo "Testing backend health endpoint..."
if curl -s -f http://localhost:8000/health > /dev/null 2>&1; then
    print_status "ok" "Backend API is responding"
    health_response=$(curl -s http://localhost:8000/health)
    echo "Response: $health_response"
else
    print_status "error" "Backend API is not responding"
    echo "This is the main issue - the backend API server is not running"
fi

echo -e "\n${BLUE}4. Checking Environment Configuration${NC}"
echo "===================================="

# Check if .env file exists
if [ -f ".env" ]; then
    print_status "ok" ".env file exists"
    
    # Check critical environment variables
    critical_vars=("POSTGRES_USER" "POSTGRES_PASSWORD" "POSTGRES_DB" "REDIS_PASSWORD")
    for var in "${critical_vars[@]}"; do
        if grep -q "^${var}=" .env; then
            print_status "ok" "${var} is set"
        else
            print_status "error" "${var} is not set"
        fi
    done
else
    print_status "error" ".env file is missing"
fi

echo -e "\n${BLUE}5. Checking Docker Logs${NC}"
echo "======================"

echo "Recent API logs:"
docker compose logs api --tail=10 2>/dev/null || echo "No API logs available"

echo -e "\nRecent PostgreSQL logs:"
docker compose logs postgres --tail=5 2>/dev/null || echo "No PostgreSQL logs available"

echo -e "\nRecent Redis logs:"
docker compose logs redis --tail=5 2>/dev/null || echo "No Redis logs available"

echo -e "\n${BLUE}6. Attempting Fixes${NC}"
echo "=================="

# Fix 1: Ensure .env file has correct values
echo "Fix 1: Checking .env configuration..."
if [ ! -f ".env" ]; then
    print_status "warn" "Creating .env file from template"
    if [ -f ".env.example" ]; then
        cp .env.example .env
        print_status "ok" "Created .env from .env.example"
    else
        print_status "error" "No .env.example found"
    fi
fi

# Fix 2: Stop and restart all services
echo -e "\nFix 2: Restarting all services..."
print_status "warn" "Stopping all services"
docker compose down

print_status "warn" "Starting all services"
docker compose up -d

# Fix 3: Wait for services to start
echo -e "\nFix 3: Waiting for services to start..."
for i in {1..60}; do
    if check_port 8000; then
        print_status "ok" "API port is now listening (after ${i} seconds)"
        break
    fi
    if [ $i -eq 60 ]; then
        print_status "error" "API port still not listening after 60 seconds"
    fi
    sleep 1
done

# Fix 4: Test connectivity again
echo -e "\nFix 4: Testing connectivity after restart..."
sleep 5

if curl -s -f http://localhost:8000/health > /dev/null 2>&1; then
    print_status "ok" "Backend API is now responding!"
    health_response=$(curl -s http://localhost:8000/health)
    echo "Response: $health_response"
else
    print_status "error" "Backend API is still not responding"
    echo "Checking detailed logs..."
    docker compose logs api --tail=20
fi

echo -e "\n${BLUE}7. Database Initialization${NC}"
echo "========================="

# Check if we need to initialize the database
if curl -s -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "Checking if database needs initialization..."
    
    # Try to create tables
    if python create_tables.py > /dev/null 2>&1; then
        print_status "ok" "Database tables created/verified"
    else
        print_status "warn" "Database table creation failed or not needed"
    fi
    
    # Try to create admin user
    echo "Checking admin user..."
    if python -c "
import sys
sys.path.append('src')
try:
    from ai_karen_engine.auth.models import User
    from ai_karen_engine.database.connection import get_db_connection
    conn = get_db_connection()
    # Simple check - if this doesn't fail, database is accessible
    print('Database accessible')
    conn.close()
except Exception as e:
    print(f'Database error: {e}')
    sys.exit(1)
" 2>/dev/null; then
        print_status "ok" "Database is accessible"
    else
        print_status "warn" "Database may need initialization"
        echo "Run: python create_admin_user.py"
    fi
fi

echo -e "\n${BLUE}8. Final Status Check${NC}"
echo "===================="

# Final comprehensive check
all_good=true

# Check Docker services
if docker compose ps --format "{{.State}}" | grep -q "running"; then
    print_status "ok" "Docker services are running"
else
    print_status "error" "Docker services are not running properly"
    all_good=false
fi

# Check API connectivity
if curl -s -f http://localhost:8000/health > /dev/null 2>&1; then
    print_status "ok" "Backend API is accessible"
else
    print_status "error" "Backend API is not accessible"
    all_good=false
fi

# Check authentication endpoint
if curl -s -X POST http://localhost:8000/api/auth/dev-login -H "Content-Type: application/json" -d '{}' | grep -q "access_token\|token" 2>/dev/null; then
    print_status "ok" "Authentication endpoint is working"
else
    print_status "warn" "Authentication endpoint may need setup"
fi

echo -e "\n${BLUE}9. Recommendations${NC}"
echo "=================="

if [ "$all_good" = true ]; then
    echo -e "${GREEN}🎉 All systems are working!${NC}"
    echo ""
    echo "Your backend should now be accessible. Try refreshing your browser."
    echo ""
    echo "Access URLs:"
    echo "• Backend API: http://localhost:8000"
    echo "• API Docs: http://localhost:8000/docs"
    echo "• Health Check: http://localhost:8000/health"
    echo "• Web UI: http://localhost:8020 (if running)"
else
    echo -e "${YELLOW}⚠️  Some issues remain. Here's what to try:${NC}"
    echo ""
    
    if ! curl -s -f http://localhost:8000/health > /dev/null 2>&1; then
        echo "Backend API is not running:"
        echo "1. Check logs: docker compose logs api"
        echo "2. Check environment: grep -E '(POSTGRES|REDIS)' .env"
        echo "3. Restart services: docker compose down && docker compose up -d"
        echo "4. Check port conflicts: ss -ltnp | grep :8000"
    fi
    
    echo ""
    echo "If problems persist:"
    echo "1. Check Docker resources (memory, disk space)"
    echo "2. Review logs: docker compose logs"
    echo "3. Try clean restart: docker compose down -v && docker compose up -d"
    echo "4. Check firewall/antivirus blocking ports"
fi

echo ""
echo "📚 Documentation:"
echo "• Environment Setup: docs/quick-fixes/ENVIRONMENT_SETUP_FIX.md"
echo "• Connection Issues: docs/quick-fixes/CONNECTION_ISSUES_CHECKLIST.md"
echo "• Comprehensive Guide: docs/troubleshooting/COMPREHENSIVE_TROUBLESHOOTING_GUIDE.md"