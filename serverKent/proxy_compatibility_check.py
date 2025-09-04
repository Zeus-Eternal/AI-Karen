#!/usr/bin/env python3
print("[DEPRECATED] Proxy compatibility check is deprecated.", flush=True)
raise SystemExit(1)
"""
Proxy compatibility check and upgrade system for codeKent.
Handles backend service detection, proxy configuration, and fallback routing.
"""

import json
import requests
import subprocess
import time
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class ProxyCompatibilityChecker:
    """Check and upgrade proxy configurations for codeKent services."""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.services = {
            "backend": {"port": 8000, "path": "/health"},
            "websocket": {"port": 8000, "path": "/ws"},
            "cpp_llama": {"port": 8080, "path": "/health"},
            "vite": {"port": 3000, "path": "/"}
        }
        self.vite_config_path = self.project_root / "vite.config.ts"
        
    def check_service_health(self, service: str) -> Tuple[bool, str]:
        """Check if a service is running and healthy."""
        config = self.services.get(service)
        if not config:
            return False, f"Unknown service: {service}"
        
        try:
            url = f"http://127.0.0.1:{config['port']}{config['path']}"
            response = requests.get(url, timeout=2)
            if response.status_code == 200:
                return True, f"Service {service} is healthy"
            else:
                return False, f"Service {service} returned status {response.status_code}"
        except requests.exceptions.ConnectionError:
            return False, f"Service {service} is not running (connection refused)"
        except requests.exceptions.Timeout:
            return False, f"Service {service} timed out"
        except Exception as e:
            return False, f"Service {service} error: {str(e)}"
    
    def get_vite_proxy_config(self) -> Dict:
        """Generate optimal Vite proxy configuration."""
        backend_healthy, _ = self.check_service_health("backend")
        cpp_llama_healthy, _ = self.check_service_health("cpp_llama")
        
        proxy_config = {}
        
        # Backend API routes
        if backend_healthy:
            proxy_config.update({
                "/v2": {
                    "target": "http://127.0.0.1:8000",
                    "changeOrigin": True,
                    "ws": True,
                    "timeout": 30000,
                    "proxyTimeout": 30000
                },
                "/ws": {
                    "target": "http://127.0.0.1:8000",
                    "changeOrigin": True,
                    "ws": True
                },
                "/api": {
                    "target": "http://127.0.0.1:8000",
                    "changeOrigin": True,
                    "ws": True
                }
            })
        else:
            # Fallback to mock responses
            proxy_config.update({
                "/v2": {
                    "target": "http://127.0.0.1:3001",  # Mock server
                    "changeOrigin": True,
                    "configure": "(proxy, options) => { proxy.on('error', () => console.warn('Backend offline, using fallback')); }"
                }
            })
        
        # cpp-llama routes
        if cpp_llama_healthy:
            proxy_config["/v1"] = {
                "target": "http://127.0.0.1:8080",
                "changeOrigin": True,
                "timeout": 60000,
                "proxyTimeout": 60000
            }
        
        return proxy_config
    
    def update_vite_config(self) -> bool:
        """Update Vite configuration with optimal proxy settings."""
        if not self.vite_config_path.exists():
            print(f"Vite config not found at {self.vite_config_path}")
            return False
        
        try:
            # Read current config
            with open(self.vite_config_path, 'r') as f:
                content = f.read()
            
            # Generate new proxy config
            proxy_config = self.get_vite_proxy_config()
            proxy_json = json.dumps(proxy_config, indent=4)
            
            # Create updated config
            new_config = f'''import {{ defineConfig }} from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({{
  plugins: [react()],
  server: {{
    port: 3000,
    host: true,
    proxy: {proxy_json.replace('"', "'")}
  }},
  build: {{
    outDir: 'dist',
    sourcemap: true
  }}
}})
'''
            
            # Backup original
            backup_path = self.vite_config_path.with_suffix('.ts.backup')
            if not backup_path.exists():
                with open(backup_path, 'w') as f:
                    f.write(content)
            
            # Write new config
            with open(self.vite_config_path, 'w') as f:
                f.write(new_config)
            
            print(f"✅ Updated Vite proxy configuration")
            return True
            
        except Exception as e:
            print(f"❌ Failed to update Vite config: {e}")
            return False
    
    def start_mock_server(self) -> bool:
        """Start a mock server for offline development."""
        mock_server_path = self.project_root / "scripts" / "mock_server.py"
        
        if not mock_server_path.exists():
            self.create_mock_server()
        
        try:
            subprocess.Popen([
                sys.executable, str(mock_server_path)
            ], cwd=self.project_root)
            time.sleep(2)  # Give it time to start
            return True
        except Exception as e:
            print(f"❌ Failed to start mock server: {e}")
            return False
    
    def create_mock_server(self):
        """Create a simple mock server for development."""
        mock_server_content = '''#!/usr/bin/env python3
"""Mock server for codeKent development when backend is offline."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(title="codeKent Mock Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {"status": "ok", "mode": "mock"}

@app.get("/v2/providers")
async def providers():
    return {
        "providers": {
            "mock": [["mock-model", "Mock Model"]]
        }
    }

@app.post("/v2/chat/completions")
async def chat_completions():
    return {
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": "Mock response - backend is offline"
            }
        }]
    }

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=3001)
'''
        
        mock_path = self.project_root / "scripts" / "mock_server.py"
        mock_path.parent.mkdir(exist_ok=True)
        
        with open(mock_path, 'w') as f:
            f.write(mock_server_content)
        
        mock_path.chmod(0o755)
        print(f"✅ Created mock server at {mock_path}")
    
    def run_full_check(self) -> Dict[str, any]:
        """Run complete compatibility check and upgrade."""
        results = {
            "services": {},
            "proxy_updated": False,
            "mock_started": False,
            "recommendations": []
        }
        
        print("🔍 Running proxy compatibility check...")
        
        # Check all services
        for service in self.services:
            healthy, message = self.check_service_health(service)
            results["services"][service] = {
                "healthy": healthy,
                "message": message
            }
            
            if healthy:
                print(f"✅ {message}")
            else:
                print(f"❌ {message}")
        
        # Update proxy configuration
        if self.update_vite_config():
            results["proxy_updated"] = True
        
        # Start mock server if backend is down
        backend_healthy = results["services"]["backend"]["healthy"]
        if not backend_healthy:
            print("🚀 Starting mock server for offline development...")
            if self.start_mock_server():
                results["mock_started"] = True
                results["recommendations"].append("Mock server started on port 3001")
        
        # Generate recommendations
        if not backend_healthy:
            results["recommendations"].extend([
                "Start the Python backend: python -m uvicorn src.app.codeKent:app --reload",
                "Check Python environment: source .env_kent/bin/activate",
                "Verify imports: python -c 'from src.app.codeKent import app'"
            ])
        
        cpp_llama_healthy = results["services"]["cpp_llama"]["healthy"]
        if not cpp_llama_healthy:
            results["recommendations"].extend([
                "Start cpp-llama server: ~/.kiro/cpp-llama/start_server.sh",
                "Build cpp-llama: ./scripts/setup_cpp_llama.sh",
                "Check cpp-llama health: ~/.kiro/cpp-llama/health_check.sh"
            ])
        
        return results


def main():
    """Main entry point for proxy compatibility check."""
    import argparse
    
    parser = argparse.ArgumentParser(description="codeKent Proxy Compatibility Check")
    parser.add_argument("--project-root", default=".", help="Project root directory")
    parser.add_argument("--update-only", action="store_true", help="Only update proxy config")
    parser.add_argument("--mock-only", action="store_true", help="Only start mock server")
    
    args = parser.parse_args()
    
    checker = ProxyCompatibilityChecker(args.project_root)
    
    if args.update_only:
        checker.update_vite_config()
        return
    
    if args.mock_only:
        checker.start_mock_server()
        return
    
    # Run full check
    results = checker.run_full_check()
    
    print("\n📊 Summary:")
    print(f"Services checked: {len(results['services'])}")
    print(f"Proxy updated: {results['proxy_updated']}")
    print(f"Mock server started: {results['mock_started']}")
    
    if results["recommendations"]:
        print("\n💡 Recommendations:")
        for rec in results["recommendations"]:
            print(f"  • {rec}")
    
    # Exit with error code if critical services are down
    backend_healthy = results["services"]["backend"]["healthy"]
    if not backend_healthy and not results["mock_started"]:
        print("\n⚠️  Critical: Backend service is down and mock server failed to start")
        sys.exit(1)
    
    print("\n✅ Proxy compatibility check complete!")


if __name__ == "__main__":
    main()
