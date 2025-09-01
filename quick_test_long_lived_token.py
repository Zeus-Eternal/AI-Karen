#!/usr/bin/env python3
"""
Quick test for long-lived token functionality
"""

import requests
import json
import time

BACKEND_URL = "http://127.0.0.1:8000"

def test_long_lived_token():
    """Quick test of the long-lived token endpoint"""
    
    print("🔐 Quick Long-Lived Token Test")
    print("=" * 40)
    
    # Test data - you may need to adjust these credentials
    login_data = {
        "email": "admin@example.com",
        "password": "admin123"
    }
    
    try:
        # Step 1: Login
        print("\n1. 🚀 Testing login...")
        response = requests.post(
            f"{BACKEND_URL}/api/auth/login",
            json=login_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            login_result = response.json()
            access_token = login_result["access_token"]
            expires_in = login_result["expires_in"]
            
            print(f"✅ Login successful!")
            print(f"   Token expires in: {expires_in} seconds ({expires_in/60:.1f} minutes)")
            
            # Step 2: Test long-lived token creation
            print("\n2. ⏰ Testing long-lived token creation...")
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            ll_response = requests.post(
                f"{BACKEND_URL}/api/auth/create-long-lived-token",
                headers=headers,
                timeout=10
            )
            
            if ll_response.status_code == 200:
                ll_result = ll_response.json()
                ll_expires_in = ll_result["expires_in"]
                
                print(f"✅ Long-lived token created!")
                print(f"   Token expires in: {ll_expires_in} seconds ({ll_expires_in/3600:.1f} hours)")
                print(f"   Token type: {ll_result.get('token_type_description', 'long_lived')}")
                
                # Step 3: Test the long-lived token
                print("\n3. 🧪 Testing long-lived token validation...")
                
                ll_headers = {
                    "Authorization": f"Bearer {ll_result['access_token']}",
                    "Content-Type": "application/json"
                }
                
                me_response = requests.get(
                    f"{BACKEND_URL}/api/auth/me",
                    headers=ll_headers,
                    timeout=10
                )
                
                if me_response.status_code == 200:
                    me_result = me_response.json()
                    print(f"✅ Long-lived token validation successful!")
                    print(f"   User: {me_result['email']}")
                    print(f"   Roles: {me_result['roles']}")
                    
                    print("\n🎉 All tests passed! Long-lived tokens are working correctly.")
                    return True
                else:
                    print(f"❌ Token validation failed: {me_response.status_code}")
                    print(f"   Error: {me_response.text}")
            else:
                print(f"❌ Long-lived token creation failed: {ll_response.status_code}")
                print(f"   Error: {ll_response.text}")
        else:
            print(f"❌ Login failed: {response.status_code}")
            print(f"   Error: {response.text}")
            print("\n💡 Tip: Make sure you have a test user with email 'admin@example.com' and password 'admin123'")
            print("   Or update the credentials in this script.")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed - is the server running on http://127.0.0.1:8000?")
        print("   Start the server with: python main.py")
    except requests.exceptions.Timeout:
        print("❌ Request timed out - server might be starting up")
        print("   Wait a moment and try again")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    
    return False

if __name__ == "__main__":
    success = test_long_lived_token()
    if success:
        print("\n✅ Long-lived token implementation is working correctly!")
    else:
        print("\n❌ Long-lived token test failed. Check the server logs for details.")