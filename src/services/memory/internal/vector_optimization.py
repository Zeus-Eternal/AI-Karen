"""
Vector Query Optimization - Task 8.1
Optimizes vector similarity search to achieve p95 latency < 50ms with ≥ 0.95 recall rate
and ≥ +15% MRR improvement vs ANN-only.
"""

import asyncio
import hashlib
import json
import logging
import time
import uuid
from collections import OrderedDict, deque
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple, Union
from enum import Enum
import numpy as np
from concurrent.futures import ThreadPoolExecutor
import threading

logger = logging.getLogger(__name__)

class IndexType(str, Enum):
    """Vector index types for optimization"""
    FLAT = "flat"           # Exact search (baseline)
    HNSW = "hnsw"          # Hierarchical Navigable Small World
    IVF_FLAT = "ivf_flat"  # Inverted File with flat quantizer
    IVF_PQ = "ivf_pq"      # Inverted File with Product Quantization

@dataclass
class VectorSearchConfig:
    """Configuration for optimized vector search"""
    # Performance targets
    target_p95_latency_ms: float = 50.0
    target_recall_rate: float = 0.95
    target_mrr_improvement: float = 0.15
    
    # Index configuration
    index_type: IndexType = IndexType.HNSW
    hnsw_m: int = 16                    # Number of bi-directional links for HNSW
    hnsw_ef_construction: int = 200     # Size of dynamic candidate list for construction
    hnsw_ef_search: int = 50           # Size of dynamic candidate list for search
    
    # IVF configuration
    ivf_nlist: int = 1024              # Number of clusters for IVF
    ivf_nprobe: int = 10               # Number of clusters to search
    
    # Product Quantization configuration
    pq_m: int = 8                      # Number of subquantizers
    pq_nbits: int = 8                  # Number of bits per subquantizer
    
    # Reranking configuration
    rerank_enabled: bool = True
    rerank_factor: float = 3.0         # Retrieve rerank_factor * top_k for reranking
    rerank_model: str = "cross_encoder" # cross_encoder, bi_encoder, or hybrid
    
    # Caching configuration
    cache_enabled: bool = True
    cache_size: int = 10000
    cache_ttl_seconds: int = 300
    
    # Parallel processing
    max_workers: int = 4
    batch_size: int = 32

@dataclass
class SearchResult:
    """Optimized search result with performance metrics"""
    id: str
    score: float
    metadata: Dict[str, Any]
    rerank_score: Optional[float] = None
    original_rank: Optional[int] = None
    final_rank: Optional[int] = None

@dataclass
class SearchMetrics:
    """Performance metrics for vector search"""
    total_latency_ms: float
    index_latency_ms: float
    rerank_latency_ms: float
    cache_hit: bool
    results_count: int
    recall_rate: Optional[float] = None
    mrr_score: Optional[float] = None
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))

class OptimizedVectorIndex:
    """Optimized vector index with multiple backend support"""
    
    def __init__(self, config: VectorSearchConfig, dimension: int):
        self.config = config
        self.dimension = dimension
        self.index = None
        self.vectors: List[np.ndarray] = []
        self.metadata: List[Dict[str, Any]] = []
        self.id_to_idx: Dict[str, int] = {}
        self.lock = threading.RLock()
        
        # Performance tracking
        self.search_count = 0
        self.total_search_time = 0.0
        self.latency_percentiles = []
        
        # Initialize index based on type
        self._initialize_index()
    
    def _initialize_index(self):
        """Initialize the appropriate index type"""
        try:
            if self.config.index_type == IndexType.HNSW:
                self._initialize_hnsw()
            elif self.config.index_type == IndexType.IVF_FLAT:
                self._initialize_ivf_flat()
            elif self.config.index_type == IndexType.IVF_PQ:
                self._initialize_ivf_pq()
            else:
                # Flat index (exact search)
                self._initialize_flat()
                
            logger.info(f"Initialized {self.config.index_type} index with dimension {self.dimension}")
            
        except Exception as e:
            logger.error(f"Failed to initialize index: {e}")
            # Fallback to flat index
            self._initialize_flat()
    
    def _initialize_hnsw(self):
        """Initialize HNSW index for fast approximate search"""
        try:
            import hnswlib
            
            self.index = hnswlib.Index(space='cosine', dim=self.dimension)
            self.index.init_index(
                max_elements=100000,
                ef_construction=self.config.hnsw_ef_construction,
                M=self.config.hnsw_m
            )
            self.index.set_ef(self.config.hnsw_ef_search)
            
        except ImportError:
            logger.warning("hnswlib not available, falling back to flat index")
            self._initialize_flat()
    
    def _initialize_ivf_flat(self):
        """Initialize IVF-Flat index"""
        # For now, use flat index as placeholder
        # In production, would use Faiss or similar
        logger.warning("IVF-Flat not implemented, using flat index")
        self._initialize_flat()
    
    def _initialize_ivf_pq(self):
        """Initialize IVF-PQ index"""
        # For now, use flat index as placeholder
        # In production, would use Faiss or similar
        logger.warning("IVF-PQ not implemented, using flat index")
        self._initialize_flat()
    
    def _initialize_flat(self):
        """Initialize flat (exact) index"""
        self.index = None  # Use numpy operations directly
    
    def add_vectors(self, vectors: List[np.ndarray], metadata: List[Dict[str, Any]]):
        """Add vectors to the index"""
        with self.lock:
            start_idx = len(self.vectors)
            
            # Store vectors and metadata
            self.vectors.extend(vectors)
            self.metadata.extend(metadata)
            
            # Update ID mapping
            for i, meta in enumerate(metadata):
                vector_id = meta.get('id', str(start_idx + i))
                self.id_to_idx[vector_id] = start_idx + i
            
            # Add to index if using HNSW
            if self.config.index_type == IndexType.HNSW and self.index is not None:
                try:
                    import hnswlib
                    
                    # Convert to numpy array
                    vectors_array = np.array(vectors, dtype=np.float32)
                    ids_array = np.array(range(start_idx, start_idx + len(vectors)))
                    
                    self.index.add_items(vectors_array, ids_array)
                    
                except Exception as e:
                    logger.error(f"Failed to add vectors to HNSW index: {e}")
    
    def search(self, query_vector: np.ndarray, top_k: int, 
               metadata_filter: Optional[Dict[str, Any]] = None) -> Tuple[List[SearchResult], SearchMetrics]:
        """Optimized vector search with performance tracking"""
        start_time = time.time()
        correlation_id = str(uuid.uuid4())
        
        try:
            with self.lock:
                if not self.vectors:
                    return [], SearchMetrics(
                        total_latency_ms=0.0,
                        index_latency_ms=0.0,
                        rerank_latency_ms=0.0,
                        cache_hit=False,
                        results_count=0,
                        correlation_id=correlation_id
                    )
                
                # Perform index search
                index_start = time.time()
                
                if self.config.index_type == IndexType.HNSW and self.index is not None:
                    results = self._search_hnsw(query_vector, top_k, metadata_filter)
                else:
                    results = self._search_flat(query_vector, top_k, metadata_filter)
                
                index_latency_ms = (time.time() - index_start) * 1000
                
                # Apply reranking if enabled
                rerank_start = time.time()
                if self.config.rerank_enabled and len(results) > 1:
                    results = self._apply_reranking(query_vector, results)
                
                rerank_latency_ms = (time.time() - rerank_start) * 1000
                
                # Calculate total latency
                total_latency_ms = (time.time() - start_time) * 1000
                
                # Update performance metrics
                self.search_count += 1
                self.total_search_time += total_latency_ms
                self.latency_percentiles.append(total_latency_ms)
                
                # Keep only recent latencies for percentile calculation
                if len(self.latency_percentiles) > 1000:
                    self.latency_percentiles = self.latency_percentiles[-1000:]
                
                metrics = SearchMetrics(
                    total_latency_ms=total_latency_ms,
                    index_latency_ms=index_latency_ms,
                    rerank_latency_ms=rerank_latency_ms,
                    cache_hit=False,
                    results_count=len(results),
                    correlation_id=correlation_id
                )
                
                logger.debug(
                    f"Vector search completed: {len(results)} results in {total_latency_ms:.2f}ms "
                    f"(index: {index_latency_ms:.2f}ms, rerank: {rerank_latency_ms:.2f}ms)",
                    extra={"correlation_id": correlation_id}
                )
                
                return results, metrics
                
        except Exception as e:
            logger.error(f"Vector search failed: {e}", extra={"correlation_id": correlation_id})
            return [], SearchMetrics(
                total_latency_ms=(time.time() - start_time) * 1000,
                index_latency_ms=0.0,
                rerank_latency_ms=0.0,
                cache_hit=False,
                results_count=0,
                correlation_id=correlation_id
            )
    
    def _search_hnsw(self, query_vector: np.ndarray, top_k: int, 
                     metadata_filter: Optional[Dict[str, Any]] = None) -> List[SearchResult]:
        """Search using HNSW index"""
        try:
            # Get more results for reranking if enabled
            search_k = int(top_k * self.config.rerank_factor) if self.config.rerank_enabled else top_k
            search_k = min(search_k, len(self.vectors))
            
            # Perform HNSW search
            labels, distances = self.index.knn_query(
                query_vector.reshape(1, -1).astype(np.float32), 
                k=search_k
            )
            
            results = []
            for i, (label, distance) in enumerate(zip(labels[0], distances[0])):
                if label >= len(self.metadata):
                    continue
                    
                metadata = self.metadata[label]
                
                # Apply metadata filter
                if metadata_filter and not self._matches_filter(metadata, metadata_filter):
                    continue
                
                # Convert distance to similarity (cosine distance -> cosine similarity)
                similarity = 1.0 - distance
                
                result = SearchResult(
                    id=metadata.get('id', str(label)),
                    score=similarity,
                    metadata=metadata,
                    original_rank=i
                )
                results.append(result)
            
            return results[:top_k] if not self.config.rerank_enabled else results
            
        except Exception as e:
            logger.error(f"HNSW search failed: {e}")
            return []
    
    def _search_flat(self, query_vector: np.ndarray, top_k: int, 
                     metadata_filter: Optional[Dict[str, Any]] = None) -> List[SearchResult]:
        """Search using flat (exact) index"""
        try:
            # Calculate similarities with all vectors
            similarities = []
            
            for i, vector in enumerate(self.vectors):
                # Apply metadata filter first
                if metadata_filter and not self._matches_filter(self.metadata[i], metadata_filter):
                    continue
                
                # Calculate cosine similarity
                similarity = self._cosine_similarity(query_vector, vector)
                similarities.append((i, similarity))
            
            # Sort by similarity (descending)
            similarities.sort(key=lambda x: x[1], reverse=True)
            
            # Get top results
            search_k = int(top_k * self.config.rerank_factor) if self.config.rerank_enabled else top_k
            top_similarities = similarities[:search_k]
            
            results = []
            for rank, (idx, similarity) in enumerate(top_similarities):
                metadata = self.metadata[idx]
                
                result = SearchResult(
                    id=metadata.get('id', str(idx)),
                    score=similarity,
                    metadata=metadata,
                    original_rank=rank
                )
                results.append(result)
            
            return results[:top_k] if not self.config.rerank_enabled else results
            
        except Exception as e:
            logger.error(f"Flat search failed: {e}")
            return []
    
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors"""
        try:
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return dot_product / (norm1 * norm2)
            
        except Exception:
            return 0.0
    
    def _matches_filter(self, metadata: Dict[str, Any], filter_dict: Dict[str, Any]) -> bool:
        """Check if metadata matches filter criteria"""
        try:
            for key, value in filter_dict.items():
                if key not in metadata or metadata[key] != value:
                    return False
            return True
        except Exception:
            return False
    
    def _apply_reranking(self, query_vector: np.ndarray, results: List[SearchResult]) -> List[SearchResult]:
        """Apply reranking to improve result quality"""
        try:
            if len(results) <= 1:
                return results
            
            # For now, implement a simple reranking based on vector similarity refinement
            # In production, this would use a cross-encoder model
            
            reranked_results = []
            
            for result in results:
                # Get the original vector
                idx = self.id_to_idx.get(result.id)
                if idx is None or idx >= len(self.vectors):
                    result.rerank_score = result.score
                    reranked_results.append(result)
                    continue
                
                original_vector = self.vectors[idx]
                
                # Apply more sophisticated similarity calculation
                # This is a placeholder - in production would use cross-encoder
                refined_similarity = self._refined_similarity(query_vector, original_vector, result.metadata)
                
                result.rerank_score = refined_similarity
                reranked_results.append(result)
            
            # Sort by rerank score
            reranked_results.sort(key=lambda x: x.rerank_score or x.score, reverse=True)
            
            # Update final ranks
            for i, result in enumerate(reranked_results):
                result.final_rank = i
            
            return reranked_results
            
        except Exception as e:
            logger.error(f"Reranking failed: {e}")
            return results
    
    def _refined_similarity(self, query_vector: np.ndarray, doc_vector: np.ndarray, 
                           metadata: Dict[str, Any]) -> float:
        """Calculate refined similarity with metadata boost"""
        try:
            # Base cosine similarity
            base_similarity = self._cosine_similarity(query_vector, doc_vector)
            
            # Apply metadata-based boosts
            boost = 1.0
            
            # Boost based on importance
            importance = metadata.get('importance', 5)
            importance_boost = (importance / 10.0) * 0.1  # Up to 10% boost
            boost += importance_boost
            
            # Boost based on recency (if available)
            if 'created_at' in metadata:
                # This would calculate recency boost in production
                recency_boost = 0.05  # Placeholder 5% boost
                boost += recency_boost
            
            # Boost based on tags match (if query had tags)
            # This would be implemented with query context in production
            
            return min(base_similarity * boost, 1.0)
            
        except Exception:
            return self._cosine_similarity(query_vector, doc_vector)
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        if not self.latency_percentiles:
            return {
                "search_count": self.search_count,
                "avg_latency_ms": 0.0,
                "p95_latency_ms": 0.0,
                "p99_latency_ms": 0.0,
                "total_vectors": len(self.vectors)
            }
        
        sorted_latencies = sorted(self.latency_percentiles)
        n = len(sorted_latencies)
        
        return {
            "search_count": self.search_count,
            "avg_latency_ms": sum(sorted_latencies) / n,
            "p50_latency_ms": sorted_latencies[int(n * 0.5)],
            "p95_latency_ms": sorted_latencies[int(n * 0.95)],
            "p99_latency_ms": sorted_latencies[int(n * 0.99)],
            "total_vectors": len(self.vectors),
            "index_type": self.config.index_type.value,
            "rerank_enabled": self.config.rerank_enabled
        }

class VectorOptimizationService:
    """Service for optimized vector operations"""
    
    def __init__(self, config: Optional[VectorSearchConfig] = None):
        self.config = config or VectorSearchConfig()
        self.indexes: Dict[str, OptimizedVectorIndex] = {}
        self.executor = ThreadPoolExecutor(max_workers=self.config.max_workers)

        # Performance tracking
        self.global_metrics = {
            "total_searches": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "avg_latency_ms": 0.0,
            "p95_latency_ms": 0.0,
            "recall_rate": 0.0,
            "mrr_improvement": 0.0
        }

        # Cache storage for query results (LRU with TTL)
        self._cache: "OrderedDict[str, Tuple[float, List[Dict[str, Any]], Dict[str, Any]]]" = OrderedDict()
        self._cache_lock = threading.RLock()

        # Maintain rolling latency history for percentile calculations
        self._latency_history = deque(maxlen=1000)

    def get_or_create_index(self, collection_name: str, dimension: int) -> OptimizedVectorIndex:
        """Get or create an optimized index for a collection"""
        if collection_name not in self.indexes:
            self.indexes[collection_name] = OptimizedVectorIndex(self.config, dimension)

        return self.indexes[collection_name]

    def _cache_operational(self) -> bool:
        """Return True if caching is enabled and properly configured."""
        return (
            self.config.cache_enabled
            and self.config.cache_size > 0
            and self.config.cache_ttl_seconds > 0
        )

    def _normalize_query_vector(
        self, query_vector: Union[List[float], np.ndarray]
    ) -> np.ndarray:
        """Ensure query vectors are numpy float32 arrays."""
        if isinstance(query_vector, list):
            query_vector = np.array(query_vector, dtype=np.float32)
        elif not isinstance(query_vector, np.ndarray):
            query_vector = np.array(query_vector, dtype=np.float32)
        elif query_vector.dtype != np.float32:
            query_vector = query_vector.astype(np.float32)

        return np.ascontiguousarray(query_vector)

    def _make_cache_key(
        self,
        collection_name: str,
        query_vector: np.ndarray,
        top_k: int,
        metadata_filter: Optional[Dict[str, Any]]
    ) -> Optional[str]:
        """Create a stable cache key for the provided query."""
        if not self._cache_operational():
            return None

        try:
            vector_hash = hashlib.sha1(query_vector.tobytes()).hexdigest()
            filter_repr = ""
            if metadata_filter:
                filter_repr = json.dumps(metadata_filter, sort_keys=True, default=str)

            return f"{collection_name}:{top_k}:{vector_hash}:{filter_repr}"
        except Exception:
            return None

    def _snapshot_results(self, results: List[SearchResult]) -> List[Dict[str, Any]]:
        """Create a serializable snapshot of search results."""
        snapshot: List[Dict[str, Any]] = []
        for result in results:
            snapshot.append(
                {
                    "id": result.id,
                    "score": result.score,
                    "metadata": dict(result.metadata),
                    "rerank_score": result.rerank_score,
                    "original_rank": result.original_rank,
                    "final_rank": result.final_rank,
                }
            )
        return snapshot

    def _hydrate_results(self, snapshot: List[Dict[str, Any]]) -> List[SearchResult]:
        """Restore SearchResult objects from cached snapshots."""
        hydrated: List[SearchResult] = []
        for entry in snapshot:
            hydrated.append(
                SearchResult(
                    id=entry["id"],
                    score=entry["score"],
                    metadata=dict(entry["metadata"]),
                    rerank_score=entry.get("rerank_score"),
                    original_rank=entry.get("original_rank"),
                    final_rank=entry.get("final_rank"),
                )
            )
        return hydrated

    def _evict_expired_locked(self, now: Optional[float] = None) -> None:
        """Remove expired cache entries. Caller must hold cache lock."""
        if not self._cache:
            return

        ttl = self.config.cache_ttl_seconds
        if ttl <= 0:
            self._cache.clear()
            return

        now = now or time.time()
        keys_to_delete = [
            key for key, (timestamp, _, _) in self._cache.items()
            if now - timestamp > ttl
        ]

        for key in keys_to_delete:
            self._cache.pop(key, None)

    def _get_from_cache(
        self, cache_key: Optional[str]
    ) -> Optional[Tuple[List[SearchResult], Dict[str, Any]]]:
        """Retrieve cached search results if available."""
        if not cache_key or not self._cache_operational():
            return None

        with self._cache_lock:
            self._evict_expired_locked()
            if cache_key not in self._cache:
                return None

            timestamp, snapshot, metrics_snapshot = self._cache.pop(cache_key)
            # Reinsert to maintain LRU ordering
            self._cache[cache_key] = (timestamp, snapshot, metrics_snapshot)

            return self._hydrate_results(snapshot), metrics_snapshot

    def _store_in_cache(
        self,
        cache_key: Optional[str],
        results: List[SearchResult],
        metrics: SearchMetrics
    ) -> None:
        """Persist search results to the cache."""
        if not cache_key or not self._cache_operational():
            return

        with self._cache_lock:
            self._evict_expired_locked()
            snapshot = self._snapshot_results(results)
            metrics_snapshot = {
                "recall_rate": metrics.recall_rate,
                "mrr_score": metrics.mrr_score,
            }

            self._cache[cache_key] = (time.time(), snapshot, metrics_snapshot)

            while len(self._cache) > self.config.cache_size:
                self._cache.popitem(last=False)

    def _update_latency_metrics(self, latency_ms: float) -> None:
        """Update rolling latency statistics."""
        self._latency_history.append(latency_ms)
        if not self._latency_history:
            return

        sorted_latencies = sorted(self._latency_history)
        index = int(len(sorted_latencies) * 0.95)
        index = min(max(index, 0), len(sorted_latencies) - 1)
        self.global_metrics["p95_latency_ms"] = sorted_latencies[index]

    def _record_search_metrics(self, metrics: SearchMetrics, cache_hit: bool) -> None:
        """Record global metrics after a search operation."""
        latency_ms = metrics.total_latency_ms

        self.global_metrics["total_searches"] += 1
        if cache_hit:
            self.global_metrics["cache_hits"] += 1
        else:
            self.global_metrics["cache_misses"] += 1

        alpha = 0.1  # Exponential moving average factor
        self.global_metrics["avg_latency_ms"] = (
            self.global_metrics["avg_latency_ms"] * (1 - alpha)
            + latency_ms * alpha
        )

        self._update_latency_metrics(latency_ms)

        if metrics.recall_rate is not None:
            self.global_metrics["recall_rate"] = (
                self.global_metrics["recall_rate"] * (1 - alpha)
                + metrics.recall_rate * alpha
            )

        if metrics.mrr_score is not None:
            self.global_metrics["mrr_improvement"] = (
                self.global_metrics["mrr_improvement"] * (1 - alpha)
                + metrics.mrr_score * alpha
            )
    
    async def search_optimized(
        self,
        collection_name: str,
        query_vector: Union[List[float], np.ndarray],
        top_k: int = 10,
        metadata_filter: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None
    ) -> Tuple[List[SearchResult], SearchMetrics]:
        """Perform optimized vector search"""
        correlation_id = correlation_id or str(uuid.uuid4())

        try:
            request_start = time.time()

            # Convert query vector to numpy array
            query_vector = self._normalize_query_vector(query_vector)

            cache_key = self._make_cache_key(collection_name, query_vector, top_k, metadata_filter)
            cached = self._get_from_cache(cache_key)

            if cached:
                cached_results, cached_metrics = cached
                total_latency_ms = (time.time() - request_start) * 1000

                metrics = SearchMetrics(
                    total_latency_ms=total_latency_ms,
                    index_latency_ms=0.0,
                    rerank_latency_ms=0.0,
                    cache_hit=True,
                    results_count=len(cached_results),
                    recall_rate=cached_metrics.get("recall_rate"),
                    mrr_score=cached_metrics.get("mrr_score"),
                    correlation_id=correlation_id
                )

                self._record_search_metrics(metrics, cache_hit=True)

                logger.debug(
                    "Returning cached optimized search results",
                    extra={"correlation_id": correlation_id}
                )

                return cached_results, metrics

            # Get the index
            if collection_name not in self.indexes:
                logger.warning(f"Index not found for collection: {collection_name}")
                return [], SearchMetrics(
                    total_latency_ms=0.0,
                    index_latency_ms=0.0,
                    rerank_latency_ms=0.0,
                    cache_hit=False,
                    results_count=0,
                    correlation_id=correlation_id
                )
            
            index = self.indexes[collection_name]

            # Perform search
            results, metrics = index.search(query_vector, top_k, metadata_filter)

            # Persist in cache for future lookups
            self._store_in_cache(cache_key, results, metrics)

            # Update global metrics
            self._record_search_metrics(metrics, cache_hit=False)

            logger.info(
                f"Optimized search completed: {len(results)} results in {metrics.total_latency_ms:.2f}ms",
                extra={"correlation_id": correlation_id}
            )
            
            return results, metrics
            
        except Exception as e:
            logger.error(f"Optimized search failed: {e}", extra={"correlation_id": correlation_id})
            return [], SearchMetrics(
                total_latency_ms=0.0,
                index_latency_ms=0.0,
                rerank_latency_ms=0.0,
                cache_hit=False,
                results_count=0,
                correlation_id=correlation_id
            )
    
    async def add_vectors_batch(
        self,
        collection_name: str,
        vectors: List[Union[List[float], np.ndarray]],
        metadata: List[Dict[str, Any]],
        dimension: int
    ) -> bool:
        """Add vectors to index in batch"""
        try:
            # Convert vectors to numpy arrays
            np_vectors = []
            for vector in vectors:
                if isinstance(vector, list):
                    np_vectors.append(np.array(vector, dtype=np.float32))
                else:
                    np_vectors.append(vector.astype(np.float32))
            
            # Get or create index
            index = self.get_or_create_index(collection_name, dimension)
            
            # Add vectors
            index.add_vectors(np_vectors, metadata)
            
            logger.info(f"Added {len(vectors)} vectors to index {collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add vectors to index: {e}")
            return False
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report"""
        report = {
            "global_metrics": self.global_metrics.copy(),
            "indexes": {}
        }
        
        for collection_name, index in self.indexes.items():
            report["indexes"][collection_name] = index.get_performance_stats()
        
        # Calculate overall p95 latency
        all_latencies = []
        for index in self.indexes.values():
            all_latencies.extend(index.latency_percentiles)
        
        if all_latencies:
            sorted_latencies = sorted(all_latencies)
            n = len(sorted_latencies)
            report["global_metrics"]["p95_latency_ms"] = sorted_latencies[int(n * 0.95)]
            
            # Check if we're meeting SLO targets
            report["slo_compliance"] = {
                "p95_latency_target_ms": self.config.target_p95_latency_ms,
                "p95_latency_actual_ms": report["global_metrics"]["p95_latency_ms"],
                "p95_latency_met": report["global_metrics"]["p95_latency_ms"] <= self.config.target_p95_latency_ms,
                "recall_target": self.config.target_recall_rate,
                "recall_actual": report["global_metrics"]["recall_rate"],
                "recall_met": report["global_metrics"]["recall_rate"] >= self.config.target_recall_rate,
                "mrr_improvement_target": self.config.target_mrr_improvement,
                "mrr_improvement_actual": report["global_metrics"]["mrr_improvement"],
                "mrr_improvement_met": report["global_metrics"]["mrr_improvement"] >= self.config.target_mrr_improvement
            }
        
        return report
    
    async def benchmark_performance(
        self,
        collection_name: str,
        test_queries: List[Union[List[float], np.ndarray]],
        ground_truth: Optional[List[List[str]]] = None
    ) -> Dict[str, Any]:
        """Benchmark search performance"""
        if collection_name not in self.indexes:
            return {"error": "Index not found"}
        
        results = {
            "total_queries": len(test_queries),
            "latencies": [],
            "recall_rates": [],
            "mrr_scores": []
        }
        
        for i, query in enumerate(test_queries):
            search_results, metrics = await self.search_optimized(
                collection_name, query, top_k=10
            )
            
            results["latencies"].append(metrics.total_latency_ms)
            
            # Calculate recall if ground truth provided
            if ground_truth and i < len(ground_truth):
                true_results = set(ground_truth[i])
                retrieved_results = set(r.id for r in search_results)
                
                if true_results:
                    recall = len(true_results.intersection(retrieved_results)) / len(true_results)
                    results["recall_rates"].append(recall)
                    
                    # Calculate MRR
                    mrr = 0.0
                    for rank, result_id in enumerate([r.id for r in search_results]):
                        if result_id in true_results:
                            mrr = 1.0 / (rank + 1)
                            break
                    results["mrr_scores"].append(mrr)
        
        # Calculate summary statistics
        if results["latencies"]:
            sorted_latencies = sorted(results["latencies"])
            n = len(sorted_latencies)
            
            results["summary"] = {
                "avg_latency_ms": sum(sorted_latencies) / n,
                "p50_latency_ms": sorted_latencies[int(n * 0.5)],
                "p95_latency_ms": sorted_latencies[int(n * 0.95)],
                "p99_latency_ms": sorted_latencies[int(n * 0.99)],
                "avg_recall": sum(results["recall_rates"]) / len(results["recall_rates"]) if results["recall_rates"] else 0.0,
                "avg_mrr": sum(results["mrr_scores"]) / len(results["mrr_scores"]) if results["mrr_scores"] else 0.0
            }
        
        return results

# Global instance
_vector_optimization_service: Optional[VectorOptimizationService] = None

def get_vector_optimization_service(config: Optional[VectorSearchConfig] = None) -> VectorOptimizationService:
    """Get the global vector optimization service instance"""
    global _vector_optimization_service
    
    if _vector_optimization_service is None:
        _vector_optimization_service = VectorOptimizationService(config)

    return _vector_optimization_service
