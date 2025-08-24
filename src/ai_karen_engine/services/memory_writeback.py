"""
Memory Write-back System with Shard Linking - Phase 4.1.b
Implements write-back functionality that links responses to source shard IDs
with proper categorization and feedback loop measurement.
"""

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Union

from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)


class InteractionType(str, Enum):
    """Types of user interactions for categorization"""

    COPILOT_RESPONSE = "copilot_response"
    USER_QUERY = "user_query"
    SYSTEM_GENERATED = "system_generated"
    USER_FEEDBACK = "user_feedback"
    CONTEXT_USAGE = "context_usage"


class ShardUsageType(str, Enum):
    """Types of shard usage for feedback measurement"""

    USED_IN_RESPONSE = "used_in_response"
    IGNORED_TOP_HIT = "ignored_top_hit"
    PARTIAL_USAGE = "partial_usage"
    BACKGROUND_CONTEXT = "background_context"


@dataclass
class ShardLink:
    """Links between responses and source memory shards"""

    shard_id: str
    usage_type: ShardUsageType
    relevance_score: float
    position_in_results: int
    content_snippet: str
    usage_timestamp: datetime
    response_id: str
    user_id: str
    org_id: Optional[str] = None


@dataclass
class WritebackEntry:
    """Entry for memory write-back with shard linking"""

    id: str
    content: str
    interaction_type: InteractionType
    source_shards: List[ShardLink]
    user_id: str
    org_id: Optional[str]
    session_id: Optional[str]
    correlation_id: str
    tags: List[str] = field(default_factory=list)
    importance: int = 5
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)


class FeedbackMetrics(BaseModel):
    """Feedback loop metrics for shard usage analysis"""

    total_retrievals: int = 0
    total_used_shards: int = 0
    total_ignored_top_hits: int = 0
    used_shard_rate: float = 0.0
    ignored_top_hit_rate: float = 0.0
    average_relevance_score: float = 0.0
    shard_usage_distribution: Dict[str, int] = Field(default_factory=dict)
    time_window_hours: int = 24


class MemoryWritebackSystem:
    """
    Memory write-back system with shard linking and feedback measurement.
    Links copilot responses to source memory shards for feedback loops.
    """

    def __init__(self, unified_memory_service, redis_client: Optional[Any] = None):
        """Initialize write-back system"""
        self.memory_service = unified_memory_service
        self.redis_client = redis_client

        # Shard link tracking
        self._shard_links: Dict[str, List[ShardLink]] = {}
        self._pending_writebacks: List[WritebackEntry] = []

        # Feedback metrics tracking
        self._feedback_metrics: Dict[str, FeedbackMetrics] = {}

        # Configuration
        self.writeback_batch_size = 10
        self.writeback_interval_seconds = 30
        self.metrics_window_hours = 24
        self.max_shard_links_per_response = 20

        # Performance metrics
        self.metrics = {
            "writebacks_processed": 0,
            "shard_links_created": 0,
            "feedback_metrics_calculated": 0,
            "avg_writeback_time_ms": 0.0,
        }

        # Start background processing
        self._writeback_task = None
        self._start_background_processing()

    async def link_response_to_shards(
        self,
        response_id: str,
        response_content: str,
        source_context_hits: List[Any],  # ContextHit objects
        user_id: str,
        org_id: Optional[str] = None,
        interaction_type: InteractionType = InteractionType.COPILOT_RESPONSE,
        correlation_id: Optional[str] = None,
    ) -> List[ShardLink]:
        """
        Link a response to its source memory shards for feedback tracking.
        Creates shard links that will be used for feedback loop measurement.
        """
        correlation_id = correlation_id or str(uuid.uuid4())

        try:
            shard_links = []

            for i, context_hit in enumerate(
                source_context_hits[: self.max_shard_links_per_response]
            ):
                # Determine usage type based on content analysis
                usage_type = await self._determine_usage_type(
                    response_content, context_hit.text, i == 0  # Is top hit
                )

                # Extract relevant content snippet
                content_snippet = self._extract_content_snippet(
                    context_hit.text, response_content
                )

                shard_link = ShardLink(
                    shard_id=context_hit.id,
                    usage_type=usage_type,
                    relevance_score=context_hit.score,
                    position_in_results=i,
                    content_snippet=content_snippet,
                    usage_timestamp=datetime.utcnow(),
                    response_id=response_id,
                    user_id=user_id,
                    org_id=org_id,
                )

                shard_links.append(shard_link)

            # Store shard links for tracking
            self._shard_links[response_id] = shard_links
            self.metrics["shard_links_created"] += len(shard_links)

            # Update feedback metrics
            await self._update_feedback_metrics(user_id, org_id, shard_links)

            logger.info(
                f"Created {len(shard_links)} shard links for response {response_id}",
                extra={"correlation_id": correlation_id, "user_id": user_id},
            )

            return shard_links

        except Exception as e:
            logger.error(f"Failed to link response to shards: {e}")
            return []

    async def queue_writeback(
        self,
        content: str,
        interaction_type: InteractionType,
        user_id: str,
        org_id: Optional[str] = None,
        session_id: Optional[str] = None,
        source_shards: Optional[List[ShardLink]] = None,
        tags: Optional[List[str]] = None,
        importance: int = 5,
        metadata: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
    ) -> str:
        """
        Queue a memory write-back entry for batch processing.
        Links the entry to source shards for feedback measurement.
        """
        correlation_id = correlation_id or str(uuid.uuid4())

        try:
            writeback_id = str(uuid.uuid4())

            # Create writeback entry
            writeback_entry = WritebackEntry(
                id=writeback_id,
                content=content,
                interaction_type=interaction_type,
                source_shards=source_shards or [],
                user_id=user_id,
                org_id=org_id,
                session_id=session_id,
                correlation_id=correlation_id,
                tags=tags or [],
                importance=importance,
                metadata=metadata or {},
            )

            # Add to pending queue
            self._pending_writebacks.append(writeback_entry)

            # Apply categorization and tagging
            await self._apply_categorization(writeback_entry)

            logger.debug(
                f"Queued writeback entry: {writeback_id}",
                extra={"correlation_id": correlation_id, "user_id": user_id},
            )

            return writeback_id

        except Exception as e:
            logger.error(f"Failed to queue writeback: {e}")
            raise

    async def process_writeback_batch(self) -> int:
        """
        Process a batch of pending writeback entries.
        Commits them to the unified memory service.
        """
        if not self._pending_writebacks:
            return 0

        start_time = time.time()

        try:
            # Get batch to process
            batch = self._pending_writebacks[: self.writeback_batch_size]
            self._pending_writebacks = self._pending_writebacks[
                self.writeback_batch_size :
            ]

            processed_count = 0

            for entry in batch:
                try:
                    # Create memory commit request
                    from ai_karen_engine.services.unified_memory_service import (
                        MemoryCommitRequest,
                    )

                    # Determine decay tier based on interaction type and importance
                    decay_tier = self._determine_decay_tier(
                        entry.interaction_type, entry.importance
                    )

                    # Enhance metadata with shard links
                    enhanced_metadata = {
                        **entry.metadata,
                        "interaction_type": entry.interaction_type.value,
                        "source_shard_count": len(entry.source_shards),
                        "source_shard_ids": [
                            link.shard_id for link in entry.source_shards
                        ],
                        "session_id": entry.session_id,
                        "writeback_id": entry.id,
                        "writeback_timestamp": entry.created_at.isoformat(),
                    }

                    # Add shard link details
                    if entry.source_shards:
                        enhanced_metadata["shard_links"] = [
                            {
                                "shard_id": link.shard_id,
                                "usage_type": link.usage_type.value,
                                "relevance_score": link.relevance_score,
                                "position": link.position_in_results,
                            }
                            for link in entry.source_shards
                        ]

                    commit_request = MemoryCommitRequest(
                        user_id=entry.user_id,
                        org_id=entry.org_id,
                        text=entry.content,
                        tags=entry.tags,
                        importance=entry.importance,
                        decay=decay_tier,
                        metadata=enhanced_metadata,
                    )

                    # Commit to memory service
                    # Assume we have access to tenant_id through the service
                    tenant_id = "default"  # This would be properly resolved

                    response = await self.memory_service.commit(
                        tenant_id=tenant_id,
                        request=commit_request,
                        correlation_id=entry.correlation_id,
                    )

                    if response.success:
                        processed_count += 1

                        # Update shard usage tracking
                        await self._update_shard_usage_tracking(entry)

                except Exception as e:
                    logger.error(f"Failed to process writeback entry {entry.id}: {e}")
                    continue

            # Update metrics
            processing_time_ms = (time.time() - start_time) * 1000
            self.metrics["writebacks_processed"] += processed_count
            self.metrics["avg_writeback_time_ms"] = (
                self.metrics["avg_writeback_time_ms"] * 0.9
                + (processing_time_ms / max(processed_count, 1)) * 0.1
            )

            logger.info(
                f"Processed {processed_count} writeback entries in {processing_time_ms:.2f}ms"
            )

            return processed_count

        except Exception as e:
            logger.error(f"Failed to process writeback batch: {e}")
            return 0

    async def calculate_feedback_metrics(
        self,
        user_id: Optional[str] = None,
        org_id: Optional[str] = None,
        time_window_hours: int = 24,
    ) -> FeedbackMetrics:
        """
        Calculate feedback loop metrics for "used shard rate" and "ignored top-hit rate".
        Provides insights for memory policy adjustment.
        """
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=time_window_hours)

            # Filter shard links by time window and user/org
            relevant_links = []
            for response_id, links in self._shard_links.items():
                for link in links:
                    if link.usage_timestamp < cutoff_time:
                        continue

                    if user_id and link.user_id != user_id:
                        continue

                    if org_id and link.org_id != org_id:
                        continue

                    relevant_links.append(link)

            if not relevant_links:
                return FeedbackMetrics(time_window_hours=time_window_hours)

            # Calculate metrics
            total_retrievals = len(relevant_links)
            used_shards = len(
                [
                    link
                    for link in relevant_links
                    if link.usage_type == ShardUsageType.USED_IN_RESPONSE
                ]
            )
            ignored_top_hits = len(
                [
                    link
                    for link in relevant_links
                    if link.usage_type == ShardUsageType.IGNORED_TOP_HIT
                    and link.position_in_results == 0
                ]
            )

            used_shard_rate = (
                used_shards / total_retrievals if total_retrievals > 0 else 0.0
            )
            ignored_top_hit_rate = (
                ignored_top_hits / total_retrievals if total_retrievals > 0 else 0.0
            )

            # Calculate average relevance score
            avg_relevance = (
                sum(link.relevance_score for link in relevant_links) / total_retrievals
            )

            # Calculate usage distribution
            usage_distribution = {}
            for link in relevant_links:
                usage_type = link.usage_type.value
                usage_distribution[usage_type] = (
                    usage_distribution.get(usage_type, 0) + 1
                )

            metrics = FeedbackMetrics(
                total_retrievals=total_retrievals,
                total_used_shards=used_shards,
                total_ignored_top_hits=ignored_top_hits,
                used_shard_rate=used_shard_rate,
                ignored_top_hit_rate=ignored_top_hit_rate,
                average_relevance_score=avg_relevance,
                shard_usage_distribution=usage_distribution,
                time_window_hours=time_window_hours,
            )

            # Cache metrics
            cache_key = f"{user_id or 'all'}:{org_id or 'all'}"
            self._feedback_metrics[cache_key] = metrics
            self.metrics["feedback_metrics_calculated"] += 1

            logger.info(
                f"Calculated feedback metrics: {used_shard_rate:.2%} used rate, "
                f"{ignored_top_hit_rate:.2%} ignored top-hit rate"
            )

            return metrics

        except Exception as e:
            logger.error(f"Failed to calculate feedback metrics: {e}")
            return FeedbackMetrics(time_window_hours=time_window_hours)

    async def _determine_usage_type(
        self, response_content: str, shard_content: str, is_top_hit: bool
    ) -> ShardUsageType:
        """Determine how a shard was used in the response"""
        try:
            # Simple content overlap analysis
            response_words = set(response_content.lower().split())
            shard_words = set(shard_content.lower().split())

            overlap = len(response_words.intersection(shard_words))
            overlap_ratio = overlap / len(shard_words) if shard_words else 0

            if overlap_ratio > 0.3:  # Significant overlap
                return ShardUsageType.USED_IN_RESPONSE
            elif is_top_hit and overlap_ratio < 0.1:  # Top hit but minimal usage
                return ShardUsageType.IGNORED_TOP_HIT
            elif overlap_ratio > 0.1:  # Some usage
                return ShardUsageType.PARTIAL_USAGE
            else:
                return ShardUsageType.BACKGROUND_CONTEXT

        except Exception as e:
            logger.warning(f"Failed to determine usage type: {e}")
            return ShardUsageType.BACKGROUND_CONTEXT

    def _extract_content_snippet(
        self, shard_content: str, response_content: str
    ) -> str:
        """Extract relevant snippet from shard content"""
        try:
            # Simple extraction - first 100 characters
            return (
                shard_content[:100] + "..."
                if len(shard_content) > 100
                else shard_content
            )
        except Exception:
            return ""

    async def _apply_categorization(self, entry: WritebackEntry):
        """Apply proper categorization and tagging for writeback entry"""
        try:
            # Add interaction type as tag
            if entry.interaction_type.value not in entry.tags:
                entry.tags.append(entry.interaction_type.value)

            # Add source-based tags
            if entry.source_shards:
                entry.tags.append("has_source_shards")

                # Add usage type tags
                usage_types = set(link.usage_type.value for link in entry.source_shards)
                entry.tags.extend(list(usage_types))

            # Limit tags
            entry.tags = entry.tags[:20]

        except Exception as e:
            logger.warning(f"Failed to apply categorization: {e}")

    def _determine_decay_tier(
        self, interaction_type: InteractionType, importance: int
    ) -> str:
        """Determine decay tier based on interaction type and importance"""
        # Copilot responses are generally more valuable
        if interaction_type == InteractionType.COPILOT_RESPONSE:
            if importance >= 8:
                return "long"
            elif importance >= 6:
                return "medium"
            else:
                return "short"

        # User queries and feedback are moderately valuable
        elif interaction_type in [
            InteractionType.USER_QUERY,
            InteractionType.USER_FEEDBACK,
        ]:
            if importance >= 7:
                return "medium"
            else:
                return "short"

        # System generated content is typically short-term
        else:
            return "short"

    async def _update_feedback_metrics(
        self, user_id: str, org_id: Optional[str], shard_links: List[ShardLink]
    ):
        """Update feedback metrics with new shard links"""
        try:
            cache_key = f"{user_id}:{org_id or 'none'}"

            if cache_key not in self._feedback_metrics:
                self._feedback_metrics[cache_key] = FeedbackMetrics()

            metrics = self._feedback_metrics[cache_key]

            # Update counters
            metrics.total_retrievals += len(shard_links)

            for link in shard_links:
                if link.usage_type == ShardUsageType.USED_IN_RESPONSE:
                    metrics.total_used_shards += 1
                elif link.usage_type == ShardUsageType.IGNORED_TOP_HIT:
                    metrics.total_ignored_top_hits += 1

                # Update usage distribution
                usage_type = link.usage_type.value
                metrics.shard_usage_distribution[usage_type] = (
                    metrics.shard_usage_distribution.get(usage_type, 0) + 1
                )

            # Recalculate rates
            if metrics.total_retrievals > 0:
                metrics.used_shard_rate = (
                    metrics.total_used_shards / metrics.total_retrievals
                )
                metrics.ignored_top_hit_rate = (
                    metrics.total_ignored_top_hits / metrics.total_retrievals
                )

        except Exception as e:
            logger.warning(f"Failed to update feedback metrics: {e}")

    async def _update_shard_usage_tracking(self, entry: WritebackEntry):
        """Update shard usage tracking for feedback loops"""
        try:
            for link in entry.source_shards:
                # This would update usage statistics in the unified memory service
                if hasattr(self.memory_service, "_usage_stats"):
                    if link.shard_id in self.memory_service._usage_stats:
                        stats = self.memory_service._usage_stats[link.shard_id]

                        if link.usage_type == ShardUsageType.USED_IN_RESPONSE:
                            stats.usage_count += 1
                            stats.last_used = datetime.utcnow()
                        elif link.usage_type == ShardUsageType.IGNORED_TOP_HIT:
                            stats.ignore_count += 1
                            stats.last_ignored = datetime.utcnow()

                        stats.total_retrievals += 1
        except Exception as e:
            logger.warning(f"Failed to update shard usage tracking: {e}")

    def _start_background_processing(self):
        """Start background task for processing writebacks"""

        async def background_processor():
            while True:
                try:
                    await asyncio.sleep(self.writeback_interval_seconds)
                    await self.process_writeback_batch()
                except Exception as e:
                    logger.error(f"Background writeback processing failed: {e}")

        # This would be started by the application
        # self._writeback_task = asyncio.create_task(background_processor())

    async def shutdown(self):
        """Shutdown the writeback system and process remaining entries"""
        try:
            # Process all remaining writebacks
            while self._pending_writebacks:
                await self.process_writeback_batch()

            # Cancel background task
            if self._writeback_task:
                self._writeback_task.cancel()
                try:
                    await self._writeback_task
                except asyncio.CancelledError:
                    pass

            logger.info("Memory writeback system shutdown completed")

        except Exception as e:
            logger.error(f"Error during writeback system shutdown: {e}")

    def get_system_metrics(self) -> Dict[str, Any]:
        """Get writeback system metrics"""
        return {
            **self.metrics,
            "pending_writebacks": len(self._pending_writebacks),
            "active_shard_links": sum(
                len(links) for links in self._shard_links.values()
            ),
            "feedback_metrics_cached": len(self._feedback_metrics),
        }


# Export public interface
__all__ = [
    "MemoryWritebackSystem",
    "InteractionType",
    "ShardUsageType",
    "ShardLink",
    "WritebackEntry",
    "FeedbackMetrics",
]
