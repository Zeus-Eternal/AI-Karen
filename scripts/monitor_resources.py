#!/usr/bin/env python3
"""
Resource monitor for AI-Karen services.
Shows real-time resource usage and service status.
"""

import asyncio
import time
import os
import sys
from pathlib import Path
from typing import Dict, Any

# Add the project root to Python path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("⚠️  psutil not available - limited monitoring")


class ServiceMonitor:
    """Monitor AI-Karen services and resource usage."""
    
    def __init__(self):
        self.process = None
        if PSUTIL_AVAILABLE:
            try:
                self.process = psutil.Process()
            except:
                pass
    
    def get_memory_usage(self) -> Dict[str, Any]:
        """Get memory usage information."""
        if not PSUTIL_AVAILABLE or not self.process:
            return {"available": False}
        
        try:
            memory_info = self.process.memory_info()
            memory_percent = self.process.memory_percent()
            
            return {
                "available": True,
                "rss_mb": memory_info.rss / 1024 / 1024,
                "vms_mb": memory_info.vms / 1024 / 1024,
                "percent": memory_percent,
                "status": "high" if memory_percent > 10 else "normal"
            }
        except:
            return {"available": False}
    
    def get_cpu_usage(self) -> Dict[str, Any]:
        """Get CPU usage information."""
        if not PSUTIL_AVAILABLE:
            return {"available": False}
        
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            
            return {
                "available": True,
                "percent": cpu_percent,
                "status": "high" if cpu_percent > 50 else "normal"
            }
        except:
            return {"available": False}
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get status of lazy services if available."""
        try:
            # Try to import the lazy registry
            from ai_karen_engine.core.lazy_loading import lazy_registry
            
            if hasattr(lazy_registry, 'list_services'):
                services = lazy_registry.list_services()
                return {
                    "available": True,
                    "services": services,
                    "count": len(services)
                }
        except:
            pass
        
        return {"available": False}
    
    def print_status(self):
        """Print current status."""
        print("\n" + "="*60)
        print("🔍 AI-Karen Resource Monitor")
        print("="*60)
        
        # Memory usage
        memory = self.get_memory_usage()
        if memory["available"]:
            status_icon = "🔴" if memory["status"] == "high" else "🟢"
            print(f"{status_icon} Memory: {memory['rss_mb']:.1f} MB ({memory['percent']:.1f}%)")
        else:
            print("⚪ Memory: Not available")
        
        # CPU usage
        cpu = self.get_cpu_usage()
        if cpu["available"]:
            status_icon = "🔴" if cpu["status"] == "high" else "🟢"
            print(f"{status_icon} CPU: {cpu['percent']:.1f}%")
        else:
            print("⚪ CPU: Not available")
        
        # Service status
        services = self.get_service_status()
        if services["available"]:
            print(f"🔧 Services: {services['count']} registered")
            
            for name, info in services["services"].items():
                state_icon = {
                    "ready": "🟢",
                    "idle": "🟡", 
                    "uninitialized": "⚪",
                    "error": "🔴",
                    "shutdown": "⚫"
                }.get(info["state"], "❓")
                
                print(f"   {state_icon} {name}: {info['state']}")
                if info["is_initialized"]:
                    print(f"      Used {info['usage_count']} times")
        else:
            print("⚪ Services: Status not available")
        
        # Environment info
        print(f"\n⚙️  Environment:")
        print(f"   Lazy loading: {os.getenv('KARI_LAZY_LOADING', 'false')}")
        print(f"   Minimal mode: {os.getenv('KARI_MINIMAL_MODE', 'false')}")
        print(f"   Ultra minimal: {os.getenv('KARI_ULTRA_MINIMAL', 'false')}")
        
        print(f"\n🕐 {time.strftime('%H:%M:%S')}")


async def monitor_loop():
    """Main monitoring loop."""
    monitor = ServiceMonitor()
    
    print("🚀 Starting AI-Karen Resource Monitor")
    print("Press Ctrl+C to stop")
    
    try:
        while True:
            os.system('clear' if os.name == 'posix' else 'cls')
            monitor.print_status()
            await asyncio.sleep(5)
    except KeyboardInterrupt:
        print("\n\n🛑 Monitor stopped")


def main():
    """Main entry point."""
    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        # Single status check
        monitor = ServiceMonitor()
        monitor.print_status()
    else:
        # Continuous monitoring
        asyncio.run(monitor_loop())


if __name__ == "__main__":
    main()
