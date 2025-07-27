#!/usr/bin/env python3
"""
Test script for Web UI authentication integration
"""

import requests
import json

def test_authentication_flow():
    """Test the complete authentication flow"""
    base_url = "http://localhost:8000"
    
    print("🔐 Testing Web UI Authentication Integration")
    print("=" * 50)
    
    # Test 1: Login with admin credentials
    print("\n1. Testing admin login...")
    login_data = {
        "email": "admin@kari.ai",
        "password": "pswd123"
    }
    
    try:
        response = requests.post(f"{base_url}/api/auth/login", json=login_data)
        if response.status_code == 200:
            login_result = response.json()
            print("✅ Admin login successful!")
            print(f"   Token: {login_result['token'][:50]}...")
            print(f"   User ID: {login_result['user_id']}")
            print(f"   Email: {login_result['email']}")
            print(f"   Roles: {login_result['roles']}")
            print(f"   Tenant ID: {login_result['tenant_id']}")
            print(f"   Preferences: {json.dumps(login_result['preferences'], indent=2)}")
            
            admin_token = login_result['token']
        else:
            print(f"❌ Admin login failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Admin login error: {e}")
        return False
    
    # Test 2: Test /me endpoint with admin token
    print("\n2. Testing /me endpoint with admin token...")
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{base_url}/api/auth/me", headers=headers)
        if response.status_code == 200:
            user_data = response.json()
            print("✅ /me endpoint successful!")
            print(f"   User ID: {user_data['user_id']}")
            print(f"   Email: {user_data['email']}")
            print(f"   Roles: {user_data['roles']}")
            print(f"   Tenant ID: {user_data['tenant_id']}")
        else:
            print(f"❌ /me endpoint failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ /me endpoint error: {e}")
        return False
    
    # Test 3: Login with user credentials
    print("\n3. Testing user login...")
    user_login_data = {
        "email": "user@kari.ai",
        "password": "pswd123"
    }
    
    try:
        response = requests.post(f"{base_url}/api/auth/login", json=user_login_data)
        if response.status_code == 200:
            user_result = response.json()
            print("✅ User login successful!")
            print(f"   User ID: {user_result['user_id']}")
            print(f"   Email: {user_result['email']}")
            print(f"   Roles: {user_result['roles']}")
            print(f"   Tenant ID: {user_result['tenant_id']}")
            
            user_token = user_result['token']
        else:
            print(f"❌ User login failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ User login error: {e}")
        return False
    
    # Test 4: Test conversation creation with authenticated user
    print("\n4. Testing conversation creation...")
    try:
        headers = {"Authorization": f"Bearer {user_token}"}
        conversation_data = {
            "session_id": f"test_session_{int(time.time())}",
            "ui_source": "web_ui",
            "title": "Test Conversation",
            "user_settings": {},
            "ui_context": {
                "user_id": user_result['user_id'],
                "created_from": "test_script"
            },
            "tags": ["test"],
            "priority": "normal"
        }
        
        response = requests.post(f"{base_url}/api/conversations/create", 
                               json=conversation_data, headers=headers)
        if response.status_code == 200:
            conv_result = response.json()
            print("✅ Conversation creation successful!")
            print(f"   Conversation ID: {conv_result['conversation']['id']}")
            print(f"   Session ID: {conv_result['conversation']['session_id']}")
            print(f"   Title: {conv_result['conversation']['title']}")
        else:
            print(f"❌ Conversation creation failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Conversation creation error: {e}")
        return False
    
    # Test 5: Test invalid credentials
    print("\n5. Testing invalid credentials...")
    invalid_data = {
        "email": "invalid@example.com",
        "password": "wrong"
    }
    
    try:
        response = requests.post(f"{base_url}/api/auth/login", json=invalid_data)
        if response.status_code == 401:
            print("✅ Invalid credentials properly rejected!")
        else:
            print(f"❌ Invalid credentials test failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Invalid credentials test error: {e}")
        return False
    
    print("\n🎉 All authentication tests passed!")
    print("=" * 50)
    print("✅ Web UI authentication integration is working correctly!")
    print("\nNext steps:")
    print("1. Open http://localhost:9002 in your browser")
    print("2. Try logging in with:")
    print("   - Admin: admin@kari.ai / pswd123")
    print("   - User: user@kari.ai / pswd123")
    print("3. Test the chat interface with authenticated users")
    
    return True

if __name__ == "__main__":
    import time
    test_authentication_flow()