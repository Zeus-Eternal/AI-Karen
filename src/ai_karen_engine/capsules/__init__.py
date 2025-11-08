"""
AI Karen Engine Capsules - Production Security Framework

Capsules are self-contained execution units with:
- Zero-trust security model (JWT + RBAC enforcement)
- Cryptographic validation (SHA-256 integrity, HMAC-SHA512 audit)
- Hardware isolation (CPU affinity, NUMA-free execution)
- Role-based access control (manifest-driven permissions)
- Comprehensive audit logging (Prometheus + forensic logs)
- Prompt safety controls (banned tokens, injection prevention)

Available Capsules:
- DevOps: Infrastructure and deployment operations
- Security: RBAC, auth, key management, compliance
- Memory: NeuroVault maintenance and optimization

Production Standards:
- All capsules require valid JWT tokens
- All operations are cryptographically signed
- All executions are isolated and auditable
- All inputs are sanitized for security

Research Alignment:
- BSI & ANSSI (2025) Zero-Trust Design Principles
- OWASP GenAI LLM-01 Prompt Injection Prevention
- Phiri (2025) Characteristically Auditable AI Systems
"""

from ai_karen_engine.capsules.devops import (
    DevOpsCapsule,
    get_capsule_handler as get_devops_handler,
    handler as devops_handler,
    CapsuleSecurityError,
)

from ai_karen_engine.capsules.security import (
    SecurityCapsule,
    get_capsule_handler as get_security_handler,
    handler as security_handler,
)

from ai_karen_engine.capsules.memory import (
    MemoryCapsule,
    get_capsule_handler as get_memory_handler,
    handler as memory_handler,
)

__all__ = [
    # DevOps Capsule
    "DevOpsCapsule",
    "get_devops_handler",
    "devops_handler",
    # Security Capsule
    "SecurityCapsule",
    "get_security_handler",
    "security_handler",
    # Memory Capsule
    "MemoryCapsule",
    "get_memory_handler",
    "memory_handler",
    # Common
    "CapsuleSecurityError",
]
