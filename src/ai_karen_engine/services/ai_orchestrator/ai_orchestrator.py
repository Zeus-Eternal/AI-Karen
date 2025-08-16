"""
AI Orchestrator Service for AI Karen Engine.
This service coordinates AI processing, decision-making, and workflow orchestration.
It converts TypeScript AI flows to Python services while maintaining compatibility
with the existing AI Karen architecture.
"""

from typing import Any, Dict, List, Optional

from ai_karen_engine.core.services.base import BaseService, ServiceConfig
from ai_karen_engine.models.shared_types import (  # ← ensure FlowType is imported
    AiData, DecideActionInput, FlowInput, FlowOutput, FlowType, PluginInfo,
    ToolType)

from ai_karen_engine.services.ai_orchestrator.context_manager import ContextManager
from ai_karen_engine.services.ai_orchestrator.decision_engine import DecisionEngine
from ai_karen_engine.services.ai_orchestrator.flow_manager import FlowManager
from ai_karen_engine.services.ai_orchestrator.prompt_manager import PromptManager


class AIOrchestrator(BaseService):
    """
    Central AI Orchestrator Service that coordinates AI processing and workflows.
    """

    def __init__(self, config: ServiceConfig):
        super().__init__(config)
        self.flow_manager = FlowManager()
        self.decision_engine = DecisionEngine()
        self.context_manager = ContextManager()  # Will be updated with memory service during initialization
        self.prompt_manager = PromptManager()
        self.llm_utils = None  # Will be initialized lazily
        self.llm_router = None  # Will be initialized lazily
        self._memory_service = None
        self._initialized = False

    def _get_llm_router(self):
        """Lazily initialize LLM router to avoid circular imports."""
        if self.llm_router is None:
            from ai_karen_engine.integrations.llm_router import LLMProfileRouter
            self.llm_router = LLMProfileRouter()
        return self.llm_router

    def _get_llm_utils(self):
        """Lazily initialize LLM utils to avoid circular imports."""
        if self.llm_utils is None:
            from ai_karen_engine.integrations.llm_utils import LLMUtils
            self.llm_utils = LLMUtils()
        return self.llm_utils

    async def initialize(self) -> None:
        """Initialize the AI Orchestrator service."""
        try:
            self.logger.info("Initializing AI Orchestrator Service")
            
            # Initialize memory service integration
            await self._initialize_memory_service()
            
            await self._register_default_flows()
            self._initialized = True
            self.logger.info("AI Orchestrator Service initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize AI Orchestrator: {e}")
            raise

    async def _initialize_memory_service(self) -> None:
        """Initialize memory service integration for semantic context building."""
        try:
            # Skip memory service integration during initialization to avoid circular dependencies
            # Memory service will be integrated lazily when first needed
            self.logger.info("Memory service integration deferred until first use")
            
        except Exception as e:
            self.logger.warning(f"Failed to initialize memory service integration: {e}")
            # Continue without memory service integration

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
        """Handle decide action flow processing with LLM integration."""
        try:
            # First use the decision engine for intent analysis and tool selection
            decide_input = DecideActionInput(
                prompt=input_data.prompt,
                short_term_memory=input_data.short_term_memory,
                long_term_memory=input_data.long_term_memory,
                personal_facts=input_data.personal_facts,
            )
            result = await self.decision_engine.decide_action(decide_input)
            
            # If no tool is needed, enhance the response with LLM
            if result.tool_to_call == ToolType.NONE:
                enhanced_response = await self._enhance_response_with_llm(
                    input_data.prompt, 
                    result.intermediate_response,
                    input_data
                )
                result.intermediate_response = enhanced_response
            
            return FlowOutput(
                response=result.intermediate_response,
                requires_plugin=result.tool_to_call != ToolType.NONE,
                tool_to_call=result.tool_to_call,
                tool_input=result.tool_input,
                suggested_new_facts=result.suggested_new_facts,
                proactive_suggestion=result.proactive_suggestion,
                ai_data=AiData(
                    confidence=0.8,
                    reasoning="Response generated by decision engine with LLM enhancement"
                )
            )
        except Exception as e:
            self.logger.error(f"Decide action flow failed: {e}")
            return FlowOutput(
                response="I'm having trouble processing your request. Could you try rephrasing it?",
                requires_plugin=False,
                ai_data=AiData(
                    confidence=0.3,
                    reasoning="Fallback due to processing error"
                )
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
        """Process conversation using LLM with memory/context awareness and proper LLM fallback hierarchy."""
        try:
            # Build dynamic system prompt with user preferences
            system_prompt = self.prompt_manager.build_system_prompt(
                "conversation_processing", 
                input_data.user_settings
            )

            # Build context information
            context_info = context.get("context_summary", "No additional context available")
            plugin_info = ", ".join(p.name for p in input_data.available_plugins or []) or "No plugins available"
            memory_info = "; ".join(mem.get("content", "") for mem in context.get("memories", [])[:3]) or "No relevant memories"
            user_preferences = ", ".join(f"{k}={v}" for k, v in input_data.user_settings.items()) or "No specific preferences"

            # Build user prompt using the prompt manager
            user_prompt = self.prompt_manager.build_user_prompt(
                "conversation_processing",
                prompt=input_data.prompt,
                context_info=context_info,
                plugin_info=plugin_info,
                memory_info=memory_info,
                user_preferences=user_preferences
            )
            
            full_prompt = f"{system_prompt}\n\n{user_prompt}"

            # Extract LLM preferences from context for proper fallback hierarchy
            llm_preferences = input_data.context.get("llm_preferences", {}) if input_data.context else {}
            preferred_provider = llm_preferences.get("preferred_llm_provider", "ollama")
            preferred_model = llm_preferences.get("preferred_model", "llama3.2:latest")
            
            self.logger.info(f"Processing conversation with LLM preferences: {preferred_provider}:{preferred_model}")

            # Implement proper LLM response hierarchy:
            # 1. User's chosen LLM (like Llama)
            # 2. System default LLMs if user choice fails  
            # 3. Hardcoded responses as final fallback
            
            # Step 1: Try user's chosen LLM
            try:
                self.logger.info(f"Attempting user's chosen LLM: {preferred_provider}:{preferred_model}")
                raw = self._get_llm_router().invoke(
                    self._get_llm_utils(),
                    full_prompt,
                    task_intent=FlowType.CONVERSATION_PROCESSING.value,
                    preferred_provider=preferred_provider,
                    preferred_model=preferred_model,
                )
                
                if isinstance(raw, str) and raw.strip():
                    response = raw.strip()
                    self.logger.info(f"Successfully got response from user's chosen LLM: {preferred_provider}")
                    return response[:4000] if len(response) > 4000 else response
                else:
                    self.logger.warning(f"Empty response from user's chosen LLM: {preferred_provider}")
                    
            except Exception as e:
                self.logger.warning(f"User's chosen LLM ({preferred_provider}) failed: {e}")
            
            # Step 2: Try system default LLMs
            default_providers = ["ollama:llama3.2:latest", "openai:gpt-3.5-turbo", "huggingface:distilbert-base-uncased"]
            for provider_model in default_providers:
                try:
                    provider, model = provider_model.split(":", 1)
                    self.logger.info(f"Attempting system default LLM: {provider}:{model}")
                    
                    raw = self._get_llm_router().invoke(
                        self._get_llm_utils(),
                        full_prompt,
                        task_intent=FlowType.CONVERSATION_PROCESSING.value,
                        preferred_provider=provider,
                        preferred_model=model,
                    )
                    
                    if isinstance(raw, str) and raw.strip():
                        response = raw.strip()
                        self.logger.info(f"Successfully got response from system default LLM: {provider}")
                        return response[:4000] if len(response) > 4000 else response
                    else:
                        self.logger.warning(f"Empty response from system default LLM: {provider}")
                        
                except Exception as e:
                    self.logger.debug(f"System default LLM ({provider_model}) failed: {e}")
                    continue
            
            # Step 3: Use hardcoded fallback response
            self.logger.info("All LLMs failed, using hardcoded fallback response")
            return await self._fallback_conversation_response(input_data, context, provider_missing=True)
            
        except Exception as ex:
            self.logger.error(f"LLM processing failed with unexpected error: {ex}")
            return await self._fallback_conversation_response(input_data, context, provider_missing=True)

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
        """Generate intelligent proactive suggestions based on conversation analysis."""
        try:
            # Generate context-aware suggestions using conversation analysis
            suggestion = await self._generate_intelligent_suggestions(input_data, context)
            return suggestion
        except Exception as e:
            self.logger.warning(f"Failed to generate intelligent suggestion: {e}")
            # Fallback to basic suggestion logic
            if len(input_data.conversation_history) > 4:
                return "We've been chatting for a bit. Is there a specific task I can help you with?"
            return None

    async def _generate_intelligent_suggestions(
        self, input_data: FlowInput, context: Dict[str, Any]
    ) -> Optional[str]:
        """Generate context-aware suggestions using conversation analysis and memory."""
        try:
            # Analyze conversation patterns and context
            conversation_analysis = await self._analyze_conversation_patterns(input_data)
            memory_insights = await self._extract_memory_insights(context)
            topic_analysis = await self._analyze_conversation_topics(input_data)
            
            # Generate suggestions based on analysis
            suggestions = []
            
            # Memory-based suggestions
            if memory_insights:
                memory_suggestions = await self._generate_memory_based_suggestions(memory_insights, input_data)
                suggestions.extend(memory_suggestions)
            
            # Topic-based suggestions
            if topic_analysis:
                topic_suggestions = await self._generate_topic_based_suggestions(topic_analysis, input_data)
                suggestions.extend(topic_suggestions)
            
            # Pattern-based suggestions
            if conversation_analysis:
                pattern_suggestions = await self._generate_pattern_based_suggestions(conversation_analysis, input_data)
                suggestions.extend(pattern_suggestions)
            
            # Filter and rank suggestions by relevance
            if suggestions:
                ranked_suggestions = await self._rank_suggestions_by_relevance(suggestions, input_data, context)
                return ranked_suggestions[0] if ranked_suggestions else None
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error in intelligent suggestion generation: {e}")
            return None

    async def _analyze_conversation_patterns(self, input_data: FlowInput) -> Dict[str, Any]:
        """Analyze conversation patterns to identify user behavior and preferences."""
        try:
            history = input_data.conversation_history or []
            if len(history) < 2:
                return {}
            
            patterns = {
                "message_length_trend": [],
                "question_frequency": 0,
                "topic_switches": 0,
                "help_requests": 0,
                "task_oriented": False,
                "conversation_length": len(history)
            }
            
            # Analyze message patterns
            for i, msg in enumerate(history):
                content = msg.get("content", "").lower()
                patterns["message_length_trend"].append(len(content))
                
                if "?" in content:
                    patterns["question_frequency"] += 1
                if any(word in content for word in ["help", "how", "what", "why", "when", "where"]):
                    patterns["help_requests"] += 1
                if any(word in content for word in ["do", "create", "make", "build", "write", "generate"]):
                    patterns["task_oriented"] = True
                    
                # Detect topic switches (simplified)
                if i > 0:
                    prev_content = history[i-1].get("content", "").lower()
                    if len(set(content.split()) & set(prev_content.split())) < 2:
                        patterns["topic_switches"] += 1
            
            return patterns
            
        except Exception as e:
            self.logger.warning(f"Error analyzing conversation patterns: {e}")
            return {}

    async def _extract_memory_insights(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract insights from memory context for suggestion generation."""
        try:
            memories = context.get("memories", [])
            if not memories:
                return {}
            
            insights = {
                "recent_topics": [],
                "user_preferences": [],
                "recurring_themes": [],
                "unfinished_tasks": []
            }
            
            # Analyze memories for patterns
            for memory in memories[:10]:  # Analyze recent memories
                content = memory.get("content", "").lower()
                tags = memory.get("tags", [])
                
                # Extract topics and themes
                if "personal_info" in tags:
                    insights["user_preferences"].append(content)
                if "task" in tags or "todo" in tags:
                    insights["unfinished_tasks"].append(content)
                
                # Simple topic extraction (could be enhanced with NLP)
                words = content.split()
                if len(words) > 3:
                    insights["recent_topics"].extend(words[:3])
            
            return insights
            
        except Exception as e:
            self.logger.warning(f"Error extracting memory insights: {e}")
            return {}

    async def _analyze_conversation_topics(self, input_data: FlowInput) -> Dict[str, Any]:
        """Analyze conversation topics using NLP if available."""
        try:
            current_prompt = input_data.prompt.lower()
            history = input_data.conversation_history or []
            
            # Simple topic categorization (could be enhanced with spaCy NER)
            topics = {
                "technical": any(word in current_prompt for word in ["code", "programming", "api", "database", "server"]),
                "creative": any(word in current_prompt for word in ["write", "create", "design", "art", "story"]),
                "informational": any(word in current_prompt for word in ["what", "how", "why", "explain", "tell me"]),
                "task_oriented": any(word in current_prompt for word in ["do", "make", "build", "help me", "can you"]),
                "personal": any(word in current_prompt for word in ["i am", "my", "me", "personal", "remember"])
            }
            
            # Analyze conversation flow
            analysis = {
                "primary_topic": max(topics.items(), key=lambda x: x[1])[0] if any(topics.values()) else "general",
                "topic_categories": [k for k, v in topics.items() if v],
                "conversation_depth": len(history),
                "current_focus": current_prompt[:100]  # First 100 chars for context
            }
            
            return analysis
            
        except Exception as e:
            self.logger.warning(f"Error analyzing conversation topics: {e}")
            return {}

    async def _generate_memory_based_suggestions(
        self, memory_insights: Dict[str, Any], input_data: FlowInput
    ) -> List[str]:
        """Generate suggestions based on memory insights."""
        suggestions = []
        
        try:
            # Suggest based on unfinished tasks
            if memory_insights.get("unfinished_tasks"):
                suggestions.append("I notice we discussed some tasks earlier. Would you like to continue working on any of them?")
            
            # Suggest based on user preferences
            if memory_insights.get("user_preferences"):
                suggestions.append("Based on what I know about your preferences, I can provide more personalized assistance.")
            
            # Suggest based on recurring themes
            if memory_insights.get("recurring_themes"):
                suggestions.append("I've noticed some recurring topics in our conversations. Would you like to explore any of them further?")
            
        except Exception as e:
            self.logger.warning(f"Error generating memory-based suggestions: {e}")
        
        return suggestions

    async def _generate_topic_based_suggestions(
        self, topic_analysis: Dict[str, Any], input_data: FlowInput
    ) -> List[str]:
        """Generate suggestions based on topic analysis."""
        suggestions = []
        
        try:
            primary_topic = topic_analysis.get("primary_topic", "general")
            
            if primary_topic == "technical":
                suggestions.extend([
                    "Would you like me to help you with code examples or technical documentation?",
                    "I can assist with debugging, architecture decisions, or best practices."
                ])
            elif primary_topic == "creative":
                suggestions.extend([
                    "I can help brainstorm ideas or provide creative feedback.",
                    "Would you like assistance with writing, design concepts, or creative problem-solving?"
                ])
            elif primary_topic == "informational":
                suggestions.extend([
                    "I can provide more detailed explanations or related information.",
                    "Would you like me to break this down into smaller, more manageable parts?"
                ])
            elif primary_topic == "task_oriented":
                suggestions.extend([
                    "I can help you break this task into smaller steps.",
                    "Would you like me to create a plan or checklist for this task?"
                ])
            elif primary_topic == "personal":
                suggestions.extend([
                    "I'll remember this information for future conversations.",
                    "Is there anything else about your preferences I should know?"
                ])
            
        except Exception as e:
            self.logger.warning(f"Error generating topic-based suggestions: {e}")
        
        return suggestions

    async def _generate_pattern_based_suggestions(
        self, conversation_analysis: Dict[str, Any], input_data: FlowInput
    ) -> List[str]:
        """Generate suggestions based on conversation patterns."""
        suggestions = []
        
        try:
            # Suggest based on conversation length
            conv_length = conversation_analysis.get("conversation_length", 0)
            if conv_length > 10:
                suggestions.append("We've covered a lot of ground. Would you like me to summarize our discussion?")
            
            # Suggest based on question frequency
            question_freq = conversation_analysis.get("question_frequency", 0)
            if question_freq > 3:
                suggestions.append("You've asked several questions. Would you like me to provide a comprehensive overview?")
            
            # Suggest based on help requests
            help_requests = conversation_analysis.get("help_requests", 0)
            if help_requests > 2:
                suggestions.append("I notice you're looking for help with multiple things. Would you like me to prioritize them?")
            
            # Suggest based on task orientation
            if conversation_analysis.get("task_oriented", False):
                suggestions.append("Would you like me to help you organize these tasks or create a workflow?")
            
            # Suggest based on topic switches
            topic_switches = conversation_analysis.get("topic_switches", 0)
            if topic_switches > 3:
                suggestions.append("We've covered several different topics. Would you like to focus on one specific area?")
            
        except Exception as e:
            self.logger.warning(f"Error generating pattern-based suggestions: {e}")
        
        return suggestions

    async def _rank_suggestions_by_relevance(
        self, suggestions: List[str], input_data: FlowInput, context: Dict[str, Any]
    ) -> List[str]:
        """Rank suggestions by relevance to current conversation context."""
        try:
            if not suggestions:
                return []
            
            # Simple relevance scoring based on context
            scored_suggestions = []
            current_prompt = input_data.prompt.lower()
            
            for suggestion in suggestions:
                score = 0
                suggestion_lower = suggestion.lower()
                
                # Score based on keyword overlap with current prompt
                prompt_words = set(current_prompt.split())
                suggestion_words = set(suggestion_lower.split())
                overlap = len(prompt_words & suggestion_words)
                score += overlap * 2
                
                # Score based on suggestion type relevance
                if "task" in current_prompt and "task" in suggestion_lower:
                    score += 5
                if "help" in current_prompt and "help" in suggestion_lower:
                    score += 3
                if "remember" in current_prompt and "remember" in suggestion_lower:
                    score += 4
                
                scored_suggestions.append((suggestion, score))
            
            # Sort by score (descending) and return suggestions
            scored_suggestions.sort(key=lambda x: x[1], reverse=True)
            return [suggestion for suggestion, _ in scored_suggestions]
            
        except Exception as e:
            self.logger.warning(f"Error ranking suggestions: {e}")
            return suggestions  # Return unranked if ranking fails

    async def _generate_conversation_ai_data(
        self, input_data: FlowInput, context: Dict[str, Any]
    ) -> AiData:
        """Generate AI metadata for the conversation processing."""
        return AiData(
            confidence=0.85,
            reasoning="Response generated by primary LLM with context.",
            knowledge_graph_insights=context.get("context_summary"),
        )

    async def _enhance_response_with_llm(
        self, user_prompt: str, base_response: str, input_data: FlowInput
    ) -> str:
        """Enhance a basic response using LLM to make it more natural and contextual."""
        try:
            # Create an enhancement prompt
            enhancement_prompt = f"""You are Karen, an AI assistant. A user asked: "{user_prompt}"

I have a basic response: "{base_response}"

Please enhance this response to be more natural, helpful, and conversational while keeping the core information intact. Make it sound more human-like and engaging.

Enhanced response:"""

            self.logger.info("Attempting to enhance response with LLM")
            
            raw = self._get_llm_router().invoke(
                self._get_llm_utils(),
                enhancement_prompt,
                task_intent="conversation_processing",
            )
            
            if isinstance(raw, str) and raw.strip():
                enhanced = raw.strip()
                self.logger.info("Successfully enhanced response with LLM")
                return enhanced[:4000] if len(enhanced) > 4000 else enhanced
            else:
                self.logger.warning("Empty response from LLM enhancement, using base response")
                return base_response
                
        except Exception as ex:
            self.logger.warning(f"LLM enhancement failed: {ex}, using base response")
            return base_response

    # ─────────────────────────────────────────────────────────────────────────────
    # Public API methods exposed to the rest of the system:
    async def process_flow(
        self, flow_type: FlowType, input_data: FlowInput
    ) -> FlowOutput:
        return await self.flow_manager.execute_flow(flow_type, input_data)

    async def conversation_processing_flow(self, input_data: FlowInput) -> FlowOutput:
        """Execute the conversation processing flow."""
        return await self.process_flow(FlowType.CONVERSATION_PROCESSING, input_data)

    async def decide_action(self, input_data: FlowInput) -> FlowOutput:
        """Execute the decide action flow."""
        return await self.process_flow(FlowType.DECIDE_ACTION, input_data)

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