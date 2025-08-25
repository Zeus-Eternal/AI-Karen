#!/usr/bin/env python3
"""
Quick fix for authentication schema user_id type mismatch
"""

import asyncio
import asyncpg
import os
from pathlib import Path

async def run_schema_fix():
    """Run the schema fix migration"""
    
    # Database connection details
    db_config = {
        'host': 'localhost',
        'port': 5432,
        'user': 'karen_user',
        'password': 'karen_secure_pass_change_me',
        'database': 'ai_karen'
    }
    
    try:
        print("Connecting to database...")
        conn = await asyncpg.connect(**db_config)
        
        print("Running schema fix migration...")
        
        # Run the basic schema creation first
        basic_schema = """
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
        """
        
        await conn.execute(basic_schema)
        print("✅ Basic schema created successfully")
        
        # Create admin user
        print("Creating admin user...")
        admin_user_id = await conn.fetchval("SELECT gen_random_uuid()")
        
        await conn.execute("""
            INSERT INTO auth_users (
                user_id, email, full_name, roles, tenant_id, preferences, 
                is_verified, is_active, created_at, updated_at
            ) VALUES (
                $1, 'admin@ai-karen.local', 'System Administrator',
                '["admin", "user"]'::jsonb, gen_random_uuid(),
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
            )
        """, admin_user_id)
        
        await conn.execute("""
            INSERT INTO auth_password_hashes (user_id, password_hash, created_at, updated_at) 
            VALUES ($1, '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj3bp.Gm.F5u', NOW(), NOW())
        """, admin_user_id)
        
        print("✅ Admin user created: admin@ai-karen.local (password: admin123)")
        
        print("Verifying schema...")
        # Check user_id types
        users_type = await conn.fetchval("""
            SELECT data_type 
            FROM information_schema.columns 
            WHERE table_name = 'auth_users' AND column_name = 'user_id'
        """)
        
        hashes_type = await conn.fetchval("""
            SELECT data_type 
            FROM information_schema.columns 
            WHERE table_name = 'auth_password_hashes' AND column_name = 'user_id'
        """)
        
        print(f"auth_users.user_id type: {users_type}")
        print(f"auth_password_hashes.user_id type: {hashes_type}")
        
        if users_type == 'uuid' and hashes_type == 'uuid':
            print("✅ SUCCESS: Schema fix completed successfully!")
            print("✅ user_id types are now consistent")
        else:
            print("❌ WARNING: Schema fix may not have completed properly")
        
        # Check if admin user exists
        admin_count = await conn.fetchval("""
            SELECT COUNT(*) FROM auth_users WHERE email = 'admin@ai-karen.local'
        """)
        
        if admin_count > 0:
            print("✅ Admin user exists: admin@ai-karen.local")
        else:
            print("❌ Admin user not found")
        
        await conn.close()
        print("Database connection closed.")
        
    except Exception as e:
        print(f"❌ Error running schema fix: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(run_schema_fix())
    if success:
        print("\n🎉 Schema fix completed! You can now restart your authentication service.")
    else:
        print("\n💥 Schema fix failed. Please check the error messages above.")