#!/usr/bin/env python3
"""
Test login validation to debug 422 errors
"""

import asyncio
import json
import aiohttp

async def test_login_endpoint():
    """Test the login endpoint directly"""
    
    # Test data
    login_data = {
        "email": "admin@ai-karen.local",
        "password": "admin123"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            # Test the login endpoint
            print("Testing login endpoint...")
            async with session.post(
                "http://localhost:8000/api/auth/login",
                json=login_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                print(f"Status: {response.status}")
                print(f"Headers: {dict(response.headers)}")
                
                response_text = await response.text()
                print(f"Response: {response_text}")
                
                if response.status == 422:
                    print("❌ Validation error (422)")
                    try:
                        error_data = json.loads(response_text)
                        print(f"Validation errors: {json.dumps(error_data, indent=2)}")
                    except:
                        print("Could not parse error response as JSON")
                elif response.status == 200:
                    print("✅ Login successful!")
                else:
                    print(f"❌ Unexpected status: {response.status}")
                    
    except Exception as e:
        print(f"❌ Error testing login: {e}")

async def test_auth_health():
    """Test the auth health endpoint"""
    
    try:
        async with aiohttp.ClientSession() as session:
            print("Testing auth health endpoint...")
            async with session.get("http://localhost:8000/api/auth/health") as response:
                print(f"Health Status: {response.status}")
                response_text = await response.text()
                print(f"Health Response: {response_text}")
                
    except Exception as e:
        print(f"❌ Error testing health: {e}")

if __name__ == "__main__":
    print("Testing login validation...")
    asyncio.run(test_auth_health())
    asyncio.run(test_login_endpoint())