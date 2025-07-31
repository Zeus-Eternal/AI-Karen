#!/bin/bash
set -e

# AI Karen Database Stack Startup Script
# This script starts all database services with proper dependency management

echo "🚀 Starting AI Karen Database Stack..."
echo "===================================="

# Function to log with timestamp and color
log() {
    local level="$1"
    local message="$2"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    case "$level" in
        "INFO")
            echo -e "\033[0;32m[$timestamp] INFO: $message\033[0m"
            ;;
        "WARN")
            echo -e "\033[0;33m[$timestamp] WARN: $message\033[0m"
            ;;
        "ERROR")
            echo -e "\033[0;31m[$timestamp] ERROR: $message\033[0m"
            ;;
        "SUCCESS")
            echo -e "\033[0;36m[$timestamp] SUCCESS: $message\033[0m"
            ;;
        *)
            echo "[$timestamp] $message"
            ;;
    esac
}

# Function to check if Docker is running
check_docker() {
    if ! command -v docker &> /dev/null; then
        log "ERROR" "Docker is not installed or not in PATH"
        exit 1
    fi

    if ! docker info &> /dev/null; then
        log "ERROR" "Docker daemon is not running"
        exit 1
    fi

    log "SUCCESS" "Docker is available and running"
}

# Function to check if Docker Compose is available
check_docker_compose() {
    if command -v docker-compose &> /dev/null; then
        COMPOSE_CMD="docker-compose"
    elif docker compose version &> /dev/null; then
        COMPOSE_CMD="docker compose"
    else
        log "ERROR" "Docker Compose is not available"
        exit 1
    fi

    log "SUCCESS" "Docker Compose is available: $COMPOSE_CMD"
}

# Function to create .env file if it doesn't exist
setup_environment() {
    if [ ! -f ".env" ]; then
        if [ -f ".env.template" ]; then
            log "INFO" "Creating .env file from template..."
            cp .env.template .env
            log "WARN" "Please review and customize the .env file with your settings"
            log "WARN" "Especially change default passwords for security!"
        else
            log "ERROR" ".env.template not found. Cannot create environment file."
            exit 1
        fi
    else
        log "INFO" "Using existing .env file"
    fi
}

# Function to create necessary directories
create_directories() {
    log "INFO" "Creating necessary directories..."

    # Create data directories
    mkdir -p data/postgres
    mkdir -p data/elasticsearch
    mkdir -p data/milvus
    mkdir -p data/redis
    mkdir -p data/duckdb
    mkdir -p data/etcd
    mkdir -p data/minio

    # Create backup directories
    mkdir -p backups/postgres
    mkdir -p backups/elasticsearch
    mkdir -p backups/milvus
    mkdir -p backups/redis
    mkdir -p backups/duckdb

    # Create log directories
    mkdir -p logs

    log "SUCCESS" "Directories created"
}

# Function to pull latest images
pull_images() {
    local pull_images="${1:-true}"

    if [ "$pull_images" = "true" ]; then
        log "INFO" "Pulling latest Docker images..."
        $COMPOSE_CMD pull
        log "SUCCESS" "Images pulled successfully"
    else
        log "INFO" "Skipping image pull (using existing images)"
    fi
}

# Function to start services in proper order
start_services() {
    local mode="${1:-detached}"

    log "INFO" "Starting database services..."

    if [ "$mode" = "detached" ]; then
        log "INFO" "Starting in detached mode..."
        $COMPOSE_CMD up -d
    else
        log "INFO" "Starting in foreground mode..."
        $COMPOSE_CMD up
    fi
}

# Function to wait for services to be healthy
wait_for_health() {
    log "INFO" "Waiting for services to become healthy..."

    local max_attempts=60
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        log "INFO" "Health check attempt $attempt/$max_attempts..."

        # Check if all services are healthy
        local unhealthy_services=$($COMPOSE_CMD ps --format json | jq -r '.[] | select(.Health != "healthy" and .Health != "") | .Service' 2>/dev/null || echo "")

        if [ -z "$unhealthy_services" ]; then
            log "SUCCESS" "All services are healthy!"
            return 0
        fi

        log "INFO" "Waiting for services to become healthy: $unhealthy_services"
        sleep 10
        attempt=$((attempt + 1))
    done

    log "WARN" "Some services may not be fully healthy yet"
    log "INFO" "You can check service status with: $COMPOSE_CMD ps"
    return 1
}

# Function to run initialization
run_initialization() {
    local skip_init="${1:-false}"

    if [ "$skip_init" = "true" ]; then
        log "INFO" "Skipping initialization (--skip-init flag provided)"
        return 0
    fi

    log "INFO" "Running database initialization..."

    # Check if initialization container exists and run it
    if $COMPOSE_CMD ps db-init &> /dev/null; then
        log "INFO" "Running initialization container..."
        $COMPOSE_CMD up db-init

        # Check if initialization was successful
        if $COMPOSE_CMD logs db-init | grep -q "AI Karen Database Initialization Complete"; then
            log "SUCCESS" "Database initialization completed successfully!"
        else
            log "WARN" "Initialization may have encountered issues. Check logs with: $COMPOSE_CMD logs db-init"
        fi
    else
        log "INFO" "No initialization container found, skipping..."
    fi
}

# Function to show service status
show_status() {
    log "INFO" "Database service status:"
    echo ""

    $COMPOSE_CMD ps

    echo ""
    log "INFO" "Service health summary:"

    # Show health status for each service
    services=("postgres" "elasticsearch" "milvus" "redis")

    for service in "${services[@]}"; do
        if $COMPOSE_CMD ps "$service" &> /dev/null; then
            local status=$($COMPOSE_CMD ps "$service" --format "table {{.Status}}" | tail -n +2)
            if echo "$status" | grep -q "healthy"; then
                log "SUCCESS" "$service: healthy"
            elif echo "$status" | grep -q "Up"; then
                log "INFO" "$service: running (health check pending)"
            else
                log "WARN" "$service: $status"
            fi
        else
            log "ERROR" "$service: not found"
        fi
    done
}

# Function to show usage information
show_usage() {
    echo "AI Karen Database Stack Startup Script"
    echo ""
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  --no-pull          Don't pull latest Docker images"
    echo "  --skip-init        Skip database initialization"
    echo "  --foreground       Run in foreground mode (don't detach)"
    echo "  --status-only      Show service status and exit"
    echo "  --help             Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                 # Start all services (default)"
    echo "  $0 --no-pull       # Start without pulling latest images"
    echo "  $0 --foreground    # Start in foreground mode"
    echo "  $0 --status-only   # Just show current status"
}

# Main function
main() {
    local pull_images="true"
    local skip_init="false"
    local mode="detached"
    local status_only="false"

    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --no-pull)
                pull_images="false"
                shift
                ;;
            --skip-init)
                skip_init="true"
                shift
                ;;
            --foreground)
                mode="foreground"
                shift
                ;;
            --status-only)
                status_only="true"
                shift
                ;;
            --help)
                show_usage
                exit 0
                ;;
            *)
                log "ERROR" "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done

    # Show status only if requested
    if [ "$status_only" = "true" ]; then
        show_status
        exit 0
    fi

    # Pre-flight checks
    check_docker
    check_docker_compose
    setup_environment
    create_directories

    # Start the stack
    pull_images "$pull_images"
    start_services "$mode"

    # If running in detached mode, wait for health and run initialization
    if [ "$mode" = "detached" ]; then
        wait_for_health
        run_initialization "$skip_init"
        show_status

        echo ""
        log "SUCCESS" "🎉 AI Karen Database Stack is running!"
        echo ""
        echo "Next steps:"
        echo "  - Check service status: $COMPOSE_CMD ps"
        echo "  - View logs: $COMPOSE_CMD logs [service_name]"
        echo "  - Stop services: ./scripts/stop.sh"
        echo "  - Access services:"
        echo "    - PostgreSQL: localhost:${POSTGRES_PORT:-5433}"
        echo "    - Elasticsearch: http://localhost:9200"
        echo "    - Milvus: localhost:19530"
        echo "    - Redis: localhost:6379"
        echo "    - MinIO Console: http://localhost:9001"
        echo ""
    fi
}

# Change to script directory
cd "$(dirname "$0")/.."

# Run main function with all arguments
main "$@"
