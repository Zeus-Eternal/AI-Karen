"""
Unified Memory System for AI-Karen

This module consolidates 4 separate memory systems:
1. Original memory system (manager.py, ag_ui_manager.py)
2. RecallManager (from recalls/)
3. NeuroVault (from neuro_vault/)
4. NeuroRecall (from neuro_recall/)

Architecture aligned with research papers:
- HippoRAG: Hippocampal-inspired memory consolidation
- LongMem: Long-term memory for LLMs
- Think-in-Memory: Memory with reasoning integration

Version: 1.0.0 (Unified Architecture - Phase 1)
"""

# ===================================
# EXISTING MEMORY SYSTEM (Runtime Support)
# ===================================

from ai_karen_engine.core.memory.memory_runtime_manager import (
    _METRICS,
    get_metrics,
    init_memory,
    export_promoted_artifacts,
    recall_context,
    update_memory,
)
from ai_karen_engine.core.memory.stm.session_buffer import SessionBuffer

from ai_karen_engine.core.memory.retrieval.np_memory import (
    load_jsonl,
    extract_pairs,
    embed_texts,
    retrieve,
)

# ===================================
# UNIFIED MEMORY ARCHITECTURE (Phase 1)
# ===================================

# Unified types
from ai_karen_engine.core.memory.types import (
    # Enums
    MemoryType,
    MemoryNamespace,
    ArtifactType,
    ArtifactSourceTier,
    ArtifactPrivacyTag,
    ArtifactTrainingEligibility,
    MemoryStatus,
    MemoryPriority,
    MemoryVisibility,
    ImportanceLevel,
    # Types
    EmbeddingVector,
    ArtifactImportanceScore,
    ArtifactRetentionScore,
    JSONLike,
    # Data structures
    MemoryMetadata,
    RuntimeMemoryArtifact,
    MemoryEntry,
    MemoryQuery,
    MemoryQueryResult,
    # Helper functions
    make_memory_id,
    clamp,
    decay_score,
    ttl_to_expires,
    now_utc,
    create_memory_entry,
    # Constants
    DEFAULT_DECAY_LAMBDA,
    DEFAULT_TOP_K,
    DEFAULT_IMPORTANCE,
    DEFAULT_CONFIDENCE,
    MAX_CONTENT_LENGTH,
    MAX_EMBEDDING_DIM,
    MAX_TAGS,
    MAX_KEYWORDS,
    TTL_EPHEMERAL,
    TTL_SHORT_TERM,
    TTL_LONG_TERM,
    TTL_PERSISTENT,
)

# Unified protocols
from ai_karen_engine.core.memory.protocols import (
    # Core protocols
    StorageBackend,
    EmbeddingProvider,
    Reranker,
    QueryExecutor,
    MemoryConsolidator,
    MemoryManager,
    # Type aliases
    StorageResult,
    SearchResult,
)


__all__ = [
    # ===================================
    # RUNTIME SUPPORT
    # ===================================
    "recall_context",
    "update_memory",
    "get_metrics",
    "_METRICS",
    "init_memory",
    "export_promoted_artifacts",
    "SessionBuffer",
    # Neuro-recall memory utilities
    "load_jsonl",
    "extract_pairs",
    "embed_texts",
    "retrieve",
    # ===================================
    # UNIFIED MEMORY ARCHITECTURE (Phase 1)
    # ===================================
    # Enums
    "MemoryType",
    "MemoryNamespace",
    "ArtifactType",
    "ArtifactSourceTier",
    "ArtifactPrivacyTag",
    "ArtifactTrainingEligibility",
    "MemoryStatus",
    "MemoryPriority",
    "MemoryVisibility",
    "ImportanceLevel",
    # Types
    "EmbeddingVector",
    "ArtifactImportanceScore",
    "ArtifactRetentionScore",
    "JSONLike",
    # Data structures
    "MemoryMetadata",
    "RuntimeMemoryArtifact",
    "MemoryEntry",
    "MemoryQuery",
    "MemoryQueryResult",
    # Protocols
    "StorageBackend",
    "EmbeddingProvider",
    "Reranker",
    "QueryExecutor",
    "MemoryConsolidator",
    "MemoryManager",
    "StorageResult",
    "SearchResult",
    # Helper functions
    "make_memory_id",
    "clamp",
    "decay_score",
    "ttl_to_expires",
    "now_utc",
    "create_memory_entry",
    # Constants
    "DEFAULT_DECAY_LAMBDA",
    "DEFAULT_TOP_K",
    "DEFAULT_IMPORTANCE",
    "DEFAULT_CONFIDENCE",
    "MAX_CONTENT_LENGTH",
    "MAX_EMBEDDING_DIM",
    "MAX_TAGS",
    "MAX_KEYWORDS",
    "TTL_EPHEMERAL",
    "TTL_SHORT_TERM",
    "TTL_LONG_TERM",
    "TTL_PERSISTENT",
]
