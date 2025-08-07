"""
Database connection pooling and optimization for authentication operations.

This module provides connection pooling, query optimization, and performance
monitoring for the unified authentication system.
"""

from __future__ import annotations

import asyncio
import logging
import sqlite3
import threading
import time
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from queue import Queue, Empty
from typing import Any, Dict, Generator, List, Optional
from urllib.parse import urlparse

from .config import DatabaseConfig
from .exceptions import DatabaseConnectionError, DatabaseOperationError

logger = logging.getLogger(__name__)


class ConnectionPool:
    """
    Database connection pool for SQLite with connection reuse and optimization.
    """
    
    def __init__(self, config: DatabaseConfig, pool_size: int = 10) -> None:
        """
        Initialize connection pool.
        
        Args:
            config: Database configuration
            pool_size: Maximum number of connections in the pool
        """
        self.config = config
        self.pool_size = pool_size
        self.pool: Queue = Queue(maxsize=pool_size)
        self.active_connections: Dict[int, sqlite3.Connection] = {}
        self.connection_stats: Dict[str, Any] = {
            "created": 0,
            "reused": 0,
            "closed": 0,
            "errors": 0,
            "peak_active": 0,
            "total_queries": 0,
            "avg_query_time": 0.0
        }
        self._lock = threading.Lock()
        self._initialized = False
        self._initialize_pool()
    
    def _initialize_pool(self) -> None:
        """Initialize the connection pool with connections."""
        try:
            parsed = urlparse(self.config.database_url)
            
            if parsed.scheme != "sqlite":
                raise DatabaseConnectionError(f"Unsupported database scheme: {parsed.scheme}")
            
            self.db_path = parsed.path.lstrip("/") if parsed.path.startswith("/") else parsed.path
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Pre-create connections for the pool
            for _ in range(min(3, self.pool_size)):  # Start with 3 connections
                conn = self._create_connection()
                self.pool.put(conn)
            
            self._initialized = True
            logger.info(f"Connection pool initialized with {self.pool.qsize()} connections")
            
        except Exception as e:
            raise DatabaseConnectionError(f"Failed to initialize connection pool: {e}")
    
    def _create_connection(self) -> sqlite3.Connection:
        """Create a new database connection with optimizations."""
        try:
            conn = sqlite3.connect(
                self.db_path,
                timeout=self.config.connection_timeout_seconds,
                check_same_thread=False,
                isolation_level=None  # Autocommit mode
            )
            
            # Set row factory for easier data access
            conn.row_factory = sqlite3.Row
            
            # Apply SQLite optimizations
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("PRAGMA journal_mode = WAL")
            conn.execute("PRAGMA synchronous = NORMAL")
            conn.execute("PRAGMA cache_size = -16000")  # 16MB cache per connection
            conn.execute("PRAGMA temp_store = MEMORY")
            conn.execute("PRAGMA mmap_size = 268435456")  # 256MB memory map
            conn.execute("PRAGMA page_size = 4096")
            conn.execute("PRAGMA auto_vacuum = INCREMENTAL")
            
            # Enable query optimization
            conn.execute("PRAGMA optimize")
            
            with self._lock:
                self.connection_stats["created"] += 1
            
            return conn
            
        except Exception as e:
            with self._lock:
                self.connection_stats["errors"] += 1
            raise DatabaseConnectionError(f"Failed to create connection: {e}")
    
    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """
        Get a connection from the pool.
        
        Yields:
            Database connection from the pool
        """
        if not self._initialized:
            raise DatabaseConnectionError("Connection pool not initialized")
        
        conn = None
        start_time = time.time()
        
        try:
            # Try to get connection from pool
            try:
                conn = self.pool.get_nowait()
                with self._lock:
                    self.connection_stats["reused"] += 1
            except Empty:
                # Pool is empty, create new connection if under limit
                with self._lock:
                    if len(self.active_connections) < self.pool_size:
                        conn = self._create_connection()
                    else:
                        # Wait for a connection to become available
                        conn = self.pool.get(timeout=self.config.connection_timeout_seconds)
                        self.connection_stats["reused"] += 1
            
            if not conn:
                raise DatabaseConnectionError("Unable to get connection from pool")
            
            # Track active connection
            conn_id = id(conn)
            with self._lock:
                self.active_connections[conn_id] = conn
                self.connection_stats["peak_active"] = max(
                    self.connection_stats["peak_active"],
                    len(self.active_connections)
                )
            
            # Test connection health
            try:
                conn.execute("SELECT 1").fetchone()
            except Exception:
                # Connection is stale, create a new one
                conn.close()
                conn = self._create_connection()
                with self._lock:
                    self.active_connections[conn_id] = conn
            
            yield conn
            
        except Exception as e:
            with self._lock:
                self.connection_stats["errors"] += 1
            logger.error(f"Connection pool error: {e}")
            raise DatabaseOperationError(f"Connection pool error: {e}", operation="get_connection")
            
        finally:
            # Return connection to pool
            if conn:
                conn_id = id(conn)
                with self._lock:
                    self.active_connections.pop(conn_id, None)
                    
                    # Update query statistics
                    query_time = time.time() - start_time
                    self.connection_stats["total_queries"] += 1
                    current_avg = self.connection_stats["avg_query_time"]
                    total_queries = self.connection_stats["total_queries"]
                    self.connection_stats["avg_query_time"] = (
                        (current_avg * (total_queries - 1) + query_time) / total_queries
                    )
                
                try:
                    # Check if connection is still healthy
                    conn.execute("SELECT 1").fetchone()
                    
                    # Return to pool if there's space
                    if self.pool.qsize() < self.pool_size:
                        self.pool.put_nowait(conn)
                    else:
                        conn.close()
                        with self._lock:
                            self.connection_stats["closed"] += 1
                            
                except Exception:
                    # Connection is broken, close it
                    try:
                        conn.close()
                    except Exception:
                        pass
                    with self._lock:
                        self.connection_stats["closed"] += 1
    
    def execute_query(
        self,
        query: str,
        params: Optional[tuple] = None,
        fetch_one: bool = False,
        fetch_all: bool = False
    ) -> Any:
        """
        Execute a query using a pooled connection.
        
        Args:
            query: SQL query to execute
            params: Query parameters
            fetch_one: Whether to fetch one result
            fetch_all: Whether to fetch all results
            
        Returns:
            Query result based on fetch parameters
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            if fetch_one:
                return cursor.fetchone()
            elif fetch_all:
                return cursor.fetchall()
            else:
                return cursor.rowcount
    
    def execute_many(self, query: str, params_list: List[tuple]) -> int:
        """
        Execute a query multiple times with different parameters.
        
        Args:
            query: SQL query to execute
            params_list: List of parameter tuples
            
        Returns:
            Total number of affected rows
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(query, params_list)
            return cursor.rowcount
    
    def execute_transaction(self, queries: List[tuple]) -> None:
        """
        Execute multiple queries in a transaction.
        
        Args:
            queries: List of (query, params) tuples
        """
        with self.get_connection() as conn:
            try:
                conn.execute("BEGIN TRANSACTION")
                
                for query, params in queries:
                    if params:
                        conn.execute(query, params)
                    else:
                        conn.execute(query)
                
                conn.execute("COMMIT")
                
            except Exception as e:
                conn.execute("ROLLBACK")
                raise DatabaseOperationError(f"Transaction failed: {e}", operation="transaction")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get connection pool statistics."""
        with self._lock:
            stats = self.connection_stats.copy()
            stats.update({
                "pool_size": self.pool_size,
                "available_connections": self.pool.qsize(),
                "active_connections": len(self.active_connections),
                "timestamp": datetime.utcnow().isoformat()
            })
            return stats
    
    def optimize_database(self) -> None:
        """Perform database optimization operations."""
        with self.get_connection() as conn:
            try:
                # Analyze tables for query optimization
                conn.execute("ANALYZE")
                
                # Update query planner statistics
                conn.execute("PRAGMA optimize")
                
                # Incremental vacuum to reclaim space
                conn.execute("PRAGMA incremental_vacuum")
                
                logger.info("Database optimization completed")
                
            except Exception as e:
                logger.error(f"Database optimization failed: {e}")
                raise DatabaseOperationError(f"Optimization failed: {e}", operation="optimize")
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on the connection pool."""
        health_status = {
            "healthy": True,
            "timestamp": datetime.utcnow().isoformat(),
            "issues": []
        }
        
        try:
            # Test connection creation
            with self.get_connection() as conn:
                result = conn.execute("SELECT 1").fetchone()
                if not result or result[0] != 1:
                    health_status["healthy"] = False
                    health_status["issues"].append("Database query test failed")
            
            # Check pool statistics
            stats = self.get_statistics()
            
            if stats["errors"] > stats["created"] * 0.1:  # More than 10% error rate
                health_status["healthy"] = False
                health_status["issues"].append("High error rate in connection pool")
            
            if stats["available_connections"] == 0 and stats["active_connections"] == 0:
                health_status["healthy"] = False
                health_status["issues"].append("No available connections in pool")
            
            health_status["statistics"] = stats
            
        except Exception as e:
            health_status["healthy"] = False
            health_status["issues"].append(f"Health check failed: {e}")
        
        return health_status
    
    def close_all(self) -> None:
        """Close all connections in the pool."""
        with self._lock:
            # Close active connections
            for conn in self.active_connections.values():
                try:
                    conn.close()
                except Exception:
                    pass
            self.active_connections.clear()
            
            # Close pooled connections
            while not self.pool.empty():
                try:
                    conn = self.pool.get_nowait()
                    conn.close()
                    self.connection_stats["closed"] += 1
                except Empty:
                    break
                except Exception:
                    pass
            
            self._initialized = False
            logger.info("All connections closed")
    
    def __del__(self) -> None:
        """Cleanup connections on deletion."""
        try:
            self.close_all()
        except Exception:
            pass


class QueryOptimizer:
    """
    Query optimization utilities for authentication operations.
    """
    
    def __init__(self, pool: ConnectionPool) -> None:
        """Initialize query optimizer with connection pool."""
        self.pool = pool
        self.query_cache: Dict[str, Any] = {}
        self.query_stats: Dict[str, Dict[str, Any]] = {}
    
    def analyze_query_performance(self, query: str, params: Optional[tuple] = None) -> Dict[str, Any]:
        """
        Analyze query performance and suggest optimizations.
        
        Args:
            query: SQL query to analyze
            params: Query parameters
            
        Returns:
            Performance analysis results
        """
        analysis = {
            "query": query,
            "timestamp": datetime.utcnow().isoformat(),
            "execution_time": 0.0,
            "rows_examined": 0,
            "index_usage": [],
            "suggestions": []
        }
        
        try:
            with self.pool.get_connection() as conn:
                # Enable query plan analysis
                conn.execute("PRAGMA query_only = ON")
                
                start_time = time.time()
                
                # Get query plan
                explain_query = f"EXPLAIN QUERY PLAN {query}"
                if params:
                    cursor = conn.execute(explain_query, params)
                else:
                    cursor = conn.execute(explain_query)
                
                query_plan = cursor.fetchall()
                analysis["execution_time"] = time.time() - start_time
                
                # Analyze query plan
                for row in query_plan:
                    detail = row[3] if len(row) > 3 else str(row)
                    
                    if "SCAN" in detail.upper():
                        analysis["suggestions"].append(f"Consider adding index for: {detail}")
                    
                    if "INDEX" in detail.upper():
                        analysis["index_usage"].append(detail)
                
                # Disable query only mode
                conn.execute("PRAGMA query_only = OFF")
                
        except Exception as e:
            analysis["error"] = str(e)
        
        return analysis
    
    def suggest_indexes(self, table_name: str) -> List[str]:
        """
        Suggest indexes for a table based on common query patterns.
        
        Args:
            table_name: Name of the table to analyze
            
        Returns:
            List of suggested index creation statements
        """
        suggestions = []
        
        # Common authentication query patterns
        auth_patterns = {
            "auth_users": [
                "CREATE INDEX IF NOT EXISTS idx_auth_users_email_active ON auth_users (email, is_active)",
                "CREATE INDEX IF NOT EXISTS idx_auth_users_tenant_active ON auth_users (tenant_id, is_active)",
                "CREATE INDEX IF NOT EXISTS idx_auth_users_last_login ON auth_users (last_login_at DESC)"
            ],
            "auth_sessions": [
                "CREATE INDEX IF NOT EXISTS idx_auth_sessions_user_active ON auth_sessions (user_id, is_active)",
                "CREATE INDEX IF NOT EXISTS idx_auth_sessions_token_active ON auth_sessions (session_token, is_active)",
                "CREATE INDEX IF NOT EXISTS idx_auth_sessions_expires_active ON auth_sessions (expires_in, is_active)"
            ],
            "auth_events": [
                "CREATE INDEX IF NOT EXISTS idx_auth_events_user_type ON auth_events (user_id, event_type)",
                "CREATE INDEX IF NOT EXISTS idx_auth_events_timestamp_type ON auth_events (timestamp DESC, event_type)",
                "CREATE INDEX IF NOT EXISTS idx_auth_events_ip_timestamp ON auth_events (ip_address, timestamp DESC)"
            ]
        }
        
        return auth_patterns.get(table_name, [])
    
    def create_recommended_indexes(self) -> Dict[str, Any]:
        """
        Create recommended indexes for authentication tables.
        
        Returns:
            Summary of index creation results
        """
        results = {
            "created": [],
            "errors": [],
            "timestamp": datetime.utcnow().isoformat()
        }
        
        try:
            with self.pool.get_connection() as conn:
                # Get all auth tables
                cursor = conn.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name LIKE 'auth_%'
                """)
                tables = [row[0] for row in cursor.fetchall()]
                
                for table in tables:
                    suggestions = self.suggest_indexes(table)
                    
                    for index_sql in suggestions:
                        try:
                            conn.execute(index_sql)
                            results["created"].append(index_sql)
                        except Exception as e:
                            results["errors"].append(f"Failed to create index: {e}")
                
        except Exception as e:
            results["errors"].append(f"Index creation failed: {e}")
        
        return results
    
    def get_table_statistics(self) -> Dict[str, Any]:
        """Get statistics for all authentication tables."""
        stats = {}
        
        try:
            with self.pool.get_connection() as conn:
                # Get table names and row counts
                cursor = conn.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name LIKE 'auth_%'
                """)
                tables = [row[0] for row in cursor.fetchall()]
                
                for table in tables:
                    cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
                    row_count = cursor.fetchone()[0]
                    
                    # Get table info
                    cursor = conn.execute(f"PRAGMA table_info({table})")
                    columns = cursor.fetchall()
                    
                    # Get index info
                    cursor = conn.execute(f"PRAGMA index_list({table})")
                    indexes = cursor.fetchall()
                    
                    stats[table] = {
                        "row_count": row_count,
                        "column_count": len(columns),
                        "index_count": len(indexes),
                        "columns": [col[1] for col in columns],
                        "indexes": [idx[1] for idx in indexes]
                    }
                    
        except Exception as e:
            logger.error(f"Failed to get table statistics: {e}")
        
        return stats