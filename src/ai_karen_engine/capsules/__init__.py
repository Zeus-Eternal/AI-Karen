"""
AI Karen Engine Capsules.

Capsules are self-contained execution units with:
- Zero-trust security model
- Cryptographic validation
- Hardware isolation
- Role-based access control
- Comprehensive audit logging
"""

from ai_karen_engine.capsules.devops import (
    DevOpsCapsule,
    get_capsule_handler,
    handler,
    CapsuleSecurityError,
)

__all__ = [
    "DevOpsCapsule",
    "get_capsule_handler",
    "handler",
    "CapsuleSecurityError",
]
