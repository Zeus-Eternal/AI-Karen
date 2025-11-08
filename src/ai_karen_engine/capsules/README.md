# Kari AI Capsule System

**Production-Grade Skill Injection Framework**

---

## 🎯 What Are Capsules?

Capsules are **self-contained cognitive skill modules** that extend Kari's capabilities without modifying core systems (CORTEX, Reasoning Engine, Memory subsystems).

> "A Capsule = a contained skill + its own runtime + its own mind."

---

## 🏗️ Architecture

```
Capsule Layer (Skill Injection Point)
├── BaseCapsule (Abstract Interface)
├── CapsuleRegistry (Auto-Discovery)
├── CapsuleOrchestrator (Lifecycle Management)
├── CORTEX Integration (Intent Mapping)
└── Production Capsules
    ├── devops/
    ├── security/
    └── memory/
```

---

## 📦 Available Capsules

| Capsule | Type | Capabilities | Status |
|---------|------|--------------|--------|
| **DevOps** | `devops` | Infrastructure ops, deployments | ✅ Production |
| **Security** | `security` | RBAC, auth, compliance | ✅ Production |
| **Memory** | `memory` | NeuroVault maintenance | ✅ Production |

---

## 🚀 Quick Start

### Using a Capsule

```python
from ai_karen_engine.capsules import get_capsule_orchestrator

orchestrator = get_capsule_orchestrator()
orchestrator.initialize()

# Execute by ID
result = orchestrator.execute_capsule(
    capsule_id="capsule.devops",
    request={"query": "deploy to production"},
    user_ctx={"sub": "admin", "roles": ["system.admin", "capsule.devops"]}
)

print(result.result)
```

### Creating a New Capsule

See **[Capsule Skill Developer Handbook](/docs/capsules/CAPSULE_SKILL_DEVELOPER_HANDBOOK.md)** for complete guide.

**Minimum steps:**

1. Create directory: `src/ai_karen_engine/capsules/my_skill/`
2. Add `manifest.yaml` (see template below)
3. Add `handler.py` with class inheriting from `BaseCapsule`
4. Implement `_execute_core()` method
5. Test and deploy

**Template:**

```python
# handler.py
from ai_karen_engine.capsules.base_capsule import BaseCapsule
from ai_karen_engine.capsules.schemas import CapsuleContext

class MySkillCapsule(BaseCapsule):
    def _execute_core(self, context: CapsuleContext):
        # Your logic here
        return {"message": "Hello from my skill!"}
```

```yaml
# manifest.yaml
id: "capsule.my_skill"
name: "My Skill"
version: "1.0.0"
description: "Does something awesome"
type: "utility"
required_roles: ["system.admin"]
author: "Your Name"
created: "2025-11-08"
updated: "2025-11-08"
```

---

## 🧬 Capsule Types

| Type | Use Case | Examples |
|------|----------|----------|
| **reasoning** | Logic, deduction, planning | `logic_refinement`, `multi_agent_planning` |
| **memory** | Memory operations | `episodic_consolidation`, `context_ranking` |
| **neuro_recall** | Recall enhancement | `semantic_retriever`, `temporal_recall` |
| **response** | Response generation | `emotionally_adaptive_reply`, `style_transfer` |
| **observation** | System monitoring | `system_monitor`, `performance_tracker` |
| **security** | Security operations | `threat_detection`, `anomaly_audit` |
| **integration** | External APIs | `web_research_agent`, `data_extraction` |
| **predictive** | Forecasting | `sentiment_forecaster`, `task_success_predictor` |
| **utility** | Helper functions | `file_parser`, `sql_builder` |
| **metacognitive** | Self-awareness | `self_reflection`, `learning_optimizer` |
| **personalization** | User adaptation | `user_profile_enhancer`, `preference_adaptation` |
| **creative** | Content generation | `story_generator`, `art_style_blender` |
| **autonomous** | Task automation | `task_executor`, `workflow_coordinator` |

---

## 🔒 Security Features

All capsules enforce:

- ✅ **JWT + RBAC** - Role-based access control
- ✅ **Input sanitization** - XSS, SQL injection, command injection prevention
- ✅ **Prompt safety** - Banned token detection
- ✅ **Hardware isolation** - CPU affinity enforcement
- ✅ **Audit logging** - HMAC-SHA512 signed trails
- ✅ **Metrics emission** - Prometheus integration
- ✅ **Circuit breakers** - Failure isolation
- ✅ **Timeout enforcement** - Configurable max execution time

---

## 📊 Observability

### Prometheus Metrics

```
capsule_executions_total{capsule_id="capsule.devops", status="success"}
capsule_execution_seconds{capsule_id="capsule.devops"}
```

### Logging

```python
import logging
logger = logging.getLogger("capsules")
```

All executions log:
- Correlation ID
- User context
- Execution time
- Success/failure status

---

## 🎓 Developer Resources

- **[Developer Handbook](/docs/capsules/CAPSULE_SKILL_DEVELOPER_HANDBOOK.md)** - Complete guide
- **[Manifest Schema Reference](/docs/capsules/MANIFEST_SCHEMA.md)** - Schema documentation
- **[API Reference](/docs/capsules/API_REFERENCE.md)** - Full API docs
- **Examples** - See `devops/`, `security/`, `memory/` capsules

---

## 🧪 Testing

```bash
# Unit tests
pytest src/ai_karen_engine/capsules/tests/

# Integration tests
pytest src/ai_karen_engine/capsules/tests/integration/

# Specific capsule
pytest src/ai_karen_engine/capsules/my_skill/tests/
```

---

## 🔄 CORTEX Integration

Capsules automatically register with CORTEX on initialization:

```python
from ai_karen_engine.capsules.cortex_integration import register_capsules_with_cortex

# Called during app startup
register_capsules_with_cortex()
```

**Intent Resolution Flow:**

```
User: "optimize memory"
  ↓
CORTEX: intent="capsule.memory"
  ↓
Orchestrator: execute_capsule("capsule.memory", ...)
  ↓
MemoryCapsule: _execute_core()
  ↓
Result
```

---

## 📈 Scaling

Capsules support:

- ✅ **Dynamic discovery** - Auto-scan on startup
- ✅ **Lazy loading** - Load only when needed
- ✅ **Hot reload** - Reload without restart
- ✅ **Versioning** - Semantic versioning support
- ✅ **A/B testing** - Performance comparison
- ✅ **Circuit breakers** - Automatic failure isolation
- ✅ **Load balancing** - Multiple capsules per capability (future)

---

## 🚨 Common Issues

### Capsule Not Discovered

**Problem:** Capsule not appearing in registry

**Solution:**
1. Check `manifest.yaml` is valid YAML
2. Ensure `id` starts with `capsule.`
3. Verify directory is in `src/ai_karen_engine/capsules/`
4. Check logs for validation errors

### RBAC Permission Denied

**Problem:** `Insufficient privileges` error

**Solution:**
1. Check `required_roles` in manifest
2. Verify user_ctx contains all required roles
3. Roles are case-sensitive!

### Circuit Breaker Open

**Problem:** Capsule execution blocked

**Solution:**
1. Check recent failures (5 consecutive failures open circuit)
2. Wait 5 minutes for auto-reset
3. Fix root cause and manually reload: `orchestrator.reload_capsules()`

---

## 📞 Support

- **Issues**: GitHub Issues
- **Docs**: `/docs/capsules/`
- **Questions**: Ask Zeus

---

## 🎯 Roadmap

- [ ] Multi-version support (run v1.0 and v2.0 simultaneously)
- [ ] Performance benchmarking dashboard
- [ ] Capsule marketplace (community capsules)
- [ ] Visual capsule builder
- [ ] Automated testing framework
- [ ] Load balancing for high-traffic capsules

---

**Built with ❤️ by Zeus | Last Updated: 2025-11-08**
