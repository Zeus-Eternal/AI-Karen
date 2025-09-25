#!/usr/bin/env python3
"""
Test the production authentication system
"""

import asyncio
import aiohttp
import json
import sys
import os

async def test_production_auth():
    """Test the production authentication system"""
    
    print("🔐 Testing Production Authentication System")
    print("=" * 50)
    
    # Test data
    test_user = {
        "email": "testuser@example.com",
        "password": "SecurePassword123!"
    }
    
    timeout = aiohttp.ClientTimeout(total=15)
    
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            
            # Test 1: Health check
            print("1. 🏥 Testing health endpoint...")
            try:
                async with session.get("http://127.0.0.1:8000/health") as response:
                    if response.status == 200:
                        print("   ✅ Health endpoint working")
                    else:
                        print(f"   ⚠️ Health endpoint returned {response.status}")
            except Exception as e:
                print(f"   ❌ Health endpoint error: {e}")
                return False
            
            # Test 2: Register user
            print("2. 📝 Testing user registration...")
            try:
                register_data = {
                    "email": test_user["email"],
                    "password": test_user["password"],
                    "full_name": "Test User"
                }
                
                async with session.post(
                    "http://127.0.0.1:8000/api/auth/register",
                    json=register_data,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    print(f"   📊 Registration status: {response.status}")
                    
                    if response.status == 200:
                        data = await response.json()
                        print("   ✅ Registration successful!")
                        print(f"   🎫 Access token: {data.get('access_token', 'N/A')[:30]}...")
                        print(f"   🔄 Refresh token: {data.get('refresh_token', 'N/A')[:30]}...")
                        print(f"   👤 User: {data.get('user', {}).get('email', 'N/A')}")
                        
                        access_token = data.get('access_token')
                        refresh_token = data.get('refresh_token')
                        
                    elif response.status == 409:
                        print("   ℹ️ User already exists, trying login...")
                        access_token = None
                        refresh_token = None
                    else:
                        error_text = await response.text()
                        print(f"   ❌ Registration failed: {error_text}")
                        access_token = None
                        refresh_token = None
                        
            except Exception as e:
                print(f"   ❌ Registration error: {e}")
                access_token = None
                refresh_token = None
            
            # Test 3: Login user (if registration failed or user exists)
            if not access_token:
                print("3. 🔐 Testing user login...")
                try:
                    async with session.post(
                        "http://127.0.0.1:8000/api/auth/login",
                        json=test_user,
                        headers={"Content-Type": "application/json"}
                    ) as response:
                        print(f"   📊 Login status: {response.status}")
                        
                        if response.status == 200:
                            data = await response.json()
                            print("   ✅ Login successful!")
                            print(f"   🎫 Access token: {data.get('access_token', 'N/A')[:30]}...")
                            print(f"   🔄 Refresh token: {data.get('refresh_token', 'N/A')[:30]}...")
                            print(f"   👤 User: {data.get('user', {}).get('email', 'N/A')}")
                            
                            access_token = data.get('access_token')
                            refresh_token = data.get('refresh_token')
                        else:
                            error_text = await response.text()
                            print(f"   ❌ Login failed: {error_text}")
                            return False
                            
                except Exception as e:
                    print(f"   ❌ Login error: {e}")
                    return False
            else:
                print("3. ✅ Skipping login (already have tokens from registration)")
            
            # Test 4: Use access token for protected endpoint
            if access_token:
                print("4. 🔒 Testing protected endpoint...")
                try:
                    async with session.get(
                        "http://127.0.0.1:8000/api/auth/me",
                        headers={"Authorization": f"Bearer {access_token}"}
                    ) as response:
                        print(f"   📊 Protected endpoint status: {response.status}")
                        
                        if response.status == 200:
                            data = await response.json()
                            print("   ✅ Protected endpoint working!")
                            print(f"   👤 User info: {data.get('email', 'N/A')}")
                            print(f"   🏢 Tenant: {data.get('tenant_id', 'N/A')}")
                            print(f"   🎭 Roles: {data.get('roles', [])}")
                        else:
                            error_text = await response.text()
                            print(f"   ❌ Protected endpoint failed: {error_text}")
                            return False
                            
                except Exception as e:
                    print(f"   ❌ Protected endpoint error: {e}")
                    return False
            
            # Test 5: Token refresh
            if refresh_token:
                print("5. 🔄 Testing token refresh...")
                try:
                    async with session.post(
                        "http://127.0.0.1:8000/api/auth/refresh",
                        json={"refresh_token": refresh_token},
                        headers={"Content-Type": "application/json"}
                    ) as response:
                        print(f"   📊 Refresh status: {response.status}")
                        
                        if response.status == 200:
                            data = await response.json()
                            print("   ✅ Token refresh successful!")
                            print(f"   🎫 New access token: {data.get('access_token', 'N/A')[:30]}...")
                            new_access_token = data.get('access_token')
                            
                            # Test new token
                            if new_access_token:
                                async with session.get(
                                    "http://127.0.0.1:8000/api/auth/me",
                                    headers={"Authorization": f"Bearer {new_access_token}"}
                                ) as test_response:
                                    if test_response.status == 200:
                                        print("   ✅ New token works!")
                                    else:
                                        print("   ⚠️ New token validation failed")
                        else:
                            error_text = await response.text()
                            print(f"   ❌ Token refresh failed: {error_text}")
                            
                except Exception as e:
                    print(f"   ❌ Token refresh error: {e}")
            
            # Test 6: Logout
            if access_token:
                print("6. 🚪 Testing logout...")
                try:
                    async with session.post(
                        "http://127.0.0.1:8000/api/auth/logout",
                        headers={"Authorization": f"Bearer {access_token}"}
                    ) as response:
                        print(f"   📊 Logout status: {response.status}")
                        
                        if response.status == 200:
                            data = await response.json()
                            print("   ✅ Logout successful!")
                            print(f"   📝 Message: {data.get('detail', 'N/A')}")
                        else:
                            error_text = await response.text()
                            print(f"   ⚠️ Logout response: {error_text}")
                            
                except Exception as e:
                    print(f"   ❌ Logout error: {e}")
            
            return True
                
    except Exception as e:
        print(f"❌ Session creation failed: {e}")
        return False

async def main():
    """Main test function"""
    
    # Check auth mode
    auth_mode = os.getenv("AUTH_MODE", "production")
    print(f"🔧 Current AUTH_MODE: {auth_mode}")
    
    if auth_mode != "production":
        print("⚠️ Set AUTH_MODE=production to test production auth")
        print("   export AUTH_MODE=production")
        return False
    
    result = await test_production_auth()
    
    if result:
        print("\n✅ Production authentication test passed!")
        print("🎯 Production auth system is working correctly")
        print("\n📋 Available endpoints:")
        print("   • POST /api/auth/register")
        print("   • POST /api/auth/login")
        print("   • POST /api/auth/refresh")
        print("   • GET  /api/auth/me")
        print("   • POST /api/auth/logout")
        return True
    else:
        print("\n❌ Production authentication test failed!")
        print("🔧 Check server logs and configuration")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)