-- Admin Management System Rollback Migration
-- This script provides a safe rollback path for the admin management system
-- Use this script if you need to revert the admin system changes

-- WARNING: This will remove all admin-related data and functionality
-- Make sure to backup your data before running this script

BEGIN;

-- Disable row-level security
ALTER TABLE users DISABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs DISABLE ROW LEVEL SECURITY;
ALTER TABLE system_config DISABLE ROW LEVEL SECURITY;

-- Drop RLS policies
DROP POLICY IF EXISTS users_admin_access ON users;
DROP POLICY IF EXISTS audit_logs_admin_access ON audit_logs;
DROP POLICY IF EXISTS system_config_admin_access ON system_config;

-- Drop triggers
DROP TRIGGER IF EXISTS validate_admin_role_change_trigger ON users;

-- Drop functions
DROP FUNCTION IF EXISTS validate_admin_role_change();
DROP FUNCTION IF EXISTS cleanup_old_audit_logs(INTEGER);
DROP FUNCTION IF EXISTS create_monthly_audit_partition(DATE);
DROP FUNCTION IF EXISTS refresh_admin_dashboard_stats();
DROP FUNCTION IF EXISTS current_user_id();

-- Drop materialized view
DROP MATERIALIZED VIEW IF EXISTS admin_dashboard_stats;

-- Drop partitioned audit logs table
DROP TABLE IF EXISTS audit_logs_partitioned CASCADE;

-- Drop backup tables
DROP TABLE IF EXISTS users_backup_pre_admin;
DROP TABLE IF EXISTS audit_logs_backup;
DROP TABLE IF EXISTS system_config_backup;

-- Remove admin-specific columns and tables
-- Note: This will remove all admin data - make sure this is what you want

-- Reset all users to 'user' role
UPDATE users SET role = 'user' WHERE role IN ('admin', 'super_admin');

-- Drop admin-specific tables
DROP TABLE IF EXISTS system_config;
DROP TABLE IF EXISTS audit_logs;

-- Drop admin-specific indexes
DROP INDEX IF EXISTS idx_users_role_active;
DROP INDEX IF EXISTS idx_users_role;
DROP INDEX IF EXISTS idx_users_email_role;
DROP INDEX IF EXISTS idx_audit_logs_user_action_timestamp;
DROP INDEX IF EXISTS idx_audit_logs_resource_timestamp;
DROP INDEX IF EXISTS idx_audit_logs_timestamp;
DROP INDEX IF EXISTS idx_system_config_category_key;
DROP INDEX IF EXISTS idx_system_config_key;

-- Remove role column from users table (if you want complete rollback)
-- Uncomment the following line if you want to completely remove role support
-- ALTER TABLE users DROP COLUMN IF EXISTS role;

-- Remove other admin-related columns
ALTER TABLE users DROP COLUMN IF EXISTS created_by;
ALTER TABLE users DROP COLUMN IF EXISTS last_login;

COMMIT;

-- Verification queries to run after rollback
-- SELECT COUNT(*) FROM users WHERE role != 'user'; -- Should return 0
-- SELECT COUNT(*) FROM information_schema.tables WHERE table_name IN ('audit_logs', 'system_config'); -- Should return 0