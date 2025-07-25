"""
AI Orchestrator Service for AI Karen Engine.
This service coordinates AI processing, decision-making, and workflow orchestration.
It converts TypeScript AI flows to Python services while maintaining compatibility
with the existing AI Karen architecture.
"""

from typing import Any, Dict, List, Optional

from ai_karen_engine.core.services.base import BaseService, ServiceConfig
from ai_karen_engine.integrations.llm_router import LLMProfileRouter
from ai_karen_engine.integrations.llm_utils import LLMUtils
from ai_karen_engine.models.shared_types import (  # ← ensure FlowType is imported
    AiData, DecideActionInput, FlowInput, FlowOutput, FlowType, PluginInfo,
    ToolType)

from .context_manager import ContextManager
from .decision_engine import DecisionEngine
from .flow_manager import FlowManager
from .prompt_manager import PromptManager


class AIOrchestrator(BaseService):
    """
    Central AI Orchestrator Service that coordinates AI processing and workflows.
    """

    def __init__(self, config: ServiceConfig):
        super().__init__(config)
        self.flow_manager = FlowManager()
        self.decision_engine = DecisionEngine()
        self.context_manager = ContextManager()
        self.prompt_manager = PromptManager()
        self.llm_utils = LLMUtils()
        self.llm_router = LLMProfileRouter()
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the AI Orchestrator service."""
        try:
            self.logger.info("Initializing AI Orchestrator Service")
            await self._register_default_flows()
            self._initialized = True
            self.logger.info("AI Orchestrator Service initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize AI Orchestrator: {e}")
            raise

    async def start(self) -> None:
        if not self._initialized:
            raise RuntimeError("Service not initialized")
        self.logger.info("AI Orchestrator Service started")

    async def stop(self) -> None:
        self.logger.info("Stopping AI Orchestrator Service")
        self.context_manager.clear_context_cache()
        self.logger.info("AI Orchestrator Service stopped")

    async def health_check(self) -> bool:
        return self._initialized and len(self.flow_manager.get_available_flows()) > 0

    async def _register_default_flows(self) -> None:
        """Register default flow handlers."""
        self.flow_manager.register_flow(
            FlowType.DECIDE_ACTION,
            self._handle_decide_action_flow,
            {"description": "Decision-making flow for determining next actions"},
        )
        self.flow_manager.register_flow(
            FlowType.CONVERSATION_PROCESSING,
            self._handle_conversation_processing_flow,
            {
                "description": "Comprehensive conversation processing with memory integration"
            },
        )
        self.logger.info("Default flows registered")

    async def _handle_decide_action_flow(self, input_data: FlowInput) -> FlowOutput:
        """Handle decide action flow processing."""
        decide_input = DecideActionInput(
            prompt=input_data.prompt,
            short_term_memory=input_data.short_term_memory,
            long_term_memory=input_data.long_term_memory,
            personal_facts=input_data.personal_facts,
        )
        result = await self.decision_engine.decide_action(decide_input)
        return FlowOutput(
            response=result.intermediate_response,
            requires_plugin=result.tool_to_call != ToolType.NONE,
            tool_to_call=result.tool_to_call,
            tool_input=result.tool_input,
            suggested_new_facts=result.suggested_new_facts,
            proactive_suggestion=result.proactive_suggestion,
        )

    async def _handle_conversation_processing_flow(
        self, input_data: FlowInput
    ) -> FlowOutput:
        """Handle conversation processing flow with memory, plugins, and proactive suggestions."""
        try:
            context = await self.context_manager.build_context(
                user_id=input_data.user_id,
                session_id=input_data.session_id,
                prompt=input_data.prompt,
                conversation_history=input_data.conversation_history,
                user_settings=input_data.user_settings,
                memories=input_data.context_from_memory,
            )

            response = await self._process_conversation_with_memory(input_data, context)

            requires_plugin, plugin_to_execute, plugin_parameters = (
                await self._assess_plugin_needs(
                    input_data.prompt, context, input_data.available_plugins or []
                )
            )

            memory_to_store = await self._identify_memory_to_store(input_data, context)

            proactive_suggestion = (
                await self._generate_conversation_proactive_suggestion(
                    input_data, context
                )
            )

            ai_data = await self._generate_conversation_ai_data(input_data, context)

            return FlowOutput(
                response=response,
                requires_plugin=requires_plugin,
                plugin_to_execute=plugin_to_execute,
                plugin_parameters=plugin_parameters,
                memory_to_store=memory_to_store,
                proactive_suggestion=proactive_suggestion,
                ai_data=ai_data,
            )
        except Exception as e:
            self.logger.error(f"Conversation processing flow failed: {e}")
            return FlowOutput(
                response="I'm experiencing some technical difficulties. Let me try a simpler response.",
                requires_plugin=False,
                ai_data=AiData(
                    confidence=0.3, reasoning="Fallback due to processing error"
                ),
            )

    async def _process_conversation_with_memory(
        self, input_data: FlowInput, context: Dict[str, Any]
    ) -> str:
        """Process conversation using LLM with memory/context awareness."""
        try:
            template = self.prompt_manager.get_template("conversation_processing")
            if not template:
                raise ValueError("conversation_processing template missing")

            user_prompt = template["user_template"].format(
                prompt=input_data.prompt,
                context_info=context.get("context_summary", ""),
                plugin_info=", ".join(
                    p.name for p in input_data.available_plugins or []
                ),
                memory_info="; ".join(
                    mem.get("content", "") for mem in context.get("memories", [])[:3]
                ),
                user_preferences=", ".join(
                    f"{k}={v}" for k, v in input_data.user_settings.items()
                ),
            )
            full_prompt = f"{template['system_prompt']}\n\n{user_prompt}"

            raw = self.llm_router.invoke(
                self.llm_utils,
                full_prompt,
                task_intent=FlowType.CONVERSATION_PROCESSING.value,
            )
            if not isinstance(raw, str):
                raise TypeError("LLM response must be text")
            response = raw.strip()
            if not response:
                return await self._fallback_conversation_response(input_data, context)

            return response[:4000] if len(response) > 4000 else response
        except Exception as ex:
            self.logger.error(f"LLM processing failed: {ex}")
            provider_missing = isinstance(ex, RuntimeError) and "no provider for intent" in str(ex).lower()
            return await self._fallback_conversation_response(
                input_data, context, provider_missing=provider_missing
            )

    async def _fallback_conversation_response(
        self,
        input_data: FlowInput,
        context: Dict[str, Any],
        provider_missing: bool = False,
    ) -> str:
        """Fallback rule-based conversation processing used if LLM fails."""
        settings = context.get("user_settings", {})
        tone = settings.get("personality_tone", "friendly")
        persona = settings.get("custom_persona_instructions", "").strip()

        prefix_parts = []
        if persona:
            prefix_parts.append(persona)
        if tone:
            prefix_parts.append(f"{tone} tone")
        prefix = " ".join(prefix_parts)
        if prefix:
            prefix += ": "

        base_msg = ""
        if provider_missing:
            base_msg = "My language model is unavailable so I'll reply directly. "

        prompt_lower = input_data.prompt.lower()
        if "help" in prompt_lower:
            reply = (
                "I'm here to assist. I can access plugins and remember our conversations to help you better."
            )
        elif "thank" in prompt_lower:
            reply = "You're welcome! I'm glad I could help."
        else:
            reply = f"I've registered your message: '{input_data.prompt}'. How can I further assist you?"

        return f"{prefix}{base_msg}{reply}"

    async def _assess_plugin_needs(
        self, prompt: str, context: Dict[str, Any], available_plugins: List[PluginInfo]
    ) -> tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """Assess if the user's request requires plugin execution."""
        # Placeholder for more sophisticated plugin routing logic
        return False, None, None

    async def _identify_memory_to_store(
        self, input_data: FlowInput, context: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Identify important information to store in memory."""
        prompt_lower = input_data.prompt.lower()
        if any(
            keyword in prompt_lower for keyword in ["remember", "my name is", "i like"]
        ):
            return {
                "content": input_data.prompt,
                "tags": ["personal_info", "explicit_request"],
                "metadata": {"importance": "high"},
            }
        return None

    async def _generate_conversation_proactive_suggestion(
        self, input_data: FlowInput, context: Dict[str, Any]
    ) -> Optional[str]:
        """Generate proactive suggestions based on the conversation."""
        if len(input_data.conversation_history) > 4:
            return "We've been chatting for a bit. Is there a specific task I can help you with?"
        return None

    async def _generate_conversation_ai_data(
        self, input_data: FlowInput, context: Dict[str, Any]
    ) -> AiData:
        """Generate AI metadata for the conversation processing."""
        return AiData(
            confidence=0.85,
            reasoning="Response generated by primary LLM with context.",
            knowledge_graph_insights=context.get("context_summary"),
        )

    # ─────────────────────────────────────────────────────────────────────────────
    # Public API methods exposed to the rest of the system:
    async def process_flow(
        self, flow_type: FlowType, input_data: FlowInput
    ) -> FlowOutput:
        return await self.flow_manager.execute_flow(flow_type, input_data)

    async def conversation_processing_flow(self, input_data: FlowInput) -> FlowOutput:
        """Execute the conversation processing flow."""
        return await self.process_flow(FlowType.CONVERSATION_PROCESSING, input_data)

    # ─────────────────────────────────────────────────────────────────────────────

    def get_metrics(self) -> Dict[str, Any]:
        """Get service metrics including flow statistics."""
        base_metrics = super().get_metrics()
        flow_metrics: Dict[str, Any] = {}
        for flow_type in FlowType:
            stats = self.flow_manager.get_flow_stats(flow_type)
            if stats:
                flow_metrics[flow_type.value] = stats
        base_metrics["flows"] = flow_metrics
        return base_metrics
