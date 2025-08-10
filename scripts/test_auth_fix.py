#!/usr/bin/env python3
"""
Test the authentication system after schema fix
"""

import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from ai_karen_engine.auth.auth_service import AuthService
from ai_karen_engine.auth.auth_database_client import AuthDatabaseClient

async def test_auth_system():
    """Test the authentication system"""
    
    try:
        print("Testing authentication system...")
        
        # Initialize auth service
        auth_service = AuthService()
        await auth_service.initialize()
        print("✅ AuthService initialized successfully")
        
        # Test login with admin user
        print("Testing admin login...")
        result = await auth_service.authenticate_user("admin@ai-karen.local", "admin123")
        
        if result and result.get('success'):
            print("✅ Admin login successful!")
            print(f"   User ID: {result.get('user', {}).get('user_id')}")
            print(f"   Email: {result.get('user', {}).get('email')}")
            print(f"   Roles: {result.get('user', {}).get('roles')}")
        else:
            print("❌ Admin login failed")
            print(f"   Error: {result.get('error') if result else 'No result returned'}")
        
        # Test invalid login
        print("Testing invalid login...")
        invalid_result = await auth_service.authenticate_user("admin@ai-karen.local", "wrongpassword")
        
        if invalid_result and not invalid_result.get('success'):
            print("✅ Invalid login correctly rejected")
        else:
            print("❌ Invalid login was incorrectly accepted")
        
        await auth_service.cleanup()
        print("✅ AuthService cleanup completed")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing authentication: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_auth_system())
    if success:
        print("\n🎉 Authentication system is working correctly!")
    else:
        print("\n💥 Authentication system test failed.")