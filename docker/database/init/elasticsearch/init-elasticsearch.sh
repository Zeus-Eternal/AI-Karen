#!/bin/bash
set -e

# Elasticsearch Initialization Script for AI Karen
# This script sets up Elasticsearch indices and configurations

echo "🔍 Initializing Elasticsearch for AI Karen..."

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Function to wait for Elasticsearch to be ready
wait_for_elasticsearch() {
    local host="${ELASTICSEARCH_HOST:-localhost}"
    local port="${ELASTICSEARCH_PORT:-9200}"
    local max_attempts=30
    local attempt=1
    
    log "Waiting for Elasticsearch to be ready at $host:$port..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s -f "http://$host:$port/_cluster/health" > /dev/null 2>&1; then
            log "✅ Elasticsearch is ready!"
            return 0
        fi
        
        log "Attempt $attempt/$max_attempts: Elasticsearch not ready yet, waiting..."
        sleep 5
        attempt=$((attempt + 1))
    done
    
    log "❌ Elasticsearch failed to become ready after $max_attempts attempts"
    return 1
}

# Function to create index with mapping
create_index() {
    local index_name="$1"
    local mapping_file="$2"
    local host="${ELASTICSEARCH_HOST:-localhost}"
    local port="${ELASTICSEARCH_PORT:-9200}"
    
    log "Creating index: $index_name"
    
    if [ -f "$mapping_file" ]; then
        # Check if index already exists
        if curl -s -f "http://$host:$port/$index_name" > /dev/null 2>&1; then
            log "Index $index_name already exists, skipping creation"
            return 0
        fi
        
        # Create index with mapping
        response=$(curl -s -X PUT "http://$host:$port/$index_name" \
            -H "Content-Type: application/json" \
            -d @"$mapping_file")
        
        if echo "$response" | grep -q '"acknowledged":true'; then
            log "✅ Index $index_name created successfully"
        else
            log "❌ Failed to create index $index_name: $response"
            return 1
        fi
    else
        log "⚠️  Mapping file $mapping_file not found for index $index_name"
        return 1
    fi
}

# Function to create index template
create_template() {
    local template_name="$1"
    local template_file="$2"
    local host="${ELASTICSEARCH_HOST:-localhost}"
    local port="${ELASTICSEARCH_PORT:-9200}"
    
    log "Creating index template: $template_name"
    
    if [ -f "$template_file" ]; then
        response=$(curl -s -X PUT "http://$host:$port/_index_template/$template_name" \
            -H "Content-Type: application/json" \
            -d @"$template_file")
        
        if echo "$response" | grep -q '"acknowledged":true'; then
            log "✅ Template $template_name created successfully"
        else
            log "❌ Failed to create template $template_name: $response"
            return 1
        fi
    else
        log "⚠️  Template file $template_file not found"
        return 1
    fi
}

# Install curl if not present
if ! command -v curl &> /dev/null; then
    log "Installing curl..."
    # Try different package managers
    if command -v apk &> /dev/null; then
        apk add --no-cache curl
    elif command -v apt-get &> /dev/null; then
        apt-get update && apt-get install -y curl
    elif command -v yum &> /dev/null; then
        yum install -y curl
    elif command -v pacman &> /dev/null; then
        pacman -S --noconfirm curl
    else
        log "❌ No known package manager found. Please install curl manually."
        return 1
    fi
fi

# Wait for Elasticsearch to be ready
wait_for_elasticsearch

# Create indices from mapping files
log "Creating Elasticsearch indices..."
log "Current directory: $(pwd)"

# Memory index for AI Karen memory storage
create_index "ai_karen_memory" "$(dirname "$0")/../../migrations/elasticsearch/memory_index.json"

# Document index for general document storage
create_index "ai_karen_documents" "$(dirname "$0")/../../migrations/elasticsearch/document_index.json"

# Analytics index for system metrics and analytics
create_index "ai_karen_analytics" "$(dirname "$0")/../../migrations/elasticsearch/analytics_index.json"

# Logs index for application logs
create_index "ai_karen_logs" "$(dirname "$0")/../../migrations/elasticsearch/logs_index.json"

# Create index templates
log "Creating index templates..."

# Template for time-series data
if [ -f "$(dirname "$0")/../../migrations/elasticsearch/timeseries_template.json" ]; then
    create_template "ai_karen_timeseries" "$(dirname "$0")/../../migrations/elasticsearch/timeseries_template.json"
fi

# Configure cluster settings
log "Configuring cluster settings..."
curl -s -X PUT "http://${ELASTICSEARCH_HOST:-localhost}:${ELASTICSEARCH_PORT:-9200}/_cluster/settings" \
    -H "Content-Type: application/json" \
    -d '{
        "persistent": {
            "cluster.routing.allocation.disk.threshold.enabled": true,
            "cluster.routing.allocation.disk.watermark.low": "85%",
            "cluster.routing.allocation.disk.watermark.high": "90%",
            "cluster.routing.allocation.disk.watermark.flood_stage": "95%",
            "indices.recovery.max_bytes_per_sec": "100mb"
        }
    }'

# Create index lifecycle policies
log "Creating index lifecycle policies..."
curl -s -X PUT "http://${ELASTICSEARCH_HOST:-localhost}:${ELASTICSEARCH_PORT:-9200}/_ilm/policy/ai_karen_logs_policy" \
    -H "Content-Type: application/json" \
    -d '{
        "policy": {
            "phases": {
                "hot": {
                    "actions": {
                        "rollover": {
                            "max_size": "1GB",
                            "max_age": "7d"
                        }
                    }
                },
                "warm": {
                    "min_age": "7d",
                    "actions": {
                        "shrink": {
                            "number_of_shards": 1
                        }
                    }
                },
                "delete": {
                    "min_age": "30d"
                }
            }
        }
    }'

# Verify indices were created
log "Verifying indices..."
indices_response=$(curl -s "http://${ELASTICSEARCH_HOST:-localhost}:${ELASTICSEARCH_PORT:-9200}/_cat/indices?v")
log "Current indices:"
echo "$indices_response"

# Check cluster health
log "Checking cluster health..."
health_response=$(curl -s "http://${ELASTICSEARCH_HOST:-localhost}:${ELASTICSEARCH_PORT:-9200}/_cluster/health?pretty")
log "Cluster health:"
echo "$health_response"

# Create a test document to verify functionality
log "Creating test document..."
curl -s -X POST "http://${ELASTICSEARCH_HOST:-localhost}:${ELASTICSEARCH_PORT:-9200}/ai_karen_memory/_doc" \
    -H "Content-Type: application/json" \
    -d '{
        "tenant_id": "test",
        "user_id": "system",
        "session_id": "init",
        "query": "Elasticsearch initialization test",
        "result": "System initialized successfully",
        "timestamp": "'$(date -Iseconds)'",
        "vector_id": 0,
        "metadata": {
            "initialization": true,
            "version": "1.0"
        }
    }'

# Test search functionality
log "Testing search functionality..."
sleep 2  # Wait for document to be indexed
search_response=$(curl -s -X GET "http://${ELASTICSEARCH_HOST:-localhost}:${ELASTICSEARCH_PORT:-9200}/ai_karen_memory/_search" \
    -H "Content-Type: application/json" \
    -d '{
        "query": {
            "match": {
                "query": "initialization"
            }
        }
    }')

if echo "$search_response" | grep -q '"total":{"value":1'; then
    log "✅ Search functionality verified"
else
    log "⚠️  Search test may have failed: $search_response"
fi

log "🎉 Elasticsearch initialization completed successfully!"
log "Indices created: ai_karen_memory, ai_karen_documents, ai_karen_analytics, ai_karen_logs"
log "Cluster health: $(curl -s "http://${ELASTICSEARCH_HOST:-localhost}:${ELASTICSEARCH_PORT:-9200}/_cluster/health" | grep -o '"status":"[^"]*"')"