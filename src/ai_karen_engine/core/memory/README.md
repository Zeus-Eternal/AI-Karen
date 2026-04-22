# Unified Memory System - AI-Karen

**Version**: 2.0.0  
**Status**: Tiered memory architecture in progress

## Overview

This package now uses a tiered memory layout under `core/memory/`:

1. **STM** - `stm/session_buffer.py`
2. **Episodic** - reserved for event journaling and promotion policy
3. **LTM** - reserved for durable semantic storage and curators
4. **Retrieval** - `retrieval/curated_recall.py`, `retrieval/np_memory.py`
5. **Adapters** - `adapters/zvec_api_service.py`, `adapters/zvec_neurovault_adapter.py`
6. **Resilience** - `resilience/offline_mode.py`
7. **Runtime authority** - `memory_runtime_manager.py`

## Target Topology

The intended package boundary is:

```text
src/ai_karen_engine/core/memory/
├── __init__.py
├── memory_runtime_manager.py
├── chat_memory_config.py
├── concurrency_manager.py
├── protocols.py
├── sync_protocol.py
├── types.py
├── stm/
│   └── session_buffer.py
├── episodic/
│   ├── event_store.py
│   ├── event_types.py
│   └── promotion.py
├── ltm/
│   ├── semantic_store.py
│   ├── curator.py
│   └── vault_adapter.py
├── retrieval/
│   ├── curated_recall.py
│   ├── np_memory.py
│   └── ranking.py
├── adapters/
│   ├── zvec_api_service.py
│   └── zvec_neurovault_adapter.py
└── resilience/
    └── offline_mode.py
```

## Authority Model

- `memory_runtime_manager.py` is the sole runtime authority.
- `stm/` owns live session state and short-horizon continuity.
- `episodic/` owns journaling, event modeling, and STM to episodic promotion.
- `ltm/` owns durable semantic storage and episodic to LTM curation.
- `retrieval/` owns recall assembly, scoring, and ranking.
- `adapters/` owns backend translation and persistence gateways.
- `resilience/` owns degraded mode and recovery behavior.
- `chat_memory_config.py`, `concurrency_manager.py`, `protocols.py`, `sync_protocol.py`, and `types.py` remain cross-cutting contracts.

## Research Paper Alignment

Our architecture implements concepts from recent research:

| Paper | Concept | Implementation |
|-------|---------|----------------|
| **LongMem** (Wang et al., 2023) | Decoupled memory bank | `ltm/` and durable adapters |
| **HippoRAG** (Gutierrez et al., 2024) | Hippocampal consolidation | episodic promotion and curator logic |
| **Think-in-Memory** (Liu et al., 2023) | Recall + post-thinking | retrieval and runtime orchestration |

References:
- LongMem: https://arxiv.org/abs/2306.07174
- HippoRAG: https://papers.nips.cc/paper_files/paper/2024/...
- Think-in-Memory: https://arxiv.org/abs/2311.08719

## Quick Start

```python
from ai_karen_engine.core.memory import (
    MemoryEntry,
    MemoryType,
    create_memory_entry,
)

# Create a memory
memory = create_memory_entry(
    content="User asked about Python decorators",
    memory_type=MemoryType.EPISODIC,
    importance=8.0,
    tenant_id="tenant_123",
    user_id="user_456"
)

print(f"Created memory: {memory.id}")
```

## Architecture

### Current focus
- ✅ Unified types (`types.py`)
- ✅ Unified protocols (`protocols.py`)
- ✅ Tiered runtime organization
- 🔄 Episodic / LTM subpackages still being populated from legacy sources

## Unified Types

### MemoryEntry
The single unified memory entry type:

```python
@dataclass
class MemoryEntry:
    id: str
    content: str
    embedding: Optional[List[float]]
    
    # Classification
    memory_type: MemoryType  # Episodic/Semantic/Procedural
    namespace: MemoryNamespace  # Short/Long/Persistent/Ephemeral
    
    # Temporal
    timestamp: datetime
    access_count: int
    
    # Scoring
    importance: float  # 1-10
    confidence: float  # 0-1
    relevance: float  # 0-1 (query-specific)
```

### Enums
- `MemoryType`: Episodic, Semantic, Procedural
- `MemoryNamespace`: Short-term, Long-term, Persistent, Ephemeral
- `MemoryStatus`: Active, Consolidating, Archived, Expired
- `MemoryPriority`: Critical, High, Medium, Low, Minimal

## Protocols

All storage backends implement `StorageBackend`:

```python
class StorageBackend(Protocol):
    def store(self, entry: MemoryEntry) -> str: ...
    def retrieve(self, entry_id: str) -> Optional[MemoryEntry]: ...
    def search_vector(self, vector, top_k) -> List[Tuple[MemoryEntry, float]]: ...
    def delete(self, entry_id: str) -> bool: ...
```

All embedding providers implement `EmbeddingProvider`:

```python
class EmbeddingProvider(Protocol):
    def embed_text(self, text: str) -> List[float]: ...
    def embed_batch(self, texts: List[str]) -> List[List[float]]: ...
```

## Import Surface

Prefer the new tiered modules directly:

```python
from ai_karen_engine.core.memory.memory_runtime_manager import recall_context, update_memory
from ai_karen_engine.core.memory.stm.session_buffer import SessionBuffer
from ai_karen_engine.core.memory.retrieval.curated_recall import filter_curated_memories
from ai_karen_engine.core.memory.retrieval.np_memory import retrieve
```

## Migration Status

### Completed ✅
- [x] Unified types system
- [x] Unified protocol definitions
- [x] Backward compatibility layer
- [x] Documentation

### In Progress 🔄
- [ ] Vault migration (Phase 2)
- [ ] Recall migration (Phase 3)
- [ ] Agents migration (Phase 4)

### Planned 📋
- [ ] Consolidation module (Phase 5)
- [ ] Cognitive integration (Phase 6)
- [ ] Update all consumers (Phase 7)
- [ ] Remove old modules (Phase 8)

## For Developers

### Creating Custom Storage Backend

```python
from ai_karen_engine.core.memory import StorageBackend, MemoryEntry
from typing import Optional, List, Tuple

class MyCustomStorage:
    """Implements StorageBackend protocol"""
    
    def store(self, entry: MemoryEntry) -> str:
        # Store logic here
        return entry.id
    
    def retrieve(self, entry_id: str) -> Optional[MemoryEntry]:
        # Retrieve logic here
        pass
    
    def search_vector(self, vector, *, top_k=10, filters=None):
        # Vector search logic here
        pass
    
    # ... implement other protocol methods
```

### Creating Custom Embedding Provider

```python
from ai_karen_engine.core.memory import EmbeddingProvider

class MyEmbedder:
    """Implements EmbeddingProvider protocol"""
    
    @property
    def dimension(self) -> int:
        return 384
    
    def embed_text(self, text: str) -> List[float]:
        # Embedding logic here
        pass
```

## Future Enhancements

1. **Memory Consolidation** (HippoRAG-inspired)
   - Automatic episodic → semantic promotion
   - Importance-based filtering
   - Background consolidation tasks

2. **Cognitive Integration**
   - Memory + CognitiveOrchestrator
   - Memory + CausalReasoning
   - Think-in-Memory pattern

3. **Advanced Retrieval**
   - Hybrid search strategies
   - Multi-modal memories
   - Graph-based memory networks

## See Also

- [UNIFIED_MEMORY_ARCHITECTURE.md](../../../UNIFIED_MEMORY_ARCHITECTURE.md) - Full architecture design
- [MEMORY_UNIFICATION_PLAN.md](../../../MEMORY_UNIFICATION_PLAN.md) - Implementation roadmap
- [MEMORY_MODULES_DISCOVERY.md](../../../MEMORY_MODULES_DISCOVERY.md) - Discovery of 4 systems

## Contributing

When adding new memory functionality:
1. Use unified `MemoryEntry` type
2. Implement appropriate protocols
3. Maintain backward compatibility
4. Add tests and documentation
