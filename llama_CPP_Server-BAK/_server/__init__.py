"""
Llama.cpp Server Package

This package contains all the components for the Llama.cpp server:
- Backend implementation
- Security management
- Configuration management
- System optimization
- Performance benchmarking
- Backup and recovery
"""

# Import main components
from .backend import LocalLlamaBackend, BackendError
from .security_manager import SecurityManager, Permission, UserRole
from .config import ServerConfig
from .config_manager import ConfigManager
from .system_optimizer import SystemOptimizer, get_system_optimizer
from .performance_benchmark import PerformanceBenchmark
from .backup_manager import BackupManager, BackupInfo, get_backup_manager
from .server import LlamaServer

# Package version
__version__ = "1.0.0"

# Package metadata
__author__ = "Llama.cpp Server Team"
__email__ = "team@llamacpp.example.com"
__description__ = "A premium llama.cpp server with extensive features"

# Public API
__all__ = [
    "LocalLlamaBackend",
    "BackendError",
    "SecurityManager",
    "Permission",
    "UserRole",
    "ServerConfig",
    "ConfigManager",
    "SystemOptimizer",
    "get_system_optimizer",
    "PerformanceBenchmark",
    "BackupManager",
    "BackupInfo",
    "get_backup_manager",
    "LlamaServer"
]
