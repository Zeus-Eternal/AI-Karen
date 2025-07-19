#!/usr/bin/env python3
"""
Milvus Migration: Create Memory Embeddings Collection
This migration creates the memory embeddings collection for AI Karen
"""

import os
import time
from pymilvus import connections, Collection, CollectionSchema, FieldSchema, DataType, utility

def log(message):
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {message}")

def create_memory_collection():
    """Create memory embeddings collection with dual embedding support"""
    collection_name = "memory_embeddings"
    
    log(f"Creating memory collection: {collection_name}")
    
    # Drop existing collection if it exists
    if utility.has_collection(collection_name):
        log(f"Dropping existing collection: {collection_name}")
        utility.drop_collection(collection_name)
    
    # Define schema with dual embeddings (query and response)
    fields = [
        FieldSchema(name="memory_id", dtype=DataType.INT64, is_primary=True, auto_id=True),
        FieldSchema(name="user_id", dtype=DataType.VARCHAR, max_length=64),
        FieldSchema(name="tenant_id", dtype=DataType.VARCHAR, max_length=64),
        FieldSchema(name="session_id", dtype=DataType.VARCHAR, max_length=128),
        FieldSchema(name="query_embedding", dtype=DataType.FLOAT_VECTOR, dim=384),
        FieldSchema(name="response_embedding", dtype=DataType.FLOAT_VECTOR, dim=384),
        FieldSchema(name="metadata", dtype=DataType.JSON),
        FieldSchema(name="timestamp", dtype=DataType.INT64),
        FieldSchema(name="importance_score", dtype=DataType.FLOAT),
        FieldSchema(name="memory_type", dtype=DataType.VARCHAR, max_length=32),
        FieldSchema(name="context_window", dtype=DataType.INT32),
        FieldSchema(name="is_archived", dtype=DataType.BOOL)
    ]
    
    schema = CollectionSchema(
        fields, 
        description="AI Karen Memory Embeddings with query-response pairs and context"
    )
    
    # Create collection
    collection = Collection(collection_name, schema)
    
    # Create index for query embeddings (optimized for similarity search)
    query_index_params = {
        "metric_type": "COSINE",
        "index_type": "IVF_FLAT",
        "params": {"nlist": 256}
    }
    collection.create_index("query_embedding", query_index_params)
    
    # Create index for response embeddings (optimized for content retrieval)
    response_index_params = {
        "metric_type": "COSINE",
        "index_type": "IVF_FLAT",
        "params": {"nlist": 256}
    }
    collection.create_index("response_embedding", response_index_params)
    
    log(f"✅ Memory collection {collection_name} created successfully")
    return collection

def create_conversation_collection():
    """Create conversation context collection for thread-aware memory"""
    collection_name = "conversation_embeddings"
    
    log(f"Creating conversation collection: {collection_name}")
    
    # Drop existing collection if it exists
    if utility.has_collection(collection_name):
        log(f"Dropping existing collection: {collection_name}")
        utility.drop_collection(collection_name)
    
    # Define schema for conversation-level embeddings
    fields = [
        FieldSchema(name="conversation_id", dtype=DataType.VARCHAR, is_primary=True, auto_id=False, max_length=128),
        FieldSchema(name="user_id", dtype=DataType.VARCHAR, max_length=64),
        FieldSchema(name="tenant_id", dtype=DataType.VARCHAR, max_length=64),
        FieldSchema(name="session_id", dtype=DataType.VARCHAR, max_length=128),
        FieldSchema(name="summary_embedding", dtype=DataType.FLOAT_VECTOR, dim=384),
        FieldSchema(name="topic_embedding", dtype=DataType.FLOAT_VECTOR, dim=384),
        FieldSchema(name="metadata", dtype=DataType.JSON),
        FieldSchema(name="start_timestamp", dtype=DataType.INT64),
        FieldSchema(name="end_timestamp", dtype=DataType.INT64),
        FieldSchema(name="message_count", dtype=DataType.INT32),
        FieldSchema(name="sentiment_score", dtype=DataType.FLOAT),
        FieldSchema(name="is_completed", dtype=DataType.BOOL)
    ]
    
    schema = CollectionSchema(
        fields, 
        description="AI Karen Conversation-level embeddings for context awareness"
    )
    
    # Create collection
    collection = Collection(collection_name, schema)
    
    # Create indexes
    summary_index_params = {
        "metric_type": "COSINE",
        "index_type": "HNSW",
        "params": {
            "M": 16,
            "efConstruction": 200
        }
    }
    collection.create_index("summary_embedding", summary_index_params)
    
    topic_index_params = {
        "metric_type": "COSINE",
        "index_type": "HNSW",
        "params": {
            "M": 16,
            "efConstruction": 200
        }
    }
    collection.create_index("topic_embedding", topic_index_params)
    
    log(f"✅ Conversation collection {collection_name} created successfully")
    return collection

def main():
    """Main migration function"""
    log("🚀 Running memory collections migration...")
    
    # Connect to Milvus
    host = os.getenv('MILVUS_HOST', 'localhost')
    port = os.getenv('MILVUS_PORT', '19530')
    
    try:
        connections.connect(alias="default", host=host, port=port)
        log(f"Connected to Milvus at {host}:{port}")
        
        # Create collections
        create_memory_collection()
        create_conversation_collection()
        
        log("🎉 Memory collections migration completed successfully!")
        
    except Exception as e:
        log(f"❌ Migration failed: {e}")
        raise

if __name__ == "__main__":
    main()