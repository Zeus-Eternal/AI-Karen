"""
Message service for managing chat messages with full CRUD operations,
search, threading, and advanced features.
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_, desc, func, text
from sqlalchemy.orm import selectinload, joinedload

from .models import (
    ChatConversation, ChatMessage, MessageAttachment
)
from .database import DatabaseOperations
from .security import log_security_event, ThreatLevel

logger = logging.getLogger(__name__)


class MessageService:
    """Service for managing chat messages with advanced features."""
    
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
        self.db_ops = DatabaseOperations(db_session)
    
    async def create_message(
        self,
        conversation_id: str,
        user_id: str,
        role: str,
        content: str,
        provider_id: Optional[str] = None,
        model_used: Optional[str] = None,
        token_count: Optional[int] = None,
        processing_time_ms: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
        parent_message_id: Optional[str] = None,
        is_streaming: bool = False,
        client_ip: Optional[str] = None
    ) -> ChatMessage:
        """Create a new message."""
        try:
            # Verify conversation ownership
            conv_result = await self.db_session.execute(
                select(ChatConversation).where(
                    and_(
                        ChatConversation.id == conversation_id,
                        ChatConversation.user_id == user_id
                    )
                )
            )
            conversation = conv_result.scalar_one_or_none()
            
            if not conversation:
                raise ValueError(f"Conversation {conversation_id} not found")
            
            # Create message
            message = ChatMessage(
                id=str(uuid.uuid4()),
                conversation_id=conversation_id,
                role=role,
                content=content,
                provider_id=provider_id,
                model_used=model_used,
                token_count=token_count,
                processing_time_ms=processing_time_ms,
                metadata=metadata or {},
                parent_message_id=parent_message_id,
                is_streaming=is_streaming,
                created_by_ip=client_ip
            )
            
            self.db_session.add(message)
            
            # Update conversation message count and timestamp
            await self.db_session.execute(
                update(ChatConversation)
                .where(ChatConversation.id == conversation_id)
                .values(
                    message_count=ChatConversation.message_count + 1,
                    updated_at=datetime.utcnow()
                )
            )
            
            await self.db_session.commit()
            await self.db_session.refresh(message)
            
            # Log message creation
            await log_security_event(
                "message_created",
                {
                    "message_id": message.id,
                    "conversation_id": conversation_id,
                    "user_id": user_id,
                    "role": role,
                    "provider_id": provider_id
                },
                user_id=user_id,
                ip_address=client_ip,
                threat_level=ThreatLevel.LOW
            )
            
            logger.info(f"Created message {message.id} in conversation {conversation_id}")
            return message
            
        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"Failed to create message: {e}")
            raise
    
    async def get_message(
        self,
        message_id: str,
        user_id: str,
        include_attachments: bool = True
    ) -> Optional[ChatMessage]:
        """Get a message by ID."""
        try:
            query = select(ChatMessage).join(ChatConversation).where(
                and_(
                    ChatMessage.id == message_id,
                    ChatConversation.user_id == user_id
                )
            )
            
            if include_attachments:
                query = query.options(
                    selectinload(ChatMessage.attachments)
                )
            
            result = await self.db_session.execute(query)
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"Failed to get message {message_id}: {e}")
            raise
    
    async def update_message(
        self,
        message_id: str,
        user_id: str,
        content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        is_streaming: Optional[bool] = None,
        streaming_completed_at: Optional[datetime] = None
    ) -> Optional[ChatMessage]:
        """Update a message."""
        try:
            # Verify message ownership
            message = await self.get_message(message_id, user_id)
            if not message:
                return None
            
            # Prepare update values
            update_values = {}
            
            if content is not None:
                update_values["content"] = content
            
            if metadata is not None:
                current_metadata = message.metadata or {}
                current_metadata.update(metadata)
                update_values["metadata"] = current_metadata
            
            if is_streaming is not None:
                update_values["is_streaming"] = is_streaming
                if not is_streaming and not streaming_completed_at:
                    update_values["streaming_completed_at"] = datetime.utcnow()
            
            if streaming_completed_at:
                update_values["streaming_completed_at"] = streaming_completed_at
            
            if update_values:
                await self.db_session.execute(
                    update(ChatMessage)
                    .where(ChatMessage.id == message_id)
                    .values(**update_values)
                )
                await self.db_session.commit()
                
                # Update conversation timestamp
                await self.db_session.execute(
                    update(ChatConversation)
                    .where(ChatConversation.id == message.conversation_id)
                    .values(updated_at=datetime.utcnow())
                )
                await self.db_session.commit()
            
            # Get updated message
            await self.db_session.refresh(message)
            
            # Log update
            await log_security_event(
                "message_updated",
                {
                    "message_id": message_id,
                    "user_id": user_id,
                    "updates": list(update_values.keys())
                },
                user_id=user_id,
                threat_level=ThreatLevel.LOW
            )
            
            return message
            
        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"Failed to update message {message_id}: {e}")
            raise
    
    async def delete_message(
        self,
        message_id: str,
        user_id: str,
        permanent: bool = False
    ) -> bool:
        """Delete or soft-delete a message."""
        try:
            message = await self.get_message(message_id, user_id)
            if not message:
                return False
            
            if permanent:
                # Permanent deletion
                await self.db_session.delete(message)
                action = "message_deleted_permanent"
            else:
                # Soft delete (mark as deleted in metadata)
                current_metadata = message.metadata or {}
                current_metadata["is_deleted"] = True
                current_metadata["deleted_at"] = datetime.utcnow().isoformat()
                
                await self.db_session.execute(
                    update(ChatMessage)
                    .where(ChatMessage.id == message_id)
                    .values(metadata=current_metadata)
                )
                action = "message_deleted_soft"
            
            # Update conversation message count
            await self.db_session.execute(
                update(ChatConversation)
                .where(ChatConversation.id == message.conversation_id)
                .values(
                    message_count=func.coalesce(
                        select(func.count(ChatMessage.id))
                        .where(
                            and_(
                                ChatMessage.conversation_id == message.conversation_id,
                                or_(
                                    ChatMessage.metadata.is_(None),
                                    ChatMessage.metadata['is_deleted'].is_(None)
                                )
                            )
                        ),
                        0
                    )
                )
            )
            
            await self.db_session.commit()
            
            # Log deletion
            await log_security_event(
                action,
                {
                    "message_id": message_id,
                    "conversation_id": message.conversation_id,
                    "user_id": user_id,
                    "permanent": permanent
                },
                user_id=user_id,
                threat_level=ThreatLevel.LOW
            )
            
            logger.info(f"{action.replace('_', ' ')} {message_id}")
            return True
            
        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"Failed to delete message {message_id}: {e}")
            raise
    
    async def get_conversation_messages(
        self,
        conversation_id: str,
        user_id: str,
        limit: int = 100,
        offset: int = 0,
        include_deleted: bool = False,
        include_attachments: bool = True
    ) -> Tuple[List[ChatMessage], int]:
        """Get messages for a conversation with pagination."""
        try:
            return await self.db_ops.get_messages_with_pagination(
                conversation_id, user_id, limit, offset, include_attachments
            )
            
        except Exception as e:
            logger.error(f"Failed to get conversation messages: {e}")
            raise
    
    async def search_messages(
        self,
        user_id: str,
        query_text: str,
        conversation_ids: Optional[List[str]] = None,
        limit: int = 100,
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[ChatMessage], int]:
        """Search messages with advanced filtering."""
        try:
            # Build base query
            base_query = select(ChatMessage).join(ChatConversation).where(
                and_(
                    ChatConversation.user_id == user_id,
                    ChatMessage.content.ilike(f"%{query_text}%")
                )
            )
            
            # Apply filters
            if conversation_ids:
                base_query = base_query.where(
                    ChatMessage.conversation_id.in_(conversation_ids)
                )
            
            if filters:
                if "role" in filters:
                    base_query = base_query.where(ChatMessage.role == filters["role"])
                
                if "provider_id" in filters:
                    base_query = base_query.where(ChatMessage.provider_id == filters["provider_id"])
                
                if "date_from" in filters:
                    base_query = base_query.where(ChatMessage.created_at >= filters["date_from"])
                
                if "date_to" in filters:
                    base_query = base_query.where(ChatMessage.created_at <= filters["date_to"])
                
                if "has_attachments" in filters:
                    if filters["has_attachments"]:
                        base_query = base_query.where(
                            ChatMessage.attachments.any()
                        )
                    else:
                        base_query = base_query.where(
                            ~ChatMessage.attachments.any()
                        )
                
                if "is_streaming" in filters:
                    base_query = base_query.where(
                        ChatMessage.is_streaming == filters["is_streaming"]
                    )
            
            # Get total count
            count_query = select(func.count()).select_from(base_query.subquery())
            total_result = await self.db_session.execute(count_query)
            total = total_result.scalar() or 0
            
            # Get results
            result = await self.db_session.execute(
                base_query.options(
                    selectinload(ChatMessage.attachments)
                )
                .order_by(desc(ChatMessage.created_at))
                .limit(limit).offset(offset)
            )
            messages = result.scalars().all()
            
            return list(messages), total
            
        except Exception as e:
            logger.error(f"Failed to search messages: {e}")
            raise
    
    async def get_message_thread(
        self,
        root_message_id: str,
        user_id: str
    ) -> List[ChatMessage]:
        """Get a complete message thread starting from root message."""
        try:
            # Verify root message ownership
            root_message = await self.get_message(root_message_id, user_id)
            if not root_message:
                return []
            
            # Get all messages in thread
            thread_messages = await self.db_ops.get_conversation_threads(
                root_message.conversation_id, user_id, root_message_id
            )
            
            return thread_messages
            
        except Exception as e:
            logger.error(f"Failed to get message thread: {e}")
            raise
    
    async def reply_to_message(
        self,
        parent_message_id: str,
        user_id: str,
        content: str,
        role: str = "user",
        metadata: Optional[Dict[str, Any]] = None
    ) -> ChatMessage:
        """Create a reply to an existing message."""
        try:
            # Get parent message
            parent_message = await self.get_message(parent_message_id, user_id)
            if not parent_message:
                raise ValueError(f"Parent message {parent_message_id} not found")
            
            # Create reply
            reply = await self.create_message(
                conversation_id=parent_message.conversation_id,
                user_id=user_id,
                role=role,
                content=content,
                parent_message_id=parent_message_id,
                metadata=metadata
            )
            
            # Update parent message metadata to track replies
            parent_metadata = parent_message.metadata or {}
            if "replies" not in parent_metadata:
                parent_metadata["replies"] = []
            parent_metadata["replies"].append({
                "message_id": reply.id,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            await self.db_session.execute(
                update(ChatMessage)
                .where(ChatMessage.id == parent_message_id)
                .values(metadata=parent_metadata)
            )
            await self.db_session.commit()
            
            return reply
            
        except Exception as e:
            logger.error(f"Failed to reply to message {parent_message_id}: {e}")
            raise
    
    async def forward_message(
        self,
        message_id: str,
        target_conversation_id: str,
        user_id: str,
        add_context: bool = True
    ) -> ChatMessage:
        """Forward a message to another conversation."""
        try:
            # Get original message
            original_message = await self.get_message(message_id, user_id)
            if not original_message:
                raise ValueError(f"Message {message_id} not found")
            
            # Verify target conversation ownership
            conv_result = await self.db_session.execute(
                select(ChatConversation).where(
                    and_(
                        ChatConversation.id == target_conversation_id,
                        ChatConversation.user_id == user_id
                    )
                )
            )
            target_conversation = conv_result.scalar_one_or_none()
            
            if not target_conversation:
                raise ValueError(f"Target conversation {target_conversation_id} not found")
            
            # Prepare forwarded content
            content = original_message.content
            if add_context:
                content = f"[Forwarded from conversation '{original_message.conversation_id}']\n\n{content}"
            
            # Create forwarded message
            forwarded_metadata = original_message.metadata.copy() if original_message.metadata else {}
            forwarded_metadata.update({
                "forwarded": True,
                "original_message_id": original_message.id,
                "original_conversation_id": original_message.conversation_id,
                "forwarded_at": datetime.utcnow().isoformat()
            })
            
            forwarded_message = await self.create_message(
                conversation_id=target_conversation_id,
                user_id=user_id,
                role=original_message.role,
                content=content,
                provider_id=original_message.provider_id,
                model_used=original_message.model_used,
                metadata=forwarded_metadata
            )
            
            # Update original message metadata
            original_metadata = original_message.metadata or {}
            if "forwards" not in original_metadata:
                original_metadata["forwards"] = []
            original_metadata["forwards"].append({
                "message_id": forwarded_message.id,
                "conversation_id": target_conversation_id,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            await self.db_session.execute(
                update(ChatMessage)
                .where(ChatMessage.id == message_id)
                .values(metadata=original_metadata)
            )
            await self.db_session.commit()
            
            return forwarded_message
            
        except Exception as e:
            logger.error(f"Failed to forward message {message_id}: {e}")
            raise
    
    async def mark_message_important(
        self,
        message_id: str,
        user_id: str,
        is_important: bool = True,
        note: Optional[str] = None
    ) -> ChatMessage:
        """Mark a message as important/unimportant."""
        try:
            message = await self.get_message(message_id, user_id)
            if not message:
                raise ValueError(f"Message {message_id} not found")
            
            # Update metadata
            metadata = message.metadata or {}
            if is_important:
                metadata["is_important"] = True
                metadata["important_at"] = datetime.utcnow().isoformat()
                if note:
                    metadata["important_note"] = note
            else:
                metadata["is_important"] = False
                metadata.pop("important_at", None)
                metadata.pop("important_note", None)
            
            await self.db_session.execute(
                update(ChatMessage)
                .where(ChatMessage.id == message_id)
                .values(metadata=metadata)
            )
            await self.db_session.commit()
            
            await self.db_session.refresh(message)
            
            # Log action
            await log_security_event(
                "message_importance_updated",
                {
                    "message_id": message_id,
                    "user_id": user_id,
                    "is_important": is_important
                },
                user_id=user_id,
                threat_level=ThreatLevel.LOW
            )
            
            return message
            
        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"Failed to mark message importance: {e}")
            raise
    
    async def add_message_reaction(
        self,
        message_id: str,
        user_id: str,
        reaction: str,
        remove: bool = False
    ) -> ChatMessage:
        """Add or remove a reaction from a message."""
        try:
            message = await self.get_message(message_id, user_id)
            if not message:
                raise ValueError(f"Message {message_id} not found")
            
            # Update reactions in metadata
            metadata = message.metadata or {}
            if "reactions" not in metadata:
                metadata["reactions"] = {}
            
            if remove:
                # Remove reaction
                if reaction in metadata["reactions"]:
                    if user_id in metadata["reactions"][reaction]:
                        metadata["reactions"][reaction].remove(user_id)
                    if not metadata["reactions"][reaction]:
                        del metadata["reactions"][reaction]
            else:
                # Add reaction
                if reaction not in metadata["reactions"]:
                    metadata["reactions"][reaction] = []
                if user_id not in metadata["reactions"][reaction]:
                    metadata["reactions"][reaction].append(user_id)
            
            await self.db_session.execute(
                update(ChatMessage)
                .where(ChatMessage.id == message_id)
                .values(metadata=metadata)
            )
            await self.db_session.commit()
            
            await self.db_session.refresh(message)
            return message
            
        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"Failed to add message reaction: {e}")
            raise
    
    async def get_message_analytics(
        self,
        user_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get message analytics for a user."""
        try:
            date_from = datetime.utcnow() - timedelta(days=days)
            
            # Message count by role
            role_stats = await self.db_session.execute(
                select(
                    ChatMessage.role,
                    func.count(ChatMessage.id).label('count'),
                    func.avg(ChatMessage.token_count).label('avg_tokens'),
                    func.sum(ChatMessage.processing_time_ms).label('total_time')
                )
                .join(ChatConversation)
                .where(and_(
                    ChatConversation.user_id == user_id,
                    ChatMessage.created_at >= date_from
                ))
                .group_by(ChatMessage.role)
            )
            role_results = role_stats.all()
            
            # Daily message volume
            daily_volume = await self.db_session.execute(
                select(
                    func.date(ChatMessage.created_at).label('date'),
                    func.count(ChatMessage.id).label('count'),
                    func.avg(ChatMessage.processing_time_ms).label('avg_time')
                )
                .join(ChatConversation)
                .where(and_(
                    ChatConversation.user_id == user_id,
                    ChatMessage.created_at >= date_from
                ))
                .group_by(func.date(ChatMessage.created_at))
                .order_by('date')
            )
            daily_results = daily_volume.all()
            
            # Provider performance
            provider_stats = await self.db_session.execute(
                select(
                    ChatMessage.provider_id,
                    func.count(ChatMessage.id).label('count'),
                    func.avg(ChatMessage.processing_time_ms).label('avg_time'),
                    func.avg(ChatMessage.token_count).label('avg_tokens')
                )
                .join(ChatConversation)
                .where(and_(
                    ChatConversation.user_id == user_id,
                    ChatMessage.created_at >= date_from,
                    ChatMessage.provider_id.isnot(None)
                ))
                .group_by(ChatMessage.provider_id)
                .order_by(desc('count'))
            )
            provider_results = provider_stats.all()
            
            # Attachment statistics
            attachment_stats = await self.db_session.execute(
                select(
                    func.count(MessageAttachment.id).label('total_attachments'),
                    func.count(func.distinct(MessageAttachment.message_id)).label('messages_with_attachments'),
                    func.avg(MessageAttachment.file_size).label('avg_file_size')
                )
                .join(ChatMessage)
                .join(ChatConversation)
                .where(and_(
                    ChatConversation.user_id == user_id,
                    MessageAttachment.created_at >= date_from
                ))
            )
            attachment_result = attachment_stats.first()
            
            return {
                "period_days": days,
                "message_stats": [
                    {
                        "role": result.role,
                        "count": result.count,
                        "average_tokens": float(result.avg_tokens or 0),
                        "total_processing_time_ms": int(result.total_time or 0)
                    }
                    for result in role_results
                ],
                "daily_volume": [
                    {
                        "date": result.date.isoformat(),
                        "message_count": result.count,
                        "average_processing_time_ms": float(result.avg_time or 0)
                    }
                    for result in daily_results
                ],
                "provider_performance": [
                    {
                        "provider_id": result.provider_id,
                        "message_count": result.count,
                        "average_processing_time_ms": float(result.avg_time or 0),
                        "average_tokens": float(result.avg_tokens or 0)
                    }
                    for result in provider_results
                ],
                "attachment_stats": {
                    "total_attachments": attachment_result.total_attachments or 0,
                    "messages_with_attachments": attachment_result.messages_with_attachments or 0,
                    "average_file_size": float(attachment_result.avg_file_size or 0)
                } if attachment_result else {
                    "total_attachments": 0,
                    "messages_with_attachments": 0,
                    "average_file_size": 0
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get message analytics: {e}")
            raise