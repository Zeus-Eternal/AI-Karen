"""
WebSocket support for real-time streaming in AI-Karen chat system.
Integrates production WebSocket functionality with canonical WebSocketGateway.
"""

import json
import logging
import asyncio
from typing import Dict, Any, Optional, List
from fastapi import (
    WebSocket,
    WebSocketDisconnect,
    Depends,
    Query,
    HTTPException,
    status,
)
from fastapi.websockets import WebSocketState
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from datetime import datetime

from ai_karen_engine.chat.websocket_gateway import (
    WebSocketGateway,
    WebSocketMessage,
    MessageType,
)
from ai_karen_engine.chat.dependencies import get_chat_orchestrator_dependency
from ai_karen_engine.chat.security import (
    validate_content,
    get_content_validator,
    SecurityLevel,
    ThreatLevel,
    ValidationResult,
)
from ai_karen_engine.chat.services import ChatService

logger = logging.getLogger(__name__)


class EnhancedWebSocketManager:
    """Enhanced WebSocket manager with security and monitoring features."""

    def __init__(self):
        self.active_connections: Dict[str, Dict[str, Any]] = {}
        self.user_sessions: Dict[str, str] = {}
        self.connection_security: Dict[str, Dict[str, Any]] = {}
        self.message_rate_limit: Dict[str, List[datetime]] = {}
        self.gateway: Optional[WebSocketGateway] = None

    async def initialize(self):
        """Initialize the WebSocket manager with gateway."""
        try:
            # Initialize canonical WebSocket gateway
            from ai_karen_engine.chat.factory import get_chat_service_factory

            factory = get_chat_service_factory()
            self.gateway = factory.get_service("websocket_gateway")

            if not self.gateway:
                self.gateway = factory.create_websocket_gateway()

            logger.info("WebSocket manager initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize WebSocket manager: {e}")
            raise

    async def connect(
        self,
        websocket: WebSocket,
        user_id: str,
        security_context: Dict[str, Any] = None,
    ):
        """Accept and store a WebSocket connection with security validation."""
        await websocket.accept()
        connection_id = f"{user_id}_{id(websocket)}"

        # Validate security context
        if security_context:
            security_result = self._validate_security_context(security_context)
            if not security_result.is_valid:
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Security validation failed: {', '.join(security_result.threats_detected)}",
                )

        # Store connection with security context
        self.active_connections[connection_id] = {
            "websocket": websocket,
            "user_id": user_id,
            "connected_at": datetime.utcnow(),
            "security_context": security_context or {},
            "message_count": 0,
            "last_message_time": None,
        }

        # Update user session mapping
        self.user_sessions[user_id] = connection_id

        # Initialize message rate tracking
        self.message_rate_limit[connection_id] = []

        # Log connection
        logger.info(f"WebSocket connection established: {connection_id}")

        # Send welcome message with compact payload
        welcome_message = {
            "t": "ce",  # type: connection_established (compressed)
            "d": {  # data: connection details
                "cid": connection_id,  # compressed: connection_id
                "uid": user_id,  # compressed: user_id
            },
        }

        await self.send_personal_message(welcome_message, connection_id)

        # Initialize canonical gateway if available
        if self.gateway:
            await self.gateway.handle_websocket_connect(websocket, user_id)

    async def disconnect(self, websocket: WebSocket, user_id: str):
        """Handle WebSocket disconnection."""
        connection_id = f"{user_id}_{id(websocket)}"

        if connection_id in self.active_connections:
            # Log disconnection
            logger.info(f"WebSocket connection closed: {connection_id}")

            # Clean up
            del self.active_connections[connection_id]
            if user_id in self.user_sessions:
                del self.user_sessions[user_id]
            if connection_id in self.message_rate_limit:
                del self.message_rate_limit[connection_id]

            # Notify canonical gateway
            if self.gateway:
                await self.gateway.handle_websocket_disconnect(websocket, user_id)

    async def send_personal_message(self, message: Dict[str, Any], connection_id: str):
        """Send a message to a specific connection."""
        if connection_id in self.active_connections:
            connection = self.active_connections[connection_id]
            websocket = connection["websocket"]

            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Failed to send message to {connection_id}: {e}")
                # Remove dead connection
                await self.disconnect(websocket, connection["user_id"])

    async def broadcast_to_conversation(
        self, message: Dict[str, Any], conversation_id: str
    ):
        """Broadcast a message to all users in a conversation."""
        if self.gateway:
            await self.gateway.broadcast_to_conversation(message, conversation_id)

    async def handle_message(self, websocket: WebSocket, user_id: str, data: str):
        """Handle incoming WebSocket messages with security validation."""
        connection_id = f"{user_id}_{id(websocket)}"

        if connection_id not in self.active_connections:
            logger.error(f"Message from unknown connection: {connection_id}")
            return

        connection = self.active_connections[connection_id]

        # Rate limiting
        if not self._check_rate_limit(connection_id):
            await self.send_personal_message(
                {
                    "t": "rle",  # type: rate_limit_exceeded (compressed)
                    "d": "Message rate limit exceeded",  # data: error message
                },
                connection_id,
            )
            return

        # Parse and validate message
        try:
            message_data = json.loads(data)
        except json.JSONDecodeError:
            await self.send_personal_message(
                {
                    "t": "e",  # type: error (compressed)
                    "d": "Invalid JSON format",  # data: error message
                },
                connection_id,
            )
            return

        # Validate message content
        validator = get_content_validator(SecurityLevel.MEDIUM)
        content_result = validator.validate_content(str(message_data), "json")

        if not content_result.is_valid:
            await self.send_personal_message(
                {
                    "t": "ve",  # type: validation_error (compressed)
                    "d": {  # data: validation details
                        "t": content_result.threats_detected,  # compressed: threats
                    },
                },
                connection_id,
            )
            return

        # Update connection stats
        connection["message_count"] += 1
        connection["last_message_time"] = datetime.utcnow()

        # Process message through canonical gateway if available
        if self.gateway:
            await self.gateway.handle_websocket_message(
                websocket, user_id, message_data
            )
        else:
            # Fallback processing
            await self._process_fallback_message(connection_id, message_data)

    async def _process_fallback_message(
        self, connection_id: str, message_data: Dict[str, Any]
    ):
        """Process message without canonical gateway."""
        message_type = message_data.get("type")

        if message_type == "chat_message":
            # Handle chat message
            await self._handle_chat_message(connection_id, message_data)
        elif message_type == "typing_indicator":
            # Handle typing indicator
            await self._handle_typing_indicator(connection_id, message_data)
        elif message_type == "ping":
            # Handle ping/pong with compact payload
            await self.send_personal_message(
                {"t": "p"},  # type: pong (compressed)
                connection_id,
            )
        else:
            logger.warning(f"Unknown message type: {message_type}")

    async def _handle_chat_message(
        self, connection_id: str, message_data: Dict[str, Any]
    ):
        """Handle chat message through chat service."""
        try:
            connection = self.active_connections[connection_id]
            orchestrator = await get_chat_orchestrator_dependency()

            # Prepare message data
            message_request = {
                "conversation_id": message_data.get("conversation_id"),
                "content": message_data.get("content"),
                "role": "user",
                "user_id": connection["user_id"],
                "security_level": SecurityLevel.MEDIUM.value,
            }

            # Send message and get streaming response with compact payload
            async for chunk in orchestrator.stream_response(
                conversation_id=message_request["conversation_id"],
                message=message_request["content"],
                user_id=message_request["user_id"],
            ):
                # Compact payload - only send delta
                await self.send_personal_message(
                    {
                        "t": "c",  # type: stream_chunk (compressed)
                        "d": chunk,  # data: content
                    },
                    connection_id,
                )

        except Exception as e:
            logger.error(f"Failed to handle chat message: {e}")
            await self.send_personal_message(
                {
                    "t": "e",  # type: error (compressed)
                    "d": f"Failed to process message: {str(e)}",  # data: error message
                },
                connection_id,
            )

    async def _handle_typing_indicator(
        self, connection_id: str, message_data: Dict[str, Any]
    ):
        """Handle typing indicator."""
        conversation_id = message_data.get("conversation_id")
        is_typing = message_data.get("is_typing", True)

        # Broadcast to conversation with compact payload
        await self.broadcast_to_conversation(
            {
                "t": "ti",  # type: typing_indicator (compressed)
                "d": {  # data: typing info
                    "uid": self.active_connections[connection_id][
                        "user_id"
                    ],  # compressed: user_id
                    "cid": conversation_id,  # compressed: conversation_id
                    "it": is_typing,  # compressed: is_typing
                },
            },
            conversation_id,
        )

    def _validate_security_context(
        self, security_context: Dict[str, Any]
    ) -> ValidationResult:
        """Validate security context for WebSocket connection."""
        validator = get_content_validator(SecurityLevel.HIGH)

        # Validate critical fields
        user_id = security_context.get("user_id")
        if user_id:
            user_result = validator.validate_content(str(user_id), "text")
            if not user_result.is_valid:
                return user_result

        # Validate conversation ID if present
        conversation_id = security_context.get("conversation_id")
        if conversation_id:
            conv_result = validator.validate_content(str(conversation_id), "text")
            if not conv_result.is_valid:
                return conv_result

        return ValidationResult(
            is_valid=True,
            threats_detected=[],
            security_level=SecurityLevel.HIGH,
            metadata={},
        )

    def _check_rate_limit(self, connection_id: str) -> bool:
        """Check if connection is within rate limits."""
        if connection_id not in self.message_rate_limit:
            return True

        messages = self.message_rate_limit[connection_id]
        now = datetime.utcnow()

        # Remove messages older than 1 minute
        messages = [msg for msg in messages if (now - msg).total_seconds() < 60]
        self.message_rate_limit[connection_id] = messages

        # Check if rate limit exceeded (max 10 messages per minute)
        if len(messages) >= 10:
            return False

        # Add current message
        messages.append(now)
        self.message_rate_limit[connection_id] = messages

        return True


# Global WebSocket manager instance
websocket_manager = EnhancedWebSocketManager()


async def get_websocket_manager() -> EnhancedWebSocketManager:
    """Get the WebSocket manager instance."""
    if not websocket_manager.gateway:
        await websocket_manager.initialize()
    return websocket_manager


# WebSocket endpoint functions
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: str,
    token: str = Query(...),
    security_context: str = Query("{}"),
):
    """WebSocket endpoint for chat streaming."""
    try:
        # Parse security context
        import json

        security_data = json.loads(security_context)

        # Initialize manager
        manager = await get_websocket_manager()

        # Connect with security validation
        await manager.connect(websocket, user_id, security_data)

        try:
            # Handle messages
            while True:
                data = await websocket.receive_text()
                await manager.handle_message(websocket, user_id, data)

        except WebSocketDisconnect:
            await manager.disconnect(websocket, user_id)

    except Exception as e:
        logger.error(f"WebSocket endpoint error: {e}")
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)


async def conversation_websocket(
    websocket: WebSocket, conversation_id: str, user_id: str, token: str = Query(...)
):
    """WebSocket endpoint for specific conversation."""
    try:
        # Initialize manager
        manager = await get_websocket_manager()

        # Connect with conversation context
        security_context = {"conversation_id": conversation_id, "user_id": user_id}
        await manager.connect(websocket, user_id, security_context)

        try:
            # Handle messages
            while True:
                data = await websocket.receive_text()
                await manager.handle_message(websocket, user_id, data)

        except WebSocketDisconnect:
            await manager.disconnect(websocket, user_id)

    except Exception as e:
        logger.error(f"Conversation WebSocket error: {e}")
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
