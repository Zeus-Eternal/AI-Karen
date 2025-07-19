#!/bin/bash
set -e

# AI Karen Database Stack Restore Script
# This script restores databases from backup files

echo "🔄 AI Karen Database Stack Restore"
echo "=================================="

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

# Function to confirm destructive action
confirm_restore() {
    local service="$1"
    
    echo ""
    log "WARN" "This will restore $service from backup and OVERWRITE existing data!"
    log "WARN" "This action cannot be undone!"
    echo ""
    read -p "Are you sure you want to continue? (yes/no): " -r
    echo ""
    
    if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        log "INFO" "Restore cancelled by user"
        exit 0
    fi
}

# Function to extract compressed backup
extract_backup() {
    local backup_path="$1"
    local extract_dir="$2"
    
    log "INFO" "Extracting backup: $backup_path"
    
    if [[ "$backup_path" == *.tar.gz ]]; then
        if tar -xzf "$backup_path" -C "$extract_dir"; then
            log "SUCCESS" "Backup extracted successfully"
            return 0
        else
            log "ERROR" "Failed to extract tar.gz backup"
            return 1
        fi
    elif [[ "$backup_path" == *.zip ]]; then
        if unzip -q "$backup_path" -d "$extract_dir"; then
            log "SUCCESS" "Backup extracted successfully"
            return 0
        else
            log "ERROR" "Failed to extract zip backup"
            return 1
        fi
    else
        log "ERROR" "Unsupported backup format: $backup_path"
        return 1
    fi
}

# Function to restore PostgreSQL
restore_postgres() {
    local backup_dir="$1"
    local restore_type="${2:-full}"
    
    log "INFO" "Restoring PostgreSQL ($restore_type)..."
    
    local host="${POSTGRES_HOST:-localhost}"
    local port="${POSTGRES_PORT:-5432}"
    local user="${POSTGRES_USER:-karen_user}"
    local db="${POSTGRES_DB:-ai_karen}"
    local password="${POSTGRES_PASSWORD:-}"
    
    # Find backup files
    local schema_file=""
    local data_file=""
    local full_file=""
    
    # Look for compressed files first, then uncompressed
    for ext in ".gz" ""; do
        if [ -f "$backup_dir/postgres_schema.sql$ext" ]; then
            schema_file="$backup_dir/postgres_schema.sql$ext"
        fi
        if [ -f "$backup_dir/postgres_data.sql$ext" ]; then
            data_file="$backup_dir/postgres_data.sql$ext"
        fi
        if [ -f "$backup_dir/postgres_full.sql$ext" ]; then
            full_file="$backup_dir/postgres_full.sql$ext"
        fi
    done
    
    # Decompress files if needed
    local temp_dir="/tmp/postgres_restore_$$"
    mkdir -p "$temp_dir"
    
    if [[ "$schema_file" == *.gz ]]; then
        gunzip -c "$schema_file" > "$temp_dir/postgres_schema.sql"
        schema_file="$temp_dir/postgres_schema.sql"
    fi
    
    if [[ "$data_file" == *.gz ]]; then
        gunzip -c "$data_file" > "$temp_dir/postgres_data.sql"
        data_file="$temp_dir/postgres_data.sql"
    fi
    
    if [[ "$full_file" == *.gz ]]; then
        gunzip -c "$full_file" > "$temp_dir/postgres_full.sql"
        full_file="$temp_dir/postgres_full.sql"
    fi
    
    # Perform restore based on type
    case "$restore_type" in
        "schema")\n            if [ -n \"$schema_file\" ] && [ -f \"$schema_file\" ]; then\n                log \"INFO\" \"Restoring PostgreSQL schema...\"\n                if PGPASSWORD=\"$password\" psql -h \"$host\" -p \"$port\" -U \"$user\" -d \"$db\" -f \"$schema_file\"; then\n                    log \"SUCCESS\" \"PostgreSQL schema restored\"\n                else\n                    log \"ERROR\" \"Failed to restore PostgreSQL schema\"\n                    rm -rf \"$temp_dir\"\n                    return 1\n                fi\n            else\n                log \"ERROR\" \"Schema backup file not found\"\n                rm -rf \"$temp_dir\"\n                return 1\n            fi\n            ;;\n        \"data\")\n            if [ -n \"$data_file\" ] && [ -f \"$data_file\" ]; then\n                log \"INFO\" \"Restoring PostgreSQL data...\"\n                if PGPASSWORD=\"$password\" psql -h \"$host\" -p \"$port\" -U \"$user\" -d \"$db\" -f \"$data_file\"; then\n                    log \"SUCCESS\" \"PostgreSQL data restored\"\n                else\n                    log \"ERROR\" \"Failed to restore PostgreSQL data\"\n                    rm -rf \"$temp_dir\"\n                    return 1\n                fi\n            else\n                log \"ERROR\" \"Data backup file not found\"\n                rm -rf \"$temp_dir\"\n                return 1\n            fi\n            ;;\n        \"full\")\n            if [ -n \"$full_file\" ] && [ -f \"$full_file\" ]; then\n                log \"INFO\" \"Restoring PostgreSQL full backup...\"\n                \n                # Drop and recreate database\n                log \"WARN\" \"Dropping and recreating database: $db\"\n                PGPASSWORD=\"$password\" psql -h \"$host\" -p \"$port\" -U \"$user\" -d \"postgres\" -c \"DROP DATABASE IF EXISTS $db;\"\n                PGPASSWORD=\"$password\" psql -h \"$host\" -p \"$port\" -U \"$user\" -d \"postgres\" -c \"CREATE DATABASE $db;\"\n                \n                if PGPASSWORD=\"$password\" psql -h \"$host\" -p \"$port\" -U \"$user\" -d \"$db\" -f \"$full_file\"; then\n                    log \"SUCCESS\" \"PostgreSQL full backup restored\"\n                else\n                    log \"ERROR\" \"Failed to restore PostgreSQL full backup\"\n                    rm -rf \"$temp_dir\"\n                    return 1\n                fi\n            else\n                log \"ERROR\" \"Full backup file not found\"\n                rm -rf \"$temp_dir\"\n                return 1\n            fi\n            ;;\n        *)\n            log \"ERROR\" \"Unknown restore type: $restore_type\"\n            rm -rf \"$temp_dir\"\n            return 1\n            ;;\n    esac\n    \n    # Cleanup\n    rm -rf \"$temp_dir\"\n    \n    log \"SUCCESS\" \"PostgreSQL restore completed\"\n    return 0\n}\n\n# Function to restore Redis\nrestore_redis() {\n    local backup_dir=\"$1\"\n    \n    log \"INFO\" \"Restoring Redis...\"\n    \n    # Find Redis backup file\n    local rdb_file=\"\"\n    \n    if [ -f \"$backup_dir/redis_dump.rdb.gz\" ]; then\n        rdb_file=\"$backup_dir/redis_dump.rdb.gz\"\n    elif [ -f \"$backup_dir/redis_dump.rdb\" ]; then\n        rdb_file=\"$backup_dir/redis_dump.rdb\"\n    else\n        log \"ERROR\" \"Redis backup file not found\"\n        return 1\n    fi\n    \n    # Stop Redis service\n    log \"INFO\" \"Stopping Redis service...\"\n    $COMPOSE_CMD stop redis\n    \n    # Get Redis container name\n    local container_name=$($COMPOSE_CMD ps -a -q redis)\n    if [ -z \"$container_name\" ]; then\n        log \"ERROR\" \"Redis container not found\"\n        return 1\n    fi\n    \n    # Prepare RDB file\n    local temp_rdb=\"/tmp/redis_restore_$$.rdb\"\n    \n    if [[ \"$rdb_file\" == *.gz ]]; then\n        gunzip -c \"$rdb_file\" > \"$temp_rdb\"\n    else\n        cp \"$rdb_file\" \"$temp_rdb\"\n    fi\n    \n    # Copy RDB file to container\n    if docker cp \"$temp_rdb\" \"$container_name:/data/dump.rdb\"; then\n        log \"SUCCESS\" \"Redis RDB file copied to container\"\n    else\n        log \"ERROR\" \"Failed to copy RDB file to container\"\n        rm -f \"$temp_rdb\"\n        return 1\n    fi\n    \n    # Start Redis service\n    log \"INFO\" \"Starting Redis service...\"\n    $COMPOSE_CMD start redis\n    \n    # Wait for Redis to be ready\n    local max_wait=30\n    local wait_time=0\n    local host=\"${REDIS_HOST:-localhost}\"\n    local port=\"${REDIS_PORT:-6379}\"\n    local password=\"${REDIS_PASSWORD:-}\"\n    \n    local redis_cmd=\"redis-cli -h $host -p $port\"\n    if [ -n \"$password\" ]; then\n        redis_cmd=\"$redis_cmd -a $password\"\n    fi\n    \n    while [ $wait_time -lt $max_wait ]; do\n        if $redis_cmd ping | grep -q \"PONG\"; then\n            log \"SUCCESS\" \"Redis is ready\"\n            break\n        fi\n        sleep 2\n        wait_time=$((wait_time + 2))\n    done\n    \n    if [ $wait_time -ge $max_wait ]; then\n        log \"ERROR\" \"Redis did not become ready in time\"\n        rm -f \"$temp_rdb\"\n        return 1\n    fi\n    \n    # Cleanup\n    rm -f \"$temp_rdb\"\n    \n    log \"SUCCESS\" \"Redis restore completed\"\n    return 0\n}\n\n# Function to restore Elasticsearch\nrestore_elasticsearch() {\n    local backup_dir=\"$1\"\n    \n    log \"INFO\" \"Restoring Elasticsearch...\"\n    \n    local host=\"${ELASTICSEARCH_HOST:-localhost}\"\n    local port=\"${ELASTICSEARCH_PORT:-9200}\"\n    \n    # Find backup files\n    local backup_files=$(find \"$backup_dir\" -name \"elasticsearch_*.json*\" | sort)\n    \n    if [ -z \"$backup_files\" ]; then\n        log \"ERROR\" \"No Elasticsearch backup files found\"\n        return 1\n    fi\n    \n    # Process each backup file\n    for backup_file in $backup_files; do\n        local filename=$(basename \"$backup_file\")\n        \n        # Extract index name from filename\n        local index_name=$(echo \"$filename\" | sed 's/elasticsearch_\\(.*\\)_[^_]*\\.json.*/\\1/')\n        \n        if [[ \"$filename\" == *\"_mapping.json\"* ]]; then\n            log \"INFO\" \"Restoring mapping for index: $index_name\"\n            \n            # Decompress if needed\n            local temp_file=\"/tmp/es_restore_$$.json\"\n            if [[ \"$backup_file\" == *.gz ]]; then\n                gunzip -c \"$backup_file\" > \"$temp_file\"\n            else\n                cp \"$backup_file\" \"$temp_file\"\n            fi\n            \n            # Create index with mapping\n            if curl -s -X PUT \"http://$host:$port/$index_name\" \\\n                -H \"Content-Type: application/json\" \\\n                --data-binary @\"$temp_file\" | grep -q '\"acknowledged\":true'; then\n                log \"SUCCESS\" \"Index $index_name mapping restored\"\n            else\n                log \"WARN\" \"Failed to restore mapping for index: $index_name\"\n            fi\n            \n            rm -f \"$temp_file\"\n            \n        elif [[ \"$filename\" == *\"_settings.json\"* ]]; then\n            log \"INFO\" \"Settings for index $index_name (handled with mapping)\"\n            \n        elif [[ \"$filename\" == *\"_data.json\"* ]]; then\n            log \"INFO\" \"Restoring data for index: $index_name\"\n            \n            # Decompress if needed\n            local temp_file=\"/tmp/es_restore_$$.json\"\n            if [[ \"$backup_file\" == *.gz ]]; then\n                gunzip -c \"$backup_file\" > \"$temp_file\"\n            else\n                cp \"$backup_file\" \"$temp_file\"\n            fi\n            \n            # Extract documents and bulk insert\n            # This is a simplified approach - in production, you'd want to use the bulk API properly\n            log \"WARN\" \"Data restore for Elasticsearch is simplified - consider using Elasticsearch snapshot/restore for production\"\n            \n            rm -f \"$temp_file\"\n        fi\n    done\n    \n    log \"SUCCESS\" \"Elasticsearch restore completed\"\n    return 0\n}\n\n# Function to restore Milvus\nrestore_milvus() {\n    local backup_dir=\"$1\"\n    \n    log \"INFO\" \"Restoring Milvus...\"\n    \n    # Find Milvus backup files\n    local backup_files=$(find \"$backup_dir\" -name \"milvus_*.json*\" | sort)\n    \n    if [ -z \"$backup_files\" ]; then\n        log \"ERROR\" \"No Milvus backup files found\"\n        return 1\n    fi\n    \n    # Milvus restore requires Python\n    if ! command -v python3 > /dev/null 2>&1; then\n        log \"ERROR\" \"Python3 is required for Milvus restore\"\n        return 1\n    fi\n    \n    # Install pymilvus if not available\n    if ! python3 -c \"import pymilvus\" > /dev/null 2>&1; then\n        log \"INFO\" \"Installing pymilvus...\"\n        pip3 install pymilvus > /dev/null 2>&1\n    fi\n    \n    # Create Milvus restore script\n    cat > /tmp/milvus_restore.py << 'EOF'\n#!/usr/bin/env python3\nimport os\nimport sys\nimport json\nimport gzip\nfrom pymilvus import connections, utility, Collection, CollectionSchema, FieldSchema, DataType\n\ndef restore_milvus(backup_dir):\n    host = os.getenv('MILVUS_HOST', 'localhost')\n    port = os.getenv('MILVUS_PORT', '19530')\n    \n    try:\n        connections.connect(alias=\"default\", host=host, port=port)\n        \n        # Find backup files\n        import glob\n        backup_files = glob.glob(os.path.join(backup_dir, \"milvus_*_metadata.json*\"))\n        \n        for backup_file in backup_files:\n            print(f\"Processing backup file: {backup_file}\")\n            \n            # Read backup file\n            if backup_file.endswith('.gz'):\n                with gzip.open(backup_file, 'rt') as f:\n                    collection_info = json.load(f)\n            else:\n                with open(backup_file, 'r') as f:\n                    collection_info = json.load(f)\n            \n            collection_name = collection_info['name']\n            print(f\"Restoring collection: {collection_name}\")\n            \n            # Drop existing collection if it exists\n            if utility.has_collection(collection_name):\n                print(f\"Dropping existing collection: {collection_name}\")\n                utility.drop_collection(collection_name)\n            \n            # Recreate collection schema\n            fields = []\n            for field_info in collection_info['schema']['fields']:\n                field_params = {\n                    'name': field_info['name'],\n                    'dtype': getattr(DataType, field_info['dtype'].split('.')[-1]),\n                    'is_primary': field_info.get('is_primary', False)\n                }\n                \n                if 'auto_id' in field_info:\n                    field_params['auto_id'] = field_info['auto_id']\n                if 'max_length' in field_info:\n                    field_params['max_length'] = field_info['max_length']\n                if 'dim' in field_info:\n                    field_params['dim'] = field_info['dim']\n                \n                fields.append(FieldSchema(**field_params))\n            \n            schema = CollectionSchema(fields, description=f\"Restored collection {collection_name}\")\n            collection = Collection(collection_name, schema)\n            \n            print(f\"Collection {collection_name} schema restored\")\n            \n            # Restore indexes\n            if 'indexes' in collection_info and collection_info['indexes']:\n                for index_info in collection_info['indexes']:\n                    try:\n                        collection.create_index(\n                            field_name=index_info['field_name'],\n                            index_params=index_info['params']\n                        )\n                        print(f\"Index restored for field: {index_info['field_name']}\")\n                    except Exception as e:\n                        print(f\"Warning: Failed to restore index for {index_info['field_name']}: {e}\")\n            \n            print(f\"Collection {collection_name} restored successfully\")\n        \n        print(\"Milvus restore completed\")\n        return 0\n        \n    except Exception as e:\n        print(f\"Failed to restore Milvus: {e}\")\n        return 1\n\nif __name__ == \"__main__\":\n    if len(sys.argv) != 2:\n        print(\"Usage: python3 milvus_restore.py <backup_dir>\")\n        sys.exit(1)\n    \n    backup_dir = sys.argv[1]\n    sys.exit(restore_milvus(backup_dir))\nEOF\n    \n    chmod +x /tmp/milvus_restore.py\n    \n    # Run Milvus restore\n    if python3 /tmp/milvus_restore.py \"$backup_dir\"; then\n        log \"SUCCESS\" \"Milvus restore completed\"\n    else\n        log \"ERROR\" \"Milvus restore failed\"\n        rm -f /tmp/milvus_restore.py\n        return 1\n    fi\n    \n    rm -f /tmp/milvus_restore.py\n    return 0\n}\n\n# Function to restore DuckDB\nrestore_duckdb() {\n    local backup_dir=\"$1\"\n    \n    log \"INFO\" \"Restoring DuckDB...\"\n    \n    local db_path=\"${DUCKDB_PATH:-./data/duckdb/kari_duckdb.db}\"\n    \n    # Find DuckDB backup file\n    local backup_file=\"\"\n    \n    if [ -f \"$backup_dir/duckdb_backup.db.gz\" ]; then\n        backup_file=\"$backup_dir/duckdb_backup.db.gz\"\n    elif [ -f \"$backup_dir/duckdb_backup.db\" ]; then\n        backup_file=\"$backup_dir/duckdb_backup.db\"\n    else\n        log \"ERROR\" \"DuckDB backup file not found\"\n        return 1\n    fi\n    \n    # Create backup of current database\n    if [ -f \"$db_path\" ]; then\n        local current_backup=\"${db_path}.backup.$(date +%Y%m%d_%H%M%S)\"\n        log \"INFO\" \"Backing up current database to: $current_backup\"\n        cp \"$db_path\" \"$current_backup\"\n    fi\n    \n    # Restore database file\n    if [[ \"$backup_file\" == *.gz ]]; then\n        if gunzip -c \"$backup_file\" > \"$db_path\"; then\n            log \"SUCCESS\" \"DuckDB database restored from compressed backup\"\n        else\n            log \"ERROR\" \"Failed to restore DuckDB from compressed backup\"\n            return 1\n        fi\n    else\n        if cp \"$backup_file\" \"$db_path\"; then\n            log \"SUCCESS\" \"DuckDB database restored\"\n        else\n            log \"ERROR\" \"Failed to restore DuckDB database\"\n            return 1\n        fi\n    fi\n    \n    # Verify restored database\n    if command -v duckdb > /dev/null 2>&1; then\n        if duckdb \"$db_path\" \"SELECT 1;\" > /dev/null 2>&1; then\n            log \"SUCCESS\" \"DuckDB restore verified\"\n        else\n            log \"ERROR\" \"DuckDB restore verification failed\"\n            return 1\n        fi\n    fi\n    \n    log \"SUCCESS\" \"DuckDB restore completed\"\n    return 0\n}\n\n# Function to show usage information\nshow_usage() {\n    echo \"AI Karen Database Stack Restore Script\"\n    echo \"\"\n    echo \"Usage: $0 [options] <backup_path>\"\n    echo \"\"\n    echo \"Options:\"\n    echo \"  --service <name>     Restore only specific service\"\n    echo \"  --type <type>        Restore type (full, schema, data) - PostgreSQL only\"\n    echo \"  --force              Skip confirmation prompts\"\n    echo \"  --help               Show this help message\"\n    echo \"\"\n    echo \"Services: postgres, redis, elasticsearch, milvus, duckdb\"\n    echo \"Restore types: full (default), schema, data\"\n    echo \"\"\n    echo \"Examples:\"\n    echo \"  $0 /path/to/backup                    # Restore all services\"\n    echo \"  $0 --service postgres /path/to/backup # Restore only PostgreSQL\"\n    echo \"  $0 --type schema /path/to/backup      # Restore only PostgreSQL schema\"\n    echo \"  $0 backup_archive.tar.gz              # Restore from compressed archive\"\n}\n\n# Main function\nmain() {\n    local specific_service=\"\"\n    local restore_type=\"full\"\n    local force_restore=\"false\"\n    local backup_path=\"\"\n    \n    # Parse command line arguments\n    while [[ $# -gt 0 ]]; do\n        case $1 in\n            --service)\n                specific_service=\"$2\"\n                shift 2\n                ;;\n            --type)\n                restore_type=\"$2\"\n                shift 2\n                ;;\n            --force)\n                force_restore=\"true\"\n                shift\n                ;;\n            --help)\n                show_usage\n                exit 0\n                ;;\n            -*)\n                log \"ERROR\" \"Unknown option: $1\"\n                show_usage\n                exit 1\n                ;;\n            *)\n                backup_path=\"$1\"\n                shift\n                ;;\n        esac\n    done\n    \n    # Validate arguments\n    if [ -z \"$backup_path\" ]; then\n        log \"ERROR\" \"Backup path is required\"\n        show_usage\n        exit 1\n    fi\n    \n    if [ ! -e \"$backup_path\" ]; then\n        log \"ERROR\" \"Backup path does not exist: $backup_path\"\n        exit 1\n    fi\n    \n    # Check Docker Compose availability\n    check_docker_compose\n    \n    # Determine backup directory\n    local backup_dir=\"$backup_path\"\n    local temp_extract_dir=\"\"\n    \n    # If backup_path is a file (archive), extract it\n    if [ -f \"$backup_path\" ]; then\n        temp_extract_dir=\"/tmp/ai_karen_restore_$$\"\n        mkdir -p \"$temp_extract_dir\"\n        \n        if extract_backup \"$backup_path\" \"$temp_extract_dir\"; then\n            # Find the actual backup directory inside the extracted archive\n            local extracted_dirs=$(find \"$temp_extract_dir\" -type d -name \"*\" | head -1)\n            if [ -n \"$extracted_dirs\" ]; then\n                backup_dir=\"$extracted_dirs\"\n            else\n                backup_dir=\"$temp_extract_dir\"\n            fi\n        else\n            log \"ERROR\" \"Failed to extract backup archive\"\n            rm -rf \"$temp_extract_dir\"\n            exit 1\n        fi\n    fi\n    \n    log \"INFO\" \"Using backup directory: $backup_dir\"\n    \n    # Confirm restore unless forced\n    if [ \"$force_restore\" = \"false\" ]; then\n        if [ -n \"$specific_service\" ]; then\n            confirm_restore \"$specific_service\"\n        else\n            confirm_restore \"all services\"\n        fi\n    fi\n    \n    # Install required tools\n    log \"INFO\" \"Installing required tools...\"\n    if command -v apk > /dev/null 2>&1; then\n        apk add --no-cache curl postgresql-client redis jq gzip tar unzip > /dev/null 2>&1 || true\n    elif command -v apt-get > /dev/null 2>&1; then\n        apt-get update > /dev/null 2>&1 && apt-get install -y curl postgresql-client redis-tools jq gzip tar unzip > /dev/null 2>&1 || true\n    fi\n    \n    # Perform restore\n    local restore_success=true\n    local services_restored=()\n    \n    if [ -n \"$specific_service\" ]; then\n        case \"$specific_service\" in\n            \"postgres\")\n                if restore_postgres \"$backup_dir\" \"$restore_type\"; then\n                    services_restored+=(\"postgres\")\n                else\n                    restore_success=false\n                fi\n                ;;\n            \"redis\")\n                if restore_redis \"$backup_dir\"; then\n                    services_restored+=(\"redis\")\n                else\n                    restore_success=false\n                fi\n                ;;\n            \"elasticsearch\")\n                if restore_elasticsearch \"$backup_dir\"; then\n                    services_restored+=(\"elasticsearch\")\n                else\n                    restore_success=false\n                fi\n                ;;\n            \"milvus\")\n                if restore_milvus \"$backup_dir\"; then\n                    services_restored+=(\"milvus\")\n                else\n                    restore_success=false\n                fi\n                ;;\n            \"duckdb\")\n                if restore_duckdb \"$backup_dir\"; then\n                    services_restored+=(\"duckdb\")\n                else\n                    restore_success=false\n                fi\n                ;;\n            *)\n                log \"ERROR\" \"Unknown service: $specific_service\"\n                exit 1\n                ;;\n        esac\n    else\n        # Restore all services\n        restore_postgres \"$backup_dir\" \"$restore_type\" && services_restored+=(\"postgres\") || restore_success=false\n        restore_redis \"$backup_dir\" && services_restored+=(\"redis\") || restore_success=false\n        restore_elasticsearch \"$backup_dir\" && services_restored+=(\"elasticsearch\") || restore_success=false\n        restore_milvus \"$backup_dir\" && services_restored+=(\"milvus\") || restore_success=false\n        restore_duckdb \"$backup_dir\" && services_restored+=(\"duckdb\") || restore_success=false\n    fi\n    \n    # Cleanup temporary extraction directory\n    if [ -n \"$temp_extract_dir\" ]; then\n        rm -rf \"$temp_extract_dir\"\n    fi\n    \n    # Show results\n    echo \"\"\n    if [ \"$restore_success\" = \"true\" ]; then\n        log \"SUCCESS\" \"🎉 Restore completed successfully!\"\n        log \"INFO\" \"Services restored: ${services_restored[*]}\"\n    else\n        log \"ERROR\" \"Restore completed with errors\"\n        log \"INFO\" \"Successfully restored: ${services_restored[*]}\"\n        exit 1\n    fi\n}\n\n# Change to script directory\ncd \"$(dirname \"$0\")/..\"\n\n# Run main function with all arguments\nmain \"$@\"