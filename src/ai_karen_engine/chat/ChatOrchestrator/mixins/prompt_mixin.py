from __future__ import annotations
import logging
import re
from typing import Optional, List, Dict, Any, Union, TYPE_CHECKING

from ai_karen_engine.chat.ChatOrchestrator.utils import resolve_display_name, build_user_identity_line
from ai_karen_engine.memory.persona_service import get_persona_service
from ai_karen_engine.models.shared_types import ChatMessage, MessageRole

if TYPE_CHECKING:
    from ai_karen_engine.memory.spacy_service import ParsedMessage
    from ai_karen_engine.chat.ChatOrchestrator.models import ProcessingContext
    from ai_karen_engine.chat.ChatOrchestrator.base import ChatOrchestratorProtocol
    Base = ChatOrchestratorProtocol
else:
    Base = object

logger = logging.getLogger(__name__)


def _looks_like_transcript_dump(content: str) -> bool:
    text = str(content or "").strip()
    if not text:
        return False
    lowered = text.lower()
    if "<|assistant|>" in lowered or "<|user|>" in lowered:
        return True

    lines = [line.strip().lower() for line in text.splitlines() if line.strip()]
    if len(lines) < 3:
        return False

    user_lines = sum(1 for line in lines if line.startswith("user:"))
    assistant_lines = sum(1 for line in lines if line.startswith("assistant:"))
    bot_lines = sum(1 for line in lines if line.startswith("bot:"))
    return user_lines >= 2 and (assistant_lines + bot_lines) >= 1


def _extract_recent_history_lines(items: Any, limit: int = 6) -> List[str]:
    lines: List[str] = []
    if not isinstance(items, list):
        return lines
    for item in items[-limit:]:
        if not isinstance(item, dict):
            continue
        role = str(item.get("role", "")).strip().lower()
        content = str(item.get("content", "")).strip()
        if role not in {"user", "assistant"} or not content:
            continue
        if _looks_like_transcript_dump(content):
            continue
        lines.append(f"{role.title()}: {content}")
    return lines


def _extract_session_turn_lines(session_state: Any, limit: int = 4) -> List[str]:
    if not isinstance(session_state, dict):
        return []
    recent_turns = session_state.get("recent_turns", [])
    return _extract_recent_history_lines(recent_turns, limit=limit)


def _extract_fact_lines(items: Any, limit: int = 4) -> List[str]:
    lines: List[str] = []
    if not isinstance(items, list):
        return lines
    for item in items[:limit]:
        if not isinstance(item, dict):
            continue
        content = str(item.get("content", "")).strip()
        if not content:
            continue
        lines.append(f"- {content}")
    return lines


def _build_structured_context_sections(
    request_context: Dict[str, Any],
    integrated_context: Dict[str, Any],
) -> List[str]:
    sections: List[str] = []

    user_fact_lines = _extract_fact_lines(request_context.get("user_facts"), limit=4)
    if user_fact_lines:
        sections.append("Known user facts:\n" + "\n".join(user_fact_lines))

    project_fact_lines = _extract_fact_lines(
        request_context.get("project_facts"), limit=4
    )
    if project_fact_lines:
        sections.append("Known project facts:\n" + "\n".join(project_fact_lines))

    episodic_lines = _extract_fact_lines(
        request_context.get("episodic_items"), limit=3
    )
    if episodic_lines:
        sections.append("Relevant episodic memory:\n" + "\n".join(episodic_lines))

    semantic_long_term_lines = _extract_fact_lines(
        request_context.get("semantic_long_term_items"), limit=3
    )
    if semantic_long_term_lines:
        sections.append(
            "Relevant long-term knowledge:\n" + "\n".join(semantic_long_term_lines)
        )

    recalled_item_lines = _extract_fact_lines(
        request_context.get("recalled_items"), limit=4
    )
    if recalled_item_lines:
        sections.append("Curated recalled context:\n" + "\n".join(recalled_item_lines))

    if isinstance(integrated_context, dict):
        memory_items = integrated_context.get("memories", [])
        if isinstance(memory_items, list) and memory_items:
            memory_lines = _extract_fact_lines(memory_items, limit=5)
            if memory_lines:
                sections.append("Relevant memory context:\n" + "\n".join(memory_lines))

        instruction_items = integrated_context.get("instructions", [])
        if isinstance(instruction_items, list) and instruction_items:
            instruction_lines = _extract_fact_lines(instruction_items, limit=5)
            if instruction_lines:
                sections.append("Active instructions:\n" + "\n".join(instruction_lines))

    return sections


def _wants_long_form_markdown_article(
    current_user_message: str,
    recent_messages: Any,
) -> bool:
    text_parts: List[str] = [str(current_user_message or "").lower()]
    if isinstance(recent_messages, list):
        for item in recent_messages[-6:]:
            if not isinstance(item, dict):
                continue
            role = str(item.get("role", "")).strip().lower()
            content = str(item.get("content", "")).strip().lower()
            if role == "user" and content:
                text_parts.append(content)

    combined = "\n".join(text_parts)
    long_form_markers = (
        "full article",
        "write an article",
        "blog article",
        "blog post",
        "full post",
        "in-depth article",
        "detailed article",
        "long-form",
        "long form",
        "full write-up",
    )
    return any(marker in combined for marker in long_form_markers)


def _extract_about_topic(text: str) -> str:
    raw = str(text or "").strip()
    if not raw:
        return ""
    match = re.search(r"\babout\s+(.+)$", raw, flags=re.IGNORECASE)
    if not match:
        return ""
    topic = match.group(1).strip().rstrip(".!?")
    return topic[:200]

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
        system_prompt += (
            "\n\nAlways prioritize the latest user message as the primary intent. "
            "If the latest request changes topic, do not continue earlier topics unless explicitly asked."
        )

        request_context = context.metadata.get("request_context", {})
        integrated_context = context.metadata.get("integrated_context", {})

        recent_messages = request_context.get("recent_messages", [])
        session_state = request_context.get("session_state", {})
        compact_summary = str(
            request_context.get("compact_summary")
            or (session_state.get("compact_summary") if isinstance(session_state, dict) else "")
            or ""
        ).strip()
        history_lines = _extract_recent_history_lines(recent_messages, limit=6)
        if history_lines:
            system_prompt += "\n\nRecent conversation history:\n" + "\n".join(history_lines)

        if compact_summary:
            system_prompt += "\n\nSession continuity summary:\n" + compact_summary
        else:
            session_turn_lines = _extract_session_turn_lines(session_state, limit=4)
            if session_turn_lines:
                system_prompt += "\n\nRecent session continuity:\n" + "\n".join(session_turn_lines)

        structured_sections = _build_structured_context_sections(
            request_context if isinstance(request_context, dict) else {},
            integrated_context if isinstance(integrated_context, dict) else {},
        )
        if structured_sections:
            system_prompt += "\n\n" + "\n\n".join(structured_sections)
            
        messages.append(ChatMessage(role=MessageRole.SYSTEM, content=system_prompt))

        if isinstance(recent_messages, list):
            for item in recent_messages[-6:]:
                if not isinstance(item, dict):
                    continue
                role = str(item.get("role", "")).strip().lower()
                content = str(item.get("content", "")).strip()
                if not content or _looks_like_transcript_dump(content):
                    continue
                if role == "user":
                    messages.append(ChatMessage(role=MessageRole.USER, content=content))
                elif role == "assistant":
                    messages.append(ChatMessage(role=MessageRole.ASSISTANT, content=content))

        # 4. User Message
        user_message = context.request.message if context.request else ""
        if _wants_long_form_markdown_article(user_message, recent_messages):
            requested_topic = _extract_about_topic(user_message)
            system_prompt += (
                "\n\nFor this request, produce a full-length markdown article. "
                "Use one H1 title at the top, then multiple H2 section headings with clear paragraphs. "
                "Do not return a short summary unless the user explicitly asks for brevity."
            )
            if requested_topic:
                system_prompt += (
                    f"\nFocus specifically on this topic: {requested_topic}. "
                    "Ignore unrelated earlier subjects in the conversation."
                )
            messages[0] = ChatMessage(role=MessageRole.SYSTEM, content=system_prompt)
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
        system_prompt += (
            "\n\nAlways prioritize the latest user message as the primary intent. "
            "If the latest request changes topic, do not continue earlier topics unless explicitly asked."
        )

        request_context = context.metadata.get("request_context", {})
        integrated_context = context.metadata.get("integrated_context", {})
        recent_messages = request_context.get("recent_messages", [])
        session_state = request_context.get("session_state", {})
        compact_summary = str(
            request_context.get("compact_summary")
            or (session_state.get("compact_summary") if isinstance(session_state, dict) else "")
            or ""
        ).strip()

        history_lines = _extract_recent_history_lines(recent_messages, limit=6)
        if history_lines:
            system_prompt += "\n\nRecent conversation history:\n" + "\n".join(history_lines)

        if compact_summary:
            system_prompt += "\n\nSession continuity summary:\n" + compact_summary
        else:
            session_turn_lines = _extract_session_turn_lines(session_state, limit=4)
            if session_turn_lines:
                system_prompt += "\n\nRecent session continuity:\n" + "\n".join(session_turn_lines)

        structured_sections = _build_structured_context_sections(
            request_context if isinstance(request_context, dict) else {},
            integrated_context if isinstance(integrated_context, dict) else {},
        )
        if structured_sections:
            system_prompt += "\n\n" + "\n\n".join(structured_sections)
        
        user_message = context.request.message if context.request else ""
        if _wants_long_form_markdown_article(user_message, recent_messages):
            requested_topic = _extract_about_topic(user_message)
            system_prompt += (
                "\n\nFor this request, produce a full-length markdown article. "
                "Use one H1 title at the top, then multiple H2 section headings with clear paragraphs. "
                "Do not return a short summary unless the user explicitly asks for brevity."
            )
            if requested_topic:
                system_prompt += (
                    f"\nFocus specifically on this topic: {requested_topic}. "
                    "Ignore unrelated earlier subjects in the conversation."
                )
        prompt = f"System: {system_prompt}\n\n"
        prompt += f"User: {user_message}\n\nAssistant: "
        return prompt
