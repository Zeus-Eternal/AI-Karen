"""
NeuroVault Core - Comprehensive Tri-Partite Memory System

This module implements the core NeuroVault memory architecture with:
- Episodic Memory: Time-stamped experiences and interactions
- Semantic Memory: Distilled facts and knowledge
- Procedural Memory: Tool usage patterns and workflows
- Intelligent retrieval with hybrid temporal-semantic scoring
- Memory decay and lifecycle management
- Security, privacy, and RBAC controls
- Comprehensive observability and metrics

Architecture follows neuroscience-inspired principles while maintaining
production-grade performance and reliability.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import math
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np

logger = logging.getLogger(__name__)


# ===================================
# MEMORY TYPES AND ENUMS
# ===================================

class MemoryType(str, Enum):
    """Tri-partite memory types following neuroscience principles."""
    EPISODIC = "episodic"      # Time-stamped experiences
    SEMANTIC = "semantic"      # Distilled facts and knowledge
    PROCEDURAL = "procedural"  # Tool usage patterns and workflows


class MemoryStatus(str, Enum):
    """Memory lifecycle status."""
    ACTIVE = "active"          # Currently accessible
    CONSOLIDATING = "consolidating"  # Being promoted from episodic to semantic
    ARCHIVED = "archived"      # Soft-deleted, retained for audit
    EXPIRED = "expired"        # Hard-deleted after retention period


class ImportanceLevel(Enum):
    """Importance scoring for memories."""
    CRITICAL = 10
    HIGH = 8
    MEDIUM = 5
    LOW = 3
    MINIMAL = 1


# ===================================
# DATA STRUCTURES
# ===================================

@dataclass
class MemoryMetadata:
    """Metadata for memory entries."""
    tenant_id: str
    user_id: str
    conversation_id: Optional[str] = None
    session_id: Optional[str] = None
    source: str = "user"  # user|ai|system|tool
    tags: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MemoryEntry:
    """
    Core memory entry structure.

    Supports all three memory types with appropriate metadata and scoring.
    """
    id: str
    memory_type: MemoryType
    content: str
    embedding: Optional[List[float]] = None
    metadata: Optional[MemoryMetadata] = None

    # Temporal information
    timestamp: datetime = field(default_factory=datetime.utcnow)
    last_accessed: Optional[datetime] = None
    access_count: int = 0

    # Scoring and relevance
    importance_score: float = 5.0  # 1-10 scale
    confidence: float = 1.0  # 0-1 scale
    decay_lambda: float = 0.08  # Decay rate (type-specific)

    # Lifecycle
    status: MemoryStatus = MemoryStatus.ACTIVE
    ttl_days: Optional[int] = None
    expires_at: Optional[datetime] = None

    # Relationships
    parent_id: Optional[str] = None  # For consolidated memories
    related_ids: List[str] = field(default_factory=list)

    # Procedural-specific
    tool_name: Optional[str] = None
    success_rate: Optional[float] = None
    usage_count: int = 0

    # Episodic-specific
    emotional_valence: Optional[float] = None  # -1 to 1
    event_type: Optional[str] = None

    def calculate_relevance_score(
        self,
        current_time: Optional[datetime] = None,
        semantic_score: float = 1.0,
    ) -> float:
        """
        Calculate composite relevance score using:
        - Semantic similarity (cosine)
        - Temporal decay
        - Importance weighting
        - Access frequency bonus

        Formula: R = (S * I * D) + A
        Where:
          S = Semantic score (cosine similarity)
          I = Importance factor (normalized)
          D = Decay factor (exponential)
          A = Access bonus (logarithmic)
        """
        if current_time is None:
            current_time = datetime.utcnow()

        # Temporal decay: e^(-λt)
        age_seconds = (current_time - self.timestamp).total_seconds()
        age_hours = age_seconds / 3600.0
        decay_factor = math.exp(-self.decay_lambda * age_hours)

        # Importance weighting (normalize to 0-1)
        importance_factor = self.importance_score / 10.0

        # Access frequency bonus (logarithmic to prevent runaway)
        access_bonus = math.log(1 + self.access_count) * 0.1

        # Composite score
        relevance = (semantic_score * importance_factor * decay_factor) + access_bonus

        return max(0.0, min(1.0, relevance))  # Clamp to [0, 1]

    def should_consolidate(self, threshold_hours: int = 24) -> bool:
        """
        Determine if episodic memory should be consolidated to semantic.

        Criteria:
        - Memory is episodic
        - Age exceeds threshold
        - Importance score is significant
        - Access count indicates repeated relevance
        """
        if self.memory_type != MemoryType.EPISODIC:
            return False

        age_hours = (datetime.utcnow() - self.timestamp).total_seconds() / 3600.0

        return (
            age_hours >= threshold_hours
            and self.importance_score >= 6.0
            and self.access_count >= 2
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "memory_type": self.memory_type.value,
            "content": self.content,
            "embedding": self.embedding,
            "metadata": asdict(self.metadata) if self.metadata else None,
            "timestamp": self.timestamp.isoformat(),
            "last_accessed": self.last_accessed.isoformat() if self.last_accessed else None,
            "access_count": self.access_count,
            "importance_score": self.importance_score,
            "confidence": self.confidence,
            "decay_lambda": self.decay_lambda,
            "status": self.status.value,
            "ttl_days": self.ttl_days,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "parent_id": self.parent_id,
            "related_ids": self.related_ids,
            "tool_name": self.tool_name,
            "success_rate": self.success_rate,
            "usage_count": self.usage_count,
            "emotional_valence": self.emotional_valence,
            "event_type": self.event_type,
        }


@dataclass
class RetrievalRequest:
    """Request parameters for memory retrieval."""
    query: str
    query_embedding: Optional[List[float]] = None
    tenant_id: str = ""
    user_id: str = ""
    memory_types: Optional[List[MemoryType]] = None
    top_k: int = 5
    min_relevance: float = 0.3
    temporal_window_hours: Optional[int] = None
    require_rbac: bool = True
    include_archived: bool = False


@dataclass
class RetrievalResult:
    """Result from memory retrieval."""
    memories: List[MemoryEntry]
    scores: List[float]
    total_matches: int
    retrieval_time_ms: float
    cache_hit: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


# ===================================
# DECAY FUNCTIONS
# ===================================

class DecayFunction:
    """Memory decay functions for different memory types."""

    # Decay lambdas (per hour) based on requirements
    DECAY_LAMBDAS = {
        MemoryType.EPISODIC: 0.12,     # Fast decay
        MemoryType.SEMANTIC: 0.04,     # Slow decay
        MemoryType.PROCEDURAL: 0.02,   # Very slow decay
    }

    @classmethod
    def get_decay_lambda(cls, memory_type: MemoryType) -> float:
        """Get decay lambda for memory type."""
        return cls.DECAY_LAMBDAS.get(memory_type, 0.08)

    @classmethod
    def calculate_decay_factor(
        cls,
        memory_type: MemoryType,
        age_hours: float,
    ) -> float:
        """Calculate exponential decay factor: e^(-λt)"""
        lambda_value = cls.get_decay_lambda(memory_type)
        return math.exp(-lambda_value * age_hours)

    @classmethod
    def calculate_half_life(cls, memory_type: MemoryType) -> float:
        """Calculate half-life in hours: ln(2)/λ"""
        lambda_value = cls.get_decay_lambda(memory_type)
        return math.log(2) / lambda_value if lambda_value > 0 else float('inf')


# ===================================
# EMBEDDING MANAGER
# ===================================

class EmbeddingManager:
    """
    Manages text embeddings for semantic similarity.

    Uses all-MPNet-base-v2 or fallback to simpler embeddings.
    """

    def __init__(self, model_name: str = "all-MPNet-base-v2", dim: int = 768):
        """Initialize embedding manager."""
        self.model_name = model_name
        self.dim = dim
        self._model = None
        self._initialized = False

    async def initialize(self):
        """Lazy initialization of embedding model."""
        if self._initialized:
            return

        try:
            # Try to use sentence-transformers
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.model_name)
            self.dim = self._model.get_sentence_embedding_dimension()
            logger.info(f"Initialized {self.model_name} embedding model (dim={self.dim})")
        except Exception as e:
            logger.warning(f"Failed to load {self.model_name}: {e}, using fallback")
            self._model = None

        self._initialized = True

    async def embed(self, text: str) -> List[float]:
        """Generate embedding for text."""
        await self.initialize()

        if self._model is not None:
            try:
                embedding = self._model.encode(text, convert_to_numpy=True)
                return embedding.tolist()
            except Exception as e:
                logger.error(f"Embedding failed: {e}")

        # Fallback to hash-based embedding
        return self._hash_embedding(text)

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        await self.initialize()

        if self._model is not None:
            try:
                embeddings = self._model.encode(texts, convert_to_numpy=True)
                return embeddings.tolist()
            except Exception as e:
                logger.error(f"Batch embedding failed: {e}")

        # Fallback
        return [self._hash_embedding(text) for text in texts]

    def _hash_embedding(self, text: str) -> List[float]:
        """Fallback hash-based embedding."""
        hash_bytes = hashlib.sha256(text.encode("utf-8")).digest()
        vec = np.frombuffer(hash_bytes, dtype=np.uint8)[:self.dim].astype("float32")
        norm = np.linalg.norm(vec) or 1.0
        return (vec / norm).tolist()

    @staticmethod
    def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        try:
            a = np.array(vec1)
            b = np.array(vec2)

            dot_product = np.dot(a, b)
            norm_a = np.linalg.norm(a)
            norm_b = np.linalg.norm(b)

            if norm_a == 0 or norm_b == 0:
                return 0.0

            return float(dot_product / (norm_a * norm_b))
        except Exception as e:
            logger.error(f"Cosine similarity calculation failed: {e}")
            return 0.0


# ===================================
# MEMORY INDEX
# ===================================

class MemoryIndex:
    """
    In-memory index for fast memory retrieval.

    Uses hierarchical indexing by type, tenant, and user for efficient filtering.
    """

    def __init__(self):
        """Initialize memory index."""
        # Hierarchical index: type -> tenant -> user -> memory_id -> entry
        self.index: Dict[str, Dict[str, Dict[str, Dict[str, MemoryEntry]]]] = {}

        # Reverse indexes for fast lookups
        self.id_to_entry: Dict[str, MemoryEntry] = {}

        # Temporal index for efficient time-based queries
        self.temporal_index: List[Tuple[datetime, str]] = []  # (timestamp, memory_id)

        # Statistics
        self.stats = {
            "total_memories": 0,
            "by_type": {mt.value: 0 for mt in MemoryType},
            "by_status": {ms.value: 0 for ms in MemoryStatus},
        }

    def add(self, memory: MemoryEntry):
        """Add memory to index."""
        memory_type = memory.memory_type.value
        tenant_id = memory.metadata.tenant_id if memory.metadata else "default"
        user_id = memory.metadata.user_id if memory.metadata else "default"

        # Create hierarchy if needed
        if memory_type not in self.index:
            self.index[memory_type] = {}
        if tenant_id not in self.index[memory_type]:
            self.index[memory_type][tenant_id] = {}
        if user_id not in self.index[memory_type][tenant_id]:
            self.index[memory_type][tenant_id][user_id] = {}

        # Add to indexes
        self.index[memory_type][tenant_id][user_id][memory.id] = memory
        self.id_to_entry[memory.id] = memory
        self.temporal_index.append((memory.timestamp, memory.id))

        # Update stats
        self.stats["total_memories"] += 1
        self.stats["by_type"][memory_type] += 1
        self.stats["by_status"][memory.status.value] += 1

    def get(self, memory_id: str) -> Optional[MemoryEntry]:
        """Get memory by ID."""
        return self.id_to_entry.get(memory_id)

    def search(
        self,
        memory_types: Optional[List[MemoryType]] = None,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
        status: Optional[MemoryStatus] = None,
        temporal_window_hours: Optional[int] = None,
    ) -> List[MemoryEntry]:
        """Search index with filters."""
        results = []

        # Filter by type
        types_to_search = (
            [mt.value for mt in memory_types]
            if memory_types
            else list(self.index.keys())
        )

        for mem_type in types_to_search:
            if mem_type not in self.index:
                continue

            # Filter by tenant
            tenants_to_search = (
                [tenant_id] if tenant_id
                else list(self.index[mem_type].keys())
            )

            for tenant in tenants_to_search:
                if tenant not in self.index[mem_type]:
                    continue

                # Filter by user
                users_to_search = (
                    [user_id] if user_id
                    else list(self.index[mem_type][tenant].keys())
                )

                for user in users_to_search:
                    if user not in self.index[mem_type][tenant]:
                        continue

                    for memory in self.index[mem_type][tenant][user].values():
                        # Filter by status
                        if status and memory.status != status:
                            continue

                        # Filter by temporal window
                        if temporal_window_hours:
                            age_hours = (
                                datetime.utcnow() - memory.timestamp
                            ).total_seconds() / 3600.0
                            if age_hours > temporal_window_hours:
                                continue

                        results.append(memory)

        return results

    def remove(self, memory_id: str):
        """Remove memory from index."""
        memory = self.id_to_entry.get(memory_id)
        if not memory:
            return

        # Remove from hierarchical index
        memory_type = memory.memory_type.value
        tenant_id = memory.metadata.tenant_id if memory.metadata else "default"
        user_id = memory.metadata.user_id if memory.metadata else "default"

        try:
            del self.index[memory_type][tenant_id][user_id][memory_id]
            del self.id_to_entry[memory_id]

            # Update stats
            self.stats["total_memories"] -= 1
            self.stats["by_type"][memory_type] -= 1
            self.stats["by_status"][memory.status.value] -= 1
        except KeyError:
            pass

    def get_stats(self) -> Dict[str, Any]:
        """Get index statistics."""
        return self.stats.copy()


# Factory function
def create_memory_entry(
    content: str,
    memory_type: MemoryType,
    tenant_id: str,
    user_id: str,
    importance_score: float = 5.0,
    **kwargs
) -> MemoryEntry:
    """Factory function to create memory entries with proper defaults."""
    entry_id = kwargs.get("id", str(uuid.uuid4()))

    metadata = MemoryMetadata(
        tenant_id=tenant_id,
        user_id=user_id,
        conversation_id=kwargs.get("conversation_id"),
        session_id=kwargs.get("session_id"),
        source=kwargs.get("source", "user"),
        tags=kwargs.get("tags", []),
        context=kwargs.get("context", {}),
    )

    decay_lambda = DecayFunction.get_decay_lambda(memory_type)

    return MemoryEntry(
        id=entry_id,
        memory_type=memory_type,
        content=content,
        metadata=metadata,
        importance_score=importance_score,
        decay_lambda=decay_lambda,
        **{k: v for k, v in kwargs.items() if k not in [
            "id", "conversation_id", "session_id", "source", "tags", "context"
        ]}
    )
