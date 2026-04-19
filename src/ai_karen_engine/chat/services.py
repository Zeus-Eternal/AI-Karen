"""
Chat service layer with business logic for AI-Karen chat system.
Integrates production service layer with canonical ChatOrchestrator architecture.
"""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_, desc
from sqlalchemy.orm import selectinload

from ai_karen_engine.chat.security import (
    ContentValidator,
    ValidationResult,
    SecurityLevel,
    get_content_validator,
    get_encryption_manager,
    validate_file_upload,
    sanitize_filename,
)
from ai_karen_engine.chat.chat_orchestrator import ChatOrchestrator
from ai_karen_engine.chat.dependencies import get_chat_orchestrator_dependency
from ai_karen_engine.chat.memory_processor import MemoryProcessor

logger = logging.getLogger(__name__)


class ChatService:
    """Main chat service that coordinates between production and canonical systems."""

    def __init__(self, db_session: Optional[AsyncSession] = None):
        self.db_session = db_session
        self.content_validator = get_content_validator(SecurityLevel.MEDIUM)
        self.encryption_manager = get_encryption_manager()
        self._orchestrator: Optional[ChatOrchestrator] = None

    async def initialize(self):
        """Initialize the chat service."""
        try:
            # Initialize orchestrator
            self._orchestrator = await get_chat_orchestrator_dependency()

            # Initialize providers if database session is available
            if self.db_session:
                await self._initialize_providers()

            logger.info("Chat service initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize chat service: {e}")
            raise

    async def _initialize_providers(self):
        """Initialize LLM providers from database."""
        # This would load provider configurations from database
        # For now, we'll use the orchestrator's default providers
        pass

    async def create_conversation(self, conversation_data: Dict[str, Any]) -> Any:
        """Create conversation - validation handled by caller/orchestrator."""
        try:
            # Delegate directly to orchestrator
            conversation = await self._orchestrator.create_conversation(
                conversation_data
            )
            return conversation

        except Exception as e:
            logger.error(f"Failed to create conversation: {e}")
            raise

    async def list_conversations(
        self, user_id: Optional[str] = None, limit: int = 20, offset: int = 0
    ) -> List[Any]:
        """List conversations for a user."""
        try:
            # Use orchestrator to list conversations
            conversations = await self._orchestrator.list_conversations(
                user_id=user_id, limit=limit, offset=offset
            )

            return conversations

        except Exception as e:
            logger.error(f"Failed to list conversations: {e}")
            raise

    async def get_conversation(self, conversation_id: str) -> Any:
        """Get a specific conversation."""
        try:
            conversation = await self._orchestrator.get_conversation(conversation_id)

            if not conversation:
                raise ValueError(f"Conversation {conversation_id} not found")

            return conversation

        except Exception as e:
            logger.error(f"Failed to get conversation: {e}")
            raise

    async def send_message(self, message_data: Dict[str, Any]) -> Any:
        """Send message - validation handled by caller/orchestrator."""
        try:
            # Delegate directly to orchestrator
            message = await self._orchestrator.send_message(message_data)
            return message

        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            raise

    async def get_messages(
        self, conversation_id: str, limit: int = 50, offset: int = 0
    ) -> List[Any]:
        """Get messages in a conversation."""
        try:
            messages = await self._orchestrator.get_messages(
                conversation_id=conversation_id, limit=limit, offset=offset
            )

            return messages

        except Exception as e:
            logger.error(f"Failed to get messages: {e}")
            raise

    async def upload_file(self, file_data: Dict[str, Any]) -> Any:
        """Upload file - validation handled by caller/orchestrator."""
        try:
            # Delegate directly to orchestrator
            uploaded_file = await self._orchestrator.upload_file(file_data)
            return uploaded_file

        except Exception as e:
            logger.error(f"Failed to upload file: {e}")
            raise

    async def stream_response(
        self, conversation_id: str, message: str, user_id: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """Stream conversation responses."""
        try:
            # Create message data
            message_data = {
                "conversation_id": conversation_id,
                "content": message,
                "role": "user",
                "user_id": user_id,
                "security_level": SecurityLevel.MEDIUM.value,
            }

            # Send message and get streaming response
            async for chunk in self._orchestrator.stream_response(
                conversation_id=conversation_id, message=message, user_id=user_id
            ):
                yield chunk

        except Exception as e:
            logger.error(f"Failed to stream response: {e}")
            yield f'{{"error": "{str(e)}"}}'

    async def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation."""
        try:
            success = await self._orchestrator.delete_conversation(conversation_id)
            return success

        except Exception as e:
            logger.error(f"Failed to delete conversation: {e}")
            raise


class SecureChatService(ChatService):
    """Enhanced chat service with additional security features."""

    def __init__(self, db_session: Optional[AsyncSession] = None):
        super().__init__(db_session)
        self._security_events: List[Dict[str, Any]] = []

    async def log_security_event(
        self,
        event_type: str,
        threat_level: str,
        user_id: Optional[str] = None,
        details: Dict[str, Any] = None,
    ):
        """Log a security event."""
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "threat_level": threat_level,
            "user_id": user_id,
            "details": details or {},
        }

        self._security_events.append(event)

        # Keep only last 1000 events
        if len(self._security_events) > 1000:
            self._security_events = self._security_events[-1000:]

        logger.warning(
            f"Security event: {event_type} - Threat: {threat_level} - User: {user_id}"
        )

    def get_security_events(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get security events."""
        return self._security_events[-limit:]

    async def create_secure_chat_service(db_session: AsyncSession) -> SecureChatService:
        """Factory method to create a secure chat service."""
        service = SecureChatService(db_session)
        await service.initialize()
        return service


# Factory functions for backward compatibility
def create_secure_chat_service(db_session: AsyncSession) -> SecureChatService:
    """Create a secure chat service instance."""
    return SecureChatService(db_session)


def get_chat_service() -> ChatService:
    """Get a basic chat service instance."""
    return ChatService()
