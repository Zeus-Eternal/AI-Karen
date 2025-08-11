# NeuroVault Memory System Database Migration

This document describes the database schema extensions for the NeuroVault Memory System, which implements tri-partite memory (episodic, semantic, procedural) with intelligent decay, reflection, and retrieval capabilities.

## Migration Overview

**Migration File**: `015_neuro_vault_schema_extensions.sql`
**Purpose**: Extend existing `memory_items` table with NeuroVault-specific columns and create supporting infrastructure
**Requirements**: PostgreSQL with `uuid-ossp` and `pgcrypto` extensions

## What This Migration Does

### 1. Extends `memory_items` Table

Adds the following columns to support tri-partite memory architecture:

#### Core NeuroVault Columns
- `neuro_type` (VARCHAR(20)): Memory type - 'episodic', 'semantic', or 'procedural'
- `decay_lambda` (REAL): Decay rate parameter specific to memory type
- `reflection_count` (INTEGER): Number of times processed by reflection engine
- `source_memories` (JSONB): Array of memory IDs that contributed to this memory
- `derived_memories` (JSONB): Array of memory IDs derived from this memory
- `importance_decay` (REAL): Current importance after applying decay (0.0 to 1.0)
- `last_reflection` (TIMESTAMPTZ): Timestamp of last reflection processing

#### Enhanced Memory Tracking
- `importance_score` (INTEGER): User/AI assigned importance (1-10)
- `access_count` (INTEGER): Number of times this memory has been accessed
- `last_accessed` (TIMESTAMPTZ): Timestamp of last access
- `user_id` (UUID): User who owns this memory
- `tenant_id` (UUID): Tenant isolation
- `session_id` (VARCHAR(255)): Session tracking
- `conversation_id` (UUID): Associated conversation

#### Web UI Integration
- `memory_type` (VARCHAR(50)): Legacy memory type for backward compatibility
- `ui_source` (VARCHAR(50)): Source UI that created the memory
- `ai_generated` (BOOLEAN): Whether memory was AI-generated
- `user_confirmed` (BOOLEAN): Whether user has confirmed AI-generated memory
- `tags` (JSONB): Array of tags for organization

### 2. Creates `memory_relationships` Table

New table to track relationships between memories:

```sql
CREATE TABLE memory_relationships (
    id UUID PRIMARY KEY,
    source_memory_id UUID REFERENCES memory_items(id),
    derived_memory_id UUID REFERENCES memory_items(id),
    relationship_type VARCHAR(50), -- 'reflection', 'consolidation', 'pattern', etc.
    confidence_score REAL,         -- 0.0 to 1.0
    metadata JSONB,
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ
);
```

### 3. Creates Indexes for Performance

Optimized indexes for common NeuroVault query patterns:
- Memory type and temporal queries
- Decay and cleanup operations
- User and tenant isolation
- Relationship traversal
- Tag-based searches

### 4. Adds Helper Functions

#### `calculate_decay_score(created_at, neuro_type, importance, access_count)`
Calculates current decay score based on:
- Memory age
- Memory type (episodic decays fastest, procedural slowest)
- Importance score (higher importance decays slower)
- Access patterns (frequently accessed memories decay slower)

#### `update_memory_access(memory_id)`
Updates access tracking when memory is retrieved:
- Increments `access_count`
- Updates `last_accessed` timestamp

#### `create_memory_relationship(source_id, derived_id, type, confidence, metadata)`
Creates relationships between memories:
- Inserts relationship record
- Updates source/derived memory arrays
- Maintains referential integrity

### 5. Creates Views for Analytics

#### `active_memories_with_decay`
Shows all active memories with calculated decay scores and cleanup recommendations.

#### `memory_relationship_details`
Provides detailed view of memory relationships with content preview.

#### `memory_analytics`
Aggregated statistics by memory type for dashboard display.

### 6. Adds Data Validation

Constraints ensure data integrity:
- Valid memory types and UI sources
- Importance scores between 1-10
- Decay values between 0.0-1.0
- Relationship confidence scores between 0.0-1.0
- No self-referential relationships

## Running the Migration

### Automated Migration (Recommended)

```bash
# Run the migration with backup
python scripts/run_neuro_vault_migration.py

# Run without backup (faster, but riskier)
python scripts/run_neuro_vault_migration.py --no-backup
```

### Manual Migration

```bash
# Connect to your PostgreSQL database
psql -h localhost -U your_user -d your_database

# Run the migration file
\i data/migrations/postgres/015_neuro_vault_schema_extensions.sql
```

### Validation

```bash
# Validate the migration was applied correctly
python scripts/validate_neuro_vault_schema.py
```

### Testing

```bash
# Run the test suite
pytest tests/test_neuro_vault_schema_migration.py -v
```

## Default Decay Rates

The migration sets up default decay rates based on memory type:

- **Episodic**: λ = 0.12 (fast decay, like human episodic memory)
- **Semantic**: λ = 0.04 (medium decay, facts and knowledge)
- **Procedural**: λ = 0.02 (slow decay, learned skills and patterns)
- **Other types**: λ = 0.08 (default for backward compatibility)

## Backward Compatibility

This migration is designed to be fully backward compatible:

- Existing memory queries continue to work
- New columns have sensible defaults
- Legacy `memory_type` field is preserved
- Existing indexes remain functional

## Performance Considerations

### Query Optimization
- Use memory type indexes for filtered queries
- Leverage composite indexes for multi-column filters
- Use the decay calculation function sparingly in WHERE clauses

### Maintenance
- Run decay cleanup jobs during low-traffic periods
- Monitor index usage and adjust as needed
- Consider partitioning for very large memory datasets

### Storage
- JSONB columns are efficiently stored and indexed
- Vector embeddings remain in separate Milvus collections
- Relationship table grows with O(n²) in worst case

## Monitoring and Maintenance

### Key Metrics to Monitor
- Memory type distribution
- Average decay scores by type
- Relationship creation rate
- Query performance on new indexes

### Maintenance Tasks
- Regular cleanup of highly decayed memories
- Periodic reindexing for optimal performance
- Backup verification of relationship data

### Troubleshooting

Common issues and solutions:

1. **Migration fails with constraint errors**
   - Check for existing invalid data in memory_items
   - Run data cleanup before migration

2. **Performance degradation after migration**
   - Analyze query plans for new columns
   - Consider additional indexes for specific use cases

3. **Relationship creation fails**
   - Verify both memories exist before creating relationships
   - Check foreign key constraints

## Security Considerations

- All new columns respect existing tenant isolation
- Relationship traversal is bounded to prevent infinite loops
- User permissions are inherited from existing memory system
- Audit logging captures all relationship changes

## Future Enhancements

This migration provides the foundation for:
- Advanced reflection algorithms
- Semantic memory consolidation
- Procedural pattern recognition
- Cross-memory similarity analysis
- Temporal memory clustering

## Support

For issues with this migration:
1. Check the validation script output
2. Review PostgreSQL logs for constraint violations
3. Verify all prerequisites are met
4. Run the test suite to identify specific failures

The migration is designed to be safe and reversible, with comprehensive validation and testing to ensure reliability in production environments.