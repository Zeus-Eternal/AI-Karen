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

## Iterative Refinement Pipeline

**New in v1.0**: Self-refinement for higher quality responses based on research papers (Self-Refine, ARIES, Thinking LLMs).

### Overview

The iterative refinement pipeline implements a 5-stage process:

1. **Initial Generation**: Generate base response
2. **Coherence Check**: Verify logical flow and relevance
3. **Persona Alignment**: Match tone and style to persona
4. **Memory Consistency**: Ensure alignment with context
5. **Quality Verification**: Final quality assessment

```python
from ai_karen_engine.core.response import (
    IterativeRefinementPipeline,
    create_refinement_pipeline,
    RefinementConfig,
)

# Create pipeline
pipeline = create_refinement_pipeline(
    generator=my_llm_client,
    memory_manager=my_memory,
    max_iterations=5,
    convergence_threshold=0.85
)

# Refine response
result = await pipeline.refine(
    request=response_request,
    initial_response="Initial draft...",
    memory_context=retrieved_memories
)

# Check results
print(f"Iterations: {result.total_iterations}")
print(f"Quality improved: {result.quality_improvement:.2f}")
print(f"Converged: {result.converged}")
print(f"Final: {result.final_response}")
```

### Refinement Stages

Each stage can be enabled/disabled:

```python
config = RefinementConfig(
    max_iterations=5,
    convergence_threshold=0.85,

    # Enable/disable stages
    enable_coherence_check=True,
    enable_persona_alignment=True,
    enable_memory_consistency=True,
    enable_quality_verification=True,

    # Stage weights
    coherence_weight=0.35,
    persona_weight=0.25,
    memory_weight=0.25,
    verification_weight=0.15,
)
```

### Convergence Detection

The pipeline automatically stops when:

1. **Quality threshold met**: Overall quality > convergence_threshold
2. **Minimal improvement**: Quality improvement < min_improvement
3. **Max iterations**: Reached maximum iterations
4. **Timeout**: Exceeded total_timeout_ms

### Integration with Reasoning

The refinement pipeline integrates with the reasoning module:

```python
# Uses SelfRefiner from reasoning module
from ai_karen_engine.core.reasoning import SelfRefiner

# Uses MetacognitiveMonitor for cognitive state tracking
from ai_karen_engine.core.reasoning import MetacognitiveMonitor

# Automatically integrated in IterativeRefinementPipeline
```

## Autonomous Learning Loop

**New in v1.0**: Continuous learning from feedback to improve response quality over time.

### Overview

The autonomous learner:

1. **Collects Feedback**: Explicit and implicit signals
2. **Detects Patterns**: Analyzes successful/failed responses
3. **Makes Decisions**: Determines adaptations
4. **Applies Changes**: Updates strategies and models

```python
from ai_karen_engine.core.response import (
    AutonomousLearner,
    create_autonomous_learner,
    FeedbackType,
)

# Create learner
learner = create_autonomous_learner(
    memory_manager=my_memory,
    enable_auto_adaptation=True
)

# Record feedback
await learner.record_feedback(
    response=formatted_response,
    feedback_type=FeedbackType.EXPLICIT_POSITIVE,
    user_satisfaction=0.9,
    conversation_continued=True,
    task_completed=True
)

# Trigger analysis and adaptation
adaptations = await learner.analyze_and_adapt()

# Check statistics
stats = learner.get_statistics()
print(f"Total feedback: {stats['total_feedback']}")
print(f"Patterns learned: {stats['patterns_learned']}")
print(f"Adaptations made: {stats['adaptations_made']}")
```

### Feedback Types

```python
class FeedbackType(str, Enum):
    EXPLICIT_POSITIVE = "explicit_positive"      # User liked it
    EXPLICIT_NEGATIVE = "explicit_negative"      # User disliked it
    IMPLICIT_POSITIVE = "implicit_positive"      # Continued conversation
    IMPLICIT_NEGATIVE = "implicit_negative"      # Rephrased question
    CORRECTION = "correction"                    # User corrected response
    CLARIFICATION_REQUEST = "clarification_request"
    ACCEPTANCE = "acceptance"                    # User acted on response
```

### Learning Patterns

The learner automatically detects patterns:

```python
# Example detected pattern
{
    "pattern_id": "pattern_optimize_code_technical_1234",
    "pattern_type": "intent_persona",
    "conditions": {
        "intent": "optimize_code",
        "persona": "technical"
    },
    "successful_features": [
        "high_quality",
        "high_relevance",
        "engaging"
    ],
    "success_rate": 0.87,
    "confidence": 0.92
}
```

### Adaptation Strategies

```python
class AdaptationStrategy(str, Enum):
    REINFORCE_SUCCESS = "reinforce_success"          # Amplify successful patterns
    AVOID_FAILURE = "avoid_failure"                  # Reduce failed patterns
    EXPLORE_ALTERNATIVE = "explore_alternative"      # Try new approaches
    REFINE_EXISTING = "refine_existing"              # Fine-tune current approach
    MAINTAIN = "maintain"                            # Keep current strategy
```

### Integration with Memory

Feedback and patterns are stored in the unified memory system:

```python
# Feedback stored as episodic memories
# Patterns stored as semantic memories
# Automatically persisted if memory_manager provided

config = LearningConfig(
    store_feedback_in_memory=True,
    feedback_memory_ttl_days=90,
    store_patterns_in_memory=True
)
```

## Complete Pipeline with Refinement and Learning

```python
from ai_karen_engine.core.response import (
    ResponseOrchestrator,
    create_refinement_pipeline,
    create_autonomous_learner,
    ResponseRequest,
    create_request,
    FeedbackType,
)

# Initialize components
orchestrator = create_response_orchestrator(...)
refinement_pipeline = create_refinement_pipeline(...)
learner = create_autonomous_learner(...)

# 1. Generate initial response
request = create_request(
    user_text="How do I optimize this code?",
    persona=PersonaType.TECHNICAL
)

initial_response = orchestrator.respond(request.user_text)

# 2. Refine response
refined_result = await refinement_pipeline.refine(
    request=request,
    initial_response=initial_response["text"],
    memory_context=initial_response.get("memory_context")
)

# 3. Create final formatted response
final_response = FormattedResponse(
    response_id=make_response_id(),
    request_id=request.request_id,
    text=refined_result.final_response,
    intent=initial_response["intent"],
    sentiment=initial_response["sentiment"],
    persona=request.persona,
    # ... other fields
)

# 4. Collect user feedback (later)
await learner.record_feedback(
    response=final_response,
    feedback_type=FeedbackType.IMPLICIT_POSITIVE,
    conversation_continued=True
)

# 5. Periodic analysis and adaptation
if learner.total_feedback_count >= 50:
    adaptations = await learner.analyze_and_adapt()
    print(f"Made {len(adaptations)} adaptations")
```

## Future Enhancements

1. **Streaming Responses**
   - Full streaming support
   - Progressive token delivery
   - Real-time metrics

2. **Multi-turn Conversations**
   - Conversation state management
   - Context window optimization
   - Turn-level memory integration

3. **A/B Testing**
   - Model comparison
   - Persona testing
   - Strategy evaluation

4. **Advanced Adaptation**
   - Model fine-tuning from feedback
   - Prompt template optimization
   - Dynamic persona adjustment

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
