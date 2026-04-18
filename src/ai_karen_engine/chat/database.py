"""
Database operations module for AI-Karen chat system.
Integrates production database operations with canonical database architecture.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_, desc, func, text
from sqlalchemy.orm import selectinload, joinedload

from ai_karen_engine.database.client import MultiTenantPostgresClient
from ai_karen_engine.database.conversation_manager import ConversationManager
from ai_karen_engine.database.models import TenantConversation, TenantMessage

logger = logging.getLogger(__name__)


class DatabaseOperations:
    """Enhanced database operations for chat system with canonical integration."""

    def __init__(self, db_session: Optional[AsyncSession] = None):
        self.db_session = db_session
        self.multi_tenant_client = MultiTenantPostgresClient() if db_session else None
        self.conversation_manager = ConversationManager() if db_session else None

    async def get_conversation_with_messages(
        self,
        conversation_id: str,
        user_id: str,
        message_limit: int = 100,
        message_offset: int = 0,
        include_attachments: bool = True,
    ) -> Optional[Any]:
        """Get conversation with messages efficiently."""
        try:
            if self.conversation_manager:
                # Use canonical conversation manager
                conversation = await self.conversation_manager.get_conversation(
                    conversation_id=conversation_id, user_id=user_id
                )

                if conversation and hasattr(conversation, "messages"):
                    # Apply pagination to messages
                    messages = conversation.messages[
                        message_offset : message_offset + message_limit
                    ]
                    return {
                        "conversation": conversation,
                        "messages": messages,
                        "total_messages": len(conversation.messages),
                    }

            # Fallback to direct database query
            if self.db_session:
                from sqlalchemy import select
                from ai_karen_engine.database.models import ChatMemory

                query = (
                    select(ChatMemory)
                    .where(
                        and_(
                            ChatMemory.conversation_id == conversation_id,
                            ChatMemory.user_id == user_id,
                        )
                    )
                    .order_by(ChatMemory.created_at.desc())
                )

                result = await self.db_session.execute(query)
                memories = result.scalars().all()

                return {
                    "conversation": {"id": conversation_id, "user_id": user_id},
                    "messages": memories,
                    "total_messages": len(memories),
                }

            return None

        except Exception as e:
            logger.error(f"Failed to get conversation with messages: {e}")
            raise

    async def create_conversation(
        self,
        user_id: str,
        title: str,
        description: Optional[str] = None,
        security_level: str = "medium",
    ) -> Any:
        """Create a new conversation."""
        try:
            if self.conversation_manager:
                # Use canonical conversation manager
                conversation_data = {
                    "user_id": user_id,
                    "title": title,
                    "description": description,
                    "security_level": security_level,
                }

                conversation = await self.conversation_manager.create_conversation(
                    conversation_data
                )
                return conversation

            # Fallback to direct database operation
            if self.db_session:
                from ai_karen_engine.database.models import TenantConversation

                conversation = TenantConversation(
                    user_id=user_id,
                    title=title,
                    description=description,
                    security_level=security_level,
                    created_at=datetime.utcnow(),
                )

                self.db_session.add(conversation)
                await self.db_session.commit()
                await self.db_session.refresh(conversation)

                return conversation

            raise ValueError("No database session available")

        except Exception as e:
            logger.error(f"Failed to create conversation: {e}")
            raise

    async def update_conversation(
        self,
        conversation_id: str,
        user_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        security_level: Optional[str] = None,
    ) -> Optional[Any]:
        """Update an existing conversation."""
        try:
            if self.conversation_manager:
                # Use canonical conversation manager
                update_data = {}
                if title is not None:
                    update_data["title"] = title
                if description is not None:
                    update_data["description"] = description
                if security_level is not None:
                    update_data["security_level"] = security_level

                if update_data:
                    conversation = await self.conversation_manager.update_conversation(
                        conversation_id=conversation_id, user_id=user_id, **update_data
                    )
                    return conversation

            # Fallback to direct database operation
            if self.db_session:
                from ai_karen_engine.database.models import TenantConversation

                query = select(TenantConversation).where(
                    and_(
                        TenantConversation.id == conversation_id,
                        TenantConversation.user_id == user_id,
                    )
                )

                result = await self.db_session.execute(query)
                conversation = result.scalar_one_or_none()

                if conversation:
                    if title is not None:
                        conversation.title = title
                    if description is not None:
                        conversation.description = description
                    if security_level is not None:
                        conversation.security_level = security_level

                    conversation.updated_at = datetime.utcnow()

                    await self.db_session.commit()
                    await self.db_session.refresh(conversation)

                return conversation

            return None

        except Exception as e:
            logger.error(f"Failed to update conversation: {e}")
            raise

    async def delete_conversation(self, conversation_id: str, user_id: str) -> bool:
        """Delete a conversation."""
        try:
            if self.conversation_manager:
                # Use canonical conversation manager
                success = await self.conversation_manager.delete_conversation(
                    conversation_id=conversation_id, user_id=user_id
                )
                return success

            # Fallback to direct database operation
            if self.db_session:
                from ai_karen_engine.database.models import (
                    TenantConversation,
                    TenantMessage,
                )

                # Delete messages first
                await self.db_session.execute(
                    delete(TenantMessage).where(
                        and_(
                            TenantMessage.conversation_id == conversation_id,
                            TenantMessage.user_id == user_id,
                        )
                    )
                )

                # Delete conversation
                result = await self.db_session.execute(
                    delete(TenantConversation).where(
                        and_(
                            TenantConversation.id == conversation_id,
                            TenantConversation.user_id == user_id,
                        )
                    )
                )

                await self.db_session.commit()
                return result.rowcount > 0

            return False

        except Exception as e:
            logger.error(f"Failed to delete conversation: {e}")
            raise

    async def get_conversations_by_user(
        self, user_id: str, limit: int = 20, offset: int = 0, include_stats: bool = True
    ) -> List[Any]:
        """Get conversations for a user with optional statistics."""
        try:
            if self.conversation_manager:
                # Use canonical conversation manager
                conversations = (
                    await self.conversation_manager.get_conversations_by_user(
                        user_id=user_id, limit=limit, offset=offset
                    )
                )

                if include_stats:
                    for conv in conversations:
                        # Add message count
                        if hasattr(conv, "messages"):
                            conv.message_count = len(conv.messages)

                return conversations

            # Fallback to direct database operation
            if self.db_session:
                from ai_karen_engine.database.models import TenantConversation

                query = (
                    select(TenantConversation)
                    .where(TenantConversation.user_id == user_id)
                    .order_by(TenantConversation.updated_at.desc())
                )

                if limit > 0:
                    query = query.limit(limit)
                if offset > 0:
                    query = query.offset(offset)

                result = await self.db_session.execute(query)
                conversations = result.scalars().all()

                if include_stats:
                    # Get message counts for each conversation
                    for conv in conversations:
                        message_query = select(func.count(TenantMessage.id)).where(
                            TenantMessage.conversation_id == conv.id
                        )
                        message_result = await self.db_session.execute(message_query)
                        conv.message_count = message_result.scalar()

                return conversations

            return []

        except Exception as e:
            logger.error(f"Failed to get conversations by user: {e}")
            raise

    async def add_message(
        self,
        conversation_id: str,
        user_id: str,
        content: str,
        role: str = "user",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Add a message to a conversation."""
        try:
            if self.conversation_manager:
                # Use canonical conversation manager
                message_data = {
                    "conversation_id": conversation_id,
                    "user_id": user_id,
                    "content": content,
                    "role": role,
                    "metadata": metadata or {},
                }

                message = await self.conversation_manager.add_message(message_data)
                return message

            # Fallback to direct database operation
            if self.db_session:
                from ai_karen_engine.database.models import TenantMessage

                message = TenantMessage(
                    conversation_id=conversation_id,
                    user_id=user_id,
                    content=content,
                    role=role,
                    metadata=metadata or {},
                    created_at=datetime.utcnow(),
                )

                self.db_session.add(message)
                await self.db_session.commit()
                await self.db_session.refresh(message)

                return message

            raise ValueError("No database session available")

        except Exception as e:
            logger.error(f"Failed to add message: {e}")
            raise

    async def get_messages(
        self,
        conversation_id: str,
        user_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        order_by: str = "created_at",
    ) -> List[Any]:
        """Get messages for a conversation."""
        try:
            if self.conversation_manager:
                # Use canonical conversation manager
                messages = await self.conversation_manager.get_messages(
                    conversation_id=conversation_id,
                    user_id=user_id,
                    limit=limit,
                    offset=offset,
                    order_by=order_by,
                )
                return messages

            # Fallback to direct database operation
            if self.db_session:
                from ai_karen_engine.database.models import TenantMessage

                query = select(TenantMessage).where(
                    TenantMessage.conversation_id == conversation_id
                )

                if user_id:
                    query = query.where(TenantMessage.user_id == user_id)

                if order_by == "created_at":
                    query = query.order_by(TenantMessage.created_at.desc())
                elif order_by == "updated_at":
                    query = query.order_by(TenantMessage.updated_at.desc())

                if limit > 0:
                    query = query.limit(limit)
                if offset > 0:
                    query = query.offset(offset)

                result = await self.db_session.execute(query)
                messages = result.scalars().all()
                return messages

            return []

        except Exception as e:
            logger.error(f"Failed to get messages: {e}")
            raise

    async def get_conversation_stats(
        self, user_id: str, days: int = 30
    ) -> Dict[str, Any]:
        """Get conversation statistics for a user."""
        try:
            if self.conversation_manager:
                # Use canonical conversation manager
                stats = await self.conversation_manager.get_conversation_stats(
                    user_id=user_id, days=days
                )
                return stats

            # Fallback to direct database operation
            if self.db_session:
                from ai_karen_engine.database.models import (
                    TenantConversation,
                    TenantMessage,
                )
                from sqlalchemy import func

                cutoff_date = datetime.utcnow() - timedelta(days=days)

                # Get conversation count
                conv_query = select(func.count(TenantConversation.id)).where(
                    and_(
                        TenantConversation.user_id == user_id,
                        TenantConversation.created_at >= cutoff_date,
                    )
                )
                conv_result = await self.db_session.execute(conv_query)
                conversation_count = conv_result.scalar()

                # Get message count
                msg_query = select(func.count(TenantMessage.id)).where(
                    and_(
                        TenantMessage.user_id == user_id,
                        TenantMessage.created_at >= cutoff_date,
                    )
                )
                msg_result = await self.db_session.execute(msg_query)
                message_count = msg_result.scalar()

                # Get average messages per conversation
                avg_messages = (
                    message_count / conversation_count if conversation_count > 0 else 0
                )

                return {
                    "conversation_count": conversation_count,
                    "message_count": message_count,
                    "avg_messages_per_conversation": round(avg_messages, 2),
                    "days": days,
                }

            return {}

        except Exception as e:
            logger.error(f"Failed to get conversation stats: {e}")
            raise

    async def cleanup_old_data(
        self, days_to_keep: int = 90, batch_size: int = 100
    ) -> Dict[str, int]:
        """Clean up old conversation data."""
        try:
            if not self.db_session:
                return {"conversations_deleted": 0, "messages_deleted": 0}

            from ai_karen_engine.database.models import (
                TenantConversation,
                TenantMessage,
            )

            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)

            conversations_deleted = 0
            messages_deleted = 0

            # Delete old messages in batches
            while True:
                msg_query = (
                    select(TenantMessage.id)
                    .where(TenantMessage.created_at < cutoff_date)
                    .limit(batch_size)
                )

                result = await self.db_session.execute(msg_query)
                message_ids = [row[0] for row in result.fetchall()]

                if not message_ids:
                    break

                await self.db_session.execute(
                    delete(TenantMessage).where(TenantMessage.id.in_(message_ids))
                )

                messages_deleted += len(message_ids)
                await self.db_session.commit()

            # Delete old conversations
            conv_query = select(TenantConversation.id).where(
                TenantConversation.created_at < cutoff_date
            )

            result = await self.db_session.execute(conv_query)
            conversation_ids = [row[0] for row in result.fetchall()]

            if conversation_ids:
                await self.db_session.execute(
                    delete(TenantConversation).where(
                        TenantConversation.id.in_(conversation_ids)
                    )
                )

                conversations_deleted = len(conversation_ids)
                await self.db_session.commit()

            return {
                "conversations_deleted": conversations_deleted,
                "messages_deleted": messages_deleted,
            }

        except Exception as e:
            logger.error(f"Failed to cleanup old data: {e}")
            raise


# Factory functions
def create_database_operations(
    db_session: Optional[AsyncSession] = None,
) -> DatabaseOperations:
    """Create database operations instance."""
    return DatabaseOperations(db_session)


def get_database_operations() -> DatabaseOperations:
    """Get global database operations instance."""
    return DatabaseOperations()
