"""
Hybrid Retrieval Router for AI Karen Memory System.

Decides which stores to use based on query type and orchestration hints.
Supports Redis, Milvus, Elasticsearch, and LeanGraph.
"""

import logging
import asyncio
import time
from typing import List

from ..types import MemoryQuery, MemoryEntry
from ...runtime.resilience import get_safe_stage_runner
from ai_karen_engine.clients.database.milvus_client import MilvusClient
from ai_karen_engine.clients.database.elastic_client import ElasticClient
from ai_karen_engine.clients.database.redis_client import RedisClient
from ai_karen_engine.core.memory.graph.service import get_leangraph_service

logger = logging.getLogger(__name__)

class HybridRetrievalRouter:
    """Intelligently routes memory queries to specialized projection stores."""

    def __init__(self):
        self.safe_runner = get_safe_stage_runner()
        self.milvus = MilvusClient(collection="memory_ledger_semantic")
        self.elastic = ElasticClient(index="memory_ledger_lexical")
        self.redis = RedisClient()
        self.leangraph = get_leangraph_service()
        
    async def recall(self, query: MemoryQuery) -> List[MemoryEntry]:
        """
        Execute hybrid retrieval across multiple stores.
        """
        start_time = time.time()
        
        # Determine retrieval strategy based on query content
        # Default: Hybrid (Lexical + Dense)
        tasks = []
        
        # 1. Hot state from Redis (Always checked for session context)
        tasks.append(self.safe_runner.run_stage(
            stage_name="redis_retrieval",
            flag_name="redis_enabled",
            func=self._query_redis,
            query=query
        ))
        
        # 2. Dense Semantic from Milvus
        tasks.append(self.safe_runner.run_stage(
            stage_name="milvus_retrieval",
            flag_name="milvus_enabled",
            func=self._query_milvus,
            query=query
        ))
        
        # 3. Lexical / Exact from Elasticsearch
        tasks.append(self.safe_runner.run_stage(
            stage_name="elasticsearch_retrieval",
            flag_name="elasticsearch_hybrid_enabled",
            func=self._query_elastic,
            query=query
        ))
        
        # 4. Optional Graph Expansion
        if self._is_graph_query(query):
            tasks.append(self.safe_runner.run_stage(
                stage_name="leangraph_retrieval",
                flag_name="graph_relationships_enabled",
                func=self._query_graph,
                query=query
            ))

        # Wait for all retrieval stages (resiliently handled by runner)
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Consolidation and Ranking
        all_candidates = []
        for res in results:
            if isinstance(res, list):
                all_candidates.extend(res)
                
        # Deduplicate by ID and rank
        unique_memories = self._deduplicate_and_rank(all_candidates, query)
        
        duration_ms = (time.time() - start_time) * 1000
        logger.info(f"Hybrid retrieval returned {len(unique_memories)} items in {duration_ms:.2f}ms")
        
        return unique_memories[:query.top_k]

    def _is_graph_query(self, query: MemoryQuery) -> bool:
        """Check if query warrants expensive graph expansion."""
        if not query.text:
            return False
        graph_triggers = ["related to", "connected", "contradict", "why", "how did this evolve"]
        return any(trigger in query.text.lower() for trigger in graph_triggers)

    async def _query_redis(self, query: MemoryQuery) -> List[MemoryEntry]:
        """Fetch hot interaction history from Redis."""
        # Implementation of Redis hot-memory fetch
        return [] # Placeholder

    async def _query_milvus(self, query: MemoryQuery) -> List[MemoryEntry]:
        """Fetch dense semantic matches from Milvus."""
        # Implementation of Milvus vector search
        return [] # Placeholder

    async def _query_elastic(self, query: MemoryQuery) -> List[MemoryEntry]:
        """Fetch exact and lexical matches from Elasticsearch."""
        # Implementation of Elasticsearch term/phrase search
        return [] # Placeholder

    async def _query_graph(self, query: MemoryQuery) -> List[MemoryEntry]:
        """Fetch multi-hop relational data from LeanGraph."""
        tenant_id = str(query.tenant_id or "")
        user_id = str(query.user_id or "")
        if not tenant_id or not user_id or not query.text:
            return []
        # Keep graph expansion optional and bounded; graph is an expansion source
        # and should never bypass the primary ranking path.
        results = await self.leangraph.get_entity_context(
            tenant_id=tenant_id,
            user_id=user_id,
            entity_text=query.text,
            limit=min(20, query.top_k * 2),
        )
        logger.info("leangraph_query_completed", extra={"component": "leangraph", "status": "completed", "tenant_id": tenant_id, "user_id": user_id, "result_count": len(results)})
        return []

    def _deduplicate_and_rank(self, candidates: List[MemoryEntry], query: MemoryQuery) -> List[MemoryEntry]:
        """Remove duplicates and apply final ranking logic."""
        seen_ids = set()
        unique = []
        for c in candidates:
            if c.id not in seen_ids:
                unique.append(c)
                seen_ids.add(c.id)
        
        # Simple recency sort for now
        return sorted(unique, key=lambda x: x.timestamp, reverse=True)

# Singleton instance
retrieval_router = HybridRetrievalRouter()

def get_retrieval_router() -> HybridRetrievalRouter:
    return retrieval_router
