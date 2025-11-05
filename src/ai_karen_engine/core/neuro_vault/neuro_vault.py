"""
NeuroVault - Production Memory System

Main implementation of the tri-partite memory system with:
- Intelligent hybrid retrieval (semantic + temporal)
- Memory consolidation and reflection
- Security and RBAC enforcement
- Comprehensive observability
- Integration with storage backends
"""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple

from ai_karen_engine.core.neuro_vault.neuro_vault_core import (
    DecayFunction,
    EmbeddingManager,
    ImportanceLevel,
    MemoryEntry,
    MemoryIndex,
    MemoryMetadata,
    MemoryStatus,
    MemoryType,
    RetrievalRequest,
    RetrievalResult,
    create_memory_entry,
)

logger = logging.getLogger(__name__)


# ===================================
# SECURITY AND RBAC
# ===================================

class MemoryRBAC:
    """Role-Based Access Control for memory operations."""

    # Permission levels
    PERMISSIONS = {
        "admin": ["read", "write", "delete", "admin"],
        "user": ["read", "write"],
        "viewer": ["read"],
        "system": ["read", "write", "delete", "admin", "system"],
    }

    @classmethod
    def check_permission(
        cls,
        user_roles: List[str],
        required_permission: str,
    ) -> bool:
        """Check if user has required permission."""
        for role in user_roles:
            if required_permission in cls.PERMISSIONS.get(role, []):
                return True
        return False

    @classmethod
    def enforce_tenant_isolation(
        cls,
        memory: MemoryEntry,
        requesting_tenant_id: str,
    ) -> bool:
        """Ensure tenant can only access their own memories."""
        if not memory.metadata:
            return False

        return memory.metadata.tenant_id == requesting_tenant_id

    @classmethod
    def can_access_memory(
        cls,
        memory: MemoryEntry,
        tenant_id: str,
        user_id: str,
        user_roles: List[str],
    ) -> bool:
        """Comprehensive access check."""
        # Check tenant isolation
        if not cls.enforce_tenant_isolation(memory, tenant_id):
            # Allow system role to cross tenants
            if not cls.check_permission(user_roles, "system"):
                return False

        # Check read permission
        return cls.check_permission(user_roles, "read")


# ===================================
# PII SCRUBBING
# ===================================

class PIIScrubber:
    """Privacy controls for sensitive information."""

    SENSITIVE_PATTERNS = {
        "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        "phone": r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
        "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
        "credit_card": r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b",
    }

    @classmethod
    def scrub(
        cls,
        text: str,
        policies: Optional[Dict[str, bool]] = None,
    ) -> str:
        """Scrub PII from text based on policies."""
        import re

        if policies is None:
            policies = {k: True for k in cls.SENSITIVE_PATTERNS.keys()}

        scrubbed = text
        for pii_type, pattern in cls.SENSITIVE_PATTERNS.items():
            if policies.get(pii_type, False):
                scrubbed = re.sub(pattern, f"[{pii_type.upper()}_REDACTED]", scrubbed)

        return scrubbed

    @classmethod
    def detect_pii(cls, text: str) -> Dict[str, int]:
        """Detect PII patterns in text."""
        import re

        detections = {}
        for pii_type, pattern in cls.SENSITIVE_PATTERNS.items():
            matches = re.findall(pattern, text)
            if matches:
                detections[pii_type] = len(matches)

        return detections


# ===================================
# METRICS
# ===================================

class MemoryMetrics:
    """Performance and observability metrics."""

    def __init__(self):
        """Initialize metrics."""
        self.metrics = {
            "retrieval_count": 0,
            "retrieval_latency_ms": [],
            "cache_hits": 0,
            "cache_misses": 0,
            "storage_count": 0,
            "consolidation_count": 0,
            "decay_operations": 0,
            "rbac_denials": 0,
        }

        # Try to use Prometheus if available
        try:
            from prometheus_client import Counter, Histogram

            self.retrieval_counter = Counter(
                "neurovault_retrieval_total",
                "Total memory retrievals",
                ["memory_type", "status"],
            )
            self.retrieval_latency = Histogram(
                "neurovault_retrieval_latency_seconds",
                "Memory retrieval latency",
                ["memory_type"],
            )
            self.storage_counter = Counter(
                "neurovault_storage_total",
                "Total memory storage operations",
                ["memory_type"],
            )
            self.prometheus_enabled = True
        except ImportError:
            self.prometheus_enabled = False

    def record_retrieval(
        self,
        memory_type: Optional[MemoryType],
        latency_ms: float,
        status: str = "success",
    ):
        """Record retrieval metrics."""
        self.metrics["retrieval_count"] += 1
        self.metrics["retrieval_latency_ms"].append(latency_ms)

        if self.prometheus_enabled:
            type_label = memory_type.value if memory_type else "mixed"
            self.retrieval_counter.labels(
                memory_type=type_label, status=status
            ).inc()
            self.retrieval_latency.labels(memory_type=type_label).observe(
                latency_ms / 1000.0
            )

    def record_cache_hit(self, hit: bool):
        """Record cache hit/miss."""
        if hit:
            self.metrics["cache_hits"] += 1
        else:
            self.metrics["cache_misses"] += 1

    def record_storage(self, memory_type: MemoryType):
        """Record storage operation."""
        self.metrics["storage_count"] += 1

        if self.prometheus_enabled:
            self.storage_counter.labels(memory_type=memory_type.value).inc()

    def get_stats(self) -> Dict[str, Any]:
        """Get metrics statistics."""
        latencies = self.metrics["retrieval_latency_ms"]

        stats = {
            "retrieval_count": self.metrics["retrieval_count"],
            "storage_count": self.metrics["storage_count"],
            "cache_hit_rate": (
                self.metrics["cache_hits"] /
                (self.metrics["cache_hits"] + self.metrics["cache_misses"])
                if (self.metrics["cache_hits"] + self.metrics["cache_misses"]) > 0
                else 0.0
            ),
            "consolidation_count": self.metrics["consolidation_count"],
            "rbac_denials": self.metrics["rbac_denials"],
        }

        if latencies:
            stats["latency_p50_ms"] = sorted(latencies)[len(latencies) // 2]
            stats["latency_p95_ms"] = sorted(latencies)[int(len(latencies) * 0.95)]
            stats["latency_p99_ms"] = sorted(latencies)[int(len(latencies) * 0.99)]
            stats["latency_avg_ms"] = sum(latencies) / len(latencies)

        return stats


# ===================================
# MAIN NEUROVAULT CLASS
# ===================================

class NeuroVault:
    """
    Comprehensive tri-partite memory system.

    Features:
    - Episodic, Semantic, and Procedural memory types
    - Intelligent hybrid retrieval (semantic + temporal + importance)
    - Memory consolidation and reflection
    - Decay and lifecycle management
    - RBAC and tenant isolation
    - PII scrubbing
    - Comprehensive metrics
    """

    def __init__(
        self,
        embedding_manager: Optional[EmbeddingManager] = None,
        enable_metrics: bool = True,
        enable_rbac: bool = True,
        enable_pii_scrubbing: bool = True,
    ):
        """Initialize NeuroVault."""
        self.embedding_manager = embedding_manager or EmbeddingManager()
        self.index = MemoryIndex()
        self.metrics = MemoryMetrics() if enable_metrics else None

        self.enable_rbac = enable_rbac
        self.enable_pii_scrubbing = enable_pii_scrubbing

        # Configuration
        self.config = {
            "consolidation_threshold_hours": 24,
            "decay_check_interval_hours": 6,
            "retention_days": {
                MemoryType.EPISODIC: 30,
                MemoryType.SEMANTIC: 365,
                MemoryType.PROCEDURAL: 180,
            },
        }

        # Cache for recent retrievals
        self._retrieval_cache: Dict[str, Tuple[RetrievalResult, float]] = {}
        self._cache_ttl = 300  # 5 minutes

        logger.info("NeuroVault initialized with tri-partite memory architecture")

    async def store_memory(
        self,
        content: str,
        memory_type: MemoryType,
        tenant_id: str,
        user_id: str,
        importance_score: float = 5.0,
        metadata: Optional[Dict[str, Any]] = None,
        user_roles: Optional[List[str]] = None,
        **kwargs
    ) -> Optional[MemoryEntry]:
        """
        Store a new memory.

        Args:
            content: Memory content
            memory_type: Type of memory (episodic, semantic, procedural)
            tenant_id: Tenant identifier
            user_id: User identifier
            importance_score: Importance (1-10)
            metadata: Additional metadata
            user_roles: User roles for RBAC
            **kwargs: Additional memory attributes

        Returns:
            Stored memory entry or None if denied
        """
        # RBAC check
        if self.enable_rbac and user_roles:
            if not MemoryRBAC.check_permission(user_roles, "write"):
                logger.warning(f"RBAC denied: User {user_id} lacks write permission")
                if self.metrics:
                    self.metrics.metrics["rbac_denials"] += 1
                return None

        # PII scrubbing
        scrubbed_content = content
        if self.enable_pii_scrubbing:
            pii_detected = PIIScrubber.detect_pii(content)
            if pii_detected:
                logger.info(f"PII detected in memory: {pii_detected}")
                scrubbed_content = PIIScrubber.scrub(content)

        # Generate embedding
        embedding = await self.embedding_manager.embed(scrubbed_content)

        # Create memory entry
        memory = create_memory_entry(
            content=scrubbed_content,
            memory_type=memory_type,
            tenant_id=tenant_id,
            user_id=user_id,
            importance_score=importance_score,
            embedding=embedding,
            **{k: v for k, v in (metadata or {}).items()},
            **kwargs
        )

        # Add to index
        self.index.add(memory)

        # Record metrics
        if self.metrics:
            self.metrics.record_storage(memory_type)

        logger.debug(f"Stored {memory_type.value} memory {memory.id}")

        return memory

    async def retrieve_memories(
        self,
        request: RetrievalRequest,
    ) -> RetrievalResult:
        """
        Retrieve memories using hybrid scoring.

        Implements intelligent retrieval with:
        - Semantic similarity (cosine)
        - Temporal decay
        - Importance weighting
        - Access frequency bonus
        - RBAC enforcement
        - Tenant isolation

        Formula: R = (S * I * D) + A
        Where:
          S = Semantic score
          I = Importance factor
          D = Decay factor
          A = Access bonus
        """
        start_time = time.time()

        # Check cache
        cache_key = self._generate_cache_key(request)
        cached = self._get_from_cache(cache_key)
        if cached:
            if self.metrics:
                self.metrics.record_cache_hit(True)
            return cached

        if self.metrics:
            self.metrics.record_cache_hit(False)

        # Generate query embedding if not provided
        query_embedding = request.query_embedding
        if not query_embedding:
            query_embedding = await self.embedding_manager.embed(request.query)

        # Search index with filters
        candidates = self.index.search(
            memory_types=request.memory_types,
            tenant_id=request.tenant_id if request.require_rbac else None,
            user_id=request.user_id if request.require_rbac else None,
            status=MemoryStatus.ACTIVE if not request.include_archived else None,
            temporal_window_hours=request.temporal_window_hours,
        )

        # Calculate relevance scores
        scored_memories: List[Tuple[float, MemoryEntry]] = []

        for memory in candidates:
            # RBAC check
            if request.require_rbac and self.enable_rbac:
                if not MemoryRBAC.can_access_memory(
                    memory,
                    request.tenant_id,
                    request.user_id,
                    ["user"],  # Default to user role
                ):
                    continue

            # Calculate semantic similarity
            if memory.embedding:
                semantic_score = EmbeddingManager.cosine_similarity(
                    query_embedding, memory.embedding
                )
            else:
                semantic_score = 0.5  # Default for missing embeddings

            # Calculate composite relevance
            relevance = memory.calculate_relevance_score(
                semantic_score=semantic_score
            )

            if relevance >= request.min_relevance:
                scored_memories.append((relevance, memory))

        # Sort by score descending
        scored_memories.sort(key=lambda x: x[0], reverse=True)

        # Take top K
        top_results = scored_memories[:request.top_k]
        memories = [m for _, m in top_results]
        scores = [s for s, _ in top_results]

        # Update access metrics on memories
        for memory in memories:
            memory.last_accessed = datetime.utcnow()
            memory.access_count += 1

        # Build result
        retrieval_time_ms = (time.time() - start_time) * 1000

        result = RetrievalResult(
            memories=memories,
            scores=scores,
            total_matches=len(candidates),
            retrieval_time_ms=retrieval_time_ms,
            cache_hit=False,
        )

        # Cache result
        self._cache_result(cache_key, result)

        # Record metrics
        if self.metrics:
            primary_type = request.memory_types[0] if request.memory_types else None
            self.metrics.record_retrieval(primary_type, retrieval_time_ms)

        logger.debug(
            f"Retrieved {len(memories)} memories in {retrieval_time_ms:.1f}ms "
            f"(total matches: {len(candidates)})"
        )

        return result

    async def consolidate_memories(
        self,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> int:
        """
        Consolidate episodic memories to semantic memories.

        This is the "reflection" process where repeated episodic memories
        are promoted to stable semantic facts.

        Returns:
            Number of memories consolidated
        """
        threshold_hours = self.config["consolidation_threshold_hours"]

        # Find consolidation candidates
        candidates = self.index.search(
            memory_types=[MemoryType.EPISODIC],
            tenant_id=tenant_id,
            user_id=user_id,
            status=MemoryStatus.ACTIVE,
        )

        consolidated_count = 0

        for memory in candidates:
            if memory.should_consolidate(threshold_hours):
                # Create semantic memory from episodic
                semantic_memory = await self.store_memory(
                    content=memory.content,
                    memory_type=MemoryType.SEMANTIC,
                    tenant_id=memory.metadata.tenant_id,
                    user_id=memory.metadata.user_id,
                    importance_score=memory.importance_score,
                    parent_id=memory.id,
                    metadata={
                        "consolidated_from": memory.id,
                        "consolidation_timestamp": datetime.utcnow().isoformat(),
                    },
                )

                if semantic_memory:
                    # Mark original as consolidated
                    memory.status = MemoryStatus.CONSOLIDATING
                    consolidated_count += 1

        if self.metrics and consolidated_count > 0:
            self.metrics.metrics["consolidation_count"] += consolidated_count

        logger.info(f"Consolidated {consolidated_count} episodic memories")

        return consolidated_count

    async def apply_decay(self) -> int:
        """
        Apply decay function and archive low-relevance memories.

        Returns:
            Number of memories archived
        """
        current_time = datetime.utcnow()
        archived_count = 0

        # Check all active memories
        for memory in self.index.search(status=MemoryStatus.ACTIVE):
            # Calculate current relevance
            relevance = memory.calculate_relevance_score(current_time=current_time)

            # Archive if below threshold
            if relevance < 0.1:  # 10% threshold
                memory.status = MemoryStatus.ARCHIVED
                archived_count += 1

        if self.metrics:
            self.metrics.metrics["decay_operations"] += archived_count

        logger.info(f"Archived {archived_count} low-relevance memories")

        return archived_count

    async def purge_expired(self) -> int:
        """
        Purge expired memories based on retention policies.

        Returns:
            Number of memories purged
        """
        current_time = datetime.utcnow()
        purged_count = 0

        for memory in self.index.search():
            # Check retention period
            retention_days = self.config["retention_days"].get(
                memory.memory_type, 365
            )
            age_days = (current_time - memory.timestamp).days

            if age_days > retention_days:
                # Check if already archived
                if memory.status == MemoryStatus.ARCHIVED:
                    self.index.remove(memory.id)
                    purged_count += 1

        logger.info(f"Purged {purged_count} expired memories")

        return purged_count

    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics."""
        stats = {
            "index_stats": self.index.get_stats(),
            "cache_size": len(self._retrieval_cache),
        }

        if self.metrics:
            stats["metrics"] = self.metrics.get_stats()

        return stats

    def _generate_cache_key(self, request: RetrievalRequest) -> str:
        """Generate cache key for request."""
        import hashlib
        import json

        key_data = {
            "query": request.query,
            "tenant_id": request.tenant_id,
            "user_id": request.user_id,
            "memory_types": [mt.value for mt in request.memory_types] if request.memory_types else None,
            "top_k": request.top_k,
        }

        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()

    def _get_from_cache(self, cache_key: str) -> Optional[RetrievalResult]:
        """Get result from cache if valid."""
        if cache_key in self._retrieval_cache:
            result, cached_at = self._retrieval_cache[cache_key]
            if time.time() - cached_at < self._cache_ttl:
                result.cache_hit = True
                return result
            else:
                # Expired
                del self._retrieval_cache[cache_key]

        return None

    def _cache_result(self, cache_key: str, result: RetrievalResult):
        """Cache retrieval result."""
        self._retrieval_cache[cache_key] = (result, time.time())

        # Limit cache size
        if len(self._retrieval_cache) > 1000:
            # Remove oldest 20%
            sorted_keys = sorted(
                self._retrieval_cache.keys(),
                key=lambda k: self._retrieval_cache[k][1]
            )
            for key in sorted_keys[:200]:
                del self._retrieval_cache[key]


# ===================================
# FACTORY FUNCTION
# ===================================

_neurovault_instance = None

def get_neurovault() -> NeuroVault:
    """Get singleton NeuroVault instance."""
    global _neurovault_instance
    if _neurovault_instance is None:
        _neurovault_instance = NeuroVault()
    return _neurovault_instance
