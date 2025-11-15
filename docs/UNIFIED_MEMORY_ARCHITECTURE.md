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
