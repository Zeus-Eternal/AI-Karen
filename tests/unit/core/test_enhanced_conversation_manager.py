"""
Tests for the enhanced conversation manager with advanced features.
"""

import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

from ai_karen_engine.chat.enhanced_conversation_manager import EnhancedConversationManager
from ai_karen_engine.chat.conversation_models import (
    Conversation, ChatMessage, ConversationFolder, ConversationTemplate,
    ConversationFilters, ConversationExportOptions, MessageRole, MessageType,
    ConversationStatus
)
from ai_karen_engine.database.client import MultiTenantPostgresClient


@pytest.fixture
def mock_db_client():
    """Mock database client."""
    client = Mock(spec=MultiTenantPostgresClient)
    
    # Create a proper async context manager mock
    mock_session = AsyncMock()
    mock_context_manager = AsyncMock()
    mock_context_manager.__aenter__ = AsyncMock(return_value=mock_session)
    mock_context_manager.__aexit__ = AsyncMock(return_value=None)
    
    client.get_async_session = Mock(return_value=mock_context_manager)
    
    return client


@pytest.fixture
def mock_distilbert_service():
    """Mock DistilBERT service."""
    service = Mock()
    service.get_embeddings = AsyncMock(return_value=[0.1] * 768)
    return service


@pytest.fixture
def mock_file_storage():
    """Mock file storage service."""
    storage = Mock()
    storage.store_file = AsyncMock()
    storage.get_file = AsyncMock()
    return storage


@pytest.fixture
def conversation_manager(mock_db_client, mock_distilbert_service, mock_file_storage):
    """Create conversation manager with mocked dependencies."""
    return EnhancedConversationManager(
        db_client=mock_db_client,
        distilbert_service=mock_distilbert_service,
        file_storage=mock_file_storage
    )


@pytest.fixture
def sample_conversation():
    """Sample conversation for testing."""
    return Conversation(
        id=str(uuid.uuid4()),
        user_id=str(uuid.uuid4()),
        title="Test Conversation",
        description="A test conversation",
        tags=["test", "sample"],
        is_favorite=True,
        message_count=5,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )


@pytest.fixture
def sample_messages():
    """Sample messages for testing."""
    conversation_id = str(uuid.uuid4())
    return [
        ChatMessage(
            id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            role=MessageRole.USER,
            content="Hello, how are you?",
            created_at=datetime.utcnow()
        ),
        ChatMessage(
            id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            role=MessageRole.ASSISTANT,
            content="I'm doing well, thank you! How can I help you today?",
            created_at=datetime.utcnow()
        )
    ]


class TestEnhancedConversationManager:
    """Test cases for enhanced conversation manager."""
    
    @pytest.mark.asyncio
    async def test_create_conversation_basic(self, conversation_manager, mock_db_client):
        """Test basic conversation creation."""
        tenant_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        
        # Create conversation
        conversation = await conversation_manager.create_conversation(
            tenant_id=tenant_id,
            user_id=user_id,
            title="Test Conversation",
            description="A test conversation",
            tags=["test"]
        )
        
        # Verify conversation properties
        assert conversation.user_id == user_id
        assert conversation.title == "Test Conversation"
        assert conversation.description == "A test conversation"
        assert "test" in conversation.tags
        assert conversation.status == ConversationStatus.ACTIVE
    
    @pytest.mark.asyncio
    async def test_create_conversation_with_template(self, conversation_manager, mock_db_client):
        """Test conversation creation with template."""
        tenant_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        template_id = str(uuid.uuid4())
        
        # Mock template
        mock_template = ConversationTemplate(
            id=template_id,
            name="Test Template",
            initial_messages=[
                ChatMessage(
                    id=str(uuid.uuid4()),
                    conversation_id="",
                    role=MessageRole.SYSTEM,
                    content="Welcome! How can I help you today?"
                )
            ]
        )
        
        with patch.object(conversation_manager, 'get_template', return_value=mock_template):
            # Mock database session
            mock_session = AsyncMock()
            mock_db_client.get_async_session.return_value.__aenter__.return_value = mock_session
            
            conversation = await conversation_manager.create_conversation(
                tenant_id=tenant_id,
                user_id=user_id,
                template_id=template_id
            )
            
            assert conversation.template_id == template_id
            assert conversation.title == "New Test Template"
    
    @pytest.mark.asyncio
    async def test_branch_conversation(self, conversation_manager, mock_db_client):
        """Test conversation branching."""
        tenant_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        conversation_id = str(uuid.uuid4())
        message_id = str(uuid.uuid4())
        
        # Mock original conversation
        original_conversation = Conversation(
            id=conversation_id,
            user_id=user_id,
            title="Original Conversation",
            tags=["original"]
        )
        
        # Mock messages
        messages = [
            ChatMessage(
                id=message_id,
                conversation_id=conversation_id,
                role=MessageRole.USER,
                content="First message"
            )
        ]
        
        with patch.object(conversation_manager, 'get_conversation', return_value=original_conversation), \
             patch.object(conversation_manager, 'get_conversation_messages', return_value=messages), \
             patch.object(conversation_manager, 'create_conversation') as mock_create, \
             patch.object(conversation_manager, 'add_message') as mock_add_message, \
             patch.object(conversation_manager, '_add_child_branch') as mock_add_branch:
            
            # Mock created branch conversation
            branch_conversation = Conversation(
                id=str(uuid.uuid4()),
                user_id=user_id,
                title="Original Conversation (Branch)"
            )
            mock_create.return_value = branch_conversation
            
            result = await conversation_manager.branch_conversation(
                tenant_id=tenant_id,
                conversation_id=conversation_id,
                from_message_id=message_id,
                user_id=user_id
            )
            
            assert result is not None
            assert result.title == "Original Conversation (Branch)"
            mock_create.assert_called_once()
            mock_add_message.assert_called_once()
            mock_add_branch.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_add_message(self, conversation_manager, mock_db_client):
        """Test adding message to conversation."""
        tenant_id = str(uuid.uuid4())
        conversation_id = str(uuid.uuid4())
        
        # Mock database session and conversation
        mock_session = AsyncMock()
        mock_db_client.get_async_session.return_value.__aenter__.return_value = mock_session
        
        mock_conversation = Mock()
        mock_conversation.id = uuid.UUID(conversation_id)
        mock_conversation.messages = []
        
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_conversation
        mock_session.execute.return_value = mock_result
        
        # Add message
        message = await conversation_manager.add_message(
            tenant_id=tenant_id,
            conversation_id=conversation_id,
            role=MessageRole.USER,
            content="Test message",
            message_type=MessageType.TEXT,
            metadata={"test": True}
        )
        
        assert message is not None
        assert message.role == MessageRole.USER
        assert message.content == "Test message"
        assert message.message_type == MessageType.TEXT
        assert message.metadata["test"] is True
        
        # Verify database update
        mock_session.execute.assert_called()
        mock_session.commit.assert_called()
    
    @pytest.mark.asyncio
    async def test_search_conversations(self, conversation_manager, mock_distilbert_service):
        """Test conversation search functionality."""
        tenant_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        query = "test search"
        
        # Mock search service
        mock_results = [
            Mock(
                conversation=Mock(id=str(uuid.uuid4()), title="Test Result"),
                relevance_score=0.8,
                matched_messages=[],
                highlight_snippets=["test snippet"]
            )
        ]
        
        with patch.object(conversation_manager.search_service, 'hybrid_search', return_value=mock_results):
            results = await conversation_manager.search_conversations(
                tenant_id=tenant_id,
                user_id=user_id,
                query=query
            )
            
            assert len(results) == 1
            assert results[0].relevance_score == 0.8
            assert "test snippet" in results[0].highlight_snippets
            
            # Verify DistilBERT was called for embeddings
            mock_distilbert_service.get_embeddings.assert_called_once_with(query)
    
    @pytest.mark.asyncio
    async def test_export_conversation_json(self, conversation_manager, sample_conversation, sample_messages):
        """Test conversation export in JSON format."""
        tenant_id = str(uuid.uuid4())
        
        with patch.object(conversation_manager, 'get_conversation', return_value=sample_conversation), \
             patch.object(conversation_manager, 'get_conversation_messages', return_value=sample_messages), \
             patch.object(conversation_manager, '_increment_export_count') as mock_increment:
            
            options = ConversationExportOptions(format="json", include_metadata=True)
            
            result = await conversation_manager.export_conversation(
                tenant_id=tenant_id,
                conversation_id=sample_conversation.id,
                user_id=sample_conversation.user_id,
                options=options
            )
            
            assert "conversation" in result
            assert "messages" in result
            assert "export_metadata" in result
            assert result["export_metadata"]["format"] == "json"
            
            mock_increment.assert_called_once_with(sample_conversation.id)
    
    @pytest.mark.asyncio
    async def test_export_conversation_markdown(self, conversation_manager, sample_conversation, sample_messages):
        """Test conversation export in Markdown format."""
        tenant_id = str(uuid.uuid4())
        
        with patch.object(conversation_manager, 'get_conversation', return_value=sample_conversation), \
             patch.object(conversation_manager, 'get_conversation_messages', return_value=sample_messages):
            
            options = ConversationExportOptions(format="markdown", include_metadata=True)
            
            result = await conversation_manager.export_conversation(
                tenant_id=tenant_id,
                conversation_id=sample_conversation.id,
                user_id=sample_conversation.user_id,
                options=options
            )
            
            assert "content" in result
            assert "filename" in result
            assert sample_conversation.title in result["content"]
            assert "👤 User" in result["content"]
            assert "🤖 Assistant" in result["content"]
    
    @pytest.mark.asyncio
    async def test_list_conversations_with_filters(self, conversation_manager, mock_db_client):
        """Test listing conversations with filters."""
        tenant_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        
        # Mock database session and results
        mock_session = AsyncMock()
        mock_db_client.get_async_session.return_value.__aenter__.return_value = mock_session
        
        mock_conversations = [
            Mock(
                id=uuid.uuid4(),
                user_id=uuid.UUID(user_id),
                title="Test Conversation 1",
                messages=[],
                conversation_metadata={"tags": ["test"], "is_favorite": True},
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            ),
            Mock(
                id=uuid.uuid4(),
                user_id=uuid.UUID(user_id),
                title="Test Conversation 2",
                messages=[],
                conversation_metadata={"tags": ["work"], "is_favorite": False},
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        ]
        
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_conversations
        mock_session.execute.return_value = mock_result
        
        # Test with filters
        filters = ConversationFilters(
            tags=["test"],
            is_favorite=True
        )
        
        conversations = await conversation_manager.list_conversations(
            tenant_id=tenant_id,
            user_id=user_id,
            filters=filters,
            limit=10
        )
        
        assert len(conversations) == 2  # Mock returns all, filtering would happen in real implementation
        assert all(conv.user_id == user_id for conv in conversations)
    
    @pytest.mark.asyncio
    async def test_create_folder(self, conversation_manager):
        """Test folder creation."""
        tenant_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        
        folder = await conversation_manager.create_folder(
            tenant_id=tenant_id,
            user_id=user_id,
            name="Test Folder",
            description="A test folder",
            color="#FF0000",
            icon="folder"
        )
        
        assert folder.user_id == user_id
        assert folder.name == "Test Folder"
        assert folder.description == "A test folder"
        assert folder.color == "#FF0000"
        assert folder.icon == "folder"
    
    @pytest.mark.asyncio
    async def test_move_to_folder(self, conversation_manager, mock_db_client):
        """Test moving conversation to folder."""
        tenant_id = str(uuid.uuid4())
        conversation_id = str(uuid.uuid4())
        folder_id = str(uuid.uuid4())
        
        # Mock database session and conversation
        mock_session = AsyncMock()
        mock_db_client.get_async_session.return_value.__aenter__.return_value = mock_session
        
        mock_conversation = Mock()
        mock_conversation.conversation_metadata = {}
        
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_conversation
        mock_session.execute.return_value = mock_result
        
        result = await conversation_manager.move_to_folder(
            tenant_id=tenant_id,
            conversation_id=conversation_id,
            folder_id=folder_id
        )
        
        assert result is True
        mock_session.execute.assert_called()
        mock_session.commit.assert_called()
    
    @pytest.mark.asyncio
    async def test_get_conversation_stats(self, conversation_manager, mock_db_client):
        """Test getting conversation statistics."""
        tenant_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        
        # Mock database session and conversations
        mock_session = AsyncMock()
        mock_db_client.get_async_session.return_value.__aenter__.return_value = mock_session
        
        mock_conversations = [
            Mock(
                conversation_metadata={
                    "status": "active",
                    "is_favorite": True,
                    "tags": ["work", "important"],
                    "folder_id": "folder1"
                },
                messages=[{"id": "1"}, {"id": "2"}],
                updated_at=datetime.utcnow()
            ),
            Mock(
                conversation_metadata={
                    "status": "archived",
                    "is_favorite": False,
                    "tags": ["personal"],
                    "folder_id": "folder2"
                },
                messages=[{"id": "3"}],
                updated_at=datetime.utcnow() - timedelta(days=5)
            )
        ]
        
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_conversations
        mock_session.execute.return_value = mock_result
        
        stats = await conversation_manager.get_conversation_stats(
            tenant_id=tenant_id,
            user_id=user_id
        )
        
        assert stats.total_conversations == 2
        assert stats.active_conversations == 1
        assert stats.archived_conversations == 1
        assert stats.favorite_conversations == 1
        assert stats.total_messages == 3
        assert stats.avg_messages_per_conversation == 1.5
        assert "work" in stats.conversations_by_tag
        assert "folder1" in stats.conversations_by_folder
    
    def test_metrics_tracking(self, conversation_manager):
        """Test that metrics are properly tracked."""
        initial_metrics = conversation_manager.metrics.copy()
        
        # Metrics should be initialized
        assert "conversations_created" in initial_metrics
        assert "conversations_branched" in initial_metrics
        assert "templates_used" in initial_metrics
        assert "searches_performed" in initial_metrics
        assert "exports_completed" in initial_metrics
        assert "avg_response_time" in initial_metrics
        
        # All should start at 0
        assert all(value == 0 or value == 0.0 for value in initial_metrics.values())


class TestConversationModels:
    """Test cases for conversation data models."""
    
    def test_chat_message_creation(self):
        """Test ChatMessage model creation."""
        message = ChatMessage(
            conversation_id=str(uuid.uuid4()),
            role=MessageRole.USER,
            content="Test message",
            message_type=MessageType.TEXT,
            metadata={"test": True}
        )
        
        assert message.role == MessageRole.USER
        assert message.content == "Test message"
        assert message.message_type == MessageType.TEXT
        assert message.metadata["test"] is True
        assert message.created_at is not None
        assert isinstance(message.id, str)
    
    def test_conversation_creation(self):
        """Test Conversation model creation."""
        conversation = Conversation(
            user_id=str(uuid.uuid4()),
            title="Test Conversation",
            description="A test conversation",
            tags=["test", "sample"],
            is_favorite=True,
            priority=1
        )
        
        assert conversation.title == "Test Conversation"
        assert conversation.description == "A test conversation"
        assert "test" in conversation.tags
        assert "sample" in conversation.tags
        assert conversation.is_favorite is True
        assert conversation.priority == 1
        assert conversation.status == ConversationStatus.ACTIVE
        assert conversation.created_at is not None
    
    def test_conversation_filters(self):
        """Test ConversationFilters model."""
        filters = ConversationFilters(
            date_from=datetime.utcnow() - timedelta(days=7),
            date_to=datetime.utcnow(),
            tags=["work", "important"],
            is_favorite=True,
            min_messages=5,
            max_messages=100
        )
        
        assert filters.tags == ["work", "important"]
        assert filters.is_favorite is True
        assert filters.min_messages == 5
        assert filters.max_messages == 100
        assert filters.date_from is not None
        assert filters.date_to is not None
    
    def test_export_options(self):
        """Test ConversationExportOptions model."""
        options = ConversationExportOptions(
            format="markdown",
            include_metadata=True,
            include_attachments=False,
            compress=True,
            encrypt=True,
            password="secret123"
        )
        
        assert options.format == "markdown"
        assert options.include_metadata is True
        assert options.include_attachments is False
        assert options.compress is True
        assert options.encrypt is True
        assert options.password == "secret123"


if __name__ == "__main__":
    pytest.main([__file__])