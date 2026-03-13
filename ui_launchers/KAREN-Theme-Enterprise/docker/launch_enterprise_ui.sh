#!/bin/bash
# Launch script for KAREN-Theme-Enterprise UI with full AI-Karen backend
# This script launches the Enterprise Theme UI alongside the complete backend stack

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   KAREN AI - Enterprise Theme UI Launcher                 ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${RED}Error: .env file not found!${NC}"
    echo -e "${YELLOW}Please copy .env.example to .env and configure it:${NC}"
    echo "  cp .env.example .env"
    exit 1
fi

# Check if docker-compose.yml exists
if [ ! -f docker-compose.yml ]; then
    echo -e "${RED}Error: docker-compose.yml not found!${NC}"
    echo -e "${YELLOW}Please run this script from the AI-Karen project root.${NC}"
    exit 1
fi

# Check if docker-compose.enterprise.yml exists
if [ ! -f docker-compose.enterprise.yml ]; then
    echo -e "${RED}Error: docker-compose.enterprise.yml not found!${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Configuration files found${NC}"

# Parse command line arguments
BUILD=false
DETACH=false
SERVICES=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -b|--build)
            BUILD=true
            shift
            ;;
        -d|--detach)
            DETACH=true
            shift
            ;;
        -s|--services)
            SERVICES="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -b, --build       Build images before starting"
            echo "  -d, --detach      Run in background (detached mode)"
            echo "  -s, --services    Specify specific services (e.g., 'postgres,redis,api,enterprise-ui')"
            echo "  -h, --help        Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                           # Start all services in foreground"
            echo "  $0 -d                        # Start all services in background"
            echo "  $0 -d -b                     # Build and start in background"
            echo "  $0 -s 'postgres redis api'   # Start only specific services"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use -h or --help for usage information"
            exit 1
            ;;
    esac
done

# Build docker compose command
COMPOSE_FILES="-f docker-compose.yml -f docker-compose.enterprise.yml"

if [ "$BUILD" = true ]; then
    echo -e "${YELLOW}Building Docker images...${NC}"
    docker compose $COMPOSE_FILES build
    echo -e "${GREEN}✓ Build complete${NC}"
fi

echo -e "${YELLOW}Starting services...${NC}"
echo ""

# Start services
if [ -z "$SERVICES" ]; then
    # Start all services
    if [ "$DETACH" = true ]; then
        docker compose $COMPOSE_FILES up -d
    else
        docker compose $COMPOSE_FILES up
    fi
else
    # Start specific services
    if [ "$DETACH" = true ]; then
        docker compose $COMPOSE_FILES up -d $SERVICES
    else
        docker compose $COMPOSE_FILES up $SERVICES
    fi
fi

# If detached, show service status
if [ "$DETACH" = true ]; then
    echo ""
    echo -e "${GREEN}✓ Services started successfully!${NC}"
    echo ""
    echo -e "${BLUE}Service Status:${NC}"
    docker compose $COMPOSE_FILES ps
    echo ""
    echo -e "${BLUE}Access Points:${NC}"
    echo "  • Enterprise UI:     http://localhost:3000"
    echo "  • Backend API:       http://localhost:8000"
    echo "  • API Docs:          http://localhost:8000/docs"
    echo "  • Grafana:           http://localhost:3001"
    echo "  • Prometheus:        http://localhost:9090"
    echo ""
    echo -e "${YELLOW}To view logs:${NC}"
    echo "  docker compose $COMPOSE_FILES logs -f enterprise-ui"
    echo ""
    echo -e "${YELLOW}To stop services:${NC}"
    echo "  docker compose $COMPOSE_FILES down"
fi
