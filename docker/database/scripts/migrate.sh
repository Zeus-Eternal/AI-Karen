#!/usr/bin/env bash
set -eo pipefail

# 🔄 AI Karen Database Migration Manager
# Enhanced version with robust error handling, rollback support, and multi-database capabilities

# --------------------------
# Configuration and Setup
# --------------------------

# Initialize colors and logging
init_logging() {
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[0;33m'
    BLUE='\033[0;34m'
    CYAN='\033[0;36m'
    NC='\033[0m'
}

log() {
    local level="$1"
    local message="$2"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    case "$level" in
        DEBUG)    color="${BLUE}"    ;;
        INFO)     color="${GREEN}"   ;;
        WARN)     color="${YELLOW}"  ;;
        ERROR)    color="${RED}"     ;;
        SUCCESS)  color="${CYAN}"    ;;
        *)        color="${NC}"      ;;
    esac
    
    printf "%b[%s] %-7s %b%s%b\n" "${color}" "$timestamp" "$level" "${NC}" "$message" "${NC}"
}

# --------------------------
# Dependency and Environment Checks
# --------------------------

check_dependencies() {
    local required=("psql" "duckdb" "curl" "jq" "python3")
    local missing=()
    
    for cmd in "${required[@]}"; do
        if ! command -v "$cmd" &> /dev/null; then
            missing+=("$cmd")
        fi
    done
    
    if [ ${#missing[@]} -gt 0 ]; then
        log "ERROR" "Missing dependencies: ${missing[*]}"
        exit 1
    fi
}

validate_env_vars() {
    local required_postgres=("POSTGRES_HOST" "POSTGRES_USER" "POSTGRES_DB")
    local missing=()
    
    for var in "${required_postgres[@]}"; do
        if [ -z "${!var}" ]; then
            missing+=("$var")
        fi
    done
    
    if [ ${#missing[@]} -gt 0 ]; then
        log "ERROR" "Missing required environment variables: ${missing[*]}"
        exit 1
    fi
}

# --------------------------
# Migration Utilities
# --------------------------

calculate_checksum() {
    [ -f "$1" ] && sha256sum "$1" | cut -d' ' -f1 || echo ""
}

ensure_migration_table() {
    local db_type="$1"
    case "$db_type" in
        postgres)
            psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB" <<'SQL' > /dev/null
CREATE TABLE IF NOT EXISTS migration_history (
    id SERIAL PRIMARY KEY,
    service VARCHAR(50) NOT NULL DEFAULT 'postgres',
    migration_name VARCHAR(255) NOT NULL,
    applied_at TIMESTAMP DEFAULT NOW(),
    checksum VARCHAR(64),
    status VARCHAR(20) DEFAULT 'applied',
    UNIQUE(service, migration_name)
);
SQL
            ;;
        duckdb)
            local db="${DUCKDB_PATH:-./data/duckdb/kari_duckdb.db}"
            duckdb "$db" -c "
CREATE TABLE IF NOT EXISTS migration_history (
    id INTEGER PRIMARY KEY,
    service VARCHAR(50) NOT NULL DEFAULT 'duckdb',
    migration_name VARCHAR(255) NOT NULL,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    checksum VARCHAR(64),
    status VARCHAR(20) DEFAULT 'applied',
    UNIQUE(service, migration_name)
);" > /dev/null
            ;;
        elasticsearch)
            local host="${ELASTICSEARCH_HOST:-localhost}"
            local port="${ELASTICSEARCH_PORT:-9200}"
            curl -s -X PUT "http://$host:$port/ai_karen_migrations" -H 'Content-Type: application/json' -d '{
                "mappings": {
                    "properties": {
                        "service": {"type":"keyword"},
                        "migration_name": {"type":"keyword"},
                        "applied_at": {"type":"date"},
                        "checksum": {"type":"keyword"},
                        "status": {"type":"keyword"}
                    }
                }
            }' > /dev/null
            ;;
    esac
}

# --------------------------
# Database Migration Functions
# --------------------------

migrate_postgres() {
    local action="${1:-up}"
    local target="${2:-}"
    local dry_run="${3:-false}"
    
    log "INFO" "Running PostgreSQL migrations ($action)..."
    
    local migration_dir="./migrations/postgres"
    [ -d "$migration_dir" ] || { log "ERROR" "Directory not found: $migration_dir"; return 1; }
    
    ensure_migration_table "postgres"
    
    case "$action" in
        up|apply)
            log "INFO" "Applying PostgreSQL migrations..."
            for f in "$migration_dir"/*.sql; do
                [ -f "$f" ] || continue
                local name checksum applied
                name=$(basename "$f")
                checksum=$(calculate_checksum "$f")
                applied=$(psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tAc \
                    "SELECT COUNT(*) FROM migration_history WHERE service='postgres' AND migration_name='$name' AND status='applied';")
                
                if [ "$applied" -eq 0 ]; then
                    if [ "$dry_run" = true ]; then
                        log "INFO" "[DRY RUN] Would apply: $name"
                    else
                        log "INFO" "Applying: $name"
                        if psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f "$f"; then
                            psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB" <<SQL > /dev/null
INSERT INTO migration_history(service,migration_name,checksum,status)
VALUES('postgres','$name','$checksum','applied')
ON CONFLICT (service,migration_name) DO UPDATE 
SET applied_at=NOW(), checksum=EXCLUDED.checksum, status='applied';
SQL
                            log "SUCCESS" "Applied: $name"
                        else
                            log "ERROR" "Failed: $name"
                            return 1
                        fi
                    fi
                else
                    log "DEBUG" "Skipped (already applied): $name"
                fi
            done
            ;;
            
        down|rollback)
            local steps="${target:-1}"
            log "INFO" "Rolling back $steps PostgreSQL migration(s)"
            
            if [ "$dry_run" = true ]; then
                log "INFO" "[DRY RUN] Would rollback last $steps migration(s)"
                return 0
            fi
            
            local migrations
            migrations=$(psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c "
                SELECT migration_name FROM migration_history 
                WHERE service='postgres' AND status='applied'
                ORDER BY applied_at DESC
                LIMIT $steps;
            ")
            
            for mig in $migrations; do
                local rollback_file="./migrations/postgres/rollbacks/${mig%.sql}_rollback.sql"
                if [ -f "$rollback_file" ]; then
                    log "INFO" "Rolling back: $mig"
                    if psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f "$rollback_file"; then
                        psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "
                            UPDATE migration_history SET status='rolledback' 
                            WHERE service='postgres' AND migration_name='$mig';
                        " > /dev/null
                        log "SUCCESS" "Rolled back: $mig"
                    else
                        log "ERROR" "Failed to rollback: $mig"
                        return 1
                    fi
                else
                    log "WARN" "No rollback script found for: $mig"
                fi
            done
            ;;
            
        status)
            log "INFO" "PostgreSQL migration status:"
            psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c \
                "SELECT migration_name, applied_at, status FROM migration_history WHERE service='postgres' ORDER BY applied_at;"
            ;;
            
        validate)
            log "INFO" "Validating PostgreSQL migrations..."
            local invalid=0
            for f in "$migration_dir"/*.sql; do
                [ -f "$f" ] || continue
                local name checksum db_checksum
                name=$(basename "$f")
                checksum=$(calculate_checksum "$f")
                db_checksum=$(psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tAc \
                    "SELECT checksum FROM migration_history WHERE service='postgres' AND migration_name='$name';")
                
                if [ -n "$db_checksum" ] && [ "$db_checksum" != "$checksum" ]; then
                    log "ERROR" "Checksum mismatch for: $name"
                    invalid=$((invalid+1))
                fi
            done
            [ "$invalid" -eq 0 ] && log "SUCCESS" "All PostgreSQL migrations valid"
            return "$invalid"
            ;;
    esac
}

migrate_duckdb() {
    local action="${1:-up}"
    local dry_run="${2:-false}"
    
    log "INFO" "Running DuckDB migrations ($action)..."
    
    local migration_dir="./migrations/duckdb"
    local db="${DUCKDB_PATH:-./data/duckdb/kari_duckdb.db}"
    [ -d "$migration_dir" ] || { log "ERROR" "Directory not found: $migration_dir"; return 1; }
    [ -f "$db" ] || { log "ERROR" "Database file not found: $db"; return 1; }
    
    ensure_migration_table "duckdb"
    
    case "$action" in
        up|apply)
            log "INFO" "Applying DuckDB migrations..."
            for f in "$migration_dir"/*.sql; do
                [ -f "$f" ] || continue
                local name checksum applied
                name=$(basename "$f")
                checksum=$(calculate_checksum "$f")
                applied=$(duckdb "$db" -c \
                    "SELECT COUNT(*) FROM migration_history WHERE service='duckdb' AND migration_name='$name' AND status='applied';")
                
                if [ "$applied" -eq 0 ]; then
                    if [ "$dry_run" = true ]; then
                        log "INFO" "[DRY RUN] Would apply: $name"
                    else
                        log "INFO" "Applying: $name"
                        if duckdb "$db" < "$f"; then
                            duckdb "$db" -c \
                                "INSERT OR REPLACE INTO migration_history(service,migration_name,checksum,status)
                                 VALUES('duckdb','$name','$checksum','applied');" > /dev/null
                            log "SUCCESS" "Applied: $name"
                        else
                            log "ERROR" "Failed: $name"
                            return 1
                        fi
                    fi
                else
                    log "DEBUG" "Skipped (already applied): $name"
                fi
            done
            ;;
            
        status)
            log "INFO" "DuckDB migration status:"
            duckdb "$db" -c \
                "SELECT migration_name, applied_at, status FROM migration_history WHERE service='duckdb' ORDER BY applied_at;"
            ;;
            
        validate)
            log "INFO" "Validating DuckDB migrations..."
            local invalid=0
            for f in "$migration_dir"/*.sql; do
                [ -f "$f" ] || continue
                local name checksum db_checksum
                name=$(basename "$f")
                checksum=$(calculate_checksum "$f")
                db_checksum=$(duckdb "$db" -c \
                    "SELECT checksum FROM migration_history WHERE service='duckdb' AND migration_name='$name';")
                
                if [ -n "$db_checksum" ] && [ "$db_checksum" != "$checksum" ]; then
                    log "ERROR" "Checksum mismatch for: $name"
                    invalid=$((invalid+1))
                fi
            done
            [ "$invalid" -eq 0 ] && log "SUCCESS" "All DuckDB migrations valid"
            return "$invalid"
            ;;
    esac
}

migrate_elasticsearch() {
    local action="${1:-up}"
    local dry_run="${2:-false}"
    
    log "INFO" "Running Elasticsearch migrations ($action)..."
    
    local migration_dir="./migrations/elasticsearch"
    local host="${ELASTICSEARCH_HOST:-localhost}"
    local port="${ELASTICSEARCH_PORT:-9200}"
    [ -d "$migration_dir" ] || { log "ERROR" "Directory not found: $migration_dir"; return 1; }
    
    ensure_migration_table "elasticsearch"
    
    case "$action" in
        up|apply)
            log "INFO" "Applying Elasticsearch migrations..."
            for f in "$migration_dir"/*.json; do
                [ -f "$f" ] || continue
                local name checksum count
                name=$(basename "$f" .json)
                checksum=$(calculate_checksum "$f")
                count=$(curl -s -X GET "http://$host:$port/ai_karen_migrations/_search" \
                    -H 'Content-Type:application/json' -d "{
                        \"query\": {\"bool\": {\"must\": [
                            {\"term\": {\"service\":\"elasticsearch\"}},
                            {\"term\": {\"migration_name\":\"$name\"}},
                            {\"term\": {\"status\":\"applied\"}}
                        ]}}}" | jq -r '.hits.total.value')
                
                if [ "$count" -eq 0 ]; then
                    if [ "$dry_run" = true ]; then
                        log "INFO" "[DRY RUN] Would apply: $name"
                    else
                        log "INFO" "Applying: $name"
                        if curl -s -X PUT "http://$host:$port/$name" \
                            -H 'Content-Type:application/json' -d @"$f" | grep -q '"acknowledged":true'; then
                            curl -s -X POST "http://$host:$port/ai_karen_migrations/_doc" \
                                -H 'Content-Type:application/json' -d "{
                                    \"service\":\"elasticsearch\",
                                    \"migration_name\":\"$name\",
                                    \"applied_at\":\"$(date -Iseconds)\",
                                    \"checksum\":\"$checksum\",
                                    \"status\":\"applied\"
                                }" > /dev/null
                            log "SUCCESS" "Applied: $name"
                        else
                            log "ERROR" "Failed: $name"
                            return 1
                        fi
                    fi
                else
                    log "DEBUG" "Skipped (already applied): $name"
                fi
            done
            ;;
            
        status)
            log "INFO" "Elasticsearch migration status:"
            curl -s -X GET "http://$host:$port/ai_karen_migrations/_search" \
                -H 'Content-Type:application/json' -d '{
                    "query":{"term":{"service":"elasticsearch"}}, 
                    "sort":[{"applied_at":{"order":"asc"}}]
                }' | jq -r '.hits.hits[]._source | "\(.migration_name) \(.applied_at) \(.status)"'
            ;;
            
        validate)
            log "INFO" "Validating Elasticsearch migrations..."
            local invalid=0
            for f in "$migration_dir"/*.json; do
                [ -f "$f" ] || continue
                local name checksum db_checksum
                name=$(basename "$f" .json)
                checksum=$(calculate_checksum "$f")
                db_checksum=$(curl -s -X GET "http://$host:$port/ai_karen_migrations/_search" \
                    -H 'Content-Type:application/json' -d "{
                        \"query\": {\"term\": {\"migration_name\":\"$name\"}}
                    }" | jq -r '.hits.hits[0]._source.checksum')
                
                if [ -n "$db_checksum" ] && [ "$db_checksum" != "$checksum" ]; then
                    log "ERROR" "Checksum mismatch for: $name"
                    invalid=$((invalid+1))
                fi
            done
            [ "$invalid" -eq 0 ] && log "SUCCESS" "All Elasticsearch migrations valid"
            return "$invalid"
            ;;
    esac
}

migrate_milvus() {
    local action="${1:-up}"
    local dry_run="${2:-false}"
    
    log "INFO" "Running Milvus migrations ($action)..."
    
    local migration_dir="./migrations/milvus"
    [ -d "$migration_dir" ] || { log "ERROR" "Directory not found: $migration_dir"; return 1; }
    
    case "$action" in
        up|apply)
            log "INFO" "Applying Milvus migrations..."
            for f in "$migration_dir"/*.py; do
                [ -f "$f" ] && [ -x "$f" ] || continue
                local name
                name=$(basename "$f")
                
                if [ "$dry_run" = true ]; then
                    log "INFO" "[DRY RUN] Would apply: $name"
                else
                    log "INFO" "Applying: $name"
                    if python3 "$f"; then
                        log "SUCCESS" "Applied: $name"
                    else
                        log "ERROR" "Failed: $name"
                        return 1
                    fi
                fi
            done
            ;;
            
        status)
            log "INFO" "Milvus collections status:"
            python3 - <<PYCODE
from pymilvus import connections, utility
import os

try:
    connections.connect(
        host=os.getenv('MILVUS_HOST', 'localhost'),
        port=os.getenv('MILVUS_PORT', '19530')
    )
    
    collections = utility.list_collections()
    print("Collections:")
    for col in collections:
        stats = utility.get_collection_stats(col)
        print(f"  - {col}: {stats['row_count']} entities")
        
except Exception as e:
    print(f"Error: {e}")
PYCODE
            ;;
    esac
}

# --------------------------
# Migration Management
# --------------------------

show_status() {
    log "INFO" "Migration status for all services:"
    echo
    
    log "INFO" "=== PostgreSQL ==="
    migrate_postgres status
    echo
    
    log "INFO" "=== DuckDB ==="
    migrate_duckdb status
    echo
    
    log "INFO" "=== Elasticsearch ==="
    migrate_elasticsearch status
    echo
    
    log "INFO" "=== Milvus ==="
    migrate_milvus status
    echo
}

validate_all() {
    log "INFO" "Validating all migrations..."
    local invalid=0
    
    migrate_postgres validate || invalid=$((invalid+1))
    migrate_duckdb validate || invalid=$((invalid+1))
    migrate_elasticsearch validate || invalid=$((invalid+1))
    
    if [ "$invalid" -eq 0 ]; then
        log "SUCCESS" "All migrations validated successfully"
        return 0
    else
        log "ERROR" "Found $invalid invalid migrations"
        return 1
    fi
}

migrate_all() {
    local action="${1:-up}"
    local target="${2:-}"
    local dry_run="${3:-false}"
    
    log "INFO" "Running all migrations ($action)..."
    
    migrate_postgres "$action" "$target" "$dry_run" || return 1
    migrate_duckdb "$action" "$dry_run" || return 1
    migrate_elasticsearch "$action" "$dry_run" || return 1
    migrate_milvus "$action" "$dry_run" || return 1
    
    log "SUCCESS" "All migrations completed successfully"
}

create_migration() {
    local service="$1"
    local name="$2"
    
    [ -z "$service" ] || [ -z "$name" ] && {
        log "ERROR" "Usage: create <service> <name>"
        return 1
    }
    
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local ext template
    
    case "$service" in
        postgres|duckdb) ext="sql" ;;
        elasticsearch)   ext="json" ;;
        milvus)          ext="py" ;;
        *) log "ERROR" "Unknown service: $service"; return 1 ;;
    esac
    
    local dir="./migrations/$service"
    local file="$dir/${timestamp}_${name}.$ext"
    
    mkdir -p "$dir"
    
    case "$service" in
        postgres)
            template="-- PostgreSQL Migration: $name\n-- Created: $(date)\n\n-- Add your migration SQL here"
            echo -e "$template" > "$file"
            ;;
        duckdb)
            template="-- DuckDB Migration: $name\n-- Created: $(date)\n\n-- Add your migration SQL here"
            echo -e "$template" > "$file"
            ;;
        elasticsearch)
            template='{
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
}'
            echo "$template" > "$file"
            ;;
        milvus)
            template="#!/usr/bin/env python3
\"\"\"
Milvus Migration: $name
Created: $(date)
\"\"\"

from pymilvus import connections, Collection, CollectionSchema, FieldSchema, DataType, utility
import os

def main():
    # Connect to Milvus
    connections.connect(
        alias=\"default\",
        host=os.getenv('MILVUS_HOST', 'localhost'),
        port=os.getenv('MILVUS_PORT', '19530')
    )
    
    # Add your migration code here
    print(\"Migration $name executed successfully\")

if __name__ == \"__main__\":
    main()"
            echo "$template" > "$file"
            chmod +x "$file"
            ;;
    esac
    
    log "SUCCESS" "Created migration: $file"
}

# --------------------------
# Main Function
# --------------------------

show_help() {
    cat <<EOF
AI Karen Database Migration Manager
===================================

Usage: $0 <command> [options] [service]

Commands:
  up [service]           Apply migrations (default: all services)
  down [service] [n]     Rollback migrations (default: 1 migration)
  status [service]       Show migration status
  validate               Validate all migrations
  create <service> <name> Create new migration
  help                   Show this help

Options:
  --dry-run              Show what would be done without executing
  --config <file>        Use alternate config file

Services: postgres, duckdb, elasticsearch, milvus

Examples:
  $0 up                    # Apply all migrations
  $0 up postgres           # Apply PostgreSQL migrations only
  $0 down duckdb 2         # Rollback 2 DuckDB migrations
  $0 status                # Show all migration statuses
  $0 create milvus add_collection  # Create new Milvus migration
  $0 validate              # Validate all migrations
EOF
}

main() {
    init_logging
    check_dependencies
    validate_env_vars
    
    local command="help"
    local service=""
    local target=""
    local dry_run=false
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            up|down|status|create|validate|help)
                command="$1"
                shift
                ;;
            postgres|duckdb|elasticsearch|milvus)
                service="$1"
                shift
                ;;
            [0-9]*)
                target="$1"
                shift
                ;;
            --dry-run)
                dry_run=true
                shift
                ;;
            --config)
                [ -f "$2" ] && source "$2" || {
                    log "ERROR" "Config file not found: $2"
                    exit 1
                }
                shift 2
                ;;
            *)
                log "ERROR" "Unknown argument: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    case "$command" in
        up)
            if [ -n "$service" ]; then
                case "$service" in
                    postgres) migrate_postgres up "" "$dry_run" ;;
                    duckdb) migrate_duckdb up "$dry_run" ;;
                    elasticsearch) migrate_elasticsearch up "$dry_run" ;;
                    milvus) migrate_milvus up "$dry_run" ;;
                esac
            else
                migrate_all up "" "$dry_run"
            fi
            ;;
            
        down)
            if [ -n "$service" ]; then
                case "$service" in
                    postgres) migrate_postgres down "$target" "$dry_run" ;;
                    duckdb|elasticsearch|milvus)
                        log "WARN" "Rollback not fully implemented for $service"
                        ;;
                esac
            else
                migrate_postgres down "${target:-1}" "$dry_run"
            fi
            ;;
            
        status)
            if [ -n "$service" ]; then
                case "$service" in
                    postgres) migrate_postgres status ;;
                    duckdb) migrate_duckdb status ;;
                    elasticsearch) migrate_elasticsearch status ;;
                    milvus) migrate_milvus status ;;
                esac
            else
                show_status
            fi
            ;;
            
        validate)
            validate_all
            ;;
            
        create)
            create_migration "$service" "$target"
            ;;
            
        help|*)
            show_help
            ;;
    esac
}

# Run the main function
main "$@"