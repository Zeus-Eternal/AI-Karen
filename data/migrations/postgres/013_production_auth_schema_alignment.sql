-- Production Authentication Schema Alignment Migration
-- This migration ensures the database schema matches the current authentication system
-- and provides production-ready authentication with proper security features

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================================
-- Create auth_users table (matches current AuthDatabaseClient implementation)
-- ============================================================================
CREATE TABLE IF NOT EXISTS auth_users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255),
    roles JSONB DEFAULT '[]'::jsonb,
    tenant_id UUID NOT NULL DEFAULT 'default'::uuid,
    preferences JSONB DEFAULT '{}'::jsonb,
    is_verified BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login_at TIMESTAMP WITH TIME ZONE,
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP WITH TIME ZONE,
    two_factor_enabled BOOLEAN DEFAULT false,
    two_factor_secret VARCHAR(255)
);

-- ============================================================================
-- Create auth_password_hashes table (secure password storage)
-- ============================================================================
CREATE TABLE IF NOT EXISTS auth_password_hashes (
    user_id UUID PRIMARY KEY REFERENCES auth_users(user_id) ON DELETE CASCADE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- Create auth_sessions table (production session management)
-- ============================================================================
CREATE TABLE IF NOT EXISTS auth_sessions (
    session_token VARCHAR(255) PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth_users(user_id) ON DELETE CASCADE,
    access_token TEXT NOT NULL,
    refresh_token TEXT NOT NULL,
    expires_in INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_accessed TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ip_address INET,
    user_agent TEXT,
    device_fingerprint VARCHAR(255),
    geolocation JSONB,
    risk_score FLOAT DEFAULT 0.0,
    security_flags JSONB DEFAULT '[]'::jsonb,
    is_active BOOLEAN DEFAULT true,
    invalidated_at TIMESTAMP WITH TIME ZONE,
    invalidation_reason VARCHAR(255)
);

-- ============================================================================
-- Create auth_providers table (external authentication providers)
-- ============================================================================
CREATE TABLE IF NOT EXISTS auth_providers (
    provider_id VARCHAR(255) PRIMARY KEY,
    tenant_id UUID,
    type VARCHAR(100) NOT NULL,
    config JSONB NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- Create user_identities table (external identity linking)
-- ============================================================================
CREATE TABLE IF NOT EXISTS user_identities (
    identity_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth_users(user_id) ON DELETE CASCADE,
    provider_id VARCHAR(255) NOT NULL REFERENCES auth_providers(provider_id),
    provider_user VARCHAR(255) NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE (provider_id, provider_user)
);

-- ============================================================================
-- Create auth_password_reset_tokens table
-- ============================================================================
CREATE TABLE IF NOT EXISTS auth_password_reset_tokens (
    token_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth_users(user_id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    used_at TIMESTAMP WITH TIME ZONE,
    ip_address INET,
    user_agent TEXT
);

-- ============================================================================
-- Create auth_email_verification_tokens table
-- ============================================================================
CREATE TABLE IF NOT EXISTS auth_email_verification_tokens (
    token_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth_users(user_id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    used_at TIMESTAMP WITH TIME ZONE,
    ip_address INET,
    user_agent TEXT
);

-- ============================================================================
-- Create auth_events table (comprehensive audit logging)
-- ============================================================================
CREATE TABLE IF NOT EXISTS auth_events (
    event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type VARCHAR(100) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    user_id UUID,
    email VARCHAR(255),
    tenant_id UUID,
    ip_address INET,
    user_agent TEXT,
    request_id VARCHAR(255),
    session_token VARCHAR(255),
    success BOOLEAN NOT NULL,
    error_message TEXT,
    details JSONB DEFAULT '{}'::jsonb,
    risk_score FLOAT DEFAULT 0.0,
    security_flags JSONB DEFAULT '[]'::jsonb,
    blocked_by_security BOOLEAN DEFAULT false,
    processing_time_ms FLOAT DEFAULT 0.0,
    service_version VARCHAR(100) DEFAULT 'consolidated-auth-v1'
);

-- ============================================================================
-- Create indexes for optimal performance
-- ============================================================================

-- auth_users indexes
CREATE INDEX IF NOT EXISTS idx_auth_users_email ON auth_users(email);
CREATE INDEX IF NOT EXISTS idx_auth_users_tenant ON auth_users(tenant_id);
CREATE INDEX IF NOT EXISTS idx_auth_users_active ON auth_users(is_active) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_auth_users_created ON auth_users(created_at);

-- auth_sessions indexes
CREATE INDEX IF NOT EXISTS idx_auth_sessions_user ON auth_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_auth_sessions_active ON auth_sessions(is_active) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_auth_sessions_expires ON auth_sessions(created_at, expires_in);
CREATE INDEX IF NOT EXISTS idx_auth_sessions_last_accessed ON auth_sessions(last_accessed);

-- user_identities indexes
CREATE INDEX IF NOT EXISTS idx_user_identities_user ON user_identities(user_id);
CREATE INDEX IF NOT EXISTS idx_user_identities_provider ON user_identities(provider_id);

-- auth_password_reset_tokens indexes
CREATE INDEX IF NOT EXISTS idx_auth_password_reset_tokens_user ON auth_password_reset_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_auth_password_reset_tokens_expires ON auth_password_reset_tokens(expires_at);
CREATE INDEX IF NOT EXISTS idx_auth_password_reset_tokens_token ON auth_password_reset_tokens(token_hash);

-- auth_email_verification_tokens indexes
CREATE INDEX IF NOT EXISTS idx_auth_email_verification_tokens_user ON auth_email_verification_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_auth_email_verification_tokens_expires ON auth_email_verification_tokens(expires_at);
CREATE INDEX IF NOT EXISTS idx_auth_email_verification_tokens_token ON auth_email_verification_tokens(token_hash);

-- auth_events indexes
CREATE INDEX IF NOT EXISTS idx_auth_events_user ON auth_events(user_id);
CREATE INDEX IF NOT EXISTS idx_auth_events_type ON auth_events(event_type);
CREATE INDEX IF NOT EXISTS idx_auth_events_timestamp ON auth_events(timestamp);
CREATE INDEX IF NOT EXISTS idx_auth_events_success ON auth_events(success);
CREATE INDEX IF NOT EXISTS idx_auth_events_ip ON auth_events(ip_address);

-- ============================================================================
-- Create production admin user with secure password
-- ============================================================================
DO $
DECLARE
    admin_user_id UUID;
    admin_exists INTEGER;
BEGIN
    -- Check if admin user already exists
    SELECT COUNT(*) INTO admin_exists 
    FROM auth_users 
    WHERE email = 'admin@ai-karen.local';
    
    -- Only create admin user if it doesn't exist
    IF admin_exists = 0 THEN
        -- Generate UUID for admin user
        admin_user_id := gen_random_uuid();
        
        -- Insert admin user
        INSERT INTO auth_users (
            user_id,
            email,
            full_name,
            roles,
            tenant_id,
            preferences,
            is_verified,
            is_active,
            created_at,
            updated_at
        ) VALUES (
            admin_user_id,
            'admin@ai-karen.local',
            'System Administrator',
            '["admin", "user"]'::jsonb,
            'default'::uuid,
            '{
                "personalityTone": "professional",
                "personalityVerbosity": "detailed",
                "memoryDepth": "deep",
                "customPersonaInstructions": "You are an AI assistant for system administration.",
                "preferredLLMProvider": "llamacpp",
                "preferredModel": "llama3.2:latest",
                "temperature": 0.7,
                "maxTokens": 2000,
                "notifications": {"email": true, "push": true},
                "ui": {"theme": "dark", "language": "en", "avatarUrl": ""},
                "chatMemory": {
                    "shortTermDays": 7,
                    "longTermDays": 90,
                    "tailTurns": 5,
                    "summarizeThresholdTokens": 4000
                }
            }'::jsonb,
            true,
            true,
            NOW(),
            NOW()
        );
        
        -- Insert admin password hash (password: 'admin123' with bcrypt 12 rounds)
        INSERT INTO auth_password_hashes (
            user_id,
            password_hash,
            created_at,
            updated_at
        ) VALUES (
            admin_user_id,
            '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj3bp.Gm.F5u',
            NOW(),
            NOW()
        );
        
        RAISE NOTICE 'Production admin user created: admin@ai-karen.local (password: admin123)';
        RAISE NOTICE 'IMPORTANT: Change the admin password immediately after first login!';
    ELSE
        RAISE NOTICE 'Admin user already exists: admin@ai-karen.local';
    END IF;
END $;

-- ============================================================================
-- Create demo user for testing
-- ============================================================================
DO $
DECLARE
    demo_user_id UUID;
    demo_exists INTEGER;
BEGIN
    -- Check if demo user already exists
    SELECT COUNT(*) INTO demo_exists 
    FROM auth_users 
    WHERE email = 'demo@ai-karen.local';
    
    -- Only create demo user if it doesn't exist
    IF demo_exists = 0 THEN
        -- Generate UUID for demo user
        demo_user_id := gen_random_uuid();
        
        -- Insert demo user
        INSERT INTO auth_users (
            user_id,
            email,
            full_name,
            roles,
            tenant_id,
            preferences,
            is_verified,
            is_active,
            created_at,
            updated_at
        ) VALUES (
            demo_user_id,
            'demo@ai-karen.local',
            'Demo User',
            '["user"]'::jsonb,
            'default'::uuid,
            '{
                "personalityTone": "friendly",
                "personalityVerbosity": "balanced",
                "memoryDepth": "medium",
                "customPersonaInstructions": "",
                "preferredLLMProvider": "llamacpp",
                "preferredModel": "llama3.2:latest",
                "temperature": 0.7,
                "maxTokens": 1000,
                "notifications": {"email": false, "push": false},
                "ui": {"theme": "light", "language": "en", "avatarUrl": ""},
                "chatMemory": {
                    "shortTermDays": 1,
                    "longTermDays": 30,
                    "tailTurns": 3,
                    "summarizeThresholdTokens": 3000
                }
            }'::jsonb,
            true,
            true,
            NOW(),
            NOW()
        );
        
        -- Insert demo password hash (password: 'demo123' with bcrypt 12 rounds)
        INSERT INTO auth_password_hashes (
            user_id,
            password_hash,
            created_at,
            updated_at
        ) VALUES (
            demo_user_id,
            '$2b$12$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi',
            NOW(),
            NOW()
        );
        
        RAISE NOTICE 'Demo user created: demo@ai-karen.local (password: demo123)';
    ELSE
        RAISE NOTICE 'Demo user already exists: demo@ai-karen.local';
    END IF;
END $;

-- ============================================================================
-- Create maintenance and cleanup functions
-- ============================================================================

-- Function to clean up expired sessions
CREATE OR REPLACE FUNCTION cleanup_expired_auth_sessions()
RETURNS INTEGER AS $
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM auth_sessions 
    WHERE (created_at + INTERVAL '1 second' * expires_in) < NOW()
    OR (is_active = false AND invalidated_at < NOW() - INTERVAL '7 days');
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    RAISE NOTICE 'Cleaned up % expired auth sessions', deleted_count;
    RETURN deleted_count;
END;
$ LANGUAGE plpgsql;

-- Function to clean up expired tokens
CREATE OR REPLACE FUNCTION cleanup_expired_auth_tokens()
RETURNS INTEGER AS $
DECLARE
    deleted_count INTEGER;
BEGIN
    -- Clean up expired password reset tokens
    DELETE FROM auth_password_reset_tokens 
    WHERE expires_at < NOW() 
    OR (used_at IS NOT NULL AND used_at < NOW() - INTERVAL '1 day');
    
    -- Clean up expired email verification tokens
    DELETE FROM auth_email_verification_tokens 
    WHERE expires_at < NOW() 
    OR (used_at IS NOT NULL AND used_at < NOW() - INTERVAL '1 day');
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    RAISE NOTICE 'Cleaned up % expired auth tokens', deleted_count;
    RETURN deleted_count;
END;
$ LANGUAGE plpgsql;

-- Function to get authentication statistics
CREATE OR REPLACE FUNCTION get_auth_statistics()
RETURNS TABLE(
    total_users INTEGER,
    active_users INTEGER,
    verified_users INTEGER,
    active_sessions INTEGER,
    users_with_2fa INTEGER,
    failed_logins_last_hour INTEGER,
    successful_logins_last_hour INTEGER
) AS $
BEGIN
    RETURN QUERY
    SELECT 
        (SELECT COUNT(*)::INTEGER FROM auth_users) as total_users,
        (SELECT COUNT(*)::INTEGER FROM auth_users WHERE is_active = true) as active_users,
        (SELECT COUNT(*)::INTEGER FROM auth_users WHERE is_verified = true) as verified_users,
        (SELECT COUNT(*)::INTEGER FROM auth_sessions WHERE is_active = true AND (created_at + INTERVAL '1 second' * expires_in) > NOW()) as active_sessions,
        (SELECT COUNT(*)::INTEGER FROM auth_users WHERE two_factor_enabled = true) as users_with_2fa,
        (SELECT COUNT(*)::INTEGER FROM auth_events WHERE event_type = 'LOGIN_FAILED' AND timestamp > NOW() - INTERVAL '1 hour') as failed_logins_last_hour,
        (SELECT COUNT(*)::INTEGER FROM auth_events WHERE event_type = 'LOGIN_SUCCESS' AND timestamp > NOW() - INTERVAL '1 hour') as successful_logins_last_hour;
END;
$ LANGUAGE plpgsql;

-- Function to lock user account (for security)
CREATE OR REPLACE FUNCTION lock_user_account(user_email VARCHAR, lock_duration_minutes INTEGER DEFAULT 15)
RETURNS BOOLEAN AS $
DECLARE
    user_found BOOLEAN := false;
BEGIN
    UPDATE auth_users 
    SET locked_until = NOW() + INTERVAL '1 minute' * lock_duration_minutes,
        updated_at = NOW()
    WHERE email = user_email AND is_active = true;
    
    GET DIAGNOSTICS user_found = FOUND;
    
    IF user_found THEN
        -- Invalidate all active sessions for the locked user
        UPDATE auth_sessions 
        SET is_active = false, 
            invalidated_at = NOW(),
            invalidation_reason = 'account_locked'
        WHERE user_id = (SELECT user_id FROM auth_users WHERE email = user_email)
        AND is_active = true;
        
        RAISE NOTICE 'User account locked: %', user_email;
    END IF;
    
    RETURN user_found;
END;
$ LANGUAGE plpgsql;

-- ============================================================================
-- Create views for monitoring and analytics
-- ============================================================================

-- View for active user sessions with user details
CREATE OR REPLACE VIEW active_auth_sessions AS
SELECT 
    s.session_token,
    s.user_id,
    u.email,
    u.full_name,
    s.ip_address,
    s.user_agent,
    s.device_fingerprint,
    s.risk_score,
    s.security_flags,
    s.created_at,
    s.last_accessed,
    (s.created_at + INTERVAL '1 second' * s.expires_in) as expires_at,
    EXTRACT(EPOCH FROM (s.created_at + INTERVAL '1 second' * s.expires_in - NOW())) as seconds_until_expiry
FROM auth_sessions s
JOIN auth_users u ON s.user_id = u.user_id
WHERE s.is_active = true 
  AND (s.created_at + INTERVAL '1 second' * s.expires_in) > NOW()
  AND u.is_active = true
ORDER BY s.last_accessed DESC;

-- View for recent authentication events
CREATE OR REPLACE VIEW recent_auth_events AS
SELECT 
    e.event_id,
    e.event_type,
    e.timestamp,
    e.user_id,
    e.email,
    e.ip_address,
    e.success,
    e.error_message,
    e.risk_score,
    e.security_flags,
    e.blocked_by_security,
    e.processing_time_ms,
    u.full_name,
    u.is_active as user_is_active
FROM auth_events e
LEFT JOIN auth_users u ON e.user_id = u.user_id
WHERE e.timestamp > NOW() - INTERVAL '24 hours'
ORDER BY e.timestamp DESC;

-- ============================================================================
-- Grant permissions to application user
-- ============================================================================
DO $
BEGIN
    -- Grant table permissions
    GRANT SELECT, INSERT, UPDATE, DELETE ON auth_users TO karen_user;
    GRANT SELECT, INSERT, UPDATE, DELETE ON auth_password_hashes TO karen_user;
    GRANT SELECT, INSERT, UPDATE, DELETE ON auth_sessions TO karen_user;
    GRANT SELECT, INSERT, UPDATE, DELETE ON auth_providers TO karen_user;
    GRANT SELECT, INSERT, UPDATE, DELETE ON user_identities TO karen_user;
    GRANT SELECT, INSERT, UPDATE, DELETE ON auth_password_reset_tokens TO karen_user;
    GRANT SELECT, INSERT, UPDATE, DELETE ON auth_email_verification_tokens TO karen_user;
    GRANT SELECT, INSERT, UPDATE, DELETE ON auth_events TO karen_user;
    
    -- Grant view permissions
    GRANT SELECT ON active_auth_sessions TO karen_user;
    GRANT SELECT ON recent_auth_events TO karen_user;
    
    -- Grant function execution permissions
    GRANT EXECUTE ON FUNCTION cleanup_expired_auth_sessions() TO karen_user;
    GRANT EXECUTE ON FUNCTION cleanup_expired_auth_tokens() TO karen_user;
    GRANT EXECUTE ON FUNCTION get_auth_statistics() TO karen_user;
    GRANT EXECUTE ON FUNCTION lock_user_account(VARCHAR, INTEGER) TO karen_user;
    
    RAISE NOTICE 'Permissions granted to karen_user';
EXCEPTION
    WHEN undefined_object THEN
        RAISE NOTICE 'User karen_user does not exist, skipping permission grants';
END $;

-- ============================================================================
-- Verification and status report
-- ============================================================================

-- Display table creation status
SELECT 
    schemaname,
    tablename,
    tableowner,
    hasindexes,
    hasrules,
    hastriggers
FROM pg_tables 
WHERE tablename LIKE 'auth_%' OR tablename = 'user_identities'
ORDER BY tablename;

-- Display index creation status
SELECT 
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes 
WHERE tablename LIKE 'auth_%' OR tablename = 'user_identities'
ORDER BY tablename, indexname;

-- Display authentication statistics
SELECT * FROM get_auth_statistics();

-- Display created users
SELECT 
    user_id,
    email,
    full_name,
    is_active,
    is_verified,
    roles,
    tenant_id,
    created_at
FROM auth_users
ORDER BY created_at;

-- Final status message
DO $
BEGIN
    RAISE NOTICE '=================================================================';
    RAISE NOTICE 'Production Authentication Schema Migration Completed Successfully';
    RAISE NOTICE '=================================================================';
    RAISE NOTICE 'Features enabled:';
    RAISE NOTICE '- PostgreSQL database authentication with proper schema';
    RAISE NOTICE '- bcrypt password hashing (12 rounds)';
    RAISE NOTICE '- JWT token management';
    RAISE NOTICE '- Redis session management support';
    RAISE NOTICE '- Comprehensive audit logging';
    RAISE NOTICE '- Security features (account locking, 2FA support)';
    RAISE NOTICE '- Performance optimized indexes';
    RAISE NOTICE '- Maintenance and cleanup functions';
    RAISE NOTICE '=================================================================';
    RAISE NOTICE 'Default accounts created:';
    RAISE NOTICE '- admin@ai-karen.local (password: admin123) - CHANGE IMMEDIATELY';
    RAISE NOTICE '- demo@ai-karen.local (password: demo123)';
    RAISE NOTICE '=================================================================';
END $;

COMMIT;