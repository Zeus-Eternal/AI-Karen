# KIRE-KRO Production System

## Overview

KIRE-KRO is a production routing-and-reasoning support subsystem for Karen AI.

It is not a rival chat runtime.

For standard chat:
- API ingress normalizes requests
- `ChatOrchestrator` owns the request lifecycle
- KIRE contributes routing intelligence
- KRO may contribute specialized reasoning or sub-orchestration support when explicitly invoked
- persistence, writeback, and frontend completion truth remain under the canonical chat runtime

KIRE-KRO therefore operates under Karen's main chat authority model rather than beside it.

### Components

1. **KIRE** (Kari Intelligent Routing Engine)
   - Intent-aware provider and model selection
   - Profile-based routing with fallback chains
   - Task analysis, capability matching, and routing confidence
   - Decision logging and routing metrics
   - Advisory routing output for the governed chat runtime

2. **KRO** (Kari Reasoning Orchestrator)
   - Specialized reasoning/orchestration support
   - Intent classification and planning for KRO-native or specialized flows
   - Helper model coordination (TinyLlama, DistilBERT, spaCy)
   - Structured reasoning artifacts for subflows
   - Not the top-level owner of standard chat lifecycle

3. **Model Discovery Engine**
   - Comprehensive model scanning (GGUF, Transformers, Stable Diffusion)
   - Automatic metadata extraction
   - Capability and modality detection
   - Resource requirement estimation

4. **CUDA Acceleration Engine**
   - GPU offloading for inference
   - Memory management
   - Performance optimization

5. **Content Optimization Engine**
   - Redundancy elimination
   - Progressive content delivery
   - Format optimization

## Authority Model

Core law:

Routes accept.
Routers classify.
Reasoners support.
Main chat orchestrator decides.
Services execute.
Persistence stores.
Frontend reflects backend truth.

KIRE-KRO must fit inside that law.

## Architecture

```
User Request
    ↓
[Thin API Route]
    ↓
[ChatOrchestrator]
    ├─→ Working context + memory assembly
    ├─→ KIRE advisory routing
    │     ├─→ Profile Resolution
    │     ├─→ Task Analysis
    │     ├─→ Cognitive Reasoning
    │     ├─→ Health Checks
    │     └─→ Provider Selection Recommendation
    ├─→ Optional KRO specialized subflow
    ├─→ Governed execution path selection
    ├─→ Persistence / writeback / telemetry
    ↓
Backend-confirmed response
```

Out-of-band KRO endpoints may still exist for diagnostics or specialized orchestration, but they do not define standard chat completion truth.

## Quick Start

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Initialize system
python -m ai_karen_engine.initialize_kire_kro
```

### Basic Usage

```python
from ai_karen_engine.core.kire_kro_integration import get_integration

# Standard chat handoff still goes through the canonical chat runtime
integration = get_integration()
response = await integration.process_user_request(
    user_input="Explain quantum computing",
    user_id="user123",
    conversation_history=[],
)

# Access normalized response
print(response["message"])
print(response["meta"]["provider"])
print(response["_integration"]["authority"])  # chat_orchestrator
```

### API Usage

```bash
# Start API server
uvicorn ai_karen_engine.main:app --host 0.0.0.0 --port 8000

# Process standard chat through governed runtime
curl -X POST http://localhost:8000/api/kro/process \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "What is machine learning?",
    "user_id": "user123"
  }'

# Execute an explicit KRO-native specialized flow
curl -X POST http://localhost:8000/api/kro/process-specialized \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "Plan a specialized reasoning workflow for this dataset",
    "user_id": "user123",
    "context": {
      "kro_native": true
    }
  }'

# Legacy orchestration chat routes still exist as compatibility ingress,
# but they now delegate to ChatOrchestrator instead of owning chat lifecycle.
curl -X POST http://localhost:8000/api/orchestration/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello Karen",
    "session_id": "session-123"
  }'

# LangGraph admin and diagnostic endpoints now live under an explicit admin namespace.
curl http://localhost:8000/api/admin/orchestration/status
curl http://localhost:8000/api/admin/orchestration/health
curl -X POST http://localhost:8000/api/admin/orchestration/debug/dry-run \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Analyze this orchestration path",
    "session_id": "session-123"
  }'

# Get available models
curl http://localhost:8000/api/kro/models

# Check system status
curl http://localhost:8000/api/kro/status

# Health check
curl http://localhost:8000/api/kro/health
```

## Configuration

### Integration Config

```python
from ai_karen_engine.core.kire_kro_integration import (
    IntegrationConfig,
    initialize_integration,
)

config = IntegrationConfig(
    enable_kire_routing=True,
    enable_cuda_acceleration=True,
    enable_content_optimization=True,
    enable_model_discovery=True,
    enable_degraded_mode=True,
    enable_metrics=True,
    cache_routing_decisions=True,
    max_concurrent_requests=10,
    request_timeout=120.0,
)

integration = await initialize_integration(config)
```

### User Profiles

Create user profiles for custom routing:

```json
{
  "id": "power_user",
  "name": "Power User Profile",
  "assignments": {
    "chat": {
      "provider": "openai",
      "model": "gpt-4o"
    },
    "code": {
      "provider": "deepseek",
      "model": "deepseek-coder"
    },
    "reasoning": {
      "provider": "openai",
      "model": "gpt-4o"
    }
  },
  "fallback_chain": ["openai", "deepseek", "llamacpp"]
}
```

## Response Format

### Standard Chat Envelope

```json
{
  "meta": {
    "timestamp": "2025-01-05T12:00:00Z",
    "agent": "ChatOrchestrator",
    "confidence": 0.92,
    "latency_ms": 1250,
    "tokens_used": 150,
    "provider": "openai",
    "model": "gpt-4o-mini",
    "degraded_mode": false
  },
  "routing": {
    "provider": "openai",
    "model": "gpt-4o-mini",
    "reasoning": "profile assignment for chat",
    "confidence": 0.92
  },
  "structured_content": {},
  "actions": [],
  "telemetry": {
    "route": "canonical"
  },
  "message": "Machine learning is...",
  "_integration": {
    "authority": "chat_orchestrator",
    "kire_enabled": true,
    "kro_specialized_available": true,
    "routing_advisory_used": true
  }
}
```

## Features

### Intelligent Routing

KIRE selects the optimal provider and model based on:
- User profile preferences
- Task type and requirements
- Provider health status
- Cost constraints
- Capability matching
- Urgency heuristics

### Graceful Degradation

When providers fail, the system:
1. Falls back to next healthy provider in chain
2. Uses helper models (TinyLlama) for basic responses
3. Notifies users of degraded mode
4. Logs incidents for admin review

### Dynamic Suggestions

The system generates contextual suggestions based on:
- Conversation history
- User expertise level (novice/intermediate/expert)
- Recent topics
- Conversation tone

### CUDA Acceleration

Automatically offloads computationally intensive operations to GPU when available:
- Model inference
- Embeddings generation
- Matrix operations

### Content Optimization

Optimizes responses for:
- Faster delivery
- Reduced redundancy
- Better readability
- Progressive loading

## Observability

### OSIRIS Logging

All operations emit structured logs:

```python
# Routing start
{
  "event": "routing.start",
  "correlation_id": "abc123",
  "user_id": "user123",
  "task_type": "chat"
}

# Routing decision
{
  "event": "routing.decision",
  "provider": "openai",
  "model": "gpt-4o-mini",
  "confidence": 0.92,
  "reasoning": "Profile assignment for chat"
}

# Governed routing outcome
{
  "event": "routing.outcome",
  "correlation_id": "abc123",
  "outcome": "used",
  "advisory_provider": "openai",
  "advisory_model": "gpt-4o-mini",
  "final_provider": "openai",
  "final_model": "gpt-4o-mini",
  "final_status": "completed",
  "execution_path": "direct_llm"
}

# KRO completion
{
  "event": "kro.done",
  "success": true,
  "latency_ms": 1250,
  "degraded_mode": false
}
```

### Prometheus Metrics

```python
# Routing metrics
kire_decisions_total{status="success", task_type="chat"}
kire_latency_seconds{task_type="chat"}
kire_provider_selection_total{provider="openai", model="gpt-4o-mini"}
kire_decision_confidence{provider="openai"}
kire_advisory_outcomes_total{outcome="used", final_status="completed", execution_path="direct_llm"}

# KRO metrics
kro_events_total{event_type="kro.done", status="success"}
kro_specialized_path_total{path="kro_orchestrator.process_request", status="success"}
```

Operationally, this means operators can now answer:
- whether KIRE advice was actually used or overridden downstream
- which final provider/model completed the governed chat path
- how often specialized KRO execution paths were invoked
- which correlation ID ties the original advisory route to the final chat outcome

## Testing

### Unit Tests

```bash
# Run all tests
pytest tests/unit/

# Run KIRE tests
pytest tests/routing/

# Run KRO tests
pytest tests/unit/core/test_kro_orchestrator.py
```

### Integration Tests

```bash
# Run integration tests
pytest tests/comprehensive/test_model_routing_validation.py
```

### System Test

```bash
# Initialize and test
python -m ai_karen_engine.initialize_kire_kro --test
```

## Troubleshooting

### Issue: Models not discovered

**Solution:**
```bash
# Refresh model registry
curl -X POST http://localhost:8000/api/kro/models/refresh

# Check models directory
ls -la models/
```

### Issue: CUDA not available

**Solution:**
```bash
# Check CUDA installation
nvidia-smi

# Disable CUDA acceleration
python -m ai_karen_engine.initialize_kire_kro --no-cuda
```

### Issue: Routing failures

**Solution:**
```bash
# Check provider health
curl http://localhost:8000/api/kro/health

# Check routing decision
curl -X POST http://localhost:8000/api/kro/routing \
  -H "Content-Type: application/json" \
  -d '{"user_input": "test", "user_id": "test"}'
```

## Performance Tuning

### Caching

Enable routing decision caching:

```python
config = IntegrationConfig(
    cache_routing_decisions=True,  # Enable caching
)
```

### Concurrency

Adjust concurrent request limit:

```python
config = IntegrationConfig(
    max_concurrent_requests=20,  # Increase for high-load
)
```

### Timeouts

Configure request timeouts:

```python
config = IntegrationConfig(
    request_timeout=60.0,  # Reduce for faster failures
)
```

## Security

### RBAC

KIRE enforces role-based access control:

```python
# Requires routing role
await routing_select_handler(
    user_ctx={"roles": ["routing"], "user_id": "user123"},
    query="test",
)

# Admin-only operations
await routing_profile_set_handler(
    user_ctx={"roles": ["admin"]},
    query="",
    context={"profile_id": "power_user"},
)
```

### Rate Limiting

Built-in rate limiting prevents abuse:
- 45 requests per 60 seconds per user
- Configurable limits
- Automatic throttling

## Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines.

## License

See [LICENSE](../LICENSE) for details.
