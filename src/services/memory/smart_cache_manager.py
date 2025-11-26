"""
Smart Cache Manager for Intelligent Response Optimization

This module implements intelligent caching based on query similarity, context awareness,
and predictive analysis to optimize response generation and reduce computational overhead.
"""

import asyncio
import hashlib
import json
import time
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any, Set, Tuple
from datetime import datetime, timedelta
import logging
from collections import defaultdict
import pickle
import zlib
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class CacheEntry:
    """Represents a cached response entry with metadata."""
    key: str
    content: Any
    timestamp: datetime
    access_count: int
    last_accessed: datetime
    context_hash: str
    query_hash: str
    relevance_score: float
    size_bytes: int
    expiry_time: Optional[datetime] = None
    tags: List[str] = None
    component_type: str = "full_response"
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []

@dataclass
class QuerySimilarity:
    """Represents similarity between queries."""
    query1_hash: str
    query2_hash: str
    similarity_score: float
    context_similarity: float
    semantic_similarity: float

@dataclass
class UsagePattern:
    """Represents usage patterns for predictive caching."""
    query_pattern: str
    frequency: int
    time_patterns: List[str]  # Hour patterns like "09:00", "14:30"
    context_patterns: List[str]
    user_patterns: List[str]
    prediction_confidence: float

@dataclass
class CacheMetrics:
    """Cache performance metrics."""
    hit_rate: float
    miss_rate: float
    total_requests: int
    cache_hits: int
    cache_misses: int
    memory_usage_bytes: int
    eviction_count: int
    warming_success_rate: float
    average_response_time: float

class SmartCacheManager:
    """
    Intelligent cache manager with query similarity, context awareness,
    and predictive caching capabilities.
    """
    
    def __init__(self, 
                 max_memory_mb: int = 512,
                 max_entries: int = 10000,
                 default_ttl_hours: int = 24,
                 similarity_threshold: float = 0.8,
                 cache_dir: Optional[str] = None):
        """
        Initialize the smart cache manager.
        
        Args:
            max_memory_mb: Maximum memory usage in MB
            max_entries: Maximum number of cache entries
            default_ttl_hours: Default time-to-live in hours
            similarity_threshold: Minimum similarity score for cache hits
            cache_dir: Directory for persistent cache storage
        """
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.max_entries = max_entries
        self.default_ttl = timedelta(hours=default_ttl_hours)
        self.similarity_threshold = similarity_threshold
        
        # Cache storage
        self.cache: Dict[str, CacheEntry] = {}
        self.query_similarities: Dict[str, List[QuerySimilarity]] = defaultdict(list)
        self.usage_patterns: List[UsagePattern] = []
        self.component_cache: Dict[str, Dict[str, Any]] = defaultdict(dict)
        
        # Metrics tracking
        self.metrics = CacheMetrics(
            hit_rate=0.0, miss_rate=0.0, total_requests=0,
            cache_hits=0, cache_misses=0, memory_usage_bytes=0,
            eviction_count=0, warming_success_rate=0.0,
            average_response_time=0.0
        )
        
        # Persistent storage
        self.cache_dir = Path(cache_dir) if cache_dir else Path("data/cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Background tasks
        self._cleanup_task: Optional[asyncio.Task] = None
        self._warming_task: Optional[asyncio.Task] = None
        
        logger.info(f"SmartCacheManager initialized with {max_memory_mb}MB limit")

    async def check_cache_relevance(self, query: str, context: Dict[str, Any]) -> Optional[Any]:
        """
        Check cache for relevant responses based on query similarity and context.
        
        Args:
            query: The user query
            context: Query context information
            
        Returns:
            Cached response if relevant match found, None otherwise
        """
        start_time = time.time()
        self.metrics.total_requests += 1
        
        try:
            query_hash = self._hash_query(query)
            context_hash = self._hash_context(context)
            
            # Direct cache hit check
            direct_key = f"{query_hash}:{context_hash}"
            if direct_key in self.cache:
                entry = self.cache[direct_key]
                if self._is_entry_valid(entry):
                    await self._update_access_stats(entry)
                    self.metrics.cache_hits += 1
                    self._update_response_time(time.time() - start_time)
                    logger.debug(f"Direct cache hit for query: {query[:50]}...")
                    return entry.content
            
            # Similarity-based cache check
            similar_entry = await self._find_similar_cached_response(query, context)
            if similar_entry:
                await self._update_access_stats(similar_entry)
                self.metrics.cache_hits += 1
                self._update_response_time(time.time() - start_time)
                logger.debug(f"Similarity cache hit for query: {query[:50]}...")
                return similar_entry.content
            
            # Component-based cache check
            components = await self._find_cached_components(query, context)
            if components:
                self.metrics.cache_hits += 1
                self._update_response_time(time.time() - start_time)
                logger.debug(f"Component cache hit for query: {query[:50]}...")
                return components
            
            self.metrics.cache_misses += 1
            self._update_response_time(time.time() - start_time)
            return None
            
        except Exception as e:
            logger.error(f"Error checking cache relevance: {e}")
            self.metrics.cache_misses += 1
            return None

    async def cache_response_components(self, 
                                      query: str, 
                                      context: Dict[str, Any],
                                      response: Any,
                                      components: Optional[Dict[str, Any]] = None) -> None:
        """
        Cache response and its reusable components.
        
        Args:
            query: The original query
            context: Query context
            response: The full response to cache
            components: Reusable components to cache separately
        """
        try:
            query_hash = self._hash_query(query)
            context_hash = self._hash_context(context)
            
            # Cache full response
            await self._cache_full_response(query, context, response, query_hash, context_hash)
            
            # Cache components if provided
            if components:
                await self._cache_response_components(components, query_hash, context_hash)
            
            # Update usage patterns
            await self._update_usage_patterns(query, context)
            
            # Trigger cleanup if needed
            await self._check_memory_pressure()
            
        except Exception as e:
            logger.error(f"Error caching response components: {e}")

    async def implement_intelligent_invalidation(self, 
                                               invalidation_criteria: Dict[str, Any]) -> int:
        """
        Implement intelligent cache invalidation based on content relevance.
        
        Args:
            invalidation_criteria: Criteria for cache invalidation
            
        Returns:
            Number of entries invalidated
        """
        try:
            invalidated_count = 0
            current_time = datetime.now()
            
            entries_to_remove = []
            
            for key, entry in self.cache.items():
                should_invalidate = False
                
                # Time-based invalidation
                if entry.expiry_time and current_time > entry.expiry_time:
                    should_invalidate = True
                    logger.debug(f"Invalidating expired entry: {key}")
                
                # Relevance-based invalidation
                if entry.relevance_score < invalidation_criteria.get('min_relevance', 0.3):
                    should_invalidate = True
                    logger.debug(f"Invalidating low-relevance entry: {key}")
                
                # Access-based invalidation
                days_since_access = (current_time - entry.last_accessed).days
                if days_since_access > invalidation_criteria.get('max_days_unused', 7):
                    should_invalidate = True
                    logger.debug(f"Invalidating unused entry: {key}")
                
                # Context-based invalidation
                if 'context_changes' in invalidation_criteria:
                    context_changes = invalidation_criteria['context_changes']
                    if self._context_has_changed(entry.context_hash, context_changes):
                        should_invalidate = True
                        logger.debug(f"Invalidating context-changed entry: {key}")
                
                if should_invalidate:
                    entries_to_remove.append(key)
                    invalidated_count += 1
            
            # Remove invalidated entries
            for key in entries_to_remove:
                del self.cache[key]
                self.metrics.eviction_count += 1
            
            logger.info(f"Invalidated {invalidated_count} cache entries")
            return invalidated_count
            
        except Exception as e:
            logger.error(f"Error in intelligent invalidation: {e}")
            return 0

    async def warm_cache_based_on_patterns(self, 
                                         usage_patterns: Optional[List[UsagePattern]] = None) -> int:
        """
        Warm cache proactively based on usage patterns and predictive analysis.
        
        Args:
            usage_patterns: Optional specific patterns to warm, uses stored patterns if None
            
        Returns:
            Number of cache entries warmed
        """
        try:
            patterns_to_use = usage_patterns or self.usage_patterns
            warmed_count = 0
            successful_warms = 0
            
            current_hour = datetime.now().strftime("%H:%M")
            
            for pattern in patterns_to_use:
                # Check if current time matches pattern
                if current_hour in pattern.time_patterns:
                    # Check prediction confidence
                    if pattern.prediction_confidence >= 0.7:
                        try:
                            # Generate cache key for pattern
                            cache_key = self._generate_pattern_cache_key(pattern)
                            
                            # Check if already cached
                            if cache_key not in self.cache:
                                # Simulate response generation for warming
                                # In real implementation, this would call the actual response generation
                                warmed_response = await self._generate_predicted_response(pattern)
                                
                                if warmed_response:
                                    # Create cache entry
                                    entry = CacheEntry(
                                        key=cache_key,
                                        content=warmed_response,
                                        timestamp=datetime.now(),
                                        access_count=0,
                                        last_accessed=datetime.now(),
                                        context_hash=self._hash_context({}),
                                        query_hash=self._hash_query(pattern.query_pattern),
                                        relevance_score=pattern.prediction_confidence,
                                        size_bytes=len(str(warmed_response)),
                                        tags=["warmed", "predicted"]
                                    )
                                    
                                    self.cache[cache_key] = entry
                                    successful_warms += 1
                                    logger.debug(f"Warmed cache for pattern: {pattern.query_pattern}")
                            
                            warmed_count += 1
                            
                        except Exception as e:
                            logger.error(f"Error warming cache for pattern {pattern.query_pattern}: {e}")
            
            # Update warming success rate
            if warmed_count > 0:
                self.metrics.warming_success_rate = successful_warms / warmed_count
            
            logger.info(f"Cache warming completed: {successful_warms}/{warmed_count} successful")
            return successful_warms
            
        except Exception as e:
            logger.error(f"Error in cache warming: {e}")
            return 0

    async def optimize_cache_memory_usage(self) -> Dict[str, Any]:
        """
        Optimize cache memory usage through compression and intelligent eviction.
        
        Returns:
            Optimization results and statistics
        """
        try:
            initial_memory = self._calculate_memory_usage()
            initial_entries = len(self.cache)
            
            optimization_results = {
                'initial_memory_bytes': initial_memory,
                'initial_entries': initial_entries,
                'compressed_entries': 0,
                'evicted_entries': 0,
                'memory_saved_bytes': 0
            }
            
            # Compress large entries
            compressed_count = await self._compress_large_entries()
            optimization_results['compressed_entries'] = compressed_count
            
            # Intelligent eviction based on access patterns and relevance
            evicted_count = await self._intelligent_eviction()
            optimization_results['evicted_entries'] = evicted_count
            
            # Calculate memory savings
            final_memory = self._calculate_memory_usage()
            optimization_results['final_memory_bytes'] = final_memory
            optimization_results['memory_saved_bytes'] = initial_memory - final_memory
            optimization_results['final_entries'] = len(self.cache)
            
            # Update metrics
            self.metrics.memory_usage_bytes = final_memory
            
            logger.info(f"Memory optimization completed: "
                       f"Saved {optimization_results['memory_saved_bytes']} bytes, "
                       f"Compressed {compressed_count} entries, "
                       f"Evicted {evicted_count} entries")
            
            return optimization_results
            
        except Exception as e:
            logger.error(f"Error optimizing cache memory: {e}")
            return {}

    async def get_cache_metrics(self) -> CacheMetrics:
        """Get current cache performance metrics."""
        # Update hit/miss rates
        if self.metrics.total_requests > 0:
            self.metrics.hit_rate = self.metrics.cache_hits / self.metrics.total_requests
            self.metrics.miss_rate = self.metrics.cache_misses / self.metrics.total_requests
        
        # Update memory usage
        self.metrics.memory_usage_bytes = self._calculate_memory_usage()
        
        return self.metrics

    async def start_background_tasks(self) -> None:
        """Start background maintenance tasks."""
        if not self._cleanup_task:
            self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
        
        if not self._warming_task:
            self._warming_task = asyncio.create_task(self._periodic_warming())
        
        logger.info("Background cache maintenance tasks started")

    async def stop_background_tasks(self) -> None:
        """Stop background maintenance tasks."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            self._cleanup_task = None
        
        if self._warming_task:
            self._warming_task.cancel()
            self._warming_task = None
        
        logger.info("Background cache maintenance tasks stopped")

    # Private helper methods
    
    def _hash_query(self, query: str) -> str:
        """Generate hash for query."""
        return hashlib.sha256(query.lower().strip().encode()).hexdigest()[:16]
    
    def _hash_context(self, context: Dict[str, Any]) -> str:
        """Generate hash for context."""
        context_str = json.dumps(context, sort_keys=True, default=str)
        return hashlib.sha256(context_str.encode()).hexdigest()[:16]
    
    def _is_entry_valid(self, entry: CacheEntry) -> bool:
        """Check if cache entry is still valid."""
        if entry.expiry_time and datetime.now() > entry.expiry_time:
            return False
        return True
    
    async def _update_access_stats(self, entry: CacheEntry) -> None:
        """Update access statistics for cache entry."""
        entry.access_count += 1
        entry.last_accessed = datetime.now()
    
    def _update_response_time(self, response_time: float) -> None:
        """Update average response time metric."""
        if self.metrics.total_requests == 1:
            self.metrics.average_response_time = response_time
        else:
            # Running average
            self.metrics.average_response_time = (
                (self.metrics.average_response_time * (self.metrics.total_requests - 1) + response_time) /
                self.metrics.total_requests
            )    

    async def _find_similar_cached_response(self, query: str, context: Dict[str, Any]) -> Optional[CacheEntry]:
        """Find cached response with similar query and context."""
        query_hash = self._hash_query(query)
        context_hash = self._hash_context(context)
        
        best_match = None
        best_similarity = 0.0
        
        for entry in self.cache.values():
            if not self._is_entry_valid(entry):
                continue
            
            # Calculate query similarity
            query_similarity = self._calculate_query_similarity(query, entry.query_hash)
            
            # Calculate context similarity
            context_similarity = self._calculate_context_similarity(context_hash, entry.context_hash)
            
            # Combined similarity score
            combined_similarity = (query_similarity * 0.7) + (context_similarity * 0.3)
            
            if combined_similarity >= self.similarity_threshold and combined_similarity > best_similarity:
                best_similarity = combined_similarity
                best_match = entry
        
        return best_match
    
    async def _find_cached_components(self, query: str, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find cached components that can be reused for the query."""
        query_hash = self._hash_query(query)
        
        if query_hash in self.component_cache:
            components = self.component_cache[query_hash]
            
            # Check component freshness and relevance
            valid_components = {}
            for comp_type, comp_data in components.items():
                if self._is_component_valid(comp_data, context):
                    valid_components[comp_type] = comp_data
            
            return valid_components if valid_components else None
        
        return None
    
    async def _cache_full_response(self, query: str, context: Dict[str, Any], 
                                 response: Any, query_hash: str, context_hash: str) -> None:
        """Cache the full response."""
        cache_key = f"{query_hash}:{context_hash}"
        
        entry = CacheEntry(
            key=cache_key,
            content=response,
            timestamp=datetime.now(),
            access_count=0,
            last_accessed=datetime.now(),
            context_hash=context_hash,
            query_hash=query_hash,
            relevance_score=1.0,  # Full response gets max relevance
            size_bytes=len(str(response)),
            expiry_time=datetime.now() + self.default_ttl,
            tags=["full_response"]
        )
        
        self.cache[cache_key] = entry
        logger.debug(f"Cached full response for query: {query[:50]}...")
    
    async def _cache_response_components(self, components: Dict[str, Any], 
                                       query_hash: str, context_hash: str) -> None:
        """Cache reusable response components."""
        for comp_type, comp_data in components.items():
            comp_key = f"{query_hash}:{comp_type}"
            
            # Add metadata to component
            component_with_metadata = {
                'data': comp_data,
                'timestamp': datetime.now().isoformat(),
                'context_hash': context_hash,
                'relevance_score': 0.8,  # Components get slightly lower relevance
                'access_count': 0
            }
            
            self.component_cache[query_hash][comp_type] = component_with_metadata
            logger.debug(f"Cached component {comp_type} for query hash: {query_hash}")
    
    async def _update_usage_patterns(self, query: str, context: Dict[str, Any]) -> None:
        """Update usage patterns for predictive caching."""
        current_time = datetime.now()
        time_pattern = current_time.strftime("%H:%M")
        
        # Extract context patterns
        context_patterns = []
        if 'user_id' in context:
            context_patterns.append(f"user:{context['user_id']}")
        if 'session_type' in context:
            context_patterns.append(f"session:{context['session_type']}")
        
        # Find or create usage pattern
        query_pattern = self._extract_query_pattern(query)
        existing_pattern = None
        
        for pattern in self.usage_patterns:
            if pattern.query_pattern == query_pattern:
                existing_pattern = pattern
                break
        
        if existing_pattern:
            existing_pattern.frequency += 1
            if time_pattern not in existing_pattern.time_patterns:
                existing_pattern.time_patterns.append(time_pattern)
            for ctx_pattern in context_patterns:
                if ctx_pattern not in existing_pattern.context_patterns:
                    existing_pattern.context_patterns.append(ctx_pattern)
        else:
            new_pattern = UsagePattern(
                query_pattern=query_pattern,
                frequency=1,
                time_patterns=[time_pattern],
                context_patterns=context_patterns,
                user_patterns=[],
                prediction_confidence=0.5  # Initial confidence
            )
            self.usage_patterns.append(new_pattern)
        
        # Update prediction confidence based on frequency
        if existing_pattern:
            existing_pattern.prediction_confidence = min(0.95, existing_pattern.frequency / 10.0)
    
    async def _check_memory_pressure(self) -> None:
        """Check if cache is under memory pressure and trigger cleanup."""
        current_memory = self._calculate_memory_usage()
        
        if current_memory > self.max_memory_bytes * 0.9:  # 90% threshold
            logger.warning(f"Cache memory pressure detected: {current_memory} bytes")
            await self._intelligent_eviction()
    
    def _calculate_memory_usage(self) -> int:
        """Calculate current memory usage of cache."""
        total_size = 0
        
        for entry in self.cache.values():
            total_size += entry.size_bytes
        
        # Add component cache size
        for query_components in self.component_cache.values():
            for component in query_components.values():
                total_size += len(str(component))
        
        return total_size
    
    def _calculate_query_similarity(self, query1: str, query2_hash: str) -> float:
        """Calculate similarity between queries."""
        # Simple implementation - in production, use semantic similarity
        query1_words = set(query1.lower().split())
        
        # For now, use a simple word overlap approach
        # In production, this would use embeddings or semantic similarity
        if len(query1_words) == 0:
            return 0.0
        
        # This is a placeholder - real implementation would compare with actual query
        # For now, return a moderate similarity score
        return 0.6
    
    def _calculate_context_similarity(self, context1_hash: str, context2_hash: str) -> float:
        """Calculate similarity between contexts."""
        if context1_hash == context2_hash:
            return 1.0
        
        # Simple hash-based similarity - in production, use semantic comparison
        common_chars = sum(1 for c1, c2 in zip(context1_hash, context2_hash) if c1 == c2)
        return common_chars / len(context1_hash)
    
    def _is_component_valid(self, component: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Check if cached component is still valid for current context."""
        if 'timestamp' not in component:
            return False
        
        # Check age
        comp_time = datetime.fromisoformat(component['timestamp'])
        age_hours = (datetime.now() - comp_time).total_seconds() / 3600
        
        if age_hours > 24:  # Components expire after 24 hours
            return False
        
        # Check relevance score
        if component.get('relevance_score', 0) < 0.5:
            return False
        
        return True
    
    def _context_has_changed(self, entry_context_hash: str, context_changes: Dict[str, Any]) -> bool:
        """Check if context has changed significantly."""
        # Simple implementation - check if any critical context keys have changed
        critical_changes = context_changes.get('critical_keys', [])
        return len(critical_changes) > 0
    
    def _generate_pattern_cache_key(self, pattern: UsagePattern) -> str:
        """Generate cache key for usage pattern."""
        pattern_str = f"{pattern.query_pattern}:{':'.join(pattern.context_patterns)}"
        return hashlib.sha256(pattern_str.encode()).hexdigest()[:16]
    
    async def _generate_predicted_response(self, pattern: UsagePattern) -> Optional[Any]:
        """Generate predicted response for cache warming."""
        # Placeholder implementation - in production, this would call the actual response generation
        # with the pattern's query and context
        
        if pattern.prediction_confidence < 0.7:
            return None
        
        # Simulate response generation
        predicted_response = {
            'type': 'predicted',
            'pattern': pattern.query_pattern,
            'confidence': pattern.prediction_confidence,
            'generated_at': datetime.now().isoformat(),
            'content': f"Predicted response for pattern: {pattern.query_pattern}"
        }
        
        return predicted_response
    
    def _extract_query_pattern(self, query: str) -> str:
        """Extract pattern from query for usage tracking."""
        # Simple pattern extraction - remove specific details, keep structure
        words = query.lower().split()
        
        # Replace specific entities with placeholders
        pattern_words = []
        for word in words:
            if word.isdigit():
                pattern_words.append("[NUMBER]")
            elif "@" in word:
                pattern_words.append("[EMAIL]")
            elif word.startswith("http"):
                pattern_words.append("[URL]")
            else:
                pattern_words.append(word)
        
        return " ".join(pattern_words[:10])  # Limit pattern length
    
    async def _compress_large_entries(self) -> int:
        """Compress large cache entries to save memory."""
        compressed_count = 0
        
        for entry in self.cache.values():
            if entry.size_bytes > 10000:  # Compress entries larger than 10KB
                try:
                    # Compress content
                    original_content = entry.content
                    compressed_content = zlib.compress(pickle.dumps(original_content))
                    
                    # Update entry with compressed content
                    entry.content = {
                        'compressed': True,
                        'data': compressed_content,
                        'original_size': entry.size_bytes
                    }
                    entry.size_bytes = len(compressed_content)
                    compressed_count += 1
                    
                except Exception as e:
                    logger.error(f"Error compressing cache entry: {e}")
        
        return compressed_count
    
    async def _intelligent_eviction(self) -> int:
        """Perform intelligent cache eviction based on access patterns and relevance."""
        if len(self.cache) <= self.max_entries * 0.8:  # Only evict if over 80% capacity
            return 0
        
        evicted_count = 0
        current_time = datetime.now()
        
        # Score entries for eviction (lower score = more likely to evict)
        entry_scores = []
        
        for key, entry in self.cache.items():
            score = self._calculate_eviction_score(entry, current_time)
            entry_scores.append((score, key))
        
        # Sort by score (lowest first)
        entry_scores.sort()
        
        # Evict lowest scoring entries
        target_evictions = len(self.cache) - int(self.max_entries * 0.7)  # Evict to 70% capacity
        
        for i in range(min(target_evictions, len(entry_scores))):
            _, key = entry_scores[i]
            del self.cache[key]
            evicted_count += 1
            self.metrics.eviction_count += 1
        
        return evicted_count
    
    def _calculate_eviction_score(self, entry: CacheEntry, current_time: datetime) -> float:
        """Calculate eviction score for cache entry (lower = more likely to evict)."""
        # Factors: recency, frequency, relevance, size
        
        # Recency score (0-1, higher = more recent)
        hours_since_access = (current_time - entry.last_accessed).total_seconds() / 3600
        recency_score = max(0, 1 - (hours_since_access / 168))  # 168 hours = 1 week
        
        # Frequency score (normalized by access count)
        frequency_score = min(1.0, entry.access_count / 10.0)
        
        # Relevance score (already 0-1)
        relevance_score = entry.relevance_score
        
        # Size penalty (larger entries get lower scores)
        size_penalty = min(1.0, entry.size_bytes / 100000)  # 100KB threshold
        
        # Combined score
        score = (recency_score * 0.3 + frequency_score * 0.3 + relevance_score * 0.3 - size_penalty * 0.1)
        
        return max(0, score)
    
    async def _periodic_cleanup(self) -> None:
        """Periodic cleanup task."""
        while True:
            try:
                await asyncio.sleep(3600)  # Run every hour
                
                # Intelligent invalidation
                invalidation_criteria = {
                    'min_relevance': 0.2,
                    'max_days_unused': 7
                }
                await self.implement_intelligent_invalidation(invalidation_criteria)
                
                # Memory optimization
                await self.optimize_cache_memory_usage()
                
                logger.debug("Periodic cache cleanup completed")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic cleanup: {e}")
    
    async def _periodic_warming(self) -> None:
        """Periodic cache warming task."""
        while True:
            try:
                await asyncio.sleep(1800)  # Run every 30 minutes
                
                # Warm cache based on patterns
                await self.warm_cache_based_on_patterns()
                
                logger.debug("Periodic cache warming completed")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic warming: {e}")

    async def save_cache_to_disk(self) -> bool:
        """Save cache to persistent storage."""
        try:
            cache_file = self.cache_dir / "smart_cache.pkl"
            patterns_file = self.cache_dir / "usage_patterns.json"
            
            # Save cache entries
            with open(cache_file, 'wb') as f:
                pickle.dump(dict(self.cache), f)
            
            # Save usage patterns
            patterns_data = [asdict(pattern) for pattern in self.usage_patterns]
            with open(patterns_file, 'w') as f:
                json.dump(patterns_data, f, indent=2, default=str)
            
            logger.info("Cache saved to disk successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error saving cache to disk: {e}")
            return False
    
    async def load_cache_from_disk(self) -> bool:
        """Load cache from persistent storage."""
        try:
            cache_file = self.cache_dir / "smart_cache.pkl"
            patterns_file = self.cache_dir / "usage_patterns.json"
            
            # Load cache entries
            if cache_file.exists():
                with open(cache_file, 'rb') as f:
                    loaded_cache = pickle.load(f)
                    self.cache = loaded_cache
            
            # Load usage patterns
            if patterns_file.exists():
                with open(patterns_file, 'r') as f:
                    patterns_data = json.load(f)
                    self.usage_patterns = [UsagePattern(**pattern) for pattern in patterns_data]
            
            logger.info("Cache loaded from disk successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error loading cache from disk: {e}")
            return False