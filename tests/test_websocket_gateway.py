"""
Tests for WebSocket Gateway functionality.

This module tests the WebSocket gateway implementation including
connection management, message handling, typing indicators,
presence management, and message queuing.
"""

import asyncio
import json
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any, List

# Import the modules to test
from src.ai_karen_engine.chat.websocket_gateway import (
    WebSocketGateway,
    WebSocketMessage,
    MessageType,
    ConnectionStatus,
    PresenceStatus,
    TypingManager,
    PresenceManager,
    MessageQueue,
    ConnectionInfo
)
from src.ai_karen_engine.chat.chat_orchestrator import ChatOrchestrator, ChatRequest, ChatResponse


class MockWebSocket:
    """Mock WebSocket for testing."""
    
    def __init__(self):
        self.messages_sent = []
        self.messages_to_receive = []
        self.closed = False
        self.client_state = "connected"
    
    async def accept(self):
        """Mock accept method."""
        pass
    
    async def send_text(self, data: str):
        """Mock send_text method."""
        if self.closed:
            raise Exception("WebSocket is closed")
        self.messages_sent.append(data)
    
    async def receive_text(self) -> str:
        """Mock receive_text method."""
        if self.closed:
            raise Exception("WebSocket is closed")
        
        if self.messages_to_receive:
            return self.messages_to_receive.pop(0)
        
        # Simulate waiting for message
        await asyncio.sleep(0.1)
        if self.messages_to_receive:
            return self.messages_to_receive.pop(0)
        
        # Simulate disconnect if no more messages
        from src.ai_karen_engine.chat.websocket_gateway import WebSocketDisconnect
        raise WebSocketDisconnect(1000)
    
    async def close(self, code: int = 1000):
        """Mock close method."""
        self.closed = True
    
    def add_message_to_receive(self, message: Dict[str, Any]):
        """Add a message to be received."""
        self.messages_to_receive.append(json.dumps(message))


class MockChatOrchestrator:
    """Mock ChatOrchestrator for testing."""
    
    def __init__(self):
        self.process_calls = []
    
    async def process_message(self, request: ChatRequest):
        """Mock process_message method."""
        self.process_calls.append(request)
        
        if request.stream:
            # Return async generator for streaming
            async def stream_generator():
                yield type('ChatStreamChunk', (), {
                    'type': 'content',
                    'content': 'Hello',
                    'metadata': {},
                    'timestamp': datetime.utcnow()
                })()
                yield type('ChatStreamChunk', (), {
                    'type': 'content',
                    'content': ' world!',
                    'metadata': {},
                    'timestamp': datetime.utcnow()
                })()
                yield type('ChatStreamChunk', (), {
                    'type': 'complete',
                    'content': '',
                    'metadata': {'processing_time': 0.5},
                    'timestamp': datetime.utcnow()
                })()
            
            return stream_generator()
        else:
            # Return traditional response
            return ChatResponse(
                response="Hello world!",
                correlation_id=request.metadata.get('correlation_id', ''),
                processing_time=0.5,
                used_fallback=False,
                context_used=True,
                metadata={}
            )


@pytest.fixture
def mock_chat_orchestrator():
    """Create mock chat orchestrator."""
    return MockChatOrchestrator()


@pytest.fixture
def websocket_gateway(mock_chat_orchestrator):
    """Create WebSocket gateway for testing."""
    return WebSocketGateway(
        chat_orchestrator=mock_chat_orchestrator,
        auth_required=False,  # Disable auth for testing
        heartbeat_interval=1.0,  # Short interval for testing
        connection_timeout=5.0   # Short timeout for testing
    )


@pytest.fixture
def mock_websocket():
    """Create mock WebSocket."""
    return MockWebSocket()


class TestTypingManager:
    """Test TypingManager functionality."""
    
    @pytest.fixture
    def typing_manager(self):
        """Create typing manager for testing."""
        return TypingManager(typing_timeout=1.0)  # Short timeout for testing
    
    @pytest.mark.asyncio
    async def test_start_typing(self, typing_manager):
        """Test starting typing indicator."""
        other_users = await typing_manager.start_typing("user1", "conv1")
        assert other_users == []
        
        # Add another user
        other_users = await typing_manager.start_typing("user2", "conv1")
        assert "user1" in other_users
        assert "user2" not in other_users
    
    @pytest.mark.asyncio
    async def test_stop_typing(self, typing_manager):
        """Test stopping typing indicator."""
        await typing_manager.start_typing("user1", "conv1")
        await typing_manager.start_typing("user2", "conv1")
        
        other_users = await typing_manager.stop_typing("user1", "conv1")
        assert "user2" in other_users
        assert "user1" not in other_users
    
    def test_get_typing_users(self, typing_manager):
        """Test getting typing users."""
        asyncio.run(typing_manager.start_typing("user1", "conv1"))
        asyncio.run(typing_manager.start_typing("user2", "conv1"))
        
        typing_users = typing_manager.get_typing_users("conv1")
        assert "user1" in typing_users
        assert "user2" in typing_users
    
    @pytest.mark.asyncio
    async def test_typing_timeout(self, typing_manager):
        """Test typing indicator timeout."""
        await typing_manager.start_typing("user1", "conv1")
        
        # Wait for timeout
        await asyncio.sleep(1.5)
        
        typing_users = typing_manager.get_typing_users("conv1")
        assert typing_users == []


class TestPresenceManager:
    """Test PresenceManager functionality."""
    
    @pytest.fixture
    def presence_manager(self):
        """Create presence manager for testing."""
        return PresenceManager(presence_timeout=1.0)  # Short timeout for testing
    
    @pytest.mark.asyncio
    async def test_update_presence(self, presence_manager):
        """Test updating user presence."""
        await presence_manager.update_presence("user1", PresenceStatus.ONLINE)
        
        presence = presence_manager.get_presence("user1")
        assert presence["status"] == PresenceStatus.ONLINE
        assert presence["last_activity"] is not None
    
    @pytest.mark.asyncio
    async def test_update_activity(self, presence_manager):
        """Test updating user activity."""
        await presence_manager.update_presence("user1", PresenceStatus.ONLINE)
        original_activity = presence_manager.get_presence("user1")["last_activity"]
        
        await asyncio.sleep(0.1)
        await presence_manager.update_activity("user1")
        
        updated_activity = presence_manager.get_presence("user1")["last_activity"]
        assert updated_activity > original_activity
    
    def test_get_online_users(self, presence_manager):
        """Test getting online users."""
        asyncio.run(presence_manager.update_presence("user1", PresenceStatus.ONLINE))
        asyncio.run(presence_manager.update_presence("user2", PresenceStatus.AWAY))
        asyncio.run(presence_manager.update_presence("user3", PresenceStatus.OFFLINE))
        
        online_users = presence_manager.get_online_users()
        assert "user1" in online_users
        assert "user2" not in online_users
        assert "user3" not in online_users


class TestMessageQueue:
    """Test MessageQueue functionality."""
    
    @pytest.fixture
    def message_queue(self):
        """Create message queue for testing."""
        return MessageQueue(max_queue_size=5, message_ttl=1.0)  # Small size and short TTL for testing
    
    @pytest.mark.asyncio
    async def test_queue_message(self, message_queue):
        """Test queuing messages."""
        message = WebSocketMessage(
            type=MessageType.CHAT_RESPONSE,
            data={"content": "Hello"}
        )
        
        await message_queue.queue_message(message, "user1")
        
        queued_messages = await message_queue.get_queued_messages("user1")
        assert len(queued_messages) == 1
        assert queued_messages[0].message.data["content"] == "Hello"
    
    @pytest.mark.asyncio
    async def test_queue_size_limit(self, message_queue):
        """Test queue size limit."""
        # Queue more messages than the limit
        for i in range(7):
            message = WebSocketMessage(
                type=MessageType.CHAT_RESPONSE,
                data={"content": f"Message {i}"}
            )
            await message_queue.queue_message(message, "user1")
        
        queued_messages = await message_queue.get_queued_messages("user1")
        assert len(queued_messages) == 5  # Should be limited to max_queue_size
    
    @pytest.mark.asyncio
    async def test_clear_queued_messages(self, message_queue):
        """Test clearing queued messages."""
        message = WebSocketMessage(
            type=MessageType.CHAT_RESPONSE,
            data={"content": "Hello"}
        )
        
        await message_queue.queue_message(message, "user1")
        await message_queue.clear_queued_messages("user1")
        
        queued_messages = await message_queue.get_queued_messages("user1")
        assert len(queued_messages) == 0
    
    @pytest.mark.asyncio
    async def test_mark_message_delivered(self, message_queue):
        """Test marking message as delivered."""
        message = WebSocketMessage(
            type=MessageType.CHAT_RESPONSE,
            data={"content": "Hello"}
        )
        
        await message_queue.queue_message(message, "user1")
        await message_queue.mark_message_delivered("user1", message.message_id)
        
        queued_messages = await message_queue.get_queued_messages("user1")
        assert len(queued_messages) == 0


class TestWebSocketGateway:
    """Test WebSocketGateway functionality."""
    
    @pytest.mark.asyncio
    async def test_websocket_connection_without_auth(self, websocket_gateway, mock_websocket):
        """Test WebSocket connection without authentication."""
        # Add a simple message to be received
        mock_websocket.add_message_to_receive({
            "type": "ping",
            "data": {}
        })
        
        connection_id = await websocket_gateway.handle_websocket_connection(mock_websocket)
        
        assert connection_id is not None
        assert len(mock_websocket.messages_sent) > 0
        
        # Check that connection status was sent
        first_message = json.loads(mock_websocket.messages_sent[0])
        assert first_message["type"] == "connection_status"
        assert first_message["data"]["status"] == "connected"
    
    @pytest.mark.asyncio
    async def test_websocket_chat_message(self, websocket_gateway, mock_websocket, mock_chat_orchestrator):
        """Test handling chat message via WebSocket."""
        # Add chat message to be received
        mock_websocket.add_message_to_receive({
            "type": "chat_message",
            "data": {
                "content": "Hello world",
                "stream": False
            },
            "conversation_id": "conv1"
        })
        
        # Create a connection with user ID
        connection_id = await websocket_gateway.handle_websocket_connection(mock_websocket)
        
        # Manually set user ID for testing (since auth is disabled)
        if connection_id in websocket_gateway.connections:
            websocket_gateway.connections[connection_id].user_id = "user1"
        
        # Wait a bit for message processing
        await asyncio.sleep(0.2)
        
        # Check that chat orchestrator was called
        assert len(mock_chat_orchestrator.process_calls) > 0
        
        # Check that response was sent
        response_messages = [
            json.loads(msg) for msg in mock_websocket.messages_sent
            if json.loads(msg)["type"] == "chat_response"
        ]
        assert len(response_messages) > 0
    
    @pytest.mark.asyncio
    async def test_typing_indicators(self, websocket_gateway, mock_websocket):
        """Test typing indicators via WebSocket."""
        # Add typing start message
        mock_websocket.add_message_to_receive({
            "type": "typing_start",
            "data": {},
            "conversation_id": "conv1"
        })
        
        connection_id = await websocket_gateway.handle_websocket_connection(mock_websocket)
        
        # Manually set user ID for testing
        if connection_id in websocket_gateway.connections:
            websocket_gateway.connections[connection_id].user_id = "user1"
        
        await asyncio.sleep(0.1)
        
        # Check typing status
        typing_users = websocket_gateway.typing_manager.get_typing_users("conv1")
        assert "user1" in typing_users
    
    @pytest.mark.asyncio
    async def test_presence_update(self, websocket_gateway, mock_websocket):
        """Test presence update via WebSocket."""
        # Add presence update message
        mock_websocket.add_message_to_receive({
            "type": "presence_update",
            "data": {
                "status": "away"
            }
        })
        
        connection_id = await websocket_gateway.handle_websocket_connection(mock_websocket)
        
        # Manually set user ID for testing
        if connection_id in websocket_gateway.connections:
            websocket_gateway.connections[connection_id].user_id = "user1"
        
        await asyncio.sleep(0.1)
        
        # Check presence status
        presence = websocket_gateway.presence_manager.get_presence("user1")
        assert presence["status"] == PresenceStatus.AWAY
    
    @pytest.mark.asyncio
    async def test_send_message_to_user(self, websocket_gateway, mock_websocket):
        """Test sending message to specific user."""
        # Establish connection
        connection_id = await websocket_gateway.handle_websocket_connection(mock_websocket)
        
        # Manually set user ID and add to user connections
        if connection_id in websocket_gateway.connections:
            websocket_gateway.connections[connection_id].user_id = "user1"
            websocket_gateway.user_connections["user1"] = {connection_id}
        
        # Send message to user
        message = WebSocketMessage(
            type=MessageType.SYSTEM_MESSAGE,
            data={"content": "System notification"}
        )
        
        success = await websocket_gateway.send_message_to_user("user1", message)
        assert success
        
        # Check that message was sent
        system_messages = [
            json.loads(msg) for msg in mock_websocket.messages_sent
            if json.loads(msg)["type"] == "system_message"
        ]
        assert len(system_messages) > 0
    
    @pytest.mark.asyncio
    async def test_offline_message_queuing(self, websocket_gateway):
        """Test message queuing for offline users."""
        message = WebSocketMessage(
            type=MessageType.CHAT_RESPONSE,
            data={"content": "Hello offline user"}
        )
        
        # Send message to offline user
        success = await websocket_gateway.send_message_to_user("offline_user", message)
        assert not success  # Should return False for offline user
        
        # Check that message was queued
        queued_messages = await websocket_gateway.message_queue.get_queued_messages("offline_user")
        assert len(queued_messages) == 1
        assert queued_messages[0].message.data["content"] == "Hello offline user"
    
    def test_connection_stats(self, websocket_gateway):
        """Test getting connection statistics."""
        stats = websocket_gateway.get_connection_stats()
        
        assert "total_connections" in stats
        assert "authenticated_connections" in stats
        assert "unique_users" in stats
        assert "active_conversations" in stats
        assert "typing_users" in stats
        assert "online_users" in stats
        assert "queue_stats" in stats
    
    @pytest.mark.asyncio
    async def test_cleanup(self, websocket_gateway):
        """Test gateway cleanup."""
        # Add some connections
        mock_ws1 = MockWebSocket()
        mock_ws2 = MockWebSocket()
        
        await websocket_gateway.handle_websocket_connection(mock_ws1)
        await websocket_gateway.handle_websocket_connection(mock_ws2)
        
        # Cleanup
        await websocket_gateway.cleanup()
        
        # Check that connections were cleaned up
        assert len(websocket_gateway.connections) == 0
        assert len(websocket_gateway.user_connections) == 0


class TestWebSocketMessage:
    """Test WebSocketMessage functionality."""
    
    def test_websocket_message_creation(self):
        """Test creating WebSocket message."""
        message = WebSocketMessage(
            type=MessageType.CHAT_MESSAGE,
            data={"content": "Hello"},
            user_id="user1",
            conversation_id="conv1"
        )
        
        assert message.type == MessageType.CHAT_MESSAGE
        assert message.data["content"] == "Hello"
        assert message.user_id == "user1"
        assert message.conversation_id == "conv1"
        assert message.message_id is not None
        assert message.timestamp is not None
    
    def test_websocket_message_serialization(self):
        """Test WebSocket message serialization."""
        message = WebSocketMessage(
            type=MessageType.CHAT_RESPONSE,
            data={"response": "Hello world"},
            correlation_id="corr123"
        )
        
        # Test that message can be serialized to JSON
        message_dict = {
            "type": message.type.value,
            "data": message.data,
            "message_id": message.message_id,
            "timestamp": message.timestamp.isoformat(),
            "correlation_id": message.correlation_id
        }
        
        json_str = json.dumps(message_dict)
        assert json_str is not None
        
        # Test deserialization
        parsed = json.loads(json_str)
        assert parsed["type"] == MessageType.CHAT_RESPONSE.value
        assert parsed["data"]["response"] == "Hello world"


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])