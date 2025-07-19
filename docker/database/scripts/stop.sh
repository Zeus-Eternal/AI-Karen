#!/bin/bash
set -e

# AI Karen Database Stack Stop Script
# This script stops all database services gracefully

echo "🛑 Stopping AI Karen Database Stack..."
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

# Function to stop services gracefully
stop_services() {
    local remove_volumes="${1:-false}"
    local timeout="${2:-30}"
    
    log "INFO" "Stopping database services (timeout: ${timeout}s)..."
    
    # Stop services with timeout
    if $COMPOSE_CMD stop --timeout "$timeout"; then
        log "SUCCESS" "Services stopped successfully"
    else
        log "WARN" "Some services may not have stopped gracefully"
    fi
    
    # Remove containers
    log "INFO" "Removing containers..."
    if $COMPOSE_CMD down; then
        log "SUCCESS" "Containers removed"
    else
        log "WARN" "Some containers may not have been removed"
    fi
    
    # Remove volumes if requested
    if [ "$remove_volumes" = "true" ]; then
        log "WARN" "Removing volumes (this will delete all data)..."
        if $COMPOSE_CMD down -v; then
            log "SUCCESS" "Volumes removed"
        else
            log "ERROR" "Failed to remove volumes"
        fi
    fi
}

# Function to force stop services
force_stop() {
    log "WARN" "Force stopping all services..."
    
    # Kill all containers
    $COMPOSE_CMD kill
    
    # Remove containers
    $COMPOSE_CMD down --remove-orphans
    
    log "SUCCESS" "Services force stopped"
}

# Function to show current status
show_status() {
    log "INFO" "Current service status:"
    echo ""
    
    if $COMPOSE_CMD ps | grep -q "Up"; then
        $COMPOSE_CMD ps
        echo ""
        log "INFO" "Some services are still running"
        return 1
    else
        log "SUCCESS" "All services are stopped"
        return 0
    fi
}

# Function to cleanup orphaned containers and networks
cleanup() {
    log "INFO" "Cleaning up orphaned containers and networks..."
    
    # Remove orphaned containers
    $COMPOSE_CMD down --remove-orphans
    
    # Prune unused networks (be careful with this)
    if docker network ls | grep -q "ai-karen"; then
        log "INFO" "Removing AI Karen networks..."
        docker network ls --format "{{.Name}}" | grep "ai-karen" | xargs -r docker network rm 2>/dev/null || true
    fi
    
    log "SUCCESS" "Cleanup completed"
}

# Function to show usage information
show_usage() {
    echo "AI Karen Database Stack Stop Script"
    echo ""
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  --remove-volumes   Remove all data volumes (WARNING: This deletes all data!)"
    echo "  --force           Force stop services (kill containers)"
    echo "  --timeout <sec>   Timeout for graceful shutdown (default: 30)"
    echo "  --cleanup         Clean up orphaned containers and networks"
    echo "  --status          Show current service status"
    echo "  --help            Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                        # Stop all services gracefully"
    echo "  $0 --force                # Force stop all services"
    echo "  $0 --remove-volumes       # Stop and remove all data"
    echo "  $0 --timeout 60           # Stop with 60 second timeout"
    echo "  $0 --cleanup              # Stop and cleanup orphaned resources"
}

# Function to confirm destructive actions
confirm_action() {
    local action="$1"
    
    echo ""
    log "WARN" "You are about to: $action"
    log "WARN" "This action cannot be undone!"
    echo ""
    read -p "Are you sure you want to continue? (yes/no): " -r
    echo ""
    
    if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        log "INFO" "Operation cancelled by user"
        exit 0
    fi
}

# Main function
main() {
    local remove_volumes="false"
    local force_stop_flag="false"
    local timeout="30"
    local cleanup_flag="false"
    local status_only="false"
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --remove-volumes)
                remove_volumes="true"
                shift
                ;;
            --force)
                force_stop_flag="true"
                shift
                ;;
            --timeout)
                timeout="$2"
                shift 2
                ;;
            --cleanup)
                cleanup_flag="true"
                shift
                ;;
            --status)
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
    
    # Validate timeout
    if ! [[ "$timeout" =~ ^[0-9]+$ ]]; then
        log "ERROR" "Timeout must be a number"
        exit 1
    fi
    
    # Check Docker Compose availability
    check_docker_compose
    
    # Show status only if requested
    if [ "$status_only" = "true" ]; then
        show_status
        exit $?
    fi
    
    # Confirm destructive actions
    if [ "$remove_volumes" = "true" ]; then
        confirm_action "remove all data volumes"
    fi
    
    if [ "$force_stop_flag" = "true" ]; then
        confirm_action "force stop all services"
    fi
    
    # Stop services
    if [ "$force_stop_flag" = "true" ]; then
        force_stop
    else
        stop_services "$remove_volumes" "$timeout"
    fi
    
    # Cleanup if requested
    if [ "$cleanup_flag" = "true" ]; then
        cleanup
    fi
    
    # Show final status
    echo ""
    if show_status; then
        log "SUCCESS" "🎉 AI Karen Database Stack stopped successfully!"
    else
        log "WARN" "Some services may still be running. Use --force to kill them."
        exit 1
    fi
}

# Change to script directory
cd "$(dirname "$0")/.."

# Run main function with all arguments
main "$@"