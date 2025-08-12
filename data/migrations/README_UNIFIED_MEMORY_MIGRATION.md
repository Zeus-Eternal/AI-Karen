# Unified Memory Schema Migration Guide

This guide covers the complete data migration process for Phase 4.1 Database Schema Consolidation, which consolidates all memory-related tables into a unified schema with comprehensive audit trails and tenant isolation.

## Overview

The migration consolidates the following legacy tables into a single `memories` table:
- `memory_items` → `memories`
- `memory_entries` → `memories`
- `web_ui_memory_entries` → `memories`
- `long_term_memory` → `memories`

## Migration Components

### 1. Schema Migration
**File**: `data/migrations/postgres/016_unified_memory_schema.sql`
- Creates unified `memories` table with all required fields
- Creates `memory_access_log` table for audit trails
- Creates `memory_relationships` table for NeuroVault compatibility
- Adds comprehensive indexes for performance and tenant isolation
- Creates helper functions for memory operations
- Creates views for analytics and reporting

### 2. Data Migration Script
**File**: `scripts/migrate_to_unified_memory_schema.py`
- Migrates existing data from legacy tables to unified schema
- Handles different data formats and structures
- Creates backup files for rollback safety
- Provides comprehensive validation and error handling

### 3. Validation Script
**File**: `scripts/validate_unified_memory_migration.py`
- Validates schema correctness and data integrity
- Checks tenant isolation and security
- Verifies index performance and function operation
- Generates detailed validation reports

### 4. Rollback Script
**File**: `scripts/rollback_unified_memory_migration.py`
- Provides safe rollback procedures if needed
- Recreates legacy table structures
- Restores data from backup files
- Validates rollback completion

### 5. Milvus Vector Store Migration
**File**: `data/migrations/milvus/001_unified_memory_collection.py`
- Creates unified Milvus collection with tenant isolation
- Implements comprehensive indexing for vector similarity search
- Supports metadata fields for importance and decay tiers

## Prerequisites

### Database Requirements
- PostgreSQL 12+ with required extensions:
  - `uuid-ossp` (UUID generation)
  - `pgcrypto` (cryptographic functions)
  - `vector` (for vector embeddings, if using pgvector)

### Python Requirements
```bash
pip install psycopg2-binary asyncpg pymilvus
```

### Environment Variables
```bash
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_DB=ai_karen
export POSTGRES_USER=karen_user
export POSTGRES_PASSWORD=your_password

export MILVUS_HOST=localhost
export MILVUS_PORT=19530
```

## Migration Process

### Step 1: Schema Migration
Run the PostgreSQL schema migration first:

```bash
# Using the migration manager
docker/database/scripts/migrate.sh up postgres

# Or manually
psql -h localhost -U karen_user -d ai_karen -f data/migrations/postgres/016_unified_memory_schema.sql
```

### Step 2: Milvus Collection Migration
Create the unified Milvus collection:

```bash
# Run the Milvus migration
python3 data/migrations/milvus/001_unified_memory_collection.py

# Or using the migration manager
docker/database/scripts/migrate.sh up milvus
```

### Step 3: Data Migration (Dry Run First)
Always run a dry run first to see what will be migrated:

```bash
# Dry run to see what would be migrated
python3 scripts/migrate_to_unified_memory_schema.py --dry-run

# Review the output, then run the actual migration
python3 scripts/migrate_to_unified_memory_schema.py
```

### Step 4: Validation
Validate the migration was successful:

```bash
python3 scripts/validate_unified_memory_migration.py
```

### Step 5: Cleanup (Optional)
After validation, you can optionally remove legacy tables:

```sql
-- Only after confirming migration success
DROP TABLE IF EXISTS memory_items CASCADE;
DROP TABLE IF EXISTS memory_entries CASCADE;
DROP TABLE IF EXISTS web_ui_memory_entries CASCADE;
DROP TABLE IF EXISTS long_term_memory CASCADE;
```

## Data Mapping

### memory_items → memories
- `id` → `id` (preserved)
- `scope` → `user_id` (tenant isolation)
- `kind` → `memory_type`
- `content` → `text`
- `metadata` → `meta`
- `created_at` → `created_at`
- Default values: `neuro_type='semantic'`, `decay_tier='medium'`

### memory_entries → memories
- `id` → `id` (preserved)
- `user_id` → `user_id`
- `tenant_id` → `org_id`
- `content` → `text`
- `memory_metadata` → `meta`
- `importance_score` → `importance`
- `memory_type` → `memory_type`
- `ui_source` → `ui_source`
- `tags` → `tags`
- Default values: `neuro_type='episodic'`, `decay_tier='short'`

### web_ui_memory_entries → memories
- `id` → `id` (preserved)
- `user_id` → `user_id`
- `tenant_id` → `org_id`
- `content` → `text`
- `metadata` → `meta`
- `memory_type` → `memory_type`
- `ui_source` → `ui_source`
- `tags` → `tags`
- Default values: `neuro_type='episodic'`, `decay_tier='short'`

### long_term_memory → memories
- `user_id` → `user_id`
- `memory_json` → parsed into multiple records if array
- Default values: `neuro_type='semantic'`, `decay_tier='long'`, `importance=6`

## Backup and Recovery

### Automatic Backups
The migration script automatically creates backup files:
- `memory_migration_backup_YYYYMMDD_HHMMSS.json`
- Contains complete data from all legacy tables
- Used for rollback procedures

### Manual Backup
Create additional backups before migration:

```bash
# PostgreSQL backup
pg_dump -h localhost -U karen_user -d ai_karen -t memory_items -t memory_entries -t web_ui_memory_entries -t long_term_memory > memory_tables_backup.sql

# Milvus backup (if applicable)
python3 -c "
from pymilvus import connections, Collection, utility
connections.connect()
for col_name in utility.list_collections():
    if 'memory' in col_name.lower():
        print(f'Collection: {col_name}, Entities: {Collection(col_name).num_entities}')
"
```

### Rollback Procedure
If rollback is needed:

```bash
# Using the rollback script
python3 scripts/rollback_unified_memory_migration.py memory_migration_backup_YYYYMMDD_HHMMSS.json

# Dry run first
python3 scripts/rollback_unified_memory_migration.py --dry-run memory_migration_backup_YYYYMMDD_HHMMSS.json
```

## Performance Considerations

### Migration Performance
- Large datasets: Run during low-traffic periods
- Batch processing: Migration processes records in batches
- Index creation: Indexes are created after data insertion for speed
- Memory usage: Monitor PostgreSQL memory during migration

### Post-Migration Performance
- Query optimization: Use tenant filters in all queries
- Index usage: Leverage composite indexes for common patterns
- Connection pooling: Use connection pooling for high-throughput scenarios
- Monitoring: Monitor query performance and adjust indexes as needed

## Monitoring and Validation

### Key Metrics to Monitor
- Record counts before and after migration
- Data integrity (no null required fields)
- Tenant isolation (proper user_id/org_id distribution)
- Index usage and query performance
- Error rates and failed migrations

### Validation Checks
The validation script checks:
- ✅ Schema correctness (tables, columns, constraints)
- ✅ Data integrity (required fields, valid values)
- ✅ Tenant isolation (proper filtering, no cross-tenant leakage)
- ✅ Index performance (query execution plans)
- ✅ Function operation (helper functions work correctly)
- ✅ Audit trail functionality (access logging works)

### Health Checks
```sql
-- Check record counts
SELECT 
    COUNT(*) as total_memories,
    COUNT(DISTINCT user_id) as unique_users,
    COUNT(DISTINCT org_id) as unique_orgs
FROM memories;

-- Check data quality
SELECT 
    COUNT(*) FILTER (WHERE text IS NULL OR text = '') as empty_text,
    COUNT(*) FILTER (WHERE user_id IS NULL) as missing_user_id,
    COUNT(*) FILTER (WHERE importance < 1 OR importance > 10) as invalid_importance
FROM memories;

-- Check tenant distribution
SELECT user_id, COUNT(*) as memory_count
FROM memories
GROUP BY user_id
ORDER BY memory_count DESC
LIMIT 10;
```

## Troubleshooting

### Common Issues

#### 1. Migration Script Fails
**Symptoms**: Script exits with database connection errors
**Solutions**:
- Verify database credentials and connectivity
- Check PostgreSQL server is running and accessible
- Ensure required extensions are installed
- Review PostgreSQL logs for detailed errors

#### 2. Data Validation Fails
**Symptoms**: Validation script reports data integrity issues
**Solutions**:
- Review validation report for specific issues
- Check for data corruption in source tables
- Verify mapping logic for problematic records
- Consider data cleanup before re-running migration

#### 3. Performance Issues
**Symptoms**: Migration takes too long or queries are slow
**Solutions**:
- Run migration during low-traffic periods
- Increase PostgreSQL memory settings
- Monitor disk I/O and ensure sufficient space
- Consider partitioning for very large datasets

#### 4. Rollback Required
**Symptoms**: Migration completed but system not working correctly
**Solutions**:
- Use rollback script with backup file
- Verify backup file integrity before rollback
- Test rollback in staging environment first
- Document issues for future migration attempts

### Debug Commands

```bash
# Check migration progress
tail -f memory_migration.log

# Verify database connections
python3 -c "
import psycopg2
conn = psycopg2.connect(host='localhost', user='karen_user', database='ai_karen', password='your_password')
print('PostgreSQL connection: OK')
conn.close()
"

# Check Milvus connection
python3 -c "
from pymilvus import connections, utility
connections.connect(host='localhost', port='19530')
print('Milvus collections:', utility.list_collections())
"

# Validate schema manually
psql -h localhost -U karen_user -d ai_karen -c "
SELECT table_name, column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'memories' 
ORDER BY ordinal_position;
"
```

## Security Considerations

### Data Protection
- All migrations create backup files with sensitive data
- Backup files should be encrypted and stored securely
- Access to migration scripts should be restricted
- Audit logs capture all migration activities

### Tenant Isolation
- All queries must include tenant filters (user_id, org_id)
- Cross-tenant access is prevented by application logic
- Database-level row security can be added for additional protection
- Regular audits should verify tenant isolation

### Access Control
- Migration scripts require database admin privileges
- Production migrations should be performed by authorized personnel
- All migration activities should be logged and auditable
- Rollback procedures should be tested and documented

## Post-Migration Tasks

### Application Updates
- Update application code to use unified `memories` table
- Remove references to legacy tables
- Update API endpoints to use new schema
- Test all memory-related functionality

### Monitoring Setup
- Configure alerts for memory table performance
- Monitor tenant isolation metrics
- Set up dashboards for memory analytics
- Implement automated health checks

### Documentation Updates
- Update API documentation with new schema
- Update deployment guides
- Train team on new memory system
- Document operational procedures

---

**Migration Version**: 016  
**Created**: 2025-01-11  
**Phase**: 4.1 Database Schema Consolidation  
**Status**: Production Ready

For support or questions about this migration, refer to the validation reports and logs, or consult the development team.