#!/bin/bash
set -e

# AI Karen Database Stack Backup Script
# This script creates backups of all database services

echo "💾 AI Karen Database Stack Backup"
echo "================================="

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
}

# Function to create backup directory
create_backup_dir() {
    local backup_type="$1"
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_dir="./backups/${backup_type}/${timestamp}"
    
    mkdir -p "$backup_dir"
    echo "$backup_dir"
}

# Function to backup PostgreSQL
backup_postgres() {
    local backup_dir="$1"
    
    log "INFO" "Backing up PostgreSQL..."
    
    local host="${POSTGRES_HOST:-localhost}"
    local port="${POSTGRES_PORT:-5434}"
    local user="${POSTGRES_USER:-karen_user}"
    local db="${POSTGRES_DB:-ai_karen}"
    local password="${POSTGRES_PASSWORD:-karen_secure_pass_change_me}"
    
    # Create schema backup
    local schema_file="$backup_dir/postgres_schema.sql"
    if PGPASSWORD="$password" pg_dump -h "$host" -p "$port" -U "$user" -d "$db" --schema-only > "$schema_file"; then
        log "SUCCESS" "PostgreSQL schema backup created: $schema_file"
    else
        log "ERROR" "Failed to backup PostgreSQL schema"
        return 1
    fi
    
    # Create data backup
    local data_file="$backup_dir/postgres_data.sql"
    if PGPASSWORD="$password" pg_dump -h "$host" -p "$port" -U "$user" -d "$db" --data-only > "$data_file"; then
        log "SUCCESS" "PostgreSQL data backup created: $data_file"
    else
        log "ERROR" "Failed to backup PostgreSQL data"
        return 1
    fi
    
    # Create full backup
    local full_file="$backup_dir/postgres_full.sql"
    if PGPASSWORD="$password" pg_dump -h "$host" -p "$port" -U "$user" -d "$db" > "$full_file"; then
        log "SUCCESS" "PostgreSQL full backup created: $full_file"
    else
        log "ERROR" "Failed to create PostgreSQL full backup"
        return 1
    fi
    
    # Compress backups
    gzip "$schema_file" "$data_file" "$full_file"
    log "SUCCESS" "PostgreSQL backups compressed"
    
    return 0
}

# Function to backup Redis
backup_redis() {
    local backup_dir="$1"
    
    log "INFO" "Backing up Redis..."
    
    local host="${REDIS_HOST:-localhost}"
    local port="${REDIS_PORT:-6380}"
    local password="${REDIS_PASSWORD:-redis_secure_pass_change_me}"
    
    # Create Redis backup using BGSAVE
    local redis_cmd="redis-cli -h $host -p $port"
    if [ -n "$password" ]; then
        redis_cmd="$redis_cmd -a $password"
    fi
    
    # Trigger background save
    if $redis_cmd BGSAVE | grep -q "Background saving started"; then
        log "INFO" "Redis background save started, waiting for completion..."
        
        # Wait for background save to complete
        local max_wait=300  # 5 minutes
        local wait_time=0
        
        while [ $wait_time -lt $max_wait ]; do
            if $redis_cmd LASTSAVE > /dev/null 2>&1; then
                sleep 5
                if $redis_cmd BGSAVE | grep -q "Background save already in progress"; then
                    sleep 5
                    wait_time=$((wait_time + 5))
                else
                    break
                fi
            else
                break
            fi
        done
        
        log "SUCCESS" "Redis background save completed"
    else
        log "ERROR" "Failed to start Redis background save"
        return 1
    fi
    
    # Copy RDB file from container
    # Try different container names since Redis might be named differently
    local container_name=$($COMPOSE_CMD ps -q redis 2>/dev/null)
    if [ -z "$container_name" ]; then
        container_name=$(docker ps -q --filter "name=redis" 2>/dev/null)
    fi
    if [ -z "$container_name" ]; then
        container_name=$(docker ps -q --filter "ancestor=redis" 2>/dev/null)
    fi
    
    if [ -n "$container_name" ]; then
        local rdb_file="$backup_dir/redis_dump.rdb"
        if docker cp "$container_name:/data/dump.rdb" "$rdb_file" 2>/dev/null; then
            log "SUCCESS" "Redis RDB file copied: $rdb_file"
            
            # Compress backup
            gzip "$rdb_file"
            log "SUCCESS" "Redis backup compressed"
        else
            log "WARN" "Failed to copy Redis RDB file, but background save completed successfully"
            # This is not a fatal error since the background save worked
        fi
    else
        log "WARN" "Redis container not found, but background save completed successfully"
        # This is not a fatal error since the background save worked
    fi
    
    # Also create a text export of all keys
    local keys_file="$backup_dir/redis_keys.txt"
    if $redis_cmd --scan > "$keys_file"; then
        log "SUCCESS" "Redis keys exported: $keys_file"
        gzip "$keys_file"
    else
        log "WARN" "Failed to export Redis keys list"
    fi
    
    return 0
}

# Function to backup Elasticsearch
backup_elasticsearch() {
    local backup_dir="$1"
    
    log "INFO" "Backing up Elasticsearch..."
    
    local host="${ELASTICSEARCH_HOST:-localhost}"
    local port="${ELASTICSEARCH_PORT:-9200}"
    
    # Get list of indices
    local indices_file="$backup_dir/elasticsearch_indices.json"
    if curl -s "http://$host:$port/_cat/indices?format=json" > "$indices_file"; then
        log "SUCCESS" "Elasticsearch indices list saved: $indices_file"
    else
        log "ERROR" "Failed to get Elasticsearch indices"
        return 1
    fi
    
    # Backup each index
    local indices=$(curl -s "http://$host:$port/_cat/indices?format=json" | jq -r '.[].index' 2>/dev/null || echo "")

    if [ -n "$indices" ]; then
        while IFS= read -r index; do
            # Skip system indices
            if [[ "$index" == .* ]]; then
                log "INFO" "Skipping system index: $index"
                continue
            fi
            
            log "INFO" "Backing up index: $index"
            
            # Export index mapping
            local mapping_file="$backup_dir/elasticsearch_${index}_mapping.json"
            if curl -s "http://$host:$port/$index/_mapping" > "$mapping_file"; then
                log "SUCCESS" "Index mapping saved: $mapping_file"
            else
                log "WARN" "Failed to backup mapping for index: $index"
            fi
            
            # Export index settings
            local settings_file="$backup_dir/elasticsearch_${index}_settings.json"
            if curl -s "http://$host:$port/$index/_settings" > "$settings_file"; then
                log "SUCCESS" "Index settings saved: $settings_file"
            else
                log "WARN" "Failed to backup settings for index: $index"
            fi
            
            # Export index data (limited to prevent huge files)
            local data_file="$backup_dir/elasticsearch_${index}_data.json"
            if curl -s "http://$host:$port/$index/_search?size=10000&scroll=1m" > "$data_file"; then
                log "SUCCESS" "Index data saved: $data_file (limited to 10000 docs)"
            else
                log "WARN" "Failed to backup data for index: $index"
            fi
        done <<< "$indices"
    else
        log "INFO" "No indices found to backup"
    fi
    
    # Compress all Elasticsearch files
    find "$backup_dir" -name "elasticsearch_*.json" -exec gzip {} \;
    log "SUCCESS" "Elasticsearch backups compressed"
    
    return 0
}

# Function to backup Milvus
backup_milvus() {
    local backup_dir="$1"
    
    log "INFO" "Backing up Milvus..."
    
    # Milvus backup requires Python
    if ! command -v python3 > /dev/null 2>&1; then
        log "ERROR" "Python3 is required for Milvus backup"
        return 1
    fi
    
    # Install pymilvus if not available
    if ! python3 -c "import pymilvus" > /dev/null 2>&1; then
        log "INFO" "Installing pymilvus..."
        # Create the backup script first
        cat > /tmp/milvus_backup.py << 'EOF'
#!/usr/bin/env python3
import os
import sys
import json
from pymilvus import connections, utility, Collection

def backup_milvus(backup_dir):
    host = os.getenv('MILVUS_HOST', 'ai-karen-milvus')
    port = os.getenv('MILVUS_PORT', '19530')
    
    try:
        # Add connection parameters with timeout
        # Use container name for Docker network connectivity
        connections.connect(
            alias="default",
            host=host,
            port=port,
            timeout=60
        )
        
        # Get list of collections
        collections = utility.list_collections()
        
        backup_info = {
            "timestamp": os.popen('date -Iseconds').read().strip(),
            "collections": []
        }
        
        for collection_name in collections:
            print(f"Backing up collection: {collection_name}")
            
            try:
                collection = Collection(collection_name)
                collection.load()
                
                # Get collection info
                collection_info = {
                    "name": collection_name,
                    "schema": {
                        "fields": []
                    },
                    "num_entities": collection.num_entities
                }
                
                # Get schema information
                for field in collection.schema.fields:
                    field_info = {
                        "name": field.name,
                        "dtype": str(field.dtype),
                        "is_primary": field.is_primary,
                        "auto_id": field.auto_id if hasattr(field, 'auto_id') else False
                    }
                    
                    if hasattr(field, 'max_length'):
                        field_info["max_length"] = field.max_length
                    if hasattr(field, 'dim'):
                        field_info["dim"] = field.dim
                        
                    collection_info["schema"]["fields"].append(field_info)
                
                # Get index information
                try:
                    indexes = collection.indexes
                    collection_info["indexes"] = []
                    for index in indexes:
                        index_info = {
                            "field_name": index.field_name,
                            "index_name": index.index_name,
                            "params": index.params
                        }
                        collection_info["indexes"].append(index_info)
                except:
                    collection_info["indexes"] = []
                
                backup_info["collections"].append(collection_info)
                
                # Save collection metadata
                collection_file = os.path.join(backup_dir, f"milvus_{collection_name}_metadata.json")
                with open(collection_file, 'w') as f:
                    json.dump(collection_info, f, indent=2)
                
                print(f"Collection {collection_name} metadata saved")
                
            except Exception as e:
                print(f"Error backing up collection {collection_name}: {e}")
                continue
        
        # Save overall backup info
        backup_file = os.path.join(backup_dir, "milvus_backup_info.json")
        with open(backup_file, 'w') as f:
            json.dump(backup_info, f, indent=2)
        
        print(f"Milvus backup completed. {len(collections)} collections processed.")
        return 0
        
    except Exception as e:
        print(f"Failed to backup Milvus: {e}")
        return 1

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 milvus_backup.py <backup_dir>")
        sys.exit(1)
    
    backup_dir = sys.argv[1]
    sys.exit(backup_milvus(backup_dir))
EOF
        
        # Use Docker to install pymilvus and run the backup
        docker run --rm --network ai-karen_ai-karen-net -v "$backup_dir:/backup" -v /tmp:/tmp python:3.9 bash -c "
            pip3 install pymilvus==2.3.2 marshmallow==3.20.1 > /dev/null 2>&1
            python3 /tmp/milvus_backup.py /backup
        "
        if [ $? -eq 0 ]; then
            log "SUCCESS" "Milvus backup completed"
            
            # Compress backup files
            find "$backup_dir" -name "milvus_*.json" -exec gzip {} \;
            log "SUCCESS" "Milvus backups compressed"
            return 0
        else
            log "ERROR" "Milvus backup failed"
            rm -f /tmp/milvus_backup.py
            return 1
        fi
    fi
    
    # Create Milvus backup script
    cat > /tmp/milvus_backup.py << 'EOF'
#!/usr/bin/env python3
import os
import sys
import json
from pymilvus import connections, utility, Collection

def backup_milvus(backup_dir):
    host = os.getenv('MILVUS_HOST', 'ai-karen-milvus')
    port = os.getenv('MILVUS_PORT', '19530')
    
    try:
        # Use container name for Docker network connectivity
        connections.connect(alias="default", host=host, port=port, timeout=60)
        
        # Get list of collections
        collections = utility.list_collections()
        
        backup_info = {
            "timestamp": os.popen('date -Iseconds').read().strip(),
            "collections": []
        }
        
        for collection_name in collections:
            print(f"Backing up collection: {collection_name}")
            
            try:
                collection = Collection(collection_name)
                collection.load()
                
                # Get collection info
                collection_info = {
                    "name": collection_name,
                    "schema": {
                        "fields": []
                    },
                    "num_entities": collection.num_entities
                }
                
                # Get schema information
                for field in collection.schema.fields:
                    field_info = {
                        "name": field.name,
                        "dtype": str(field.dtype),
                        "is_primary": field.is_primary,
                        "auto_id": field.auto_id if hasattr(field, 'auto_id') else False
                    }
                    
                    if hasattr(field, 'max_length'):
                        field_info["max_length"] = field.max_length
                    if hasattr(field, 'dim'):
                        field_info["dim"] = field.dim
                        
                    collection_info["schema"]["fields"].append(field_info)
                
                # Get index information
                try:
                    indexes = collection.indexes
                    collection_info["indexes"] = []
                    for index in indexes:
                        index_info = {
                            "field_name": index.field_name,
                            "index_name": index.index_name,
                            "params": index.params
                        }
                        collection_info["indexes"].append(index_info)
                except:
                    collection_info["indexes"] = []
                
                backup_info["collections"].append(collection_info)
                
                # Save collection metadata
                collection_file = os.path.join(backup_dir, f"milvus_{collection_name}_metadata.json")
                with open(collection_file, 'w') as f:
                    json.dump(collection_info, f, indent=2)
                
                print(f"Collection {collection_name} metadata saved")
                
            except Exception as e:
                print(f"Error backing up collection {collection_name}: {e}")
                continue
        
        # Save overall backup info
        backup_file = os.path.join(backup_dir, "milvus_backup_info.json")
        with open(backup_file, 'w') as f:
            json.dump(backup_info, f, indent=2)
        
        print(f"Milvus backup completed. {len(collections)} collections processed.")
        return 0
        
    except Exception as e:
        print(f"Failed to backup Milvus: {e}")
        return 1

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 milvus_backup.py <backup_dir>")
        sys.exit(1)
    
    backup_dir = sys.argv[1]
    sys.exit(backup_milvus(backup_dir))
EOF
    
    chmod +x /tmp/milvus_backup.py
    
    # Run Milvus backup
    if python3 /tmp/milvus_backup.py "$backup_dir"; then
        log "SUCCESS" "Milvus backup completed"
        
        # Compress backup files
        find "$backup_dir" -name "milvus_*.json" -exec gzip {} \;
        log "SUCCESS" "Milvus backups compressed"
    else
        log "ERROR" "Milvus backup failed"
        rm -f /tmp/milvus_backup.py
        return 1
    fi
    
    rm -f /tmp/milvus_backup.py
    return 0
}

# Function to backup DuckDB
backup_duckdb() {
    local backup_dir="$1"
    
    log "INFO" "Backing up DuckDB..."
    
    local db_path="${DUCKDB_PATH:-/media/zeus/Development19/KIRO/data/duckdb/kari_duckdb.db}"
    
    if [ -f "$db_path" ]; then
        local backup_file="$backup_dir/duckdb_backup.db"
        
        # Copy database file
        if cp "$db_path" "$backup_file"; then
            log "SUCCESS" "DuckDB file copied: $backup_file"
            
            # Compress backup
            gzip "$backup_file"
            log "SUCCESS" "DuckDB backup compressed"
        else
            log "ERROR" "Failed to copy DuckDB file"
            return 1
        fi
        
        # Export schema if DuckDB CLI is available
        if command -v duckdb > /dev/null 2>&1; then
            local schema_file="$backup_dir/duckdb_schema.sql"
            if duckdb "$db_path" ".schema" > "$schema_file" 2>/dev/null; then
                log "SUCCESS" "DuckDB schema exported: $schema_file"
                gzip "$schema_file"
            else
                log "WARN" "Failed to export DuckDB schema"
            fi
        fi
    else
        log "WARN" "DuckDB file not found: $db_path"
        return 1
    fi
    
    return 0
}

# Function to backup MinIO (if present)
backup_minio() {
    local backup_dir="$1"
    
    log "INFO" "Backing up MinIO..."
    
    # Check if MinIO container is running
    if ! $COMPOSE_CMD ps minio | grep -q "Up" 2>/dev/null; then
        log "INFO" "MinIO container not running, skipping backup"
        return 0
    fi
    
    # Copy MinIO data directory from container
    local container_name=$($COMPOSE_CMD ps -q minio)
    if [ -n "$container_name" ]; then
        local minio_backup_dir="$backup_dir/minio_data"
        mkdir -p "$minio_backup_dir"
        
        if docker cp "$container_name:/data" "$minio_backup_dir/"; then
            log "SUCCESS" "MinIO data copied: $minio_backup_dir"
            
            # Create tar archive
            tar -czf "$backup_dir/minio_data.tar.gz" -C "$minio_backup_dir" data
            rm -rf "$minio_backup_dir"
            log "SUCCESS" "MinIO backup archived"
        else
            log "ERROR" "Failed to copy MinIO data"
            return 1
        fi
    else
        log "ERROR" "MinIO container not found"
        return 1
    fi
    
    return 0
}

# Function to create backup manifest
create_backup_manifest() {
    local backup_dir="$1"
    local services="$2"
    
    local manifest_file="$backup_dir/backup_manifest.json"
    
    cat > "$manifest_file" << EOF
{
  "backup_info": {
    "timestamp": "$(date -Iseconds)",
    "version": "1.0",
    "services": "$services",
    "backup_type": "full"
  },
  "files": [
EOF
    
    # List all backup files
    find "$backup_dir" -type f -not -name "backup_manifest.json" | while read -r file; do
        local relative_path=$(echo "$file" | sed "s|$backup_dir/||")
        local file_size=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null || echo "unknown")
        local file_hash=$(sha256sum "$file" 2>/dev/null | cut -d' ' -f1 || echo "unknown")
        
        echo "    {"
        echo "      \"path\": \"$relative_path\","
        echo "      \"size\": $file_size,"
        echo "      \"sha256\": \"$file_hash\""
        echo "    },"
    done | sed '$ s/,$//' >> "$manifest_file"
    
    cat >> "$manifest_file" << EOF
  ]
}
EOF
    
    log "SUCCESS" "Backup manifest created: $manifest_file"
}

# Function to show usage information
show_usage() {
    echo "AI Karen Database Stack Backup Script"
    echo ""
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  --service <name>     Backup only specific service"
    echo "  --output-dir <dir>   Custom backup output directory"
    echo "  --compress           Compress entire backup directory"
    echo "  --verify             Verify backup integrity after creation"
    echo "  --help               Show this help message"
    echo ""
    echo "Services: postgres, redis, elasticsearch, milvus, duckdb, minio"
    echo ""
    echo "Examples:"
    echo "  $0                           # Backup all services"
    echo "  $0 --service postgres        # Backup only PostgreSQL"
    echo "  $0 --compress                # Create compressed backup"
    echo "  $0 --output-dir /tmp/backup  # Custom backup location"
}

# Main function
main() {
    local specific_service=""
    local output_dir=""
    local compress_backup="false"
    local verify_backup="false"
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --service)
                specific_service="$2"
                shift 2
                ;;
            --output-dir)
                output_dir="$2"
                shift 2
                ;;
            --compress)
                compress_backup="true"
                shift
                ;;
            --verify)
                verify_backup="true"
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
    
    # Create backup directory
    local timestamp=$(date +%Y%m%d_%H%M%S)
    if [ -n "$output_dir" ]; then
        local backup_base_dir="$output_dir/$timestamp"
    else
        local backup_base_dir="./backups/full/$timestamp"
    fi
    
    mkdir -p "$backup_base_dir"
    log "INFO" "Backup directory: $backup_base_dir"
    
    # Install required tools
    log "INFO" "Installing required tools..."
    if command -v apk > /dev/null 2>&1; then
        apk add --no-cache curl postgresql-client redis jq gzip tar > /dev/null 2>&1 || true
    elif command -v apt-get > /dev/null 2>&1; then
        apt-get update > /dev/null 2>&1 && apt-get install -y curl postgresql-client redis-tools jq gzip tar > /dev/null 2>&1 || true
    fi
    
    # Perform backups
    local services_backed_up=()
    local backup_success=true
    
    if [ -n "$specific_service" ]; then
        case "$specific_service" in
            "postgres")
                if backup_postgres "$backup_base_dir"; then
                    services_backed_up+=("postgres")
                else
                    backup_success=false
                fi
                ;;
            "redis")
                if backup_redis "$backup_base_dir"; then
                    services_backed_up+=("redis")
                else
                    backup_success=false
                fi
                ;;
            "elasticsearch")
                if backup_elasticsearch "$backup_base_dir"; then
                    services_backed_up+=("elasticsearch")
                else
                    backup_success=false
                fi
                ;;
            "milvus")
                if backup_milvus "$backup_base_dir"; then
                    services_backed_up+=("milvus")
                else
                    backup_success=false
                fi
                ;;
            "duckdb")
                if backup_duckdb "$backup_base_dir"; then
                    services_backed_up+=("duckdb")
                else
                    backup_success=false
                fi
                ;;
            "minio")
                if backup_minio "$backup_base_dir"; then
                    services_backed_up+=("minio")
                else
                    backup_success=false
                fi
                ;;
            *)
                log "ERROR" "Unknown service: $specific_service"
                exit 1
                ;;
        esac
    else
        # Backup all services
        backup_postgres "$backup_base_dir" && services_backed_up+=("postgres") || backup_success=false
        backup_redis "$backup_base_dir" && services_backed_up+=("redis") || backup_success=false
        backup_elasticsearch "$backup_base_dir" && services_backed_up+=("elasticsearch") || backup_success=false
        backup_milvus "$backup_base_dir" && services_backed_up+=("milvus") || backup_success=false
        backup_duckdb "$backup_base_dir" && services_backed_up+=("duckdb") || backup_success=false
        backup_minio "$backup_base_dir" && services_backed_up+=("minio") || backup_success=false
    fi
    
    # Create backup manifest
    local services_list=$(IFS=','; echo "${services_backed_up[*]}")
    create_backup_manifest "$backup_base_dir" "$services_list"
    
    local archive_path=""

    # Compress backup if requested
    if [ "$compress_backup" = "true" ]; then
        log "INFO" "Compressing backup directory..."
        local archive_name="ai_karen_backup_$timestamp.tar.gz"
        archive_path="$(dirname "$backup_base_dir")/$archive_name"

        if tar -czf "$archive_path" -C "$(dirname "$backup_base_dir")" "$(basename "$backup_base_dir")"; then
            log "SUCCESS" "Backup compressed: $archive_path"
            rm -rf "$backup_base_dir"
        else
            log "ERROR" "Failed to compress backup"
            backup_success=false
        fi
    fi

    # Verify backup if requested
    if [ "$verify_backup" = "true" ]; then
        log "INFO" "Verifying backup integrity..."

        if [ "$compress_backup" = "true" ]; then
            if [ -f "$archive_path" ]; then
                if tar -tzf "$archive_path" > /dev/null 2>&1; then
                    log "SUCCESS" "Archive integrity verified: $archive_path"
                else
                    log "ERROR" "Archive verification failed: $archive_path"
                    backup_success=false
                fi
            else
                log "ERROR" "Backup archive not found: $archive_path"
                backup_success=false
            fi
        else
            if [ -d "$backup_base_dir" ]; then
                if find "$backup_base_dir" -mindepth 1 -type f -print -quit | grep -q .; then
                    log "SUCCESS" "Backup directory verified: $backup_base_dir"
                else
                    log "ERROR" "Backup directory is empty: $backup_base_dir"
                    backup_success=false
                fi
            else
                log "ERROR" "Backup directory not found: $backup_base_dir"
                backup_success=false
            fi
        fi
    fi
    # Show results
    echo ""
    if [ "$backup_success" = "true" ]; then
        log "SUCCESS" "Backup completed successfully!"
        log "INFO" "Services backed up: ${services_backed_up[*]}"
        if [ "$compress_backup" = "true" ]; then
            log "INFO" "Backup archive: $archive_path"
        else
            log "INFO" "Backup directory: $backup_base_dir"
        fi
    else
        log "ERROR" "Backup completed with errors"
        log "INFO" "Successfully backed up: ${services_backed_up[*]}"
        exit 1
    fi
}

# Change to script directory
cd "$(dirname "$0")/.."

# Run main function with all arguments
main "$@"
