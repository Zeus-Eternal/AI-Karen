#!/usr/bin/env python3
"""
Test login with more detailed error handling
"""

import asyncio
import json
import aiohttp

async def test_login_variations():
    """Test different login request formats"""
    
    test_cases = [
        {
            "name": "Valid admin login",
            "data": {
                "email": "admin@ai-karen.local",
                "password": "admin123"
            }
        },
        {
            "name": "Simple email format",
            "data": {
                "email": "admin@example.com",
                "password": "admin123"
            }
        },
        {
            "name": "Missing password",
            "data": {
                "email": "admin@ai-karen.local"
            }
        },
        {
            "name": "Missing email",
            "data": {
                "password": "admin123"
            }
        },
        {
            "name": "Invalid email format",
            "data": {
                "email": "not-an-email",
                "password": "admin123"
            }
        }
    ]
    
    for test_case in test_cases:
        print(f"\n--- Testing: {test_case['name']} ---")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "http://localhost:8000/api/auth/login",
                    json=test_case['data'],
                    headers={"Content-Type": "application/json"}
                ) as response:
                    print(f"Status: {response.status}")
                    
                    response_text = await response.text()
                    print(f"Response: {response_text}")
                    
                    if response.status == 422:
                        try:
                            error_data = json.loads(response_text)
                            if 'detail' in error_data and isinstance(error_data['detail'], list):
                                print("Validation errors:")
                                for error in error_data['detail']:
                                    print(f"  - {error.get('loc', [])}: {error.get('msg', '')}")
                        except:
                            pass
                            
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_login_variations())