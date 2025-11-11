"""
Unit tests for WebUIMemoryService.
"""

import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch


def create_async_context_manager_mock(session_mock):
    """Helper function to create properly mocked async context manager."""
    async_context_manager = AsyncMock()
    async_context_manager.__aenter__ = AsyncMock(return_value=session_mock)
    async_context_manager.__aexit__ = AsyncMock(return_value=None)
    return Mock(return_value=async_context_manager)

from src.ai_karen_engine.services.memory_service import (
    WebUIMemoryService,
    WebUIMemoryQuery,
    WebUIMemoryEntry,
    MemoryType,
    UISource,
    MemoryContextBuilder
)
from src.ai_karen_engine.database.memory_manager import MemoryManager, MemoryEntry


class TestWebUIMemoryService:
    """Test cases for WebUIMemoryService."""
    
    @pytest.fixture
    def mock_base_manager(self):
        """Mock base memory manager."""
        manager = Mock(spec=MemoryManager)
        manager.db_client = Mock()
        manager.metrics = {
            "queries_total": 0,
            "memories_stored": 0,
            "memories_retrieved": 0
        }
        return manager
    
    @pytest.fixture
    def memory_service(self, mock_base_manager):
        """Create WebUIMemoryService instance."""
        return WebUIMemoryService(mock_base_manager)
    
    @pytest.mark.asyncio
    async def test_store_web_ui_memory_basic(self, memory_service, mock_base_manager):
        """Test basic memory storage."""
        # Setup
        tenant_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        content = "I like pizza"
        
        mock_base_manager.store_memory = AsyncMock(return_value="memory-123")
        memory_service._update_web_ui_fields = AsyncMock()
        memory_service._generate_auto_tags = AsyncMock(return_value=["food", "preference"])
        memory_service._extract_facts = AsyncMock(return_value=["User likes pizza"])
        
        # Execute
        result = await memory_service.store_web_ui_memory(
            tenant_id=tenant_id,
            content=content,
            user_id=user_id,
            ui_source=UISource.WEB,
            memory_type=MemoryType.PREFERENCE
        )
        
        # Verify
        assert result == "memory-123"
        mock_base_manager.store_memory.assert_called_once()
        memory_service._update_web_ui_fields.assert_called_once()
        
        # Check that metadata includes web UI fields
        call_args = mock_base_manager.store_memory.call_args
        metadata = call_args.kwargs["metadata"]
        assert metadata["ui_source"] == "web"
        assert metadata["memory_type"] == "preference"
        assert metadata["importance_score"] == 5  # default
        assert metadata["ai_generated"] is False
        assert metadata["user_confirmed"] is True

    @pytest.mark.asyncio
    async def test_store_ag_ui_memory(self, memory_service, mock_base_manager):
        """Test storing memory from AG-UI source."""
        tenant_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        content = "AG-UI memory entry"

        mock_base_manager.store_memory = AsyncMock(return_value="memory-789")
        memory_service._update_web_ui_fields = AsyncMock()
        memory_service._generate_auto_tags = AsyncMock(return_value=[])
        memory_service._extract_facts = AsyncMock(return_value=[])

        result = await memory_service.store_web_ui_memory(
            tenant_id=tenant_id,
            content=content,
            user_id=user_id,
            ui_source=UISource.AG_UI,
            memory_type=MemoryType.GENERAL
        )

        assert result == "memory-789"
        call_args = mock_base_manager.store_memory.call_args
        metadata = call_args.kwargs["metadata"]
        assert metadata["ui_source"] == "ag_ui"
    
    @pytest.mark.asyncio
    async def test_store_ai_generated_memory(self, memory_service, mock_base_manager):
        """Test storing AI-generated memory."""
        # Setup
        tenant_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        content = "User seems to prefer Italian food based on conversation"
        
        mock_base_manager.store_memory = AsyncMock(return_value="memory-456")
        memory_service._update_web_ui_fields = AsyncMock()
        memory_service._generate_auto_tags = AsyncMock(return_value=["ai-insight"])
        memory_service._extract_facts = AsyncMock(return_value=[])
        
        # Execute
        result = await memory_service.store_web_ui_memory(
            tenant_id=tenant_id,
            content=content,
            user_id=user_id,
            ui_source=UISource.WEB,
            memory_type=MemoryType.INSIGHT,
            ai_generated=True,
            importance_score=7
        )
        
        # Verify
        assert result == "memory-456"
        
        call_args = mock_base_manager.store_memory.call_args
        metadata = call_args.kwargs["metadata"]
        assert metadata["ai_generated"] is True
        assert metadata["user_confirmed"] is False  # AI generated needs confirmation
        assert metadata["importance_score"] == 7
    
    @pytest.mark.asyncio
    async def test_query_memories_with_filters(self, memory_service, mock_base_manager):
        """Test querying memories with web UI filters."""
        # Setup
        tenant_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        
        # Mock base memory entries
        base_memory = MemoryEntry(
            id="memory-123",
            content="I like pizza",
            timestamp=1234567890,
            user_id=user_id,
            tags=["food", "preference"]
        )
        
        mock_base_manager.query_memories = AsyncMock(return_value=[base_memory])
        memory_service._get_web_ui_memory_data = AsyncMock(return_value={
            "memory-123": {
                "ui_source": "web",
                "memory_type": "preference",
                "importance_score": 8,
                "access_count": 5,
                "ai_generated": False,
                "user_confirmed": True
            }
        })
        memory_service._increment_access_count = AsyncMock()
        
        # Create query
        query = WebUIMemoryQuery(
            text="food preferences",
            user_id=user_id,
            memory_types=[MemoryType.PREFERENCE],
            importance_range=(7, 10),
            only_user_confirmed=True
        )
        
        # Execute
        results = await memory_service.query_memories(tenant_id, query)
        
        # Verify
        assert len(results) == 1
        result = results[0]
        assert isinstance(result, WebUIMemoryEntry)
        assert result.id == "memory-123"
        assert result.content == "I like pizza"
        assert result.ui_source == UISource.WEB
        assert result.memory_type == MemoryType.PREFERENCE
        assert result.importance_score == 8
        assert result.user_confirmed is True
        
        memory_service._increment_access_count.assert_called_once_with(tenant_id, "memory-123")
    
    @pytest.mark.asyncio
    async def test_query_memories_filtering(self, memory_service, mock_base_manager):
        """Test that web UI filters work correctly."""
        # Setup
        tenant_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        
        base_memory = MemoryEntry(
            id="memory-123",
            content="Test content",
            timestamp=1234567890,
            user_id=user_id
        )
        
        mock_base_manager.query_memories = AsyncMock(return_value=[base_memory])
        memory_service._get_web_ui_memory_data = AsyncMock(return_value={
            "memory-123": {
                "ui_source": "desktop",  # Different UI source
                "memory_type": "general",
                "importance_score": 3,  # Below range
                "ai_generated": True,
                "user_confirmed": False  # Not confirmed
            }
        })
        
        # Query with filters that should exclude this memory
        query = WebUIMemoryQuery(
            text="test",
            user_id=user_id,
            ui_source=UISource.WEB,  # Filter for web only
            importance_range=(5, 10),  # Importance 5-10
            only_user_confirmed=True  # Only confirmed memories
        )
        
        # Execute
        results = await memory_service.query_memories(tenant_id, query)
        
        # Verify - should be filtered out
        assert len(results) == 0
    
    @pytest.mark.asyncio
    async def test_build_conversation_context(self, memory_service):
        """Test building conversation context."""
        # Setup
        tenant_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        query = "What do I like to eat?"
        
        # Mock memories of different types
        memories = [
            WebUIMemoryEntry(
                id="fact-1",
                content="I am vegetarian",
                memory_type=MemoryType.FACT,
                importance_score=9,
                similarity_score=0.8,
                timestamp=1234567890,
                tags=["diet", "preference"]
            ),
            WebUIMemoryEntry(
                id="pref-1", 
                content="I love Italian food",
                memory_type=MemoryType.PREFERENCE,
                importance_score=7,
                similarity_score=0.7,
                timestamp=1234567800,
                tags=["food", "preference"]
            )
        ]
        
        memory_service.query_memories = AsyncMock(return_value=memories)
        memory_service.context_builder._get_conversation_context = AsyncMock(return_value={
            "title": "Food Discussion",
            "summary": "Talking about food preferences"
        })
        
        # Execute
        context = await memory_service.build_conversation_context(
            tenant_id=tenant_id,
            query=query,
            user_id=user_id,
            conversation_id="conv-123"  # Provide conversation_id to trigger context retrieval
        )
        
        # Verify
        assert context["total_memories"] == 2
        assert len(context["memories"]) == 2
        assert context["memory_types_found"] == [MemoryType.FACT, MemoryType.PREFERENCE]
        assert context["conversation_context"] is not None
        
        # Check that facts come first (higher weight)
        first_memory = context["memories"][0]
        assert first_memory["type"] == "fact"
        assert first_memory["content"] == "I am vegetarian"
    
    @pytest.mark.asyncio
    async def test_confirm_memory(self, memory_service):
        """Test confirming AI-generated memory."""
        # Setup
        tenant_id = str(uuid.uuid4())
        memory_id = "memory-123"
        
        # Mock database session with proper async context manager
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock()
        mock_session.commit = AsyncMock()
        
        async_context_manager = AsyncMock()
        async_context_manager.__aenter__ = AsyncMock(return_value=mock_session)
        async_context_manager.__aexit__ = AsyncMock(return_value=None)
        memory_service.db_client.get_async_session = Mock(return_value=async_context_manager)
        
        # Execute
        result = await memory_service.confirm_memory(tenant_id, memory_id, confirmed=True)
        
        # Verify
        assert result is True
        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()
        assert memory_service.web_ui_metrics["memory_confirmations"] == 1
    
    @pytest.mark.asyncio
    async def test_update_memory_importance(self, memory_service):
        """Test updating memory importance score."""
        # Setup
        tenant_id = str(uuid.uuid4())
        memory_id = "memory-123"
        new_importance = 8
        
        # Mock database session with proper async context manager
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock()
        mock_session.commit = AsyncMock()
        
        async_context_manager = AsyncMock()
        async_context_manager.__aenter__ = AsyncMock(return_value=mock_session)
        async_context_manager.__aexit__ = AsyncMock(return_value=None)
        memory_service.db_client.get_async_session = Mock(return_value=async_context_manager)
        
        # Execute
        result = await memory_service.update_memory_importance(tenant_id, memory_id, new_importance)
        
        # Verify
        assert result is True
        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_memory_importance_invalid_score(self, memory_service):
        """Test updating memory importance with invalid score."""
        tenant_id = str(uuid.uuid4())
        memory_id = "memory-123"
        
        # Test invalid scores
        with pytest.raises(ValueError, match="Importance score must be between 1 and 10"):
            await memory_service.update_memory_importance(tenant_id, memory_id, 0)
        
        with pytest.raises(ValueError, match="Importance score must be between 1 and 10"):
            await memory_service.update_memory_importance(tenant_id, memory_id, 11)
    
    @pytest.mark.asyncio
    async def test_get_memory_analytics(self, memory_service):
        """Test getting memory analytics."""
        # Setup
        tenant_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        
        # Mock database session and results
        mock_memory = Mock()
        mock_memory.memory_type = "preference"
        mock_memory.ui_source = "web"
        mock_memory.importance_score = 7
        mock_memory.ai_generated = False
        mock_memory.user_confirmed = True
        mock_memory.tags = ["food", "preference"]
        mock_memory.vector_id = "memory-123"
        mock_memory.content = "I like pizza"
        mock_memory.access_count = 5
        mock_memory.created_at = datetime.utcnow()
        
        mock_session = AsyncMock()
        
        # Mock the main query result
        mock_result = Mock()
        mock_result.fetchall = Mock(return_value=[mock_memory])
        
        # Mock the most_accessed query result
        mock_most_accessed_result = Mock()
        mock_most_accessed_result.fetchall = Mock(return_value=[mock_memory])
        
        # Mock the recent activity query result
        mock_recent_result = Mock()
        mock_recent_result.fetchall = Mock(return_value=[mock_memory])
        
        # Set up execute to return different results for different queries
        mock_session.execute = AsyncMock(side_effect=[mock_result, mock_most_accessed_result, mock_recent_result])
        
        memory_service.db_client.get_async_session = create_async_context_manager_mock(mock_session)
        
        # Execute
        analytics = await memory_service.get_memory_analytics(tenant_id, user_id)
        
        # Verify
        assert analytics["total_memories"] == 1
        assert analytics["memories_by_type"]["preference"] == 1
        assert analytics["memories_by_ui_source"]["web"] == 1
        assert analytics["memories_by_importance"]["7"] == 1
        assert analytics["ai_generated_count"] == 0
        assert analytics["user_confirmed_count"] == 1
        assert analytics["average_importance"] == 7.0
        assert analytics["tag_frequency"]["food"] == 1
        assert analytics["tag_frequency"]["preference"] == 1
    
    @pytest.mark.asyncio
    async def test_generate_auto_tags(self, memory_service):
        """Test automatic tag generation."""
        # Test with different content types
        content1 = "I always remember to call my mom on Sundays"
        tags1 = await memory_service._generate_auto_tags(content1, MemoryType.FACT)
        assert "always" in tags1
        assert "remember" in tags1
        assert "fact" in tags1
        
        content2 = "This is a very detailed explanation of how the system works and what it does. " * 5  # Make it longer than 200 chars
        tags2 = await memory_service._generate_auto_tags(content2, MemoryType.GENERAL)
        assert "general" in tags2
        assert "detailed" in tags2  # Should be found in long content
        
        content3 = "No"
        tags3 = await memory_service._generate_auto_tags(content3, MemoryType.PREFERENCE)
        assert "brief" in tags3
        assert "preference" in tags3
    
    @pytest.mark.asyncio
    async def test_extract_facts(self, memory_service):
        """Test fact extraction from content."""
        content = "I am John. I like pizza. I work at Google. I live in San Francisco."
        facts = await memory_service._extract_facts(content)
        
        assert len(facts) > 0
        # Should extract sentences with fact patterns
        fact_contents = " ".join(facts)
        assert "I am" in fact_contents or "I like" in fact_contents or "I work at" in fact_contents or "I live in" in fact_contents
    
    def test_passes_web_ui_filters(self, memory_service):
        """Test web UI filter logic."""
        web_data = {
            "ui_source": "web",
            "memory_type": "preference", 
            "importance_score": 7,
            "user_confirmed": True,
            "ai_generated": False,
            "conversation_id": "conv-123"
        }
        
        # Test passing filters
        query1 = WebUIMemoryQuery(
            text="test",
            ui_source=UISource.WEB,
            memory_types=[MemoryType.PREFERENCE],
            importance_range=(5, 10),
            only_user_confirmed=True,
            conversation_id="conv-123"
        )
        assert memory_service._passes_web_ui_filters(web_data, query1) is True
        
        # Test failing UI source filter
        query2 = WebUIMemoryQuery(
            text="test",
            ui_source=UISource.DESKTOP
        )
        assert memory_service._passes_web_ui_filters(web_data, query2) is False
        
        # Test failing importance range filter
        query3 = WebUIMemoryQuery(
            text="test",
            importance_range=(8, 10)
        )
        assert memory_service._passes_web_ui_filters(web_data, query3) is False
        
        # Test failing user confirmed filter
        web_data_unconfirmed = web_data.copy()
        web_data_unconfirmed["user_confirmed"] = False
        query4 = WebUIMemoryQuery(
            text="test",
            only_user_confirmed=True
        )
        assert memory_service._passes_web_ui_filters(web_data_unconfirmed, query4) is False
    
    def test_get_metrics(self, memory_service, mock_base_manager):
        """Test getting combined metrics."""
        # Setup base manager metrics
        mock_base_manager.metrics = {
            "queries_total": 100,
            "memories_stored": 50
        }
        
        # Setup web UI metrics
        memory_service.web_ui_metrics = {
            "context_builds": 25,
            "web_ui_queries": 75
        }
        
        # Execute
        metrics = memory_service.get_metrics()
        
        # Verify combined metrics
        assert metrics["queries_total"] == 100
        assert metrics["memories_stored"] == 50
        assert metrics["context_builds"] == 25
        assert metrics["web_ui_queries"] == 75
    
    @pytest.mark.asyncio
    async def test_store_memory_with_ttl(self, memory_service, mock_base_manager):
        """Test storing memory with TTL."""
        # Setup
        tenant_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        content = "Temporary memory"
        
        mock_base_manager.store_memory = AsyncMock(return_value="memory-ttl")
        memory_service._update_web_ui_fields = AsyncMock()
        memory_service._generate_auto_tags = AsyncMock(return_value=["temp"])
        memory_service._extract_facts = AsyncMock(return_value=[])
        
        # Execute
        result = await memory_service.store_web_ui_memory(
            tenant_id=tenant_id,
            content=content,
            user_id=user_id,
            ui_source=UISource.WEB,
            memory_type=MemoryType.GENERAL,
            ttl_hours=24
        )
        
        # Verify
        assert result == "memory-ttl"
        call_args = mock_base_manager.store_memory.call_args
        assert call_args.kwargs["ttl_hours"] == 24

    @pytest.mark.asyncio
    async def test_store_memory_without_user_id(self, memory_service, mock_base_manager):
        """Ensure memories can be stored when user_id is missing."""
        tenant_id = str(uuid.uuid4())
        content = "Anonymous memory"

        mock_base_manager.store_memory = AsyncMock(return_value="memory-anon")
        memory_service._update_web_ui_fields = AsyncMock()
        memory_service._generate_auto_tags = AsyncMock(return_value=[])
        memory_service._extract_facts = AsyncMock(return_value=[])

        result = await memory_service.store_web_ui_memory(
            tenant_id=tenant_id,
            content=content,
            user_id=None,
            ui_source=UISource.WEB,
            memory_type=MemoryType.GENERAL,
        )

        assert result == "memory-anon"
        call_args = mock_base_manager.store_memory.call_args
        assert call_args.kwargs["user_id"] is None
    
    @pytest.mark.asyncio
    async def test_store_memory_error_handling(self, memory_service, mock_base_manager):
        """Test error handling in memory storage."""
        # Setup
        tenant_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        content = "Test content"
        
        mock_base_manager.store_memory = AsyncMock(side_effect=Exception("Database error"))
        memory_service._generate_auto_tags = AsyncMock(return_value=[])
        memory_service._extract_facts = AsyncMock(return_value=[])
        
        # Execute and verify exception is raised
        with pytest.raises(Exception, match="Database error"):
            await memory_service.store_web_ui_memory(
                tenant_id=tenant_id,
                content=content,
                user_id=user_id,
                ui_source=UISource.WEB
            )
    
    @pytest.mark.asyncio
    async def test_query_memories_error_handling(self, memory_service, mock_base_manager):
        """Test error handling in memory querying."""
        # Setup
        tenant_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        
        mock_base_manager.query_memories = AsyncMock(side_effect=Exception("Query error"))
        
        query = WebUIMemoryQuery(
            text="test query",
            user_id=user_id
        )
        
        # Execute and verify exception is raised
        with pytest.raises(Exception, match="Query error"):
            await memory_service.query_memories(tenant_id, query)
    
    @pytest.mark.asyncio
    async def test_confirm_memory_error_handling(self, memory_service):
        """Test error handling in memory confirmation."""
        # Setup
        tenant_id = str(uuid.uuid4())
        memory_id = "memory-123"
        
        # Mock database session that raises an error
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(side_effect=Exception("Database error"))
        
        memory_service.db_client.get_async_session = AsyncMock()
        memory_service.db_client.get_async_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        memory_service.db_client.get_async_session.return_value.__aexit__ = AsyncMock(return_value=None)
        
        # Execute
        result = await memory_service.confirm_memory(tenant_id, memory_id, confirmed=True)
        
        # Verify error is handled gracefully
        assert result is False
    
    @pytest.mark.asyncio
    async def test_update_memory_importance_error_handling(self, memory_service):
        """Test error handling in importance update."""
        # Setup
        tenant_id = str(uuid.uuid4())
        memory_id = "memory-123"
        
        # Mock database session that raises an error
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(side_effect=Exception("Database error"))
        
        memory_service.db_client.get_async_session = AsyncMock()
        memory_service.db_client.get_async_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        memory_service.db_client.get_async_session.return_value.__aexit__ = AsyncMock(return_value=None)
        
        # Execute
        result = await memory_service.update_memory_importance(tenant_id, memory_id, 8)
        
        # Verify error is handled gracefully
        assert result is False
    
    @pytest.mark.asyncio
    async def test_get_memory_analytics_empty_result(self, memory_service):
        """Test analytics with no memories."""
        # Setup
        tenant_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        
        # Mock empty database result
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock()
        mock_session.execute.return_value.fetchall.return_value = []
        
        memory_service.db_client.get_async_session = AsyncMock()
        memory_service.db_client.get_async_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        memory_service.db_client.get_async_session.return_value.__aexit__ = AsyncMock(return_value=None)
        
        # Execute
        analytics = await memory_service.get_memory_analytics(tenant_id, user_id)
        
        # Verify
        assert analytics["total_memories"] == 0
        assert analytics["memories_by_type"] == {}
        assert analytics["average_importance"] == 0
        assert analytics["most_accessed_memories"] == []
    
    @pytest.mark.asyncio
    async def test_get_memory_analytics_error_handling(self, memory_service):
        """Test error handling in analytics."""
        # Setup
        tenant_id = str(uuid.uuid4())
        
        # Mock database session that raises an error
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(side_effect=Exception("Database error"))
        
        memory_service.db_client.get_async_session = AsyncMock()
        memory_service.db_client.get_async_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        memory_service.db_client.get_async_session.return_value.__aexit__ = AsyncMock(return_value=None)
        
        # Execute
        analytics = await memory_service.get_memory_analytics(tenant_id)
        
        # Verify error is handled gracefully
        assert "error" in analytics
        assert "Database error" in analytics["error"]
    
    @pytest.mark.asyncio
    async def test_increment_access_count_error_handling(self, memory_service):
        """Test error handling in access count increment."""
        # Setup
        tenant_id = str(uuid.uuid4())
        memory_id = "memory-123"
        
        # Mock database session that raises an error
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(side_effect=Exception("Database error"))
        
        memory_service.db_client.get_async_session = AsyncMock()
        memory_service.db_client.get_async_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        memory_service.db_client.get_async_session.return_value.__aexit__ = AsyncMock(return_value=None)
        
        # Execute - should not raise exception
        await memory_service._increment_access_count(tenant_id, memory_id)
        
        # Verify it was called (error is logged but not raised)
        mock_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_web_ui_memory_data_error_handling(self, memory_service):
        """Test error handling in web UI data retrieval."""
        # Setup
        tenant_id = str(uuid.uuid4())
        memory_ids = ["memory-1", "memory-2"]
        
        # Mock database session that raises an error
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(side_effect=Exception("Database error"))
        
        memory_service.db_client.get_async_session = AsyncMock()
        memory_service.db_client.get_async_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        memory_service.db_client.get_async_session.return_value.__aexit__ = AsyncMock(return_value=None)
        
        # Execute
        result = await memory_service._get_web_ui_memory_data(tenant_id, memory_ids)
        
        # Verify error is handled gracefully
        assert result == {}
    
    def test_webui_memory_entry_to_dict(self):
        """Test WebUIMemoryEntry to_dict conversion."""
        # Create a WebUIMemoryEntry
        entry = WebUIMemoryEntry(
            id="memory-123",
            content="Test content",
            timestamp=1234567890,
            user_id="user-123",
            tags=["test", "memory"],
            ui_source=UISource.WEB,
            conversation_id="conv-123",
            memory_type=MemoryType.PREFERENCE,
            importance_score=8,
            access_count=5,
            ai_generated=True,
            user_confirmed=False
        )
        
        # Convert to dict
        result = entry.to_dict()
        
        # Verify all fields are present
        assert result["id"] == "memory-123"
        assert result["content"] == "Test content"
        assert result["ui_source"] == "web"
        assert result["conversation_id"] == "conv-123"
        assert result["memory_type"] == "preference"
        assert result["importance_score"] == 8
        assert result["access_count"] == 5
        assert result["ai_generated"] is True
        assert result["user_confirmed"] is False
    
    def test_webui_memory_query_to_memory_query(self):
        """Test WebUIMemoryQuery conversion to base MemoryQuery."""
        # Create WebUIMemoryQuery
        web_query = WebUIMemoryQuery(
            text="test query",
            user_id="user-123",
            session_id="session-123",
            tags=["test"],
            top_k=15,
            similarity_threshold=0.8
        )
        
        # Convert to base query
        base_query = web_query.to_memory_query()
        
        # Verify conversion
        assert base_query.text == "test query"
        assert base_query.user_id == "user-123"
        assert base_query.session_id == "session-123"
        assert base_query.tags == ["test"]
        assert base_query.top_k == 15
        assert base_query.similarity_threshold == 0.8


class TestMemoryContextBuilder:
    """Test cases for MemoryContextBuilder."""
    
    @pytest.fixture
    def mock_memory_service(self):
        """Mock memory service."""
        service = Mock(spec=WebUIMemoryService)
        service.db_client = Mock()
        return service
    
    @pytest.fixture
    def context_builder(self, mock_memory_service):
        """Create MemoryContextBuilder instance."""
        return MemoryContextBuilder(mock_memory_service)
    
    @pytest.mark.asyncio
    async def test_build_context_with_different_memory_types(self, context_builder, mock_memory_service):
        """Test context building with different memory types."""
        # Setup memories with different types and importance
        memories = [
            WebUIMemoryEntry(
                id="fact-1",
                content="I am vegetarian",
                memory_type=MemoryType.FACT,
                importance_score=9,
                similarity_score=0.9,
                timestamp=1234567890,
                tags=["diet"]
            ),
            WebUIMemoryEntry(
                id="pref-1",
                content="I prefer Italian restaurants",
                memory_type=MemoryType.PREFERENCE,
                importance_score=8,
                similarity_score=0.8,
                timestamp=1234567880,
                tags=["food"]
            ),
            WebUIMemoryEntry(
                id="general-1",
                content="We talked about food yesterday",
                memory_type=MemoryType.GENERAL,
                importance_score=5,
                similarity_score=0.6,
                timestamp=1234567870,
                tags=["conversation"]
            )
        ]
        
        mock_memory_service.query_memories = AsyncMock(return_value=memories)
        context_builder._get_conversation_context = AsyncMock(return_value=None)
        
        # Execute
        context = await context_builder.build_context(
            tenant_id="tenant-123",
            query="What food do I like?",
            user_id="user-123"
        )
        
        # Verify
        assert context["total_memories"] == 3
        assert len(context["memories"]) == 3
        
        # Check ordering - facts should come first (highest weight)
        memory_types = [m["type"] for m in context["memories"]]
        assert memory_types[0] == "fact"  # Highest weight
        assert memory_types[1] == "preference"  # Second highest
        assert memory_types[2] == "general"  # Lowest weight
    
    @pytest.mark.asyncio
    async def test_build_context_token_limit(self, context_builder, mock_memory_service):
        """Test that context respects token limits."""
        # Create a memory with very long content
        long_content = "This is a very long memory content. " * 200  # ~1400 characters
        
        memories = [
            WebUIMemoryEntry(
                id="long-1",
                content=long_content,
                memory_type=MemoryType.FACT,
                importance_score=9,
                similarity_score=0.9,
                timestamp=1234567890,
                tags=["long"]
            ),
            WebUIMemoryEntry(
                id="short-1",
                content="Short memory",
                memory_type=MemoryType.FACT,
                importance_score=8,
                similarity_score=0.8,
                timestamp=1234567880,
                tags=["short"]
            )
        ]
        
        mock_memory_service.query_memories = AsyncMock(return_value=memories)
        context_builder._get_conversation_context = AsyncMock(return_value=None)
        
        # Set a low token limit for testing
        context_builder.max_context_tokens = 500
        
        # Execute
        context = await context_builder.build_context(
            tenant_id="tenant-123",
            query="test",
            user_id="user-123"
        )
        
        # Verify that context respects token limit
        total_tokens = context["context_metadata"]["total_tokens_estimate"]
        assert total_tokens <= context_builder.max_context_tokens
        
        # Should include the long memory but not the short one due to token limit
        assert len(context["memories"]) == 1
        assert context["memories"][0]["content"] == long_content
    
    @pytest.mark.asyncio
    async def test_build_context_with_conversation_id(self, context_builder, mock_memory_service):
        """Test context building with conversation context."""
        # Setup
        conversation_id = "conv-123"
        memories = [
            WebUIMemoryEntry(
                id="mem-1",
                content="Test memory",
                memory_type=MemoryType.GENERAL,
                importance_score=5,
                similarity_score=0.7,
                timestamp=1234567890,
                tags=["test"]
            )
        ]
        
        conversation_context = {
            "title": "Test Conversation",
            "summary": "A test conversation about various topics",
            "ui_context": {"theme": "dark"},
            "ai_insights": ["User prefers concise answers"],
            "user_settings": {"language": "en"},
            "tags": ["test", "conversation"],
            "last_updated": "2024-01-01T00:00:00"
        }
        
        mock_memory_service.query_memories = AsyncMock(return_value=memories)
        context_builder._get_conversation_context = AsyncMock(return_value=conversation_context)
        
        # Execute
        context = await context_builder.build_context(
            tenant_id="tenant-123",
            query="test query",
            user_id="user-123",
            conversation_id=conversation_id
        )
        
        # Verify
        assert context["conversation_context"] == conversation_context
        assert context["context_metadata"]["conversation_id"] == conversation_id
        context_builder._get_conversation_context.assert_called_once_with("tenant-123", conversation_id)
    
    @pytest.mark.asyncio
    async def test_build_context_error_handling(self, context_builder, mock_memory_service):
        """Test error handling in context building."""
        # Setup
        mock_memory_service.query_memories = AsyncMock(side_effect=Exception("Query failed"))
        
        # Execute
        context = await context_builder.build_context(
            tenant_id="tenant-123",
            query="test query",
            user_id="user-123"
        )
        
        # Verify error is handled gracefully
        assert context["memories"] == []
        assert context["total_memories"] == 0
        assert context["memory_types_found"] == []
        assert context["conversation_context"] is None
        assert "error" in context
        assert "Query failed" in context["error"]
    
    @pytest.mark.asyncio
    async def test_get_conversation_context_success(self, context_builder, mock_memory_service):
        """Test successful conversation context retrieval."""
        # Setup
        tenant_id = "tenant-123"
        conversation_id = "conv-123"
        
        # Mock conversation object
        mock_conversation = Mock()
        mock_conversation.title = "Test Conversation"
        mock_conversation.summary = "A test conversation"
        mock_conversation.ui_context = {"theme": "light"}
        mock_conversation.ai_insights = ["User is helpful"]
        mock_conversation.user_settings = {"notifications": True}
        mock_conversation.tags = ["test"]
        mock_conversation.updated_at = datetime(2024, 1, 1, 12, 0, 0)
        
        # Mock database session
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock()
        mock_session.execute.return_value.scalar_one_or_none.return_value = mock_conversation
        
        mock_memory_service.db_client.get_async_session = AsyncMock()
        mock_memory_service.db_client.get_async_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_memory_service.db_client.get_async_session.return_value.__aexit__ = AsyncMock(return_value=None)
        
        # Execute
        result = await context_builder._get_conversation_context(tenant_id, conversation_id)
        
        # Verify
        assert result is not None
        assert result["title"] == "Test Conversation"
        assert result["summary"] == "A test conversation"
        assert result["ui_context"] == {"theme": "light"}
        assert result["ai_insights"] == ["User is helpful"]
        assert result["user_settings"] == {"notifications": True}
        assert result["tags"] == ["test"]
        assert result["last_updated"] == "2024-01-01T12:00:00"
    
    @pytest.mark.asyncio
    async def test_get_conversation_context_not_found(self, context_builder, mock_memory_service):
        """Test conversation context when conversation not found."""
        # Setup
        tenant_id = "tenant-123"
        conversation_id = "conv-nonexistent"
        
        # Mock database session returning None
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock()
        mock_session.execute.return_value.scalar_one_or_none.return_value = None
        
        mock_memory_service.db_client.get_async_session = AsyncMock()
        mock_memory_service.db_client.get_async_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_memory_service.db_client.get_async_session.return_value.__aexit__ = AsyncMock(return_value=None)
        
        # Execute
        result = await context_builder._get_conversation_context(tenant_id, conversation_id)
        
        # Verify
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_conversation_context_error_handling(self, context_builder, mock_memory_service):
        """Test error handling in conversation context retrieval."""
        # Setup
        tenant_id = "tenant-123"
        conversation_id = "conv-123"
        
        # Mock database session that raises an error
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(side_effect=Exception("Database error"))
        
        mock_memory_service.db_client.get_async_session = AsyncMock()
        mock_memory_service.db_client.get_async_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_memory_service.db_client.get_async_session.return_value.__aexit__ = AsyncMock(return_value=None)
        
        # Execute
        result = await context_builder._get_conversation_context(tenant_id, conversation_id)
        
        # Verify error is handled gracefully
        assert result is None


class TestWebUIMemoryServiceIntegration:
    """Integration-style tests for WebUIMemoryService."""
    
    @pytest.fixture
    def mock_base_manager(self):
        """Mock base memory manager with more realistic behavior."""
        manager = Mock(spec=MemoryManager)
        manager.db_client = Mock()
        manager.metrics = {
            "queries_total": 0,
            "memories_stored": 0,
            "memories_retrieved": 0
        }
        return manager
    
    @pytest.fixture
    def memory_service(self, mock_base_manager):
        """Create WebUIMemoryService instance."""
        return WebUIMemoryService(mock_base_manager)
    
    @pytest.mark.asyncio
    async def test_full_memory_lifecycle(self, memory_service, mock_base_manager):
        """Test complete memory lifecycle: store -> query -> update -> confirm."""
        # Setup
        tenant_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        content = "I prefer vegetarian restaurants"
        
        # Mock storage
        mock_base_manager.store_memory = AsyncMock(return_value="memory-lifecycle")
        memory_service._update_web_ui_fields = AsyncMock()
        memory_service._generate_auto_tags = AsyncMock(return_value=["food", "preference", "vegetarian"])
        memory_service._extract_facts = AsyncMock(return_value=["User prefers vegetarian restaurants"])
        
        # 1. Store memory
        memory_id = await memory_service.store_web_ui_memory(
            tenant_id=tenant_id,
            content=content,
            user_id=user_id,
            ui_source=UISource.WEB,
            memory_type=MemoryType.PREFERENCE,
            ai_generated=True,  # AI generated, needs confirmation
            importance_score=7
        )
        
        assert memory_id == "memory-lifecycle"
        
        # 2. Query memory
        base_memory = MemoryEntry(
            id=memory_id,
            content=content,
            timestamp=1234567890,
            user_id=user_id,
            tags=["food", "preference", "vegetarian"]
        )
        
        mock_base_manager.query_memories = AsyncMock(return_value=[base_memory])
        memory_service._get_web_ui_memory_data = AsyncMock(return_value={
            memory_id: {
                "ui_source": "web",
                "memory_type": "preference",
                "importance_score": 7,
                "access_count": 0,
                "ai_generated": True,
                "user_confirmed": False
            }
        })
        memory_service._increment_access_count = AsyncMock()
        
        query = WebUIMemoryQuery(
            text="vegetarian food",
            user_id=user_id,
            memory_types=[MemoryType.PREFERENCE]
        )
        
        results = await memory_service.query_memories(tenant_id, query)
        assert len(results) == 1
        assert results[0].ai_generated is True
        assert results[0].user_confirmed is False
        
        # 3. Update importance
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock()
        mock_session.commit = AsyncMock()
        
        memory_service.db_client.get_async_session = AsyncMock()
        memory_service.db_client.get_async_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        memory_service.db_client.get_async_session.return_value.__aexit__ = AsyncMock(return_value=None)
        
        update_result = await memory_service.update_memory_importance(tenant_id, memory_id, 9)
        assert update_result is True
        
        # 4. Confirm memory
        confirm_result = await memory_service.confirm_memory(tenant_id, memory_id, confirmed=True)
        assert confirm_result is True
        assert memory_service.web_ui_metrics["memory_confirmations"] == 1
    
    @pytest.mark.asyncio
    async def test_context_building_with_multiple_memory_types(self, memory_service):
        """Test context building with various memory types and priorities."""
        # Setup
        tenant_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        query = "Tell me about my food preferences and dietary restrictions"
        
        # Create diverse memories
        memories = [
            WebUIMemoryEntry(
                id="fact-diet",
                content="I am allergic to nuts",
                memory_type=MemoryType.FACT,
                importance_score=10,  # Critical health info
                similarity_score=0.9,
                timestamp=1234567890,
                tags=["health", "allergy", "nuts"]
            ),
            WebUIMemoryEntry(
                id="pref-cuisine",
                content="I love Mediterranean cuisine",
                memory_type=MemoryType.PREFERENCE,
                importance_score=8,
                similarity_score=0.8,
                timestamp=1234567880,
                tags=["food", "mediterranean", "preference"]
            ),
            WebUIMemoryEntry(
                id="context-restaurant",
                content="Last visited Tony's Italian Restaurant",
                memory_type=MemoryType.CONTEXT,
                importance_score=6,
                similarity_score=0.7,
                timestamp=1234567870,
                tags=["restaurant", "italian", "recent"]
            ),
            WebUIMemoryEntry(
                id="insight-pattern",
                content="User tends to prefer lighter meals in the evening",
                memory_type=MemoryType.INSIGHT,
                importance_score=7,
                similarity_score=0.6,
                timestamp=1234567860,
                tags=["pattern", "evening", "light"],
                ai_generated=True,
                user_confirmed=True
            ),
            WebUIMemoryEntry(
                id="general-comment",
                content="Food is important for social gatherings",
                memory_type=MemoryType.GENERAL,
                importance_score=4,
                similarity_score=0.5,
                timestamp=1234567850,
                tags=["social", "general"]
            )
        ]
        
        memory_service.query_memories = AsyncMock(return_value=memories)
        memory_service.context_builder._get_conversation_context = AsyncMock(return_value=None)
        
        # Execute
        context = await memory_service.build_conversation_context(
            tenant_id=tenant_id,
            query=query,
            user_id=user_id
        )
        
        # Verify context structure and ordering
        assert context["total_memories"] == 5
        assert len(context["memories"]) == 5
        
        # Check that memories are ordered by type weight and importance
        memory_types = [m["type"] for m in context["memories"]]
        expected_order = ["fact", "preference", "context", "insight", "general"]
        assert memory_types == expected_order
        
        # Verify the critical health fact comes first
        first_memory = context["memories"][0]
        assert first_memory["content"] == "I am allergic to nuts"
        assert first_memory["importance"] == 10
        
        # Check memory types found
        assert set(context["memory_types_found"]) == {
            MemoryType.FACT, MemoryType.PREFERENCE, MemoryType.CONTEXT, 
            MemoryType.INSIGHT, MemoryType.GENERAL
        }
        
        # Verify metrics were updated
        assert memory_service.web_ui_metrics["context_builds"] == 1
    
    @pytest.mark.asyncio
    async def test_analytics_comprehensive(self, memory_service):
        """Test comprehensive analytics with diverse memory data."""
        # Setup
        tenant_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        
        # Create mock memories with diverse characteristics
        now = datetime.utcnow()
        mock_memories = []
        
        # Recent AI-generated memory (unconfirmed)
        mem1 = Mock()
        mem1.memory_type = "insight"
        mem1.ui_source = "web"
        mem1.importance_score = 8
        mem1.ai_generated = True
        mem1.user_confirmed = False
        mem1.tags = ["ai", "insight", "pattern"]
        mem1.vector_id = "mem-1"
        mem1.content = "User prefers quick meals during weekdays"
        mem1.access_count = 3
        mem1.created_at = now - timedelta(hours=2)
        mock_memories.append(mem1)
        
        # User-created preference (confirmed)
        mem2 = Mock()
        mem2.memory_type = "preference"
        mem2.ui_source = "desktop"
        mem2.importance_score = 9
        mem2.ai_generated = False
        mem2.user_confirmed = True
        mem2.tags = ["food", "preference", "spicy"]
        mem2.vector_id = "mem-2"
        mem2.content = "I love spicy food"
        mem2.access_count = 15
        mem2.created_at = now - timedelta(days=1)
        mock_memories.append(mem2)
        
        # Old general memory
        mem3 = Mock()
        mem3.memory_type = "general"
        mem3.ui_source = "api"
        mem3.importance_score = 5
        mem3.ai_generated = False
        mem3.user_confirmed = True
        mem3.tags = ["general", "conversation"]
        mem3.vector_id = "mem-3"
        mem3.content = "We discussed various topics"
        mem3.access_count = 1
        mem3.created_at = now - timedelta(days=30)
        mock_memories.append(mem3)
        
        # Mock database sessions for different queries
        mock_session = AsyncMock()
        
        # Main query returns all memories
        mock_session.execute = AsyncMock()
        mock_session.execute.return_value.fetchall.return_value = mock_memories
        
        memory_service.db_client.get_async_session = AsyncMock()
        memory_service.db_client.get_async_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        memory_service.db_client.get_async_session.return_value.__aexit__ = AsyncMock(return_value=None)
        
        # Execute
        analytics = await memory_service.get_memory_analytics(tenant_id, user_id)
        
        # Verify comprehensive analytics
        assert analytics["total_memories"] == 3
        
        # Memory type distribution
        assert analytics["memories_by_type"]["insight"] == 1
        assert analytics["memories_by_type"]["preference"] == 1
        assert analytics["memories_by_type"]["general"] == 1
        
        # UI source distribution
        assert analytics["memories_by_ui_source"]["web"] == 1
        assert analytics["memories_by_ui_source"]["desktop"] == 1
        assert analytics["memories_by_ui_source"]["api"] == 1
        
        # Importance distribution
        assert analytics["memories_by_importance"]["8"] == 1
        assert analytics["memories_by_importance"]["9"] == 1
        assert analytics["memories_by_importance"]["5"] == 1
        
        # AI vs user content
        assert analytics["ai_generated_count"] == 1
        assert analytics["user_confirmed_count"] == 2
        
        # Average importance
        expected_avg = (8 + 9 + 5) / 3
        assert analytics["average_importance"] == expected_avg
        
        # Tag frequency
        assert analytics["tag_frequency"]["food"] == 1
        assert analytics["tag_frequency"]["preference"] == 1
        assert analytics["tag_frequency"]["general"] == 1
        assert analytics["tag_frequency"]["ai"] == 1
        
        # Web UI metrics included
        assert "web_ui_metrics" in analytics
        assert analytics["web_ui_metrics"] == memory_service.web_ui_metrics
        
        # Verify that context respects token limit
        total_tokens = context["context_metadata"]["total_tokens_estimate"]
        assert total_tokens <= context_builder.max_context_tokens
        
        # Should include the long memory but not the short one due to token limit
        assert len(context["memories"]) == 1
        assert context["memories"][0]["content"] == long_content