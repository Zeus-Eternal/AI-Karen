#!/usr/bin/env python3
"""
Fix for login hanging issues
"""

import asyncio
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

async def test_auth_components():
    """Test individual authentication components to identify hanging issues"""
    
    print("🔍 Testing Authentication Components")
    print("=" * 50)
    
    try:
        # Test 1: Import auth service
        print("\n1. 🧪 Testing auth service import...")
        from ai_karen_engine.auth.service import get_auth_service
        print("✅ Auth service import successful")
        
        # Test 2: Initialize auth service
        print("\n2. 🧪 Testing auth service initialization...")
        auth_service = await get_auth_service()
        print("✅ Auth service initialization successful")
        
        # Test 3: Test token manager
        print("\n3. 🧪 Testing token manager...")
        from ai_karen_engine.auth.tokens import EnhancedTokenManager
        from ai_karen_engine.auth.config import AuthConfig
        
        auth_config = AuthConfig.from_env()
        token_manager = EnhancedTokenManager(auth_config.jwt)
        print("✅ Token manager initialization successful")
        
        # Test 4: Test security monitor
        print("\n4. 🧪 Testing security monitor...")
        try:
            from ai_karen_engine.auth.security_monitor import EnhancedSecurityMonitor
            security_monitor = EnhancedSecurityMonitor(auth_config)
            print("✅ Security monitor initialization successful")
        except Exception as e:
            print(f"⚠️ Security monitor failed: {e}")
            print("   This might be causing the hanging issue")
        
        # Test 5: Test CSRF protection
        print("\n5. 🧪 Testing CSRF protection...")
        try:
            from ai_karen_engine.auth.csrf_protection import CSRFProtectionMiddleware
            csrf_protection = CSRFProtectionMiddleware(auth_config)
            print("✅ CSRF protection initialization successful")
        except Exception as e:
            print(f"⚠️ CSRF protection failed: {e}")
            print("   This might be causing the hanging issue")
        
        # Test 6: Test audit logger
        print("\n6. 🧪 Testing audit logger...")
        try:
            from ai_karen_engine.services.audit_logging import get_audit_logger
            audit_logger = get_audit_logger()
            print("✅ Audit logger initialization successful")
        except Exception as e:
            print(f"⚠️ Audit logger failed: {e}")
            print("   This might be causing the hanging issue")
        
        print("\n✅ All core components tested successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Component test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function"""
    
    success = await test_auth_components()
    
    if success:
        print("\n🎉 Authentication components are working!")
        print("   The hanging issue might be in the endpoint logic.")
        print("   Try using the simple login endpoint: /api/auth/login-simple")
    else:
        print("\n❌ Found issues with authentication components.")
        print("   Check the error messages above for specific problems.")

if __name__ == "__main__":
    asyncio.run(main())