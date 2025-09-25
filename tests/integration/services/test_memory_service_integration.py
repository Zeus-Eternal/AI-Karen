"""
Integration tests for Memory Service - Task 1 Complete Validation
Tests the complete memory service integration with error handling and fallbacks.
"""

import pytest
import asyncio
import uuid
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

from src.ai_karen_engine.services.integrated_memory_service import (
    IntegratedMemoryService,
    ContextualMemoryQuery,
    ContextualMemoryResult
)
from src.ai_karen_engine.services.memory_service import MemoryType, UISource
from src.ai_karen_engine.database.memory_manager import MemoryManager
from src.ai_karen_engine.database.client import MultiTenantPostgresClient


class TestIntegratedMemoryService:
    """Test integrated memory service functionality"""
    
    @pytest.fixture
    def mock_db_client(self):
        """Mock database client"""
        client = Mock(spec=MultiTenantPostgresClient)
        
        # Create proper async context manager mock
        mock_session = AsyncMock()
        async_context_manager = AsyncMock()
        async_context_manager.__aenter__ = AsyncMock(return_value=mock_session)
        async_context_manager.__aexit__ = AsyncMock(return_value=None)
        
        client.get_async_session = Mock(return_value=async_context_manager)
        return client
    
    @pytest.fixture
    def mock_base_manager(self, mock_db_client):
        """Mock base memory manager"""
        manager = Mock(spec=MemoryManager)
        manager.db_client = mock_db_client
        return manager
    
    @pytest.fixture
    def integrated_service(self, mock_base_manager, mock_db_client):
        """Create integrated memory service with mocked dependencies"""
        return IntegratedMemoryService(mock_base_manager, mock_db_client)
    
    @pytest.mark.asyncio
    async def test_contextual_memory_query_success(self, integrated_service):
        """Test successful contextual memory query"""
        # Mock the enhanced memory service query
        with patch.object(integrated_service.enhanced_memory_service, 'query_memories', 
                         new_callable=AsyncMock) as mock_query:
            
            # Mock memory results
            from src.ai_karen_engine.services.memory_service import WebUIMemoryEntry
            mock_memories = [
                WebUIMemoryEntry(
                    id="mem1",
                    content="Test memory content",
                    metadata={"user_id": "user1"},
                    timestamp=datetime.utcnow().timestamp(),
                    similarity_score=0.9
                )
            ]
            mock_query.return_value = mock_memories
            
            # Mock conversation tracker
            with patch.object(integrated_service.conversation_tracker, 'get_conversation_context',
                             new_callable=AsyncMock) as mock_context:
                mock_context.return_value = {
                    "session_id": "session1",
                    "recent_turns": [],
                    "context_summary": "Previous conversation context",
                    "memory_references": []
                }
                
                query = ContextualMemoryQuery(
                    text="test query",
                    user_id="user1",
                    session_id="session1",
                    include_conversation_context=True
                )
                
                result = await integrated_service.query_memories_with_context("tenant1", query)
                
                assert isinstance(result, ContextualMemoryResult)
                assert len(result.memories) == 1
                assert result.memories[0].id == "mem1"
                assert result.total_memories_found == 1
                assert not result.used_fallback
                assert result.correlation_id != ""
                assert integrated_service.integration_stats["contextual_queries"] == 1
    
    @pytest.mark.asyncio
    async def test_contextual_query_without_conversation_context(self, integrated_service):
        """Test contextual query without conversation context"""
        with patch.object(integrated_service.enhanced_memory_service, 'query_memories', 
                         new_callable=AsyncMock) as mock_query:
            
            from src.ai_karen_engine.services.memory_service import WebUIMemoryEntry
            mock_memories = [
                WebUIMemoryEntry(
                    id="mem1",
                    content="Test content",
                    metadata={"user_id": "user1"},
                    timestamp=datetime.utcnow().timestamp(),
                    similarity_score=0.8
                )
            ]
            mock_query.return_value = mock_memories
            
            query = ContextualMemoryQuery(
                text="test query",
                user_id="user1",
                include_conversation_context=False
            )
            
            result = await integrated_service.query_memories_with_context("tenant1", query)
            
            assert len(result.memories) == 1
            assert result.conversation_context == {}
            assert result.context_summary == ""
    
    @pytest.mark.asyncio
    async def test_store_conversation_memory(self, integrated_service):
        """Test storing conversation memory"""
        # Mock conversation tracker
        with patch.object(integrated_service.conversation_tracker, 'add_conversation_turn',
                         new_callable=AsyncMock) as mock_add_turn:
            
            from src.ai_karen_engine.services.conversation_tracker import ConversationTurn
            mock_turn = ConversationTurn(
                id="turn1",
                user_message="Hello",
                assistant_response="Hi there!",
                timestamp=datetime.utcnow()
            )
            mock_add_turn.return_value = mock_turn
            
            # Mock enhanced memory service
            with patch.object(integrated_service.enhanced_memory_service, 'store_web_ui_memory',
                             new_callable=AsyncMock) as mock_store:
                mock_store.return_value = "mem123"
                
                memory_id, turn = await integrated_service.store_conversation_memory(
                    tenant_id="tenant1",
                    user_message="Hello",
                    assistant_response="Hi there!",
                    user_id="user1",
                    session_id="session1"
                )
                
                assert memory_id == "mem123"
                assert turn.id == "turn1"
                assert turn.user_message == "Hello"
                assert turn.assistant_response == "Hi there!"
                assert integrated_service.integration_stats["conversation_memories_stored"] == 1
    
    @pytest.mark.asyncio
    async def test_conversation_session_management(self, integrated_service):
        """Test conversation session management"""
        # Mock conversation tracker
        with patch.object(integrated_service.conversation_tracker, 'start_session',
                         new_callable=AsyncMock) as mock_start:
            
            from src.ai_karen_engine.services.conversation_tracker import ConversationSession
            mock_session = ConversationSession(
                session_id="session1",
                user_id="user1",
                tenant_id="tenant1"
            )
            mock_start.return_value = mock_session
            
            session = await integrated_service.start_conversation_session(
                session_id="session1",
                user_id="user1",
                tenant_id="tenant1"
            )
            
            assert session.session_id == "session1"
            assert session.user_id == "user1"
            assert session.tenant_id == "tenant1"
            
            mock_start.assert_called_once_with(
                session_id="session1",
                user_id="user1",
                tenant_id="tenant1",
                conversation_id=None,
                metadata=None
            )
    
    @pytest.mark.asyncio
    async def test_service_health_reporting(self, integrated_service):
        """Test service health reporting"""
        # Mock enhanced memory service health
        with patch.object(integrated_service.enhanced_memory_service, 'get_service_health',
                         new_callable=AsyncMock) as mock_health:
            mock_health.return_value = {
                "status": "healthy",
                "success_rate": 0.95,
                "circuit_breakers": {
                    "vector_store": {"state": "closed"},
                    "sql_fallback": {"state": "closed"}
                }
            }
            
            health = await integrated_service.get_service_health()
            
            assert health["status"] == "healthy"
            assert "memory_service" in health
            assert "conversation_tracker" in health
            assert "integration_stats" in health
            assert "timestamp" in health
    
    @pytest.mark.asyncio
    async def test_error_handling_graceful_degradation(self, integrated_service):
        """Test error handling and graceful degradation"""
        # Mock memory service failure
        with patch.object(integrated_service.enhanced_memory_service, 'query_memories', 
                         new_callable=AsyncMock) as mock_query:
            mock_query.side_effect = Exception("Memory service error")
            
            query = ContextualMemoryQuery(
                text="test query",
                user_id="user1",
                session_id="session1"
            )
            
            result = await integrated_service.query_memories_with_context("tenant1", query)
            
            # Should return empty result for graceful degradation
            assert len(result.memories) == 0
            assert result.used_fallback == True
            assert "error" in result.conversation_context
    
    @pytest.mark.asyncio
    async def test_memory_enhancement_with_context(self, integrated_service):
        """Test memory enhancement with conversation context"""
        with patch.object(integrated_service.enhanced_memory_service, 'query_memories', 
                         new_callable=AsyncMock) as mock_query:
            
            from src.ai_karen_engine.services.memory_service import WebUIMemoryEntry
            mock_memory = WebUIMemoryEntry(
                id="mem1",
                content="Test content",
                metadata={"user_id": "user1"},
                timestamp=datetime.utcnow().timestamp(),
                similarity_score=0.7
            )
            mock_query.return_value = [mock_memory]
            
            # Mock conversation context with memory references
            with patch.object(integrated_service.conversation_tracker, 'get_conversation_context',
                             new_callable=AsyncMock) as mock_context:
                mock_context.return_value = {
                    "session_id": "session1",
                    "recent_turns": [],
                    "context_summary": "Previous context",
                    "memory_references": ["mem1"]  # This memory was referenced
                }
                
                query = ContextualMemoryQuery(
                    text="test query",
                    user_id="user1",
                    session_id="session1",
                    include_conversation_context=True
                )
                
                result = await integrated_service.query_memories_with_context("tenant1", query)
                
                # Memory should be enhanced due to context reference
                enhanced_memory = result.memories[0]
                assert enhanced_memory.similarity_score > 0.7  # Should be boosted
                assert enhanced_memory.metadata.get("referenced_in_conversation") == True
                assert integrated_service.integration_stats["context_enhanced_results"] == 1
                assert integrated_service.integration_stats["cross_session_references"] == 1
    
    @pytest.mark.asyncio
    async def test_conversation_history_with_memories(self, integrated_service):
        """Test getting conversation history with related memories"""
        # Mock conversation tracker
        with patch.object(integrated_service.conversation_tracker, 'get_session_history',
                         new_callable=AsyncMock) as mock_history:
            
            from src.ai_karen_engine.services.conversation_tracker import ConversationTurn
            mock_turns = [
                ConversationTurn(
                    id="turn1",
                    user_message="Hello",
                    assistant_response="Hi!",
                    timestamp=datetime.utcnow(),
                    memory_references=["mem1", "mem2"]
                ),
                ConversationTurn(
                    id="turn2",
                    user_message="How are you?",
                    assistant_response="Good!",
                    timestamp=datetime.utcnow(),
                    memory_references=["mem3"]
                )
            ]
            mock_history.return_value = mock_turns
            
            history = await integrated_service.get_conversation_history_with_memories(
                session_id="session1",
                include_related_memories=True
            )
            
            assert history["session_id"] == "session1"
            assert len(history["turns"]) == 2
            assert history["turn_count"] == 2
            assert len(history["memory_references"]) == 3  # mem1, mem2, mem3
            assert "mem1" in history["memory_references"]
            assert "mem2" in history["memory_references"]
            assert "mem3" in history["memory_references"]
    
    @pytest.mark.asyncio
    async def test_service_state_reset(self, integrated_service):
        """Test service state reset functionality"""
        # Set some stats
        integrated_service.integration_stats["contextual_queries"] = 10
        integrated_service.integration_stats["context_enhanced_results"] = 5
        
        # Mock enhanced memory service reset
        with patch.object(integrated_service.enhanced_memory_service, 'reset_circuit_breakers',
                         new_callable=AsyncMock) as mock_reset:
            
            await integrated_service.reset_service_state()
            
            # Stats should be reset
            assert integrated_service.integration_stats["contextual_queries"] == 0
            assert integrated_service.integration_stats["context_enhanced_results"] == 0
            
            mock_reset.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])