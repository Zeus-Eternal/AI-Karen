# Unified Memory System - AI-Karen

**Version**: 1.0.0 (Phase 1)  
**Status**: Foundation implemented, migration in progress

## Overview

This module provides a unified memory architecture consolidating **4 separate memory systems**:

1. **Original memory system** - manager.py, AG-UI integration
2. **RecallManager** - from `recalls/` module
3. **NeuroVault** - from `neuro_vault/` tri-partite memory
4. **NeuroRecall** - from `neuro_recall/` hierarchical agents

## Research Paper Alignment

Our architecture implements concepts from recent research:

| Paper | Concept | Implementation |
|-------|---------|----------------|
| **LongMem** (Wang et al., 2023) | Decoupled memory bank | `vault/` storage layer |
| **HippoRAG** (Gutierrez et al., 2024) | Hippocampal consolidation | `consolidation/` module |
| **Think-in-Memory** (Liu et al., 2023) | Recall + post-thinking | `agents/` with reflection |

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

### Phase 1 (Current): Foundation
- ✅ Unified types (`types.py`)
- ✅ Unified protocols (`protocols.py`)
- ✅ Backward compatibility maintained

### Phase 2-4: Migration
- Migrate `neuro_vault/` → `memory/vault/`
- Migrate `recalls/` → `memory/recall/`
- Migrate `neuro_recall/` → `memory/agents/`

### Phase 5-6: New Capabilities
- Memory consolidation (episodic → semantic)
- Cognitive-memory integration
- Causal-memory integration

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

## Backward Compatibility

All existing imports continue to work:

```python
# OLD (still works)
from ai_karen_engine.core.memory import recall_context, update_memory
from ai_karen_engine.core.memory import AGUIMemoryManager

# NEW (Phase 1)
from ai_karen_engine.core.memory import MemoryEntry, MemoryType
from ai_karen_engine.core.memory import StorageBackend, EmbeddingProvider
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
