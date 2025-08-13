"""
Unified Memory Service - Phase 4.1.b
Consolidates all memory adapters into single service with unified query/commit paths.
"""

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
from pydantic import BaseModel, Field

from ai_karen_engine.services.structured_logging import PIIRedactor

from ..core.embedding_manager import EmbeddingManager
from ..core.milvus_client import MilvusClient
from ..database.client import MultiTenantPostgresClient
from ..database.memory_manager import MemoryEntry, MemoryManager, MemoryQuery
from .memory_policy import DecayTier, ImportanceLevel, MemoryPolicy, MemoryPolicyManager
from .memory_writeback import InteractionType, MemoryWritebackSystem, ShardUsageType

logger = logging.getLogger(__name__)


# Unified data models for consistent interface
class ContextHit(BaseModel):
    """Unified memory hit representation across all interfaces"""

    id: str
    text: str
    preview: Optional[str] = None
    score: float
    tags: List[str] = Field(default_factory=list)
    recency: Optional[str] = None
    meta: Dict[str, Any] = Field(default_factory=dict)
    importance: int = Field(5, ge=1, le=10)
    decay_tier: str = Field("short")
    created_at: datetime
    updated_at: Optional[datetime] = None
    user_id: str
    org_id: Optional[str] = None


class MemoryCommitRequest(BaseModel):
    """Unified memory commit request"""

    user_id: str = Field(..., min_length=1)
    org_id: Optional[str] = None
    text: str = Field(..., min_length=1, max_length=16000)
    tags: List[str] = Field(default_factory=list)
    importance: int = Field(5, ge=1, le=10)
    decay: str = Field("short", pattern="^(short|medium|long|pinned)$")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MemoryQueryRequest(BaseModel):
    """Unified memory query request"""

    user_id: str = Field(..., min_length=1)
    org_id: Optional[str] = None
    query: str = Field(..., min_length=1, max_length=4096)
    top_k: int = Field(12, ge=1, le=50)
    similarity_threshold: float = Field(0.7, ge=0.0, le=1.0)
    include_metadata: bool = Field(True)


class MemorySearchResponse(BaseModel):
    """Unified memory search response"""

    hits: List[ContextHit]
    total_found: int
    query_time_ms: float
    correlation_id: str


class MemoryCommitResponse(BaseModel):
    """Unified memory commit response"""

    id: str
    success: bool
    decay_tier: str
    expires_at: Optional[datetime]
    correlation_id: str


@dataclass
class MemoryUsageStats:
    """Memory usage statistics for feedback loops"""

    memory_id: str
    usage_count: int = 0
    ignore_count: int = 0
    total_retrievals: int = 0
    last_used: Optional[datetime] = None
    last_ignored: Optional[datetime] = None
    recency_score: float = 0.0


class UnifiedMemoryService:
    """
    Unified memory service consolidating all adapters.
    Provides single query/commit paths for AG-UI, chat, and copilot interfaces.
    """

    def __init__(
        self,
        db_client: MultiTenantPostgresClient,
        milvus_client: MilvusClient,
        embedding_manager: EmbeddingManager,
        redis_client: Optional[Any] = None,
        policy_manager: Optional[MemoryPolicyManager] = None,
    ):
        """Initialize unified memory service"""
        self.db_client = db_client
        self.milvus_client = milvus_client
        self.embedding_manager = embedding_manager
        self.redis_client = redis_client

        # Initialize policy manager
        self.policy_manager = policy_manager or MemoryPolicyManager()
        self.policy = self.policy_manager.policy

        # Initialize base memory manager for compatibility
        self.base_manager = MemoryManager(
            db_client=db_client,
            milvus_client=milvus_client,
            embedding_manager=embedding_manager,
            redis_client=redis_client,
        )

        # Initialize writeback system for shard linking
        self.writeback_system = MemoryWritebackSystem(
            unified_memory_service=self, redis_client=redis_client
        )

        # Usage tracking for feedback loops
        self._usage_stats: Dict[str, MemoryUsageStats] = {}

        # Performance metrics
        self.metrics = {
            "unified_queries": 0,
            "unified_commits": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "tier_promotions": 0,
            "tier_demotions": 0,
            "avg_query_time_ms": 0.0,
            "avg_commit_time_ms": 0.0,
        }

    async def query(
        self,
        tenant_id: Union[str, uuid.UUID],
        request: MemoryQueryRequest,
        correlation_id: Optional[str] = None,
    ) -> MemorySearchResponse:
        """
        Single query path supporting all interfaces (AG-UI, chat, copilot).
        Provides consistent results with tenant filtering and policy application.
        """
        start_time = time.time()
        correlation_id = correlation_id or str(uuid.uuid4())

        try:
            self.metrics["unified_queries"] += 1

            # 1. Tenant filtering - build metadata filter
            metadata_filter = {"user_id": request.user_id}
            if request.org_id:
                metadata_filter["org_id"] = request.org_id

            # 2. Create base query with policy-driven parameters
            rerank_window = self.policy.calculate_rerank_window(request.top_k)

            base_query = MemoryQuery(
                text=request.query,
                metadata_filter=metadata_filter,
                top_k=rerank_window,  # Get more for reranking
                similarity_threshold=request.similarity_threshold,
                include_embeddings=False,
            )

            # 3. Execute vector similarity search
            base_memories = await self.base_manager.query_memories(
                tenant_id, base_query
            )

            # 4. Apply policy-based filtering and ranking
            filtered_memories = await self._apply_policy_filtering(base_memories)

            # 5. Convert to unified format
            context_hits = await self._convert_to_context_hits(
                filtered_memories, request.user_id, request.org_id
            )

            # 6. Apply final ranking and limit results
            ranked_hits = self._apply_final_ranking(context_hits)
            final_hits = ranked_hits[: request.top_k]

            # 7. Update usage statistics for feedback loops
            await self._update_usage_stats(final_hits, used=True)

            # 8. Calculate metrics
            query_time_ms = (time.time() - start_time) * 1000
            self.metrics["avg_query_time_ms"] = (
                self.metrics["avg_query_time_ms"] * 0.9 + query_time_ms * 0.1
            )

            logger.info(
                f"Unified query completed: {len(final_hits)} hits in {query_time_ms:.2f}ms",
                extra={"correlation_id": correlation_id, "tenant_id": str(tenant_id)},
            )

            return MemorySearchResponse(
                hits=final_hits,
                total_found=len(base_memories),
                query_time_ms=query_time_ms,
                correlation_id=correlation_id,
            )

        except Exception as e:
            logger.error(
                f"Unified query failed: {e}",
                extra={"correlation_id": correlation_id, "tenant_id": str(tenant_id)},
            )
            raise

    async def commit(
        self,
        tenant_id: Union[str, uuid.UUID],
        request: MemoryCommitRequest,
        correlation_id: Optional[str] = None,
    ) -> MemoryCommitResponse:
        """
        Single commit path with consistent tagging and decay policies.
        Handles embedding generation and decay tier assignment.
        """
        start_time = time.time()
        correlation_id = correlation_id or str(uuid.uuid4())

        try:
            self.metrics["unified_commits"] += 1

            # 1. Validate and assign decay tier based on importance
            decay_tier = DecayTier(request.decay)
            if (
                decay_tier == DecayTier.SHORT
                and request.importance >= self.policy.importance_long_threshold
            ):
                # Auto-promote to long-term based on importance
                decay_tier = DecayTier.LONG
                logger.info(
                    f"Auto-promoted memory to long-term based on importance {request.importance}"
                )

            # 2. Prepare metadata with unified fields
            unified_metadata = {
                "user_id": request.user_id,
                "org_id": request.org_id,
                "importance": request.importance,
                "decay_tier": decay_tier.value,
                "tags": request.tags,
                "created_at": datetime.utcnow().isoformat(),
                "interface": "unified",  # Mark as coming from unified service
                **request.metadata,
            }

            # 3. Store using base manager
            memory_id = await self.base_manager.store_memory(
                tenant_id=tenant_id,
                content=request.text,
                scope=f"user:{request.user_id}",
                kind="memory",
                metadata=unified_metadata,
            )

            if not memory_id:
                raise ValueError(
                    "Failed to store memory - content not surprising enough"
                )

            # 4. Calculate expiry date
            expires_at = self.policy.calculate_expiry_date(decay_tier)

            # 5. Initialize usage stats
            self._usage_stats[memory_id] = MemoryUsageStats(memory_id=memory_id)

            # 6. Calculate metrics
            commit_time_ms = (time.time() - start_time) * 1000
            self.metrics["avg_commit_time_ms"] = (
                self.metrics["avg_commit_time_ms"] * 0.9 + commit_time_ms * 0.1
            )

            logger.info(
                f"Unified commit completed: {memory_id} in {commit_time_ms:.2f}ms",
                extra={"correlation_id": correlation_id, "tenant_id": str(tenant_id)},
            )

            return MemoryCommitResponse(
                id=memory_id,
                success=True,
                decay_tier=decay_tier.value,
                expires_at=expires_at,
                correlation_id=correlation_id,
            )

        except Exception as e:
            logger.error(
                f"Unified commit failed: {e}",
                extra={"correlation_id": correlation_id, "tenant_id": str(tenant_id)},
            )
            raise

    async def update(
        self,
        tenant_id: Union[str, uuid.UUID],
        memory_id: str,
        updates: Dict[str, Any],
        correlation_id: Optional[str] = None,
    ) -> bool:
        """
        Update memory with version tracking and importance recalculation.
        Implements comprehensive UPDATE operation with audit trails.
        """
        correlation_id = correlation_id or str(uuid.uuid4())

        try:
            # 1. Get current memory for version tracking
            current_memory = await self._get_memory_by_id(tenant_id, memory_id)
            if not current_memory:
                logger.warning(f"Memory not found for update: {memory_id}")
                return False

            # 2. Create audit trail entry
            await self._create_audit_entry(
                tenant_id=tenant_id,
                memory_id=memory_id,
                action="UPDATE",
                correlation_id=correlation_id,
                changes=updates,
                previous_version=current_memory.metadata.get("version", 1),
            )

            # 3. Prepare updated metadata with version increment
            current_metadata = current_memory.metadata or {}
            current_version = current_metadata.get("version", 1)
            new_version = current_version + 1

            updated_metadata = {
                **current_metadata,
                "version": new_version,
                "updated_at": datetime.utcnow().isoformat(),
                "updated_by": updates.get("updated_by", "system"),
                **updates.get("metadata", {}),
            }

            # 4. Handle importance recalculation
            new_importance = updates.get("importance")
            if new_importance is not None:
                # Validate importance
                if not (1 <= new_importance <= 10):
                    raise ValueError("Importance must be between 1 and 10")

                updated_metadata["importance"] = new_importance

                # Recalculate decay tier if importance changed significantly
                old_importance = current_metadata.get("importance", 5)
                if abs(new_importance - old_importance) >= 2:
                    new_decay_tier = self.policy.assign_decay_tier(new_importance)
                    updated_metadata["decay_tier"] = new_decay_tier.value

                    # Update expiry date
                    created_at = datetime.fromisoformat(
                        current_metadata.get(
                            "created_at", datetime.utcnow().isoformat()
                        )
                    )
                    new_expiry = self.policy.calculate_expiry_date(
                        new_decay_tier, created_at
                    )
                    if new_expiry:
                        updated_metadata["expires_at"] = new_expiry.isoformat()

            # 5. Handle content updates (requires re-embedding)
            new_content = updates.get("content")
            if new_content is not None:
                # Generate new embedding
                new_embedding = await self.embedding_manager.get_embedding(new_content)

                # Update vector store
                collection_name = self.base_manager._get_collection_name(tenant_id)

                # Delete old vector
                await self.milvus_client.delete(
                    collection_name=collection_name,
                    filter_expr=f"memory_id == '{memory_id}'",
                )

                # Insert new vector
                vector_metadata = {
                    "memory_id": memory_id,
                    "scope": f"user:{updated_metadata.get('user_id', 'unknown')}",
                    "kind": "memory",
                    "timestamp": time.time(),
                    **{
                        k: v
                        for k, v in updated_metadata.items()
                        if k not in ["content", "embedding"]
                    },
                }

                await self.milvus_client.insert(
                    collection_name=collection_name,
                    vectors=[new_embedding.tolist()],
                    metadata=[vector_metadata],
                )

                # Update content in metadata
                updated_metadata["content"] = new_content
                updated_metadata["embedding_updated"] = True

            # 6. Handle tag updates
            new_tags = updates.get("tags")
            if new_tags is not None:
                # Validate and normalize tags
                validated_tags = []
                for tag in new_tags:
                    if isinstance(tag, str) and tag.strip():
                        validated_tags.append(tag.strip().lower())

                updated_metadata["tags"] = validated_tags[:20]  # Limit to 20 tags

            # 7. Update database record
            async with self.db_client.get_async_session() as session:
                from sqlalchemy import update

                from ..database.models import TenantMemoryItem

                await session.execute(
                    update(TenantMemoryItem)
                    .where(TenantMemoryItem.id == uuid.UUID(memory_id))
                    .values(
                        content=new_content or current_memory.content,
                        metadata=updated_metadata,
                        updated_at=datetime.utcnow(),
                    )
                )
                await session.commit()

            # 8. Update usage stats if available
            if memory_id in self._usage_stats:
                self._usage_stats[memory_id].last_used = datetime.utcnow()

            logger.info(
                f"Memory updated successfully: {memory_id} (version {new_version})",
                extra={"correlation_id": correlation_id, "tenant_id": str(tenant_id)},
            )

            return True

        except Exception as e:
            logger.error(
                f"Memory update failed: {e}",
                extra={"correlation_id": correlation_id, "tenant_id": str(tenant_id)},
            )
            return False

    async def delete(
        self,
        tenant_id: Union[str, uuid.UUID],
        memory_id: str,
        hard_delete: bool = False,
        correlation_id: Optional[str] = None,
    ) -> bool:
        """
        Delete memory with soft/hard deletion options and audit trails.
        Implements comprehensive DELETE operation with privacy compliance.
        """
        correlation_id = correlation_id or str(uuid.uuid4())

        try:
            # 1. Get current memory for audit trail
            current_memory = await self._get_memory_by_id(tenant_id, memory_id)
            if not current_memory:
                logger.warning(f"Memory not found for deletion: {memory_id}")
                return False

            # 2. Create audit trail entry
            await self._create_audit_entry(
                tenant_id=tenant_id,
                memory_id=memory_id,
                action="DELETE",
                correlation_id=correlation_id,
                changes={"hard_delete": hard_delete},
                previous_version=current_memory.metadata.get("version", 1),
            )

            if hard_delete:
                # 3a. Hard deletion - completely remove from all storage layers

                # Delete from vector store
                collection_name = self.base_manager._get_collection_name(tenant_id)
                await self.milvus_client.delete(
                    collection_name=collection_name,
                    filter_expr=f"memory_id == '{memory_id}'",
                )

                # Delete from PostgreSQL
                async with self.db_client.get_async_session() as session:
                    from sqlalchemy import delete

                    from ..database.models import TenantMemoryItem

                    await session.execute(
                        delete(TenantMemoryItem).where(
                            TenantMemoryItem.id == uuid.UUID(memory_id)
                        )
                    )
                    await session.commit()

                # Delete from Redis cache if available
                if self.redis_client:
                    cache_key = f"memory:{tenant_id}:{memory_id}"
                    await self.redis_client.delete(cache_key)

                logger.info(
                    f"Hard deletion completed: {memory_id}",
                    extra={
                        "correlation_id": correlation_id,
                        "tenant_id": str(tenant_id),
                    },
                )

            else:
                # 3b. Soft deletion - mark as deleted with audit trail
                current_metadata = current_memory.metadata or {}

                updated_metadata = {
                    **current_metadata,
                    "deleted_at": datetime.utcnow().isoformat(),
                    "deleted_by": "system",  # Could be enhanced with user context
                    "deletion_reason": "user_request",
                    "soft_deleted": True,
                    "version": current_metadata.get("version", 1) + 1,
                }

                # Update database record to mark as deleted
                async with self.db_client.get_async_session() as session:
                    from sqlalchemy import update

                    from ..database.models import TenantMemoryItem

                    await session.execute(
                        update(TenantMemoryItem)
                        .where(TenantMemoryItem.id == uuid.UUID(memory_id))
                        .values(metadata=updated_metadata, updated_at=datetime.utcnow())
                    )
                    await session.commit()

                # Remove from vector store (soft deleted memories shouldn't appear in searches)
                collection_name = self.base_manager._get_collection_name(tenant_id)
                await self.milvus_client.delete(
                    collection_name=collection_name,
                    filter_expr=f"memory_id == '{memory_id}'",
                )

                logger.info(
                    f"Soft deletion completed: {memory_id}",
                    extra={
                        "correlation_id": correlation_id,
                        "tenant_id": str(tenant_id),
                    },
                )

            # 4. Clean up usage stats
            if memory_id in self._usage_stats:
                del self._usage_stats[memory_id]

            return True

        except Exception as e:
            logger.error(
                f"Memory deletion failed: {e}",
                extra={"correlation_id": correlation_id, "tenant_id": str(tenant_id)},
            )
            return False

    async def _apply_policy_filtering(
        self, memories: List[MemoryEntry]
    ) -> List[MemoryEntry]:
        """Apply memory policy filtering and decay checks"""
        filtered = []
        current_time = datetime.utcnow()

        for memory in memories:
            # Check if memory has expired based on decay tier
            metadata = memory.metadata or {}
            decay_tier_str = metadata.get("decay_tier", "short")

            try:
                decay_tier = DecayTier(decay_tier_str)
                created_at = datetime.fromisoformat(
                    metadata.get("created_at", current_time.isoformat())
                )

                if not self.policy.is_expired(decay_tier, created_at):
                    filtered.append(memory)
                else:
                    logger.debug(f"Filtered expired memory: {memory.id}")
            except (ValueError, TypeError):
                # If we can't parse decay info, include the memory
                filtered.append(memory)

        return filtered

    async def _convert_to_context_hits(
        self, memories: List[MemoryEntry], user_id: str, org_id: Optional[str]
    ) -> List[ContextHit]:
        """Convert MemoryEntry objects to unified ContextHit format"""
        context_hits = []

        for memory in memories:
            metadata = memory.metadata or {}

            # Extract unified fields
            importance = metadata.get("importance", 5)
            decay_tier = metadata.get("decay_tier", "short")
            tags = metadata.get("tags", [])

            # Parse timestamps
            created_at = datetime.utcnow()
            updated_at = None

            try:
                if "created_at" in metadata:
                    created_at = datetime.fromisoformat(metadata["created_at"])
                if "updated_at" in metadata:
                    updated_at = datetime.fromisoformat(metadata["updated_at"])
            except (ValueError, TypeError):
                pass

            # Calculate recency string
            age = datetime.utcnow() - created_at
            if age.days == 0:
                recency = "today"
            elif age.days == 1:
                recency = "yesterday"
            elif age.days < 7:
                recency = f"{age.days} days ago"
            elif age.days < 30:
                recency = f"{age.days // 7} weeks ago"
            else:
                recency = f"{age.days // 30} months ago"

            redacted_text = PIIRedactor.redact_pii(memory.content)
            context_hit = ContextHit(
                id=memory.id,
                text=redacted_text,
                preview=redacted_text[:100],
                score=memory.similarity_score or 0.0,
                tags=tags,
                recency=recency,
                meta=metadata,
                importance=importance,
                decay_tier=decay_tier,
                created_at=created_at,
                updated_at=updated_at,
                user_id=user_id,
                org_id=org_id,
            )

            context_hits.append(context_hit)

        return context_hits

    def _apply_final_ranking(self, context_hits: List[ContextHit]) -> List[ContextHit]:
        """Apply final ranking with importance and recency weighting"""
        current_time = datetime.utcnow()

        for hit in context_hits:
            # Calculate age in days
            age_days = (current_time - hit.created_at).total_seconds() / (24 * 3600)

            # Apply recency weighting
            recency_weight = np.exp(-self.policy.recency_alpha * age_days)

            # Combine similarity, importance, and recency
            importance_weight = hit.importance / 10.0  # Normalize to 0-1
            combined_score = (
                hit.score * 0.5
                + importance_weight * 0.3  # Similarity: 50%
                + recency_weight * 0.2  # Importance: 30%  # Recency: 20%
            )

            # Update score for ranking
            hit.score = combined_score

        # Sort by combined score
        return sorted(context_hits, key=lambda h: h.score, reverse=True)

    async def _update_usage_stats(self, context_hits: List[ContextHit], used: bool):
        """Update usage statistics for feedback loops"""
        for i, hit in enumerate(context_hits):
            if hit.id not in self._usage_stats:
                self._usage_stats[hit.id] = MemoryUsageStats(memory_id=hit.id)

            stats = self._usage_stats[hit.id]
            stats.total_retrievals += 1

            if used:
                stats.usage_count += 1
                stats.last_used = datetime.utcnow()

                # Update recency score
                age_hours = (datetime.utcnow() - hit.created_at).total_seconds() / 3600
                stats.recency_score = np.exp(-age_hours / (24 * 7))  # Decay over weeks
            else:
                stats.ignore_count += 1
                stats.last_ignored = datetime.utcnow()

                # Track if top hit was ignored
                if i == 0:  # First result
                    # This would be logged for feedback metrics
                    pass

    async def get_feedback_metrics(
        self, tenant_id: Union[str, uuid.UUID]
    ) -> Dict[str, float]:
        """Calculate feedback loop metrics for policy adjustment"""
        if not self._usage_stats:
            return {
                "used_shard_rate": 0.0,
                "ignored_top_hit_rate": 0.0,
                "total_memories": 0,
            }

        total_usage = sum(stats.usage_count for stats in self._usage_stats.values())
        total_retrievals = sum(
            stats.total_retrievals for stats in self._usage_stats.values()
        )

        used_shard_rate = (
            total_usage / total_retrievals if total_retrievals > 0 else 0.0
        )

        # This would calculate ignored top hit rate from retrieval logs
        ignored_top_hit_rate = 0.0  # Placeholder

        return {
            "used_shard_rate": used_shard_rate,
            "ignored_top_hit_rate": ignored_top_hit_rate,
            "total_memories": len(self._usage_stats),
            "total_retrievals": total_retrievals,
            "total_usage": total_usage,
        }

    async def run_policy_adjustment(
        self, tenant_id: Union[str, uuid.UUID]
    ) -> Dict[str, Any]:
        """Run policy-based memory tier adjustments"""
        adjustments = {
            "promotions": 0,
            "demotions": 0,
            "importance_boosts": 0,
            "processed": 0,
        }

        for memory_id, stats in self._usage_stats.items():
            # Convert stats to dict for policy evaluation
            usage_stats = {
                "usage_count": stats.usage_count,
                "ignore_count": stats.ignore_count,
                "total_retrievals": stats.total_retrievals,
                "recency_score": stats.recency_score,
            }

            # This would get current tier and importance from database
            current_tier = DecayTier.SHORT  # Placeholder
            current_importance = 5  # Placeholder

            # Evaluate for adjustment
            recommendations = self.policy_manager.evaluate_memory_for_adjustment(
                memory_id, current_tier, current_importance, usage_stats
            )

            # Apply recommendations (would update database)
            if recommendations["should_promote"]:
                adjustments["promotions"] += 1
                self.metrics["tier_promotions"] += 1

            if recommendations["should_demote"]:
                adjustments["demotions"] += 1
                self.metrics["tier_demotions"] += 1

            if recommendations["importance_boost"] > 0:
                adjustments["importance_boosts"] += 1

            adjustments["processed"] += 1

        logger.info(f"Policy adjustment completed: {adjustments}")
        return adjustments

    def get_service_metrics(self) -> Dict[str, Any]:
        """Get service performance metrics"""
        return {
            **self.metrics,
            "policy_summary": self.policy_manager.get_policy_summary(),
            "active_memories": len(self._usage_stats),
            "base_manager_metrics": self.base_manager.metrics,
        }

    async def _get_memory_by_id(
        self, tenant_id: Union[str, uuid.UUID], memory_id: str
    ) -> Optional[MemoryEntry]:
        """Get memory by ID for CRUD operations"""
        try:
            async with self.db_client.get_async_session() as session:
                from sqlalchemy import select

                from ..database.models import TenantMemoryItem

                result = await session.execute(
                    select(TenantMemoryItem).where(
                        TenantMemoryItem.id == uuid.UUID(memory_id)
                    )
                )

                memory_record = result.scalar_one_or_none()
                if not memory_record:
                    return None

                # Convert to MemoryEntry
                memory_entry = MemoryEntry(
                    id=str(memory_record.id),
                    content=memory_record.content,
                    metadata=memory_record.metadata or {},
                    scope=memory_record.scope,
                    kind=memory_record.kind,
                    timestamp=memory_record.created_at.timestamp()
                    if memory_record.created_at
                    else time.time(),
                )

                if memory_record.embedding:
                    memory_entry.embedding = np.array(memory_record.embedding)

                return memory_entry

        except Exception as e:
            logger.error(f"Failed to get memory by ID {memory_id}: {e}")
            return None

    async def _create_audit_entry(
        self,
        tenant_id: Union[str, uuid.UUID],
        memory_id: str,
        action: str,
        correlation_id: str,
        changes: Dict[str, Any],
        previous_version: int,
    ):
        """Create audit trail entry for memory operations"""
        try:
            # This would create an audit log entry in a dedicated audit table
            # For now, we'll log the audit information
            audit_entry = {
                "tenant_id": str(tenant_id),
                "memory_id": memory_id,
                "action": action,
                "correlation_id": correlation_id,
                "changes": changes,
                "previous_version": previous_version,
                "timestamp": datetime.utcnow().isoformat(),
                "user_agent": "unified_memory_service",
            }

            logger.info(
                f"Audit trail: {action} operation on memory {memory_id}",
                extra=audit_entry,
            )

            # TODO: Store in dedicated audit table when implemented
            # This would be part of the comprehensive audit logging system

        except Exception as e:
            logger.error(f"Failed to create audit entry: {e}")
            # Don't fail the main operation if audit logging fails

    async def create(
        self,
        tenant_id: Union[str, uuid.UUID],
        request: MemoryCommitRequest,
        correlation_id: Optional[str] = None,
    ) -> MemoryCommitResponse:
        """
        CREATE operation with embedding generation and decay tier assignment.
        Alias for commit() method to complete CRUD interface.
        """
        return await self.commit(tenant_id, request, correlation_id)

    async def read(
        self,
        tenant_id: Union[str, uuid.UUID],
        memory_id: str,
        correlation_id: Optional[str] = None,
    ) -> Optional[ContextHit]:
        """
        READ operation to get a specific memory by ID.
        Part of comprehensive CRUD operations.
        """
        correlation_id = correlation_id or str(uuid.uuid4())

        try:
            memory = await self._get_memory_by_id(tenant_id, memory_id)
            if not memory:
                return None

            # Convert to ContextHit format
            metadata = memory.metadata or {}
            user_id = metadata.get("user_id", "unknown")
            org_id = metadata.get("org_id")

            context_hits = await self._convert_to_context_hits(
                [memory], user_id, org_id
            )

            if context_hits:
                # Update usage stats for read operation
                await self._update_usage_stats(context_hits, used=True)
                return context_hits[0]

            return None

        except Exception as e:
            logger.error(
                f"Memory read failed: {e}",
                extra={"correlation_id": correlation_id, "tenant_id": str(tenant_id)},
            )
            return None

    async def list_memories(
        self,
        tenant_id: Union[str, uuid.UUID],
        user_id: str,
        org_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        include_deleted: bool = False,
        correlation_id: Optional[str] = None,
    ) -> List[ContextHit]:
        """
        List memories for a user with pagination.
        Part of comprehensive CRUD operations.
        """
        correlation_id = correlation_id or str(uuid.uuid4())

        try:
            async with self.db_client.get_async_session() as session:
                from sqlalchemy import and_, or_, select

                from ..database.models import TenantMemoryItem

                # Build query conditions
                conditions = []

                # Filter by user_id in metadata
                conditions.append(
                    TenantMemoryItem.metadata.op("->>")("user_id") == user_id
                )

                # Filter by org_id if provided
                if org_id:
                    conditions.append(
                        TenantMemoryItem.metadata.op("->>")("org_id") == org_id
                    )

                # Filter out soft deleted unless requested
                if not include_deleted:
                    conditions.append(
                        or_(
                            TenantMemoryItem.metadata.op("->>")("soft_deleted").is_(
                                None
                            ),
                            TenantMemoryItem.metadata.op("->>")("soft_deleted")
                            != "true",
                        )
                    )

                # Execute query
                query = (
                    select(TenantMemoryItem)
                    .where(and_(*conditions))
                    .order_by(TenantMemoryItem.created_at.desc())
                    .limit(limit)
                    .offset(offset)
                )

                result = await session.execute(query)
                memory_records = result.fetchall()

                # Convert to MemoryEntry objects
                memories = []
                for record in memory_records:
                    memory_entry = MemoryEntry(
                        id=str(record.id),
                        content=record.content,
                        metadata=record.metadata or {},
                        scope=record.scope,
                        kind=record.kind,
                        timestamp=record.created_at.timestamp()
                        if record.created_at
                        else time.time(),
                    )
                    memories.append(memory_entry)

                # Convert to ContextHit format
                context_hits = await self._convert_to_context_hits(
                    memories, user_id, org_id
                )

                logger.info(
                    f"Listed {len(context_hits)} memories for user {user_id}",
                    extra={
                        "correlation_id": correlation_id,
                        "tenant_id": str(tenant_id),
                    },
                )

                return context_hits

        except Exception as e:
            logger.error(
                f"Memory listing failed: {e}",
                extra={"correlation_id": correlation_id, "tenant_id": str(tenant_id)},
            )
            return []

    async def get_memory_stats(
        self,
        tenant_id: Union[str, uuid.UUID],
        user_id: Optional[str] = None,
        org_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get comprehensive memory statistics"""
        try:
            async with self.db_client.get_async_session() as session:
                from sqlalchemy import and_, func, select

                from ..database.models import TenantMemoryItem

                # Build base query conditions
                conditions = []
                if user_id:
                    conditions.append(
                        TenantMemoryItem.metadata.op("->>")("user_id") == user_id
                    )
                if org_id:
                    conditions.append(
                        TenantMemoryItem.metadata.op("->>")("org_id") == org_id
                    )

                # Total memories
                total_query = select(func.count(TenantMemoryItem.id))
                if conditions:
                    total_query = total_query.where(and_(*conditions))

                total_result = await session.execute(total_query)
                total_memories = total_result.scalar() or 0

                # Memories by decay tier
                tier_stats = {}
                for tier in ["short", "medium", "long", "pinned"]:
                    tier_conditions = conditions + [
                        TenantMemoryItem.metadata.op("->>")("decay_tier") == tier
                    ]
                    tier_query = select(func.count(TenantMemoryItem.id)).where(
                        and_(*tier_conditions)
                    )
                    tier_result = await session.execute(tier_query)
                    tier_stats[tier] = tier_result.scalar() or 0

                # Recent memories (last 24 hours)
                recent_cutoff = datetime.utcnow() - timedelta(hours=24)
                recent_conditions = conditions + [
                    TenantMemoryItem.created_at > recent_cutoff
                ]
                recent_query = select(func.count(TenantMemoryItem.id)).where(
                    and_(*recent_conditions)
                )
                recent_result = await session.execute(recent_query)
                recent_memories = recent_result.scalar() or 0

                # Soft deleted memories
                deleted_conditions = conditions + [
                    TenantMemoryItem.metadata.op("->>")("soft_deleted") == "true"
                ]
                deleted_query = select(func.count(TenantMemoryItem.id)).where(
                    and_(*deleted_conditions)
                )
                deleted_result = await session.execute(deleted_query)
                deleted_memories = deleted_result.scalar() or 0

                return {
                    "total_memories": total_memories,
                    "memories_by_decay_tier": tier_stats,
                    "recent_memories_24h": recent_memories,
                    "soft_deleted_memories": deleted_memories,
                    "usage_stats": {
                        "active_memories_tracked": len(self._usage_stats),
                        "total_retrievals": sum(
                            s.total_retrievals for s in self._usage_stats.values()
                        ),
                        "total_usage": sum(
                            s.usage_count for s in self._usage_stats.values()
                        ),
                    },
                    "service_metrics": self.get_service_metrics(),
                }

        except Exception as e:
            logger.error(f"Failed to get memory stats: {e}")
            return {"error": str(e)}

    async def link_response_to_shards(
        self,
        response_id: str,
        response_content: str,
        source_context_hits: List[ContextHit],
        user_id: str,
        org_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> List[Any]:
        """
        Link copilot response to source memory shards for feedback tracking.
        Part of memory write-back system with shard linking.
        """
        return await self.writeback_system.link_response_to_shards(
            response_id=response_id,
            response_content=response_content,
            source_context_hits=source_context_hits,
            user_id=user_id,
            org_id=org_id,
            interaction_type=InteractionType.COPILOT_RESPONSE,
            correlation_id=correlation_id,
        )

    async def queue_interaction_writeback(
        self,
        content: str,
        interaction_type: InteractionType,
        user_id: str,
        org_id: Optional[str] = None,
        session_id: Optional[str] = None,
        source_shards: Optional[List[Any]] = None,
        tags: Optional[List[str]] = None,
        importance: int = 5,
        metadata: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
    ) -> str:
        """
        Queue user interaction for memory write-back with proper categorization.
        Part of memory write-back system with shard linking.
        """
        return await self.writeback_system.queue_writeback(
            content=content,
            interaction_type=interaction_type,
            user_id=user_id,
            org_id=org_id,
            session_id=session_id,
            source_shards=source_shards,
            tags=tags,
            importance=importance,
            metadata=metadata,
            correlation_id=correlation_id,
        )

    async def get_writeback_feedback_metrics(
        self,
        user_id: Optional[str] = None,
        org_id: Optional[str] = None,
        time_window_hours: int = 24,
    ) -> Dict[str, Any]:
        """
        Get feedback loop metrics for "used shard rate" and "ignored top-hit rate".
        Part of memory write-back system with shard linking.
        """
        return await self.writeback_system.calculate_feedback_metrics(
            user_id=user_id, org_id=org_id, time_window_hours=time_window_hours
        )

    async def process_pending_writebacks(self) -> int:
        """
        Process pending memory writebacks.
        Part of memory write-back system with shard linking.
        """
        return await self.writeback_system.process_writeback_batch()

    def get_service_metrics(self) -> Dict[str, Any]:
        """Get comprehensive service performance metrics"""
        base_metrics = {
            **self.metrics,
            "policy_summary": self.policy_manager.get_policy_summary(),
            "active_memories": len(self._usage_stats),
            "base_manager_metrics": self.base_manager.metrics,
        }

        # Add writeback system metrics
        writeback_metrics = self.writeback_system.get_system_metrics()
        base_metrics["writeback_system"] = writeback_metrics

        return base_metrics

    async def shutdown(self):
        """Shutdown the unified memory service and all subsystems"""
        try:
            # Shutdown writeback system
            await self.writeback_system.shutdown()

            logger.info("Unified memory service shutdown completed")

        except Exception as e:
            logger.error(f"Error during unified memory service shutdown: {e}")


# Export public interface - updated to include writeback components
__all__ = [
    "UnifiedMemoryService",
    "ContextHit",
    "MemoryCommitRequest",
    "MemoryQueryRequest",
    "MemorySearchResponse",
    "MemoryCommitResponse",
    "MemoryUsageStats",
    "InteractionType",
    "ShardUsageType",
]
