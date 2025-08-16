"""
Kari Diagnostics Logic (Production)
- Gathers health metrics, error traces, subsystem pings
- Reports CPU, RAM, disk, GPU, service status, and system uptime
- Zero UI dependencies; pure backend logic
"""

import psutil
import platform
import socket
import time
from typing import Dict, Any, Optional

from ui_logic.utils.api import ping_services
from ai_karen_engine.integrations.provider_status import collect_provider_statuses
from ai_karen_engine.integrations.diagnostic_prompt import make_admin_diagnostic_prompt

def get_system_diagnostics() -> Dict[str, Any]:
    """
    Returns system health/metrics for the dashboard.
    Robust: Always returns all fields, handles exceptions gracefully.
    """
    info = {}
    # --- Core system stats ---
    try:
        info["hostname"] = socket.gethostname()
        info["platform"] = platform.system()
        info["platform_release"] = platform.release()
        info["platform_version"] = platform.version()
        info["arch"] = platform.machine()
        info["python_version"] = platform.python_version()
        info["cpu_percent"] = psutil.cpu_percent(interval=0.5)
        info["num_cores"] = psutil.cpu_count(logical=True)
        info["load_avg"] = list(psutil.getloadavg()) if hasattr(psutil, "getloadavg") else []
        mem = psutil.virtual_memory()
        info["mem_percent"] = mem.percent
        info["mem_used_mb"] = int(mem.used / (1024 ** 2))
        info["mem_total_mb"] = int(mem.total / (1024 ** 2))
        disk = psutil.disk_usage("/")
        info["disk_percent"] = disk.percent
        info["disk_used_gb"] = round(disk.used / (1024 ** 3), 2)
        info["disk_total_gb"] = round(disk.total / (1024 ** 3), 2)
        info["disk_free_gb"] = round(disk.free / (1024 ** 3), 2)
        info["boot_time"] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(psutil.boot_time()))
        info["uptime_seconds"] = int(time.time() - psutil.boot_time())
    except Exception as e:
        info["diagnostics_error"] = f"System stats error: {e}"

    # --- GPU stats (optional, never fails build) ---
    try:
        import GPUtil
        gpus = GPUtil.getGPUs()
        info["gpus"] = [
            {
                "id": gpu.id,
                "name": gpu.name,
                "load_percent": round(gpu.load * 100, 2),
                "mem_total_mb": gpu.memoryTotal,
                "mem_used_mb": gpu.memoryUsed,
                "mem_free_mb": gpu.memoryFree,
                "temperature": gpu.temperature,
            }
            for gpu in gpus
        ]
        info["gpu_support"] = True
    except ImportError:
        info["gpus"] = []
        info["gpu_support"] = False
    except Exception as e:
        info["gpus"] = []
        info["gpu_error"] = str(e)
        info["gpu_support"] = False

    # --- Services ping (API, DB, LLM, etc) ---
    try:
        info["services"] = ping_services()
    except Exception as e:
        info["services"] = {"error": f"Service ping failed: {e}"}

    # LLM provider statuses
    try:
        statuses = collect_provider_statuses()
        info["llm_providers"] = statuses
        info["llm_prompt"] = make_admin_diagnostic_prompt(statuses)
    except Exception as e:
        info["llm_providers_error"] = str(e)

    # --- Network info (IP, safe subset) ---
    try:
        info["ip_address"] = socket.gethostbyname(socket.gethostname())
    except Exception:
        info["ip_address"] = "Unknown"

    return info

def run_diagnostics_check(check: Optional[str] = None) -> Dict[str, Any]:
    """
    Runs a focused diagnostic check (e.g., 'cpu', 'memory', 'disk', 'gpu', 'services').
    If check is None, returns full diagnostics.
    """
    if check is None:
        return get_system_diagnostics()
    result = {}
    try:
        if check == "cpu":
            result["cpu_percent"] = psutil.cpu_percent(interval=0.5)
            result["num_cores"] = psutil.cpu_count(logical=True)
            result["load_avg"] = list(psutil.getloadavg()) if hasattr(psutil, "getloadavg") else []
        elif check == "memory":
            mem = psutil.virtual_memory()
            result["mem_percent"] = mem.percent
            result["mem_used_mb"] = int(mem.used / (1024 ** 2))
            result["mem_total_mb"] = int(mem.total / (1024 ** 2))
        elif check == "disk":
            disk = psutil.disk_usage("/")
            result["disk_percent"] = disk.percent
            result["disk_used_gb"] = round(disk.used / (1024 ** 3), 2)
            result["disk_total_gb"] = round(disk.total / (1024 ** 3), 2)
            result["disk_free_gb"] = round(disk.free / (1024 ** 3), 2)
        elif check == "gpu":
            try:
                import GPUtil
                gpus = GPUtil.getGPUs()
                result["gpus"] = [
                    {
                        "id": gpu.id,
                        "name": gpu.name,
                        "load_percent": round(gpu.load * 100, 2),
                        "mem_total_mb": gpu.memoryTotal,
                        "mem_used_mb": gpu.memoryUsed,
                        "mem_free_mb": gpu.memoryFree,
                        "temperature": gpu.temperature,
                    }
                    for gpu in gpus
                ]
                result["gpu_support"] = True
            except ImportError:
                result["gpus"] = []
                result["gpu_support"] = False
            except Exception as e:
                result["gpus"] = []
                result["gpu_error"] = str(e)
                result["gpu_support"] = False
        elif check == "services":
            result["services"] = ping_services()
        else:
            result["error"] = f"Unknown diagnostic check: {check}"
    except Exception as e:
        result["diagnostics_error"] = str(e)
    return result

__all__ = ["get_system_diagnostics", "run_diagnostics_check"]
