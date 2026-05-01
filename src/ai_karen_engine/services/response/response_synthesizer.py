from __future__ import annotations

import logging
from typing import Any

class ResponseSynthesizer:
    def __init__(self, llm_router: Any):
        self.llm_router = llm_router
        self.prompt_builder = ResponsePromptBuilder()
        self.sanitizer = ResponseSanitizer()
        self.validator = ResponseValidator()

    async def synthesize(self, contract: ResponseContract, *, user_preferences: dict[str, Any] | None = None, conversation_id: str | None = None, stream: bool = False) -> tuple[str, dict[str, Any]]:
        from ai_karen_engine.services.models.routing.llm_router_service import ChatRequest
        
        prefs = user_preferences or {}
        
        # Determine intent and subtype if not already set
        if contract.intent == "general.chat" and not contract.subtype:
            from ai_karen_engine.core.cortex.routing_intents import resolve_capability_decision
            decision = resolve_capability_decision(contract.latest_user_message)
            contract.intent = decision.intent
            contract.subtype = decision.subtype

        request = ChatRequest(
            message=contract.latest_user_message,
            intent=contract.intent,
            subtype=contract.subtype,
            response_mode=contract.response_mode,
            context={
                "messages": self.prompt_builder.build_messages(contract),
                "response_contract": {"purpose": contract.purpose, "intent": contract.intent, "subtype": contract.subtype},
                "tool_results": contract.tool_results,
                "specialist_findings": contract.specialist_findings,
                "reasoning_summary": contract.reasoning_summary,
                "runtime_metadata": contract.runtime_metadata,
            },
            stream=stream,
            preferred_model=prefs.get("preferred_model"),
            conversation_id=conversation_id,
        )

        text, metadata = await self._invoke_router(request, prefs)
        
        # Validation and potential retry
        validation = self.validator.validate(text, contract)
        if not validation.valid:
            logger.warning(f"Response validation failed: {validation.reason}. Attempting retry with stricter contract.")
            
            # Stricter contract for retry
            contract.disallow_unrequested_menu = True
            contract.disallow_debug_prefixes = True
            
            retry_request = ChatRequest(
                message=contract.latest_user_message,
                intent=contract.intent,
                subtype=contract.subtype,
                response_mode=contract.response_mode,
                context={
                    "messages": self.prompt_builder.build_messages(contract),
                    "retry_attempt": 1,
                    "previous_error": validation.reason,
                },
                stream=stream,
                conversation_id=conversation_id,
            )
            
            text, metadata = await self._invoke_router(retry_request, prefs)
            
            # Final validation check
            final_validation = self.validator.validate(text, contract)
            if not final_validation.valid:
                logger.error(f"Response validation failed again after retry: {final_validation.reason}")
                # We could potentially try another model here, but for now let's just return what we have or a fallback message
                if contract.purpose == "chat" and not text:
                     text = "I'm sorry, I'm having trouble generating a valid response right now. Please try again or switch models."

        return self.sanitizer.sanitize(text), metadata

    async def _invoke_router(self, request: ChatRequest, prefs: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        text = ""
        metadata: dict[str, Any] = {}
        async for chunk in self.llm_router.process_chat_request(request, user_preferences=prefs):
            if isinstance(chunk, str):
                text += chunk
            elif isinstance(chunk, dict) and isinstance(chunk.get("metadata"), dict):
                metadata.update(chunk["metadata"])
        return text, metadata
