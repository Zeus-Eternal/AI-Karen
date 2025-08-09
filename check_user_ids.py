#!/usr/bin/env python3

import os
import sys
import asyncio
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from ai_karen_engine.database.client import get_db_session_context
from ai_karen_engine.database.models import AuthUser

async def check_user_ids():
    """Check user IDs in both databases (now both using PostgreSQL)"""
    try:
        # Check main database
        print("=== Main Database (PostgreSQL/SQLAlchemy) ===")
        with get_db_session_context() as session:
            user = session.query(AuthUser).filter(AuthUser.email == "test@example.com").first()
            if user:
                print(f"User ID: {user.user_id}")
                print(f"Email: {user.email}")
                print(f"Password hash: {user.password_hash}")
            else:
                print("User not found in main database")
        
        print("\n=== Auth Database (PostgreSQL - Consolidated) ===")
        # Check consolidated auth database
        from src.ai_karen_engine.auth.config import AuthConfig
        from src.ai_karen_engine.auth.database import AuthDatabaseClient
        
        config = AuthConfig.from_env()
        db_client = AuthDatabaseClient(config.database)
        await db_client.initialize_schema()
        
        async with db_client.session_factory() as session:
            from sqlalchemy import text
            
            # Get user from auth_users table
            result = await session.execute(text("""
                SELECT user_id, email FROM auth_users WHERE email = :email
            """), {"email": "test@example.com"})
            auth_user = result.fetchone()
            
            if auth_user:
                print(f"User ID: {auth_user.user_id}")
                print(f"Email: {auth_user.email}")
                
                # Get password hash
                hash_result = await session.execute(text("""
                    SELECT password_hash FROM auth_password_hashes WHERE user_id = :user_id
                """), {"user_id": str(auth_user.user_id)})
                hash_row = hash_result.fetchone()
                
                if hash_row:
                    print(f"Password hash: {hash_row.password_hash}")
                else:
                    print("No password hash found")
            else:
                print("User not found in auth database")
        
        await db_client.close()
        
    except Exception as e:
        print(f"❌ Error checking user IDs: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_user_ids())