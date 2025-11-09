"""
DevOps Capsule - Nuclear-Grade Implementation for AI Karen.

This module provides:
- Zero-trust prompt execution with cryptographic validation
- Hardware-aware LLM operations (cross-platform)
- Military-grade RBAC with JWT validation
- Quantum-resistant audit trails
- Observability-ready logging (Prometheus integration)
"""

from ai_karen_engine.capsules.devops.handler import (
    DevOpsCapsule,
    get_capsule_handler,
    handler,
    CapsuleSecurityError,
    validate_jwt,
    get_correlation_id,
)

__all__ = [
    "DevOpsCapsule",
    "get_capsule_handler",
    "handler",
    "CapsuleSecurityError",
    "validate_jwt",
    "get_correlation_id",
]
