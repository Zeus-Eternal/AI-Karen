#!/usr/bin/env python3
"""
Test script to verify session persistence fixes

This script tests the session persistence functionality to ensure
users don't get redirected to login on each page refresh.
"""

import asyncio
import aiohttp
import json
from datetime import datetime


async def test_session_persistence():
    """Test the complete session persistence flow"""
    
    print("🔧 Testing Session Persistence Fixes")
    print("=" * 50)
    
    base_url = "http://localhost:8000"
    
    async with aiohttp.ClientSession() as session:
        
        # Test 1: Login and get cookies
        print("\n1. Testing login and cookie setting...")
        
        login_data = {
            "email": "test@example.com",
            "password": "testpassword123"
        }
        
        try:
            async with session.post(
                f"{base_url}/api/auth/login",
                json=login_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Login successful: {data.get('user', {}).get('email', 'Unknown')}")
                    
                    # Check cookies
                    cookies = response.cookies
                    refresh_cookie = cookies.get('kari_refresh_token')
                    session_cookie = cookies.get('kari_session')
                    
                    if refresh_cookie:
                        print(f"✅ Refresh token cookie set: {refresh_cookie.key}")
                        print(f"   - Path: {refresh_cookie.get('path', 'Not set')}")
                        print(f"   - HttpOnly: {refresh_cookie.get('httponly', 'Not set')}")
                        print(f"   - Secure: {refresh_cookie.get('secure', 'Not set')}")
                        print(f"   - SameSite: {refresh_cookie.get('samesite', 'Not set')}")
                    else:
                        print("❌ No refresh token cookie found")
                    
                    if session_cookie:
                        print(f"✅ Session cookie set: {session_cookie.key}")
                    else:
                        print("❌ No session cookie found")
                        
                else:
                    print(f"❌ Login failed: {response.status} - {await response.text()}")
                    return
                    
        except Exception as e:
            print(f"❌ Login error: {e}")
            return
        
        # Test 2: Validate session using cookies
        print("\n2. Testing session validation with cookies...")
        
        try:
            async with session.get(
                f"{base_url}/api/auth/validate-session"
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    if data.get('valid'):
                        print(f"✅ Session validation successful: {data.get('user', {}).get('email', 'Unknown')}")
                    else:
                        print(f"❌ Session validation failed: {data.get('error', 'Unknown error')}")
                else:
                    print(f"❌ Session validation request failed: {response.status}")
                    
        except Exception as e:
            print(f"❌ Session validation error: {e}")
        
        # Test 3: Test token refresh
        print("\n3. Testing token refresh...")
        
        try:
            async with session.post(
                f"{base_url}/api/auth/refresh"
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Token refresh successful: expires in {data.get('expires_in', 'Unknown')}s")
                    
                    # Check if new cookies are set
                    new_cookies = response.cookies
                    if new_cookies.get('kari_refresh_token'):
                        print("✅ New refresh token cookie set")
                    
                else:
                    print(f"❌ Token refresh failed: {response.status} - {await response.text()}")
                    
        except Exception as e:
            print(f"❌ Token refresh error: {e}")
        
        # Test 4: Test protected endpoint access
        print("\n4. Testing protected endpoint access...")
        
        try:
            async with session.get(
                f"{base_url}/api/auth/me"
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Protected endpoint access successful: {data.get('email', 'Unknown')}")
                else:
                    print(f"❌ Protected endpoint access failed: {response.status}")
                    
        except Exception as e:
            print(f"❌ Protected endpoint error: {e}")
        
        # Test 5: Test logout
        print("\n5. Testing logout and cookie clearing...")
        
        try:
            async with session.post(
                f"{base_url}/api/auth/logout"
            ) as response:
                
                if response.status == 200:
                    print("✅ Logout successful")
                    
                    # Check if cookies are cleared
                    logout_cookies = response.cookies
                    refresh_cookie = logout_cookies.get('kari_refresh_token')
                    session_cookie = logout_cookies.get('kari_session')
                    
                    if refresh_cookie and refresh_cookie.value == "":
                        print("✅ Refresh token cookie cleared")
                    else:
                        print("❌ Refresh token cookie not properly cleared")
                    
                    if session_cookie and session_cookie.value == "":
                        print("✅ Session cookie cleared")
                    else:
                        print("❌ Session cookie not properly cleared")
                        
                else:
                    print(f"❌ Logout failed: {response.status}")
                    
        except Exception as e:
            print(f"❌ Logout error: {e}")
    
    print("\n" + "=" * 50)
    print("🏁 Session persistence test completed")


async def test_cookie_configuration():
    """Test cookie configuration for different environments"""
    
    print("\n🍪 Testing Cookie Configuration")
    print("=" * 50)
    
    try:
        from src.ai_karen_engine.auth.cookie_manager import get_cookie_manager
        
        cookie_manager = get_cookie_manager()
        security_info = cookie_manager.get_cookie_security_info()
        validation = cookie_manager.validate_cookie_security()
        
        print(f"Environment: {security_info['environment']}")
        print(f"Is Production: {security_info['is_production']}")
        print(f"Secure Flag: {security_info['secure']}")
        print(f"HttpOnly Flag: {security_info['httponly']}")
        print(f"SameSite: {security_info['samesite']}")
        print(f"Refresh Cookie Name: {security_info['refresh_token_cookie']}")
        print(f"Session Cookie Name: {security_info['session_cookie']}")
        
        if validation['valid']:
            print("✅ Cookie configuration is valid")
        else:
            print("❌ Cookie configuration issues found:")
            for issue in validation['issues']:
                print(f"   - {issue}")
            
            print("\nRecommendations:")
            for rec in validation['recommendations']:
                print(f"   - {rec}")
                
    except Exception as e:
        print(f"❌ Cookie configuration test error: {e}")


if __name__ == "__main__":
    print("🚀 Starting Session Persistence Tests")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    # Test cookie configuration
    asyncio.run(test_cookie_configuration())
    
    # Test session persistence flow
    asyncio.run(test_session_persistence())
    
    print("\n💡 Next Steps:")
    print("1. Ensure the server is running on http://localhost:8000")
    print("2. Create a test user account if login fails")
    print("3. Check browser developer tools for cookie behavior")
    print("4. Verify frontend session recovery works on page refresh")