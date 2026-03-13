"""
Conversation service for managing chat conversations with full CRUD operations,
search, filtering, and analytics capabilities.
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_, desc, func, text
from sqlalchemy.orm import selectinload, joinedload

from .models import (
    ChatConversation, ChatMessage, ChatSession, MessageAttachment,
    ChatProviderConfiguration
)
from .database import DatabaseOperations
from .security import log_security_event, ThreatLevel

logger = logging.getLogger(__name__)


class ConversationService:
    """Service for managing chat conversations with advanced features."""
    
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
        self.db_ops = DatabaseOperations(db_session)
    
    async def create_conversation(
        self,
        user_id: str,
        title: Optional[str] = None,
        provider_id: Optional[str] = None,
        model_used: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        is_pinned: bool = False,
        client_ip: Optional[str] = None
    ) -> ChatConversation:
        """Create a new conversation with enhanced features."""
        try:
            conversation_id = str(uuid.uuid4())
            
            # Create conversation
            conversation = ChatConversation(
                id=conversation_id,
                user_id=user_id,
                title=title or "New Conversation",
                provider_id=provider_id,
                model_used=model_used,
                metadata=metadata or {},
                is_archived=False,
                created_by_ip=client_ip,
                last_modified_by=user_id
            )
            
            # Add tags if provided
            if tags:
                conversation.metadata["tags"] = tags
            
            # Set pin status
            if is_pinned:
                conversation.metadata["is_pinned"] = True
                conversation.metadata["pinned_at"] = datetime.utcnow().isoformat()
            
            self.db_session.add(conversation)
            await self.db_session.commit()
            await self.db_session.refresh(conversation)
            
            # Log creation
            await log_security_event(
                "conversation_created",
                {
                    "conversation_id": conversation_id,
                    "user_id": user_id,
                    "title": title,
                    "provider_id": provider_id,
                    "tags": tags
                },
                user_id=user_id,
                ip_address=client_ip,
                threat_level=ThreatLevel.LOW
            )
            
            logger.info(f"Created conversation {conversation_id} for user {user_id}")
            return conversation
            
        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"Failed to create conversation: {e}")
            raise
    
    async def get_conversation(
        self,
        conversation_id: str,
        user_id: str,
        include_messages: bool = False,
        message_limit: int = 50
    ) -> Optional[ChatConversation]:
        """Get a conversation by ID with optional message inclusion."""
        try:
            query = select(ChatConversation).where(
                and_(
                    ChatConversation.id == conversation_id,
                    ChatConversation.user_id == user_id
                )
            )
            
            if include_messages:
                query = query.options(
                    selectinload(ChatConversation.messages).limit(message_limit)
                )
            
            result = await self.db_session.execute(query)
            conversation = result.scalar_one_or_none()
            
            if conversation:
                # Update access tracking
                await self.db_session.execute(
                    update(ChatConversation)
                    .where(ChatConversation.id == conversation_id)
                    .values(
                        access_count=ChatConversation.access_count + 1,
                        last_accessed_at=datetime.utcnow()
                    )
                )
                await self.db_session.commit()
            
            return conversation
            
        except Exception as e:
            logger.error(f"Failed to get conversation {conversation_id}: {e}")
            raise
    
    async def update_conversation(
        self,
        conversation_id: str,
        user_id: str,
        title: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        is_pinned: Optional[bool] = None,
        is_archived: Optional[bool] = None
    ) -> Optional[ChatConversation]:
        """Update conversation properties."""
        try:
            # Verify ownership
            conversation = await self.get_conversation(conversation_id, user_id)
            if not conversation:
                return None
            
            # Prepare update values
            update_values = {"last_modified_by": user_id}
            
            if title is not None:
                update_values["title"] = title
            
            if is_archived is not None:
                update_values["is_archived"] = is_archived
                if is_archived:
                    update_values["archived_at"] = datetime.utcnow()
            
            # Update metadata
            if metadata is not None or tags is not None or is_pinned is not None:
                current_metadata = conversation.metadata or {}
                
                if metadata:
                    current_metadata.update(metadata)
                
                if tags is not None:
                    current_metadata["tags"] = tags
                
                if is_pinned is not None:
                    if is_pinned:
                        current_metadata["is_pinned"] = True
                        current_metadata["pinned_at"] = datetime.utcnow().isoformat()
                    else:
                        current_metadata["is_pinned"] = False
                        current_metadata.pop("pinned_at", None)
                
                update_values["metadata"] = current_metadata
            
            # Apply updates
            if update_values:
                await self.db_session.execute(
                    update(ChatConversation)
                    .where(ChatConversation.id == conversation_id)
                    .values(**update_values)
                )
                await self.db_session.commit()
            
            # Get updated conversation
            await self.db_session.refresh(conversation)
            
            # Log update
            await log_security_event(
                "conversation_updated",
                {
                    "conversation_id": conversation_id,
                    "user_id": user_id,
                    "updates": list(update_values.keys())
                },
                user_id=user_id,
                threat_level=ThreatLevel.LOW
            )
            
            return conversation
            
        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"Failed to update conversation {conversation_id}: {e}")
            raise
    
    async def delete_conversation(
        self,
        conversation_id: str,
        user_id: str,
        permanent: bool = False
    ) -> bool:
        """Delete or archive a conversation."""
        try:
            conversation = await self.get_conversation(conversation_id, user_id)
            if not conversation:
                return False
            
            if permanent:
                # Permanent deletion
                await self.db_session.delete(conversation)
                action = "conversation_deleted_permanent"
            else:
                # Soft delete (archive)
                await self.db_session.execute(
                    update(ChatConversation)
                    .where(ChatConversation.id == conversation_id)
                    .values(
                        is_archived=True,
                        archived_at=datetime.utcnow()
                    )
                )
                action = "conversation_archived"
            
            await self.db_session.commit()
            
            # Log action
            await log_security_event(
                action,
                {
                    "conversation_id": conversation_id,
                    "user_id": user_id,
                    "permanent": permanent
                },
                user_id=user_id,
                threat_level=ThreatLevel.LOW
            )
            
            logger.info(f"{action.replace('_', ' ')} {conversation_id} for user {user_id}")
            return True
            
        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"Failed to delete conversation {conversation_id}: {e}")
            raise
    
    async def list_conversations(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
        include_archived: bool = False,
        sort_by: str = "updated_at",
        sort_order: str = "desc",
        filters: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[ChatConversation], int]:
        """List conversations with filtering and sorting."""
        try:
            # Build base query
            query = select(ChatConversation).where(ChatConversation.user_id == user_id)
            
            # Apply filters
            if not include_archived:
                query = query.where(ChatConversation.is_archived == False)
            
            if filters:
                if "provider_id" in filters:
                    query = query.where(ChatConversation.provider_id == filters["provider_id"])
                
                if "tags" in filters and filters["tags"]:
                    # Filter by tags in metadata
                    tag_conditions = []
                    for tag in filters["tags"]:
                        tag_conditions.append(
                            func.jsonb_extract_path_text(ChatConversation.metadata, 'tags').like(f'%{tag}%')
                        )
                    if tag_conditions:
                        query = query.where(or_(*tag_conditions))
                
                if "date_from" in filters:
                    query = query.where(ChatConversation.created_at >= filters["date_from"])
                
                if "date_to" in filters:
                    query = query.where(ChatConversation.created_at <= filters["date_to"])
                
                if "is_pinned" in filters:
                    if filters["is_pinned"]:
                        query = query.where(
                            func.jsonb_extract_path_text(ChatConversation.metadata, 'is_pinned') == 'true'
                        )
                    else:
                        query = query.where(
                            or_(
                                func.jsonb_extract_path_text(ChatConversation.metadata, 'is_pinned') != 'true',
                                func.jsonb_extract_path_text(ChatConversation.metadata, 'is_pinned').is_(None)
                            )
                        )
            
            # Get total count
            count_query = select(func.count()).select_from(query.subquery())
            total_result = await self.db_session.execute(count_query)
            total = total_result.scalar()
            
            # Apply sorting
            if sort_by == "updated_at":
                order_column = ChatConversation.updated_at
            elif sort_by == "created_at":
                order_column = ChatConversation.created_at
            elif sort_by == "title":
                order_column = ChatConversation.title
            elif sort_by == "message_count":
                order_column = ChatConversation.message_count
            else:
                order_column = ChatConversation.updated_at
            
            if sort_order.lower() == "desc":
                query = query.order_by(desc(order_column))
            else:
                query = query.order_by(order_column)
            
            # Apply pagination
            query = query.limit(limit).offset(offset)
            
            # Execute query
            result = await self.db_session.execute(query)
            conversations = result.scalars().all()
            
            return list(conversations), total
            
        except Exception as e:
            logger.error(f"Failed to list conversations for user {user_id}: {e}")
            raise
    
    async def search_conversations(
        self,
        user_id: str,
        query_text: str,
        limit: int = 50,
        offset: int = 0,
        search_in: List[str] = None
    ) -> Tuple[List[ChatConversation], int]:
        """Search conversations by text content."""
        try:
            if search_in is None:
                search_in = ["title", "metadata"]
            
            # Build search conditions
            search_conditions = []
            
            if "title" in search_in:
                search_conditions.append(ChatConversation.title.ilike(f"%{query_text}%"))
            
            if "metadata" in search_in:
                search_conditions.append(
                    func.cast(ChatConversation.metadata, func.TEXT).ilike(f"%{query_text}%")
                )
            
            if not search_conditions:
                return [], 0
            
            # Build query
            base_query = select(ChatConversation).where(
                and_(
                    ChatConversation.user_id == user_id,
                    ChatConversation.is_archived == False,
                    or_(*search_conditions)
                )
            )
            
            # Get total count
            count_query = select(func.count()).select_from(base_query.subquery())
            total_result = await self.db_session.execute(count_query)
            total = total_result.scalar()
            
            # Get results
            result = await self.db_session.execute(
                base_query.order_by(desc(ChatConversation.updated_at))
                .limit(limit).offset(offset)
            )
            conversations = result.scalars().all()
            
            return list(conversations), total
            
        except Exception as e:
            logger.error(f"Failed to search conversations for user {user_id}: {e}")
            raise
    
    async def get_conversation_statistics(
        self,
        user_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get conversation statistics for a user."""
        try:
            date_from = datetime.utcnow() - timedelta(days=days)
            
            # Total conversations
            total_result = await self.db_session.execute(
                select(func.count(ChatConversation.id))
                .where(and_(
                    ChatConversation.user_id == user_id,
                    ChatConversation.created_at >= date_from
                ))
            )
            total_conversations = total_result.scalar()
            
            # Active conversations (with messages in last 7 days)
            active_date = datetime.utcnow() - timedelta(days=7)
            active_result = await self.db_session.execute(
                select(func.count(func.distinct(ChatMessage.conversation_id)))
                .join(ChatMessage)
                .where(and_(
                    ChatConversation.user_id == user_id,
                    ChatMessage.created_at >= active_date
                ))
            )
            active_conversations = active_result.scalar()
            
            # Archived conversations
            archived_result = await self.db_session.execute(
                select(func.count(ChatConversation.id))
                .where(and_(
                    ChatConversation.user_id == user_id,
                    ChatConversation.is_archived == True
                ))
            )
            archived_conversations = archived_result.scalar()
            
            # Provider usage
            provider_result = await self.db_session.execute(
                select(
                    ChatConversation.provider_id,
                    func.count(ChatConversation.id).label('count')
                )
                .where(and_(
                    ChatConversation.user_id == user_id,
                    ChatConversation.created_at >= date_from
                ))
                .group_by(ChatConversation.provider_id)
                .order_by(desc('count'))
            )
            provider_usage = dict(provider_result.all())
            
            # Average messages per conversation
            avg_messages_result = await self.db_session.execute(
                select(func.avg(ChatConversation.message_count))
                .where(and_(
                    ChatConversation.user_id == user_id,
                    ChatConversation.created_at >= date_from
                ))
            )
            avg_messages = avg_messages_result.scalar() or 0
            
            return {
                "total_conversations": total_conversations,
                "active_conversations": active_conversations,
                "archived_conversations": archived_conversations,
                "provider_usage": provider_usage,
                "average_messages_per_conversation": float(avg_messages),
                "period_days": days
            }
            
        except Exception as e:
            logger.error(f"Failed to get conversation statistics for user {user_id}: {e}")
            raise
    
    async def export_conversations(
        self,
        user_id: str,
        conversation_ids: Optional[List[str]] = None,
        format: str = "json",
        include_messages: bool = True,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Export conversations in specified format."""
        try:
            # Build query
            query = select(ChatConversation).where(ChatConversation.user_id == user_id)
            
            if conversation_ids:
                query = query.where(ChatConversation.id.in_(conversation_ids))
            
            if date_from:
                query = query.where(ChatConversation.created_at >= date_from)
            
            if date_to:
                query = query.where(ChatConversation.created_at <= date_to)
            
            # Include messages if requested
            if include_messages:
                query = query.options(
                    selectinload(ChatConversation.messages)
                    .joinedload(ChatMessage.attachments)
                )
            
            result = await self.db_session.execute(query)
            conversations = result.scalars().all()
            
            # Format export data
            export_data = {
                "export_info": {
                    "user_id": user_id,
                    "exported_at": datetime.utcnow().isoformat(),
                    "format": format,
                    "include_messages": include_messages,
                    "conversation_count": len(conversations)
                },
                "conversations": []
            }
            
            for conv in conversations:
                conv_data = {
                    "id": str(conv.id),
                    "title": conv.title,
                    "created_at": conv.created_at.isoformat(),
                    "updated_at": conv.updated_at.isoformat(),
                    "provider_id": conv.provider_id,
                    "model_used": conv.model_used,
                    "message_count": conv.message_count,
                    "metadata": conv.metadata,
                    "is_archived": conv.is_archived
                }
                
                if include_messages:
                    conv_data["messages"] = []
                    for msg in conv.messages:
                        msg_data = {
                            "id": str(msg.id),
                            "role": msg.role,
                            "content": msg.content,
                            "created_at": msg.created_at.isoformat(),
                            "updated_at": msg.updated_at.isoformat(),
                            "provider_id": msg.provider_id,
                            "model_used": msg.model_used,
                            "token_count": msg.token_count,
                            "processing_time_ms": msg.processing_time_ms,
                            "metadata": msg.metadata,
                            "parent_message_id": str(msg.parent_message_id) if msg.parent_message_id else None
                        }
                        
                        if msg.attachments:
                            msg_data["attachments"] = [
                                {
                                    "id": str(att.id),
                                    "filename": att.filename,
                                    "file_path": att.file_path,
                                    "mime_type": att.mime_type,
                                    "file_size": att.file_size,
                                    "created_at": att.created_at.isoformat(),
                                    "metadata": att.metadata
                                }
                                for att in msg.attachments
                            ]
                        
                        conv_data["messages"].append(msg_data)
                
                export_data["conversations"].append(conv_data)
            
            return export_data
            
        except Exception as e:
            logger.error(f"Failed to export conversations for user {user_id}: {e}")
            raise
    
    async def import_conversations(
        self,
        user_id: str,
        import_data: Dict[str, Any],
        merge_strategy: str = "skip_duplicates"
    ) -> Dict[str, Any]:
        """Import conversations from exported data."""
        try:
            conversations = import_data.get("conversations", [])
            imported_count = 0
            skipped_count = 0
            error_count = 0
            errors = []
            
            for conv_data in conversations:
                try:
                    # Check for existing conversation
                    existing_result = await self.db_session.execute(
                        select(ChatConversation).where(
                            and_(
                                ChatConversation.user_id == user_id,
                                ChatConversation.title == conv_data["title"],
                                ChatConversation.created_at == datetime.fromisoformat(conv_data["created_at"].replace('Z', '+00:00'))
                            )
                        )
                    )
                    existing = existing_result.scalar_one_or_none()
                    
                    if existing and merge_strategy == "skip_duplicates":
                        skipped_count += 1
                        continue
                    
                    # Create new conversation
                    conversation = ChatConversation(
                        id=str(uuid.uuid4()),
                        user_id=user_id,
                        title=conv_data["title"],
                        provider_id=conv_data.get("provider_id"),
                        model_used=conv_data.get("model_used"),
                        metadata=conv_data.get("metadata", {}),
                        is_archived=conv_data.get("is_archived", False),
                        created_at=datetime.fromisoformat(conv_data["created_at"].replace('Z', '+00:00')),
                        updated_at=datetime.fromisoformat(conv_data["updated_at"].replace('Z', '+00:00'))
                    )
                    
                    self.db_session.add(conversation)
                    await self.db_session.flush()  # Get the ID
                    
                    # Import messages if present
                    if "messages" in conv_data:
                        for msg_data in conv_data["messages"]:
                            message = ChatMessage(
                                id=str(uuid.uuid4()),
                                conversation_id=conversation.id,
                                role=msg_data["role"],
                                content=msg_data["content"],
                                provider_id=msg_data.get("provider_id"),
                                model_used=msg_data.get("model_used"),
                                token_count=msg_data.get("token_count"),
                                processing_time_ms=msg_data.get("processing_time_ms"),
                                metadata=msg_data.get("metadata", {}),
                                parent_message_id=msg_data.get("parent_message_id"),
                                created_at=datetime.fromisoformat(msg_data["created_at"].replace('Z', '+00:00')),
                                updated_at=datetime.fromisoformat(msg_data["updated_at"].replace('Z', '+00:00'))
                            )
                            
                            self.db_session.add(message)
                    
                    imported_count += 1
                    
                except Exception as e:
                    error_count += 1
                    errors.append(f"Failed to import conversation '{conv_data.get('title', 'Unknown')}': {str(e)}")
                    logger.error(f"Failed to import conversation: {e}")
            
            await self.db_session.commit()
            
            # Log import
            await log_security_event(
                "conversations_imported",
                {
                    "user_id": user_id,
                    "imported_count": imported_count,
                    "skipped_count": skipped_count,
                    "error_count": error_count
                },
                user_id=user_id,
                threat_level=ThreatLevel.LOW
            )
            
            return {
                "imported_count": imported_count,
                "skipped_count": skipped_count,
                "error_count": error_count,
                "errors": errors
            }
            
        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"Failed to import conversations for user {user_id}: {e}")
            raise
    
    async def bulk_update_conversations(
        self,
        user_id: str,
        conversation_ids: List[str],
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Bulk update multiple conversations."""
        try:
            # Verify ownership of all conversations
            result = await self.db_session.execute(
                select(ChatConversation.id).where(
                    and_(
                        ChatConversation.user_id == user_id,
                        ChatConversation.id.in_(conversation_ids)
                    )
                )
            )
            owned_ids = [str(row[0]) for row in result.all()]
            
            if len(owned_ids) != len(conversation_ids):
                unauthorized = set(conversation_ids) - set(owned_ids)
                raise ValueError(f"Unauthorized access to conversations: {unauthorized}")
            
            # Prepare update values
            update_values = {"last_modified_by": user_id}
            
            if "title" in updates:
                update_values["title"] = updates["title"]
            
            if "is_archived" in updates:
                update_values["is_archived"] = updates["is_archived"]
                if updates["is_archived"]:
                    update_values["archived_at"] = datetime.utcnow()
            
            # Handle metadata updates
            metadata_updates = {k: v for k, v in updates.items() 
                              if k not in ["title", "is_archived"]}
            
            if metadata_updates:
                # Update metadata for all conversations
                for conv_id in owned_ids:
                    conv_result = await self.db_session.execute(
                        select(ChatConversation).where(ChatConversation.id == conv_id)
                    )
                    conv = conv_result.scalar_one()
                    
                    current_metadata = conv.metadata or {}
                    current_metadata.update(metadata_updates)
                    
                    await self.db_session.execute(
                        update(ChatConversation)
                        .where(ChatConversation.id == conv_id)
                        .values(metadata=current_metadata)
                    )
            
            # Apply basic updates
            if any(k in update_values for k in ["title", "is_archived"]):
                await self.db_session.execute(
                    update(ChatConversation)
                    .where(ChatConversation.id.in_(owned_ids))
                    .values(**{k: v for k, v in update_values.items() 
                              if k in ["title", "is_archived", "last_modified_by"]})
                )
            
            await self.db_session.commit()
            
            # Log bulk update
            await log_security_event(
                "conversations_bulk_updated",
                {
                    "user_id": user_id,
                    "conversation_count": len(owned_ids),
                    "updates": list(updates.keys())
                },
                user_id=user_id,
                threat_level=ThreatLevel.LOW
            )
            
            return {
                "updated_count": len(owned_ids),
                "updates_applied": list(updates.keys())
            }
            
        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"Failed to bulk update conversations for user {user_id}: {e}")
            raise