# Capsule Skill Developer Handbook

**Version:** 1.0.0
**Author:** Zeus - Chief Architect
**Last Updated:** 2025-11-08

---

## 🧠 Executive Summary

This handbook is the **official developer guide** for creating new cognitive skill capsules in Kari AI. Capsules are self-contained skill modules that extend Kari's capabilities without modifying core systems (CORTEX, Reasoning Engine, Memory subsystems).

**Key Principle:**
> "A Capsule = a contained skill + its own runtime + its own mind."

---

## 📚 Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Capsule Anatomy](#capsule-anatomy)
3. [Development Workflow](#development-workflow)
4. [BaseCapsule API Reference](#basecapsule-api-reference)
5. [Manifest Schema Reference](#manifest-schema-reference)
6. [Security Requirements](#security-requirements)
7. [CORTEX Integration](#cortex-integration)
8. [Testing Guidelines](#testing-guidelines)
9. [Deployment Checklist](#deployment-checklist)
10. [Examples](#examples)

---

## 🏗️ Architecture Overview

### System Context

```
┌─────────────────────────────────────────────────┐
│              CORTEX (Intent Router)              │
│  - Receives user queries                         │
│  - Resolves intents                              │
│  - Dispatches to plugins OR capsules             │
└──────────────┬──────────────────────────────────┘
               │
         ┌─────┴──────┐
         │            │
         ▼            ▼
  ┌────────────┐  ┌──────────────────┐
  │  Plugins   │  │ Capsule Orchestrator │
  └────────────┘  └──────────┬───────────┘
                              │
                    ┌─────────┴─────────┐
                    │ Capsule Registry   │
                    │ - Auto-discovery   │
                    │ - Validation       │
                    │ - Lazy loading     │
                    └─────────┬──────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
        ┌──────────┐    ┌──────────┐    ┌──────────┐
        │ DevOps   │    │ Security │    │  Memory  │
        │ Capsule  │    │ Capsule  │    │ Capsule  │
        └──────────┘    └──────────┘    └──────────┘
```

### Core Components

| Component | Purpose |
|-----------|---------|
| **BaseCapsule** | Abstract base class - all capsules inherit from this |
| **CapsuleRegistry** | Auto-discovers and registers capsules from filesystem |
| **CapsuleOrchestrator** | Manages lifecycle, execution, circuit breakers |
| **CapsuleManifest** | Pydantic schema for manifest validation |
| **CapsuleContext** | Runtime context passed to capsule execution |
| **CapsuleResult** | Standardized execution output |

---

## 🧬 Capsule Anatomy

Every capsule is a directory with the following structure:

```
my_capsule/
├── manifest.yaml       # Required: Capsule configuration
├── handler.py          # Required: Python entrypoint with capsule class
├── prompt.txt          # Optional: Prompt template
├── __init__.py         # Optional: Package exports
├── schemas.py          # Optional: Custom Pydantic schemas
├── tests/              # Recommended: Unit tests
│   └── test_handler.py
└── README.md           # Recommended: Documentation
```

### Minimum Viable Capsule

**1. `manifest.yaml`**
```yaml
id: "capsule.my_skill"
name: "My Skill Capsule"
version: "1.0.0"
description: |
  A skill that does something awesome.

type: "utility"
capabilities:
  - process_data
  - validate_input

required_roles:
  - "system.admin"

allowed_tools:
  - "llm.generate_text"

security_policy:
  allow_network_access: false
  allow_file_system_access: false
  require_hardware_isolation: true
  max_execution_time: 60

auditable: true
sandboxed: true
prometheus_enabled: true

max_tokens: 256
temperature: 0.7

author: "Your Name"
created: "2025-11-08"
updated: "2025-11-08"
```

**2. `handler.py`**
```python
"""My Skill Capsule Handler"""

from ai_karen_engine.capsules.base_capsule import BaseCapsule, CapsuleExecutionError
from ai_karen_engine.capsules.schemas import CapsuleContext

class MySkillCapsule(BaseCapsule):
    """My awesome skill capsule"""

    def _execute_core(self, context: CapsuleContext):
        """Core execution logic"""

        # Access request data
        query = context.request.get("query", "")
        user = context.user_ctx.get("sub", "unknown")

        # Your logic here
        result = self._process_query(query, user)

        return result

    def _process_query(self, query: str, user: str):
        """Your custom logic"""
        return {
            "message": f"Processed query from {user}",
            "data": query.upper()
        }
```

**3. `prompt.txt` (optional)**
```
You are a helpful assistant specialized in {{ context.capability }}.

User query: {{ context.query }}

Provide a detailed response.
```

---

## 🛠️ Development Workflow

### Step 1: Design Your Skill

Answer these questions:
- **What cognitive function** does this capsule provide? (reasoning, memory, response, etc.)
- **What capabilities** does it expose? (list specific actions)
- **What inputs** does it need?
- **What outputs** does it produce?
- **What RBAC roles** should have access?
- **Does it need LLM access?** If yes, what tools?

### Step 2: Create Capsule Directory

```bash
cd src/ai_karen_engine/capsules
mkdir my_skill
cd my_skill
```

### Step 3: Write Manifest

Use the template above. Key decisions:
- **ID**: Must start with `capsule.` and use snake_case
- **Type**: Choose from enum (see schema reference)
- **Capabilities**: List concrete actions (used for CORTEX intent mapping)
- **Security Policy**: Be restrictive by default

### Step 4: Implement Handler

```python
from ai_karen_engine.capsules.base_capsule import BaseCapsule
from ai_karen_engine.capsules.schemas import CapsuleContext

class MySkillCapsule(BaseCapsule):

    def _execute_core(self, context: CapsuleContext):
        """
        Implement your core logic here.

        Context provides:
        - context.user_ctx: User session data + roles
        - context.request: Sanitized request payload
        - context.correlation_id: Trace ID
        - context.memory_context: Retrieved memories (if applicable)

        Must return: Any serializable type
        """
        # Your implementation
        pass

    def _pre_execution_hook(self, context: CapsuleContext):
        """Optional: Setup before execution"""
        pass

    def _post_execution_hook(self, result, context: CapsuleContext):
        """Optional: Cleanup after execution"""
        pass
```

### Step 5: Test Locally

```python
from pathlib import Path
from ai_karen_engine.capsules.registry import get_capsule_registry

# Load capsule
registry = get_capsule_registry()
registry.discover(Path("src/ai_karen_engine/capsules"))

# Get instance
capsule = registry.get_capsule("capsule.my_skill")

# Execute
result = capsule.execute(
    request={"query": "test"},
    user_ctx={"sub": "test_user", "roles": ["system.admin"]},
    correlation_id="test-123"
)

print(result)
```

### Step 6: Write Tests

```python
# tests/test_handler.py
import pytest
from pathlib import Path
from my_skill.handler import MySkillCapsule

def test_capsule_initialization():
    capsule = MySkillCapsule(Path(__file__).parent.parent)
    assert capsule.get_id() == "capsule.my_skill"

def test_capsule_execution():
    capsule = MySkillCapsule(Path(__file__).parent.parent)

    result = capsule.execute(
        request={"query": "hello"},
        user_ctx={"sub": "test", "roles": ["system.admin"]},
        correlation_id="test-001"
    )

    assert result.result is not None
    assert result.metadata["capsule_id"] == "capsule.my_skill"
```

### Step 7: Register with System

Capsules are auto-discovered on startup. To manually trigger:

```python
from ai_karen_engine.capsules.cortex_integration import register_capsules_with_cortex

# This is called during app initialization
register_capsules_with_cortex()
```

---

## 📖 BaseCapsule API Reference

### Core Methods (Implement These)

#### `_execute_core(context: CapsuleContext) -> Any`
**Required.** Your core business logic.

**Args:**
- `context`: CapsuleContext with user_ctx, request, correlation_id, memory_context

**Returns:** Any serializable type

**Raises:** CapsuleExecutionError on failure

---

### Lifecycle Hooks (Optional)

#### `_pre_execution_hook(context: CapsuleContext) -> None`
Called before `_execute_core`. Use for setup tasks.

#### `_post_execution_hook(result: Any, context: CapsuleContext) -> None`
Called after `_execute_core`. Use for cleanup.

---

### Utility Methods (Use These)

#### `get_manifest() -> CapsuleManifest`
Returns the capsule's manifest.

#### `get_capabilities() -> List[str]`
Returns list of capabilities.

#### `get_id() -> str`
Returns capsule ID.

#### `get_version() -> str`
Returns semantic version.

---

### Main Entry Point (Don't Override)

#### `execute(request, user_ctx, correlation_id, memory_context) -> CapsuleResult`

This is the **template method** that:
1. Validates RBAC
2. Sanitizes input
3. Calls pre-execution hook
4. Calls `_execute_core`
5. Calls post-execution hook
6. Packages result

**Do not override** unless you have a very good reason.

---

## 📋 Manifest Schema Reference

### Required Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `id` | string | Unique ID (must start with `capsule.`) | `"capsule.my_skill"` |
| `name` | string | Human-readable name | `"My Skill Capsule"` |
| `version` | string | Semantic version (X.Y.Z) | `"1.0.0"` |
| `description` | string | Multi-line description | `"Does XYZ..."` |
| `type` | enum | Capsule classification | `"reasoning"` |
| `required_roles` | list[string] | RBAC roles needed | `["system.admin"]` |
| `author` | string | Author name | `"Zeus"` |
| `created` | string | Creation date (YYYY-MM-DD) | `"2025-11-08"` |
| `updated` | string | Last update date | `"2025-11-08"` |

### Optional Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `capabilities` | list[string] | `[]` | List of capabilities |
| `entrypoint` | string | `"handler.py"` | Python module path |
| `prompt_file` | string | `"prompt.txt"` | Prompt template path |
| `prompt_type` | enum | `"jinja2"` | Template format |
| `requires` | list[string] | `[]` | Capsule dependencies |
| `memory_scope` | list[string] | `[]` | Memory access (vector, short_term, long_term) |
| `allowed_tools` | list[string] | `[]` | Tool whitelist |
| `max_tokens` | int | `256` | LLM max tokens |
| `temperature` | float | `0.7` | LLM temperature |
| `priority` | int | `50` | Execution priority (0-100) |
| `tags` | list[string] | `[]` | Search tags |

### CapsuleType Enum

```python
class CapsuleType(str, Enum):
    REASONING = "reasoning"          # Logic, deduction, planning
    MEMORY = "memory"                # Memory operations
    NEURO_RECALL = "neuro_recall"    # Recall enhancement
    RESPONSE = "response"            # Response generation
    OBSERVATION = "observation"      # System monitoring
    SECURITY = "security"            # Security operations
    INTEGRATION = "integration"      # External API integration
    PREDICTIVE = "predictive"        # Prediction/forecasting
    UTILITY = "utility"              # Helper functions
    METACOGNITIVE = "metacognitive"  # Self-awareness
    PERSONALIZATION = "personalization" # User adaptation
    CREATIVE = "creative"            # Content generation
    AUTONOMOUS = "autonomous"        # Task automation
    DEVOPS = "devops"               # Infrastructure ops
```

### SecurityPolicy Schema

```yaml
security_policy:
  allow_network_access: false        # Network calls allowed?
  allow_file_system_access: false    # Filesystem access allowed?
  allow_system_calls: false          # System commands allowed?
  require_hardware_isolation: true   # CPU affinity enforcement?
  max_execution_time: 60            # Max seconds (1-600)
```

---

## 🔒 Security Requirements

### Zero-Trust Principles

All capsules must:
1. **Validate all inputs** - BaseCapsule does this automatically
2. **Enforce RBAC** - BaseCapsule checks `required_roles`
3. **Sign audit trails** - Use HMAC-SHA512 (see examples)
4. **Emit metrics** - Prometheus counters/histograms
5. **Sanitize prompts** - Check for banned tokens, injection patterns

### Banned Tokens

These strings **cannot** appear in user input:
- `system(`, `exec(`, `eval(`
- `import `, `os.`, `subprocess`
- `pickle`, `base64`, `__import__`
- `compile(`, `globals(`, `locals(`
- `__builtins__`

### Input Sanitization

BaseCapsule automatically:
- HTML-encodes input
- Removes Unicode control characters
- Checks for SQL injection patterns
- Checks for shell injection patterns
- Enforces max length (8192 chars)

### RBAC Enforcement

```python
# In manifest:
required_roles:
  - "system.admin"
  - "capsule.my_skill"

# User context must have ALL roles:
user_ctx = {
    "sub": "user123",
    "roles": ["system.admin", "capsule.my_skill", "user"]
}
```

---

## 🎯 CORTEX Integration

### How Capsules Register with CORTEX

1. **Auto-Discovery**: Registry scans `src/ai_karen_engine/capsules/`
2. **Intent Mapping**: Each capsule ID becomes an intent
3. **Capability Mapping**: Each capability becomes searchable
4. **Dispatch**: CORTEX routes intent → Orchestrator → Capsule

### Example Flow

```
User: "optimize my memory"
  ↓
CORTEX resolves → intent="capsule.memory"
  ↓
CapsuleCortexAdapter.execute_capsule_intent()
  ↓
CapsuleOrchestrator.execute_capsule("capsule.memory", ...)
  ↓
MemoryCapsule._execute_core()
  ↓
Return CapsuleResult
```

### Registering Capabilities

Capabilities are **more granular** than intents:

```yaml
# manifest.yaml
id: "capsule.data_processor"
capabilities:
  - process_csv
  - validate_json
  - transform_xml
```

Users can invoke:
```
"process csv data"  → CORTEX matches "process_csv" → routes to capsule.data_processor
```

---

## 🧪 Testing Guidelines

### Unit Tests

Test these aspects:
1. **Manifest validation** - Ensure manifest loads without errors
2. **Initialization** - Capsule instantiates correctly
3. **RBAC enforcement** - Reject users without required roles
4. **Input sanitization** - Reject malicious input
5. **Core logic** - Your `_execute_core` works correctly
6. **Error handling** - Graceful failure modes

### Example Test Suite

```python
import pytest
from pathlib import Path
from my_skill.handler import MySkillCapsule
from ai_karen_engine.capsules.base_capsule import CapsuleExecutionError

class TestMySkillCapsule:

    @pytest.fixture
    def capsule(self):
        return MySkillCapsule(Path(__file__).parent.parent)

    def test_manifest_loads(self, capsule):
        assert capsule.get_id() == "capsule.my_skill"
        assert capsule.get_version() == "1.0.0"

    def test_rbac_enforcement(self, capsule):
        with pytest.raises(CapsuleExecutionError, match="Insufficient privileges"):
            capsule.execute(
                request={"query": "test"},
                user_ctx={"sub": "user", "roles": []},  # No roles!
                correlation_id="test"
            )

    def test_successful_execution(self, capsule):
        result = capsule.execute(
            request={"query": "hello world"},
            user_ctx={"sub": "admin", "roles": ["system.admin"]},
            correlation_id="test-001"
        )
        assert result.result is not None
        assert result.metadata["capsule_id"] == "capsule.my_skill"

    def test_input_sanitization(self, capsule):
        with pytest.raises(CapsuleExecutionError, match="sanitization"):
            capsule.execute(
                request={"query": "exec('malicious code')"},
                user_ctx={"sub": "admin", "roles": ["system.admin"]},
                correlation_id="test-002"
            )
```

### Integration Tests

Test with live system:
```python
from ai_karen_engine.capsules.cortex_integration import dispatch_capsule_from_cortex

async def test_cortex_dispatch():
    result = await dispatch_capsule_from_cortex(
        intent="capsule.my_skill",
        user_ctx={"sub": "test", "roles": ["system.admin"]},
        query="test query"
    )
    assert result["result"] is not None
```

---

## ✅ Deployment Checklist

Before deploying a new capsule to production:

- [ ] Manifest validated with Pydantic
- [ ] All required files present (handler.py, manifest.yaml)
- [ ] Unit tests written and passing
- [ ] Integration tests passing
- [ ] RBAC roles defined and documented
- [ ] Security policy reviewed (network/filesystem access)
- [ ] Prometheus metrics emitting correctly
- [ ] Audit logging functional
- [ ] Error handling comprehensive
- [ ] Documentation written (README.md)
- [ ] Code review completed
- [ ] Performance tested (execution time < max_execution_time)
- [ ] Circuit breaker tested (handles failures gracefully)

---

## 📚 Examples

### Example 1: Reasoning Capsule

```yaml
# manifest.yaml
id: "capsule.logic_reasoner"
name: "Logic Reasoning Capsule"
version: "1.0.0"
description: "Performs formal logic reasoning and deduction"
type: "reasoning"
capabilities:
  - deduce_conclusion
  - validate_argument
  - detect_fallacy
required_roles:
  - "capsule.reasoning"
allowed_tools:
  - "llm.generate_text"
max_tokens: 512
temperature: 0.3
author: "Zeus"
created: "2025-11-08"
updated: "2025-11-08"
```

```python
# handler.py
from ai_karen_engine.capsules.base_capsule import BaseCapsule
from ai_karen_engine.capsules.schemas import CapsuleContext

class LogicReasonerCapsule(BaseCapsule):

    def _execute_core(self, context: CapsuleContext):
        query = context.request.get("query", "")

        # Use LLM for reasoning
        from ai_karen_engine.integrations.llm_registry import registry
        from ai_karen_engine.core.prompt_router import render_prompt

        prompt = render_prompt(self.prompt_template, context={
            "query": query,
            "capability": "formal logic reasoning"
        })

        llm = registry.get_active()
        result = llm.generate_text(
            prompt,
            max_tokens=self.manifest.max_tokens,
            temperature=self.manifest.temperature
        )

        return {
            "reasoning": result,
            "confidence": 0.85,
            "method": "deductive"
        }
```

### Example 2: Integration Capsule

```yaml
# manifest.yaml
id: "capsule.web_research"
name: "Web Research Capsule"
version: "1.0.0"
description: "Performs web research and data extraction"
type: "integration"
capabilities:
  - search_web
  - extract_data
  - summarize_findings
required_roles:
  - "capsule.integration"
  - "network.access"
security_policy:
  allow_network_access: true  # Required for web access
  max_execution_time: 120
allowed_tools:
  - "llm.generate_text"
  - "web.fetch"
author: "Zeus"
created: "2025-11-08"
updated: "2025-11-08"
```

```python
# handler.py
import requests
from ai_karen_engine.capsules.base_capsule import BaseCapsule, CapsuleExecutionError
from ai_karen_engine.capsules.schemas import CapsuleContext

class WebResearchCapsule(BaseCapsule):

    def _pre_execution_hook(self, context: CapsuleContext):
        # Verify network access permission
        if not self.manifest.security_policy.allow_network_access:
            raise CapsuleExecutionError("Network access not permitted")

    def _execute_core(self, context: CapsuleContext):
        query = context.request.get("query", "")

        # Perform web search (simplified)
        try:
            response = requests.get(
                "https://api.example.com/search",
                params={"q": query},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            raise CapsuleExecutionError(f"Web request failed: {e}")

        # Summarize findings with LLM
        from ai_karen_engine.integrations.llm_registry import registry

        llm = registry.get_active()
        summary = llm.generate_text(
            f"Summarize these search results: {data}",
            max_tokens=256
        )

        return {
            "raw_results": data,
            "summary": summary,
            "source": "web_search"
        }
```

### Example 3: Metacognitive Capsule

```yaml
# manifest.yaml
id: "capsule.self_reflection"
name: "Self-Reflection Capsule"
version: "1.0.0"
description: "Analyzes Kari's own reasoning and performance"
type: "metacognitive"
capabilities:
  - analyze_reasoning
  - estimate_confidence
  - identify_gaps
required_roles:
  - "capsule.metacognitive"
allowed_tools:
  - "llm.generate_text"
  - "neuro_vault.query"
author: "Zeus"
created: "2025-11-08"
updated: "2025-11-08"
```

```python
# handler.py
from ai_karen_engine.capsules.base_capsule import BaseCapsule
from ai_karen_engine.capsules.schemas import CapsuleContext

class SelfReflectionCapsule(BaseCapsule):

    def _execute_core(self, context: CapsuleContext):
        # Analyze recent reasoning history from memory
        memory_ctx = context.memory_context or []

        # Use LLM for self-analysis
        from ai_karen_engine.integrations.llm_registry import registry

        prompt = f"""
        Analyze your recent reasoning history and identify:
        1. Patterns in your thinking
        2. Confidence levels
        3. Knowledge gaps

        Recent context: {memory_ctx[:5]}
        """

        llm = registry.get_active()
        analysis = llm.generate_text(prompt, max_tokens=512, temperature=0.5)

        return {
            "analysis": analysis,
            "context_analyzed": len(memory_ctx),
            "timestamp": context.correlation_id
        }
```

---

## 🎓 Best Practices

1. **Keep capsules focused** - One skill, one capsule
2. **Use capabilities for discoverability** - Make them searchable
3. **Default to restrictive security** - Least privilege principle
4. **Emit metrics** - Every execution should be observable
5. **Handle errors gracefully** - Never crash silently
6. **Document everything** - Future you will thank you
7. **Test thoroughly** - Unit + integration tests
8. **Version semantically** - Breaking changes → major version
9. **Use prompt templates** - Separate logic from prompts
10. **Follow naming conventions** - `capsule.snake_case_name`

---

## 🚀 Next Steps

1. Read through existing capsules: `devops`, `security`, `memory`
2. Pick a skill type from the [classification table](../CAPSULE_SKILL_INJECTION_FRAMEWORK.md)
3. Follow the development workflow
4. Submit for code review
5. Deploy to production

---

## 📞 Support

- **Issues**: GitHub Issues
- **Docs**: `/docs/capsules/`
- **Examples**: `/src/ai_karen_engine/capsules/`
- **Questions**: Ask Zeus

---

**Remember:** Capsules are Kari's **skill injection points** — use them to make her smarter, safer, and more capable without touching her core brain. 🧠
