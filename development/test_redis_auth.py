#!/usr/bin/env python3
"""
Test script to verify Redis session management in EnhancedAuthService
"""

import asyncio
import os
import sys
from datetime import datetime, timezone

# Set required environment variables before any imports
os.environ["KARI_DUCKDB_PASSWORD"] = "dev-duckdb-pass"
os.environ["KARI_JOB_ENC_KEY"] = "MaL42789OGRr0--UUf_RV_kanWzb2tSCd6hU6R-sOZo="
os.environ["KARI_JOB_SIGNING_KEY"] = "dev-job-key-456"

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ai_karen_engine.auth.enhanced_auth_service import EnhancedAuthService

async def test_redis_auth():
    """Test Redis session management functionality"""
    print("🧪 Testing EnhancedAuthService with Redis session management...")
    
    # Set required environment variables
    os.environ["KARI_DUCKDB_PASSWORD"] = "dev-duckdb-pass"
    os.environ["KARI_JOB_ENC_KEY"] = "MaL42789OGRr0--UUf_RV_kanWzb2tSCd6hU6R-sOZo="
    
    # Set Redis URL for testing (use default if not set)
    redis_url = os.getenv("REDIS_URL", "redis://:karen-redis-pass-change-me@localhost:6380/0")
    os.environ["REDIS_URL"] = redis_url
    print(f"📝 Using Redis URL: {redis_url}")
    
    # Create auth service instance
    auth_service = EnhancedAuthService()
    
    # Test authentication
    print("\n1. 🔐 Testing user authentication...")
    try:
        user = await auth_service.authenticate_user(
            email="admin@kari.ai",
            password="password123",
            ip_address="127.0.0.1",
            user_agent="test-agent"
        )
        
        if user:
            print("✅ Authentication successful!")
            print(f"   User: {user['email']}")
            print(f"   Roles: {user['roles']}")
        else:
            print("❌ Authentication failed")
            return False
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return False
    
    # Test session creation
    print("\n2. 🎫 Testing session creation...")
    try:
        session = await auth_service.create_session(
            user_data=user,
            ip_address="127.0.0.1",
            user_agent="test-agent"
        )
        
        if session:
            print("✅ Session creation successful!")
            print(f"   Session ID: {session['session_id']}")
            print(f"   Expires at: {session['expires_at']}")
        else:
            print("❌ Session creation failed")
            return False
    except Exception as e:
        print(f"❌ Session creation error: {e}")
        return False
    
    # Test session validation
    print("\n3. ✅ Testing session validation...")
    try:
        session_id = session['session_id']
        validated_user = await auth_service.validate_session(
            session_id=session_id,
            ip_address="127.0.0.1",
            user_agent="test-agent"
        )
        
        if validated_user:
            print("✅ Session validation successful!")
            print(f"   Validated user: {validated_user['email']}")
        else:
            print("❌ Session validation failed")
            return False
    except Exception as e:
        print(f"❌ Session validation error: {e}")
        return False
    
    # Test session invalidation
    print("\n4. 🗑️ Testing session invalidation...")
    try:
        await auth_service.invalidate_session(session_id)
        print("✅ Session invalidation successful!")
        
        # Verify session is actually invalidated
        invalid_session = await auth_service.validate_session(
            session_id=session_id,
            ip_address="127.0.0.1",
            user_agent="test-agent"
        )
        
        if not invalid_session:
            print("✅ Session properly invalidated (no longer valid)")
        else:
            print("❌ Session still valid after invalidation")
            return False
    except Exception as e:
        print(f"❌ Session invalidation error: {e}")
        return False
    
    print("\n🎉 All tests passed! Redis session management is working correctly.")
    return True

async def test_redis_fallback():
    """Test that the service falls back to in-memory when Redis is unavailable"""
    print("\n🧪 Testing fallback to in-memory session storage...")
    
    # Set invalid Redis URL to trigger fallback
    os.environ["REDIS_URL"] = "redis://invalid-host:6379/0"
    
    # Create new auth service instance
    auth_service = EnhancedAuthService()
    
    try:
        # Test authentication
        user = await auth_service.authenticate_user(
            email="admin@kari.ai",
            password="password123",
            ip_address="127.0.0.1",
            user_agent="test-agent"
        )
        
        if user:
            print("✅ Authentication successful with fallback!")
            
            # Test session creation with fallback
            session = await auth_service.create_session(
                user_data=user,
                ip_address="127.0.0.1",
                user_agent="test-agent"
            )
            
            if session:
                print("✅ Session creation successful with fallback!")
                return True
            else:
                print("❌ Session creation failed with fallback")
                return False
        else:
            print("❌ Authentication failed with fallback")
            return False
            
    except Exception as e:
        print(f"❌ Fallback test error: {e}")
        return False

async def main():
    """Run all tests"""
    print("=" * 60)
    print("🧪 AI Karen Authentication System Test")
    print("=" * 60)
    
    # Test 1: Redis session management
    success1 = await test_redis_auth()
    
    # Test 2: Fallback to in-memory
    success2 = await test_redis_fallback()
    
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS:")
    print(f"   Redis Session Management: {'✅ PASS' if success1 else '❌ FAIL'}")
    print(f"   Fallback to In-Memory:    {'✅ PASS' if success2 else '❌ FAIL'}")
    
    if success1 and success2:
        print("\n🎉 ALL TESTS PASSED! Redis integration is working correctly.")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED! Check the implementation.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)