"""
Integrated Memory Service - Task 1 Complete Implementation
Combines enhanced memory service with conversation tracking for complete memory recall functionality.
"""

import asyncio
import logging
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass

from ai_karen_engine.database.memory_manager import MemoryManager
from ai_karen_engine.database.client import MultiTenantPostgresClient

from .enhanced_memory_service import EnhancedMemoryService, MemoryServiceError
from .conversation_tracker import ConversationTracker, ConversationSession, ConversationTurn
from .memory_service import MemoryType, UISource, WebUIMemoryEntry, WebUIMemoryQuery

logger = logging.getLogger(__name__)

@dataclass
class ContextualMemoryQuery:
    """Enhanced memory query with conversation context"""
    text: str
    user_id: str
    session_id: Optional[str] = None
    conversation_id: Optional[str] = None
    include_conversation_context: bool = True
    context_window_size: int = 5
    top_k: int = 10
    similarity_threshold: float = 0.7
    memory_types: List[MemoryType] = None
    tags: List[str] = None

@dataclass
class ContextualMemoryResult:
    """Enhanced memory result with conversation context"""
    memories: List[WebUIMemoryEntry]
    conversation_context: Dict[str, Any]
    context_summary: str
    total_memories_found: int
    query_time_ms: float
    used_fallback: bool = False
    correlation_id: str = ""

class IntegratedMemoryService:
    """Integrated memory service with conversation tracking and context management"""
    
    def __init__(
        self,
        base_memory_manager: MemoryManager,
        db_client: MultiTenantPostgresClient
    ):
        self.enhanced_memory_service = EnhancedMemoryService(base_memory_manager)
        self.conversation_tracker = ConversationTracker(db_client)
        self.db_client = db_client
        
        # Integration statistics
        self.integration_stats = {
            "contextual_queries": 0,
            "context_enhanced_results": 0,
            "conversation_memories_stored": 0,
            "cross_session_references": 0
        }
        
        logger.info("Integrated memory service initialized")
    
    async def query_memories_with_context(
        self,
        tenant_id: Union[str, uuid.UUID],
        query: ContextualMemoryQuery
    ) -> ContextualMemoryResult:
        """Query memories with full conversation context integration"""
        start_time = time.time()
        correlation_id = str(uuid.uuid4())
        
        self.integration_stats["contextual_queries"] += 1
        
        logger.info(
            f"Starting contextual memory query for tenant {tenant_id}",
            extra={
                "correlation_id": correlation_id,
                "query_text": query.text[:100] + "..." if len(query.text) > 100 else query.text,
                "user_id": query.user_id,
                "session_id": query.session_id,
                "include_context": query.include_conversation_context
            }
        )
        
        try:
            # 1. Get conversation context if requested
            conversation_context = {}
            context_summary = ""
            
            if query.include_conversation_context and query.session_id:
                try:
                    conversation_context = await self.conversation_tracker.get_conversation_context(
                        query.session_id,
                        include_memory_references=True,
                        context_window_size=query.context_window_size
                    )
                    
                    context_summary = conversation_context.get("context_summary", "")
                    
                    logger.debug(
                        f"Retrieved conversation context with {len(conversation_context.get('recent_turns', []))} recent turns",
                        extra={"correlation_id": correlation_id}
                    )
                    
                except Exception as e:
                    logger.warning(
                        f"Failed to get conversation context: {e}",
                        extra={"correlation_id": correlation_id}
                    )
                    conversation_context = {"error": str(e)}
            
            # 2. Enhance query with conversation context
            enhanced_query_text = self._enhance_query_with_context(query.text, context_summary)
            
            # 3. Create WebUIMemoryQuery for the enhanced memory service
            web_ui_query = WebUIMemoryQuery(
                text=enhanced_query_text,
                user_id=query.user_id,
                session_id=query.session_id,
                conversation_id=query.conversation_id,
                memory_types=query.memory_types or [],
                tags=query.tags or [],
                top_k=query.top_k,
                similarity_threshold=query.similarity_threshold
            )
            
            # 4. Query memories using enhanced memory service
            used_fallback = False
            try:
                memories = await self.enhanced_memory_service.query_memories(tenant_id, web_ui_query)
            except MemoryServiceError as e:
                logger.warning(f"Memory service error, using fallback: {e}")
                memories = []
                used_fallback = True
            
            # 5. Post-process results with conversation context
            if conversation_context and not conversation_context.get("error"):
                memories = await self._enhance_memories_with_context(
                    memories, conversation_context, correlation_id
                )
                self.integration_stats["context_enhanced_results"] += 1
            
            # 6. Calculate timing and create result
            query_time_ms = (time.time() - start_time) * 1000
            
            result = ContextualMemoryResult(
                memories=memories,
                conversation_context=conversation_context,
                context_summary=context_summary,
                total_memories_found=len(memories),
                query_time_ms=query_time_ms,
                used_fallback=used_fallback,
                correlation_id=correlation_id
            )
            
            logger.info(
                f"Contextual memory query completed: {len(memories)} memories in {query_time_ms:.2f}ms",
                extra={
                    "correlation_id": correlation_id,
                    "used_fallback": used_fallback,
                    "context_enhanced": bool(conversation_context and not conversation_context.get("error"))
                }
            )
            
            return result
            
        except Exception as e:
            query_time_ms = (time.time() - start_time) * 1000
            
            logger.error(
                f"Contextual memory query failed: {e}",
                extra={
                    "correlation_id": correlation_id,
                    "tenant_id": str(tenant_id),
                    "query_text": query.text[:100] + "..." if len(query.text) > 100 else query.text
                }
            )
            
            # Return empty result for graceful degradation
            return ContextualMemoryResult(
                memories=[],
                conversation_context={"error": str(e)},
                context_summary="",
                total_memories_found=0,
                query_time_ms=query_time_ms,
                used_fallback=True,
                correlation_id=correlation_id
            )
    
    async def store_conversation_memory(
        self,
        tenant_id: Union[str, uuid.UUID],
        user_message: str,
        assistant_response: str,
        user_id: str,
        session_id: str,
        conversation_id: Optional[str] = None,
        memory_references: Optional[List[str]] = None,
        context_used: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Tuple[Optional[str], ConversationTurn]:
        """Store conversation turn in both memory and conversation tracking"""
        correlation_id = str(uuid.uuid4())
        
        logger.info(
            f"Storing conversation memory for session {session_id}",
            extra={
                "correlation_id": correlation_id,
                "user_id": user_id,
                "user_message_length": len(user_message),
                "assistant_response_length": len(assistant_response)
            }
        )
        
        try:
            # 1. Store in conversation tracker
            conversation_turn = await self.conversation_tracker.add_conversation_turn(
                session_id=session_id,
                user_message=user_message,
                assistant_response=assistant_response,
                memory_references=memory_references,
                context_used=context_used,
                metadata=metadata
            )
            
            # 2. Store in memory service
            conversation_content = f"User: {user_message}\nAssistant: {assistant_response}"
            
            memory_metadata = {
                "type": "conversation",
                "user_message": user_message,
                "assistant_response": assistant_response,
                "turn_id": conversation_turn.id,
                "memory_references": memory_references or [],
                "context_used": context_used or [],
                **(metadata or {})
            }
            
            memory_id = await self.enhanced_memory_service.store_web_ui_memory(
                tenant_id=tenant_id,
                content=conversation_content,
                user_id=user_id,
                ui_source=UISource.WEB,
                session_id=session_id,
                conversation_id=conversation_id,
                memory_type=MemoryType.CONVERSATION,
                tags=["conversation", "chat"],
                importance_score=5,
                ai_generated=False,
                metadata=memory_metadata
            )
            
            self.integration_stats["conversation_memories_stored"] += 1
            
            logger.info(
                f"Conversation memory stored successfully",
                extra={
                    "correlation_id": correlation_id,
                    "memory_id": memory_id,
                    "turn_id": conversation_turn.id
                }
            )
            
            return memory_id, conversation_turn
            
        except Exception as e:
            logger.error(
                f"Failed to store conversation memory: {e}",
                extra={
                    "correlation_id": correlation_id,
                    "session_id": session_id,
                    "user_id": user_id
                }
            )
            
            # Still return the conversation turn even if memory storage failed
            try:
                conversation_turn = await self.conversation_tracker.add_conversation_turn(
                    session_id=session_id,
                    user_message=user_message,
                    assistant_response=assistant_response,
                    memory_references=memory_references,
                    context_used=context_used,
                    metadata=metadata
                )
                return None, conversation_turn
            except Exception as turn_error:
                logger.error(f"Failed to store conversation turn: {turn_error}")
                # Create a minimal turn for return
                return None, ConversationTurn(
                    id=str(uuid.uuid4()),
                    user_message=user_message,
                    assistant_response=assistant_response,
                    timestamp=datetime.utcnow()
                )
    
    async def start_conversation_session(
        self,
        session_id: str,
        user_id: str,
        tenant_id: Union[str, uuid.UUID],
        conversation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ConversationSession:
        """Start a conversation session with memory integration"""
        return await self.conversation_tracker.start_session(
            session_id=session_id,
            user_id=user_id,
            tenant_id=tenant_id,
            conversation_id=conversation_id,
            metadata=metadata
        )
    
    async def end_conversation_session(self, session_id: str):
        """End a conversation session"""
        await self.conversation_tracker.end_session(session_id, save_to_db=True)
    
    async def get_conversation_history_with_memories(
        self,
        session_id: str,
        include_related_memories: bool = True,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get conversation history with related memories"""
        try:
            # Get conversation history
            turns = await self.conversation_tracker.get_session_history(session_id, limit)
            
            history = {
                "session_id": session_id,
                "turns": [turn.to_dict() for turn in turns],
                "turn_count": len(turns)
            }
            
            if include_related_memories and turns:
                # Get all memory references from turns
                all_memory_refs = []
                for turn in turns:
                    all_memory_refs.extend(turn.memory_references)
                
                # Remove duplicates
                unique_memory_refs = list(set(all_memory_refs))
                
                history["memory_references"] = unique_memory_refs
                history["memory_reference_count"] = len(unique_memory_refs)
                
                # Could add logic here to fetch the actual memory content
                # if needed for display purposes
            
            return history
            
        except Exception as e:
            logger.error(f"Failed to get conversation history with memories: {e}")
            return {"error": str(e), "session_id": session_id}
    
    def _enhance_query_with_context(self, original_query: str, context_summary: str) -> str:
        """Enhance query text with conversation context"""
        if not context_summary:
            return original_query
        
        # Simple context enhancement - could be made more sophisticated
        # with NLP analysis of what context is relevant
        context_lines = context_summary.split('\n')
        recent_context = '\n'.join(context_lines[-6:])  # Last 3 exchanges
        
        if len(recent_context) > 500:  # Limit context size
            recent_context = recent_context[-500:]
        
        enhanced_query = f"Context: {recent_context}\n\nQuery: {original_query}"
        return enhanced_query
    
    async def _enhance_memories_with_context(
        self,
        memories: List[WebUIMemoryEntry],
        conversation_context: Dict[str, Any],
        correlation_id: str
    ) -> List[WebUIMemoryEntry]:
        """Enhance memory results with conversation context"""
        try:
            # Get memory references from conversation context
            context_memory_refs = set(conversation_context.get("memory_references", []))
            
            # Mark memories that were referenced in recent conversation
            for memory in memories:
                if memory.id in context_memory_refs:
                    # Boost similarity score for memories referenced in conversation
                    if memory.similarity_score:
                        memory.similarity_score = min(memory.similarity_score * 1.2, 1.0)
                    
                    # Add context metadata
                    if not memory.metadata:
                        memory.metadata = {}
                    memory.metadata["referenced_in_conversation"] = True
                    
                    self.integration_stats["cross_session_references"] += 1
            
            # Sort by enhanced similarity score
            memories.sort(key=lambda m: m.similarity_score or 0, reverse=True)
            
            logger.debug(
                f"Enhanced {len(memories)} memories with conversation context",
                extra={"correlation_id": correlation_id}
            )
            
            return memories
            
        except Exception as e:
            logger.warning(
                f"Failed to enhance memories with context: {e}",
                extra={"correlation_id": correlation_id}
            )
            return memories
    
    async def get_service_health(self) -> Dict[str, Any]:
        """Get comprehensive service health status"""
        memory_health = await self.enhanced_memory_service.get_service_health()
        tracker_stats = self.conversation_tracker.get_tracker_stats()
        
        return {
            "status": memory_health["status"],
            "memory_service": memory_health,
            "conversation_tracker": tracker_stats,
            "integration_stats": self.integration_stats,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def reset_service_state(self):
        """Reset service state (for administrative use)"""
        await self.enhanced_memory_service.reset_circuit_breakers()
        
        # Reset integration stats
        self.integration_stats = {
            "contextual_queries": 0,
            "context_enhanced_results": 0,
            "conversation_memories_stored": 0,
            "cross_session_references": 0
        }
        
        logger.info("Integrated memory service state reset")

# Factory function
def create_integrated_memory_service(
    base_memory_manager: MemoryManager,
    db_client: MultiTenantPostgresClient
) -> IntegratedMemoryService:
    """Create an integrated memory service instance"""
    return IntegratedMemoryService(base_memory_manager, db_client)