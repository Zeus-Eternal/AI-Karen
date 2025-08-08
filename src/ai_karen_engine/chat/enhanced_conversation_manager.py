"""
Enhanced ConversationManager with advanced features for production-ready chat system.
Supports branching, templates, folders, search, and comprehensive conversation management.
"""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import text, select, insert, update, delete, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ai_karen_engine.database.client import MultiTenantPostgresClient
from ai_karen_engine.database.models import TenantConversation, AuthUser
from ai_karen_engine.chat.conversation_models import (
    Conversation, ChatMessage, ConversationFolder, ConversationTemplate,
    ConversationFilters, ConversationSearchResult, ConversationExportOptions,
    ConversationImportOptions, ConversationBranch, ConversationStats,
    QuickAction, MessageRole, MessageType, ConversationStatus
)

logger = logging.getLogger(__name__)


class ConversationSearchService:
    """Service for searching conversations with full-text and semantic search."""
    
    def __init__(self, distilbert_service=None):
        self.distilbert_service = distilbert_service
        
    async def hybrid_search(
        self,
        user_id: str,
        text_query: str,
        embedding_query: Optional[List[float]] = None,
        filters: Optional[ConversationFilters] = None,
        limit: int = 20
    ) -> List[ConversationSearchResult]:
        """Perform hybrid search combining text and semantic similarity."""
        # This would integrate with full-text search and vector search
        # For now, returning mock results
        return []


class ConversationExportService:
    """Service for exporting conversations in various formats."""
    
    async def export_conversation(
        self,
        conversation: Conversation,
        messages: List[ChatMessage],
        options: ConversationExportOptions
    ) -> Dict[str, Any]:
        """Export conversation in specified format."""
        if options.format == "json":
            return await self._export_json(conversation, messages, options)
        elif options.format == "markdown":
            return await self._export_markdown(conversation, messages, options)
        elif options.format == "pdf":
            return await self._export_pdf(conversation, messages, options)
        elif options.format == "html":
            return await self._export_html(conversation, messages, options)
        else:
            raise ValueError(f"Unsupported export format: {options.format}")
    
    async def _export_json(
        self,
        conversation: Conversation,
        messages: List[ChatMessage],
        options: ConversationExportOptions
    ) -> Dict[str, Any]:
        """Export as JSON format."""
        export_data = {
            "conversation": conversation.model_dump(),
            "messages": [msg.model_dump() for msg in messages],
            "export_metadata": {
                "exported_at": datetime.utcnow().isoformat(),
                "format": "json",
                "version": "1.0"
            }
        }
        
        if not options.include_metadata:
            # Remove metadata fields
            export_data["conversation"].pop("metadata", None)
            for msg in export_data["messages"]:
                msg.pop("metadata", None)
        
        return export_data
    
    async def _export_markdown(
        self,
        conversation: Conversation,
        messages: List[ChatMessage],
        options: ConversationExportOptions
    ) -> Dict[str, Any]:
        """Export as Markdown format."""
        md_content = f"# {conversation.title}\n\n"
        
        if conversation.description:
            md_content += f"{conversation.description}\n\n"
        
        if options.include_metadata:
            md_content += f"**Created:** {conversation.created_at}\n"
            md_content += f"**Messages:** {len(messages)}\n"
            if conversation.tags:
                md_content += f"**Tags:** {', '.join(conversation.tags)}\n"
            md_content += "\n---\n\n"
        
        for msg in messages:
            if not options.include_system_messages and msg.role == MessageRole.SYSTEM:
                continue
                
            role_emoji = {"user": "👤", "assistant": "🤖", "system": "⚙️"}.get(msg.role.value, "")
            md_content += f"## {role_emoji} {msg.role.value.title()}\n\n"
            md_content += f"{msg.content}\n\n"
            
            if options.include_metadata and msg.created_at:
                md_content += f"*{msg.created_at}*\n\n"
        
        return {
            "content": md_content,
            "filename": f"{conversation.title}.md"
        }
    
    async def _export_pdf(
        self,
        conversation: Conversation,
        messages: List[ChatMessage],
        options: ConversationExportOptions
    ) -> Dict[str, Any]:
        """Export as PDF format."""
        # This would use a PDF generation library like reportlab
        # For now, returning placeholder
        return {
            "content": b"PDF content placeholder",
            "filename": f"{conversation.title}.pdf",
            "content_type": "application/pdf"
        }
    
    async def _export_html(
        self,
        conversation: Conversation,
        messages: List[ChatMessage],
        options: ConversationExportOptions
    ) -> Dict[str, Any]:
        """Export as HTML format."""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{conversation.title}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .message {{ margin: 20px 0; padding: 15px; border-radius: 8px; }}
                .user {{ background-color: #e3f2fd; }}
                .assistant {{ background-color: #f3e5f5; }}
                .system {{ background-color: #f5f5f5; }}
                .timestamp {{ font-size: 0.8em; color: #666; }}
            </style>
        </head>
        <body>
            <h1>{conversation.title}</h1>
        """
        
        if conversation.description:
            html_content += f"<p>{conversation.description}</p>"
        
        for msg in messages:
            if not options.include_system_messages and msg.role == MessageRole.SYSTEM:
                continue
                
            html_content += f"""
            <div class="message {msg.role.value}">
                <strong>{msg.role.value.title()}:</strong>
                <p>{msg.content}</p>
                {f'<div class="timestamp">{msg.created_at}</div>' if options.include_metadata else ''}
            </div>
            """
        
        html_content += "</body></html>"
        
        return {
            "content": html_content,
            "filename": f"{conversation.title}.html"
        }


class EnhancedConversationManager:
    """Enhanced conversation manager with advanced features."""
    
    def __init__(
        self,
        db_client: MultiTenantPostgresClient,
        distilbert_service=None,
        file_storage=None
    ):
        """Initialize enhanced conversation manager."""
        self.db_client = db_client
        self.distilbert_service = distilbert_service
        self.file_storage = file_storage
        
        # Services
        self.search_service = ConversationSearchService(db_client, distilbert_service)
        self.export_service = ConversationExportService()
        
        # Configuration
        self.max_context_messages = 50
        self.auto_title_threshold = 3
        self.summary_interval_messages = 100
        self.inactive_threshold_days = 30
        
        # Performance tracking
        self.metrics = {
            "conversations_created": 0,
            "conversations_branched": 0,
            "templates_used": 0,
            "searches_performed": 0,
            "exports_completed": 0,
            "avg_response_time": 0.0
        }
    
    # CRUD Operations
    
    async def create_conversation(
        self,
        tenant_id: Union[str, uuid.UUID],
        user_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        folder_id: Optional[str] = None,
        template_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        initial_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Conversation:
        """Create a new conversation with advanced features."""
        start_time = time.time()
        
        try:
            conversation_id = str(uuid.uuid4())
            
            # Apply template if specified
            template_data = None
            if template_id:
                template_data = await self.get_template(template_id)
                if template_data:
                    if not title:
                        title = f"New {template_data.name}"
                    self.metrics["templates_used"] += 1
            
            # Generate title if not provided
            if not title:
                title = await self._generate_conversation_title(user_id, initial_message)
            
            # Create conversation object
            conversation = Conversation(
                id=conversation_id,
                user_id=user_id,
                title=title,
                description=description,
                folder_id=folder_id,
                template_id=template_id,
                tags=tags or [],
                metadata=metadata or {}
            )
            
            # Store in database
            async with self.db_client.get_async_session() as session:
                db_conversation = TenantConversation(
                    id=uuid.UUID(conversation_id),
                    user_id=uuid.UUID(user_id),
                    title=title,
                    messages=[],
                    conversation_metadata={
                        **conversation.metadata,
                        "folder_id": folder_id,
                        "template_id": template_id,
                        "tags": tags or [],
                        "description": description,
                        "status": conversation.status.value,
                        "is_favorite": conversation.is_favorite,
                        "priority": conversation.priority
                    }
                )
                
                session.add(db_conversation)
                await session.commit()
            
            # Add initial messages from template
            if template_data and template_data.initial_messages:
                for template_msg in template_data.initial_messages:
                    await self.add_message(
                        tenant_id=tenant_id,
                        conversation_id=conversation_id,
                        role=template_msg.role,
                        content=template_msg.content,
                        message_type=template_msg.message_type,
                        metadata=template_msg.metadata
                    )
            
            # Add initial user message if provided
            if initial_message:
                await self.add_message(
                    tenant_id=tenant_id,
                    conversation_id=conversation_id,
                    role=MessageRole.USER,
                    content=initial_message
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
        include_messages: bool = True,
        include_branches: bool = False
    ) -> Optional[Conversation]:
        """Get conversation by ID with enhanced features."""
        try:
            async with self.db_client.get_async_session() as session:
                result = await session.execute(
                    select(TenantConversation)
                    .where(TenantConversation.id == uuid.UUID(conversation_id))
                )
                
                db_conversation = result.scalar_one_or_none()
                if not db_conversation:
                    return None
                
                # Convert to enhanced conversation object
                metadata = db_conversation.conversation_metadata or {}
                
                conversation = Conversation(
                    id=str(db_conversation.id),
                    user_id=str(db_conversation.user_id),
                    title=db_conversation.title or "Untitled Conversation",
                    description=metadata.get("description"),
                    status=ConversationStatus(metadata.get("status", "active")),
                    folder_id=metadata.get("folder_id"),
                    tags=metadata.get("tags", []),
                    is_favorite=metadata.get("is_favorite", False),
                    priority=metadata.get("priority", 0),
                    template_id=metadata.get("template_id"),
                    parent_conversation_id=metadata.get("parent_conversation_id"),
                    branch_point_message_id=metadata.get("branch_point_message_id"),
                    child_branches=metadata.get("child_branches", []),
                    message_count=len(db_conversation.messages or []),
                    created_at=db_conversation.created_at,
                    updated_at=db_conversation.updated_at,
                    metadata=metadata
                )
                
                # Update last accessed time
                await self._update_last_accessed(conversation_id)
                
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
        message_type: MessageType = MessageType.TEXT,
        metadata: Optional[Dict[str, Any]] = None,
        parent_message_id: Optional[str] = None,
        attachments: Optional[List[str]] = None
    ) -> Optional[ChatMessage]:
        """Add a message to conversation with enhanced features."""
        try:
            message = ChatMessage(
                id=str(uuid.uuid4()),
                conversation_id=conversation_id,
                role=role,
                content=content,
                message_type=message_type,
                metadata=metadata or {},
                parent_message_id=parent_message_id,
                attachments=attachments or []
            )
            
            # Update conversation in database
            async with self.db_client.get_async_session() as session:
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
                current_messages.append(message.model_dump())
                
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
            
            logger.debug(f"Added message to conversation {conversation_id}")
            return message
            
        except Exception as e:
            logger.error(f"Failed to add message to conversation {conversation_id}: {e}")
            return None
    
    # Advanced Features
    
    async def branch_conversation(
        self,
        tenant_id: Union[str, uuid.UUID],
        conversation_id: str,
        from_message_id: str,
        user_id: str,
        branch_title: Optional[str] = None
    ) -> Optional[Conversation]:
        """Create a new conversation branch from a specific message."""
        try:
            # Get original conversation
            original_conversation = await self.get_conversation(
                tenant_id, conversation_id, include_messages=True
            )
            if not original_conversation:
                return None
            
            # Get messages up to branch point
            messages = await self.get_conversation_messages(
                tenant_id, conversation_id, up_to_message_id=from_message_id
            )
            
            # Create branch title
            if not branch_title:
                branch_title = f"{original_conversation.title} (Branch)"
            
            # Create new conversation
            branch_conversation = await self.create_conversation(
                tenant_id=tenant_id,
                user_id=user_id,
                title=branch_title,
                folder_id=original_conversation.folder_id,
                tags=original_conversation.tags,
                metadata={
                    "parent_conversation_id": conversation_id,
                    "branch_point_message_id": from_message_id,
                    "is_branch": True
                }
            )
            
            # Copy messages up to branch point
            for message in messages:
                await self.add_message(
                    tenant_id=tenant_id,
                    conversation_id=branch_conversation.id,
                    role=message.role,
                    content=message.content,
                    message_type=message.message_type,
                    metadata=message.metadata,
                    attachments=message.attachments
                )
            
            # Update parent conversation to track this branch
            await self._add_child_branch(conversation_id, branch_conversation.id)
            
            self.metrics["conversations_branched"] += 1
            
            logger.info(f"Created branch {branch_conversation.id} from {conversation_id}")
            return branch_conversation
            
        except Exception as e:
            logger.error(f"Failed to branch conversation {conversation_id}: {e}")
            return None
    
    async def get_conversation_messages(
        self,
        tenant_id: Union[str, uuid.UUID],
        conversation_id: str,
        up_to_message_id: Optional[str] = None,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[ChatMessage]:
        """Get messages from a conversation with filtering options."""
        try:
            async with self.db_client.get_async_session() as session:
                result = await session.execute(
                    select(TenantConversation)
                    .where(TenantConversation.id == uuid.UUID(conversation_id))
                )
                
                db_conversation = result.scalar_one_or_none()
                if not db_conversation:
                    return []
                
                messages_data = db_conversation.messages or []
                messages = [ChatMessage(**msg_data) for msg_data in messages_data]
                
                # Filter up to specific message if requested
                if up_to_message_id:
                    filtered_messages = []
                    for msg in messages:
                        filtered_messages.append(msg)
                        if msg.id == up_to_message_id:
                            break
                    messages = filtered_messages
                
                # Apply pagination
                if offset > 0:
                    messages = messages[offset:]
                if limit:
                    messages = messages[:limit]
                
                return messages
                
        except Exception as e:
            logger.error(f"Failed to get messages for conversation {conversation_id}: {e}")
            return []
    
    # Folder Management
    
    async def create_folder(
        self,
        tenant_id: Union[str, uuid.UUID],
        user_id: str,
        name: str,
        description: Optional[str] = None,
        parent_folder_id: Optional[str] = None,
        color: Optional[str] = None,
        icon: Optional[str] = None
    ) -> ConversationFolder:
        """Create a new conversation folder."""
        folder = ConversationFolder(
            user_id=user_id,
            name=name,
            description=description,
            parent_folder_id=parent_folder_id,
            color=color,
            icon=icon
        )
        
        # Store in database (would need to extend schema)
        # For now, storing in conversation metadata
        
        logger.info(f"Created folder {folder.id} for user {user_id}")
        return folder
    
    async def move_to_folder(
        self,
        tenant_id: Union[str, uuid.UUID],
        conversation_id: str,
        folder_id: Optional[str]
    ) -> bool:
        """Move conversation to a folder."""
        try:
            async with self.db_client.get_async_session() as session:
                result = await session.execute(
                    select(TenantConversation)
                    .where(TenantConversation.id == uuid.UUID(conversation_id))
                )
                
                db_conversation = result.scalar_one_or_none()
                if not db_conversation:
                    return False
                
                # Update metadata
                metadata = db_conversation.conversation_metadata or {}
                metadata["folder_id"] = folder_id
                
                await session.execute(
                    update(TenantConversation)
                    .where(TenantConversation.id == uuid.UUID(conversation_id))
                    .values(
                        conversation_metadata=metadata,
                        updated_at=datetime.utcnow()
                    )
                )
                await session.commit()
                
                return True
                
        except Exception as e:
            logger.error(f"Failed to move conversation {conversation_id} to folder: {e}")
            return False
    
    # Template Management
    
    async def create_template(
        self,
        user_id: Optional[str],
        name: str,
        description: Optional[str] = None,
        category: str = "general",
        initial_messages: Optional[List[ChatMessage]] = None,
        tags: Optional[List[str]] = None,
        is_public: bool = False
    ) -> ConversationTemplate:
        """Create a new conversation template."""
        template = ConversationTemplate(
            user_id=user_id,
            name=name,
            description=description,
            category=category,
            initial_messages=initial_messages or [],
            tags=tags or [],
            is_public=is_public
        )
        
        # Store in database (would need to extend schema)
        
        logger.info(f"Created template {template.id}")
        return template
    
    async def get_template(self, template_id: str) -> Optional[ConversationTemplate]:
        """Get a conversation template by ID."""
        # This would fetch from database
        # For now, returning None
        return None
    
    async def list_templates(
        self,
        user_id: Optional[str] = None,
        category: Optional[str] = None,
        is_public: Optional[bool] = None
    ) -> List[ConversationTemplate]:
        """List available conversation templates."""
        # This would fetch from database with filters
        return []
    
    # Search and Filtering
    
    async def search_conversations(
        self,
        tenant_id: Union[str, uuid.UUID],
        user_id: str,
        query: str,
        filters: Optional[ConversationFilters] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[ConversationSearchResult]:
        """Search conversations with full-text and semantic search."""
        try:
            self.metrics["searches_performed"] += 1
            
            # Generate query embedding for semantic search if available
            query_embedding = None
            if self.distilbert_service:
                query_embedding = await self.distilbert_service.get_embeddings(query)
            
            # Perform hybrid search
            results = await self.search_service.hybrid_search(
                user_id=user_id,
                text_query=query,
                embedding_query=query_embedding,
                filters=filters,
                limit=limit
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to search conversations: {e}")
            return []
    
    async def list_conversations(
        self,
        tenant_id: Union[str, uuid.UUID],
        user_id: str,
        filters: Optional[ConversationFilters] = None,
        sort_by: str = "updated_at",
        sort_order: str = "desc",
        limit: int = 50,
        offset: int = 0
    ) -> List[Conversation]:
        """List conversations with advanced filtering and sorting."""
        try:
            async with self.db_client.get_async_session() as session:
                query = (
                    select(TenantConversation)
                    .where(TenantConversation.user_id == uuid.UUID(user_id))
                )
                
                # Apply filters
                if filters:
                    if filters.status:
                        # Filter by status in metadata
                        pass  # Would need JSON query
                    
                    if filters.is_favorite is not None:
                        # Filter by favorite status in metadata
                        pass  # Would need JSON query
                    
                    if filters.folder_ids:
                        # Filter by folder IDs in metadata
                        pass  # Would need JSON query
                    
                    if filters.tags:
                        # Filter by tags in metadata
                        pass  # Would need JSON query
                    
                    if filters.date_from:
                        query = query.where(TenantConversation.created_at >= filters.date_from)
                    
                    if filters.date_to:
                        query = query.where(TenantConversation.created_at <= filters.date_to)
                    
                    if filters.min_messages:
                        # Would need to filter by message count
                        pass
                    
                    if filters.max_messages:
                        # Would need to filter by message count
                        pass
                
                # Apply sorting
                if sort_by == "created_at":
                    if sort_order == "desc":
                        query = query.order_by(TenantConversation.created_at.desc())
                    else:
                        query = query.order_by(TenantConversation.created_at.asc())
                elif sort_by == "updated_at":
                    if sort_order == "desc":
                        query = query.order_by(TenantConversation.updated_at.desc())
                    else:
                        query = query.order_by(TenantConversation.updated_at.asc())
                elif sort_by == "title":
                    if sort_order == "desc":
                        query = query.order_by(TenantConversation.title.desc())
                    else:
                        query = query.order_by(TenantConversation.title.asc())
                
                # Apply pagination
                query = query.limit(limit).offset(offset)
                
                result = await session.execute(query)
                db_conversations = result.scalars().all()
                
                conversations = []
                for db_conv in db_conversations:
                    metadata = db_conv.conversation_metadata or {}
                    
                    conversation = Conversation(
                        id=str(db_conv.id),
                        user_id=str(db_conv.user_id),
                        title=db_conv.title or "Untitled Conversation",
                        description=metadata.get("description"),
                        status=ConversationStatus(metadata.get("status", "active")),
                        folder_id=metadata.get("folder_id"),
                        tags=metadata.get("tags", []),
                        is_favorite=metadata.get("is_favorite", False),
                        priority=metadata.get("priority", 0),
                        message_count=len(db_conv.messages or []),
                        created_at=db_conv.created_at,
                        updated_at=db_conv.updated_at,
                        metadata=metadata
                    )
                    conversations.append(conversation)
                
                return conversations
                
        except Exception as e:
            logger.error(f"Failed to list conversations for user {user_id}: {e}")
            return []
    
    # Export/Import
    
    async def export_conversation(
        self,
        tenant_id: Union[str, uuid.UUID],
        conversation_id: str,
        user_id: str,
        options: ConversationExportOptions
    ) -> Dict[str, Any]:
        """Export conversation in specified format."""
        try:
            conversation = await self.get_conversation(tenant_id, conversation_id)
            if not conversation:
                raise ValueError(f"Conversation {conversation_id} not found")
            
            messages = await self.get_conversation_messages(tenant_id, conversation_id)
            
            result = await self.export_service.export_conversation(
                conversation, messages, options
            )
            
            # Update export count
            await self._increment_export_count(conversation_id)
            
            self.metrics["exports_completed"] += 1
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to export conversation {conversation_id}: {e}")
            raise
    
    # Utility Methods
    
    async def _generate_conversation_title(
        self,
        user_id: str,
        initial_message: Optional[str] = None
    ) -> str:
        """Generate a conversation title."""
        if initial_message:
            # Simple title generation from first message
            title = initial_message[:50] + "..." if len(initial_message) > 50 else initial_message
            return title
        else:
            return f"New Conversation - {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}"
    
    async def _update_last_accessed(self, conversation_id: str):
        """Update the last accessed timestamp for a conversation."""
        try:
            async with self.db_client.get_async_session() as session:
                result = await session.execute(
                    select(TenantConversation)
                    .where(TenantConversation.id == uuid.UUID(conversation_id))
                )
                
                db_conversation = result.scalar_one_or_none()
                if db_conversation:
                    metadata = db_conversation.conversation_metadata or {}
                    metadata["last_accessed_at"] = datetime.utcnow().isoformat()
                    metadata["view_count"] = metadata.get("view_count", 0) + 1
                    
                    await session.execute(
                        update(TenantConversation)
                        .where(TenantConversation.id == uuid.UUID(conversation_id))
                        .values(conversation_metadata=metadata)
                    )
                    await session.commit()
                    
        except Exception as e:
            logger.warning(f"Failed to update last accessed for {conversation_id}: {e}")
    
    async def _add_child_branch(self, parent_id: str, branch_id: str):
        """Add a child branch to parent conversation."""
        try:
            async with self.db_client.get_async_session() as session:
                result = await session.execute(
                    select(TenantConversation)
                    .where(TenantConversation.id == uuid.UUID(parent_id))
                )
                
                db_conversation = result.scalar_one_or_none()
                if db_conversation:
                    metadata = db_conversation.conversation_metadata or {}
                    child_branches = metadata.get("child_branches", [])
                    if branch_id not in child_branches:
                        child_branches.append(branch_id)
                        metadata["child_branches"] = child_branches
                    
                    await session.execute(
                        update(TenantConversation)
                        .where(TenantConversation.id == uuid.UUID(parent_id))
                        .values(conversation_metadata=metadata)
                    )
                    await session.commit()
                    
        except Exception as e:
            logger.warning(f"Failed to add child branch {branch_id} to {parent_id}: {e}")
    
    async def _increment_export_count(self, conversation_id: str):
        """Increment the export count for a conversation."""
        try:
            async with self.db_client.get_async_session() as session:
                result = await session.execute(
                    select(TenantConversation)
                    .where(TenantConversation.id == uuid.UUID(conversation_id))
                )
                
                db_conversation = result.scalar_one_or_none()
                if db_conversation:
                    metadata = db_conversation.conversation_metadata or {}
                    metadata["export_count"] = metadata.get("export_count", 0) + 1
                    
                    await session.execute(
                        update(TenantConversation)
                        .where(TenantConversation.id == uuid.UUID(conversation_id))
                        .values(conversation_metadata=metadata)
                    )
                    await session.commit()
                    
        except Exception as e:
            logger.warning(f"Failed to increment export count for {conversation_id}: {e}")
    
    # Statistics and Analytics
    
    async def get_conversation_stats(
        self,
        tenant_id: Union[str, uuid.UUID],
        user_id: str
    ) -> ConversationStats:
        """Get comprehensive conversation statistics."""
        try:
            async with self.db_client.get_async_session() as session:
                # Get all conversations for user
                result = await session.execute(
                    select(TenantConversation)
                    .where(TenantConversation.user_id == uuid.UUID(user_id))
                )
                
                conversations = result.scalars().all()
                
                stats = ConversationStats()
                stats.total_conversations = len(conversations)
                
                total_messages = 0
                folders = {}
                tags = {}
                templates = {}
                recent_activity = {}
                
                for conv in conversations:
                    metadata = conv.conversation_metadata or {}
                    
                    # Count by status
                    status = metadata.get("status", "active")
                    if status == "active":
                        stats.active_conversations += 1
                    elif status == "archived":
                        stats.archived_conversations += 1
                    
                    # Count favorites
                    if metadata.get("is_favorite", False):
                        stats.favorite_conversations += 1
                    
                    # Count messages
                    message_count = len(conv.messages or [])
                    total_messages += message_count
                    
                    # Count by folder
                    folder_id = metadata.get("folder_id", "none")
                    folders[folder_id] = folders.get(folder_id, 0) + 1
                    
                    # Count by tags
                    conv_tags = metadata.get("tags", [])
                    for tag in conv_tags:
                        tags[tag] = tags.get(tag, 0) + 1
                    
                    # Count by template
                    template_id = metadata.get("template_id", "none")
                    templates[template_id] = templates.get(template_id, 0) + 1
                    
                    # Recent activity (last 30 days)
                    if conv.updated_at:
                        date_key = conv.updated_at.strftime("%Y-%m-%d")
                        if (datetime.utcnow() - conv.updated_at).days <= 30:
                            recent_activity[date_key] = recent_activity.get(date_key, 0) + 1
                
                stats.total_messages = total_messages
                stats.avg_messages_per_conversation = (
                    total_messages / stats.total_conversations 
                    if stats.total_conversations > 0 else 0.0
                )
                stats.conversations_by_folder = folders
                stats.conversations_by_tag = tags
                stats.conversations_by_template = templates
                stats.recent_activity = recent_activity
                
                return stats
                
        except Exception as e:
            logger.error(f"Failed to get conversation stats: {e}")
            return ConversationStats()