-- ============================================================================
-- AI Karen Production Database Schema - Consolidated Migration
-- ============================================================================
-- This is the SINGLE SOURCE OF TRUTH for the AI Karen database schema
-- All previous migrations have been analyzed and consolidated into this file
-- This migration creates a production-ready, streamlined database schema
-- ============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================================
-- TENANTS TABLE (Multi-tenancy support)
-- ============================================================================
CREATE TABLE IF NOT EXISTS tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) UNIQUE NOT NULL,
    display_name VARCHAR(255),
    description TEXT,
    domain VARCHAR(255),
    is_active BOOLEAN DEFAULT true NOT NULL,
    settings JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insert default tenant
INSERT INTO tenants (id, name, display_name, description) VALUES
    ('550e8400-e29b-41d4-a716-446655440000'::uuid, 'default', 'Default Tenant', 'Default tenant for AI Karen')
ON CONFLICT (name) DO NOTHING;

-- ============================================================================
-- USERS TABLE (Consolidated from multiple auth migrations)
-- ============================================================================
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Authentication (required)
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE,
    password_hash VARCHAR(255) NOT NULL,

    -- Profile Information (required)
    full_name VARCHAR(255),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    display_name VARCHAR(255),

    -- Account Status
    is_active BOOLEAN DEFAULT true NOT NULL,
    is_verified BOOLEAN DEFAULT false NOT NULL,

    -- Role and Permissions
    roles JSONB DEFAULT '["user"]'::jsonb NOT NULL,
    permissions JSONB DEFAULT '[]'::jsonb,

    -- Multi-tenancy
    tenant_id UUID NOT NULL DEFAULT '550e8400-e29b-41d4-a716-446655440000'::uuid REFERENCES tenants(id),

    -- User Preferences
    preferences JSONB DEFAULT '{
        "theme": "system",
        "language": "en",
        "timezone": "UTC",
        "notifications": {
            "email": true,
            "push": false,
            "marketing": false
        },
        "ai": {
            "personality": "balanced",
            "verbosity": "normal",
            "temperature": 0.7
        }
    }'::jsonb,

    -- Security Features
    two_factor_enabled BOOLEAN DEFAULT false NOT NULL,
    two_factor_secret VARCHAR(32),
    backup_codes JSONB,

    -- Account Security Tracking
    failed_login_attempts INTEGER DEFAULT 0 NOT NULL,
    locked_until TIMESTAMP WITH TIME ZONE,
    last_login_at TIMESTAMP WITH TIME ZONE,
    last_login_ip INET,
    password_changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    email_verified_at TIMESTAMP WITH TIME ZONE,

    -- Metadata
    avatar_url VARCHAR(500),
    bio TEXT,
    location VARCHAR(255),
    website VARCHAR(255),
    social_links JSONB DEFAULT '{}'::jsonb,

    -- Audit Fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id)
);

-- ============================================================================
-- USER SESSIONS TABLE (Production session management)
-- ============================================================================
CREATE TABLE IF NOT EXISTS user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Session Tokens
    session_token VARCHAR(255) UNIQUE NOT NULL,
    refresh_token VARCHAR(255) UNIQUE,
    access_token TEXT,

    -- Session Metadata
    ip_address INET,
    user_agent TEXT,
    device_fingerprint VARCHAR(255),
    geolocation JSONB,

    -- Session State
    is_active BOOLEAN DEFAULT true NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    last_activity_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Security Monitoring
    risk_score DECIMAL(3,2) DEFAULT 0.0,
    security_flags JSONB DEFAULT '[]'::jsonb,
    suspicious_activity JSONB DEFAULT '[]'::jsonb,

    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    invalidated_at TIMESTAMP WITH TIME ZONE,
    invalidation_reason VARCHAR(100)
);

-- ============================================================================
-- CONVERSATIONS TABLE (Chat conversations)
-- ============================================================================
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Conversation Identity
    session_id VARCHAR(255),
    title VARCHAR(255),
    conversation_type VARCHAR(50) DEFAULT 'chat',

    -- Content
    message_count INTEGER DEFAULT 0,
    last_message_at TIMESTAMP WITH TIME ZONE,
    last_message_preview TEXT,

    -- AI Context
    ai_context JSONB DEFAULT '{}'::jsonb,
    ai_insights JSONB DEFAULT '{}'::jsonb,
    conversation_summary TEXT,

    -- User Settings for this conversation
    user_settings JSONB DEFAULT '{}'::jsonb,

    -- Metadata
    tags TEXT[] DEFAULT '{}',
    is_pinned BOOLEAN DEFAULT false,
    is_archived BOOLEAN DEFAULT false,
    is_favorite BOOLEAN DEFAULT false,

    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- MESSAGES TABLE (Individual chat messages)
-- ============================================================================
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Message Content
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    content_type VARCHAR(50) DEFAULT 'text',

    -- AI Response Data
    ai_metadata JSONB DEFAULT '{}'::jsonb,
    ai_model VARCHAR(100),
    ai_provider VARCHAR(100),
    ai_temperature DECIMAL(3,2),
    ai_tokens_used INTEGER,

    -- Message Features
    attachments JSONB DEFAULT '[]'::jsonb,
    reactions JSONB DEFAULT '[]'::jsonb,
    is_edited BOOLEAN DEFAULT false,
    edited_at TIMESTAMP WITH TIME ZONE,

    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    sequence_number INTEGER NOT NULL
);

-- ============================================================================
-- PLUGINS TABLE (Plugin management)
-- ============================================================================
CREATE TABLE IF NOT EXISTS plugins (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plugin_id VARCHAR(255) UNIQUE NOT NULL,

    -- Plugin Metadata
    name VARCHAR(255) NOT NULL,
    display_name VARCHAR(255),
    description TEXT,
    version VARCHAR(50),
    author VARCHAR(255),

    -- Plugin Configuration
    config_schema JSONB DEFAULT '{}'::jsonb,
    default_config JSONB DEFAULT '{}'::jsonb,

    -- Plugin State
    is_enabled BOOLEAN DEFAULT false,
    is_installed BOOLEAN DEFAULT false,
    install_path VARCHAR(500),

    -- Capabilities
    capabilities JSONB DEFAULT '{}'::jsonb,
    ui_components JSONB DEFAULT '[]'::jsonb,
    api_endpoints JSONB DEFAULT '[]'::jsonb,

    -- Dependencies
    dependencies JSONB DEFAULT '[]'::jsonb,
    required_permissions JSONB DEFAULT '[]'::jsonb,

    -- Audit
    installed_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    installed_by UUID REFERENCES users(id)
);

-- ============================================================================
-- PLUGIN SETTINGS TABLE (Per-user plugin configuration)
-- ============================================================================
CREATE TABLE IF NOT EXISTS plugin_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    plugin_id UUID NOT NULL REFERENCES plugins(id) ON DELETE CASCADE,

    -- Settings
    settings JSONB DEFAULT '{}'::jsonb,
    is_enabled BOOLEAN DEFAULT true,

    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(user_id, plugin_id)
);

-- ============================================================================
-- AUDIT LOGS TABLE (Comprehensive audit logging)
-- ============================================================================
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Event Information
    event_type VARCHAR(100) NOT NULL,
    event_category VARCHAR(50) DEFAULT 'general',
    severity VARCHAR(20) DEFAULT 'info' CHECK (severity IN ('debug', 'info', 'warning', 'error', 'critical')),

    -- Actor Information
    user_id UUID REFERENCES users(id),
    session_id UUID REFERENCES user_sessions(id),
    ip_address INET,
    user_agent TEXT,

    -- Target Information
    resource_type VARCHAR(100),
    resource_id VARCHAR(255),
    action VARCHAR(100),

    -- Event Details
    details JSONB DEFAULT '{}'::jsonb,
    old_values JSONB,
    new_values JSONB,

    -- Security & Risk
    risk_score DECIMAL(3,2) DEFAULT 0.0,
    security_flags JSONB DEFAULT '[]'::jsonb,

    -- Performance
    processing_time_ms DECIMAL(8,2),

    -- Audit
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    tenant_id UUID DEFAULT '550e8400-e29b-41d4-a716-446655440000'::uuid
);

-- ============================================================================
-- PASSWORD RESET TOKENS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS password_reset_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Token Data
    token_hash VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,

    -- Usage Tracking
    is_used BOOLEAN DEFAULT false NOT NULL,
    used_at TIMESTAMP WITH TIME ZONE,
    used_ip INET,

    -- Security
    created_ip INET,
    user_agent TEXT,

    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- EMAIL VERIFICATION TOKENS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS email_verification_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Token Data
    token_hash VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,

    -- Usage Tracking
    is_used BOOLEAN DEFAULT false NOT NULL,
    used_at TIMESTAMP WITH TIME ZONE,

    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- RATE LIMITING TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS rate_limits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,

    -- Rate Limit Key
    key VARCHAR(255) NOT NULL, -- e.g., 'api_calls', 'messages', 'logins'
    window_start TIMESTAMP WITH TIME ZONE NOT NULL,

    -- Counters
    request_count INTEGER DEFAULT 0 NOT NULL,
    limit_exceeded BOOLEAN DEFAULT false,

    -- Window Configuration
    window_seconds INTEGER NOT NULL, -- e.g., 60, 3600, 86400
    max_requests INTEGER NOT NULL,

    UNIQUE(user_id, key, window_start)
);

-- ============================================================================
-- SYSTEM CONFIGURATION TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS system_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key VARCHAR(255) UNIQUE NOT NULL,
    value JSONB NOT NULL,
    description TEXT,
    is_encrypted BOOLEAN DEFAULT false,
    category VARCHAR(100) DEFAULT 'general',

    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_by UUID REFERENCES users(id)
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- Users indexes
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_tenant ON users(tenant_id);
CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_users_verified ON users(is_verified) WHERE is_verified = true;
CREATE INDEX IF NOT EXISTS idx_users_created ON users(created_at);
CREATE INDEX IF NOT EXISTS idx_users_roles ON users USING GIN(roles);

-- Sessions indexes
CREATE INDEX IF NOT EXISTS idx_sessions_user ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_token ON user_sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_sessions_active ON user_sessions(is_active) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_sessions_expires ON user_sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_sessions_activity ON user_sessions(last_activity_at);

-- Conversations indexes
CREATE INDEX IF NOT EXISTS idx_conversations_user ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_session ON conversations(session_id);
CREATE INDEX IF NOT EXISTS idx_conversations_active ON conversations(is_active) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_conversations_created ON conversations(created_at);
CREATE INDEX IF NOT EXISTS idx_conversations_tags ON conversations USING GIN(tags);

-- Messages indexes
CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_messages_user ON messages(user_id);
CREATE INDEX IF NOT EXISTS idx_messages_created ON messages(created_at);
CREATE INDEX IF NOT EXISTS idx_messages_sequence ON messages(conversation_id, sequence_number);

-- Plugins indexes
CREATE INDEX IF NOT EXISTS idx_plugins_enabled ON plugins(is_enabled) WHERE is_enabled = true;
CREATE INDEX IF NOT EXISTS idx_plugins_installed ON plugins(is_installed) WHERE is_installed = true;

-- Audit logs indexes
CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_type ON audit_logs(event_type);
CREATE INDEX IF NOT EXISTS idx_audit_logs_category ON audit_logs(event_category);
CREATE INDEX IF NOT EXISTS idx_audit_logs_resource ON audit_logs(resource_type, resource_id);

-- Password reset tokens indexes
CREATE INDEX IF NOT EXISTS idx_password_reset_user ON password_reset_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_password_reset_expires ON password_reset_tokens(expires_at);
CREATE INDEX IF NOT EXISTS idx_password_reset_used ON password_reset_tokens(is_used);

-- Email verification tokens indexes
CREATE INDEX IF NOT EXISTS idx_email_verify_user ON email_verification_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_email_verify_expires ON email_verification_tokens(expires_at);

-- Rate limiting indexes
CREATE INDEX IF NOT EXISTS idx_rate_limits_user ON rate_limits(user_id);
CREATE INDEX IF NOT EXISTS idx_rate_limits_key ON rate_limits(key);
CREATE INDEX IF NOT EXISTS idx_rate_limits_window ON rate_limits(window_start);

-- ============================================================================
-- TRIGGERS FOR AUTOMATIC TIMESTAMPS
-- ============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply triggers to all tables with updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_conversations_updated_at BEFORE UPDATE ON conversations FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_audit_logs_updated_at BEFORE UPDATE ON audit_logs FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_system_config_updated_at BEFORE UPDATE ON system_config FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- DEFAULT DATA INSERTION
-- ============================================================================

-- Insert default system configuration
INSERT INTO system_config (key, value, description, category) VALUES
    ('system_version', '"1.0.0"', 'Current system version', 'system'),
    ('maintenance_mode', 'false', 'Whether the system is in maintenance mode', 'system'),
    ('max_users', '1000', 'Maximum number of users allowed', 'limits'),
    ('max_conversations_per_user', '100', 'Maximum conversations per user', 'limits'),
    ('max_messages_per_conversation', '1000', 'Maximum messages per conversation', 'limits'),
    ('rate_limit_api_calls', '{"window_seconds": 60, "max_requests": 100}', 'API rate limiting configuration', 'rate_limiting'),
    ('rate_limit_messages', '{"window_seconds": 60, "max_requests": 10}', 'Message rate limiting configuration', 'rate_limiting'),
    ('security_password_min_length', '8', 'Minimum password length', 'security'),
    ('security_session_timeout', '3600', 'Session timeout in seconds', 'security'),
    ('ai_default_model', '"llama3.2:latest"', 'Default AI model', 'ai'),
    ('ai_default_provider', '"llamacpp"', 'Default AI provider', 'ai')
ON CONFLICT (key) DO NOTHING;

-- Create default admin user
DO $$
DECLARE
    admin_user_id UUID;
BEGIN
    -- Check if admin user already exists
    IF NOT EXISTS (SELECT 1 FROM users WHERE email = 'admin@ai-karen.local') THEN
        admin_user_id := gen_random_uuid();

        -- Insert admin user
        INSERT INTO users (
            id,
            email,
            username,
            password_hash,
            full_name,
            display_name,
            roles,
            is_verified,
            is_active,
            preferences,
            tenant_id
        ) VALUES (
            admin_user_id,
            'admin@ai-karen.local',
            'admin',
            '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj3bp.Gm.F5u', -- 'admin123'
            'System Administrator',
            'Admin',
            '["super_admin", "admin", "user"]'::jsonb,
            true,
            true,
            '{
                "theme": "dark",
                "language": "en",
                "notifications": {
                    "email": true,
                    "push": true,
                    "marketing": false
                },
                "ai": {
                    "personality": "professional",
                    "verbosity": "detailed",
                    "temperature": 0.7
                }
            }'::jsonb,
            '550e8400-e29b-41d4-a716-446655440000'::uuid
        );

        -- Log admin user creation
        INSERT INTO audit_logs (event_type, event_category, severity, user_id, details, resource_type, resource_id, action)
        VALUES ('USER_CREATED', 'authentication', 'info', admin_user_id, '{"method": "migration", "role": "admin"}', 'user', admin_user_id::text, 'create');

        RAISE NOTICE 'Admin user created: admin@ai-karen.local (password: admin123)';
    END IF;
END $$;

-- Create demo user
DO $$
DECLARE
    demo_user_id UUID;
BEGIN
    -- Check if demo user already exists
    IF NOT EXISTS (SELECT 1 FROM users WHERE email = 'demo@ai-karen.local') THEN
        demo_user_id := gen_random_uuid();

        -- Insert demo user
        INSERT INTO users (
            id,
            email,
            username,
            password_hash,
            full_name,
            display_name,
            roles,
            is_verified,
            is_active,
            preferences,
            tenant_id
        ) VALUES (
            demo_user_id,
            'demo@ai-karen.local',
            'demo',
            '$2b$12$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi', -- 'demo123'
            'Demo User',
            'Demo',
            '["user"]'::jsonb,
            true,
            true,
            '{
                "theme": "light",
                "language": "en",
                "notifications": {
                    "email": false,
                    "push": false,
                    "marketing": false
                },
                "ai": {
                    "personality": "friendly",
                    "verbosity": "balanced",
                    "temperature": 0.7
                }
            }'::jsonb,
            '550e8400-e29b-41d4-a716-446655440000'::uuid
        );

        -- Log demo user creation
        INSERT INTO audit_logs (event_type, event_category, severity, user_id, details, resource_type, resource_id, action)
        VALUES ('USER_CREATED', 'authentication', 'info', demo_user_id, '{"method": "migration", "role": "demo"}', 'user', demo_user_id::text, 'create');

        RAISE NOTICE 'Demo user created: demo@ai-karen.local (password: demo123)';
    END IF;
END $$;

-- ============================================================================
-- UTILITY FUNCTIONS
-- ============================================================================

-- Function to clean up expired sessions
CREATE OR REPLACE FUNCTION cleanup_expired_sessions()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM user_sessions
    WHERE expires_at < NOW()
       OR (is_active = false AND invalidated_at < NOW() - INTERVAL '7 days');

    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Function to clean up expired tokens
CREATE OR REPLACE FUNCTION cleanup_expired_tokens()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    -- Clean up expired password reset tokens
    DELETE FROM password_reset_tokens
    WHERE expires_at < NOW()
       OR (is_used = true AND used_at < NOW() - INTERVAL '1 day');

    -- Clean up expired email verification tokens
    DELETE FROM email_verification_tokens
    WHERE expires_at < NOW()
       OR (is_used = true AND used_at < NOW() - INTERVAL '1 day');

    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Function to clean up old audit logs (keep last 90 days)
CREATE OR REPLACE FUNCTION cleanup_old_audit_logs(days_to_keep INTEGER DEFAULT 90)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM audit_logs
    WHERE timestamp < NOW() - INTERVAL '1 day' * days_to_keep;

    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Function to get system statistics
CREATE OR REPLACE FUNCTION get_system_stats()
RETURNS TABLE(
    total_users INTEGER,
    active_users INTEGER,
    verified_users INTEGER,
    total_conversations INTEGER,
    total_messages INTEGER,
    active_sessions INTEGER,
    installed_plugins INTEGER,
    audit_events_today INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        (SELECT COUNT(*)::INTEGER FROM users) as total_users,
        (SELECT COUNT(*)::INTEGER FROM users WHERE is_active = true) as active_users,
        (SELECT COUNT(*)::INTEGER FROM users WHERE is_verified = true) as verified_users,
        (SELECT COUNT(*)::INTEGER FROM conversations) as total_conversations,
        (SELECT COUNT(*)::INTEGER FROM messages) as total_messages,
        (SELECT COUNT(*)::INTEGER FROM user_sessions WHERE is_active = true AND expires_at > NOW()) as active_sessions,
        (SELECT COUNT(*)::INTEGER FROM plugins WHERE is_installed = true) as installed_plugins,
        (SELECT COUNT(*)::INTEGER FROM audit_logs WHERE timestamp >= CURRENT_DATE) as audit_events_today;
END;
$$ LANGUAGE plpgsql;

-- Function to lock user account
CREATE OR REPLACE FUNCTION lock_user_account(user_email VARCHAR, lock_minutes INTEGER DEFAULT 15)
RETURNS BOOLEAN AS $$
DECLARE
    user_found BOOLEAN := false;
    target_user_id UUID;
BEGIN
    -- Find user
    SELECT id INTO target_user_id
    FROM users
    WHERE email = user_email AND is_active = true;

    IF target_user_id IS NOT NULL THEN
        -- Lock the account
        UPDATE users
        SET locked_until = NOW() + INTERVAL '1 minute' * lock_minutes,
            failed_login_attempts = failed_login_attempts + 1,
            updated_at = NOW()
        WHERE id = target_user_id;

        -- Invalidate all active sessions
        UPDATE user_sessions
        SET is_active = false,
            invalidated_at = NOW(),
            invalidation_reason = 'account_locked'
        WHERE user_id = target_user_id AND is_active = true;

        -- Log the action
        INSERT INTO audit_logs (event_type, event_category, severity, user_id, details, action)
        VALUES ('ACCOUNT_LOCKED', 'security', 'warning', target_user_id, jsonb_build_object('lock_minutes', lock_minutes), 'lock');

        user_found := true;
    END IF;

    RETURN user_found;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- VIEWS FOR COMMON QUERIES
-- ============================================================================

-- View for active user sessions
CREATE OR REPLACE VIEW active_sessions AS
SELECT
    s.id,
    s.user_id,
    u.email,
    u.full_name,
    s.session_token,
    s.ip_address,
    s.user_agent,
    s.last_activity_at,
    s.expires_at,
    s.risk_score,
    s.created_at
FROM user_sessions s
JOIN users u ON s.user_id = u.id
WHERE s.is_active = true
  AND s.expires_at > NOW()
  AND u.is_active = true;

-- View for recent user activity
CREATE OR REPLACE VIEW recent_user_activity AS
SELECT
    u.id,
    u.email,
    u.full_name,
    u.last_login_at,
    u.last_login_ip,
    COUNT(DISTINCT c.id) as conversation_count,
    COUNT(m.id) as message_count,
    MAX(m.created_at) as last_message_at
FROM users u
LEFT JOIN conversations c ON u.id = c.user_id
LEFT JOIN messages m ON c.id = m.conversation_id
WHERE u.is_active = true
GROUP BY u.id, u.email, u.full_name, u.last_login_at, u.last_login_ip
ORDER BY u.last_login_at DESC NULLS LAST;

-- ============================================================================
-- PERMISSIONS (Adjust username as needed for your deployment)
-- ============================================================================

-- Grant permissions to application user (adjust username as needed)
DO $$
BEGIN
    -- Grant table permissions
    GRANT SELECT, INSERT, UPDATE, DELETE ON tenants TO karen_user;
    GRANT SELECT, INSERT, UPDATE, DELETE ON users TO karen_user;
    GRANT SELECT, INSERT, UPDATE, DELETE ON user_sessions TO karen_user;
    GRANT SELECT, INSERT, UPDATE, DELETE ON conversations TO karen_user;
    GRANT SELECT, INSERT, UPDATE, DELETE ON messages TO karen_user;
    GRANT SELECT, INSERT, UPDATE, DELETE ON plugins TO karen_user;
    GRANT SELECT, INSERT, UPDATE, DELETE ON plugin_settings TO karen_user;
    GRANT SELECT, INSERT, UPDATE, DELETE ON audit_logs TO karen_user;
    GRANT SELECT, INSERT, UPDATE, DELETE ON password_reset_tokens TO karen_user;
    GRANT SELECT, INSERT, UPDATE, DELETE ON email_verification_tokens TO karen_user;
    GRANT SELECT, INSERT, UPDATE, DELETE ON rate_limits TO karen_user;
    GRANT SELECT, INSERT, UPDATE, DELETE ON system_config TO karen_user;

    -- Grant view permissions
    GRANT SELECT ON active_sessions TO karen_user;
    GRANT SELECT ON recent_user_activity TO karen_user;

    -- Grant function permissions
    GRANT EXECUTE ON FUNCTION cleanup_expired_sessions() TO karen_user;
    GRANT EXECUTE ON FUNCTION cleanup_expired_tokens() TO karen_user;
    GRANT EXECUTE ON FUNCTION cleanup_old_audit_logs(INTEGER) TO karen_user;
    GRANT EXECUTE ON FUNCTION get_system_stats() TO karen_user;
    GRANT EXECUTE ON FUNCTION lock_user_account(VARCHAR, INTEGER) TO karen_user;

    -- Grant sequence permissions
    GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO karen_user;

    RAISE NOTICE 'Database permissions granted to karen_user';
EXCEPTION
    WHEN undefined_object THEN
        RAISE NOTICE 'User karen_user does not exist, permissions not granted';
END $$;

-- ============================================================================
-- VERIFICATION AND STATUS
-- ============================================================================

-- Display migration completion status
DO $$
BEGIN
    RAISE NOTICE '=================================================================';
    RAISE NOTICE 'AI Karen Production Database Schema Migration Complete';
    RAISE NOTICE '=================================================================';
    RAISE NOTICE 'Schema Features:';
    RAISE NOTICE '- Multi-tenant architecture with tenants table';
    RAISE NOTICE '- Comprehensive user management with all required fields';
    RAISE NOTICE '- Production-ready authentication and session management';
    RAISE NOTICE '- Full conversation and messaging system';
    RAISE NOTICE '- Plugin management and configuration';
    RAISE NOTICE '- Comprehensive audit logging';
    RAISE NOTICE '- Rate limiting and security features';
    RAISE NOTICE '- System configuration management';
    RAISE NOTICE '=================================================================';
    RAISE NOTICE 'Default Accounts:';
    RAISE NOTICE '- admin@ai-karen.local (password: admin123) - CHANGE IMMEDIATELY';
    RAISE NOTICE '- demo@ai-karen.local (password: demo123)';
    RAISE NOTICE '=================================================================';
END $$;

-- Display system statistics
SELECT * FROM get_system_stats();

COMMIT;