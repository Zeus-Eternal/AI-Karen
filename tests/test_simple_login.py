#!/usr/bin/env python3
"""
Simple login test to debug hanging issues
"""

import requests
import json
import time

BACKEND_URL = "http://127.0.0.1:8000"

def test_simple_login():
    """Test the simple login endpoint"""
    
    print("🔐 Simple Login Test")
    print("=" * 30)
    
    # Test data
    login_data = {
        "email": "admin@example.com",
        "password": "admin123"
    }
    
    try:
        print("\n1. 🚀 Testing simple login endpoint...")
        print(f"   URL: {BACKEND_URL}/api/auth/login-simple")
        print(f"   Data: {login_data}")
        
        start_time = time.time()
        
        response = requests.post(
            f"{BACKEND_URL}/api/auth/login-simple",
            json=login_data,
            headers={"Content-Type": "application/json"},
            timeout=30  # 30 second timeout
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"   Response time: {duration:.2f} seconds")
        print(f"   Status code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Simple login successful!")
            print(f"   User ID: {result['user']['user_id']}")
            print(f"   Email: {result['user']['email']}")
            print(f"   Token expires in: {result['expires_in']} seconds")
            return True
        else:
            print(f"❌ Simple login failed: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data}")
            except:
                print(f"   Error: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out after 30 seconds")
        print("   This indicates the login endpoint is hanging")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed - is the server running?")
        print("   Start the server with: python main.py")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_health_endpoint():
    """Test if the server is responding at all"""
    
    print("\n2. 🏥 Testing server health...")
    
    try:
        response = requests.get(
            f"{BACKEND_URL}/api/health",
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ Server is healthy and responding")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Debugging Login Hanging Issues")
    print("=" * 40)
    
    # Test server health first
    if test_health_endpoint():
        # Test simple login
        success = test_simple_login()
        
        if success:
            print("\n✅ Simple login is working!")
            print("   The hanging issue might be in the complex login endpoint.")
            print("   Try using /api/auth/login-simple for now.")
        else:
            print("\n❌ Simple login is also failing.")
            print("   Check server logs for authentication service issues.")
    else:
        print("\n❌ Server is not responding.")
        print("   Make sure the server is running: python main.py")