import asyncio
import contextlib
import json
import logging
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set

from ai_karen_engine.chat.chat_orchestrator import ChatRequest
from ai_karen_engine.event_bus import get_event_bus

logger = logging.getLogger(__name__)


@dataclass
class CollaborationUser:
    """Represents a user in a collaboration session."""

    user_id: str
    username: str
    status: str = "online"
    last_seen: Optional[datetime] = None
    typing_in: Optional[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.last_seen is None:
            self.last_seen = datetime.utcnow()


@dataclass
class CollaborationSession:
    """Represents an active collaboration session."""

    session_id: str
    conversation_id: str
    participants: List[CollaborationUser]
    session_type: str = "chat"
    started_at: Optional[datetime] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.started_at is None:
            self.started_at = datetime.utcnow()


class WebSocketMessage:
    """Represents a message sent or received over the websocket."""

    def __init__(
        self,
        content: str,
        type_: "MessageType",
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.content = content
        self.type = type_
        self.metadata = metadata or {}
        self.timestamp = datetime.utcnow()
        self.message_id = str(uuid.uuid4())


class MessageType:
    """Enumeration of websocket message types."""

    TEXT = "text"
    BINARY = "binary"
    PING = "ping"
    PONG = "pong"
    CLOSE = "close"

    # Collaboration-specific message types
    PRESENCE_UPDATE = "presence_update"
    TYPING_INDICATOR = "typing_indicator"
    COLLABORATION_INVITE = "collaboration_invite"
    COLLABORATION_JOIN = "collaboration_join"
    COLLABORATION_LEAVE = "collaboration_leave"
    COLLABORATIVE_EDIT = "collaborative_edit"
    CURSOR_POSITION = "cursor_position"
    SCREEN_SHARE_START = "screen_share_start"
    SCREEN_SHARE_END = "screen_share_end"


class PresenceManager:
    """Manages user presence indicators."""

    def __init__(self):
        self.presence_data: Dict[str, CollaborationUser] = {}
        self.event_bus = get_event_bus()

    async def update_presence(
        self,
        user_id: str,
        status: str,
        conversation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Update user presence status."""
        try:
            if user_id not in self.presence_data:
                self.presence_data[user_id] = CollaborationUser(
                    user_id=user_id,
                    username=metadata.get("username", user_id) if metadata else user_id,
                    status=status,
                    metadata=metadata or {},
                )
            else:
                self.presence_data[user_id].status = status
                self.presence_data[user_id].last_seen = datetime.utcnow()
                if metadata:
                    self.presence_data[user_id].metadata.update(metadata)

            # Publish presence update event
            self.event_bus.publish_presence_update(
                user_id=user_id,
                status=status,
                conversation_id=conversation_id,
                metadata=metadata,
            )

            logger.debug(f"Updated presence for user {user_id}: {status}")

        except Exception as e:
            logger.error(f"Failed to update presence for user {user_id}: {e}")

    def get_presence(self, user_id: str) -> Optional[CollaborationUser]:
        """Get presence information for a user."""
        return self.presence_data.get(user_id)

    def get_online_users(
        self, conversation_id: Optional[str] = None
    ) -> List[CollaborationUser]:
        """Get list of online users."""
        online_users = []
        for user in self.presence_data.values():
            if user.status == "online":
                # If conversation_id is specified, we need to check if the user was updated with that conversation_id
                # Since we don't store conversation_id in the user object, we'll return all online users for now
                # In a real implementation, we'd need to track user-conversation relationships separately
                if conversation_id is None:
                    online_users.append(user)
                else:
                    # For now, include all online users when filtering by conversation
                    # This would need proper conversation tracking in a real implementation
                    online_users.append(user)
        return online_users

    async def cleanup_expired_presence(self, timeout_minutes: int = 5) -> None:
        """Clean up expired presence data."""
        try:
            cutoff_time = datetime.utcnow() - timedelta(minutes=timeout_minutes)
            expired_users = []

            for user_id, user in self.presence_data.items():
                if user.last_seen and user.last_seen < cutoff_time:
                    expired_users.append(user_id)

            for user_id in expired_users:
                await self.update_presence(user_id, "offline")

            logger.debug(f"Cleaned up {len(expired_users)} expired presence entries")

        except Exception as e:
            logger.error(f"Failed to cleanup expired presence: {e}")


class TypingManager:
    """Manages typing indicators."""

    def __init__(self):
        self.typing_data: Dict[
            str, Dict[str, Any]
        ] = {}  # conversation_id -> {user_id: typing_info}
        self.event_bus = get_event_bus()

    async def set_typing(
        self,
        user_id: str,
        conversation_id: str,
        is_typing: bool,
        expires_in_seconds: int = 5,
    ) -> None:
        """Set typing indicator for a user in a conversation."""
        try:
            if conversation_id not in self.typing_data:
                self.typing_data[conversation_id] = {}

            if is_typing:
                self.typing_data[conversation_id][user_id] = {
                    "started_at": datetime.utcnow(),
                    "expires_at": datetime.utcnow()
                    + timedelta(seconds=expires_in_seconds),
                }
            else:
                self.typing_data[conversation_id].pop(user_id, None)

            # Publish typing indicator event
            self.event_bus.publish_typing_indicator(
                user_id=user_id,
                conversation_id=conversation_id,
                is_typing=is_typing,
                expires_in_seconds=expires_in_seconds,
            )

            logger.debug(
                f"Set typing indicator for user {user_id} in conversation {conversation_id}: {is_typing}"
            )

        except Exception as e:
            logger.error(f"Failed to set typing indicator: {e}")

    def get_typing_users(self, conversation_id: str) -> List[str]:
        """Get list of users currently typing in a conversation."""
        if conversation_id not in self.typing_data:
            return []

        current_time = datetime.utcnow()
        typing_users = []

        for user_id, typing_info in self.typing_data[conversation_id].items():
            if typing_info["expires_at"] > current_time:
                typing_users.append(user_id)

        return typing_users

    async def cleanup_expired_typing(self) -> None:
        """Clean up expired typing indicators."""
        try:
            current_time = datetime.utcnow()

            for conversation_id in list(self.typing_data.keys()):
                expired_users = []

                for user_id, typing_info in self.typing_data[conversation_id].items():
                    if typing_info["expires_at"] <= current_time:
                        expired_users.append(user_id)

                for user_id in expired_users:
                    self.typing_data[conversation_id].pop(user_id, None)

                # Remove empty conversation entries
                if not self.typing_data[conversation_id]:
                    del self.typing_data[conversation_id]

            logger.debug("Cleaned up expired typing indicators")

        except Exception as e:
            logger.error(f"Failed to cleanup expired typing indicators: {e}")


class CollaborationManager:
    """Manages collaboration sessions and features."""

    def __init__(self):
        self.active_sessions: Dict[str, CollaborationSession] = {}
        self.user_sessions: Dict[str, Set[str]] = {}  # user_id -> set of session_ids
        self.event_bus = get_event_bus()

    async def create_session(
        self,
        conversation_id: str,
        initiator_user_id: str,
        session_type: str = "chat",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Create a new collaboration session."""
        try:
            session_id = str(uuid.uuid4())

            # Create initial participant
            initiator = CollaborationUser(
                user_id=initiator_user_id,
                username=metadata.get("initiator_username", initiator_user_id)
                if metadata
                else initiator_user_id,
                status="online",
            )

            session = CollaborationSession(
                session_id=session_id,
                conversation_id=conversation_id,
                participants=[initiator],
                session_type=session_type,
                metadata=metadata or {},
            )

            self.active_sessions[session_id] = session

            # Track user sessions
            if initiator_user_id not in self.user_sessions:
                self.user_sessions[initiator_user_id] = set()
            self.user_sessions[initiator_user_id].add(session_id)

            # Publish session start event
            self.event_bus.publish_collaboration_session(
                session_id=session_id,
                action="start",
                participants=[initiator_user_id],
                conversation_id=conversation_id,
                session_type=session_type,
                metadata=metadata,
            )

            logger.info(
                f"Created collaboration session {session_id} for conversation {conversation_id}"
            )
            return session_id

        except Exception as e:
            logger.error(f"Failed to create collaboration session: {e}")
            raise

    async def join_session(
        self, session_id: str, user_id: str, username: Optional[str] = None
    ) -> bool:
        """Add a user to an existing collaboration session."""
        try:
            if session_id not in self.active_sessions:
                logger.warning(f"Attempted to join non-existent session {session_id}")
                return False

            session = self.active_sessions[session_id]

            # Check if user is already in session
            for participant in session.participants:
                if participant.user_id == user_id:
                    participant.status = "online"
                    participant.last_seen = datetime.utcnow()
                    logger.debug(f"User {user_id} rejoined session {session_id}")
                    return True

            # Add new participant
            new_participant = CollaborationUser(
                user_id=user_id, username=username or user_id, status="online"
            )
            session.participants.append(new_participant)

            # Track user sessions
            if user_id not in self.user_sessions:
                self.user_sessions[user_id] = set()
            self.user_sessions[user_id].add(session_id)

            # Publish join event
            self.event_bus.publish(
                capsule="collaboration",
                event_type="user_joined_session",
                payload={
                    "session_id": session_id,
                    "user_id": user_id,
                    "conversation_id": session.conversation_id,
                    "timestamp": time.time(),
                },
                roles=["user", "admin"],
            )

            logger.info(f"User {user_id} joined collaboration session {session_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to join session {session_id}: {e}")
            return False

    async def leave_session(self, session_id: str, user_id: str) -> bool:
        """Remove a user from a collaboration session."""
        try:
            if session_id not in self.active_sessions:
                return False

            session = self.active_sessions[session_id]

            # Remove participant
            session.participants = [
                p for p in session.participants if p.user_id != user_id
            ]

            # Update user sessions tracking
            if user_id in self.user_sessions:
                self.user_sessions[user_id].discard(session_id)
                if not self.user_sessions[user_id]:
                    del self.user_sessions[user_id]

            # If no participants left, end the session
            if not session.participants:
                await self.end_session(session_id)
            else:
                # Publish leave event
                self.event_bus.publish(
                    capsule="collaboration",
                    event_type="user_left_session",
                    payload={
                        "session_id": session_id,
                        "user_id": user_id,
                        "conversation_id": session.conversation_id,
                        "timestamp": time.time(),
                    },
                    roles=["user", "admin"],
                )

            logger.info(f"User {user_id} left collaboration session {session_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to leave session {session_id}: {e}")
            return False

    async def end_session(self, session_id: str) -> bool:
        """End a collaboration session."""
        try:
            if session_id not in self.active_sessions:
                return False

            session = self.active_sessions[session_id]

            # Remove from user sessions tracking
            for participant in session.participants:
                if participant.user_id in self.user_sessions:
                    self.user_sessions[participant.user_id].discard(session_id)
                    if not self.user_sessions[participant.user_id]:
                        del self.user_sessions[participant.user_id]

            # Publish session end event
            self.event_bus.publish_collaboration_session(
                session_id=session_id,
                action="end",
                participants=[p.user_id for p in session.participants],
                conversation_id=session.conversation_id,
                session_type=session.session_type,
            )

            # Remove session
            del self.active_sessions[session_id]

            logger.info(f"Ended collaboration session {session_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to end session {session_id}: {e}")
            return False

    def get_session(self, session_id: str) -> Optional[CollaborationSession]:
        """Get collaboration session by ID."""
        return self.active_sessions.get(session_id)

    def get_user_sessions(self, user_id: str) -> List[CollaborationSession]:
        """Get all active sessions for a user."""
        if user_id not in self.user_sessions:
            return []

        sessions = []
        for session_id in self.user_sessions[user_id]:
            if session_id in self.active_sessions:
                sessions.append(self.active_sessions[session_id])

        return sessions

    def get_conversation_sessions(
        self, conversation_id: str
    ) -> List[CollaborationSession]:
        """Get all active sessions for a conversation."""
        return [
            session
            for session in self.active_sessions.values()
            if session.conversation_id == conversation_id
        ]


class WebSocketGateway:
    """Enhanced WebSocket gateway with collaboration features."""

    def __init__(
        self,
        chat_orchestrator=None,
        cleanup_interval: float = 30.0,
        heartbeat_interval: float = 30.0,
    ) -> None:
        self.cleanup_interval = cleanup_interval
        self.heartbeat_interval = heartbeat_interval
        self.chat_orchestrator = chat_orchestrator

        # Collaboration managers
        self.presence_manager = PresenceManager()
        self.typing_manager = TypingManager()
        self.collaboration_manager = CollaborationManager()

        # Connection tracking
        self.active_connections: Dict[
            str, Dict[str, Any]
        ] = {}  # connection_id -> connection_info
        self.user_connections: Dict[
            str, Set[str]
        ] = {}  # user_id -> set of connection_ids
        self.conversation_connections: Dict[
            str, Set[str]
        ] = {}  # conversation_id -> set of connection_ids

        # Background tasks
        self._typing_cleanup_task: Optional[asyncio.Task] = None
        self._presence_cleanup_task: Optional[asyncio.Task] = None
        self._message_cleanup_task: Optional[asyncio.Task] = None
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._collaboration_cleanup_task: Optional[asyncio.Task] = None
        self._tasks: List[asyncio.Task] = []

        # Message queue for offline users
        self.message_queue: Dict[str, List[Dict[str, Any]]] = {}

        # Event bus for collaboration events
        self.event_bus = get_event_bus()

    async def start(self) -> None:
        """Start background maintenance tasks."""
        self._typing_cleanup_task = asyncio.create_task(self._cleanup_expired_typing())
        self._presence_cleanup_task = asyncio.create_task(
            self._cleanup_expired_presence()
        )
        self._message_cleanup_task = asyncio.create_task(
            self._cleanup_expired_messages()
        )
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        self._collaboration_cleanup_task = asyncio.create_task(
            self._cleanup_collaboration_sessions()
        )
        self._tasks = [
            self._typing_cleanup_task,
            self._presence_cleanup_task,
            self._message_cleanup_task,
            self._heartbeat_task,
            self._collaboration_cleanup_task,
        ]

    async def _cleanup_collaboration_sessions(self) -> None:  # pragma: no cover - loop
        """Clean up inactive collaboration sessions."""
        try:
            while True:
                await asyncio.sleep(self.cleanup_interval * 2)  # Run less frequently

                current_time = datetime.utcnow()
                inactive_sessions = []

                for (
                    session_id,
                    session,
                ) in self.collaboration_manager.active_sessions.items():
                    # Check if session has been inactive for more than 30 minutes
                    if session.started_at and (
                        current_time - session.started_at
                    ) > timedelta(minutes=30):
                        # Check if any participants are still online
                        has_online_participants = False
                        for participant in session.participants:
                            presence = self.presence_manager.get_presence(
                                participant.user_id
                            )
                            if presence and presence.status == "online":
                                has_online_participants = True
                                break

                        if not has_online_participants:
                            inactive_sessions.append(session_id)

                # End inactive sessions
                for session_id in inactive_sessions:
                    await self.collaboration_manager.end_session(session_id)
                    logger.info(
                        f"Cleaned up inactive collaboration session: {session_id}"
                    )

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Failed to cleanup collaboration sessions: {e}")

    async def shutdown(self) -> None:
        """Cancel and await background tasks."""
        for task in self._tasks:
            task.cancel()
        for task in self._tasks:
            with contextlib.suppress(asyncio.CancelledError):
                await task
        # Reset references so any pending coroutines are not left dangling
        # which previously triggered 'coroutine was never awaited' warnings
        # during shutdown.
        self._typing_cleanup_task = None
        self._presence_cleanup_task = None
        self._message_cleanup_task = None
        self._heartbeat_task = None
        self._tasks.clear()

    async def _cleanup_expired_typing(self) -> None:  # pragma: no cover - loop
        try:
            while True:
                await asyncio.sleep(self.cleanup_interval)
                await self.typing_manager.cleanup_expired_typing()
        except asyncio.CancelledError:
            pass

    async def _cleanup_expired_presence(self) -> None:  # pragma: no cover - loop
        try:
            while True:
                await asyncio.sleep(self.cleanup_interval)
                await self.presence_manager.cleanup_expired_presence()
        except asyncio.CancelledError:
            pass

    async def _cleanup_expired_messages(self) -> None:  # pragma: no cover - loop
        try:
            while True:
                await asyncio.sleep(self.cleanup_interval)
                await self._cleanup_message_queue()
        except asyncio.CancelledError:
            pass

    async def _heartbeat_loop(self) -> None:  # pragma: no cover - loop
        try:
            while True:
                await asyncio.sleep(self.heartbeat_interval)
                await self._send_heartbeat_to_connections()
        except asyncio.CancelledError:
            pass

    async def _cleanup_message_queue(self) -> None:
        """Clean up expired messages from the message queue."""
        try:
            current_time = datetime.utcnow()
            for user_id in list(self.message_queue.keys()):
                # Remove messages older than 24 hours
                cutoff_time = current_time - timedelta(hours=24)
                self.message_queue[user_id] = [
                    msg
                    for msg in self.message_queue[user_id]
                    if datetime.fromisoformat(
                        msg.get("timestamp", current_time.isoformat())
                    )
                    > cutoff_time
                ]

                # Remove empty queues
                if not self.message_queue[user_id]:
                    del self.message_queue[user_id]

            logger.debug("Cleaned up expired messages from queue")

        except Exception as e:
            logger.error(f"Failed to cleanup message queue: {e}")

    async def _send_heartbeat_to_connections(self) -> None:
        """Send heartbeat to all active connections."""
        try:
            heartbeat_message = {
                "type": MessageType.PING,
                "timestamp": datetime.utcnow().isoformat(),
                "data": {"heartbeat": True},
            }

            # Send to all active connections
            for connection_id, connection_info in self.active_connections.items():
                try:
                    websocket = connection_info.get("websocket")
                    if websocket:
                        await websocket.send_text(json.dumps(heartbeat_message))
                except Exception as e:
                    logger.debug(
                        f"Failed to send heartbeat to connection {connection_id}: {e}"
                    )
                    # Mark connection for cleanup
                    connection_info["needs_cleanup"] = True

            # Clean up failed connections
            failed_connections = [
                conn_id
                for conn_id, conn_info in self.active_connections.items()
                if conn_info.get("needs_cleanup", False)
            ]

            for conn_id in failed_connections:
                await self._cleanup_connection(conn_id)

        except Exception as e:
            logger.error(f"Failed to send heartbeat: {e}")

    async def handle_websocket_connection(self, websocket) -> str:
        """Handle a new WebSocket connection with collaboration features."""
        connection_id = str(uuid.uuid4())

        try:
            # Accept the connection
            await websocket.accept()

            # Initialize connection info
            connection_info = {
                "connection_id": connection_id,
                "websocket": websocket,
                "connected_at": datetime.utcnow(),
                "user_id": None,
                "conversation_id": None,
                "authenticated": False,
                "last_activity": datetime.utcnow(),
            }

            self.active_connections[connection_id] = connection_info

            logger.info(f"WebSocket connection established: {connection_id}")

            # Handle messages
            while True:
                try:
                    # Receive message
                    data = await websocket.receive_text()
                    message_data = json.loads(data)

                    # Update last activity
                    connection_info["last_activity"] = datetime.utcnow()

                    # Process message
                    await self._process_websocket_message(connection_id, message_data)

                except Exception as e:
                    logger.error(f"Error processing WebSocket message: {e}")
                    await self._send_error_message(websocket, str(e))

        except Exception as e:
            logger.error(f"WebSocket connection error: {e}")
        finally:
            await self._cleanup_connection(connection_id)

        return connection_id

    async def _process_websocket_message(
        self, connection_id: str, message_data: Dict[str, Any]
    ) -> None:
        """Process incoming WebSocket message with collaboration features."""
        try:
            connection_info = self.active_connections.get(connection_id)
            if not connection_info:
                return

            message_type = message_data.get("type")

            # Handle different message types
            if message_type == "auth":
                await self._handle_auth_message(connection_id, message_data)

            elif message_type == "chat":
                await self._handle_chat_message(connection_id, message_data)

            elif message_type == MessageType.PRESENCE_UPDATE:
                await self._handle_presence_update(connection_id, message_data)

            elif message_type == MessageType.TYPING_INDICATOR:
                await self._handle_typing_indicator(connection_id, message_data)

            elif message_type == MessageType.COLLABORATION_INVITE:
                await self._handle_collaboration_invite(connection_id, message_data)

            elif message_type == MessageType.COLLABORATION_JOIN:
                await self._handle_collaboration_join(connection_id, message_data)

            elif message_type == MessageType.COLLABORATION_LEAVE:
                await self._handle_collaboration_leave(connection_id, message_data)

            elif message_type == MessageType.COLLABORATIVE_EDIT:
                await self._handle_collaborative_edit(connection_id, message_data)

            elif message_type == MessageType.PONG:
                # Handle pong response
                logger.debug(f"Received pong from connection {connection_id}")

            else:
                logger.warning(f"Unknown message type: {message_type}")

        except Exception as e:
            logger.error(f"Failed to process WebSocket message: {e}")

    async def _handle_auth_message(
        self, connection_id: str, message_data: Dict[str, Any]
    ) -> None:
        """Handle authentication message."""
        try:
            connection_info = self.active_connections.get(connection_id)
            if not connection_info:
                return

            user_id = message_data.get("user_id")
            conversation_id = message_data.get("conversation_id")

            if user_id:
                # Update connection info
                connection_info["user_id"] = user_id
                connection_info["conversation_id"] = conversation_id
                connection_info["authenticated"] = True

                # Track user connections
                if user_id not in self.user_connections:
                    self.user_connections[user_id] = set()
                self.user_connections[user_id].add(connection_id)

                # Track conversation connections
                if conversation_id:
                    if conversation_id not in self.conversation_connections:
                        self.conversation_connections[conversation_id] = set()
                    self.conversation_connections[conversation_id].add(connection_id)

                # Update presence
                await self.presence_manager.update_presence(
                    user_id=user_id,
                    status="online",
                    conversation_id=conversation_id,
                    metadata={"username": message_data.get("username", user_id)},
                )

                # Send authentication success
                await self._send_message(
                    connection_info["websocket"],
                    {
                        "type": "auth_success",
                        "user_id": user_id,
                        "connection_id": connection_id,
                    },
                )

                logger.info(
                    f"User {user_id} authenticated on connection {connection_id}"
                )

        except Exception as e:
            logger.error(f"Failed to handle auth message: {e}")

    async def _handle_presence_update(
        self, connection_id: str, message_data: Dict[str, Any]
    ) -> None:
        """Handle presence update message."""
        try:
            connection_info = self.active_connections.get(connection_id)
            if not connection_info or not connection_info.get("authenticated"):
                return

            user_id = connection_info["user_id"]
            status = message_data.get("status", "online")
            conversation_id = connection_info.get("conversation_id")

            await self.presence_manager.update_presence(
                user_id=user_id,
                status=status,
                conversation_id=conversation_id,
                metadata=message_data.get("metadata", {}),
            )

            # Broadcast presence update to conversation participants
            if conversation_id:
                await self._broadcast_to_conversation(
                    conversation_id,
                    {
                        "type": MessageType.PRESENCE_UPDATE,
                        "user_id": user_id,
                        "status": status,
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                    exclude_user=user_id,
                )

        except Exception as e:
            logger.error(f"Failed to handle presence update: {e}")

    async def _handle_typing_indicator(
        self, connection_id: str, message_data: Dict[str, Any]
    ) -> None:
        """Handle typing indicator message."""
        try:
            connection_info = self.active_connections.get(connection_id)
            if not connection_info or not connection_info.get("authenticated"):
                return

            user_id = connection_info["user_id"]
            conversation_id = connection_info.get("conversation_id")
            is_typing = message_data.get("is_typing", False)

            if conversation_id:
                await self.typing_manager.set_typing(
                    user_id=user_id,
                    conversation_id=conversation_id,
                    is_typing=is_typing,
                )

                # Broadcast typing indicator to conversation participants
                await self._broadcast_to_conversation(
                    conversation_id,
                    {
                        "type": MessageType.TYPING_INDICATOR,
                        "user_id": user_id,
                        "is_typing": is_typing,
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                    exclude_user=user_id,
                )

        except Exception as e:
            logger.error(f"Failed to handle typing indicator: {e}")

    async def _handle_collaboration_invite(
        self, connection_id: str, message_data: Dict[str, Any]
    ) -> None:
        """Handle collaboration session invite."""
        try:
            connection_info = self.active_connections.get(connection_id)
            if not connection_info or not connection_info.get("authenticated"):
                return

            user_id = connection_info["user_id"]
            conversation_id = connection_info.get("conversation_id")
            invited_users = message_data.get("invited_users", [])
            session_type = message_data.get("session_type", "chat")

            if conversation_id:
                # Create collaboration session
                session_id = await self.collaboration_manager.create_session(
                    conversation_id=conversation_id,
                    initiator_user_id=user_id,
                    session_type=session_type,
                    metadata={
                        "initiator_username": message_data.get("username", user_id),
                        "invited_users": invited_users,
                    },
                )

                # Send invites to invited users
                for invited_user_id in invited_users:
                    await self._send_to_user(
                        invited_user_id,
                        {
                            "type": MessageType.COLLABORATION_INVITE,
                            "session_id": session_id,
                            "initiator": user_id,
                            "conversation_id": conversation_id,
                            "session_type": session_type,
                            "timestamp": datetime.utcnow().isoformat(),
                        },
                    )

                # Confirm to initiator
                await self._send_message(
                    connection_info["websocket"],
                    {
                        "type": "collaboration_session_created",
                        "session_id": session_id,
                        "invited_users": invited_users,
                    },
                )

        except Exception as e:
            logger.error(f"Failed to handle collaboration invite: {e}")

    async def _handle_collaboration_join(
        self, connection_id: str, message_data: Dict[str, Any]
    ) -> None:
        """Handle joining a collaboration session."""
        try:
            connection_info = self.active_connections.get(connection_id)
            if not connection_info or not connection_info.get("authenticated"):
                return

            user_id = connection_info["user_id"]
            session_id = message_data.get("session_id")
            username = message_data.get("username", user_id)

            if session_id:
                success = await self.collaboration_manager.join_session(
                    session_id=session_id, user_id=user_id, username=username
                )

                if success:
                    session = self.collaboration_manager.get_session(session_id)
                    if session:
                        # Notify all session participants
                        for participant in session.participants:
                            await self._send_to_user(
                                participant.user_id,
                                {
                                    "type": "user_joined_collaboration",
                                    "session_id": session_id,
                                    "user_id": user_id,
                                    "username": username,
                                    "timestamp": datetime.utcnow().isoformat(),
                                },
                            )

                # Send join result
                await self._send_message(
                    connection_info["websocket"],
                    {
                        "type": "collaboration_join_result",
                        "session_id": session_id,
                        "success": success,
                    },
                )

        except Exception as e:
            logger.error(f"Failed to handle collaboration join: {e}")

    async def _handle_collaboration_leave(
        self, connection_id: str, message_data: Dict[str, Any]
    ) -> None:
        """Handle leaving a collaboration session."""
        try:
            connection_info = self.active_connections.get(connection_id)
            if not connection_info or not connection_info.get("authenticated"):
                return

            user_id = connection_info["user_id"]
            session_id = message_data.get("session_id")

            if session_id:
                success = await self.collaboration_manager.leave_session(
                    session_id=session_id, user_id=user_id
                )

                # Send leave result
                await self._send_message(
                    connection_info["websocket"],
                    {
                        "type": "collaboration_leave_result",
                        "session_id": session_id,
                        "success": success,
                    },
                )

        except Exception as e:
            logger.error(f"Failed to handle collaboration leave: {e}")

    async def _handle_collaborative_edit(
        self, connection_id: str, message_data: Dict[str, Any]
    ) -> None:
        """Handle collaborative editing message."""
        try:
            connection_info = self.active_connections.get(connection_id)
            if not connection_info or not connection_info.get("authenticated"):
                return

            user_id = connection_info["user_id"]
            session_id = message_data.get("session_id")
            edit_data = message_data.get("edit_data", {})

            if session_id:
                session = self.collaboration_manager.get_session(session_id)
                if session and any(p.user_id == user_id for p in session.participants):
                    # Broadcast edit to other session participants
                    for participant in session.participants:
                        if participant.user_id != user_id:
                            await self._send_to_user(
                                participant.user_id,
                                {
                                    "type": MessageType.COLLABORATIVE_EDIT,
                                    "session_id": session_id,
                                    "user_id": user_id,
                                    "edit_data": edit_data,
                                    "timestamp": datetime.utcnow().isoformat(),
                                },
                            )

        except Exception as e:
            logger.error(f"Failed to handle collaborative edit: {e}")

    async def _handle_chat_message(
        self, connection_id: str, message_data: Dict[str, Any]
    ) -> None:
        """Handle regular chat message."""
        try:
            connection_info = self.active_connections.get(connection_id)
            if not connection_info or not connection_info.get("authenticated"):
                return

            user_id = connection_info["user_id"]
            conversation_id = connection_info.get("conversation_id")
            message_content = message_data.get("message", "")

            if self.chat_orchestrator and message_content:
                logger.info(
                    f"Processing chat message from user {user_id}: {message_content[:50]}..."
                )

                chat_request = ChatRequest(
                    message=message_content,
                    user_id=user_id,
                    conversation_id=conversation_id or str(uuid.uuid4()),
                    session_id=connection_info.get("session_id"),
                    stream=False,
                    include_context=True,
                    metadata={},
                )

                response = await self.chat_orchestrator.process_message(chat_request)

                await self._send_message(
                    connection_info["websocket"],
                    {
                        "type": "chat_response",
                        "message": response.response,
                        "timestamp": datetime.utcnow().isoformat(),
                        "metadata": {
                            "correlation_id": response.correlation_id,
                            "processing_time": response.processing_time,
                            **response.metadata,
                        },
                    },
                )

        except Exception as e:
            logger.error(f"Failed to handle chat message: {e}")

    async def _send_message(self, websocket, message_data: Dict[str, Any]) -> None:
        """Send message to a WebSocket connection."""
        try:
            await websocket.send_text(json.dumps(message_data))
        except Exception as e:
            logger.error(f"Failed to send WebSocket message: {e}")

    async def _send_error_message(self, websocket, error_message: str) -> None:
        """Send error message to WebSocket connection."""
        try:
            await websocket.send_text(
                json.dumps(
                    {
                        "type": "error",
                        "message": error_message,
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                )
            )
        except Exception as e:
            logger.error(f"Failed to send error message: {e}")

    async def _send_to_user(self, user_id: str, message_data: Dict[str, Any]) -> None:
        """Send message to all connections of a specific user."""
        try:
            if user_id not in self.user_connections:
                # Queue message for offline user
                if user_id not in self.message_queue:
                    self.message_queue[user_id] = []

                self.message_queue[user_id].append(
                    {**message_data, "queued_at": datetime.utcnow().isoformat()}
                )
                return

            # Send to all user connections
            for connection_id in self.user_connections[user_id]:
                connection_info = self.active_connections.get(connection_id)
                if connection_info:
                    await self._send_message(connection_info["websocket"], message_data)

        except Exception as e:
            logger.error(f"Failed to send message to user {user_id}: {e}")

    async def _broadcast_to_conversation(
        self,
        conversation_id: str,
        message_data: Dict[str, Any],
        exclude_user: Optional[str] = None,
    ) -> None:
        """Broadcast message to all participants in a conversation."""
        try:
            if conversation_id not in self.conversation_connections:
                return

            for connection_id in self.conversation_connections[conversation_id]:
                connection_info = self.active_connections.get(connection_id)
                if connection_info and connection_info.get("user_id") != exclude_user:
                    await self._send_message(connection_info["websocket"], message_data)

        except Exception as e:
            logger.error(f"Failed to broadcast to conversation {conversation_id}: {e}")

    async def _cleanup_connection(self, connection_id: str) -> None:
        """Clean up a WebSocket connection."""
        try:
            connection_info = self.active_connections.get(connection_id)
            if not connection_info:
                return

            user_id = connection_info.get("user_id")
            conversation_id = connection_info.get("conversation_id")

            # Remove from tracking
            if user_id and user_id in self.user_connections:
                self.user_connections[user_id].discard(connection_id)
                if not self.user_connections[user_id]:
                    del self.user_connections[user_id]
                    # Update presence to offline
                    await self.presence_manager.update_presence(user_id, "offline")

            if conversation_id and conversation_id in self.conversation_connections:
                self.conversation_connections[conversation_id].discard(connection_id)
                if not self.conversation_connections[conversation_id]:
                    del self.conversation_connections[conversation_id]

            # Remove connection
            del self.active_connections[connection_id]

            logger.info(f"Cleaned up WebSocket connection: {connection_id}")

        except Exception as e:
            logger.error(f"Failed to cleanup connection {connection_id}: {e}")

    def get_connection_stats(self) -> Dict[str, Any]:
        """Get WebSocket connection statistics."""
        try:
            online_users = self.presence_manager.get_online_users()

            return {
                "total_connections": len(self.active_connections),
                "authenticated_connections": len(
                    [
                        c
                        for c in self.active_connections.values()
                        if c.get("authenticated", False)
                    ]
                ),
                "unique_users": len(self.user_connections),
                "active_conversations": len(self.conversation_connections),
                "typing_users": sum(
                    len(self.typing_manager.get_typing_users(conv_id))
                    for conv_id in self.conversation_connections.keys()
                ),
                "online_users": len(online_users),
                "queue_stats": {
                    "queued_users": len(self.message_queue),
                    "total_queued_messages": sum(
                        len(msgs) for msgs in self.message_queue.values()
                    ),
                },
            }
        except Exception as e:
            logger.error(f"Failed to get connection stats: {e}")
            return {}

    def get_user_connections(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all active connections for a user."""
        try:
            if user_id not in self.user_connections:
                return []

            connections = []
            for connection_id in self.user_connections[user_id]:
                connection_info = self.active_connections.get(connection_id)
                if connection_info:
                    connections.append(
                        {
                            "connection_id": connection_id,
                            "connected_at": connection_info["connected_at"].isoformat(),
                            "last_activity": connection_info[
                                "last_activity"
                            ].isoformat(),
                            "conversation_id": connection_info.get("conversation_id"),
                        }
                    )

            return connections
        except Exception as e:
            logger.error(f"Failed to get user connections: {e}")
            return []

    def get_conversation_connections(
        self, conversation_id: str
    ) -> List[Dict[str, Any]]:
        """Get all active connections for a conversation."""
        try:
            if conversation_id not in self.conversation_connections:
                return []

            connections = []
            for connection_id in self.conversation_connections[conversation_id]:
                connection_info = self.active_connections.get(connection_id)
                if connection_info:
                    connections.append(
                        {
                            "connection_id": connection_id,
                            "user_id": connection_info.get("user_id"),
                            "connected_at": connection_info["connected_at"].isoformat(),
                            "last_activity": connection_info[
                                "last_activity"
                            ].isoformat(),
                        }
                    )

            return connections
        except Exception as e:
            logger.error(f"Failed to get conversation connections: {e}")
            return []
