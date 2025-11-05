"""
Short-Term Memory - Vector-based fast recall using existing MilvusClient

Provides fast similarity search for recent interactions and context.
Uses vector embeddings for semantic search with decay function.
Integrates with existing MilvusClient infrastructure.
"""

import logging
import hashlib
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
import asyncio
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class MemoryVector:
    """Vector representation of a memory."""
    id: str
    user_id: str
    content: str
    embedding: List[float]
    timestamp: str
    metadata: Dict[str, Any]
    relevance_score: float = 1.0


@dataclass
class SearchResult:
    """Result from similarity search."""
    vector: MemoryVector
    similarity: float
    decayed_score: float
    rank: int


class ShortTermMemory:
    """
    Short-term memory using existing MilvusClient.

    Features:
    - Fast similarity search via Milvus
    - Embedding generation with sentence-transformers
    - Relevance decay over time
    - In-memory fallback when Milvus unavailable
    - Health monitoring
    """

    def __init__(
        self,
        user_id: str,
        milvus_client: Optional[Any] = None,
        decay_half_life_hours: float = 24.0,
        max_memories: int = 10000,
        enable_fallback: bool = True
    ):
        self.user_id = user_id
        self.milvus_client = milvus_client
        self.decay_half_life = timedelta(hours=decay_half_life_hours)
        self.max_memories = max_memories
        self.enable_fallback = enable_fallback

        # Determine if using fallback
        self._using_fallback = milvus_client is None

        # Fallback: in-memory vector store
        self._fallback_vectors: List[MemoryVector] = []

        # Embedding function
        self._embedding_function = None

        # Metrics
        self._total_inserts = 0
        self._total_searches = 0

        logger.info(f"ShortTermMemory initialized for user {user_id} (fallback={self._using_fallback})")

    async def initialize(self) -> None:
        """Initialize embedding function."""
        await self._initialize_embedding_function()

    async def _initialize_embedding_function(self) -> None:
        """Initialize embedding function."""
        try:
            from sentence_transformers import SentenceTransformer
            self._embedding_function = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Loaded SentenceTransformer embedding model")
        except ImportError:
            logger.warning("sentence-transformers not available, using random embeddings")
            self._embedding_function = None

    def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text."""
        if self._embedding_function is not None:
            try:
                embedding = self._embedding_function.encode(text)
                # Normalize
                normalized = embedding / np.linalg.norm(embedding)
                return normalized.tolist()
            except Exception as e:
                logger.error(f"Embedding generation failed: {e}")

        # Fallback: random embedding (for testing)
        logger.debug("Using random embedding (fallback)")
        vec = np.random.rand(384)
        return (vec / np.linalg.norm(vec)).tolist()

    def _calculate_decay(self, timestamp: datetime) -> float:
        """
        Calculate relevance decay based on time.

        Uses exponential decay: score = e^(-t/half_life)

        Args:
            timestamp: Memory timestamp

        Returns:
            Decay factor between 0 and 1
        """
        now = datetime.utcnow()
        age = now - timestamp

        # Exponential decay
        decay = np.exp(-age.total_seconds() / self.decay_half_life.total_seconds())
        return float(decay)

    async def store(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> MemoryVector:
        """
        Store a memory in short-term storage.

        Args:
            content: Memory content (text)
            metadata: Optional metadata

        Returns:
            MemoryVector with embedding
        """
        # Generate ID
        memory_id = hashlib.sha256(
            f"{self.user_id}{datetime.utcnow().isoformat()}{content}".encode()
        ).hexdigest()[:16]

        # Generate embedding
        embedding = self._generate_embedding(content)

        # Create memory vector
        vector = MemoryVector(
            id=memory_id,
            user_id=self.user_id,
            content=content,
            embedding=embedding,
            timestamp=datetime.utcnow().isoformat(),
            metadata=metadata or {},
            relevance_score=1.0
        )

        # Store in Milvus or fallback
        if self._using_fallback:
            await self._store_fallback(vector)
        else:
            await self._store_milvus(vector)

        self._total_inserts += 1

        # Cleanup if max memories exceeded
        await self._cleanup_old_memories()

        logger.debug(f"Stored memory: {memory_id}")
        return vector

    async def _store_milvus(self, vector: MemoryVector) -> None:
        """Store vector using MilvusClient."""
        # Since MilvusClient uses synchronous methods, wrap in executor
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            self.milvus_client.upsert_persona_embedding,
            f"{self.user_id}_{vector.id}",
            vector.embedding
        )

    async def _store_fallback(self, vector: MemoryVector) -> None:
        """Store vector in fallback in-memory store."""
        self._fallback_vectors.append(vector)

    async def search(
        self,
        query: str,
        top_k: int = 10,
        apply_decay: bool = True,
        min_similarity: float = 0.0
    ) -> List[SearchResult]:
        """
        Search for similar memories.

        Args:
            query: Search query
            top_k: Number of results to return
            apply_decay: Apply time-based relevance decay
            min_similarity: Minimum similarity threshold

        Returns:
            List of SearchResult objects
        """
        # Generate query embedding
        query_embedding = self._generate_embedding(query)

        # Search in Milvus or fallback
        if self._using_fallback:
            results = await self._search_fallback(query_embedding, top_k, apply_decay, min_similarity)
        else:
            results = await self._search_milvus(query_embedding, top_k, apply_decay, min_similarity)

        self._total_searches += 1

        logger.debug(f"Search returned {len(results)} results")
        return results

    async def _search_milvus(
        self,
        query_embedding: List[float],
        top_k: int,
        apply_decay: bool,
        min_similarity: float
    ) -> List[SearchResult]:
        """Search using MilvusClient."""
        # MilvusClient doesn't have a direct search method in the simple implementation
        # For now, use fallback. In production, we'd need to extend MilvusClient
        # to support general-purpose vector search.
        logger.warning("MilvusClient search not yet implemented, using fallback")
        return await self._search_fallback(query_embedding, top_k, apply_decay, min_similarity)

    async def _search_fallback(
        self,
        query_embedding: List[float],
        top_k: int,
        apply_decay: bool,
        min_similarity: float
    ) -> List[SearchResult]:
        """Search in fallback in-memory store."""
        # Calculate similarities
        results = []
        query_vec = np.array(query_embedding)

        for vector in self._fallback_vectors:
            vec = np.array(vector.embedding)

            # Cosine similarity
            similarity = float(np.dot(query_vec, vec) / (np.linalg.norm(query_vec) * np.linalg.norm(vec)))

            if similarity < min_similarity:
                continue

            # Calculate decay
            timestamp = datetime.fromisoformat(vector.timestamp)
            decay_factor = self._calculate_decay(timestamp) if apply_decay else 1.0
            decayed_score = similarity * decay_factor

            results.append((vector, similarity, decayed_score))

        # Sort by decayed score
        results.sort(key=lambda x: x[2], reverse=True)

        # Return top-k
        search_results = []
        for rank, (vector, similarity, decayed_score) in enumerate(results[:top_k]):
            search_results.append(SearchResult(
                vector=vector,
                similarity=similarity,
                decayed_score=decayed_score,
                rank=rank
            ))

        return search_results

    async def batch_store(self, items: List[Tuple[str, Optional[Dict[str, Any]]]]) -> List[MemoryVector]:
        """
        Store multiple memories in batch.

        Args:
            items: List of (content, metadata) tuples

        Returns:
            List of MemoryVector objects
        """
        vectors = []
        for content, metadata in items:
            vector = await self.store(content, metadata)
            vectors.append(vector)

        logger.info(f"Batch stored {len(vectors)} memories")
        return vectors

    async def _cleanup_old_memories(self) -> None:
        """Remove oldest memories if max limit exceeded."""
        if self._using_fallback:
            if len(self._fallback_vectors) > self.max_memories:
                # Sort by timestamp and keep most recent
                self._fallback_vectors.sort(key=lambda v: v.timestamp, reverse=True)
                removed = len(self._fallback_vectors) - self.max_memories
                self._fallback_vectors = self._fallback_vectors[:self.max_memories]
                logger.info(f"Cleaned up {removed} old memories")

    async def get_statistics(self) -> Dict[str, Any]:
        """
        Get memory statistics.

        Returns:
            Dictionary with statistics
        """
        stats = {
            "user_id": self.user_id,
            "using_fallback": self._using_fallback,
            "decay_half_life_hours": self.decay_half_life.total_seconds() / 3600,
            "max_memories": self.max_memories,
            "metrics": {
                "total_inserts": self._total_inserts,
                "total_searches": self._total_searches
            }
        }

        if self._using_fallback:
            stats["memory_count"] = len(self._fallback_vectors)
        else:
            stats["memory_count"] = 0  # Would need to query Milvus

        return stats

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check.

        Returns:
            Health check results
        """
        healthy = True
        issues = []

        # Check Milvus connection
        if not self._using_fallback and self.milvus_client:
            try:
                pool_util = self.milvus_client.pool_utilization()
                if pool_util > 0.9:
                    issues.append(f"High pool utilization: {pool_util:.2f}")
            except Exception as e:
                healthy = False
                issues.append(f"Milvus connection error: {e}")

        # Check embedding function
        if self._embedding_function is None:
            issues.append("Using fallback embedding (random)")

        return {
            "healthy": healthy,
            "using_fallback": self._using_fallback,
            "issues": issues,
            "statistics": await self.get_statistics()
        }


__all__ = [
    "ShortTermMemory",
    "MemoryVector",
    "SearchResult"
]
