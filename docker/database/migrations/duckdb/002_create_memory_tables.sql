-- DuckDB Memory and Role Tables Creation
-- This migration creates memory and role management tables

-- Create long term memory table
CREATE TABLE IF NOT EXISTS long_term_memory (
    id INTEGER PRIMARY KEY,
    user_id VARCHAR NOT NULL,
    memory_json VARCHAR NOT NULL,
    memory_type VARCHAR DEFAULT 'general', -- 'general', 'preference', 'context', 'skill'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP, -- NULL for permanent memories
    importance_score FLOAT DEFAULT 0.5, -- 0.0 to 1.0 importance rating
    tags VARCHAR -- Comma-separated tags for categorization
);

-- Create user roles table with enhanced structure
CREATE TABLE IF NOT EXISTS user_roles (
    id INTEGER PRIMARY KEY,
    user_id VARCHAR NOT NULL,
    role VARCHAR NOT NULL,
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    granted_by VARCHAR,
    expires_at TIMESTAMP, -- NULL for permanent roles
    is_active BOOLEAN DEFAULT true,
    metadata VARCHAR -- JSON string for role-specific data
);

-- Create user sessions table for tracking active sessions
CREATE TABLE IF NOT EXISTS user_sessions (
    session_id VARCHAR PRIMARY KEY,
    user_id VARCHAR NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    ip_address VARCHAR,
    user_agent VARCHAR,
    is_active BOOLEAN DEFAULT true
);

-- Create indexes for long_term_memory
CREATE INDEX IF NOT EXISTS idx_long_term_memory_user_id ON long_term_memory(user_id);
CREATE INDEX IF NOT EXISTS idx_long_term_memory_type ON long_term_memory(memory_type);
CREATE INDEX IF NOT EXISTS idx_long_term_memory_created_at ON long_term_memory(created_at);
CREATE INDEX IF NOT EXISTS idx_long_term_memory_importance ON long_term_memory(importance_score);
CREATE INDEX IF NOT EXISTS idx_long_term_memory_expires_at ON long_term_memory(expires_at);

-- Create indexes for user_roles
CREATE INDEX IF NOT EXISTS idx_user_roles_user_id ON user_roles(user_id);
CREATE INDEX IF NOT EXISTS idx_user_roles_role ON user_roles(role);
CREATE INDEX IF NOT EXISTS idx_user_roles_granted_at ON user_roles(granted_at);
CREATE INDEX IF NOT EXISTS idx_user_roles_is_active ON user_roles(is_active);

-- Create indexes for user_sessions
CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_last_activity ON user_sessions(last_activity);
CREATE INDEX IF NOT EXISTS idx_user_sessions_is_active ON user_sessions(is_active);