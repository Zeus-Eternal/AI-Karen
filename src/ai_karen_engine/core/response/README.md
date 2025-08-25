# Response Core v1 — Prompt-First Orchestrator

The Response Core is a local-first, prompt-driven response system that ensures Karen AI operates fully without external provider keys while maintaining enterprise-grade reliability and optional cloud acceleration.

## Overview

The ResponseOrchestrator centralizes response logic through a unified pipeline that:

1. **Analyzes** user intent and sentiment using spaCy
2. **Recalls** relevant context from memory
3. **Builds** structured prompts using Jinja2 templates
4. **Selects** appropriate models (local-first routing)
5. **Generates** responses using LLM clients
6. **Formats** output consistently
7. **Persists** interactions to memory

## Key Features

- **Local-First Operation**: Works without external API keys using local models
- **Protocol-Based Architecture**: Modular components with dependency injection
- **Persona-Driven Responses**: Intelligent persona selection based on intent and mood
- **Graceful Degradation**: Robust error handling with fallback mechanisms
- **Enterprise Observability**: Prometheus metrics and structured audit logging
- **Optional Cloud Acceleration**: Can use cloud models when explicitly enabled

## Quick Start

### Basic Usage

```python
from ai_karen_engine.core.response import create_local_only_orchestrator

# Create a local-only orchestrator
orchestrator = create_local_only_orchestrator(user_id="your_user_id")

# Generate a response
response = orchestrator.respond("Help me optimize this Python code")

print(f"Intent: {response['intent']}")
print(f"Persona: {response['persona']}")
print(f"Response: {response['content']}")
```

### Custom Configuration

```python
from ai_karen_engine.core.response import create_response_orchestrator, PipelineConfig

# Create custom configuration
config = PipelineConfig(
    persona_default="technical_writer",
    local_only=False,  # Allow cloud acceleration
    enable_copilotkit=True,
    memory_recall_limit=10
)

# Create orchestrator with custom config
orchestrator = create_response_orchestrator(
    user_id="your_user_id",
    config=config
)

# Generate response with UI capabilities
response = orchestrator.respond(
    "Explain this machine learning algorithm",
    ui_caps={
        "copilotkit": True,
        "project_name": "ML Documentation"
    }
)
```

## Architecture

### Core Components

- **ResponseOrchestrator**: Central coordinator managing the response pipeline
- **PipelineConfig**: Configuration dataclass controlling behavior
- **Protocol Interfaces**: Contracts for pluggable components (Analyzer, Memory, LLMClient)
- **Adapters**: Implementations that wrap existing Karen AI components
- **Factory Functions**: Convenient creation of orchestrator instances

### Protocol Interfaces

The system uses protocol-based dependency injection:

```python
from ai_karen_engine.core.response.protocols import Analyzer, Memory, LLMClient

class MyCustomAnalyzer(Analyzer):
    def detect_intent(self, text: str) -> str:
        # Custom intent detection logic
        return "custom_intent"
    
    def sentiment(self, text: str) -> str:
        # Custom sentiment analysis
        return "positive"
    
    def entities(self, text: str) -> Dict[str, Any]:
        # Custom entity extraction
        return {}
```

### Persona System

The orchestrator automatically selects personas based on intent and mood:

- **ruthless_optimizer**: For code optimization and performance tasks
- **calm_fixit**: For debugging and error resolution (especially when user is frustrated)
- **technical_writer**: For documentation and explanation tasks

Persona selection follows this priority:
1. Explicit persona in UI capabilities
2. Mood-based mapping (frustrated → calm_fixit)
3. Intent-based mapping (optimize_code → ruthless_optimizer)
4. Default persona

## Configuration Options

### PipelineConfig Parameters

```python
@dataclass(frozen=True)
class PipelineConfig:
    # Persona Configuration
    persona_default: str = "ruthless_optimizer"
    persona_mapping: Dict[str, Dict[str, str]] = ...
    
    # Model Selection
    max_context_tokens: int = 8192
    local_only: bool = True
    local_model_preference: str = "local:tinyllama-1.1b"
    cloud_routing_threshold: int = 4096
    
    # Memory Configuration
    memory_recall_limit: int = 5
    memory_relevance_threshold: float = 0.7
    
    # Feature Flags
    enable_copilotkit: bool = True
    enable_onboarding: bool = True
    enable_persona_detection: bool = True
    enable_memory_persistence: bool = True
    
    # Performance
    request_timeout: float = 30.0
    max_retries: int = 2
    
    # Observability
    enable_metrics: bool = True
    enable_audit_logging: bool = True
```

## Integration with Existing Systems

The Response Core integrates seamlessly with existing Karen AI components:

### Memory Integration

Uses the existing `ai_karen_engine.core.memory.manager` for context recall and persistence:

```python
from ai_karen_engine.core.response.adapters import MemoryManagerAdapter

memory = MemoryManagerAdapter(user_id="user123", tenant_id="tenant456")
```

### LLM Integration

Leverages the existing `LLMOrchestrator` for model routing and generation:

```python
from ai_karen_engine.core.response.adapters import LLMOrchestratorAdapter

llm_client = LLMOrchestratorAdapter()
```

### NLP Integration

Uses the existing spaCy-based NLP services for analysis:

```python
from ai_karen_engine.core.response.adapters import SpacyAnalyzerAdapter

analyzer = SpacyAnalyzerAdapter()
```

## Response Format

The orchestrator returns structured responses:

```python
{
    "intent": "optimize_code",
    "persona": "ruthless_optimizer", 
    "mood": "neutral",
    "content": "Here's how to optimize your code...",
    "metadata": {
        "model_used": "local:tinyllama-1.1b",
        "context_tokens": 1024,
        "generation_time_ms": 150,
        "routing_decision": "local",
        "correlation_id": "uuid-string",
        "entities": {...}
    },
    "onboarding": {  # Optional, when gaps detected
        "project_context": {
            "question": "What project are you working on?",
            "priority": "high",
            "reason": "Better context helps me provide more relevant assistance"
        }
    }
}
```

## Error Handling

The system provides robust error handling with graceful degradation:

1. **Component Failures**: Falls back to simpler processing
2. **Analysis Failures**: Uses keyword-based fallbacks
3. **Memory Failures**: Continues without context
4. **LLM Failures**: Returns structured error response
5. **Cloud Failures**: Always falls back to local models

## Observability

### Prometheus Metrics

- `response_orchestrator_requests_total`: Total requests by persona/intent/model
- `response_orchestrator_latency_seconds`: Response latency by persona/intent
- `response_orchestrator_routing_total`: Routing decisions (local vs cloud)

### Audit Logging

Structured logs with correlation IDs for tracking:

```json
{
    "timestamp": "2024-01-01T12:00:00Z",
    "level": "INFO",
    "correlation_id": "req_123",
    "component": "response_orchestrator",
    "event": "response_generated",
    "details": {
        "intent": "optimize_code",
        "persona": "ruthless_optimizer",
        "model_used": "local:tinyllama-1.1b",
        "generation_time_ms": 150
    }
}
```

## Testing

Run the test suite:

```bash
python -m pytest tests/test_response_core_orchestrator.py -v
```

Run the demo:

```bash
python examples/response_core_orchestrator_demo.py
```

## Future Extensions

The protocol-based architecture makes it easy to add new components:

- **Custom Analyzers**: Advanced NLP models, domain-specific analysis
- **Custom Memory**: Vector databases, graph databases, external APIs
- **Custom LLM Clients**: New model providers, specialized models
- **Custom Formatters**: Domain-specific output formatting
- **Custom Model Selectors**: Advanced routing logic, cost optimization

## Requirements Satisfied

This implementation satisfies the following requirements from the spec:

- **1.1**: Local-first operation with Tiny LLaMA/Ollama default
- **1.2**: Continues operating without cloud provider keys
- **2.1**: Consistent prompt-first orchestration pipeline
- **2.2**: Structured flow: analyze → recall → prompt → route → generate → format → persist

The modular architecture with dependency injection enables easy testing, maintenance, and future extensions while maintaining the local-first principle.