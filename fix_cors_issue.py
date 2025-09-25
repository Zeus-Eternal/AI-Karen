#!/usr/bin/env python3
"""
Fix CORS issue by adding the frontend origin to allowed origins
"""

import os
import sys

def fix_cors_for_frontend():
    """Add the frontend origin to CORS allowed origins"""
    
    frontend_origin = "http://10.96.136.74:8010"
    
    print("🔧 CORS Fix for AI-Karen")
    print("=" * 30)
    print(f"Adding frontend origin: {frontend_origin}")
    
    # Method 1: Environment variable approach
    print("\n📝 Method 1: Set environment variable")
    print("Run your backend with this environment variable:")
    
    current_cors = os.getenv("CORS_ORIGINS", "")
    if current_cors:
        new_cors = f"{current_cors},{frontend_origin}"
    else:
        new_cors = f"http://localhost:3000,http://localhost:8020,http://localhost:8010,{frontend_origin}"
    
    print(f'export CORS_ORIGINS="{new_cors}"')
    print("python start.py")
    
    # Method 2: Alternative environment variable
    print("\n📝 Method 2: Use KARI_CORS_ORIGINS")
    print(f'export KARI_CORS_ORIGINS="{new_cors}"')
    print("python start.py")
    
    # Method 3: Enable dev origins (most permissive)
    print("\n📝 Method 3: Enable dev origins (recommended for development)")
    print("export ALLOW_DEV_ORIGINS=true")
    print("export CORS_ALLOW_ORIGIN_REGEX='^https?://.*:(\\d+)?$'")
    print("python start.py")
    
    # Method 4: Quick test command
    print("\n🚀 Quick Test Command:")
    print(f'CORS_ORIGINS="{new_cors}" ALLOW_DEV_ORIGINS=true python start.py')
    
    print("\n✅ After restarting with CORS fix:")
    print("   1. Your frontend should be able to connect")
    print("   2. No more CORS errors in browser console")
    print("   3. Chat requests should work properly")

def test_cors_fix():
    """Test if CORS is working"""
    import requests
    
    print("\n🧪 Testing CORS Configuration")
    print("-" * 30)
    
    # Test preflight request
    try:
        response = requests.options(
            "http://localhost:8000/copilot/assist",
            headers={
                "Origin": "http://10.96.136.74:8010",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type,Authorization"
            },
            timeout=5
        )
        
        if response.status_code == 200:
            cors_headers = {
                "Access-Control-Allow-Origin": response.headers.get("Access-Control-Allow-Origin"),
                "Access-Control-Allow-Methods": response.headers.get("Access-Control-Allow-Methods"),
                "Access-Control-Allow-Headers": response.headers.get("Access-Control-Allow-Headers"),
                "Access-Control-Allow-Credentials": response.headers.get("Access-Control-Allow-Credentials")
            }
            
            print("✅ CORS preflight successful!")
            print("   CORS Headers:")
            for header, value in cors_headers.items():
                if value:
                    print(f"     {header}: {value}")
            
            if cors_headers["Access-Control-Allow-Origin"] in ["*", "http://10.96.136.74:8010"]:
                print("✅ Frontend origin is allowed!")
            else:
                print("❌ Frontend origin not in allowed origins")
                
        else:
            print(f"❌ CORS preflight failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ CORS test failed: {e}")
        print("   Make sure backend is running on http://localhost:8000")

def create_cors_test_script():
    """Create a test script to verify CORS"""
    
    script_content = '''#!/usr/bin/env python3
"""
Test CORS configuration for AI-Karen
"""

import requests

def test_cors():
    """Test CORS preflight and actual request"""
    
    frontend_origin = "http://10.96.136.74:8010"
    backend_url = "http://localhost:8000"
    
    print("🧪 Testing CORS Configuration")
    print("=" * 40)
    print(f"Frontend: {frontend_origin}")
    print(f"Backend: {backend_url}")
    
    # Test 1: Preflight request
    print("\\n1. Testing CORS preflight...")
    try:
        response = requests.options(
            f"{backend_url}/copilot/assist",
            headers={
                "Origin": frontend_origin,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type,Authorization"
            },
            timeout=5
        )
        
        print(f"   Status: {response.status_code}")
        
        cors_origin = response.headers.get("Access-Control-Allow-Origin")
        cors_methods = response.headers.get("Access-Control-Allow-Methods")
        cors_headers = response.headers.get("Access-Control-Allow-Headers")
        
        print(f"   Allow-Origin: {cors_origin}")
        print(f"   Allow-Methods: {cors_methods}")
        print(f"   Allow-Headers: {cors_headers}")
        
        if cors_origin in ["*", frontend_origin]:
            print("   ✅ CORS preflight passed!")
        else:
            print("   ❌ CORS preflight failed - origin not allowed")
            
    except Exception as e:
        print(f"   ❌ Preflight error: {e}")
    
    # Test 2: Health endpoint
    print("\\n2. Testing health endpoint...")
    try:
        response = requests.get(
            f"{backend_url}/health",
            headers={"Origin": frontend_origin},
            timeout=5
        )
        
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        
        cors_origin = response.headers.get("Access-Control-Allow-Origin")
        if cors_origin:
            print(f"   CORS Origin: {cors_origin}")
            print("   ✅ Health endpoint CORS working!")
        else:
            print("   ❌ No CORS headers in response")
            
    except Exception as e:
        print(f"   ❌ Health test error: {e}")
    
    # Test 3: Copilot endpoint (requires auth)
    print("\\n3. Testing copilot endpoint...")
    try:
        response = requests.post(
            f"{backend_url}/copilot/assist",
            headers={
                "Origin": frontend_origin,
                "Content-Type": "application/json"
            },
            json={"message": "test"},
            timeout=5
        )
        
        print(f"   Status: {response.status_code}")
        
        cors_origin = response.headers.get("Access-Control-Allow-Origin")
        if cors_origin:
            print(f"   CORS Origin: {cors_origin}")
            print("   ✅ Copilot endpoint CORS working!")
        else:
            print("   ❌ No CORS headers in copilot response")
            
    except Exception as e:
        print(f"   ❌ Copilot test error: {e}")

if __name__ == "__main__":
    test_cors()
'''
    
    import os
    os.makedirs("tests/manual", exist_ok=True)
    out_path = "tests/manual/test_cors_config.py"
    with open(out_path, "w") as f:
        f.write(script_content)
    
    print(f"📝 Created {out_path}")
    print("   Run this after restarting backend to verify CORS fix")

def main():
    fix_cors_for_frontend()
    test_cors_fix()
    create_cors_test_script()

if __name__ == "__main__":
    main()
