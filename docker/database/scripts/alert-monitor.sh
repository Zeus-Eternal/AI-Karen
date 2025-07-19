#!/bin/bash
set -e

# AI Karen Database Stack Alert Monitor
# This script monitors database services and sends alerts on failures

echo "🚨 AI Karen Database Stack Alert Monitor"
echo "======================================="

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
        "ALERT")
            echo -e "\033[0;41m[$timestamp] ALERT: $message\033[0m"
            ;;
        *)
            echo "[$timestamp] $message"
            ;;
    esac
}

# Configuration
ALERT_LOG_FILE="${ALERT_LOG_FILE:-./logs/alerts.log}"
RECOVERY_LOG_FILE="${RECOVERY_LOG_FILE:-./logs/recovery.log}"
CHECK_INTERVAL="${CHECK_INTERVAL:-60}"
MAX_RECOVERY_ATTEMPTS="${MAX_RECOVERY_ATTEMPTS:-3}"
ALERT_WEBHOOK_URL="${ALERT_WEBHOOK_URL:-}"
ALERT_EMAIL="${ALERT_EMAIL:-}"

# Service status tracking
declare -A SERVICE_STATUS
declare -A SERVICE_FAILURE_COUNT
declare -A SERVICE_LAST_ALERT

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
}

# Function to create log directories
setup_logging() {
    mkdir -p "$(dirname "$ALERT_LOG_FILE")"
    mkdir -p "$(dirname "$RECOVERY_LOG_FILE")"
    
    # Create log files if they don't exist
    touch "$ALERT_LOG_FILE"
    touch "$RECOVERY_LOG_FILE"
}

# Function to send webhook alert
send_webhook_alert() {
    local service="$1"
    local status="$2"
    local message="$3"
    
    if [ -n "$ALERT_WEBHOOK_URL" ]; then
        local payload=$(cat << EOF
{
    "service": "$service",
    "status": "$status",
    "message": "$message",
    "timestamp": "$(date -Iseconds)",
    "hostname": "$(hostname)"
}
EOF
)
        
        if curl -s -X POST "$ALERT_WEBHOOK_URL" \
            -H "Content-Type: application/json" \
            -d "$payload" > /dev/null; then
            log "INFO" "Webhook alert sent for $service"
        else
            log "WARN" "Failed to send webhook alert for $service"
        fi
    fi
}

# Function to send email alert
send_email_alert() {
    local service="$1"
    local status="$2"
    local message="$3"
    
    if [ -n "$ALERT_EMAIL" ] && command -v mail > /dev/null 2>&1; then
        local subject="AI Karen Database Alert: $service $status"
        local body="Service: $service
Status: $status
Message: $message
Timestamp: $(date)
Hostname: $(hostname)

This is an automated alert from the AI Karen Database monitoring system."
        
        if echo "$body" | mail -s "$subject" "$ALERT_EMAIL"; then
            log "INFO" "Email alert sent for $service"
        else
            log "WARN" "Failed to send email alert for $service"
        fi
    fi
}

# Function to log alert
log_alert() {
    local service="$1"
    local status="$2"
    local message="$3"
    
    local alert_entry="$(date -Iseconds) | $service | $status | $message"
    echo "$alert_entry" >> "$ALERT_LOG_FILE"
    
    log "ALERT" "$service: $message"
}

# Function to send alert
send_alert() {
    local service="$1"
    local status="$2"
    local message="$3"
    
    # Check if we've already sent an alert recently (avoid spam)
    local current_time=$(date +%s)
    local last_alert_time=${SERVICE_LAST_ALERT[$service]:-0}
    local alert_cooldown=300  # 5 minutes
    
    if [ $((current_time - last_alert_time)) -lt $alert_cooldown ]; then
        return 0
    fi
    
    # Log the alert
    log_alert "$service" "$status" "$message"
    
    # Send notifications
    send_webhook_alert "$service" "$status" "$message"
    send_email_alert "$service" "$status" "$message"
    
    # Update last alert time
    SERVICE_LAST_ALERT[$service]=$current_time
}

# Function to check PostgreSQL health
check_postgres_health() {
    local host="${POSTGRES_HOST:-localhost}"
    local port="${POSTGRES_PORT:-5432}"
    local user="${POSTGRES_USER:-karen_user}"
    local db="${POSTGRES_DB:-ai_karen}"
    local password="${POSTGRES_PASSWORD:-}"
    
    if PGPASSWORD="$password" pg_isready -h "$host" -p "$port" -U "$user" -d "$db" &> /dev/null; then
        return 0
    else
        return 1
    fi
}

# Function to check Redis health
check_redis_health() {
    local host="${REDIS_HOST:-localhost}"
    local port="${REDIS_PORT:-6379}"
    local password="${REDIS_PASSWORD:-}"
    
    local redis_cmd="redis-cli -h $host -p $port"
    if [ -n "$password" ]; then
        redis_cmd="$redis_cmd -a $password"
    fi
    
    if $redis_cmd ping | grep -q "PONG" 2>/dev/null; then
        return 0
    else
        return 1
    fi
}

# Function to check Elasticsearch health
check_elasticsearch_health() {
    local host="${ELASTICSEARCH_HOST:-localhost}"
    local port="${ELASTICSEARCH_PORT:-9200}"
    
    if curl -s -f "http://$host:$port/_cluster/health" > /dev/null; then
        local cluster_status=$(curl -s "http://$host:$port/_cluster/health" | jq -r '.status' 2>/dev/null)
        if [ "$cluster_status" = "red" ]; then
            return 1
        else
            return 0
        fi
    else
        return 1
    fi
}

# Function to check Milvus health
check_milvus_health() {
    local host="${MILVUS_HOST:-localhost}"
    local port="${MILVUS_PORT:-19530}"
    
    if nc -z "$host" "$port" 2>/dev/null; then
        return 0
    else
        return 1
    fi
}

# Function to check service container status
check_container_status() {
    local service="$1"
    
    if $COMPOSE_CMD ps "$service" | grep -q "Up"; then
        return 0
    else
        return 1
    fi
}

# Function to attempt service recovery
attempt_recovery() {
    local service="$1"
    local recovery_method="$2"
    
    log "INFO" "Attempting recovery for $service using method: $recovery_method"
    
    local recovery_entry="$(date -Iseconds) | $service | $recovery_method | STARTED"
    echo "$recovery_entry" >> "$RECOVERY_LOG_FILE"
    
    case "$recovery_method" in
        "restart")
            if $COMPOSE_CMD restart "$service"; then
                log "SUCCESS" "Service $service restarted successfully"
                echo "$(date -Iseconds) | $service | restart | SUCCESS" >> "$RECOVERY_LOG_FILE"
                return 0
            else
                log "ERROR" "Failed to restart service $service"
                echo "$(date -Iseconds) | $service | restart | FAILED" >> "$RECOVERY_LOG_FILE"
                return 1
            fi
            ;;
        "recreate")
            if $COMPOSE_CMD up -d --force-recreate "$service"; then
                log "SUCCESS" "Service $service recreated successfully"
                echo "$(date -Iseconds) | $service | recreate | SUCCESS" >> "$RECOVERY_LOG_FILE"
                return 0
            else
                log "ERROR" "Failed to recreate service $service"
                echo "$(date -Iseconds) | $service | recreate | FAILED" >> "$RECOVERY_LOG_FILE"
                return 1
            fi
            ;;
        "pull_restart")
            if $COMPOSE_CMD pull "$service" && $COMPOSE_CMD up -d "$service"; then
                log "SUCCESS" "Service $service pulled and restarted successfully"
                echo "$(date -Iseconds) | $service | pull_restart | SUCCESS" >> "$RECOVERY_LOG_FILE"
                return 0
            else
                log "ERROR" "Failed to pull and restart service $service"
                echo "$(date -Iseconds) | $service | pull_restart | FAILED" >> "$RECOVERY_LOG_FILE"
                return 1
            fi
            ;;
        *)
            log "ERROR" "Unknown recovery method: $recovery_method"
            return 1
            ;;
    esac
}

# Function to handle service failure
handle_service_failure() {
    local service="$1"
    local failure_reason="$2"
    
    # Increment failure count
    SERVICE_FAILURE_COUNT[$service]=$((${SERVICE_FAILURE_COUNT[$service]:-0} + 1))
    local failure_count=${SERVICE_FAILURE_COUNT[$service]}
    
    log "WARN" "Service $service failed (attempt $failure_count): $failure_reason"
    
    # Send alert
    send_alert "$service" "FAILED" "$failure_reason (failure count: $failure_count)"
    
    # Attempt recovery if within limits
    if [ $failure_count -le $MAX_RECOVERY_ATTEMPTS ]; then
        local recovery_method="restart"
        
        # Escalate recovery method based on failure count
        case $failure_count in
            1) recovery_method="restart" ;;
            2) recovery_method="recreate" ;;
            3) recovery_method="pull_restart" ;;
        esac
        
        if attempt_recovery "$service" "$recovery_method"; then
            # Wait for service to stabilize
            sleep 30
            
            # Check if recovery was successful
            if check_service_health "$service"; then
                log "SUCCESS" "Service $service recovered successfully"
                SERVICE_FAILURE_COUNT[$service]=0
                send_alert "$service" "RECOVERED" "Service recovered after $recovery_method"
                return 0
            else
                log "ERROR" "Service $service recovery failed"
                return 1
            fi
        else
            log "ERROR" "Recovery attempt failed for service $service"
            return 1
        fi
    else
        log "ERROR" "Service $service has exceeded maximum recovery attempts ($MAX_RECOVERY_ATTEMPTS)"
        send_alert "$service" "CRITICAL" "Service has exceeded maximum recovery attempts and requires manual intervention"
        return 1
    fi
}

# Function to check service health
check_service_health() {
    local service="$1"
    
    # First check if container is running
    if ! check_container_status "$service"; then
        return 1
    fi
    
    # Then check service-specific health
    case "$service" in
        "postgres")
            check_postgres_health
            ;;
        "redis")
            check_redis_health
            ;;
        "elasticsearch")
            check_elasticsearch_health
            ;;
        "milvus")
            check_milvus_health
            ;;
        *)
            # For other services, just check container status
            return 0
            ;;
    esac
}

# Function to monitor all services
monitor_services() {
    local services=("postgres" "redis" "elasticsearch" "milvus" "etcd" "minio")
    
    for service in "${services[@]}"; do
        # Skip if service is not defined in compose file
        if ! $COMPOSE_CMD config --services | grep -q "^$service$"; then
            continue
        fi
        
        local current_status="healthy"
        local previous_status=${SERVICE_STATUS[$service]:-"unknown"}
        
        if check_service_health "$service"; then
            current_status="healthy"
            
            # If service was previously unhealthy, send recovery alert
            if [ "$previous_status" = "unhealthy" ]; then
                log "SUCCESS" "Service $service is now healthy"
                send_alert "$service" "RECOVERED" "Service is now healthy"
                SERVICE_FAILURE_COUNT[$service]=0
            fi
        else
            current_status="unhealthy"
            
            # If service was previously healthy, handle failure
            if [ "$previous_status" = "healthy" ] || [ "$previous_status" = "unknown" ]; then
                handle_service_failure "$service" "Health check failed"
            fi
        fi
        
        SERVICE_STATUS[$service]=$current_status
    done
}

# Function to check system resources
check_system_resources() {
    # Check disk space
    local disk_usage=$(df -h . | tail -n1 | awk '{print $5}' | tr -d '%')
    if [ "$disk_usage" -gt 90 ]; then
        send_alert "system" "CRITICAL" "Disk usage is critically high: ${disk_usage}%"
    elif [ "$disk_usage" -gt 80 ]; then
        send_alert "system" "WARNING" "Disk usage is high: ${disk_usage}%"
    fi
    
    # Check memory usage
    if command -v free > /dev/null 2>&1; then
        local mem_usage=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100.0}')
        if [ "$mem_usage" -gt 90 ]; then
            send_alert "system" "CRITICAL" "Memory usage is critically high: ${mem_usage}%"
        elif [ "$mem_usage" -gt 80 ]; then
            send_alert "system" "WARNING" "Memory usage is high: ${mem_usage}%"
        fi
    fi
    
    # Check Docker daemon
    if ! docker system df > /dev/null 2>&1; then
        send_alert "docker" "CRITICAL" "Docker daemon is not responsive"
    fi
}

# Function to show usage information
show_usage() {
    echo "AI Karen Database Stack Alert Monitor"
    echo ""
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  --interval <sec>     Check interval in seconds (default: 60)"
    echo "  --max-attempts <n>   Maximum recovery attempts (default: 3)"
    echo "  --webhook <url>      Webhook URL for alerts"
    echo "  --email <address>    Email address for alerts"
    echo "  --daemon             Run as daemon (background process)"
    echo "  --help               Show this help message"
    echo ""
    echo "Environment Variables:"
    echo "  CHECK_INTERVAL       Check interval in seconds"
    echo "  MAX_RECOVERY_ATTEMPTS Maximum recovery attempts"
    echo "  ALERT_WEBHOOK_URL    Webhook URL for alerts"
    echo "  ALERT_EMAIL          Email address for alerts"
    echo "  ALERT_LOG_FILE       Alert log file path"
    echo "  RECOVERY_LOG_FILE    Recovery log file path"
    echo ""
    echo "Examples:"
    echo "  $0                           # Run with default settings"
    echo "  $0 --interval 30             # Check every 30 seconds"
    echo "  $0 --webhook http://...      # Send alerts to webhook"
    echo "  $0 --daemon                  # Run as background daemon"
}

# Function to run as daemon
run_daemon() {
    log "INFO" "Starting alert monitor daemon (PID: $$)"
    log "INFO" "Check interval: ${CHECK_INTERVAL}s"
    log "INFO" "Max recovery attempts: $MAX_RECOVERY_ATTEMPTS"
    
    # Create PID file
    echo $$ > ./logs/alert-monitor.pid
    
    # Trap signals for graceful shutdown
    trap 'log "INFO" "Shutting down alert monitor daemon"; rm -f ./logs/alert-monitor.pid; exit 0' SIGTERM SIGINT
    
    while true; do
        monitor_services
        check_system_resources
        sleep "$CHECK_INTERVAL"
    done
}

# Main function
main() {
    local daemon_mode="false"
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --interval)
                CHECK_INTERVAL="$2"
                shift 2
                ;;
            --max-attempts)
                MAX_RECOVERY_ATTEMPTS="$2"
                shift 2
                ;;
            --webhook)
                ALERT_WEBHOOK_URL="$2"
                shift 2
                ;;
            --email)
                ALERT_EMAIL="$2"
                shift 2
                ;;
            --daemon)
                daemon_mode="true"
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
    
    # Validate interval
    if ! [[ "$CHECK_INTERVAL" =~ ^[0-9]+$ ]] || [ "$CHECK_INTERVAL" -lt 10 ]; then
        log "ERROR" "Check interval must be at least 10 seconds"
        exit 1
    fi
    
    # Check Docker Compose availability
    check_docker_compose
    
    # Setup logging
    setup_logging
    
    # Install required tools
    if command -v apk > /dev/null 2>&1; then
        apk add --no-cache curl postgresql-client redis jq netcat-openbsd > /dev/null 2>&1 || true
    elif command -v apt-get > /dev/null 2>&1; then
        apt-get update > /dev/null 2>&1 && apt-get install -y curl postgresql-client redis-tools jq netcat > /dev/null 2>&1 || true
    fi
    
    if [ "$daemon_mode" = "true" ]; then
        run_daemon
    else
        # Run once
        log "INFO" "Running single monitoring check..."
        monitor_services
        check_system_resources
        log "INFO" "Monitoring check completed"
    fi
}

# Change to script directory
cd "$(dirname "$0")/.."

# Run main function with all arguments
main "$@"