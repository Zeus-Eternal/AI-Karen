# KIRE-KRO Production System

## Overview

The KIRE-KRO system is the production-grade AI orchestration layer for AI-Karen, providing intelligent LLM routing, reasoning coordination, and response optimization.

### Components

1. **KIRE** (Kari Intelligent Routing Engine)
   - Intelligent LLM provider and model selection
   - Profile-based routing with fallback chains
   - Health monitoring and graceful degradation
   - RBAC enforcement and rate limiting
   - Comprehensive OSIRIS logging

2. **KRO** (Kari Reasoning Orchestrator)
   - Prompt-first controller for response generation
   - Intent classification and planning
   - Helper model coordination (TinyLlama, DistilBERT, spaCy)
   - Dynamic prompt suggestions
   - Structured response envelopes

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

## Architecture

```
User Request
    ↓
[KRO Orchestrator]
    ├─→ Intent Classification (DistilBERT)
    ├─→ Planning (TinyLlama scaffolding)
    ├─→ Routing (KIRE)
    │     ├─→ Profile Resolution
    │     ├─→ Task Analysis
    │     ├─→ Cognitive Reasoning
    │     ├─→ Health Checks
    │     └─→ Provider Selection
    ├─→ Execution (Main LLM + CUDA)
    ├─→ Optimization (Content Engine)
    └─→ Suggestions (Dynamic Engine)
    ↓
Response Envelope
```

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
from ai_karen_engine.core import process_request

# Process a user request
response = await process_request(
    user_input="Explain quantum computing",
    user_id="user123",
    conversation_history=[],
)

# Access response
print(response["message"])  # User-facing message
print(response["meta"]["provider"])  # Used provider
print(response["meta"]["model"])  # Used model
print(response["suggestions"])  # Next-step suggestions
```

### API Usage

```bash
# Start API server
uvicorn ai_karen_engine.main:app --host 0.0.0.0 --port 8000

# Process request
curl -X POST http://localhost:8000/api/kro/process \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "What is machine learning?",
    "user_id": "user123"
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

### Response Envelope

```json
{
  "meta": {
    "timestamp": "2025-01-05T12:00:00Z",
    "agent": "KRO",
    "confidence": 0.92,
    "latency_ms": 1250,
    "tokens_used": 150,
    "provider": "openai",
    "model": "gpt-4o-mini",
    "degraded_mode": false
  },
  "classification": {
    "intent": "General",
    "category": "factual",
    "sentiment": "neutral",
    "style": "factual",
    "importance": 5,
    "keywords": "machine|learning|explanation"
  },
  "reasoning_summary": "Classified as general query and routed to OpenAI GPT-4o-mini for factual explanation.",
  "plan": [
    {
      "step": 1,
      "action": "classify",
      "detail": "Classified as General"
    },
    {
      "step": 2,
      "action": "synthesize",
      "detail": "Compose answer from knowledge"
    }
  ],
  "evidence": [],
  "memory_writes": [],
  "ui": {
    "layout_hint": "default",
    "components": [
      {
        "type": "text",
        "body_md": "Machine learning is..."
      }
    ]
  },
  "telemetry": {
    "tools_called": [],
    "errors": [],
    "notes": ""
  },
  "suggestions": [
    "Explain the types of machine learning",
    "How does supervised learning work?",
    "Show me a practical example"
  ],
  "message": "Machine learning is..."
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

# KRO metrics
kro_events_total{event_type="kro.done", status="success"}
```

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
