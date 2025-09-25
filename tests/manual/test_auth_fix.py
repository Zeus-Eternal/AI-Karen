#!/usr/bin/env python3
"""
Test script to verify the authentication fix is working
"""

import requests
import json

def test_backend_auth():
    """Test backend auth endpoint directly"""
    print("🔍 Testing backend auth endpoint...")
    
    try:
        response = requests.post(
            "http://localhost:8000/api/auth/dev-login",
            headers={"Content-Type": "application/json"},
            json={}
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Backend auth successful!")
            print(f"   Token: {data['access_token'][:50]}...")
            print(f"   User: {data['user']['email']}")
            return True
        else:
            print(f"❌ Backend auth failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Backend auth error: {e}")
        return False

def test_frontend_auth():
    """Test frontend auth proxy endpoint"""
    print("\n🔍 Testing frontend auth proxy...")
    
    try:
        response = requests.post(
            "http://localhost:8010/api/auth/login-simple",
            headers={"Content-Type": "application/json"},
            json={}
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Frontend auth proxy successful!")
            print(f"   Token: {data['access_token'][:50]}...")
            print(f"   User: {data['user']['email']}")
            return True
        else:
            print(f"❌ Frontend auth proxy failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Frontend auth proxy error: {e}")
        return False

def test_frontend_page():
    """Test if frontend page loads"""
    print("\n🔍 Testing frontend page load...")
    
    try:
        response = requests.get("http://localhost:8010/")
        
        if response.status_code == 200:
            print("✅ Frontend page loads successfully!")
            return True
        else:
            print(f"❌ Frontend page failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Frontend page error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testing AI-Karen Authentication Fix")
    print("=" * 50)
    
    backend_ok = test_backend_auth()
    frontend_ok = test_frontend_auth()
    page_ok = test_frontend_page()
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"   Backend Auth:     {'✅ PASS' if backend_ok else '❌ FAIL'}")
    print(f"   Frontend Proxy:   {'✅ PASS' if frontend_ok else '❌ FAIL'}")
    print(f"   Frontend Page:    {'✅ PASS' if page_ok else '❌ FAIL'}")
    
    if backend_ok and frontend_ok and page_ok:
        print("\n🎉 ALL TESTS PASSED! Authentication is working correctly.")
        print("\n💡 Next steps:")
        print("   1. Open http://localhost:8010 in your browser")
        print("   2. The auto-login should work automatically")
        print("   3. If you see login errors, they should resolve after this fix")
    else:
        print("\n⚠️  Some tests failed. Check the logs above for details.")

