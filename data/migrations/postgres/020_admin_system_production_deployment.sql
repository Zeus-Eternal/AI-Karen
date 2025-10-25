-- Admin Management System Production Deployment Migration
-- This migration script prepares the database for production deployment of the admin system
-- Run this script after the main admin system migration (018_admin_management_system.sql)

-- Enable row-level security for enhanced data protection
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE system_config ENABLE ROW LEVEL SECURITY;

-- Create RLS policies for users table
CREATE POLICY users_admin_access ON users
    FOR ALL TO authenticated
    USING (
        -- Super admins can access all users
        EXISTS (
            SELECT 1 FROM users u 
            WHERE u.id = current_user_id() 
            AND u.role = 'super_admin'
        )
        OR
        -- Admins can access non-admin users
        (
            EXISTS (
                SELECT 1 FROM users u 
                WHERE u.id = current_user_id() 
                AND u.role = 'admin'
            )
            AND role = 'user'
        )
        OR
        -- Users can only access their own record
        id = current_user_id()
    );

-- Create RLS policies for audit_logs table
CREATE POLICY audit_logs_admin_access ON audit_logs
    FOR SELECT TO authenticated
    USING (
        -- Only super admins can view audit logs
        EXISTS (
            SELECT 1 FROM users u 
            WHERE u.id = current_user_id() 
            AND u.role = 'super_admin'
        )
    );

-- Create RLS policies for system_config table
CREATE POLICY system_config_admin_access ON system_config
    FOR ALL TO authenticated
    USING (
        -- Only super admins can access system config
        EXISTS (
            SELECT 1 FROM users u 
            WHERE u.id = current_user_id() 
            AND u.role = 'super_admin'
        )
    );

-- Create function to get current user ID (implement based on your session system)
CREATE OR REPLACE FUNCTION current_user_id()
RETURNS UUID AS $$
BEGIN
    -- This should be implemented based on your session management system
    -- For now, return the user ID from the session context
    RETURN COALESCE(
        current_setting('app.current_user_id', true)::UUID,
        '00000000-0000-0000-0000-000000000000'::UUID
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create additional indexes for production performance
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_role_active 
ON users (role, is_active) WHERE is_active = true;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_logs_user_action_timestamp 
ON audit_logs (user_id, action, timestamp DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_logs_resource_timestamp 
ON audit_logs (resource_type, resource_id, timestamp DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_system_config_category_key 
ON system_config (category, key);

-- Create partitioned table for audit logs (for better performance with large datasets)
CREATE TABLE audit_logs_partitioned (
    LIKE audit_logs INCLUDING ALL
) PARTITION BY RANGE (timestamp);

-- Create initial partitions for the current and next month
CREATE TABLE audit_logs_y2024m01 PARTITION OF audit_logs_partitioned
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

CREATE TABLE audit_logs_y2024m02 PARTITION OF audit_logs_partitioned
    FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');

-- Create function to automatically create monthly partitions
CREATE OR REPLACE FUNCTION create_monthly_audit_partition(partition_date DATE)
RETURNS VOID AS $$
DECLARE
    partition_name TEXT;
    start_date DATE;
    end_date DATE;
BEGIN
    start_date := DATE_TRUNC('month', partition_date);
    end_date := start_date + INTERVAL '1 month';
    partition_name := 'audit_logs_y' || EXTRACT(YEAR FROM start_date) || 'm' || 
                     LPAD(EXTRACT(MONTH FROM start_date)::TEXT, 2, '0');
    
    EXECUTE format('CREATE TABLE IF NOT EXISTS %I PARTITION OF audit_logs_partitioned
                    FOR VALUES FROM (%L) TO (%L)',
                   partition_name, start_date, end_date);
END;
$$ LANGUAGE plpgsql;

-- Create stored procedure for audit log cleanup
CREATE OR REPLACE FUNCTION cleanup_old_audit_logs(retention_months INTEGER DEFAULT 12)
RETURNS INTEGER AS $$
DECLARE
    cutoff_date DATE;
    deleted_count INTEGER;
BEGIN
    cutoff_date := CURRENT_DATE - (retention_months || ' months')::INTERVAL;
    
    DELETE FROM audit_logs WHERE timestamp < cutoff_date;
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Create function to validate admin role assignments
CREATE OR REPLACE FUNCTION validate_admin_role_change()
RETURNS TRIGGER AS $$
BEGIN
    -- Prevent removing the last super admin
    IF OLD.role = 'super_admin' AND NEW.role != 'super_admin' THEN
        IF (SELECT COUNT(*) FROM users WHERE role = 'super_admin' AND id != NEW.id) = 0 THEN
            RAISE EXCEPTION 'Cannot remove the last super admin';
        END IF;
    END IF;
    
    -- Log role changes in audit log
    IF OLD.role != NEW.role THEN
        INSERT INTO audit_logs (user_id, action, resource_type, resource_id, details, ip_address, user_agent, timestamp)
        VALUES (
            current_user_id(),
            'role_change',
            'user',
            NEW.id::TEXT,
            jsonb_build_object('old_role', OLD.role, 'new_role', NEW.role),
            COALESCE(current_setting('app.client_ip', true), '127.0.0.1'),
            COALESCE(current_setting('app.user_agent', true), 'system'),
            NOW()
        );
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for role change validation
DROP TRIGGER IF EXISTS validate_admin_role_change_trigger ON users;
CREATE TRIGGER validate_admin_role_change_trigger
    BEFORE UPDATE ON users
    FOR EACH ROW
    WHEN (OLD.role IS DISTINCT FROM NEW.role)
    EXECUTE FUNCTION validate_admin_role_change();

-- Create materialized view for admin dashboard statistics
CREATE MATERIALIZED VIEW admin_dashboard_stats AS
SELECT 
    (SELECT COUNT(*) FROM users WHERE role = 'user') as total_users,
    (SELECT COUNT(*) FROM users WHERE role = 'admin') as total_admins,
    (SELECT COUNT(*) FROM users WHERE role = 'super_admin') as total_super_admins,
    (SELECT COUNT(*) FROM users WHERE is_active = true) as active_users,
    (SELECT COUNT(*) FROM users WHERE created_at >= CURRENT_DATE - INTERVAL '30 days') as new_users_30d,
    (SELECT COUNT(*) FROM audit_logs WHERE timestamp >= CURRENT_DATE - INTERVAL '24 hours') as audit_entries_24h,
    CURRENT_TIMESTAMP as last_updated;

-- Create index on materialized view
CREATE UNIQUE INDEX ON admin_dashboard_stats (last_updated);

-- Create function to refresh dashboard stats
CREATE OR REPLACE FUNCTION refresh_admin_dashboard_stats()
RETURNS VOID AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY admin_dashboard_stats;
END;
$$ LANGUAGE plpgsql;

-- Grant appropriate permissions
GRANT SELECT ON admin_dashboard_stats TO authenticated;
GRANT EXECUTE ON FUNCTION refresh_admin_dashboard_stats() TO authenticated;
GRANT EXECUTE ON FUNCTION cleanup_old_audit_logs(INTEGER) TO authenticated;
GRANT EXECUTE ON FUNCTION create_monthly_audit_partition(DATE) TO authenticated;

-- Insert default system configuration values
INSERT INTO system_config (key, value, category, updated_by, updated_at) VALUES
    ('password_min_length', '12', 'security', '00000000-0000-0000-0000-000000000000', NOW()),
    ('password_require_uppercase', 'true', 'security', '00000000-0000-0000-0000-000000000000', NOW()),
    ('password_require_lowercase', 'true', 'security', '00000000-0000-0000-0000-000000000000', NOW()),
    ('password_require_numbers', 'true', 'security', '00000000-0000-0000-0000-000000000000', NOW()),
    ('password_require_special', 'true', 'security', '00000000-0000-0000-0000-000000000000', NOW()),
    ('session_timeout_admin', '1800', 'security', '00000000-0000-0000-0000-000000000000', NOW()),
    ('session_timeout_user', '3600', 'security', '00000000-0000-0000-0000-000000000000', NOW()),
    ('max_login_attempts', '5', 'security', '00000000-0000-0000-0000-000000000000', NOW()),
    ('lockout_duration', '900', 'security', '00000000-0000-0000-0000-000000000000', NOW()),
    ('mfa_required_admin', 'true', 'security', '00000000-0000-0000-0000-000000000000', NOW()),
    ('audit_retention_months', '12', 'general', '00000000-0000-0000-0000-000000000000', NOW()),
    ('email_from_address', 'admin@example.com', 'email', '00000000-0000-0000-0000-000000000000', NOW()),
    ('email_from_name', 'System Administrator', 'email', '00000000-0000-0000-0000-000000000000', NOW())
ON CONFLICT (key) DO NOTHING;

-- Create backup table structure for emergency rollback
CREATE TABLE users_backup_pre_admin AS SELECT * FROM users WHERE 1=0;
CREATE TABLE audit_logs_backup AS SELECT * FROM audit_logs WHERE 1=0;
CREATE TABLE system_config_backup AS SELECT * FROM system_config WHERE 1=0;

COMMENT ON TABLE users_backup_pre_admin IS 'Backup table for users before admin system deployment';
COMMENT ON TABLE audit_logs_backup IS 'Backup table for audit logs';
COMMENT ON TABLE system_config_backup IS 'Backup table for system configuration';