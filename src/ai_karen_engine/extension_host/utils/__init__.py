"""
Utility modules for the KARI extension host.

This package contains utility modules for validation and other helper functions
used by the extension host.
"""

from .validation import (
    validate_manifest,
    validate_extension_config,
    validate_extension_name,
    validate_hook_point,
    validate_permissions
)

__all__ = [
    "validate_manifest",
    "validate_extension_config", 
    "validate_extension_name",
    "validate_hook_point",
    "validate_permissions"
]