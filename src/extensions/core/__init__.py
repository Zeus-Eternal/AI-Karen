"""
Core extension integration helpers exposed to the server.
"""

from .integration import initialize_extensions, ExtensionSystemIntegration

__all__ = [
    "initialize_extensions",
    "ExtensionSystemIntegration",
]
