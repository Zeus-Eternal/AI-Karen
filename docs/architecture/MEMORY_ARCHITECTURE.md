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
# Unified Memory Architecture - Research Paper Alignment

## Overview

This document proposes a unified memory architecture for AI-Karen that aligns the three currently separate memory modules with recent academic research on long-term memory in LLMs.

## Current Architecture Issues

### Separate Modules with Overlapping Concerns

1. **`recalls/`** - RecallManager for memory tier orchestration
   - Has: `RecallItem`, `StoreAdapter`, `EmbeddingClient`, memory tiers

2. **`neuro_recall/`** - Agent-based hierarchical recall
   - Has: META-PLANNER, EXECUTOR, SR/ICE integration

3. **`neuro_vault/`** - Tri-partite memory system
   - Has: `MemoryEntry`, Episodic/Semantic/Procedural, `EmbeddingManager`

### Problems:
- ❌ Duplicate concepts (MemoryEntry vs RecallItem, multiple embedding clients)
- ❌ No clear hierarchy or integration layer
- ❌ Each has own protocols/adapters that don't interoperate
- ❌ No unified API for consumers
- ❌ Unclear which module to use for what purpose

## Research Paper Alignment

### 1. LongMem: Augmenting Language Models with Long-Term Memory
**Paper**: Wang et al., 2023 ([arXiv:2306.07174](https://arxiv.org/abs/2306.07174))

**Key Concepts**:
- Decoupled architecture: frozen LLM + separate memory network
- Long-term memory bank (65k+ tokens)
- Memory encoding and retrieval as separate concerns

**Maps to Our Systems**:
- **Memory Bank** → `neuro_vault` (tri-partite storage)
- **Memory Encoding** → Embedding generation and storage
- **Memory Retrieval** → `recalls` RecallManager

### 2. HippoRAG: Neurobiologically Inspired Long-Term Memory
**Paper**: Gutierrez et al., 2024 ([NeurIPS 2024](https://papers.nips.cc/paper_files/paper/2024/file/6ddc001d07ca4f319af96a3024f6dbd1-Paper-Conference.pdf))

**Key Concepts**:
- Hippocampal indexing inspired by human memory biology
- Knowledge graphs + LLM + vector retrieval
- Pattern separation and pattern completion
- Episodic memory → semantic memory consolidation

**Maps to Our Systems**:
- **Hippocampal Indexing** → `neuro_vault` memory indexing
- **Pattern Separation** → Episodic memory (experiences)
- **Pattern Completion** → Semantic memory (facts)
- **Consolidation** → Episodic → Semantic promotion (currently missing!)
- **Graph Integration** → Could integrate with `reasoning/graph/`

### 3. Think-in-Memory: Recalling and Post-thinking
**Paper**: Liu et al., 2023 ([arXiv:2311.08719](https://arxiv.org/abs/2311.08719))

**Key Concepts**:
- Recall past "thoughts" from memory
- Post-thinking: reflect on recalled memories and update them
- Dynamic feedback loops between reasoning and memory
- Memory has both storage and active reasoning

**Maps to Our Systems**:
- **Recalling** → `neuro_recall` agents retrieving memories
- **Post-thinking** → Agents using SR/ICE to process memories
- **Feedback Loops** → Write back refined memories (currently limited)
- **Active Reasoning** → `reasoning` module + memory integration

### 4. Memory Tiers in LLM-Agents (Review)
**Paper**: ResearchGate review ([Link](https://www.researchgate.net/publication/377603378_Memory_Matters_The_Need_to_Improve_Long-Term_Memory_in_LLM-Agents))

**Key Concepts**:
- Short-term memory (working memory, immediate context)
- Long-term memory (persistent, searchable)
- Episodic memory (time-stamped experiences)
- Semantic memory (distilled facts and knowledge)
- Procedural memory (how-to knowledge, tool usage)

**Maps to Our Systems**:
- **Short-term** → `recalls` ephemeral tier
- **Long-term** → `recalls` persistent tier + `neuro_vault`
- **Episodic/Semantic/Procedural** → `neuro_vault` tri-partite system

## Proposed Unified Architecture

### New Structure: `src/ai_karen_engine/core/memory/`

```
memory/
├── __init__.py                    # Unified Memory API (single entry point)
├── types.py                       # Shared types (MemoryEntry, RecallItem unified)
├── protocols.py                   # Shared protocols (StorageAdapter, EmbeddingClient)
│
├── vault/                         # Long-Term Storage (HippoRAG/LongMem inspired)
│   ├── __init__.py
│   ├── core.py                   # Main NeuroVault (from neuro_vault/)
│   ├── episodic.py               # Episodic memory tier (time-stamped experiences)
│   ├── semantic.py               # Semantic memory tier (distilled facts)
│   ├── procedural.py             # Procedural memory tier (tool patterns)
│   └── storage.py                # Storage backends (Milvus, FAISS, etc.)
│
├── recall/                        # Retrieval Layer (HippoRAG retrieval + LongMem)
│   ├── __init__.py
│   ├── manager.py                # RecallManager (from recalls/)
│   ├── strategies.py             # Retrieval strategies (semantic, temporal, hybrid)
│   ├── adapters.py               # Storage adapters
│   └── reranking.py              # Re-ranking logic
│
├── agents/                        # Think-in-Memory Agents
│   ├── __init__.py
│   ├── hierarchical.py           # NeuroRecall agents (from neuro_recall/)
│   ├── meta_planner.py           # META-PLANNER
│   ├── executor.py               # EXECUTOR
│   └── reflection.py             # Post-thinking and memory updates
│
├── consolidation/                 # Memory Consolidation (HippoRAG inspired)
│   ├── __init__.py
│   ├── episodic_to_semantic.py  # Promote experiences → facts
│   ├── importance_scoring.py    # Determine what to consolidate
│   └── decay.py                  # Memory decay and forgetting
│
└── integration/                   # Integration with Reasoning
    ├── __init__.py
    ├── cognitive_memory.py       # Memory + CognitiveOrchestrator
    └── causal_memory.py          # Memory + CausalReasoning
```

### Key Improvements

1. **Unified Types** (`types.py`)
   ```python
   @dataclass
   class MemoryEntry:
       """Unified memory entry (combines MemoryEntry + RecallItem)"""
       id: str
       content: str
       embedding: Optional[List[float]]

       # Memory classification
       memory_type: MemoryType  # Episodic/Semantic/Procedural
       namespace: MemoryNamespace  # Short/Long/Persistent

       # Temporal
       timestamp: datetime
       last_accessed: Optional[datetime]
       access_count: int

       # Scoring
       importance: float
       confidence: float
       relevance: float

       # Metadata
       metadata: MemoryMetadata
   ```

2. **Unified Protocols** (`protocols.py`)
   ```python
   @runtime_checkable
   class StorageAdapter(Protocol):
       """Unified storage protocol (replaces StoreAdapter + VectorStore)"""
       def store(self, entry: MemoryEntry) -> str: ...
       def retrieve(self, query: MemoryQuery) -> List[MemoryEntry]: ...
       def search_vector(self, vector: List[float], top_k: int) -> List[MemoryEntry]: ...
       def delete(self, entry_id: str) -> bool: ...

   @runtime_checkable
   class EmbeddingProvider(Protocol):
       """Unified embedding protocol"""
       def embed_text(self, text: str) -> List[float]: ...
       def embed_batch(self, texts: List[str]) -> List[List[float]]: ...
   ```

3. **Memory Vault** (`vault/`)
   - Consolidates `neuro_vault` functionality
   - Clear separation: episodic.py, semantic.py, procedural.py
   - Implements HippoRAG-style hippocampal indexing
   - Storage backends unified

4. **Recall Layer** (`recall/`)
   - Consolidates `recalls` RecallManager
   - Retrieval strategies from research papers
   - Unified adapters for all storage backends

5. **Memory Agents** (`agents/`)
   - Consolidates `neuro_recall` agents
   - Implements Think-in-Memory pattern
   - Post-thinking and memory updates
   - Integration with reasoning module

6. **Consolidation** (`consolidation/`) - NEW!
   - Implements HippoRAG consolidation
   - Episodic → Semantic promotion
   - Importance-based filtering
   - Memory decay and forgetting

## Research Paper Mapping

| Paper Concept | Unified Module | Implementation |
|---------------|----------------|----------------|
| **LongMem: Memory Bank** | `memory/vault/` | Long-term storage with tri-partite memory |
| **LongMem: Memory Encoding** | `memory/protocols.py` | `EmbeddingProvider` |
| **LongMem: Memory Retrieval** | `memory/recall/` | `RecallManager` with strategies |
| **HippoRAG: Hippocampal Indexing** | `memory/vault/core.py` | `MemoryIndex` with pattern sep/completion |
| **HippoRAG: Episodic Memory** | `memory/vault/episodic.py` | Time-stamped experiences |
| **HippoRAG: Semantic Memory** | `memory/vault/semantic.py` | Distilled facts |
| **HippoRAG: Consolidation** | `memory/consolidation/` | Episodic → Semantic promotion |
| **Think-in-Memory: Recall** | `memory/recall/manager.py` | Query and retrieve |
| **Think-in-Memory: Post-thinking** | `memory/agents/reflection.py` | Process and update memories |
| **Think-in-Memory: Feedback** | `memory/agents/executor.py` | Write back refined memories |
| **Review: Short-term Memory** | `memory/recall/` (ephemeral) | Working memory |
| **Review: Long-term Memory** | `memory/vault/` | Persistent storage |
| **Review: Memory Tiers** | `memory/types.py` | `MemoryNamespace` enum |

## Migration Path

### Phase 1: Create Unified Structure (Non-breaking)
1. Create `memory/` folder with new structure
2. Implement unified `types.py` and `protocols.py`
3. Keep old modules functioning with deprecation warnings

### Phase 2: Migrate Core Functionality
1. Move `neuro_vault` → `memory/vault/`
2. Move `recalls` → `memory/recall/`
3. Move `neuro_recall` → `memory/agents/`
4. Update internal imports within memory/

### Phase 3: Add New Capabilities
1. Implement `consolidation/` (new!)
2. Add `integration/` with reasoning module
3. Implement research paper algorithms

### Phase 4: Update External Consumers
1. Update API routes to use `memory/`
2. Update services to use unified types
3. Deprecate old imports

### Phase 5: Remove Old Modules
1. Mark old modules as deprecated
2. Final migration period (1-2 versions)
3. Remove `recalls/`, `neuro_recall/`, `neuro_vault/`

## Benefits

### For Developers
- ✅ Single import: `from ai_karen_engine.core.memory import ...`
- ✅ Unified types and protocols (no confusion)
- ✅ Clear separation of concerns (vault vs recall vs agents)
- ✅ Better documentation and examples

### For Architecture
- ✅ Aligns with academic research (HippoRAG, LongMem, Think-in-Memory)
- ✅ Clear memory hierarchy (episodic/semantic/procedural)
- ✅ Proper consolidation pipeline (episodic → semantic)
- ✅ Integration with reasoning module

### For Performance
- ✅ Shared storage adapters (no duplicate connections)
- ✅ Shared embedding providers (no duplicate models)
- ✅ Efficient cross-tier recall
- ✅ Better caching opportunities

### For Research Alignment
- ✅ Directly implements HippoRAG architecture
- ✅ Implements LongMem decoupled design
- ✅ Implements Think-in-Memory feedback loops
- ✅ Easy to cite papers in documentation

## Example Usage (After Migration)

```python
from ai_karen_engine.core.memory import (
    MemorySystem,           # Main entry point
    MemoryEntry,           # Unified type
    MemoryType,            # Episodic/Semantic/Procedural
    MemoryQuery,           # Query builder
    RecallStrategy,        # Retrieval strategies
)

# Initialize unified memory system
memory = MemorySystem(
    vault_backend="milvus",
    embedding_provider="sentence-transformers",
    enable_consolidation=True,  # Auto episodic→semantic
)

# Store episodic memory (experience)
memory.store(
    content="User asked about Python decorators",
    memory_type=MemoryType.EPISODIC,
    importance=8.0,
    metadata={"user_id": "u123", "session": "s456"}
)

# Recall with strategy
results = memory.recall(
    query="What did user ask about Python?",
    strategy=RecallStrategy.HYBRID,  # Semantic + Temporal
    memory_types=[MemoryType.EPISODIC, MemoryType.SEMANTIC],
    top_k=10
)

# Use Think-in-Memory agent
agent = memory.create_agent(
    agent_type="hierarchical",
    enable_reflection=True,  # Post-thinking
)
response = await agent.process(
    query="Explain Python decorators based on our history",
    use_memory=True
)
```

## Recommendation

**Proceed with unified memory architecture?**

This would:
1. Create `src/ai_karen_engine/core/memory/` with structure above
2. Gradually migrate current modules
3. Implement missing pieces (consolidation, integration)
4. Align with research papers
5. Create comprehensive documentation

The work can be done incrementally without breaking existing code.

**Next Steps if Approved:**
1. Create detailed migration plan
2. Implement Phase 1 (unified structure)
3. Write migration guide
4. Update all documentation with paper references
