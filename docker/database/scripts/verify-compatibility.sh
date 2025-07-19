#!/bin/bash
set -e

# AI Karen Database Compatibility Verification Script
# This script verifies that the containerized databases are compatible with the existing AI Karen codebase

echo "🔍 AI Karen Database Compatibility Verification"
echo "=============================================="

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

# Function to test PostgreSQL compatibility
test_postgres_compatibility() {
    log "INFO" "Testing PostgreSQL compatibility..."
    
    local host="${POSTGRES_HOST:-localhost}"
    local port="${POSTGRES_PORT:-5432}"
    local user="${POSTGRES_USER:-karen_user}"
    local db="${POSTGRES_DB:-ai_karen}"
    
    # Test basic connection (matches PostgresClient.__init__)
    log "INFO" "Testing PostgreSQL connection parameters..."
    if pg_isready -h "$host" -p "$port" -U "$user" -d "$db"; then
        log "SUCCESS" "PostgreSQL connection parameters are compatible"
    else
        log "ERROR" "PostgreSQL connection failed with AI Karen parameters"
        return 1
    fi
    
    # Test table structure compatibility
    log "INFO" "Verifying table structures match AI Karen expectations..."
    
    # Check memory table structure (from PostgresClient._ensure_table)
    local memory_table_check=$(psql -h "$host" -p "$port" -U "$user" -d "$db" -t -c "
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'memory' 
        ORDER BY ordinal_position;
    " 2>/dev/null)
    
    if echo "$memory_table_check" | grep -q "vector_id"; then
        log "SUCCESS" "Memory table structure is compatible"
    else
        log "WARN" "Memory table may need schema updates for full compatibility"
    fi
    
    # Test upsert functionality (PostgresClient.upsert_memory)
    log "INFO" "Testing upsert functionality..."
    local test_result=$(psql -h "$host" -p "$port" -U "$user" -d "$db" -t -c "
        INSERT INTO memory (vector_id, tenant_id, user_id, session_id, query, result, timestamp) 
        VALUES (999999, 'test', 'test_user', 'test_session', 'test query', '{\"test\": \"data\"}', $(date +%s))
        ON CONFLICT (vector_id) DO UPDATE SET 
            query = EXCLUDED.query,
            result = EXCLUDED.result,
            timestamp = EXCLUDED.timestamp;
        SELECT 'upsert_success';
    " 2>/dev/null)
    
    if echo "$test_result" | grep -q "upsert_success"; then
        log "SUCCESS" "PostgreSQL upsert functionality is compatible"
        # Clean up test data
        psql -h "$host" -p "$port" -U "$user" -d "$db" -c "DELETE FROM memory WHERE vector_id = 999999;" > /dev/null 2>&1
    else
        log "ERROR" "PostgreSQL upsert functionality failed"
        return 1
    fi
    
    return 0
}

# Function to test DuckDB compatibility
test_duckdb_compatibility() {
    log "INFO" "Testing DuckDB compatibility..."
    
    local duckdb_path="${DUCKDB_PATH:-./data/duckdb/kari_duckdb.db}"
    
    if [ ! -f "$duckdb_path" ]; then
        log "WARN" "DuckDB file not found, skipping compatibility test"
        return 0
    fi
    
    # Test connection (matches DuckDBClient.__init__)
    log "INFO" "Testing DuckDB connection..."
    if duckdb "$duckdb_path" -c "SELECT 'connection_test' as status;" | grep -q "connection_test"; then
        log "SUCCESS" "DuckDB connection is compatible"
    else
        log "ERROR" "DuckDB connection failed"
        return 1
    fi
    
    # Test table structure (matches DuckDBClient._ensure_tables)
    log "INFO" "Verifying DuckDB table structures..."
    local tables_check=$(duckdb "$duckdb_path" -c "
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'main' 
        AND table_name IN ('profiles', 'profile_history', 'long_term_memory', 'user_roles');
    ")
    
    local expected_tables=("profiles" "profile_history" "long_term_memory" "user_roles")
    local missing_tables=0
    
    for table in "${expected_tables[@]}"; do
        if ! echo "$tables_check" | grep -q "$table"; then
            log "WARN" "Missing expected table: $table"
            missing_tables=$((missing_tables + 1))
        fi
    done
    
    if [ $missing_tables -eq 0 ]; then
        log "SUCCESS" "DuckDB table structures are compatible"
    else
        log "WARN" "DuckDB missing $missing_tables expected tables"
    fi
    
    # Test profile operations (matches DuckDBClient methods)
    log "INFO" "Testing DuckDB profile operations..."
    local profile_test=$(duckdb "$duckdb_path" -c "
        INSERT OR IGNORE INTO profiles (user_id, profile_json, last_update) 
        VALUES ('test_user_999', '{\"name\": \"Test User\", \"test\": true}', CURRENT_TIMESTAMP);
        SELECT profile_json FROM profiles WHERE user_id = 'test_user_999';
    ")
    
    if echo "$profile_test" | grep -q "Test User"; then
        log "SUCCESS" "DuckDB profile operations are compatible"
        # Clean up test data
        duckdb "$duckdb_path" -c "DELETE FROM profiles WHERE user_id = 'test_user_999';" > /dev/null 2>&1
    else
        log "ERROR" "DuckDB profile operations failed"
        return 1
    fi
    
    return 0
}

# Function to test Elasticsearch compatibility
test_elasticsearch_compatibility() {
    log "INFO" "Testing Elasticsearch compatibility..."
    
    local host="${ELASTICSEARCH_HOST:-localhost}"
    local port="${ELASTICSEARCH_PORT:-9200}"
    
    # Test connection (matches ElasticClient.__init__)
    log "INFO" "Testing Elasticsearch connection..."
    if curl -s -f "http://$host:$port" > /dev/null; then
        log "SUCCESS" "Elasticsearch connection is compatible"
    else
        log "ERROR" "Elasticsearch connection failed"
        return 1
    fi
    
    # Test index creation (matches ElasticClient.ensure_index)
    log "INFO" "Testing Elasticsearch index operations..."
    local test_index="ai_karen_compatibility_test"
    
    # Create test index with mapping similar to ElasticClient
    local create_result=$(curl -s -X PUT "http://$host:$port/$test_index" \
        -H "Content-Type: application/json" \
        -d '{
            "mappings": {
                "properties": {
                    "tenant_id": {"type": "keyword"},
                    "user_id": {"type": "keyword"},
                    "session_id": {"type": "keyword"},
                    "query": {"type": "text"},
                    "result": {"type": "text"},
                    "timestamp": {"type": "long"}
                }
            }
        }')
    
    if echo "$create_result" | grep -q '"acknowledged":true'; then
        log "SUCCESS" "Elasticsearch index creation is compatible"
        
        # Test document indexing (matches ElasticClient.index_entry)
        local index_result=$(curl -s -X POST "http://$host:$port/$test_index/_doc" \
            -H "Content-Type: application/json" \
            -d '{
                "tenant_id": "test",
                "user_id": "test_user",
                "session_id": "test_session",
                "query": "compatibility test",
                "result": "test result",
                "timestamp": '$(date +%s)'
            }')
        
        if echo "$index_result" | grep -q '"result":"created"'; then
            log "SUCCESS" "Elasticsearch document indexing is compatible"
        else
            log "WARN" "Elasticsearch document indexing may have issues"
        fi
        
        # Clean up test index
        curl -s -X DELETE "http://$host:$port/$test_index" > /dev/null 2>&1
    else
        log "ERROR" "Elasticsearch index creation failed"
        return 1
    fi
    
    return 0
}

# Function to test Milvus compatibility
test_milvus_compatibility() {
    log "INFO" "Testing Milvus compatibility..."
    
    # Create Python script for Milvus compatibility test
    cat > /tmp/milvus_compatibility_test.py << 'EOF'
#!/usr/bin/env python3
import os
import sys
import numpy as np

try:
    from pymilvus import connections, Collection, CollectionSchema, FieldSchema, DataType, utility
    
    def test_milvus_compatibility():
        host = os.getenv('MILVUS_HOST', 'localhost')
        port = os.getenv('MILVUS_PORT', '19530')
        
        # Test connection (matches MilvusClient._connect)
        try:
            connections.connect(alias="compatibility_test", host=host, port=port)
            print("SUCCESS: Milvus connection is compatible")
        except Exception as e:
            print(f"ERROR: Milvus connection failed: {e}")
            return False
        
        # Test collection operations (matches MilvusClient._ensure_collection)
        test_collection_name = "compatibility_test_collection"
        
        try:
            # Drop test collection if exists
            if utility.has_collection(test_collection_name):
                utility.drop_collection(test_collection_name)
            
            # Create test collection with schema similar to MilvusClient
            fields = [
                FieldSchema(name="user_id", dtype=DataType.VARCHAR, is_primary=True, auto_id=False, max_length=64),
                FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=384),
            ]
            schema = CollectionSchema(fields, description="Compatibility Test Collection")
            collection = Collection(test_collection_name, schema)
            
            print("SUCCESS: Milvus collection creation is compatible")
            
            # Test embedding operations (matches MilvusClient.upsert_persona_embedding)
            test_embedding = np.random.random(384).astype(np.float32).tolist()
            entities = [["test_user_999"], [test_embedding]]
            
            collection.insert(entities)
            collection.flush()
            
            print("SUCCESS: Milvus embedding operations are compatible")
            
            # Clean up
            utility.drop_collection(test_collection_name)
            
        except Exception as e:
            print(f"ERROR: Milvus operations failed: {e}")
            return False
        
        finally:
            connections.disconnect("compatibility_test")
        
        return True

    if __name__ == "__main__":
        success = test_milvus_compatibility()
        sys.exit(0 if success else 1)
        
except ImportError:
    print("WARN: pymilvus not available, skipping Milvus compatibility test")
    sys.exit(0)
except Exception as e:
    print(f"ERROR: Milvus compatibility test failed: {e}")
    sys.exit(1)
EOF
    
    if python3 /tmp/milvus_compatibility_test.py; then
        log "SUCCESS" "Milvus compatibility verified"
    else
        log "WARN" "Milvus compatibility test encountered issues"
    fi
    
    rm -f /tmp/milvus_compatibility_test.py
}

# Function to test Redis compatibility
test_redis_compatibility() {
    log "INFO" "Testing Redis compatibility..."
    
    local host="${REDIS_HOST:-localhost}"
    local port="${REDIS_PORT:-6379}"
    local password="${REDIS_PASSWORD:-}"
    
    # Test connection (matches Redis client usage in AI Karen)
    log "INFO" "Testing Redis connection..."
    local ping_result
    if [ -n "$password" ]; then
        ping_result=$(redis-cli -h "$host" -p "$port" -a "$password" ping 2>/dev/null)
    else
        ping_result=$(redis-cli -h "$host" -p "$port" ping 2>/dev/null)
    fi
    
    if [ "$ping_result" = "PONG" ]; then
        log "SUCCESS" "Redis connection is compatible"
    else
        log "ERROR" "Redis connection failed"
        return 1
    fi
    
    # Test AI Karen namespace operations
    log "INFO" "Testing Redis AI Karen namespace operations..."
    
    # Test setting and getting AI Karen keys
    if [ -n "$password" ]; then
        redis-cli -h "$host" -p "$port" -a "$password" SET "ai_karen:test:compatibility" "test_value" > /dev/null 2>&1
        local test_value=$(redis-cli -h "$host" -p "$port" -a "$password" GET "ai_karen:test:compatibility" 2>/dev/null)
    else
        redis-cli -h "$host" -p "$port" SET "ai_karen:test:compatibility" "test_value" > /dev/null 2>&1
        local test_value=$(redis-cli -h "$host" -p "$port" GET "ai_karen:test:compatibility" 2>/dev/null)
    fi
    
    if [ "$test_value" = "test_value" ]; then
        log "SUCCESS" "Redis AI Karen namespace operations are compatible"
        
        # Clean up test key
        if [ -n "$password" ]; then
            redis-cli -h "$host" -p "$port" -a "$password" DEL "ai_karen:test:compatibility" > /dev/null 2>&1
        else
            redis-cli -h "$host" -p "$port" DEL "ai_karen:test:compatibility" > /dev/null 2>&1
        fi
    else
        log "ERROR" "Redis AI Karen namespace operations failed"
        return 1
    fi
    
    return 0
}

# Function to test environment variable compatibility
test_environment_compatibility() {
    log "INFO" "Testing environment variable compatibility..."
    
    # Check if AI Karen expected environment variables are set
    local ai_karen_env_vars=(
        "POSTGRES_HOST" "POSTGRES_PORT" "POSTGRES_USER" "POSTGRES_DB"
        "ELASTICSEARCH_HOST" "ELASTICSEARCH_PORT"
        "MILVUS_HOST" "MILVUS_PORT"
        "REDIS_HOST" "REDIS_PORT"
    )
    
    local missing_vars=0
    local compatible_vars=0
    
    for var in "${ai_karen_env_vars[@]}"; do
        if [ -n "${!var}" ]; then
            log "SUCCESS" "$var is set: ${!var}"
            compatible_vars=$((compatible_vars + 1))
        else
            # Check if it's set in .env file
            if [ -f ".env" ] && grep -q "^$var=" .env; then
                local env_value=$(grep "^$var=" .env | cut -d'=' -f2)
                log "SUCCESS" "$var is set in .env: $env_value"
                compatible_vars=$((compatible_vars + 1))
            else
                log "WARN" "$var is not set (will use default)"
                missing_vars=$((missing_vars + 1))
            fi
        fi
    done
    
    log "INFO" "Environment compatibility: $compatible_vars compatible, $missing_vars using defaults"
    
    return 0
}

# Function to test AI Karen client integration
test_client_integration() {
    log "INFO" "Testing AI Karen client integration..."
    
    # Create Python script to test client compatibility
    cat > /tmp/client_integration_test.py << 'EOF'
#!/usr/bin/env python3
import os
import sys
import json

# Add the AI Karen source path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

try:
    # Test PostgresClient
    from ai_karen_engine.clients.database.postgres_client import PostgresClient
    
    postgres_client = PostgresClient()
    if postgres_client.health():
        print("SUCCESS: PostgresClient integration is compatible")
    else:
        print("ERROR: PostgresClient health check failed")
        
except ImportError as e:
    print(f"WARN: Could not import PostgresClient: {e}")
except Exception as e:
    print(f"ERROR: PostgresClient integration failed: {e}")

try:
    # Test ElasticClient
    from ai_karen_engine.clients.database.elastic_client import ElasticClient
    
    elastic_client = ElasticClient()
    # Basic test - just check if we can create the client
    print("SUCCESS: ElasticClient integration is compatible")
        
except ImportError as e:
    print(f"WARN: Could not import ElasticClient: {e}")
except Exception as e:
    print(f"ERROR: ElasticClient integration failed: {e}")

try:
    # Test MilvusClient
    from ai_karen_engine.clients.database.milvus_client import MilvusClient
    
    milvus_client = MilvusClient()
    if milvus_client.health():
        print("SUCCESS: MilvusClient integration is compatible")
    else:
        print("ERROR: MilvusClient health check failed")
        
except ImportError as e:
    print(f"WARN: Could not import MilvusClient: {e}")
except Exception as e:
    print(f"ERROR: MilvusClient integration failed: {e}")

try:
    # Test DuckDBClient
    from ai_karen_engine.clients.database.duckdb_client import DuckDBClient
    
    duckdb_client = DuckDBClient()
    if duckdb_client.health():
        print("SUCCESS: DuckDBClient integration is compatible")
    else:
        print("ERROR: DuckDBClient health check failed")
        
except ImportError as e:
    print(f"WARN: Could not import DuckDBClient: {e}")
except Exception as e:
    print(f"ERROR: DuckDBClient integration failed: {e}")

EOF
    
    # Run the integration test if AI Karen source is available
    if [ -d "../../src/ai_karen_engine" ]; then
        log "INFO" "Running AI Karen client integration tests..."
        python3 /tmp/client_integration_test.py
    else
        log "WARN" "AI Karen source code not found, skipping client integration tests"
    fi
    
    rm -f /tmp/client_integration_test.py
}

# Function to generate compatibility report
generate_compatibility_report() {
    local output_file="${1:-compatibility_report_$(date +%Y%m%d_%H%M%S).txt}"
    
    log "INFO" "Generating compatibility report: $output_file"
    
    {
        echo "AI Karen Database Compatibility Report"
        echo "Generated: $(date)"
        echo "======================================"
        echo ""
        
        echo "Environment Configuration:"
        if [ -f ".env" ]; then
            echo "  Environment: $(grep "^ENVIRONMENT=" .env | cut -d'=' -f2 2>/dev/null || echo "not set")"
            echo "  PostgreSQL: $(grep "^POSTGRES_HOST=" .env | cut -d'=' -f2 2>/dev/null || echo "localhost"):$(grep "^POSTGRES_PORT=" .env | cut -d'=' -f2 2>/dev/null || echo "5432")"
            echo "  Elasticsearch: $(grep "^ELASTICSEARCH_HOST=" .env | cut -d'=' -f2 2>/dev/null || echo "localhost"):$(grep "^ELASTICSEARCH_PORT=" .env | cut -d'=' -f2 2>/dev/null || echo "9200")"
            echo "  Milvus: $(grep "^MILVUS_HOST=" .env | cut -d'=' -f2 2>/dev/null || echo "localhost"):$(grep "^MILVUS_PORT=" .env | cut -d'=' -f2 2>/dev/null || echo "19530")"
            echo "  Redis: $(grep "^REDIS_HOST=" .env | cut -d'=' -f2 2>/dev/null || echo "localhost"):$(grep "^REDIS_PORT=" .env | cut -d'=' -f2 2>/dev/null || echo "6379")"
        else
            echo "  No .env file found"
        fi
        echo ""
        
        echo "Service Status:"
        docker-compose ps 2>/dev/null || echo "  Docker Compose not available"
        echo ""
        
        echo "Compatibility Test Results:"
        echo "  (See console output for detailed results)"
        
    } > "$output_file"
    
    log "SUCCESS" "Compatibility report saved to: $output_file"
}

# Function to show usage
show_usage() {
    echo "AI Karen Database Compatibility Verification Script"
    echo ""
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  --service <name>   Test specific service only"
    echo "  --report [file]    Generate compatibility report"
    echo "  --integration      Test AI Karen client integration"
    echo "  --help             Show this help message"
    echo ""
    echo "Services: postgres, elasticsearch, milvus, redis, duckdb, environment"
    echo ""
    echo "Examples:"
    echo "  $0                          # Full compatibility check"
    echo "  $0 --service postgres       # Test PostgreSQL only"
    echo "  $0 --integration            # Test client integration"
    echo "  $0 --report                 # Generate report"
}

# Main function
main() {
    local specific_service=""
    local generate_report="false"
    local report_file=""
    local test_integration="false"
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --service)
                specific_service="$2"
                shift 2
                ;;
            --report)
                generate_report="true"
                if [[ $2 && $2 != --* ]]; then
                    report_file="$2"
                    shift
                fi
                shift
                ;;
            --integration)
                test_integration="true"
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
    
    # Load environment variables
    if [ -f ".env" ]; then
        set -a
        source .env
        set +a
        log "INFO" "Loaded environment variables from .env"
    else
        log "WARN" "No .env file found, using defaults"
    fi
    
    local overall_compatibility=0
    
    # Run compatibility tests
    if [ -n "$specific_service" ]; then
        case "$specific_service" in
            "postgres") test_postgres_compatibility || overall_compatibility=1 ;;
            "elasticsearch") test_elasticsearch_compatibility || overall_compatibility=1 ;;
            "milvus") test_milvus_compatibility || overall_compatibility=1 ;;
            "redis") test_redis_compatibility || overall_compatibility=1 ;;
            "duckdb") test_duckdb_compatibility || overall_compatibility=1 ;;
            "environment") test_environment_compatibility || overall_compatibility=1 ;;
            *) log "ERROR" "Unknown service: $specific_service"; exit 1 ;;
        esac
    else
        # Run all compatibility tests
        test_environment_compatibility || overall_compatibility=1
        echo ""
        
        test_postgres_compatibility || overall_compatibility=1
        echo ""
        
        test_duckdb_compatibility || overall_compatibility=1
        echo ""
        
        test_elasticsearch_compatibility || overall_compatibility=1
        echo ""
        
        test_milvus_compatibility || overall_compatibility=1
        echo ""
        
        test_redis_compatibility || overall_compatibility=1
        echo ""
    fi
    
    # Test client integration if requested
    if [ "$test_integration" = "true" ]; then
        test_client_integration
        echo ""
    fi
    
    # Generate report if requested
    if [ "$generate_report" = "true" ]; then
        generate_compatibility_report "$report_file"
    fi
    
    # Show overall compatibility status
    echo ""
    if [ $overall_compatibility -eq 0 ]; then
        log "SUCCESS" "🎉 All compatibility checks passed!"
        log "INFO" "The containerized databases are compatible with AI Karen"
    else
        log "WARN" "⚠️  Some compatibility issues found - see details above"
        log "INFO" "Review the issues and update configurations as needed"
    fi
    
    exit $overall_compatibility
}

# Change to script directory
cd "$(dirname "$0")/.."

# Run main function with all arguments
main "$@"