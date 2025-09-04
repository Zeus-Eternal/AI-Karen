#!/usr/bin/env python3
"""
Fix server issues and ensure stable operation
"""

import os
import sys
import subprocess
import time
import requests
import signal
from pathlib import Path

def check_server_health():
    """Check if the server is responding"""
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def check_frontend_health():
    """Check if the frontend is responding"""
    try:
        response = requests.get("http://localhost:8010/api/health", timeout=10)
        return response.status_code == 200
    except:
        return False

def kill_existing_servers():
    """Kill any existing server processes"""
    try:
        # Kill Python processes running main.py
        subprocess.run(["pkill", "-f", "main.py"], check=False)
        time.sleep(2)
    except:
        pass

def start_backend_server():
    """Start the backend server"""
    print("🚀 Starting backend server...")
    
    # Ensure we're in the right directory
    os.chdir("/media/zeus/Development7/KIRO/AI-Karen")
    
    # Activate virtual environment and start server
    env = os.environ.copy()
    env["PATH"] = "/media/zeus/Development7/KIRO/AI-Karen/.karen_env/bin:" + env["PATH"]
    
    # Start server in background
    process = subprocess.Popen(
        ["/media/zeus/Development7/KIRO/AI-Karen/.karen_env/bin/python", "main.py"],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    
    # Wait for server to start
    print("⏳ Waiting for backend server to start...")
    for i in range(30):  # Wait up to 30 seconds
        if check_server_health():
            print("✅ Backend server is healthy!")
            return process
        time.sleep(1)
        print(f"   Waiting... ({i+1}/30)")
    
    print("❌ Backend server failed to start properly")
    return None

def check_frontend_proxy():
    """Check if the frontend proxy is working"""
    print("🔍 Testing frontend proxy...")
    
    # Test health endpoint through proxy
    if check_frontend_health():
        print("✅ Frontend proxy is working!")
        return True
    else:
        print("❌ Frontend proxy is not working")
        return False

def main():
    print("🔧 Karen AI Server Fix Script")
    print("=" * 50)
    
    # Step 1: Kill existing servers
    print("1. Cleaning up existing processes...")
    kill_existing_servers()
    
    # Step 2: Start backend server
    print("\n2. Starting backend server...")
    backend_process = start_backend_server()
    
    if not backend_process:
        print("❌ Failed to start backend server")
        return 1
    
    # Step 3: Test frontend proxy
    print("\n3. Testing frontend proxy...")
    time.sleep(2)  # Give a moment for everything to settle
    
    if not check_frontend_proxy():
        print("❌ Frontend proxy test failed")
        return 1
    
    # Step 4: Test specific endpoints
    print("\n4. Testing specific endpoints...")
    
    try:
        # Test models endpoint
        response = requests.get("http://localhost:8010/api/models/library?quick=true", timeout=10)
        if response.status_code == 200:
            print("✅ Models endpoint working")
        else:
            print(f"⚠️ Models endpoint returned {response.status_code}")
    except Exception as e:
        print(f"❌ Models endpoint failed: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Server fix completed!")
    print("📊 Status Summary:")
    print(f"   • Backend Server: {'✅ Running' if check_server_health() else '❌ Not responding'}")
    print(f"   • Frontend Proxy: {'✅ Working' if check_frontend_proxy() else '❌ Not working'}")
    print("\n🌐 Access URLs:")
    print("   • Frontend: http://localhost:8010")
    print("   • Backend: http://localhost:8000")
    print("   • Health Check: http://localhost:8010/api/health")
    print("\n💡 Tips:")
    print("   • If issues persist, check the server logs")
    print("   • Make sure the virtual environment is activated")
    print("   • Ensure all dependencies are installed")
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n🛑 Script interrupted by user")
        sys.exit(1)