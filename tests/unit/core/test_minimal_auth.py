#!/usr/bin/env python3
"""
Minimal authentication test to isolate the timeout issue
"""

import asyncio
import aiohttp
import json
import sys
from datetime import datetime

async def test_minimal_auth():
    """Test authentication with minimal complexity"""
    
    print("🔧 Minimal Authentication Test")
    print("=" * 40)
    
    # Test data
    test_user = {
        "email": "test@example.com",
        "password": "testpass123"
    }
    
    timeout = aiohttp.ClientTimeout(total=10)  # 10 second timeout
    
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            
            # Test 1: Health check first
            print("1. 🏥 Testing health endpoint...")
            try:
                async with session.get("http://127.0.0.1:8000/health") as response:
                    if response.status == 200:
                        print("   ✅ Health endpoint working")
                    else:
                        print(f"   ❌ Health endpoint returned {response.status}")
                        return False
            except asyncio.TimeoutError:
                print("   ❌ Health endpoint timed out")
                return False
            except Exception as e:
                print(f"   ❌ Health endpoint error: {e}")
                return False
            
            # Test 2: Try simple login endpoint
            print("2. 🔐 Testing simple login endpoint...")
            try:
                async with session.post(
                    "http://127.0.0.1:8000/api/auth/login-simple",
                    json=test_user,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    print(f"   📊 Response status: {response.status}")
                    
                    if response.status == 200:
                        data = await response.json()
                        print("   ✅ Simple login successful!")
                        print(f"   🎫 Access token received: {data.get('access_token', 'N/A')[:20]}...")
                        return True
                    elif response.status == 401:
                        print("   ⚠️ Authentication failed (expected - no user exists)")
                        return True  # This is actually good - server is responding
                    else:
                        error_text = await response.text()
                        print(f"   ❌ Login failed with status {response.status}")
                        print(f"   📝 Error: {error_text}")
                        return False
                        
            except asyncio.TimeoutError:
                print("   ❌ Simple login timed out")
                return False
            except Exception as e:
                print(f"   ❌ Simple login error: {e}")
                return False
                
    except Exception as e:
        print(f"❌ Session creation failed: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_minimal_auth())
    if result:
        print("\n✅ Minimal auth test passed!")
        sys.exit(0)
    else:
        print("\n❌ Minimal auth test failed!")
        sys.exit(1)