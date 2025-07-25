import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from ai_karen_engine.models.shared_types import MemoryContext


class ContextManager:
    """
    Manages conversation context and memory integration.
    Builds context from various sources including memory, conversation history, and user preferences.
    """
    
    def __init__(self):
        self.logger = logging.getLogger("ai_orchestrator.context_manager")
        self._context_cache: Dict[str, Dict[str, Any]] = {}
        self._cache_ttl = 300  # 5 minutes
    
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
        Build comprehensive context for AI processing.
        """
        try:
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
                "conversation_themes": []
            }
            
            # Extract relevant facts from memories
            if memories:
                context["relevant_facts"] = [
                    {
                        "content": mem.content,
                        "relevance": mem.similarity_score or 0.0,
                        "tags": mem.tags or []
                    }
                    for mem in memories
                ]
            
            # Analyze conversation themes
            if conversation_history:
                themes = await self._extract_conversation_themes(conversation_history)
                context["conversation_themes"] = themes
            
            # Generate context summary
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
