#!/usr/bin/env python3
"""
Test script for long-lived token functionality
"""

import asyncio
import aiohttp
import json
from datetime import datetime, timezone

BACKEND_URL = "http://127.0.0.1:8000"

async def test_long_lived_token():
    """Test the long-lived token creation after login"""
    
    async with aiohttp.ClientSession() as session:
        print("🔐 Testing Long-Lived Token Creation")
        print("=" * 50)
        
        # Step 1: Login to get initial token
        print("\n1. 🚀 Attempting login...")
        login_data = {
            "email": "admin@example.com",  # Replace with your test user
            "password": "admin123"         # Replace with your test password
        }
        
        try:
            async with session.post(
                f"{BACKEND_URL}/api/auth/login",
                json=login_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    login_result = await response.json()
                    access_token = login_result["access_token"]
                    expires_in = login_result["expires_in"]
                    
                    print(f"✅ Login successful!")
                    print(f"   Access token expires in: {expires_in} seconds ({expires_in/60:.1f} minutes)")
                    print(f"   User ID: {login_result['user']['user_id']}")
                    print(f"   Email: {login_result['user']['email']}")
                    
                    # Step 2: Create long-lived token
                    print("\n2. ⏰ Creating long-lived token...")
                    
                    headers = {
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": "application/json"
                    }
                    
                    async with session.post(
                        f"{BACKEND_URL}/api/auth/create-long-lived-token",
                        headers=headers
                    ) as ll_response:
                        if ll_response.status == 200:
                            ll_result = await ll_response.json()
                            ll_token = ll_result["access_token"]
                            ll_expires_in = ll_result["expires_in"]
                            
                            print(f"✅ Long-lived token created successfully!")
                            print(f"   Token expires in: {ll_expires_in} seconds ({ll_expires_in/3600:.1f} hours)")
                            print(f"   Token type: {ll_result.get('token_type_description', 'long_lived')}")
                            
                            # Step 3: Test the long-lived token
                            print("\n3. 🧪 Testing long-lived token...")
                            
                            ll_headers = {
                                "Authorization": f"Bearer {ll_token}",
                                "Content-Type": "application/json"
                            }
                            
                            async with session.get(
                                f"{BACKEND_URL}/api/auth/me",
                                headers=ll_headers
                            ) as me_response:
                                if me_response.status == 200:
                                    me_result = await me_response.json()
                                    print(f"✅ Long-lived token validation successful!")
                                    print(f"   Validated user: {me_result['email']}")
                                    print(f"   User roles: {me_result['roles']}")
                                    
                                    # Step 4: Test API call with long-lived token
                                    print("\n4. 🌐 Testing API call with long-lived token...")
                                    
                                    async with session.get(
                                        f"{BACKEND_URL}/api/health",
                                        headers=ll_headers
                                    ) as health_response:
                                        if health_response.status == 200:
                                            health_result = await health_response.json()
                                            print(f"✅ API call successful with long-lived token!")
                                            print(f"   Health status: {health_result.get('status', 'unknown')}")
                                        else:
                                            print(f"❌ API call failed: {health_response.status}")
                                            error_text = await health_response.text()
                                            print(f"   Error: {error_text}")
                                else:
                                    print(f"❌ Long-lived token validation failed: {me_response.status}")
                                    error_text = await me_response.text()
                                    print(f"   Error: {error_text}")
                        else:
                            print(f"❌ Long-lived token creation failed: {ll_response.status}")
                            error_text = await ll_response.text()
                            print(f"   Error: {error_text}")
                else:
                    print(f"❌ Login failed: {response.status}")
                    error_text = await response.text()
                    print(f"   Error: {error_text}")
                    
        except aiohttp.ClientError as e:
            print(f"❌ Network error: {e}")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
        
        print("\n" + "=" * 50)
        print("🏁 Test completed")


if __name__ == "__main__":
    asyncio.run(test_long_lived_token())