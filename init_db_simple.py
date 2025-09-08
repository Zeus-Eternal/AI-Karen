#!/usr/bin/env python3
"""
Simple database initialization script (PostgreSQL)

Creates/updates consolidated auth tables and ensures an admin user exists.
Matches the current backend schema:
- auth_users (no password hash here)
- auth_password_hashes (stores password)
- auth_sessions (session_token PK)

Admin account created/ensured:
- Email: admin@kari.ai (override with ADMIN_EMAIL)
- Password: ChangeMeNow_123! (override with ADMIN_PASSWORD)
"""

import asyncio
import asyncpg
import bcrypt
import json
import os
import uuid
from datetime import datetime

async def init_database():
    """Initialize the database with tables and an admin user."""

    # Database connection parameters (env with sensible defaults)
    DB_CONFIG = {
        'host': os.getenv('POSTGRES_HOST', os.getenv('PGHOST', 'localhost')),
        'port': int(os.getenv('POSTGRES_PORT', os.getenv('PGPORT', '5432'))),
        'user': os.getenv('POSTGRES_USER', os.getenv('PGUSER', 'karen_user')),
        'password': os.getenv('POSTGRES_PASSWORD', os.getenv('PGPASSWORD', 'karen_secure_pass_change_me')),
        'database': os.getenv('POSTGRES_DB', os.getenv('PGDATABASE', 'ai_karen')),
    }
    
    try:
        # Connect to PostgreSQL
        conn = await asyncpg.connect(**DB_CONFIG)
        print("✅ Connected to PostgreSQL")
        
        # Enable pgcrypto (for gen_random_uuid) best-effort
        try:
            await conn.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
        except Exception:
            pass

        # auth_users table (consolidated schema)
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS auth_users (
                user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                email VARCHAR(255) UNIQUE NOT NULL,
                full_name VARCHAR(255),
                roles JSONB DEFAULT '[]'::jsonb,
                tenant_id UUID NOT NULL,
                preferences JSONB DEFAULT '{}'::jsonb,
                is_verified BOOLEAN DEFAULT FALSE,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                last_login_at TIMESTAMP WITH TIME ZONE,
                failed_login_attempts INTEGER DEFAULT 0,
                locked_until TIMESTAMP WITH TIME ZONE,
                two_factor_enabled BOOLEAN DEFAULT FALSE,
                two_factor_secret VARCHAR(255)
            )
        ''')
        print("✅ Ensured auth_users table")

        # auth_password_hashes table
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS auth_password_hashes (
                user_id UUID PRIMARY KEY REFERENCES auth_users(user_id) ON DELETE CASCADE,
                password_hash VARCHAR(255) NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        ''')
        print("✅ Ensured auth_password_hashes table")
        
        # auth_sessions table (session_token PK)
        await conn.execute('''
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
                is_active BOOLEAN DEFAULT TRUE,
                invalidated_at TIMESTAMP WITH TIME ZONE,
                invalidation_reason VARCHAR(255)
            )
        ''')
        print("✅ Ensured auth_sessions table")

        # Minimum useful indexes
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_auth_users_email ON auth_users(email)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_auth_users_tenant ON auth_users(tenant_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_auth_sessions_user ON auth_sessions(user_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_auth_sessions_active ON auth_sessions(is_active) WHERE is_active = true")
        
        # Ensure admin user
        admin_email = os.getenv("ADMIN_EMAIL", "admin@kari.ai")
        admin_password = os.getenv("ADMIN_PASSWORD", "Password123!")
        
        # Hash the password
        password_hash = bcrypt.hashpw(admin_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Check if user already exists
        existing_user = await conn.fetchrow('SELECT user_id FROM auth_users WHERE email = $1', admin_email)
        
        if not existing_user:
            user_id = str(uuid.uuid4())
            tenant_id = str(uuid.uuid4())
            await conn.execute('''
                INSERT INTO auth_users (
                    user_id, email, full_name, roles, tenant_id, preferences,
                    is_verified, is_active, created_at, updated_at
                ) VALUES ($1,$2,$3,$4,$5,$6, $7,$8, NOW(), NOW())
            ''', user_id, admin_email, 'Administrator', json.dumps(["admin","user"]), tenant_id, json.dumps({}), True, True)
            await conn.execute('''
                INSERT INTO auth_password_hashes (user_id, password_hash)
                VALUES ($1, $2)
            ''', user_id, password_hash)
            print(f"✅ Created admin user: {admin_email}")
        else:
            print(f"✅ Admin user already exists: {admin_email}")
        
        # Close connection
        await conn.close()
        print("✅ Database initialization complete!")
        print(f"\nYou can now login with:")
        print(f"  Email: {admin_email}")
        print(f"  Password: {admin_password}")
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(init_database())
    if not success:
        exit(1)
