"""
AI Karen Engine Capsules - Production Skill Injection Framework

Capsules are self-contained cognitive skill modules with:
- Zero-trust security model (JWT + RBAC enforcement)
- Cryptographic validation (SHA-256 integrity, HMAC-SHA512 audit)
- Hardware isolation (CPU affinity, NUMA-free execution)
- Role-based access control (manifest-driven permissions)
- Comprehensive audit logging (Prometheus + forensic logs)
- Prompt safety controls (banned tokens, injection prevention)
- Dynamic discovery and registration
- CORTEX intent mapping integration

Available Capsules:
- DevOps: Infrastructure and deployment operations
- Security: RBAC, auth, key management, compliance
- Memory: NeuroVault maintenance and optimization

Production Standards:
- All capsules require valid JWT tokens
- All operations are cryptographically signed
- All executions are isolated and auditable
- All inputs are sanitized for security
- All capsules inherit from BaseCapsule
- All manifests validated with Pydantic schemas

Research Alignment:
- BSI & ANSSI (2025) Zero-Trust Design Principles
- OWASP GenAI LLM-01 Prompt Injection Prevention
- Phiri (2025) Characteristically Auditable AI Systems
"""

# Core Infrastructure
from ai_karen_engine.capsules.base_capsule import (
    BaseCapsule,
    CapsuleExecutionError,
    CapsuleValidationError,
)

from ai_karen_engine.capsules.schemas import (
    CapsuleManifest,
    CapsuleContext,
    CapsuleResult,
    CapsuleType,
    PromptType,
    SecurityPolicy,
)

from ai_karen_engine.capsules.registry import (
    CapsuleRegistry,
    CapsuleRegistryError,
    get_capsule_registry,
)

from ai_karen_engine.capsules.orchestrator import (
    CapsuleOrchestrator,
    get_capsule_orchestrator,
)

from ai_karen_engine.capsules.cortex_integration import (
    CapsuleCortexAdapter,
    get_cortex_adapter,
    register_capsules_with_cortex,
    dispatch_capsule_from_cortex,
)

from ai_karen_engine.capsules.initialization import (
    initialize_capsule_system,
    get_system_status,
)

# Legacy Capsules (will be migrated to BaseCapsule pattern)
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
    # Core Infrastructure
    "BaseCapsule",
    "CapsuleExecutionError",
    "CapsuleValidationError",
    "CapsuleManifest",
    "CapsuleContext",
    "CapsuleResult",
    "CapsuleType",
    "PromptType",
    "SecurityPolicy",
    "CapsuleRegistry",
    "CapsuleRegistryError",
    "get_capsule_registry",
    "CapsuleOrchestrator",
    "get_capsule_orchestrator",
    # CORTEX Integration
    "CapsuleCortexAdapter",
    "get_cortex_adapter",
    "register_capsules_with_cortex",
    "dispatch_capsule_from_cortex",
    # Initialization
    "initialize_capsule_system",
    "get_system_status",
    # Legacy Capsules
    "DevOpsCapsule",
    "get_devops_handler",
    "devops_handler",
    "SecurityCapsule",
    "get_security_handler",
    "security_handler",
    "MemoryCapsule",
    "get_memory_handler",
    "memory_handler",
    "CapsuleSecurityError",
]
