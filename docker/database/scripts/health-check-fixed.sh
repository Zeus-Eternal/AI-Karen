#!/bin/bash
set -e

# AI Karen Database Stack Health Check Script
# This script performs comprehensive health checks on all database services

echo "🏥 AI Karen Database Stack Health Check"
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

# Global variables for health status
OVERALL_HEALTH="healthy"
HEALTH_ISSUES=()

# Function to record health issue
record_issue() {
    local service="$1"
    local issue="$2"
    
    OVERALL_HEALTH="unhealthy"
    HEALTH_ISSUES+=("$service: $issue")
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
}

# Function to check PostgreSQL health
check_postgres_health() {
    local service_name="ai-karen-postgres"
    
    echo ""
    log "INFO" "Checking PostgreSQL health..."
    
    # Check if container is running
    if ! docker ps | grep -q "$service_name"; then
        record_issue "$service_name" "Container not running"
        log "ERROR" "PostgreSQL container is not running"
        return 1
    fi
    
    # Check database connectivity
    local host="${POSTGRES_HOST:-localhost}"
    local port="${POSTGRES_PORT:-5434}"
    local user="${POSTGRES_USER:-karen_user}"
    local db="${POSTGRES_DB:-ai_karen}"
    local password="${POSTGRES_PASSWORD:-}"
    
    if PGPASSWORD="$password" pg_isready -h "$host" -p "$port" -U "$user" -d "$db" &> /dev/null; then
        log "SUCCESS" "PostgreSQL is accepting connections"
    else
        record_issue "$service_name" "Database not accepting connections"
        log "ERROR" "PostgreSQL is not accepting connections"
        return 1
    fi
    
    # Check database tables
    local table_count=$(PGPASSWORD="$password" psql -h "$host" -p "$port" -U "$user" -d "$db" -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" 2>/dev/null | tr -d ' ' || echo "0")
    
    log "INFO" "PostgreSQL has $table_count tables"
    
    # Check disk usage
    local db_size=$(PGPASSWORD="$password" psql -h "$host" -p "$port" -U "$user" -d "$db" -t -c "SELECT pg_size_pretty(pg_database_size('$db'));" 2>/dev/null | tr -d ' ' || echo "unknown")
    
    log "INFO" "PostgreSQL database size: $db_size"
    
    # Check active connections
    local active_connections=$(PGPASSWORD="$password" psql -h "$host" -p "$port" -U "$user" -d "$db" -t -c "SELECT COUNT(*) FROM pg_stat_activity WHERE state = 'active';" 2>/dev/null | tr -d ' ' || echo "unknown")
    
    log "INFO" "PostgreSQL active connections: $active_connections"
    
    log "SUCCESS" "PostgreSQL health check passed"
    return 0
}

# Function to check Redis health
check_redis_health() {
    local service_name="ai-karen-redis"
    
    echo ""
    log "INFO" "Checking Redis health..."
    
    # Check if container is running
    if ! docker ps | grep -q "$service_name"; then
        record_issue "$service_name" "Container not running"
        log "ERROR" "Redis container is not running"
        return 1
    fi
    
    # Check Redis connectivity
    local host="${REDIS_HOST:-localhost}"
    local port="${REDIS_PORT:-6380}"
    local password="${REDIS_PASSWORD:-redis_secure_pass_change_me}"
    
    # Try to connect with password
    if docker exec "$service_name" redis-cli -a "$password" ping | grep -q "PONG"; then
        log "SUCCESS" "Redis is responding to ping"
    else
        record_issue "$service_name" "Redis not responding to ping"
        log "ERROR" "Redis is not responding to ping"
        return 1
    fi
    
    # Check Redis info
    local redis_version=$(docker exec "$service_name" redis-cli -a "$password" info server | grep "redis_version:" | cut -d':' -f2 | tr -d '\r' || echo "unknown")
    log "INFO" "Redis version: $redis_version"
    
    # Check memory usage
    local used_memory=$(docker exec "$service_name" redis-cli -a "$password" info memory | grep "used_memory_human:" | cut -d':' -f2 | tr -d '\r' || echo "unknown")
    log "INFO" "Redis memory usage: $used_memory"
    
    # Check connected clients
    local connected_clients=$(docker exec "$service_name" redis-cli -a "$password" info clients | grep "connected_clients:" | cut -d':' -f2 | tr -d '\r' || echo "unknown")
    log "INFO" "Redis connected clients: $connected_clients"
    
    # Check keyspace
    local total_keys=$(docker exec "$service_name" redis-cli -a "$password" info keyspace | grep -o "keys=[0-9]*" | cut -d'=' -f2 | paste -sd+ | bc 2>/dev/null || echo "0")
    log "INFO" "Redis total keys: $total_keys"
    
    log "SUCCESS" "Redis health check passed"
    return 0
}

# Function to check Elasticsearch health
check_elasticsearch_health() {
    local service_name="ai-karen-elasticsearch"
    
    echo ""
    log "INFO" "Checking Elasticsearch health..."
    
    # Check if container is running
    if ! docker ps | grep -q "$service_name"; then
        record_issue "$service_name" "Container not running"
        log "ERROR" "Elasticsearch container is not running"
        return 1
    fi
    
    # Check Elasticsearch connectivity
    local host="${ELASTICSEARCH_HOST:-localhost}"
    local port="${ELASTICSEARCH_PORT:-9200}"
    
    if curl -s -f "http://$host:$port/_cluster/health" > /dev/null; then
        log "SUCCESS" "Elasticsearch is responding"
    else
        record_issue "$service_name" "Elasticsearch not responding"
        log "ERROR" "Elasticsearch is not responding"
        return 1
    fi
    
    # Check cluster health
    local cluster_status=$(curl -s "http://$host:$port/_cluster/health" | jq -r '.status' 2>/dev/null || echo "unknown")
    
    case "$cluster_status" in
        "green")
            log "SUCCESS" "Elasticsearch cluster status: green"
            ;;
        "yellow")
            log "WARN" "Elasticsearch cluster status: yellow"
            ;;
        "red")
            record_issue "$service_name" "Cluster status is red"
            log "ERROR" "Elasticsearch cluster status: red"
            ;;
        *)
            log "WARN" "Elasticsearch cluster status: $cluster_status"
            ;;
    esac
    
    # Check node info
    local node_count=$(curl -s "http://$host:$port/_cluster/health" | jq -r '.number_of_nodes' 2>/dev/null || echo "unknown")
    log "INFO" "Elasticsearch nodes: $node_count"
    
    # Check indices
    local index_count=$(curl -s "http://$host:$port/_cat/indices?format=json" | jq '. | length' 2>/dev/null || echo "unknown")
    log "INFO" "Elasticsearch indices: $index_count"
    
    # Check disk usage
    local disk_usage=$(curl -s "http://$host:$port/_cat/allocation?format=json" | jq -r '.[0]."disk.percent"' 2>/dev/null || echo "unknown")
    log "INFO" "Elasticsearch disk usage: $disk_usage%"
    
    log "SUCCESS" "Elasticsearch health check passed"
    return 0
}

# Function to check Milvus health
check_milvus_health() {
    local service_name="ai-karen-milvus"
    
    echo ""
    log "INFO" "Checking Milvus health..."
    
    # Check if container is running
    if ! docker ps | grep -q "$service_name"; then
        record_issue "$service_name" "Container not running"
        log "ERROR" "Milvus container is not running"
        return 1
    fi
    
    # Check Milvus connectivity using HTTP endpoint
    local host="${MILVUS_HOST:-localhost}"
    local port="${MILVUS_PORT:-9091}"
    
    # Try to check Milvus health via HTTP endpoint
    if docker exec "$service_name" curl -s "http://localhost:$port/healthz" | grep -q "OK"; then
        log "SUCCESS" "Milvus is responding"
        
        # Try to get more info if possible
        local milvus_info=$(docker exec "$service_name" curl -s "http://localhost:$port/healthz" 2>/dev/null || echo "OK")
        log "INFO" "Milvus health status: $milvus_info"
    else
        # Fallback to port check
        if nc -z "$host" "$port" 2>/dev/null; then
            log "SUCCESS" "Milvus port is accessible"
        else
            record_issue "$service_name" "Milvus not responding"
            log "ERROR" "Milvus health check failed"
            return 1
        fi
    fi
    
    log "SUCCESS" "Milvus health check passed"
    return 0
}

# Function to check DuckDB health
check_duckdb_health() {
    local service_name="duckdb"
    
    echo ""
    log "INFO" "Checking DuckDB health..."
    
    # DuckDB runs as a file-based database, check if file exists and is accessible
    local db_path="${DUCKDB_PATH:-./data/duckdb/kari_duckdb.db}"
    
    if [ -f "$db_path" ]; then
        log "SUCCESS" "DuckDB database file exists: $db_path"
        
        # Check file size
        local file_size=$(du -h "$db_path" | cut -f1)
        log "INFO" "DuckDB file size: $file_size"
        
        # Check if we can query the database
        if command -v duckdb > /dev/null 2>&1; then
            local table_count=$(duckdb "$db_path" "SELECT COUNT(*) FROM information_schema.tables;" 2>/dev/null || echo "0")
            log "INFO" "DuckDB tables: $table_count"
            
            # Check database version
            local version=$(duckdb "$db_path" "SELECT version();" 2>/dev/null | head -n1 || echo "unknown")
            log "INFO" "DuckDB version: $version"
        else
            log "WARN" "DuckDB CLI not available, skipping detailed checks"
        fi
    else
        log "WARN" "DuckDB database file not found: $db_path"
        log "INFO" "This is normal if DuckDB hasn't been initialized yet"
    fi
    
    log "SUCCESS" "DuckDB health check passed"
    return 0
}

# Function to check MinIO health (if present)
check_minio_health() {
    local service_name="ai-karen-minio"
    
    echo ""
    log "INFO" "Checking MinIO health..."
    
    # Check if MinIO container is running
    if ! docker ps | grep -q "$service_name" 2>/dev/null; then
        log "INFO" "MinIO container not found or not running (optional service)"
        return 0
    fi
    
    # Check MinIO API
    local host="${MINIO_HOST:-localhost}"
    local port="${MINIO_PORT:-9000}"
    
    if curl -s -f "http://$host:$port/minio/health/live" > /dev/null; then
        log "SUCCESS" "MinIO is responding"
    else
        record_issue "$service_name" "MinIO not responding"
        log "ERROR" "MinIO is not responding"
        return 1
    fi
    
    log "SUCCESS" "MinIO health check passed"
    return 0
}

# Function to check etcd health (if present)
check_etcd_health() {
    local service_name="ai-karen-milvus-etcd"
    
    echo ""
    log "INFO" "Checking etcd health..."
    
    # Check if etcd container is running
    if ! docker ps | grep -q "$service_name" 2>/dev/null; then
        log "INFO" "etcd container not found or not running (optional service)"
        return 0
    fi
    
    # Check etcd health endpoint
    local host="${ETCD_HOST:-localhost}"
    local port="${ETCD_PORT:-2379}"
    
    if docker exec "$service_name" etcdctl endpoint health | grep -q "is healthy"; then
        log "SUCCESS" "etcd is healthy"
    else
        record_issue "$service_name" "etcd not healthy"
        log "ERROR" "etcd is not healthy"
        return 1
    fi
    
    log "SUCCESS" "etcd health check passed"
    return 0
}

# Function to check overall system resources
check_system_resources() {
    echo ""
    log "INFO" "Checking system resources..."
    
    # Check disk space
    local disk_usage=$(df -h . | tail -n1 | awk '{print $5}' | tr -d '%')
    if [ "$disk_usage" -gt 90 ]; then
        record_issue "system" "Disk usage is high: ${disk_usage}%"
        log "ERROR" "Disk usage is critically high: ${disk_usage}%"
    elif [ "$disk_usage" -gt 80 ]; then
        log "WARN" "Disk usage is high: ${disk_usage}%"
    else
        log "SUCCESS" "Disk usage is acceptable: ${disk_usage}%"
    fi
    
    # Check memory usage
    if command -v free > /dev/null 2>&1; then
        local mem_usage=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100.0}')
        if [ "$mem_usage" -gt 90 ]; then
            record_issue "system" "Memory usage is high: ${mem_usage}%"
            log "ERROR" "Memory usage is critically high: ${mem_usage}%"
        elif [ "$mem_usage" -gt 80 ]; then
            log "WARN" "Memory usage is high: ${mem_usage}%"
        else
            log "SUCCESS" "Memory usage is acceptable: ${mem_usage}%"
        fi
    fi
    
    # Check Docker daemon
    if docker system df > /dev/null 2>&1; then
        log "SUCCESS" "Docker daemon is responsive"
    else
        record_issue "system" "Docker daemon not responsive"
        log "ERROR" "Docker daemon is not responsive"
    fi
}

# Function to generate health report
generate_health_report() {
    echo ""
    echo "==========================================="
    echo "AI Karen Database Stack Health Report"
    echo "Generated: $(date)"
    echo "==========================================="
    
    if [ "$OVERALL_HEALTH" = "healthy" ]; then
        log "SUCCESS" "Overall Status: HEALTHY ✅"
    else
        log "ERROR" "Overall Status: UNHEALTHY ❌"
        
        echo ""
        log "ERROR" "Issues found:"
        for issue in "${HEALTH_ISSUES[@]}"; do
            echo "  - $issue"
        done
    fi
    
    echo ""
    echo "Service Status Summary:"
    docker ps | grep -E "(ai-karen-postgres|ai-karen-redis|ai-karen-elasticsearch|ai-karen-milvus|ai-karen-minio|ai-karen-milvus-etcd)"
    
    echo ""
    echo "For detailed logs, run:"
    echo "  docker-compose logs [service_name]"
    echo ""
    echo "To restart services, run:"
    echo "  ./scripts/restart.sh"
}

# Function to show usage information
show_usage() {
    echo "AI Karen Database Stack Health Check Script"
    echo ""
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  --service <name>  Check only specific service"
    echo "  --quick          Quick check (skip detailed tests)"
    echo "  --json           Output results in JSON format"
    echo "  --help           Show this help message"
    echo ""
    echo "Services: postgres, redis, elasticsearch, milvus, duckdb, minio, etcd"
    echo ""
    echo "Examples:"
    echo "  $0                      # Check all services"
    echo "  $0 --service postgres   # Check only PostgreSQL"
    echo "  $0 --quick              # Quick health check"
}

# Main function
main() {
    local specific_service=""
    local quick_check="false"
    local json_output="false"
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --service)
                specific_service="$2"
                shift 2
                ;;
            --quick)
                quick_check="true"
                shift
                ;;
            --json)
                json_output="true"
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
    
    # Check Docker Compose availability
    check_docker_compose
    
    # Install required tools
    log "INFO" "Installing required tools..."
    if command -v apk > /dev/null 2>&1; then
        apk add --no-cache curl postgresql-client redis jq netcat-openbsd > /dev/null 2>&1 || true
    elif command -v apt-get > /dev/null 2>&1; then
        apt-get update > /dev/null 2>&1 && apt-get install -y curl postgresql-client redis-tools jq netcat > /dev/null 2>&1 || true
    fi
    
    # Run health checks
    if [ -n "$specific_service" ]; then
        case "$specific_service" in
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
            "duckdb")
                check_duckdb_health
                ;;
            "minio")
                check_minio_health
                ;;
            "etcd")
                check_etcd_health
                ;;
            *)
                log "ERROR" "Unknown service: $specific_service"
                exit 1
                ;;
        esac
    else
        # Check all services
        check_postgres_health || true
        check_redis_health || true
        check_elasticsearch_health || true
        check_milvus_health || true
        check_duckdb_health || true
        check_minio_health || true
        check_etcd_health || true
        
        if [ "$quick_check" = "false" ]; then
            check_system_resources
        fi
    fi
    
    # Generate report
    if [ "$json_output" = "true" ]; then
        # TODO: Implement JSON output format
        log "WARN" "JSON output not yet implemented, using text format"
    fi
    
    generate_health_report
    
    # Exit with appropriate code
    if [ "$OVERALL_HEALTH" = "healthy" ]; then
        exit 0
    else
        exit 1
    fi
}

# Change to script directory
cd "$(dirname "$0")/.."

# Run main function with all arguments
main "$@"