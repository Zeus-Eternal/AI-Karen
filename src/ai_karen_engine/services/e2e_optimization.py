"""
End-to-End Performance Optimization - Task 8.3
Optimizes complete turn pipeline to achieve p95 latency < 3 seconds
with caching strategies, connection pooling, and resource optimization.
"""

import asyncio
import json
import logging
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, AsyncIterator, Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)


class CacheType(str, Enum):
    """Types of caches in the system"""

    MEMORY = "memory"  # Memory query results
    LLM_RESPONSE = "llm_response"  # LLM generation results
    EMBEDDING = "embedding"  # Text embeddings
    CONTEXT = "context"  # Built conversation contexts


class OptimizationLevel(str, Enum):
    """Optimization levels for different scenarios"""

    CONSERVATIVE = "conservative"  # Safe optimizations
    AGGRESSIVE = "aggressive"  # Maximum performance
    BALANCED = "balanced"  # Balance of safety and performance


@dataclass
class E2ERequest:
    """End-to-end request model"""

    user_id: str
    query: str
    conversation_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    stream: bool = True
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class E2EResponse:
    """End-to-end response model"""

    response: str
    context_used: List[Dict[str, Any]]
    total_latency_ms: float
    memory_latency_ms: float
    llm_latency_ms: float
    cache_hits: Dict[str, bool]
    correlation_id: str


@dataclass
class E2EMetrics:
    """End-to-end performance metrics"""

    correlation_id: str
    total_latency_ms: float
    memory_query_latency_ms: float
    context_build_latency_ms: float
    llm_generation_latency_ms: float
    first_token_latency_ms: float
    tokens_generated: int
    cache_hits: Dict[str, bool]
    memory_results_count: int
    context_tokens_estimate: int
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)


class ConnectionPool:
    """Connection pool for database and external services"""

    def __init__(self, max_connections: int = 20, timeout_seconds: float = 30.0):
        self.max_connections = max_connections
        self.timeout_seconds = timeout_seconds
        self.active_connections = 0
        self.semaphore = asyncio.Semaphore(max_connections)
        self.lock = threading.RLock()

        # Connection health tracking
        self.connection_metrics = {
            "total_acquired": 0,
            "total_released": 0,
            "active_count": 0,
            "timeout_count": 0,
            "error_count": 0,
        }

    async def acquire(self, correlation_id: Optional[str] = None) -> bool:
        """Acquire a connection from the pool"""
        try:
            # Wait for available connection with timeout
            await asyncio.wait_for(
                self.semaphore.acquire(), timeout=self.timeout_seconds
            )

            with self.lock:
                self.active_connections += 1
                self.connection_metrics["total_acquired"] += 1
                self.connection_metrics["active_count"] = self.active_connections

            return True

        except asyncio.TimeoutError:
            with self.lock:
                self.connection_metrics["timeout_count"] += 1

            logger.warning(
                f"Connection pool timeout after {self.timeout_seconds}s",
                extra={"correlation_id": correlation_id},
            )
            return False

        except Exception as e:
            with self.lock:
                self.connection_metrics["error_count"] += 1

            logger.error(
                f"Connection pool error: {e}", extra={"correlation_id": correlation_id}
            )
            return False

    def release(self, correlation_id: Optional[str] = None):
        """Release a connection back to the pool"""
        try:
            with self.lock:
                if self.active_connections > 0:
                    self.active_connections -= 1
                    self.connection_metrics["total_released"] += 1
                    self.connection_metrics["active_count"] = self.active_connections

            self.semaphore.release()

        except Exception as e:
            logger.error(
                f"Connection release error: {e}",
                extra={"correlation_id": correlation_id},
            )

    def get_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics"""
        with self.lock:
            return {
                "max_connections": self.max_connections,
                "active_connections": self.active_connections,
                "utilization": self.active_connections / self.max_connections,
                "metrics": self.connection_metrics.copy(),
            }


class HotQueryCache:
    """Cache for frequently accessed queries and contexts"""

    def __init__(self, max_size: int = 5000, ttl_seconds: int = 1800):  # 30 minutes
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.caches: Dict[CacheType, Dict[str, Dict[str, Any]]] = {
            cache_type: {} for cache_type in CacheType
        }
        self.access_times: Dict[CacheType, Dict[str, float]] = {
            cache_type: {} for cache_type in CacheType
        }
        self.lock = threading.RLock()

        # Cache statistics
        self.stats = {
            cache_type.value: {"hits": 0, "misses": 0, "evictions": 0, "size": 0}
            for cache_type in CacheType
        }

    def _generate_key(self, cache_type: CacheType, **kwargs) -> str:
        """Generate cache key for given parameters"""
        if cache_type == CacheType.MEMORY:
            return f"mem:{kwargs.get('user_id', '')}:{hash(kwargs.get('query', ''))}"
        elif cache_type == CacheType.LLM_RESPONSE:
            return f"llm:{kwargs.get('model', '')}:{hash(kwargs.get('prompt', ''))}"
        elif cache_type == CacheType.EMBEDDING:
            return f"emb:{hash(kwargs.get('text', ''))}"
        elif cache_type == CacheType.CONTEXT:
            return f"ctx:{kwargs.get('user_id', '')}:{hash(kwargs.get('query', ''))}"
        else:
            return f"unknown:{hash(str(kwargs))}"

    def get(self, cache_type: CacheType, **kwargs) -> Optional[Any]:
        """Get cached value if available and not expired"""
        cache_key = self._generate_key(cache_type, **kwargs)

        with self.lock:
            cache = self.caches[cache_type]

            if cache_key not in cache:
                self.stats[cache_type.value]["misses"] += 1
                return None

            cached_data = cache[cache_key]
            cache_time = cached_data.get("timestamp", 0)

            # Check if expired
            if time.time() - cache_time > self.ttl_seconds:
                del cache[cache_key]
                self.access_times[cache_type].pop(cache_key, None)
                self.stats[cache_type.value]["misses"] += 1
                self.stats[cache_type.value]["size"] = len(cache)
                return None

            # Update access time
            self.access_times[cache_type][cache_key] = time.time()
            self.stats[cache_type.value]["hits"] += 1

            return cached_data.get("value")

    def put(self, cache_type: CacheType, value: Any, **kwargs):
        """Cache a value"""
        cache_key = self._generate_key(cache_type, **kwargs)

        with self.lock:
            cache = self.caches[cache_type]

            # Evict old entries if cache is full
            if len(cache) >= self.max_size:
                self._evict_oldest(cache_type)

            cache[cache_key] = {"value": value, "timestamp": time.time()}
            self.access_times[cache_type][cache_key] = time.time()
            self.stats[cache_type.value]["size"] = len(cache)

    def _evict_oldest(self, cache_type: CacheType):
        """Evict the oldest cache entry for a specific cache type"""
        access_times = self.access_times[cache_type]
        cache = self.caches[cache_type]

        if not access_times:
            return

        oldest_key = min(access_times.keys(), key=lambda k: access_times[k])
        cache.pop(oldest_key, None)
        access_times.pop(oldest_key, None)
        self.stats[cache_type.value]["evictions"] += 1

    def clear(self, cache_type: Optional[CacheType] = None):
        """Clear cache(s)"""
        with self.lock:
            if cache_type:
                self.caches[cache_type].clear()
                self.access_times[cache_type].clear()
                self.stats[cache_type.value]["size"] = 0
            else:
                for ct in CacheType:
                    self.caches[ct].clear()
                    self.access_times[ct].clear()
                    self.stats[ct.value]["size"] = 0

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self.lock:
            total_stats = {
                "total_size": sum(len(cache) for cache in self.caches.values()),
                "max_size": self.max_size,
                "ttl_seconds": self.ttl_seconds,
                "by_type": self.stats.copy(),
            }

            # Calculate hit rates
            for cache_type_str, stats in total_stats["by_type"].items():
                total_requests = stats["hits"] + stats["misses"]
                stats["hit_rate"] = stats["hits"] / max(total_requests, 1)

            return total_stats


class E2EOptimizationService:
    """End-to-end optimization service for complete turn pipeline"""

    def __init__(
        self,
        optimization_level: OptimizationLevel = OptimizationLevel.BALANCED,
        max_connections: int = 20,
        cache_size: int = 5000,
        cache_ttl_seconds: int = 1800,
    ):
        self.optimization_level = optimization_level
        self.connection_pool = ConnectionPool(max_connections)
        self.hot_cache = HotQueryCache(cache_size, cache_ttl_seconds)

        # Performance targets
        self.performance_targets = {
            "total_latency_p95_ms": 3000.0,  # 3 seconds
            "memory_latency_p95_ms": 50.0,  # 50ms
            "llm_first_token_p95_ms": 1200.0,  # 1.2 seconds
            "cache_hit_rate_target": 0.4,  # 40% cache hit rate
        }

        # Metrics tracking
        self.metrics_history: List[E2EMetrics] = []
        self.executor = ThreadPoolExecutor(max_workers=10)

        # Service dependencies (will be injected)
        self.vector_service = None
        self.llm_service = None
        self.memory_service = None

        # Background optimization tasks
        self._optimization_tasks: List[asyncio.Task] = []
        self._background_tasks_started = False

    def set_services(self, vector_service=None, llm_service=None, memory_service=None):
        """Inject service dependencies"""
        if vector_service:
            self.vector_service = vector_service
        if llm_service:
            self.llm_service = llm_service
        if memory_service:
            self.memory_service = memory_service

    async def start_background_tasks(self):
        """Start background optimization tasks (call when event loop is available)"""
        if not self._background_tasks_started:
            try:
                # Cache warming task
                self._optimization_tasks.append(
                    asyncio.create_task(self._cache_warming_loop())
                )

                # Performance monitoring task
                self._optimization_tasks.append(
                    asyncio.create_task(self._performance_monitoring_loop())
                )

                # Connection pool monitoring task
                self._optimization_tasks.append(
                    asyncio.create_task(self._connection_monitoring_loop())
                )

                self._background_tasks_started = True
                logger.info("Background optimization tasks started")

            except Exception as e:
                logger.error(f"Failed to start background tasks: {e}")

    async def stop_background_tasks(self):
        """Stop background optimization tasks"""
        for task in self._optimization_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        self._optimization_tasks.clear()
        self._background_tasks_started = False
        logger.info("Background optimization tasks stopped")

    def _start_background_tasks(self):
        """Start background optimization tasks"""
        # Cache warming task
        self._optimization_tasks.append(asyncio.create_task(self._cache_warming_loop()))

        # Performance monitoring task
        self._optimization_tasks.append(
            asyncio.create_task(self._performance_monitoring_loop())
        )

        # Connection pool monitoring task
        self._optimization_tasks.append(
            asyncio.create_task(self._connection_monitoring_loop())
        )

    async def process_e2e_request(
        self, request: E2ERequest, tenant_id: Union[str, uuid.UUID]
    ) -> AsyncIterator[str]:
        """
        Process end-to-end request with full optimization pipeline
        """
        start_time = time.time()
        correlation_id = request.correlation_id

        # Initialize metrics
        metrics = E2EMetrics(
            correlation_id=correlation_id,
            total_latency_ms=0.0,
            memory_query_latency_ms=0.0,
            context_build_latency_ms=0.0,
            llm_generation_latency_ms=0.0,
            first_token_latency_ms=0.0,
            tokens_generated=0,
            cache_hits={},
            memory_results_count=0,
            context_tokens_estimate=0,
        )

        try:
            # Acquire connection from pool
            if not await self.connection_pool.acquire(correlation_id):
                raise RuntimeError("Connection pool exhausted")

            try:
                # Step 1: Memory query with caching
                memory_start = time.time()
                memory_results, memory_cache_hit = await self._optimized_memory_query(
                    request, tenant_id, correlation_id
                )
                metrics.memory_query_latency_ms = (time.time() - memory_start) * 1000
                metrics.memory_results_count = len(memory_results)
                metrics.cache_hits["memory"] = memory_cache_hit

                # Step 2: Context building with caching
                context_start = time.time()
                context, context_cache_hit = await self._optimized_context_building(
                    request, memory_results, correlation_id
                )
                metrics.context_build_latency_ms = (time.time() - context_start) * 1000
                metrics.context_tokens_estimate = (
                    len(str(context)) // 4
                )  # Rough estimate
                metrics.cache_hits["context"] = context_cache_hit

                # Step 3: LLM generation with optimization
                llm_start = time.time()
                first_token_time = None
                tokens_generated = 0

                async for chunk in self._optimized_llm_generation(
                    request, context, correlation_id
                ):
                    if first_token_time is None:
                        first_token_time = time.time()
                        metrics.first_token_latency_ms = (
                            first_token_time - llm_start
                        ) * 1000

                    tokens_generated += 1
                    yield chunk

                metrics.llm_generation_latency_ms = (time.time() - llm_start) * 1000
                metrics.tokens_generated = tokens_generated

                # Calculate total latency
                metrics.total_latency_ms = (time.time() - start_time) * 1000

                # Record metrics
                self._record_e2e_metrics(metrics)

                logger.info(
                    f"E2E request completed: {metrics.total_latency_ms:.2f}ms total "
                    f"(memory: {metrics.memory_query_latency_ms:.2f}ms, "
                    f"context: {metrics.context_build_latency_ms:.2f}ms, "
                    f"llm: {metrics.llm_generation_latency_ms:.2f}ms, "
                    f"first-token: {metrics.first_token_latency_ms:.2f}ms)",
                    extra={"correlation_id": correlation_id},
                )

            finally:
                # Always release connection
                self.connection_pool.release(correlation_id)

        except Exception as e:
            metrics.error = str(e)
            metrics.total_latency_ms = (time.time() - start_time) * 1000
            self._record_e2e_metrics(metrics)

            logger.error(
                f"E2E request failed: {e}", extra={"correlation_id": correlation_id}
            )
            raise

    async def _optimized_memory_query(
        self, request: E2ERequest, tenant_id: Union[str, uuid.UUID], correlation_id: str
    ) -> Tuple[List[Dict[str, Any]], bool]:
        """Optimized memory query with caching"""
        # Check cache first
        cached_results = self.hot_cache.get(
            CacheType.MEMORY, user_id=request.user_id, query=request.query
        )

        if cached_results is not None:
            logger.debug(f"Memory cache hit", extra={"correlation_id": correlation_id})
            return cached_results, True

        # Query memory service
        if self.memory_service:
            try:
                # Use the optimized memory service if available
                from ai_karen_engine.services.unified_memory_service import (
                    MemoryQueryRequest,
                )

                memory_request = MemoryQueryRequest(
                    user_id=request.user_id,
                    query=request.query,
                    top_k=10,
                    similarity_threshold=0.7,
                )

                response = await self.memory_service.query(
                    tenant_id, memory_request, correlation_id
                )

                # Convert to simple format for caching
                results = [
                    {
                        "id": hit.id,
                        "text": hit.text,
                        "score": hit.score,
                        "tags": hit.tags,
                        "importance": hit.importance,
                    }
                    for hit in response.hits
                ]

                # Cache the results
                self.hot_cache.put(
                    CacheType.MEMORY,
                    results,
                    user_id=request.user_id,
                    query=request.query,
                )

                return results, False

            except Exception as e:
                logger.error(
                    f"Memory service error: {e}",
                    extra={"correlation_id": correlation_id},
                )
                return [], False

        # Fallback: return empty results
        return [], False

    async def _optimized_context_building(
        self,
        request: E2ERequest,
        memory_results: List[Dict[str, Any]],
        correlation_id: str,
    ) -> Tuple[Dict[str, Any], bool]:
        """Optimized context building with caching"""
        # Check cache first
        cached_context = self.hot_cache.get(
            CacheType.CONTEXT, user_id=request.user_id, query=request.query
        )

        if cached_context is not None:
            logger.debug(f"Context cache hit", extra={"correlation_id": correlation_id})
            return cached_context, True

        # Build context from memory results
        context = {
            "query": request.query,
            "user_id": request.user_id,
            "conversation_id": request.conversation_id,
            "memories": memory_results[:5],  # Top 5 memories
            "context_metadata": {
                "total_memories": len(memory_results),
                "generated_at": datetime.utcnow().isoformat(),
            },
        }

        # Add conversation context if available
        if request.context:
            context["conversation_context"] = request.context

        # Cache the context
        self.hot_cache.put(
            CacheType.CONTEXT, context, user_id=request.user_id, query=request.query
        )

        return context, False

    async def _optimized_llm_generation(
        self, request: E2ERequest, context: Dict[str, Any], correlation_id: str
    ) -> AsyncIterator[str]:
        """Optimized LLM generation with caching and streaming"""
        # For streaming requests, we can't cache the full response
        # But we can optimize the generation process

        if self.llm_service:
            try:
                # Use the optimized LLM service
                async for chunk in self.llm_service.generate_optimized(
                    prompt=self._build_prompt(request.query, context),
                    stream=request.stream,
                    max_tokens=request.max_tokens,
                    temperature=request.temperature,
                    correlation_id=correlation_id,
                ):
                    yield chunk

            except Exception as e:
                logger.error(
                    f"LLM service error: {e}", extra={"correlation_id": correlation_id}
                )
                yield f"I apologize, but I encountered an error processing your request: {str(e)}"
        else:
            # Fallback response
            yield "I'm processing your request, but the LLM service is not available."

    def _build_prompt(self, query: str, context: Dict[str, Any]) -> str:
        """Build optimized prompt from query and context"""
        memories = context.get("memories", [])

        if not memories:
            return f"User query: {query}\n\nPlease provide a helpful response."

        # Build context from memories
        context_parts = []
        for memory in memories:
            context_parts.append(f"- {memory.get('text', '')}")

        context_text = "\n".join(context_parts)

        prompt = f"""Based on the following context, please answer the user's query:

Context:
{context_text}

User query: {query}

Please provide a helpful and accurate response based on the context provided."""

        return prompt

    def _record_e2e_metrics(self, metrics: E2EMetrics):
        """Record end-to-end metrics"""
        self.metrics_history.append(metrics)

        # Keep only recent metrics (last 1000)
        if len(self.metrics_history) > 1000:
            self.metrics_history = self.metrics_history[-1000:]

    async def _cache_warming_loop(self):
        """Background task for cache warming"""
        while True:
            try:
                await asyncio.sleep(300)  # Every 5 minutes
                await self._warm_hot_caches()
            except Exception as e:
                logger.error(f"Cache warming error: {e}")

    async def _warm_hot_caches(self):
        """Warm up caches with frequently accessed data"""
        try:
            # This would analyze recent queries and pre-populate caches
            # For now, just log the cache warming attempt
            logger.debug("Cache warming cycle started")

            # Get cache stats
            cache_stats = self.hot_cache.get_stats()

            # If hit rate is low, we might want to adjust caching strategy
            for cache_type, stats in cache_stats["by_type"].items():
                if stats["hit_rate"] < 0.2:  # Less than 20% hit rate
                    logger.info(
                        f"Low hit rate for {cache_type}: {stats['hit_rate']:.2%}"
                    )

            logger.debug("Cache warming cycle completed")

        except Exception as e:
            logger.error(f"Cache warming failed: {e}")

    async def _performance_monitoring_loop(self):
        """Background task for performance monitoring"""
        while True:
            try:
                await asyncio.sleep(60)  # Every minute
                await self._check_performance_targets()
            except Exception as e:
                logger.error(f"Performance monitoring error: {e}")

    async def _check_performance_targets(self):
        """Check if performance targets are being met"""
        if len(self.metrics_history) < 10:
            return  # Not enough data

        # Get recent metrics
        recent_metrics = self.metrics_history[-100:]  # Last 100 requests

        # Calculate p95 latencies
        total_latencies = [
            m.total_latency_ms for m in recent_metrics if m.error is None
        ]
        memory_latencies = [
            m.memory_query_latency_ms for m in recent_metrics if m.error is None
        ]
        first_token_latencies = [
            m.first_token_latency_ms
            for m in recent_metrics
            if m.error is None and m.first_token_latency_ms > 0
        ]

        if total_latencies:
            sorted_total = sorted(total_latencies)
            p95_total = sorted_total[int(len(sorted_total) * 0.95)]

            target = self.performance_targets["total_latency_p95_ms"]

            if p95_total > target:
                logger.warning(
                    f"E2E latency SLO violation: {p95_total:.2f}ms > {target}ms"
                )
            else:
                logger.debug(f"E2E latency SLO met: {p95_total:.2f}ms <= {target}ms")

        if memory_latencies:
            sorted_memory = sorted(memory_latencies)
            p95_memory = sorted_memory[int(len(sorted_memory) * 0.95)]

            target = self.performance_targets["memory_latency_p95_ms"]

            if p95_memory > target:
                logger.warning(
                    f"Memory latency SLO violation: {p95_memory:.2f}ms > {target}ms"
                )

        if first_token_latencies:
            sorted_ft = sorted(first_token_latencies)
            p95_ft = sorted_ft[int(len(sorted_ft) * 0.95)]

            target = self.performance_targets["llm_first_token_p95_ms"]

            if p95_ft > target:
                logger.warning(
                    f"First token latency SLO violation: {p95_ft:.2f}ms > {target}ms"
                )

    async def _connection_monitoring_loop(self):
        """Background task for connection pool monitoring"""
        while True:
            try:
                await asyncio.sleep(30)  # Every 30 seconds
                self._monitor_connection_pool()
            except Exception as e:
                logger.error(f"Connection monitoring error: {e}")

    def _monitor_connection_pool(self):
        """Monitor connection pool health"""
        stats = self.connection_pool.get_stats()

        # Log warnings if utilization is high
        if stats["utilization"] > 0.8:
            logger.warning(
                f"High connection pool utilization: {stats['utilization']:.1%}"
            )

        # Log errors if there are timeouts
        if stats["metrics"]["timeout_count"] > 0:
            logger.warning(
                f"Connection pool timeouts: {stats['metrics']['timeout_count']}"
            )

    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report"""
        if not self.metrics_history:
            return {"error": "No metrics available"}

        recent_metrics = self.metrics_history[-100:]

        # Calculate statistics
        total_latencies = [
            m.total_latency_ms for m in recent_metrics if m.error is None
        ]
        memory_latencies = [
            m.memory_query_latency_ms for m in recent_metrics if m.error is None
        ]
        context_latencies = [
            m.context_build_latency_ms for m in recent_metrics if m.error is None
        ]
        llm_latencies = [
            m.llm_generation_latency_ms for m in recent_metrics if m.error is None
        ]
        first_token_latencies = [
            m.first_token_latency_ms
            for m in recent_metrics
            if m.error is None and m.first_token_latency_ms > 0
        ]

        # Cache hit rates
        memory_cache_hits = sum(
            1 for m in recent_metrics if m.cache_hits.get("memory", False)
        )
        context_cache_hits = sum(
            1 for m in recent_metrics if m.cache_hits.get("context", False)
        )
        total_requests = len(recent_metrics)

        errors = sum(1 for m in recent_metrics if m.error is not None)

        report = {
            "summary": {
                "total_requests": total_requests,
                "error_rate": errors / max(total_requests, 1),
                "memory_cache_hit_rate": memory_cache_hits / max(total_requests, 1),
                "context_cache_hit_rate": context_cache_hits / max(total_requests, 1),
            },
            "latency_metrics": {},
            "slo_compliance": {},
            "cache_stats": self.hot_cache.get_stats(),
            "connection_pool_stats": self.connection_pool.get_stats(),
        }

        # Latency metrics
        if total_latencies:
            sorted_total = sorted(total_latencies)
            report["latency_metrics"]["total"] = {
                "avg_ms": sum(sorted_total) / len(sorted_total),
                "p50_ms": sorted_total[int(len(sorted_total) * 0.5)],
                "p95_ms": sorted_total[int(len(sorted_total) * 0.95)],
                "p99_ms": sorted_total[int(len(sorted_total) * 0.99)],
                "max_ms": max(sorted_total),
                "min_ms": min(sorted_total),
            }

        if memory_latencies:
            sorted_memory = sorted(memory_latencies)
            report["latency_metrics"]["memory"] = {
                "avg_ms": sum(sorted_memory) / len(sorted_memory),
                "p95_ms": sorted_memory[int(len(sorted_memory) * 0.95)],
            }

        if first_token_latencies:
            sorted_ft = sorted(first_token_latencies)
            report["latency_metrics"]["first_token"] = {
                "avg_ms": sum(sorted_ft) / len(sorted_ft),
                "p95_ms": sorted_ft[int(len(sorted_ft) * 0.95)],
            }

        # SLO compliance
        if total_latencies:
            p95_total = sorted(total_latencies)[int(len(total_latencies) * 0.95)]
            report["slo_compliance"]["total_latency"] = {
                "target_ms": self.performance_targets["total_latency_p95_ms"],
                "actual_p95_ms": p95_total,
                "is_met": p95_total <= self.performance_targets["total_latency_p95_ms"],
            }

        return report

    async def benchmark_e2e_performance(
        self, test_requests: List[E2ERequest], tenant_id: Union[str, uuid.UUID]
    ) -> Dict[str, Any]:
        """Benchmark end-to-end performance"""
        results = {"test_requests": len(test_requests), "results": [], "summary": {}}

        for i, request in enumerate(test_requests):
            start_time = time.time()

            try:
                # Process request and collect all chunks
                response_parts = []
                async for chunk in self.process_e2e_request(request, tenant_id):
                    response_parts.append(chunk)

                total_time = (time.time() - start_time) * 1000

                results["results"].append(
                    {
                        "request_index": i,
                        "success": True,
                        "total_latency_ms": total_time,
                        "response_length": len("".join(response_parts)),
                        "correlation_id": request.correlation_id,
                    }
                )

            except Exception as e:
                results["results"].append(
                    {
                        "request_index": i,
                        "success": False,
                        "error": str(e),
                        "total_latency_ms": (time.time() - start_time) * 1000,
                        "correlation_id": request.correlation_id,
                    }
                )

        # Calculate summary statistics
        successful_results = [r for r in results["results"] if r["success"]]

        if successful_results:
            latencies = [r["total_latency_ms"] for r in successful_results]
            sorted_latencies = sorted(latencies)

            results["summary"] = {
                "success_rate": len(successful_results) / len(test_requests),
                "avg_latency_ms": sum(latencies) / len(latencies),
                "p95_latency_ms": sorted_latencies[int(len(sorted_latencies) * 0.95)],
                "min_latency_ms": min(latencies),
                "max_latency_ms": max(latencies),
                "slo_compliance": sorted_latencies[int(len(sorted_latencies) * 0.95)]
                <= self.performance_targets["total_latency_p95_ms"],
            }

        return results


# Global instance
_e2e_optimization_service: Optional[E2EOptimizationService] = None


def get_e2e_optimization_service(
    optimization_level: OptimizationLevel = OptimizationLevel.BALANCED,
) -> E2EOptimizationService:
    """Get the global E2E optimization service instance"""
    global _e2e_optimization_service

    if _e2e_optimization_service is None:
        _e2e_optimization_service = E2EOptimizationService(optimization_level)

    return _e2e_optimization_service
