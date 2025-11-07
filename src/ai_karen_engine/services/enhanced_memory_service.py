"""
Enhanced Memory Service - Task 1.1 Implementation
Fixes memory retrieval failures with proper error handling and logging.
"""

import asyncio
import logging
import time
import traceback
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

try:
    from pydantic import BaseModel, ConfigDict, Field
except ImportError:
    from ai_karen_engine.pydantic_stub import BaseModel, ConfigDict, Field
from sqlalchemy import and_, desc, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ai_karen_engine.database.client import MultiTenantPostgresClient
from ai_karen_engine.database.memory_manager import (
    MemoryEntry,
    MemoryManager,
    MemoryQuery,
)
from ai_karen_engine.database.models import TenantConversation, TenantMemoryEntry

# Import existing memory service components
from ai_karen_engine.services.memory_service import (
    MemoryContextBuilder,
    MemoryType,
    UISource,
    WebUIMemoryEntry,
    WebUIMemoryQuery,
    WebUIMemoryService,
)

logger = logging.getLogger(__name__)


class MemoryServiceError(Exception):
    """Base exception for memory service errors"""

    def __init__(
        self,
        message: str,
        error_code: str = "MEMORY_ERROR",
        details: Dict[str, Any] = None,
    ):
        super().__init__(message)
        self.error_code = error_code
        self.details = details or {}
        self.timestamp = datetime.utcnow()


class MemoryRetrievalError(MemoryServiceError):
    """Exception for memory retrieval failures"""

    def __init__(self, message: str, query: str = "", details: Dict[str, Any] = None):
        super().__init__(message, "MEMORY_RETRIEVAL_ERROR", details)
        self.query = query


class MemoryStorageError(MemoryServiceError):
    """Exception for memory storage failures"""

    def __init__(self, message: str, content: str = "", details: Dict[str, Any] = None):
        super().__init__(message, "MEMORY_STORAGE_ERROR", details)
        self.content = content[:100] + "..." if len(content) > 100 else content


class CircuitBreakerState(Enum):
    """Circuit breaker states"""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration"""

    failure_threshold: int = 5
    recovery_timeout: int = 60  # seconds
    success_threshold: int = 3  # for half-open state


@dataclass
class CircuitBreakerStats:
    """Circuit breaker statistics"""

    state: CircuitBreakerState = CircuitBreakerState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None


class CircuitBreaker:
    """Circuit breaker for vector store operations"""

    def __init__(self, name: str, config: CircuitBreakerConfig = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.stats = CircuitBreakerStats()
        self._lock = asyncio.Lock()

    async def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        async with self._lock:
            if self.stats.state == CircuitBreakerState.OPEN:
                if self._should_attempt_reset():
                    self.stats.state = CircuitBreakerState.HALF_OPEN
                    logger.info(
                        f"Circuit breaker {self.name} transitioning to HALF_OPEN"
                    )
                else:
                    raise MemoryServiceError(
                        f"Circuit breaker {self.name} is OPEN",
                        "CIRCUIT_BREAKER_OPEN",
                        {"failure_count": self.stats.failure_count},
                    )

        try:
            result = await func(*args, **kwargs)
            await self._on_success()
            return result
        except Exception as e:
            await self._on_failure(e)
            raise

    def _should_attempt_reset(self) -> bool:
        """Check if circuit breaker should attempt reset"""
        if not self.stats.last_failure_time:
            return True

        time_since_failure = datetime.utcnow() - self.stats.last_failure_time
        return time_since_failure.total_seconds() >= self.config.recovery_timeout

    async def _on_success(self):
        """Handle successful operation"""
        async with self._lock:
            self.stats.success_count += 1
            self.stats.last_success_time = datetime.utcnow()

            if self.stats.state == CircuitBreakerState.HALF_OPEN:
                if self.stats.success_count >= self.config.success_threshold:
                    self.stats.state = CircuitBreakerState.CLOSED
                    self.stats.failure_count = 0
                    self.stats.success_count = 0
                    logger.info(f"Circuit breaker {self.name} reset to CLOSED")

    async def _on_failure(self, error: Exception):
        """Handle failed operation"""
        async with self._lock:
            self.stats.failure_count += 1
            self.stats.last_failure_time = datetime.utcnow()

            if self.stats.state == CircuitBreakerState.CLOSED:
                if self.stats.failure_count >= self.config.failure_threshold:
                    self.stats.state = CircuitBreakerState.OPEN
                    logger.warning(
                        f"Circuit breaker {self.name} opened due to {self.stats.failure_count} failures"
                    )
            elif self.stats.state == CircuitBreakerState.HALF_OPEN:
                self.stats.state = CircuitBreakerState.OPEN
                logger.warning(
                    f"Circuit breaker {self.name} reopened after failure in HALF_OPEN state"
                )


class EnhancedMemoryService(WebUIMemoryService):
    """Enhanced memory service with proper error handling and fallback mechanisms"""

    def __init__(self, base_memory_manager: MemoryManager):
        """Initialize enhanced memory service"""
        super().__init__(base_memory_manager)

        # Circuit breakers for different operations
        self.vector_circuit_breaker = CircuitBreaker("vector_store")
        self.sql_circuit_breaker = CircuitBreaker("sql_fallback")

        # Error tracking
        self.error_stats = {
            "vector_failures": 0,
            "sql_failures": 0,
            "total_queries": 0,
            "successful_queries": 0,
            "fallback_queries": 0,
            "last_error": None,
            "error_history": [],
        }

        # Performance tracking
        self.performance_stats = {
            "avg_query_time": 0.0,
            "avg_vector_time": 0.0,
            "avg_sql_time": 0.0,
            "query_count": 0,
        }

        logger.info("Enhanced memory service initialized with circuit breakers")

    async def query_memories(
        self, tenant_id: Union[str, uuid.UUID], query: WebUIMemoryQuery
    ) -> List[WebUIMemoryEntry]:
        """Enhanced memory query with error handling and fallback mechanisms"""
        start_time = time.time()
        correlation_id = str(uuid.uuid4())

        self.error_stats["total_queries"] += 1

        logger.info(
            f"Starting memory query for tenant {tenant_id}",
            extra={
                "correlation_id": correlation_id,
                "query_text": query.text[:100] + "..."
                if len(query.text) > 100
                else query.text,
                "user_id": query.user_id,
                "top_k": query.top_k,
            },
        )

        try:
            # First attempt: Vector search with circuit breaker
            try:
                memories = await self.vector_circuit_breaker.call(
                    self._query_vector_store, tenant_id, query, correlation_id
                )

                query_time = time.time() - start_time
                self._update_performance_stats(query_time, "vector")
                self.error_stats["successful_queries"] += 1

                logger.info(
                    f"Vector query successful: {len(memories)} memories retrieved in {query_time:.3f}s",
                    extra={"correlation_id": correlation_id},
                )

                return memories

            except MemoryServiceError as e:
                if e.error_code == "CIRCUIT_BREAKER_OPEN":
                    logger.warning(
                        f"Vector store circuit breaker open, falling back to SQL",
                        extra={"correlation_id": correlation_id},
                    )
                else:
                    logger.error(
                        f"Vector store query failed: {e}",
                        extra={
                            "correlation_id": correlation_id,
                            "error_code": e.error_code,
                        },
                    )
                    self.error_stats["vector_failures"] += 1
                    self._record_error(e, correlation_id)

                # Fall back to SQL search
                return await self._fallback_to_sql_search(
                    tenant_id, query, correlation_id
                )

        except Exception as e:
            query_time = time.time() - start_time
            self._update_performance_stats(query_time, "error")

            logger.error(
                f"Memory query failed completely: {e}",
                extra={
                    "correlation_id": correlation_id,
                    "tenant_id": str(tenant_id),
                    "query_text": query.text[:100] + "..."
                    if len(query.text) > 100
                    else query.text,
                    "traceback": traceback.format_exc(),
                },
            )

            self._record_error(e, correlation_id)

            # Return empty list for graceful degradation
            return []

    async def _query_vector_store(
        self,
        tenant_id: Union[str, uuid.UUID],
        query: WebUIMemoryQuery,
        correlation_id: str,
    ) -> List[WebUIMemoryEntry]:
        """Query vector store with detailed error logging"""
        try:
            logger.debug(
                f"Querying vector store",
                extra={"correlation_id": correlation_id, "tenant_id": str(tenant_id)},
            )

            # Use parent class method with enhanced error handling
            base_memories = await super().query_memories(tenant_id, query)

            logger.debug(
                f"Vector store returned {len(base_memories)} memories",
                extra={"correlation_id": correlation_id},
            )

            return base_memories

        except Exception as e:
            error_details = {
                "tenant_id": str(tenant_id),
                "query_text": query.text[:100] + "..."
                if len(query.text) > 100
                else query.text,
                "user_id": query.user_id,
                "top_k": query.top_k,
                "error_type": type(e).__name__,
                "traceback": traceback.format_exc(),
            }

            logger.error(
                f"Vector store query failed: {e}",
                extra={"correlation_id": correlation_id, **error_details},
            )

            raise MemoryRetrievalError(
                f"Vector store query failed: {e}", query.text, error_details
            )

    async def _fallback_to_sql_search(
        self,
        tenant_id: Union[str, uuid.UUID],
        query: WebUIMemoryQuery,
        correlation_id: str,
    ) -> List[WebUIMemoryEntry]:
        """Fallback to SQL-based search when vector operations fail"""
        start_time = time.time()

        logger.info(
            f"Attempting SQL fallback search",
            extra={"correlation_id": correlation_id, "tenant_id": str(tenant_id)},
        )

        try:
            memories = await self.sql_circuit_breaker.call(
                self._sql_text_search, tenant_id, query, correlation_id
            )

            query_time = time.time() - start_time
            self._update_performance_stats(query_time, "sql")
            self.error_stats["fallback_queries"] += 1

            logger.info(
                f"SQL fallback successful: {len(memories)} memories retrieved in {query_time:.3f}s",
                extra={"correlation_id": correlation_id},
            )

            return memories

        except Exception as e:
            self.error_stats["sql_failures"] += 1

            logger.error(
                f"SQL fallback also failed: {e}",
                extra={
                    "correlation_id": correlation_id,
                    "tenant_id": str(tenant_id),
                    "traceback": traceback.format_exc(),
                },
            )

            self._record_error(e, correlation_id)

            # Return empty list for graceful degradation
            return []

    async def _sql_text_search(
        self,
        tenant_id: Union[str, uuid.UUID],
        query: WebUIMemoryQuery,
        correlation_id: str,
    ) -> List[WebUIMemoryEntry]:
        """SQL-based text search as fallback"""
        try:
            async with self.db_client.get_async_session() as session:
                # Build SQL query with text search
                sql_query = (
                    select(TenantMemoryEntry)
                    .where(
                        and_(
                            TenantMemoryEntry.user_id == uuid.UUID(query.user_id)
                            if query.user_id
                            else True,
                            TenantMemoryEntry.content.ilike(f"%{query.text}%"),
                        )
                    )
                    .order_by(desc(TenantMemoryEntry.created_at))
                    .limit(query.top_k)
                )

                result = await session.execute(sql_query)
                db_memories = result.fetchall()

                # Convert to WebUIMemoryEntry format
                memories = []
                for db_memory in db_memories:
                    try:
                        memory = WebUIMemoryEntry(
                            id=db_memory.vector_id or str(db_memory.id),
                            content=db_memory.content,
                            metadata=db_memory.metadata or {},
                            timestamp=db_memory.created_at.timestamp(),
                            tags=db_memory.tags or [],
                            user_id=str(db_memory.user_id),
                            session_id=db_memory.session_id,
                            similarity_score=0.5,  # Default score for SQL search
                            ui_source=UISource(db_memory.ui_source)
                            if db_memory.ui_source
                            else UISource.API,
                            conversation_id=str(db_memory.conversation_id)
                            if db_memory.conversation_id
                            else None,
                            memory_type=MemoryType(db_memory.memory_type)
                            if db_memory.memory_type
                            else MemoryType.GENERAL,
                            importance_score=db_memory.importance_score or 5,
                            access_count=db_memory.access_count or 0,
                            last_accessed=db_memory.last_accessed,
                            ai_generated=db_memory.ai_generated or False,
                            user_confirmed=db_memory.user_confirmed or True,
                        )
                        memories.append(memory)
                    except Exception as e:
                        logger.warning(
                            f"Failed to convert DB memory to WebUIMemoryEntry: {e}",
                            extra={
                                "correlation_id": correlation_id,
                                "memory_id": str(db_memory.id),
                            },
                        )
                        continue

                logger.debug(
                    f"SQL search converted {len(memories)} memories from {len(db_memories)} DB records",
                    extra={"correlation_id": correlation_id},
                )

                return memories

        except Exception as e:
            error_details = {
                "tenant_id": str(tenant_id),
                "query_text": query.text[:100] + "..."
                if len(query.text) > 100
                else query.text,
                "user_id": query.user_id,
                "error_type": type(e).__name__,
                "traceback": traceback.format_exc(),
            }

            logger.error(
                f"SQL text search failed: {e}",
                extra={"correlation_id": correlation_id, **error_details},
            )

            raise MemoryRetrievalError(
                f"SQL text search failed: {e}", query.text, error_details
            )

    async def store_web_ui_memory(
        self,
        tenant_id: Union[str, uuid.UUID],
        content: str,
        user_id: str,
        ui_source: UISource,
        session_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        memory_type: MemoryType = MemoryType.GENERAL,
        tags: Optional[List[str]] = None,
        importance_score: int = None,
        ai_generated: bool = False,
        metadata: Optional[Dict[str, Any]] = None,
        ttl_hours: Optional[int] = None,
    ) -> Optional[str]:
        """Enhanced memory storage with error handling"""
        correlation_id = str(uuid.uuid4())

        logger.info(
            f"Storing memory for tenant {tenant_id}",
            extra={
                "correlation_id": correlation_id,
                "user_id": user_id,
                "content_length": len(content),
                "memory_type": memory_type.value,
                "ui_source": ui_source.value,
            },
        )

        try:
            memory_id = await super().store_web_ui_memory(
                tenant_id=tenant_id,
                content=content,
                user_id=user_id,
                ui_source=ui_source,
                session_id=session_id,
                conversation_id=conversation_id,
                memory_type=memory_type,
                tags=tags,
                importance_score=importance_score,
                ai_generated=ai_generated,
                metadata=metadata,
                ttl_hours=ttl_hours,
            )

            if memory_id:
                logger.info(
                    f"Memory stored successfully: {memory_id}",
                    extra={"correlation_id": correlation_id},
                )
            else:
                logger.warning(
                    f"Memory storage returned None - content may not be surprising enough",
                    extra={"correlation_id": correlation_id},
                )

            return memory_id

        except Exception as e:
            error_details = {
                "tenant_id": str(tenant_id),
                "user_id": user_id,
                "content_length": len(content),
                "memory_type": memory_type.value,
                "error_type": type(e).__name__,
                "traceback": traceback.format_exc(),
            }

            logger.error(
                f"Memory storage failed: {e}",
                extra={"correlation_id": correlation_id, **error_details},
            )

            self._record_error(e, correlation_id)

            raise MemoryStorageError(
                f"Memory storage failed: {e}", content, error_details
            )

    def _update_performance_stats(self, query_time: float, operation_type: str):
        """Update performance statistics"""
        self.performance_stats["query_count"] += 1

        # Update average query time
        current_avg = self.performance_stats["avg_query_time"]
        count = self.performance_stats["query_count"]
        self.performance_stats["avg_query_time"] = (
            current_avg * (count - 1) + query_time
        ) / count

        # Update operation-specific averages
        if operation_type == "vector":
            current_avg = self.performance_stats["avg_vector_time"]
            self.performance_stats["avg_vector_time"] = (
                current_avg * 0.9 + query_time * 0.1
            )
        elif operation_type == "sql":
            current_avg = self.performance_stats["avg_sql_time"]
            self.performance_stats["avg_sql_time"] = (
                current_avg * 0.9 + query_time * 0.1
            )

    def _record_error(self, error: Exception, correlation_id: str):
        """Record error for tracking and analysis"""
        error_record = {
            "timestamp": datetime.utcnow(),
            "error_type": type(error).__name__,
            "error_message": str(error),
            "correlation_id": correlation_id,
            "traceback": traceback.format_exc()
            if hasattr(error, "__traceback__")
            else None,
        }

        self.error_stats["last_error"] = error_record
        self.error_stats["error_history"].append(error_record)

        # Keep only last 100 errors
        if len(self.error_stats["error_history"]) > 100:
            self.error_stats["error_history"] = self.error_stats["error_history"][-100:]

    async def get_service_health(self) -> Dict[str, Any]:
        """Get service health status and statistics"""
        total_queries = self.error_stats["total_queries"]
        successful_queries = self.error_stats["successful_queries"]

        success_rate = (
            (successful_queries / total_queries) if total_queries > 0 else 0.0
        )

        return {
            "status": "healthy"
            if success_rate > 0.8
            else "degraded"
            if success_rate > 0.5
            else "unhealthy",
            "success_rate": success_rate,
            "circuit_breakers": {
                "vector_store": {
                    "state": self.vector_circuit_breaker.stats.state.value,
                    "failure_count": self.vector_circuit_breaker.stats.failure_count,
                    "last_failure": self.vector_circuit_breaker.stats.last_failure_time.isoformat()
                    if self.vector_circuit_breaker.stats.last_failure_time
                    else None,
                },
                "sql_fallback": {
                    "state": self.sql_circuit_breaker.stats.state.value,
                    "failure_count": self.sql_circuit_breaker.stats.failure_count,
                    "last_failure": self.sql_circuit_breaker.stats.last_failure_time.isoformat()
                    if self.sql_circuit_breaker.stats.last_failure_time
                    else None,
                },
            },
            "error_stats": self.error_stats.copy(),
            "performance_stats": self.performance_stats.copy(),
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def reset_circuit_breakers(self):
        """Reset circuit breakers (for administrative use)"""
        self.vector_circuit_breaker.stats = CircuitBreakerStats()
        self.sql_circuit_breaker.stats = CircuitBreakerStats()

        logger.info("Circuit breakers reset")


# Factory function for creating enhanced memory service
def create_enhanced_memory_service(
    base_memory_manager: MemoryManager,
) -> EnhancedMemoryService:
    """Create an enhanced memory service instance"""
    return EnhancedMemoryService(base_memory_manager)
