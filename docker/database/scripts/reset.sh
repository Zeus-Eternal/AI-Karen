#!/bin/bash
set -e

# AI Karen Database Stack Reset Script
# This script completely resets the database stack (DESTRUCTIVE OPERATION)

echo "⚠️  AI Karen Database Stack Reset"
echo "================================="
echo ""
echo "🚨 WARNING: This will PERMANENTLY DELETE all database data!"
echo "🚨 This operation cannot be undone!"
echo ""

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
        "DANGER")
            echo -e "\033[1;31m[$timestamp] DANGER: $message\033[0m"
            ;;
        *)
            echo "[$timestamp] $message"
            ;;
    esac
}

# Function to confirm the destructive operation
confirm_reset() {
    local skip_confirmation="${1:-false}"
    
    if [ "$skip_confirmation" = "true" ]; then
        log "WARN" "Skipping confirmation (--force flag provided)"
        return 0
    fi
    
    echo "This will:"
    echo "  ❌ Delete all PostgreSQL data"
    echo "  ❌ Delete all Elasticsearch indices"
    echo "  ❌ Delete all Milvus collections"
    echo "  ❌ Delete all Redis data"
    echo "  ❌ Delete all DuckDB databases"
    echo "  ❌ Remove all Docker volumes"
    echo "  ❌ Remove all containers"
    echo ""
    
    read -p "Type 'RESET' to confirm this destructive operation: " -r
    echo ""
    
    if [ "$REPLY" != "RESET" ]; then
        log "INFO" "Operation cancelled"
        exit 0
    fi
    
    echo ""
    read -p "Are you absolutely sure? This cannot be undone! (yes/no): " -r
    echo ""
    
    if [ "$REPLY" != "yes" ]; then
        log "INFO" "Operation cancelled"
        exit 0
    fi
}

# Function to create backup before reset
create_backup() {
    local create_backup="${1:-false}"
    
    if [ "$create_backup" = "false" ]; then
        return 0
    fi
    
    log "INFO" "Creating backup before reset..."
    
    if [ -f "./scripts/backup.sh" ]; then
        local backup_name="pre_reset_$(date +%Y%m%d_%H%M%S)"
        ./scripts/backup.sh --name "$backup_name"
        log "SUCCESS" "Backup created: $backup_name"
    else
        log "WARN" "Backup script not found, skipping backup"
    fi
}

# Function to check Docker Compose availability
check_docker_compose() {
    if command -v docker-compose &> /dev/null; then
        COMPOSE_CMD="docker-compose"
    elif docker compose version &> /dev/null; then
        COMPOSE_CMD="docker compose"
    else
        log "ERROR" "Docker Compose is not available"
        exit 1
    fi
}

# Function to stop and remove all containers
stop_and_remove_containers() {
    log "DANGER" "Stopping and removing all containers..."
    
    # Force stop all containers
    $COMPOSE_CMD kill 2>/dev/null || true
    
    # Remove all containers
    $COMPOSE_CMD down --remove-orphans 2>/dev/null || true
    
    # Remove any remaining containers manually
    local ai_karen_containers=$(docker ps -a --filter "name=ai-karen" --format "{{.Names}}" 2>/dev/null || true)
    if [ -n "$ai_karen_containers" ]; then
        log "INFO" "Removing remaining AI Karen containers..."
        echo "$ai_karen_containers" | xargs docker rm -f 2>/dev/null || true
    fi
    
    log "SUCCESS" "Containers removed"
}

# Function to remove all volumes
remove_volumes() {
    log "DANGER" "Removing all Docker volumes..."
    
    # Remove volumes using docker-compose
    $COMPOSE_CMD down -v 2>/dev/null || true
    
    # Remove AI Karen specific volumes manually
    local ai_karen_volumes=$(docker volume ls --filter "name=ai-karen" --format "{{.Name}}" 2>/dev/null || true)
    if [ -n "$ai_karen_volumes" ]; then
        log "INFO" "Removing AI Karen volumes..."
        echo "$ai_karen_volumes" | xargs docker volume rm -f 2>/dev/null || true
    fi
    
    # Remove volumes by pattern
    local volume_patterns=("postgres_data" "elasticsearch_data" "milvus_data" "redis_data" "etcd_data" "minio_data" "duckdb_data")
    
    for pattern in "${volume_patterns[@]}"; do
        local volumes=$(docker volume ls --filter "name=$pattern" --format "{{.Name}}" 2>/dev/null || true)
        if [ -n "$volumes" ]; then
            log "INFO" "Removing volumes matching pattern: $pattern"
            echo "$volumes" | xargs docker volume rm -f 2>/dev/null || true
        fi
    done
    
    log "SUCCESS" "Volumes removed"
}

# Function to remove local data directories
remove_local_data() {
    log "DANGER" "Removing local data directories..."
    
    local data_dirs=(
        "data/postgres"
        "data/elasticsearch"
        "data/milvus"
        "data/redis"
        "data/duckdb"
        "data/etcd"
        "data/minio"
    )
    
    for dir in "${data_dirs[@]}"; do
        if [ -d "$dir" ]; then
            log "INFO" "Removing directory: $dir"
            rm -rf "$dir"
        fi
    done
    
    # Remove any .db files in the current directory
    find . -name "*.db" -type f -delete 2>/dev/null || true
    
    log "SUCCESS" "Local data directories removed"
}

# Function to clean up Docker resources
cleanup_docker_resources() {
    local aggressive="${1:-false}"
    
    log "INFO" "Cleaning up Docker resources..."
    
    # Remove unused containers
    docker container prune -f 2>/dev/null || true
    
    # Remove unused networks
    docker network prune -f 2>/dev/null || true
    
    # Remove unused volumes
    docker volume prune -f 2>/dev/null || true
    
    if [ "$aggressive" = "true" ]; then
        log "INFO" "Performing aggressive cleanup..."
        
        # Remove unused images
        docker image prune -a -f 2>/dev/null || true
        
        # Remove build cache
        docker builder prune -a -f 2>/dev/null || true
    fi
    
    log "SUCCESS" "Docker resources cleaned up"
}

# Function to remove configuration files
remove_config_files() {
    local remove_env="${1:-false}"
    
    log "INFO" "Cleaning up configuration files..."
    
    # Remove migration state
    rm -f migration_state.json
    
    # Remove temporary files
    rm -rf /tmp/ai_karen_init 2>/dev/null || true
    
    # Remove logs
    rm -rf logs/* 2>/dev/null || true
    
    if [ "$remove_env" = "true" ]; then
        log "WARN" "Removing .env file..."
        rm -f .env
    fi
    
    log "SUCCESS" "Configuration files cleaned up"
}

# Function to verify reset completion
verify_reset() {
    log "INFO" "Verifying reset completion..."
    
    # Check for running containers
    local running_containers=$($COMPOSE_CMD ps -q 2>/dev/null | wc -l)
    if [ "$running_containers" -eq 0 ]; then
        log "SUCCESS" "No containers running"
    else
        log "WARN" "Some containers may still be running"
    fi
    
    # Check for volumes
    local remaining_volumes=$(docker volume ls --filter "name=ai-karen" --format "{{.Name}}" 2>/dev/null | wc -l)
    if [ "$remaining_volumes" -eq 0 ]; then
        log "SUCCESS" "No AI Karen volumes remaining"
    else
        log "WARN" "Some volumes may still exist"
    fi
    
    # Check data directories
    local data_exists=false
    local data_dirs=("data/postgres" "data/elasticsearch" "data/milvus" "data/redis" "data/duckdb")
    
    for dir in "${data_dirs[@]}"; do
        if [ -d "$dir" ] && [ "$(ls -A "$dir" 2>/dev/null)" ]; then
            data_exists=true
            break
        fi
    done
    
    if [ "$data_exists" = "false" ]; then
        log "SUCCESS" "No local data directories with content"
    else
        log "WARN" "Some data directories may still contain files"
    fi
}

# Function to show post-reset instructions
show_post_reset_instructions() {
    echo ""
    log "SUCCESS" "🎉 Database stack reset completed!"
    echo ""
    echo "Next steps to get back up and running:"
    echo "  1. Review and customize .env file (if removed)"
    echo "  2. Start the database stack: ./scripts/start.sh"
    echo "  3. The system will automatically initialize with fresh data"
    echo ""
    echo "If you created a backup, you can restore it with:"
    echo "  ./scripts/restore.sh <backup_name>"
    echo ""
}

# Function to show usage information
show_usage() {
    echo "AI Karen Database Stack Reset Script"
    echo ""
    echo "⚠️  WARNING: This is a DESTRUCTIVE operation that will delete all data!"
    echo ""
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  --force            Skip confirmation prompts (DANGEROUS!)"
    echo "  --backup           Create backup before reset"
    echo "  --keep-env         Keep .env file (don't remove configuration)"
    echo "  --aggressive       Aggressive Docker cleanup (removes images too)"
    echo "  --help             Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                 # Interactive reset with confirmations"
    echo "  $0 --backup        # Create backup before reset"
    echo "  $0 --force         # Skip confirmations (DANGEROUS!)"
    echo ""
    echo "What gets reset:"
    echo "  ❌ All database data (PostgreSQL, Elasticsearch, Milvus, Redis, DuckDB)"
    echo "  ❌ All Docker containers and volumes"
    echo "  ❌ All local data directories"
    echo "  ❌ Migration state and temporary files"
    echo "  ❌ Log files"
    echo "  ❌ .env file (unless --keep-env is used)"
}

# Main function
main() {
    local force="false"
    local backup="false"
    local keep_env="true"
    local aggressive="false"
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --force)
                force="true"
                shift
                ;;
            --backup)
                backup="true"
                shift
                ;;
            --keep-env)
                keep_env="true"
                shift
                ;;
            --remove-env)
                keep_env="false"
                shift
                ;;
            --aggressive)
                aggressive="true"
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
    
    # Check prerequisites
    check_docker_compose
    
    # Confirm the destructive operation
    confirm_reset "$force"
    
    log "DANGER" "Starting database stack reset..."
    
    # Create backup if requested
    create_backup "$backup"
    
    # Perform reset operations
    stop_and_remove_containers
    remove_volumes
    remove_local_data
    cleanup_docker_resources "$aggressive"
    remove_config_files "$([[ $keep_env == false ]] && echo true || echo false)"
    
    # Verify reset completion
    verify_reset
    
    # Show post-reset instructions
    show_post_reset_instructions
}

# Change to script directory
cd "$(dirname "$0")/.."

# Run main function with all arguments
main "$@"