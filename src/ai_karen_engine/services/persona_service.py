"""
Persona Service
Business logic for managing personas, style controls, and NLP-driven adaptation
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from ai_karen_engine.models.persona_models import (
    SYSTEM_PERSONAS, ChatStyleContext, Persona, PersonaMemoryEntry,
    PersonaStyleOverride, ToneEnum, UserPersonaPreferences, VerbosityEnum
)

logger = logging.getLogger(__name__)


class PersonaService:
    """Service for managing personas and style controls"""
    
    def __init__(self, db_client=None, nlp_analyzer=None):
        """Initialize persona service with database and NLP dependencies"""
        self.db_client = db_client
        self.nlp_analyzer = nlp_analyzer or self._create_default_nlp_analyzer()
        
        # Cache for frequently accessed personas
        self._persona_cache: Dict[str, Persona] = {}
        self._user_preferences_cache: Dict[str, UserPersonaPreferences] = {}
        
        # Load system personas into cache
        for persona in SYSTEM_PERSONAS:
            self._persona_cache[persona.id] = persona
    
    def _create_default_nlp_analyzer(self):
        """Create a default NLP analyzer for style detection"""
        try:
            from ai_karen_engine.services.nlp_style_analyzer import NLPStyleAnalyzer
            return NLPStyleAnalyzer()
        except ImportError:
            logger.warning("NLP style analyzer not available, using mock analyzer")
            return MockNLPAnalyzer()
    
    # Persona Management
    
    async def create_persona(
        self, 
        user_id: str, 
        tenant_id: str, 
        persona_data: Dict[str, Any]
    ) -> Persona:
        """Create a new custom persona for a user"""
        
        # Validate persona data
        persona = Persona(**persona_data)
        persona.is_system_persona = False
        
        # Get user preferences
        preferences = await self.get_user_preferences(user_id, tenant_id)
        
        # Check for duplicate names
        existing_names = {p.name for p in preferences.custom_personas}
        if persona.name in existing_names:
            raise ValueError(f"Persona name '{persona.name}' already exists")
        
        # Add to user's custom personas
        preferences.custom_personas.append(persona)
        preferences.updated_at = datetime.utcnow()
        
        # Save to database
        await self._save_user_preferences(user_id, tenant_id, preferences)
        
        # Update cache
        self._persona_cache[persona.id] = persona
        self._user_preferences_cache[f"{user_id}:{tenant_id}"] = preferences
        
        logger.info(f"Created persona '{persona.name}' for user {user_id}")
        return persona
    
    async def update_persona(
        self, 
        user_id: str, 
        tenant_id: str, 
        persona_id: str, 
        updates: Dict[str, Any]
    ) -> Persona:
        """Update an existing persona"""
        
        # Check if it's a system persona (read-only)
        if persona_id in [p.id for p in SYSTEM_PERSONAS]:
            raise ValueError("System personas cannot be modified")
        
        preferences = await self.get_user_preferences(user_id, tenant_id)
        
        # Find the persona to update
        persona_index = None
        for i, persona in enumerate(preferences.custom_personas):
            if persona.id == persona_id:
                persona_index = i
                break
        
        if persona_index is None:
            raise ValueError(f"Persona {persona_id} not found")
        
        # Apply updates
        persona_dict = preferences.custom_personas[persona_index].dict()
        persona_dict.update(updates)
        persona_dict['updated_at'] = datetime.utcnow()
        
        # Validate updated persona
        updated_persona = Persona(**persona_dict)
        preferences.custom_personas[persona_index] = updated_persona
        preferences.updated_at = datetime.utcnow()
        
        # Save to database
        await self._save_user_preferences(user_id, tenant_id, preferences)
        
        # Update cache
        self._persona_cache[persona_id] = updated_persona
        self._user_preferences_cache[f"{user_id}:{tenant_id}"] = preferences
        
        logger.info(f"Updated persona '{updated_persona.name}' for user {user_id}")
        return updated_persona
    
    async def delete_persona(
        self, 
        user_id: str, 
        tenant_id: str, 
        persona_id: str
    ) -> bool:
        """Delete a custom persona"""
        
        # Check if it's a system persona (cannot delete)
        if persona_id in [p.id for p in SYSTEM_PERSONAS]:
            raise ValueError("System personas cannot be deleted")
        
        preferences = await self.get_user_preferences(user_id, tenant_id)
        
        # Find and remove the persona
        original_count = len(preferences.custom_personas)
        preferences.custom_personas = [
            p for p in preferences.custom_personas if p.id != persona_id
        ]
        
        if len(preferences.custom_personas) == original_count:
            return False  # Persona not found
        
        # If this was the active persona, clear it
        if preferences.active_persona_id == persona_id:
            preferences.active_persona_id = None
        
        preferences.updated_at = datetime.utcnow()
        
        # Save to database
        await self._save_user_preferences(user_id, tenant_id, preferences)
        
        # Remove from cache
        self._persona_cache.pop(persona_id, None)
        self._user_preferences_cache[f"{user_id}:{tenant_id}"] = preferences
        
        logger.info(f"Deleted persona {persona_id} for user {user_id}")
        return True
    
    async def get_persona(self, persona_id: str, user_id: str = None, tenant_id: str = None) -> Optional[Persona]:
        """Get a persona by ID"""
        
        # Check cache first
        if persona_id in self._persona_cache:
            return self._persona_cache[persona_id]
        
        # Check system personas
        for persona in SYSTEM_PERSONAS:
            if persona.id == persona_id:
                self._persona_cache[persona_id] = persona
                return persona
        
        # Check user's custom personas if user context provided
        if user_id and tenant_id:
            preferences = await self.get_user_preferences(user_id, tenant_id)
            for persona in preferences.custom_personas:
                if persona.id == persona_id:
                    self._persona_cache[persona_id] = persona
                    return persona
        
        return None
    
    async def list_available_personas(self, user_id: str, tenant_id: str) -> List[Persona]:
        """List all personas available to a user (system + custom)"""
        
        personas = list(SYSTEM_PERSONAS)  # Start with system personas
        
        # Add user's custom personas
        preferences = await self.get_user_preferences(user_id, tenant_id)
        personas.extend(preferences.custom_personas)
        
        # Filter only active personas
        return [p for p in personas if p.is_active]
    
    # User Preferences Management
    
    async def get_user_preferences(self, user_id: str, tenant_id: str) -> UserPersonaPreferences:
        """Get user's persona preferences"""
        
        cache_key = f"{user_id}:{tenant_id}"
        
        # Check cache first
        if cache_key in self._user_preferences_cache:
            return self._user_preferences_cache[cache_key]
        
        # Load from database
        preferences_data = await self._load_user_preferences(user_id, tenant_id)
        
        if preferences_data:
            preferences = UserPersonaPreferences(**preferences_data)
        else:
            # Create default preferences
            preferences = UserPersonaPreferences(
                user_id=user_id,
                tenant_id=tenant_id
            )
            await self._save_user_preferences(user_id, tenant_id, preferences)
        
        # Cache the preferences
        self._user_preferences_cache[cache_key] = preferences
        return preferences
    
    async def update_user_preferences(
        self, 
        user_id: str, 
        tenant_id: str, 
        updates: Dict[str, Any]
    ) -> UserPersonaPreferences:
        """Update user's persona preferences"""
        
        preferences = await self.get_user_preferences(user_id, tenant_id)
        
        # Apply updates
        for key, value in updates.items():
            if hasattr(preferences, key):
                setattr(preferences, key, value)
        
        preferences.updated_at = datetime.utcnow()
        
        # Save to database
        await self._save_user_preferences(user_id, tenant_id, preferences)
        
        # Update cache
        cache_key = f"{user_id}:{tenant_id}"
        self._user_preferences_cache[cache_key] = preferences
        
        logger.info(f"Updated preferences for user {user_id}")
        return preferences
    
    async def switch_persona(
        self, 
        user_id: str, 
        tenant_id: str, 
        persona_id: Optional[str]
    ) -> UserPersonaPreferences:
        """Switch user's active persona"""
        
        # Validate persona exists if provided
        if persona_id:
            persona = await self.get_persona(persona_id, user_id, tenant_id)
            if not persona:
                raise ValueError(f"Persona {persona_id} not found")
        
        # Update preferences
        return await self.update_user_preferences(
            user_id, 
            tenant_id, 
            {"active_persona_id": persona_id}
        )
    
    # Style Analysis and Adaptation
    
    async def analyze_user_style(self, message: str) -> Dict[str, Any]:
        """Analyze user's writing style using NLP"""
        
        try:
            analysis = await self.nlp_analyzer.analyze_style(message)
            return {
                "detected_tone": analysis.get("tone"),
                "formality_score": analysis.get("formality", 0.5),
                "sentiment_score": analysis.get("sentiment", 0.0),
                "complexity_score": analysis.get("complexity", 0.5),
                "emotion_indicators": analysis.get("emotions", [])
            }
        except Exception as e:
            logger.warning(f"Style analysis failed: {e}")
            return {
                "detected_tone": None,
                "formality_score": 0.5,
                "sentiment_score": 0.0,
                "complexity_score": 0.5,
                "emotion_indicators": []
            }
    
    async def build_chat_context(
        self,
        user_id: str,
        tenant_id: str,
        message: str,
        conversation_id: Optional[str] = None,
        style_override: Optional[PersonaStyleOverride] = None,
        turn_number: int = 1
    ) -> ChatStyleContext:
        """Build complete chat style context for a conversation turn"""
        
        # Get user preferences
        preferences = await self.get_user_preferences(user_id, tenant_id)
        
        # Get active persona
        persona = None
        if preferences.active_persona_id:
            persona = await self.get_persona(
                preferences.active_persona_id, 
                user_id, 
                tenant_id
            )
        
        # Analyze user's style if adaptation is enabled
        style_analysis = {}
        if preferences.enable_style_adaptation:
            style_analysis = await self.analyze_user_style(message)
        
        # Build context
        context = ChatStyleContext(
            persona=persona,
            style_override=style_override,
            detected_user_tone=style_analysis.get("detected_tone"),
            detected_formality=style_analysis.get("formality_score"),
            detected_sentiment=style_analysis.get("sentiment_score"),
            conversation_id=conversation_id,
            turn_number=turn_number
        )
        
        # Set memory filtering if enabled
        if preferences.enable_persona_memory_filtering and persona:
            context.memory_persona_filter = persona.id
            context.memory_tone_filter = persona.default_tone
        
        return context
    
    # Memory Integration
    
    async def store_persona_memory(
        self,
        user_id: str,
        tenant_id: str,
        content: str,
        context: ChatStyleContext,
        conversation_id: Optional[str] = None,
        importance_score: float = 0.5
    ) -> PersonaMemoryEntry:
        """Store a memory entry with persona context"""
        
        memory_entry = PersonaMemoryEntry(
            content=content,
            user_id=user_id,
            tenant_id=tenant_id,
            conversation_id=conversation_id,
            importance_score=importance_score
        )
        
        # Add persona context
        if context.persona:
            memory_entry.persona_id = context.persona.id
            memory_entry.persona_name = context.persona.name
            memory_entry.tone_used = context.get_effective_tone()
            memory_entry.verbosity_used = context.get_effective_verbosity()
        
        # Store in database (implementation depends on your memory system)
        await self._store_memory_entry(memory_entry)
        
        logger.debug(f"Stored persona memory for user {user_id}")
        return memory_entry
    
    async def recall_persona_memories(
        self,
        user_id: str,
        tenant_id: str,
        query: str,
        context: ChatStyleContext,
        limit: int = 10
    ) -> List[PersonaMemoryEntry]:
        """Recall memories with persona-aware filtering"""
        
        # Build filter criteria
        filters = {
            "user_id": user_id,
            "tenant_id": tenant_id
        }
        
        # Apply persona filtering if enabled
        if context.memory_persona_filter:
            filters["persona_id"] = context.memory_persona_filter
        
        # Apply tone filtering if specified
        if context.memory_tone_filter:
            filters["tone_used"] = context.memory_tone_filter.value
        
        # Retrieve memories (implementation depends on your memory system)
        memories = await self._retrieve_memories(query, filters, limit)
        
        logger.debug(f"Retrieved {len(memories)} persona memories for user {user_id}")
        return memories
    
    # Database Operations (to be implemented based on your DB setup)
    
    async def _load_user_preferences(self, user_id: str, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Load user preferences from database"""
        if not self.db_client:
            return None
        
        try:
            # This would be implemented based on your database client
            # For now, return None to create default preferences
            return None
        except Exception as e:
            logger.error(f"Failed to load user preferences: {e}")
            return None
    
    async def _save_user_preferences(
        self, 
        user_id: str, 
        tenant_id: str, 
        preferences: UserPersonaPreferences
    ) -> bool:
        """Save user preferences to database"""
        if not self.db_client:
            logger.warning("No database client available for saving preferences")
            return False
        
        try:
            # This would be implemented based on your database client
            # For now, just log the operation
            logger.debug(f"Saving preferences for user {user_id} (mock operation)")
            return True
        except Exception as e:
            logger.error(f"Failed to save user preferences: {e}")
            return False
    
    async def _store_memory_entry(self, memory_entry: PersonaMemoryEntry) -> bool:
        """Store memory entry in database"""
        if not self.db_client:
            logger.warning("No database client available for storing memory")
            return False
        
        try:
            # This would integrate with your existing memory system
            logger.debug(f"Storing memory entry {memory_entry.id} (mock operation)")
            return True
        except Exception as e:
            logger.error(f"Failed to store memory entry: {e}")
            return False
    
    async def _retrieve_memories(
        self, 
        query: str, 
        filters: Dict[str, Any], 
        limit: int
    ) -> List[PersonaMemoryEntry]:
        """Retrieve memories from database with filtering"""
        if not self.db_client:
            logger.warning("No database client available for retrieving memories")
            return []
        
        try:
            # This would integrate with your existing memory system
            logger.debug(f"Retrieving memories with query '{query}' (mock operation)")
            return []
        except Exception as e:
            logger.error(f"Failed to retrieve memories: {e}")
            return []


class MockNLPAnalyzer:
    """Mock NLP analyzer for when spaCy/transformers are not available"""
    
    async def analyze_style(self, text: str) -> Dict[str, Any]:
        """Mock style analysis"""
        
        # Simple heuristics for demonstration
        word_count = len(text.split())
        has_questions = "?" in text
        has_exclamations = "!" in text
        formal_words = ["please", "thank you", "kindly", "regards"]
        casual_words = ["hey", "yeah", "cool", "awesome", "lol"]
        
        formality_score = 0.5
        if any(word in text.lower() for word in formal_words):
            formality_score += 0.2
        if any(word in text.lower() for word in casual_words):
            formality_score -= 0.2
        
        formality_score = max(0.0, min(1.0, formality_score))
        
        # Determine tone based on simple heuristics
        tone = ToneEnum.FRIENDLY
        if formality_score > 0.7:
            tone = ToneEnum.PROFESSIONAL
        elif formality_score < 0.3:
            tone = ToneEnum.CASUAL
        elif has_questions and word_count > 20:
            tone = ToneEnum.TECHNICAL
        
        return {
            "tone": tone,
            "formality": formality_score,
            "sentiment": 0.1 if has_exclamations else -0.1 if "problem" in text.lower() else 0.0,
            "complexity": min(1.0, word_count / 50.0),
            "emotions": ["curious"] if has_questions else ["neutral"]
        }


# Global service instance
_persona_service: Optional[PersonaService] = None


def get_persona_service() -> PersonaService:
    """Get the global persona service instance"""
    global _persona_service
    if _persona_service is None:
        _persona_service = PersonaService()
    return _persona_service


def initialize_persona_service(db_client=None, nlp_analyzer=None) -> PersonaService:
    """Initialize the global persona service with dependencies"""
    global _persona_service
    _persona_service = PersonaService(db_client=db_client, nlp_analyzer=nlp_analyzer)
    return _persona_service