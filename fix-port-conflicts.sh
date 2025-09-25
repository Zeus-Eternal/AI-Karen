#!/bin/bash

echo "🔧 AI-Karen Port Conflict Fix"
echo "============================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${RED}❌ Port 5433 is already in use (PostgreSQL conflict)${NC}"
echo ""

echo -e "${BLUE}1. Identifying what's using port 5433...${NC}"
echo "================================================"

# Check what's using port 5433
if command -v ss >/dev/null 2>&1; then
    echo "Processes using port 5433:"
    ss -ltnp | grep ":5433 " || echo "No processes found with ss"
elif command -v lsof >/dev/null 2>&1; then
    echo "Processes using port 5433:"
    lsof -i :5433 || echo "No processes found with lsof"
else
    echo "Neither ss nor lsof available, using netstat..."
    netstat -tlnp | grep ":5433 " || echo "No processes found with netstat"
fi

echo ""
echo -e "${BLUE}2. Checking for existing PostgreSQL instances...${NC}"
echo "=============================================="

# Check for running PostgreSQL processes
if pgrep -f postgres > /dev/null; then
    echo "Found running PostgreSQL processes:"
    pgrep -f postgres | while read pid; do
        echo "PID $pid: $(ps -p $pid -o cmd --no-headers)"
    done
else
    echo "No PostgreSQL processes found"
fi

# Check for Docker containers using PostgreSQL
echo ""
echo "Checking for Docker containers with PostgreSQL..."
docker ps --format "table {{.Names}}\t{{.Ports}}" | grep -E "(postgres|5432|5433)" || echo "No PostgreSQL Docker containers found"

echo ""
echo -e "${BLUE}3. Applying fixes...${NC}"
echo "=================="

# Solution 1: Stop any existing AI-Karen containers
echo "Fix 1: Stopping any existing AI-Karen containers..."
docker compose down 2>/dev/null || echo "No existing containers to stop"

# Solution 2: Kill processes using port 5433 (if safe to do so)
echo ""
echo "Fix 2: Checking if we can free port 5433..."

# Get the PID using port 5433
port_pid=$(ss -ltnp 2>/dev/null | grep ":5433 " | grep -o 'pid=[0-9]*' | cut -d'=' -f2 | head -1)

if [ -n "$port_pid" ]; then
    # Get process info
    process_info=$(ps -p $port_pid -o comm,cmd --no-headers 2>/dev/null)
    echo "Process using port 5433: PID $port_pid - $process_info"
    
    # Check if it's a Docker container or system PostgreSQL
    if echo "$process_info" | grep -q "docker\|containerd"; then
        echo "This appears to be a Docker container. Attempting to stop it..."
        # Try to find and stop the container
        container_id=$(docker ps -q --filter "publish=5433")
        if [ -n "$container_id" ]; then
            echo "Stopping Docker container: $container_id"
            docker stop $container_id
        fi
    elif echo "$process_info" | grep -q "postgres"; then
        echo -e "${YELLOW}⚠️  This appears to be a system PostgreSQL instance.${NC}"
        echo "Options:"
        echo "1. Stop system PostgreSQL: sudo systemctl stop postgresql"
        echo "2. Change AI-Karen PostgreSQL port (recommended)"
        echo ""
        echo "Choosing option 2: Changing AI-Karen PostgreSQL port..."
        
        # Change the port in docker-compose.yml or .env
        if grep -q "POSTGRES_PORT" .env; then
            sed -i 's/POSTGRES_PORT=5433/POSTGRES_PORT=5434/' .env
            echo "Changed POSTGRES_PORT to 5434 in .env"
        else
            echo "POSTGRES_PORT=5434" >> .env
            echo "Added POSTGRES_PORT=5434 to .env"
        fi
    else
        echo -e "${YELLOW}⚠️  Unknown process using port 5433. You may need to manually stop it.${NC}"
        echo "Process: $process_info"
        echo "To kill it: sudo kill $port_pid"
    fi
else
    echo "Port 5433 appears to be free now"
fi

# Solution 3: Use alternative ports
echo ""
echo "Fix 3: Configuring alternative ports..."

# Update .env with alternative ports to avoid conflicts
if [ -f .env ]; then
    # Backup .env
    cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
    
    # Set alternative ports
    if ! grep -q "POSTGRES_PORT" .env; then
        echo "POSTGRES_PORT=5434" >> .env
    else
        sed -i 's/POSTGRES_PORT=.*/POSTGRES_PORT=5434/' .env
    fi
    
    if ! grep -q "REDIS_PORT" .env; then
        echo "REDIS_PORT=6381" >> .env
    else
        sed -i 's/REDIS_PORT=.*/REDIS_PORT=6381/' .env
    fi
    
    echo "Updated ports in .env:"
    grep -E "(POSTGRES_PORT|REDIS_PORT)" .env
else
    echo "Creating .env with alternative ports..."
    cat >> .env << EOF
POSTGRES_PORT=5434
REDIS_PORT=6381
EOF
fi

echo ""
echo -e "${BLUE}4. Starting services with new configuration...${NC}"
echo "============================================="

# Start services
echo "Starting AI-Karen services..."
docker compose up -d

echo ""
echo "Waiting for services to start..."
sleep 10

echo ""
echo -e "${BLUE}5. Verifying services...${NC}"
echo "======================"

# Check container status
echo "Container status:"
docker compose ps

echo ""
echo "Port status:"
echo "PostgreSQL (should be on 5434): $(ss -ltn | grep ":5434 " && echo "✅ Running" || echo "❌ Not running")"
echo "Redis (should be on 6381): $(ss -ltn | grep ":6381 " && echo "✅ Running" || echo "❌ Not running")"
echo "API (should be on 8000): $(ss -ltn | grep ":8000 " && echo "✅ Running" || echo "❌ Not running")"

echo ""
echo -e "${BLUE}6. Testing connectivity...${NC}"
echo "========================"

# Wait a bit more for services to be fully ready
sleep 15

# Test API health
if curl -s -f http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Backend API is responding!${NC}"
    health_response=$(curl -s http://localhost:8000/health)
    echo "Health response: $health_response"
else
    echo -e "${RED}❌ Backend API is not responding yet${NC}"
    echo "Checking API logs..."
    docker compose logs api --tail=10
fi

# Test database connectivity
echo ""
echo "Testing database connectivity..."
if docker compose exec -T postgres pg_isready -U karen_user -d ai_karen > /dev/null 2>&1; then
    echo -e "${GREEN}✅ PostgreSQL is ready${NC}"
else
    echo -e "${YELLOW}⚠️  PostgreSQL may still be starting up${NC}"
fi

echo ""
echo -e "${BLUE}7. Final recommendations...${NC}"
echo "=========================="

if curl -s -f http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}🎉 Success! AI-Karen is now running with alternative ports.${NC}"
    echo ""
    echo "Updated configuration:"
    echo "• PostgreSQL: localhost:5434 (was 5433)"
    echo "• Redis: localhost:6381 (was 6380)"
    echo "• API: localhost:8000"
    echo "• Web UI: localhost:8020"
    echo ""
    echo "Next steps:"
    echo "1. Initialize database: python create_tables.py"
    echo "2. Create admin user: python create_admin_user.py"
    echo "3. Access web UI: http://localhost:8020"
else
    echo -e "${YELLOW}⚠️  Services are starting but may need more time.${NC}"
    echo ""
    echo "Wait 30 seconds and try:"
    echo "• Check status: docker compose ps"
    echo "• Check logs: docker compose logs api"
    echo "• Test health: curl http://localhost:8000/health"
    echo ""
    echo "If problems persist:"
    echo "1. Check what's still using ports: ss -ltn | grep -E ':(5433|5434|8000)'"
    echo "2. Try different ports in .env file"
    echo "3. Restart Docker: sudo systemctl restart docker"
fi

echo ""
echo "📚 The .env file has been updated with new ports to avoid conflicts."
echo "📚 A backup of your original .env was created."