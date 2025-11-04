# src/ai_karen_engine/core/recalls/__init__.py
"""
NeuroVault (Recalls) — Public Facade

This package surface centralizes:
- Types and enums for recalls (RecallItem, RecallQuery, RecallResult, …)
- The orchestrator (RecallManager) and config
- Store adapter protocol(s) and in-memory default
- Optional helpers: default factory, lightweight singleton accessor
- Version + minimal metrics hooks

Design goals:
- Stable, import-friendly surface for the rest of Kari AI
- Local-first, backend-agnostic: swap real stores (Milvus/pgvector/Redis) via DI
"""

from __future__ import annotations

from typing import Optional

# ---- Version ---------------------------------------------------------------

__version__: str = "0.3.9"  # sync with NeuroVault Core phase


# ---- Types & Enums (re-export) --------------------------------------------

from .recall_types import (
    # Enums
    RecallNamespace,
    RecallType,
    RecallPriority,
    RecallStatus,
    RecallVisibility,
    # Aliases
    EmbeddingVector,
    JSONLike,
    # Models
    RecallContext,
    RecallPayload,
    RecallItem,
    RecallQuery,
    RecallResult,
    RecallError,
    # Helpers
    make_recall_id,
    clamp01,
    decay_score,
    ttl_to_expires,
    now_utc,
    new_recall,
    # Defaults
    DEFAULT_DECAY_LAMBDA,
    DEFAULT_MAX_TAGS,
    DEFAULT_MAX_METADATA_KV,
    DEFAULT_MAX_METADATA_KEY_LEN,
    DEFAULT_MAX_METADATA_VAL_LEN,
    DEFAULT_MAX_EMBED_DIM,
)

# ---- Manager & Adapters (re-export) ---------------------------------------

from .recall_manager import (
    # Orchestrator
    RecallManager,
    RecallManagerConfig,
    # Protocols
    EmbeddingClient,
    Reranker,
    StoreAdapter,
    # Defaults / factory
    InMemoryStore,
    build_default_manager,
)

# Optional extras live in recall_manager (kept isolated from core)
try:  # pragma: no cover
    from .recall_manager import HFEmbeddingClient, JSONLRecallIndex  # type: ignore
except Exception:  # pragma: no cover
    # Extras are optional; absence should not break core imports.
    HFEmbeddingClient = None  # type: ignore
    JSONLRecallIndex = None  # type: ignore


# ---- Lightweight Singleton Accessor ---------------------------------------

# Provides a convenient, lazy-initialized manager for simple consumers.
# Power users should DI their own manager instance explicitly.
_DEFAULT_MANAGER: Optional[RecallManager] = None

def get_recall_manager() -> RecallManager:
    """
    Returns a process-local default RecallManager.
    Uses in-memory stores and no embedder by default (safe baseline).
    """
    global _DEFAULT_MANAGER
    if _DEFAULT_MANAGER is None:
        _DEFAULT_MANAGER = build_default_manager()
    return _DEFAULT_MANAGER


def set_recall_manager(manager: RecallManager) -> None:
    """
    Override the process-local default RecallManager (e.g., during app bootstrap).
    """
    global _DEFAULT_MANAGER
    _DEFAULT_MANAGER = manager


# ---- Minimal Metrics Hooks (no hard deps) ----------------------------------

# These are no-ops by default; wire Prometheus in your app layer if desired.

def register_metrics() -> None:  # pragma: no cover
    """
    Placeholder for metrics registration. Call from your service bootstrap if you
    want to expose histograms/counters around RecallManager.query/upsert.
    """
    return None


# ---- Public Surface --------------------------------------------------------

__all__ = [
    "__version__",
    # Enums
    "RecallNamespace",
    "RecallType",
    "RecallPriority",
    "RecallStatus",
    "RecallVisibility",
    # Aliases
    "EmbeddingVector",
    "JSONLike",
    # Models
    "RecallContext",
    "RecallPayload",
    "RecallItem",
    "RecallQuery",
    "RecallResult",
    "RecallError",
    # Helpers
    "make_recall_id",
    "clamp01",
    "decay_score",
    "ttl_to_expires",
    "now_utc",
    "new_recall",
    # Manager/Config
    "RecallManager",
    "RecallManagerConfig",
    # Protocols & Adapters
    "EmbeddingClient",
    "Reranker",
    "StoreAdapter",
    "InMemoryStore",
    # Factory
    "build_default_manager",
    # Singleton helpers
    "get_recall_manager",
    "set_recall_manager",
    # Optional extras
    "HFEmbeddingClient",
    "JSONLRecallIndex",
    # Defaults
    "DEFAULT_DECAY_LAMBDA",
    "DEFAULT_MAX_TAGS",
    "DEFAULT_MAX_METADATA_KV",
    "DEFAULT_MAX_METADATA_KEY_LEN",
    "DEFAULT_MAX_METADATA_VAL_LEN",
    "DEFAULT_MAX_EMBED_DIM",
]
