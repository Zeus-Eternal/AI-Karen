# Memory Module Unification - Implementation Plan

## Executive Summary

This document outlines the step-by-step plan to unify three separate memory modules (`recalls/`, `neuro_recall/`, `neuro_vault/`) into a single coherent `memory/` subsystem aligned with recent research papers on LLM memory architectures.

## Current vs Proposed Structure

### Current (Fragmented)
```
core/
├── recalls/              # RecallManager, memory tiers
├── neuro_recall/         # Agents with SR/ICE
└── neuro_vault/          # Tri-partite memory
```

### Proposed (Unified)
```
core/
└── memory/               # Unified memory subsystem
    ├── vault/            # Long-term storage (HippoRAG/LongMem)
    ├── recall/           # Retrieval layer
    ├── agents/           # Think-in-Memory agents
    ├── consolidation/    # Memory consolidation (NEW!)
    └── integration/      # Reasoning integration
```

## Implementation Phases

### Phase 1: Foundation (Week 1) ✅ Non-Breaking

**Goal**: Create unified structure without breaking existing code

**Tasks**:
1. Create `memory/` folder structure
2. Implement unified types (`types.py`)
3. Implement unified protocols (`protocols.py`)
4. Create main `__init__.py` with facade pattern

**Files to Create**:
```
memory/
├── __init__.py           # Main API facade
├── types.py              # Unified MemoryEntry, MemoryQuery, etc.
├── protocols.py          # StorageAdapter, EmbeddingProvider
└── README.md             # Architecture documentation
```

**Code Example** (`types.py`):
```python
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any

class MemoryType(str, Enum):
    """Tri-partite memory classification"""
    EPISODIC = "episodic"      # Time-stamped experiences
    SEMANTIC = "semantic"      # Distilled facts
    PROCEDURAL = "procedural"  # Tool patterns/workflows

class MemoryNamespace(str, Enum):
    """Memory tier/duration"""
    SHORT_TERM = "short_term"      # Working memory
    LONG_TERM = "long_term"        # Persistent
    PERSISTENT = "persistent"      # Never expires
    EPHEMERAL = "ephemeral"        # Temporary

@dataclass
class MemoryMetadata:
    """Metadata for memory entries"""
    tenant_id: str
    user_id: str
    conversation_id: Optional[str] = None
    session_id: Optional[str] = None
    source: str = "user"
    tags: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)

@dataclass
class MemoryEntry:
    """Unified memory entry (replaces MemoryEntry + RecallItem)"""
    id: str
    content: str
    embedding: Optional[List[float]] = None

    # Classification
    memory_type: MemoryType = MemoryType.EPISODIC
    namespace: MemoryNamespace = MemoryNamespace.LONG_TERM

    # Temporal
    timestamp: datetime = field(default_factory=datetime.utcnow)
    last_accessed: Optional[datetime] = None
    access_count: int = 0

    # Scoring
    importance: float = 5.0     # 1-10 scale
    confidence: float = 1.0     # 0-1 scale
    relevance: float = 0.0      # Query-specific

    # Metadata
    metadata: Optional[MemoryMetadata] = None

    # Lifecycle
    status: str = "active"
    expires_at: Optional[datetime] = None
    ttl_seconds: Optional[float] = None
```

**Verification**: Old modules still work, new module importable

---

### Phase 2: Migrate Vault (Week 2) ✅ Non-Breaking

**Goal**: Move `neuro_vault/` → `memory/vault/` with adapters

**Tasks**:
1. Create `memory/vault/` folder
2. Move `neuro_vault_core.py` → `vault/core.py`
3. Move `neuro_vault.py` → `vault/neuro_vault.py`
4. Create adapter in old location that imports from new

**Files**:
```
memory/vault/
├── __init__.py           # Re-export NeuroVault, MemoryEntry
├── core.py               # Core vault logic (from neuro_vault_core.py)
├── neuro_vault.py        # Main NeuroVault class
├── episodic.py           # Episodic memory tier (extracted)
├── semantic.py           # Semantic memory tier (extracted)
├── procedural.py         # Procedural memory tier (extracted)
└── storage.py            # Storage backends
```

**Backward Compatibility Adapter** (`neuro_vault/__init__.py`):
```python
"""
DEPRECATED: This module has moved to ai_karen_engine.core.memory.vault

This file provides backward compatibility. Please update imports to:
    from ai_karen_engine.core.memory.vault import NeuroVault
"""
import warnings
from ai_karen_engine.core.memory.vault import (
    NeuroVault,
    MemoryEntry,
    MemoryType,
    MemoryStatus,
    # ... all exports
)

warnings.warn(
    "ai_karen_engine.core.neuro_vault is deprecated. "
    "Use ai_karen_engine.core.memory.vault instead.",
    DeprecationWarning,
    stacklevel=2
)

__all__ = [...]  # Same as before
```

**Verification**: Both old and new imports work with deprecation warning

---

### Phase 3: Migrate Recall (Week 3) ✅ Non-Breaking

**Goal**: Move `recalls/` → `memory/recall/`

**Tasks**:
1. Create `memory/recall/` folder
2. Move `recall_manager.py` → `recall/manager.py`
3. Move `recall_types.py` → integrate into `memory/types.py`
4. Create adapter in old location

**Files**:
```
memory/recall/
├── __init__.py           # Re-export RecallManager
├── manager.py            # RecallManager (from recall_manager.py)
├── strategies.py         # Retrieval strategies
├── adapters.py           # Storage adapters (merged with vault/storage.py)
└── reranking.py          # Re-ranking logic
```

**Unify Types**: Merge `RecallItem` → `MemoryEntry`
```python
# Old RecallItem fields → MemoryEntry fields
RecallItem.recall_id      → MemoryEntry.id
RecallItem.text           → MemoryEntry.content
RecallItem.embedding      → MemoryEntry.embedding
RecallItem.namespace      → MemoryEntry.namespace
RecallItem.recall_type    → MemoryEntry.memory_type
# ... etc
```

**Backward Compatibility Adapter** (`recalls/__init__.py`):
```python
"""
DEPRECATED: This module has moved to ai_karen_engine.core.memory.recall
"""
import warnings
from ai_karen_engine.core.memory.recall import (
    RecallManager,
    RecallQuery,
    RecallResult,
    # ...
)
from ai_karen_engine.core.memory.types import (
    MemoryEntry as RecallItem,  # Alias for compatibility
    # ...
)

warnings.warn(
    "ai_karen_engine.core.recalls is deprecated. "
    "Use ai_karen_engine.core.memory.recall instead.",
    DeprecationWarning,
    stacklevel=2
)
```

**Verification**: Both old and new imports work

---

### Phase 4: Migrate Agents (Week 4) ✅ Non-Breaking

**Goal**: Move `neuro_recall/` → `memory/agents/`

**Tasks**:
1. Create `memory/agents/` folder
2. Move agent files to new location
3. Update imports to use `memory.vault` and `memory.recall`
4. Create adapter in old location

**Files**:
```
memory/agents/
├── __init__.py
├── hierarchical.py       # Main agent logic
├── meta_planner.py       # META-PLANNER (extracted from agent.py)
├── executor.py           # EXECUTOR (extracted from agent.py)
├── reflection.py         # Post-thinking (NEW! - Think-in-Memory)
└── local_server.py       # Local server (from agent_local_server.py)
```

**Update Imports**:
```python
# Old
from ai_karen_engine.core.reasoning.soft_reasoning.engine import SoftReasoningEngine
from ai_karen_engine.core.reasoning.synthesis.ice_wrapper import PremiumICEWrapper

# Still valid (reasoning stays separate)

# New additions
from ai_karen_engine.core.memory.vault import NeuroVault
from ai_karen_engine.core.memory.recall import RecallManager
```

**Backward Compatibility** (`neuro_recall/__init__.py`):
```python
"""
DEPRECATED: This module has moved to ai_karen_engine.core.memory.agents
"""
# ... similar pattern
```

---

### Phase 5: Add Consolidation (Week 5) 🆕 NEW CAPABILITY

**Goal**: Implement memory consolidation (HippoRAG-inspired)

**Tasks**:
1. Create `memory/consolidation/` folder
2. Implement episodic → semantic promotion
3. Implement importance scoring
4. Implement memory decay
5. Integrate with vault and recall

**Files**:
```
memory/consolidation/
├── __init__.py
├── consolidator.py       # Main consolidation logic
├── episodic_to_semantic.py  # Promotion algorithm
├── importance_scoring.py    # Determine what to promote
├── decay.py                 # Memory decay/forgetting
└── scheduler.py             # Background consolidation tasks
```

**Code Example** (`episodic_to_semantic.py`):
```python
"""
HippoRAG-inspired memory consolidation.

Promotes frequently accessed or important episodic memories
to semantic memory (distilled facts).
"""
from typing import List
from ai_karen_engine.core.memory.types import MemoryEntry, MemoryType
from ai_karen_engine.core.memory.vault import NeuroVault

class EpisodicToSemanticConsolidator:
    """
    Consolidates episodic memories into semantic facts.

    Based on HippoRAG's hippocampal consolidation pattern.
    """

    def __init__(
        self,
        vault: NeuroVault,
        min_access_count: int = 3,
        min_importance: float = 7.0,
        consolidation_window: timedelta = timedelta(days=7)
    ):
        self.vault = vault
        self.min_access_count = min_access_count
        self.min_importance = min_importance
        self.consolidation_window = consolidation_window

    def identify_candidates(self) -> List[MemoryEntry]:
        """Find episodic memories ready for consolidation."""
        # Get episodic memories from vault
        episodes = self.vault.query(
            memory_type=MemoryType.EPISODIC,
            min_importance=self.min_importance,
            since=datetime.utcnow() - self.consolidation_window
        )

        # Filter by access count
        candidates = [
            m for m in episodes
            if m.access_count >= self.min_access_count
        ]

        return candidates

    async def consolidate(self, episode: MemoryEntry) -> MemoryEntry:
        """
        Convert episodic memory to semantic memory.

        Uses LLM to distill experience into fact.
        """
        # Use reasoning module to extract semantic content
        from ai_karen_engine.core.reasoning import CognitiveOrchestrator

        orchestrator = CognitiveOrchestrator()

        # Extract fact from experience
        result = await orchestrator.process({
            "task_type": "distill_fact",
            "content": episode.content,
            "metadata": episode.metadata
        })

        # Create semantic memory
        semantic = MemoryEntry(
            id=f"semantic_{episode.id}",
            content=result.distilled_fact,
            memory_type=MemoryType.SEMANTIC,
            namespace=MemoryNamespace.PERSISTENT,
            importance=episode.importance,
            confidence=result.confidence,
            metadata={
                **episode.metadata,
                "derived_from": episode.id,
                "consolidation_time": datetime.utcnow().isoformat()
            }
        )

        # Store semantic memory
        self.vault.store(semantic)

        # Archive original episodic (optionally)
        episode.status = "consolidated"
        self.vault.update(episode)

        return semantic
```

**Verification**: Consolidation runs and promotes memories

---

### Phase 6: Integration Layer (Week 6) 🆕 NEW CAPABILITY

**Goal**: Integrate memory with reasoning module

**Tasks**:
1. Create `memory/integration/` folder
2. Implement cognitive-memory bridge
3. Implement causal-memory bridge
4. Create unified query interface

**Files**:
```
memory/integration/
├── __init__.py
├── cognitive_memory.py    # Memory + CognitiveOrchestrator
├── causal_memory.py       # Memory + CausalReasoning
└── reasoning_bridge.py    # General reasoning-memory bridge
```

**Code Example** (`cognitive_memory.py`):
```python
"""
Integration between Memory and CognitiveOrchestrator.

Implements Think-in-Memory pattern: reasoning uses memory,
memory is updated based on reasoning.
"""
from ai_karen_engine.core.memory import MemorySystem
from ai_karen_engine.core.reasoning import CognitiveOrchestrator, CognitiveTask

class CognitiveMemorySystem:
    """
    Unified system combining memory and cognitive reasoning.

    Implements Think-in-Memory feedback loops.
    """

    def __init__(self, memory: MemorySystem, orchestrator: CognitiveOrchestrator):
        self.memory = memory
        self.orchestrator = orchestrator

    async def recall_and_think(self, query: str) -> dict:
        """
        1. Recall relevant memories
        2. Use cognitive orchestrator to process
        3. Update memories based on reasoning (post-thinking)
        """
        # Step 1: Recall
        recalled = self.memory.recall(
            query=query,
            strategy="hybrid",
            top_k=10
        )

        # Step 2: Cognitive processing
        task = CognitiveTask(
            query=query,
            context={
                "memories": [m.content for m in recalled],
                "memory_ids": [m.id for m in recalled]
            }
        )

        result = await self.orchestrator.process(task)

        # Step 3: Post-thinking - update memories
        for memory_id in result.context.get("accessed_memories", []):
            self.memory.update_access(memory_id)

        # Store new episodic memory of this reasoning
        self.memory.store(
            content=f"Reasoning: {query} → {result.response}",
            memory_type="episodic",
            importance=result.confidence * 10,
            metadata={"reasoning_trace": result.trace}
        )

        return {
            "response": result.response,
            "recalled_memories": recalled,
            "reasoning_trace": result.trace
        }
```

---

### Phase 7: Update Consumers (Week 7-8)

**Goal**: Update external code to use unified memory

**Tasks**:
1. Update API routes
2. Update services
3. Update tests
4. Update documentation

**Files to Update**:
- `api_routes/chat_runtime.py`
- `api_routes/copilot_routes.py`
- `services/memory_service.py`
- `services/unified_memory_service.py`
- All test files

**Migration Pattern**:
```python
# Old
from ai_karen_engine.core.neuro_vault import NeuroVault, MemoryEntry
from ai_karen_engine.core.recalls import RecallManager, RecallQuery

vault = NeuroVault(...)
recall = RecallManager(...)

# New
from ai_karen_engine.core.memory import MemorySystem

memory = MemorySystem(
    vault_backend="milvus",
    enable_consolidation=True
)

# Single unified API
memory.store(...)
memory.recall(...)
memory.consolidate()
```

---

### Phase 8: Deprecation & Cleanup (Week 9-10)

**Goal**: Remove old modules

**Tasks**:
1. Add deprecation warnings (Done in Phase 2-4)
2. Update all internal references
3. Migration guide for external users
4. Final migration period (2-4 weeks)
5. Remove old modules

**Timeline**:
- Week 9: Announce deprecation
- Week 10-12: Migration period (warnings only)
- Week 13: Remove old modules

---

## Verification Checklist

### Phase 1
- [ ] `memory/` folder created
- [ ] `types.py` with unified `MemoryEntry`
- [ ] `protocols.py` with unified protocols
- [ ] Imports work: `from ai_karen_engine.core.memory import MemoryEntry`

### Phase 2
- [ ] `memory/vault/` created
- [ ] NeuroVault moved and working
- [ ] Old import still works with warning
- [ ] Tests pass

### Phase 3
- [ ] `memory/recall/` created
- [ ] RecallManager moved and working
- [ ] Old import still works with warning
- [ ] Tests pass

### Phase 4
- [ ] `memory/agents/` created
- [ ] NeuroRecall agents moved
- [ ] Old import still works with warning
- [ ] Tests pass

### Phase 5
- [ ] `memory/consolidation/` created
- [ ] Episodic→Semantic promotion works
- [ ] Background task scheduler works
- [ ] Tests pass

### Phase 6
- [ ] `memory/integration/` created
- [ ] Cognitive-memory integration works
- [ ] Causal-memory integration works
- [ ] Tests pass

### Phase 7
- [ ] All API routes updated
- [ ] All services updated
- [ ] All tests updated
- [ ] Documentation updated

### Phase 8
- [ ] Deprecation warnings in place
- [ ] Migration guide published
- [ ] Old modules removed
- [ ] All tests pass

---

## Risk Mitigation

### Risk 1: Breaking Changes
**Mitigation**: Keep old modules with adapters during transition

### Risk 2: Performance Regression
**Mitigation**: Benchmark each phase, shared adapters should improve performance

### Risk 3: Integration Complexity
**Mitigation**: Incremental phases, extensive testing

### Risk 4: User Confusion
**Mitigation**: Clear documentation, migration guide, examples

---

## Success Metrics

- [ ] Single import for all memory operations
- [ ] No duplicate storage connections
- [ ] Memory consolidation working (episodic → semantic)
- [ ] Integration with reasoning module
- [ ] All research paper concepts implemented
- [ ] Comprehensive documentation with paper references
- [ ] All old tests pass
- [ ] New integration tests pass

---

## Next Steps

**If approved:**
1. Create Phase 1 implementation branch
2. Implement unified types and protocols
3. Write tests for Phase 1
4. Review and merge
5. Continue with Phase 2

**Estimated Total Time**: 10 weeks for full migration

**Quick Start (Phase 1 only)**: 1 week
