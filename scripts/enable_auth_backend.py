#!/usr/bin/env python3
"""
Enable auth routes on the running backend
"""

import os
import sys
import requests
import subprocess

def check_backend_status():
    """Check if backend is running and healthy"""
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend is running and healthy")
            return True
    except:
        pass
    
    print("❌ Backend is not running on port 8000")
    return False

def test_auth_endpoints():
    """Test if auth endpoints are working"""
    endpoints = [
        ("GET", "/api/auth/health"),
        ("POST", "/api/auth/dev-login"),
    ]
    
    working_endpoints = []
    
    for method, endpoint in endpoints:
        try:
            if method == "GET":
                response = requests.get(f"http://localhost:8000{endpoint}", timeout=5)
            else:
                response = requests.post(f"http://localhost:8000{endpoint}", timeout=5)
            
            if response.status_code != 404:
                working_endpoints.append((endpoint, response.status_code))
                print(f"✅ {method} {endpoint}: {response.status_code}")
            else:
                print(f"❌ {method} {endpoint}: Not Found")
        except Exception as e:
            print(f"❌ {method} {endpoint}: {e}")
    
    return working_endpoints

def restart_backend_with_auth():
    """Instructions to restart backend with auth enabled"""
    print("\n🔧 To enable auth routes, restart your backend with these environment variables:")
    print("   export AUTH_ALLOW_DEV_LOGIN=true")
    print("   export AUTH_MODE=development")
    print("   export ENVIRONMENT=development")
    print("   python start.py")
    print("")
    print("Or run this command:")
    print("   AUTH_ALLOW_DEV_LOGIN=true AUTH_MODE=development ENVIRONMENT=development python start.py")

def create_simple_auth_test():
    """Create a simple test to verify auth is working"""
    test_script = '''
import requests
import json

def test_dev_login():
    """Test the dev login endpoint"""
    try:
        response = requests.post("http://localhost:8000/api/auth/dev-login")
        if response.status_code == 200:
            data = response.json()
            print("✅ Dev login successful!")
            print(f"   Token: {data.get('access_token', 'N/A')[:50]}...")
            print(f"   User: {data.get('user', {}).get('email', 'N/A')}")
            return data.get('access_token')
        else:
            print(f"❌ Dev login failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Dev login error: {e}")
        return None

def test_protected_endpoint(token):
    """Test a protected endpoint with the token"""
    if not token:
        return
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get("http://localhost:8000/api/auth/me", headers=headers)
        if response.status_code == 200:
            data = response.json()
            print("✅ Protected endpoint access successful!")
            print(f"   User info: {json.dumps(data, indent=2)}")
        else:
            print(f"❌ Protected endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Protected endpoint error: {e}")

if __name__ == "__main__":
    print("🧪 Testing AI-Karen Auth System")
    print("=" * 40)
    
    token = test_dev_login()
    test_protected_endpoint(token)
'''
    
    import os
    os.makedirs("tests/manual", exist_ok=True)
    out_path = "tests/manual/test_auth_simple.py"
    with open(out_path, "w") as f:
        f.write(test_script)
    
    print(f"📝 Created {out_path} - run this after restarting backend")

def main():
    print("🚀 AI-Karen Auth Enabler")
    print("=" * 30)
    
    if not check_backend_status():
        print("\n❌ Backend not running. Start it first with: python start.py")
        return
    
    working = test_auth_endpoints()
    
    if working:
        print(f"\n✅ Found {len(working)} working auth endpoints!")
        print("   Your auth system might already be working.")
        print("   Try the dev login: curl -X POST http://localhost:8000/api/auth/dev-login")
    else:
        print("\n❌ No auth endpoints found.")
        restart_backend_with_auth()
    
    create_simple_auth_test()
    
    print("\n🌐 Frontend Fix:")
    print("   Update your frontend to use: http://localhost:8000")
    print("   Instead of: http://10.96.136.74:8010")

if __name__ == "__main__":
    main()
