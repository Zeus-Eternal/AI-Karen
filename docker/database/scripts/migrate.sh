#!/bin/bash
set -e

# Database Migration Manager for AI Karen
# This script manages migrations across all database systems

echo "🔄 AI Karen Database Migration Manager"
echo "====================================="

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

# Function to calculate file checksum
calculate_checksum() {
    local file="$1"
    if [ -f "$file" ]; then
        sha256sum "$file" | cut -d' ' -f1
    else
        echo ""
    fi
}

# Function to run PostgreSQL migrations
migrate_postgres() {
    local action="${1:-up}"
    local target_version="$2"
    
    log "INFO" "Running PostgreSQL migrations ($action)..."
    
    local migration_dir="./migrations/postgres"
    if [ ! -d "$migration_dir" ]; then
        log "ERROR" "PostgreSQL migration directory not found: $migration_dir"
        return 1
    fi
    
    # Ensure migration tracking table exists
    psql -h "${POSTGRES_HOST}" -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -c "
        CREATE TABLE IF NOT EXISTS migration_history (
            id SERIAL PRIMARY KEY,
            service VARCHAR(50) NOT NULL DEFAULT 'postgres',
            migration_name VARCHAR(255) NOT NULL,
            applied_at TIMESTAMP DEFAULT NOW(),
            checksum VARCHAR(64),
            status VARCHAR(20) DEFAULT 'applied',
            UNIQUE(service, migration_name)
        );
    " > /dev/null
    
    case "$action" in
        "up"|"apply")
            log "INFO" "Applying PostgreSQL migrations..."
            
            for migration_file in "$migration_dir"/*.sql; do
                if [ -f "$migration_file" ]; then
                    local filename=$(basename "$migration_file")
                    local checksum=$(calculate_checksum "$migration_file")
                    
                    # Check if migration already applied
                    local applied=$(psql -h "${POSTGRES_HOST}" -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -t -c "
                        SELECT COUNT(*) FROM migration_history 
                        WHERE service = 'postgres' AND migration_name = '$filename' AND status = 'applied';
                    " | tr -d ' ')
                    
                    if [ "$applied" = "0" ]; then
                        log "INFO" "Applying migration: $filename"
                        
                        if psql -h "${POSTGRES_HOST}" -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -f "$migration_file"; then
                            # Record successful migration
                            psql -h "${POSTGRES_HOST}" -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -c "
                                INSERT INTO migration_history (service, migration_name, checksum, status) 
                                VALUES ('postgres', '$filename', '$checksum', 'applied')
                                ON CONFLICT (service, migration_name) DO UPDATE SET
                                    applied_at = NOW(),
                                    checksum = EXCLUDED.checksum,
                                    status = 'applied';
                            " > /dev/null
                            
                            log "SUCCESS" "Migration applied: $filename"
                        else
                            log "ERROR" "Failed to apply migration: $filename"
                            return 1
                        fi
                    else
                        log "INFO" "Migration already applied: $filename"
                    fi
                fi
            done
            ;;
            
        "status")
            log "INFO" "PostgreSQL migration status:"
            psql -h "${POSTGRES_HOST}" -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -c "
                SELECT migration_name, applied_at, status 
                FROM migration_history 
                WHERE service = 'postgres' 
                ORDER BY applied_at;
            "
            ;;
            
        "rollback")
            log "WARN" "PostgreSQL rollback not implemented - manual intervention required"
            ;;
    esac
}

# Function to run DuckDB migrations
migrate_duckdb() {
    local action="${1:-up}"
    
    log "INFO" "Running DuckDB migrations ($action)..."
    
    local migration_dir="./migrations/duckdb"
    local duckdb_path="${DUCKDB_PATH:-./data/duckdb/kari_duckdb.db}"
    
    if [ ! -d "$migration_dir" ]; then
        log "ERROR" "DuckDB migration directory not found: $migration_dir"
        return 1
    fi
    
    if [ ! -f "$duckdb_path" ]; then
        log "ERROR" "DuckDB database file not found: $duckdb_path"
        return 1
    fi
    
    case "$action" in
        "up"|"apply")
            log "INFO" "Applying DuckDB migrations..."
            
            # Ensure migration tracking table exists
            duckdb "$duckdb_path" -c "
                CREATE TABLE IF NOT EXISTS migration_history (
                    id INTEGER PRIMARY KEY,
                    service VARCHAR(50) NOT NULL DEFAULT 'duckdb',
                    migration_name VARCHAR(255) NOT NULL,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    checksum VARCHAR(64),
                    status VARCHAR(20) DEFAULT 'applied',
                    UNIQUE(service, migration_name)
                );
            "
            
            for migration_file in "$migration_dir"/*.sql; do
                if [ -f "$migration_file" ]; then
                    local filename=$(basename "$migration_file")
                    local checksum=$(calculate_checksum "$migration_file")
                    
                    # Check if migration already applied
                    local applied=$(duckdb "$duckdb_path" -c "
                        SELECT COUNT(*) FROM migration_history 
                        WHERE service = 'duckdb' AND migration_name = '$filename' AND status = 'applied';
                    ")
                    
                    if [ "$applied" = "0" ]; then
                        log "INFO" "Applying DuckDB migration: $filename"
                        
                        if duckdb "$duckdb_path" < "$migration_file"; then
                            # Record successful migration
                            duckdb "$duckdb_path" -c "
                                INSERT OR REPLACE INTO migration_history (service, migration_name, checksum, status) 
                                VALUES ('duckdb', '$filename', '$checksum', 'applied');
                            "
                            
                            log "SUCCESS" "DuckDB migration applied: $filename"
                        else
                            log "ERROR" "Failed to apply DuckDB migration: $filename"
                            return 1
                        fi
                    else
                        log "INFO" "DuckDB migration already applied: $filename"
                    fi
                fi
            done
            ;;
            
        "status")
            log "INFO" "DuckDB migration status:"
            duckdb "$duckdb_path" -c "
                SELECT migration_name, applied_at, status 
                FROM migration_history 
                WHERE service = 'duckdb' 
                ORDER BY applied_at;
            "
            ;;
    esac
}

# Function to run Elasticsearch migrations
migrate_elasticsearch() {
    local action="${1:-up}"
    
    log "INFO" "Running Elasticsearch migrations ($action)..."
    
    local migration_dir="./migrations/elasticsearch"
    local es_host="${ELASTICSEARCH_HOST:-localhost}"
    local es_port="${ELASTICSEARCH_PORT:-9200}"
    
    if [ ! -d "$migration_dir" ]; then
        log "ERROR" "Elasticsearch migration directory not found: $migration_dir"
        return 1
    fi
    
    case "$action" in
        "up"|"apply")
            log "INFO" "Applying Elasticsearch migrations..."
            
            # Create migration tracking index
            curl -s -X PUT "http://$es_host:$es_port/ai_karen_migrations" \
                -H "Content-Type: application/json" \
                -d '{
                    "mappings": {
                        "properties": {
                            "service": {"type": "keyword"},
                            "migration_name": {"type": "keyword"},
                            "applied_at": {"type": "date"},
                            "checksum": {"type": "keyword"},
                            "status": {"type": "keyword"}
                        }
                    }
                }' > /dev/null
            
            for migration_file in "$migration_dir"/*.json; do
                if [ -f "$migration_file" ]; then
                    local filename=$(basename "$migration_file" .json)
                    local checksum=$(calculate_checksum "$migration_file")
                    
                    # Check if migration already applied
                    local response=$(curl -s -X GET "http://$es_host:$es_port/ai_karen_migrations/_search" \
                        -H "Content-Type: application/json" \
                        -d "{
                            \"query\": {
                                \"bool\": {
                                    \"must\": [
                                        {\"term\": {\"service\": \"elasticsearch\"}},
                                        {\"term\": {\"migration_name\": \"$filename\"}},
                                        {\"term\": {\"status\": \"applied\"}}
                                    ]
                                }
                            }
                        }")
                    
                    local hit_count=$(echo "$response" | grep -o '"total":{"value":[0-9]*' | grep -o '[0-9]*$')
                    
                    if [ "$hit_count" = "0" ] || [ -z "$hit_count" ]; then
                        log "INFO" "Applying Elasticsearch migration: $filename"
                        
                        # Apply the index mapping/settings
                        if curl -s -X PUT "http://$es_host:$es_port/$filename" \
                            -H "Content-Type: application/json" \
                            -d @"$migration_file" | grep -q '"acknowledged":true'; then
                            
                            # Record successful migration
                            curl -s -X POST "http://$es_host:$es_port/ai_karen_migrations/_doc" \
                                -H "Content-Type: application/json" \
                                -d "{
                                    \"service\": \"elasticsearch\",
                                    \"migration_name\": \"$filename\",
                                    \"applied_at\": \"$(date -Iseconds)\",
                                    \"checksum\": \"$checksum\",
                                    \"status\": \"applied\"
                                }" > /dev/null
                            
                            log "SUCCESS" "Elasticsearch migration applied: $filename"
                        else
                            log "ERROR" "Failed to apply Elasticsearch migration: $filename"
                            return 1
                        fi
                    else
                        log "INFO" "Elasticsearch migration already applied: $filename"
                    fi
                fi
            done
            ;;
            
        "status")
            log "INFO" "Elasticsearch migration status:"
            curl -s -X GET "http://$es_host:$es_port/ai_karen_migrations/_search" \
                -H "Content-Type: application/json" \
                -d '{
                    "query": {"term": {"service": "elasticsearch"}},
                    "sort": [{"applied_at": {"order": "asc"}}]
                }' | jq -r '.hits.hits[]._source | "\(.migration_name) - \(.applied_at) - \(.status)"' 2>/dev/null || echo "jq not available for pretty output"
            ;;
    esac
}

# Function to run Milvus migrations
migrate_milvus() {
    local action="${1:-up}"
    
    log "INFO" "Running Milvus migrations ($action)..."
    
    local migration_dir="./migrations/milvus"
    
    if [ ! -d "$migration_dir" ]; then
        log "ERROR" "Milvus migration directory not found: $migration_dir"
        return 1
    fi
    
    case "$action" in
        "up"|"apply")
            log "INFO" "Applying Milvus migrations..."
            
            for migration_file in "$migration_dir"/*.py; do
                if [ -f "$migration_file" ] && [ -x "$migration_file" ]; then
                    local filename=$(basename "$migration_file")
                    
                    log "INFO" "Applying Milvus migration: $filename"
                    
                    if python3 "$migration_file"; then
                        log "SUCCESS" "Milvus migration applied: $filename"
                    else
                        log "ERROR" "Failed to apply Milvus migration: $filename"
                        return 1
                    fi
                fi
            done
            ;;
            
        "status")
            log "INFO" "Milvus collections status:"
            python3 -c "
from pymilvus import connections, utility
import os

try:
    connections.connect(
        host=os.getenv('MILVUS_HOST', 'localhost'),
        port=os.getenv('MILVUS_PORT', '19530')
    )
    
    collections = utility.list_collections()
    print('Collections:')
    for collection in collections:
        print(f'  - {collection}')
        
except Exception as e:
    print(f'Error: {e}')
"
            ;;
    esac
}

# Function to show migration status for all services
show_status() {
    log "INFO" "Migration status for all services:"
    echo ""
    
    echo "PostgreSQL:"
    migrate_postgres status
    echo ""
    
    echo "DuckDB:"
    migrate_duckdb status
    echo ""
    
    echo "Elasticsearch:"
    migrate_elasticsearch status
    echo ""
    
    echo "Milvus:"
    migrate_milvus status
    echo ""
}

# Function to run all migrations
migrate_all() {
    local action="${1:-up}"
    
    log "INFO" "Running migrations for all services ($action)..."
    
    migrate_postgres "$action"
    migrate_duckdb "$action"
    migrate_elasticsearch "$action"
    migrate_milvus "$action"
    
    log "SUCCESS" "All migrations completed!"
}

# Function to create a new migration
create_migration() {
    local service="$1"
    local name="$2"
    
    if [ -z "$service" ] || [ -z "$name" ]; then
        log "ERROR" "Usage: create_migration <service> <name>"
        log "INFO" "Services: postgres, duckdb, elasticsearch, milvus"
        return 1
    fi
    
    local migration_dir="./migrations/$service"
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local filename=""
    
    case "$service" in
        "postgres"|"duckdb")
            filename="${timestamp}_${name}.sql"
            ;;
        "elasticsearch")
            filename="${timestamp}_${name}.json"
            ;;
        "milvus")
            filename="${timestamp}_${name}.py"
            ;;
        *)
            log "ERROR" "Unknown service: $service"
            return 1
            ;;
    esac
    
    local filepath="$migration_dir/$filename"
    
    if [ ! -d "$migration_dir" ]; then
        mkdir -p "$migration_dir"
    fi
    
    case "$service" in
        "postgres")
            cat > "$filepath" << EOF
-- PostgreSQL Migration: $name
-- Created: $(date)

-- Add your migration SQL here
-- Example:
-- CREATE TABLE example (
--     id SERIAL PRIMARY KEY,
--     name VARCHAR NOT NULL
-- );
EOF
            ;;
        "duckdb")
            cat > "$filepath" << EOF
-- DuckDB Migration: $name
-- Created: $(date)

-- Add your migration SQL here
-- Example:
-- CREATE TABLE example (
--     id INTEGER PRIMARY KEY,
--     name VARCHAR NOT NULL
-- );
EOF
            ;;
        "elasticsearch")
            cat > "$filepath" << EOF
{
  "settings": {
    "number_of_shards": 1,
    "number_of_replicas": 0
  },
  "mappings": {
    "properties": {
      "example_field": {
        "type": "text"
      }
    }
  }
}
EOF
            ;;
        "milvus")
            cat > "$filepath" << EOF
#!/usr/bin/env python3
"""
Milvus Migration: $name
Created: $(date)
"""

import os
from pymilvus import connections, Collection, CollectionSchema, FieldSchema, DataType, utility

def main():
    # Connect to Milvus
    host = os.getenv('MILVUS_HOST', 'localhost')
    port = os.getenv('MILVUS_PORT', '19530')
    
    connections.connect(alias="default", host=host, port=port)
    
    # Add your migration code here
    print("Migration $name executed successfully")

if __name__ == "__main__":
    main()
EOF
            chmod +x "$filepath"
            ;;
    esac
    
    log "SUCCESS" "Migration created: $filepath"
}

# Main function
main() {
    local command="${1:-help}"
    
    case "$command" in
        "up"|"apply")
            local service="$2"
            if [ -n "$service" ]; then
                case "$service" in
                    "postgres") migrate_postgres up ;;
                    "duckdb") migrate_duckdb up ;;
                    "elasticsearch") migrate_elasticsearch up ;;
                    "milvus") migrate_milvus up ;;
                    *) log "ERROR" "Unknown service: $service" ;;
                esac
            else
                migrate_all up
            fi
            ;;
        "status")
            local service="$2"
            if [ -n "$service" ]; then
                case "$service" in
                    "postgres") migrate_postgres status ;;
                    "duckdb") migrate_duckdb status ;;
                    "elasticsearch") migrate_elasticsearch status ;;
                    "milvus") migrate_milvus status ;;
                    *) log "ERROR" "Unknown service: $service" ;;
                esac
            else
                show_status
            fi
            ;;
        "create")
            create_migration "$2" "$3"
            ;;
        "help"|*)
            echo "AI Karen Database Migration Manager"
            echo ""
            echo "Usage: $0 <command> [options]"
            echo ""
            echo "Commands:"
            echo "  up [service]           Apply migrations (all services or specific)"
            echo "  status [service]       Show migration status"
            echo "  create <service> <name> Create new migration file"
            echo "  help                   Show this help"
            echo ""
            echo "Services: postgres, duckdb, elasticsearch, milvus"
            echo ""
            echo "Examples:"
            echo "  $0 up                  # Apply all migrations"
            echo "  $0 up postgres         # Apply PostgreSQL migrations only"
            echo "  $0 status              # Show status for all services"
            echo "  $0 create postgres add_user_table  # Create new PostgreSQL migration"
            ;;
    esac
}

# Run main function with all arguments
main "$@"