"""
Conversation Tracker - Task 1.2 Implementation
Maintains session-based conversation history and context tracking.
"""

import asyncio
import logging
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, field
from collections import deque
import json

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select, update, and_, or_, desc, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from ai_karen_engine.database.client import MultiTenantPostgresClient
from ai_karen_engine.database.models import TenantConversation, TenantMemoryEntry

logger = logging.getLogger(__name__)

@dataclass
class ConversationTurn:
    """Represents a single conversation turn"""
    id: str
    user_message: str
    assistant_response: str
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    memory_references: List[str] = field(default_factory=list)
    context_used: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "user_message": self.user_message,
            "assistant_response": self.assistant_response,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
            "memory_references": self.memory_references,
            "context_used": self.context_used
        }

@dataclass
class ConversationSession:
    """Represents a conversation session"""
    session_id: str
    user_id: str
    tenant_id: str
    conversation_id: Optional[str] = None
    turns: deque = field(default_factory=lambda: deque(maxlen=50))  # Keep last 50 turns
    context_window: List[ConversationTurn] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_activity: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_turn(self, turn: ConversationTurn):
        """Add a conversation turn"""
        self.turns.append(turn)
        self.last_activity = datetime.utcnow()
        self._update_context_window()
    
    def _update_context_window(self, window_size: int = 5):
        """Update context window with recent turns"""
        # Keep the most recent turns for context
        recent_turns = list(self.turns)[-window_size:]
        self.context_window = recent_turns
    
    def get_context_summary(self) -> str:
        """Get a summary of recent conversation context"""
        if not self.context_window:
            return ""
        
        context_parts = []
        for turn in self.context_window:
            context_parts.append(f"User: {turn.user_message}")
            context_parts.append(f"Assistant: {turn.assistant_response}")
        
        return "\n".join(context_parts)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "tenant_id": self.tenant_id,
            "conversation_id": self.conversation_id,
            "turns": [turn.to_dict() for turn in self.turns],
            "context_window": [turn.to_dict() for turn in self.context_window],
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "metadata": self.metadata
        }

class ConversationTracker:
    """Tracks and manages conversation sessions and context"""
    
    def __init__(self, db_client: MultiTenantPostgresClient):
        self.db_client = db_client
        self.active_sessions: Dict[str, ConversationSession] = {}
        self.session_timeout = timedelta(hours=2)  # Sessions expire after 2 hours of inactivity
        
        # Configuration
        self.max_context_window = 5
        self.max_turns_per_session = 50
        self.auto_save_interval = 10  # Save to DB every 10 turns
        
        # Statistics
        self.stats = {
            "total_sessions": 0,
            "active_sessions": 0,
            "total_turns": 0,
            "context_builds": 0,
            "memory_references": 0
        }
        
        # Start cleanup task if there's a running event loop
        try:
            asyncio.create_task(self._cleanup_expired_sessions())
        except RuntimeError:
            # No running event loop, cleanup will be started when needed
            pass
        
        logger.info("Conversation tracker initialized")
    
    async def start_session(
        self,
        session_id: str,
        user_id: str,
        tenant_id: Union[str, uuid.UUID],
        conversation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ConversationSession:
        """Start or resume a conversation session"""
        tenant_id_str = str(tenant_id)
        
        # Check if session already exists
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            session.last_activity = datetime.utcnow()
            logger.debug(f"Resumed existing session: {session_id}")
            return session
        
        # Try to load from database
        session = await self._load_session_from_db(session_id, user_id, tenant_id_str)
        
        if not session:
            # Create new session
            session = ConversationSession(
                session_id=session_id,
                user_id=user_id,
                tenant_id=tenant_id_str,
                conversation_id=conversation_id,
                metadata=metadata or {}
            )
            
            self.stats["total_sessions"] += 1
            logger.info(f"Created new conversation session: {session_id}")
        else:
            logger.info(f"Loaded conversation session from DB: {session_id}")
        
        self.active_sessions[session_id] = session
        self.stats["active_sessions"] = len(self.active_sessions)
        
        return session
    
    async def add_conversation_turn(
        self,
        session_id: str,
        user_message: str,
        assistant_response: str,
        memory_references: Optional[List[str]] = None,
        context_used: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ConversationTurn:
        """Add a conversation turn to the session"""
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found. Start session first.")
        
        session = self.active_sessions[session_id]
        
        # Create conversation turn
        turn = ConversationTurn(
            id=str(uuid.uuid4()),
            user_message=user_message,
            assistant_response=assistant_response,
            timestamp=datetime.utcnow(),
            metadata=metadata or {},
            memory_references=memory_references or [],
            context_used=context_used or []
        )
        
        # Add to session
        session.add_turn(turn)
        
        # Update statistics
        self.stats["total_turns"] += 1
        if memory_references:
            self.stats["memory_references"] += len(memory_references)
        
        # Auto-save to database periodically
        if len(session.turns) % self.auto_save_interval == 0:
            await self._save_session_to_db(session)
        
        logger.debug(
            f"Added conversation turn to session {session_id}",
            extra={
                "turn_id": turn.id,
                "user_message_length": len(user_message),
                "assistant_response_length": len(assistant_response),
                "memory_references_count": len(memory_references or [])
            }
        )
        
        return turn
    
    async def get_conversation_context(
        self,
        session_id: str,
        include_memory_references: bool = True,
        context_window_size: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get conversation context for the session"""
        if session_id not in self.active_sessions:
            # Try to load from database
            session = await self._load_session_from_db_by_id(session_id)
            if not session:
                return {"error": f"Session {session_id} not found"}
            self.active_sessions[session_id] = session
        
        session = self.active_sessions[session_id]
        window_size = context_window_size or self.max_context_window
        
        # Get recent turns for context
        recent_turns = list(session.turns)[-window_size:]
        
        # Build context
        context = {
            "session_id": session_id,
            "user_id": session.user_id,
            "tenant_id": session.tenant_id,
            "conversation_id": session.conversation_id,
            "turn_count": len(session.turns),
            "recent_turns": [turn.to_dict() for turn in recent_turns],
            "context_summary": session.get_context_summary(),
            "last_activity": session.last_activity.isoformat(),
            "session_metadata": session.metadata
        }
        
        # Include memory references if requested
        if include_memory_references:
            all_memory_refs = []
            for turn in recent_turns:
                all_memory_refs.extend(turn.memory_references)
            
            context["memory_references"] = list(set(all_memory_refs))  # Remove duplicates
            context["memory_reference_count"] = len(context["memory_references"])
        
        self.stats["context_builds"] += 1
        
        logger.debug(
            f"Built conversation context for session {session_id}",
            extra={
                "recent_turns_count": len(recent_turns),
                "memory_references_count": len(context.get("memory_references", []))
            }
        )
        
        return context
    
    async def get_session_history(
        self,
        session_id: str,
        limit: Optional[int] = None
    ) -> List[ConversationTurn]:
        """Get conversation history for a session"""
        if session_id not in self.active_sessions:
            session = await self._load_session_from_db_by_id(session_id)
            if not session:
                return []
            self.active_sessions[session_id] = session
        
        session = self.active_sessions[session_id]
        turns = list(session.turns)
        
        if limit:
            turns = turns[-limit:]
        
        return turns
    
    async def end_session(self, session_id: str, save_to_db: bool = True):
        """End a conversation session"""
        if session_id not in self.active_sessions:
            logger.warning(f"Attempted to end non-existent session: {session_id}")
            return
        
        session = self.active_sessions[session_id]
        
        if save_to_db:
            await self._save_session_to_db(session)
        
        del self.active_sessions[session_id]
        self.stats["active_sessions"] = len(self.active_sessions)
        
        logger.info(f"Ended conversation session: {session_id}")
    
    async def _load_session_from_db(
        self,
        session_id: str,
        user_id: str,
        tenant_id: str
    ) -> Optional[ConversationSession]:
        """Load session from database"""
        try:
            async with self.db_client.get_async_session() as db_session:
                # Look for existing conversation
                result = await db_session.execute(
                    select(TenantConversation).where(
                        and_(
                            TenantConversation.session_id == session_id,
                            TenantConversation.user_id == uuid.UUID(user_id)
                        )
                    )
                )
                
                conversation = result.scalar_one_or_none()
                
                if not conversation:
                    return None
                
                # Create session from database data
                session = ConversationSession(
                    session_id=session_id,
                    user_id=user_id,
                    tenant_id=tenant_id,
                    conversation_id=str(conversation.id),
                    created_at=conversation.created_at,
                    last_activity=conversation.updated_at,
                    metadata=conversation.ui_context or {}
                )
                
                # Load conversation turns from memory entries
                memory_result = await db_session.execute(
                    select(TenantMemoryEntry).where(
                        and_(
                            TenantMemoryEntry.session_id == session_id,
                            TenantMemoryEntry.user_id == uuid.UUID(user_id),
                            TenantMemoryEntry.memory_type == "conversation"
                        )
                    ).order_by(TenantMemoryEntry.created_at)
                )
                
                memory_entries = memory_result.fetchall()
                
                for entry in memory_entries:
                    try:
                        # Parse conversation turn from memory content
                        if entry.metadata and "user_message" in entry.metadata:
                            turn = ConversationTurn(
                                id=entry.vector_id or str(entry.id),
                                user_message=entry.metadata["user_message"],
                                assistant_response=entry.metadata.get("assistant_response", ""),
                                timestamp=entry.created_at,
                                metadata=entry.metadata,
                                memory_references=[],
                                context_used=[]
                            )
                            session.add_turn(turn)
                    except Exception as e:
                        logger.warning(f"Failed to parse conversation turn from memory entry {entry.id}: {e}")
                        continue
                
                logger.debug(f"Loaded session {session_id} with {len(session.turns)} turns from database")
                return session
                
        except Exception as e:
            logger.error(f"Failed to load session {session_id} from database: {e}")
            return None
    
    async def _load_session_from_db_by_id(self, session_id: str) -> Optional[ConversationSession]:
        """Load session from database by session ID only"""
        try:
            async with self.db_client.get_async_session() as db_session:
                result = await db_session.execute(
                    select(TenantConversation).where(
                        TenantConversation.session_id == session_id
                    )
                )
                
                conversation = result.scalar_one_or_none()
                
                if not conversation:
                    return None
                
                return await self._load_session_from_db(
                    session_id,
                    str(conversation.user_id),
                    str(conversation.tenant_id) if conversation.tenant_id else str(conversation.user_id)
                )
                
        except Exception as e:
            logger.error(f"Failed to load session {session_id} by ID: {e}")
            return None
    
    async def _save_session_to_db(self, session: ConversationSession):
        """Save session to database"""
        try:
            async with self.db_client.get_async_session() as db_session:
                # Update or create conversation record
                if session.conversation_id:
                    # Update existing conversation
                    await db_session.execute(
                        update(TenantConversation)
                        .where(TenantConversation.id == uuid.UUID(session.conversation_id))
                        .values(
                            updated_at=session.last_activity,
                            ui_context=session.metadata,
                            summary=session.get_context_summary()[:500]  # Truncate summary
                        )
                    )
                else:
                    # Create new conversation
                    conversation = TenantConversation(
                        id=uuid.uuid4(),
                        user_id=uuid.UUID(session.user_id),
                        tenant_id=uuid.UUID(session.tenant_id) if session.tenant_id != session.user_id else None,
                        session_id=session.session_id,
                        title=f"Conversation {session.session_id[:8]}",
                        summary=session.get_context_summary()[:500],
                        ui_context=session.metadata,
                        created_at=session.created_at,
                        updated_at=session.last_activity
                    )
                    
                    db_session.add(conversation)
                    await db_session.flush()
                    session.conversation_id = str(conversation.id)
                
                await db_session.commit()
                
                logger.debug(f"Saved session {session.session_id} to database")
                
        except Exception as e:
            logger.error(f"Failed to save session {session.session_id} to database: {e}")
    
    async def _cleanup_expired_sessions(self):
        """Cleanup expired sessions periodically"""
        while True:
            try:
                await asyncio.sleep(300)  # Check every 5 minutes
                
                current_time = datetime.utcnow()
                expired_sessions = []
                
                for session_id, session in self.active_sessions.items():
                    if current_time - session.last_activity > self.session_timeout:
                        expired_sessions.append(session_id)
                
                for session_id in expired_sessions:
                    await self.end_session(session_id, save_to_db=True)
                
                if expired_sessions:
                    logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
                
            except Exception as e:
                logger.error(f"Error during session cleanup: {e}")
    
    async def get_user_sessions(
        self,
        user_id: str,
        tenant_id: Union[str, uuid.UUID],
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get recent sessions for a user"""
        try:
            async with self.db_client.get_async_session() as db_session:
                result = await db_session.execute(
                    select(TenantConversation)
                    .where(TenantConversation.user_id == uuid.UUID(user_id))
                    .order_by(desc(TenantConversation.updated_at))
                    .limit(limit)
                )
                
                conversations = result.fetchall()
                
                sessions = []
                for conv in conversations:
                    session_info = {
                        "session_id": conv.session_id,
                        "conversation_id": str(conv.id),
                        "title": conv.title,
                        "summary": conv.summary,
                        "created_at": conv.created_at.isoformat(),
                        "updated_at": conv.updated_at.isoformat(),
                        "is_active": conv.session_id in self.active_sessions
                    }
                    sessions.append(session_info)
                
                return sessions
                
        except Exception as e:
            logger.error(f"Failed to get user sessions for {user_id}: {e}")
            return []
    
    def get_tracker_stats(self) -> Dict[str, Any]:
        """Get tracker statistics"""
        return {
            **self.stats,
            "active_sessions": len(self.active_sessions),
            "session_timeout_hours": self.session_timeout.total_seconds() / 3600,
            "max_context_window": self.max_context_window,
            "max_turns_per_session": self.max_turns_per_session,
            "auto_save_interval": self.auto_save_interval
        }

# Factory function
def create_conversation_tracker(db_client: MultiTenantPostgresClient) -> ConversationTracker:
    """Create a conversation tracker instance"""
    return ConversationTracker(db_client)