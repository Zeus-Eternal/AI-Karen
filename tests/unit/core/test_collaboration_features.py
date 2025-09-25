"""
Comprehensive tests for collaboration features.

This module tests the collaboration capabilities including presence indicators,
typing indicators, collaboration sessions, and real-time synchronization.
"""

import asyncio
import json
import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

from ai_karen_engine.chat.websocket_gateway import (
    PresenceManager,
    TypingManager,
    CollaborationManager,
    CollaborationUser,
    CollaborationSession,
    WebSocketGateway,
    MessageType
)
from ai_karen_engine.event_bus import get_event_bus


class TestPresenceManager:
    """Test presence management functionality."""
    
    @pytest.fixture
    def presence_manager(self):
        """Create a PresenceManager instance for testing."""
        return PresenceManager()
    
    @pytest.mark.asyncio
    async def test_update_presence(self, presence_manager):
        """Test updating user presence."""
        await presence_manager.update_presence(
            user_id="user123",
            status="online",
            conversation_id="conv456",
            metadata={"username": "testuser", "device": "desktop"}
        )
        
        presence = presence_manager.get_presence("user123")
        assert presence is not None
        assert presence.user_id == "user123"
        assert presence.status == "online"
        assert presence.metadata["username"] == "testuser"
        assert presence.metadata["device"] == "desktop"
    
    @pytest.mark.asyncio
    async def test_presence_status_changes(self, presence_manager):
        """Test presence status changes."""
        # Set initial presence
        await presence_manager.update_presence("user123", "online")
        presence = presence_manager.get_presence("user123")
        assert presence.status == "online"
        
        # Change to away
        await presence_manager.update_presence("user123", "away")
        presence = presence_manager.get_presence("user123")
        assert presence.status == "away"
        
        # Change to offline
        await presence_manager.update_presence("user123", "offline")
        presence = presence_manager.get_presence("user123")
        assert presence.status == "offline"
    
    def test_get_online_users(self, presence_manager):
        """Test getting online users."""
        # Initially no online users
        online_users = presence_manager.get_online_users()
        assert len(online_users) == 0
        
        # Add online users
        asyncio.run(presence_manager.update_presence("user1", "online", "conv1"))
        asyncio.run(presence_manager.update_presence("user2", "online", "conv1"))
        asyncio.run(presence_manager.update_presence("user3", "away", "conv1"))
        asyncio.run(presence_manager.update_presence("user4", "online", "conv2"))
        
        # Test all online users
        online_users = presence_manager.get_online_users()
        assert len(online_users) == 3
        online_user_ids = [user.user_id for user in online_users]
        assert "user1" in online_user_ids
        assert "user2" in online_user_ids
        assert "user4" in online_user_ids
        assert "user3" not in online_user_ids  # away, not online
        
        # Test filtered by conversation
        online_users_conv1 = presence_manager.get_online_users("conv1")
        assert len(online_users_conv1) == 2
        online_user_ids_conv1 = [user.user_id for user in online_users_conv1]
        assert "user1" in online_user_ids_conv1
        assert "user2" in online_user_ids_conv1
    
    @pytest.mark.asyncio
    async def test_cleanup_expired_presence(self, presence_manager):
        """Test cleanup of expired presence data."""
        # Add user with current timestamp
        await presence_manager.update_presence("user1", "online")
        
        # Manually set old timestamp
        presence_manager.presence_data["user1"].last_seen = datetime.utcnow() - timedelta(minutes=10)
        
        # Run cleanup with 5 minute timeout
        await presence_manager.cleanup_expired_presence(timeout_minutes=5)
        
        # User should be marked offline
        presence = presence_manager.get_presence("user1")
        assert presence.status == "offline"


class TestTypingManager:
    """Test typing indicator functionality."""
    
    @pytest.fixture
    def typing_manager(self):
        """Create a TypingManager instance for testing."""
        return TypingManager()
    
    @pytest.mark.asyncio
    async def test_set_typing_start(self, typing_manager):
        """Test starting typing indicator."""
        await typing_manager.set_typing("user123", "conv456", True, 5)
        
        typing_users = typing_manager.get_typing_users("conv456")
        assert len(typing_users) == 1
        assert typing_users[0] == "user123"
    
    @pytest.mark.asyncio
    async def test_set_typing_stop(self, typing_manager):
        """Test stopping typing indicator."""
        # Start typing
        await typing_manager.set_typing("user123", "conv456", True, 5)
        assert len(typing_manager.get_typing_users("conv456")) == 1
        
        # Stop typing
        await typing_manager.set_typing("user123", "conv456", False)
        assert len(typing_manager.get_typing_users("conv456")) == 0
    
    @pytest.mark.asyncio
    async def test_multiple_users_typing(self, typing_manager):
        """Test multiple users typing in same conversation."""
        await typing_manager.set_typing("user1", "conv456", True, 10)
        await typing_manager.set_typing("user2", "conv456", True, 10)
        await typing_manager.set_typing("user3", "conv789", True, 10)
        
        # Check conv456 has 2 typing users
        typing_users_conv456 = typing_manager.get_typing_users("conv456")
        assert len(typing_users_conv456) == 2
        assert "user1" in typing_users_conv456
        assert "user2" in typing_users_conv456
        
        # Check conv789 has 1 typing user
        typing_users_conv789 = typing_manager.get_typing_users("conv789")
        assert len(typing_users_conv789) == 1
        assert "user3" in typing_users_conv789
    
    @pytest.mark.asyncio
    async def test_typing_expiration(self, typing_manager):
        """Test typing indicator expiration."""
        # Set typing with very short expiration
        await typing_manager.set_typing("user123", "conv456", True, 0.1)
        
        # Should be typing initially
        typing_users = typing_manager.get_typing_users("conv456")
        assert len(typing_users) == 1
        
        # Wait for expiration
        await asyncio.sleep(0.2)
        
        # Run cleanup
        await typing_manager.cleanup_expired_typing()
        
        # Should no longer be typing
        typing_users = typing_manager.get_typing_users("conv456")
        assert len(typing_users) == 0


class TestCollaborationManager:
    """Test collaboration session management."""
    
    @pytest.fixture
    def collaboration_manager(self):
        """Create a CollaborationManager instance for testing."""
        return CollaborationManager()
    
    @pytest.mark.asyncio
    async def test_create_session(self, collaboration_manager):
        """Test creating a collaboration session."""
        session_id = await collaboration_manager.create_session(
            conversation_id="conv456",
            initiator_user_id="user123",
            session_type="chat",
            metadata={"title": "Test Session"}
        )
        
        assert session_id is not None
        
        session = collaboration_manager.get_session(session_id)
        assert session is not None
        assert session.conversation_id == "conv456"
        assert session.session_type == "chat"
        assert len(session.participants) == 1
        assert session.participants[0].user_id == "user123"
        assert session.metadata["title"] == "Test Session"
    
    @pytest.mark.asyncio
    async def test_join_session(self, collaboration_manager):
        """Test joining a collaboration session."""
        # Create session
        session_id = await collaboration_manager.create_session(
            conversation_id="conv456",
            initiator_user_id="user123"
        )
        
        # Join session
        success = await collaboration_manager.join_session(
            session_id=session_id,
            user_id="user456",
            username="testuser2"
        )
        
        assert success is True
        
        session = collaboration_manager.get_session(session_id)
        assert len(session.participants) == 2
        
        participant_ids = [p.user_id for p in session.participants]
        assert "user123" in participant_ids
        assert "user456" in participant_ids
    
    @pytest.mark.asyncio
    async def test_join_nonexistent_session(self, collaboration_manager):
        """Test joining a non-existent session."""
        success = await collaboration_manager.join_session(
            session_id="nonexistent",
            user_id="user456"
        )
        
        assert success is False
    
    @pytest.mark.asyncio
    async def test_rejoin_session(self, collaboration_manager):
        """Test rejoining a session user is already in."""
        # Create and join session
        session_id = await collaboration_manager.create_session(
            conversation_id="conv456",
            initiator_user_id="user123"
        )
        
        # Try to join again (should update status)
        success = await collaboration_manager.join_session(
            session_id=session_id,
            user_id="user123",
            username="updated_username"
        )
        
        assert success is True
        
        session = collaboration_manager.get_session(session_id)
        assert len(session.participants) == 1  # Still only one participant
        assert session.participants[0].status == "online"
    
    @pytest.mark.asyncio
    async def test_leave_session(self, collaboration_manager):
        """Test leaving a collaboration session."""
        # Create session with multiple participants
        session_id = await collaboration_manager.create_session(
            conversation_id="conv456",
            initiator_user_id="user123"
        )
        await collaboration_manager.join_session(session_id, "user456")
        
        # Leave session
        success = await collaboration_manager.leave_session(session_id, "user456")
        assert success is True
        
        session = collaboration_manager.get_session(session_id)
        assert len(session.participants) == 1
        assert session.participants[0].user_id == "user123"
    
    @pytest.mark.asyncio
    async def test_leave_session_last_participant(self, collaboration_manager):
        """Test leaving session as last participant ends the session."""
        # Create session
        session_id = await collaboration_manager.create_session(
            conversation_id="conv456",
            initiator_user_id="user123"
        )
        
        # Leave as last participant
        success = await collaboration_manager.leave_session(session_id, "user123")
        assert success is True
        
        # Session should be ended
        session = collaboration_manager.get_session(session_id)
        assert session is None
    
    @pytest.mark.asyncio
    async def test_end_session(self, collaboration_manager):
        """Test ending a collaboration session."""
        # Create session
        session_id = await collaboration_manager.create_session(
            conversation_id="conv456",
            initiator_user_id="user123"
        )
        
        # End session
        success = await collaboration_manager.end_session(session_id)
        assert success is True
        
        # Session should be removed
        session = collaboration_manager.get_session(session_id)
        assert session is None
    
    def test_get_user_sessions(self, collaboration_manager):
        """Test getting sessions for a user."""
        # Create multiple sessions
        session_id1 = asyncio.run(collaboration_manager.create_session(
            "conv1", "user123", "chat"
        ))
        session_id2 = asyncio.run(collaboration_manager.create_session(
            "conv2", "user123", "screen_share"
        ))
        
        # Join another session
        session_id3 = asyncio.run(collaboration_manager.create_session(
            "conv3", "user456", "chat"
        ))
        asyncio.run(collaboration_manager.join_session(session_id3, "user123"))
        
        # Get user sessions
        user_sessions = collaboration_manager.get_user_sessions("user123")
        assert len(user_sessions) == 3
        
        session_ids = [s.session_id for s in user_sessions]
        assert session_id1 in session_ids
        assert session_id2 in session_ids
        assert session_id3 in session_ids
    
    def test_get_conversation_sessions(self, collaboration_manager):
        """Test getting sessions for a conversation."""
        # Create sessions for same conversation
        session_id1 = asyncio.run(collaboration_manager.create_session(
            "conv456", "user123", "chat"
        ))
        session_id2 = asyncio.run(collaboration_manager.create_session(
            "conv456", "user456", "screen_share"
        ))
        
        # Create session for different conversation
        asyncio.run(collaboration_manager.create_session(
            "conv789", "user123", "chat"
        ))
        
        # Get conversation sessions
        conv_sessions = collaboration_manager.get_conversation_sessions("conv456")
        assert len(conv_sessions) == 2
        
        session_ids = [s.session_id for s in conv_sessions]
        assert session_id1 in session_ids
        assert session_id2 in session_ids


class TestEventBusCollaboration:
    """Test EventBus collaboration features."""
    
    @pytest.fixture
    def event_bus(self):
        """Get EventBus instance for testing."""
        return get_event_bus()
    
    def test_publish_presence_update(self, event_bus):
        """Test publishing presence update events."""
        event_id = event_bus.publish_presence_update(
            user_id="user123",
            status="online",
            conversation_id="conv456",
            metadata={"device": "mobile"}
        )
        
        assert event_id is not None
        
        # Check presence tracking
        presence = event_bus.get_user_presence("user123")
        assert presence is not None
        assert presence["status"] == "online"
        assert presence["conversation_id"] == "conv456"
    
    def test_publish_typing_indicator(self, event_bus):
        """Test publishing typing indicator events."""
        event_id = event_bus.publish_typing_indicator(
            user_id="user123",
            conversation_id="conv456",
            is_typing=True,
            expires_in_seconds=5
        )
        
        assert event_id is not None
        
        # Check typing tracking
        typing_users = event_bus.get_typing_users("conv456")
        assert "user123" in typing_users
    
    def test_publish_collaboration_session(self, event_bus):
        """Test publishing collaboration session events."""
        event_id = event_bus.publish_collaboration_session(
            session_id="session123",
            action="start",
            participants=["user123", "user456"],
            conversation_id="conv456",
            session_type="chat"
        )
        
        assert event_id is not None
        
        # Check session tracking
        sessions = event_bus.get_collaboration_sessions("conv456")
        assert len(sessions) == 1
        assert sessions[0]["session_id"] == "session123"
    
    def test_get_online_users_filtered(self, event_bus):
        """Test getting online users filtered by conversation."""
        # Add users to different conversations
        event_bus.publish_presence_update("user1", "online", "conv1")
        event_bus.publish_presence_update("user2", "online", "conv1")
        event_bus.publish_presence_update("user3", "online", "conv2")
        event_bus.publish_presence_update("user4", "away", "conv1")
        
        # Test all online users
        all_online = event_bus.get_online_users()
        assert len(all_online) == 3
        assert "user1" in all_online
        assert "user2" in all_online
        assert "user3" in all_online
        
        # Test filtered by conversation
        conv1_online = event_bus.get_online_users("conv1")
        assert len(conv1_online) == 2
        assert "user1" in conv1_online
        assert "user2" in conv1_online


class TestWebSocketGatewayCollaboration:
    """Test WebSocket gateway collaboration features."""
    
    @pytest.fixture
    def websocket_gateway(self):
        """Create WebSocketGateway instance for testing."""
        return WebSocketGateway()
    
    @pytest.fixture
    def mock_websocket(self):
        """Create mock WebSocket for testing."""
        websocket = Mock()
        websocket.accept = AsyncMock()
        websocket.send_text = AsyncMock()
        websocket.receive_text = AsyncMock()
        websocket.close = AsyncMock()
        return websocket
    
    @pytest.mark.asyncio
    async def test_handle_presence_update_message(self, websocket_gateway, mock_websocket):
        """Test handling presence update WebSocket messages."""
        # Set up connection
        connection_id = "conn123"
        websocket_gateway.active_connections[connection_id] = {
            "connection_id": connection_id,
            "websocket": mock_websocket,
            "user_id": "user123",
            "conversation_id": "conv456",
            "authenticated": True,
            "last_activity": datetime.utcnow()
        }
        
        # Handle presence update message
        message_data = {
            "type": MessageType.PRESENCE_UPDATE,
            "status": "away",
            "metadata": {"reason": "idle"}
        }
        
        await websocket_gateway._process_websocket_message(connection_id, message_data)
        
        # Verify presence was updated
        presence = websocket_gateway.presence_manager.get_presence("user123")
        assert presence.status == "away"
    
    @pytest.mark.asyncio
    async def test_handle_typing_indicator_message(self, websocket_gateway, mock_websocket):
        """Test handling typing indicator WebSocket messages."""
        # Set up connection
        connection_id = "conn123"
        websocket_gateway.active_connections[connection_id] = {
            "connection_id": connection_id,
            "websocket": mock_websocket,
            "user_id": "user123",
            "conversation_id": "conv456",
            "authenticated": True,
            "last_activity": datetime.utcnow()
        }
        
        # Handle typing start message
        message_data = {
            "type": MessageType.TYPING_INDICATOR,
            "is_typing": True
        }
        
        await websocket_gateway._process_websocket_message(connection_id, message_data)
        
        # Verify typing indicator was set
        typing_users = websocket_gateway.typing_manager.get_typing_users("conv456")
        assert "user123" in typing_users
    
    @pytest.mark.asyncio
    async def test_handle_collaboration_invite(self, websocket_gateway, mock_websocket):
        """Test handling collaboration invite messages."""
        # Set up connection
        connection_id = "conn123"
        websocket_gateway.active_connections[connection_id] = {
            "connection_id": connection_id,
            "websocket": mock_websocket,
            "user_id": "user123",
            "conversation_id": "conv456",
            "authenticated": True,
            "last_activity": datetime.utcnow()
        }
        
        # Handle collaboration invite
        message_data = {
            "type": MessageType.COLLABORATION_INVITE,
            "invited_users": ["user456", "user789"],
            "session_type": "screen_share",
            "username": "testuser"
        }
        
        await websocket_gateway._process_websocket_message(connection_id, message_data)
        
        # Verify session was created
        user_sessions = websocket_gateway.collaboration_manager.get_user_sessions("user123")
        assert len(user_sessions) == 1
        assert user_sessions[0].session_type == "screen_share"
    
    def test_connection_stats_with_collaboration(self, websocket_gateway):
        """Test connection statistics include collaboration data."""
        # Add some test data
        websocket_gateway.active_connections["conn1"] = {
            "authenticated": True,
            "user_id": "user1",
            "conversation_id": "conv1"
        }
        websocket_gateway.active_connections["conn2"] = {
            "authenticated": True,
            "user_id": "user2",
            "conversation_id": "conv1"
        }
        websocket_gateway.user_connections["user1"] = {"conn1"}
        websocket_gateway.user_connections["user2"] = {"conn2"}
        websocket_gateway.conversation_connections["conv1"] = {"conn1", "conn2"}
        
        # Add presence data
        asyncio.run(websocket_gateway.presence_manager.update_presence("user1", "online"))
        asyncio.run(websocket_gateway.presence_manager.update_presence("user2", "online"))
        
        # Add typing data
        asyncio.run(websocket_gateway.typing_manager.set_typing("user1", "conv1", True))
        
        stats = websocket_gateway.get_connection_stats()
        
        assert stats["total_connections"] == 2
        assert stats["authenticated_connections"] == 2
        assert stats["unique_users"] == 2
        assert stats["active_conversations"] == 1
        assert stats["typing_users"] == 1
        assert stats["online_users"] == 2


class TestCollaborationAnalytics:
    """Test collaboration analytics integration."""
    
    @pytest.mark.asyncio
    async def test_collaboration_analytics_tracking(self):
        """Test collaboration analytics data collection."""
        from extensions.analytics.dashboard.analytics_extension import AnalyticsDashboardExtension
        
        analytics = AnalyticsDashboardExtension()
        
        # Test session tracking
        result = await analytics._track_collaboration_session(
            context={
                'session': {
                    'session_id': 'session123',
                    'conversation_id': 'conv456',
                    'session_type': 'screen_share',
                    'participants': ['user1', 'user2', 'user3']
                },
                'action': 'start'
            },
            user_context={'userId': 'user1'}
        )
        
        assert result['success'] is True
        assert result['collaboration_tracked'] is True
    
    @pytest.mark.asyncio
    async def test_collaboration_analytics_data_retrieval(self):
        """Test retrieving collaboration analytics data."""
        from extensions.analytics.dashboard.analytics_extension import AnalyticsDashboardExtension
        
        analytics = AnalyticsDashboardExtension()
        
        # Get collaboration analytics
        data = await analytics.get_collaboration_analytics(
            timeframe='24h',
            conversation_id='conv456'
        )
        
        # Verify data structure
        assert isinstance(data, dict)
        assert 'active_sessions' in data
        assert 'total_participants' in data
        assert 'session_types' in data
        assert 'presence_status' in data
        assert 'typing_activity' in data
        assert 'collaborative_edits' in data
        assert 'websocket_connections' in data
        
        # Verify data types
        assert isinstance(data['active_sessions'], int)
        assert isinstance(data['session_types'], dict)
        assert isinstance(data['presence_status'], dict)


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])