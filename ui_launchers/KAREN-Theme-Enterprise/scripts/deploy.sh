#!/bin/bash

# Production Deployment Script
# Automated deployment with health checks, rollback capabilities,
# and comprehensive monitoring integration

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DEPLOYMENT_ENV="${DEPLOYMENT_ENV:-production}"
DOCKER_COMPOSE_FILE="${PROJECT_ROOT}/docker-compose.production.yml"
BACKUP_DIR="${PROJECT_ROOT}/backups"
LOG_FILE="${PROJECT_ROOT}/logs/deployment.log"
HEALTH_CHECK_TIMEOUT=300
ROLLBACK_ENABLED="${ROLLBACK_ENABLED:-true}"
SLACK_WEBHOOK_URL="${SLACK_WEBHOOK_URL:-}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    echo -e "${timestamp} [${level}] ${message}" | tee -a "$LOG_FILE"
    
    case "$level" in
        "ERROR")
            echo -e "${RED}${timestamp} [${level}] ${message}${NC}" >&2
            ;;
        "WARN")
            echo -e "${YELLOW}${timestamp} [${level}] ${message}${NC}"
            ;;
        "SUCCESS")
            echo -e "${GREEN}${timestamp} [${level}] ${message}${NC}"
            ;;
        "INFO")
            echo -e "${BLUE}${timestamp} [${level}] ${message}${NC}"
            ;;
    esac
}

# Send notification to Slack
send_slack_notification() {
    local status="$1"
    local message="$2"
    
    if [[ -n "$SLACK_WEBHOOK_URL" ]]; then
        local color="good"
        if [[ "$status" == "error" ]]; then
            color="danger"
        elif [[ "$status" == "warning" ]]; then
            color="warning"
        fi
        
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"attachments\":[{\"color\":\"$color\",\"text\":\"$message\"}]}" \
            "$SLACK_WEBHOOK_URL" 2>/dev/null || true
    fi
}

# Check prerequisites
check_prerequisites() {
    log "INFO" "Checking deployment prerequisites..."
    
    # Check if Docker is running
    if ! docker info >/dev/null 2>&1; then
        log "ERROR" "Docker is not running or not accessible"
        exit 1
    fi
    
    # Check if Docker Compose is available
    if ! command -v docker-compose >/dev/null 2>&1; then
        log "ERROR" "Docker Compose is not installed"
        exit 1
    fi
    
    # Check if required environment file exists
    if [[ ! -f "${PROJECT_ROOT}/.env.${DEPLOYMENT_ENV}" ]]; then
        log "ERROR" "Environment file .env.${DEPLOYMENT_ENV} not found"
        exit 1
    fi
    
    # Check if Docker Compose file exists
    if [[ ! -f "$DOCKER_COMPOSE_FILE" ]]; then
        log "ERROR" "Docker Compose file not found: $DOCKER_COMPOSE_FILE"
        exit 1
    fi
    
    # Create necessary directories
    mkdir -p "$BACKUP_DIR" "$(dirname "$LOG_FILE")"
    
    log "SUCCESS" "Prerequisites check passed"
}

# Create backup of current deployment
create_backup() {
    log "INFO" "Creating backup of current deployment..."
    
    local backup_timestamp=$(date '+%Y%m%d_%H%M%S')
    local backup_path="${BACKUP_DIR}/backup_${backup_timestamp}"
    
    mkdir -p "$backup_path"
    
    # Backup database if running
    if docker-compose -f "$DOCKER_COMPOSE_FILE" ps postgres | grep -q "Up"; then
        log "INFO" "Backing up PostgreSQL database..."
        docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T postgres \
            pg_dump -U "${POSTGRES_USER}" "${POSTGRES_DB}" > "${backup_path}/database.sql" || {
            log "WARN" "Database backup failed, continuing deployment..."
        }
    fi
    
    # Backup Redis data if running
    if docker-compose -f "$DOCKER_COMPOSE_FILE" ps redis | grep -q "Up"; then
        log "INFO" "Backing up Redis data..."
        docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T redis \
            redis-cli --rdb - > "${backup_path}/redis.rdb" || {
            log "WARN" "Redis backup failed, continuing deployment..."
        }
    fi
    
    # Backup current Docker images
    log "INFO" "Backing up current Docker images..."
    docker images --format "table {{.Repository}}:{{.Tag}}" | grep "kari" > "${backup_path}/images.txt" || true
    
    # Store backup path for potential rollback
    echo "$backup_path" > "${PROJECT_ROOT}/.last_backup"
    
    log "SUCCESS" "Backup created at: $backup_path"
}

# Build and deploy new version
deploy() {
    log "INFO" "Starting deployment process..."
    
    # Load environment variables
    set -a
    source "${PROJECT_ROOT}/.env.${DEPLOYMENT_ENV}"
    set +a
    
    # Build new images
    log "INFO" "Building Docker images..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" build --no-cache web-ui || {
        log "ERROR" "Failed to build Docker images"
        exit 1
    }
    
    # Stop old containers gracefully
    log "INFO" "Stopping existing containers..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" down --timeout 30 || {
        log "WARN" "Some containers didn't stop gracefully, forcing shutdown..."
        docker-compose -f "$DOCKER_COMPOSE_FILE" down --timeout 5
    }
    
    # Start new containers
    log "INFO" "Starting new containers..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" up -d || {
        log "ERROR" "Failed to start new containers"
        if [[ "$ROLLBACK_ENABLED" == "true" ]]; then
            rollback
        fi
        exit 1
    }
    
    log "SUCCESS" "Containers started successfully"
}

# Health check function
health_check() {
    log "INFO" "Performing health checks..."
    
    local start_time=$(date +%s)
    local timeout_time=$((start_time + HEALTH_CHECK_TIMEOUT))
    
    # Wait for containers to be ready
    log "INFO" "Waiting for containers to be ready..."
    sleep 30
    
    # Check application health
    while [[ $(date +%s) -lt $timeout_time ]]; do
        log "INFO" "Checking application health..."
        
        # Check main application
        if curl -f -s "http://localhost:3000/api/health" >/dev/null 2>&1; then
            log "SUCCESS" "Main application health check passed"
            
            # Check readiness
            if curl -f -s "http://localhost:3000/api/ready" >/dev/null 2>&1; then
                log "SUCCESS" "Application readiness check passed"
                
                # Check database connectivity
                if docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T postgres \
                   pg_isready -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" >/dev/null 2>&1; then
                    log "SUCCESS" "Database connectivity check passed"
                    
                    # Check Redis connectivity
                    if docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T redis \
                       redis-cli ping >/dev/null 2>&1; then
                        log "SUCCESS" "Redis connectivity check passed"
                        log "SUCCESS" "All health checks passed"
                        return 0
                    fi
                fi
            fi
        fi
        
        log "INFO" "Health checks not yet passing, retrying in 10 seconds..."
        sleep 10
    done
    
    log "ERROR" "Health checks failed after ${HEALTH_CHECK_TIMEOUT} seconds"
    return 1
}

# Rollback function
rollback() {
    log "WARN" "Initiating rollback procedure..."
    
    if [[ ! -f "${PROJECT_ROOT}/.last_backup" ]]; then
        log "ERROR" "No backup information found, cannot rollback"
        return 1
    fi
    
    local backup_path=$(cat "${PROJECT_ROOT}/.last_backup")
    
    if [[ ! -d "$backup_path" ]]; then
        log "ERROR" "Backup directory not found: $backup_path"
        return 1
    fi
    
    # Stop current containers
    log "INFO" "Stopping current containers for rollback..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" down --timeout 30
    
    # Restore database if backup exists
    if [[ -f "${backup_path}/database.sql" ]]; then
        log "INFO" "Restoring database from backup..."
        docker-compose -f "$DOCKER_COMPOSE_FILE" up -d postgres
        sleep 30
        docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T postgres \
            psql -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" < "${backup_path}/database.sql" || {
            log "WARN" "Database restore failed"
        }
    fi
    
    # Restore Redis if backup exists
    if [[ -f "${backup_path}/redis.rdb" ]]; then
        log "INFO" "Restoring Redis from backup..."
        docker-compose -f "$DOCKER_COMPOSE_FILE" up -d redis
        sleep 10
        docker cp "${backup_path}/redis.rdb" "$(docker-compose -f "$DOCKER_COMPOSE_FILE" ps -q redis):/data/dump.rdb" || {
            log "WARN" "Redis restore failed"
        }
        docker-compose -f "$DOCKER_COMPOSE_FILE" restart redis
    fi
    
    # Start all services
    log "INFO" "Starting services after rollback..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" up -d
    
    # Wait and check health after rollback
    sleep 30
    if health_check; then
        log "SUCCESS" "Rollback completed successfully"
        send_slack_notification "warning" "Deployment rolled back successfully"
        return 0
    else
        log "ERROR" "Rollback failed - system may be in inconsistent state"
        send_slack_notification "error" "Rollback failed - manual intervention required"
        return 1
    fi
}

# Cleanup old images and containers
cleanup() {
    log "INFO" "Cleaning up old Docker resources..."
    
    # Remove unused images
    docker image prune -f >/dev/null 2>&1 || true
    
    # Remove unused containers
    docker container prune -f >/dev/null 2>&1 || true
    
    # Remove unused volumes (be careful with this in production)
    # docker volume prune -f >/dev/null 2>&1 || true
    
    # Remove old backups (keep last 5)
    if [[ -d "$BACKUP_DIR" ]]; then
        find "$BACKUP_DIR" -maxdepth 1 -type d -name "backup_*" | \
            sort -r | tail -n +6 | xargs -r rm -rf
    fi
    
    log "SUCCESS" "Cleanup completed"
}

# Show deployment status
show_status() {
    log "INFO" "Deployment Status:"
    echo "===================="
    
    # Show container status
    docker-compose -f "$DOCKER_COMPOSE_FILE" ps
    
    echo ""
    log "INFO" "Service URLs:"
    echo "- Main Application: http://localhost:3000"
    echo "- Health Check: http://localhost:3000/api/health"
    echo "- Readiness Check: http://localhost:3000/api/ready"
    echo "- Grafana: http://localhost:3001"
    echo "- Prometheus: http://localhost:9090"
    
    echo ""
    log "INFO" "Logs can be viewed with:"
    echo "docker-compose -f $DOCKER_COMPOSE_FILE logs -f [service_name]"
}

# Main deployment function
main() {
    local start_time=$(date +%s)
    
    log "INFO" "Starting deployment to $DEPLOYMENT_ENV environment"
    send_slack_notification "good" "Starting deployment to $DEPLOYMENT_ENV environment"
    
    # Trap to handle script interruption
    trap 'log "ERROR" "Deployment interrupted"; send_slack_notification "error" "Deployment interrupted"; exit 1' INT TERM
    
    # Run deployment steps
    check_prerequisites
    create_backup
    deploy
    
    if health_check; then
        cleanup
        show_status
        
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        
        log "SUCCESS" "Deployment completed successfully in ${duration} seconds"
        send_slack_notification "good" "Deployment to $DEPLOYMENT_ENV completed successfully in ${duration} seconds"
    else
        log "ERROR" "Deployment failed health checks"
        
        if [[ "$ROLLBACK_ENABLED" == "true" ]]; then
            if rollback; then
                log "INFO" "System rolled back to previous version"
            else
                log "ERROR" "Rollback failed - manual intervention required"
                send_slack_notification "error" "Deployment failed and rollback failed - manual intervention required"
                exit 1
            fi
        else
            log "ERROR" "Rollback disabled - manual intervention required"
            send_slack_notification "error" "Deployment failed - manual intervention required"
            exit 1
        fi
    fi
}

# Handle command line arguments
case "${1:-deploy}" in
    "deploy")
        main
        ;;
    "rollback")
        rollback
        ;;
    "status")
        show_status
        ;;
    "health")
        health_check
        ;;
    "cleanup")
        cleanup
        ;;
    *)
        echo "Usage: $0 {deploy|rollback|status|health|cleanup}"
        echo ""
        echo "Commands:"
        echo "  deploy   - Deploy the application (default)"
        echo "  rollback - Rollback to previous version"
        echo "  status   - Show deployment status"
        echo "  health   - Run health checks"
        echo "  cleanup  - Clean up old Docker resources"
        exit 1
        ;;
esac