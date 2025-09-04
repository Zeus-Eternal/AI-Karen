#!/usr/bin/env python3
"""
Fix frontend issues and ensure proper connectivity
"""

import os
import sys
import subprocess
import time
import requests
import json
from pathlib import Path

def test_endpoint(url, method='GET', data=None, timeout=10):
    """Test an endpoint and return status"""
    try:
        if method == 'POST':
            response = requests.post(url, json=data, timeout=timeout)
        else:
            response = requests.get(url, timeout=timeout)
        return {
            'status': response.status_code,
            'success': response.status_code < 400,
            'response': response.text[:200] if response.text else ''
        }
    except Exception as e:
        return {
            'status': 0,
            'success': False,
            'error': str(e)
        }

def check_frontend_health():
    """Check if the frontend is running"""
    try:
        response = requests.get("http://localhost:8010", timeout=5)
        return response.status_code == 200
    except:
        return False

def main():
    print("🔧 Karen AI Frontend Fix Script")
    print("=" * 50)
    
    # Step 1: Check if frontend is running
    print("1. Checking frontend status...")
    if not check_frontend_health():
        print("❌ Frontend is not running on port 8010")
        print("   Please start the frontend with: cd ui_launchers/web_ui && npm run dev")
        return 1
    else:
        print("✅ Frontend is running on port 8010")
    
    # Step 2: Test backend connectivity through proxy
    print("\n2. Testing backend connectivity through proxy...")
    
    # Test health endpoint
    health_result = test_endpoint("http://localhost:8010/api/health")
    if health_result['success']:
        print("✅ Health endpoint working")
    else:
        print(f"❌ Health endpoint failed: {health_result.get('error', health_result['status'])}")
    
    # Test models endpoint
    models_result = test_endpoint("http://localhost:8010/api/models/library?quick=true")
    if models_result['success']:
        print("✅ Models endpoint working")
    else:
        print(f"❌ Models endpoint failed: {health_result.get('error', models_result['status'])}")
    
    # Test copilot endpoint
    copilot_result = test_endpoint(
        "http://localhost:8010/copilot/assist", 
        method='POST', 
        data={"message": "test"},
        timeout=30
    )
    if copilot_result['success']:
        print("✅ Copilot endpoint working")
    else:
        print(f"❌ Copilot endpoint failed: {copilot_result.get('error', copilot_result['status'])}")
    
    # Step 3: Test authentication
    print("\n3. Testing authentication...")
    
    # Test auth endpoint (expect validation error, but should respond)
    auth_result = test_endpoint(
        "http://localhost:8010/api/auth/login",
        method='POST',
        data={"username": "test", "password": "test"}
    )
    
    # 422 is expected for invalid credentials, 502 means backend connection issue
    if auth_result['status'] in [422, 400]:
        print("✅ Auth endpoint responding (validation error expected)")
    elif auth_result['status'] == 502:
        print("❌ Auth endpoint - backend connection issue")
    else:
        print(f"⚠️ Auth endpoint returned {auth_result['status']}")
    
    # Step 4: Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    
    endpoints = [
        ("Health", health_result),
        ("Models", models_result),
        ("Copilot", copilot_result),
        ("Auth", auth_result)
    ]
    
    all_working = True
    for name, result in endpoints:
        status = "✅" if result['success'] or (name == "Auth" and result['status'] in [422, 400]) else "❌"
        print(f"   • {name}: {status}")
        if not result['success'] and not (name == "Auth" and result['status'] in [422, 400]):
            all_working = False
    
    print("\n🌐 Access URLs:")
    print("   • Frontend: http://localhost:8010")
    print("   • Backend (direct): http://localhost:8000")
    print("   • Health Check: http://localhost:8010/api/health")
    print("   • Models: http://localhost:8010/api/models/library")
    print("   • Copilot: http://localhost:8010/copilot/assist")
    
    if all_working:
        print("\n🎉 All endpoints are working correctly!")
        print("💡 The frontend should now be able to communicate with the backend.")
        print("   Try refreshing the page and testing the chat functionality.")
    else:
        print("\n⚠️ Some endpoints are not working properly.")
        print("💡 Troubleshooting tips:")
        print("   • Make sure the backend server is running on port 8000")
        print("   • Check the server logs for any errors")
        print("   • Ensure the virtual environment is activated")
        print("   • Try restarting both frontend and backend")
    
    return 0 if all_working else 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n🛑 Script interrupted by user")
        sys.exit(1)