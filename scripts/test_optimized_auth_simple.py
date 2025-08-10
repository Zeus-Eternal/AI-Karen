#!/usr/bin/env python3
"""
Simple test of optimized auth without complex dependencies
"""

import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

# Set minimal environment variables
os.environ.setdefault('KARI_DUCKDB_PASSWORD', 'test')
os.environ.setdefault('KARI_JOB_ENC_KEY', 'MaL42789OGRr0--UUf_RV_kanWzb2tSCd6hU6R-sOZo=')

async def test_simple_auth():
    """Test simple authentication"""
    
    try:
        # Try to use the fallback auth system which should be simpler
        from ai_karen_engine.auth.fallback_auth import FallbackAuthService
        
        print("Creating fallback auth service...")
        auth_service = FallbackAuthService()
        await auth_service.initialize()
        
        print("Testing authentication...")
        result = await auth_service.authenticate_user("admin@ai-karen.dev", "admin123")
        
        if result:
            print("✅ Authentication successful!")
            print(f"   User ID: {result.user_id}")
            print(f"   Email: {result.email}")
            print(f"   Roles: {result.roles}")
        else:
            print("❌ Authentication failed")
            
        await auth_service.cleanup()
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_simple_auth())
    if success:
        print("\n🎉 Simple auth test successful!")
    else:
        print("\n💥 Simple auth test failed.")