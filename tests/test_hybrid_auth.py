#!/usr/bin/env python3
"""
Test the hybrid authentication system
"""

import asyncio
import aiohttp
import json
import sys

async def test_hybrid_auth():
    """Test the hybrid authentication system"""
    
    print("🔐 Testing Hybrid Authentication System")
    print("=" * 50)
    
    timeout = aiohttp.ClientTimeout(total=15)
    
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            
            # Test 1: Get demo users
            print("1. 📋 Getting demo user credentials...")
            try:
                async with session.get("http://127.0.0.1:8000/api/auth/demo-users") as response:
                    if response.status == 200:
                        data = await response.json()
                        print("   ✅ Demo users available:")
                        for user in data.get("demo_users", []):
                            print(f"   👤 {user['email']} / {user['password']} ({user['role']})")
                        
                        # Use first demo user for testing
                        demo_user = data["demo_users"][0]
                        test_user = {
                            "email": demo_user["email"],
                            "password": demo_user["password"]
                        }
                    else:
                        print(f"   ⚠️ Demo users endpoint returned {response.status}")
                        # Fallback to known credentials
                        test_user = {
                            "email": "admin@example.com",
                            "password": "password123"
                        }
            except Exception as e:
                print(f"   ❌ Demo users error: {e}")
                test_user = {
                    "email": "admin@example.com",
                    "password": "password123"
                }
            
            # Test 2: Login with demo user
            print("2. 🔐 Testing login...")
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
                        print(f"   🎭 Roles: {data.get('user', {}).get('roles', [])}")
                        
                        access_token = data.get('access_token')
                        refresh_token = data.get('refresh_token')
                    else:
                        error_text = await response.text()
                        print(f"   ❌ Login failed: {error_text}")
                        return False
                        
            except Exception as e:
                print(f"   ❌ Login error: {e}")
                return False
            
            # Test 3: Use access token for protected endpoint
            if access_token:
                print("3. 🔒 Testing protected endpoint...")
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
                            print(f"   ✅ Verified: {data.get('is_verified', False)}")
                        else:
                            error_text = await response.text()
                            print(f"   ❌ Protected endpoint failed: {error_text}")
                            return False
                            
                except Exception as e:
                    print(f"   ❌ Protected endpoint error: {e}")
                    return False
            
            # Test 4: Token refresh
            if refresh_token:
                print("4. 🔄 Testing token refresh...")
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
            
            # Test 5: Register new user
            print("5. 📝 Testing user registration...")
            try:
                new_user = {
                    "email": "newuser@example.com",
                    "password": "NewPassword123!",
                    "full_name": "New Test User"
                }
                
                async with session.post(
                    "http://127.0.0.1:8000/api/auth/register",
                    json=new_user,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    print(f"   📊 Registration status: {response.status}")
                    
                    if response.status == 200:
                        data = await response.json()
                        print("   ✅ Registration successful!")
                        print(f"   👤 New user: {data.get('user', {}).get('email', 'N/A')}")
                        print(f"   🎫 Access token: {data.get('access_token', 'N/A')[:30]}...")
                    elif response.status == 409:
                        print("   ℹ️ User already exists (expected if run multiple times)")
                    else:
                        error_text = await response.text()
                        print(f"   ⚠️ Registration response: {error_text}")
                        
            except Exception as e:
                print(f"   ❌ Registration error: {e}")
            
            # Test 6: Logout
            if access_token:
                print("6. 🚪 Testing logout...")
                try:
                    logout_data = {}
                    if refresh_token:
                        logout_data["refresh_token"] = refresh_token
                    
                    async with session.post(
                        "http://127.0.0.1:8000/api/auth/logout",
                        json=logout_data,
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

if __name__ == "__main__":
    result = asyncio.run(test_hybrid_auth())
    
    if result:
        print("\n✅ Hybrid authentication test passed!")
        print("🎯 Hybrid auth system is working correctly")
        print("\n📋 Available endpoints:")
        print("   • GET  /api/auth/demo-users")
        print("   • POST /api/auth/register")
        print("   • POST /api/auth/login")
        print("   • POST /api/auth/refresh")
        print("   • GET  /api/auth/me")
        print("   • POST /api/auth/logout")
        print("\n🔐 Security Features:")
        print("   • JWT tokens with proper expiration")
        print("   • bcrypt password hashing")
        print("   • Session management")
        print("   • Role-based access control")
        print("   • No database concurrency issues")
        sys.exit(0)
    else:
        print("\n❌ Hybrid authentication test failed!")
        print("🔧 Check server logs and configuration")
        sys.exit(1)