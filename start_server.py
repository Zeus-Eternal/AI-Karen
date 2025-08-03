#!/usr/bin/env python3
"""
AI Karen Backend Server Startup Script
This script properly starts the FastAPI server with uvicorn
"""

import os
import sys
import subprocess
import signal
import time
from pathlib import Path
from typing import Optional

def check_virtual_env() -> bool:
    """Check if we're in the correct virtual environment"""
    venv_path = Path(".env_ai")
    if not venv_path.exists():
        print("❌ Virtual environment .env_ai not found!")
        print("Please create it first: python -m venv .env_ai")
        return False
    
    # More reliable virtual environment check
    if (os.environ.get('VIRTUAL_ENV', '').endswith('.env_ai') or sys.prefix.endswith('.env_ai')):
        return True
    
    print("⚠️ Not in virtual environment. Activating...")
    return False

def check_dependencies() -> bool:
    """Check if required dependencies are installed"""
    required = ['uvicorn', 'fastapi']
    missing = []
    
    for package in required:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"❌ Missing dependencies: {', '.join(missing)}")
        print("Please install dependencies: pip install -r requirements.txt")
        return False
    
    print("✅ All required dependencies found")
    return True

def get_local_ips() -> list[str]:
    """Get local IP addresses for display"""
    import socket
    ips = []
    try:
        hostname = socket.gethostname()
        ips.append(f"http://{hostname}:{port}")
        ips.append("http://localhost:8000")
        ips.append("http://127.0.0.1:8000")
        ips.append("http://0.0.0.0:8000")
    except:
        ips = [
            "http://localhost:8000",
            "http://127.0.0.1:8000",
            "http://0.0.0.0:8000"
        ]
    return ips

def start_server() -> bool:
    """Start the FastAPI server with uvicorn"""
    print("🚀 Starting AI Karen Backend Server...")
    
    # Server configuration
    host = os.getenv("HOST", "0.0.0.0")  # Bind to all interfaces
    port = int(os.getenv("PORT", "8000"))
    app = "main:create_app"
    
    print(f"📍 Server will be available at:")
    for url in get_local_ips():
        print(f"   - {url}")
    
    # Start uvicorn
    try:
        import uvicorn
        print(f"\n🔧 Starting uvicorn server...")
        print(f"   Host: {host}")
        print(f"   Port: {port}")
        print(f"   App: {app}")
        print(f"   Reload: True (development mode)")
        print("-" * 50)
        
        # Start the server with more configuration options
        uvicorn.run(
            app,
            host=host,
            port=port,
            reload=True,
            log_level="info",
            access_log=True,
            workers=1,  # Explicitly set workers for development
            reload_dirs=["."] if os.getenv("ENV") == "development" else None,
            factory=True,
        )
        
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Server failed to start: {str(e)}", file=sys.stderr)
        return False
    
    return True

def main() -> None:
    """Main function to start the server"""
    print("\n🔍 AI Karen Backend Server Startup")
    print("=" * 50)
    
    # Check if main.py exists
    if not Path("main.py").exists():
        print("❌ main.py not found! Please run this script from the project root.", file=sys.stderr)
        sys.exit(1)
    
    # Check virtual environment
    if not check_virtual_env():
        print("\n💡 To activate virtual environment:")
        print("  On Unix/Linux: source .env_ai/bin/activate")
        print("  On Windows: .env_ai\\Scripts\\activate")
        print("\nThen run this script again.")
        sys.exit(1)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Start the server
    print("\n🚀 Starting server...")
    print("Press Ctrl+C to stop the server")
    print("-" * 50)
    
    if not start_server():
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n🔥 Unexpected error: {str(e)}", file=sys.stderr)
        sys.exit(1)