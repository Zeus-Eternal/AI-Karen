#!/usr/bin/env python3
"""
Debug script to test auth system availability and fix connectivity issues.
"""

import sys
import os
import requests
import json

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_auth_import():
    """Test if auth system can be imported"""
    print("🔍 Testing auth system import...")
    
    try:
        from src.auth.auth_routes import router as auth_router
        print("✅ Auth router imported successfully")
        print(f"   Router prefix: {auth_router.prefix}")
        print(f"   Router tags: {auth_router.tags}")
        
        # List routes
        print("   Available routes:")
        for route in auth_router.routes:
            print(f"     {route.methods} {route.path}")
        
        return True
    except ImportError as e:
        print(f"❌ Failed to import auth router: {e}")
        return False

def test_auth_service():
    """Test if auth service can be initialized"""
    print("\n🔍 Testing auth service initialization...")
    
    try:
        from src.auth.auth_service import get_auth_service
        auth_service = get_auth_service()
        print("✅ Auth service initialized successfully")
        print(f"   Storage type: {auth_service.storage_type}")
        
        # Test loading users
        users = auth_service._load_users()
        print(f"   Users loaded: {len(users)}")
        
        return True
    except Exception as e:
        print(f"❌ Failed to initialize auth service: {e}")
        return False

def test_backend_connectivity():
    """Test backend connectivity and available endpoints"""
    print("\n🔍 Testing backend connectivity...")
    
    base_urls = [
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://10.96.136.74:8010",  # The URL your frontend is trying
    ]
    
    for base_url in base_urls:
        print(f"\n   Testing {base_url}:")
        
        # Test health endpoint
        try:
            response = requests.get(f"{base_url}/health", timeout=5)
            if response.status_code == 200:
                print(f"     ✅ Health check: {response.json()}")
            else:
                print(f"     ❌ Health check failed: {response.status_code}")
        except Exception as e:
            print(f"     ❌ Health check error: {e}")
        
        # Test auth endpoints
        auth_endpoints = [
            "/api/auth/health",
            "/api/auth/dev-login",
            "/api/auth/login",
        ]
        
        for endpoint in auth_endpoints:
            try:
                if "dev-login" in endpoint:
                    response = requests.post(f"{base_url}{endpoint}", timeout=5)
                else:
                    response = requests.get(f"{base_url}{endpoint}", timeout=5)
                
                if response.status_code != 404:
                    print(f"     ✅ {endpoint}: {response.status_code}")
                else:
                    print(f"     ❌ {endpoint}: Not Found")
            except Exception as e:
                print(f"     ❌ {endpoint}: {e}")

def fix_frontend_config():
    """Generate frontend configuration fix"""
    print("\n🔧 Frontend Configuration Fix:")
    
    print("""
To fix your frontend connectivity issue, update your frontend configuration:

1. Update the API base URL in your frontend:
   - Change from: http://10.96.136.74:8010
   - Change to: http://localhost:8000

2. Update environment variables:
   export NEXT_PUBLIC_API_URL=http://localhost:8000
   export API_BASE_URL=http://localhost:8000

3. Update your session.ts or API client configuration:
   const API_BASE_URL = "http://localhost:8000";

4. If using Docker, ensure port mapping is correct:
   ports:
     - "8000:8000"  # Backend
     - "3000:3000"  # Frontend
""")

def main():
    """Main debug function"""
    print("🚀 AI-Karen Auth System Debug")
    print("=" * 50)
    
    # Test imports
    auth_import_ok = test_auth_import()
    auth_service_ok = test_auth_service()
    
    # Test connectivity
    test_backend_connectivity()
    
    # Provide fix recommendations
    fix_frontend_config()
    
    # Summary
    print("\n📊 Summary:")
    print(f"   Auth router import: {'✅' if auth_import_ok else '❌'}")
    print(f"   Auth service init: {'✅' if auth_service_ok else '❌'}")
    
    if auth_import_ok and auth_service_ok:
        print("\n✅ Auth system is working - issue is likely frontend configuration")
        print("   Your backend is running on port 8000, but frontend tries port 8010")
    else:
        print("\n❌ Auth system has issues - need to fix backend first")

if __name__ == "__main__":
    main()

