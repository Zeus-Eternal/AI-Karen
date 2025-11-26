#!/usr/bin/env python3
"""
One-click installation script for KAREN integration

This script automates the entire setup process for llama.cpp server
with KAREN integration, requiring minimal user interaction.
"""

import os
import sys
import json
import logging
import platform
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

# Add _server directory to Python path
server_path = Path(__file__).parent / "_server"
sys.path.insert(0, str(server_path))

# Import configuration manager
ConfigManager = None
CONFIG_MANAGER_AVAILABLE = False
try:
    from _server.config_manager import ConfigManager as _ConfigManager
    ConfigManager = _ConfigManager
    CONFIG_MANAGER_AVAILABLE = True
except ImportError:
    CONFIG_MANAGER_AVAILABLE = False

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class KarenInstaller:
    """One-click installer for KAREN integration"""
    
    def __init__(self, auto_mode: bool = False):
        """Initialize the installer
        
        Args:
            auto_mode: If True, use default settings without prompting
        """
        self.auto_mode = auto_mode
        self.config_manager = None
        self.config = None
        self.installation_successful = False
        
        # Initialize configuration
        self._initialize_config()
    
    def _initialize_config(self) -> None:
        """Initialize configuration manager"""
        if CONFIG_MANAGER_AVAILABLE and ConfigManager:
            try:
                self.config_manager = ConfigManager()
                self.config = self.config_manager.config
            except Exception as e:
                logger.warning(f"Failed to initialize ConfigManager: {e}")
                self.config_manager = None
                self.config_path = Path.cwd() / "config.json"
                if self.config_path.exists():
                    with open(self.config_path, 'r') as f:
                        self.config = json.load(f)
                else:
                    self.config = self._get_default_config()
        else:
            # Fallback to manual configuration
            self.config_manager = None
            self.config_path = Path.cwd() / "config.json"
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    self.config = json.load(f)
            else:
                self.config = self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            "server": {
                "host": "0.0.0.0",
                "port": 8080,
                "log_level": "INFO",
                "cors_allow_origins": ["*"],
                "rate_limit_per_min": 120,
                "auth_token": None
            },
            "models": {
                "directory": str(Path.cwd() / "models" / "llama-cpp"),
                "default_model": None,
                "auto_load_default": True,
                "max_loaded_models": 2,
                "max_cache_gb": 8
            },
            "performance": {
                "optimize_for": "balanced",
                "enable_gpu": True,
                "num_threads": 4,
                "batch_size": 128,
                "context_window": 4096,
                "low_vram": False
            },
            "backend": {
                "type": "auto",
                "local": {
                    "n_ctx": 4096,
                    "n_threads": 4,
                    "n_batch": 512,
                    "use_mmap": True,
                    "use_mlock": False,
                    "embedding": False,
                    "low_mem": False,
                    "verbose": False
                },
                "remote": {
                    "url": "http://localhost:8000",
                    "timeout": 30,
                    "auth_token": None
                }
            },
            "karen": {
                "integration_enabled": True,
                "endpoint": "http://localhost:8000",
                "health_timeout_s": 2
            },
            "observability": {
                "enable_prometheus": False,
                "prometheus_port": 9090,
                "enable_tracing": False
            },
            "installation": {
                "install_path": str(Path.cwd() / "_llama_cpp"),
                "use_virtual_environment": True,
                "venv_path": str(Path.cwd() / "venv"),
                "install_method": "auto",
                "cuda_version": None
            }
        }
    
    def _set_config_value(self, key: str, value: Any) -> None:
        """Set a configuration value using dot notation"""
        if self.config_manager:
            self.config_manager.set(key, value)
        else:
            # Manual implementation for nested dictionary
            keys = key.split('.')
            config = self.config
            
            for k in keys[:-1]:
                if config is None or k not in config:
                    if config is None:
                        config = {}
                    config[k] = {}
                config = config[k]
            
            if config is not None:
                config[keys[-1]] = value
    
    def _save_config(self) -> bool:
        """Save configuration to file"""
        if self.config_manager:
            return self.config_manager.save_config()
        else:
            try:
                with open(self.config_path, 'w') as f:
                    json.dump(self.config, f, indent=2)
                logger.info(f"Saved configuration to {self.config_path}")
                return True
            except Exception as e:
                logger.error(f"Failed to save configuration: {e}")
                return False
    
    def _run_command(self, command: List[str], cwd: Optional[Path] = None) -> Tuple[bool, str]:
        """Run a command and return success status and output"""
        try:
            result = subprocess.run(
                command,
                cwd=cwd,
                capture_output=True,
                text=True,
                check=True
            )
            return True, result.stdout
        except subprocess.CalledProcessError as e:
            return False, e.stderr
        except FileNotFoundError:
            return False, f"Command not found: {command[0]}"
    
    def _check_system_requirements(self) -> bool:
        """Check if system meets minimum requirements"""
        print("Checking system requirements...")
        
        # Check Python version
        py_version = sys.version_info
        if py_version < (3, 8):
            print(f"Error: Python 3.8 or higher is required. Current version: {py_version}")
            return False
        
        # Check available disk space
        try:
            import shutil
            disk_usage = shutil.disk_usage(Path.cwd())
            free_gb = disk_usage.free / (1024 ** 3)
            if free_gb < 10:
                print(f"Error: At least 10GB of free disk space is required. Available: {free_gb:.1f}GB")
                return False
        except Exception as e:
            logger.warning(f"Failed to check disk space: {e}")
        
        print("System requirements check passed.")
        return True
    
    def _install_dependencies(self) -> bool:
        """Install required dependencies"""
        print("Installing dependencies...")
        
        # Install basic Python dependencies
        packages = ["fastapi", "uvicorn", "pydantic", "python-multipart", "requests"]
        
        for package in packages:
            print(f"Installing {package}...")
            success, output = self._run_command([sys.executable, "-m", "pip", "install", package])
            if not success:
                print(f"Failed to install {package}: {output}")
                return False
        
        print("Dependencies installed successfully.")
        return True
    
    def _install_llamacpp(self) -> bool:
        """Install llama.cpp"""
        print("Installing llama.cpp...")
        
        # Run the installation script
        install_script = Path(__file__).parent / "install_llamacpp.py"
        if not install_script.exists():
            print("Error: install_llamacpp.py not found.")
            return False
        
        # Build command arguments
        cmd = [sys.executable, str(install_script)]
        
        if self.auto_mode:
            cmd.extend(["--auto", "--no-confirm"])
        
        # Run installation script
        success, output = self._run_command(cmd)
        if not success:
            print(f"Failed to install llama.cpp: {output}")
            return False
        
        print("llama.cpp installed successfully.")
        return True
    
    def _download_sample_model(self) -> bool:
        """Download a sample model for testing"""
        print("Downloading sample model...")
        
        # Skip in auto mode or if user declines
        if not self.auto_mode:
            download = input("Download a sample model for testing? (y/n): ").lower() == 'y'
            if not download:
                print("Skipping model download.")
                return True
        
        # Run the model downloader
        downloader_script = Path(__file__).parent / "model_downloader.py"
        if not downloader_script.exists():
            print("Error: model_downloader.py not found.")
            return False
        
        # For auto mode, we'll download a small model automatically
        if self.auto_mode:
            print("Auto mode: Skipping model download. You can download models later.")
            return True
        
        # Run downloader in interactive mode
        success, output = self._run_command([sys.executable, str(downloader_script)])
        if not success:
            print(f"Failed to run model downloader: {output}")
            return False
        
        print("Sample model download completed.")
        return True
    
    def _configure_for_karen(self) -> bool:
        """Configure llama.cpp server for KAREN integration"""
        print("Configuring for KAREN integration...")
        
        # Set KAREN-specific configuration
        self._set_config_value("karen.integration_enabled", True)
        self._set_config_value("karen.endpoint", "http://localhost:8000")
        self._set_config_value("karen.health_timeout_s", 2)
        
        # Optimize performance for KAREN
        import multiprocessing
        cpu_cores = multiprocessing.cpu_count()
        
        self._set_config_value("performance.num_threads", cpu_cores)
        self._set_config_value("backend.local.n_threads", cpu_cores)
        self._set_config_value("backend.local.n_ctx", 4096)
        self._set_config_value("backend.local.n_batch", 512)
        
        # Save configuration
        if not self._save_config():
            print("Failed to save configuration.")
            return False
        
        print("Configuration for KAREN integration completed.")
        return True
    
    def _create_startup_scripts(self) -> bool:
        """Create startup scripts for easy server management"""
        print("Creating startup scripts...")
        
        # Create scripts directory if it doesn't exist
        scripts_dir = Path(__file__).parent / "scripts"
        scripts_dir.mkdir(exist_ok=True)
        
        # Create start script
        start_script = scripts_dir / "start_server.sh"
        start_content = f"""#!/bin/bash
# Start llama.cpp server for KAREN integration

cd "$(dirname "$0")/.."

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Start the server
echo "Starting llama.cpp server..."
python runServer.py
"""
        
        try:
            with open(start_script, 'w') as f:
                f.write(start_content)
            
            # Make script executable
            os.chmod(start_script, 0o755)
            
            # Create stop script
            stop_script = scripts_dir / "stop_server.sh"
            stop_content = """#!/bin/bash
# Stop llama.cpp server

echo "Stopping llama.cpp server..."
pkill -f "python runServer.py"
echo "Server stopped."
"""
            
            with open(stop_script, 'w') as f:
                f.write(stop_content)
            
            # Make script executable
            os.chmod(stop_script, 0o755)
            
            # Create restart script
            restart_script = scripts_dir / "restart_server.sh"
            restart_content = """#!/bin/bash
# Restart llama.cpp server

echo "Restarting llama.cpp server..."
pkill -f "python runServer.py"
sleep 2

cd "$(dirname "$0")/.."

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Start the server
echo "Starting llama.cpp server..."
python runServer.py
"""
            
            with open(restart_script, 'w') as f:
                f.write(restart_content)
            
            # Make script executable
            os.chmod(restart_script, 0o755)
            
            print("Startup scripts created successfully.")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create startup scripts: {e}")
            return False
    
    def _create_karen_integration_file(self) -> bool:
        """Create KAREN integration configuration file"""
        print("Creating KAREN integration file...")
        
        # Create KAREN integration config
        karen_config = {
            "name": "llama-cpp-server",
            "version": "1.0.0",
            "description": "Llama.cpp server integration for KAREN",
            "endpoint": "http://localhost:8080",
            "health_endpoint": "http://localhost:8080/health",
            "models_endpoint": "http://localhost:8080/models",
            "inference_endpoint": "http://localhost:8080/inference",
            "auth_token": None,
            "timeout": 30,
            "max_retries": 3,
            "retry_delay": 5
        }
        
        # Save KAREN integration config
        karen_config_path = Path(__file__).parent / "karen_integration.json"
        
        try:
            with open(karen_config_path, 'w') as f:
                json.dump(karen_config, f, indent=2)
            
            print("KAREN integration file created successfully.")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create KAREN integration file: {e}")
            return False
    
    def _create_desktop_shortcut(self) -> bool:
        """Create desktop shortcut for easy access"""
        print("Creating desktop shortcut...")
        
        # Skip in auto mode
        if self.auto_mode:
            print("Auto mode: Skipping desktop shortcut creation.")
            return True
        
        # Ask user if they want a desktop shortcut
        create_shortcut = input("Create desktop shortcut? (y/n): ").lower() == 'y'
        if not create_shortcut:
            print("Skipping desktop shortcut creation.")
            return True
        
        # Determine desktop path
        desktop_path = Path.home() / "Desktop"
        if not desktop_path.exists():
            desktop_path = Path.home() / "Desktop"
            if not desktop_path.exists():
                print("Desktop not found. Skipping shortcut creation.")
                return True
        
        # Create shortcut
        shortcut_path = desktop_path / "llama-cpp-server.desktop"
        
        # Get current directory
        current_dir = Path(__file__).parent.absolute()
        
        shortcut_content = f"""[Desktop Entry]
Version=1.0
Type=Application
Name=Llama.cpp Server
Comment=Start Llama.cpp Server for KAREN Integration
Exec=bash -c 'cd {current_dir} && ./scripts/start_server.sh'
Icon={current_dir}/icon.png
Terminal=true
Categories=Utility;Application;
"""
        
        try:
            with open(shortcut_path, 'w') as f:
                f.write(shortcut_content)
            
            # Make shortcut executable
            os.chmod(shortcut_path, 0o755)
            
            print("Desktop shortcut created successfully.")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create desktop shortcut: {e}")
            return False
    
    def _run_final_checks(self) -> bool:
        """Run final checks to ensure installation is complete"""
        print("Running final checks...")
        
        # Check if config file exists
        if not self.config_path.exists():
            print("Error: Configuration file not found.")
            return False
        
        # Check if model directory exists
        model_dir = Path(self.config.get("models.directory", ""))
        if not model_dir.exists():
            print("Warning: Model directory not found. Creating it...")
            model_dir.mkdir(parents=True, exist_ok=True)
        
        # Check if installation directory exists
        install_dir = Path(self.config.get("installation.install_path", ""))
        if not install_dir.exists():
            print("Warning: Installation directory not found. This is normal if llama.cpp was not installed.")
        
        # Check if scripts directory exists
        scripts_dir = Path(__file__).parent / "scripts"
        if not scripts_dir.exists():
            print("Warning: Scripts directory not found.")
            return False
        
        # Check if startup scripts exist
        start_script = scripts_dir / "start_server.sh"
        if not start_script.exists():
            print("Warning: Start script not found.")
            return False
        
        # Check if KAREN integration file exists
        karen_config_path = Path(__file__).parent / "karen_integration.json"
        if not karen_config_path.exists():
            print("Warning: KAREN integration file not found.")
            return False
        
        print("Final checks passed.")
        return True
    
    def install(self) -> bool:
        """Run the complete installation process"""
        print("Starting one-click installation for KAREN integration...")
        print("=" * 60)
        print()
        
        # Check system requirements
        if not self._check_system_requirements():
            print("System requirements check failed. Installation aborted.")
            return False
        
        print()
        
        # Install dependencies
        if not self._install_dependencies():
            print("Failed to install dependencies. Installation aborted.")
            return False
        
        print()
        
        # Install llama.cpp
        if not self._install_llamacpp():
            print("Failed to install llama.cpp. Installation aborted.")
            return False
        
        print()
        
        # Download sample model
        if not self._download_sample_model():
            print("Failed to download sample model. Continuing anyway...")
        
        print()
        
        # Configure for KAREN
        if not self._configure_for_karen():
            print("Failed to configure for KAREN. Installation aborted.")
            return False
        
        print()
        
        # Create startup scripts
        if not self._create_startup_scripts():
            print("Failed to create startup scripts. Installation aborted.")
            return False
        
        print()
        
        # Create KAREN integration file
        if not self._create_karen_integration_file():
            print("Failed to create KAREN integration file. Installation aborted.")
            return False
        
        print()
        
        # Create desktop shortcut
        if not self._create_desktop_shortcut():
            print("Failed to create desktop shortcut. Continuing anyway...")
        
        print()
        
        # Run final checks
        if not self._run_final_checks():
            print("Final checks failed. Installation may be incomplete.")
            return False
        
        print()
        print("=" * 60)
        print("Installation completed successfully!")
        print("=" * 60)
        print()
        print("Next steps:")
        print("1. Download GGUF models using: python model_downloader.py")
        print("2. Start the server using: ./scripts/start_server.sh")
        print("3. Access the API at: http://localhost:8080")
        print("4. Configure KAREN to use the integration file: karen_integration.json")
        print()
        
        self.installation_successful = True
        return True


def main():
    """Main entry point"""
    # Parse command line arguments
    auto_mode = "--auto" in sys.argv
    
    installer = KarenInstaller(auto_mode=auto_mode)
    success = installer.install()
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())