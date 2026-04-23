"""Memory retrieval package."""

from .curated_recall import (
    CURATED_MEMORY_KIND,
    DEFAULT_CURATED_MEMORY_CLASSES,
    build_curated_metadata_filter,
    filter_curated_memories,
    is_curated_memory_metadata,
)
from .np_memory import load_jsonl, extract_pairs, embed_texts, retrieve
from .retrieval_router import get_retrieval_router, HybridRetrievalRouter
from .recall_manager import (
    EmbeddingClient,
    InMemoryStore,
    RecallItem,
    RecallManager,
    RecallManagerConfig,
    RecallNamespace,
    RecallPayload,
    RecallPriority,
    RecallQuery,
    RecallResult,
    RecallStats,
    RecallStatus,
    RecallType,
    RecallVisibility,
    Reranker,
    build_default_manager,
)

__all__ = [
    "CURATED_MEMORY_KIND",
    "DEFAULT_CURATED_MEMORY_CLASSES",
    "build_curated_metadata_filter",
    "filter_curated_memories",
    "is_curated_memory_metadata",
    "load_jsonl",
    "extract_pairs",
    "embed_texts",
    "retrieve",
    "get_retrieval_router",
    "HybridRetrievalRouter",
    "EmbeddingClient",
    "InMemoryStore",
    "RecallItem",
    "RecallManager",
    "RecallManagerConfig",
    "RecallNamespace",
    "RecallPayload",
    "RecallPriority",
    "RecallQuery",
    "RecallResult",
    "RecallStats",
    "RecallStatus",
    "RecallType",
    "RecallVisibility",
    "Reranker",
    "build_default_manager",
]
