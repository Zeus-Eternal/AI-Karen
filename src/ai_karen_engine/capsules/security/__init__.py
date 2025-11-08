"""
Security Capsule - Zero-Trust Security Operations

This capsule handles RBAC, authentication, key management, and compliance operations.
"""

from ai_karen_engine.capsules.security.handler import (
    SecurityCapsule,
    get_capsule_handler,
    handler,
)

__all__ = [
    "SecurityCapsule",
    "get_capsule_handler",
    "handler",
]
