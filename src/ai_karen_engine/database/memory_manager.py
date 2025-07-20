"""
Production-grade memory management system for AI Karen.
Integrates Milvus, Redis, Postgres, and Elasticsearch for comprehensive memory operations.
"""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, field
from contextlib import asynccontextmanager

import numpy as np
from sqlalchemy import text, select, insert, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from .client import MultiTenantPostgresClient
from .models import TenantMemoryEntry
from ..core.milvus_client import MilvusClient
from ..core.embedding_manager import EmbeddingManager

logger = logging.getLogger(__name__)


@dataclass
class MemoryEntry:
    """Represents a memory entry with all associated data."""
    id: str
    content: str
    embedding: Optional[np.ndarray] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    ttl: Optional[datetime] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    similarity_score: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "content": self.content,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
            "ttl": self.ttl.isoformat() if self.ttl else None,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "tags": self.tags,
            "similarity_score": self.similarity_score
        }


@dataclass
class MemoryQuery:
    """Represents a memory query with all parameters."""
    text: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    metadata_filter: Dict[str, Any] = field(default_factory=dict)
    time_range: Optional[Tuple[datetime, datetime]] = None
    top_k: int = 10
    similarity_threshold: float = 0.7
    include_embeddings: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            "text": self.text[:100] + "..." if len(self.text) > 100 else self.text,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "tags": self.tags,
            "metadata_filter": self.metadata_filter,
            "time_range": [t.isoformat() for t in self.time_range] if self.time_range else None,
            "top_k": self.top_k,
            "similarity_threshold": self.similarity_threshold
        }


class MemoryManager:
    """Production-grade memory management system."""
    
    def __init__(
        self,
        db_client: MultiTenantPostgresClient,
        milvus_client: MilvusClient,
        embedding_manager: EmbeddingManager,
        redis_client: Optional[Any] = None,
        elasticsearch_client: Optional[Any] = None
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
        self.surprise_threshold = 0.85  # Minimum similarity to consider "surprising"
        self.recency_alpha = 0.05  # Exponential decay factor for recency weighting
        
        # Performance tracking
        self.metrics = {
            "queries_total": 0,
            "queries_cached": 0,
            "embeddings_generated": 0,
            "memories_stored": 0,
            "memories_retrieved": 0,
            "avg_query_time": 0.0,
            "avg_embedding_time": 0.0
        }
    
    async def store_memory(
        self,
        tenant_id: Union[str, uuid.UUID],
        content: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        ttl_hours: Optional[int] = None
    ) -> str:
        """Store a memory entry with vector embedding.
        
        Args:
            tenant_id: Tenant ID
            content: Memory content
            user_id: User ID
            session_id: Session ID
            metadata: Additional metadata
            tags: Memory tags
            ttl_hours: Time to live in hours
            
        Returns:
            Memory entry ID
        """
        start_time = time.time()
        
        try:
            # Generate embedding
            embedding_start = time.time()
            embedding = await self.embedding_manager.get_embedding(content)
            embedding_time = time.time() - embedding_start
            
            # Check for surprise (novelty)
            is_surprising = await self._check_surprise(tenant_id, embedding, user_id)
            if not is_surprising:
                logger.debug(f"Content not surprising enough, skipping storage: {content[:50]}...")
                return None
            
            # Create memory entry
            memory_id = str(uuid.uuid4())
            ttl = datetime.utcnow() + timedelta(hours=ttl_hours or self.default_ttl_hours)
            
            memory_entry = MemoryEntry(
                id=memory_id,
                content=content,
                embedding=embedding,
                metadata=metadata or {},
                timestamp=time.time(),
                ttl=ttl,
                user_id=user_id,
                session_id=session_id,
                tags=tags or []
            )
            
            # Store in vector database
            collection_name = self._get_collection_name(tenant_id)
            vector_metadata = {
                "memory_id": memory_id,
                "user_id": user_id or "",
                "session_id": session_id or "",
                "timestamp": memory_entry.timestamp,
                "ttl": int(ttl.timestamp()),
                "tags": json.dumps(tags or [])
            }
            
            # Add additional metadata
            if metadata:
                vector_metadata.update(metadata)
            
            await self.milvus_client.insert(
                collection_name=collection_name,
                vectors=[embedding.tolist()],
                metadata=[vector_metadata]
            )
            
            # Store metadata in Postgres
            async with self.db_client.get_async_session() as session:
                schema_name = self.db_client.get_tenant_schema_name(tenant_id)
                
                memory_metadata = {
                    "tags": tags or [],
                    "embedding_model": getattr(self.embedding_manager, 'model_name', 'default')
                }
                if metadata:
                    memory_metadata.update(metadata)
                
                memory_record = TenantMemoryEntry(
                    id=uuid.UUID(memory_id),
                    vector_id=memory_id,
                    user_id=uuid.UUID(user_id) if user_id else None,
                    session_id=session_id,
                    content=content,
                    embedding_id=memory_id,
                    memory_metadata=memory_metadata,
                    ttl=ttl,
                    timestamp=int(memory_entry.timestamp)
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
            logger.info(f"Stored memory {memory_id} for tenant {tenant_id} in {total_time:.3f}s")
            
            return memory_id
            
        except Exception as e:
            logger.error(f"Failed to store memory for tenant {tenant_id}: {e}")
            raise
    
    async def query_memories(
        self,
        tenant_id: Union[str, uuid.UUID],
        query: MemoryQuery
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
            query_embedding = await self.embedding_manager.get_embedding(query.text)
            
            # Search vector database
            collection_name = self._get_collection_name(tenant_id)
            
            # Build metadata filter
            metadata_filter = self._build_metadata_filter(query)
            
            vector_results = await self.milvus_client.search(
                collection_name=collection_name,
                query_vectors=[query_embedding.tolist()],
                top_k=query.top_k * 2,  # Get more results for filtering
                metadata_filter=metadata_filter
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
            scored_memories = self._apply_recency_weighting(filtered_memories, similarity_scores)
            
            # Limit results
            final_memories = scored_memories[:query.top_k]
            
            # Cache results
            if self.redis_client:
                await self._cache_query_result(cache_key, final_memories)
            
            # Update metrics
            self.metrics["memories_retrieved"] += len(final_memories)
            query_time = time.time() - start_time
            self.metrics["avg_query_time"] = (
                self.metrics["avg_query_time"] * 0.9 + query_time * 0.1
            )
            
            logger.info(f"Retrieved {len(final_memories)} memories for tenant {tenant_id} in {query_time:.3f}s")
            
            return final_memories
            
        except Exception as e:
            logger.error(f"Failed to query memories for tenant {tenant_id}: {e}")
            raise
    
    async def delete_memory(
        self,
        tenant_id: Union[str, uuid.UUID],
        memory_id: str
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
            await self.milvus_client.delete(
                collection_name=collection_name,
                filter_expr=f"memory_id == '{memory_id}'"
            )
            
            # Delete from Postgres
            async with self.db_client.get_async_session() as session:
                await session.execute(
                    delete(TenantMemoryEntry).where(TenantMemoryEntry.vector_id == memory_id)
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
            logger.error(f"Failed to delete memory {memory_id} for tenant {tenant_id}: {e}")
            return False
    
    async def prune_expired_memories(self, tenant_id: Union[str, uuid.UUID]) -> int:
        """Prune expired memories for a tenant.
        
        Args:
            tenant_id: Tenant ID
            
        Returns:
            Number of memories pruned
        """
        try:
            now = datetime.utcnow()
            
            # Get expired memory IDs from Postgres
            async with self.db_client.get_async_session() as session:
                result = await session.execute(
                    select(TenantMemoryEntry.vector_id)
                    .where(TenantMemoryEntry.ttl < now)
                )
                expired_ids = [row[0] for row in result.fetchall()]
            
            if not expired_ids:
                return 0
            
            # Delete from vector database
            collection_name = self._get_collection_name(tenant_id)
            for memory_id in expired_ids:
                await self.milvus_client.delete(
                    collection_name=collection_name,
                    filter_expr=f"memory_id == '{memory_id}'"
                )
            
            # Delete from Postgres
            async with self.db_client.get_async_session() as session:
                await session.execute(
                    delete(TenantMemoryEntry).where(TenantMemoryEntry.ttl < now)
                )
                await session.commit()
            
            # Delete from Elasticsearch
            if self.elasticsearch_client:
                for memory_id in expired_ids:
                    await self._delete_from_elasticsearch(tenant_id, memory_id)
            
            logger.info(f"Pruned {len(expired_ids)} expired memories for tenant {tenant_id}")
            return len(expired_ids)
            
        except Exception as e:
            logger.error(f"Failed to prune memories for tenant {tenant_id}: {e}")
            return 0
    
    async def get_memory_stats(self, tenant_id: Union[str, uuid.UUID]) -> Dict[str, Any]:
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
                    select(TenantMemoryEntry).where(TenantMemoryEntry.id.isnot(None))
                )
                total_count = len(total_result.fetchall())
                
                # Memories by user
                user_result = await session.execute(
                    text(f"""
                        SELECT user_id, COUNT(*) as count
                        FROM {self.db_client.get_tenant_schema_name(tenant_id)}.memory_entries
                        GROUP BY user_id
                    """)
                )
                user_counts = {str(row[0]): row[1] for row in user_result.fetchall()}
                
                # Recent activity (last 24 hours)
                recent_cutoff = datetime.utcnow() - timedelta(hours=24)
                recent_result = await session.execute(
                    select(TenantMemoryEntry)
                    .where(TenantMemoryEntry.created_at > recent_cutoff)
                )
                recent_count = len(recent_result.fetchall())
                
                # Expired memories
                expired_result = await session.execute(
                    select(TenantMemoryEntry)
                    .where(TenantMemoryEntry.ttl < datetime.utcnow())
                )
                expired_count = len(expired_result.fetchall())
                
                return {
                    "total_memories": total_count,
                    "memories_by_user": user_counts,
                    "recent_memories_24h": recent_count,
                    "expired_memories": expired_count,
                    "collection_name": self._get_collection_name(tenant_id),
                    "metrics": self.metrics.copy()
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
        user_id: Optional[str] = None
    ) -> bool:
        """Check if content is surprising enough to store."""
        try:
            collection_name = self._get_collection_name(tenant_id)
            
            # Search for similar content
            results = await self.milvus_client.search(
                collection_name=collection_name,
                query_vectors=[embedding.tolist()],
                top_k=1,
                metadata_filter={"user_id": user_id} if user_id else None
            )
            
            if not results or not results[0]:
                return True  # No similar content, definitely surprising
            
            # Check similarity of most similar result
            max_similarity = results[0][0].distance if results[0] else 0
            return max_similarity < self.surprise_threshold
            
        except Exception as e:
            logger.warning(f"Failed to check surprise, assuming surprising: {e}")
            return True
    
    def _build_metadata_filter(self, query: MemoryQuery) -> Dict[str, Any]:
        """Build metadata filter for vector search."""
        filter_conditions = []
        
        if query.user_id:
            filter_conditions.append(f"user_id == '{query.user_id}'")
        
        if query.session_id:
            filter_conditions.append(f"session_id == '{query.session_id}'")
        
        if query.time_range:
            start_ts = int(query.time_range[0].timestamp())
            end_ts = int(query.time_range[1].timestamp())
            filter_conditions.append(f"timestamp >= {start_ts} and timestamp <= {end_ts}")
        
        # TTL filter (not expired)
        current_ts = int(datetime.utcnow().timestamp())
        filter_conditions.append(f"ttl > {current_ts}")
        
        if query.tags:
            # This is simplified - in practice, you'd need more complex tag filtering
            for tag in query.tags:
                filter_conditions.append(f"tags like '%{tag}%'")
        
        return " and ".join(filter_conditions) if filter_conditions else None
    
    async def _get_memories_from_postgres(
        self,
        tenant_id: Union[str, uuid.UUID],
        memory_ids: List[str],
        include_embeddings: bool = False
    ) -> List[MemoryEntry]:
        """Get full memory entries from Postgres."""
        try:
            async with self.db_client.get_async_session() as session:
                result = await session.execute(
                    select(TenantMemoryEntry)
                    .where(TenantMemoryEntry.vector_id.in_(memory_ids))
                )
                
                memories = []
                for row in result.fetchall():
                    memory = MemoryEntry(
                        id=row.vector_id,
                        content=row.content,
                        metadata=row.memory_metadata or {},
                        timestamp=row.timestamp or time.time(),
                        ttl=row.ttl,
                        user_id=str(row.user_id) if row.user_id else None,
                        session_id=row.session_id,
                        tags=row.memory_metadata.get("tags", []) if row.memory_metadata else []
                    )
                    
                    if include_embeddings:
                        # Get embedding from vector database if needed
                        pass  # Implementation depends on Milvus client capabilities
                    
                    memories.append(memory)
                
                return memories
                
        except Exception as e:
            logger.error(f"Failed to get memories from Postgres: {e}")
            return []
    
    def _apply_filters(self, memories: List[MemoryEntry], query: MemoryQuery) -> List[MemoryEntry]:
        """Apply additional filters to memory results."""
        filtered = memories
        
        # Filter by metadata
        if query.metadata_filter:
            filtered = [
                m for m in filtered
                if all(
                    m.metadata.get(k) == v
                    for k, v in query.metadata_filter.items()
                )
            ]
        
        # Filter by tags
        if query.tags:
            filtered = [
                m for m in filtered
                if any(tag in m.tags for tag in query.tags)
            ]
        
        return filtered
    
    def _apply_recency_weighting(
        self,
        memories: List[MemoryEntry],
        similarity_scores: Dict[str, float]
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
    
    def _get_cache_key(self, tenant_id: Union[str, uuid.UUID], query: MemoryQuery) -> str:
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
                cache_key,
                self.cache_ttl_seconds,
                json.dumps(data)
            )
        except Exception as e:
            logger.warning(f"Failed to cache query result: {e}")
    
    async def _cache_memory(self, tenant_id: Union[str, uuid.UUID], memory: MemoryEntry):
        """Cache recent memory entry."""
        if not self.redis_client:
            return
        
        try:
            cache_key = f"memory:{tenant_id}:{memory.id}"
            await self.redis_client.setex(
                cache_key,
                self.cache_ttl_seconds,
                json.dumps(memory.to_dict())
            )
        except Exception as e:
            logger.warning(f"Failed to cache memory: {e}")
    
    async def _clear_memory_cache(self, tenant_id: Union[str, uuid.UUID], memory_id: str):
        """Clear memory from cache."""
        if not self.redis_client:
            return
        
        try:
            cache_key = f"memory:{tenant_id}:{memory_id}"
            await self.redis_client.delete(cache_key)
        except Exception as e:
            logger.warning(f"Failed to clear memory cache: {e}")
    
    async def _store_in_elasticsearch(self, tenant_id: Union[str, uuid.UUID], memory: MemoryEntry):
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
                "user_id": memory.user_id,
                "session_id": memory.session_id,
                "tags": memory.tags
            }
            
            await self.elasticsearch_client.index(
                index=index_name,
                id=memory.id,
                body=doc
            )
        except Exception as e:
            logger.warning(f"Failed to store in Elasticsearch: {e}")
    
    async def _delete_from_elasticsearch(self, tenant_id: Union[str, uuid.UUID], memory_id: str):
        """Delete memory from Elasticsearch."""
        if not self.elasticsearch_client:
            return
        
        try:
            index_name = f"tenant_{str(tenant_id).replace('-', '_')}_memories"
            await self.elasticsearch_client.delete(
                index=index_name,
                id=memory_id
            )
        except Exception as e:
            logger.warning(f"Failed to delete from Elasticsearch: {e}")