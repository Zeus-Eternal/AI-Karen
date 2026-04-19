from __future__ import annotations
import logging
import time
from typing import Optional, cast, TYPE_CHECKING, List, Dict, Any
from langchain_core.messages import HumanMessage

if TYPE_CHECKING:
    from ..models import ProcessingResult, ChatRequest, ProcessingContext, ErrorType
    from ..base import ChatOrchestratorProtocol
else:
    Base = object


class ChatAgentMixin(Base):
    """Integrates LangGraph-powered agentic workflows into the unified ChatOrchestrator."""

    async def _execute_agent_loop(
        self,
        request: ChatRequest,
        context: ProcessingContext,
        event_emitter: Optional[Any] = None,
    ) -> ProcessingResult:
        """
        Execute bounded agent loop with step tracking and event emission.

        This method implements a bounded iteration loop that:
        - Calls LangGraph to get next action
        - Executes action through proper service (tool, extension, internet, memory)
        - Updates working state and context
        - Emits step events for streaming
        - Returns when action is ANSWER, TERMINATE, or max steps reached
        """
        from ai_karen_engine.core.langgraph_orchestrator import (
            LangGraphOrchestrator,
            OrchestrationConfig,
        )
        from ai_karen_engine.chat.agent_action_models import (
            AgentAction,
            AgentActionType,
            AgentTrace,
            WebSearchResult,
            ExtensionExecutionResult,
            Citation,
            AgentExecutionTrace,
            AgentStep,
        )
        from ai_karen_engine.config.config_manager import get_config

        config = get_config()
        agent_config = config.agent_runtime

        max_steps = agent_config.max_agent_steps
        max_web_searches = agent_config.max_web_searches
        web_search_count = 0
        tool_invocation_count = 0
        step_count = 0

        agent_trace = AgentTrace(
            correlation_id=context.correlation_id, status="in_progress"
        )

        working_state = {
            "messages": [HumanMessage(content=request.message)],
            "user_id": request.user_id,
            "session_id": request.session_id or request.conversation_id,
            "tenant_id": request.metadata.get("org_id", "default"),
            "auth_context": request.metadata.get("auth_context", {}),
            "request_config": request.metadata,
            "errors": [],
            "warnings": [],
            "context_updates": [],
        }

        try:
            agent_engine = LangGraphOrchestrator(
                config=OrchestrationConfig(
                    checkpoint_enabled=True,
                    enable_auth_gate=False,
                    enable_safety_gate=False,
                ),
                memory_service=self.memory_service,
                tool_service=self.tool_integration_service,
            )

            logger.info(
                f"Starting agent loop for {context.correlation_id} with max {max_steps} steps"
            )

            while step_count < max_steps:
                step_count += 1

                try:
                    current_state = await agent_engine.graph.ainvoke(working_state)

                    action_data = current_state.get("next_action", {})
                    if not action_data and not current_state.get("response"):
                        action_data = {
                            "action": "answer",
                            "reason": "No explicit action needed",
                        }

                    action = AgentAction(
                        action=action_data.get("action", "answer"),
                        reason=action_data.get("reason", ""),
                        tool=action_data.get("tool"),
                        extension_id=action_data.get("extension_id"),
                        params=action_data.get("params", {}),
                        confidence=action_data.get("confidence", 1.0),
                        correlation_id=context.correlation_id,
                    )

                    agent_trace.actions.append(
                        {
                            "step": step_count,
                            "action_type": action.action.value,
                            "reason": action.reason,
                            "tool": action.tool,
                            "confidence": action.confidence,
                            "timestamp": time.time(),
                        }
                    )

                    if event_emitter:
                        await event_emitter(
                            {
                                "type": "agent_step_started",
                                "step_id": action.step_id,
                                "action_type": action.action.value,
                                "step_count": step_count,
                                "max_steps": max_steps,
                                "metadata": {
                                    "reason": action.reason,
                                    "tool": action.tool,
                                    "confidence": action.confidence,
                                },
                            }
                        )

                    if action.action == AgentActionType.ANSWER:
                        agent_trace.status = "completed"
                        agent_trace.end_time = time.time()
                        agent_trace.total_steps = step_count

                        response = current_state.get("response", "")
                        if event_emitter:
                            await event_emitter(
                                {
                                    "type": "agent_step_completed",
                                    "step_id": action.step_id,
                                    "action_type": "answer",
                                    "metadata": {"response_length": len(response)},
                                }
                            )

                        return ProcessingResult(
                            success=not bool(current_state.get("errors")),
                            response=response,
                            structured_content=current_state.get(
                                "response_metadata", {}
                            ).get("structured_content")
                            or {},
                            actions=current_state.get("response_metadata", {}).get(
                                "actions"
                            )
                            or current_state.get("tool_calls")
                            or [],
                            llm_metadata={
                                "engine": "langgraph",
                                "intent": current_state.get("detected_intent"),
                                "confidence": current_state.get("intent_confidence"),
                                **current_state.get("response_metadata", {}),
                                "agent_trace": agent_trace.model_dump(),
                            },
                            processing_time=current_state.get(
                                "response_metadata", {}
                            ).get("duration", 0.0),
                            used_fallback=False,
                            context={"agent_trace": agent_trace.model_dump()},
                            correlation_id=context.correlation_id,
                        )

                    elif action.action == AgentActionType.SEARCH_WEB:
                        if web_search_count >= max_web_searches:
                            working_state["errors"].append(
                                f"Max web searches ({max_web_searches}) exceeded"
                            )
                            break

                        web_search_count += 1

                        if event_emitter:
                            await event_emitter(
                                {
                                    "type": "web_search_started",
                                    "step_id": action.step_id,
                                    "query": action.params.get(
                                        "query", request.message
                                    ),
                                }
                            )

                        search_result = await self._execute_web_search(
                            action, request, context
                        )

                        if event_emitter:
                            await event_emitter(
                                {
                                    "type": "web_search_sources_found",
                                    "step_id": action.step_id,
                                    "sources_count": len(
                                        search_result.sources
                                        if hasattr(search_result, "sources")
                                        else search_result.get("results", [])
                                    ),
                                    "metadata": {
                                        "execution_time_ms": search_result.execution_time_ms
                                        if hasattr(search_result, "execution_time_ms")
                                        else search_result.get("metadata", {}).get(
                                            "execution_time_ms", 0
                                        )
                                    },
                                }
                            )

                        if (
                            hasattr(search_result, "citations")
                            and search_result.citations
                        ):
                            if event_emitter:
                                await event_emitter(
                                    {
                                        "type": "citation_bundle_ready",
                                        "step_id": action.step_id,
                                        "citations": [
                                            c.model_dump()
                                            if hasattr(c, "model_dump")
                                            else c
                                            for c in search_result.citations
                                        ],
                                        "sources_count": len(search_result.citations),
                                        "metadata": {"query": search_result.query},
                                    }
                                )

                        working_state["context_updates"].append(
                            {
                                "type": "web_search",
                                "data": search_result.model_dump()
                                if hasattr(search_result, "model_dump")
                                else search_result,
                            }
                        )

                    elif action.action == AgentActionType.CALL_TOOL:
                        tool_invocation_count += 1
                        if tool_invocation_count > agent_config.max_tool_invocations:
                            working_state["errors"].append(
                                f"Max tool invocations ({agent_config.max_tool_invocations}) exceeded"
                            )
                            break

                        if event_emitter:
                            await event_emitter(
                                {
                                    "type": "tool_execution_started",
                                    "step_id": action.step_id,
                                    "tool_name": action.tool,
                                }
                            )

                        tool_result = await self._execute_tool_action(action, context)

                        if event_emitter:
                            await event_emitter(
                                {
                                    "type": "tool_execution_completed",
                                    "step_id": action.step_id,
                                    "tool_name": action.tool,
                                    "metadata": {
                                        "success": tool_result.get("success", False)
                                    },
                                }
                            )

                        working_state["context_updates"].append(
                            {"type": "tool_result", "data": tool_result}
                        )

                    elif action.action == AgentActionType.USE_EXTENSION:
                        if event_emitter:
                            await event_emitter(
                                {
                                    "type": "extension_execution_started",
                                    "step_id": action.step_id,
                                    "extension_id": action.extension_id,
                                }
                            )

                        extension_result = await self._execute_extension_action(
                            action, context
                        )

                        if event_emitter:
                            await event_emitter(
                                {
                                    "type": "extension_execution_completed",
                                    "step_id": action.step_id,
                                    "extension_id": action.extension_id,
                                    "metadata": {"success": extension_result.success},
                                }
                            )

                        working_state["context_updates"].append(
                            {
                                "type": "extension_result",
                                "data": extension_result.model_dump(),
                            }
                        )

                    elif action.action == AgentActionType.TERMINATE:
                        agent_trace.status = "terminated"
                        agent_trace.end_time = time.time()
                        agent_trace.total_steps = step_count

                        return ProcessingResult(
                            success=True,
                            response=action.reason or "Agent terminated",
                            context={"agent_trace": agent_trace.model_dump()},
                            correlation_id=context.correlation_id,
                        )

                except Exception as step_exc:
                    logger.error(
                        f"Agent step {step_count} failed: {step_exc}", exc_info=True
                    )
                    working_state["errors"].append(
                        f"Step {step_count} error: {str(step_exc)}"
                    )
                    break

            agent_trace.status = "max_steps_reached"
            agent_trace.end_time = time.time()
            agent_trace.total_steps = step_count

            fallback_response = f"Agent execution completed after {step_count} steps. "
            if working_state.get("errors"):
                fallback_response += (
                    f"Errors encountered: {'; '.join(working_state['errors'][-2:])}"
                )

            return ProcessingResult(
                success=not bool(working_state.get("errors")),
                response=fallback_response,
                context={"agent_trace": agent_trace.model_dump()},
                correlation_id=context.correlation_id,
                error_type=ErrorType.UNKNOWN_ERROR
                if working_state.get("errors")
                else None,
            )

        except Exception as exc:
            logger.error(
                f"Agent loop failed for {context.correlation_id}: {exc}", exc_info=True
            )
            agent_trace.status = "failed"
            agent_trace.end_time = time.time()
            agent_trace.total_steps = step_count

            return ProcessingResult(
                success=False,
                error=str(exc),
                error_type=ErrorType.UNKNOWN_ERROR,
                context={"agent_trace": agent_trace.model_dump()},
                correlation_id=context.correlation_id,
            )

    async def _execute_web_search(
        self, action, request: ChatRequest, context: ProcessingContext
    ) -> WebSearchResult:  # Changed return type
        """Execute web search action through InternetCapabilityService."""
        from ai_karen_engine.services.internet_capability_service import (
            InternetCapabilityService,
        )

        internet_service = InternetCapabilityService()
        query = action.params.get("query", request.message)

        try:
            result = await internet_service.execute(query)
            return result
        except Exception as e:
            logger.error(f"Web search failed: {e}", exc_info=True)
            return WebSearchResult(
                query=query,
                mode="general",
                sources=[],
                citations=[],
                metadata={"error": str(e), "status": "failed"},
                execution_time_ms=0,
            )

    async def _execute_tool_action(
        self, action, context: ProcessingContext
    ) -> Dict[str, Any]:
        """Execute tool action through ToolIntegrationService."""
        if not self.tool_integration_service:
            return {"success": False, "error": "Tool integration service not available"}

        try:
            result = await self.tool_integration_service.execute_tool(
                tool_name=action.tool,
                params=action.params,
                user_id=context.user_id,
                correlation_id=context.correlation_id,
            )
            return result
        except Exception as e:
            logger.error(f"Tool execution failed: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    async def _execute_extension_action(self, action, context: ProcessingContext):
        """Execute extension action through PluginManager."""
        from ai_karen_engine.extensions.platform.core.integration.manager import (
            PluginManager,
        )

        try:
            plugin_manager = PluginManager()
            result = await plugin_manager.dispatch_agent_action(action, context)
            return result
        except Exception as e:
            logger.error(f"Extension execution failed: {e}", exc_info=True)
            from ai_karen_engine.chat.agent_action_models import (
                ExtensionExecutionResult,
            )

            return ExtensionExecutionResult(
                extension_id=action.extension_id or "unknown",
                success=False,
                error=str(e),
            )

    async def _orchestrate_agentic_workflow(
        self, request: ChatRequest, context: ProcessingContext
    ) -> Optional[ProcessingResult]:
        """
        Delegate to bounded agent loop with step tracking and event emission.
        """
        try:
            event_emitter = getattr(context, "event_emitter", None)
            result = await self._execute_agent_loop(request, context, event_emitter)
            return result

        except Exception as exc:
            logger.error(
                f"Agentic delegation failed for {context.correlation_id}: {exc}",
                exc_info=True,
            )
            return None
