#!/usr/bin/env python3
"""
Milvus Migration: Unified Memory Collection Schema
Created: 2025-01-11
Phase: 4.1 Database Schema Consolidation

Creates unified Milvus collection schema with tenant isolation fields,
proper indexing for vector similarity search and tenant filtering,
and metadata fields for importance, decay_tier, and temporal information.
"""

import os
import sys
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

try:
    from pymilvus import (
        connections, Collection, CollectionSchema, FieldSchema, DataType, 
        utility, Index
    )
except ImportError:
    print("Error: pymilvus not installed. Install with: pip install pymilvus")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UnifiedMemoryCollectionMigration:
    """Migration class for creating unified memory collection in Milvus"""
    
    def __init__(self):
        self.collection_name = "kari_memories_unified"
        self.old_collections = [
            "kari_memories",
            "memory_embeddings", 
            "ag_ui_memories",
            "chat_memories",
            "copilot_memories"
        ]
        self.embedding_dim = 768  # DistilBERT embedding dimension
        
    def connect_to_milvus(self) -> bool:
        """Connect to Milvus server"""
        try:
            host = os.getenv('MILVUS_HOST', 'localhost')
            port = os.getenv('MILVUS_PORT', '19530')
            
            logger.info(f"Connecting to Milvus at {host}:{port}")
            connections.connect(
                alias="default",
                host=host,
                port=port
            )
            
            # Test connection
            collections = utility.list_collections()
            logger.info(f"Connected successfully. Existing collections: {collections}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Milvus: {e}")
            return False
    
    def create_collection_schema(self) -> CollectionSchema:
        """Create the unified memory collection schema"""
        
        fields = [
            # Primary key - UUID as string
            FieldSchema(
                name="id",
                dtype=DataType.VARCHAR,
                max_length=36,
                is_primary=True,
                description="Memory UUID primary key"
            ),
            
            # Tenant isolation fields
            FieldSchema(
                name="user_id",
                dtype=DataType.VARCHAR,
                max_length=255,
                description="User identifier for tenant isolation"
            ),
            FieldSchema(
                name="org_id",
                dtype=DataType.VARCHAR,
                max_length=255,
                description="Organization identifier for multi-tenant isolation"
            ),
            
            # Vector embedding
            FieldSchema(
                name="embedding",
                dtype=DataType.FLOAT_VECTOR,
                dim=self.embedding_dim,
                description="Text embedding vector (DistilBERT 768-dim)"
            ),
            
            # Memory metadata fields
            FieldSchema(
                name="importance",
                dtype=DataType.INT8,
                description="Importance score (1-10)"
            ),
            FieldSchema(
                name="decay_tier",
                dtype=DataType.VARCHAR,
                max_length=20,
                description="Decay tier: short, medium, long, pinned"
            ),
            FieldSchema(
                name="memory_type",
                dtype=DataType.VARCHAR,
                max_length=50,
                description="Memory type: general, fact, preference, etc."
            ),
            FieldSchema(
                name="neuro_type",
                dtype=DataType.VARCHAR,
                max_length=20,
                description="NeuroVault type: episodic, semantic, procedural"
            ),
            FieldSchema(
                name="ui_source",
                dtype=DataType.VARCHAR,
                max_length=50,
                description="UI source: web, api, ag_ui, copilot, etc."
            ),
            
            # Temporal fields (stored as Unix timestamps for efficiency)
            FieldSchema(
                name="created_at",
                dtype=DataType.INT64,
                description="Creation timestamp (Unix epoch)"
            ),
            FieldSchema(
                name="updated_at",
                dtype=DataType.INT64,
                description="Last update timestamp (Unix epoch)"
            ),
            FieldSchema(
                name="last_accessed",
                dtype=DataType.INT64,
                description="Last access timestamp (Unix epoch)"
            ),
            FieldSchema(
                name="expires_at",
                dtype=DataType.INT64,
                description="Expiration timestamp (Unix epoch, 0 for never)"
            ),
            
            # Access and quality metrics
            FieldSchema(
                name="access_count",
                dtype=DataType.INT32,
                description="Number of times accessed"
            ),
            FieldSchema(
                name="importance_decay",
                dtype=DataType.FLOAT,
                description="Current importance after decay (0.0-1.0)"
            ),
            FieldSchema(
                name="decay_lambda",
                dtype=DataType.FLOAT,
                description="Decay rate parameter (0.0-1.0)"
            ),
            
            # Session and conversation tracking
            FieldSchema(
                name="session_id",
                dtype=DataType.VARCHAR,
                max_length=255,
                description="Session identifier"
            ),
            FieldSchema(
                name="conversation_id",
                dtype=DataType.VARCHAR,
                max_length=36,
                description="Conversation UUID"
            ),
            
            # Boolean flags
            FieldSchema(
                name="ai_generated",
                dtype=DataType.BOOL,
                description="Whether memory was AI-generated"
            ),
            FieldSchema(
                name="user_confirmed",
                dtype=DataType.BOOL,
                description="Whether user confirmed AI-generated memory"
            ),
            FieldSchema(
                name="is_deleted",
                dtype=DataType.BOOL,
                description="Soft deletion flag"
            ),
            
            # Version for optimistic locking
            FieldSchema(
                name="version",
                dtype=DataType.INT32,
                description="Version number for optimistic locking"
            )
        ]
        
        schema = CollectionSchema(
            fields=fields,
            description="Unified memory collection with tenant isolation and comprehensive metadata",
            enable_dynamic_field=True  # Allow additional fields for future extensibility
        )
        
        return schema
    
    def create_collection(self) -> bool:
        """Create the unified memory collection"""
        try:
            # Check if collection already exists
            if utility.has_collection(self.collection_name):
                logger.info(f"Collection {self.collection_name} already exists")
                return True
            
            # Create collection schema
            schema = self.create_collection_schema()
            
            # Create collection
            logger.info(f"Creating collection: {self.collection_name}")
            collection = Collection(
                name=self.collection_name,
                schema=schema,
                using='default',
                shards_num=2  # Reasonable default for most deployments
            )
            
            logger.info(f"Collection {self.collection_name} created successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create collection: {e}")
            return False
    
    def create_indexes(self) -> bool:
        """Create indexes for efficient querying"""
        try:
            collection = Collection(self.collection_name)
            
            # Vector similarity index (primary index for embeddings)
            vector_index_params = {
                "metric_type": "COSINE",  # Cosine similarity for text embeddings
                "index_type": "IVF_FLAT",
                "params": {
                    "nlist": 1024  # Number of cluster units
                }
            }
            
            logger.info("Creating vector similarity index...")
            collection.create_index(
                field_name="embedding",
                index_params=vector_index_params,
                index_name="embedding_cosine_idx"
            )
            
            # Tenant isolation indexes
            logger.info("Creating tenant isolation indexes...")
            
            # User ID index for tenant filtering
            collection.create_index(
                field_name="user_id",
                index_params={"index_type": "TRIE"},
                index_name="user_id_idx"
            )
            
            # Organization ID index for multi-tenant filtering
            collection.create_index(
                field_name="org_id", 
                index_params={"index_type": "TRIE"},
                index_name="org_id_idx"
            )
            
            # Temporal indexes for time-based queries
            logger.info("Creating temporal indexes...")
            
            collection.create_index(
                field_name="created_at",
                index_params={"index_type": "STL_SORT"},
                index_name="created_at_idx"
            )
            
            collection.create_index(
                field_name="last_accessed",
                index_params={"index_type": "STL_SORT"},
                index_name="last_accessed_idx"
            )
            
            collection.create_index(
                field_name="expires_at",
                index_params={"index_type": "STL_SORT"},
                index_name="expires_at_idx"
            )
            
            # Metadata indexes for filtering
            logger.info("Creating metadata indexes...")
            
            collection.create_index(
                field_name="importance",
                index_params={"index_type": "STL_SORT"},
                index_name="importance_idx"
            )
            
            collection.create_index(
                field_name="decay_tier",
                index_params={"index_type": "TRIE"},
                index_name="decay_tier_idx"
            )
            
            collection.create_index(
                field_name="memory_type",
                index_params={"index_type": "TRIE"},
                index_name="memory_type_idx"
            )
            
            collection.create_index(
                field_name="neuro_type",
                index_params={"index_type": "TRIE"},
                index_name="neuro_type_idx"
            )
            
            collection.create_index(
                field_name="ui_source",
                index_params={"index_type": "TRIE"},
                index_name="ui_source_idx"
            )
            
            # Access pattern indexes
            collection.create_index(
                field_name="access_count",
                index_params={"index_type": "STL_SORT"},
                index_name="access_count_idx"
            )
            
            collection.create_index(
                field_name="importance_decay",
                index_params={"index_type": "STL_SORT"},
                index_name="importance_decay_idx"
            )
            
            # Session and conversation indexes
            collection.create_index(
                field_name="session_id",
                index_params={"index_type": "TRIE"},
                index_name="session_id_idx"
            )
            
            collection.create_index(
                field_name="conversation_id",
                index_params={"index_type": "TRIE"},
                index_name="conversation_id_idx"
            )
            
            # Boolean flag indexes
            collection.create_index(
                field_name="is_deleted",
                index_params={"index_type": "TRIE"},
                index_name="is_deleted_idx"
            )
            
            logger.info("All indexes created successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create indexes: {e}")
            return False
    
    def load_collection(self) -> bool:
        """Load collection into memory for querying"""
        try:
            collection = Collection(self.collection_name)
            logger.info(f"Loading collection {self.collection_name} into memory...")
            collection.load()
            logger.info("Collection loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load collection: {e}")
            return False
    
    def verify_collection(self) -> bool:
        """Verify collection was created correctly"""
        try:
            if not utility.has_collection(self.collection_name):
                logger.error(f"Collection {self.collection_name} does not exist")
                return False
            
            collection = Collection(self.collection_name)
            
            # Check schema
            schema = collection.schema
            logger.info(f"Collection schema: {len(schema.fields)} fields")
            
            # Check indexes
            indexes = collection.indexes
            logger.info(f"Collection indexes: {len(indexes)} indexes created")
            
            # Print collection stats
            stats = collection.num_entities
            logger.info(f"Collection entities: {stats}")
            
            # List all indexes for verification
            for index in indexes:
                logger.info(f"Index: {index.field_name} -> {index.index_name} ({index.params})")
            
            logger.info("Collection verification completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Collection verification failed: {e}")
            return False
    
    def backup_old_collections(self) -> bool:
        """Create backup information for old collections before migration"""
        try:
            backup_info = {
                "migration_date": datetime.now().isoformat(),
                "old_collections": [],
                "new_collection": self.collection_name
            }
            
            for old_collection in self.old_collections:
                if utility.has_collection(old_collection):
                    collection = Collection(old_collection)
                    stats = {
                        "name": old_collection,
                        "entity_count": collection.num_entities,
                        "schema_fields": len(collection.schema.fields),
                        "indexes": len(collection.indexes)
                    }
                    backup_info["old_collections"].append(stats)
                    logger.info(f"Found old collection: {old_collection} with {stats['entity_count']} entities")
            
            # Save backup info to file
            import json
            backup_file = f"data/migrations/milvus/backup_info_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(backup_file, 'w') as f:
                json.dump(backup_info, f, indent=2)
            
            logger.info(f"Backup information saved to: {backup_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create backup info: {e}")
            return False
    
    def run_migration(self) -> bool:
        """Run the complete migration"""
        logger.info("Starting Milvus unified memory collection migration...")
        
        # Connect to Milvus
        if not self.connect_to_milvus():
            return False
        
        # Create backup info
        if not self.backup_old_collections():
            logger.warning("Failed to create backup info, continuing...")
        
        # Create collection
        if not self.create_collection():
            return False
        
        # Create indexes
        if not self.create_indexes():
            return False
        
        # Load collection
        if not self.load_collection():
            return False
        
        # Verify collection
        if not self.verify_collection():
            return False
        
        logger.info("Milvus unified memory collection migration completed successfully!")
        return True

def main():
    """Main migration function"""
    migration = UnifiedMemoryCollectionMigration()
    
    try:
        success = migration.run_migration()
        if success:
            print("✅ Migration completed successfully")
            sys.exit(0)
        else:
            print("❌ Migration failed")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️  Migration interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during migration: {e}")
        print(f"❌ Migration failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()