#!/usr/bin/env python3
"""
Test Production Authentication System
Tests the production database authentication implementation
"""

import asyncio
import sys
import os
import requests
import json
from datetime import datetime

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ai_karen_engine.security.auth_service import AuthService
from ai_karen_engine.security.config import AuthConfig, FeatureToggles

auth_service = AuthService(AuthConfig(features=FeatureToggles(use_database=True)))
from ai_karen_engine.database.client import create_database_tables, check_database_health
from ai_karen_engine.core.logging import get_logger

logger = get_logger(__name__)


async def test_user_creation():
    """Test user creation with production auth service"""
    print("🧪 Testing user creation...")
    
    try:
        # Create test user
        test_user = await auth_service.create_user(
            email="test@karen.ai",
            password="test123",
            full_name="Test User",
            roles=["user"],
            tenant_id="default"
        )
        
        print(f"✅ User created successfully: {test_user.email}")
        return test_user
        
    except ValueError as e:
        if "User already exists" in str(e):
            print("ℹ️  Test user already exists")
            return None
        else:
            print(f"❌ User creation failed: {e}")
            return None
    except Exception as e:
        print(f"❌ User creation failed: {e}")
        return None


async def test_user_authentication():
    """Test user authentication"""
    print("🧪 Testing user authentication...")
    
    try:
        # Test valid credentials
        user_data = await auth_service.authenticate_user(
            email="test@karen.ai",
            password="test123",
            ip_address="127.0.0.1",
            user_agent="test-client"
        )
        
        if user_data:
            print(f"✅ Authentication successful: {user_data['email']}")
            return user_data
        else:
            print("❌ Authentication failed with valid credentials")
            return None
            
    except Exception as e:
        print(f"❌ Authentication test failed: {e}")
        return None


async def test_session_management():
    """Test session creation and validation"""
    print("🧪 Testing session management...")
    
    try:
        # First authenticate to get user ID
        user_data = await auth_service.authenticate_user(
            email="test@karen.ai",
            password="test123",
            ip_address="127.0.0.1",
            user_agent="test-client"
        )
        
        if not user_data:
            print("❌ Cannot test sessions - authentication failed")
            return None
        
        # Create session
        session_data = await auth_service.create_session(
            user_id=user_data["user_id"],
            ip_address="127.0.0.1",
            user_agent="test-client"
        )
        
        print(f"✅ Session created: {session_data['token_type']}")
        
        # Validate session using JWT token
        validated_user = await auth_service.validate_session(
            session_token=session_data["access_token"],
            ip_address="127.0.0.1",
            user_agent="test-client"
        )
        
        if validated_user:
            print(f"✅ Session validation successful: {validated_user['email']}")
        else:
            print("❌ Session validation failed")
            
        return session_data
        
    except Exception as e:
        print(f"❌ Session management test failed: {e}")
        return None


async def test_password_reset():
    """Test password reset functionality"""
    print("🧪 Testing password reset...")
    
    try:
        # Create password reset token
        reset_token = await auth_service.create_password_reset_token(
            email="test@karen.ai",
            ip_address="127.0.0.1",
            user_agent="test-client"
        )
        
        if reset_token:
            print(f"✅ Password reset token created")
            
            # Test password reset
            success = await auth_service.verify_password_reset_token(
                token=reset_token,
                new_password="newtest123"
            )
            
            if success:
                print("✅ Password reset successful")
                
                # Test login with new password
                user_data = await auth_service.authenticate_user(
                    email="test@karen.ai",
                    password="newtest123",
                    ip_address="127.0.0.1",
                    user_agent="test-client"
                )
                
                if user_data:
                    print("✅ Login with new password successful")
                    
                    # Reset password back for other tests
                    await auth_service.update_password(
                        user_id=user_data["user_id"],
                        new_password="test123"
                    )
                    print("✅ Password reset back to original")
                    
                else:
                    print("❌ Login with new password failed")
            else:
                print("❌ Password reset failed")
        else:
            print("❌ Password reset token creation failed")
            
    except Exception as e:
        print(f"❌ Password reset test failed: {e}")


def test_api_endpoints():
    """Test API endpoints with production authentication"""
    print("🧪 Testing API endpoints...")
    
    base_url = "http://localhost:8000"
    
    try:
        # Test registration
        print("Testing registration endpoint...")
        register_data = {
            "email": "api_test@karen.ai",
            "password": "apitest123",
            "full_name": "API Test User",
            "tenant_id": "default"
        }
        
        response = requests.post(
            f"{base_url}/api/auth/register",
            json=register_data,
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ Registration endpoint working")
            register_result = response.json()
        elif response.status_code == 400 and "already exists" in response.text:
            print("ℹ️  User already exists, testing login...")
        else:
            print(f"❌ Registration failed: {response.status_code} - {response.text}")
            return
        
        # Test login
        print("Testing login endpoint...")
        login_data = {
            "email": "api_test@karen.ai",
            "password": "apitest123"
        }
        
        response = requests.post(
            f"{base_url}/api/auth/login",
            json=login_data,
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ Login endpoint working")
            login_result = response.json()
            access_token = login_result["access_token"]
            
            # Test /me endpoint
            print("Testing /me endpoint...")
            headers = {"Authorization": f"Bearer {access_token}"}
            
            response = requests.get(
                f"{base_url}/api/auth/me",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                print("✅ /me endpoint working")
                me_result = response.json()
                print(f"   User: {me_result['email']}")
            else:
                print(f"❌ /me endpoint failed: {response.status_code}")
                
        else:
            print(f"❌ Login failed: {response.status_code} - {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("⚠️  Cannot connect to API server. Make sure the server is running on localhost:8000")
    except Exception as e:
        print(f"❌ API endpoint test failed: {e}")


async def main():
    """Main test function"""
    print("🚀 Testing AI Karen Production Authentication System")
    print("=" * 60)
    
    # Check database health
    print("1. Checking database connection...")
    if not check_database_health():
        print("❌ Database connection failed. Please check your DATABASE_URL configuration.")
        sys.exit(1)
    print("✅ Database connection successful")
    
    # Ensure tables exist
    print("2. Ensuring database tables exist...")
    try:
        create_database_tables()
        print("✅ Database tables ready")
    except Exception as e:
        print(f"❌ Failed to create tables: {e}")
        sys.exit(1)
    
    # Test user creation
    print("3. Testing user creation...")
    await test_user_creation()
    
    # Test authentication
    print("4. Testing authentication...")
    await test_user_authentication()
    
    # Test session management
    print("5. Testing session management...")
    await test_session_management()
    
    # Test password reset
    print("6. Testing password reset...")
    await test_password_reset()
    
    # Test API endpoints
    print("7. Testing API endpoints...")
    test_api_endpoints()
    
    print("\n🎉 Production authentication testing complete!")
    print("\n📋 Next steps:")
    print("1. Start the server: python main.py")
    print("2. Test the web UI authentication")
    print("3. Verify Redis session storage is working")
    print("4. Test with different user agents and IP addresses")


if __name__ == "__main__":
    asyncio.run(main())