#!/usr/bin/env python3
"""
Simple database initialization script
Creates the database tables and a test user
"""

import asyncio
import asyncpg
import bcrypt
import json
from datetime import datetime

async def init_database():
    """Initialize the database with tables and a test user"""
    
    # Database connection parameters
    DB_CONFIG = {
        'host': 'localhost',
        'port': 5432,
        'user': 'karen_user',
        'password': 'karen_secure_pass_change_me',
        'database': 'ai_karen'
    }
    
    try:
        # Connect to PostgreSQL
        conn = await asyncpg.connect(**DB_CONFIG)
        print("✅ Connected to PostgreSQL")
        
        # Create auth_users table
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS auth_users (
                user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                email TEXT UNIQUE NOT NULL,
                full_name TEXT,
                password_hash TEXT,
                tenant_id TEXT DEFAULT 'default',
                roles JSONB NOT NULL DEFAULT '["user"]'::jsonb,
                preferences JSONB DEFAULT '{}'::jsonb,
                is_verified BOOLEAN DEFAULT TRUE,
                is_active BOOLEAN DEFAULT TRUE,
                two_factor_enabled BOOLEAN DEFAULT FALSE,
                two_factor_secret TEXT,
                created_at TIMESTAMP NOT NULL DEFAULT now(),
                updated_at TIMESTAMP NOT NULL DEFAULT now(),
                last_login_at TIMESTAMP,
                failed_login_attempts INT DEFAULT 0,
                locked_until TIMESTAMP
            )
        ''')
        print("✅ Created auth_users table")
        
        # Create auth_sessions table
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS auth_sessions (
                session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID NOT NULL REFERENCES auth_users(user_id) ON DELETE CASCADE,
                access_token TEXT NOT NULL,
                refresh_token TEXT NOT NULL,
                expires_in INT NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT now(),
                last_accessed TIMESTAMP NOT NULL DEFAULT now(),
                ip_address TEXT,
                user_agent TEXT,
                device_fingerprint TEXT,
                geolocation JSONB,
                risk_score NUMERIC(5,2) DEFAULT 0,
                security_flags JSONB DEFAULT '[]'::jsonb,
                is_active BOOLEAN DEFAULT TRUE,
                invalidated_at TIMESTAMP,
                invalidation_reason TEXT
            )
        ''')
        print("✅ Created auth_sessions table")
        
        # Create a test user
        test_email = "admin@karen.ai"
        test_password = "admin123"
        
        # Hash the password
        password_hash = bcrypt.hashpw(test_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Check if user already exists
        existing_user = await conn.fetchrow('SELECT user_id FROM auth_users WHERE email = $1', test_email)
        
        if not existing_user:
            # Insert test user
            await conn.execute('''
                INSERT INTO auth_users (email, password_hash, roles, is_verified, is_active)
                VALUES ($1, $2, $3, $4, $5)
            ''', test_email, password_hash, json.dumps(["admin", "user"]), True, True)
            print(f"✅ Created test user: {test_email}")
        else:
            print(f"✅ Test user already exists: {test_email}")
        
        # Close connection
        await conn.close()
        print("✅ Database initialization complete!")
        print(f"\nYou can now login with:")
        print(f"  Email: {test_email}")
        print(f"  Password: {test_password}")
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(init_database())
    if not success:
        exit(1)