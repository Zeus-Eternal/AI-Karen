#!/usr/bin/env python3

import os
import sys
import asyncio
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

async def check_password_hash():
    """Check if password hash exists in auth system (PostgreSQL)"""
    try:
        # Connect to the PostgreSQL auth database
        from src.ai_karen_engine.auth.config import AuthConfig
        from src.ai_karen_engine.auth.database import AuthDatabaseClient
        
        config = AuthConfig.from_env()
        db_client = AuthDatabaseClient(config.database)
        await db_client.initialize_schema()
        
        async with db_client.session_factory() as session:
            from sqlalchemy import text
            
            # Check if auth_password_hashes table exists
            result = await session.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'auth_password_hashes'
                )
            """))
            table_exists = result.scalar()
            
            if not table_exists:
                print("❌ auth_password_hashes table does not exist")
                return False
            
            print("✅ auth_password_hashes table exists")
            
            # Check if our test user has a password hash
            result = await session.execute(text("""
                SELECT h.user_id, h.password_hash 
                FROM auth_password_hashes h
                JOIN auth_users u ON h.user_id = u.user_id
                WHERE u.email = :email
            """), {"email": "test@example.com"})
            row = result.fetchone()
            
            if row:
                print(f"✅ Password hash found for test user")
                print(f"User ID: {row.user_id}")
                print(f"Password hash: {row.password_hash}")
                return True
            else:
                print("❌ No password hash found for test user")
                
                # Check if user exists in auth_users table
                user_result = await session.execute(text("""
                    SELECT user_id, email FROM auth_users WHERE email = :email
                """), {"email": "test@example.com"})
                user_row = user_result.fetchone()
                
                if user_row:
                    print(f"✅ User exists in auth_users: {user_row.user_id}")
                else:
                    print("❌ User does not exist in auth_users table")
                
                return False
        
        await db_client.close()
        
    except Exception as e:
        print(f"❌ Error checking password hash: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(check_password_hash())