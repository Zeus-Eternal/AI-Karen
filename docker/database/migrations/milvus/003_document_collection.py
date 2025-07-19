#!/usr/bin/env python3
"""
Milvus Migration: Create Document Embeddings Collection
This migration creates the document embeddings collection for AI Karen
"""

import os
import time
from pymilvus import connections, Collection, CollectionSchema, FieldSchema, DataType, utility

def log(message):
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {message}")

def create_document_collection():
    """Create document embeddings collection with multi-level embeddings"""
    collection_name = "document_embeddings"
    
    log(f"Creating document collection: {collection_name}")
    
    # Drop existing collection if it exists
    if utility.has_collection(collection_name):
        log(f"Dropping existing collection: {collection_name}")
        utility.drop_collection(collection_name)
    
    # Define schema with multiple embedding types
    fields = [
        FieldSchema(name="document_id", dtype=DataType.VARCHAR, is_primary=True, auto_id=False, max_length=128),
        FieldSchema(name="tenant_id", dtype=DataType.VARCHAR, max_length=64),
        FieldSchema(name="user_id", dtype=DataType.VARCHAR, max_length=64),
        FieldSchema(name="title_embedding", dtype=DataType.FLOAT_VECTOR, dim=384),
        FieldSchema(name="content_embedding", dtype=DataType.FLOAT_VECTOR, dim=384),
        FieldSchema(name="summary_embedding", dtype=DataType.FLOAT_VECTOR, dim=384),
        FieldSchema(name="metadata", dtype=DataType.JSON),
        FieldSchema(name="timestamp", dtype=DataType.INT64),
        FieldSchema(name="document_type", dtype=DataType.VARCHAR, max_length=32),
        FieldSchema(name="file_size", dtype=DataType.INT64),
        FieldSchema(name="language", dtype=DataType.VARCHAR, max_length=16),
        FieldSchema(name="is_public", dtype=DataType.BOOL),
        FieldSchema(name="quality_score", dtype=DataType.FLOAT)
    ]
    
    schema = CollectionSchema(
        fields, 
        description="AI Karen Document Embeddings with multi-level semantic understanding"
    )
    
    # Create collection
    collection = Collection(collection_name, schema)
    
    # Create index for title embeddings (optimized for quick title matching)
    title_index_params = {
        "metric_type": "COSINE",
        "index_type": "HNSW",
        "params": {
            "M": 16,
            "efConstruction": 200
        }
    }
    collection.create_index("title_embedding", title_index_params)
    
    # Create index for content embeddings (optimized for content similarity)
    content_index_params = {
        "metric_type": "COSINE",
        "index_type": "IVF_FLAT",
        "params": {"nlist": 256}
    }
    collection.create_index("content_embedding", content_index_params)
    
    # Create index for summary embeddings (optimized for overview matching)
    summary_index_params = {
        "metric_type": "COSINE",
        "index_type": "HNSW",
        "params": {
            "M": 16,
            "efConstruction": 200
        }
    }
    collection.create_index("summary_embedding", summary_index_params)
    
    log(f"✅ Document collection {collection_name} created successfully")
    return collection

def create_chunk_collection():
    """Create document chunk collection for large document processing"""
    collection_name = "document_chunks"
    
    log(f"Creating document chunk collection: {collection_name}")
    
    # Drop existing collection if it exists
    if utility.has_collection(collection_name):
        log(f"Dropping existing collection: {collection_name}")
        utility.drop_collection(collection_name)
    
    # Define schema for document chunks
    fields = [
        FieldSchema(name="chunk_id", dtype=DataType.VARCHAR, is_primary=True, auto_id=False, max_length=128),
        FieldSchema(name="document_id", dtype=DataType.VARCHAR, max_length=128),
        FieldSchema(name="tenant_id", dtype=DataType.VARCHAR, max_length=64),
        FieldSchema(name="user_id", dtype=DataType.VARCHAR, max_length=64),
        FieldSchema(name="chunk_embedding", dtype=DataType.FLOAT_VECTOR, dim=384),
        FieldSchema(name="metadata", dtype=DataType.JSON),
        FieldSchema(name="chunk_index", dtype=DataType.INT32),
        FieldSchema(name="chunk_size", dtype=DataType.INT32),
        FieldSchema(name="overlap_size", dtype=DataType.INT32),
        FieldSchema(name="timestamp", dtype=DataType.INT64),
        FieldSchema(name="chunk_type", dtype=DataType.VARCHAR, max_length=32),
        FieldSchema(name="importance_score", dtype=DataType.FLOAT)
    ]
    
    schema = CollectionSchema(
        fields, 
        description="AI Karen Document Chunks for granular semantic search"
    )
    
    # Create collection
    collection = Collection(collection_name, schema)
    
    # Create index for chunk embeddings
    chunk_index_params = {
        "metric_type": "COSINE",
        "index_type": "IVF_FLAT",
        "params": {"nlist": 512}  # Higher nlist for more chunks
    }
    collection.create_index("chunk_embedding", chunk_index_params)
    
    log(f"✅ Document chunk collection {collection_name} created successfully")
    return collection

def create_knowledge_graph_collection():
    """Create knowledge graph embeddings collection"""
    collection_name = "knowledge_embeddings"
    
    log(f"Creating knowledge graph collection: {collection_name}")
    
    # Drop existing collection if it exists
    if utility.has_collection(collection_name):
        log(f"Dropping existing collection: {collection_name}")
        utility.drop_collection(collection_name)
    
    # Define schema for knowledge graph entities
    fields = [
        FieldSchema(name="entity_id", dtype=DataType.VARCHAR, is_primary=True, auto_id=False, max_length=128),
        FieldSchema(name="tenant_id", dtype=DataType.VARCHAR, max_length=64),
        FieldSchema(name="entity_embedding", dtype=DataType.FLOAT_VECTOR, dim=384),
        FieldSchema(name="relation_embedding", dtype=DataType.FLOAT_VECTOR, dim=384),
        FieldSchema(name="metadata", dtype=DataType.JSON),
        FieldSchema(name="entity_type", dtype=DataType.VARCHAR, max_length=32),
        FieldSchema(name="confidence_score", dtype=DataType.FLOAT),
        FieldSchema(name="timestamp", dtype=DataType.INT64),
        FieldSchema(name="source_documents", dtype=DataType.JSON),
        FieldSchema(name="is_verified", dtype=DataType.BOOL)
    ]
    
    schema = CollectionSchema(
        fields, 
        description="AI Karen Knowledge Graph Embeddings for entity and relation understanding"
    )
    
    # Create collection
    collection = Collection(collection_name, schema)
    
    # Create indexes
    entity_index_params = {
        "metric_type": "COSINE",
        "index_type": "HNSW",
        "params": {
            "M": 16,
            "efConstruction": 200
        }
    }
    collection.create_index("entity_embedding", entity_index_params)
    
    relation_index_params = {
        "metric_type": "COSINE",
        "index_type": "HNSW",
        "params": {
            "M": 16,
            "efConstruction": 200
        }
    }
    collection.create_index("relation_embedding", relation_index_params)
    
    log(f"✅ Knowledge graph collection {collection_name} created successfully")
    return collection

def main():
    """Main migration function"""
    log("🚀 Running document collections migration...")
    
    # Connect to Milvus
    host = os.getenv('MILVUS_HOST', 'localhost')
    port = os.getenv('MILVUS_PORT', '19530')
    
    try:
        connections.connect(alias="default", host=host, port=port)
        log(f"Connected to Milvus at {host}:{port}")
        
        # Create collections
        create_document_collection()
        create_chunk_collection()
        create_knowledge_graph_collection()
        
        log("🎉 Document collections migration completed successfully!")
        
    except Exception as e:
        log(f"❌ Migration failed: {e}")
        raise

if __name__ == "__main__":
    main()