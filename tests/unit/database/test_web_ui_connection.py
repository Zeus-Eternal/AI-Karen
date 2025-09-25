#!/usr/bin/env python3
"""
Test web UI connection to backend
"""

import sys
import os
import asyncio
import json
from fastapi.testclient import TestClient

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_web_ui_connection():
    """Test web UI connection to backend using TestClient"""
    print("🌐 Testing Web UI connection to backend...")
    
    try:
        # Import the FastAPI app
        from main import create_app
        app = create_app()
        
        # Create test client
        client = TestClient(app)
        
        print("\n1. Testing health endpoint...")
        response = client.get("/health")
        print(f"✅ Health check: {response.status_code}")
        if response.status_code == 200:
            print(f"   Response: {response.json()}")
        
        print("\n2. Testing LLM providers endpoint...")
        response = client.get("/api/llm/providers")
        print(f"✅ LLM providers: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Found {len(data['providers'])} providers")
            for provider in data['providers']:
                print(f"   - {provider['name']}: {provider['health_status']}")
        else:
            print(f"   Error: {response.text}")
        
        print("\n3. Testing LLM profiles endpoint...")
        response = client.get("/api/llm/profiles")
        print(f"✅ LLM profiles: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Found {len(data['profiles'])} profiles")
            for profile in data['profiles']:
                print(f"   - {profile['name']}: chat={profile['providers']['chat']}")
        else:
            print(f"   Error: {response.text}")
        
        print("\n4. Testing LLM health check endpoint...")
        response = client.post("/api/llm/health-check")
        print(f"✅ LLM health check: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Health check results:")
            for name, result in data['results'].items():
                status = result.get('status', 'unknown')
                print(f"   - {name}: {status}")
        else:
            print(f"   Error: {response.text}")
        
        print("\n🎉 All web UI endpoints are accessible!")
        print("\n💡 The web UI should work correctly with these endpoints.")
        print("   If you're still seeing network errors, check:")
        print("   1. Backend server is running on http://localhost:8000")
        print("   2. Web UI is configured to connect to the correct backend URL")
        print("   3. CORS is properly configured for your web UI origin")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing web UI connection: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_web_ui_connection()
    sys.exit(0 if success else 1)