#!/bin/bash
set -e

# Milvus Initialization Script for AI Karen
# This script sets up Milvus collections and configurations

echo "🚀 Initializing Milvus for AI Karen..."

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Function to wait for Milvus to be ready
wait_for_milvus() {
    local host="${MILVUS_HOST:-localhost}"
    local port="${MILVUS_PORT:-19530}"
    local max_attempts=30
    local attempt=1
    
    log "Waiting for Milvus to be ready at $host:$port..."
    
    # Install netcat if not present
    if ! command -v nc &> /dev/null; then
        log "Installing netcat..."
        apk add --no-cache netcat-openbsd
    fi
    
    while [ $attempt -le $max_attempts ]; do
        if nc -z "$host" "$port" 2>/dev/null; then
            log "✅ Milvus is ready!"
            return 0
        fi
        
        log "Attempt $attempt/$max_attempts: Milvus not ready yet, waiting..."
        sleep 5
        attempt=$((attempt + 1))
    done
    
    log "❌ Milvus failed to become ready after $max_attempts attempts"
    return 1
}

# Install Python and pymilvus if not present
if ! command -v python3 &> /dev/null; then
    log "Installing Python and dependencies..."
    apk add --no-cache python3 py3-pip
    pip3 install pymilvus==2.3.2 numpy
fi

# Wait for Milvus to be ready
wait_for_milvus

# Create Python script for Milvus initialization
cat > /tmp/init_milvus.py << 'EOF'
#!/usr/bin/env python3
import os
import sys
import time
from pymilvus import connections, Collection, CollectionSchema, FieldSchema, DataType, utility

def log(message):
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {message}")

def connect_to_milvus():
    """Connect to Milvus server"""
    host = os.getenv('MILVUS_HOST', 'localhost')
    port = os.getenv('MILVUS_PORT', '19530')
    
    log(f"Connecting to Milvus at {host}:{port}...")
    
    try:
        connections.connect(
            alias="default",
            host=host,
            port=port
        )
        log("✅ Connected to Milvus successfully")
        return True
    except Exception as e:
        log(f"❌ Failed to connect to Milvus: {e}")
        return False

def create_persona_collection():
    """Create persona embeddings collection"""
    collection_name = "persona_embeddings"
    
    if utility.has_collection(collection_name):
        log(f"Collection {collection_name} already exists, dropping it...")
        utility.drop_collection(collection_name)
    
    log(f"Creating collection: {collection_name}")
    
    # Define schema
    fields = [
        FieldSchema(name="user_id", dtype=DataType.VARCHAR, is_primary=True, auto_id=False, max_length=64),
        FieldSchema(name="tenant_id", dtype=DataType.VARCHAR, max_length=64),
        FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=384),
        FieldSchema(name="metadata", dtype=DataType.JSON),
        FieldSchema(name="timestamp", dtype=DataType.INT64),
        FieldSchema(name="version", dtype=DataType.INT32)
    ]
    
    schema = CollectionSchema(fields, description="AI Karen Persona Embeddings")
    collection = Collection(collection_name, schema)
    
    # Create index
    index_params = {
        "metric_type": "COSINE",
        "index_type": "IVF_FLAT",
        "params": {"nlist": 128}
    }
    collection.create_index("embedding", index_params)
    
    log(f"✅ Collection {collection_name} created successfully")
    return collection

def create_memory_collection():
    """Create memory embeddings collection"""
    collection_name = "memory_embeddings"
    
    if utility.has_collection(collection_name):
        log(f"Collection {collection_name} already exists, dropping it...")
        utility.drop_collection(collection_name)
    
    log(f"Creating collection: {collection_name}")
    
    # Define schema
    fields = [
        FieldSchema(name="memory_id", dtype=DataType.INT64, is_primary=True, auto_id=True),
        FieldSchema(name="user_id", dtype=DataType.VARCHAR, max_length=64),
        FieldSchema(name="tenant_id", dtype=DataType.VARCHAR, max_length=64),
        FieldSchema(name="session_id", dtype=DataType.VARCHAR, max_length=128),
        FieldSchema(name="query_embedding", dtype=DataType.FLOAT_VECTOR, dim=384),
        FieldSchema(name="response_embedding", dtype=DataType.FLOAT_VECTOR, dim=384),
        FieldSchema(name="metadata", dtype=DataType.JSON),
        FieldSchema(name="timestamp", dtype=DataType.INT64),
        FieldSchema(name="importance_score", dtype=DataType.FLOAT)
    ]
    
    schema = CollectionSchema(fields, description="AI Karen Memory Embeddings")
    collection = Collection(collection_name, schema)
    
    # Create indexes
    query_index_params = {
        "metric_type": "COSINE",
        "index_type": "IVF_FLAT",
        "params": {"nlist": 256}
    }
    collection.create_index("query_embedding", query_index_params)
    
    response_index_params = {
        "metric_type": "COSINE",
        "index_type": "IVF_FLAT",
        "params": {"nlist": 256}
    }
    collection.create_index("response_embedding", response_index_params)
    
    log(f"✅ Collection {collection_name} created successfully")
    return collection

def create_document_collection():
    """Create document embeddings collection"""
    collection_name = "document_embeddings"
    
    if utility.has_collection(collection_name):
        log(f"Collection {collection_name} already exists, dropping it...")
        utility.drop_collection(collection_name)
    
    log(f"Creating collection: {collection_name}")
    
    # Define schema
    fields = [
        FieldSchema(name="document_id", dtype=DataType.VARCHAR, is_primary=True, auto_id=False, max_length=128),
        FieldSchema(name="tenant_id", dtype=DataType.VARCHAR, max_length=64),
        FieldSchema(name="user_id", dtype=DataType.VARCHAR, max_length=64),
        FieldSchema(name="title_embedding", dtype=DataType.FLOAT_VECTOR, dim=384),
        FieldSchema(name="content_embedding", dtype=DataType.FLOAT_VECTOR, dim=384),
        FieldSchema(name="metadata", dtype=DataType.JSON),
        FieldSchema(name="timestamp", dtype=DataType.INT64),
        FieldSchema(name="document_type", dtype=DataType.VARCHAR, max_length=32)
    ]
    
    schema = CollectionSchema(fields, description="AI Karen Document Embeddings")
    collection = Collection(collection_name, schema)
    
    # Create indexes
    title_index_params = {
        "metric_type": "COSINE",
        "index_type": "IVF_FLAT",
        "params": {"nlist": 128}
    }
    collection.create_index("title_embedding", title_index_params)
    
    content_index_params = {
        "metric_type": "COSINE",
        "index_type": "IVF_FLAT",
        "params": {"nlist": 256}
    }
    collection.create_index("content_embedding", content_index_params)
    
    log(f"✅ Collection {collection_name} created successfully")
    return collection

def insert_test_data():
    """Insert test data to verify functionality"""
    import numpy as np
    
    log("Inserting test data...")
    
    # Test persona collection
    persona_collection = Collection("persona_embeddings")
    test_embedding = np.random.random(384).tolist()
    
    persona_data = [
        ["test_user_1"],  # user_id
        ["default"],      # tenant_id
        [test_embedding], # embedding
        [{"name": "Test User", "bio": "Test persona for initialization"}], # metadata
        [int(time.time())], # timestamp
        [1]               # version
    ]
    
    persona_collection.insert(persona_data)
    persona_collection.flush()
    log("✅ Test data inserted into persona_embeddings")
    
    # Test memory collection
    memory_collection = Collection("memory_embeddings")
    query_embedding = np.random.random(384).tolist()
    response_embedding = np.random.random(384).tolist()
    
    memory_data = [
        ["test_user_1"],        # user_id
        ["default"],            # tenant_id
        ["init_session"],       # session_id
        [query_embedding],      # query_embedding
        [response_embedding],   # response_embedding
        [{"query": "test query", "response": "test response"}], # metadata
        [int(time.time())],     # timestamp
        [0.8]                   # importance_score
    ]
    
    memory_collection.insert(memory_data)
    memory_collection.flush()
    log("✅ Test data inserted into memory_embeddings")

def verify_collections():
    """Verify all collections are working properly"""
    log("Verifying collections...")
    
    collections = ["persona_embeddings", "memory_embeddings", "document_embeddings"]
    
    for collection_name in collections:
        if utility.has_collection(collection_name):
            collection = Collection(collection_name)
            collection.load()
            count = collection.num_entities
            log(f"✅ Collection {collection_name}: {count} entities")
        else:
            log(f"❌ Collection {collection_name} not found")

def main():
    """Main initialization function"""
    log("🚀 Starting Milvus initialization...")
    
    if not connect_to_milvus():
        sys.exit(1)
    
    try:
        # Create collections
        create_persona_collection()
        create_memory_collection()
        create_document_collection()
        
        # Insert test data
        insert_test_data()
        
        # Verify everything is working
        verify_collections()
        
        log("🎉 Milvus initialization completed successfully!")
        
    except Exception as e:
        log(f"❌ Initialization failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
EOF

# Run the Python initialization script
log "Running Milvus initialization script..."
python3 /tmp/init_milvus.py

# Clean up
rm -f /tmp/init_milvus.py

log "🎉 Milvus initialization completed successfully!"
log "Collections created: persona_embeddings, memory_embeddings, document_embeddings"