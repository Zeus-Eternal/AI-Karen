# NeuroVault Memory System

## Overview

NeuroVault is Kari's production-grade tri-partite memory system inspired by neuroscience principles. It provides human-like memory capabilities with episodic experiences, semantic knowledge, and procedural learning.

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   NeuroVault Core                        │
├─────────────────────────────────────────────────────────┤
│  Episodic Memory    │  Semantic Memory  │  Procedural   │
│  (Experiences)      │  (Facts/Knowledge)│  (Tool Usage) │
│  λ = 0.12          │  λ = 0.04         │  λ = 0.02     │
└─────────────────────────────────────────────────────────┘
         ↓                    ↓                   ↓
┌─────────────────────────────────────────────────────────┐
│           Intelligent Hybrid Retrieval                   │
│   R = (S × I × D) + A                                   │
│   S: Semantic similarity (cosine)                        │
│   I: Importance weighting                                │
│   D: Temporal decay (exponential)                        │
│   A: Access frequency bonus                              │
└─────────────────────────────────────────────────────────┘
         ↓                    ↓                   ↓
┌─────────────────────────────────────────────────────────┐
│              Storage Backends                            │
│  PostgreSQL  │  Milvus (HNSW)  │  Redis Cache           │
└─────────────────────────────────────────────────────────┘
```

## Memory Types

### 1. Episodic Memory
- **Purpose**: Time-stamped experiences and interactions
- **Decay Rate**: λ = 0.12 (fast decay)
- **Half-Life**: ~5.8 hours
- **Use Cases**:
  - Recent conversations
  - User interactions
  - Emotional context
- **Consolidation**: Promoted to semantic after 24 hours if important

### 2. Semantic Memory
- **Purpose**: Distilled facts and knowledge
- **Decay Rate**: λ = 0.04 (slow decay)
- **Half-Life**: ~17.3 hours
- **Use Cases**:
  - User preferences
  - Factual knowledge
  - Consolidated insights
- **Retention**: 365 days default

### 3. Procedural Memory
- **Purpose**: Tool usage patterns and workflows
- **Decay Rate**: λ = 0.02 (very slow decay)
- **Half-Life**: ~34.7 hours
- **Use Cases**:
  - Successful tool patterns
  - Workflow optimization
  - Skill learning
- **Retention**: 180 days default

## Key Features

### Intelligent Retrieval

The retrieval system uses hybrid scoring:

```python
relevance = (semantic_score * importance_factor * decay_factor) + access_bonus

where:
- semantic_score: cosine similarity [0, 1]
- importance_factor: normalized importance [0, 1]
- decay_factor: e^(-λt)
- access_bonus: log(1 + access_count) * 0.1
```

**Performance Targets**:
- p95 latency: < 150ms
- Recall@5 accuracy: > 85%
- Cache hit rate: > 60%

### Memory Consolidation (Reflection)

Episodic memories are automatically promoted to semantic:

**Criteria**:
1. Age > 24 hours
2. Importance score ≥ 6.0
3. Access count ≥ 2

**Process**:
1. Identify consolidation candidates
2. Create semantic memory from episodic content
3. Mark original as `CONSOLIDATING`
4. Background task runs every 6 hours

### Memory Decay

Natural forgetting via exponential decay:

```python
decay_factor = e^(-λ * age_hours)
```

**Decay Lambdas**:
- Episodic: 0.12 per hour
- Semantic: 0.04 per hour
- Procedural: 0.02 per hour

**Archival**:
- Memories with relevance < 0.1 are archived
- Archived memories retained for audit
- Purged after retention period

### Security and Privacy

#### RBAC (Role-Based Access Control)

```python
permissions = {
    "admin": ["read", "write", "delete", "admin"],
    "user": ["read", "write"],
    "viewer": ["read"],
    "system": ["read", "write", "delete", "admin", "system"],
}
```

#### Tenant Isolation

- Row-level security by tenant_id
- Cross-tenant access only for system role
- Automatic filtering in all queries

#### PII Scrubbing

Automatically detects and redacts:
- Email addresses
- Phone numbers
- SSNs
- Credit card numbers

```python
# Before storage
"Contact me at john@example.com"

# After scrubbing
"Contact me at [EMAIL_REDACTED]"
```

## Usage

### Basic Operations

```python
from ai_karen_engine.services.neurovault_integration_service import (
    get_neurovault_integration,
    initialize_neurovault_service,
)

# Initialize service
service = await initialize_neurovault_service()

# Store conversation memory
memory = await service.store_conversation_memory(
    user_message="What is the capital of France?",
    ai_response="The capital of France is Paris.",
    tenant_id="tenant_123",
    user_id="user_456",
    conversation_id="conv_789",
    importance_score=5.0,
)

# Retrieve relevant memories
result = await service.retrieve_relevant_memories(
    query="France",
    tenant_id="tenant_123",
    user_id="user_456",
    top_k=5,
)

# Access retrieved memories
for memory, score in zip(result.memories, result.scores):
    print(f"Score: {score:.2f} - {memory.content[:100]}...")
```

### Advanced Features

```python
# Store tool usage pattern
await service.store_tool_usage(
    tool_name="web_search",
    success=True,
    tenant_id="tenant_123",
    user_id="user_456",
)

# Get conversation context
context_memories = await service.get_conversation_context(
    conversation_id="conv_789",
    tenant_id="tenant_123",
    user_id="user_456",
    max_turns=10,
)

# Manual consolidation
consolidated_count = await service.neurovault.consolidate_memories(
    tenant_id="tenant_123",
    user_id="user_456",
)

# Apply decay
archived_count = await service.neurovault.apply_decay()

# Get statistics
stats = service.get_stats()
print(f"Total memories: {stats['index_stats']['total_memories']}")
print(f"Cache hit rate: {stats['metrics']['cache_hit_rate']:.2%}")
```

## Integration with Chat Orchestrator

NeuroVault automatically integrates with the chat system:

```python
# In chat orchestrator
from ai_karen_engine.services.neurovault_integration_service import (
    get_neurovault_integration
)

async def process_chat_message(user_message, user_id, conversation_id):
    # Get relevant context from NeuroVault
    service = get_neurovault_integration()

    context = await service.retrieve_relevant_memories(
        query=user_message,
        tenant_id=tenant_id,
        user_id=user_id,
        conversation_id=conversation_id,
        top_k=5,
    )

    # Generate response with context
    ai_response = await generate_response(user_message, context)

    # Store interaction in NeuroVault
    await service.store_conversation_memory(
        user_message=user_message,
        ai_response=ai_response,
        tenant_id=tenant_id,
        user_id=user_id,
        conversation_id=conversation_id,
    )

    return ai_response
```

## Performance Metrics

NeuroVault emits comprehensive Prometheus metrics:

### Counters
```
neurovault_retrieval_total{memory_type, status}
neurovault_storage_total{memory_type}
```

### Histograms
```
neurovault_retrieval_latency_seconds{memory_type}
```

### Custom Metrics
```python
stats = service.get_stats()

# Retrieval metrics
retrieval_count = stats["metrics"]["retrieval_count"]
latency_p95 = stats["metrics"]["latency_p95_ms"]
cache_hit_rate = stats["metrics"]["cache_hit_rate"]

# Memory metrics
total_memories = stats["index_stats"]["total_memories"]
by_type = stats["index_stats"]["by_type"]
```

## Configuration

```python
# Custom configuration
from ai_karen_engine.core.neuro_vault import NeuroVault, EmbeddingManager

# Custom embedding model
embedding_manager = EmbeddingManager(
    model_name="all-MPNet-base-v2",
    dim=768,
)

# Custom NeuroVault instance
neurovault = NeuroVault(
    embedding_manager=embedding_manager,
    enable_metrics=True,
    enable_rbac=True,
    enable_pii_scrubbing=True,
)

# Configure retention periods
neurovault.config["retention_days"] = {
    MemoryType.EPISODIC: 30,
    MemoryType.SEMANTIC: 365,
    MemoryType.PROCEDURAL: 180,
}

# Configure consolidation
neurovault.config["consolidation_threshold_hours"] = 24
neurovault.config["decay_check_interval_hours"] = 6
```

## Database Schema

### PostgreSQL Schema

```sql
CREATE TABLE memories (
    id UUID PRIMARY KEY,
    memory_type VARCHAR(20) NOT NULL,  -- episodic, semantic, procedural
    content TEXT NOT NULL,
    tenant_id VARCHAR(255) NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    conversation_id VARCHAR(255),

    -- Temporal
    timestamp TIMESTAMP NOT NULL,
    last_accessed TIMESTAMP,
    access_count INTEGER DEFAULT 0,

    -- Scoring
    importance_score FLOAT DEFAULT 5.0,
    confidence FLOAT DEFAULT 1.0,
    decay_lambda FLOAT NOT NULL,

    -- Lifecycle
    status VARCHAR(20) DEFAULT 'active',
    ttl_days INTEGER,
    expires_at TIMESTAMP,

    -- Relationships
    parent_id UUID,
    related_ids UUID[],

    -- Type-specific
    tool_name VARCHAR(255),
    success_rate FLOAT,
    usage_count INTEGER DEFAULT 0,
    emotional_valence FLOAT,
    event_type VARCHAR(50),

    -- Metadata
    metadata JSONB,

    -- Indexes
    CONSTRAINT fk_parent FOREIGN KEY (parent_id) REFERENCES memories(id)
);

CREATE INDEX idx_memories_tenant_user ON memories(tenant_id, user_id);
CREATE INDEX idx_memories_type ON memories(memory_type);
CREATE INDEX idx_memories_timestamp ON memories(timestamp DESC);
CREATE INDEX idx_memories_conversation ON memories(conversation_id) WHERE conversation_id IS NOT NULL;
CREATE INDEX idx_memories_status ON memories(status);
```

### Milvus Collection

```python
collection_schema = {
    "name": "kari_memories",
    "description": "Memory embeddings for semantic search",
    "fields": [
        {
            "name": "id",
            "type": "VARCHAR",
            "max_length": 36,
            "is_primary": True,
        },
        {
            "name": "embedding",
            "type": "FLOAT_VECTOR",
            "dim": 768,
        },
        {
            "name": "tenant_id",
            "type": "VARCHAR",
            "max_length": 255,
        },
        {
            "name": "memory_type",
            "type": "VARCHAR",
            "max_length": 20,
        },
    ],
    "index_params": {
        "metric_type": "COSINE",
        "index_type": "HNSW",
        "params": {"M": 16, "efConstruction": 200},
    },
}
```

## Monitoring and Debugging

### Check System Health

```python
stats = service.get_stats()

print(f"Total memories: {stats['index_stats']['total_memories']}")
print(f"By type: {stats['index_stats']['by_type']}")
print(f"Cache hit rate: {stats['metrics']['cache_hit_rate']:.2%}")
print(f"Avg latency: {stats['metrics']['latency_avg_ms']:.1f}ms")
```

### Debug Retrieval

```python
result = await service.retrieve_relevant_memories(
    query="test query",
    tenant_id="tenant_123",
    user_id="user_456",
)

print(f"Retrieved {len(result.memories)} memories in {result.retrieval_time_ms:.1f}ms")
print(f"Total matches: {result.total_matches}")
print(f"Cache hit: {result.cache_hit}")

for memory, score in zip(result.memories, result.scores):
    print(f"\nScore: {score:.3f}")
    print(f"Type: {memory.memory_type.value}")
    print(f"Age: {(datetime.utcnow() - memory.timestamp).total_seconds() / 3600:.1f}h")
    print(f"Importance: {memory.importance_score}/10")
    print(f"Access count: {memory.access_count}")
```

## Testing

```python
import pytest
from ai_karen_engine.core.neuro_vault import (
    NeuroVault,
    MemoryType,
    RetrievalRequest,
    create_memory_entry,
)

@pytest.mark.asyncio
async def test_memory_storage_and_retrieval():
    neurovault = NeuroVault()

    # Store memory
    memory = await neurovault.store_memory(
        content="Paris is the capital of France",
        memory_type=MemoryType.SEMANTIC,
        tenant_id="test_tenant",
        user_id="test_user",
        importance_score=8.0,
    )

    assert memory is not None
    assert memory.memory_type == MemoryType.SEMANTIC

    # Retrieve memory
    request = RetrievalRequest(
        query="capital of France",
        tenant_id="test_tenant",
        user_id="test_user",
        top_k=1,
    )

    result = await neurovault.retrieve_memories(request)

    assert len(result.memories) > 0
    assert result.scores[0] > 0.5
    assert "Paris" in result.memories[0].content
```

## Troubleshooting

### Issue: Low retrieval accuracy

**Solution**:
1. Check embedding quality
2. Adjust minimum relevance threshold
3. Increase top_k
4. Review importance scores

### Issue: High latency

**Solution**:
1. Enable caching
2. Reduce top_k
3. Optimize temporal window
4. Check Milvus index parameters

### Issue: Memory not consolidating

**Solution**:
1. Check consolidation criteria (age, importance, access_count)
2. Verify background task is running
3. Manually trigger consolidation
4. Check logs for errors

## Requirements Fulfilled

✅ Req 1: Multi-tier memory architecture (episodic, semantic, procedural)
✅ Req 2: Intelligent hybrid retrieval (semantic + temporal)
✅ Req 3: Memory decay and lifecycle management
✅ Req 4: Security, privacy, and RBAC controls
✅ Req 5: Performance monitoring and observability
✅ Req 6: Integration with existing systems
✅ Req 7: Storage with PostgreSQL, Milvus, Redis
✅ Req 8: Advanced embeddings (all-MPNet-base-v2)

## License

See main project LICENSE file.
