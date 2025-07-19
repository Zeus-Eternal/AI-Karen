#!/bin/bash
set -e

# AI Karen Database Stack Monitoring Script
# This script provides real-time monitoring of database services

echo "📊 AI Karen Database Stack Monitor"
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

# Function to get container stats
get_container_stats() {
    local service="$1"
    local container_id=$($COMPOSE_CMD ps -q "$service" 2>/dev/null)
    
    if [ -n "$container_id" ]; then
        docker stats "$container_id" --no-stream --format "table {{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}" | tail -n +2
    else
        echo "N/A\tN/A\tN/A\tN/A"
    fi
}

# Function to get service status
get_service_status() {
    local service="$1"
    local status=$($COMPOSE_CMD ps "$service" --format "table {{.Status}}" 2>/dev/null | tail -n +2)
    
    if echo "$status" | grep -q "Up"; then
        if echo "$status" | grep -q "healthy"; then
            echo "🟢 Healthy"
        else
            echo "🟡 Running"
        fi
    elif echo "$status" | grep -q "Exit"; then
        echo "🔴 Stopped"
    else
        echo "⚫ Unknown"
    fi
}

# Function to monitor PostgreSQL
monitor_postgres() {
    local host="${POSTGRES_HOST:-localhost}"
    local port="${POSTGRES_PORT:-5432}"
    local user="${POSTGRES_USER:-karen_user}"
    local db="${POSTGRES_DB:-ai_karen}"
    local password="${POSTGRES_PASSWORD:-}"
    
    echo "PostgreSQL Metrics:"
    echo "=================="
    
    # Connection status
    if PGPASSWORD="$password" pg_isready -h "$host" -p "$port" -U "$user" -d "$db" &> /dev/null; then
        echo "Status: 🟢 Connected"
    else
        echo "Status: 🔴 Disconnected"
        return
    fi
    
    # Database size
    local db_size=$(PGPASSWORD="$password" psql -h "$host" -p "$port" -U "$user" -d "$db" -t -c \
        "SELECT pg_size_pretty(pg_database_size('$db'));" 2>/dev/null | tr -d ' ' || echo "unknown")
    echo "Database Size: $db_size"
    
    # Active connections
    local active_conn=$(PGPASSWORD="$password" psql -h "$host" -p "$port" -U "$user" -d "$db" -t -c \
        "SELECT COUNT(*) FROM pg_stat_activity WHERE state = 'active';" 2>/dev/null | tr -d ' ' || echo "unknown")
    echo "Active Connections: $active_conn"
    
    # Total connections
    local total_conn=$(PGPASSWORD="$password" psql -h "$host" -p "$port" -U "$user" -d "$db" -t -c \
        "SELECT COUNT(*) FROM pg_stat_activity;" 2>/dev/null | tr -d ' ' || echo "unknown")
    echo "Total Connections: $total_conn"
    
    # Slow queries (queries running > 5 seconds)
    local slow_queries=$(PGPASSWORD="$password" psql -h "$host" -p "$port" -U "$user" -d "$db" -t -c \
        "SELECT COUNT(*) FROM pg_stat_activity WHERE state = 'active' AND now() - query_start > interval '5 seconds';" 2>/dev/null | tr -d ' ' || echo "unknown")
    echo "Slow Queries (>5s): $slow_queries"
    
    # Table count
    local table_count=$(PGPASSWORD="$password" psql -h "$host" -p "$port" -U "$user" -d "$db" -t -c \
        "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" 2>/dev/null | tr -d ' ' || echo "unknown")
    echo "Tables: $table_count"
    
    echo ""
}

# Function to monitor Redis
monitor_redis() {
    local host="${REDIS_HOST:-localhost}"
    local port="${REDIS_PORT:-6379}"
    local password="${REDIS_PASSWORD:-}"
    
    echo "Redis Metrics:"
    echo "============="
    
    local redis_cmd="redis-cli -h $host -p $port"
    if [ -n "$password" ]; then
        redis_cmd="$redis_cmd -a $password"
    fi
    
    # Connection status
    if $redis_cmd ping | grep -q "PONG" 2>/dev/null; then
        echo "Status: 🟢 Connected"
    else
        echo "Status: 🔴 Disconnected"
        return
    fi
    
    # Memory usage
    local used_memory=$($redis_cmd info memory | grep "used_memory_human:" | cut -d':' -f2 | tr -d '\r' || echo "unknown")
    echo "Memory Used: $used_memory"
    
    # Peak memory
    local peak_memory=$($redis_cmd info memory | grep "used_memory_peak_human:" | cut -d':' -f2 | tr -d '\r' || echo "unknown")
    echo "Peak Memory: $peak_memory"
    
    # Connected clients
    local connected_clients=$($redis_cmd info clients | grep "connected_clients:" | cut -d':' -f2 | tr -d '\r' || echo "unknown")
    echo "Connected Clients: $connected_clients"
    
    # Total commands processed
    local total_commands=$($redis_cmd info stats | grep "total_commands_processed:" | cut -d':' -f2 | tr -d '\r' || echo "unknown")
    echo "Total Commands: $total_commands"
    
    # Keyspace hits/misses
    local keyspace_hits=$($redis_cmd info stats | grep "keyspace_hits:" | cut -d':' -f2 | tr -d '\r' || echo "unknown")
    local keyspace_misses=$($redis_cmd info stats | grep "keyspace_misses:" | cut -d':' -f2 | tr -d '\r' || echo "unknown")
    echo "Cache Hits: $keyspace_hits"
    echo "Cache Misses: $keyspace_misses"
    
    # Total keys
    local total_keys=$($redis_cmd info keyspace | grep -o "keys=[0-9]*" | cut -d'=' -f2 | paste -sd+ | bc 2>/dev/null || echo "0")
    echo "Total Keys: $total_keys"
    
    echo ""
}

# Function to monitor Elasticsearch
monitor_elasticsearch() {
    local host="${ELASTICSEARCH_HOST:-localhost}"
    local port="${ELASTICSEARCH_PORT:-9200}"
    
    echo "Elasticsearch Metrics:"
    echo "====================="
    
    # Connection status
    if curl -s -f "http://$host:$port/_cluster/health" > /dev/null; then
        echo "Status: 🟢 Connected"
    else
        echo "Status: 🔴 Disconnected"
        return
    fi
    
    # Cluster health
    local cluster_status=$(curl -s "http://$host:$port/_cluster/health" | jq -r '.status' 2>/dev/null || echo "unknown")
    case "$cluster_status" in
        "green") echo "Cluster Health: 🟢 Green" ;;
        "yellow") echo "Cluster Health: 🟡 Yellow" ;;
        "red") echo "Cluster Health: 🔴 Red" ;;
        *) echo "Cluster Health: ⚫ $cluster_status" ;;
    esac
    
    # Node count
    local node_count=$(curl -s "http://$host:$port/_cluster/health" | jq -r '.number_of_nodes' 2>/dev/null || echo "unknown")
    echo "Nodes: $node_count"
    
    # Index count
    local index_count=$(curl -s "http://$host:$port/_cat/indices?format=json" | jq '. | length' 2>/dev/null || echo "unknown")
    echo "Indices: $index_count"
    
    # Document count
    local doc_count=$(curl -s "http://$host:$port/_cat/indices?format=json" | jq '[.[].\"docs.count\" | tonumber] | add' 2>/dev/null || echo "unknown")
    echo "Documents: $doc_count"
    
    # Store size
    local store_size=$(curl -s "http://$host:$port/_cat/indices?format=json" | jq -r '[.[].\"store.size\"] | join(\", \")' 2>/dev/null | head -c 50 || echo "unknown")
    echo "Store Size: $store_size"
    
    # Active shards
    local active_shards=$(curl -s "http://$host:$port/_cluster/health" | jq -r '.active_shards' 2>/dev/null || echo "unknown")
    echo "Active Shards: $active_shards"
    
    echo ""
}

# Function to monitor Milvus
monitor_milvus() {
    local host="${MILVUS_HOST:-localhost}"
    local port="${MILVUS_PORT:-19530}"
    
    echo "Milvus Metrics:"
    echo "==============="
    
    # Check if Python is available for detailed monitoring
    if command -v python3 > /dev/null 2>&1; then
        # Create temporary monitoring script
        cat > /tmp/milvus_monitor.py << 'EOF'
#!/usr/bin/env python3
import os
import sys
from pymilvus import connections, utility

def monitor_milvus():
    host = os.getenv('MILVUS_HOST', 'localhost')
    port = os.getenv('MILVUS_PORT', '19530')
    
    try:
        connections.connect(alias="default", host=host, port=port)
        print("Status: 🟢 Connected")
        
        # Get collections
        collections = utility.list_collections()
        print(f"Collections: {len(collections)}")
        
        # Get collection details
        total_entities = 0
        for collection_name in collections:
            try:
                from pymilvus import Collection
                collection = Collection(collection_name)
                collection.load()
                entities = collection.num_entities
                total_entities += entities
                print(f"  - {collection_name}: {entities} entities")
            except Exception as e:
                print(f"  - {collection_name}: Error ({e})")
        
        print(f"Total Entities: {total_entities}")
        
    except Exception as e:
        print("Status: 🔴 Disconnected")
        print(f"Error: {e}")

if __name__ == "__main__":
    monitor_milvus()
EOF
        
        chmod +x /tmp/milvus_monitor.py
        
        # Install pymilvus if not available
        if ! python3 -c "import pymilvus" > /dev/null 2>&1; then
            pip3 install pymilvus > /dev/null 2>&1
        fi
        
        # Run monitoring
        python3 /tmp/milvus_monitor.py
        rm -f /tmp/milvus_monitor.py
    else
        # Basic port check
        if nc -z "$host" "$port" 2>/dev/null; then
            echo "Status: 🟢 Port Accessible"
        else
            echo "Status: 🔴 Port Not Accessible"
        fi
        echo "Collections: Unknown (Python required for details)"
    fi
    
    echo ""
}

# Function to monitor DuckDB
monitor_duckdb() {
    local db_path="${DUCKDB_PATH:-./data/duckdb/kari_duckdb.db}"
    
    echo "DuckDB Metrics:"
    echo "==============="
    
    if [ -f "$db_path" ]; then
        echo "Status: 🟢 File Exists"
        
        # File size
        local file_size=$(du -h "$db_path" | cut -f1)
        echo "File Size: $file_size"
        
        # Last modified
        local last_modified=$(stat -c %y "$db_path" 2>/dev/null || stat -f %Sm "$db_path" 2>/dev/null || echo "unknown")
        echo "Last Modified: $last_modified"
        
        # Database info (if DuckDB CLI is available)
        if command -v duckdb > /dev/null 2>&1; then
            local table_count=$(duckdb "$db_path" "SELECT COUNT(*) FROM information_schema.tables;" 2>/dev/null || echo "unknown")
            echo "Tables: $table_count"
            
            local version=$(duckdb "$db_path" "SELECT version();" 2>/dev/null | head -n1 || echo "unknown")
            echo "Version: $version"
        else
            echo "Tables: Unknown (DuckDB CLI not available)"
        fi
    else
        echo "Status: 🔴 File Not Found"
        echo "Path: $db_path"
    fi
    
    echo ""
}

# Function to monitor system resources
monitor_system() {
    echo "System Resources:"
    echo "================="
    
    # CPU usage
    if command -v top > /dev/null 2>&1; then
        local cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1 || echo "unknown")
        echo "CPU Usage: ${cpu_usage}%"
    fi
    
    # Memory usage
    if command -v free > /dev/null 2>&1; then
        local mem_info=$(free -h | grep Mem)\n        local mem_total=$(echo \"$mem_info\" | awk '{print $2}')\n        local mem_used=$(echo \"$mem_info\" | awk '{print $3}')\n        local mem_percent=$(free | grep Mem | awk '{printf \"%.1f\", $3/$2 * 100.0}')\n        echo \"Memory: $mem_used / $mem_total (${mem_percent}%)\"\n    fi\n    \n    # Disk usage\n    local disk_usage=$(df -h . | tail -n1 | awk '{print $5}' | tr -d '%')\n    local disk_used=$(df -h . | tail -n1 | awk '{print $3}')\n    local disk_total=$(df -h . | tail -n1 | awk '{print $2}')\n    echo \"Disk: $disk_used / $disk_total (${disk_usage}%)\"\n    \n    # Load average\n    if [ -f /proc/loadavg ]; then\n        local load_avg=$(cat /proc/loadavg | cut -d' ' -f1-3)\n        echo \"Load Average: $load_avg\"\n    fi\n    \n    echo \"\"\n}\n\n# Function to display container stats table\ndisplay_container_stats() {\n    echo \"Container Resource Usage:\"\n    echo \"========================\"\n    printf \"%-15s %-10s %-8s %-20s %-15s %-15s\\n\" \"SERVICE\" \"STATUS\" \"CPU%\" \"MEMORY\" \"NET I/O\" \"BLOCK I/O\"\n    printf \"%-15s %-10s %-8s %-20s %-15s %-15s\\n\" \"-------\" \"------\" \"----\" \"------\" \"-------\" \"---------\"\n    \n    local services=(\"postgres\" \"redis\" \"elasticsearch\" \"milvus\" \"etcd\" \"minio\")\n    \n    for service in \"${services[@]}\"; do\n        if $COMPOSE_CMD ps \"$service\" &> /dev/null; then\n            local status=$(get_service_status \"$service\")\n            local stats=$(get_container_stats \"$service\")\n            \n            if [ \"$stats\" != \"N/A\\tN/A\\tN/A\\tN/A\" ]; then\n                local cpu=$(echo \"$stats\" | cut -f1)\n                local memory=$(echo \"$stats\" | cut -f2)\n                local net_io=$(echo \"$stats\" | cut -f3)\n                local block_io=$(echo \"$stats\" | cut -f4)\n                \n                printf \"%-15s %-10s %-8s %-20s %-15s %-15s\\n\" \"$service\" \"$status\" \"$cpu\" \"$memory\" \"$net_io\" \"$block_io\"\n            else\n                printf \"%-15s %-10s %-8s %-20s %-15s %-15s\\n\" \"$service\" \"$status\" \"N/A\" \"N/A\" \"N/A\" \"N/A\"\n            fi\n        fi\n    done\n    \n    echo \"\"\n}\n\n# Function to show logs summary\nshow_logs_summary() {\n    echo \"Recent Log Activity:\"\n    echo \"===================\"\n    \n    local services=(\"postgres\" \"redis\" \"elasticsearch\" \"milvus\")\n    \n    for service in \"${services[@]}\"; do\n        if $COMPOSE_CMD ps \"$service\" &> /dev/null; then\n            echo \"$service:\"\n            local recent_logs=$($COMPOSE_CMD logs --tail=3 \"$service\" 2>/dev/null | tail -n 3 || echo \"  No recent logs\")\n            if [ -n \"$recent_logs\" ]; then\n                echo \"$recent_logs\" | sed 's/^/  /'\n            else\n                echo \"  No recent logs\"\n            fi\n            echo \"\"\n        fi\n    done\n}\n\n# Function to run continuous monitoring\ncontinuous_monitor() {\n    local interval=\"${1:-10}\"\n    \n    log \"INFO\" \"Starting continuous monitoring (interval: ${interval}s)\"\n    log \"INFO\" \"Press Ctrl+C to stop\"\n    echo \"\"\n    \n    while true; do\n        clear\n        echo \"AI Karen Database Stack Monitor - $(date)\"\n        echo \"========================================\"\n        echo \"\"\n        \n        display_container_stats\n        monitor_system\n        monitor_postgres\n        monitor_redis\n        monitor_elasticsearch\n        monitor_milvus\n        monitor_duckdb\n        \n        echo \"Next update in ${interval} seconds... (Press Ctrl+C to stop)\"\n        sleep \"$interval\"\n    done\n}\n\n# Function to show usage information\nshow_usage() {\n    echo \"AI Karen Database Stack Monitoring Script\"\n    echo \"\"\n    echo \"Usage: $0 [options]\"\n    echo \"\"\n    echo \"Options:\"\n    echo \"  --service <name>     Monitor only specific service\"\n    echo \"  --continuous         Run continuous monitoring\"\n    echo \"  --interval <sec>     Update interval for continuous mode (default: 10)\"\n    echo \"  --stats-only         Show only container stats\"\n    echo \"  --logs               Show recent log activity\"\n    echo \"  --help               Show this help message\"\n    echo \"\"\n    echo \"Services: postgres, redis, elasticsearch, milvus, duckdb, system\"\n    echo \"\"\n    echo \"Examples:\"\n    echo \"  $0                           # One-time monitoring of all services\"\n    echo \"  $0 --service postgres        # Monitor only PostgreSQL\"\n    echo \"  $0 --continuous              # Continuous monitoring\"\n    echo \"  $0 --continuous --interval 5 # Continuous monitoring every 5 seconds\"\n    echo \"  $0 --stats-only              # Show only container resource stats\"\n}\n\n# Main function\nmain() {\n    local specific_service=\"\"\n    local continuous_mode=\"false\"\n    local interval=\"10\"\n    local stats_only=\"false\"\n    local show_logs=\"false\"\n    \n    # Parse command line arguments\n    while [[ $# -gt 0 ]]; do\n        case $1 in\n            --service)\n                specific_service=\"$2\"\n                shift 2\n                ;;\n            --continuous)\n                continuous_mode=\"true\"\n                shift\n                ;;\n            --interval)\n                interval=\"$2\"\n                shift 2\n                ;;\n            --stats-only)\n                stats_only=\"true\"\n                shift\n                ;;\n            --logs)\n                show_logs=\"true\"\n                shift\n                ;;\n            --help)\n                show_usage\n                exit 0\n                ;;\n            *)\n                log \"ERROR\" \"Unknown option: $1\"\n                show_usage\n                exit 1\n                ;;\n        esac\n    done\n    \n    # Validate interval\n    if ! [[ \"$interval\" =~ ^[0-9]+$ ]] || [ \"$interval\" -lt 1 ]; then\n        log \"ERROR\" \"Interval must be a positive number\"\n        exit 1\n    fi\n    \n    # Check Docker Compose availability\n    check_docker_compose\n    \n    # Install required tools\n    if command -v apk > /dev/null 2>&1; then\n        apk add --no-cache curl postgresql-client redis jq bc netcat-openbsd > /dev/null 2>&1 || true\n    elif command -v apt-get > /dev/null 2>&1; then\n        apt-get update > /dev/null 2>&1 && apt-get install -y curl postgresql-client redis-tools jq bc netcat > /dev/null 2>&1 || true\n    fi\n    \n    # Run monitoring based on options\n    if [ \"$continuous_mode\" = \"true\" ]; then\n        continuous_monitor \"$interval\"\n    elif [ \"$stats_only\" = \"true\" ]; then\n        display_container_stats\n    elif [ \"$show_logs\" = \"true\" ]; then\n        show_logs_summary\n    elif [ -n \"$specific_service\" ]; then\n        case \"$specific_service\" in\n            \"postgres\")\n                monitor_postgres\n                ;;\n            \"redis\")\n                monitor_redis\n                ;;\n            \"elasticsearch\")\n                monitor_elasticsearch\n                ;;\n            \"milvus\")\n                monitor_milvus\n                ;;\n            \"duckdb\")\n                monitor_duckdb\n                ;;\n            \"system\")\n                monitor_system\n                ;;\n            *)\n                log \"ERROR\" \"Unknown service: $specific_service\"\n                exit 1\n                ;;\n        esac\n    else\n        # One-time monitoring of all services\n        display_container_stats\n        monitor_system\n        monitor_postgres\n        monitor_redis\n        monitor_elasticsearch\n        monitor_milvus\n        monitor_duckdb\n    fi\n}\n\n# Change to script directory\ncd \"$(dirname \"$0\")/..\"\n\n# Run main function with all arguments\nmain \"$@\"