"""
Unit tests for WebUIConversationService.
"""

import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

from src.ai_karen_engine.services.conversation_service import (
    WebUIConversationService,
    WebUIConversation,
    WebUIMessage,
    ConversationStatus,
    ConversationPriority,
    ConversationContextBuilder,
    UISource
)
from src.ai_karen_engine.database.conversation_manager import (
    ConversationManager,
    Conversation,
    Message,
    MessageRole
)
from src.ai_karen_engine.services.memory_service import WebUIMemoryService


class TestWebUIConversationService:
    """Test cases for WebUIConversationService."""
    
    @pytest.fixture
    def mock_base_manager(self):
        """Mock base conversation manager."""
        manager = Mock(spec=ConversationManager)
        manager.db_client = Mock()
        manager.metrics = {
            "conversations_created": 0,
            "messages_added": 0,
            "conversations_retrieved": 0
        }
        return manager
    
    @pytest.fixture
    def mock_memory_service(self):
        """Mock memory service."""
        service = Mock(spec=WebUIMemoryService)
        service.store_web_ui_memory = AsyncMock()
        service.build_conversation_context = AsyncMock()
        return service
    
    @pytest.fixture
    def conversation_service(self, mock_base_manager, mock_memory_service):
        """Create WebUIConversationService instance."""
        return WebUIConversationService(mock_base_manager, mock_memory_service)
    
    @pytest.mark.asyncio
    async def test_create_web_ui_conversation(self, conversation_service, mock_base_manager, mock_memory_service):
        """Test creating web UI conversation."""
        # Setup
        tenant_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        session_id = "session-123"
        
        # Mock base conversation
        base_conversation = Conversation(
            id=str(uuid.uuid4()),
            user_id=user_id,
            title="Test Conversation",
            messages=[],
            metadata={}
        )
        
        mock_base_manager.create_conversation = AsyncMock(return_value=base_conversation)
        conversation_service._update_web_ui_conversation_fields = AsyncMock()
        conversation_service._convert_to_web_ui_conversation = AsyncMock()
        
        # Mock converted conversation
        web_ui_conversation = WebUIConversation(
            id=base_conversation.id,
            user_id=user_id,
            title="Test Conversation",
            messages=[],
            session_id=session_id,
            ui_context={"test": "context"},
            priority=ConversationPriority.NORMAL
        )
        conversation_service._convert_to_web_ui_conversation.return_value = web_ui_conversation
        
        # Execute
        result = await conversation_service.create_web_ui_conversation(
            tenant_id=tenant_id,
            user_id=user_id,
            session_id=session_id,
            ui_source=UISource.WEB,
            title="Test Conversation",
            initial_message="Hello",
            user_settings={"theme": "dark"},
            ui_context={"test": "context"},
            tags=["test", "conversation"],
            priority=ConversationPriority.HIGH
        )
        
        # Verify
        assert result is not None
        assert result.id == base_conversation.id
        assert result.session_id == session_id
        assert result.priority == ConversationPriority.NORMAL  # From mock
        
        # Verify base manager was called
        mock_base_manager.create_conversation.assert_called_once()
        call_args = mock_base_manager.create_conversation.call_args
        assert call_args.kwargs["user_id"] == user_id
        assert call_args.kwargs["title"] == "Test Conversation"
        assert call_args.kwargs["initial_message"] == "Hello"
        
        # Verify metadata includes web UI fields
        metadata = call_args.kwargs["metadata"]
        assert metadata["ui_source"] == "web"
        assert metadata["session_id"] == session_id
        assert metadata["priority"] == "high"
        
        # Verify memory storage was called for initial message
        mock_memory_service.store_web_ui_memory.assert_called_once()
        
        # Verify metrics updated
        assert conversation_service.web_ui_metrics["web_ui_conversations_created"] == 1
    
    @pytest.mark.asyncio
    async def test_get_web_ui_conversation(self, conversation_service, mock_base_manager):
        """Test getting web UI conversation."""
        # Setup
        tenant_id = str(uuid.uuid4())
        conversation_id = str(uuid.uuid4())
        
        # Mock base conversation
        base_conversation = Conversation(
            id=conversation_id,
            user_id=str(uuid.uuid4()),
            title="Test Conversation",
            messages=[],
            metadata={}
        )
        
        mock_base_manager.get_conversation = AsyncMock(return_value=base_conversation)
        conversation_service._get_web_ui_conversation_data = AsyncMock(return_value={
            "session_id": "session-123",
            "ui_context": {"theme": "dark"},
            "user_settings": {"notifications": True},
            "tags": ["test"],
            "priority": "high",
            "summary": "Test summary"
        })
        conversation_service._convert_to_web_ui_conversation = AsyncMock()
        conversation_service._add_web_ui_context = AsyncMock()
        
        # Mock converted conversation
        web_ui_conversation = WebUIConversation(
            id=conversation_id,
            user_id=base_conversation.user_id,
            title="Test Conversation",
            messages=[],
            session_id="session-123"
        )
        conversation_service._convert_to_web_ui_conversation.return_value = web_ui_conversation
        
        # Execute
        result = await conversation_service.get_web_ui_conversation(
            tenant_id, conversation_id, include_context=True
        )
        
        # Verify
        assert result is not None
        assert result.id == conversation_id
        
        # Verify base manager was called
        mock_base_manager.get_conversation.assert_called_once_with(
            tenant_id, conversation_id, include_context=False
        )
        
        # Verify web UI data was fetched
        conversation_service._get_web_ui_conversation_data.assert_called_once_with(
            tenant_id, conversation_id
        )
        
        # Verify context was added
        conversation_service._add_web_ui_context.assert_called_once_with(
            tenant_id, web_ui_conversation
        )
    
    @pytest.mark.asyncio
    async def test_add_web_ui_message(self, conversation_service, mock_base_manager, mock_memory_service):
        """Test adding web UI message."""
        # Setup
        tenant_id = str(uuid.uuid4())
        conversation_id = str(uuid.uuid4())
        
        # Mock base message
        base_message = Message(
            id=str(uuid.uuid4()),
            role=MessageRole.USER,
            content="Hello there",
            timestamp=datetime.utcnow(),
            metadata={"ui_source": "web"}
        )
        
        mock_base_manager.add_message = AsyncMock(return_value=base_message)
        conversation_service._generate_proactive_suggestions = AsyncMock()
        conversation_service.get_web_ui_conversation = AsyncMock()
        
        # Mock conversation for auto-summarize check
        mock_conversation = Mock()
        mock_conversation.messages = [Mock() for _ in range(49)]  # Just below threshold
        conversation_service.get_web_ui_conversation.return_value = mock_conversation
        
        # Execute
        result = await conversation_service.add_web_ui_message(
            tenant_id=tenant_id,
            conversation_id=conversation_id,
            role=MessageRole.USER,
            content="Hello there",
            ui_source=UISource.WEB,
            ai_confidence=0.95,
            processing_time_ms=150,
            tokens_used=10,
            model_used="gpt-4"
        )
        
        # Verify
        assert result is not None
        assert isinstance(result, WebUIMessage)
        assert result.id == base_message.id
        assert result.content == "Hello there"
        assert result.ui_source == UISource.WEB
        assert result.ai_confidence == 0.95
        assert result.processing_time_ms == 150
        assert result.tokens_used == 10
        assert result.model_used == "gpt-4"
        
        # Verify base manager was called with web UI metadata
        mock_base_manager.add_message.assert_called_once()
        call_args = mock_base_manager.add_message.call_args
        metadata = call_args.kwargs["metadata"]
        assert metadata["ui_source"] == "web"
        assert metadata["ai_confidence"] == 0.95
        assert metadata["processing_time_ms"] == 150
        
        # Verify memory storage for user message
        mock_memory_service.store_web_ui_memory.assert_called_once()
        
        # Verify proactive suggestions were generated
        conversation_service._generate_proactive_suggestions.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_build_conversation_context(self, conversation_service):
        """Test building conversation context."""
        # Setup
        tenant_id = str(uuid.uuid4())
        conversation_id = str(uuid.uuid4())
        current_message = "What's the weather like?"
        
        # Mock context builder
        conversation_service.context_builder = Mock()
        conversation_service.context_builder.build_comprehensive_context = AsyncMock(return_value={
            "conversation_summary": {"id": conversation_id},
            "recent_messages": [],
            "relevant_memories": {"facts": [], "preferences": []},
            "ai_insights": {},
            "context_metadata": {"built_at": datetime.utcnow().isoformat()}
        })
        
        # Execute
        result = await conversation_service.build_conversation_context(
            tenant_id, conversation_id, current_message, 
            include_memories=True, include_insights=True
        )
        
        # Verify
        assert result is not None
        assert "conversation_summary" in result
        assert "recent_messages" in result
        assert "relevant_memories" in result
        assert conversation_service.web_ui_metrics["context_builds"] == 1
        
        # Verify context builder was called
        conversation_service.context_builder.build_comprehensive_context.assert_called_once_with(
            tenant_id, conversation_id, current_message, True, True
        )
    
    @pytest.mark.asyncio
    async def test_update_conversation_ui_context(self, conversation_service):
        """Test updating conversation UI context."""
        # Setup
        tenant_id = str(uuid.uuid4())
        conversation_id = str(uuid.uuid4())
        ui_context = {"theme": "dark", "sidebar_collapsed": True}
        
        # Mock database session
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock()
        mock_session.commit = AsyncMock()
        
        conversation_service.db_client.get_async_session = AsyncMock()
        conversation_service.db_client.get_async_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        conversation_service.db_client.get_async_session.return_value.__aexit__ = AsyncMock(return_value=None)
        
        # Execute
        result = await conversation_service.update_conversation_ui_context(
            tenant_id, conversation_id, ui_context
        )
        
        # Verify
        assert result is True
        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()
        assert conversation_service.web_ui_metrics["ui_context_updates"] == 1
    
    @pytest.mark.asyncio
    async def test_add_conversation_tags(self, conversation_service):
        """Test adding tags to conversation."""
        # Setup
        tenant_id = str(uuid.uuid4())
        conversation_id = str(uuid.uuid4())
        new_tags = ["important", "follow-up"]
        
        # Mock existing conversation
        existing_conversation = WebUIConversation(
            id=conversation_id,
            user_id=str(uuid.uuid4()),
            title="Test",
            messages=[],
            tags=["existing", "tag"]
        )
        
        conversation_service.get_web_ui_conversation = AsyncMock(return_value=existing_conversation)
        
        # Mock database session
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock()
        mock_session.commit = AsyncMock()
        
        conversation_service.db_client.get_async_session = AsyncMock()
        conversation_service.db_client.get_async_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        conversation_service.db_client.get_async_session.return_value.__aexit__ = AsyncMock(return_value=None)
        
        # Execute
        result = await conversation_service.add_conversation_tags(
            tenant_id, conversation_id, new_tags
        )
        
        # Verify
        assert result is True
        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()
        
        # Verify tags were merged (existing + new, no duplicates)
        call_args = mock_session.execute.call_args
        # The exact verification would depend on the SQL update structure
    
    @pytest.mark.asyncio
    async def test_generate_proactive_suggestions(self, conversation_service):
        """Test generating proactive suggestions."""
        # Setup
        tenant_id = str(uuid.uuid4())
        conversation_id = str(uuid.uuid4())
        user_message = "Can you remind me to call mom tomorrow?"
        
        # Mock database session
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock()
        mock_session.commit = AsyncMock()
        
        # Mock current insights query result
        mock_session.execute.return_value.scalar.return_value = {"existing": "insights"}
        
        conversation_service.db_client.get_async_session = AsyncMock()
        conversation_service.db_client.get_async_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        conversation_service.db_client.get_async_session.return_value.__aexit__ = AsyncMock(return_value=None)
        
        # Execute
        await conversation_service._generate_proactive_suggestions(
            tenant_id, conversation_id, user_message
        )
        
        # Verify
        # Should have called database twice (select and update)
        assert mock_session.execute.call_count == 2
        mock_session.commit.assert_called_once()
        assert conversation_service.web_ui_metrics["proactive_suggestions_generated"] == 1
    
    @pytest.mark.asyncio
    async def test_get_conversation_analytics(self, conversation_service, mock_base_manager):
        """Test getting conversation analytics."""
        # Setup
        tenant_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        
        # Mock base stats
        mock_base_manager.get_conversation_stats = AsyncMock(return_value={
            "total_conversations": 10,
            "active_conversations": 8,
            "total_messages": 150
        })
        
        # Mock database session and conversations
        mock_conversation = Mock()
        mock_conversation.ui_context = {"ui_source": "web"}
        mock_conversation.conversation_metadata = {"priority": "high"}
        mock_conversation.tags = ["important", "work"]
        mock_conversation.summary = "Test summary"
        
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock()
        mock_session.execute.return_value.fetchall.return_value = [mock_conversation]
        
        conversation_service.db_client.get_async_session = AsyncMock()
        conversation_service.db_client.get_async_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        conversation_service.db_client.get_async_session.return_value.__aexit__ = AsyncMock(return_value=None)
        
        # Execute
        result = await conversation_service.get_conversation_analytics(
            tenant_id, user_id
        )
        
        # Verify
        assert result["total_conversations"] == 10
        assert result["active_conversations"] == 8
        assert result["total_messages"] == 150
        assert "conversations_by_ui_source" in result
        assert "conversations_by_priority" in result
        assert "conversations_with_tags" in result
        assert "most_common_tags" in result
        assert "web_ui_metrics" in result
        
        # Verify web UI specific analytics
        assert result["conversations_by_ui_source"]["web"] == 1
        assert result["conversations_by_priority"]["high"] == 1
        assert result["conversations_with_tags"] == 1
        assert result["conversations_with_summaries"] == 1
    
    def test_get_metrics(self, conversation_service, mock_base_manager):
        """Test getting combined metrics."""
        # Setup base manager metrics
        mock_base_manager.metrics = {
            "conversations_created": 50,
            "messages_added": 200
        }
        
        # Setup web UI metrics
        conversation_service.web_ui_metrics = {
            "web_ui_conversations_created": 25,
            "context_builds": 75
        }
        
        # Execute
        metrics = conversation_service.get_metrics()
        
        # Verify combined metrics
        assert metrics["conversations_created"] == 50
        assert metrics["messages_added"] == 200
        assert metrics["web_ui_conversations_created"] == 25
        assert metrics["context_builds"] == 75


class TestConversationContextBuilder:
    """Test cases for ConversationContextBuilder."""
    
    @pytest.fixture
    def mock_conversation_service(self):
        """Mock conversation service."""
        service = Mock(spec=WebUIConversationService)
        service.memory_service = Mock()
        return service
    
    @pytest.fixture
    def context_builder(self, mock_conversation_service):
        """Create ConversationContextBuilder instance."""
        return ConversationContextBuilder(mock_conversation_service)
    
    @pytest.mark.asyncio
    async def test_build_comprehensive_context(self, context_builder, mock_conversation_service):
        """Test building comprehensive context."""
        # Setup
        tenant_id = str(uuid.uuid4())
        conversation_id = str(uuid.uuid4())
        current_message = "What should I have for lunch?"
        
        # Mock conversation
        mock_conversation = WebUIConversation(
            id=conversation_id,
            user_id=str(uuid.uuid4()),
            title="Food Discussion",
            messages=[
                WebUIMessage(
                    id="msg-1",
                    role=MessageRole.USER,
                    content="I'm hungry",
                    timestamp=datetime.utcnow()
                )
            ],
            ai_insights={"food_preferences": "vegetarian"},
            user_settings={"dietary_restrictions": ["vegetarian"]}
        )
        
        mock_conversation_service.get_web_ui_conversation = AsyncMock(return_value=mock_conversation)
        context_builder._build_memory_context = AsyncMock(return_value={
            "facts": [{"content": "User is vegetarian"}],
            "preferences": [{"content": "Likes Italian food"}]
        })
        context_builder._build_insights_context = AsyncMock(return_value={
            "conversation_insights": {"topic": "food"}
        })
        context_builder._analyze_conversation_patterns = AsyncMock(return_value={
            "engagement_level": "high"
        })
        
        # Execute
        result = await context_builder.build_comprehensive_context(
            tenant_id, conversation_id, current_message
        )
        
        # Verify
        assert result["conversation_summary"]["conversation_id"] == conversation_id
        assert len(result["recent_messages"]) == 1
        assert result["recent_messages"][0]["content"] == "I'm hungry"
        assert "facts" in result["relevant_memories"]
        assert "preferences" in result["relevant_memories"]
        assert result["ai_insights"]["food_preferences"] == "vegetarian"
        assert result["user_preferences"]["dietary_restrictions"] == ["vegetarian"]
        assert result["conversation_patterns"]["engagement_level"] == "high"
    
    def test_analyze_message_patterns(self, context_builder):
        """Test analyzing message patterns."""
        # Setup messages with different characteristics
        messages = [
            Message(
                id="1",
                role=MessageRole.USER,
                content="Short",
                timestamp=datetime.utcnow()
            ),
            Message(
                id="2",
                role=MessageRole.ASSISTANT,
                content="Response",
                timestamp=datetime.utcnow() + timedelta(seconds=3)
            ),
            Message(
                id="3",
                role=MessageRole.USER,
                content="This is a much longer message with more detail and explanation",
                timestamp=datetime.utcnow() + timedelta(seconds=10)
            )
        ]
        
        # Execute
        patterns = context_builder._analyze_message_patterns(messages)
        
        # Verify
        assert len(patterns) == 2  # response_time and message_length patterns
        
        # Check response time pattern
        response_pattern = next(p for p in patterns if p["type"] == "response_time")
        assert response_pattern["average_seconds"] == 3.0
        assert response_pattern["pattern"] == "fast"
        
        # Check message length pattern
        length_pattern = next(p for p in patterns if p["type"] == "message_length")
        assert length_pattern["pattern"] in ["concise", "balanced", "verbose"]
    
    def test_analyze_user_behavior(self, context_builder):
        """Test analyzing user behavior."""
        # Setup messages with different behavior patterns
        messages = [
            Message(
                id="1",
                role=MessageRole.USER,
                content="What's the weather like?",
                timestamp=datetime.utcnow()
            ),
            Message(
                id="2",
                role=MessageRole.USER,
                content="Please help me with this task, thank you",
                timestamp=datetime.utcnow()
            ),
            Message(
                id="3",
                role=MessageRole.USER,
                content="How do I configure this setting?",
                timestamp=datetime.utcnow()
            )
        ]
        
        # Execute
        behavior = context_builder._analyze_user_behavior(messages)
        
        # Verify
        assert behavior["question_frequency"] == 2/3  # 2 questions out of 3 messages
        assert behavior["politeness_level"] == "moderate"  # Contains "please" and "thank"
        assert behavior["interaction_style"] == "inquisitive"  # High question frequency
    
    def test_analyze_conversation_flow(self, context_builder):
        """Test analyzing conversation flow."""
        # Setup messages with topic changes
        messages = [
            Message(
                id="1",
                role=MessageRole.USER,
                content="Tell me about the weather today",
                timestamp=datetime.utcnow()
            ),
            Message(
                id="2",
                role=MessageRole.USER,
                content="What's the weather forecast for tomorrow",
                timestamp=datetime.utcnow()
            ),
            Message(
                id="3",
                role=MessageRole.USER,
                content="How do I cook pasta",  # Topic change
                timestamp=datetime.utcnow()
            )
        ]
        
        # Execute
        flow = context_builder._analyze_conversation_flow(messages)
        
        # Verify
        assert "topic_changes" in flow
        assert "continuity" in flow
        assert "flow_quality" in flow
        assert "engagement_trend" in flow
        
        # Should detect at least one topic change (weather -> cooking)
        assert flow["topic_changes"] >= 1


class TestWebUIConversation:
    """Test cases for WebUIConversation class."""
    
    def test_add_remove_tags(self):
        """Test adding and removing tags."""
        conversation = WebUIConversation(
            id="conv-1",
            user_id="user-1",
            title="Test",
            messages=[],
            tags=["existing"]
        )
        
        # Test adding tags
        conversation.add_tag("new_tag")
        assert "new_tag" in conversation.tags
        assert "existing" in conversation.tags
        
        # Test adding duplicate tag
        conversation.add_tag("existing")
        assert conversation.tags.count("existing") == 1  # No duplicates
        
        # Test removing tags
        conversation.remove_tag("existing")
        assert "existing" not in conversation.tags
        assert "new_tag" in conversation.tags
    
    def test_update_contexts(self):
        """Test updating UI context and AI insights."""
        conversation = WebUIConversation(
            id="conv-1",
            user_id="user-1",
            title="Test",
            messages=[],
            ui_context={"theme": "light"},
            ai_insights={"sentiment": "positive"}
        )
        
        # Test updating UI context
        conversation.update_ui_context({"sidebar": "collapsed", "theme": "dark"})
        assert conversation.ui_context["theme"] == "dark"
        assert conversation.ui_context["sidebar"] == "collapsed"
        
        # Test updating AI insights
        conversation.update_ai_insights({"confidence": 0.9, "sentiment": "neutral"})
        assert conversation.ai_insights["sentiment"] == "neutral"
        assert conversation.ai_insights["confidence"] == 0.9
    
    def test_get_context_summary(self):
        """Test getting context summary."""
        conversation = WebUIConversation(
            id="conv-1",
            user_id="user-1",
            title="Test",
            messages=[Mock(), Mock()],  # 2 messages
            session_id="session-1",
            tags=["important", "work"],
            priority=ConversationPriority.HIGH,
            status=ConversationStatus.ACTIVE,
            user_settings={"notifications": True},
            ai_insights={"topic": "work"},
            summary="Work discussion"
        )
        
        summary = conversation.get_context_summary()
        
        assert summary["conversation_id"] == "conv-1"
        assert summary["session_id"] == "session-1"
        assert summary["message_count"] == 2
        assert summary["tags"] == ["important", "work"]
        assert summary["priority"] == "high"
        assert summary["status"] == "active"
        assert summary["user_settings"]["notifications"] is True
        assert summary["ai_insights"]["topic"] == "work"
        assert summary["summary"] == "Work discussion"