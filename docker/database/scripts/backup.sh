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
    local port="${POSTGRES_PORT:-5432}"
    local user="${POSTGRES_USER:-karen_user}"
    local db="${POSTGRES_DB:-ai_karen}"
    local password="${POSTGRES_PASSWORD:-}"
    
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
    local port="${REDIS_PORT:-6379}"
    local password="${REDIS_PASSWORD:-}"
    
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
    local container_name=$($COMPOSE_CMD ps -q redis)
    if [ -n "$container_name" ]; then
        local rdb_file="$backup_dir/redis_dump.rdb"
        if docker cp "$container_name:/data/dump.rdb" "$rdb_file"; then
            log "SUCCESS" "Redis RDB file copied: $rdb_file"
            
            # Compress backup
            gzip "$rdb_file"
            log "SUCCESS" "Redis backup compressed"
        else
            log "ERROR" "Failed to copy Redis RDB file"
            return 1
        fi
    else
        log "ERROR" "Redis container not found"
        return 1
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
    local indices=$(curl -s "http://$host:$port/_cat/indices?format=json" | jq -r '.[].index' 2>/dev/null || echo "")\n    \n    if [ -n \"$indices\" ]; then\n        for index in $indices; do\n            # Skip system indices\n            if [[ \"$index\" == .* ]]; then\n                log \"INFO\" \"Skipping system index: $index\"\n                continue\n            fi\n            \n            log \"INFO\" \"Backing up index: $index\"\n            \n            # Export index mapping\n            local mapping_file=\"$backup_dir/elasticsearch_${index}_mapping.json\"\n            if curl -s \"http://$host:$port/$index/_mapping\" > \"$mapping_file\"; then\n                log \"SUCCESS\" \"Index mapping saved: $mapping_file\"\n            else\n                log \"WARN\" \"Failed to backup mapping for index: $index\"\n            fi\n            \n            # Export index settings\n            local settings_file=\"$backup_dir/elasticsearch_${index}_settings.json\"\n            if curl -s \"http://$host:$port/$index/_settings\" > \"$settings_file\"; then\n                log \"SUCCESS\" \"Index settings saved: $settings_file\"\n            else\n                log \"WARN\" \"Failed to backup settings for index: $index\"\n            fi\n            \n            # Export index data (limited to prevent huge files)\n            local data_file=\"$backup_dir/elasticsearch_${index}_data.json\"\n            if curl -s \"http://$host:$port/$index/_search?size=10000&scroll=1m\" > \"$data_file\"; then\n                log \"SUCCESS\" \"Index data saved: $data_file (limited to 10000 docs)\"\n            else\n                log \"WARN\" \"Failed to backup data for index: $index\"\n            fi\n        done\n    else\n        log \"INFO\" \"No indices found to backup\"\n    fi\n    \n    # Compress all Elasticsearch files\n    find \"$backup_dir\" -name \"elasticsearch_*.json\" -exec gzip {} \\;\n    log \"SUCCESS\" \"Elasticsearch backups compressed\"\n    \n    return 0\n}\n\n# Function to backup Milvus\nbackup_milvus() {\n    local backup_dir=\"$1\"\n    \n    log \"INFO\" \"Backing up Milvus...\"\n    \n    # Milvus backup requires Python\n    if ! command -v python3 > /dev/null 2>&1; then\n        log \"ERROR\" \"Python3 is required for Milvus backup\"\n        return 1\n    fi\n    \n    # Install pymilvus if not available\n    if ! python3 -c \"import pymilvus\" > /dev/null 2>&1; then\n        log \"INFO\" \"Installing pymilvus...\"\n        pip3 install pymilvus > /dev/null 2>&1\n    fi\n    \n    # Create Milvus backup script\n    cat > /tmp/milvus_backup.py << 'EOF'\n#!/usr/bin/env python3\nimport os\nimport sys\nimport json\nfrom pymilvus import connections, utility, Collection\n\ndef backup_milvus(backup_dir):\n    host = os.getenv('MILVUS_HOST', 'localhost')\n    port = os.getenv('MILVUS_PORT', '19530')\n    \n    try:\n        connections.connect(alias=\"default\", host=host, port=port)\n        \n        # Get list of collections\n        collections = utility.list_collections()\n        \n        backup_info = {\n            \"timestamp\": os.popen('date -Iseconds').read().strip(),\n            \"collections\": []\n        }\n        \n        for collection_name in collections:\n            print(f\"Backing up collection: {collection_name}\")\n            \n            try:\n                collection = Collection(collection_name)\n                collection.load()\n                \n                # Get collection info\n                collection_info = {\n                    \"name\": collection_name,\n                    \"schema\": {\n                        \"fields\": []\n                    },\n                    \"num_entities\": collection.num_entities\n                }\n                \n                # Get schema information\n                for field in collection.schema.fields:\n                    field_info = {\n                        \"name\": field.name,\n                        \"dtype\": str(field.dtype),\n                        \"is_primary\": field.is_primary,\n                        \"auto_id\": field.auto_id if hasattr(field, 'auto_id') else False\n                    }\n                    \n                    if hasattr(field, 'max_length'):\n                        field_info[\"max_length\"] = field.max_length\n                    if hasattr(field, 'dim'):\n                        field_info[\"dim\"] = field.dim\n                        \n                    collection_info[\"schema\"][\"fields\"].append(field_info)\n                \n                # Get index information\n                try:\n                    indexes = collection.indexes\n                    collection_info[\"indexes\"] = []\n                    for index in indexes:\n                        index_info = {\n                            \"field_name\": index.field_name,\n                            \"index_name\": index.index_name,\n                            \"params\": index.params\n                        }\n                        collection_info[\"indexes\"].append(index_info)\n                except:\n                    collection_info[\"indexes\"] = []\n                \n                backup_info[\"collections\"].append(collection_info)\n                \n                # Save collection metadata\n                collection_file = os.path.join(backup_dir, f\"milvus_{collection_name}_metadata.json\")\n                with open(collection_file, 'w') as f:\n                    json.dump(collection_info, f, indent=2)\n                \n                print(f\"Collection {collection_name} metadata saved\")\n                \n            except Exception as e:\n                print(f\"Error backing up collection {collection_name}: {e}\")\n                continue\n        \n        # Save overall backup info\n        backup_file = os.path.join(backup_dir, \"milvus_backup_info.json\")\n        with open(backup_file, 'w') as f:\n            json.dump(backup_info, f, indent=2)\n        \n        print(f\"Milvus backup completed. {len(collections)} collections processed.\")\n        return 0\n        \n    except Exception as e:\n        print(f\"Failed to backup Milvus: {e}\")\n        return 1\n\nif __name__ == \"__main__\":\n    if len(sys.argv) != 2:\n        print(\"Usage: python3 milvus_backup.py <backup_dir>\")\n        sys.exit(1)\n    \n    backup_dir = sys.argv[1]\n    sys.exit(backup_milvus(backup_dir))\nEOF\n    \n    chmod +x /tmp/milvus_backup.py\n    \n    # Run Milvus backup\n    if python3 /tmp/milvus_backup.py \"$backup_dir\"; then\n        log \"SUCCESS\" \"Milvus backup completed\"\n        \n        # Compress backup files\n        find \"$backup_dir\" -name \"milvus_*.json\" -exec gzip {} \\;\n        log \"SUCCESS\" \"Milvus backups compressed\"\n    else\n        log \"ERROR\" \"Milvus backup failed\"\n        rm -f /tmp/milvus_backup.py\n        return 1\n    fi\n    \n    rm -f /tmp/milvus_backup.py\n    return 0\n}\n\n# Function to backup DuckDB\nbackup_duckdb() {\n    local backup_dir=\"$1\"\n    \n    log \"INFO\" \"Backing up DuckDB...\"\n    \n    local db_path=\"${DUCKDB_PATH:-./data/duckdb/kari_duckdb.db}\"\n    \n    if [ -f \"$db_path\" ]; then\n        local backup_file=\"$backup_dir/duckdb_backup.db\"\n        \n        # Copy database file\n        if cp \"$db_path\" \"$backup_file\"; then\n            log \"SUCCESS\" \"DuckDB file copied: $backup_file\"\n            \n            # Compress backup\n            gzip \"$backup_file\"\n            log \"SUCCESS\" \"DuckDB backup compressed\"\n        else\n            log \"ERROR\" \"Failed to copy DuckDB file\"\n            return 1\n        fi\n        \n        # Export schema if DuckDB CLI is available\n        if command -v duckdb > /dev/null 2>&1; then\n            local schema_file=\"$backup_dir/duckdb_schema.sql\"\n            if duckdb \"$db_path\" \".schema\" > \"$schema_file\" 2>/dev/null; then\n                log \"SUCCESS\" \"DuckDB schema exported: $schema_file\"\n                gzip \"$schema_file\"\n            else\n                log \"WARN\" \"Failed to export DuckDB schema\"\n            fi\n        fi\n    else\n        log \"WARN\" \"DuckDB file not found: $db_path\"\n        return 1\n    fi\n    \n    return 0\n}\n\n# Function to backup MinIO (if present)\nbackup_minio() {\n    local backup_dir=\"$1\"\n    \n    log \"INFO\" \"Backing up MinIO...\"\n    \n    # Check if MinIO container is running\n    if ! $COMPOSE_CMD ps minio | grep -q \"Up\" 2>/dev/null; then\n        log \"INFO\" \"MinIO container not running, skipping backup\"\n        return 0\n    fi\n    \n    # Copy MinIO data directory from container\n    local container_name=$($COMPOSE_CMD ps -q minio)\n    if [ -n \"$container_name\" ]; then\n        local minio_backup_dir=\"$backup_dir/minio_data\"\n        mkdir -p \"$minio_backup_dir\"\n        \n        if docker cp \"$container_name:/data\" \"$minio_backup_dir/\"; then\n            log \"SUCCESS\" \"MinIO data copied: $minio_backup_dir\"\n            \n            # Create tar archive\n            tar -czf \"$backup_dir/minio_data.tar.gz\" -C \"$minio_backup_dir\" data\n            rm -rf \"$minio_backup_dir\"\n            log \"SUCCESS\" \"MinIO backup archived\"\n        else\n            log \"ERROR\" \"Failed to copy MinIO data\"\n            return 1\n        fi\n    else\n        log \"ERROR\" \"MinIO container not found\"\n        return 1\n    fi\n    \n    return 0\n}\n\n# Function to create backup manifest\ncreate_backup_manifest() {\n    local backup_dir=\"$1\"\n    local services=\"$2\"\n    \n    local manifest_file=\"$backup_dir/backup_manifest.json\"\n    \n    cat > \"$manifest_file\" << EOF\n{\n  \"backup_info\": {\n    \"timestamp\": \"$(date -Iseconds)\",\n    \"version\": \"1.0\",\n    \"services\": \"$services\",\n    \"backup_type\": \"full\"\n  },\n  \"files\": [\nEOF\n    \n    # List all backup files\n    find \"$backup_dir\" -type f -not -name \"backup_manifest.json\" | while read -r file; do\n        local relative_path=$(echo \"$file\" | sed \"s|$backup_dir/||\")\n        local file_size=$(stat -f%z \"$file\" 2>/dev/null || stat -c%s \"$file\" 2>/dev/null || echo \"unknown\")\n        local file_hash=$(sha256sum \"$file\" 2>/dev/null | cut -d' ' -f1 || echo \"unknown\")\n        \n        echo \"    {\"\n        echo \"      \\\"path\\\": \\\"$relative_path\\\",\"\n        echo \"      \\\"size\\\": $file_size,\"\n        echo \"      \\\"sha256\\\": \\\"$file_hash\\\"\"\n        echo \"    },\"\n    done | sed '$ s/,$//' >> \"$manifest_file\"\n    \n    cat >> \"$manifest_file\" << EOF\n  ]\n}\nEOF\n    \n    log \"SUCCESS\" \"Backup manifest created: $manifest_file\"\n}\n\n# Function to show usage information\nshow_usage() {\n    echo \"AI Karen Database Stack Backup Script\"\n    echo \"\"\n    echo \"Usage: $0 [options]\"\n    echo \"\"\n    echo \"Options:\"\n    echo \"  --service <name>     Backup only specific service\"\n    echo \"  --output-dir <dir>   Custom backup output directory\"\n    echo \"  --compress           Compress entire backup directory\"\n    echo \"  --verify             Verify backup integrity after creation\"\n    echo \"  --help               Show this help message\"\n    echo \"\"\n    echo \"Services: postgres, redis, elasticsearch, milvus, duckdb, minio\"\n    echo \"\"\n    echo \"Examples:\"\n    echo \"  $0                           # Backup all services\"\n    echo \"  $0 --service postgres        # Backup only PostgreSQL\"\n    echo \"  $0 --compress                # Create compressed backup\"\n    echo \"  $0 --output-dir /tmp/backup  # Custom backup location\"\n}\n\n# Main function\nmain() {\n    local specific_service=\"\"\n    local output_dir=\"\"\n    local compress_backup=\"false\"\n    local verify_backup=\"false\"\n    \n    # Parse command line arguments\n    while [[ $# -gt 0 ]]; do\n        case $1 in\n            --service)\n                specific_service=\"$2\"\n                shift 2\n                ;;\n            --output-dir)\n                output_dir=\"$2\"\n                shift 2\n                ;;\n            --compress)\n                compress_backup=\"true\"\n                shift\n                ;;\n            --verify)\n                verify_backup=\"true\"\n                shift\n                ;;\n            --help)\n                show_usage\n                exit 0\n                ;;\n            *)\n                log \"ERROR\" \"Unknown option: $1\"\n                show_usage\n                exit 1\n                ;;\n        esac\n    done\n    \n    # Check Docker Compose availability\n    check_docker_compose\n    \n    # Create backup directory\n    local timestamp=$(date +%Y%m%d_%H%M%S)\n    if [ -n \"$output_dir\" ]; then\n        local backup_base_dir=\"$output_dir/$timestamp\"\n    else\n        local backup_base_dir=\"./backups/full/$timestamp\"\n    fi\n    \n    mkdir -p \"$backup_base_dir\"\n    log \"INFO\" \"Backup directory: $backup_base_dir\"\n    \n    # Install required tools\n    log \"INFO\" \"Installing required tools...\"\n    if command -v apk > /dev/null 2>&1; then\n        apk add --no-cache curl postgresql-client redis jq gzip tar > /dev/null 2>&1 || true\n    elif command -v apt-get > /dev/null 2>&1; then\n        apt-get update > /dev/null 2>&1 && apt-get install -y curl postgresql-client redis-tools jq gzip tar > /dev/null 2>&1 || true\n    fi\n    \n    # Perform backups\n    local services_backed_up=()\n    local backup_success=true\n    \n    if [ -n \"$specific_service\" ]; then\n        case \"$specific_service\" in\n            \"postgres\")\n                if backup_postgres \"$backup_base_dir\"; then\n                    services_backed_up+=(\"postgres\")\n                else\n                    backup_success=false\n                fi\n                ;;\n            \"redis\")\n                if backup_redis \"$backup_base_dir\"; then\n                    services_backed_up+=(\"redis\")\n                else\n                    backup_success=false\n                fi\n                ;;\n            \"elasticsearch\")\n                if backup_elasticsearch \"$backup_base_dir\"; then\n                    services_backed_up+=(\"elasticsearch\")\n                else\n                    backup_success=false\n                fi\n                ;;\n            \"milvus\")\n                if backup_milvus \"$backup_base_dir\"; then\n                    services_backed_up+=(\"milvus\")\n                else\n                    backup_success=false\n                fi\n                ;;\n            \"duckdb\")\n                if backup_duckdb \"$backup_base_dir\"; then\n                    services_backed_up+=(\"duckdb\")\n                else\n                    backup_success=false\n                fi\n                ;;\n            \"minio\")\n                if backup_minio \"$backup_base_dir\"; then\n                    services_backed_up+=(\"minio\")\n                else\n                    backup_success=false\n                fi\n                ;;\n            *)\n                log \"ERROR\" \"Unknown service: $specific_service\"\n                exit 1\n                ;;\n        esac\n    else\n        # Backup all services\n        backup_postgres \"$backup_base_dir\" && services_backed_up+=(\"postgres\") || backup_success=false\n        backup_redis \"$backup_base_dir\" && services_backed_up+=(\"redis\") || backup_success=false\n        backup_elasticsearch \"$backup_base_dir\" && services_backed_up+=(\"elasticsearch\") || backup_success=false\n        backup_milvus \"$backup_base_dir\" && services_backed_up+=(\"milvus\") || backup_success=false\n        backup_duckdb \"$backup_base_dir\" && services_backed_up+=(\"duckdb\") || backup_success=false\n        backup_minio \"$backup_base_dir\" && services_backed_up+=(\"minio\") || backup_success=false\n    fi\n    \n    # Create backup manifest\n    local services_list=$(IFS=','; echo \"${services_backed_up[*]}\")\n    create_backup_manifest \"$backup_base_dir\" \"$services_list\"\n    \n    # Compress backup if requested\n    if [ \"$compress_backup\" = \"true\" ]; then\n        log \"INFO\" \"Compressing backup directory...\"\n        local archive_name=\"ai_karen_backup_$timestamp.tar.gz\"\n        local archive_path=\"$(dirname \"$backup_base_dir\")/$archive_name\"\n        \n        if tar -czf \"$archive_path\" -C \"$(dirname \"$backup_base_dir\")\" \"$(basename \"$backup_base_dir\")\"; then\n            log \"SUCCESS\" \"Backup compressed: $archive_path\"\n            rm -rf \"$backup_base_dir\"\n        else\n            log \"ERROR\" \"Failed to compress backup\"\n            backup_success=false\n        fi\n    fi\n    \n    # Verify backup if requested\n    if [ \"$verify_backup\" = \"true\" ]; then\n        log \"INFO\" \"Verifying backup integrity...\"\n        # TODO: Implement backup verification\n        log \"WARN\" \"Backup verification not yet implemented\"\n    fi\n    \n    # Show results\n    echo \"\"\n    if [ \"$backup_success\" = \"true\" ]; then\n        log \"SUCCESS\" \"🎉 Backup completed successfully!\"\n        log \"INFO\" \"Services backed up: ${services_backed_up[*]}\"\n        if [ \"$compress_backup\" = \"true\" ]; then\n            log \"INFO\" \"Backup archive: $archive_path\"\n        else\n            log \"INFO\" \"Backup directory: $backup_base_dir\"\n        fi\n    else\n        log \"ERROR\" \"Backup completed with errors\"\n        log \"INFO\" \"Successfully backed up: ${services_backed_up[*]}\"\n        exit 1\n    fi\n}\n\n# Change to script directory\ncd \"$(dirname \"$0\")/..\"\n\n# Run main function with all arguments\nmain \"$@\"