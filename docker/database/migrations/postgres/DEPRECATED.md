# DEPRECATED: Docker Database Migrations

**⚠️ This directory is deprecated as of Phase 4.1 Database Schema Consolidation**

## Migration Notice

All PostgreSQL migrations have been consolidated to the canonical location:
```
data/migrations/postgres/
```

## What This Means

- **DO NOT** add new migrations to this directory
- **DO NOT** modify existing files in this directory
- All scripts and configurations now reference `data/migrations/postgres/`

## Migration Status

The following files in this directory are superseded by newer versions in `data/migrations/postgres/`:

### Superseded Files
- `001_create_tables.sql` → Superseded by `data/migrations/postgres/001_create_tables.sql`
- `002_create_extension_tables.sql` → Superseded by `data/migrations/postgres/002_create_extension_tables.sql`
- `003_enhance_memory_table.sql` → Functionality merged into newer migrations
- `004_create_memory_entries_table.sql` → Superseded by `data/migrations/postgres/002_create_memory_entries_table.sql` and `004_create_memory_entries_table.sql`
- `005_create_conversations_table.sql` → Superseded by `data/migrations/postgres/005_create_conversations_table.sql`
- `006_create_plugin_executions_table.sql` → Superseded by `data/migrations/postgres/006_create_plugin_executions_table.sql`
- `007_create_audit_log_table.sql` → Superseded by `data/migrations/postgres/007_create_audit_log_table.sql`
- `008_add_messages_table.sql` → Superseded by `data/migrations/postgres/011_add_messages_table.sql`

## Current Migration Sequence

The canonical migration sequence is now maintained in `data/migrations/postgres/` with proper versioning:

1. `001_create_auth_tables.sql` - Authentication system tables
2. `001_create_tables.sql` - Core system tables
3. `002_create_extension_tables.sql` - Extension system tables
4. `002_create_memory_entries_table.sql` - Basic memory entries
5. `003_web_ui_integration.sql` - Web UI integration
6. `004_create_memory_entries_table.sql` - Enhanced memory entries
7. `005_create_conversations_table.sql` - Conversation tracking
8. `006_create_plugin_executions_table.sql` - Plugin execution tracking
9. `007_create_audit_log_table.sql` - Audit logging
10. `008_create_web_ui_memory_entries_table.sql` - Web UI memory entries
11. `009_create_memory_items_table.sql` - Memory items table
12. `009_create_production_auth_tables.sql` - Production auth tables
13. `010_add_production_auth_columns.sql` - Production auth columns
14. `011_add_messages_table.sql` - Messages table
15. `012_create_usage_and_rate_limit_tables.sql` - Usage and rate limiting
16. `013_production_auth_schema_alignment.sql` - Auth schema alignment
17. `014_fix_user_id_type_mismatch.sql` - User ID type fixes
18. `015_neuro_vault_schema_extensions.sql` - NeuroVault memory system

## Action Required

If you have any custom scripts or configurations referencing this directory, update them to use:
```
data/migrations/postgres/
```

## Removal Timeline

This directory will be removed in a future release after all references have been updated and validated.

---
**Date**: 2025-01-11  
**Phase**: 4.1 Database Schema Consolidation  
**Status**: Deprecated - Use `data/migrations/postgres/` instead