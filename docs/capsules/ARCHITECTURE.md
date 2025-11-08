# Capsule System Architecture

**Production-Grade Skill Injection Framework for Kari AI**

---

## 🎯 Executive Summary

The Capsule System is a **skill injection framework** that enables extending Kari's cognitive capabilities through self-contained, secure, observable modules without modifying core systems.

**Design Philosophy:**
> "A Capsule = a contained skill + its own runtime + its own mind."

---

## 🏗️ System Architecture

### High-Level Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     USER REQUEST                             │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
         ┌─────────────────────────────┐
         │  CORTEX Intent Resolution   │
         │  - Analyzes query            │
         │  - Resolves intent           │
         │  - Routes to handler         │
         └──────────┬─────────┬────────┘
                    │         │
         ┌──────────┘         └─────────────┐
         │                                   │
         ▼                                   ▼
  ┌─────────────┐                  ┌───────────────────┐
  │   Plugins   │                  │ Capsule Orchestrator│
  │  (Legacy)   │                  │  - Discovery        │
  └─────────────┘                  │  - Validation       │
                                   │  - Execution        │
                                   │  - Circuit Breaking │
                                   └──────────┬──────────┘
                                              │
                                   ┌──────────┴──────────┐
                                   │  Capsule Registry    │
                                   │  - Auto-discovery    │
                                   │  - Manifest validation│
                                   │  - Lazy loading      │
                                   └──────────┬──────────┘
                                              │
                     ┌────────────────────────┼────────────────────┐
                     │                        │                    │
                     ▼                        ▼                    ▼
              ┌────────────┐           ┌────────────┐      ┌────────────┐
              │  DevOps    │           │  Security  │      │   Memory   │
              │  Capsule   │           │  Capsule   │      │  Capsule   │
              └────────────┘           └────────────┘      └────────────┘
                     │                        │                    │
                     └────────────────────────┼────────────────────┘
                                              │
                                              ▼
                                   ┌─────────────────────┐
                                   │  Shared Services     │
                                   │  - LLM Registry      │
                                   │  - Memory Manager    │
                                   │  - Prometheus        │
                                   │  - Audit Logger      │
                                   └─────────────────────┘
```

---

## 🧩 Core Components

### 1. BaseCapsule (Abstract Base Class)

**Location:** `src/ai_karen_engine/capsules/base_capsule.py`

**Responsibilities:**
- Defines standard interface for all capsules
- Implements template method pattern for execution lifecycle
- Enforces RBAC validation
- Handles input sanitization
- Provides lifecycle hooks (pre/post execution)

**Key Methods:**
```python
# Abstract (must implement)
_execute_core(context: CapsuleContext) -> Any

# Lifecycle hooks (optional)
_pre_execution_hook(context: CapsuleContext) -> None
_post_execution_hook(result: Any, context: CapsuleContext) -> None

# Template method (don't override)
execute(request, user_ctx, correlation_id, memory_context) -> CapsuleResult
```

**Design Pattern:** Template Method + Strategy

---

### 2. CapsuleRegistry

**Location:** `src/ai_karen_engine/capsules/registry.py`

**Responsibilities:**
- Auto-discover capsules from filesystem
- Validate manifests using Pydantic schemas
- Lazy-load capsule classes
- Cache instances
- Provide lookup services

**Key Features:**
- **Singleton pattern** - One global registry
- **Lazy loading** - Only load when needed
- **Hot reload** - Can reload instances without restart
- **Type filtering** - List by capsule type
- **Metrics tracking** - Discovery success/failure counts

**Discovery Algorithm:**
```python
1. Scan capsules directory
2. For each subdirectory:
   a. Look for manifest.yaml
   b. Validate manifest schema
   c. Register metadata
   d. Store manifest
3. Return count of discovered capsules
```

---

### 3. CapsuleOrchestrator

**Location:** `src/ai_karen_engine/capsules/orchestrator.py`

**Responsibilities:**
- Manage capsule lifecycle
- Execute capsules with observability
- Circuit breaking for failure isolation
- Intent → Capsule mapping
- Capability-based routing

**Key Features:**

**Circuit Breaker:**
```python
Failure threshold: 5 consecutive failures
Cooldown period: 5 minutes
Auto-reset: Yes
```

**Execution Flow:**
```python
1. Check circuit breaker
2. Get capsule instance from registry
3. Execute with metrics
4. Record success/failure
5. Update circuit breaker state
6. Return result
```

**Design Patterns:**
- Singleton
- Circuit Breaker
- Bulkhead (hardware isolation)

---

### 4. Schema Validation

**Location:** `src/ai_karen_engine/capsules/schemas.py`

**Pydantic Models:**

#### CapsuleManifest
```python
- id: str (pattern: ^capsule\.)
- name: str
- version: str (semver)
- type: CapsuleType (enum)
- required_roles: List[str]
- security_policy: SecurityPolicy
- ... (30+ fields)
```

#### CapsuleContext
```python
- user_ctx: Dict
- request: Dict
- correlation_id: str
- memory_context: Optional[List]
- audit_payload: Optional[Dict]
```

#### CapsuleResult
```python
- result: Any
- metadata: Dict
- audit: Optional[Dict]
- security: Optional[Dict]
- metrics: Optional[Dict]
- errors: Optional[List[str]]
```

---

### 5. CORTEX Integration

**Location:** `src/ai_karen_engine/capsules/cortex_integration.py`

**Responsibilities:**
- Adapter between capsules and CORTEX dispatch
- Register capsule intents
- Map capabilities to intents
- Route execution through CORTEX

**Integration Points:**

```python
# Registration (during app init)
register_capsules_with_cortex()

# Dispatch (during runtime)
result = await dispatch_capsule_from_cortex(
    intent="capsule.my_skill",
    user_ctx={...},
    query="...",
)
```

**Flow:**
```
User Query
  ↓
CORTEX: resolve_intent() → "capsule.my_skill"
  ↓
CapsuleCortexAdapter: resolve_capsule_intent()
  ↓
CapsuleOrchestrator: execute_capsule()
  ↓
Capsule Instance: execute()
  ↓
Result
```

---

### 6. Initialization System

**Location:** `src/ai_karen_engine/capsules/initialization.py`

**Responsibilities:**
- Bootstrap capsule system during app startup
- Auto-discover capsules
- Register with CORTEX
- Provide system status

**Usage:**
```python
from ai_karen_engine.capsules import initialize_capsule_system

# During app startup
metrics = initialize_capsule_system(
    auto_discover=True,
    register_with_cortex=True
)

# Returns:
{
    "initialized": True,
    "capsules_discovered": 3,
    "cortex_registered": True,
    "errors": []
}
```

---

## 🔒 Security Architecture

### Zero-Trust Model

All capsules enforce:

1. **Authentication** - JWT token validation
2. **Authorization** - RBAC role checking
3. **Input Sanitization** - Multi-layer defense
4. **Audit Logging** - HMAC-SHA512 signed trails
5. **Hardware Isolation** - CPU affinity enforcement
6. **Timeout Enforcement** - Max execution time limits

### Security Layers

```
┌─────────────────────────────────────────┐
│  Layer 1: JWT Validation                │
│  - Verify token signature                │
│  - Check expiration                      │
└──────────────┬──────────────────────────┘
               ▼
┌─────────────────────────────────────────┐
│  Layer 2: RBAC Enforcement              │
│  - Extract user roles                    │
│  - Verify against required_roles         │
└──────────────┬──────────────────────────┘
               ▼
┌─────────────────────────────────────────┐
│  Layer 3: Input Sanitization            │
│  - HTML encoding                         │
│  - Unicode control char removal          │
│  - Banned token detection                │
│  - SQL injection prevention              │
│  - Shell injection prevention            │
└──────────────┬──────────────────────────┘
               ▼
┌─────────────────────────────────────────┐
│  Layer 4: Prompt Safety                 │
│  - Validate rendered prompts             │
│  - Check for banned patterns             │
└──────────────┬──────────────────────────┘
               ▼
┌─────────────────────────────────────────┐
│  Layer 5: Tool Whitelisting             │
│  - Verify tool access permissions        │
│  - Enforce allowed_tools list            │
└──────────────┬──────────────────────────┘
               ▼
         Execution
```

### Banned Tokens

```python
BANNED_TOKENS = {
    "system(", "exec(", "import ", "os.",
    "open(", "eval(", "subprocess", "pickle",
    "base64", "__import__", "compile(",
    "globals(", "locals(", "__builtins__"
}
```

---

## 📊 Observability Architecture

### Metrics (Prometheus)

```python
# Registry metrics
capsule_discovery_total
capsule_load_success_total
capsule_load_failure_total

# Orchestrator metrics
capsule_executions_total{capsule_id, status}
capsule_execution_seconds{capsule_id}
capsule_circuit_breaker_open{capsule_id}

# Per-capsule metrics (customizable)
capsule_devops_success_total
capsule_security_success_total
capsule_memory_success_total
```

### Logging

**Structured logging with correlation IDs:**

```python
logger.info(
    "Capsule executed successfully",
    extra={
        "correlation_id": "abc-123",
        "capsule_id": "capsule.devops",
        "user": "admin",
        "execution_time": 1.23
    }
)
```

### Audit Trails

**HMAC-SHA512 signed:**

```python
audit_payload = {
    "user": "admin",
    "action": "devops_task",
    "timestamp": 1699999999,
    "correlation_id": "abc-123",
    "capsule": "devops"
}
audit_payload["signature"] = hmac_sha512(audit_payload)
```

---

## 🔄 Execution Lifecycle

### Complete Flow

```python
1. User submits request
2. CORTEX resolves intent
3. CapsuleCortexAdapter receives intent
4. Orchestrator checks circuit breaker
5. Registry loads/retrieves capsule instance
6. Capsule.execute() begins:
   a. Validate JWT (BaseCapsule)
   b. Check RBAC (BaseCapsule)
   c. Sanitize input (BaseCapsule)
   d. Build CapsuleContext (BaseCapsule)
   e. Call _pre_execution_hook() (Capsule)
   f. Call _execute_core() (Capsule)
   g. Call _post_execution_hook() (Capsule)
   h. Package CapsuleResult (BaseCapsule)
7. Orchestrator records metrics
8. Orchestrator updates circuit breaker
9. Result returned to CORTEX
10. CORTEX returns to user
```

**Timing Breakdown:**
```
Total: ~500ms (typical)
├── CORTEX resolution: 10ms
├── Registry lookup: 5ms
├── RBAC + sanitization: 20ms
├── Core execution: 400ms (LLM call)
└── Result packaging: 5ms
```

---

## 🧬 Capsule Taxonomy

### By Type

| Type | Count | Purpose |
|------|-------|---------|
| **reasoning** | 0 | Logic, deduction, planning |
| **memory** | 1 | Memory operations |
| **security** | 1 | Security operations |
| **devops** | 1 | Infrastructure management |
| **integration** | 0 | External API integration |
| **predictive** | 0 | Forecasting, prediction |
| **utility** | 0 | Helper functions |
| **metacognitive** | 0 | Self-awareness |
| **personalization** | 0 | User adaptation |
| **creative** | 0 | Content generation |
| **autonomous** | 0 | Task automation |

### By Capability

```
Total Capabilities: ~30 (across 3 capsules)

DevOps Capabilities:
- provision_infrastructure
- restart_service
- deploy_code
- apply_patch
- run_compliance_scan
- view_audit_log
- manage_rbac

Security Capabilities:
- rbac_management
- key_rotation
- auth_validation
- compliance_check
- security_audit
- threat_detection

Memory Capabilities:
- memory_refresh
- memory_prune
- vector_compaction
- memory_health_check
- memory_optimization
- cache_invalidation
```

---

## 🚀 Scaling Considerations

### Current Limitations

1. **Single-threaded execution** - One capsule at a time (per request)
2. **No load balancing** - Single instance per capsule
3. **No distributed execution** - All local
4. **No caching layer** - Results not cached

### Future Enhancements

1. **Parallel execution** - Multiple capsules per request
2. **Load balancing** - Multiple instances per capability
3. **Distributed execution** - Kubernetes pods
4. **Result caching** - Redis cache layer
5. **A/B testing** - Multiple versions side-by-side
6. **Auto-scaling** - Scale based on demand

---

## 🧪 Testing Strategy

### Unit Tests

Test each component in isolation:
- BaseCapsule: Template method, RBAC, sanitization
- Registry: Discovery, validation, loading
- Orchestrator: Execution, circuit breaking
- Schemas: Pydantic validation

### Integration Tests

Test component interactions:
- Registry + Orchestrator
- Orchestrator + CORTEX
- End-to-end capsule execution

### Performance Tests

Test under load:
- 100 concurrent capsule executions
- Circuit breaker behavior under failures
- Memory usage with 50+ capsules

---

## 📚 Related Documentation

- **[Developer Handbook](/docs/capsules/CAPSULE_SKILL_DEVELOPER_HANDBOOK.md)** - How to build capsules
- **[README](/src/ai_karen_engine/capsules/README.md)** - Quick start guide
- **[Manifest Schema](/docs/capsules/MANIFEST_SCHEMA.md)** - Schema reference

---

**Built with ❤️ by Zeus | Last Updated: 2025-11-08**
