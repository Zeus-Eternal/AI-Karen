#!/usr/bin/env python3
"""
Check Database Schema
Shows existing tables and their structure
"""

import sys
import os
import psycopg2

def get_database_url():
    """Get database URL from environment"""
    database_url = (
        os.getenv("DATABASE_URL") or
        os.getenv("POSTGRES_URL") or
        os.getenv("DB_URL")
    )
    
    if not database_url:
        # Try to construct from individual components
        host = os.getenv("POSTGRES_HOST", "localhost")
        port = os.getenv("POSTGRES_PORT", "5432")
        db = os.getenv("POSTGRES_DB", "ai_karen")
        user = os.getenv("POSTGRES_USER", "karen_user")
        password = os.getenv("POSTGRES_PASSWORD", "karen_secure_pass_change_me")
        
        database_url = f"postgresql://{user}:{password}@{host}:{port}/{db}"
    
    return database_url

def check_schema():
    """Check database schema"""
    database_url = get_database_url()
    
    if not database_url:
        print("❌ Database URL not provided")
        sys.exit(1)
    
    print(f"🔗 Using database: {database_url.split('@')[1] if '@' in database_url else database_url}")
    
    try:
        with psycopg2.connect(database_url) as conn:
            with conn.cursor() as cur:
                # List all tables
                cur.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                    ORDER BY table_name
                """)
                
                tables = cur.fetchall()
                
                print(f"\n📋 Found {len(tables)} tables:")
                for table in tables:
                    print(f"  - {table[0]}")
                
                # Check if users table exists and its structure
                cur.execute("""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_name = 'users'
                    ORDER BY ordinal_position
                """)
                
                user_columns = cur.fetchall()
                
                if user_columns:
                    print(f"\n👤 Users table structure:")
                    for col in user_columns:
                        nullable = "NULL" if col[2] == "YES" else "NOT NULL"
                        print(f"  - {col[0]}: {col[1]} {nullable}")
                else:
                    print("\n👤 Users table does not exist")
                
                # Check if user_sessions table exists
                cur.execute("""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_name = 'user_sessions'
                    ORDER BY ordinal_position
                """)
                
                session_columns = cur.fetchall()
                
                if session_columns:
                    print(f"\n🔐 User sessions table structure:")
                    for col in session_columns:
                        nullable = "NULL" if col[2] == "YES" else "NOT NULL"
                        print(f"  - {col[0]}: {col[1]} {nullable}")
                else:
                    print("\n🔐 User sessions table does not exist")
                
    except Exception as e:
        print(f"❌ Failed to check schema: {e}")
        sys.exit(1)

if __name__ == "__main__":
    check_schema()