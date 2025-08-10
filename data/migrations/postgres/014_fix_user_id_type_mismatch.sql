-- Fix user_id type mismatch between auth_users and auth_password_hashes tables
-- This migration ensures all user_id columns are consistently UUID type

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Drop existing tables to recreate with correct schema (in correct order)
DROP TABLE IF EXISTS auth_password_hashes CASCADE;
DROP TABLE IF EXISTS auth_sessions CASCADE;
DROP TABLE IF EXISTS auth_users CASCADE;

-- Create auth_users table first (parent table)
CREATE TABLE auth_users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255),
    roles JSONB DEFAULT '[]'::jsonb,
    tenant_id UUID NOT NULL DEFAULT gen_random_uuid(),
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

-- Create auth_password_hashes table with proper UUID foreign key
CREATE TABLE auth_password_hashes (
    user_id UUID PRIMARY KEY REFERENCES auth_users(user_id) ON DELETE CASCADE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create auth_sessions table
CREATE TABLE auth_sessions (
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

-- Create indexes
CREATE INDEX idx_auth_users_email ON auth_users(email);
CREATE INDEX idx_auth_users_tenant ON auth_users(tenant_id);
CREATE INDEX idx_auth_users_active ON auth_users(is_active) WHERE is_active = true;
CREATE INDEX idx_auth_sessions_user ON auth_sessions(user_id);
CREATE INDEX idx_auth_sessions_active ON auth_sessions(is_active) WHERE is_active = true;

-- Create default admin user if it doesn't exist
DO $
DECLARE
    admin_user_id UUID;
    admin_exists INTEGER;
BEGIN
    SELECT COUNT(*) INTO admin_exists 
    FROM auth_users 
    WHERE email = 'admin@ai-karen.local';
    
    IF admin_exists = 0 THEN
        admin_user_id := gen_random_uuid();
        
        INSERT INTO auth_users (
            user_id, email, full_name, roles, tenant_id, preferences, 
            is_verified, is_active, created_at, updated_at
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
                "preferredLLMProvider": "ollama",
                "preferredModel": "llama3.2:latest",
                "temperature": 0.7,
                "maxTokens": 2000
            }'::jsonb,
            true, true, NOW(), NOW()
        );
        
        INSERT INTO auth_password_hashes (user_id, password_hash, created_at, updated_at) 
        VALUES (
            admin_user_id,
            '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj3bp.Gm.F5u',
            NOW(), NOW()
        );
        
        RAISE NOTICE 'Admin user created: admin@ai-karen.local (password: admin123)';
    END IF;
END $;

-- Verify the fix
DO $
DECLARE
    users_type text;
    hashes_type text;
BEGIN
    SELECT data_type INTO users_type
    FROM information_schema.columns 
    WHERE table_name = 'auth_users' AND column_name = 'user_id';
    
    SELECT data_type INTO hashes_type
    FROM information_schema.columns 
    WHERE table_name = 'auth_password_hashes' AND column_name = 'user_id';
    
    RAISE NOTICE 'Final verification:';
    RAISE NOTICE 'auth_users.user_id type: %', users_type;
    RAISE NOTICE 'auth_password_hashes.user_id type: %', hashes_type;
    
    IF users_type = 'uuid' AND hashes_type = 'uuid' THEN
        RAISE NOTICE 'SUCCESS: user_id types are now consistent!';
    ELSE
        RAISE NOTICE 'WARNING: user_id types are still inconsistent!';
    END IF;
END $;

COMMIT;