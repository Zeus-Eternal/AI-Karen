#!/usr/bin/env python3
"""
Production Server Startup Script

This script handles graceful server startup with proper port management,
health checks, and production-ready configuration.
"""

import os
import sys
import time
import signal
import psutil
import subprocess
from pathlib import Path

# Load environment variables first
from dotenv import load_dotenv
load_dotenv()

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def find_process_using_port(port: int):
    """Find process using the specified port"""
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            for conn in proc.connections():
                if conn.laddr.port == port:
                    return proc
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return None


def kill_existing_server(port: int = 8000):
    """Kill existing server on the specified port"""
    proc = find_process_using_port(port)
    if proc:
        logger.info(f"Found existing process on port {port}: PID {proc.pid}")
        try:
            # Try graceful shutdown first
            proc.terminate()
            proc.wait(timeout=10)
            logger.info(f"Gracefully terminated process {proc.pid}")
        except psutil.TimeoutExpired:
            # Force kill if graceful shutdown fails
            proc.kill()
            logger.info(f"Force killed process {proc.pid}")
        except Exception as e:
            logger.error(f"Error killing process: {e}")
            return False
    return True


def check_dependencies():
    """Check if all required dependencies are available"""
    logger.info("🔍 Checking dependencies...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        logger.error("Python 3.8+ required")
        return False
    
    # Check required directories
    required_dirs = ["data", "logs", "models", "config"]
    for dir_name in required_dirs:
        dir_path = Path(dir_name)
        if not dir_path.exists():
            logger.info(f"Creating directory: {dir_name}")
            dir_path.mkdir(parents=True, exist_ok=True)
    
    # Check environment variables
    required_env_vars = [
        "SECRET_KEY",
        "AUTH_SECRET_KEY",
        "DATABASE_URL",
        "POSTGRES_URL",
        "AUTH_DATABASE_URL"
    ]
    
    missing_vars = []
    for var in required_env_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"Missing environment variables: {missing_vars}")
        return False
    
    logger.info("✅ All dependencies checked")
    return True


def run_system_checks():
    """Run comprehensive system checks"""
    logger.info("🔧 Running system checks...")
    
    try:
        # Set required environment variables for the check
        env = os.environ.copy()
        env.update({
            "KARI_DUCKDB_PASSWORD": "dev-duckdb-pass",
            "KARI_JOB_SIGNING_KEY": "dev-job-key-456",
            "KARI_JOB_ENC_KEY": "MaL42789OGRr0--UUf_RV_kanWzb2tSCd6hU6R-sOZo="
        })
        
        result = subprocess.run([
            sys.executable, "scripts/fix_system_issues.py"
        ], env=env, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("✅ All system checks passed")
            return True
        else:
            logger.warning("⚠️ Some system checks failed, but continuing...")
            logger.info(result.stdout)
            if result.stderr:
                logger.error(result.stderr)
            return True  # Continue even if some checks fail
            
    except Exception as e:
        logger.error(f"System checks failed: {e}")
        return False


def start_server(port: int = 8000, host: str = "0.0.0.0"):
    """Start the production server"""
    logger.info(f"🚀 Starting AI Karen Engine on {host}:{port}")
    
    # Set production environment variables
    env = os.environ.copy()
    env.update({
        "ENVIRONMENT": "production",
        "DEBUG": "false",
        "LOG_LEVEL": "INFO",
        "KARI_DUCKDB_PASSWORD": "dev-duckdb-pass",
        "KARI_JOB_SIGNING_KEY": "dev-job-key-456",
        "KARI_JOB_ENC_KEY": "MaL42789OGRr0--UUf_RV_kanWzb2tSCd6hU6R-sOZo="
    })
    
    try:
        # Start the server
        cmd = [sys.executable, "main.py"]
        process = subprocess.Popen(cmd, env=env)
        
        # Wait a moment for startup
        time.sleep(3)
        
        # Check if process is still running
        if process.poll() is None:
            logger.info(f"✅ Server started successfully (PID: {process.pid})")
            logger.info(f"🌐 Server available at http://{host}:{port}")
            logger.info("📊 Health check: http://localhost:8000/api/health/degraded-mode")
            logger.info("📚 API docs: http://localhost:8000/docs")
            
            # Wait for the process to complete
            try:
                process.wait()
            except KeyboardInterrupt:
                logger.info("🛑 Received shutdown signal")
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                logger.info("✅ Server shutdown complete")
        else:
            logger.error("❌ Server failed to start")
            return False
            
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        return False
    
    return True


def main():
    """Main startup function"""
    logger.info("🎯 AI Karen Engine - Production Startup")
    logger.info("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        logger.error("❌ Dependency check failed")
        sys.exit(1)
    
    # Kill existing server
    if not kill_existing_server():
        logger.error("❌ Failed to stop existing server")
        sys.exit(1)
    
    # Run system checks
    if not run_system_checks():
        logger.error("❌ System checks failed")
        sys.exit(1)
    
    # Start server
    if not start_server():
        logger.error("❌ Server startup failed")
        sys.exit(1)
    
    logger.info("🎉 Production startup complete!")


if __name__ == "__main__":
    main()