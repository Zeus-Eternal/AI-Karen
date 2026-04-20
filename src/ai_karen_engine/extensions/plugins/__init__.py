"""
Plugins Module

Contains user and community plugin packages for the extension system.
"""

# We can't use hyphens in python imports directly, so we'll use a dynamic approach or rename back if needed.
# However, for the extension system's discovery, it just needs to find the folders.

__all__ = [
    "web-search",
]
