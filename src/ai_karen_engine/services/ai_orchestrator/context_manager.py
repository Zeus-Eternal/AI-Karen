import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from ai_karen_engine.models.shared_types import MemoryContext

if TYPE_CHECKING:
    from ai_karen_engine.services.memory_service import WebUIMemoryService, WebUIMemoryQuery


class ContextManager:
    """
    Manages conversation context and memory integration.
    Builds context from various sources including memory, conversation history, and user preferences.
    """
    
    def __init__(self, memory_service: Optional["WebUIMemoryService"] = None):
        self.logger = logging.getLogger("ai_orchestrator.context_manager")
        self._context_cache: Dict[str, Dict[str, Any]] = {}
        self._cache_ttl = 300  # 5 minutes
        self._memory_service = memory_service
    
    async def build_context(
        self, 
        user_id: Optional[str],
        session_id: Optional[str],
        prompt: str,
        conversation_history: List[Dict[str, Any]],
        user_settings: Dict[str, Any],
        memories: Optional[List[MemoryContext]] = None
    ) -> Dict[str, Any]:
        """
        Build comprehensive context for AI processing with semantic memory integration.
        """
        try:
            # Retrieve semantic memories if not provided
            if memories is None and self._memory_service:
                memories = await self._retrieve_semantic_memories(
                    prompt, user_id, session_id, conversation_history
                )
            
            context = {
                "user_id": user_id,
                "session_id": session_id,
                "current_prompt": prompt,
                "timestamp": datetime.now().isoformat(),
                "conversation_history": conversation_history,
                "user_settings": user_settings,
                "memories": memories or [],
                "context_summary": "",
                "relevant_facts": [],
                "conversation_themes": [],
                "semantic_context": {}
            }
            
            # Extract and rank relevant facts from memories using semantic similarity
            if memories:
                context["relevant_facts"] = await self._extract_and_rank_facts(memories, prompt)
                context["semantic_context"] = await self._build_semantic_context(memories, prompt)
            
            # Analyze conversation themes with enhanced NLP
            if conversation_history:
                themes = await self._extract_conversation_themes(conversation_history)
                context["conversation_themes"] = themes
            
            # Generate enhanced context summary
            context["context_summary"] = await self._generate_context_summary(context)
            
            # Cache context for reuse
            if user_id and session_id:
                cache_key = f"{user_id}:{session_id}"
                self._context_cache[cache_key] = {
                    "context": context,
                    "timestamp": datetime.now()
                }
            
            return context
            
        except Exception as e:
            self.logger.error(f"Context building failed: {e}")
            return {
                "user_id": user_id,
                "session_id": session_id,
                "current_prompt": prompt,
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
    
    async def _extract_conversation_themes(self, conversation_history: List[Dict[str, Any]]) -> List[str]:
        """Extract themes from conversation history."""
        # Simple theme extraction - in production, this would use NLP
        themes = set()
        
        all_content = " ".join([
            msg.get("content", "") for msg in conversation_history
            if isinstance(msg.get("content"), str)
        ]).lower()
        
        theme_keywords = {
            "weather": ["weather", "temperature", "rain", "sunny", "cloudy"],
            "time": ["time", "clock", "hour", "minute", "schedule"],
            "technology": ["computer", "software", "app", "tech", "digital"],
            "work": ["work", "job", "career", "office", "business"],
            "entertainment": ["movie", "music", "game", "book", "show"]
        }
        
        for theme, keywords in theme_keywords.items():
            if any(keyword in all_content for keyword in keywords):
                themes.add(theme)
        
        return list(themes)
    
    async def _generate_context_summary(self, context: Dict[str, Any]) -> str:
        """Generate a summary of the current context."""
        summary_parts = []
        
        if context.get("conversation_themes"):
            themes_str = ", ".join(context["conversation_themes"])
            summary_parts.append(f"Conversation themes: {themes_str}")
        
        if context.get("relevant_facts"):
            fact_count = len(context["relevant_facts"])
            summary_parts.append(f"{fact_count} relevant memories available")
        
        if context.get("user_settings"):
            settings = context["user_settings"]
            if settings.get("personality_tone"):
                summary_parts.append(f"Tone: {settings['personality_tone']}")
        
        return "; ".join(summary_parts) if summary_parts else "Basic context available"
    
    def get_cached_context(self, user_id: str, session_id: str) -> Optional[Dict[str, Any]]:
        """Get cached context if available and not expired."""
        cache_key = f"{user_id}:{session_id}"
        cached = self._context_cache.get(cache_key)
        
        if cached:
            age = (datetime.now() - cached["timestamp"]).total_seconds()
            if age < self._cache_ttl:
                return cached["context"]
            else:
                del self._context_cache[cache_key]
        
        return None
    
    def clear_context_cache(self, user_id: Optional[str] = None, session_id: Optional[str] = None) -> None:
        """Clear context cache for specific user/session or all."""
        if user_id and session_id:
            cache_key = f"{user_id}:{session_id}"
            self._context_cache.pop(cache_key, None)
        elif user_id:
            keys_to_remove = [k for k in self._context_cache.keys() if k.startswith(f"{user_id}:")]
            for key in keys_to_remove:
                del self._context_cache[key]
        else:
            self._context_cache.clear()

    async def _retrieve_semantic_memories(
        self, 
        prompt: str, 
        user_id: Optional[str], 
        session_id: Optional[str],
        conversation_history: List[Dict[str, Any]]
    ) -> List[MemoryContext]:
        """Retrieve semantically relevant memories using DistilBERT embeddings."""
        try:
            if not self._memory_service:
                self.logger.warning("Memory service not available for semantic retrieval")
                return []

            # Build query text from prompt and recent conversation
            query_parts = [prompt]
            
            # Add recent conversation context for better semantic matching
            if conversation_history:
                recent_messages = conversation_history[-3:]  # Last 3 messages
                for msg in recent_messages:
                    if isinstance(msg.get("content"), str):
                        query_parts.append(msg["content"])
            
            query_text = " ".join(query_parts)
            
            # Import WebUIMemoryQuery dynamically to avoid circular imports
            from ai_karen_engine.services.memory_service import WebUIMemoryQuery
            
            # Create memory query with semantic search parameters
            memory_query = WebUIMemoryQuery(
                text=query_text,
                user_id=user_id or "anonymous",
                session_id=session_id,
                ui_source=None,  # Search across all UI sources
                memory_types=[],  # Search all memory types
                tags=[],
                importance_range=None,
                only_user_confirmed=True,  # Only confirmed memories
                only_ai_generated=False,
                time_range=None,
                top_k=10,  # Get top 10 semantically similar memories
                similarity_threshold=0.6,  # Minimum similarity threshold
                include_embeddings=False
            )
            
            # Query memories using the memory service
            memories = await self._memory_service.query_memories("default", memory_query)
            
            # Convert to MemoryContext objects
            memory_contexts = []
            for mem in memories:
                memory_context = MemoryContext(
                    content=mem.content,
                    tags=mem.tags,
                    similarity_score=mem.similarity_score,
                    timestamp=mem.timestamp,
                    metadata=mem.metadata
                )
                memory_contexts.append(memory_context)
            
            self.logger.info(f"Retrieved {len(memory_contexts)} semantic memories for context")
            return memory_contexts
            
        except Exception as e:
            self.logger.error(f"Semantic memory retrieval failed: {e}")
            return []

    async def _extract_and_rank_facts(
        self, 
        memories: List[MemoryContext], 
        prompt: str
    ) -> List[Dict[str, Any]]:
        """Extract and rank relevant facts from memories using semantic similarity."""
        try:
            ranked_facts = []
            
            for memory in memories:
                # Calculate relevance score (already provided by semantic search)
                relevance_score = memory.similarity_score or 0.0
                
                # Extract key information from memory content
                fact = {
                    "content": memory.content,
                    "relevance": relevance_score,
                    "tags": memory.tags or [],
                    "timestamp": memory.timestamp,
                    "confidence": self._calculate_fact_confidence(memory, prompt),
                    "importance": self._extract_importance_from_metadata(memory.metadata)
                }
                
                ranked_facts.append(fact)
            
            # Sort by relevance score (descending)
            ranked_facts.sort(key=lambda x: x["relevance"], reverse=True)
            
            # Return top 5 most relevant facts
            return ranked_facts[:5]
            
        except Exception as e:
            self.logger.error(f"Fact extraction and ranking failed: {e}")
            return []

    async def _build_semantic_context(
        self, 
        memories: List[MemoryContext], 
        prompt: str
    ) -> Dict[str, Any]:
        """Build semantic context information from memories."""
        try:
            semantic_context = {
                "total_memories": len(memories),
                "high_relevance_count": 0,
                "memory_types": set(),
                "common_tags": [],
                "temporal_distribution": {},
                "semantic_clusters": []
            }
            
            # Analyze memory relevance distribution
            high_relevance_threshold = 0.8
            for memory in memories:
                if (memory.similarity_score or 0.0) >= high_relevance_threshold:
                    semantic_context["high_relevance_count"] += 1
                
                # Collect memory types from tags
                if memory.tags:
                    semantic_context["memory_types"].update(memory.tags)
            
            # Find common tags across memories
            if memories:
                all_tags = []
                for memory in memories:
                    if memory.tags:
                        all_tags.extend(memory.tags)
                
                # Count tag frequency
                tag_counts = {}
                for tag in all_tags:
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1
                
                # Get most common tags
                common_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:3]
                semantic_context["common_tags"] = [tag for tag, count in common_tags]
            
            # Convert memory_types set to list for JSON serialization
            semantic_context["memory_types"] = list(semantic_context["memory_types"])
            
            return semantic_context
            
        except Exception as e:
            self.logger.error(f"Semantic context building failed: {e}")
            return {}

    def _calculate_fact_confidence(self, memory: MemoryContext, prompt: str) -> float:
        """Calculate confidence score for a fact based on various factors."""
        try:
            confidence = 0.5  # Base confidence
            
            # Boost confidence based on similarity score
            if memory.similarity_score:
                confidence += memory.similarity_score * 0.3
            
            # Boost confidence for memories with specific tags
            if memory.tags:
                important_tags = ["personal_info", "preference", "fact", "confirmed"]
                if any(tag in memory.tags for tag in important_tags):
                    confidence += 0.1
            
            # Boost confidence for recent memories
            if memory.timestamp:
                # Simple recency boost - more sophisticated time decay could be implemented
                confidence += 0.05
            
            return min(confidence, 1.0)  # Cap at 1.0
            
        except Exception as e:
            self.logger.error(f"Confidence calculation failed: {e}")
            return 0.5

    def _extract_importance_from_metadata(self, metadata: Optional[Dict[str, Any]]) -> int:
        """Extract importance score from memory metadata."""
        if not metadata:
            return 5  # Default importance
        
        # Look for importance indicators in metadata
        importance = metadata.get("importance", 5)
        if isinstance(importance, (int, float)):
            return int(importance)
        
        # Look for importance score
        importance_score = metadata.get("importance_score", 5)
        if isinstance(importance_score, (int, float)):
            return int(importance_score)
        
        return 5  # Default importance
