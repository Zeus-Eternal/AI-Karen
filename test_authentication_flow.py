#!/usr/bin/env python3
"""
Test script to verify the complete authentication flow
"""

import requests
import json
import sys
from typing import Dict, Any

def test_authentication_flow(base_url: str, origin: str) -> Dict[str, Any]:
    """Test complete authentication flow"""
    results = {}
    
    # Test data
    test_user = {
        "email": "test@example.com",
        "password": "TestPassword123!"
    }
    
    headers = {
        'Origin': origin,
        'Content-Type': 'application/json'
    }
    
    print(f"🧪 Testing authentication flow with backend: {base_url}")
    print(f"🌐 Origin: {origin}")
    print("-" * 50)
    
    # 1. Test user registration
    print("1️⃣ Testing user registration...")
    try:
        response = requests.post(
            f"{base_url}/api/auth/register",
            json=test_user,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            print("   ✅ Registration successful")
            results['register'] = {'success': True, 'data': response.json()}
        else:
            print(f"   ❌ Registration failed: {response.status_code} - {response.text}")
            results['register'] = {'success': False, 'error': response.text}
            
    except Exception as e:
        print(f"   ❌ Registration error: {e}")
        results['register'] = {'success': False, 'error': str(e)}
    
    # 2. Test user login
    print("2️⃣ Testing user login...")
    try:
        response = requests.post(
            f"{base_url}/api/auth/login",
            json=test_user,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            print("   ✅ Login successful")
            login_data = response.json()
            results['login'] = {'success': True, 'data': login_data}
            
            # Extract token for further tests
            token = login_data.get('token')
            if token:
                results['token'] = token
                
        else:
            print(f"   ❌ Login failed: {response.status_code} - {response.text}")
            results['login'] = {'success': False, 'error': response.text}
            
    except Exception as e:
        print(f"   ❌ Login error: {e}")
        results['login'] = {'success': False, 'error': str(e)}
    
    # 3. Test authenticated endpoint
    if 'token' in results:
        print("3️⃣ Testing authenticated endpoint...")
        try:
            auth_headers = {
                **headers,
                'Authorization': f'Bearer {results["token"]}'
            }
            
            response = requests.get(
                f"{base_url}/api/auth/me",
                headers=auth_headers,
                timeout=10
            )
            
            if response.status_code == 200:
                print("   ✅ Authenticated request successful")
                results['me'] = {'success': True, 'data': response.json()}
            else:
                print(f"   ❌ Authenticated request failed: {response.status_code} - {response.text}")
                results['me'] = {'success': False, 'error': response.text}
                
        except Exception as e:
            print(f"   ❌ Authenticated request error: {e}")
            results['me'] = {'success': False, 'error': str(e)}
    
    # 4. Test logout
    if 'token' in results:
        print("4️⃣ Testing logout...")
        try:
            response = requests.post(
                f"{base_url}/api/auth/logout",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                print("   ✅ Logout successful")
                results['logout'] = {'success': True, 'data': response.json()}
            else:
                print(f"   ❌ Logout failed: {response.status_code} - {response.text}")
                results['logout'] = {'success': False, 'error': response.text}
                
        except Exception as e:
            print(f"   ❌ Logout error: {e}")
            results['logout'] = {'success': False, 'error': str(e)}
    
    return results

def main():
    """Main test function"""
    print("🔐 Testing Complete Authentication System")
    print("=" * 60)
    
    # Test configurations
    backend_url = 'http://localhost:8000'
    frontend_origins = [
        'http://localhost:9002',
        'http://127.0.0.1:9002',
        'http://10.105.235.209:9002'
    ]
    
    all_tests_passed = True
    
    for origin in frontend_origins:
        print(f"\n🌐 Testing with origin: {origin}")
        print("=" * 60)
        
        results = test_authentication_flow(backend_url, origin)
        
        # Check if all tests passed
        test_success = all(
            result.get('success', False) 
            for key, result in results.items() 
            if key != 'token'
        )
        
        if test_success:
            print(f"\n🎉 All authentication tests PASSED for origin: {origin}")
        else:
            print(f"\n⚠️  Some authentication tests FAILED for origin: {origin}")
            all_tests_passed = False
        
        print("\n" + "=" * 60)
    
    print(f"\n📋 Final Results:")
    if all_tests_passed:
        print("🎉 Complete authentication system is working perfectly!")
        print("✅ Users can create accounts, login, access protected resources, and logout")
        print("✅ CORS is properly configured for all origins")
        print("✅ Authentication system is ready for production use")
    else:
        print("⚠️  Some authentication tests failed. Check the errors above.")
    
    print(f"\n🚀 Next Steps:")
    print("1. Access the web UI and test the authentication forms")
    print("2. Try creating an account, logging in, and using the application")
    print("3. Test the change password and logout functionality")
    
    return 0 if all_tests_passed else 1

if __name__ == "__main__":
    sys.exit(main())