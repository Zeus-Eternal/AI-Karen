"""
AI Orchestrator Service for AI Karen Engine.

This service coordinates AI processing, decision-making, and workflow orchestration.
It converts TypeScript AI flows to Python services while maintaining compatibility
with the existing AI Karen architecture.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime

from ai_karen_engine.core.services.base import BaseService, ServiceConfig
from ai_karen_engine.models.shared_types import (
    FlowType, FlowInput, FlowOutput, DecideActionInput, DecideActionOutput,
    ToolType, ToolInput, MemoryDepth, PersonalityTone, PersonalityVerbosity,
    AiData, MemoryContext, PluginInfo
)
from ai_karen_engine.integrations.llm_router import LLMProfileRouter
from ai_karen_engine.integrations.llm_utils import LLMUtils

from .flow_manager import FlowManager
from .decision_engine import DecisionEngine
from .context_manager import ContextManager
from .prompt_manager import PromptManager


# FlowManager
# ---

# DecisionEngine
# ---

# ContextManager
# ---

# PromptManager
# ---

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
            {"description": "Decision-making flow for determining next actions"}
        )
        self.flow_manager.register_flow(
            FlowType.CONVERSATION_PROCESSING,
            self._handle_conversation_processing_flow,
            {"description": "Comprehensive conversation processing with memory integration"}
        )
        self.logger.info("Default flows registered")
    
    async def _handle_decide_action_flow(self, input_data: FlowInput) -> FlowOutput:
        """Handle decide action flow processing."""
        decide_input = DecideActionInput(
            prompt=input_data.prompt,
            short_term_memory=input_data.short_term_memory,
            long_term_memory=input_data.long_term_memory,
            personal_facts=input_data.personal_facts
        )
        result = await self.decision_engine.decide_action(decide_input)
        return FlowOutput(
            response=result.intermediate_response,
            requires_plugin=result.tool_to_call != ToolType.NONE,
            tool_to_call=result.tool_to_call,
            tool_input=result.tool_input,
            suggested_new_facts=result.suggested_new_facts,
            proactive_suggestion=result.proactive_suggestion
        )
    
    async def _handle_conversation_processing_flow(self, input_data: FlowInput) -> FlowOutput:
        """Handle conversation processing flow with memory, plugins, and proactive suggestions."""
        try:
            context = await self.context_manager.build_context(
                user_id=input_data.user_id, session_id=input_data.session_id,
                prompt=input_data.prompt, conversation_history=input_data.conversation_history,
                user_settings=input_data.user_settings, memories=input_data.context_from_memory
            )
            
            response = await self._process_conversation_with_memory(input_data, context)
            
            requires_plugin, plugin_to_execute, plugin_parameters = await self._assess_plugin_needs(
                input_data.prompt, context, input_data.available_plugins or []
            )
            
            memory_to_store = await self._identify_memory_to_store(input_data, context)
            
            proactive_suggestion = await self._generate_conversation_proactive_suggestion(input_data, context)
            
            ai_data = await self._generate_conversation_ai_data(input_data, context)
            
            return FlowOutput(
                response=response,
                requires_plugin=requires_plugin,
                plugin_to_execute=plugin_to_execute,
                plugin_parameters=plugin_parameters,
                memory_to_store=memory_to_store,
                proactive_suggestion=proactive_suggestion,
                ai_data=ai_data
            )
        except Exception as e:
            self.logger.error(f"Conversation processing flow failed: {e}")
            return FlowOutput(
                response="I'm experiencing some technical difficulties. Let me try a simpler response.",
                requires_plugin=False,
                ai_data=AiData(confidence=0.3, reasoning="Fallback due to processing error")
            )

    async def _process_conversation_with_memory(self, input_data: FlowInput, context: Dict[str, Any]) -> str:
        """Process conversation using LLM with memory/context awareness."""
        try:
            template = self.prompt_manager.get_template("conversation_processing")
            if not template:
                raise ValueError("conversation_processing template missing")

            user_prompt = template["user_template"].format(
                prompt=input_data.prompt,
                context_info=context.get("context_summary", ""),
                plugin_info=", ".join(p.name for p in input_data.available_plugins or []),
                memory_info="; ".join(mem.get("content", "") for mem in context.get("memories", [])[:3]),
                user_preferences=", ".join(f"{k}={v}" for k, v in input_data.user_settings.items()),
            )
            full_prompt = f"{template['system_prompt']}\n\n{user_prompt}"

            raw = self.llm_router.invoke(self.llm_utils, full_prompt, task_intent="chat")
            if not isinstance(raw, str):
                raise TypeError("LLM response must be text")
            response = raw.strip()
            if not response:
                return await self._fallback_conversation_response(input_data, context)
            
            return response[:4000] if len(response) > 4000 else response
        except Exception as ex:
            self.logger.error(f"LLM processing failed: {ex}")
            return await self._fallback_conversation_response(input_data, context)

    async def _fallback_conversation_response(self, input_data: FlowInput, context: Dict[str, Any]) -> str:
        """Fallback rule-based conversation processing used if LLM fails."""
        prompt_lower = input_data.prompt.lower()
        if "help" in prompt_lower:
            return "I'm here to assist. I can access plugins and remember our conversations to help you better."
        elif "thank" in prompt_lower:
            return "You're welcome! I'm glad I could help."
        else:
            return f"I've registered your message: '{input_data.prompt}'. How can I further assist you?"

    async def _assess_plugin_needs(
        self, prompt: str, context: Dict[str, Any], available_plugins: List[PluginInfo]
    ) -> tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """Assess if the user's request requires plugin execution."""
        # This is a placeholder for more sophisticated plugin routing logic
        return False, None, None
    
    async def _identify_memory_to_store(self, input_data: FlowInput, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Identify important information to store in memory."""
        prompt_lower = input_data.prompt.lower()
        if any(keyword in prompt_lower for keyword in ["remember", "my name is", "i like"]):
            return {
                "content": input_data.prompt,
                "tags": ["personal_info", "explicit_request"],
                "metadata": {"importance": "high"}
            }
        return None
    
    async def _generate_conversation_proactive_suggestion(self, input_data: FlowInput, context: Dict[str, Any]) -> Optional[str]:
        """Generate proactive suggestions based on the conversation."""
        if len(input_data.conversation_history) > 4:
            return "We've been chatting for a bit. Is there a specific task I can help you with?"
        return None
    
    async def _generate_conversation_ai_data(self, input_data: FlowInput, context: Dict[str, Any]) -> AiData:
        """Generate AI metadata for the conversation processing."""
        return AiData(
            confidence=0.85,
            reasoning="Response generated by primary LLM with context.",
            knowledge_graph_insights=context.get("context_summary")
        )

    async def conversation_processing_flow(self, input_data: FlowInput) -> FlowOutput:
        """Orchestrate a basic conversation processing flow.

        This demonstrates the stages of the flow:
        ``ingest_request`` -> ``ingest_modifiers`` -> ``ai_trigger`` -> ``post_actions``.
        Each stage is currently a placeholder that simply logs its execution.

        Parameters
        ----------
        input_data : FlowInput
            Incoming data for the conversation processing flow.

        Returns
        -------
        FlowOutput
            Result returned from the ``ai_trigger`` stage.
        """

        self.logger.info("conversation_processing_flow start")

        # Step 1: ingest_request
        self.logger.debug("Flow stage: ingest_request")
        request_data = input_data

        # Step 2: ingest_modifiers (no-op placeholder)
        self.logger.debug("Flow stage: ingest_modifiers")
        modified_data = request_data

        # Step 3: ai_trigger - delegate to existing handler
        self.logger.debug("Flow stage: ai_trigger")
        result = await self._handle_conversation_processing_flow(modified_data)

        # Step 4: post_actions (no-op placeholder)
        self.logger.debug("Flow stage: post_actions")

        self.logger.info("conversation_processing_flow end")
        return result
    
    # Public API methods
    async def process_flow(self, flow_type: FlowType, input_data: FlowInput) -> FlowOutput:
        return await self.flow_manager.execute_flow(flow_type, input_data)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get service metrics including flow statistics."""
        base_metrics = super().get_metrics()
        flow_metrics = {}
        for flow_type in FlowType:
            stats = self.flow_manager.get_flow_stats(flow_type)
            if stats:
                flow_metrics[flow_type.value] = stats
        base_metrics["flows"] = flow_metrics
        return base_metrics