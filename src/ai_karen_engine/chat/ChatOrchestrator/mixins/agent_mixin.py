from __future__ import annotations
import logging
from typing import Optional, cast, TYPE_CHECKING
from langchain_core.messages import HumanMessage

if TYPE_CHECKING:
    from ..models import ProcessingResult, ChatRequest, ProcessingContext, ErrorType
    from ..base import ChatOrchestratorProtocol
    Base = ChatOrchestratorProtocol
else:
    Base = object


class ChatAgentMixin(Base):
    """Integrates LangGraph-powered agentic workflows into the unified ChatOrchestrator."""

    async def _orchestrate_agentic_workflow(
        self,
        request: ChatRequest,
        context: ProcessingContext
    ) -> Optional[ProcessingResult]:
        """
        Delegate to LangGraphOrchestrator for complex, multi-step, or tool-heavy reasoning.
        """
        try:
            from ai_karen_engine.core.langgraph_orchestrator import LangGraphOrchestrator, OrchestrationConfig
            
            agent_engine = LangGraphOrchestrator(
                config=OrchestrationConfig(
                    checkpoint_enabled=True,
                    enable_auth_gate=False,
                    enable_safety_gate=False,
                ),
                memory_service=self.memory_service,
                tool_service=self.tool_integration_service,
            )
            
            messages = [HumanMessage(content=request.message)]
            
            initial_state = {
                "messages": messages,
                "user_id": request.user_id,
                "session_id": request.session_id or request.conversation_id,
                "tenant_id": request.metadata.get("org_id", "default"),
                "auth_context": request.metadata.get("auth_context", {}),
                "request_config": request.metadata,
                "errors": [],
                "warnings": []
            }
            
            logger.info(f"Delegating to LangGraph agent for {context.correlation_id}")
            final_state = await agent_engine.graph.ainvoke(initial_state)
            
            return ProcessingResult(
                success=not bool(final_state.get("errors")),
                response=final_state.get("response", ""),
                structured_content=final_state.get("response_metadata", {}).get("structured_content") or {},
                actions=final_state.get("response_metadata", {}).get("actions") or final_state.get("tool_calls") or [],
                llm_metadata={
                    "engine": "langgraph",
                    "intent": final_state.get("detected_intent"),
                    "confidence": final_state.get("intent_confidence"),
                    **final_state.get("response_metadata", {})
                },
                processing_time=final_state.get("response_metadata", {}).get("duration", 0.0),
                used_fallback=False,
                context={"agent_trace": final_state.get("intent_analysis", {})},
                correlation_id=context.correlation_id,
            )
            
        except Exception as exc:
            logger.error(f"Agentic delegation failed for {context.correlation_id}: {exc}", exc_info=True)
            return None
