"""
Memory Manager - Orchestrates all memory tiers for EchoCore

Provides unified interface to short-term, long-term, and persistent memory.
Determines appropriate memory layer based on query type and coordinates retrieval.
"""

import logging
from typing import Any, Dict, List, Optional
from enum import Enum

from ai_karen_engine.echocore.memory_tiers.short_term_memory import (
    ShortTermMemory,
    MemoryVector,
    SearchResult
)
from ai_karen_engine.echocore.memory_tiers.long_term_memory import (
    LongTermMemory,
    TrendAnalysis
)
from ai_karen_engine.echocore.memory_tiers.persistent_memory import (
    PersistentMemory,
    UserData,
    InteractionRecord
)

logger = logging.getLogger(__name__)


class MemoryTier(str, Enum):
    """Memory tier types."""
    SHORT_TERM = "short_term"
    LONG_TERM = "long_term"
    PERSISTENT = "persistent"
    ALL = "all"


class QueryType(str, Enum):
    """Types of memory queries."""
    RECENT_CONTEXT = "recent_context"  # Recent interactions
    SEMANTIC_SEARCH = "semantic_search"  # Similarity search
    TREND_ANALYSIS = "trend_analysis"  # Historical trends
    USER_PROFILE = "user_profile"  # User data
    INTERACTION_HISTORY = "interaction_history"  # Full history


class MemoryManager:
    """
    Orchestrates all memory tiers for comprehensive memory management.

    Features:
    - Unified interface across memory tiers
    - Intelligent tier selection based on query type
    - Cross-tier retrieval and synthesis
    - Memory consolidation
    - Health monitoring
    """

    def __init__(
        self,
        user_id: str,
        short_term: Optional[ShortTermMemory] = None,
        long_term: Optional[LongTermMemory] = None,
        persistent: Optional[PersistentMemory] = None
    ):
        self.user_id = user_id
        self.short_term = short_term
        self.long_term = long_term
        self.persistent = persistent

        # Track which tiers are available
        self.available_tiers = {}
        if short_term:
            self.available_tiers[MemoryTier.SHORT_TERM] = short_term
        if long_term:
            self.available_tiers[MemoryTier.LONG_TERM] = long_term
        if persistent:
            self.available_tiers[MemoryTier.PERSISTENT] = persistent

        logger.info(
            f"MemoryManager initialized for user {user_id} "
            f"with tiers: {list(self.available_tiers.keys())}"
        )

    async def initialize(self) -> None:
        """Initialize all memory tiers."""
        if self.short_term:
            await self.short_term.initialize()
        # long_term and persistent don't need async initialization currently

    def _determine_tier(self, query_type: QueryType) -> MemoryTier:
        """
        Determine appropriate memory tier based on query type.

        Args:
            query_type: Type of query

        Returns:
            Appropriate memory tier
        """
        tier_mapping = {
            QueryType.RECENT_CONTEXT: MemoryTier.SHORT_TERM,
            QueryType.SEMANTIC_SEARCH: MemoryTier.SHORT_TERM,
            QueryType.TREND_ANALYSIS: MemoryTier.LONG_TERM,
            QueryType.USER_PROFILE: MemoryTier.PERSISTENT,
            QueryType.INTERACTION_HISTORY: MemoryTier.PERSISTENT
        }

        return tier_mapping.get(query_type, MemoryTier.SHORT_TERM)

    async def store_memory(
        self,
        content: str,
        tier: MemoryTier = MemoryTier.SHORT_TERM,
        metadata: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Store a memory in appropriate tier(s).

        Args:
            content: Memory content
            tier: Target tier (or ALL for all tiers)
            metadata: Optional metadata
            session_id: Session ID (for persistent tier)

        Returns:
            Dictionary with storage results
        """
        results = {}

        # Store in specified tier(s)
        if tier == MemoryTier.ALL or tier == MemoryTier.SHORT_TERM:
            if self.short_term:
                vector = await self.short_term.store(content, metadata)
                results[MemoryTier.SHORT_TERM] = {
                    "id": vector.id,
                    "timestamp": vector.timestamp
                }

        if tier == MemoryTier.ALL or tier == MemoryTier.LONG_TERM:
            if self.long_term:
                record = await self.long_term.store_interaction(
                    interaction_type=metadata.get("type", "memory") if metadata else "memory",
                    content=content,
                    metadata=metadata
                )
                results[MemoryTier.LONG_TERM] = {
                    "timestamp": record["timestamp"]
                }

        if tier == MemoryTier.ALL or tier == MemoryTier.PERSISTENT:
            if self.persistent and session_id:
                interaction = await self.persistent.store_interaction(
                    session_id=session_id,
                    query=content,
                    result="",  # Would be filled in by caller
                    metadata=metadata
                )
                results[MemoryTier.PERSISTENT] = {
                    "id": interaction.id,
                    "timestamp": interaction.timestamp
                }

        logger.debug(f"Stored memory in tiers: {list(results.keys())}")
        return results

    async def retrieve_memory(
        self,
        query: str,
        query_type: QueryType = QueryType.SEMANTIC_SEARCH,
        top_k: int = 10,
        include_context: bool = True
    ) -> Dict[str, Any]:
        """
        Retrieve memory based on query and type.

        Args:
            query: Search query
            query_type: Type of query to determine tier
            top_k: Number of results to return
            include_context: Include additional context from other tiers

        Returns:
            Dictionary with retrieval results
        """
        results = {
            "query": query,
            "query_type": query_type.value,
            "results": []
        }

        # Determine primary tier
        primary_tier = self._determine_tier(query_type)

        # Retrieve from primary tier
        if query_type in [QueryType.RECENT_CONTEXT, QueryType.SEMANTIC_SEARCH]:
            if self.short_term:
                search_results = await self.short_term.search(
                    query=query,
                    top_k=top_k,
                    apply_decay=(query_type == QueryType.RECENT_CONTEXT)
                )
                results["results"] = [
                    {
                        "content": sr.vector.content,
                        "similarity": sr.similarity,
                        "decayed_score": sr.decayed_score,
                        "timestamp": sr.vector.timestamp,
                        "metadata": sr.vector.metadata,
                        "tier": MemoryTier.SHORT_TERM.value
                    }
                    for sr in search_results
                ]

        elif query_type == QueryType.USER_PROFILE:
            if self.persistent:
                user_data = await self.persistent.get_user_data()
                if user_data:
                    results["user_data"] = {
                        "name": user_data.name,
                        "age": user_data.age,
                        "date_of_birth": user_data.date_of_birth,
                        "preferences": user_data.preferences,
                        "metadata": user_data.metadata
                    }

        elif query_type == QueryType.INTERACTION_HISTORY:
            if self.persistent:
                interactions = await self.persistent.get_interactions(limit=top_k)
                results["interactions"] = [
                    {
                        "query": i.query,
                        "result": i.result,
                        "timestamp": i.timestamp,
                        "session_id": i.session_id
                    }
                    for i in interactions
                ]

        elif query_type == QueryType.TREND_ANALYSIS:
            if self.long_term:
                trend = await self.long_term.query_trends(
                    metric="interaction_count",
                    days=30
                )
                results["trend"] = {
                    "metric": trend.metric,
                    "trend": trend.trend,
                    "change_percent": trend.change_percent,
                    "summary": trend.summary,
                    "data_points": trend.data_points
                }

        # Add context from other tiers if requested
        if include_context:
            results["context"] = await self._get_cross_tier_context(query)

        logger.debug(f"Retrieved memory for query_type: {query_type}")
        return results

    async def _get_cross_tier_context(self, query: str) -> Dict[str, Any]:
        """
        Get contextual information from all tiers.

        Args:
            query: Query for context

        Returns:
            Dictionary with cross-tier context
        """
        context = {}

        # Get user profile if available
        if self.persistent:
            user_data = await self.persistent.get_user_data()
            if user_data:
                context["user_profile"] = {
                    "name": user_data.name,
                    "preferences": user_data.preferences
                }

        # Get recent interactions count
        if self.long_term:
            stats = await self.long_term.get_statistics()
            context["long_term_stats"] = stats

        # Get short-term memory stats
        if self.short_term:
            stats = await self.short_term.get_statistics()
            context["short_term_stats"] = stats

        return context

    async def consolidate_memories(self) -> Dict[str, Any]:
        """
        Consolidate memories across tiers.

        Moves short-term memories to long-term storage based on criteria.

        Returns:
            Dictionary with consolidation results
        """
        results = {
            "consolidated_count": 0,
            "moved_to_long_term": 0
        }

        # Implementation would identify important short-term memories
        # and move them to long-term storage
        # For now, placeholder

        logger.info("Memory consolidation completed")
        return results

    async def get_comprehensive_statistics(self) -> Dict[str, Any]:
        """
        Get statistics from all memory tiers.

        Returns:
            Comprehensive statistics dictionary
        """
        stats = {
            "user_id": self.user_id,
            "available_tiers": list(self.available_tiers.keys()),
            "tiers": {}
        }

        if self.short_term:
            stats["tiers"][MemoryTier.SHORT_TERM.value] = await self.short_term.get_statistics()

        if self.long_term:
            stats["tiers"][MemoryTier.LONG_TERM.value] = await self.long_term.get_statistics()

        if self.persistent:
            stats["tiers"][MemoryTier.PERSISTENT.value] = await self.persistent.get_statistics()

        return stats

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on all memory tiers.

        Returns:
            Health check results
        """
        health = {
            "healthy": True,
            "issues": [],
            "tiers": {}
        }

        # Check each tier
        if self.short_term:
            tier_health = await self.short_term.health_check()
            health["tiers"][MemoryTier.SHORT_TERM.value] = tier_health
            if not tier_health["healthy"]:
                health["healthy"] = False
                health["issues"].extend([
                    f"SHORT_TERM: {issue}" for issue in tier_health["issues"]
                ])

        if self.long_term:
            tier_health = await self.long_term.health_check()
            health["tiers"][MemoryTier.LONG_TERM.value] = tier_health
            if not tier_health["healthy"]:
                health["healthy"] = False
                health["issues"].extend([
                    f"LONG_TERM: {issue}" for issue in tier_health["issues"]
                ])

        if self.persistent:
            tier_health = await self.persistent.health_check()
            health["tiers"][MemoryTier.PERSISTENT.value] = tier_health
            if not tier_health["healthy"]:
                health["healthy"] = False
                health["issues"].extend([
                    f"PERSISTENT: {issue}" for issue in tier_health["issues"]
                ])

        return health


__all__ = [
    "MemoryManager",
    "MemoryTier",
    "QueryType"
]
