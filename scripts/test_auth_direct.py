#!/usr/bin/env python3
"""
Test auth service directly to isolate the issue
"""

import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

# Set minimal environment variables to avoid initialization errors
os.environ.setdefault('KARI_DUCKDB_PASSWORD', 'test')
os.environ.setdefault('KARI_JOB_ENC_KEY', 'test-key-for-development-only-32chars')

async def test_auth_direct():
    """Test the auth service directly"""
    
    try:
        from ai_karen_engine.auth.database import AuthDatabaseClient
        from ai_karen_engine.auth.config import AuthConfig
        
        print("Creating auth config...")
        config = AuthConfig()
        
        print("Creating database client...")
        db_client = AuthDatabaseClient(config.database)
        
        print("Testing get_user_by_email...")
        user_data = await db_client.get_user_by_email("admin@ai-karen.local")
        
        if user_data:
            print("✅ User found!")
            print(f"  User ID: {user_data.user_id} ({type(user_data.user_id)})")
            print(f"  Email: {user_data.email}")
            print(f"  Roles: {user_data.roles}")
            print(f"  Tenant ID: {user_data.tenant_id} ({type(user_data.tenant_id)})")
            print(f"  Preferences: {user_data.preferences}")
        else:
            print("❌ User not found")
            
        await db_client.close()
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_auth_direct())
    if success:
        print("\n🎉 Direct auth test successful!")
    else:
        print("\n💥 Direct auth test failed.")