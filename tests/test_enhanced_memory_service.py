"""
Tests for Enhanced Memory Service - Task 1.1 Validation
Tests memory retrieval failures, error handling, and fallback mechanisms.
"""

import pytest
import asyncio
import uuid
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from src.ai_karen_engine.services.enhanced_memory_service import (
    EnhancedMemoryService,
    MemoryServiceError,
    MemoryRetrievalError,
    CircuitBreaker,
    CircuitBreakerState,
    CircuitBreakerConfig
)
from src.ai_karen_engine.services.memory_service import (
    WebUIMemoryQuery, WebUIMemoryEntry, MemoryType, UISource
)
from src.ai_karen_engine.database.memory_manager import MemoryManager


class TestCircuitBreaker:
    """Test circuit breaker functionality"""
    
    @pytest.fixture
    def circuit_breaker(self):
        config = CircuitBreakerConfig(failure_threshold=3, recovery_timeout=1)
        return CircuitBreaker("test", config)
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_closed_state(self, circuit_breaker):
        """Test circuit breaker in closed state allows calls"""
        async def success_func():
            return "success"
        
        result = await circuit_breaker.call(success_func)
        assert result == "success"
        assert circuit_breaker.stats.state == CircuitBreakerState.CLOSED
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_opens_after_failures(self, circuit_breaker):
        """Test circuit breaker opens after threshold failures"""
        async def failure_func():
            raise Exception("Test failure")
        
        # Trigger failures to open circuit breaker
        for i in range(3):
            with pytest.raises(Exception):
                await circuit_breaker.call(failure_func)
        
        assert circuit_breaker.stats.state == CircuitBreakerState.OPEN
        assert circuit_breaker.stats.failure_count == 3
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_blocks_when_open(self, circuit_breaker):
        """Test circuit breaker blocks calls when open"""
        async def failure_func():
            raise Exception("Test failure")
        
        # Open the circuit breaker
        for i in range(3):
            with pytest.raises(Exception):
                await circuit_breaker.call(failure_func)
        
        # Should now block calls
        with pytest.raises(MemoryServiceError) as exc_info:
            await circuit_breaker.call(failure_func)
        
        assert exc_info.value.error_code == "CIRCUIT_BREAKER_OPEN"
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_half_open_recovery(self, circuit_breaker):
        """Test circuit breaker recovery through half-open state"""
        async def failure_func():
            raise Exception("Test failure")
        
        async def success_func():
            return "success"
        
        # Open the circuit breaker
        for i in range(3):
            with pytest.raises(Exception):
                await circuit_breaker.call(failure_func)
        
        assert circuit_breaker.stats.state == CircuitBreakerState.OPEN
        
        # Wait for recovery timeout
        await asyncio.sleep(1.1)
        
        # Should transition to half-open and allow calls
        result = await circuit_breaker.call(success_func)
        assert result == "success"
        
        # After enough successes, should close
        for i in range(2):  # Need 3 total successes
            await circuit_breaker.call(success_func)
        
        assert circuit_breaker.stats.state == CircuitBreakerState.CLOSED


class TestEnhancedMemoryService:
    """Test enhanced memory service functionality"""
    
    @pytest.fixture
    def mock_base_manager(self):
        """Mock base memory manager"""
        manager = Mock(spec=MemoryManager)
        
        # Create a proper async context manager mock
        mock_session = AsyncMock()
        async_context_manager = AsyncMock()
        async_context_manager.__aenter__ = AsyncMock(return_value=mock_session)
        async_context_manager.__aexit__ = AsyncMock(return_value=None)
        
        manager.db_client = Mock()
        manager.db_client.get_async_session = Mock(return_value=async_context_manager)
        
        return manager
    
    @pytest.fixture
    def enhanced_service(self, mock_base_manager):
        """Create enhanced memory service with mocked dependencies"""
        return EnhancedMemoryService(mock_base_manager)
    
    @pytest.mark.asyncio
    async def test_successful_vector_query(self, enhanced_service, mock_base_manager):
        """Test successful vector store query"""
        # Mock successful parent query
        mock_memories = [
            WebUIMemoryEntry(
                id="mem1",
                content="Test memory content",
                metadata={"tags": ["test"], "user_id": "user1"},
                timestamp=datetime.utcnow().timestamp(),
                similarity_score=0.9
            )
        ]
        
        with patch.object(enhanced_service.__class__.__bases__[0], 'query_memories', 
                         new_callable=AsyncMock) as mock_query:
            mock_query.return_value = mock_memories
            
            query = WebUIMemoryQuery(
                text="test query",
                user_id="user1",
                top_k=5
            )
            
            result = await enhanced_service.query_memories("tenant1", query)
            
            assert len(result) == 1
            assert result[0].id == "mem1"
            assert result[0].content == "Test memory content"
            assert enhanced_service.error_stats["successful_queries"] == 1
    
    @pytest.mark.asyncio
    async def test_vector_failure_fallback_to_sql(self, enhanced_service, mock_base_manager):
        """Test fallback to SQL when vector store fails"""
        # Mock vector store failure
        with patch.object(enhanced_service.__class__.__bases__[0], 'query_memories', 
                         new_callable=AsyncMock) as mock_vector_query:
            mock_vector_query.side_effect = Exception("Vector store error")
            
            # Mock SQL fallback success
            mock_session = AsyncMock()
            mock_result = Mock()
            mock_db_memory = Mock()
            mock_db_memory.id = uuid.uuid4()
            mock_db_memory.vector_id = "mem1"
            mock_db_memory.content = "SQL fallback content"
            mock_db_memory.created_at = datetime.utcnow()
            mock_db_memory.user_id = uuid.uuid4()
            mock_db_memory.tags = ["sql"]
            mock_db_memory.metadata = {}
            mock_db_memory.ui_source = "web"
            mock_db_memory.conversation_id = None
            mock_db_memory.memory_type = "general"
            mock_db_memory.importance_score = 5
            mock_db_memory.access_count = 0
            mock_db_memory.last_accessed = None
            mock_db_memory.ai_generated = False
            mock_db_memory.user_confirmed = True
            mock_db_memory.session_id = None
            
            mock_result.fetchall.return_value = [mock_db_memory]
            mock_session.execute.return_value = mock_result
            
            # Properly mock the async context manager
            async_context_manager = AsyncMock()
            async_context_manager.__aenter__.return_value = mock_session
            async_context_manager.__aexit__.return_value = None
            mock_base_manager.db_client.get_async_session.return_value = async_context_manager
            
            query = WebUIMemoryQuery(
                text="test query",
                user_id="user1",
                top_k=5
            )
            
            result = await enhanced_service.query_memories("tenant1", query)
            
            assert len(result) == 1
            assert result[0].content == "SQL fallback content"
            assert enhanced_service.error_stats["fallback_queries"] == 1
            assert enhanced_service.error_stats["vector_failures"] == 1
    
    @pytest.mark.asyncio
    async def test_complete_failure_graceful_degradation(self, enhanced_service, mock_base_manager):
        """Test graceful degradation when both vector and SQL fail"""
        # Mock both vector and SQL failures
        with patch.object(enhanced_service.__class__.__bases__[0], 'query_memories', 
                         new_callable=AsyncMock) as mock_vector_query:
            mock_vector_query.side_effect = Exception("Vector store error")
            
            # Mock SQL failure
            mock_session = AsyncMock()
            mock_session.execute.side_effect = Exception("SQL error")
            mock_base_manager.db_client.get_async_session.return_value.__aenter__.return_value = mock_session
            
            query = WebUIMemoryQuery(
                text="test query",
                user_id="user1",
                top_k=5
            )
            
            result = await enhanced_service.query_memories("tenant1", query)
            
            # Should return empty list for graceful degradation
            assert result == []
            assert enhanced_service.error_stats["vector_failures"] == 1
            assert enhanced_service.error_stats["sql_failures"] == 1
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_integration(self, enhanced_service, mock_base_manager):
        """Test circuit breaker integration with memory queries"""
        # Mock repeated vector failures to open circuit breaker
        with patch.object(enhanced_service.__class__.__bases__[0], 'query_memories', 
                         new_callable=AsyncMock) as mock_vector_query:
            mock_vector_query.side_effect = Exception("Vector store error")
            
            # Mock SQL fallback success
            mock_session = AsyncMock()
            mock_result = Mock()
            mock_result.fetchall.return_value = []
            mock_session.execute.return_value = mock_result
            mock_base_manager.db_client.get_async_session.return_value.__aenter__.return_value = mock_session
            
            query = WebUIMemoryQuery(
                text="test query",
                user_id="user1",
                top_k=5
            )
            
            # Trigger enough failures to open circuit breaker
            for i in range(6):
                await enhanced_service.query_memories("tenant1", query)
            
            # Circuit breaker should be open
            assert enhanced_service.vector_circuit_breaker.stats.state == CircuitBreakerState.OPEN
            
            # Next query should skip vector store and go directly to SQL
            result = await enhanced_service.query_memories("tenant1", query)
            assert result == []
    
    @pytest.mark.asyncio
    async def test_memory_storage_with_error_handling(self, enhanced_service, mock_base_manager):
        """Test memory storage with error handling"""
        # Mock successful storage
        with patch.object(enhanced_service.__class__.__bases__[0], 'store_web_ui_memory', 
                         new_callable=AsyncMock) as mock_store:
            mock_store.return_value = "mem123"
            
            memory_id = await enhanced_service.store_web_ui_memory(
                tenant_id="tenant1",
                content="Test content",
                user_id="user1",
                ui_source=UISource.WEB
            )
            
            assert memory_id == "mem123"
            mock_store.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_memory_storage_failure_handling(self, enhanced_service, mock_base_manager):
        """Test memory storage failure handling"""
        # Mock storage failure
        with patch.object(enhanced_service.__class__.__bases__[0], 'store_web_ui_memory', 
                         new_callable=AsyncMock) as mock_store:
            mock_store.side_effect = Exception("Storage error")
            
            with pytest.raises(Exception):  # Should propagate storage errors
                await enhanced_service.store_web_ui_memory(
                    tenant_id="tenant1",
                    content="Test content",
                    user_id="user1",
                    ui_source=UISource.WEB
                )
            
            # Error should be recorded
            assert enhanced_service.error_stats["last_error"] is not None
    
    @pytest.mark.asyncio
    async def test_service_health_reporting(self, enhanced_service):
        """Test service health reporting"""
        health = await enhanced_service.get_service_health()
        
        assert "status" in health
        assert "circuit_breakers" in health
        assert "error_stats" in health
        assert "performance_stats" in health
        assert "timestamp" in health
        
        # Check circuit breaker status
        assert "vector_store" in health["circuit_breakers"]
        assert "sql_fallback" in health["circuit_breakers"]
    
    @pytest.mark.asyncio
    async def test_performance_stats_tracking(self, enhanced_service, mock_base_manager):
        """Test performance statistics tracking"""
        # Mock successful query
        mock_memories = [WebUIMemoryEntry(
            id="mem1",
            content="Test content",
            metadata={"user_id": "user1"},
            timestamp=datetime.utcnow().timestamp(),
            similarity_score=0.8
        )]
        
        with patch.object(enhanced_service.__class__.__bases__[0], 'query_memories', 
                         new_callable=AsyncMock) as mock_query:
            mock_query.return_value = mock_memories
            
            query = WebUIMemoryQuery(
                text="test query",
                user_id="user1",
                top_k=5
            )
            
            # Perform multiple queries
            for i in range(3):
                await enhanced_service.query_memories("tenant1", query)
            
            # Check performance stats
            assert enhanced_service.performance_stats["query_count"] == 3
            assert enhanced_service.performance_stats["avg_query_time"] > 0
            assert enhanced_service.performance_stats["avg_vector_time"] > 0
    
    @pytest.mark.asyncio
    async def test_error_history_tracking(self, enhanced_service, mock_base_manager):
        """Test error history tracking"""
        # Mock query failure
        with patch.object(enhanced_service.__class__.__bases__[0], 'query_memories', 
                         new_callable=AsyncMock) as mock_query:
            mock_query.side_effect = Exception("Test error")
            
            # Mock SQL failure too
            mock_session = AsyncMock()
            mock_session.execute.side_effect = Exception("SQL error")
            mock_base_manager.db_client.get_async_session.return_value.__aenter__.return_value = mock_session
            
            query = WebUIMemoryQuery(
                text="test query",
                user_id="user1",
                top_k=5
            )
            
            # Trigger error
            await enhanced_service.query_memories("tenant1", query)
            
            # Check error tracking
            assert enhanced_service.error_stats["last_error"] is not None
            assert len(enhanced_service.error_stats["error_history"]) > 0
            
            last_error = enhanced_service.error_stats["last_error"]
            assert "timestamp" in last_error
            assert "error_type" in last_error
            assert "error_message" in last_error
            assert "correlation_id" in last_error
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_reset(self, enhanced_service):
        """Test circuit breaker reset functionality"""
        # Open circuit breaker by setting failure count
        enhanced_service.vector_circuit_breaker.stats.failure_count = 10
        enhanced_service.vector_circuit_breaker.stats.state = CircuitBreakerState.OPEN
        
        # Reset circuit breakers
        await enhanced_service.reset_circuit_breakers()
        
        # Should be reset to closed state
        assert enhanced_service.vector_circuit_breaker.stats.state == CircuitBreakerState.CLOSED
        assert enhanced_service.vector_circuit_breaker.stats.failure_count == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])