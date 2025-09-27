"""
Enhanced Conversation Service for Web UI Integration.
Extends the existing ConversationManager with web UI specific features and context building.
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

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select, update, and_, or_, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from ai_karen_engine.database.conversation_manager import (
    ConversationManager,
    Conversation,
    Message,
    MessageRole,
    normalize_user_id,
)
from ai_karen_engine.database.models import TenantConversation
from ai_karen_engine.services.memory_service import (
    WebUIMemoryService,
    WebUIMemoryQuery,
    MemoryType,
    UISource,
)
from ai_karen_engine.database.client import MultiTenantPostgresClient

logger = logging.getLogger(__name__)


class ConversationStatus(str, Enum):
    """Conversation status for web UI."""
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"
    DELETED = "deleted"


class ConversationPriority(str, Enum):
    """Conversation priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class WebUIMessage(Message):
    """Extended message with web UI specific fields."""
    ui_source: Optional[UISource] = None
    ai_confidence: Optional[float] = None
    processing_time_ms: Optional[int] = None
    tokens_used: Optional[int] = None
    model_used: Optional[str] = None
    user_feedback: Optional[str] = None  # thumbs up/down, etc.
    edited: bool = False
    edit_history: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with web UI fields."""
        base_dict = super().to_dict()
        base_dict.update({
            "ui_source": self.ui_source.value if self.ui_source else None,
            "ai_confidence": self.ai_confidence,
            "processing_time_ms": self.processing_time_ms,
            "tokens_used": self.tokens_used,
            "model_used": self.model_used,
            "user_feedback": self.user_feedback,
            "edited": self.edited,
            "edit_history": self.edit_history
        })
        return base_dict


@dataclass
class WebUIConversation(Conversation):
    """Extended conversation with web UI specific fields."""
    session_id: Optional[str] = None
    ui_context: Dict[str, Any] = field(default_factory=dict)
    ai_insights: Dict[str, Any] = field(default_factory=dict)
    user_settings: Dict[str, Any] = field(default_factory=dict)
    summary: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    last_ai_response_id: Optional[str] = None
    status: ConversationStatus = ConversationStatus.ACTIVE
    priority: ConversationPriority = ConversationPriority.NORMAL
    context_memories: List[Dict[str, Any]] = field(default_factory=list)
    proactive_suggestions: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with web UI fields."""
        base_dict = super().to_dict()
        base_dict.update({
            "session_id": self.session_id,
            "ui_context": self.ui_context,
            "ai_insights": self.ai_insights,
            "user_settings": self.user_settings,
            "summary": self.summary,
            "tags": self.tags,
            "last_ai_response_id": self.last_ai_response_id,
            "status": self.status.value,
            "priority": self.priority.value,
            "context_memories": self.context_memories,
            "proactive_suggestions": self.proactive_suggestions
        })
        return base_dict
    
    def add_tag(self, tag: str):
        """Add a tag to the conversation."""
        if tag not in self.tags:
            self.tags.append(tag)
    
    def remove_tag(self, tag: str):
        """Remove a tag from the conversation."""
        if tag in self.tags:
            self.tags.remove(tag)
    
    def update_ui_context(self, context_data: dict):
        """Update UI context with new data."""
        self.ui_context.update(context_data)
    
    def update_ai_insights(self, insights_data: dict):
        """Update AI insights with new data."""
        self.ai_insights.update(insights_data)
    
    def get_context_summary(self) -> Dict[str, Any]:
        """Get a summary of conversation context for AI processing."""
        return {
            "conversation_id": self.id,
            "session_id": self.session_id,
            "message_count": len(self.messages),
            "tags": self.tags,
            "priority": self.priority.value,
            "status": self.status.value,
            "user_settings": self.user_settings,
            "recent_memories": self.context_memories[-5:] if self.context_memories else [],
            "ai_insights": self.ai_insights,
            "last_activity": self.updated_at.isoformat(),
            "summary": self.summary
        }


class ConversationContextBuilder:
    """Builds comprehensive conversation context for web UI."""
    
    def __init__(self, conversation_service: 'WebUIConversationService'):
        self.conversation_service = conversation_service
        self.memory_service = conversation_service.memory_service
        self.max_context_messages = 20
        self.max_context_memories = 10
        self.context_relevance_threshold = 0.7
    
    async def build_comprehensive_context(
        self,
        tenant_id: Union[str, uuid.UUID],
        conversation_id: str,
        current_message: str,
        include_memories: bool = True,
        include_insights: bool = True
    ) -> Dict[str, Any]:
        """Build comprehensive context for conversation processing."""
        try:
            # Get conversation
            conversation = await self.conversation_service.get_web_ui_conversation(
                tenant_id, conversation_id
            )
            if not conversation:
                return {"error": "Conversation not found"}
            
            # Build context components
            context = {
                "conversation_summary": conversation.get_context_summary(),
                "recent_messages": [],
                "relevant_memories": [],
                "ai_insights": conversation.ai_insights,
                "user_preferences": conversation.user_settings,
                "context_metadata": {
                    "built_at": datetime.utcnow().isoformat(),
                    "query": current_message,
                    "conversation_id": conversation_id
                }
            }
            
            # Add recent messages
            recent_messages = conversation.get_context_window(self.max_context_messages)
            context["recent_messages"] = [
                {
                    "role": msg.role.value,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat(),
                    "metadata": msg.metadata
                }
                for msg in recent_messages
            ]
            
            # Add relevant memories if requested
            if include_memories and self.memory_service:
                memory_context = await self._build_memory_context(
                    tenant_id, conversation, current_message
                )
                context["relevant_memories"] = memory_context
            
            # Add AI insights if requested
            if include_insights:
                insights_context = await self._build_insights_context(
                    tenant_id, conversation, current_message
                )
                context["ai_insights_context"] = insights_context
            
            # Add conversation patterns
            patterns = await self._analyze_conversation_patterns(conversation)
            context["conversation_patterns"] = patterns
            
            return context
            
        except Exception as e:
            logger.error(f"Failed to build comprehensive context: {e}")
            return {"error": str(e)}
    
    async def _build_memory_context(
        self,
        tenant_id: Union[str, uuid.UUID],
        conversation: WebUIConversation,
        current_message: str
    ) -> List[Dict[str, Any]]:
        """Build memory context for conversation."""
        try:
            # Query for relevant memories
            memory_query = WebUIMemoryQuery(
                text=current_message,
                user_id=conversation.user_id,
                conversation_id=conversation.id,
                top_k=self.max_context_memories,
                similarity_threshold=self.context_relevance_threshold
            )
            
            memories = await self.memory_service.query_memories(tenant_id, memory_query)
            
            # Group memories by type for better context organization
            memory_context = {
                "facts": [],
                "preferences": [],
                "insights": [],
                "general": []
            }
            
            for memory in memories:
                memory_data = {
                    "content": memory.content,
                    "similarity_score": memory.similarity_score,
                    "importance_score": memory.importance_score,
                    "timestamp": memory.timestamp,
                    "tags": memory.tags,
                    "memory_type": memory.memory_type.value
                }
                
                if memory.memory_type == MemoryType.FACT:
                    memory_context["facts"].append(memory_data)
                elif memory.memory_type == MemoryType.PREFERENCE:
                    memory_context["preferences"].append(memory_data)
                elif memory.memory_type == MemoryType.INSIGHT:
                    memory_context["insights"].append(memory_data)
                else:
                    memory_context["general"].append(memory_data)
            
            return memory_context
            
        except Exception as e:
            logger.error(f"Failed to build memory context: {e}")
            return []
    
    async def _build_insights_context(
        self,
        tenant_id: Union[str, uuid.UUID],
        conversation: WebUIConversation,
        current_message: str
    ) -> Dict[str, Any]:
        """Build AI insights context."""
        try:
            insights_context = {
                "conversation_insights": conversation.ai_insights,
                "message_patterns": [],
                "user_behavior": {},
                "conversation_flow": {}
            }
            
            # Analyze message patterns
            if conversation.messages:
                insights_context["message_patterns"] = self._analyze_message_patterns(
                    conversation.messages
                )
            
            # Analyze user behavior
            insights_context["user_behavior"] = self._analyze_user_behavior(
                conversation.messages
            )
            
            # Analyze conversation flow
            insights_context["conversation_flow"] = self._analyze_conversation_flow(
                conversation.messages
            )
            
            return insights_context
            
        except Exception as e:
            logger.error(f"Failed to build insights context: {e}")
            return {}
    
    async def _analyze_conversation_patterns(
        self,
        conversation: WebUIConversation
    ) -> Dict[str, Any]:
        """Analyze conversation patterns for context."""
        try:
            patterns = {
                "message_frequency": {},
                "topic_shifts": [],
                "engagement_level": "medium",
                "conversation_style": "balanced"
            }
            
            if not conversation.messages:
                return patterns
            
            # Analyze message frequency by hour
            message_hours = {}
            for msg in conversation.messages:
                hour = msg.timestamp.hour
                message_hours[hour] = message_hours.get(hour, 0) + 1
            
            patterns["message_frequency"] = message_hours
            
            # Analyze engagement level based on message length and frequency
            user_messages = [m for m in conversation.messages if m.role == MessageRole.USER]
            if user_messages:
                avg_length = sum(len(m.content) for m in user_messages) / len(user_messages)
                if avg_length > 100:
                    patterns["engagement_level"] = "high"
                elif avg_length < 30:
                    patterns["engagement_level"] = "low"
            
            # Analyze conversation style
            question_count = sum(1 for m in user_messages if "?" in m.content)
            if question_count > len(user_messages) * 0.6:
                patterns["conversation_style"] = "inquisitive"
            elif any(word in m.content.lower() for m in user_messages for word in ["please", "thank", "sorry"]):
                patterns["conversation_style"] = "polite"
            
            return patterns
            
        except Exception as e:
            logger.error(f"Failed to analyze conversation patterns: {e}")
            return {}
    
    def _analyze_message_patterns(self, messages: List[Message]) -> List[Dict[str, Any]]:
        """Analyze patterns in messages."""
        patterns = []
        
        if len(messages) < 2:
            return patterns
        
        # Analyze response times
        response_times = []
        for i in range(1, len(messages)):
            if messages[i-1].role == MessageRole.USER and messages[i].role == MessageRole.ASSISTANT:
                time_diff = (messages[i].timestamp - messages[i-1].timestamp).total_seconds()
                response_times.append(time_diff)
        
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            patterns.append({
                "type": "response_time",
                "average_seconds": avg_response_time,
                "pattern": "fast" if avg_response_time < 5 else "normal" if avg_response_time < 15 else "slow"
            })
        
        # Analyze message length patterns
        user_messages = [m for m in messages if m.role == MessageRole.USER]
        if user_messages:
            lengths = [len(m.content) for m in user_messages]
            avg_length = sum(lengths) / len(lengths)
            patterns.append({
                "type": "message_length",
                "average_length": avg_length,
                "pattern": "verbose" if avg_length > 100 else "concise" if avg_length < 30 else "balanced"
            })
        
        return patterns
    
    def _analyze_user_behavior(self, messages: List[Message]) -> Dict[str, Any]:
        """Analyze user behavior patterns."""
        behavior = {
            "interaction_style": "balanced",
            "question_frequency": 0,
            "politeness_level": "neutral",
            "topic_consistency": "consistent"
        }
        
        user_messages = [m for m in messages if m.role == MessageRole.USER]
        if not user_messages:
            return behavior
        
        # Analyze question frequency
        question_count = sum(1 for m in user_messages if "?" in m.content)
        behavior["question_frequency"] = question_count / len(user_messages)
        
        # Analyze politeness
        polite_words = ["please", "thank", "sorry", "excuse", "pardon"]
        polite_count = sum(1 for m in user_messages for word in polite_words if word in m.content.lower())
        if polite_count > len(user_messages) * 0.3:
            behavior["politeness_level"] = "high"
        elif polite_count > 0:
            behavior["politeness_level"] = "moderate"
        
        # Analyze interaction style
        if behavior["question_frequency"] > 0.6:
            behavior["interaction_style"] = "inquisitive"
        elif any(len(m.content) > 200 for m in user_messages):
            behavior["interaction_style"] = "detailed"
        elif all(len(m.content) < 50 for m in user_messages):
            behavior["interaction_style"] = "concise"
        
        return behavior
    
    def _analyze_conversation_flow(self, messages: List[Message]) -> Dict[str, Any]:
        """Analyze conversation flow patterns."""
        flow = {
            "continuity": "good",
            "topic_changes": 0,
            "flow_quality": "smooth",
            "engagement_trend": "stable"
        }
        
        if len(messages) < 3:
            return flow
        
        # Simple topic change detection (in production, use more sophisticated NLP)
        user_messages = [m for m in messages if m.role == MessageRole.USER]
        topic_changes = 0
        
        for i in range(1, len(user_messages)):
            # Simple heuristic: if messages share few common words, it might be a topic change
            prev_words = set(user_messages[i-1].content.lower().split())
            curr_words = set(user_messages[i].content.lower().split())
            
            # Remove common stop words for better analysis
            stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by", "is", "are", "was", "were", "be", "been", "have", "has", "had", "do", "does", "did", "will", "would", "could", "should", "may", "might", "can", "i", "you", "he", "she", "it", "we", "they", "me", "him", "her", "us", "them", "my", "your", "his", "her", "its", "our", "their"}
            prev_words -= stop_words
            curr_words -= stop_words
            
            if len(prev_words & curr_words) / max(len(prev_words | curr_words), 1) < 0.2:
                topic_changes += 1
        
        flow["topic_changes"] = topic_changes
        
        if topic_changes > len(user_messages) * 0.5:
            flow["continuity"] = "fragmented"
            flow["flow_quality"] = "choppy"
        elif topic_changes == 0:
            flow["continuity"] = "excellent"
            flow["flow_quality"] = "very_smooth"
        
        return flow


class WebUIConversationService:
    """Enhanced conversation service with web UI specific features."""
    
    def __init__(
        self,
        base_conversation_manager: ConversationManager,
        memory_service: WebUIMemoryService
    ):
        """Initialize with existing conversation manager and memory service."""
        self.base_manager = base_conversation_manager
        self.memory_service = memory_service
        self.db_client = base_conversation_manager.db_client
        self.context_builder = ConversationContextBuilder(self)
        
        # Web UI specific configuration
        self.auto_summarize_threshold = 50  # messages
        self.proactive_suggestion_enabled = True
        self.context_memory_integration = True
        
        # Enhanced web UI session tracking
        self.session_timeout_minutes = 60  # Session timeout
        self.max_sessions_per_user = 10  # Max concurrent sessions
        self.session_cleanup_interval = 300  # Cleanup every 5 minutes
        
        # Web UI context tracking configuration
        self.context_retention_days = 30  # How long to keep context data
        self.max_context_size_mb = 10  # Max context size per conversation
        self.context_compression_enabled = True
        
        # Performance metrics
        self.web_ui_metrics = {
            "web_ui_conversations_created": 0,
            "context_builds": 0,
            "summaries_generated": 0,
            "proactive_suggestions_generated": 0,
            "ui_context_updates": 0,
            "session_tracking_updates": 0,
            "context_tracking_updates": 0,
            "session_cleanups": 0
        }
        
        # Session tracking cache
        self.active_sessions = {}  # session_id -> session_data
        self.user_sessions = {}  # user_id -> [session_ids]
    
    async def create_web_ui_conversation(
        self,
        tenant_id: Union[str, uuid.UUID],
        user_id: str,
        session_id: str,
        ui_source: UISource,
        title: Optional[str] = None,
        initial_message: Optional[str] = None,
        user_settings: Optional[Dict[str, Any]] = None,
        ui_context: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        priority: ConversationPriority = ConversationPriority.NORMAL
    ) -> Optional[WebUIConversation]:
        """Create a new conversation with web UI features."""
        try:
            # Create base conversation
            base_conversation = await self.base_manager.create_conversation(
                tenant_id=tenant_id,
                user_id=user_id,
                title=title,
                initial_message=initial_message,
                metadata={
                    "ui_source": ui_source.value,
                    "session_id": session_id,
                    "user_settings": user_settings or {},
                    "ui_context": ui_context or {},
                    "tags": tags or [],
                    "priority": priority.value
                }
            )
            
            if not base_conversation:
                return None
            
            # Update database with web UI specific fields
            await self._update_web_ui_conversation_fields(
                tenant_id, base_conversation.id, session_id, ui_context or {}, 
                user_settings or {}, tags or []
            )
            
            # Convert to WebUIConversation
            web_ui_conversation = await self._convert_to_web_ui_conversation(
                base_conversation, session_id, ui_context or {}, 
                user_settings or {}, tags or [], priority
            )
            
            # Store initial message in memory if provided
            if initial_message and self.context_memory_integration:
                await self.memory_service.store_web_ui_memory(
                    tenant_id=tenant_id,
                    content=initial_message,
                    user_id=user_id,
                    ui_source=ui_source,
                    session_id=session_id,
                    conversation_id=base_conversation.id,
                    memory_type=MemoryType.CONVERSATION,
                    tags=["conversation_start"] + (tags or [])
                )
            
            self.web_ui_metrics["web_ui_conversations_created"] += 1
            
            return web_ui_conversation
            
        except Exception as e:
            logger.error(f"Failed to create web UI conversation: {e}")
            return None
    
    async def get_web_ui_conversation(
        self,
        tenant_id: Union[str, uuid.UUID],
        conversation_id: str,
        include_context: bool = True,
        user_id: Optional[str] = None,
    ) -> Optional[WebUIConversation]:
        """Get conversation with web UI features."""
        try:
            # Get base conversation
            base_conversation = await self.base_manager.get_conversation(
                tenant_id, conversation_id, include_context=False
            )

            if not base_conversation:
                return None

            # Enforce ownership when requested
            if user_id:
                expected_user_id = str(normalize_user_id(user_id))
                if str(base_conversation.user_id) != expected_user_id:
                    logger.warning(
                        "User %s attempted to access conversation %s they do not own",
                        user_id,
                        conversation_id,
                    )
                    return None

            # Get web UI specific data
            web_ui_data = await self._get_web_ui_conversation_data(tenant_id, conversation_id)

            # Convert to WebUIConversation
            web_ui_conversation = await self._convert_to_web_ui_conversation(
                base_conversation,
                web_ui_data.get("session_id"),
                web_ui_data.get("ui_context", {}),
                web_ui_data.get("user_settings", {}),
                web_ui_data.get("tags", []),
                ConversationPriority(web_ui_data.get("priority", "normal")),
                web_ui_data.get("summary"),
                web_ui_data.get("last_ai_response_id")
            )
            
            # Add context if requested
            if include_context and self.context_memory_integration:
                await self._add_web_ui_context(tenant_id, web_ui_conversation)
            
            return web_ui_conversation

        except Exception as e:
            logger.error(f"Failed to get web UI conversation: {e}")
            return None

    async def get_web_ui_conversation_by_session(
        self,
        tenant_id: Union[str, uuid.UUID],
        session_id: str,
        user_id: Optional[str] = None,
        include_context: bool = True,
    ) -> Optional[WebUIConversation]:
        """Lookup a conversation using its tracked session identifier."""

        try:
            async with self.db_client.get_async_session() as session:
                query = select(TenantConversation).where(
                    TenantConversation.session_id == session_id
                )

                if user_id:
                    query = query.where(
                        TenantConversation.user_id == normalize_user_id(user_id)
                    )

                result = await session.execute(query)
                db_conversation = result.scalar_one_or_none()

            if not db_conversation:
                return None

            return await self.get_web_ui_conversation(
                tenant_id,
                str(db_conversation.id),
                include_context=include_context,
                user_id=user_id,
            )

        except Exception as e:
            logger.error(
                "Failed to get conversation by session %s: %s", session_id, e
            )
            return None
    
    async def add_web_ui_message(
        self,
        tenant_id: Union[str, uuid.UUID],
        conversation_id: str,
        role: MessageRole,
        content: str,
        ui_source: UISource,
        metadata: Optional[Dict[str, Any]] = None,
        ai_confidence: Optional[float] = None,
        processing_time_ms: Optional[int] = None,
        tokens_used: Optional[int] = None,
        model_used: Optional[str] = None
    ) -> Optional[WebUIMessage]:
        """Add a message with web UI specific features."""
        try:
            # Prepare web UI metadata
            web_ui_metadata = {
                "ui_source": ui_source.value,
                "ai_confidence": ai_confidence,
                "processing_time_ms": processing_time_ms,
                "tokens_used": tokens_used,
                "model_used": model_used
            }
            
            if metadata:
                web_ui_metadata.update(metadata)
            
            # Add message using base manager
            base_message = await self.base_manager.add_message(
                tenant_id=tenant_id,
                conversation_id=conversation_id,
                role=role,
                content=content,
                metadata=web_ui_metadata
            )
            
            if not base_message:
                return None
            
            # Convert to WebUIMessage
            web_ui_message = WebUIMessage(
                id=base_message.id,
                role=base_message.role,
                content=base_message.content,
                timestamp=base_message.timestamp,
                metadata=base_message.metadata,
                function_call=base_message.function_call,
                function_response=base_message.function_response,
                ui_source=ui_source,
                ai_confidence=ai_confidence,
                processing_time_ms=processing_time_ms,
                tokens_used=tokens_used,
                model_used=model_used
            )
            
            # Store in memory if it's a user message
            if role == MessageRole.USER and self.context_memory_integration:
                await self.memory_service.store_web_ui_memory(
                    tenant_id=tenant_id,
                    content=content,
                    user_id=base_message.metadata.get("user_id"),  # This should be available from conversation
                    ui_source=ui_source,
                    conversation_id=conversation_id,
                    memory_type=MemoryType.CONVERSATION,
                    tags=["user_message"],
                    metadata={"message_id": base_message.id}
                )
            
            # Generate proactive suggestions if enabled
            if self.proactive_suggestion_enabled and role == MessageRole.USER:
                await self._generate_proactive_suggestions(tenant_id, conversation_id, content)
            
            # Auto-summarize if threshold reached
            conversation = await self.get_web_ui_conversation(tenant_id, conversation_id, include_context=False)
            if conversation and len(conversation.messages) >= self.auto_summarize_threshold:
                await self._generate_web_ui_summary(tenant_id, conversation_id)
            
            return web_ui_message
            
        except Exception as e:
            logger.error(f"Failed to add web UI message: {e}")
            return None
    
    async def build_conversation_context(
        self,
        tenant_id: Union[str, uuid.UUID],
        conversation_id: str,
        current_message: str,
        include_memories: bool = True,
        include_insights: bool = True
    ) -> Dict[str, Any]:
        """Build comprehensive conversation context."""
        self.web_ui_metrics["context_builds"] += 1
        return await self.context_builder.build_comprehensive_context(
            tenant_id, conversation_id, current_message, include_memories, include_insights
        )
    
    async def update_conversation_ui_context(
        self,
        tenant_id: Union[str, uuid.UUID],
        conversation_id: str,
        ui_context: Dict[str, Any]
    ) -> bool:
        """Update conversation UI context."""
        try:
            async with self.db_client.get_async_session() as session:
                await session.execute(
                    update(TenantConversation)
                    .where(TenantConversation.id == uuid.UUID(conversation_id))
                    .values(ui_context=ui_context, updated_at=datetime.utcnow())
                )
                await session.commit()
                
                self.web_ui_metrics["ui_context_updates"] += 1
                return True
                
        except Exception as e:
            logger.error(f"Failed to update UI context: {e}")
            return False
    
    async def update_conversation_ai_insights(
        self,
        tenant_id: Union[str, uuid.UUID],
        conversation_id: str,
        ai_insights: Dict[str, Any]
    ) -> bool:
        """Update conversation AI insights."""
        try:
            async with self.db_client.get_async_session() as session:
                await session.execute(
                    update(TenantConversation)
                    .where(TenantConversation.id == uuid.UUID(conversation_id))
                    .values(ai_insights=ai_insights, updated_at=datetime.utcnow())
                )
                await session.commit()
                return True
                
        except Exception as e:
            logger.error(f"Failed to update AI insights: {e}")
            return False
    
    # Enhanced Web UI Session Tracking Methods
    
    async def track_web_ui_session(
        self,
        tenant_id: Union[str, uuid.UUID],
        user_id: str,
        session_id: str,
        ui_source: UISource,
        session_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Track web UI session with enhanced metadata."""
        try:
            session_info = {
                "session_id": session_id,
                "user_id": user_id,
                "ui_source": ui_source.value,
                "created_at": datetime.utcnow(),
                "last_activity": datetime.utcnow(),
                "data": session_data or {},
                "active": True
            }
            
            # Store in cache for quick access
            self.active_sessions[session_id] = session_info
            
            # Track user sessions
            if user_id not in self.user_sessions:
                self.user_sessions[user_id] = []
            
            if session_id not in self.user_sessions[user_id]:
                self.user_sessions[user_id].append(session_id)
            
            # Enforce max sessions per user
            if len(self.user_sessions[user_id]) > self.max_sessions_per_user:
                oldest_session = self.user_sessions[user_id].pop(0)
                await self._cleanup_session(oldest_session)
            
            # Update database with session tracking
            async with self.db_client.get_async_session() as session:
                # Update all conversations for this session with session tracking data
                normalized_user_id = normalize_user_id(user_id)

                await session.execute(
                    update(TenantConversation)
                    .where(
                        and_(
                            TenantConversation.session_id == session_id,
                            TenantConversation.user_id == normalized_user_id,
                        )
                    )
                    .values(
                        ui_context=func.jsonb_set(
                            TenantConversation.ui_context,
                            '{session_tracking}',
                            json.dumps({
                                "last_activity": datetime.utcnow().isoformat(),
                                "ui_source": ui_source.value,
                                "session_data": session_data or {}
                            })
                        ),
                        updated_at=datetime.utcnow()
                    )
                )
                await session.commit()
            
            self.web_ui_metrics["session_tracking_updates"] += 1
            return True
            
        except Exception as e:
            logger.error(f"Failed to track web UI session: {e}")
            return False
    
    async def update_session_activity(
        self,
        session_id: str,
        activity_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update session activity timestamp and data."""
        try:
            if session_id in self.active_sessions:
                self.active_sessions[session_id]["last_activity"] = datetime.utcnow()
                if activity_data:
                    self.active_sessions[session_id]["data"].update(activity_data)
                
                # Update database
                async with self.db_client.get_async_session() as session:
                    await session.execute(
                        update(TenantConversation)
                        .where(TenantConversation.session_id == session_id)
                        .values(
                            ui_context=func.jsonb_set(
                                TenantConversation.ui_context,
                                '{session_tracking,last_activity}',
                                json.dumps(datetime.utcnow().isoformat())
                            ),
                            updated_at=datetime.utcnow()
                        )
                    )
                    await session.commit()
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to update session activity: {e}")
            return False
    
    async def get_user_active_sessions(
        self,
        user_id: str
    ) -> List[Dict[str, Any]]:
        """Get all active sessions for a user."""
        try:
            user_sessions = []
            
            if user_id in self.user_sessions:
                for session_id in self.user_sessions[user_id]:
                    if session_id in self.active_sessions:
                        session_info = self.active_sessions[session_id].copy()
                        
                        # Check if session is still active (not timed out)
                        last_activity = session_info["last_activity"]
                        timeout_threshold = datetime.utcnow() - timedelta(minutes=self.session_timeout_minutes)
                        
                        if last_activity > timeout_threshold:
                            user_sessions.append(session_info)
                        else:
                            # Session timed out, clean it up
                            await self._cleanup_session(session_id)
            
            return user_sessions
            
        except Exception as e:
            logger.error(f"Failed to get user active sessions: {e}")
            return []
    
    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions."""
        try:
            cleaned_count = 0
            timeout_threshold = datetime.utcnow() - timedelta(minutes=self.session_timeout_minutes)
            
            expired_sessions = []
            for session_id, session_info in self.active_sessions.items():
                if session_info["last_activity"] < timeout_threshold:
                    expired_sessions.append(session_id)
            
            for session_id in expired_sessions:
                await self._cleanup_session(session_id)
                cleaned_count += 1
            
            self.web_ui_metrics["session_cleanups"] += cleaned_count
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup expired sessions: {e}")
            return 0
    
    async def _cleanup_session(self, session_id: str) -> bool:
        """Clean up a specific session."""
        try:
            # Remove from cache
            if session_id in self.active_sessions:
                user_id = self.active_sessions[session_id]["user_id"]
                del self.active_sessions[session_id]
                
                # Remove from user sessions
                if user_id in self.user_sessions and session_id in self.user_sessions[user_id]:
                    self.user_sessions[user_id].remove(session_id)
                    
                    # Clean up empty user session lists
                    if not self.user_sessions[user_id]:
                        del self.user_sessions[user_id]
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to cleanup session {session_id}: {e}")
            return False
    
    # Enhanced Web UI Context Tracking Methods
    
    async def track_web_ui_context(
        self,
        tenant_id: Union[str, uuid.UUID],
        conversation_id: str,
        context_type: str,
        context_data: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> bool:
        """Track web UI context with enhanced metadata and compression."""
        try:
            # Prepare context tracking data
            context_entry = {
                "type": context_type,
                "data": context_data,
                "timestamp": datetime.utcnow().isoformat(),
                "user_id": user_id,
                "size_bytes": len(json.dumps(context_data))
            }
            
            # Check context size limits
            if self._check_context_size_limit(context_entry["size_bytes"]):
                if self.context_compression_enabled:
                    context_entry = await self._compress_context_data(context_entry)
                else:
                    logger.warning(f"Context data too large for conversation {conversation_id}")
                    return False
            
            # Update database with context tracking
            async with self.db_client.get_async_session() as session:
                # Get current ui_context
                result = await session.execute(
                    select(TenantConversation.ui_context)
                    .where(TenantConversation.id == uuid.UUID(conversation_id))
                )
                current_context = result.scalar_one_or_none() or {}
                
                # Initialize context tracking if not exists
                if "context_tracking" not in current_context:
                    current_context["context_tracking"] = {
                        "entries": [],
                        "total_size_bytes": 0,
                        "last_updated": datetime.utcnow().isoformat()
                    }
                
                # Add new context entry
                current_context["context_tracking"]["entries"].append(context_entry)
                current_context["context_tracking"]["total_size_bytes"] += context_entry["size_bytes"]
                current_context["context_tracking"]["last_updated"] = datetime.utcnow().isoformat()
                
                # Cleanup old context entries if needed
                current_context = await self._cleanup_old_context_entries(current_context)
                
                # Update database
                await session.execute(
                    update(TenantConversation)
                    .where(TenantConversation.id == uuid.UUID(conversation_id))
                    .values(
                        ui_context=current_context,
                        updated_at=datetime.utcnow()
                    )
                )
                await session.commit()
            
            self.web_ui_metrics["context_tracking_updates"] += 1
            return True
            
        except Exception as e:
            logger.error(f"Failed to track web UI context: {e}")
            return False
    
    async def get_conversation_context_history(
        self,
        tenant_id: Union[str, uuid.UUID],
        conversation_id: str,
        context_type: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get conversation context tracking history."""
        try:
            async with self.db_client.get_async_session() as session:
                result = await session.execute(
                    select(TenantConversation.ui_context)
                    .where(TenantConversation.id == uuid.UUID(conversation_id))
                )
                ui_context = result.scalar_one_or_none() or {}
                
                context_tracking = ui_context.get("context_tracking", {})
                entries = context_tracking.get("entries", [])
                
                # Filter by context type if specified
                if context_type:
                    entries = [e for e in entries if e.get("type") == context_type]
                
                # Sort by timestamp (newest first) and limit
                entries.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
                return entries[:limit]
                
        except Exception as e:
            logger.error(f"Failed to get context history: {e}")
            return []
    
    def _check_context_size_limit(self, size_bytes: int) -> bool:
        """Check if context size exceeds limits."""
        max_size_bytes = self.max_context_size_mb * 1024 * 1024
        return size_bytes > max_size_bytes
    
    async def _compress_context_data(self, context_entry: Dict[str, Any]) -> Dict[str, Any]:
        """Compress context data if it's too large."""
        try:
            import gzip
            import base64
            
            # Compress the data
            original_data = json.dumps(context_entry["data"])
            compressed_data = gzip.compress(original_data.encode('utf-8'))
            encoded_data = base64.b64encode(compressed_data).decode('utf-8')
            
            # Update context entry
            context_entry["data"] = {
                "compressed": True,
                "data": encoded_data,
                "original_size": len(original_data)
            }
            context_entry["size_bytes"] = len(encoded_data)
            context_entry["compressed"] = True
            
            return context_entry
            
        except Exception as e:
            logger.error(f"Failed to compress context data: {e}")
            return context_entry
    
    async def _cleanup_old_context_entries(self, ui_context: Dict[str, Any]) -> Dict[str, Any]:
        """Clean up old context entries based on retention policy."""
        try:
            context_tracking = ui_context.get("context_tracking", {})
            entries = context_tracking.get("entries", [])
            
            if not entries:
                return ui_context
            
            # Calculate retention cutoff
            retention_cutoff = datetime.utcnow() - timedelta(days=self.context_retention_days)
            
            # Filter out old entries
            filtered_entries = []
            total_size = 0
            
            for entry in entries:
                entry_time = datetime.fromisoformat(entry.get("timestamp", ""))
                if entry_time > retention_cutoff:
                    filtered_entries.append(entry)
                    total_size += entry.get("size_bytes", 0)
            
            # Update context tracking
            context_tracking["entries"] = filtered_entries
            context_tracking["total_size_bytes"] = total_size
            ui_context["context_tracking"] = context_tracking
            
            return ui_context
            
        except Exception as e:
            logger.error(f"Failed to cleanup old context entries: {e}")
            return ui_context
    
    # Integration with existing TenantConversation model
    
    async def integrate_with_tenant_conversation(
        self,
        tenant_id: Union[str, uuid.UUID],
        conversation_id: str,
        session_id: str,
        ui_context: Dict[str, Any],
        user_settings: Dict[str, Any]
    ) -> bool:
        """Integrate web UI context tracking with existing TenantConversation model."""
        try:
            async with self.db_client.get_async_session() as session:
                # Update TenantConversation with enhanced web UI integration
                await session.execute(
                    update(TenantConversation)
                    .where(TenantConversation.id == uuid.UUID(conversation_id))
                    .values(
                        session_id=session_id,
                        ui_context=ui_context,
                        user_settings=user_settings,
                        updated_at=datetime.utcnow()
                    )
                )
                await session.commit()
                
                return True
                
        except Exception as e:
            logger.error(f"Failed to update AI insights: {e}")
            return False
    
    async def add_conversation_tags(
        self,
        tenant_id: Union[str, uuid.UUID],
        conversation_id: str,
        tags: List[str]
    ) -> bool:
        """Add tags to conversation."""
        try:
            conversation = await self.get_web_ui_conversation(tenant_id, conversation_id, include_context=False)
            if not conversation:
                return False
            
            # Merge with existing tags
            existing_tags = set(conversation.tags)
            new_tags = existing_tags.union(set(tags))
            
            async with self.db_client.get_async_session() as session:
                await session.execute(
                    update(TenantConversation)
                    .where(TenantConversation.id == uuid.UUID(conversation_id))
                    .values(tags=list(new_tags), updated_at=datetime.utcnow())
                )
                await session.commit()
                return True
                
        except Exception as e:
            logger.error(f"Failed to add conversation tags: {e}")
            return False
    
    async def get_conversation_analytics(
        self,
        tenant_id: Union[str, uuid.UUID],
        user_id: Optional[str] = None,
        time_range: Optional[Tuple[datetime, datetime]] = None
    ) -> Dict[str, Any]:
        """Get conversation analytics for web UI dashboard."""
        try:
            base_stats = await self.base_manager.get_conversation_stats(tenant_id, user_id)
            
            # Add web UI specific analytics
            async with self.db_client.get_async_session() as session:
                # Base query conditions
                query_conditions = []
                if user_id:
                query_conditions.append(
                    TenantConversation.user_id == normalize_user_id(user_id)
                )
                if time_range:
                    query_conditions.append(TenantConversation.created_at >= time_range[0])
                    query_conditions.append(TenantConversation.created_at <= time_range[1])
                
                base_query = select(TenantConversation)
                if query_conditions:
                    base_query = base_query.where(and_(*query_conditions))
                
                # Get all conversations for analysis
                result = await session.execute(base_query)
                conversations = result.fetchall()
                
                # Analyze web UI specific metrics
                analytics = {
                    **base_stats,
                    "conversations_by_ui_source": {},
                    "conversations_by_priority": {},
                    "conversations_with_tags": 0,
                    "average_tags_per_conversation": 0,
                    "conversations_with_summaries": 0,
                    "most_common_tags": {},
                    "web_ui_metrics": self.web_ui_metrics.copy()
                }
                
                if conversations:
                    total_tags = 0
                    tag_frequency = {}
                    
                    for conv in conversations:
                        # UI source distribution
                        ui_source = conv.ui_context.get("ui_source", "unknown") if conv.ui_context else "unknown"
                        analytics["conversations_by_ui_source"][ui_source] = analytics["conversations_by_ui_source"].get(ui_source, 0) + 1
                        
                        # Priority distribution (if available in metadata)
                        priority = conv.conversation_metadata.get("priority", "normal") if conv.conversation_metadata else "normal"
                        analytics["conversations_by_priority"][priority] = analytics["conversations_by_priority"].get(priority, 0) + 1
                        
                        # Tag analysis
                        if conv.tags:
                            analytics["conversations_with_tags"] += 1
                            total_tags += len(conv.tags)
                            for tag in conv.tags:
                                tag_frequency[tag] = tag_frequency.get(tag, 0) + 1
                        
                        # Summary analysis
                        if conv.summary:
                            analytics["conversations_with_summaries"] += 1
                    
                    analytics["average_tags_per_conversation"] = total_tags / len(conversations)
                    analytics["most_common_tags"] = dict(sorted(tag_frequency.items(), key=lambda x: x[1], reverse=True)[:10])
                
                return analytics
                
        except Exception as e:
            logger.error(f"Failed to get conversation analytics: {e}")
            return {"error": str(e)}
    
    async def _update_web_ui_conversation_fields(
        self,
        tenant_id: Union[str, uuid.UUID],
        conversation_id: str,
        session_id: str,
        ui_context: Dict[str, Any],
        user_settings: Dict[str, Any],
        tags: List[str]
    ):
        """Update database with web UI specific fields."""
        try:
            async with self.db_client.get_async_session() as session:
                await session.execute(
                    update(TenantConversation)
                    .where(TenantConversation.id == uuid.UUID(conversation_id))
                    .values(
                        session_id=session_id,
                        ui_context=ui_context,
                        user_settings=user_settings,
                        tags=tags,
                        updated_at=datetime.utcnow()
                    )
                )
                await session.commit()
                
        except Exception as e:
            logger.error(f"Failed to update web UI conversation fields: {e}")
    
    async def _get_web_ui_conversation_data(
        self,
        tenant_id: Union[str, uuid.UUID],
        conversation_id: str
    ) -> Dict[str, Any]:
        """Get web UI specific data for conversation."""
        try:
            async with self.db_client.get_async_session() as session:
                result = await session.execute(
                    select(TenantConversation)
                    .where(TenantConversation.id == uuid.UUID(conversation_id))
                )
                
                conversation = result.scalar_one_or_none()
                if conversation:
                    return {
                        "session_id": conversation.session_id,
                        "ui_context": conversation.ui_context or {},
                        "ai_insights": conversation.ai_insights or {},
                        "user_settings": conversation.user_settings or {},
                        "summary": conversation.summary,
                        "tags": conversation.tags or [],
                        "last_ai_response_id": conversation.last_ai_response_id,
                        "priority": conversation.conversation_metadata.get("priority", "normal") if conversation.conversation_metadata else "normal"
                    }
                
                return {}
                
        except Exception as e:
            logger.error(f"Failed to get web UI conversation data: {e}")
            return {}
    
    async def _convert_to_web_ui_conversation(
        self,
        base_conversation: Conversation,
        session_id: Optional[str] = None,
        ui_context: Dict[str, Any] = None,
        user_settings: Dict[str, Any] = None,
        tags: List[str] = None,
        priority: ConversationPriority = ConversationPriority.NORMAL,
        summary: Optional[str] = None,
        last_ai_response_id: Optional[str] = None
    ) -> WebUIConversation:
        """Convert base conversation to WebUIConversation."""
        # Convert messages to WebUIMessage
        web_ui_messages = []
        for msg in base_conversation.messages:
            web_ui_msg = WebUIMessage(
                id=msg.id,
                role=msg.role,
                content=msg.content,
                timestamp=msg.timestamp,
                metadata=msg.metadata,
                function_call=msg.function_call,
                function_response=msg.function_response,
                ui_source=UISource(msg.metadata.get("ui_source", "api")) if msg.metadata.get("ui_source") else None,
                ai_confidence=msg.metadata.get("ai_confidence"),
                processing_time_ms=msg.metadata.get("processing_time_ms"),
                tokens_used=msg.metadata.get("tokens_used"),
                model_used=msg.metadata.get("model_used")
            )
            web_ui_messages.append(web_ui_msg)
        
        return WebUIConversation(
            id=base_conversation.id,
            user_id=base_conversation.user_id,
            title=base_conversation.title,
            messages=web_ui_messages,
            metadata=base_conversation.metadata,
            is_active=base_conversation.is_active,
            created_at=base_conversation.created_at,
            updated_at=base_conversation.updated_at,
            session_id=session_id,
            ui_context=ui_context or {},
            ai_insights={},  # Will be populated by _add_web_ui_context
            user_settings=user_settings or {},
            summary=summary,
            tags=tags or [],
            last_ai_response_id=last_ai_response_id,
            priority=priority
        )
    
    async def _add_web_ui_context(
        self,
        tenant_id: Union[str, uuid.UUID],
        conversation: WebUIConversation
    ):
        """Add web UI specific context to conversation."""
        try:
            if not conversation.messages:
                return
            
            # Get last user message for context
            last_user_message = None
            for msg in reversed(conversation.messages):
                if msg.role == MessageRole.USER:
                    last_user_message = msg
                    break
            
            if not last_user_message:
                return
            
            # Build memory context
            if self.context_memory_integration:
                memory_context = await self.memory_service.build_conversation_context(
                    tenant_id=tenant_id,
                    query=last_user_message.content,
                    user_id=conversation.user_id,
                    session_id=conversation.session_id,
                    conversation_id=conversation.id
                )
                
                conversation.context_memories = memory_context.get("memories", [])
            
        except Exception as e:
            logger.error(f"Failed to add web UI context: {e}")
    
    async def _generate_proactive_suggestions(
        self,
        tenant_id: Union[str, uuid.UUID],
        conversation_id: str,
        user_message: str
    ):
        """Generate proactive suggestions based on user message."""
        try:
            # This is a simplified implementation
            # In production, you would use LLM to generate contextual suggestions
            suggestions = []
            
            # Simple keyword-based suggestions
            if "weather" in user_message.lower():
                suggestions.append("Would you like me to check the weather forecast for tomorrow?")
            elif "remind" in user_message.lower():
                suggestions.append("Should I set up a reminder for you?")
            elif "schedule" in user_message.lower():
                suggestions.append("Would you like me to help you manage your calendar?")
            
            if suggestions:
                # Update conversation with suggestions
                async with self.db_client.get_async_session() as session:
                    # Get current ai_insights
                    result = await session.execute(
                        select(TenantConversation.ai_insights)
                        .where(TenantConversation.id == uuid.UUID(conversation_id))
                    )
                    current_insights = result.scalar() or {}
                    
                    # Add suggestions
                    current_insights["proactive_suggestions"] = suggestions
                    current_insights["suggestions_generated_at"] = datetime.utcnow().isoformat()
                    
                    await session.execute(
                        update(TenantConversation)
                        .where(TenantConversation.id == uuid.UUID(conversation_id))
                        .values(ai_insights=current_insights)
                    )
                    await session.commit()
                    
                    self.web_ui_metrics["proactive_suggestions_generated"] += 1
            
        except Exception as e:
            logger.error(f"Failed to generate proactive suggestions: {e}")
    
    async def _generate_web_ui_summary(
        self,
        tenant_id: Union[str, uuid.UUID],
        conversation_id: str
    ):
        """Generate conversation summary for web UI."""
        try:
            conversation = await self.get_web_ui_conversation(tenant_id, conversation_id, include_context=False)
            if not conversation:
                return
            
            # Simple summary generation (in production, use LLM)
            user_messages = [m for m in conversation.messages if m.role == MessageRole.USER]
            assistant_messages = [m for m in conversation.messages if m.role == MessageRole.ASSISTANT]
            
            summary = f"Conversation with {len(conversation.messages)} messages ({len(user_messages)} from user, {len(assistant_messages)} from assistant)"
            
            if conversation.tags:
                summary += f". Topics: {', '.join(conversation.tags)}"
            
            # Update conversation with summary
            async with self.db_client.get_async_session() as session:
                await session.execute(
                    update(TenantConversation)
                    .where(TenantConversation.id == uuid.UUID(conversation_id))
                    .values(
                        summary=summary,
                        updated_at=datetime.utcnow()
                    )
                )
                await session.commit()
                
                self.web_ui_metrics["summaries_generated"] += 1
            
        except Exception as e:
            logger.error(f"Failed to generate web UI summary: {e}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get combined metrics from base manager and web UI service."""
        base_metrics = self.base_manager.metrics.copy()
        base_metrics.update(self.web_ui_metrics)
        return base_metrics



__all__ = [
    "WebUIConversationService",
    "WebUIConversation", 
    "WebUIMessage",
    "ConversationStatus",
    "ConversationPriority",
    "ConversationContextBuilder"
]
    
