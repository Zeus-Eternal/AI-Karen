#!/usr/bin/env python3
"""
Milvus Migration: Create Persona Embeddings Collection
This migration creates the persona embeddings collection for AI Karen
"""

import os
import time
from pymilvus import connections, Collection, CollectionSchema, FieldSchema, DataType, utility

def log(message):
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {message}")

def create_persona_collection():
    """Create persona embeddings collection with enhanced schema"""
    collection_name = "persona_embeddings"
    
    log(f"Creating enhanced persona collection: {collection_name}")
    
    # Drop existing collection if it exists
    if utility.has_collection(collection_name):
        log(f"Dropping existing collection: {collection_name}")
        utility.drop_collection(collection_name)
    
    # Define enhanced schema
    fields = [
        FieldSchema(name="user_id", dtype=DataType.VARCHAR, is_primary=True, auto_id=False, max_length=64),
        FieldSchema(name="tenant_id", dtype=DataType.VARCHAR, max_length=64),
        FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=384),
        FieldSchema(name="metadata", dtype=DataType.JSON),
        FieldSchema(name="timestamp", dtype=DataType.INT64),
        FieldSchema(name="version", dtype=DataType.INT32),
        FieldSchema(name="persona_type", dtype=DataType.VARCHAR, max_length=32),
        FieldSchema(name="is_active", dtype=DataType.BOOL),
        FieldSchema(name="confidence_score", dtype=DataType.FLOAT)
    ]
    
    schema = CollectionSchema(
        fields, 
        description="AI Karen Enhanced Persona Embeddings with metadata and versioning"
    )
    
    # Create collection
    collection = Collection(collection_name, schema)
    
    # Create optimized index for persona embeddings
    index_params = {
        "metric_type": "COSINE",
        "index_type": "HNSW",  # More efficient for persona similarity
        "params": {
            "M": 16,
            "efConstruction": 200
        }
    }
    
    collection.create_index("embedding", index_params)
    
    log(f"✅ Enhanced persona collection {collection_name} created successfully")
    return collection

def main():
    """Main migration function"""
    log("🚀 Running persona collection migration...")
    
    # Connect to Milvus
    host = os.getenv('MILVUS_HOST', 'localhost')
    port = os.getenv('MILVUS_PORT', '19530')
    
    try:
        connections.connect(alias="default", host=host, port=port)
        log(f"Connected to Milvus at {host}:{port}")
        
        # Create collection
        create_persona_collection()
        
        log("🎉 Persona collection migration completed successfully!")
        
    except Exception as e:
        log(f"❌ Migration failed: {e}")
        raise

if __name__ == "__main__":
    main()