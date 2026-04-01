"""
This module contains utility methods for the ChatOrchestrator.
"""
import asyncio
import logging
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from ai_karen_engine.hooks.models import HookContext, HookExecutionSummary

if TYPE_CHECKING:
    from ai_karen_engine.chat.ChatOrchestrator.base import ChatOrchestratorProtocol
    Base = ChatOrchestratorProtocol
else:
    Base = object

logger = logging.getLogger(__name__)


class ChatUtilityMixin(Base):
    """A mixin for utility methods in the ChatOrchestrator."""

    _hook_timeout_seconds: float

    async def _trigger_hooks_with_timeout(
        self,
        hook_manager: Any,
        hook_context: HookContext,
    ) -> HookExecutionSummary:
        """Run hooks with a bounded timeout so chat completion cannot hang indefinitely."""
        from ai_karen_engine.hooks.models import HookExecutionSummary

        try:
            return await asyncio.wait_for(
                hook_manager.trigger_hooks(hook_context),
                timeout=self._hook_timeout_seconds,
            )
        except Exception as exc:
            logger.warning(
                "Hook execution failed or timed out for %s: %s",
                hook_context.hook_type,
                exc,
            )
            return HookExecutionSummary(
                hook_type=hook_context.hook_type,
                total_hooks=0,
                successful_hooks=0,
                failed_hooks=0,
                total_execution_time_ms=0.0,
                results=[],
            )

    def _add_local_prefix(self, prompt: str, provider: Optional[str]) -> str:
        """Add Assistant: prefix for local models to prevent truncation."""
        if not provider:
            return prompt
            
        local_providers = ["llamacpp", "local", "small_language_model", "transformers"]
        if any(p in provider.lower() for p in local_providers):
            if not prompt.rstrip().endswith("Assistant:"):
                return prompt.rstrip() + "\n\nAssistant: "
        return prompt

    def _resolve_provider_aliases(self, provider: Optional[str]) -> List[str]:
        """Return canonical provider aliases used across settings, registry, and runtime."""
        raw = (provider or "").strip()
        if not raw:
            return []

        aliases: List[str] = [raw]
        normalized = raw.replace("_", "-").lower()
        canonical_map = {
            "llama-cpp": "llamacpp",
            "llama_cpp": "llamacpp",
            "llamacpp": "llamacpp",
            "local": "local",
        }
        canonical = canonical_map.get(normalized)
        if canonical and canonical not in aliases:
            aliases.append(canonical)

        if canonical == "llamacpp" and "local" not in aliases:
            aliases.append("local")

        return aliases

    def _get_model_display_name(self, model_id: Optional[str]) -> Optional[str]:
        """Return a human-friendly name for a given model ID."""
        if not model_id:
            return None
        
        # Mapping of common IDs to friendly names
        mapping = {
            "phi-3-mini-4k-instruct-q4.gguf": "Phi-3 Mini",
            "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf": "TinyLlama 1.1B",
            "tinyllama-1.1b-chat-v2.0.Q4_K_M.gguf": "TinyLlama 1.1B v2",
            "gemini-1.5-pro": "Gemini 1.5 Pro",
            "gemini-1.5-flash": "Gemini 1.5 Flash",
            "claude-3-opus-20240229": "Claude 3 Opus",
            "claude-3-sonnet-20240229": "Claude 3 Sonnet",
            "claude-3-haiku-20240307": "Claude 3 Haiku",
            "gpt-4o": "GPT-4o",
            "gpt-4-turbo": "GPT-4 Turbo",
        }
        
        if model_id in mapping:
            return mapping[model_id]
        
        # Fallback: prettify the ID
        name = model_id
        if name.endswith(".gguf"):
            name = name[:-5]
        
        # Replace common separators with spaces and title case
        name = name.replace("-", " ").replace("_", " ").replace("/", " / ")
        words = name.split()
        
        # Keep some words uppercase
        upper_words = {"llm", "ai", "gpt", "api", "url", "id", "cls", "r1"}
        processed_words = [
            w.upper() if w.lower() in upper_words else w.capitalize()
            for w in words
        ]
        
        return " ".join(processed_words)
