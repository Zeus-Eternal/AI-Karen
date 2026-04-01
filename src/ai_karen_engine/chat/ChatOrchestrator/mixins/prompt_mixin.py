from __future__ import annotations
import logging
from typing import Optional, List, Dict, Any, Union, TYPE_CHECKING

from ai_karen_engine.chat.ChatOrchestrator.utils import resolve_display_name, build_user_identity_line
from ai_karen_engine.services.persona_service import get_persona_service
from ai_karen_engine.models.shared_types import ChatMessage, MessageRole

if TYPE_CHECKING:
    from ai_karen_engine.services.memory.spacy_service import ParsedMessage
    from ai_karen_engine.chat.ChatOrchestrator.models import ProcessingContext
    from ai_karen_engine.chat.ChatOrchestrator.base import ChatOrchestratorProtocol
    Base = ChatOrchestratorProtocol
else:
    Base = object

logger = logging.getLogger(__name__)

class ChatPromptMixin(Base):
    """Methods for building prompts and structured messages."""

    async def _get_persona_system_prompt(self, context: ProcessingContext) -> str:
        """Resolve the active persona's system prompt."""
        persona_service = get_persona_service()
        metadata = context.metadata
        persona_id = metadata.get("persona_id")
        
        if persona_id:
            persona = await persona_service.get_persona(persona_id)
            if persona:
                return persona.system_prompt
        
        # Fallback to default persona (the first system persona)
        from ai_karen_engine.models.persona_models import SYSTEM_PERSONAS
        default_persona = SYSTEM_PERSONAS[0] if SYSTEM_PERSONAS else None
        return default_persona.system_prompt if default_persona else "You are Karen, a helpful AI assistant."

    async def _build_chat_messages(
        self,
        context: ProcessingContext
    ) -> List[ChatMessage]:
        """Build a list of ChatMessage objects for the LLM."""
        messages = []
        
        # 1. System Prompt
        system_prompt = await self._get_persona_system_prompt(context)
        
        # 2. Identity Injection
        display_name = await resolve_display_name(
            auth_service=self.auth_service,
            user_id=context.user_id,
            request_context=context.metadata
        )
        if display_name:
            system_prompt += "\n\n" + build_user_identity_line(display_name)
            
        messages.append(ChatMessage(role=MessageRole.SYSTEM, content=system_prompt))
        
        # 3. Context & Instructions (Simplified for this Mixin)
        # In a real implementation, we would add history and retrieved memories here.
        # Note: integrated_context and active_instructions should be part of context or separate if needed.
        # For now, we utilize the context.metadata or internal flags.
        
        # 4. User Message
        user_message = context.request.message if context.request else ""
        messages.append(ChatMessage(role=MessageRole.USER, content=user_message))
        
        return messages

    async def _build_enhanced_prompt(
        self,
        context: ProcessingContext
    ) -> str:
        """Build a single string prompt (e.g. for completion models)."""
        system_prompt = await self._get_persona_system_prompt(context)
        
        # Identity
        display_name = await resolve_display_name(
            auth_service=self.auth_service,
            user_id=context.user_id,
            request_context=context.metadata
        )
        if display_name:
            system_prompt += "\n\n" + build_user_identity_line(display_name)
            
        # Note: Add instructions/context here if needed from context
        
        user_message = context.request.message if context.request else ""
        prompt = f"System: {system_prompt}\n\n"
        prompt += f"User: {user_message}\n\nAssistant: "
        return prompt
