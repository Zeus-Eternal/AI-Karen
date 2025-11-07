# Unified Response System - AI-Karen

**Version**: 1.0.0 (Unified Architecture)  
**Status**: Enhanced with unified types, fully integrated

## Overview

The response system orchestrates the complete AI response pipeline:

```
Input → Analyze → Recall → Reason → Generate → Format → Output
```

Now fully integrated with:
- **Memory module**: MemoryEntry, MemoryQuery, MemoryContext
- **Reasoning module**: CognitiveOrchestrator, SoftReasoning, CausalReasoning

## Architecture

### Response Pipeline

```
┌─────────────┐
│ User Input  │
└──────┬──────┘
       │
┌──────▼──────────────────────┐
│ 1. ANALYZE                  │
│    - Intent detection       │
│    - Sentiment analysis     │
│    - Entity extraction      │
│    → AnalysisResult         │
└──────┬──────────────────────┘
       │
┌──────▼──────────────────────┐
│ 2. RECALL (Memory)          │
│    - Query memory system    │
│    - Retrieve context       │
│    → MemoryContext          │
└──────┬──────────────────────┘
       │
┌──────▼──────────────────────┐
│ 3. REASON (Optional)        │
│    - Cognitive processing   │
│    - Causal reasoning       │
│    → ReasoningTrace         │
└──────┬──────────────────────┘
       │
┌──────▼──────────────────────┐
│ 4. SELECT MODEL             │
│    - Choose LLM             │
│    - Routing decision       │
│    → ModelSelection         │
└──────┬──────────────────────┘
       │
┌──────▼──────────────────────┐
│ 5. GENERATE                 │
│    - Build prompt           │
│    - LLM generation         │
│    → GenerationMetrics      │
└──────┬──────────────────────┘
       │
┌──────▼──────────────────────┐
│ 6. FORMAT                   │
│    - DRY formatting         │
│    - Add metadata           │
│    → FormattedResponse      │
└──────┬──────────────────────┘
       │
┌──────▼──────────┐
│ Final Response  │
└─────────────────┘
```

## Quick Start

### Basic Usage

```python
from ai_karen_engine.core.response import (
    ResponseOrchestrator,
    create_response_orchestrator,
    ResponseRequest,
    create_request,
)

# Create orchestrator
orchestrator = create_local_only_orchestrator()

# Create request
request = create_request(
    user_text="How do I optimize this Python code?",
    user_id="user_123",
    tenant_id="tenant_456"
)

# Generate response
response = orchestrator.respond(request.user_text)

print(response["text"])
print(f"Intent: {response['intent']}")
print(f"Time: {response['total_time_ms']}ms")
```

### Using Unified Types

```python
from ai_karen_engine.core.response import (
    ResponseRequest,
    UnifiedFormattedResponse,
    IntentType,
    PersonaType,
    ModelType,
)

# Create structured request
request = ResponseRequest(
    request_id="req_abc123",
    user_text="Explain decorators in Python",
    persona=PersonaType.EDUCATIONAL,
    model_preference=ModelType.LOCAL_MEDIUM,
    max_tokens=500
)

# Response includes full trace
response: UnifiedFormattedResponse
```

## Integration with Memory

The response system integrates with the unified memory module:

```python
from ai_karen_engine.core.response import ResponseOrchestrator
from ai_karen_engine.core.memory import MemorySystem

# Memory system provides context
memory = MemorySystem(...)

# Response system uses memory via protocol
response_orchestrator = ResponseOrchestrator(
    analyzer=...,
    memory=memory,  # Implements Memory protocol
    llm_client=...
)

# Memory context is included in response
response = orchestrator.respond("...")
print(response.memory_context.total_recalled)
print(response.memory_context.avg_relevance)
```

## Integration with Reasoning

The response system can leverage cognitive reasoning:

```python
from ai_karen_engine.core.response import ResponseOrchestrator
from ai_karen_engine.core.reasoning import CognitiveOrchestrator

# Cognitive reasoning enhances responses
cognitive = CognitiveOrchestrator(...)

# Can be integrated in custom response pipeline
# Reasoning trace is captured in response
response = orchestrator.respond("...")
print(response.reasoning_trace.strategy)
print(response.reasoning_trace.used_soft_reasoning)
```

## Unified Types

### ResponseRequest
Complete request specification:

```python
@dataclass
class ResponseRequest:
    request_id: str
    user_text: str
    
    # Context
    user_id: Optional[str]
    tenant_id: Optional[str]
    conversation_id: Optional[str]
    
    # Preferences
    persona: PersonaType
    model_preference: Optional[ModelType]
    
    # Capabilities
    ui_caps: Dict[str, Any]
    streaming_enabled: bool
```

### FormattedResponse (Unified)
Complete response with full trace:

```python
@dataclass
class UnifiedFormattedResponse:
    response_id: str
    request_id: str
    text: str
    
    # Classification
    intent: IntentType
    sentiment: SentimentType
    persona: PersonaType
    
    # Pipeline trace
    analysis: AnalysisResult
    memory_context: MemoryContext
    reasoning_trace: ReasoningTrace
    model_selection: ModelSelection
    generation_metrics: GenerationMetrics
    
    # Metadata
    total_time_ms: float
    timestamp: datetime
```

## Protocols

### Existing Protocols
All existing protocols are preserved:

- `Analyzer`: Text analysis (intent, sentiment, entities)
- `Memory`: Context recall and persistence
- `LLMClient`: LLM generation
- `StreamingLLMClient`: Streaming support
- `ModelSelector`: Model selection logic
- `PromptBuilder`: Prompt construction
- `ResponseFormatter`: Response formatting

### Integration Points

```python
from ai_karen_engine.core.response import Analyzer, Memory
from ai_karen_engine.core.memory import MemoryManager

# Memory module can implement response.Memory protocol
class MemoryAdapter:
    """Adapts MemoryManager to response.Memory protocol"""
    
    def __init__(self, memory_manager: MemoryManager):
        self.memory = memory_manager
    
    def recall(self, query: str, k: int = 5):
        # Use unified memory query
        results = self.memory.recall(query, top_k=k)
        return [m.to_dict() for m in results]
    
    def save_turn(self, user_msg: str, assistant_msg: str, meta: Dict):
        # Store in unified memory system
        self.memory.store_text(
            content=f"User: {user_msg}\nAssistant: {assistant_msg}",
            memory_type="episodic",
            **meta
        )
```

## Enums

### IntentType
```python
class IntentType(str, Enum):
    GENERAL_ASSIST = "general_assist"
    OPTIMIZE_CODE = "optimize_code"
    DEBUG_ERROR = "debug_error"
    EXPLAIN_CONCEPT = "explain_concept"
    GENERATE_CODE = "generate_code"
    # ... more
```

### PersonaType
```python
class PersonaType(str, Enum):
    PROFESSIONAL = "professional"
    FRIENDLY = "friendly"
    TECHNICAL = "technical"
    CREATIVE = "creative"
    # ... more
```

### ModelType
```python
class ModelType(str, Enum):
    LOCAL_SMALL = "local_small"
    LOCAL_MEDIUM = "local_medium"
    LOCAL_LARGE = "local_large"
    CLOUD_FAST = "cloud_fast"
    CLOUD_SMART = "cloud_smart"
    HYBRID = "hybrid"
```

## Factory Functions

```python
from ai_karen_engine.core.response import (
    create_response_orchestrator,
    create_local_only_orchestrator,
    create_enhanced_orchestrator,
)

# Local-only (no external APIs)
local_orch = create_local_only_orchestrator()

# Enhanced (with optional cloud)
enhanced_orch = create_enhanced_orchestrator(
    enable_cloud=True,
    fallback_to_local=True
)

# Custom configuration
custom_orch = create_response_orchestrator(
    analyzer=my_analyzer,
    memory=my_memory,
    llm_client=my_llm,
    config=my_config
)
```

## Metrics and Observability

All response pipeline stages are tracked:

```python
response = orchestrator.respond("...")

# Analysis metrics
print(f"Analysis: {response.analysis.analysis_time_ms}ms")
print(f"Confidence: {response.analysis.confidence}")

# Memory metrics
print(f"Recall: {response.memory_context.recall_time_ms}ms")
print(f"Contexts: {response.memory_context.total_recalled}")

# Generation metrics
print(f"Generation: {response.generation_metrics.generation_time_ms}ms")
print(f"Tokens: {response.generation_metrics.total_tokens}")
print(f"Model: {response.generation_metrics.model_used}")

# Total
print(f"Total: {response.total_time_ms}ms")
```

## Backward Compatibility

All existing code continues to work:

```python
# OLD (still works)
from ai_karen_engine.core.response import (
    ResponseOrchestrator,
    IntentType,  # From analyzer.py
    SentimentType,  # From analyzer.py
)

# NEW (unified types)
from ai_karen_engine.core.response import (
    ResponseRequest,
    UnifiedFormattedResponse,
    IntentType,  # From types.py
    SentimentType,  # From types.py
)
```

## Future Enhancements

1. **Streaming Responses**
   - Full streaming support
   - Progressive token delivery
   - Real-time metrics

2. **Advanced Reasoning Integration**
   - Self-refine for response quality
   - Causal reasoning for explanations
   - Metacognition for strategy selection

3. **Multi-turn Conversations**
   - Conversation state management
   - Context window optimization
   - Turn-level memory integration

4. **A/B Testing**
   - Model comparison
   - Persona testing
   - Strategy evaluation

## See Also

- [Memory Module](../memory/README.md) - Unified memory system
- [Reasoning Module](../reasoning/README.md) - Cognitive reasoning
- [UNIFIED_MEMORY_ARCHITECTURE.md](../../../UNIFIED_MEMORY_ARCHITECTURE.md)

## Contributing

When enhancing the response system:
1. Use unified types from `types.py`
2. Implement appropriate protocols
3. Maintain backward compatibility
4. Add comprehensive metrics
5. Document integration points
