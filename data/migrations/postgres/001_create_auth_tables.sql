-- AI Karen Authentication Tables
-- This script creates all the necessary tables for user authentication and session management
-- Compatible with PostgreSQL 12+

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- Users Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS users (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Authentication fields
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    
    -- Profile fields
    full_name VARCHAR(255),
    is_active BOOLEAN NOT NULL DEFAULT true,
    is_verified BOOLEAN NOT NULL DEFAULT false,
    
    -- Role and permissions
    roles TEXT NOT NULL DEFAULT 'user', -- JSON array of roles
    tenant_id VARCHAR(36) NOT NULL DEFAULT 'default',
    
    -- Preferences
    preferences TEXT, -- JSON preferences
    
    -- 2FA settings
    two_factor_enabled BOOLEAN NOT NULL DEFAULT false,
    two_factor_secret VARCHAR(32),
    backup_codes TEXT, -- JSON array of backup codes
    
    -- Security tracking
    failed_login_attempts INTEGER NOT NULL DEFAULT 0,
    locked_until TIMESTAMP,
    last_login_at TIMESTAMP,
    last_login_ip VARCHAR(45), -- IPv6 compatible
    
    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for users table
CREATE INDEX IF NOT EXISTS idx_user_email_active ON users(email, is_active);
CREATE INDEX IF NOT EXISTS idx_user_tenant ON users(tenant_id);
CREATE INDEX IF NOT EXISTS idx_user_created ON users(created_at);

-- Create trigger to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON users 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- User Sessions Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS user_sessions (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Foreign key to user
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Session data
    session_token VARCHAR(255) NOT NULL UNIQUE,
    refresh_token VARCHAR(255) UNIQUE,
    
    -- Session metadata
    user_agent TEXT,
    ip_address VARCHAR(45),
    device_fingerprint VARCHAR(255),
    
    -- Session state
    is_active BOOLEAN NOT NULL DEFAULT true,
    expires_at TIMESTAMP NOT NULL,
    last_activity_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Security flags
    is_suspicious BOOLEAN NOT NULL DEFAULT false,
    risk_score INTEGER NOT NULL DEFAULT 0, -- 0-100 risk score
    
    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for user_sessions table
CREATE INDEX IF NOT EXISTS idx_session_token_active ON user_sessions(session_token, is_active);
CREATE INDEX IF NOT EXISTS idx_session_user_active ON user_sessions(user_id, is_active);
CREATE INDEX IF NOT EXISTS idx_session_expires ON user_sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_session_activity ON user_sessions(last_activity_at);

-- Create trigger for user_sessions updated_at
CREATE TRIGGER update_user_sessions_updated_at 
    BEFORE UPDATE ON user_sessions 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- Chat Memories Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS chat_memories (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Foreign key to user
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Chat identification
    chat_id VARCHAR(36) NOT NULL,
    
    -- Memory settings (user-configurable)
    short_term_days INTEGER NOT NULL DEFAULT 1,
    long_term_days INTEGER NOT NULL DEFAULT 30,
    tail_turns INTEGER NOT NULL DEFAULT 3,
    summarize_threshold_tokens INTEGER NOT NULL DEFAULT 3000,
    
    -- Memory state
    total_turns INTEGER NOT NULL DEFAULT 0,
    last_summarized_at TIMESTAMP,
    current_token_count INTEGER NOT NULL DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for chat_memories table
CREATE INDEX IF NOT EXISTS idx_chat_user_chat ON chat_memories(user_id, chat_id);
CREATE INDEX IF NOT EXISTS idx_chat_updated ON chat_memories(updated_at);

-- Create trigger for chat_memories updated_at
CREATE TRIGGER update_chat_memories_updated_at 
    BEFORE UPDATE ON chat_memories 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- Password Reset Tokens Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS password_reset_tokens (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Foreign key to user
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Token data
    token VARCHAR(255) NOT NULL UNIQUE,
    expires_at TIMESTAMP NOT NULL,
    is_used BOOLEAN NOT NULL DEFAULT false,
    
    -- Security tracking
    ip_address VARCHAR(45),
    user_agent TEXT,
    
    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    used_at TIMESTAMP
);

-- Create indexes for password_reset_tokens table
CREATE INDEX IF NOT EXISTS idx_reset_token_expires ON password_reset_tokens(token, expires_at, is_used);
CREATE INDEX IF NOT EXISTS idx_reset_user ON password_reset_tokens(user_id);

-- ============================================================================
-- Email Verification Tokens Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS email_verification_tokens (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Foreign key to user
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Token data
    token VARCHAR(255) NOT NULL UNIQUE,
    expires_at TIMESTAMP NOT NULL,
    is_used BOOLEAN NOT NULL DEFAULT false,
    
    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    used_at TIMESTAMP
);

-- Create indexes for email_verification_tokens table
CREATE INDEX IF NOT EXISTS idx_verify_token_expires ON email_verification_tokens(token, expires_at, is_used);
CREATE INDEX IF NOT EXISTS idx_verify_user ON email_verification_tokens(user_id);

-- ============================================================================
-- Insert Default Test User (for development/testing)
-- ============================================================================
-- Note: This creates a test user with email 'test@example.com' and password 'testpassword'
-- The password hash is generated using bcrypt with 12 rounds
-- Remove this section in production deployments

DO $$
DECLARE
    test_user_exists INTEGER;
BEGIN
    -- Check if test user already exists
    SELECT COUNT(*) INTO test_user_exists 
    FROM users 
    WHERE email = 'test@example.com';
    
    -- Only create test user if it doesn't exist
    IF test_user_exists = 0 THEN
        INSERT INTO users (
            id,
            email,
            password_hash,
            full_name,
            is_active,
            is_verified,
            roles,
            tenant_id,
            created_at,
            updated_at
        ) VALUES (
            uuid_generate_v4(),
            'test@example.com',
            '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj3bp.Txjyvq', -- 'testpassword'
            'Test User',
            true,
            true,
            '["user"]',
            'default',
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP
        );
        
        RAISE NOTICE 'Test user created: test@example.com / testpassword';
    ELSE
        RAISE NOTICE 'Test user already exists: test@example.com';
    END IF;
END $$;

-- ============================================================================
-- Create Admin User (for development/testing)
-- ============================================================================
-- Note: This creates an admin user with email 'admin@example.com' and password 'adminpassword'
-- Remove this section in production deployments

DO $$
DECLARE
    admin_user_exists INTEGER;
BEGIN
    -- Check if admin user already exists
    SELECT COUNT(*) INTO admin_user_exists 
    FROM users 
    WHERE email = 'admin@example.com';
    
    -- Only create admin user if it doesn't exist
    IF admin_user_exists = 0 THEN
        INSERT INTO users (
            id,
            email,
            password_hash,
            full_name,
            is_active,
            is_verified,
            roles,
            tenant_id,
            created_at,
            updated_at
        ) VALUES (
            uuid_generate_v4(),
            'admin@example.com',
            '$2b$12$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi', -- 'adminpassword'
            'Admin User',
            true,
            true,
            '["admin", "user"]',
            'default',
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP
        );
        
        RAISE NOTICE 'Admin user created: admin@example.com / adminpassword';
    ELSE
        RAISE NOTICE 'Admin user already exists: admin@example.com';
    END IF;
END $$;

-- ============================================================================
-- Cleanup and Maintenance Functions
-- ============================================================================

-- Function to clean up expired sessions
CREATE OR REPLACE FUNCTION cleanup_expired_sessions()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM user_sessions 
    WHERE expires_at < CURRENT_TIMESTAMP 
    OR (is_active = false AND updated_at < CURRENT_TIMESTAMP - INTERVAL '7 days');
    
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
    WHERE expires_at < CURRENT_TIMESTAMP 
    OR (is_used = true AND used_at < CURRENT_TIMESTAMP - INTERVAL '1 day');
    
    -- Clean up expired email verification tokens
    DELETE FROM email_verification_tokens 
    WHERE expires_at < CURRENT_TIMESTAMP 
    OR (is_used = true AND used_at < CURRENT_TIMESTAMP - INTERVAL '1 day');
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Function to get user statistics
CREATE OR REPLACE FUNCTION get_user_stats()
RETURNS TABLE(
    total_users INTEGER,
    active_users INTEGER,
    verified_users INTEGER,
    active_sessions INTEGER,
    users_with_2fa INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        (SELECT COUNT(*)::INTEGER FROM users) as total_users,
        (SELECT COUNT(*)::INTEGER FROM users WHERE is_active = true) as active_users,
        (SELECT COUNT(*)::INTEGER FROM users WHERE is_verified = true) as verified_users,
        (SELECT COUNT(*)::INTEGER FROM user_sessions WHERE is_active = true AND expires_at > CURRENT_TIMESTAMP) as active_sessions,
        (SELECT COUNT(*)::INTEGER FROM users WHERE two_factor_enabled = true) as users_with_2fa;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- Grant Permissions
-- ============================================================================
-- Grant necessary permissions to the application user
-- Adjust the username as needed for your deployment

GRANT SELECT, INSERT, UPDATE, DELETE ON users TO karen_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON user_sessions TO karen_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON chat_memories TO karen_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON password_reset_tokens TO karen_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON email_verification_tokens TO karen_user;

GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO karen_user;

-- ============================================================================
-- Verification Queries
-- ============================================================================
-- Run these queries to verify the tables were created correctly

-- Check table creation
SELECT 
    schemaname,
    tablename,
    tableowner
FROM pg_tables 
WHERE tablename IN ('users', 'user_sessions', 'chat_memories', 'password_reset_tokens', 'email_verification_tokens')
ORDER BY tablename;

-- Check indexes
SELECT 
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes 
WHERE tablename IN ('users', 'user_sessions', 'chat_memories', 'password_reset_tokens', 'email_verification_tokens')
ORDER BY tablename, indexname;

-- Check user statistics
SELECT * FROM get_user_stats();

-- Show created users
SELECT 
    id,
    email,
    full_name,
    is_active,
    is_verified,
    roles,
    tenant_id,
    created_at
FROM users
ORDER BY created_at;

COMMIT;