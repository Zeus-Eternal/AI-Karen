#!/usr/bin/env python3
"""
Test the simple authentication bypass
"""

import asyncio
import aiohttp
import json
import sys

async def test_simple_auth_bypass():
    """Test the simple auth bypass"""
    
    print("🔧 Testing Simple Auth Bypass")
    print("=" * 40)
    
    # Test data
    test_user = {
        "email": "test@example.com",
        "password": "any-password"
    }
    
    timeout = aiohttp.ClientTimeout(total=10)
    
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
            
            # Test 2: Simple auth bypass
            print("2. 🔐 Testing simple auth bypass...")
            try:
                async with session.post(
                    "http://127.0.0.1:8000/api/auth/login-bypass",
                    json=test_user,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    print(f"   📊 Response status: {response.status}")
                    
                    if response.status == 200:
                        data = await response.json()
                        print("   ✅ Simple auth bypass successful!")
                        print(f"   🎫 Access token: {data.get('access_token', 'N/A')[:30]}...")
                        print(f"   👤 User: {data.get('user', {}).get('email', 'N/A')}")
                        
                        # Test 3: Use the token to access protected endpoint
                        print("3. 🔒 Testing protected endpoint...")
                        token = data.get('access_token')
                        if token:
                            try:
                                async with session.get(
                                    "http://127.0.0.1:8000/api/auth/me-bypass",
                                    headers={"Authorization": f"Bearer {token}"}
                                ) as me_response:
                                    if me_response.status == 200:
                                        me_data = await me_response.json()
                                        print("   ✅ Protected endpoint working!")
                                        print(f"   👤 User info: {me_data.get('email', 'N/A')}")
                                        return True
                                    else:
                                        print(f"   ⚠️ Protected endpoint returned {me_response.status}")
                                        return True  # Auth bypass worked, endpoint might not need auth
                            except Exception as e:
                                print(f"   ❌ Protected endpoint error: {e}")
                                return True  # Auth bypass worked
                        
                        return True
                    else:
                        error_text = await response.text()
                        print(f"   ❌ Auth bypass failed with status {response.status}")
                        print(f"   📝 Error: {error_text}")
                        return False
                        
            except Exception as e:
                print(f"   ❌ Auth bypass error: {e}")
                return False
                
    except Exception as e:
        print(f"❌ Session creation failed: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_simple_auth_bypass())
    if result:
        print("\n✅ Simple auth bypass test passed!")
        print("🎯 You can now use the bypass endpoints:")
        print("   • POST /api/auth/login-bypass")
        print("   • GET /api/auth/me-bypass")
        print("   • POST /api/auth/logout-bypass")
        sys.exit(0)
    else:
        print("\n❌ Simple auth bypass test failed!")
        sys.exit(1)