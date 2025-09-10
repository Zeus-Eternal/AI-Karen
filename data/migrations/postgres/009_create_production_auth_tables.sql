-- Production Authentication Tables Migration
-- Creates all necessary tables for production database authentication

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table with proper security features
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Authentication fields
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    
    -- Profile fields
    full_name VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    is_verified BOOLEAN DEFAULT FALSE NOT NULL,
    
    -- Role and permissions
    roles TEXT NOT NULL DEFAULT '["user"]', -- JSON array of roles
    tenant_id VARCHAR(36) NOT NULL DEFAULT 'default',
    
    -- Preferences
    preferences TEXT, -- JSON preferences
    
    -- 2FA settings
    two_factor_enabled BOOLEAN DEFAULT FALSE NOT NULL,
    two_factor_secret VARCHAR(32),
    backup_codes TEXT, -- JSON array of backup codes
    
    -- Security tracking
    failed_login_attempts INTEGER DEFAULT 0 NOT NULL,
    locked_until TIMESTAMP,
    last_login_at TIMESTAMP,
    last_login_ip VARCHAR(45), -- IPv6 compatible
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Create indexes for users table
CREATE INDEX IF NOT EXISTS idx_user_email_active ON users(email, is_active);
CREATE INDEX IF NOT EXISTS idx_user_tenant ON users(tenant_id);
CREATE INDEX IF NOT EXISTS idx_user_created ON users(created_at);

-- User sessions table for production session management
CREATE TABLE IF NOT EXISTS user_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Foreign key to user
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Session data
    session_token VARCHAR(255) UNIQUE NOT NULL,
    refresh_token VARCHAR(255) UNIQUE,
    
    -- Session metadata
    user_agent TEXT,
    ip_address VARCHAR(45),
    device_fingerprint VARCHAR(255),
    
    -- Session state
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    last_activity_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    -- Security flags
    is_suspicious BOOLEAN DEFAULT FALSE NOT NULL,
    risk_score INTEGER DEFAULT 0 NOT NULL, -- 0-100 risk score
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Create indexes for user_sessions table
CREATE INDEX IF NOT EXISTS idx_session_token_active ON user_sessions(session_token, is_active);
CREATE INDEX IF NOT EXISTS idx_session_user_active ON user_sessions(user_id, is_active);
CREATE INDEX IF NOT EXISTS idx_session_expires ON user_sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_session_activity ON user_sessions(last_activity_at);

-- Chat memory metadata for user isolation
CREATE TABLE IF NOT EXISTS chat_memories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Foreign key to user
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Chat identification
    chat_id VARCHAR(36) NOT NULL,
    
    -- Memory settings (user-configurable)
    short_term_days INTEGER DEFAULT 1 NOT NULL,
    long_term_days INTEGER DEFAULT 30 NOT NULL,
    tail_turns INTEGER DEFAULT 3 NOT NULL,
    summarize_threshold_tokens INTEGER DEFAULT 3000 NOT NULL,
    
    -- Memory state
    total_turns INTEGER DEFAULT 0 NOT NULL,
    last_summarized_at TIMESTAMP,
    current_token_count INTEGER DEFAULT 0 NOT NULL,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Create indexes for chat_memories table
CREATE INDEX IF NOT EXISTS idx_chat_user_chat ON chat_memories(user_id, chat_id);
CREATE INDEX IF NOT EXISTS idx_chat_updated ON chat_memories(updated_at);

-- Password reset tokens table
CREATE TABLE IF NOT EXISTS password_reset_tokens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Foreign key to user
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Token data
    token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    is_used BOOLEAN DEFAULT FALSE NOT NULL,
    
    -- Security tracking
    ip_address VARCHAR(45),
    user_agent TEXT,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    used_at TIMESTAMP
);

-- Create indexes for password_reset_tokens table
CREATE INDEX IF NOT EXISTS idx_reset_token_expires ON password_reset_tokens(token, expires_at, is_used);
CREATE INDEX IF NOT EXISTS idx_reset_user ON password_reset_tokens(user_id);

-- Email verification tokens table
CREATE TABLE IF NOT EXISTS email_verification_tokens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Foreign key to user
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Token data
    token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    is_used BOOLEAN DEFAULT FALSE NOT NULL,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    used_at TIMESTAMP
);

-- Create indexes for email_verification_tokens table
CREATE INDEX IF NOT EXISTS idx_verify_token_expires ON email_verification_tokens(token, expires_at, is_used);
CREATE INDEX IF NOT EXISTS idx_verify_user ON email_verification_tokens(user_id);

-- Create trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply the trigger to tables that need it
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_sessions_updated_at BEFORE UPDATE ON user_sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_chat_memories_updated_at BEFORE UPDATE ON chat_memories
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert default admin user if not exists
-- Password is 'admin123' hashed with bcrypt (12 rounds)
INSERT INTO users (
    email, 
    password_hash, 
    full_name, 
    is_verified, 
    roles, 
    tenant_id,
    preferences
) VALUES (
    'admin@karen.ai',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj3bp.Gm.F5u', -- admin123
    'System Administrator',
    TRUE,
    '["admin", "user"]',
    'default',
    '{"personalityTone": "professional", "personalityVerbosity": "detailed", "memoryDepth": "deep", "customPersonaInstructions": "You are an AI assistant for system administration.", "preferredLLMProvider": "llamacpp", "preferredModel": "llama3.2:latest", "temperature": 0.7, "maxTokens": 2000, "notifications": {"email": true, "push": true}, "ui": {"theme": "dark", "language": "en", "avatarUrl": ""}, "chatMemory": {"shortTermDays": 7, "longTermDays": 90, "tailTurns": 5, "summarizeThresholdTokens": 4000}}'
) ON CONFLICT (email) DO NOTHING;

-- Insert demo user if not exists
-- Password is 'demo123' hashed with bcrypt (12 rounds)
INSERT INTO users (
    email, 
    password_hash, 
    full_name, 
    is_verified, 
    roles, 
    tenant_id,
    preferences
) VALUES (
    'demo@karen.ai',
    '$2b$12$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi', -- demo123
    'Demo User',
    TRUE,
    '["user"]',
    'default',
    '{"personalityTone": "friendly", "personalityVerbosity": "balanced", "memoryDepth": "medium", "customPersonaInstructions": "", "preferredLLMProvider": "llamacpp", "preferredModel": "llama3.2:latest", "temperature": 0.7, "maxTokens": 1000, "notifications": {"email": false, "push": false}, "ui": {"theme": "light", "language": "en", "avatarUrl": ""}, "chatMemory": {"shortTermDays": 1, "longTermDays": 30, "tailTurns": 3, "summarizeThresholdTokens": 3000}}'
) ON CONFLICT (email) DO NOTHING;

-- Create a function to clean up expired sessions and tokens
CREATE OR REPLACE FUNCTION cleanup_expired_auth_data()
RETURNS void AS $$
BEGIN
    -- Clean up expired sessions
    DELETE FROM user_sessions 
    WHERE expires_at < CURRENT_TIMESTAMP;
    
    -- Clean up expired password reset tokens
    DELETE FROM password_reset_tokens 
    WHERE expires_at < CURRENT_TIMESTAMP;
    
    -- Clean up expired email verification tokens
    DELETE FROM email_verification_tokens 
    WHERE expires_at < CURRENT_TIMESTAMP;
    
    -- Log cleanup
    RAISE NOTICE 'Cleaned up expired authentication data at %', CURRENT_TIMESTAMP;
END;
$$ LANGUAGE plpgsql;

-- Create a view for active user sessions
CREATE OR REPLACE VIEW active_user_sessions AS
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
    s.is_suspicious,
    s.created_at
FROM user_sessions s
JOIN users u ON s.user_id = u.id
WHERE s.is_active = TRUE 
  AND s.expires_at > CURRENT_TIMESTAMP
  AND u.is_active = TRUE;

-- Grant necessary permissions (adjust as needed for your setup)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON users TO your_app_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON user_sessions TO your_app_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON chat_memories TO your_app_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON password_reset_tokens TO your_app_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON email_verification_tokens TO your_app_user;
-- GRANT SELECT ON active_user_sessions TO your_app_user;

COMMIT;