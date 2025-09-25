"""
Tests for Conversation Tracker - Task 1.2 Validation
Tests conversation context tracking and session management.
"""

import pytest
import asyncio
import uuid
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from src.ai_karen_engine.services.conversation_tracker import (
    ConversationTracker,
    ConversationSession,
    ConversationTurn
)
from src.ai_karen_engine.database.client import MultiTenantPostgresClient


class TestConversationTurn:
    """Test conversation turn functionality"""
    
    def test_conversation_turn_creation(self):
        """Test creating a conversation turn"""
        turn = ConversationTurn(
            id="turn1",
            user_message="Hello",
            assistant_response="Hi there!",
            timestamp=datetime.utcnow(),
            metadata={"test": "value"},
            memory_references=["mem1", "mem2"],
            context_used=["context1"]
        )
        
        assert turn.id == "turn1"
        assert turn.user_message == "Hello"
        assert turn.assistant_response == "Hi there!"
        assert turn.metadata["test"] == "value"
        assert len(turn.memory_references) == 2
        assert len(turn.context_used) == 1
    
    def test_conversation_turn_to_dict(self):
        """Test converting conversation turn to dictionary"""
        timestamp = datetime.utcnow()
        turn = ConversationTurn(
            id="turn1",
            user_message="Hello",
            assistant_response="Hi there!",
            timestamp=timestamp
        )
        
        turn_dict = turn.to_dict()
        
        assert turn_dict["id"] == "turn1"
        assert turn_dict["user_message"] == "Hello"
        assert turn_dict["assistant_response"] == "Hi there!"
        assert turn_dict["timestamp"] == timestamp.isoformat()
        assert turn_dict["metadata"] == {}
        assert turn_dict["memory_references"] == []
        assert turn_dict["context_used"] == []


class TestConversationSession:
    """Test conversation session functionality"""
    
    def test_session_creation(self):
        """Test creating a conversation session"""
        session = ConversationSession(
            session_id="session1",
            user_id="user1",
            tenant_id="tenant1",
            conversation_id="conv1",
            metadata={"test": "value"}
        )
        
        assert session.session_id == "session1"
        assert session.user_id == "user1"
        assert session.tenant_id == "tenant1"
        assert session.conversation_id == "conv1"
        assert session.metadata["test"] == "value"
        assert len(session.turns) == 0
        assert len(session.context_window) == 0
    
    def test_add_turn_to_session(self):
        """Test adding turns to a session"""
        session = ConversationSession(
            session_id="session1",
            user_id="user1",
            tenant_id="tenant1"
        )
        
        turn1 = ConversationTurn(
            id="turn1",
            user_message="Hello",
            assistant_response="Hi!",
            timestamp=datetime.utcnow()
        )
        
        turn2 = ConversationTurn(
            id="turn2",
            user_message="How are you?",
            assistant_response="I'm good!",
            timestamp=datetime.utcnow()
        )
        
        session.add_turn(turn1)
        session.add_turn(turn2)
        
        assert len(session.turns) == 2
        assert len(session.context_window) == 2
        assert session.turns[0].id == "turn1"
        assert session.turns[1].id == "turn2"
    
    def test_context_window_management(self):
        """Test context window size management"""
        session = ConversationSession(
            session_id="session1",
            user_id="user1",
            tenant_id="tenant1"
        )
        
        # Add more turns than context window size
        for i in range(10):
            turn = ConversationTurn(
                id=f"turn{i}",
                user_message=f"Message {i}",
                assistant_response=f"Response {i}",
                timestamp=datetime.utcnow()
            )
            session.add_turn(turn)
        
        # Context window should be limited to 5 most recent
        assert len(session.context_window) == 5
        assert session.context_window[0].id == "turn5"
        assert session.context_window[-1].id == "turn9"
    
    def test_context_summary_generation(self):
        """Test context summary generation"""
        session = ConversationSession(
            session_id="session1",
            user_id="user1",
            tenant_id="tenant1"
        )
        
        turn1 = ConversationTurn(
            id="turn1",
            user_message="Hello",
            assistant_response="Hi there!",
            timestamp=datetime.utcnow()
        )
        
        turn2 = ConversationTurn(
            id="turn2",
            user_message="How are you?",
            assistant_response="I'm doing well, thank you!",
            timestamp=datetime.utcnow()
        )
        
        session.add_turn(turn1)
        session.add_turn(turn2)
        
        summary = session.get_context_summary()
        
        assert "User: Hello" in summary
        assert "Assistant: Hi there!" in summary
        assert "User: How are you?" in summary
        assert "Assistant: I'm doing well, thank you!" in summary
    
    def test_session_to_dict(self):
        """Test converting session to dictionary"""
        session = ConversationSession(
            session_id="session1",
            user_id="user1",
            tenant_id="tenant1"
        )
        
        turn = ConversationTurn(
            id="turn1",
            user_message="Hello",
            assistant_response="Hi!",
            timestamp=datetime.utcnow()
        )
        session.add_turn(turn)
        
        session_dict = session.to_dict()
        
        assert session_dict["session_id"] == "session1"
        assert session_dict["user_id"] == "user1"
        assert session_dict["tenant_id"] == "tenant1"
        assert len(session_dict["turns"]) == 1
        assert len(session_dict["context_window"]) == 1
        assert "created_at" in session_dict
        assert "last_activity" in session_dict


class TestConversationTracker:
    """Test conversation tracker functionality"""
    
    @pytest.fixture
    def mock_db_client(self):
        """Mock database client"""
        client = Mock(spec=MultiTenantPostgresClient)
        client.get_async_session = AsyncMock()
        return client
    
    @pytest.fixture
    def conversation_tracker(self, mock_db_client):
        """Create conversation tracker with mocked dependencies"""
        return ConversationTracker(mock_db_client)
    
    @pytest.mark.asyncio
    async def test_start_new_session(self, conversation_tracker, mock_db_client):
        """Test starting a new conversation session"""
        # Mock database query returning no existing session
        mock_session = AsyncMock()
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result
        mock_db_client.get_async_session.return_value.__aenter__.return_value = mock_session
        
        session = await conversation_tracker.start_session(
            session_id="session1",
            user_id="user1",
            tenant_id="tenant1",
            metadata={"test": "value"}
        )
        
        assert session.session_id == "session1"
        assert session.user_id == "user1"
        assert session.tenant_id == "tenant1"
        assert session.metadata["test"] == "value"
        assert "session1" in conversation_tracker.active_sessions
        assert conversation_tracker.stats["total_sessions"] == 1
    
    @pytest.mark.asyncio
    async def test_resume_existing_session(self, conversation_tracker):
        """Test resuming an existing session"""
        # Create initial session
        session1 = await conversation_tracker.start_session(
            session_id="session1",
            user_id="user1",
            tenant_id="tenant1"
        )
        
        original_activity = session1.last_activity
        
        # Wait a bit and resume
        await asyncio.sleep(0.01)
        session2 = await conversation_tracker.start_session(
            session_id="session1",
            user_id="user1",
            tenant_id="tenant1"
        )
        
        # Should be the same session object
        assert session1 is session2
        assert session2.last_activity > original_activity
        assert conversation_tracker.stats["total_sessions"] == 1  # No new session created
    
    @pytest.mark.asyncio
    async def test_add_conversation_turn(self, conversation_tracker):
        """Test adding conversation turns"""
        session = await conversation_tracker.start_session(
            session_id="session1",
            user_id="user1",
            tenant_id="tenant1"
        )
        
        turn = await conversation_tracker.add_conversation_turn(
            session_id="session1",
            user_message="Hello",
            assistant_response="Hi there!",
            memory_references=["mem1", "mem2"],
            context_used=["context1"],
            metadata={"test": "value"}
        )
        
        assert turn.user_message == "Hello"
        assert turn.assistant_response == "Hi there!"
        assert len(turn.memory_references) == 2
        assert len(turn.context_used) == 1
        assert turn.metadata["test"] == "value"
        
        # Check session was updated
        assert len(session.turns) == 1
        assert session.turns[0].id == turn.id
        assert conversation_tracker.stats["total_turns"] == 1
        assert conversation_tracker.stats["memory_references"] == 2
    
    @pytest.mark.asyncio
    async def test_add_turn_to_nonexistent_session(self, conversation_tracker):
        """Test adding turn to non-existent session raises error"""
        with pytest.raises(ValueError, match="Session session1 not found"):
            await conversation_tracker.add_conversation_turn(
                session_id="session1",
                user_message="Hello",
                assistant_response="Hi!"
            )
    
    @pytest.mark.asyncio
    async def test_get_conversation_context(self, conversation_tracker):
        """Test getting conversation context"""
        session = await conversation_tracker.start_session(
            session_id="session1",
            user_id="user1",
            tenant_id="tenant1",
            conversation_id="conv1",
            metadata={"test": "value"}
        )
        
        # Add some turns
        await conversation_tracker.add_conversation_turn(
            session_id="session1",
            user_message="Hello",
            assistant_response="Hi!",
            memory_references=["mem1"]
        )
        
        await conversation_tracker.add_conversation_turn(
            session_id="session1",
            user_message="How are you?",
            assistant_response="Good!",
            memory_references=["mem2"]
        )
        
        context = await conversation_tracker.get_conversation_context(
            session_id="session1",
            include_memory_references=True
        )
        
        assert context["session_id"] == "session1"
        assert context["user_id"] == "user1"
        assert context["tenant_id"] == "tenant1"
        assert context["conversation_id"] == "conv1"
        assert context["turn_count"] == 2
        assert len(context["recent_turns"]) == 2
        assert len(context["memory_references"]) == 2
        assert "mem1" in context["memory_references"]
        assert "mem2" in context["memory_references"]
        assert context["memory_reference_count"] == 2
        assert "User: Hello" in context["context_summary"]
        assert "Assistant: Hi!" in context["context_summary"]
    
    @pytest.mark.asyncio
    async def test_get_context_with_window_size(self, conversation_tracker):
        """Test getting context with specific window size"""
        session = await conversation_tracker.start_session(
            session_id="session1",
            user_id="user1",
            tenant_id="tenant1"
        )
        
        # Add multiple turns
        for i in range(10):
            await conversation_tracker.add_conversation_turn(
                session_id="session1",
                user_message=f"Message {i}",
                assistant_response=f"Response {i}"
            )
        
        context = await conversation_tracker.get_conversation_context(
            session_id="session1",
            context_window_size=3
        )
        
        # Should only include last 3 turns
        assert len(context["recent_turns"]) == 3
        assert context["recent_turns"][0]["user_message"] == "Message 7"
        assert context["recent_turns"][-1]["user_message"] == "Message 9"
    
    @pytest.mark.asyncio
    async def test_get_session_history(self, conversation_tracker):
        """Test getting session history"""
        session = await conversation_tracker.start_session(
            session_id="session1",
            user_id="user1",
            tenant_id="tenant1"
        )
        
        # Add turns
        for i in range(5):
            await conversation_tracker.add_conversation_turn(
                session_id="session1",
                user_message=f"Message {i}",
                assistant_response=f"Response {i}"
            )
        
        # Get all history
        history = await conversation_tracker.get_session_history("session1")
        assert len(history) == 5
        
        # Get limited history
        limited_history = await conversation_tracker.get_session_history("session1", limit=3)
        assert len(limited_history) == 3
        assert limited_history[0].user_message == "Message 2"  # Last 3
        assert limited_history[-1].user_message == "Message 4"
    
    @pytest.mark.asyncio
    async def test_end_session(self, conversation_tracker, mock_db_client):
        """Test ending a session"""
        # Mock database operations
        mock_session = AsyncMock()
        mock_db_client.get_async_session.return_value.__aenter__.return_value = mock_session
        
        session = await conversation_tracker.start_session(
            session_id="session1",
            user_id="user1",
            tenant_id="tenant1"
        )
        
        assert "session1" in conversation_tracker.active_sessions
        
        await conversation_tracker.end_session("session1", save_to_db=True)
        
        assert "session1" not in conversation_tracker.active_sessions
        # Should have called database save operations
        mock_session.execute.assert_called()
    
    @pytest.mark.asyncio
    async def test_auto_save_functionality(self, conversation_tracker, mock_db_client):
        """Test auto-save functionality"""
        # Mock database operations
        mock_session = AsyncMock()
        mock_db_client.get_async_session.return_value.__aenter__.return_value = mock_session
        
        session = await conversation_tracker.start_session(
            session_id="session1",
            user_id="user1",
            tenant_id="tenant1"
        )
        
        # Add turns up to auto-save interval (10)
        for i in range(10):
            await conversation_tracker.add_conversation_turn(
                session_id="session1",
                user_message=f"Message {i}",
                assistant_response=f"Response {i}"
            )
        
        # Should have triggered auto-save
        mock_session.execute.assert_called()
    
    @pytest.mark.asyncio
    async def test_get_user_sessions(self, conversation_tracker, mock_db_client):
        """Test getting user sessions from database"""
        # Mock database query
        mock_session = AsyncMock()
        mock_result = Mock()
        
        # Mock conversation records
        mock_conv1 = Mock()
        mock_conv1.id = uuid.uuid4()
        mock_conv1.session_id = "session1"
        mock_conv1.title = "Conversation 1"
        mock_conv1.summary = "Test summary"
        mock_conv1.created_at = datetime.utcnow()
        mock_conv1.updated_at = datetime.utcnow()
        
        mock_conv2 = Mock()
        mock_conv2.id = uuid.uuid4()
        mock_conv2.session_id = "session2"
        mock_conv2.title = "Conversation 2"
        mock_conv2.summary = "Another summary"
        mock_conv2.created_at = datetime.utcnow()
        mock_conv2.updated_at = datetime.utcnow()
        
        mock_result.fetchall.return_value = [mock_conv1, mock_conv2]
        mock_session.execute.return_value = mock_result
        mock_db_client.get_async_session.return_value.__aenter__.return_value = mock_session
        
        sessions = await conversation_tracker.get_user_sessions("user1", "tenant1", limit=10)
        
        assert len(sessions) == 2
        assert sessions[0]["session_id"] == "session1"
        assert sessions[0]["title"] == "Conversation 1"
        assert sessions[0]["is_active"] == False
        assert sessions[1]["session_id"] == "session2"
        assert sessions[1]["title"] == "Conversation 2"
    
    def test_tracker_stats(self, conversation_tracker):
        """Test getting tracker statistics"""
        stats = conversation_tracker.get_tracker_stats()
        
        assert "total_sessions" in stats
        assert "active_sessions" in stats
        assert "total_turns" in stats
        assert "context_builds" in stats
        assert "memory_references" in stats
        assert "session_timeout_hours" in stats
        assert "max_context_window" in stats
        assert "max_turns_per_session" in stats
        assert "auto_save_interval" in stats
        
        # Check initial values
        assert stats["total_sessions"] == 0
        assert stats["active_sessions"] == 0
        assert stats["total_turns"] == 0
    
    @pytest.mark.asyncio
    async def test_context_without_memory_references(self, conversation_tracker):
        """Test getting context without memory references"""
        session = await conversation_tracker.start_session(
            session_id="session1",
            user_id="user1",
            tenant_id="tenant1"
        )
        
        await conversation_tracker.add_conversation_turn(
            session_id="session1",
            user_message="Hello",
            assistant_response="Hi!",
            memory_references=["mem1"]
        )
        
        context = await conversation_tracker.get_conversation_context(
            session_id="session1",
            include_memory_references=False
        )
        
        assert "memory_references" not in context
        assert "memory_reference_count" not in context
        assert context["turn_count"] == 1
        assert len(context["recent_turns"]) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])