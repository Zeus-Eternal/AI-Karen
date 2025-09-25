#!/usr/bin/env python3
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
    print("\n1. Testing CORS preflight...")
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
    print("\n2. Testing health endpoint...")
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
    print("\n3. Testing copilot endpoint...")
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

