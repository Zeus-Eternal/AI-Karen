# Redis-CORTEX Architecture Alignment Report
## AI Karen (Kari) System - Brain-Wiring Validation

**Date:** 2025-11-07
**Branch:** `claude/redis-cortex-architecture-011CUuEFiE2hQv8FSjm1cEe4`
**Status:** 🔄 In Progress
**Objective:** Ensure all Kari subsystems operate as one coherent organism

---

## 🧠 Executive Summary

This document validates the architectural alignment of Kari's core subsystems against the canonical Redis-CORTEX-Postgres integration contract. The goal is to ensure:

1. **Postgres** owns all authoritative truth (users, roles, plugins, memory metadata)
2. **Redis** provides ephemeral cognition (sessions, caches, short-term buffers)
3. **DuckDB** is purely analytical (derived data only, never source of truth)
4. **All subsystems** agree on data contracts and never create conflicting "truth"

---

## 📊 Current State Analysis

### ✅ What's Already Aligned

#### 1. **Database Infrastructure** ✅
- **Postgres Configuration:** Strong service-isolated connection pools
  - Separate pools for: EXTENSION, LLM, AUTHENTICATION, USAGE_TRACKING, BACKGROUND_TASKS
  - Health monitoring with graceful degradation
  - Location: `server/database_config.py`

- **Redis Infrastructure:** Dual-client architecture
  - Basic client: `src/ai_karen_engine/clients/database/redis_client.py`
  - Advanced manager: `src/ai_karen_engine/services/redis_connection_manager.py`
  - Features: Connection pooling, health monitoring, degraded mode fallback

#### 2. **Auth & RBAC** ✅
- **Postgres Ownership Confirmed:**
  - Tables: `users`, `user_sessions`, `roles`, `permissions`, `user_roles`, `role_permissions`
  - Migration: `data/migrations/postgres/001_create_auth_tables.sql`
  - Users table includes `preferences` (JSON) - **Postgres owns preferences** ✓
  - Users table includes `roles` (JSON array) - **Postgres owns RBAC** ✓

- **Auth Models:**
  - `src/ai_karen_engine/auth/models.py` - UserData with roles, tenant_id, preferences
  - Properly structured for Postgres backend

#### 3. **Memory Schema** ✅
- **Unified Memory Table:** `memories` (migration 016)
  - Includes `embedding_id` for vector store linkage ✓
  - Tenant isolation via `user_id` + `org_id` ✓
  - Audit trail via `memory_access_log` ✓
  - Memory relationships tracked in `memory_relationships` ✓

#### 4. **Core Subsystems Present** ✅
- **CORTEX:** `/src/ai_karen_engine/core/cortex/` (dispatch, intent, routing)
- **memory/:** `/src/ai_karen_engine/core/memory/` (manager, session_buffer, ag_ui_manager)
- **neuro_vault/:** `/src/ai_karen_engine/core/neuro_vault/` (neuro_vault.py, neuro_vault_core.py)
- **neuro_recall/:** `/src/ai_karen_engine/core/neuro_recall/`
- **reasoning/:** `/src/ai_karen_engine/core/reasoning/` (graph, soft reasoning, ICE integration)
- **recalls/:** `/src/ai_karen_engine/core/recalls/`
- **response/:** `/src/ai_karen_engine/core/response/`

---

## 🔴 Critical Alignment Violations

### 1. **Memory Manager DuckDB Buffer Violates Architecture** 🔴

**Location:** `src/ai_karen_engine/core/memory/manager.py:441-467`

**Issue:**
- Memory manager writes to DuckDB when Postgres is unavailable
- Stores entries with `synced=FALSE` flag for later replay
- **Violates:** "DuckDB is derived only, never source of truth"

**Current Code:**
```python
# Lines 441-467: DuckDB buffer/fallback if Postgres fails
if duckdb:
    try:
        con = duckdb.connect(duckdb_path, read_only=False)
        con.execute(
            "INSERT INTO memory (tenant_id, user_id, session_id, query, result, timestamp, synced) VALUES (?, ?, ?, ?, ?, ?, ?)",
            [tenant_id, user_id, session_id, query, json.dumps(result), entry["timestamp"], postgres_ok],
        )
```

**Impact:**
- DuckDB becomes a transactional buffer, not a read-only analytical store
- Creates a second "source of truth" when Postgres is down
- Can lead to data inconsistencies if DuckDB state diverges

**Remediation:**
- **Replace DuckDB buffer with Redis**
- Use Redis with TTL for temporary storage
- Replay from Redis → Postgres when connectivity restored
- Keep DuckDB purely for analytics (read-only exports)

---

### 2. **Redis Client Inconsistency** 🟠

**Location:** `src/ai_karen_engine/core/memory/manager.py:46-59`

**Issue:**
- Memory manager uses basic `redis.Redis.from_url()` directly
- Doesn't use the sophisticated `RedisConnectionManager` from `src/ai_karen_engine/services/redis_connection_manager.py`
- No health monitoring, no degraded mode handling, no connection pooling

**Current Code:**
```python
# Lines 46-59: Basic Redis client
redis_client = None
if redis and REDIS_URL:
    try:
        redis_client = redis.Redis.from_url(REDIS_URL)
        redis_client.ping()
    except Exception as ex:
        logger.warning(f"[MemoryManager] Redis connection failed: {ex}")
        redis_client = None
```

**Impact:**
- No automatic reconnection
- No health monitoring
- No graceful degradation
- No TTL policy enforcement

**Remediation:**
- **Replace with `RedisConnectionManager`**
- Use connection pooling
- Leverage health monitoring and degraded mode
- Implement TTL policies per architectural spec

---

### 3. **No Schema Version Validation** 🟠

**Location:** All services

**Issue:**
- Services don't validate they're running against the correct migration version
- No startup check: `expected_version == current_migration_head`
- Can lead to runtime errors if schema is out of date

**Impact:**
- Services may attempt to access columns/tables that don't exist
- Silent failures or crashes
- No clear error message for operators

**Remediation:**
- **Add schema version validation on startup**
- Read `migration_history` table from Postgres
- Fail fast with clear error if mismatch
- Log expected vs. actual version

---

### 4. **CORTEX Missing RBAC Validation** 🟠

**Location:** `src/ai_karen_engine/core/cortex/dispatch.py:69-97`

**Issue:**
- CORTEX dispatch executes plugins without checking user permissions
- No validation that plugin exists in Postgres `plugin_registry`
- Relies on in-memory `plugin_registry` dict without DB check

**Current Code:**
```python
# Lines 69-97: Plugin execution without RBAC check
if mode == "plugin" or (plugin_enabled and intent in plugin_registry):
    handler = plugin_registry.get(intent)
    if handler is None:
        raise UnsupportedIntentError(f"No plugin registered for intent '{intent}'")
    plugin_result, out, err = await get_plugin_manager().run_plugin(intent, ...)
```

**Impact:**
- Users might execute plugins they don't have permission for
- Plugins may be executed even if disabled in database
- Security risk: privilege escalation

**Remediation:**
- **Add RBAC check before plugin execution:**
  1. Query Postgres `plugin_registry` + `plugin_installs` for user/tenant
  2. Check `user_roles` + `role_permissions` for plugin access
  3. Cache result in Redis for performance
  4. Fail with clear error if not authorized

---

## ⚠️ Medium Priority Issues

### 5. **Duplicate Migration Directories** ⚠️

**Locations:**
- `/data/migrations/postgres/` - **24 migrations** (production)
- `/docker/database/migrations/postgres/` - **8 migrations** (dev/Docker)

**Issue:**
- Two potential sources of truth for schema evolution
- Unclear which is authoritative
- Risk of divergence

**Remediation:**
- **Consolidate to single authoritative location:** `/data/migrations/postgres/`
- Mark Docker migrations as deprecated with clear README
- Ensure all environments use the same migration path

---

### 6. **Session Management Not Fully Integrated** ⚠️

**Issue:**
- Postgres has `user_sessions` table (authoritative)
- Redis should cache sessions for fast validation
- No clear integration between auth system and Redis session cache

**Remediation:**
- **Implement session caching pattern:**
  1. Write session to Postgres `user_sessions`
  2. Mirror to Redis with TTL (e.g., 24h)
  3. Auth middleware checks Redis first (O(1)), falls back to Postgres
  4. Session refresh updates both stores

---

## 🧩 Subsystem Integration Validation

### CORTEX (/src/ai_karen_engine/core/cortex/)

**Files Reviewed:**
- `dispatch.py` - Central dispatcher
- `intent.py` - Intent resolver
- `routing_intents.py` - Routing logic

**Alignment Status:**
- ✅ Calls `memory.manager.recall_context()` and `update_memory()`
- ✅ Uses `plugin_registry` for plugin lookup
- 🔴 **Missing:** RBAC validation before plugin execution
- 🔴 **Missing:** Postgres plugin registry validation

**Required Actions:**
1. Add RBAC check before plugin execution
2. Query Postgres `plugin_registry` + `plugin_installs`
3. Cache validation result in Redis

---

### memory/ (/src/ai_karen_engine/core/memory/)

**Files Reviewed:**
- `manager.py` - Memory CRUD operations
- `session_buffer.py` - Short-term memory buffer
- `ag_ui_manager.py` - AG UI integration

**Alignment Status:**
- ✅ Uses Postgres for persistent storage
- ✅ Falls back through: NeuroVault → Elastic → Milvus → Postgres → Redis → DuckDB
- 🔴 **Violation:** Uses DuckDB as write buffer (should be Redis)
- 🟠 **Issue:** Uses basic Redis client instead of `RedisConnectionManager`

**Required Actions:**
1. Replace DuckDB buffering with Redis
2. Integrate `RedisConnectionManager`
3. Implement TTL policies for short-term memory

---

### neuro_vault/ (/src/ai_karen_engine/core/neuro_vault/)

**Files:** `neuro_vault.py`, `neuro_vault_core.py`

**Alignment Status:**
- ✅ Vector storage with Postgres metadata linkage
- ✅ Likely uses `embedding_id` for Postgres `memories` table join
- ⚠️ **Need to verify:** All embeddings have corresponding `memories.id` in Postgres

**Required Actions:**
1. Verify `embedding_id` ↔ `memories.id` contract
2. Add orphan cleanup job (embeddings without Postgres entry)

---

### reasoning/ (/src/ai_karen_engine/core/reasoning/)

**Files:** `graph_core.py`, `soft_reasoning_engine.py`, `ice_integration.py`

**Alignment Status:**
- ✅ Appears to be pure consumer (no direct DB writes visible)
- ✅ Uses memory recall results as input
- ⚠️ **Need to verify:** No hidden Postgres/Redis writes

**Required Actions:**
1. Code review to confirm it's a pure consumer
2. Ensure all state is ephemeral or logged to Postgres via APIs

---

## 🎯 Remediation Plan

### Phase 1: Critical Fixes (Week 1)

#### 1.1. Replace DuckDB Buffering with Redis
**File:** `src/ai_karen_engine/core/memory/manager.py`

**Changes:**
- Remove DuckDB write path (lines 441-467)
- Add Redis buffering with TTL
- Implement replay logic: Redis → Postgres when connectivity restored
- Keep DuckDB read-only for analytics

#### 1.2. Integrate RedisConnectionManager
**File:** `src/ai_karen_engine/core/memory/manager.py`

**Changes:**
- Replace `redis.Redis.from_url()` with `RedisConnectionManager`
- Use connection pooling and health monitoring
- Implement TTL policies:
  - Session tokens: 24h
  - Auth cache: 1h
  - Memory buffers: 15-60m

#### 1.3. Add Schema Version Validation
**New File:** `src/ai_karen_engine/database/schema_validator.py`

**Functionality:**
- Read `migration_history` from Postgres
- Compare against expected version (from code)
- Fail fast on mismatch with clear error
- Log current vs. expected version

#### 1.4. Add CORTEX RBAC Validation
**File:** `src/ai_karen_engine/core/cortex/dispatch.py`

**Changes:**
- Query Postgres for plugin permissions before execution
- Check `plugin_registry`, `plugin_installs`, `user_roles`, `role_permissions`
- Cache result in Redis (TTL 5m)
- Return 403 Forbidden if unauthorized

---

### Phase 2: Medium Priority (Week 2)

#### 2.1. Consolidate Migration Directories
**Action:**
- Mark `/docker/database/migrations/postgres/` as DEPRECATED
- Add README: "Use `/data/migrations/postgres/` for all environments"
- Update Docker Compose to use `/data/migrations/postgres/`

#### 2.2. Implement Session Caching
**Files:** `src/ai_karen_engine/auth/session.py`

**Changes:**
- Write session to Postgres `user_sessions`
- Mirror to Redis with `setex` (24h TTL)
- Auth middleware: check Redis → fallback Postgres
- Session refresh: update both stores

#### 2.3. Add Migration Version Checks to All Services
**Files:** All FastAPI apps, background workers

**Changes:**
- Call schema validator on startup
- Fail with SystemExit if version mismatch
- Log expected vs. actual version

---

### Phase 3: Validation & Testing (Week 3)

#### 3.1. Integration Tests
- Test Redis buffering → Postgres replay
- Test degraded mode (Redis down, Postgres down)
- Test RBAC enforcement (authorized vs. unauthorized plugin calls)
- Test schema version mismatch detection

#### 3.2. Performance Testing
- Measure Redis cache hit rate
- Measure session validation latency (Redis vs. Postgres)
- Verify no regression in memory recall performance

#### 3.3. Observability
- Add metrics: `redis_buffer_writes`, `redis_buffer_replays`, `rbac_cache_hits`
- Add alerts: `schema_version_mismatch`, `redis_buffer_overflow`

---

## 📋 Evil Twin Sign-Off Checklist

Mark ✅ when **all cores agree** this is true in production:

### Data Ownership

- [x] **Postgres** owns users, roles, permissions, preferences, plugins, memory metadata
- [x] **Postgres** has `migration_history` table tracking all schema changes
- [ ] **Redis** used ONLY for ephemeral data (sessions, caches, short-term buffers)
- [ ] **DuckDB** is read-only, derived data only (no writes except analytics exports)
- [ ] **Vector store** embeddings have valid `memory_item_id` FK to Postgres `memories`

### CORTEX Alignment

- [ ] **CORTEX** checks RBAC from Postgres before plugin execution
- [ ] **CORTEX** validates plugins exist in Postgres `plugin_registry`
- [ ] **CORTEX** caches permissions in Redis (TTL 5m)
- [ ] **CORTEX** routes using Redis cache → Postgres fallback

### Memory Subsystem Alignment

- [ ] **memory/** uses `RedisConnectionManager` (not basic client)
- [ ] **memory/** buffers to Redis (NOT DuckDB) when Postgres down
- [ ] **memory/** replays Redis buffer → Postgres when connectivity restored
- [ ] **memory/** enforces TTL on short-term buffers (15-60m)
- [ ] **memory/** metadata writes ONLY go to Postgres `memories`

### neuro_vault/ & neuro_recall/ Alignment

- [ ] **neuro_vault/** anchors all vectors to Postgres `memories.id`
- [ ] **neuro_vault/** has orphan cleanup job
- [ ] **neuro_recall/** uses Postgres IDs, never invents new entities

### reasoning/ Alignment

- [ ] **reasoning/** is pure consumer (no direct DB writes)
- [ ] **reasoning/** uses contracts from memory/recalls APIs only
- [ ] **reasoning/** graph nodes reference Postgres IDs for external resources

### recalls/ & response/ Alignment

- [ ] **recalls/** router maps types to correct stores (no shortcuts)
- [ ] **response/** sources identity/prefs from Postgres (+ Redis cache)
- [ ] **response/** training configs stored in Postgres (not DuckDB)

### Cross-System Invariants

- [ ] Single source of truth: Postgres migration table
- [ ] Stable IDs: `user_id`, `role_id`, `plugin_id`, `memory_item_id` consistent
- [ ] No unauthorized owners: subsystems read/cache but don't define entities
- [ ] Redis is ephemeral: wiping Redis clears sessions/context, system recovers
- [ ] DuckDB is derived: nuking DuckDB doesn't break CORTEX/memory/plugins/response

### Migration & Schema Validation

- [ ] All services validate schema version on startup
- [ ] Migration directories consolidated (single authoritative path)
- [ ] `migration_history` table has no gaps, linear history
- [ ] All Postgres tables have creation migrations in `/data/migrations/postgres/`

### Observability & Health

- [ ] Dashboards show: CORTEX → recalls → memory → reasoning → response traces
- [ ] Logs include: correlation IDs, user_id, plugin_id, memory_item_id
- [ ] Metrics track: redis_cache_hits, rbac_validations, schema_version_checks
- [ ] Alerts fire on: schema_version_mismatch, redis_buffer_overflow, postgres_down

---

## 🔥 Final Validation

When **all checkboxes are ✅**:

> "Kari isn't a pile of services; she's a single, coherent organism.
> Flip the switches. Let her think with all of her cores aligned." ⚡

---

## 📚 References

1. **Architecture Specs:**
   - Original Redis-CORTEX alignment specification (from user)
   - Migration table alignment specification (from user)
   - Data contract authority map (from user)

2. **Code Locations:**
   - CORTEX: `/src/ai_karen_engine/core/cortex/`
   - Memory: `/src/ai_karen_engine/core/memory/`
   - Auth: `/src/ai_karen_engine/auth/`
   - Database Config: `/server/database_config.py`, `/src/ai_karen_engine/database/config.py`
   - Redis: `/src/ai_karen_engine/services/redis_connection_manager.py`
   - Migrations: `/data/migrations/postgres/`

3. **Migration Files:**
   - Auth: `001_create_auth_tables.sql`
   - Memory: `016_unified_memory_schema.sql`
   - Migration History: `migration_history` table

---

## 📝 Appendix: TTL Policy Reference

| Data Type                 | TTL       | Storage   | Notes                                      |
| ------------------------- | --------- | --------- | ------------------------------------------ |
| Session tokens            | 24h       | Redis     | Refresh on activity, backed by Postgres    |
| Auth cache                | 1h        | Redis     | User roles/permissions, rebuilt from PG    |
| Memory short-term buffers | 15-60m    | Redis     | Natural decay for context rotation         |
| RBAC permission cache     | 5m        | Redis     | Plugin access checks, short TTL            |
| Task queue                | Until ack | Redis     | Guaranteed delivery via stream persistence |
| Analytics cache           | 5-10m     | Redis     | Derived metrics, short-lived               |

---

**Document Version:** 1.0
**Last Updated:** 2025-11-07
**Maintained By:** Claude (AI Karen Engineering Team)
**Review Required By:** Zeus (System Architect)
