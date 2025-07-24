"""
Production-grade conversation management system for AI Karen.
Handles multi-tenant conversations with advanced features like context management,
conversation summarization, and intelligent memory integration.
"""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum

from sqlalchemy import text, select, insert, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ai_karen_engine.database.client import MultiTenantPostgresClient
from ai_karen_engine.database.models import TenantConversation, User
from ai_karen_engine.database.memory_manager import MemoryManager, MemoryQuery
from ai_karen_engine.core.embedding_manager import EmbeddingManager

logger = logging.getLogger(__name__)


class MessageRole(Enum):
    """Message roles in conversation."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    FUNCTION = "function"


@dataclass
class Message:
    """Represents a conversation message."""
    id: str
    role: MessageRole
    content: str
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    function_call: Optional[Dict[str, Any]] = None
    function_response: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "role": self.role.value,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
            "function_call": self.function_call,
            "function_response": self.function_response
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            role=MessageRole(data["role"]),
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            metadata=data.get("metadata", {}),
            function_call=data.get("function_call"),
            function_response=data.get("function_response")
        )


@dataclass
class Conversation:
    """Represents a complete conversation."""
    id: str
    user_id: str
    title: Optional[str]
    messages: List[Message]
    metadata: Dict[str, Any] = field(default_factory=dict)
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "messages": [msg.to_dict() for msg in self.messages],
            "metadata": self.metadata,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "message_count": len(self.messages),
            "last_message_at": self.messages[-1].timestamp.isoformat() if self.messages else None
        }
    
    def get_context_window(self, max_messages: int = 20) -> List[Message]:
        """Get recent messages for context window."""
        return self.messages[-max_messages:] if self.messages else []
    
    def get_summary_text(self) -> str:
        """Get a text summary of the conversation."""
        if not self.messages:
            return "Empty conversation"
        
        user_messages = [m for m in self.messages if m.role == MessageRole.USER]
        assistant_messages = [m for m in self.messages if m.role == MessageRole.ASSISTANT]
        
        summary_parts = []
        if self.title:
            summary_parts.append(f"Title: {self.title}")
        
        summary_parts.append(f"Messages: {len(self.messages)}")
        summary_parts.append(f"User messages: {len(user_messages)}")
        summary_parts.append(f"Assistant messages: {len(assistant_messages)}")
        
        if self.messages:
            summary_parts.append(f"Started: {self.messages[0].timestamp}")
            summary_parts.append(f"Last activity: {self.messages[-1].timestamp}")
        
        return " | ".join(summary_parts)


class ConversationManager:
    """Production-grade conversation management system."""
    
    def __init__(
        self,
        db_client: MultiTenantPostgresClient,
        memory_manager: Optional[MemoryManager] = None,
        embedding_manager: Optional[EmbeddingManager] = None
    ):
        """Initialize conversation manager.
        
        Args:
            db_client: Database client
            memory_manager: Memory manager for context integration
            embedding_manager: Embedding manager for conversation analysis
        """
        self.db_client = db_client
        self.memory_manager = memory_manager
        self.embedding_manager = embedding_manager
        
        # Configuration
        self.max_context_messages = 50
        self.auto_title_threshold = 3  # Auto-generate title after N messages
        self.summary_interval_messages = 100  # Summarize every N messages
        self.inactive_threshold_days = 30  # Mark as inactive after N days
        
        # Performance tracking
        self.metrics = {
            "conversations_created": 0,
            "messages_added": 0,
            "conversations_retrieved": 0,
            "summaries_generated": 0,
            "avg_response_time": 0.0
        }
    
    async def create_conversation(
        self,
        tenant_id: Union[str, uuid.UUID],
        user_id: str,
        title: Optional[str] = None,
        initial_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Conversation:
        """Create a new conversation.
        
        Args:
            tenant_id: Tenant ID
            user_id: User ID
            title: Conversation title
            initial_message: Initial user message
            metadata: Additional metadata
            
        Returns:
            Created conversation
        """
        start_time = time.time()
        
        try:
            conversation_id = str(uuid.uuid4())
            messages = []
            
            # Add initial message if provided
            if initial_message:
                message = Message(
                    id=str(uuid.uuid4()),
                    role=MessageRole.USER,
                    content=initial_message,
                    timestamp=datetime.utcnow()
                )
                messages.append(message)
            
            conversation = Conversation(
                id=conversation_id,
                user_id=user_id,
                title=title,
                messages=messages,
                metadata=metadata or {}
            )
            
            # Store in database
            async with self.db_client.get_async_session() as session:
                db_conversation = TenantConversation(
                    id=uuid.UUID(conversation_id),
                    user_id=uuid.UUID(user_id),
                    title=title,
                    messages=[msg.to_dict() for msg in messages],
                    conversation_metadata=metadata or {}
                )
                
                session.add(db_conversation)
                await session.commit()
            
            # Store initial message in memory if available
            if initial_message and self.memory_manager:
                await self.memory_manager.store_memory(
                    tenant_id=tenant_id,
                    content=initial_message,
                    user_id=user_id,
                    session_id=conversation_id,
                    metadata={"type": "conversation_start", "conversation_id": conversation_id}
                )
            
            self.metrics["conversations_created"] += 1
            
            response_time = time.time() - start_time
            self.metrics["avg_response_time"] = (
                self.metrics["avg_response_time"] * 0.9 + response_time * 0.1
            )
            
            logger.info(f"Created conversation {conversation_id} for user {user_id}")
            return conversation
            
        except Exception as e:
            logger.error(f"Failed to create conversation: {e}")
            raise
    
    async def get_conversation(
        self,
        tenant_id: Union[str, uuid.UUID],
        conversation_id: str,
        include_context: bool = True
    ) -> Optional[Conversation]:
        """Get conversation by ID.
        
        Args:
            tenant_id: Tenant ID
            conversation_id: Conversation ID
            include_context: Whether to include memory context
            
        Returns:
            Conversation if found
        """
        try:
            async with self.db_client.get_async_session() as session:
                result = await session.execute(
                    select(TenantConversation)
                    .where(TenantConversation.id == uuid.UUID(conversation_id))
                )
                
                db_conversation = result.scalar_one_or_none()
                if not db_conversation:
                    return None
                
                # Convert to conversation object
                messages = [
                    Message.from_dict(msg_data)
                    for msg_data in (db_conversation.messages or [])
                ]
                
                conversation = Conversation(
                    id=str(db_conversation.id),
                    user_id=str(db_conversation.user_id),
                    title=db_conversation.title,
                    messages=messages,
                    metadata=db_conversation.conversation_metadata or {},
                    is_active=db_conversation.is_active,
                    created_at=db_conversation.created_at,
                    updated_at=db_conversation.updated_at
                )
                
                # Add memory context if requested
                if include_context and self.memory_manager and messages:
                    await self._add_memory_context(tenant_id, conversation)
                
                self.metrics["conversations_retrieved"] += 1
                return conversation
                
        except Exception as e:
            logger.error(f"Failed to get conversation {conversation_id}: {e}")
            return None
    
    async def add_message(
        self,
        tenant_id: Union[str, uuid.UUID],
        conversation_id: str,
        role: MessageRole,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        function_call: Optional[Dict[str, Any]] = None,
        function_response: Optional[Dict[str, Any]] = None
    ) -> Optional[Message]:
        """Add a message to conversation.
        
        Args:
            tenant_id: Tenant ID
            conversation_id: Conversation ID
            role: Message role
            content: Message content
            metadata: Message metadata
            function_call: Function call data
            function_response: Function response data
            
        Returns:
            Added message
        """
        try:
            message = Message(
                id=str(uuid.uuid4()),
                role=role,
                content=content,
                timestamp=datetime.utcnow(),
                metadata=metadata or {},
                function_call=function_call,
                function_response=function_response
            )
            
            # Update conversation in database
            async with self.db_client.get_async_session() as session:
                # Get current conversation
                result = await session.execute(
                    select(TenantConversation)
                    .where(TenantConversation.id == uuid.UUID(conversation_id))
                )
                
                db_conversation = result.scalar_one_or_none()
                if not db_conversation:
                    logger.error(f"Conversation {conversation_id} not found")
                    return None
                
                # Add message to conversation
                current_messages = db_conversation.messages or []
                current_messages.append(message.to_dict())
                
                # Update conversation
                await session.execute(
                    update(TenantConversation)
                    .where(TenantConversation.id == uuid.UUID(conversation_id))
                    .values(
                        messages=current_messages,
                        updated_at=datetime.utcnow()
                    )
                )
                await session.commit()
            
            # Store in memory if it's a user message
            if role == MessageRole.USER and self.memory_manager:
                await self.memory_manager.store_memory(
                    tenant_id=tenant_id,
                    content=content,
                    user_id=db_conversation.user_id,
                    session_id=conversation_id,
                    metadata={
                        "type": "user_message",
                        "conversation_id": conversation_id,
                        "message_id": message.id
                    }
                )
            
            # Auto-generate title if needed
            if len(current_messages) == self.auto_title_threshold and not db_conversation.title:
                await self._auto_generate_title(tenant_id, conversation_id)
            
            # Generate summary if needed
            if len(current_messages) % self.summary_interval_messages == 0:
                await self._generate_conversation_summary(tenant_id, conversation_id)
            
            self.metrics["messages_added"] += 1
            
            logger.debug(f"Added message to conversation {conversation_id}")
            return message
            
        except Exception as e:
            logger.error(f"Failed to add message to conversation {conversation_id}: {e}")
            return None
    
    async def list_conversations(
        self,
        tenant_id: Union[str, uuid.UUID],
        user_id: str,
        active_only: bool = True,
        limit: int = 50,
        offset: int = 0
    ) -> List[Conversation]:
        """List conversations for a user.
        
        Args:
            tenant_id: Tenant ID
            user_id: User ID
            active_only: Only return active conversations
            limit: Maximum number of conversations
            offset: Number of conversations to skip
            
        Returns:
            List of conversations
        """
        try:
            async with self.db_client.get_async_session() as session:
                query = (
                    select(TenantConversation)
                    .where(TenantConversation.user_id == uuid.UUID(user_id))
                    .order_by(TenantConversation.updated_at.desc())
                )
                
                if active_only:
                    query = query.where(TenantConversation.is_active == True)
                
                query = query.limit(limit).offset(offset)
                
                result = await session.execute(query)
                db_conversations = result.scalars().all()
                
                conversations = []
                for db_conv in db_conversations:
                    messages = [
                        Message.from_dict(msg_data)
                        for msg_data in (db_conv.messages or [])
                    ]
                    
                    conversation = Conversation(
                        id=str(db_conv.id),
                        user_id=str(db_conv.user_id),
                        title=db_conv.title,
                        messages=messages,
                        metadata=db_conv.conversation_metadata or {},
                        is_active=db_conv.is_active,
                        created_at=db_conv.created_at,
                        updated_at=db_conv.updated_at
                    )
                    conversations.append(conversation)
                
                return conversations
                
        except Exception as e:
            logger.error(f"Failed to list conversations for user {user_id}: {e}")
            return []
    
    async def update_conversation(
        self,
        tenant_id: Union[str, uuid.UUID],
        conversation_id: str,
        title: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        is_active: Optional[bool] = None
    ) -> bool:
        """Update conversation properties.
        
        Args:
            tenant_id: Tenant ID
            conversation_id: Conversation ID
            title: New title
            metadata: New metadata
            is_active: Active status
            
        Returns:
            True if successful
        """
        try:
            updates = {"updated_at": datetime.utcnow()}
            
            if title is not None:
                updates["title"] = title
            if metadata is not None:
                updates["conversation_metadata"] = metadata
            if is_active is not None:
                updates["is_active"] = is_active
            
            async with self.db_client.get_async_session() as session:
                await session.execute(
                    update(TenantConversation)
                    .where(TenantConversation.id == uuid.UUID(conversation_id))
                    .values(**updates)
                )
                await session.commit()
            
            logger.info(f"Updated conversation {conversation_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update conversation {conversation_id}: {e}")
            return False
    
    async def delete_conversation(
        self,
        tenant_id: Union[str, uuid.UUID],
        conversation_id: str
    ) -> bool:
        """Delete a conversation.
        
        Args:
            tenant_id: Tenant ID
            conversation_id: Conversation ID
            
        Returns:
            True if successful
        """
        try:
            async with self.db_client.get_async_session() as session:
                await session.execute(
                    delete(TenantConversation)
                    .where(TenantConversation.id == uuid.UUID(conversation_id))
                )
                await session.commit()
            
            # Clean up related memories
            if self.memory_manager:
                # This would require implementing a method to delete memories by session_id
                pass
            
            logger.info(f"Deleted conversation {conversation_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete conversation {conversation_id}: {e}")
            return False
    
    async def get_conversation_context(
        self,
        tenant_id: Union[str, uuid.UUID],
        conversation_id: str,
        query_text: str,
        max_context_items: int = 5
    ) -> List[Dict[str, Any]]:
        """Get relevant context for conversation from memory.
        
        Args:
            tenant_id: Tenant ID
            conversation_id: Conversation ID
            query_text: Text to find context for
            max_context_items: Maximum context items to return
            
        Returns:
            List of context items
        """
        if not self.memory_manager:
            return []
        
        try:
            # Get conversation to find user_id
            conversation = await self.get_conversation(tenant_id, conversation_id, include_context=False)
            if not conversation:
                return []
            
            # Query memory for relevant context
            memory_query = MemoryQuery(
                text=query_text,
                user_id=conversation.user_id,
                top_k=max_context_items,
                similarity_threshold=0.7
            )
            
            memories = await self.memory_manager.query_memories(tenant_id, memory_query)
            
            # Convert to context format
            context_items = []
            for memory in memories:
                context_items.append({
                    "content": memory.content,
                    "timestamp": memory.timestamp,
                    "similarity_score": memory.similarity_score,
                    "metadata": memory.metadata,
                    "source": "memory"
                })
            
            return context_items
            
        except Exception as e:
            logger.error(f"Failed to get conversation context: {e}")
            return []
    
    async def get_conversation_stats(
        self,
        tenant_id: Union[str, uuid.UUID],
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get conversation statistics.
        
        Args:
            tenant_id: Tenant ID
            user_id: Optional user ID to filter by
            
        Returns:
            Conversation statistics
        """
        try:
            async with self.db_client.get_async_session() as session:
                # Base query
                base_query = select(TenantConversation)
                if user_id:
                    base_query = base_query.where(TenantConversation.user_id == uuid.UUID(user_id))
                
                # Total conversations
                total_result = await session.execute(
                    select(func.count()).select_from(base_query.subquery())
                )
                total_conversations = total_result.scalar()
                
                # Active conversations
                active_result = await session.execute(
                    select(func.count()).select_from(
                        base_query.where(TenantConversation.is_active == True).subquery()
                    )
                )
                active_conversations = active_result.scalar()
                
                # Recent conversations (last 7 days)
                recent_cutoff = datetime.utcnow() - timedelta(days=7)
                recent_result = await session.execute(
                    select(func.count()).select_from(
                        base_query.where(TenantConversation.updated_at > recent_cutoff).subquery()
                    )
                )
                recent_conversations = recent_result.scalar()
                
                # Average messages per conversation
                all_conversations = await session.execute(base_query)
                conversations = all_conversations.scalars().all()
                
                total_messages = sum(len(conv.messages or []) for conv in conversations)
                avg_messages = total_messages / total_conversations if total_conversations > 0 else 0
                
                return {
                    "total_conversations": total_conversations,
                    "active_conversations": active_conversations,
                    "recent_conversations_7d": recent_conversations,
                    "total_messages": total_messages,
                    "avg_messages_per_conversation": round(avg_messages, 2),
                    "metrics": self.metrics.copy()
                }
                
        except Exception as e:
            logger.error(f"Failed to get conversation stats: {e}")
            return {"error": str(e)}
    
    async def _add_memory_context(self, tenant_id: Union[str, uuid.UUID], conversation: Conversation):
        """Add relevant memory context to conversation."""
        if not self.memory_manager or not conversation.messages:
            return
        
        try:
            # Get the last user message for context
            last_user_message = None
            for msg in reversed(conversation.messages):
                if msg.role == MessageRole.USER:
                    last_user_message = msg
                    break
            
            if not last_user_message:
                return
            
            # Query for relevant memories
            memory_query = MemoryQuery(
                text=last_user_message.content,
                user_id=conversation.user_id,
                top_k=3,
                similarity_threshold=0.75
            )
            
            memories = await self.memory_manager.query_memories(tenant_id, memory_query)
            
            # Add context to conversation metadata
            if memories:
                conversation.metadata["memory_context"] = [
                    {
                        "content": memory.content,
                        "similarity_score": memory.similarity_score,
                        "timestamp": memory.timestamp
                    }
                    for memory in memories
                ]
                
        except Exception as e:
            logger.warning(f"Failed to add memory context: {e}")
    
    async def _auto_generate_title(self, tenant_id: Union[str, uuid.UUID], conversation_id: str):
        """Auto-generate conversation title based on content."""
        try:
            conversation = await self.get_conversation(tenant_id, conversation_id, include_context=False)
            if not conversation or not conversation.messages:
                return
            
            # Get first few user messages
            user_messages = [
                msg.content for msg in conversation.messages[:5]
                if msg.role == MessageRole.USER
            ]
            
            if not user_messages:
                return
            
            # Simple title generation (in production, use LLM)
            first_message = user_messages[0]
            title = first_message[:50] + "..." if len(first_message) > 50 else first_message
            
            # Update conversation title
            await self.update_conversation(tenant_id, conversation_id, title=title)
            
            logger.info(f"Auto-generated title for conversation {conversation_id}: {title}")
            
        except Exception as e:
            logger.error(f"Failed to auto-generate title: {e}")
    
    async def _generate_conversation_summary(self, tenant_id: Union[str, uuid.UUID], conversation_id: str):
        """Generate conversation summary for long conversations."""
        try:
            conversation = await self.get_conversation(tenant_id, conversation_id, include_context=False)
            if not conversation or len(conversation.messages) < self.summary_interval_messages:
                return
            
            # Generate summary (in production, use LLM)
            summary = f"Conversation with {len(conversation.messages)} messages"
            
            # Store summary in metadata
            metadata = conversation.metadata.copy()
            metadata["summary"] = summary
            metadata["summary_generated_at"] = datetime.utcnow().isoformat()
            
            await self.update_conversation(tenant_id, conversation_id, metadata=metadata)
            
            self.metrics["summaries_generated"] += 1
            logger.info(f"Generated summary for conversation {conversation_id}")
            
        except Exception as e:
            logger.error(f"Failed to generate conversation summary: {e}")
    
    async def cleanup_inactive_conversations(
        self,
        tenant_id: Union[str, uuid.UUID],
        days_inactive: int = None
    ) -> int:
        """Mark old conversations as inactive.
        
        Args:
            tenant_id: Tenant ID
            days_inactive: Days of inactivity threshold
            
        Returns:
            Number of conversations marked inactive
        """
        days_inactive = days_inactive or self.inactive_threshold_days
        cutoff_date = datetime.utcnow() - timedelta(days=days_inactive)
        
        try:
            async with self.db_client.get_async_session() as session:
                result = await session.execute(
                    update(TenantConversation)
                    .where(
                        TenantConversation.updated_at < cutoff_date,
                        TenantConversation.is_active == True
                    )
                    .values(is_active=False, updated_at=datetime.utcnow())
                )
                
                await session.commit()
                count = result.rowcount
                
                logger.info(f"Marked {count} conversations as inactive for tenant {tenant_id}")
                return count
                
        except Exception as e:
            logger.error(f"Failed to cleanup inactive conversations: {e}")
            return 0
