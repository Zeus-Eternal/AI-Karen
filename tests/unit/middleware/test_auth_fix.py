#!/usr/bin/env python3
"""
Test the authentication fix
"""

import requests
import time

BACKEND_URL = "http://127.0.0.1:8000"

def test_auth_fix():
    """Test the simplified authentication"""
    
    print("🔧 Testing Authentication Fix")
    print("=" * 35)
    
    # Test credentials
    login_data = {
        "email": "admin@example.com",
        "password": "admin123"
    }
    
    try:
        print(f"\n1. 🚀 Testing login endpoint...")
        print(f"   URL: {BACKEND_URL}/api/auth/login")
        
        start_time = time.time()
        
        response = requests.post(
            f"{BACKEND_URL}/api/auth/login",
            json=login_data,
            headers={"Content-Type": "application/json"},
            timeout=20  # 20 second timeout
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"   ⏱️  Response time: {duration:.2f} seconds")
        print(f"   📊 Status code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Login successful!")
            print(f"   👤 User: {result['user']['email']}")
            print(f"   🔑 Token expires in: {result['expires_in']} seconds")
            print(f"   🎯 Authentication fix is working!")
            return True
        elif response.status_code == 401:
            print(f"❌ Invalid credentials")
            print(f"   💡 Make sure you have a test user or update the credentials")
            return False
        else:
            print(f"❌ Login failed: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data}")
            except:
                print(f"   Error: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Request still timing out after 20 seconds")
        print("   The authentication system still has issues")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed - is the server running?")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = test_auth_fix()
    
    if success:
        print("\n🎉 Authentication fix successful!")
        print("   Login should now work without hanging.")
    else:
        print("\n❌ Authentication fix needs more work.")
        print("   Check server logs for additional issues.")