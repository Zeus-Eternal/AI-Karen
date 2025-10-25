-- Admin Management System Migration
-- This migration adds role-based access control, audit logging, and system configuration
-- for the admin management system

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Add role column to existing auth_users table with default 'user' value
-- First check if the column doesn't already exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'auth_users' AND column_name = 'role'
    ) THEN
        ALTER TABLE auth_users ADD COLUMN role VARCHAR(20) DEFAULT 'user' NOT NULL;
        
        -- Create index for role-based queries
        CREATE INDEX idx_auth_users_role ON auth_users(role);
        
        -- Add constraint to ensure valid roles
        ALTER TABLE auth_users ADD CONSTRAINT chk_auth_users_role 
        CHECK (role IN ('super_admin', 'admin', 'user'));
        
        RAISE NOTICE 'Added role column to auth_users table';
    ELSE
        RAISE NOTICE 'Role column already exists in auth_users table';
    END IF;
END $$;

-- Create audit_logs table for tracking administrative actions
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth_users(user_id) ON DELETE CASCADE,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    resource_id VARCHAR(255),
    details JSONB DEFAULT '{}'::jsonb,
    ip_address INET,
    user_agent TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Indexes for performance
    CONSTRAINT audit_logs_action_check CHECK (action != ''),
    CONSTRAINT audit_logs_resource_type_check CHECK (resource_type != '')
);

-- Create indexes for audit_logs table for performance
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_audit_logs_resource_type ON audit_logs(resource_type);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_timestamp ON audit_logs(user_id, timestamp DESC);

-- Create system_config table for application settings
CREATE TABLE IF NOT EXISTS system_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key VARCHAR(100) UNIQUE NOT NULL,
    value TEXT NOT NULL,
    value_type VARCHAR(20) DEFAULT 'string' NOT NULL,
    category VARCHAR(50) DEFAULT 'general' NOT NULL,
    description TEXT,
    updated_by UUID NOT NULL REFERENCES auth_users(user_id) ON DELETE RESTRICT,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT system_config_key_check CHECK (key != ''),
    CONSTRAINT system_config_value_type_check CHECK (value_type IN ('string', 'number', 'boolean', 'json')),
    CONSTRAINT system_config_category_check CHECK (category IN ('security', 'email', 'general', 'authentication'))
);

-- Create indexes for system_config table
CREATE INDEX IF NOT EXISTS idx_system_config_key ON system_config(key);
CREATE INDEX IF NOT EXISTS idx_system_config_category ON system_config(category);
CREATE INDEX IF NOT EXISTS idx_system_config_updated_by ON system_config(updated_by);

-- Create permissions table for fine-grained access control
CREATE TABLE IF NOT EXISTS permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    category VARCHAR(50) DEFAULT 'general' NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT permissions_name_check CHECK (name != ''),
    CONSTRAINT permissions_category_check CHECK (category IN ('user_management', 'system_config', 'audit', 'security'))
);

-- Create role_permissions table for mapping roles to permissions
CREATE TABLE IF NOT EXISTS role_permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    role VARCHAR(20) NOT NULL,
    permission_id UUID NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Unique constraint to prevent duplicate role-permission mappings
    UNIQUE(role, permission_id),
    
    -- Constraint to ensure valid roles
    CONSTRAINT role_permissions_role_check CHECK (role IN ('super_admin', 'admin', 'user'))
);

-- Create indexes for role_permissions table
CREATE INDEX IF NOT EXISTS idx_role_permissions_role ON role_permissions(role);
CREATE INDEX IF NOT EXISTS idx_role_permissions_permission_id ON role_permissions(permission_id);

-- Insert default permissions
INSERT INTO permissions (name, description, category) VALUES
    ('user.create', 'Create new user accounts', 'user_management'),
    ('user.read', 'View user account information', 'user_management'),
    ('user.update', 'Update user account information', 'user_management'),
    ('user.delete', 'Delete user accounts', 'user_management'),
    ('user.list', 'List all user accounts', 'user_management'),
    ('admin.create', 'Create new admin accounts', 'user_management'),
    ('admin.promote', 'Promote users to admin role', 'user_management'),
    ('admin.demote', 'Demote admins to user role', 'user_management'),
    ('system.config.read', 'View system configuration', 'system_config'),
    ('system.config.update', 'Update system configuration', 'system_config'),
    ('audit.read', 'View audit logs', 'audit'),
    ('security.manage', 'Manage security settings', 'security')
ON CONFLICT (name) DO NOTHING;

-- Insert default role-permission mappings
INSERT INTO role_permissions (role, permission_id) 
SELECT 'super_admin', id FROM permissions
ON CONFLICT (role, permission_id) DO NOTHING;

INSERT INTO role_permissions (role, permission_id) 
SELECT 'admin', id FROM permissions 
WHERE name IN ('user.create', 'user.read', 'user.update', 'user.delete', 'user.list', 'audit.read')
ON CONFLICT (role, permission_id) DO NOTHING;

INSERT INTO role_permissions (role, permission_id) 
SELECT 'user', id FROM permissions 
WHERE name IN ('user.read')
ON CONFLICT (role, permission_id) DO NOTHING;

-- Insert default system configuration values
INSERT INTO system_config (key, value, value_type, category, description, updated_by) 
SELECT 
    'password_min_length', 
    '12', 
    'number', 
    'security', 
    'Minimum password length requirement',
    user_id
FROM auth_users 
WHERE email = 'admin@ai-karen.local'
LIMIT 1
ON CONFLICT (key) DO NOTHING;

INSERT INTO system_config (key, value, value_type, category, description, updated_by) 
SELECT 
    'session_timeout_admin', 
    '1800', 
    'number', 
    'security', 
    'Admin session timeout in seconds (30 minutes)',
    user_id
FROM auth_users 
WHERE email = 'admin@ai-karen.local'
LIMIT 1
ON CONFLICT (key) DO NOTHING;

INSERT INTO system_config (key, value, value_type, category, description, updated_by) 
SELECT 
    'mfa_required_for_admins', 
    'true', 
    'boolean', 
    'security', 
    'Require MFA for admin accounts',
    user_id
FROM auth_users 
WHERE email = 'admin@ai-karen.local'
LIMIT 1
ON CONFLICT (key) DO NOTHING;

INSERT INTO system_config (key, value, value_type, category, description, updated_by) 
SELECT 
    'email_verification_required', 
    'true', 
    'boolean', 
    'authentication', 
    'Require email verification for new accounts',
    user_id
FROM auth_users 
WHERE email = 'admin@ai-karen.local'
LIMIT 1
ON CONFLICT (key) DO NOTHING;

-- Update existing admin user to super_admin role if it exists
UPDATE auth_users 
SET role = 'super_admin', updated_at = NOW()
WHERE email = 'admin@ai-karen.local' AND role != 'super_admin';

-- Create function to automatically log audit events
CREATE OR REPLACE FUNCTION log_audit_event(
    p_user_id UUID,
    p_action VARCHAR(100),
    p_resource_type VARCHAR(50),
    p_resource_id VARCHAR(255) DEFAULT NULL,
    p_details JSONB DEFAULT '{}'::jsonb,
    p_ip_address INET DEFAULT NULL,
    p_user_agent TEXT DEFAULT NULL
) RETURNS UUID AS $$
DECLARE
    audit_id UUID;
BEGIN
    INSERT INTO audit_logs (
        user_id, action, resource_type, resource_id, 
        details, ip_address, user_agent, timestamp
    ) VALUES (
        p_user_id, p_action, p_resource_type, p_resource_id,
        p_details, p_ip_address, p_user_agent, NOW()
    ) RETURNING id INTO audit_id;
    
    RETURN audit_id;
END;
$$ LANGUAGE plpgsql;

-- Create function to check user permissions
CREATE OR REPLACE FUNCTION user_has_permission(
    p_user_id UUID,
    p_permission_name VARCHAR(100)
) RETURNS BOOLEAN AS $$
DECLARE
    user_role VARCHAR(20);
    has_permission BOOLEAN := FALSE;
BEGIN
    -- Get user role
    SELECT role INTO user_role
    FROM auth_users
    WHERE user_id = p_user_id AND is_active = true;
    
    IF user_role IS NULL THEN
        RETURN FALSE;
    END IF;
    
    -- Check if user's role has the permission
    SELECT EXISTS(
        SELECT 1
        FROM role_permissions rp
        JOIN permissions p ON rp.permission_id = p.id
        WHERE rp.role = user_role AND p.name = p_permission_name
    ) INTO has_permission;
    
    RETURN has_permission;
END;
$$ LANGUAGE plpgsql;

-- Create function to get user permissions
CREATE OR REPLACE FUNCTION get_user_permissions(p_user_id UUID)
RETURNS TABLE(permission_name VARCHAR(100), permission_description TEXT, permission_category VARCHAR(50)) AS $$
DECLARE
    user_role VARCHAR(20);
BEGIN
    -- Get user role
    SELECT role INTO user_role
    FROM auth_users
    WHERE user_id = p_user_id AND is_active = true;
    
    IF user_role IS NULL THEN
        RETURN;
    END IF;
    
    -- Return permissions for the user's role
    RETURN QUERY
    SELECT p.name, p.description, p.category
    FROM role_permissions rp
    JOIN permissions p ON rp.permission_id = p.id
    WHERE rp.role = user_role
    ORDER BY p.category, p.name;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply the trigger to relevant tables
DROP TRIGGER IF EXISTS update_auth_users_updated_at ON auth_users;
CREATE TRIGGER update_auth_users_updated_at
    BEFORE UPDATE ON auth_users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_system_config_updated_at ON system_config;
CREATE TRIGGER update_system_config_updated_at
    BEFORE UPDATE ON system_config
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Verify the migration
DO $$
DECLARE
    role_column_exists BOOLEAN;
    audit_table_exists BOOLEAN;
    config_table_exists BOOLEAN;
    permissions_count INTEGER;
BEGIN
    -- Check if role column exists
    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'auth_users' AND column_name = 'role'
    ) INTO role_column_exists;
    
    -- Check if audit_logs table exists
    SELECT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_name = 'audit_logs'
    ) INTO audit_table_exists;
    
    -- Check if system_config table exists
    SELECT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_name = 'system_config'
    ) INTO config_table_exists;
    
    -- Count permissions
    SELECT COUNT(*) INTO permissions_count FROM permissions;
    
    RAISE NOTICE 'Migration verification:';
    RAISE NOTICE 'Role column exists: %', role_column_exists;
    RAISE NOTICE 'Audit logs table exists: %', audit_table_exists;
    RAISE NOTICE 'System config table exists: %', config_table_exists;
    RAISE NOTICE 'Permissions created: %', permissions_count;
    
    IF role_column_exists AND audit_table_exists AND config_table_exists AND permissions_count > 0 THEN
        RAISE NOTICE 'SUCCESS: Admin management system migration completed successfully!';
    ELSE
        RAISE NOTICE 'WARNING: Migration may not have completed successfully!';
    END IF;
END $$;

COMMIT;