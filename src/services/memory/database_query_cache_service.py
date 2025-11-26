"""
Database Query Cache Service

Provides intelligent caching for database operations to improve performance
and reduce database load in production environments.
"""

import logging
import hashlib
import json
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from functools import wraps
import asyncio

from production_cache_service import get_cache_service

logger = logging.getLogger(__name__)


@dataclass
class QueryCacheConfig:
    """Configuration for query caching."""
    ttl: int = 3600  # Default 1 hour
    tags: List[str] = None
    invalidate_on_write: bool = True
    max_result_size: int = 1024 * 1024  # 1MB max result size
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []


class DatabaseQueryCacheService:
    """
    Service for caching database query results with intelligent invalidation.
    
    Features:
    - Query result caching with configurable TTL
    - Automatic cache invalidation on data modifications
    - Table-based and tag-based cache invalidation
    - Query fingerprinting for consistent cache keys
    - Performance monitoring and statistics
    """
    
    def __init__(self):
        self.cache_service = get_cache_service()
        self.cache_namespace = 'database_queries'
        
        # Default cache configurations for different query types
        self.default_configs = {
            'select': QueryCacheConfig(ttl=3600, tags=['read_query']),
            'count': QueryCacheConfig(ttl=1800, tags=['count_query']),
            'aggregate': QueryCacheConfig(ttl=1800, tags=['aggregate_query']),
            'lookup': QueryCacheConfig(ttl=7200, tags=['lookup_query']),
            'metadata': QueryCacheConfig(ttl=14400, tags=['metadata_query']),
        }
        
        # Tables that should have shorter cache TTL due to frequent updates
        self.dynamic_tables = {
            'user_sessions': 300,  # 5 minutes
            'chat_messages': 600,  # 10 minutes
            'model_downloads': 300,  # 5 minutes
            'system_metrics': 180,  # 3 minutes
        }
        
        # Tables that rarely change and can be cached longer
        self.static_tables = {
            'users': 3600,  # 1 hour
            'models': 7200,  # 2 hours
            'providers': 14400,  # 4 hours
            'configurations': 7200,  # 2 hours
        }
        
        logger.info("Database query cache service initialized")
    
    def _generate_query_fingerprint(self, query: str, params: Optional[Dict] = None) -> str:
        """
        Generate a fingerprint for a query and its parameters.
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            Query fingerprint hash
        """
        # Normalize query (remove extra whitespace, convert to lowercase)
        normalized_query = ' '.join(query.strip().lower().split())
        
        # Include parameters in fingerprint
        fingerprint_data = {
            'query': normalized_query,
            'params': params or {}
        }
        
        fingerprint_str = json.dumps(fingerprint_data, sort_keys=True, default=str)
        return hashlib.sha256(fingerprint_str.encode()).hexdigest()[:16]
    
    def _extract_table_names(self, query: str) -> List[str]:
        """
        Extract table names from a SQL query.
        
        Args:
            query: SQL query string
            
        Returns:
            List of table names found in the query
        """
        # Simple table name extraction (can be enhanced with proper SQL parsing)
        query_lower = query.lower()
        tables = []
        
        # Look for FROM clauses
        import re
        from_matches = re.findall(r'from\s+([a-zA-Z_][a-zA-Z0-9_]*)', query_lower)
        tables.extend(from_matches)
        
        # Look for JOIN clauses
        join_matches = re.findall(r'join\s+([a-zA-Z_][a-zA-Z0-9_]*)', query_lower)
        tables.extend(join_matches)
        
        # Look for UPDATE clauses
        update_matches = re.findall(r'update\s+([a-zA-Z_][a-zA-Z0-9_]*)', query_lower)
        tables.extend(update_matches)
        
        # Look for INSERT INTO clauses
        insert_matches = re.findall(r'insert\s+into\s+([a-zA-Z_][a-zA-Z0-9_]*)', query_lower)
        tables.extend(insert_matches)
        
        # Look for DELETE FROM clauses
        delete_matches = re.findall(r'delete\s+from\s+([a-zA-Z_][a-zA-Z0-9_]*)', query_lower)
        tables.extend(delete_matches)
        
        return list(set(tables))  # Remove duplicates
    
    def _get_query_type(self, query: str) -> str:
        """
        Determine the type of query for cache configuration.
        
        Args:
            query: SQL query string
            
        Returns:
            Query type string
        """
        query_lower = query.strip().lower()
        
        if query_lower.startswith('select count('):
            return 'count'
        elif query_lower.startswith('select') and any(func in query_lower for func in ['sum(', 'avg(', 'max(', 'min(']):
            return 'aggregate'
        elif query_lower.startswith('select'):
            return 'select'
        elif 'lookup' in query_lower or 'find' in query_lower:
            return 'lookup'
        elif 'information_schema' in query_lower or 'pg_' in query_lower:
            return 'metadata'
        else:
            return 'other'
    
    def _get_cache_config(self, query: str, tables: List[str]) -> QueryCacheConfig:
        """
        Get cache configuration for a query.
        
        Args:
            query: SQL query string
            tables: List of tables involved in the query
            
        Returns:
            Cache configuration for the query
        """
        query_type = self._get_query_type(query)
        config = self.default_configs.get(query_type, QueryCacheConfig())
        
        # Adjust TTL based on table characteristics
        if tables:
            min_ttl = config.ttl
            for table in tables:
                if table in self.dynamic_tables:
                    min_ttl = min(min_ttl, self.dynamic_tables[table])
                elif table in self.static_tables:
                    min_ttl = max(min_ttl, self.static_tables[table])
            
            config.ttl = min_ttl
        
        # Add table-based tags
        config.tags = config.tags + [f"table:{table}" for table in tables]
        
        return config
    
    def _should_cache_query(self, query: str, result: Any) -> bool:
        """
        Determine if a query result should be cached.
        
        Args:
            query: SQL query string
            result: Query result
            
        Returns:
            True if the query should be cached
        """
        query_lower = query.strip().lower()
        
        # Don't cache write operations
        if any(op in query_lower for op in ['insert', 'update', 'delete', 'create', 'drop', 'alter']):
            return False
        
        # Don't cache very large results
        try:
            result_size = len(json.dumps(result, default=str).encode('utf-8'))
            if result_size > 1024 * 1024:  # 1MB
                logger.debug(f"Query result too large to cache: {result_size} bytes")
                return False
        except Exception:
            # If we can't serialize the result, don't cache it
            return False
        
        # Don't cache empty results for some query types
        if not result and self._get_query_type(query) in ['select', 'lookup']:
            return False
        
        return True
    
    async def get_cached_query_result(
        self,
        query: str,
        params: Optional[Dict] = None,
        cache_config: Optional[QueryCacheConfig] = None
    ) -> Optional[Any]:
        """
        Get a cached query result.
        
        Args:
            query: SQL query string
            params: Query parameters
            cache_config: Custom cache configuration
            
        Returns:
            Cached result or None if not found
        """
        try:
            # Generate cache key
            query_fingerprint = self._generate_query_fingerprint(query, params)
            cache_key = f"query:{query_fingerprint}"
            
            # Get cached result
            cached_data = await self.cache_service.get(self.cache_namespace, cache_key)
            if cached_data:
                logger.debug(f"Cache hit for query: {query_fingerprint}")
                return cached_data.get('result')
            
            logger.debug(f"Cache miss for query: {query_fingerprint}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting cached query result: {e}")
            return None
    
    async def cache_query_result(
        self,
        query: str,
        result: Any,
        params: Optional[Dict] = None,
        cache_config: Optional[QueryCacheConfig] = None
    ) -> bool:
        """
        Cache a query result.
        
        Args:
            query: SQL query string
            result: Query result to cache
            params: Query parameters
            cache_config: Custom cache configuration
            
        Returns:
            True if cached successfully
        """
        try:
            # Check if we should cache this query
            if not self._should_cache_query(query, result):
                return False
            
            # Generate cache key and configuration
            query_fingerprint = self._generate_query_fingerprint(query, params)
            cache_key = f"query:{query_fingerprint}"
            
            tables = self._extract_table_names(query)
            config = cache_config or self._get_cache_config(query, tables)
            
            # Prepare cache data
            cache_data = {
                'result': result,
                'query': query,
                'params': params,
                'tables': tables,
                'cached_at': datetime.now().isoformat(),
                'query_type': self._get_query_type(query)
            }
            
            # Cache the result
            success = await self.cache_service.set(
                self.cache_namespace,
                cache_key,
                cache_data,
                ttl=config.ttl,
                tags=config.tags
            )
            
            if success:
                logger.debug(f"Cached query result: {query_fingerprint} (TTL: {config.ttl}s)")
            
            return success
            
        except Exception as e:
            logger.error(f"Error caching query result: {e}")
            return False
    
    async def invalidate_table_cache(self, table_name: str) -> int:
        """
        Invalidate all cached queries for a specific table.
        
        Args:
            table_name: Name of the table
            
        Returns:
            Number of entries invalidated
        """
        return await self.cache_service.invalidate_by_tags([f"table:{table_name}"])
    
    async def invalidate_query_type_cache(self, query_type: str) -> int:
        """
        Invalidate all cached queries of a specific type.
        
        Args:
            query_type: Type of queries to invalidate
            
        Returns:
            Number of entries invalidated
        """
        return await self.cache_service.invalidate_by_tags([f"{query_type}_query"])
    
    async def invalidate_all_query_cache(self) -> int:
        """
        Invalidate all cached query results.
        
        Returns:
            Number of entries invalidated
        """
        return await self.cache_service.clear_namespace(self.cache_namespace)
    
    def cached_query(
        self,
        cache_config: Optional[QueryCacheConfig] = None,
        extract_query_func: Optional[callable] = None
    ):
        """
        Decorator for caching database query results.
        
        Args:
            cache_config: Custom cache configuration
            extract_query_func: Function to extract query from function args
        """
        def decorator(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                # Extract query and params
                if extract_query_func:
                    query, params = extract_query_func(*args, **kwargs)
                else:
                    # Default extraction - assume first arg is query, second is params
                    query = args[0] if args else kwargs.get('query', '')
                    params = args[1] if len(args) > 1 else kwargs.get('params')
                
                # Try to get from cache
                cached_result = await self.get_cached_query_result(query, params, cache_config)
                if cached_result is not None:
                    return cached_result
                
                # Execute function and cache result
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                
                # Cache the result
                await self.cache_query_result(query, result, params, cache_config)
                return result
            
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                # Extract query and params
                if extract_query_func:
                    query, params = extract_query_func(*args, **kwargs)
                else:
                    query = args[0] if args else kwargs.get('query', '')
                    params = args[1] if len(args) > 1 else kwargs.get('params')
                
                # Try to get from cache (sync version)
                loop = None
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                
                cached_result = loop.run_until_complete(
                    self.get_cached_query_result(query, params, cache_config)
                )
                if cached_result is not None:
                    return cached_result
                
                # Execute function and cache result
                result = func(*args, **kwargs)
                loop.run_until_complete(
                    self.cache_query_result(query, result, params, cache_config)
                )
                return result
            
            return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
        
        return decorator
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics for database queries."""
        stats = self.cache_service.get_stats()
        stats['namespace'] = self.cache_namespace
        stats['table_configs'] = {
            'dynamic_tables': self.dynamic_tables,
            'static_tables': self.static_tables
        }
        stats['default_configs'] = {
            name: {
                'ttl': config.ttl,
                'tags': config.tags,
                'invalidate_on_write': config.invalidate_on_write
            }
            for name, config in self.default_configs.items()
        }
        return stats


# Global database query cache service instance
_db_cache_service: Optional[DatabaseQueryCacheService] = None


def get_db_cache_service() -> DatabaseQueryCacheService:
    """Get the global database query cache service instance."""
    global _db_cache_service
    
    if _db_cache_service is None:
        _db_cache_service = DatabaseQueryCacheService()
    
    return _db_cache_service


def reset_db_cache_service() -> None:
    """Reset the global database query cache service (for testing)."""
    global _db_cache_service
    _db_cache_service = None