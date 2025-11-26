#!/usr/bin/env python3
"""
Interactive setup script for llama.cpp server

This script provides a user-friendly interface for configuring
the llama.cpp server with customizable options.
"""

import os
import sys
import json
import platform
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Union

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


class SetupWizard:
    """Interactive setup wizard for llama.cpp server configuration"""
    
    def __init__(self):
        """Initialize the setup wizard"""
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
        
        self.setup_complete = False
    
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
    
    def _discover_model_directories(self) -> List[tuple]:
        """Discover recommended model directories in the KAREN project structure"""
        recommended_dirs = []
        
        # Current working directory
        cwd = Path.cwd()
        
        # Option 1: models/llama-cpp in the current directory
        option1_path = cwd / "models" / "llama-cpp"
        recommended_dirs.append(("Default: models/llama-cpp in current directory", str(option1_path)))
        
        # Option 2: Try to find KAREN's models directory
        karen_models_path = cwd / "data" / "models" / "llama-cpp"
        if not karen_models_path.exists():
            # Try alternative paths
            alternative_paths = [
                cwd / "models",
                cwd / "data" / "models",
                cwd.parent / "models" / "llama-cpp",
                cwd.parent / "data" / "models" / "llama-cpp"
            ]
            
            for path in alternative_paths:
                if path.exists():
                    karen_models_path = path / "llama-cpp"
                    break
        
        recommended_dirs.append(("KAREN models directory", str(karen_models_path)))
        
        return recommended_dirs
    
    def _clear_screen(self) -> None:
        """Clear the terminal screen"""
        os.system('cls' if platform.system() == 'Windows' else 'clear')
    
    def _display_header(self) -> None:
        """Display the setup header"""
        print("=" * 60)
        print("    Llama.cpp Server Setup Wizard")
        print("=" * 60)
        print()
        print("This wizard will help you configure the llama.cpp server")
        print("for optimal performance with your system.")
        print()
    
    def _get_input(self, prompt: str, default: Any = None, options: Optional[List[str]] = None) -> str:
        """Get user input with validation"""
        if default is not None:
            prompt = f"{prompt} [{default}]: "
        else:
            prompt = f"{prompt}: "
        
        while True:
            user_input = input(prompt).strip()
            
            if not user_input and default is not None:
                return str(default)
            
            if options and user_input not in options:
                print(f"Invalid option. Please choose from: {', '.join(options)}")
                continue
            
            return user_input
    
    def _get_yes_no(self, prompt: str, default: bool = True) -> bool:
        """Get yes/no input from user"""
        default_str = "Y/n" if default else "y/N"
        user_input = self._get_input(prompt, default_str).lower()
        return user_input in ('y', 'yes', 'true', '1')
    
    def _get_number_input(self, prompt: str, default: Optional[int] = None, min_val: Optional[int] = None, max_val: Optional[int] = None) -> int:
        """Get numeric input with validation"""
        while True:
            user_input = self._get_input(prompt, default)
            try:
                num = int(user_input)
                if min_val is not None and num < min_val:
                    print(f"Value must be at least {min_val}")
                    continue
                if max_val is not None and num > max_val:
                    print(f"Value must be at most {max_val}")
                    continue
                return num
            except ValueError:
                print("Please enter a valid number")
    
    def _get_path_input(self, prompt: str, default: Optional[str] = None, must_exist: bool = False) -> str:
        """Get path input with validation"""
        while True:
            user_input = self._get_input(prompt, default)
            if not user_input:
                return default or ""
            
            path = Path(user_input)
            if must_exist and not path.exists():
                print(f"Path does not exist: {user_input}")
                continue
            
            return str(path.absolute())
    
    def setup_server_configuration(self) -> None:
        """Configure server settings"""
        print("--- Server Configuration ---")
        print()
        
        # Server host
        current_host = self.config.get("server", {}).get("host", "0.0.0.0")
        host = self._get_input("Server host", current_host)
        self._set_config_value("server.host", host)
        
        # Server port
        current_port = self.config.get("server", {}).get("port", 8080)
        port = self._get_number_input("Server port", current_port, 1, 65535)
        self._set_config_value("server.port", port)
        
        # Log level
        current_log_level = self.config.get("server", {}).get("log_level", "INFO")
        log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        print(f"Available log levels: {', '.join(log_levels)}")
        log_level = self._get_input("Log level", current_log_level, log_levels)
        self._set_config_value("server.log_level", log_level)
        
        # CORS origins
        current_cors = self.config.get("server", {}).get("cors_allow_origins", ["*"])
        if self._get_yes_no("Customize CORS origins (default: all allowed)", False):
            print("Enter CORS origins (one per line, empty line to finish):")
            cors_origins = []
            while True:
                origin = input("> ").strip()
                if not origin:
                    break
                cors_origins.append(origin)
            if cors_origins:
                self._set_config_value("server.cors_allow_origins", cors_origins)
        
        # Rate limiting
        current_rate = self.config.get("server", {}).get("rate_limit_per_min", 120)
        rate_limit = self._get_number_input("Rate limit per minute", current_rate, 1)
        self._set_config_value("server.rate_limit_per_min", rate_limit)
        
        print()
    
    def setup_model_configuration(self) -> None:
        """Configure model settings"""
        print("--- Model Configuration ---")
        print()
        
        # Try to discover existing models directory
        recommended_dirs = self._discover_model_directories()
        
        print("Available model directory options:")
        for i, (desc, path) in enumerate(recommended_dirs, 1):
            exists = "✓" if Path(path).exists() else "✗"
            print(f"{i}. {desc}: {path} {exists}")
        
        print("3. Custom path")
        print()
        
        # Get user selection
        choice = self._get_input("Select a model directory option", "1", ["1", "2", "3"])
        
        if choice == "1":
            model_dir = recommended_dirs[0][1]
            print(f"Selected: {recommended_dirs[0][0]}")
        elif choice == "2":
            model_dir = recommended_dirs[1][1]
            print(f"Selected: {recommended_dirs[1][0]}")
        else:  # choice == "3"
            current_dir = self.config.get("models", {}).get("directory", str(Path.cwd() / "models" / "llama-cpp"))
            model_dir = self._get_path_input("Enter custom model directory path", current_dir)
        
        self._set_config_value("models.directory", model_dir)
        
        # Create directory if it doesn't exist
        if not Path(model_dir).exists():
            if self._get_yes_no(f"Create directory: {model_dir}", True):
                Path(model_dir).mkdir(parents=True, exist_ok=True)
                print(f"Created directory: {model_dir}")
        
        # Default model
        current_default = self.config.get("models", {}).get("default_model")
        default_model = self._get_input("Default model (leave empty for none)", current_default)
        self._set_config_value("models.default_model", default_model if default_model else None)
        
        # Auto-load default model
        current_auto_load = self.config.get("models", {}).get("auto_load_default", True)
        auto_load = self._get_yes_no("Auto-load default model on startup", current_auto_load)
        self._set_config_value("models.auto_load_default", auto_load)
        
        # Max loaded models
        current_max = self.config.get("models", {}).get("max_loaded_models", 2)
        max_loaded = self._get_number_input("Maximum loaded models", current_max, 1, 10)
        self._set_config_value("models.max_loaded_models", max_loaded)
        
        # Max cache GB
        current_cache = self.config.get("models", {}).get("max_cache_gb", 8)
        max_cache = self._get_number_input("Maximum cache size (GB)", current_cache, 1, 64)
        self._set_config_value("models.max_cache_gb", max_cache)
        
        print()
    
    def setup_performance_configuration(self) -> None:
        """Configure performance settings"""
        print("--- Performance Configuration ---")
        print()
        
        # Optimization target
        current_opt = self.config.get("performance", {}).get("optimize_for", "balanced")
        options = ["speed", "balanced", "memory"]
        print(f"Available optimization targets: {', '.join(options)}")
        optimize_for = self._get_input("Optimize for", current_opt, options)
        self._set_config_value("performance.optimize_for", optimize_for)
        
        # GPU acceleration
        current_gpu = self.config.get("performance", {}).get("enable_gpu", True)
        enable_gpu = self._get_yes_no("Enable GPU acceleration", current_gpu)
        self._set_config_value("performance.enable_gpu", enable_gpu)
        
        # Number of threads
        current_threads = self.config.get("performance", {}).get("num_threads", 4)
        num_threads = self._get_number_input("Number of threads", current_threads, 1, 64)
        self._set_config_value("performance.num_threads", num_threads)
        
        # Batch size
        current_batch = self.config.get("performance", {}).get("batch_size", 128)
        batch_size = self._get_number_input("Batch size", current_batch, 1, 2048)
        self._set_config_value("performance.batch_size", batch_size)
        
        # Context window
        current_ctx = self.config.get("performance", {}).get("context_window", 4096)
        context_window = self._get_number_input("Context window size", current_ctx, 512, 32768)
        self._set_config_value("performance.context_window", context_window)
        
        # Low VRAM mode
        current_low_vram = self.config.get("performance", {}).get("low_vram", False)
        low_vram = self._get_yes_no("Enable low VRAM mode", current_low_vram)
        self._set_config_value("performance.low_vram", low_vram)
        
        print()
    
    def setup_installation_configuration(self) -> None:
        """Configure installation settings"""
        print("--- Installation Configuration ---")
        print()
        
        # Installation path
        current_install = self.config.get("installation", {}).get("install_path", str(Path.cwd() / "_llama_cpp"))
        install_path = self._get_path_input("Installation path", current_install)
        self._set_config_value("installation.install_path", install_path)
        
        # Virtual environment
        current_venv = self.config.get("installation", {}).get("use_virtual_environment", True)
        use_venv = self._get_yes_no("Use virtual environment", current_venv)
        self._set_config_value("installation.use_virtual_environment", use_venv)
        
        if use_venv:
            # Virtual environment path
            current_venv_path = self.config.get("installation", {}).get("venv_path", str(Path.cwd() / "venv"))
            venv_path = self._get_path_input("Virtual environment path", current_venv_path)
            self._set_config_value("installation.venv_path", venv_path)
        
        # Installation method
        current_method = self.config.get("installation", {}).get("install_method", "auto")
        methods = ["auto", "pip", "pip-metal", "pip-cuda"]
        print(f"Available installation methods: {', '.join(methods)}")
        install_method = self._get_input("Installation method", current_method, methods)
        self._set_config_value("installation.install_method", install_method)
        
        # CUDA version
        if install_method == "pip-cuda":
            current_cuda = self.config.get("installation", {}).get("cuda_version")
            cuda_versions = ["11.8", "12.0", "12.1", "12.2"]
            print(f"Common CUDA versions: {', '.join(cuda_versions)}")
            cuda_version = self._get_input("CUDA version (leave empty for default)", current_cuda)
            self._set_config_value("installation.cuda_version", cuda_version if cuda_version else None)
        
        print()
    
    def setup_karen_configuration(self) -> None:
        """Configure KAREN integration settings"""
        print("--- KAREN Integration Configuration ---")
        print()
        
        # Enable integration
        current_enabled = self.config.get("karen", {}).get("integration_enabled", True)
        enable_integration = self._get_yes_no("Enable KAREN integration", current_enabled)
        self._set_config_value("karen.integration_enabled", enable_integration)
        
        if enable_integration:
            # KAREN endpoint
            current_endpoint = self.config.get("karen", {}).get("endpoint", "http://localhost:8000")
            endpoint = self._get_input("KAREN endpoint", current_endpoint)
            self._set_config_value("karen.endpoint", endpoint)
            
            # Health timeout
            current_timeout = self.config.get("karen", {}).get("health_timeout_s", 2)
            timeout = self._get_number_input("Health check timeout (seconds)", current_timeout, 1, 60)
            self._set_config_value("karen.health_timeout_s", timeout)
        
        print()
    
    def setup_observability_configuration(self) -> None:
        """Configure observability settings"""
        print("--- Observability Configuration ---")
        print()
        
        # Prometheus metrics
        current_prometheus = self.config.get("observability", {}).get("enable_prometheus", False)
        enable_prometheus = self._get_yes_no("Enable Prometheus metrics", current_prometheus)
        self._set_config_value("observability.enable_prometheus", enable_prometheus)
        
        if enable_prometheus:
            # Prometheus port
            current_port = self.config.get("observability", {}).get("prometheus_port", 9090)
            prometheus_port = self._get_number_input("Prometheus port", current_port, 1, 65535)
            self._set_config_value("observability.prometheus_port", prometheus_port)
        
        # Tracing
        current_tracing = self.config.get("observability", {}).get("enable_tracing", False)
        enable_tracing = self._get_yes_no("Enable tracing", current_tracing)
        self._set_config_value("observability.enable_tracing", enable_tracing)
        
        print()
    
    def save_configuration(self) -> bool:
        """Save the configuration to file"""
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
    
    def _set_config_value(self, key: str, value: Any) -> None:
        """Set a configuration value using dot notation"""
        if self.config_manager:
            self.config_manager.set(key, value)
        else:
            # Manual implementation for nested dictionary
            keys = key.split('.')
            config = self.config
            
            for k in keys[:-1]:
                if k not in config:
                    config[k] = {}
                config = config[k]
            
            config[keys[-1]] = value
    
    def show_summary(self) -> None:
        """Display configuration summary"""
        print("--- Configuration Summary ---")
        print()
        
        print(f"Server host: {self.config.get('server', {}).get('host')}")
        print(f"Server port: {self.config.get('server', {}).get('port')}")
        print(f"Model directory: {self.config.get('models', {}).get('directory')}")
        print(f"Installation path: {self.config.get('installation', {}).get('install_path')}")
        print(f"Virtual environment: {'Enabled' if self.config.get('installation', {}).get('use_virtual_environment') else 'Disabled'}")
        print(f"KAREN integration: {'Enabled' if self.config.get('karen', {}).get('integration_enabled') else 'Disabled'}")
        print(f"Prometheus metrics: {'Enabled' if self.config.get('observability', {}).get('enable_prometheus') else 'Disabled'}")
        print()
    
    def run(self) -> bool:
        """Run the interactive setup wizard"""
        self._clear_screen()
        self._display_header()
        
        # Main menu loop
        while True:
            print("Main Menu:")
            print("1. Server Configuration")
            print("2. Model Configuration")
            print("3. Performance Configuration")
            print("4. Installation Configuration")
            print("5. KAREN Integration")
            print("6. Observability Configuration")
            print("7. Show Summary")
            print("8. Save and Exit")
            print("9. Exit Without Saving")
            print()
            
            choice = self._get_input("Select an option", "1", ["1", "2", "3", "4", "5", "6", "7", "8", "9"])
            
            self._clear_screen()
            self._display_header()
            
            if choice == "1":
                self.setup_server_configuration()
            elif choice == "2":
                self.setup_model_configuration()
            elif choice == "3":
                self.setup_performance_configuration()
            elif choice == "4":
                self.setup_installation_configuration()
            elif choice == "5":
                self.setup_karen_configuration()
            elif choice == "6":
                self.setup_observability_configuration()
            elif choice == "7":
                self.show_summary()
            elif choice == "8":
                if self.save_configuration():
                    print("Configuration saved successfully!")
                    self.setup_complete = True
                    return True
                else:
                    print("Failed to save configuration!")
                    input("Press Enter to continue...")
            elif choice == "9":
                if self._get_yes_no("Are you sure you want to exit without saving?", False):
                    return False
            
            self._clear_screen()
            self._display_header()


def main():
    """Main entry point"""
    wizard = SetupWizard()
    success = wizard.run()
    
    if success:
        print("\nSetup completed successfully!")
        print("\nNext steps:")
        print("1. Run the installation wizard: python install_llamacpp.py")
        print("2. Download GGUF models to your model directory")
        print("3. Start the server: python runServer.py")
    else:
        print("\nSetup was cancelled.")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
