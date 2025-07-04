"""
Kari Diagnostics Logic
- Gathers health metrics, error traces, subsystem pings
- Reports CPU, RAM, disk, GPU, service status
"""

import psutil
from typing import Dict, Any
from ui.utils.api import ping_services

def get_system_diagnostics() -> Dict[str, Any]:
    """Returns system health/metrics for the dashboard."""
    return {
        "cpu_percent": psutil.cpu_percent(),
        "mem_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage("/").percent,
        "uptime": psutil.boot_time(),
        "services": ping_services()
    }
