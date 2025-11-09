# Migration Consolidation Plan
## Kari Database Schema Evolution - Single Source of Truth

**Date:** 2025-11-07
**Status:** 🔄 In Progress
**Objective:** Consolidate all database migrations into a single authoritative location

---

## 📋 Current State

### Migration Directories Found

1. **`/data/migrations/postgres/`** - **24 migrations** (PRODUCTION/AUTHORITATIVE)
   - Complete migration history from 001 to 021
   - Includes: auth tables, memory schema, neuro_vault, admin system
   - Has `migration_history` table tracking
   - **This is the canonical migration source**

2. **`/docker/database/migrations/postgres/`** - **8 migrations** (DEV/DEPRECATED)
   - Older, incomplete migration set
   - Used by Docker Compose dev environment
   - **Should NOT be used for production**

3. **`/data/migrations/milvus/`** - **4 migrations** (Vector Store)
   - Milvus vector collection migrations
   - Separate tracking system for vector DB schema

4. **`/docker/database/migrations/duckdb/`** - **3 migrations** (Analytics)
   - DuckDB analytics schema
   - **Note:** Per architecture, DuckDB should be derived/read-only

5. **`/docker/database/migrations/elasticsearch/`** - **4 index definitions**
   - Elasticsearch index templates
   - JSON-based, not SQL migrations

---

## ⚠️ Issues Identified

### 1. **Duplicate Postgres Migration Paths**
- Two directories claiming to manage Postgres schema
- Docker migrations are incomplete/outdated
- Risk of divergence and confusion

### 2. **DuckDB Migrations Conflict with Architecture**
- DuckDB should be read-only (derived data only)
- Having migrations implies DuckDB owns schema
- Violates "DuckDB is analytical only" principle

### 3. **No Clear Migration Authority Documentation**
- README files don't clarify which path is authoritative
- Developers/operators may use wrong migration set

---

## 🎯 Consolidation Plan

### Phase 1: Establish Authority (IMMEDIATE)

#### 1.1. Mark Docker Migrations as DEPRECATED

**File:** `/docker/database/migrations/postgres/DEPRECATED.md`

**Action:** Create deprecation notice:

```markdown
# ⚠️ DEPRECATED - DO NOT USE

This migration directory is **DEPRECATED** and should NOT be used.

**Authoritative Migration Location:**
`/data/migrations/postgres/`

**Why Deprecated:**
- Incomplete migration history (only 8 vs. 24 migrations)
- Not synchronized with production schema
- Missing critical migrations (unified memory, neuro_vault, admin system)

**What to Do:**
1. Update your Docker Compose to use `/data/migrations/postgres/`
2. Run migrations from the authoritative location
3. DO NOT create new migrations here

**Migration Path:**
```yaml
# docker-compose.yml
volumes:
  - ./data/migrations/postgres:/migrations/postgres:ro
```

See: `/data/migrations/README_MIGRATION_CONSOLIDATION.md`
```

#### 1.2. Update Docker Compose

**File:** `docker-compose.yml` or equivalent

**Change:**
```yaml
# OLD (WRONG)
volumes:
  - ./docker/database/migrations/postgres:/migrations:ro

# NEW (CORRECT)
volumes:
  - ./data/migrations/postgres:/migrations:ro
```

#### 1.3. Create Authoritative README

**File:** `/data/migrations/README.md`

**Content:**
```markdown
# Kari Database Migrations - Authoritative Source

This directory contains the **canonical** database migrations for Kari.

## Directory Structure

- `postgres/` - PostgreSQL migrations (AUTHORITATIVE)
- `milvus/` - Milvus vector store migrations
- Other stores managed per their requirements

## Migration Philosophy

### Postgres: Source of Truth
- All user data, auth, RBAC, plugins, memory metadata
- Linear migration history tracked in `migration_history` table
- All environments (dev/staging/prod) use this location

### Redis: No Migrations
- Redis is ephemeral (sessions, caches, buffers)
- Configuration-driven, not schema-driven
- No migration files needed

### DuckDB: Derived Only
- DuckDB is analytical (read-only exports from Postgres)
- No migrations (data is rebuildable from Postgres)
- Schema created by ETL export process

### Vector Stores (Milvus): Separate Tracking
- Vector collections have their own migration system
- Coordinated with Postgres via `embedding_id` foreign keys

## Running Migrations

### Prerequisites
- Postgres connection configured
- Migrations run in numerical order

### Manual Execution
```bash
# Run all pending migrations
python scripts/migrations/run_migrations.py

# Check current version
python scripts/migrations/check_version.py
```

### Automatic (Application Startup)
Migrations can run automatically on startup (configurable).

## Creating New Migrations

### Naming Convention
```
<number>_<description>.sql

Example:
022_add_plugin_versioning.sql
```

### Template
```sql
-- <number>_<description>.sql
-- Purpose: Brief description of what this migration does

BEGIN;

-- Your schema changes here

-- Update migration history
INSERT INTO migration_history (service, migration_name, checksum, status)
VALUES (
    'postgres',
    '<number>_<description>.sql',
    encode(digest('<number>_<description>.sql', 'sha256'), 'hex'),
    'applied'
) ON CONFLICT (service, migration_name) DO UPDATE
SET applied_at = NOW(), checksum = EXCLUDED.checksum, status = 'applied';

COMMIT;
```

### Testing
1. Test on fresh database
2. Test idempotency (run twice)
3. Verify rollback (if applicable)

## Migration History Table

```sql
CREATE TABLE IF NOT EXISTS migration_history (
    id SERIAL PRIMARY KEY,
    service VARCHAR(50) NOT NULL,
    migration_name VARCHAR(255) NOT NULL,
    checksum VARCHAR(64),
    status VARCHAR(20) NOT NULL,
    applied_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(service, migration_name)
);
```

Query current version:
```sql
SELECT * FROM migration_history
WHERE service = 'postgres'
ORDER BY applied_at DESC
LIMIT 10;
```

## Troubleshooting

### Migration Failed
1. Check `migration_history` for status
2. Review error logs
3. Manually verify schema state
4. DO NOT skip migrations - fix and retry

### Version Mismatch
If application expects version X but DB is at version Y:
- Application will fail fast with clear error
- Run pending migrations
- Restart application

## DO NOT

- ❌ Create migrations in `/docker/database/migrations/postgres/` (DEPRECATED)
- ❌ Write to DuckDB via migrations (derived data only)
- ❌ Skip migration numbers
- ❌ Modify applied migrations (create new rollback migration instead)
- ❌ Run migrations out of order

## Architecture References

See:
- `/docs/REDIS_CORTEX_ARCHITECTURE_ALIGNMENT.md`
- Original architecture specifications from Zeus
```

---

### Phase 2: DuckDB Migration Cleanup

#### 2.1. Remove DuckDB Migrations (Architecture Compliance)

**Rationale:**
- DuckDB is analytical only (derived from Postgres)
- Should NOT have schema migrations
- Data is rebuildable from Postgres exports

**Action:**
1. Document current DuckDB schema as "reference only"
2. Create ETL export script that rebuilds DuckDB from Postgres
3. Remove `/docker/database/migrations/duckdb/` or mark as REFERENCE_ONLY

**File:** `/docker/database/migrations/duckdb/README_REFERENCE_ONLY.md`

```markdown
# ⚠️ REFERENCE ONLY - NOT AUTHORITATIVE

DuckDB schema is **derived from Postgres** via ETL export.

**Do NOT run these as migrations.**

These files are for reference only to show the expected DuckDB schema
after Postgres data export.

**How DuckDB is Populated:**
1. Postgres is source of truth
2. ETL job exports Postgres data → DuckDB
3. DuckDB schema created automatically from export

**Rebuild DuckDB:**
```bash
python scripts/analytics/rebuild_duckdb_from_postgres.py
```

See: Architecture alignment document for details.
```

---

### Phase 3: Validation & Enforcement

#### 3.1. Add Migration Version Validator

**File:** `src/ai_karen_engine/database/schema_validator.py`

```python
"""
Schema Version Validator

Ensures application runs against correct database schema version.
Fails fast on mismatch to prevent runtime errors.
"""

import logging
from typing import Optional, Dict, Any
from sqlalchemy import text

logger = logging.getLogger(__name__)

# Expected migration version (update when adding migrations)
EXPECTED_MIGRATION_VERSION = "021_admin_system_rollback.sql"


async def validate_schema_version(db_engine) -> Dict[str, Any]:
    """
    Validate that database schema matches expected version.

    Returns:
        Dict with validation status and details

    Raises:
        RuntimeError if version mismatch (fail fast)
    """
    try:
        async with db_engine.connect() as conn:
            # Get latest applied migration
            result = await conn.execute(text(
                """
                SELECT migration_name, applied_at
                FROM migration_history
                WHERE service = 'postgres'
                ORDER BY applied_at DESC
                LIMIT 1
                """
            ))
            row = result.fetchone()

            if not row:
                error_msg = "No migrations applied! Run migrations first."
                logger.error(error_msg)
                raise RuntimeError(error_msg)

            current_version = row[0]
            applied_at = row[1]

            if current_version != EXPECTED_MIGRATION_VERSION:
                error_msg = (
                    f"Schema version mismatch!\n"
                    f"Expected: {EXPECTED_MIGRATION_VERSION}\n"
                    f"Current:  {current_version}\n"
                    f"Applied at: {applied_at}\n"
                    f"Action: Run pending migrations"
                )
                logger.error(error_msg)
                raise RuntimeError(error_msg)

            logger.info(
                f"Schema version validated: {current_version} (applied {applied_at})"
            )

            return {
                "valid": True,
                "expected_version": EXPECTED_MIGRATION_VERSION,
                "current_version": current_version,
                "applied_at": applied_at
            }

    except Exception as ex:
        logger.error(f"Schema version validation failed: {ex}")
        raise
```

#### 3.2. Add Startup Validation to Services

**File:** `server/main.py` or equivalent

```python
from ai_karen_engine.database.schema_validator import validate_schema_version

@app.on_event("startup")
async def startup_validation():
    """Validate schema version on startup"""
    try:
        db_engine = get_database_engine()
        validation_result = await validate_schema_version(db_engine)
        logger.info(f"Schema validation passed: {validation_result}")
    except RuntimeError as ex:
        logger.critical(f"FATAL: Schema validation failed: {ex}")
        # Fail fast - do not start service with wrong schema
        sys.exit(1)
```

---

## 🧩 Migration Table Contract

### Single Source of Truth

**Table:** `migration_history`
**Location:** Postgres
**Purpose:** Track all schema changes across Kari

**Schema:**
```sql
CREATE TABLE IF NOT EXISTS migration_history (
    id SERIAL PRIMARY KEY,
    service VARCHAR(50) NOT NULL,          -- 'postgres', 'milvus', etc.
    migration_name VARCHAR(255) NOT NULL,  -- Filename of migration
    checksum VARCHAR(64),                  -- SHA256 of migration file
    status VARCHAR(20) NOT NULL,           -- 'applied', 'failed', 'rolled_back'
    applied_at TIMESTAMPTZ DEFAULT NOW(),
    applied_by VARCHAR(100),               -- User/service that applied
    execution_time_ms INTEGER,
    error_message TEXT,
    UNIQUE(service, migration_name)
);
```

### Invariants

1. **Linear History:** No gaps in migration numbers
2. **Immutable Applied:** Never modify applied migrations (create rollback migration instead)
3. **Checksum Validation:** Detect tampering with applied migrations
4. **Fail Fast:** Application startup validates version

---

## ✅ Sign-Off Checklist

- [x] Docker Postgres migrations marked DEPRECATED
- [x] Authoritative README created in `/data/migrations/`
- [ ] Docker Compose updated to use `/data/migrations/postgres/`
- [ ] DuckDB migrations marked REFERENCE_ONLY (architecture compliance)
- [ ] Schema validator implemented
- [ ] All services validate schema version on startup
- [ ] Migration documentation reviewed by team
- [ ] CI/CD updated to use correct migration path

---

## 📚 References

1. **Architecture Alignment:**
   - `/docs/REDIS_CORTEX_ARCHITECTURE_ALIGNMENT.md`
   - Original specifications from Zeus

2. **Migration Files:**
   - Authoritative: `/data/migrations/postgres/`
   - Deprecated: `/docker/database/migrations/postgres/` (DO NOT USE)

3. **Migration Scripts:**
   - `/scripts/migrations/run_migrations.py`
   - `/scripts/migrations/check_version.py`

---

**Document Version:** 1.0
**Last Updated:** 2025-11-07
**Maintained By:** Claude (AI Karen Engineering Team)
**Review Required By:** Zeus (System Architect)
