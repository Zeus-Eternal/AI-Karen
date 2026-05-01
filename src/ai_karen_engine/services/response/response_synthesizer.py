from __future__ import annotations

from typing import Any

from ai_karen_engine.services.models.routing.llm_router_service import ChatRequest

from .response_contracts import ResponseContract
from .response_prompt_builder import ResponsePromptBuilder
from .response_sanitizer import ResponseSanitizer


class ResponseSynthesizer:
    def __init__(self, llm_router: Any):
        self.llm_router = llm_router
        self.prompt_builder = ResponsePromptBuilder()
        self.sanitizer = ResponseSanitizer()

    async def synthesize(self, contract: ResponseContract, *, user_preferences: dict[str, Any] | None = None, conversation_id: str | None = None, stream: bool = False) -> tuple[str, dict[str, Any]]:
        prefs = user_preferences or {}
        request = ChatRequest(
            message=contract.latest_user_message,
            context={
                "messages": self.prompt_builder.build_messages(contract),
                "response_contract": {"purpose": contract.purpose},
                "tool_results": contract.tool_results,
                "specialist_findings": contract.specialist_findings,
                "reasoning_summary": contract.reasoning_summary,
                "runtime_metadata": contract.runtime_metadata,
            },
            stream=stream,
            preferred_model=prefs.get("preferred_model"),
            conversation_id=conversation_id,
        )
        text = ""
        metadata: dict[str, Any] = {}
        async for chunk in self.llm_router.process_chat_request(request, user_preferences=prefs):
            if isinstance(chunk, str):
                text += chunk
            elif isinstance(chunk, dict) and isinstance(chunk.get("metadata"), dict):
                metadata.update(chunk["metadata"])
        return self.sanitizer.sanitize(text), metadata
