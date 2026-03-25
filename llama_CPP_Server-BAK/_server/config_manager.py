#!/usr/bin/env python3
"""
Configuration manager for llama.cpp server

This module provides a centralized way to manage configuration settings
for the llama.cpp server, including model location and installation options.
"""

import json
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union

logger = logging.getLogger(__name__)


class ConfigManager:
    """Manages configuration for the llama.cpp server"""
    
    def __init__(self, config_path: Union[str, Path, None] = None):
        """Initialize the configuration manager
        
        Args:
            config_path: Path to the configuration file. If None, uses default path.
        """
        if config_path is None:
            self.config_path = Path.cwd() / "config.json"
        else:
            self.config_path = Path(config_path)
        
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default if not exists"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                logger.info(f"Loaded configuration from {self.config_path}")
                return config
            except Exception as e:
                logger.error(f"Failed to load configuration: {e}")
                logger.info("Using default configuration")
                return self._get_default_config()
        else:
            logger.info("Configuration file not found, using defaults")
            return self._get_default_config()
    
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
                "install_method": "auto",  # auto|pip|pip-metal|pip-cuda
                "cuda_version": None  # Auto-detect or specify
            }
        }
    
    def save_config(self) -> bool:
        """Save current configuration to file"""
        try:
            # Create parent directory if it doesn't exist
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            
            logger.info(f"Saved configuration to {self.config_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            return False
    
    def save(self) -> bool:
        """Alias for save_config method"""
        return self.save_config()
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key (supports dot notation)"""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value by key (supports dot notation)"""
        keys = key.split('.')
        config = self.config
        
        # Navigate to the parent of the target key
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # Set the value
        config[keys[-1]] = value
    
    def get_model_directory(self) -> Path:
        """Get the model directory path"""
        directory = self.get("models.directory", str(Path.cwd() / "models" / "llama-cpp"))
        return Path(directory)
    
    def set_model_directory(self, path: Union[str, Path]) -> None:
        """Set the model directory path"""
        self.set("models.directory", str(Path(path)))
    
    def get_installation_path(self) -> Path:
        """Get the installation path"""
        path = self.get("installation.install_path", str(Path.cwd() / "_llama_cpp"))
        return Path(path)
    
    def set_installation_path(self, path: Union[str, Path]) -> None:
        """Set the installation path"""
        self.set("installation.install_path", str(Path(path)))
    
    def get_venv_path(self) -> Path:
        """Get the virtual environment path"""
        path = self.get("installation.venv_path", str(Path.cwd() / "venv"))
        return Path(path)
    
    def set_venv_path(self, path: Union[str, Path]) -> None:
        """Set the virtual environment path"""
        self.set("installation.venv_path", str(Path(path)))
    
    def use_virtual_environment(self) -> bool:
        """Check if virtual environment should be used"""
        return self.get("installation.use_virtual_environment", True)
    
    def set_use_virtual_environment(self, use_venv: bool) -> None:
        """Set whether to use virtual environment"""
        self.set("installation.use_virtual_environment", use_venv)
    
    def get_install_method(self) -> str:
        """Get the installation method"""
        return self.get("installation.install_method", "auto")
    
    def set_install_method(self, method: str) -> None:
        """Set the installation method"""
        if method in ["auto", "pip", "pip-metal", "pip-cuda"]:
            self.set("installation.install_method", method)
        else:
            raise ValueError(f"Invalid installation method: {method}")
    
    def get_cuda_version(self) -> Optional[str]:
        """Get the CUDA version"""
        return self.get("installation.cuda_version")
    
    def set_cuda_version(self, version: Optional[str]) -> None:
        """Set the CUDA version"""
        self.set("installation.cuda_version", version)
    
    def create_directories(self) -> None:
        """Create necessary directories based on configuration"""
        directories = [
            self.get_installation_path(),
            self.get_model_directory(),
            self.get_model_directory() / "downloads"
        ]
        
        if self.use_virtual_environment():
            directories.append(self.get_venv_path())
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {directory}")
    
    def update_from_env(self) -> None:
        """Update configuration from environment variables"""
        # Model directory
        if "LLAMACPP_MODEL_DIR" in os.environ:
            self.set_model_directory(os.environ["LLAMACPP_MODEL_DIR"])
        
        # Installation path
        if "LLAMACPP_INSTALL_PATH" in os.environ:
            self.set_installation_path(os.environ["LLAMACPP_INSTALL_PATH"])
        
        # Virtual environment path
        if "LLAMACPP_VENV_PATH" in os.environ:
            self.set_venv_path(os.environ["LLAMACPP_VENV_PATH"])
        
        # Use virtual environment
        if "LLAMACPP_USE_VENV" in os.environ:
            use_venv = os.environ["LLAMACPP_USE_VENV"].lower() in ("true", "1", "yes", "on")
            self.set_use_virtual_environment(use_venv)
        
        # Installation method
        if "LLAMACPP_INSTALL_METHOD" in os.environ:
            method = os.environ["LLAMACPP_INSTALL_METHOD"]
            if method in ["auto", "pip", "pip-metal", "pip-cuda"]:
                self.set_install_method(method)
        
        # CUDA version
        if "LLAMACPP_CUDA_VERSION" in os.environ:
            self.set_cuda_version(os.environ["LLAMACPP_CUDA_VERSION"])
        
        # Server host
        if "LLAMACPP_HOST" in os.environ:
            self.set("server.host", os.environ["LLAMACPP_HOST"])
        
        # Server port
        if "LLAMACPP_PORT" in os.environ:
            try:
                port = int(os.environ["LLAMACPP_PORT"])
                self.set("server.port", port)
            except ValueError:
                logger.warning(f"Invalid LLAMACPP_PORT value: {os.environ['LLAMACPP_PORT']}")
        
        # Log level
        if "LLAMACPP_LOG_LEVEL" in os.environ:
            self.set("server.log_level", os.environ["LLAMACPP_LOG_LEVEL"])
        
        logger.info("Updated configuration from environment variables")