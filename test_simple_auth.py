#!/usr/bin/env python3
"""
Simple Authentication Test Script
Tests the new simplified auth system.
"""

import asyncio
import aiohttp
import json

async def test_auth():
    """Test the simplified auth system"""
    print("🧪 Testing Simple Authentication System")
    print("=" * 40)
    
    base_url = "http://localhost:8000"
    
    async with aiohttp.ClientSession() as session:
        # Test 1: Health check
        try:
            async with session.get(f"{base_url}/health") as response:
                if response.status == 200:
                    print("1. ✅ Health endpoint working")
                else:
                    print(f"1. ❌ Health endpoint failed: {response.status}")
                    return False
        except Exception as e:
            print(f"1. ❌ Health endpoint error: {e}")
            return False
        
        # Test 2: Auth health
        try:
            async with session.get(f"{base_url}/api/auth/health") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"2. ✅ Auth service healthy: {data.get('users', '0')} users")
                else:
                    print(f"2. ❌ Auth health failed: {response.status}")
                    return False
        except Exception as e:
            print(f"2. ❌ Auth health error: {e}")
            return False
        
        # Test 3: Login
        try:
            login_data = {
                "email": "admin@example.com",
                "password": "admin"
            }
            
            async with session.post(
                f"{base_url}/api/auth/login",
                json=login_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    token = data.get("access_token")
                    user = data.get("user", {})
                    print(f"3. ✅ Login successful: {user.get('email')}")
                    print(f"   🎫 Token: {token[:20]}...")
                    
                    # Test 4: Protected endpoint
                    headers = {"Authorization": f"Bearer {token}"}
                    async with session.get(f"{base_url}/api/auth/me", headers=headers) as me_response:
                        if me_response.status == 200:
                            me_data = await me_response.json()
                            print(f"4. ✅ Protected endpoint working: {me_data.get('email')}")
                            return True
                        else:
                            print(f"4. ❌ Protected endpoint failed: {me_response.status}")
                            return False
                else:
                    print(f"3. ❌ Login failed: {response.status}")
                    error_text = await response.text()
                    print(f"   Error: {error_text}")
                    return False
        except Exception as e:
            print(f"3. ❌ Login error: {e}")
            return False

if __name__ == "__main__":
    success = asyncio.run(test_auth())
    
    if success:
        print("\n✅ Simple auth system is working correctly!")
        print("🔐 You can now login with:")
        print("   Email: admin@example.com")
        print("   Password: admin")
    else:
        print("\n❌ Simple auth system test failed!")
        print("🔧 Make sure the server is running on port 8000")