"""
WebSocket Gateway for Real-Time Chat Communication

This module implements WebSocket connection management with authentication,
message queuing for offline scenarios, typing indicators, presence management,
and connection recovery with reconnection logic.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Union, Callable, Awaitable
from enum import Enum

try:
    from fastapi import WebSocket, WebSocketDisconnect, status
    from fastapi.websockets import WebSocketState
except ImportError:
    # Stub for testing
    class WebSocket:
        def __init__(self): pass
        async def accept(self): pass
        async def send_text(self, data: str): pass
        async def send_json(self, data: dict): pass
        async def receive_text(self) -> str: return ""
        async def receive_json(self) -> dict: return {}
        async def close(self, code: int = 1000): pass
        @property
        def client_state(self): return "connected"
    
    class WebSocketDisconnect(Exception):
        def __init__(self, code: int = 1000): self.code = code
    
    class WebSocketState:
        CONNECTING = "connecting"
        CONNECTED = "connected"
        DISCONNECTED = "disconnected"

try:
    from pydantic import BaseModel, Field
except ImportError:
    from ai_karen_engine.pydantic_stub import BaseModel, Field

from ai_karen_engine.chat.chat_orchestrator import ChatOrchestrator, ChatRequest, ChatStreamChunk
from ai_karen_engine.utils.auth import validate_session

logger = logging.getLogger(__name__)


class ConnectionStatus(str, Enum):
    """WebSocket connection status."""
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    RECONNECTING = "reconnecting"
    FAILED = "failed"


class MessageType(str, Enum):
    """WebSocket message types."""
    # Client to server
    CHAT_MESSAGE = "chat_message"
    TYPING_START = "typing_start"
    TYPING_STOP = "typing_stop"
    PRESENCE_UPDATE = "presence_update"
    PING = "ping"
    AUTH = "auth"
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"
    
    # Server to client
    CHAT_RESPONSE = "chat_response"
    CHAT_STREAM_CHUNK = "chat_stream_chunk"
    TYPING_INDICATOR = "typing_indicator"
    PRESENCE_STATUS = "presence_status"
    PONG = "pong"
    ERROR = "error"
    AUTH_SUCCESS = "auth_success"
    AUTH_FAILED = "auth_failed"
    CONNECTION_STATUS = "connection_status"
    SYSTEM_MESSAGE = "system_message"


class PresenceStatus(str, Enum):
    """User presence status."""
    ONLINE = "online"
    AWAY = "away"
    BUSY = "busy"
    OFFLINE = "offline"


@dataclass
class WebSocketMessage:
    """WebSocket message structure."""
    type: MessageType
    data: Dict[str, Any] = field(default_factory=dict)
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    correlation_id: Optional[str] = None
    user_id: Optional[str] = None
    conversation_id: Optional[str] = None


@dataclass
class ConnectionInfo:
    """Information about a WebSocket connection."""
    connection_id: str
    websocket: WebSocket
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    conversation_id: Optional[str] = None
    status: ConnectionStatus = ConnectionStatus.CONNECTING
    connected_at: datetime = field(default_factory=datetime.utcnow)
    last_activity: datetime = field(default_factory=datetime.utcnow)
    subscriptions: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Typing and presence
    is_typing: bool = False
    typing_in_conversation: Optional[str] = None
    presence_status: PresenceStatus = PresenceStatus.ONLINE
    
    # Connection recovery
    reconnect_attempts: int = 0
    max_reconnect_attempts: int = 5
    reconnect_delay: float = 1.0


@dataclass
class QueuedMessage:
    """Message queued for offline delivery."""
    message: WebSocketMessage
    target_user_id: str
    target_conversation_id: Optional[str] = None
    queued_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    delivery_attempts: int = 0
    max_delivery_attempts: int = 3


class TypingManager:
    """Manages typing indicators across conversations."""
    
    def __init__(self, typing_timeout: float = 5.0):
        self.typing_timeout = typing_timeout
        self.typing_users: Dict[str, Dict[str, datetime]] = {}  # conversation_id -> {user_id: last_typing_time}
        self._cleanup_task: Optional[asyncio.Task] = None
        self._start_cleanup_task()
    
    def _start_cleanup_task(self):
        """Start the cleanup task for expired typing indicators."""
        try:
            if self._cleanup_task is None or self._cleanup_task.done():
                self._cleanup_task = asyncio.create_task(self._cleanup_expired_typing())
        except RuntimeError:
            # No event loop running, will start task later
            self._cleanup_task = None
    
    async def _cleanup_expired_typing(self):
        """Periodically clean up expired typing indicators."""
        while True:
            try:
                await asyncio.sleep(1.0)  # Check every second
                current_time = datetime.utcnow()
                
                for conversation_id in list(self.typing_users.keys()):
                    users_typing = self.typing_users[conversation_id]
                    expired_users = [
                        user_id for user_id, last_typing in users_typing.items()
                        if (current_time - last_typing).total_seconds() > self.typing_timeout
                    ]
                    
                    for user_id in expired_users:
                        del users_typing[user_id]
                        logger.debug(f"Expired typing indicator for user {user_id} in conversation {conversation_id}")
                    
                    if not users_typing:
                        del self.typing_users[conversation_id]
                        
            except Exception as e:
                logger.error(f"Error in typing cleanup task: {e}")
                await asyncio.sleep(5.0)  # Wait longer on error
    
    async def start_typing(self, user_id: str, conversation_id: str) -> List[str]:
        """Start typing indicator for user in conversation. Returns list of other users in conversation."""
        if conversation_id not in self.typing_users:
            self.typing_users[conversation_id] = {}
        
        self.typing_users[conversation_id][user_id] = datetime.utcnow()
        
        # Return other users in the conversation (for notification)
        return [uid for uid in self.typing_users[conversation_id].keys() if uid != user_id]
    
    async def stop_typing(self, user_id: str, conversation_id: str) -> List[str]:
        """Stop typing indicator for user in conversation. Returns list of other users in conversation."""
        if conversation_id in self.typing_users and user_id in self.typing_users[conversation_id]:
            del self.typing_users[conversation_id][user_id]
            
            if not self.typing_users[conversation_id]:
                del self.typing_users[conversation_id]
        
        # Return other users in the conversation (for notification)
        other_users = []
        if conversation_id in self.typing_users:
            other_users = [uid for uid in self.typing_users[conversation_id].keys() if uid != user_id]
        
        return other_users
    
    def get_typing_users(self, conversation_id: str) -> List[str]:
        """Get list of users currently typing in conversation."""
        return list(self.typing_users.get(conversation_id, {}).keys())
    
    def cleanup(self):
        """Clean up the typing manager."""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()


class PresenceManager:
    """Manages user presence status."""
    
    def __init__(self, presence_timeout: float = 300.0):  # 5 minutes
        self.presence_timeout = presence_timeout
        self.user_presence: Dict[str, Dict[str, Any]] = {}  # user_id -> presence_info
        self._cleanup_task: Optional[asyncio.Task] = None
        self._start_cleanup_task()
    
    def _start_cleanup_task(self):
        """Start the cleanup task for expired presence."""
        try:
            if self._cleanup_task is None or self._cleanup_task.done():
                self._cleanup_task = asyncio.create_task(self._cleanup_expired_presence())
        except RuntimeError:
            # No event loop running, will start task later
            self._cleanup_task = None
    
    async def _cleanup_expired_presence(self):
        """Periodically clean up expired presence status."""
        while True:
            try:
                await asyncio.sleep(30.0)  # Check every 30 seconds
                current_time = datetime.utcnow()
                
                for user_id in list(self.user_presence.keys()):
                    presence_info = self.user_presence[user_id]
                    last_activity = presence_info.get("last_activity")
                    
                    if last_activity and (current_time - last_activity).total_seconds() > self.presence_timeout:
                        presence_info["status"] = PresenceStatus.OFFLINE
                        logger.debug(f"User {user_id} marked as offline due to inactivity")
                        
            except Exception as e:
                logger.error(f"Error in presence cleanup task: {e}")
                await asyncio.sleep(60.0)  # Wait longer on error
    
    async def update_presence(self, user_id: str, status: PresenceStatus, metadata: Optional[Dict[str, Any]] = None):
        """Update user presence status."""
        if user_id not in self.user_presence:
            self.user_presence[user_id] = {}
        
        self.user_presence[user_id].update({
            "status": status,
            "last_activity": datetime.utcnow(),
            "metadata": metadata or {}
        })
        
        logger.debug(f"Updated presence for user {user_id}: {status}")
    
    async def update_activity(self, user_id: str):
        """Update user activity timestamp."""
        if user_id in self.user_presence:
            self.user_presence[user_id]["last_activity"] = datetime.utcnow()
    
    def get_presence(self, user_id: str) -> Dict[str, Any]:
        """Get user presence information."""
        return self.user_presence.get(user_id, {
            "status": PresenceStatus.OFFLINE,
            "last_activity": None,
            "metadata": {}
        })
    
    def get_online_users(self) -> List[str]:
        """Get list of online users."""
        online_users = []
        for user_id, presence_info in self.user_presence.items():
            if presence_info.get("status") == PresenceStatus.ONLINE:
                online_users.append(user_id)
        return online_users
    
    def cleanup(self):
        """Clean up the presence manager."""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()


class MessageQueue:
    """Manages message queuing for offline scenarios."""
    
    def __init__(self, max_queue_size: int = 1000, message_ttl: float = 86400.0):  # 24 hours
        self.max_queue_size = max_queue_size
        self.message_ttl = message_ttl
        self.queued_messages: Dict[str, List[QueuedMessage]] = {}  # user_id -> messages
        self._cleanup_task: Optional[asyncio.Task] = None
        self._start_cleanup_task()
    
    def _start_cleanup_task(self):
        """Start the cleanup task for expired messages."""
        try:
            if self._cleanup_task is None or self._cleanup_task.done():
                self._cleanup_task = asyncio.create_task(self._cleanup_expired_messages())
        except RuntimeError:
            # No event loop running, will start task later
            self._cleanup_task = None
    
    async def _cleanup_expired_messages(self):
        """Periodically clean up expired queued messages."""
        while True:
            try:
                await asyncio.sleep(300.0)  # Check every 5 minutes
                current_time = datetime.utcnow()
                
                for user_id in list(self.queued_messages.keys()):
                    messages = self.queued_messages[user_id]
                    
                    # Remove expired messages
                    valid_messages = []
                    for msg in messages:
                        if msg.expires_at and current_time > msg.expires_at:
                            logger.debug(f"Expired queued message {msg.message.message_id} for user {user_id}")
                            continue
                        
                        # Check TTL
                        if (current_time - msg.queued_at).total_seconds() > self.message_ttl:
                            logger.debug(f"TTL expired for queued message {msg.message.message_id} for user {user_id}")
                            continue
                        
                        valid_messages.append(msg)
                    
                    if valid_messages:
                        self.queued_messages[user_id] = valid_messages
                    else:
                        del self.queued_messages[user_id]
                        
            except Exception as e:
                logger.error(f"Error in message queue cleanup task: {e}")
                await asyncio.sleep(600.0)  # Wait longer on error
    
    async def queue_message(self, message: WebSocketMessage, target_user_id: str, target_conversation_id: Optional[str] = None):
        """Queue a message for offline delivery."""
        if target_user_id not in self.queued_messages:
            self.queued_messages[target_user_id] = []
        
        # Check queue size limit
        if len(self.queued_messages[target_user_id]) >= self.max_queue_size:
            # Remove oldest message
            self.queued_messages[target_user_id].pop(0)
            logger.warning(f"Queue size limit reached for user {target_user_id}, removed oldest message")
        
        # Set expiration time
        expires_at = datetime.utcnow() + timedelta(seconds=self.message_ttl)
        
        queued_msg = QueuedMessage(
            message=message,
            target_user_id=target_user_id,
            target_conversation_id=target_conversation_id,
            expires_at=expires_at
        )
        
        self.queued_messages[target_user_id].append(queued_msg)
        logger.debug(f"Queued message {message.message_id} for user {target_user_id}")
    
    async def get_queued_messages(self, user_id: str) -> List[QueuedMessage]:
        """Get all queued messages for a user."""
        return self.queued_messages.get(user_id, [])
    
    async def clear_queued_messages(self, user_id: str):
        """Clear all queued messages for a user."""
        if user_id in self.queued_messages:
            del self.queued_messages[user_id]
            logger.debug(f"Cleared queued messages for user {user_id}")
    
    async def mark_message_delivered(self, user_id: str, message_id: str):
        """Mark a queued message as delivered."""
        if user_id in self.queued_messages:
            self.queued_messages[user_id] = [
                msg for msg in self.queued_messages[user_id]
                if msg.message.message_id != message_id
            ]
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics."""
        total_messages = sum(len(messages) for messages in self.queued_messages.values())
        return {
            "total_queued_messages": total_messages,
            "users_with_queued_messages": len(self.queued_messages),
            "average_messages_per_user": total_messages / len(self.queued_messages) if self.queued_messages else 0
        }
    
    def cleanup(self):
        """Clean up the message queue."""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()


class WebSocketGateway:
    """
    WebSocket Gateway for Real-Time Chat Communication.
    
    Features:
    - WebSocket connection management with authentication
    - Message queuing system for offline scenarios
    - Typing indicators and presence management
    - Connection recovery and reconnection logic
    """
    
    def __init__(
        self,
        chat_orchestrator: ChatOrchestrator,
        auth_required: bool = True,
        heartbeat_interval: float = 30.0,
        connection_timeout: float = 300.0
    ):
        self.chat_orchestrator = chat_orchestrator
        self.auth_required = auth_required
        self.heartbeat_interval = heartbeat_interval
        self.connection_timeout = connection_timeout
        
        # Connection management
        self.connections: Dict[str, ConnectionInfo] = {}
        self.user_connections: Dict[str, Set[str]] = {}  # user_id -> connection_ids
        self.conversation_connections: Dict[str, Set[str]] = {}  # conversation_id -> connection_ids
        
        # Managers
        self.typing_manager = TypingManager()
        self.presence_manager = PresenceManager()
        self.message_queue = MessageQueue()
        
        # Background tasks
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._connection_cleanup_task: Optional[asyncio.Task] = None
        
        self._start_background_tasks()
        
        logger.info("WebSocketGateway initialized")
    
    def _start_background_tasks(self):
        """Start background tasks for connection management."""
        try:
            if self._heartbeat_task is None or self._heartbeat_task.done():
                self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
            
            if self._connection_cleanup_task is None or self._connection_cleanup_task.done():
                self._connection_cleanup_task = asyncio.create_task(self._connection_cleanup_loop())
        except RuntimeError:
            # No event loop running, will start tasks later
            self._heartbeat_task = None
            self._connection_cleanup_task = None
    
    async def _heartbeat_loop(self):
        """Send periodic heartbeat messages to maintain connections."""
        while True:
            try:
                await asyncio.sleep(self.heartbeat_interval)
                
                current_time = datetime.utcnow()
                for connection_id, conn_info in list(self.connections.items()):
                    try:
                        # Send ping
                        ping_message = WebSocketMessage(
                            type=MessageType.PING,
                            data={"timestamp": current_time.isoformat()}
                        )
                        await self._send_message_to_connection(connection_id, ping_message)
                        
                    except Exception as e:
                        logger.warning(f"Failed to send heartbeat to connection {connection_id}: {e}")
                        await self._handle_connection_error(connection_id, e)
                        
            except Exception as e:
                logger.error(f"Error in heartbeat loop: {e}")
                await asyncio.sleep(60.0)  # Wait longer on error
    
    async def _connection_cleanup_loop(self):
        """Clean up inactive connections."""
        while True:
            try:
                await asyncio.sleep(60.0)  # Check every minute
                
                current_time = datetime.utcnow()
                inactive_connections = []
                
                for connection_id, conn_info in self.connections.items():
                    if (current_time - conn_info.last_activity).total_seconds() > self.connection_timeout:
                        inactive_connections.append(connection_id)
                
                for connection_id in inactive_connections:
                    logger.info(f"Cleaning up inactive connection {connection_id}")
                    await self._disconnect_connection(connection_id, "Connection timeout")
                    
            except Exception as e:
                logger.error(f"Error in connection cleanup loop: {e}")
                await asyncio.sleep(300.0)  # Wait longer on error
    
    async def handle_websocket_connection(self, websocket: WebSocket, connection_id: Optional[str] = None) -> str:
        """
        Handle a new WebSocket connection.
        
        Args:
            websocket: WebSocket connection
            connection_id: Optional connection ID (generated if not provided)
            
        Returns:
            Connection ID
        """
        if connection_id is None:
            connection_id = str(uuid.uuid4())
        
        # Accept the connection
        await websocket.accept()
        
        # Create connection info
        conn_info = ConnectionInfo(
            connection_id=connection_id,
            websocket=websocket,
            status=ConnectionStatus.CONNECTED
        )
        
        self.connections[connection_id] = conn_info
        
        logger.info(f"WebSocket connection established: {connection_id}")
        
        try:
            # Send connection status
            status_message = WebSocketMessage(
                type=MessageType.CONNECTION_STATUS,
                data={
                    "status": ConnectionStatus.CONNECTED.value,
                    "connection_id": connection_id,
                    "server_time": datetime.utcnow().isoformat()
                }
            )
            await self._send_message_to_connection(connection_id, status_message)
            
            # Handle authentication if required
            if self.auth_required:
                await self._handle_authentication(connection_id)
            
            # Send queued messages if user is authenticated
            if conn_info.user_id:
                await self._send_queued_messages(connection_id)
            
            # Main message handling loop
            await self._handle_connection_messages(connection_id)
            
        except WebSocketDisconnect as e:
            logger.info(f"WebSocket disconnected: {connection_id} (code: {e.code})")
        except Exception as e:
            logger.error(f"Error handling WebSocket connection {connection_id}: {e}", exc_info=True)
        finally:
            await self._disconnect_connection(connection_id, "Connection closed")
        
        return connection_id
    
    async def _handle_authentication(self, connection_id: str):
        """Handle WebSocket authentication."""
        conn_info = self.connections[connection_id]
        
        # Wait for auth message
        auth_timeout = 30.0  # 30 seconds to authenticate
        start_time = time.time()
        
        while time.time() - start_time < auth_timeout:
            try:
                # Receive message with timeout
                message_data = await asyncio.wait_for(
                    conn_info.websocket.receive_text(),
                    timeout=5.0
                )
                
                message = json.loads(message_data)
                
                if message.get("type") == MessageType.AUTH.value:
                    token = message.get("data", {}).get("token")
                    if not token:
                        await self._send_auth_failed(connection_id, "Missing token")
                        return
                    
                    # Validate token
                    user_data = validate_session(token, "", "")  # TODO: Add proper user agent and IP
                    if not user_data:
                        await self._send_auth_failed(connection_id, "Invalid token")
                        return
                    
                    # Update connection info
                    conn_info.user_id = user_data.get("sub")
                    conn_info.session_id = message.get("data", {}).get("session_id")
                    conn_info.conversation_id = message.get("data", {}).get("conversation_id")
                    
                    # Track user connections
                    if conn_info.user_id not in self.user_connections:
                        self.user_connections[conn_info.user_id] = set()
                    self.user_connections[conn_info.user_id].add(connection_id)
                    
                    # Track conversation connections
                    if conn_info.conversation_id:
                        if conn_info.conversation_id not in self.conversation_connections:
                            self.conversation_connections[conn_info.conversation_id] = set()
                        self.conversation_connections[conn_info.conversation_id].add(connection_id)
                    
                    # Update presence
                    await self.presence_manager.update_presence(
                        conn_info.user_id,
                        PresenceStatus.ONLINE,
                        {"connection_id": connection_id}
                    )
                    
                    # Send auth success
                    await self._send_auth_success(connection_id)
                    return
                    
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error during authentication for {connection_id}: {e}")
                await self._send_auth_failed(connection_id, "Authentication error")
                return
        
        # Authentication timeout
        await self._send_auth_failed(connection_id, "Authentication timeout")
        await self._disconnect_connection(connection_id, "Authentication timeout")
    
    async def _send_auth_success(self, connection_id: str):
        """Send authentication success message."""
        conn_info = self.connections[connection_id]
        message = WebSocketMessage(
            type=MessageType.AUTH_SUCCESS,
            data={
                "user_id": conn_info.user_id,
                "session_id": conn_info.session_id,
                "connection_id": connection_id
            }
        )
        await self._send_message_to_connection(connection_id, message)
    
    async def _send_auth_failed(self, connection_id: str, reason: str):
        """Send authentication failed message."""
        message = WebSocketMessage(
            type=MessageType.AUTH_FAILED,
            data={"reason": reason}
        )
        await self._send_message_to_connection(connection_id, message)
    
    async def _send_queued_messages(self, connection_id: str):
        """Send queued messages to a newly connected user."""
        conn_info = self.connections[connection_id]
        if not conn_info.user_id:
            return
        
        queued_messages = await self.message_queue.get_queued_messages(conn_info.user_id)
        
        for queued_msg in queued_messages:
            try:
                await self._send_message_to_connection(connection_id, queued_msg.message)
                await self.message_queue.mark_message_delivered(conn_info.user_id, queued_msg.message.message_id)
                logger.debug(f"Delivered queued message {queued_msg.message.message_id} to {conn_info.user_id}")
            except Exception as e:
                logger.error(f"Failed to deliver queued message: {e}")
        
        # Clear delivered messages
        await self.message_queue.clear_queued_messages(conn_info.user_id)
    
    async def _handle_connection_messages(self, connection_id: str):
        """Handle incoming messages from a WebSocket connection."""
        conn_info = self.connections[connection_id]
        
        while conn_info.status == ConnectionStatus.CONNECTED:
            try:
                # Receive message
                message_data = await conn_info.websocket.receive_text()
                message_dict = json.loads(message_data)
                
                # Update activity
                conn_info.last_activity = datetime.utcnow()
                if conn_info.user_id:
                    await self.presence_manager.update_activity(conn_info.user_id)
                
                # Parse message
                message = WebSocketMessage(
                    type=MessageType(message_dict.get("type")),
                    data=message_dict.get("data", {}),
                    message_id=message_dict.get("message_id", str(uuid.uuid4())),
                    correlation_id=message_dict.get("correlation_id"),
                    user_id=conn_info.user_id,
                    conversation_id=message_dict.get("conversation_id") or conn_info.conversation_id
                )
                
                # Handle message based on type
                await self._handle_message(connection_id, message)
                
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError as e:
                logger.warning(f"Invalid JSON from connection {connection_id}: {e}")
                await self._send_error(connection_id, "Invalid JSON format")
            except Exception as e:
                logger.error(f"Error handling message from {connection_id}: {e}")
                await self._send_error(connection_id, f"Message handling error: {str(e)}")
    
    async def _handle_message(self, connection_id: str, message: WebSocketMessage):
        """Handle a specific message type."""
        conn_info = self.connections[connection_id]
        
        if message.type == MessageType.CHAT_MESSAGE:
            await self._handle_chat_message(connection_id, message)
        
        elif message.type == MessageType.TYPING_START:
            await self._handle_typing_start(connection_id, message)
        
        elif message.type == MessageType.TYPING_STOP:
            await self._handle_typing_stop(connection_id, message)
        
        elif message.type == MessageType.PRESENCE_UPDATE:
            await self._handle_presence_update(connection_id, message)
        
        elif message.type == MessageType.PING:
            await self._handle_ping(connection_id, message)
        
        elif message.type == MessageType.SUBSCRIBE:
            await self._handle_subscribe(connection_id, message)
        
        elif message.type == MessageType.UNSUBSCRIBE:
            await self._handle_unsubscribe(connection_id, message)
        
        else:
            logger.warning(f"Unknown message type from {connection_id}: {message.type}")
            await self._send_error(connection_id, f"Unknown message type: {message.type}")
    
    async def _handle_chat_message(self, connection_id: str, message: WebSocketMessage):
        """Handle chat message."""
        conn_info = self.connections[connection_id]
        
        if not conn_info.user_id:
            await self._send_error(connection_id, "Authentication required")
            return
        
        if not message.conversation_id:
            await self._send_error(connection_id, "Conversation ID required")
            return
        
        try:
            # Create chat request
            chat_request = ChatRequest(
                message=message.data.get("content", ""),
                user_id=conn_info.user_id,
                conversation_id=message.conversation_id,
                session_id=conn_info.session_id,
                stream=message.data.get("stream", True),
                include_context=message.data.get("include_context", True),
                metadata={
                    "connection_id": connection_id,
                    "message_id": message.message_id,
                    "correlation_id": message.correlation_id
                }
            )
            
            # Process with chat orchestrator
            if chat_request.stream:
                # Handle streaming response
                async for chunk in await self.chat_orchestrator.process_message(chat_request):
                    chunk_message = WebSocketMessage(
                        type=MessageType.CHAT_STREAM_CHUNK,
                        data={
                            "chunk_type": chunk.type,
                            "content": chunk.content,
                            "metadata": chunk.metadata
                        },
                        correlation_id=message.correlation_id,
                        conversation_id=message.conversation_id
                    )
                    await self._send_message_to_connection(connection_id, chunk_message)
            else:
                # Handle traditional response
                response = await self.chat_orchestrator.process_message(chat_request)
                response_message = WebSocketMessage(
                    type=MessageType.CHAT_RESPONSE,
                    data={
                        "response": response.response,
                        "processing_time": response.processing_time,
                        "used_fallback": response.used_fallback,
                        "context_used": response.context_used,
                        "metadata": response.metadata
                    },
                    correlation_id=message.correlation_id,
                    conversation_id=message.conversation_id
                )
                await self._send_message_to_connection(connection_id, response_message)
                
        except Exception as e:
            logger.error(f"Error processing chat message: {e}")
            await self._send_error(connection_id, f"Chat processing error: {str(e)}", message.correlation_id)
    
    async def _handle_typing_start(self, connection_id: str, message: WebSocketMessage):
        """Handle typing start indicator."""
        conn_info = self.connections[connection_id]
        
        if not conn_info.user_id or not message.conversation_id:
            return
        
        # Update connection typing status
        conn_info.is_typing = True
        conn_info.typing_in_conversation = message.conversation_id
        
        # Update typing manager
        other_users = await self.typing_manager.start_typing(conn_info.user_id, message.conversation_id)
        
        # Notify other users in the conversation
        typing_message = WebSocketMessage(
            type=MessageType.TYPING_INDICATOR,
            data={
                "user_id": conn_info.user_id,
                "is_typing": True,
                "conversation_id": message.conversation_id
            },
            conversation_id=message.conversation_id
        )
        
        await self._broadcast_to_conversation(message.conversation_id, typing_message, exclude_user=conn_info.user_id)
    
    async def _handle_typing_stop(self, connection_id: str, message: WebSocketMessage):
        """Handle typing stop indicator."""
        conn_info = self.connections[connection_id]
        
        if not conn_info.user_id or not message.conversation_id:
            return
        
        # Update connection typing status
        conn_info.is_typing = False
        conn_info.typing_in_conversation = None
        
        # Update typing manager
        other_users = await self.typing_manager.stop_typing(conn_info.user_id, message.conversation_id)
        
        # Notify other users in the conversation
        typing_message = WebSocketMessage(
            type=MessageType.TYPING_INDICATOR,
            data={
                "user_id": conn_info.user_id,
                "is_typing": False,
                "conversation_id": message.conversation_id
            },
            conversation_id=message.conversation_id
        )
        
        await self._broadcast_to_conversation(message.conversation_id, typing_message, exclude_user=conn_info.user_id)
    
    async def _handle_presence_update(self, connection_id: str, message: WebSocketMessage):
        """Handle presence status update."""
        conn_info = self.connections[connection_id]
        
        if not conn_info.user_id:
            return
        
        status_str = message.data.get("status")
        if not status_str:
            return
        
        try:
            status = PresenceStatus(status_str)
            conn_info.presence_status = status
            
            await self.presence_manager.update_presence(
                conn_info.user_id,
                status,
                message.data.get("metadata", {})
            )
            
            # Broadcast presence update
            presence_message = WebSocketMessage(
                type=MessageType.PRESENCE_STATUS,
                data={
                    "user_id": conn_info.user_id,
                    "status": status.value,
                    "metadata": message.data.get("metadata", {})
                }
            )
            
            await self._broadcast_to_all_users(presence_message, exclude_user=conn_info.user_id)
            
        except ValueError:
            await self._send_error(connection_id, f"Invalid presence status: {status_str}")
    
    async def _handle_ping(self, connection_id: str, message: WebSocketMessage):
        """Handle ping message."""
        pong_message = WebSocketMessage(
            type=MessageType.PONG,
            data=message.data,
            correlation_id=message.correlation_id
        )
        await self._send_message_to_connection(connection_id, pong_message)
    
    async def _handle_subscribe(self, connection_id: str, message: WebSocketMessage):
        """Handle subscription to topics."""
        conn_info = self.connections[connection_id]
        topics = message.data.get("topics", [])
        
        for topic in topics:
            conn_info.subscriptions.add(topic)
        
        logger.debug(f"Connection {connection_id} subscribed to topics: {topics}")
    
    async def _handle_unsubscribe(self, connection_id: str, message: WebSocketMessage):
        """Handle unsubscription from topics."""
        conn_info = self.connections[connection_id]
        topics = message.data.get("topics", [])
        
        for topic in topics:
            conn_info.subscriptions.discard(topic)
        
        logger.debug(f"Connection {connection_id} unsubscribed from topics: {topics}")
    
    async def _send_message_to_connection(self, connection_id: str, message: WebSocketMessage):
        """Send message to a specific connection."""
        if connection_id not in self.connections:
            return
        
        conn_info = self.connections[connection_id]
        
        try:
            message_dict = {
                "type": message.type.value,
                "data": message.data,
                "message_id": message.message_id,
                "timestamp": message.timestamp.isoformat(),
                "correlation_id": message.correlation_id,
                "conversation_id": message.conversation_id
            }
            
            await conn_info.websocket.send_text(json.dumps(message_dict))
            
        except Exception as e:
            logger.error(f"Failed to send message to connection {connection_id}: {e}")
            await self._handle_connection_error(connection_id, e)
    
    async def _send_error(self, connection_id: str, error_message: str, correlation_id: Optional[str] = None):
        """Send error message to connection."""
        error_msg = WebSocketMessage(
            type=MessageType.ERROR,
            data={"error": error_message},
            correlation_id=correlation_id
        )
        await self._send_message_to_connection(connection_id, error_msg)
    
    async def _broadcast_to_conversation(self, conversation_id: str, message: WebSocketMessage, exclude_user: Optional[str] = None):
        """Broadcast message to all connections in a conversation."""
        if conversation_id not in self.conversation_connections:
            return
        
        connection_ids = self.conversation_connections[conversation_id].copy()
        
        for connection_id in connection_ids:
            if connection_id not in self.connections:
                continue
            
            conn_info = self.connections[connection_id]
            if exclude_user and conn_info.user_id == exclude_user:
                continue
            
            try:
                await self._send_message_to_connection(connection_id, message)
            except Exception as e:
                logger.error(f"Failed to broadcast to connection {connection_id}: {e}")
    
    async def _broadcast_to_all_users(self, message: WebSocketMessage, exclude_user: Optional[str] = None):
        """Broadcast message to all connected users."""
        for connection_id, conn_info in self.connections.items():
            if exclude_user and conn_info.user_id == exclude_user:
                continue
            
            try:
                await self._send_message_to_connection(connection_id, message)
            except Exception as e:
                logger.error(f"Failed to broadcast to connection {connection_id}: {e}")
    
    async def _handle_connection_error(self, connection_id: str, error: Exception):
        """Handle connection error."""
        logger.warning(f"Connection error for {connection_id}: {error}")
        await self._disconnect_connection(connection_id, f"Connection error: {str(error)}")
    
    async def _disconnect_connection(self, connection_id: str, reason: str):
        """Disconnect and clean up a connection."""
        if connection_id not in self.connections:
            return
        
        conn_info = self.connections[connection_id]
        
        try:
            # Update status
            conn_info.status = ConnectionStatus.DISCONNECTED
            
            # Stop typing if active
            if conn_info.is_typing and conn_info.typing_in_conversation:
                await self.typing_manager.stop_typing(conn_info.user_id, conn_info.typing_in_conversation)
            
            # Update presence to offline
            if conn_info.user_id:
                await self.presence_manager.update_presence(conn_info.user_id, PresenceStatus.OFFLINE)
            
            # Close WebSocket
            if conn_info.websocket.client_state != WebSocketState.DISCONNECTED:
                await conn_info.websocket.close()
            
            # Clean up tracking
            if conn_info.user_id and conn_info.user_id in self.user_connections:
                self.user_connections[conn_info.user_id].discard(connection_id)
                if not self.user_connections[conn_info.user_id]:
                    del self.user_connections[conn_info.user_id]
            
            if conn_info.conversation_id and conn_info.conversation_id in self.conversation_connections:
                self.conversation_connections[conn_info.conversation_id].discard(connection_id)
                if not self.conversation_connections[conn_info.conversation_id]:
                    del self.conversation_connections[conn_info.conversation_id]
            
            # Remove connection
            del self.connections[connection_id]
            
            logger.info(f"Connection {connection_id} disconnected: {reason}")
            
        except Exception as e:
            logger.error(f"Error during connection cleanup for {connection_id}: {e}")
    
    async def send_message_to_user(self, user_id: str, message: WebSocketMessage) -> bool:
        """Send message to all connections of a specific user."""
        if user_id not in self.user_connections:
            # User is offline, queue the message
            await self.message_queue.queue_message(message, user_id)
            return False
        
        connection_ids = self.user_connections[user_id].copy()
        sent_to_any = False
        
        for connection_id in connection_ids:
            try:
                await self._send_message_to_connection(connection_id, message)
                sent_to_any = True
            except Exception as e:
                logger.error(f"Failed to send message to user {user_id} connection {connection_id}: {e}")
        
        return sent_to_any
    
    async def send_message_to_conversation(self, conversation_id: str, message: WebSocketMessage, exclude_user: Optional[str] = None):
        """Send message to all users in a conversation."""
        await self._broadcast_to_conversation(conversation_id, message, exclude_user)
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection statistics."""
        total_connections = len(self.connections)
        authenticated_connections = sum(1 for conn in self.connections.values() if conn.user_id)
        typing_users = sum(1 for conn in self.connections.values() if conn.is_typing)
        
        return {
            "total_connections": total_connections,
            "authenticated_connections": authenticated_connections,
            "unique_users": len(self.user_connections),
            "active_conversations": len(self.conversation_connections),
            "typing_users": typing_users,
            "online_users": len(self.presence_manager.get_online_users()),
            "queue_stats": self.message_queue.get_queue_stats()
        }
    
    def get_user_connections(self, user_id: str) -> List[str]:
        """Get all connection IDs for a user."""
        return list(self.user_connections.get(user_id, set()))
    
    def get_conversation_connections(self, conversation_id: str) -> List[str]:
        """Get all connection IDs for a conversation."""
        return list(self.conversation_connections.get(conversation_id, set()))
    
    async def cleanup(self):
        """Clean up the WebSocket gateway."""
        # Cancel background tasks
        if self._heartbeat_task and not self._heartbeat_task.done():
            self._heartbeat_task.cancel()
        
        if self._connection_cleanup_task and not self._connection_cleanup_task.done():
            self._connection_cleanup_task.cancel()
        
        # Disconnect all connections
        for connection_id in list(self.connections.keys()):
            await self._disconnect_connection(connection_id, "Server shutdown")
        
        # Clean up managers
        self.typing_manager.cleanup()
        self.presence_manager.cleanup()
        self.message_queue.cleanup()
        
        logger.info("WebSocketGateway cleaned up")