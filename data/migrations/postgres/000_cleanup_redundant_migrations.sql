-- ============================================================================
-- CLEANUP: Remove Redundant Migration Tables
-- ============================================================================
-- This migration cleans up all the redundant tables created by previous
-- messy migrations and prepares for the consolidated schema
-- ============================================================================

-- Start transaction
BEGIN;

-- Drop tables from old migrations in reverse order (to handle dependencies)
-- These tables were created by various auth migrations that are now consolidated

-- Drop tables that may have been created by migration 023
DROP TABLE IF EXISTS context_management_tables CASCADE;

-- Drop tables that may have been created by migration 022
DROP TABLE IF EXISTS enhanced_auth_validation_system CASCADE;

-- Drop tables that may have been created by migration 021
DROP TABLE IF EXISTS admin_system_rollback CASCADE;

-- Drop tables that may have been created by migration 020
DROP TABLE IF EXISTS admin_system_production_deployment CASCADE;

-- Drop tables that may have been created by migration 019
DROP TABLE IF EXISTS performance_optimization_indexes CASCADE;

-- Drop tables that may have been created by migration 018
DROP TABLE IF EXISTS admin_management_system CASCADE;

-- Drop tables that may have been created by migration 013
DROP TABLE IF EXISTS auth_users CASCADE;
DROP TABLE IF EXISTS auth_password_hashes CASCADE;
DROP TABLE IF EXISTS auth_sessions CASCADE;
DROP TABLE IF EXISTS auth_providers CASCADE;
DROP TABLE IF EXISTS user_identities CASCADE;
DROP TABLE IF EXISTS auth_password_reset_tokens CASCADE;
DROP TABLE IF EXISTS auth_email_verification_tokens CASCADE;
DROP TABLE IF EXISTS auth_events CASCADE;

-- Drop tables that may have been created by migration 010
-- (Note: some of these may conflict with the consolidated schema, so we drop them)

-- Drop tables that may have been created by migration 009
-- (Already handled above)

-- Drop tables that may have been created by migration 008
DROP TABLE IF EXISTS web_ui_memory_entries_table CASCADE;

-- Drop tables that may have been created by migration 007
DROP TABLE IF EXISTS audit_log_table CASCADE;

-- Drop tables that may have been created by migration 006
DROP TABLE IF EXISTS plugin_executions_table CASCADE;

-- Drop tables that may have been created by migration 005
-- (conversations table will be recreated in consolidated schema)

-- Drop tables that may have been created by migration 004
DROP TABLE IF EXISTS memory_entries_table CASCADE;

-- Drop tables that may have been created by migration 002
DROP TABLE IF EXISTS memory_entries_table CASCADE; -- (duplicate name, different migration)

-- Clean up any orphaned indexes that may remain
DO $$
DECLARE
    index_name TEXT;
BEGIN
    -- Drop any indexes that start with old migration prefixes
    FOR index_name IN
        SELECT indexname
        FROM pg_indexes
        WHERE schemaname = 'public'
        AND (indexname LIKE 'idx_auth_%'
             OR indexname LIKE 'idx_user_%'
             OR indexname LIKE 'idx_session_%'
             OR indexname LIKE 'idx_audit_%'
             OR indexname LIKE 'idx_memory_%'
             OR indexname LIKE 'idx_chat_%'
             OR indexname LIKE 'idx_plugin_%'
             OR indexname LIKE 'idx_reset_%'
             OR indexname LIKE 'idx_verify_%')
        AND tablename NOT IN ('tenants', 'users', 'user_sessions', 'conversations', 'messages', 'plugins', 'plugin_settings', 'audit_logs', 'password_reset_tokens', 'email_verification_tokens', 'rate_limits', 'system_config')
    LOOP
        EXECUTE 'DROP INDEX IF EXISTS ' || index_name;
        RAISE NOTICE 'Dropped orphaned index: %', index_name;
    END LOOP;
END $$;

-- Clean up any orphaned triggers
DO $$
DECLARE
    trigger_name TEXT;
    table_name TEXT;
BEGIN
    FOR trigger_name, table_name IN
        SELECT t.tgname, c.relname
        FROM pg_trigger t
        JOIN pg_class c ON t.tgrelid = c.oid
        WHERE t.tgisinternal = false
        AND c.relname NOT IN ('tenants', 'users', 'user_sessions', 'conversations', 'messages', 'plugins', 'plugin_settings', 'audit_logs', 'password_reset_tokens', 'email_verification_tokens', 'rate_limits', 'system_config')
    LOOP
        EXECUTE 'DROP TRIGGER IF EXISTS ' || trigger_name || ' ON ' || table_name;
        RAISE NOTICE 'Dropped orphaned trigger: % on %', trigger_name, table_name;
    END LOOP;
END $$;

-- Clean up any orphaned functions (be careful not to drop system functions)
DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE;
DROP FUNCTION IF EXISTS cleanup_expired_sessions() CASCADE;
DROP FUNCTION IF EXISTS cleanup_expired_tokens() CASCADE;
DROP FUNCTION IF EXISTS cleanup_expired_auth_data() CASCADE;
DROP FUNCTION IF EXISTS get_user_stats() CASCADE;
DROP FUNCTION IF EXISTS cleanup_expired_auth_sessions() CASCADE;
DROP FUNCTION IF EXISTS cleanup_expired_auth_tokens() CASCADE;
DROP FUNCTION IF EXISTS get_auth_statistics() CASCADE;
DROP FUNCTION IF EXISTS lock_user_account(VARCHAR, INTEGER) CASCADE;

-- Clean up orphaned views
DROP VIEW IF EXISTS active_user_sessions CASCADE;
DROP VIEW IF EXISTS active_auth_sessions CASCADE;
DROP VIEW IF EXISTS recent_auth_events CASCADE;

-- Log the cleanup
DO $$
BEGIN
    RAISE NOTICE '=================================================================';
    RAISE NOTICE 'Database Cleanup Complete';
    RAISE NOTICE '=================================================================';
    RAISE NOTICE 'Removed redundant tables and objects from old migrations';
    RAISE NOTICE 'Ready for consolidated production schema';
    RAISE NOTICE '=================================================================';
END $$;

COMMIT;