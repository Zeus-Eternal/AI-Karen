#!/usr/bin/env python3
"""
AI Karen Backend Runner
Robust script to start and manage the FastAPI backend server
"""

import os
import sys
import subprocess
import signal
from pathlib import Path
from typing import List, Optional

class BackendRunner:
    def __init__(self):
        self.process: Optional[subprocess.Popen] = None
        self.venv_path = Path(".env_ai")
        self.host = os.getenv("HOST", "0.0.0.0")
        self.port = os.getenv("PORT", "8000")
        self.web_ui_url = os.getenv("WEB_UI_URL", "http://localhost:9002")

    def check_environment(self) -> bool:
        """Verify all required environment conditions"""
        if not self._check_project_root():
            return False
        if not self._check_virtualenv():
            return False
        if not self._check_dependencies():
            return False
        return True

    def _check_project_root(self) -> bool:
        """Ensure we're in the project root directory"""
        if not Path("main.py").exists():
            print("❌ main.py not found! Run this from the project root directory.")
            return False
        return True

    def _check_virtualenv(self) -> bool:
        """Verify virtual environment exists"""
        if not self.venv_path.exists():
            print("❌ Virtual environment .env_ai not found!")
            print("Create it with: python -m venv .env_ai")
            print("Then activate and install dependencies:")
            print("source .env_ai/bin/activate && pip install -r requirements.txt")
            return False
        return True

    def _check_dependencies(self) -> bool:
        """Check required dependencies are installed"""
        uvicorn_exe = self._get_venv_executable("uvicorn")
        if not uvicorn_exe.exists():
            print(f"❌ Uvicorn not found at {uvicorn_exe}")
            print("Install it with: source .env_ai/bin/activate && pip install uvicorn")
            return False
        return True

    def _get_venv_executable(self, name: str) -> Path:
        """Get path to executable in virtual environment"""
        if sys.platform == "win32":
            return self.venv_path / "Scripts" / f"{name}.exe"
        return self.venv_path / "bin" / name

    def _get_server_urls(self) -> List[str]:
        """Return list of server URLs"""
        base_urls = [
            f"http://localhost:{self.port}",
            f"http://127.0.0.1:{self.port}",
            f"http://{self.host}:{self.port}"
        ]
        
        try:
            import socket
            hostname = socket.gethostname()
            base_urls.append(f"http://{hostname}:{self.port}")
        except:
            pass
            
        return base_urls

    def start_server(self) -> None:
        """Start the backend server"""
        print("🚀 Starting AI Karen Backend Server...")
        print("📍 Server will be available at:")
        for url in self._get_server_urls():
            print(f"   - {url}")
        print(f"🔧 CORS configured for {self.web_ui_url} (Web UI)")
        print("⏹️  Press Ctrl+C to stop the server")
        print("-" * 60)

        uvicorn_exe = self._get_venv_executable("uvicorn")
        cmd = [
            str(uvicorn_exe),
            "main:app",
            "--host", self.host,
            "--port", self.port,
            "--reload",
            "--log-level", "info"
        ]

        try:
            self.process = subprocess.Popen(cmd)
            self.process.wait()
        except KeyboardInterrupt:
            self.stop_server()
        except Exception as e:
            print(f"❌ Server failed to start: {e}", file=sys.stderr)
            sys.exit(1)

    def stop_server(self) -> None:
        """Stop the running server"""
        if self.process:
            print("\n🛑 Stopping server...")
            if sys.platform == "win32":
                self.process.send_signal(signal.CTRL_C_EVENT)
            else:
                self.process.send_signal(signal.SIGINT)
            self.process.wait()
            print("Server stopped")

def main():
    runner = BackendRunner()
    
    if not runner.check_environment():
        sys.exit(1)
        
    try:
        runner.start_server()
    except Exception as e:
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()