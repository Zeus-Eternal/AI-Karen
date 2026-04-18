"""
Extensions Service Recovery Package

Provides recovery mechanisms for extension services with graceful degradation.
"""

from .extension_service_recovery import (
    initialize_extension_service_recovery_manager,
    get_extension_service_recovery_manager,
    shutdown_extension_service_recovery_manager,
)

__all__ = [
    "initialize_extension_service_recovery_manager",
    "get_extension_service_recovery_manager",
    "shutdown_extension_service_recovery_manager",
]
