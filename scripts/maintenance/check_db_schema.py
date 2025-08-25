#!/usr/bin/env python3
"""
Check Database Schema
Inspect the current database schema to understand the table structure.
"""

import asyncio
import asyncpg
import os

async def check_schema():
    """Check the current database schema."""
    print("🔍 Checking database schema...")
    
    # Database connection details from environment
    db_config = {
        'host': os.getenv('POSTGRES_HOST', 'localhost'),
        'port': int(os.getenv('POSTGRES_PORT', '5432')),
        'user': os.getenv('POSTGRES_USER', 'karen_user'),
        'password': os.getenv('POSTGRES_PASSWORD', 'karen_secure_pass_change_me'),
        'database': os.getenv('POSTGRES_DB', 'ai_karen')
    }
    
    try:
        print(f"   📡 Connecting to database at {db_config['host']}:{db_config['port']}")
        conn = await asyncpg.connect(**db_config)
        
        # List all tables
        tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name
        """)
        
        print(f"\n📋 Found {len(tables)} tables:")
        for table in tables:
            print(f"   • {table['table_name']}")
        
        # Check auth-related tables specifically
        auth_tables = [t['table_name'] for t in tables if 'auth' in t['table_name'].lower()]
        
        if auth_tables:
            print(f"\n🔐 Auth-related tables:")
            for table_name in auth_tables:
                print(f"\n   📊 Table: {table_name}")
                columns = await conn.fetch("""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns 
                    WHERE table_name = $1 AND table_schema = 'public'
                    ORDER BY ordinal_position
                """, table_name)
                
                for col in columns:
                    nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                    default = f" DEFAULT {col['column_default']}" if col['column_default'] else ""
                    print(f"      - {col['column_name']}: {col['data_type']} {nullable}{default}")
        
        # Check if there are any existing users
        if 'auth_users' in [t['table_name'] for t in tables]:
            users = await conn.fetch("SELECT email, roles, is_active FROM auth_users LIMIT 5")
            print(f"\n👥 Existing users ({len(users)}):")
            for user in users:
                print(f"   • {user['email']} - Roles: {user['roles']} - Active: {user['is_active']}")
        
        await conn.close()
        return True
        
    except Exception as e:
        print(f"   ❌ Failed to check schema: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(check_schema())