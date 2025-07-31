#!/bin/bash
set -e

# AI Karen Database Stack Restart Script
# This script restarts all database services

echo "🔄 Restarting AI Karen Database Stack..."
echo "======================================"

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

# Function to show usage information
show_usage() {
    echo "AI Karen Database Stack Restart Script"
    echo ""
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  --hard            Hard restart (stop and start, don't use docker-compose restart)"
    echo "  --pull            Pull latest images before restarting"
    echo "  --service <name>  Restart only specific service"
    echo "  --timeout <sec>   Timeout for stop operation (default: 30)"
    echo "  --skip-init       Skip database initialization after restart"
    echo "  --help            Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                           # Restart all services"
    echo "  $0 --hard                    # Hard restart (stop then start)"
    echo "  $0 --service postgres        # Restart only PostgreSQL"
    echo "  $0 --pull                    # Pull images and restart"
    echo "  $0 --hard --pull             # Hard restart with image pull"
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

# Function to restart services using docker-compose restart
soft_restart() {
    local service="$1"

    if [ -n "$service" ]; then
        log "INFO" "Soft restarting service: $service"
        $COMPOSE_CMD restart "$service"
    else
        log "INFO" "Soft restarting all services..."
        $COMPOSE_CMD restart
    fi

    log "SUCCESS" "Services restarted"
}

# Function to hard restart (stop then start)
hard_restart() {
    local service="$1"
    local timeout="$2"
    local pull_images="$3"
    local skip_init="$4"

    log "INFO" "Performing hard restart..."

    # Stop services
    if [ -n "$service" ]; then
        log "INFO" "Stopping service: $service"
        $COMPOSE_CMD stop --timeout "$timeout" "$service"
    else
        log "INFO" "Stopping all services..."
        $COMPOSE_CMD stop --timeout "$timeout"
    fi

    # Pull images if requested
    if [ "$pull_images" = "true" ]; then
        log "INFO" "Pulling latest images..."
        if [ -n "$service" ]; then
            $COMPOSE_CMD pull "$service"
        else
            $COMPOSE_CMD pull
        fi
    fi

    # Start services
    if [ -n "$service" ]; then
        log "INFO" "Starting service: $service"
        $COMPOSE_CMD up -d "$service"
    else
        log "INFO" "Starting all services..."
        $COMPOSE_CMD up -d
    fi

    # Wait for services to be ready
    log "INFO" "Waiting for services to be ready..."
    sleep 10

    # Run initialization if not skipped and restarting all services
    if [ "$skip_init" = "false" ] && [ -z "$service" ]; then
        if $COMPOSE_CMD ps db-init &> /dev/null; then
            log "INFO" "Running initialization..."
            $COMPOSE_CMD up db-init
        fi
    fi

    log "SUCCESS" "Hard restart completed"
}

# Function to show service status
show_status() {
    local service="$1"

    log "INFO" "Service status:"
    echo ""

    if [ -n "$service" ]; then
        $COMPOSE_CMD ps "$service"
    else
        $COMPOSE_CMD ps
    fi

    echo ""
}

# Function to wait for service health
wait_for_health() {
    local service="$1"
    local max_attempts=30
    local attempt=1

    log "INFO" "Waiting for service health..."

    while [ $attempt -le $max_attempts ]; do
        log "INFO" "Health check attempt $attempt/$max_attempts..."

        if [ -n "$service" ]; then
            # Check specific service
            local status=$($COMPOSE_CMD ps "$service" --format "table {{.Status}}" | tail -n +2)
            if echo "$status" | grep -q "healthy\\|Up"; then
                log "SUCCESS" "Service $service is ready!"
                return 0
            fi
        else
            # Check all services
            local unhealthy_services=$($COMPOSE_CMD ps --format json | jq -r '.[] | select(.Health != "healthy" and .Health != "" and .State == "running") | .Service' 2>/dev/null || echo "")

            if [ -z "$unhealthy_services" ]; then
                log "SUCCESS" "All services are ready!"
                return 0
            fi

            log "INFO" "Waiting for services: $unhealthy_services"
        fi

        sleep 5
        attempt=$((attempt + 1))
    done

    log "WARN" "Services may not be fully ready yet"
    return 1
}

# Main function
main() {
    local hard_restart_flag="false"
    local pull_images="false"
    local service=""
    local timeout="30"
    local skip_init="false"

    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --hard)
                hard_restart_flag="true"
                shift
                ;;
            --pull)
                pull_images="true"
                shift
                ;;
            --service)
                service="$2"
                shift 2
                ;;
            --timeout)
                timeout="$2"
                shift 2
                ;;
            --skip-init)
                skip_init="true"
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

    # Validate timeout
    if ! [[ "$timeout" =~ ^[0-9]+$ ]]; then
        log "ERROR" "Timeout must be a number"
        exit 1
    fi

    # Check Docker Compose availability
    check_docker_compose

    # Show current status
    log "INFO" "Current status before restart:"
    show_status "$service"

    # Perform restart
    if [ "$hard_restart_flag" = "true" ]; then
        hard_restart "$service" "$timeout" "$pull_images" "$skip_init"
    else
        # For soft restart, pull images first if requested
        if [ "$pull_images" = "true" ]; then
            log "INFO" "Pulling latest images..."
            if [ -n "$service" ]; then
                $COMPOSE_CMD pull "$service"
            else
                $COMPOSE_CMD pull
            fi
        fi

        soft_restart "$service"
    fi

    # Wait for services to be healthy
    wait_for_health "$service"

    # Show final status
    echo ""
    log "INFO" "Final status after restart:"
    show_status "$service"

    echo ""
    log "SUCCESS" "🎉 AI Karen Database Stack restart completed!"

    if [ -z "$service" ]; then
        echo ""
        echo "Service URLs:"
        echo "  - PostgreSQL: localhost:${POSTGRES_PORT:-5433}"
        echo "  - Elasticsearch: http://localhost:9200"
        echo "  - Milvus: localhost:19530"
        echo "  - Redis: localhost:6379"
        echo "  - MinIO Console: http://localhost:9001"
    fi
}

# Change to script directory
cd "$(dirname "$0")/.."

# Run main function with all arguments
main "$@"
