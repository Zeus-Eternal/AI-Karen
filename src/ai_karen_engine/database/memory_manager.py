"""Utilities for storing and querying memory entries.

This module wraps database access and optional Milvus vector operations. When
the Milvus client is unavailable the manager degrades gracefully, skipping
vector actions and falling back to metadata-only behaviour.
"""

import json
import logging
import os
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, field

import numpy as np
from sqlalchemy import text, select, delete

from ai_karen_engine.database.client import MultiTenantPostgresClient
from ai_karen_engine.database.models import TenantMemoryItem
from ai_karen_engine.core.milvus_client import MilvusClient
from ai_karen_engine.core.embedding_manager import EmbeddingManager

logger = logging.getLogger(__name__)


@dataclass
class MemoryItem:
    """Represents a memory item with all associated data."""

    id: str
    content: str
    embedding: Optional[np.ndarray] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    scope: Optional[str] = None
    kind: Optional[str] = None
    timestamp: float = field(default_factory=time.time)
    similarity_score: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "content": self.content,
            "metadata": self.metadata,
            "scope": self.scope,
            "kind": self.kind,
            "timestamp": self.timestamp,
            "similarity_score": self.similarity_score,
        }

# Backwards compatibility alias
MemoryEntry = MemoryItem


@dataclass
class MemoryQuery:
    """Represents a memory query with all parameters."""

    text: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    conversation_id: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    scope: Optional[str] = None
    kind: Optional[str] = None
    metadata_filter: Dict[str, Any] = field(default_factory=dict)
    time_range: Optional[Tuple[datetime, datetime]] = None
    top_k: int = 10
    similarity_threshold: float = 0.7
    include_embeddings: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging and caching."""
        return {
            "text": self.text[:100] + "..." if len(self.text) > 100 else self.text,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "conversation_id": self.conversation_id,
            "tags": self.tags,
            "scope": self.scope,
            "kind": self.kind,
            "metadata_filter": self.metadata_filter,
            "time_range": (
                [t.isoformat() for t in self.time_range] if self.time_range else None
            ),
            "top_k": self.top_k,
            "similarity_threshold": self.similarity_threshold,
        }


class MemoryManager:
    """Production-grade memory management system."""

    def __init__(
        self,
        db_client: MultiTenantPostgresClient,
        milvus_client: Optional[MilvusClient] = None,
        embedding_manager: EmbeddingManager,
        redis_client: Optional[Any] = None,
        elasticsearch_client: Optional[Any] = None,
    ):
        """Initialize memory manager.

        Args:
            db_client: Database client for metadata
            milvus_client: Vector database client
            embedding_manager: Embedding generation manager
            redis_client: Redis client for caching
            elasticsearch_client: Elasticsearch client for full-text search
        """
        self.db_client = db_client
        self.milvus_client = milvus_client
        self.embedding_manager = embedding_manager
        self.redis_client = redis_client
        self.elasticsearch_client = elasticsearch_client

        # Configuration
        self.default_ttl_hours = 24 * 7  # 1 week
        self.cache_ttl_seconds = 300  # 5 minutes
        self.surprise_threshold = float(
            os.getenv("KARI_MEMORY_SURPRISE_THRESHOLD", "0.85")
        )
        self.disable_surprise_check = (
            os.getenv("KARI_DISABLE_MEMORY_SURPRISE_FILTER", "false").lower() == "true"
        )
        self.recency_alpha = 0.05  # Exponential decay factor for recency weighting

        # Performance tracking
        self.metrics = {
            "queries_total": 0,
            "queries_cached": 0,
            "embeddings_generated": 0,
            "memories_stored": 0,
            "memories_retrieved": 0,
            "avg_query_time": 0.0,
            "avg_embedding_time": 0.0,
        }

    async def store_memory(
        self,
        tenant_id: Union[str, uuid.UUID],
        content: str,
        scope: str,
        kind: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Store a memory item with vector embedding.

        Args:
            tenant_id: Tenant ID
            content: Memory content
            scope: Logical scope for the memory
            kind: Kind/type of memory
            metadata: Additional metadata

        Returns:
            Memory item ID
        """
        start_time = time.time()

        try:
            # Generate embedding
            embedding_start = time.time()
            embedding_raw = await self.embedding_manager.get_embedding(content)
            # Ensure it's a numpy array for .tolist() compatibility
            import numpy as np

            embedding = (
                np.array(embedding_raw)
                if not isinstance(embedding_raw, np.ndarray)
                else embedding_raw
            )
            embedding_time = time.time() - embedding_start

            # Check for surprise (novelty)
            is_surprising = await self._check_surprise(
                tenant_id, embedding, scope, kind
            )
            if not is_surprising:
                logger.debug(
                    f"Content not surprising enough, skipping storage: {content[:50]}..."
                )
                return None

            # Create memory entry
            memory_id = str(uuid.uuid4())
            memory_entry = MemoryItem(
                id=memory_id,
                content=content,
                embedding=embedding,
                metadata=metadata or {},
                scope=scope,
                kind=kind,
                timestamp=time.time(),
            )

            # Store in vector database
            collection_name = self._get_collection_name(tenant_id)
            vector_metadata = {
                "memory_id": memory_id,
                "scope": scope,
                "kind": kind,
                "timestamp": memory_entry.timestamp,
            }

            # Add additional metadata
            if metadata:
                vector_metadata.update(metadata)

            if self.milvus_client:
                await self.milvus_client.insert(
                    collection_name=collection_name,
                    vectors=[embedding.tolist()],
                    metadata=[vector_metadata],
                )
            else:
                logger.warning("Milvus client unavailable - skipping vector insert")

            # Store metadata in Postgres
            async with self.db_client.get_async_session() as session:
                memory_record = TenantMemoryItem(
                    id=uuid.UUID(memory_id),
                    scope=scope,
                    kind=kind,
                    content=content,
                    embedding=embedding.tolist(),
                    metadata=metadata or {},
                    created_at=datetime.utcnow(),
                )

                session.add(memory_record)
                await session.commit()

            # Store in Elasticsearch for full-text search
            if self.elasticsearch_client:
                await self._store_in_elasticsearch(tenant_id, memory_entry)

            # Cache recent memory
            if self.redis_client:
                await self._cache_memory(tenant_id, memory_entry)

            # Update metrics
            self.metrics["memories_stored"] += 1
            self.metrics["embeddings_generated"] += 1
            self.metrics["avg_embedding_time"] = (
                self.metrics["avg_embedding_time"] * 0.9 + embedding_time * 0.1
            )

            total_time = time.time() - start_time
            logger.info(
                f"Stored memory {memory_id} for tenant {tenant_id} in {total_time:.3f}s"
            )

            return memory_id

        except Exception as e:
            logger.error(f"Failed to store memory for tenant {tenant_id}: {e}")
            raise

    async def query_memories(
        self, tenant_id: Union[str, uuid.UUID], query: MemoryQuery
    ) -> List[MemoryEntry]:
        """Query memories using hybrid search (vector + metadata + full-text).

        Args:
            tenant_id: Tenant ID
            query: Memory query parameters

        Returns:
            List of matching memory entries
        """
        start_time = time.time()
        self.metrics["queries_total"] += 1

        try:
            # Check cache first
            cache_key = self._get_cache_key(tenant_id, query)
            if self.redis_client:
                cached_result = await self._get_cached_query(cache_key)
                if cached_result:
                    self.metrics["queries_cached"] += 1
                    return cached_result

            # Generate query embedding
            query_embedding_raw = await self.embedding_manager.get_embedding(query.text)
            # Ensure it's a numpy array for .tolist() compatibility
            import numpy as np

            query_embedding = (
                np.array(query_embedding_raw)
                if not isinstance(query_embedding_raw, np.ndarray)
                else query_embedding_raw
            )

            # Search vector database
            collection_name = self._get_collection_name(tenant_id)

            # Build metadata filter
            metadata_filter = self._build_metadata_filter(query)

            if not self.milvus_client:
                logger.warning("Milvus client unavailable - returning empty results")
                return []

            vector_results = await self.milvus_client.search(
                collection_name=collection_name,
                query_vectors=[query_embedding.tolist()],
                top_k=query.top_k * 2,  # Get more results for filtering
                metadata_filter=metadata_filter,
            )

            # Get memory IDs from vector results
            memory_ids = []
            similarity_scores = {}

            for result in vector_results[0]:  # First query results
                if result.distance >= query.similarity_threshold:
                    memory_id = result.entity.get("memory_id")
                    if memory_id:
                        memory_ids.append(memory_id)
                        similarity_scores[memory_id] = result.distance

            if not memory_ids:
                return []

            # Get full memory entries from Postgres
            memories = await self._get_memories_from_postgres(
                tenant_id, memory_ids, query.include_embeddings
            )

            # Apply additional filters
            filtered_memories = self._apply_filters(memories, query)

            # Apply recency weighting and sort
            scored_memories = self._apply_recency_weighting(
                filtered_memories, similarity_scores
            )

            # Limit results
            final_memories = scored_memories[: query.top_k]

            # Cache results
            if self.redis_client:
                await self._cache_query_result(cache_key, final_memories)

            # Update metrics
            self.metrics["memories_retrieved"] += len(final_memories)
            query_time = time.time() - start_time
            self.metrics["avg_query_time"] = (
                self.metrics["avg_query_time"] * 0.9 + query_time * 0.1
            )

            logger.info(
                f"Retrieved {len(final_memories)} memories for tenant {tenant_id} in {query_time:.3f}s"
            )

            return final_memories

        except Exception as e:
            logger.error(f"Failed to query memories for tenant {tenant_id}: {e}")
            raise

    async def delete_memory(
        self, tenant_id: Union[str, uuid.UUID], memory_id: str
    ) -> bool:
        """Delete a memory entry.

        Args:
            tenant_id: Tenant ID
            memory_id: Memory entry ID

        Returns:
            True if successful
        """
        try:
            # Delete from vector database
            collection_name = self._get_collection_name(tenant_id)
            if self.milvus_client:
                await self.milvus_client.delete(
                    collection_name=collection_name,
                    filter_expr=f"memory_id == '{memory_id}'",
                )
            else:
                logger.warning("Milvus client unavailable - skipping vector delete")

            # Delete from Postgres
            async with self.db_client.get_async_session() as session:
                await session.execute(
                    delete(TenantMemoryItem).where(
                        TenantMemoryItem.id == uuid.UUID(memory_id)
                    )
                )
                await session.commit()

            # Delete from Elasticsearch
            if self.elasticsearch_client:
                await self._delete_from_elasticsearch(tenant_id, memory_id)

            # Clear from cache
            if self.redis_client:
                await self._clear_memory_cache(tenant_id, memory_id)

            logger.info(f"Deleted memory {memory_id} for tenant {tenant_id}")
            return True

        except Exception as e:
            logger.error(
                f"Failed to delete memory {memory_id} for tenant {tenant_id}: {e}"
            )
            return False

    async def prune_expired_memories(self, tenant_id: Union[str, uuid.UUID]) -> int:
        """Placeholder for API compatibility; memory_items have no TTL."""
        logger.info("prune_expired_memories called but not applicable for memory_items")
        return 0

    async def get_memory_stats(
        self, tenant_id: Union[str, uuid.UUID]
    ) -> Dict[str, Any]:
        """Get memory statistics for a tenant.

        Args:
            tenant_id: Tenant ID

        Returns:
            Memory statistics
        """
        try:
            async with self.db_client.get_async_session() as session:
                # Total memories
                total_result = await session.execute(
                    select(TenantMemoryItem).where(TenantMemoryItem.id.isnot(None))
                )
                total_count = len(total_result.fetchall())

                # Memories by scope and kind
                scope_result = await session.execute(
                    text(
                        f"""
                        SELECT scope, kind, COUNT(*) as count
                        FROM {self.db_client.get_tenant_schema_name(tenant_id)}.memory_items
                        GROUP BY scope, kind
                    """
                    )
                )
                scope_counts = {
                    (row[0], row[1]): row[2] for row in scope_result.fetchall()
                }

                # Recent activity (last 24 hours)
                recent_cutoff = datetime.utcnow() - timedelta(hours=24)
                recent_result = await session.execute(
                    select(TenantMemoryItem).where(
                        TenantMemoryItem.created_at > recent_cutoff
                    )
                )
                recent_count = len(recent_result.fetchall())

                return {
                    "total_memories": total_count,
                    "memories_by_scope_kind": scope_counts,
                    "recent_memories_24h": recent_count,
                    "collection_name": self._get_collection_name(tenant_id),
                    "metrics": self.metrics.copy(),
                }

        except Exception as e:
            logger.error(f"Failed to get memory stats for tenant {tenant_id}: {e}")
            return {"error": str(e)}

    def _get_collection_name(self, tenant_id: Union[str, uuid.UUID]) -> str:
        """Get Milvus collection name for tenant."""
        return f"tenant_{str(tenant_id).replace('-', '_')}_memories"

    async def _check_surprise(
        self,
        tenant_id: Union[str, uuid.UUID],
        embedding: np.ndarray,
        scope: Optional[str] = None,
        kind: Optional[str] = None,
    ) -> bool:
        """Check if content is surprising enough to store."""
        if self.disable_surprise_check:
            return True
        try:
            collection_name = self._get_collection_name(tenant_id)

            # Search for similar content
            metadata = {}
            if scope:
                metadata["scope"] = scope
            if kind:
                metadata["kind"] = kind
            if not self.milvus_client:
                logger.warning("Milvus client unavailable - assuming content is surprising")
                return True

            results = await self.milvus_client.search(
                collection_name=collection_name,
                query_vectors=[embedding.tolist()],
                top_k=1,
                metadata_filter=metadata or None,
            )

            if not results or not results[0]:
                return True  # No similar content, definitely surprising

            # Check similarity of most similar result
            max_similarity = results[0][0].distance if results[0] else 0
            return max_similarity < self.surprise_threshold

        except Exception as e:
            logger.warning(f"Failed to check surprise, assuming surprising: {e}")
            return True

    def _build_metadata_filter(self, query: MemoryQuery) -> Optional[Dict[str, Any]]:
        """Build metadata filter for vector search."""
        metadata_filter: Dict[str, Any] = dict(query.metadata_filter)

        if query.user_id:
            metadata_filter["user_id"] = query.user_id
        if query.session_id:
            metadata_filter["session_id"] = query.session_id
        if query.conversation_id:
            metadata_filter["conversation_id"] = query.conversation_id
        if query.tags:
            metadata_filter["tags"] = query.tags
        if query.scope:
            metadata_filter["scope"] = query.scope
        if query.kind:
            metadata_filter["kind"] = query.kind

        # For the in-memory MilvusClient, we'll use simple key-value matching

        return metadata_filter if metadata_filter else None

    async def _get_memories_from_postgres(
        self,
        tenant_id: Union[str, uuid.UUID],
        memory_ids: List[str],
        include_embeddings: bool = False,
    ) -> List[MemoryItem]:
        """Get full memory entries from Postgres."""
        try:
            async with self.db_client.get_async_session() as session:
                result = await session.execute(
                    select(TenantMemoryItem).where(
                        TenantMemoryItem.id.in_(memory_ids)
                    )
                )

                memories: List[MemoryItem] = []
                for row in result.fetchall():
                    memory = MemoryItem(
                        id=str(row.id),
                        content=row.content,
                        metadata=row.metadata or {},
                        scope=row.scope,
                        kind=row.kind,
                        timestamp=row.created_at.timestamp() if row.created_at else time.time(),
                    )

                    if include_embeddings and row.embedding is not None:
                        memory.embedding = np.array(row.embedding)

                    memories.append(memory)

                return memories

        except Exception as e:
            logger.error(f"Failed to get memories from Postgres: {e}")
            return []

    def _apply_filters(
        self, memories: List[MemoryEntry], query: MemoryQuery
    ) -> List[MemoryEntry]:
        """Apply additional filters to memory results."""
        filtered = memories

        # Filter by explicit metadata filter
        if query.metadata_filter:
            filtered = [
                m
                for m in filtered
                if all(m.metadata.get(k) == v for k, v in query.metadata_filter.items())
            ]

        # Filter by user/session/conversation identifiers
        if query.user_id:
            filtered = [m for m in filtered if m.metadata.get("user_id") == query.user_id]
        if query.session_id:
            filtered = [m for m in filtered if m.metadata.get("session_id") == query.session_id]
        if query.conversation_id:
            filtered = [
                m for m in filtered if m.metadata.get("conversation_id") == query.conversation_id
            ]

        # Filter by tags
        if query.tags:
            filtered = [
                m
                for m in filtered
                if all(tag in (m.metadata.get("tags") or []) for tag in query.tags)
            ]

        return filtered

    def _apply_recency_weighting(
        self, memories: List[MemoryEntry], similarity_scores: Dict[str, float]
    ) -> List[MemoryEntry]:
        """Apply recency weighting and sort memories."""
        current_time = time.time()

        for memory in memories:
            # Get similarity score
            similarity = similarity_scores.get(memory.id, 0.0)

            # Calculate recency weight
            age_days = (current_time - memory.timestamp) / (24 * 3600)
            recency_weight = np.exp(-self.recency_alpha * age_days)

            # Combined score
            memory.similarity_score = similarity * recency_weight

        # Sort by combined score
        return sorted(memories, key=lambda m: m.similarity_score or 0, reverse=True)

    def _get_cache_key(
        self, tenant_id: Union[str, uuid.UUID], query: MemoryQuery
    ) -> str:
        """Generate cache key for query."""
        import hashlib

        query_str = json.dumps(query.to_dict(), sort_keys=True)
        query_hash = hashlib.md5(query_str.encode()).hexdigest()
        return f"memory_query:{tenant_id}:{query_hash}"

    async def _get_cached_query(self, cache_key: str) -> Optional[List[MemoryEntry]]:
        """Get cached query result."""
        if not self.redis_client:
            return None

        try:
            cached_data = await self.redis_client.get(cache_key)
            if cached_data:
                data = json.loads(cached_data)
                return [MemoryEntry(**item) for item in data]
        except Exception as e:
            logger.warning(f"Failed to get cached query: {e}")

        return None

    async def _cache_query_result(self, cache_key: str, memories: List[MemoryEntry]):
        """Cache query result."""
        if not self.redis_client:
            return

        try:
            data = [memory.to_dict() for memory in memories]
            await self.redis_client.setex(
                cache_key, self.cache_ttl_seconds, json.dumps(data)
            )
        except Exception as e:
            logger.warning(f"Failed to cache query result: {e}")

    async def _cache_memory(
        self, tenant_id: Union[str, uuid.UUID], memory: MemoryEntry
    ):
        """Cache recent memory entry."""
        if not self.redis_client:
            return

        try:
            cache_key = f"memory:{tenant_id}:{memory.id}"
            await self.redis_client.setex(
                cache_key, self.cache_ttl_seconds, json.dumps(memory.to_dict())
            )
        except Exception as e:
            logger.warning(f"Failed to cache memory: {e}")

    async def _clear_memory_cache(
        self, tenant_id: Union[str, uuid.UUID], memory_id: str
    ):
        """Clear memory from cache."""
        if not self.redis_client:
            return

        try:
            cache_key = f"memory:{tenant_id}:{memory_id}"
            await self.redis_client.delete(cache_key)
        except Exception as e:
            logger.warning(f"Failed to clear memory cache: {e}")

    async def _store_in_elasticsearch(
        self, tenant_id: Union[str, uuid.UUID], memory: MemoryEntry
    ):
        """Store memory in Elasticsearch for full-text search."""
        if not self.elasticsearch_client:
            return

        try:
            index_name = f"tenant_{str(tenant_id).replace('-', '_')}_memories"
            doc = {
                "memory_id": memory.id,
                "content": memory.content,
                "metadata": memory.metadata,
                "timestamp": memory.timestamp,
                "scope": memory.scope,
                "kind": memory.kind,
            }

            await self.elasticsearch_client.index(
                index=index_name, id=memory.id, body=doc
            )
        except Exception as e:
            logger.warning(f"Failed to store in Elasticsearch: {e}")

    async def _delete_from_elasticsearch(
        self, tenant_id: Union[str, uuid.UUID], memory_id: str
    ):
        """Delete memory from Elasticsearch."""
        if not self.elasticsearch_client:
            return

        try:
            index_name = f"tenant_{str(tenant_id).replace('-', '_')}_memories"
            await self.elasticsearch_client.delete(index=index_name, id=memory_id)
        except Exception as e:
            logger.warning(f"Failed to delete from Elasticsearch: {e}")
