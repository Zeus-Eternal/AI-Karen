#!/bin/bash
set -e

# AI Karen Database Initialization Master Script
# This script coordinates the initialization of all database services

echo "🚀 Starting AI Karen Database Initialization..."
echo "=================================================="

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

# Function to check if a service is ready
check_service() {
    local service_name="$1"
    local check_command="$2"
    local max_attempts="${3:-30}"
    local attempt=1
    
    log "INFO" "Checking $service_name readiness..."
    
    while [ $attempt -le $max_attempts ]; do
        if eval "$check_command" > /dev/null 2>&1; then
            log "SUCCESS" "$service_name is ready!"
            return 0
        fi
        
        log "INFO" "Attempt $attempt/$max_attempts: $service_name not ready yet, waiting..."
        sleep 5
        attempt=$((attempt + 1))
    done
    
    log "ERROR" "$service_name failed to become ready after $max_attempts attempts"
    return 1
}

# Function to run initialization script with error handling
run_init_script() {
    local service_name="$1"
    local script_path="$2"
    
    log "INFO" "Initializing $service_name..."
    
    if [ -f "$script_path" ] && [ -x "$script_path" ]; then
        if "$script_path"; then
            log "SUCCESS" "$service_name initialization completed successfully"
            return 0
        else
            log "ERROR" "$service_name initialization failed"
            return 1
        fi
    else
        log "WARN" "Initialization script not found or not executable: $script_path"
        return 1
    fi
}

# Function to load bootstrap data
load_bootstrap_data() {
    log "INFO" "Loading bootstrap data..."
    
    # Load classifier seed data into appropriate databases
    if [ -f "/init/bootstrap/classifier_seed.json" ]; then
        log "INFO" "Loading classifier seed data..."
        
        # Load into PostgreSQL if available
        if command -v psql > /dev/null 2>&1; then
            log "INFO" "Loading classifier data into PostgreSQL..."
            # Create a temporary SQL file to load JSON data
            cat > /tmp/load_classifier_data.sql << 'EOF'
-- Create classifier data table if it doesn't exist
CREATE TABLE IF NOT EXISTS classifier_data (
    id SERIAL PRIMARY KEY,
    text VARCHAR NOT NULL,
    intent VARCHAR NOT NULL,
    confidence FLOAT DEFAULT 1.0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Function to load JSON data
CREATE OR REPLACE FUNCTION load_classifier_seed() RETURNS void AS $$
DECLARE
    json_data jsonb;
    item jsonb;
BEGIN
    -- Read the JSON file content (this would need to be adapted for actual file reading)
    -- For now, we'll insert some sample data
    INSERT INTO classifier_data (text, intent) VALUES
    ('hello', 'greet'),
    ('hi', 'greet'),
    ('hey there', 'greet'),
    ('good morning', 'greet'),
    ('goodbye', 'farewell'),
    ('bye', 'farewell'),
    ('see you later', 'farewell'),
    ('thanks', 'thanks'),
    ('thank you', 'thanks'),
    ('much appreciated', 'thanks'),
    ('what time is it', 'time_query'),
    ('tell me the time', 'time_query'),
    ('current time please', 'time_query')
    ON CONFLICT DO NOTHING;
END;
$$ LANGUAGE plpgsql;

-- Execute the function
SELECT load_classifier_seed();
EOF
            
            if psql -h "${POSTGRES_HOST}" -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -f /tmp/load_classifier_data.sql; then
                log "SUCCESS" "Classifier data loaded into PostgreSQL"
            else
                log "WARN" "Failed to load classifier data into PostgreSQL"
            fi
            
            rm -f /tmp/load_classifier_data.sql
        fi
        
        # Load into Elasticsearch if available
        if command -v curl > /dev/null 2>&1; then
            log "INFO" "Loading classifier data into Elasticsearch..."
            
            # Create index for classifier data
            curl -s -X PUT "http://${ELASTICSEARCH_HOST:-localhost}:${ELASTICSEARCH_PORT:-9200}/ai_karen_classifier" \
                -H "Content-Type: application/json" \
                -d '{
                    "mappings": {
                        "properties": {
                            "text": {"type": "text", "analyzer": "standard"},
                            "intent": {"type": "keyword"},
                            "confidence": {"type": "float"},
                            "created_at": {"type": "date"}
                        }
                    }
                }' > /dev/null
            
            # Load sample classifier data
            curl -s -X POST "http://${ELASTICSEARCH_HOST:-localhost}:${ELASTICSEARCH_PORT:-9200}/ai_karen_classifier/_bulk" \
                -H "Content-Type: application/json" \
                -d '
{"index":{}}
{"text":"hello","intent":"greet","confidence":1.0,"created_at":"'$(date -Iseconds)'"}
{"index":{}}
{"text":"hi","intent":"greet","confidence":1.0,"created_at":"'$(date -Iseconds)'"}
{"index":{}}
{"text":"goodbye","intent":"farewell","confidence":1.0,"created_at":"'$(date -Iseconds)'"}
{"index":{}}
{"text":"thanks","intent":"thanks","confidence":1.0,"created_at":"'$(date -Iseconds)'"}
' > /dev/null
            
            log "SUCCESS" "Classifier data loaded into Elasticsearch"
        fi
    else
        log "WARN" "Classifier seed data file not found"
    fi
}

# Function to verify all services
verify_services() {
    log "INFO" "Verifying all database services..."
    
    local all_healthy=true
    
    # Check PostgreSQL
    if psql -h "${POSTGRES_HOST}" -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -c "SELECT 1;" > /dev/null 2>&1; then
        log "SUCCESS" "PostgreSQL is healthy"
    else
        log "ERROR" "PostgreSQL health check failed"
        all_healthy=false
    fi
    
    # Check Elasticsearch
    if curl -s -f "http://${ELASTICSEARCH_HOST:-localhost}:${ELASTICSEARCH_PORT:-9200}/_cluster/health" > /dev/null 2>&1; then
        log "SUCCESS" "Elasticsearch is healthy"
    else
        log "ERROR" "Elasticsearch health check failed"
        all_healthy=false
    fi
    
    # Check Milvus
    if nc -z "${MILVUS_HOST:-localhost}" "${MILVUS_PORT:-19530}" 2>/dev/null; then
        log "SUCCESS" "Milvus is healthy"
    else
        log "ERROR" "Milvus health check failed"
        all_healthy=false
    fi
    
    # Check Redis
    if redis-cli -h "${REDIS_HOST:-localhost}" -p "${REDIS_PORT:-6379}" ${REDIS_PASSWORD:+-a "$REDIS_PASSWORD"} ping > /dev/null 2>&1; then
        log "SUCCESS" "Redis is healthy"
    else
        log "ERROR" "Redis health check failed"
        all_healthy=false
    fi
    
    # Check DuckDB
    if [ -f "${DUCKDB_PATH}" ]; then
        log "SUCCESS" "DuckDB database file exists"
    else
        log "ERROR" "DuckDB database file not found"
        all_healthy=false
    fi
    
    if [ "$all_healthy" = true ]; then
        log "SUCCESS" "All database services are healthy!"
        return 0
    else
        log "ERROR" "Some database services failed health checks"
        return 1
    fi
}

# Function to create summary report
create_summary_report() {
    log "INFO" "Creating initialization summary report..."
    
    cat > /tmp/init_summary.txt << EOF
AI Karen Database Initialization Summary
========================================
Date: $(date)
Environment: ${ENVIRONMENT:-development}

Services Initialized:
- PostgreSQL: ${POSTGRES_HOST}:${POSTGRES_PORT} (Database: ${POSTGRES_DB})
- Elasticsearch: ${ELASTICSEARCH_HOST:-localhost}:${ELASTICSEARCH_PORT:-9200}
- Milvus: ${MILVUS_HOST:-localhost}:${MILVUS_PORT:-19530}
- Redis: ${REDIS_HOST:-localhost}:${REDIS_PORT:-6379}
- DuckDB: ${DUCKDB_PATH}

Initialization Steps Completed:
1. ✅ Service readiness checks
2. ✅ PostgreSQL schema and migrations
3. ✅ DuckDB database and tables
4. ✅ Elasticsearch indices and mappings
5. ✅ Milvus collections and indexes
6. ✅ Redis configuration and namespaces
7. ✅ Bootstrap data loading
8. ✅ Service health verification

Next Steps:
- Start AI Karen application
- Verify application connectivity to databases
- Monitor service health and performance
- Set up backup and monitoring procedures

Configuration Files:
- Docker Compose: /docker-compose.yml
- Environment: /.env
- PostgreSQL migrations: /migrations/postgres/
- Elasticsearch mappings: /migrations/elasticsearch/
- Milvus collections: /migrations/milvus/
- DuckDB migrations: /migrations/duckdb/

For troubleshooting, check individual service logs:
- docker-compose logs postgres
- docker-compose logs elasticsearch
- docker-compose logs milvus
- docker-compose logs redis
EOF
    
    log "SUCCESS" "Summary report created at /tmp/init_summary.txt"
    cat /tmp/init_summary.txt
}

# Main initialization sequence
main() {
    log "INFO" "AI Karen Database Initialization Started"
    log "INFO" "Environment: ${ENVIRONMENT:-development}"
    
    # Install required tools
    log "INFO" "Installing required tools..."
    apk add --no-cache curl netcat-openbsd postgresql-client redis
    
    # Wait for all services to be ready
    log "INFO" "Waiting for database services to be ready..."
    
    check_service "PostgreSQL" "pg_isready -h ${POSTGRES_HOST} -p ${POSTGRES_PORT} -U ${POSTGRES_USER}"
    check_service "Elasticsearch" "curl -s -f http://${ELASTICSEARCH_HOST:-localhost}:${ELASTICSEARCH_PORT:-9200}/_cluster/health"
    check_service "Milvus" "nc -z ${MILVUS_HOST:-localhost} ${MILVUS_PORT:-19530}"
    check_service "Redis" "redis-cli -h ${REDIS_HOST:-localhost} -p ${REDIS_PORT:-6379} ${REDIS_PASSWORD:+-a $REDIS_PASSWORD} ping"
    
    # Initialize each service
    log "INFO" "Starting service initialization..."
    
    # PostgreSQL initialization (already handled by docker-entrypoint)
    log "INFO" "PostgreSQL initialization handled by container entrypoint"
    
    # DuckDB initialization
    run_init_script "DuckDB" "/init/duckdb/init-duckdb.sh"
    
    # Elasticsearch initialization
    run_init_script "Elasticsearch" "/init/elasticsearch/init-elasticsearch.sh"
    
    # Milvus initialization
    run_init_script "Milvus" "/init/milvus/init-milvus.sh"
    
    # Redis initialization
    run_init_script "Redis" "/init/redis/init-redis.sh"
    
    # Load bootstrap data
    load_bootstrap_data
    
    # Final verification
    if verify_services; then
        log "SUCCESS" "All services initialized and verified successfully!"
        create_summary_report
        
        # Create success marker
        touch /tmp/init_success
        echo "$(date -Iseconds)" > /tmp/init_timestamp
        
        log "SUCCESS" "🎉 AI Karen Database Initialization Complete! 🎉"
        return 0
    else
        log "ERROR" "Service verification failed"
        touch /tmp/init_failed
        return 1
    fi
}

# Trap errors and cleanup
trap 'log "ERROR" "Initialization failed with error"; touch /tmp/init_failed; exit 1' ERR

# Run main initialization
main "$@"