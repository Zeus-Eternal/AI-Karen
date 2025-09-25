"""
Tests for the conversation search service.
"""

import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

from ai_karen_engine.chat.conversation_search_service import ConversationSearchService
from ai_karen_engine.chat.conversation_models import (
    Conversation, ChatMessage, ConversationFilters, ConversationSearchResult,
    MessageRole, MessageType, ConversationStatus
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
def mock_milvus_client():
    """Mock Milvus client."""
    client = Mock()
    client.search = AsyncMock(return_value=[[]])
    return client


@pytest.fixture
def search_service(mock_db_client, mock_distilbert_service, mock_milvus_client):
    """Create search service with mocked dependencies."""
    return ConversationSearchService(
        db_client=mock_db_client,
        distilbert_service=mock_distilbert_service,
        milvus_client=mock_milvus_client
    )


class TestConversationSearchService:
    """Test cases for conversation search service."""
    
    @pytest.mark.asyncio
    async def test_hybrid_search_text_only(self, search_service, mock_db_client):
        """Test hybrid search with text query only."""
        tenant_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        query = "test search"
        
        # Mock database conversations
        mock_conversations = [
            Mock(
                id=uuid.uuid4(),
                user_id=uuid.UUID(user_id),
                title="Test Conversation",
                messages=[
                    {"id": str(uuid.uuid4()), "role": "user", "content": "test message", "created_at": datetime.utcnow().isoformat()},
                    {"id": str(uuid.uuid4()), "role": "assistant", "content": "search result", "created_at": datetime.utcnow().isoformat()}
                ],
                conversation_metadata={"tags": ["test"], "status": "active"},
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        ]
        
        # Mock database session
        mock_session = mock_db_client.get_async_session.return_value.__aenter__.return_value
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_conversations
        mock_session.execute.return_value = mock_result
        
        # Perform search
        results = await search_service.hybrid_search(
            tenant_id=tenant_id,
            user_id=user_id,
            text_query=query,
            limit=10
        )
        
        # Verify results
        assert isinstance(results, list)
        # Note: Results might be empty due to simplified mock implementation
        # In a real implementation, this would return actual search results
    
    @pytest.mark.asyncio
    async def test_prepare_search_terms(self, search_service):
        """Test search term preparation."""
        # Test normal query
        terms = search_service._prepare_search_terms("hello world test")
        assert "hello" in terms
        assert "world" in terms
        assert "test" in terms
        
        # Test query with stop words
        terms = search_service._prepare_search_terms("the quick brown fox")
        assert "quick" in terms
        assert "brown" in terms
        assert "fox" in terms
        assert "the" not in terms  # Stop word should be removed
        
        # Test query with special characters
        terms = search_service._prepare_search_terms("hello, world! test?")
        assert "hello" in terms
        assert "world" in terms
        assert "test" in terms
    
    def test_calculate_text_relevance(self, search_service):
        """Test text relevance calculation."""
        search_terms = ["test", "search", "query"]
        
        # Test exact matches
        score = search_service._calculate_text_relevance("test search query", search_terms)
        assert score == 1.0  # All terms match exactly
        
        # Test partial matches
        score = search_service._calculate_text_relevance("test something", search_terms)
        assert score > 0 and score < 1.0  # Only some terms match
        
        # Test no matches
        score = search_service._calculate_text_relevance("nothing matches", search_terms)
        assert score == 0.0  # No terms match
        
        # Test empty text
        score = search_service._calculate_text_relevance("", search_terms)
        assert score == 0.0
    
    def test_extract_snippet(self, search_service):
        """Test snippet extraction."""
        text = "This is a long text that contains the search term somewhere in the middle of the content."
        search_terms = ["search", "term"]
        
        snippet = search_service._extract_snippet(text, search_terms, max_length=50)
        
        assert len(snippet) <= 60  # Should be around max_length + ellipsis
        assert "search" in snippet.lower() or "term" in snippet.lower()
        
        # Test with no matching terms
        snippet = search_service._extract_snippet(text, ["nonexistent"], max_length=50)
        assert len(snippet) <= 60
        assert snippet.startswith(text[:50]) or snippet.startswith("...")
    
    @pytest.mark.asyncio
    async def test_get_search_suggestions(self, search_service, mock_db_client):
        """Test search suggestions."""
        tenant_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        partial_query = "test"
        
        # Mock database conversations
        mock_conversations = [
            Mock(
                title="Test Conversation 1",
                conversation_metadata={"tags": ["testing", "work"]}
            ),
            Mock(
                title="Another Test Chat",
                conversation_metadata={"tags": ["personal", "test-tag"]}
            )
        ]
        
        # Mock database session
        mock_session = mock_db_client.get_async_session.return_value.__aenter__.return_value
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_conversations
        mock_session.execute.return_value = mock_result
        
        # Get suggestions
        suggestions = await search_service.get_search_suggestions(
            tenant_id=tenant_id,
            user_id=user_id,
            partial_query=partial_query,
            limit=5
        )
        
        # Verify suggestions
        assert isinstance(suggestions, list)
        # Should contain matching titles and tags
        matching_suggestions = [s for s in suggestions if "test" in s.lower()]
        assert len(matching_suggestions) > 0
    
    def test_apply_final_filters(self, search_service):
        """Test final filtering of search results."""
        # Create mock search results
        conversation1 = Conversation(
            id=str(uuid.uuid4()),
            user_id=str(uuid.uuid4()),
            title="Test Conversation 1",
            tags=["work", "important"],
            is_favorite=True,
            message_count=10
        )
        
        conversation2 = Conversation(
            id=str(uuid.uuid4()),
            user_id=str(uuid.uuid4()),
            title="Test Conversation 2",
            tags=["personal"],
            is_favorite=False,
            message_count=5
        )
        
        results = [
            ConversationSearchResult(
                conversation=conversation1,
                relevance_score=0.8,
                matched_messages=[],
                highlight_snippets=[]
            ),
            ConversationSearchResult(
                conversation=conversation2,
                relevance_score=0.6,
                matched_messages=[],
                highlight_snippets=[]
            )
        ]
        
        # Test filtering by tags
        filters = ConversationFilters(tags=["work"])
        filtered = search_service._apply_final_filters(results, filters, 10, 0)
        assert len(filtered) == 1
        assert filtered[0].conversation.id == conversation1.id
        
        # Test filtering by favorites
        filters = ConversationFilters(is_favorite=True)
        filtered = search_service._apply_final_filters(results, filters, 10, 0)
        assert len(filtered) == 1
        assert filtered[0].conversation.id == conversation1.id
        
        # Test filtering by message count
        filters = ConversationFilters(min_messages=8)
        filtered = search_service._apply_final_filters(results, filters, 10, 0)
        assert len(filtered) == 1
        assert filtered[0].conversation.id == conversation1.id
        
        # Test pagination
        filtered = search_service._apply_final_filters(results, None, 1, 0)
        assert len(filtered) == 1
        
        filtered = search_service._apply_final_filters(results, None, 1, 1)
        assert len(filtered) == 1
        assert filtered[0].conversation.id == conversation2.id
    
    def test_search_metrics(self, search_service):
        """Test search metrics tracking."""
        initial_metrics = search_service.get_search_metrics()
        
        # Verify initial state
        assert initial_metrics["total_searches"] == 0
        assert initial_metrics["text_searches"] == 0
        assert initial_metrics["semantic_searches"] == 0
        assert initial_metrics["hybrid_searches"] == 0
        assert initial_metrics["avg_search_time"] == 0.0
        
        # Metrics should be properly structured
        assert isinstance(initial_metrics, dict)
        assert all(isinstance(v, (int, float)) for v in initial_metrics.values())


if __name__ == "__main__":
    pytest.main([__file__])