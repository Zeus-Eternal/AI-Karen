# Milvus Migrations

This directory contains Milvus vector database migrations for the AI-Karen platform.

## Migration Files

### 001_unified_memory_collection.py
**Purpose**: Creates the unified memory collection schema for Phase 4.1 Database Schema Consolidation

**Features**:
- Unified collection schema with tenant isolation fields
- Comprehensive indexing for vector similarity search and tenant filtering
- Metadata fields for importance, decay_tier, and temporal information
- Support for NeuroVault tri-partite memory types
- Optimized for multi-tenant deployments

**Schema Fields**:
- `id` (VARCHAR): Memory UUID primary key
- `user_id` (VARCHAR): User identifier for tenant isolation
- `org_id` (VARCHAR): Organization identifier for multi-tenant isolation
- `embedding` (FLOAT_VECTOR): Text embedding vector (DistilBERT 768-dim)
- `importance` (INT8): Importance score (1-10)
- `decay_tier` (VARCHAR): Decay tier (short, medium, long, pinned)
- `memory_type` (VARCHAR): Memory type (general, fact, preference, etc.)
- `neuro_type` (VARCHAR): NeuroVault type (episodic, semantic, procedural)
- `ui_source` (VARCHAR): UI source (web, api, ag_ui, copilot, etc.)
- `created_at` (INT64): Creation timestamp (Unix epoch)
- `updated_at` (INT64): Last update timestamp (Unix epoch)
- `last_accessed` (INT64): Last access timestamp (Unix epoch)
- `expires_at` (INT64): Expiration timestamp (Unix epoch, 0 for never)
- `access_count` (INT32): Number of times accessed
- `importance_decay` (FLOAT): Current importance after decay (0.0-1.0)
- `decay_lambda` (FLOAT): Decay rate parameter (0.0-1.0)
- `session_id` (VARCHAR): Session identifier
- `conversation_id` (VARCHAR): Conversation UUID
- `ai_generated` (BOOL): Whether memory was AI-generated
- `user_confirmed` (BOOL): Whether user confirmed AI-generated memory
- `is_deleted` (BOOL): Soft deletion flag
- `version` (INT32): Version number for optimistic locking

**Indexes Created**:
- Vector similarity index (COSINE metric, IVF_FLAT)
- Tenant isolation indexes (user_id, org_id)
- Temporal indexes (created_at, last_accessed, expires_at)
- Metadata indexes (importance, decay_tier, memory_type, neuro_type, ui_source)
- Access pattern indexes (access_count, importance_decay)
- Session tracking indexes (session_id, conversation_id)
- Boolean flag indexes (is_deleted)

## Running Migrations

### Prerequisites
- Python 3.7+
- pymilvus package installed (`pip install pymilvus`)
- Milvus server running and accessible
- Environment variables set:
  - `MILVUS_HOST` (default: localhost)
  - `MILVUS_PORT` (default: 19530)

### Manual Execution
```bash
# Run the migration directly
python3 data/migrations/milvus/001_unified_memory_collection.py

# Or make it executable and run
chmod +x data/migrations/milvus/001_unified_memory_collection.py
./data/migrations/milvus/001_unified_memory_collection.py
```

### Using Migration Manager
```bash
# Run all Milvus migrations
docker/database/scripts/migrate.sh up milvus

# Check migration status
docker/database/scripts/migrate.sh status milvus
```

## Migration Process

1. **Connection**: Connects to Milvus server using environment variables
2. **Backup**: Creates backup information for existing collections
3. **Schema Creation**: Creates unified collection schema with all required fields
4. **Index Creation**: Creates optimized indexes for query performance
5. **Collection Loading**: Loads collection into memory for querying
6. **Verification**: Verifies collection and indexes were created correctly

## Backup and Recovery

The migration automatically creates backup information files in JSON format:
- `backup_info_YYYYMMDD_HHMMSS.json`: Contains metadata about old collections

### Old Collections Backed Up
- `kari_memories`
- `memory_embeddings`
- `ag_ui_memories`
- `chat_memories`
- `copilot_memories`

## Performance Considerations

### Index Configuration
- **Vector Index**: IVF_FLAT with COSINE metric for text similarity
- **Scalar Indexes**: TRIE for categorical fields, STL_SORT for numerical fields
- **Cluster Units**: 1024 nlist for balanced performance/memory usage

### Query Optimization
- Use tenant filters (user_id, org_id) in all queries for isolation
- Leverage temporal indexes for time-based filtering
- Combine vector similarity with metadata filtering for precise results

### Memory Usage
- Collection is loaded into memory for optimal query performance
- Shards: 2 (configurable based on deployment size)
- Dynamic fields enabled for future extensibility

## Troubleshooting

### Common Issues

1. **Connection Failed**
   - Verify Milvus server is running
   - Check MILVUS_HOST and MILVUS_PORT environment variables
   - Ensure network connectivity

2. **Index Creation Failed**
   - Check Milvus server resources (memory, CPU)
   - Verify collection exists before creating indexes
   - Review Milvus server logs for detailed errors

3. **Collection Load Failed**
   - Ensure all indexes are created successfully
   - Check available memory on Milvus server
   - Verify collection schema is valid

### Validation Commands
```bash
# Check collection exists
python3 -c "from pymilvus import utility; print(utility.list_collections())"

# Check collection stats
python3 -c "from pymilvus import Collection; c=Collection('kari_memories_unified'); print(f'Entities: {c.num_entities}')"

# List indexes
python3 -c "from pymilvus import Collection; c=Collection('kari_memories_unified'); print([i.field_name for i in c.indexes])"
```

## Migration Rollback

Currently, Milvus migrations do not support automatic rollback. To rollback:

1. Drop the new collection:
   ```python
   from pymilvus import utility
   utility.drop_collection("kari_memories_unified")
   ```

2. Restore from backup (if data migration was performed)
3. Update application configuration to use old collection names

## Security Considerations

- All queries must include tenant isolation filters
- Vector embeddings should be validated before insertion
- Access patterns are logged for audit purposes
- Soft deletion prevents accidental data loss

## Future Enhancements

This schema provides foundation for:
- Advanced vector similarity algorithms
- Temporal memory clustering
- Cross-tenant similarity analysis (with proper authorization)
- Real-time memory decay processing
- Automated memory consolidation

---
**Migration Version**: 001  
**Created**: 2025-01-11  
**Phase**: 4.1 Database Schema Consolidation  
**Status**: Production Ready