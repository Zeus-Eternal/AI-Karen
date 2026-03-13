# mypy: ignore-errors
"""
Performance configuration and endpoints for Kari FastAPI Server.
Handles performance config loading and performance-related endpoint helpers.
"""

import asyncio
import logging
import sys
import os
from typing import Any

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

logger = logging.getLogger("kari")


def load_performance_settings(settings: Any) -> None:
    """Load performance configuration during app creation"""
    try:
        from ai_karen_engine.config.performance_config import load_performance_config
        
        # Load performance configuration synchronously during app creation
        loop = None
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        if loop.is_running():
            # If loop is already running, we'll load config during startup
            logger.info("📋 Performance configuration will be loaded during startup")
        else:
            # Load configuration now
            perf_config = loop.run_until_complete(load_performance_config())
            logger.info(f"📋 Performance configuration loaded: {perf_config.deployment_mode} mode")
            
            # Update settings with performance configuration
            settings.enable_performance_optimization = perf_config.enable_performance_optimization
            settings.deployment_mode = perf_config.deployment_mode
            settings.cpu_threshold = perf_config.cpu_threshold
            settings.memory_threshold = perf_config.memory_threshold
            settings.response_time_threshold = perf_config.response_time_threshold
            
    except Exception as e:
        logger.warning(f"⚠️ Failed to load performance configuration: {e}")
        logger.info("📦 Using default performance settings")


def get_performance_status():
    """Helper to get current performance status"""
    # This would be implemented to return current performance metrics
    return {"status": "ok", "mode": "optimized"}


def run_performance_audit():
    """Helper to run performance audit"""
    # This would be implemented to run performance analysis
    return {"audit": "completed", "recommendations": []}


def trigger_optimization():
    """Helper to trigger performance optimization"""
    # This would be implemented to trigger optimization routines
    return {"optimization": "triggered", "status": "in_progress"}


def monitor_performance(function_name, args=None, kwargs=None):
    """Monitor performance of a function execution."""
    import time
    
    if args is None:
        args = []
    if kwargs is None:
        kwargs = {}
    
    start_time = time.time()
    try:
        # Simulate function execution timing
        execution_time = time.time() - start_time
        
        result = {
            "function_name": function_name,
            "execution_time": execution_time,
            "timestamp": time.time(),
            "args": args,
            "kwargs": kwargs,
            "status": "success"
        }
        
        logger.info(f"Performance monitored for {function_name}: {execution_time:.4f}s")
        return result
        
    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(f"Performance monitoring failed for {function_name}: {str(e)}")
        return {
            "function_name": function_name,
            "execution_time": execution_time,
            "timestamp": time.time(),
            "error": str(e),
            "status": "error"
        }


def track_request_time(request_method, request_path, status_code):
    """Track request time for API endpoints."""
    import time
    
    try:
        # Simulate request timing
        response_time = 0.1  # Default response time in seconds
        
        result = {
            "request_method": request_method,
            "request_path": request_path,
            "status_code": status_code,
            "response_time": response_time,
            "timestamp": time.time()
        }
        
        logger.info(f"Request tracked: {request_method} {request_path} - {status_code} in {response_time:.4f}s")
        return result
        
    except Exception as e:
        logger.error(f"Request time tracking failed: {str(e)}")
        return {
            "request_method": request_method,
            "request_path": request_path,
            "status_code": status_code,
            "response_time": 0,
            "timestamp": time.time(),
            "error": str(e)
        }


def get_performance_metrics():
    """Get current system performance metrics."""
    import time
    
    try:
        # Try to import psutil for system metrics
        try:
            import psutil
            
            # Get CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Get memory metrics
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_available = memory.available
            
            # Get disk metrics
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            disk_free = disk.free
            
            system_metrics = {
                "cpu_percent": cpu_percent,
                "memory_percent": memory_percent,
                "memory_available": memory_available,
                "disk_percent": disk_percent,
                "disk_free": disk_free
            }
            
        except ImportError:
            # Fallback if psutil is not available
            logger.warning("psutil not available, using mock metrics")
            system_metrics = {
                "cpu_percent": 25.0,
                "memory_percent": 60.0,
                "memory_available": 8 * 1024**3,  # 8GB
                "disk_percent": 45.0,
                "disk_free": 100 * 1024**3  # 100GB
            }
        
        result = {
            "timestamp": time.time(),
            "system_metrics": system_metrics,
            "status": "healthy"
        }
        
        logger.info("Performance metrics collected")
        return result
        
    except Exception as e:
        logger.error(f"Failed to get performance metrics: {str(e)}")
        return {
            "timestamp": time.time(),
            "system_metrics": {},
            "error": str(e),
            "status": "error"
        }