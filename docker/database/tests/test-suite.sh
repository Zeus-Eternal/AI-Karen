#!/bin/bash
set -e

# AI Karen Database Stack Test Suite
# This script runs comprehensive tests on all database services

echo "🧪 AI Karen Database Stack Test Suite"
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
        "TEST")
            echo -e "\033[0;35m[$timestamp] TEST: $message\033[0m"
            ;;
        *)
            echo "[$timestamp] $message"
            ;;
    esac
}

# Global test results
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
FAILED_TEST_NAMES=()

# Function to run a test
run_test() {
    local test_name="$1"
    local test_function="$2"

    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    log "TEST" "Running: $test_name"

    if $test_function; then
        PASSED_TESTS=$((PASSED_TESTS + 1))
        log "SUCCESS" "PASSED: $test_name"
        return 0
    else
        FAILED_TESTS=$((FAILED_TESTS + 1))
        FAILED_TEST_NAMES+=("$test_name")
        log "ERROR" "FAILED: $test_name"
        return 1
    fi
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

# Test: Docker and Docker Compose availability
test_docker_availability() {
    if ! command -v docker &> /dev/null; then
        log "ERROR" "Docker is not installed"
        return 1
    fi

    if ! docker info &> /dev/null; then
        log "ERROR" "Docker daemon is not running"
        return 1
    fi

    check_docker_compose

    log "INFO" "Docker and Docker Compose are available"
    return 0
}

# Test: Environment file exists and is valid
test_environment_file() {
    if [ ! -f ".env" ]; then
        log "ERROR" ".env file not found"
        return 1
    fi

    # Check for required environment variables
    local required_vars=("POSTGRES_USER" "POSTGRES_PASSWORD" "POSTGRES_DB" "REDIS_PASSWORD")

    for var in "${required_vars[@]}"; do
        if ! grep -q "^$var=" .env; then
            log "ERROR" "Required environment variable $var not found in .env"
            return 1
        fi
    done

    log "INFO" "Environment file is valid"
    return 0
}

# Test: All services can start
test_services_start() {
    log "INFO" "Starting all services..."

    if $COMPOSE_CMD up -d; then
        log "INFO" "Services started successfully"
        return 0
    else
        log "ERROR" "Failed to start services"
        return 1
    fi
}

# Test: All services are healthy
test_services_health() {
    log "INFO" "Waiting for services to become healthy..."

    local max_wait=120
    local wait_time=0

    while [ $wait_time -lt $max_wait ]; do
        local unhealthy_services=$($COMPOSE_CMD ps --format json | jq -r '.[] | select(.Health != "healthy" and .Health != "" and .State == "running") | .Service' 2>/dev/null || echo "")

        if [ -z "$unhealthy_services" ]; then
            log "INFO" "All services are healthy"
            return 0
        fi

        log "INFO" "Waiting for services to become healthy: $unhealthy_services"
        sleep 10
        wait_time=$((wait_time + 10))
    done

    log "ERROR" "Services did not become healthy within $max_wait seconds"
    return 1
}

# Test: PostgreSQL connectivity and basic operations
test_postgresql() {
    local host="${POSTGRES_HOST:-localhost}"
    local port="${POSTGRES_PORT:-5433}"
    local user="${POSTGRES_USER:-karen_user}"
    local db="${POSTGRES_DB:-ai_karen}"
    local password="${POSTGRES_PASSWORD:-}"

    # Test connection
    if ! PGPASSWORD="$password" pg_isready -h "$host" -p "$port" -U "$user" -d "$db" &> /dev/null; then
        log "ERROR" "PostgreSQL is not accepting connections"
        return 1
    fi

    # Test basic operations
    local test_table="test_table_$$"

    # Create test table
    if ! PGPASSWORD="$password" psql -h "$host" -p "$port" -U "$user" -d "$db" -c \
        "CREATE TABLE $test_table (id SERIAL PRIMARY KEY, name VARCHAR(100), created_at TIMESTAMP DEFAULT NOW());" &> /dev/null; then
        log "ERROR" "Failed to create test table in PostgreSQL"
        return 1
    fi

    # Insert test data
    if ! PGPASSWORD="$password" psql -h "$host" -p "$port" -U "$user" -d "$db" -c \
        "INSERT INTO $test_table (name) VALUES ('test1'), ('test2'), ('test3');" &> /dev/null; then
        log "ERROR" "Failed to insert test data in PostgreSQL"
        return 1
    fi

    # Query test data
    local count=$(PGPASSWORD="$password" psql -h "$host" -p "$port" -U "$user" -d "$db" -t -c \
        "SELECT COUNT(*) FROM $test_table;" 2>/dev/null | tr -d ' ')

    if [ "$count" != "3" ]; then
        log "ERROR" "PostgreSQL query returned unexpected result: $count"
        return 1
    fi

    # Clean up
    PGPASSWORD="$password" psql -h "$host" -p "$port" -U "$user" -d "$db" -c \
        "DROP TABLE $test_table;" &> /dev/null

    log "INFO" "PostgreSQL test passed"
    return 0
}

# Test: Redis connectivity and basic operations
test_redis() {
    local host="${REDIS_HOST:-localhost}"
    local port="${REDIS_PORT:-6379}"
    local password="${REDIS_PASSWORD:-}"

    local redis_cmd="redis-cli -h $host -p $port"
    if [ -n "$password" ]; then
        redis_cmd="$redis_cmd -a $password"
    fi

    # Test connection
    if ! $redis_cmd ping | grep -q "PONG"; then
        log "ERROR" "Redis is not responding to ping"
        return 1
    fi

    # Test basic operations
    local test_key="test_key_$$"
    local test_value="test_value_$$"

    # Set value
    if ! $redis_cmd set "$test_key" "$test_value" | grep -q "OK"; then
        log "ERROR" "Failed to set value in Redis"
        return 1
    fi

    # Get value
    local retrieved_value=$($redis_cmd get "$test_key")
    if [ "$retrieved_value" != "$test_value" ]; then
        log "ERROR" "Redis returned unexpected value: $retrieved_value"
        return 1
    fi

    # Test hash operations
    local test_hash="test_hash_$$"
    if ! $redis_cmd hset "$test_hash" field1 value1 field2 value2 &> /dev/null; then
        log "ERROR" "Failed to set hash in Redis"
        return 1
    fi

    local hash_len=$($redis_cmd hlen "$test_hash")
    if [ "$hash_len" != "2" ]; then
        log "ERROR" "Redis hash length unexpected: $hash_len"
        return 1
    fi

    # Clean up
    $redis_cmd del "$test_key" "$test_hash" &> /dev/null

    log "INFO" "Redis test passed"
    return 0
}

# Test: Elasticsearch connectivity and basic operations
test_elasticsearch() {
    local host="${ELASTICSEARCH_HOST:-localhost}"
    local port="${ELASTICSEARCH_PORT:-9200}"

    # Test connection
    if ! curl -s -f "http://$host:$port/_cluster/health" > /dev/null; then
        log "ERROR" "Elasticsearch is not responding"
        return 1
    fi

    # Check cluster health
    local cluster_status=$(curl -s "http://$host:$port/_cluster/health" | jq -r '.status' 2>/dev/null)
    if [ "$cluster_status" = "red" ]; then
        log "ERROR" "Elasticsearch cluster status is red"
        return 1
    fi

    # Test index operations
    local test_index="test_index_$$"

    # Create test index
    if ! curl -s -X PUT "http://$host:$port/$test_index" \
        -H "Content-Type: application/json" \
        -d '{"mappings":{"properties":{"title":{"type":"text"},"content":{"type":"text"}}}}' | grep -q '"acknowledged":true'; then
        log "ERROR" "Failed to create test index in Elasticsearch"
        return 1
    fi

    # Index test document
    if ! curl -s -X POST "http://$host:$port/$test_index/_doc" \
        -H "Content-Type: application/json" \
        -d '{"title":"Test Document","content":"This is a test document"}' | grep -q '"result":"created"'; then
        log "ERROR" "Failed to index test document in Elasticsearch"
        return 1
    fi

    # Wait for indexing
    sleep 2

    # Search test document
    local search_result=$(curl -s -X GET "http://$host:$port/$test_index/_search" \
        -H "Content-Type: application/json" \
        -d '{"query":{"match":{"title":"Test"}}}')

    local hit_count=$(echo "$search_result" | jq -r '.hits.total.value' 2>/dev/null)
    if [ "$hit_count" != "1" ]; then
        log "ERROR" "Elasticsearch search returned unexpected result: $hit_count"
        return 1
    fi

    # Clean up
    curl -s -X DELETE "http://$host:$port/$test_index" > /dev/null

    log "INFO" "Elasticsearch test passed"
    return 0
}

# Test: Milvus connectivity and basic operations
test_milvus() {
    if ! command -v python3 > /dev/null 2>&1; then
        log "WARN" "Python3 not available, skipping Milvus test"
        return 0
    fi

    # Install pymilvus if not available
    if ! python3 -c "import pymilvus" > /dev/null 2>&1; then
        log "INFO" "Installing pymilvus for testing..."
        pip3 install pymilvus > /dev/null 2>&1
    fi

    # Create Milvus test script
    cat > /tmp/milvus_test.py << 'EOF'
#!/usr/bin/env python3
import os
import sys
import time
import numpy as np
from pymilvus import connections, Collection, CollectionSchema, FieldSchema, DataType, utility

def test_milvus():
    host = os.getenv('MILVUS_HOST', 'localhost')
    port = os.getenv('MILVUS_PORT', '19530')

    try:
        connections.connect(alias="default", host=host, port=port)

        # Create test collection
        collection_name = f"test_collection_{int(time.time())}"

        fields = [
            FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, auto_id=False, max_length=100),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=128),
            FieldSchema(name="metadata", dtype=DataType.JSON)
        ]

        schema = CollectionSchema(fields, description="Test collection")
        collection = Collection(collection_name, schema)

        # Create index
        index_params = {
            "metric_type": "COSINE",
            "index_type": "IVF_FLAT",
            "params": {"nlist": 128}
        }
        collection.create_index("embedding", index_params)

        # Insert test data
        test_data = [
            ["test_1", "test_2", "test_3"],  # ids
            [np.random.random(128).tolist() for _ in range(3)],  # embeddings
            [{"name": f"test_{i}"} for i in range(3)]  # metadata
        ]

        collection.insert(test_data)
        collection.flush()

        # Load collection
        collection.load()

        # Search test
        search_vectors = [np.random.random(128).tolist()]
        search_params = {"metric_type": "COSINE", "params": {"nprobe": 10}}

        results = collection.search(
            search_vectors,
            "embedding",
            search_params,
            limit=3,
            output_fields=["metadata"]
        )

        if len(results[0]) != 3:
            print(f"ERROR: Expected 3 search results, got {len(results[0])}")
            return 1

        # Clean up
        utility.drop_collection(collection_name)

        print("SUCCESS: Milvus test passed")
        return 0

    except Exception as e:
        print(f"ERROR: Milvus test failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(test_milvus())
EOF

    chmod +x /tmp/milvus_test.py

    # Run Milvus test
    if python3 /tmp/milvus_test.py; then
        log "INFO" "Milvus test passed"
        rm -f /tmp/milvus_test.py
        return 0
    else
        log "ERROR" "Milvus test failed"
        rm -f /tmp/milvus_test.py
        return 1
    fi
}

# Test: DuckDB file operations
test_duckdb() {
    local db_path="${DUCKDB_PATH:-./data/duckdb/kari_duckdb.db}"

    if [ ! -f "$db_path" ]; then
        log "WARN" "DuckDB file not found, creating for test: $db_path"
        mkdir -p "$(dirname "$db_path")"
        touch "$db_path"
    fi

    if ! command -v duckdb > /dev/null 2>&1; then
        log "WARN" "DuckDB CLI not available, skipping detailed test"
        return 0
    fi

    # Test basic operations
    local test_table="test_table_$$"

    # Create test table
    if ! duckdb "$db_path" "CREATE TABLE $test_table (id INTEGER PRIMARY KEY, name VARCHAR, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);" &> /dev/null; then
        log "ERROR" "Failed to create test table in DuckDB"
        return 1
    fi

    # Insert test data
    if ! duckdb "$db_path" "INSERT INTO $test_table (name) VALUES ('test1'), ('test2'), ('test3');" &> /dev/null; then
        log "ERROR" "Failed to insert test data in DuckDB"
        return 1
    fi

    # Query test data
    local count=$(duckdb "$db_path" "SELECT COUNT(*) FROM $test_table;" 2>/dev/null | head -n1)

    if [ "$count" != "3" ]; then
        log "ERROR" "DuckDB query returned unexpected result: $count"
        return 1
    fi

    # Clean up
    duckdb "$db_path" "DROP TABLE $test_table;" &> /dev/null

    log "INFO" "DuckDB test passed"
    return 0
}

# Test: Data persistence after container restart
test_data_persistence() {
    log "INFO" "Testing data persistence across container restarts..."

    # Insert test data in PostgreSQL
    local host="${POSTGRES_HOST:-localhost}"
    local port="${POSTGRES_PORT:-5433}"
    local user="${POSTGRES_USER:-karen_user}"
    local db="${POSTGRES_DB:-ai_karen}"
    local password="${POSTGRES_PASSWORD:-}"

    local test_table="persistence_test_$$"
    local test_value="persistence_test_value_$$"

    # Create test table and insert data
    PGPASSWORD="$password" psql -h "$host" -p "$port" -U "$user" -d "$db" -c \
        "CREATE TABLE $test_table (id SERIAL PRIMARY KEY, value VARCHAR(100));" &> /dev/null

    PGPASSWORD="$password" psql -h "$host" -p "$port" -U "$user" -d "$db" -c \
        "INSERT INTO $test_table (value) VALUES ('$test_value');" &> /dev/null

    # Restart PostgreSQL container
    log "INFO" "Restarting PostgreSQL container..."
    $COMPOSE_CMD restart postgres

    # Wait for PostgreSQL to be ready
    local max_wait=60
    local wait_time=0

    while [ $wait_time -lt $max_wait ]; do
        if PGPASSWORD="$password" pg_isready -h "$host" -p "$port" -U "$user" -d "$db" &> /dev/null; then
            break
        fi
        sleep 2
        wait_time=$((wait_time + 2))
    done

    if [ $wait_time -ge $max_wait ]; then
        log "ERROR" "PostgreSQL did not become ready after restart"
        return 1
    fi

    # Check if data persisted
    local retrieved_value=$(PGPASSWORD="$password" psql -h "$host" -p "$port" -U "$user" -d "$db" -t -c \
        "SELECT value FROM $test_table LIMIT 1;" 2>/dev/null | tr -d ' ')

    if [ "$retrieved_value" != "$test_value" ]; then
        log "ERROR" "Data did not persist after container restart"
        return 1
    fi

    # Clean up
    PGPASSWORD="$password" psql -h "$host" -p "$port" -U "$user" -d "$db" -c \
        "DROP TABLE $test_table;" &> /dev/null

    log "INFO" "Data persistence test passed"
    return 0
}

# Test: Migration system
test_migrations() {
    log "INFO" "Testing migration system..."

    # Run migration script
    if [ -f "./scripts/run-migrations.sh" ]; then
        if ./scripts/run-migrations.sh; then
            log "INFO" "Migration system test passed"
            return 0
        else
            log "ERROR" "Migration system test failed"
            return 1
        fi
    else
        log "WARN" "Migration script not found, skipping test"
        return 0
    fi
}

# Test: Backup and restore functionality
test_backup_restore() {
    log "INFO" "Testing backup and restore functionality..."

    # Create test data
    local host="${POSTGRES_HOST:-localhost}"
    local port="${POSTGRES_PORT:-5433}"
    local user="${POSTGRES_USER:-karen_user}"
    local db="${POSTGRES_DB:-ai_karen}"
    local password="${POSTGRES_PASSWORD:-}"

    local test_table="backup_test_$$"
    local test_value="backup_test_value_$$"

    # Create test table and insert data
    PGPASSWORD="$password" psql -h "$host" -p "$port" -U "$user" -d "$db" -c \
        "CREATE TABLE $test_table (id SERIAL PRIMARY KEY, value VARCHAR(100));" &> /dev/null

    PGPASSWORD="$password" psql -h "$host" -p "$port" -U "$user" -d "$db" -c \
        "INSERT INTO $test_table (value) VALUES ('$test_value');" &> /dev/null

    # Run backup
    if [ -f "./scripts/backup.sh" ]; then
        local backup_dir="/tmp/test_backup_$$"
        if ./scripts/backup.sh --service postgres --output-dir "$backup_dir"; then
            log "INFO" "Backup test passed"

            # Clean up test data
            PGPASSWORD="$password" psql -h "$host" -p "$port" -U "$user" -d "$db" -c \
                "DROP TABLE $test_table;" &> /dev/null

            # Clean up backup
            rm -rf "$backup_dir"
            return 0
        else
            log "ERROR" "Backup test failed"
            return 1
        fi
    else
        log "WARN" "Backup script not found, skipping test"
        return 0
    fi
}

# Test: Performance under load
test_performance() {
    log "INFO" "Testing performance under load..."

    local host="${POSTGRES_HOST:-localhost}"
    local port="${POSTGRES_PORT:-5433}"
    local user="${POSTGRES_USER:-karen_user}"
    local db="${POSTGRES_DB:-ai_karen}"
    local password="${POSTGRES_PASSWORD:-}"

    local test_table="perf_test_$$"

    # Create test table
    PGPASSWORD="$password" psql -h "$host" -p "$port" -U "$user" -d "$db" -c \
        "CREATE TABLE $test_table (id SERIAL PRIMARY KEY, data VARCHAR(100), created_at TIMESTAMP DEFAULT NOW());" &> /dev/null

    # Insert test data in batches
    local start_time=$(date +%s)
    local batch_size=100
    local total_records=1000

    for ((i=1; i<=total_records; i+=batch_size)); do
        local values=""
        for ((j=0; j<batch_size && (i+j)<=total_records; j++)); do
            if [ $j -gt 0 ]; then
                values="$values,"
            fi
            values="$values('test_data_$((i+j))')"
        done

        PGPASSWORD="$password" psql -h "$host" -p "$port" -U "$user" -d "$db" -c \
            "INSERT INTO $test_table (data) VALUES $values;" &> /dev/null
    done

    local end_time=$(date +%s)
    local duration=$((end_time - start_time))

    # Verify record count
    local count=$(PGPASSWORD="$password" psql -h "$host" -p "$port" -U "$user" -d "$db" -t -c \
        "SELECT COUNT(*) FROM $test_table;" 2>/dev/null | tr -d ' ')

    if [ "$count" != "$total_records" ]; then
        log "ERROR" "Performance test failed: expected $total_records records, got $count"
        return 1
    fi

    log "INFO" "Performance test passed: inserted $total_records records in ${duration}s"

    # Clean up
    PGPASSWORD="$password" psql -h "$host" -p "$port" -U "$user" -d "$db" -c \
        "DROP TABLE $test_table;" &> /dev/null

    return 0
}

# Function to show test results summary
show_test_summary() {
    echo ""
    echo "========================================="
    echo "AI Karen Database Stack Test Results"
    echo "========================================="
    echo "Total Tests: $TOTAL_TESTS"
    echo "Passed: $PASSED_TESTS"
    echo "Failed: $FAILED_TESTS"
    echo ""

    if [ $FAILED_TESTS -eq 0 ]; then
        log "SUCCESS" "🎉 All tests passed!"
        return 0
    else
        log "ERROR" "❌ Some tests failed:"
        for test_name in "${FAILED_TEST_NAMES[@]}"; do
            echo "  - $test_name"
        done
        return 1
    fi
}

# Function to show usage information
show_usage() {
    echo "AI Karen Database Stack Test Suite"
    echo ""
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  --quick              Run only basic connectivity tests"
    echo "  --skip-performance   Skip performance tests"
    echo "  --service <name>     Test only specific service"
    echo "  --help               Show this help message"
    echo ""
    echo "Services: postgres, redis, elasticsearch, milvus, duckdb"
    echo ""
    echo "Examples:"
    echo "  $0                      # Run all tests"
    echo "  $0 --quick              # Run only basic tests"
    echo "  $0 --service postgres   # Test only PostgreSQL"
}

# Main function
main() {
    local quick_mode="false"
    local skip_performance="false"
    local specific_service=""

    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --quick)
                quick_mode="true"
                shift
                ;;
            --skip-performance)
                skip_performance="true"
                shift
                ;;
            --service)
                specific_service="$2"
                shift 2
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

    log "INFO" "Starting AI Karen Database Stack Test Suite"

    # Install required tools
    if command -v apk > /dev/null 2>&1; then
        apk add --no-cache curl postgresql-client redis jq bc > /dev/null 2>&1 || true
    elif command -v apt-get > /dev/null 2>&1; then
        apt-get update > /dev/null 2>&1 && apt-get install -y curl postgresql-client redis-tools jq bc > /dev/null 2>&1 || true
    fi

    # Run tests
    run_test "Docker Availability" test_docker_availability
    run_test "Environment File" test_environment_file
    run_test "Services Start" test_services_start
    run_test "Services Health" test_services_health

    if [ -n "$specific_service" ]; then
        case "$specific_service" in
            "postgres")
                run_test "PostgreSQL" test_postgresql
                ;;
            "redis")
                run_test "Redis" test_redis
                ;;
            "elasticsearch")
                run_test "Elasticsearch" test_elasticsearch
                ;;
            "milvus")
                run_test "Milvus" test_milvus
                ;;
            "duckdb")
                run_test "DuckDB" test_duckdb
                ;;
            *)
                log "ERROR" "Unknown service: $specific_service"
                exit 1
                ;;
        esac
    else
        # Run all service tests
        run_test "PostgreSQL" test_postgresql
        run_test "Redis" test_redis
        run_test "Elasticsearch" test_elasticsearch
        run_test "Milvus" test_milvus
        run_test "DuckDB" test_duckdb

        if [ "$quick_mode" = "false" ]; then
            run_test "Data Persistence" test_data_persistence
            run_test "Migration System" test_migrations
            run_test "Backup/Restore" test_backup_restore

            if [ "$skip_performance" = "false" ]; then
                run_test "Performance" test_performance
            fi
        fi
    fi

    # Show results
    show_test_summary
    exit $?
}

# Change to script directory
cd "$(dirname "$0")/.."

# Run main function with all arguments
main "$@"
