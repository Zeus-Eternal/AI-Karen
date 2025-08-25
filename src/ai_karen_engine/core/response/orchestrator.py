"""
ResponseOrchestrator: Core pipeline for prompt-first response generation.

This module implements the central coordinator that manages the entire response
pipeline: analyze → recall → prompt → route → generate → format → persist.
"""

import logging
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from .protocols import Analyzer, Memory, LLMClient, ModelSelector, PromptBuilder, ResponseFormatter
from .config import PipelineConfig, DEFAULT_CONFIG

logger = logging.getLogger(__name__)


class ResponseOrchestrator:
    """Central coordinator for the response generation pipeline.
    
    This class orchestrates the entire response flow using dependency injection
    to work with pluggable components that implement the defined protocols.
    """
    
    def __init__(
        self,
        analyzer: Analyzer,
        memory: Memory,
        llm_client: LLMClient,
        config: Optional[PipelineConfig] = None,
        model_selector: Optional[ModelSelector] = None,
        prompt_builder: Optional[PromptBuilder] = None,
        response_formatter: Optional[ResponseFormatter] = None,
    ):
        """Initialize the ResponseOrchestrator.
        
        Args:
            analyzer: Component implementing Analyzer protocol
            memory: Component implementing Memory protocol  
            llm_client: Component implementing LLMClient protocol
            config: Pipeline configuration (uses default if None)
            model_selector: Optional model selection component
            prompt_builder: Optional prompt building component
            response_formatter: Optional response formatting component
        """
        self.analyzer = analyzer
        self.memory = memory
        self.llm_client = llm_client
        self.config = config or DEFAULT_CONFIG
        self.model_selector = model_selector
        self.prompt_builder = prompt_builder
        self.response_formatter = response_formatter
        
        # Initialize metrics if enabled
        self._init_metrics()
        
        logger.info("ResponseOrchestrator initialized with local-first configuration")
    
    def _init_metrics(self) -> None:
        """Initialize Prometheus metrics if available."""
        if not self.config.enable_metrics:
            self.response_counter = None
            self.response_latency = None
            self.routing_counter = None
            return
            
        try:
            from prometheus_client import Counter, Histogram, CollectorRegistry
            import uuid
            
            # Create unique metric names to avoid collisions
            instance_id = str(uuid.uuid4())[:8]
            
            self.response_counter = Counter(
                f'response_orchestrator_requests_total_{instance_id}',
                'Total response requests',
                ['persona', 'intent', 'model_type']
            )
            
            self.response_latency = Histogram(
                f'response_orchestrator_latency_seconds_{instance_id}',
                'Response generation latency',
                ['persona', 'intent']
            )
            
            self.routing_counter = Counter(
                f'response_orchestrator_routing_total_{instance_id}',
                'Model routing decisions',
                ['routing_decision', 'model_type']
            )
            
        except (ImportError, ValueError) as e:
            logger.debug(f"Prometheus metrics initialization failed: {e}")
            self.response_counter = None
            self.response_latency = None
            self.routing_counter = None
    
    def respond(self, user_text: str, ui_caps: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate response using the complete pipeline.
        
        Args:
            user_text: User's input text
            ui_caps: UI capabilities and context (copilotkit, persona_set, etc.)
            
        Returns:
            Dictionary containing response and metadata
        """
        start_time = time.time()
        correlation_id = str(uuid.uuid4())
        ui_caps = ui_caps or {}
        
        try:
            # Step 1: Analyze user input
            intent = self._safe_analyze_intent(user_text)
            mood = self._safe_analyze_sentiment(user_text)
            entities = self._safe_extract_entities(user_text)
            
            # Step 2: Choose persona
            persona = self._choose_persona(intent, mood, ui_caps)
            
            # Step 3: Recall relevant context
            context = self._safe_recall_context(user_text)
            
            # Step 4: Build prompt
            messages = self._build_prompt(user_text, persona, context, intent, mood, entities)
            
            # Step 5: Select model and generate response
            model_used = self._select_model(intent, len(str(messages)))
            raw_response = self._generate_response(messages, model_used)
            
            # Step 6: Format response
            formatted_response = self._format_response(
                raw_response, intent, persona, ui_caps
            )
            
            # Step 7: Persist interaction
            self._persist_interaction(user_text, formatted_response, {
                "intent": intent,
                "persona": persona,
                "mood": mood,
                "model_used": model_used,
                "correlation_id": correlation_id,
            })
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Update metrics
            self._update_metrics(persona, intent, model_used, processing_time)
            
            # Build final response
            response = {
                "intent": intent,
                "persona": persona,
                "mood": mood,
                "content": formatted_response,
                "metadata": {
                    "model_used": model_used,
                    "context_tokens": len(str(messages)),
                    "generation_time_ms": int(processing_time * 1000),
                    "routing_decision": "local" if "local:" in model_used else "cloud",
                    "correlation_id": correlation_id,
                    "entities": entities,
                }
            }
            
            # Add onboarding guidance if needed
            if self.config.enable_onboarding:
                gaps = self._profile_gaps(ui_caps, persona)
                if gaps:
                    response["onboarding"] = gaps
            
            logger.info(
                f"Response generated successfully: intent={intent}, persona={persona}, "
                f"model={model_used}, time={processing_time:.3f}s"
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Response generation failed: {str(e)}", exc_info=True)
            
            # Return graceful fallback response
            return self._create_fallback_response(user_text, str(e), correlation_id)
    
    def _safe_analyze_intent(self, text: str) -> str:
        """Safely analyze intent with fallback."""
        try:
            return self.analyzer.detect_intent(text)
        except Exception as e:
            logger.warning(f"Intent detection failed: {e}")
            return "general_assist"
    
    def _safe_analyze_sentiment(self, text: str) -> str:
        """Safely analyze sentiment with fallback."""
        try:
            return self.analyzer.sentiment(text)
        except Exception as e:
            logger.warning(f"Sentiment analysis failed: {e}")
            return "neutral"
    
    def _safe_extract_entities(self, text: str) -> Dict[str, Any]:
        """Safely extract entities with fallback."""
        try:
            return self.analyzer.entities(text)
        except Exception as e:
            logger.warning(f"Entity extraction failed: {e}")
            return {}
    
    def _safe_recall_context(self, query: str) -> List[Dict[str, Any]]:
        """Safely recall context with fallback."""
        try:
            return self.memory.recall(query, self.config.memory_recall_limit) or []
        except Exception as e:
            logger.warning(f"Memory recall failed: {e}")
            return []
    
    def _choose_persona(self, intent: str, mood: str, ui_caps: Dict[str, Any]) -> str:
        """Choose appropriate persona based on intent, mood, and UI capabilities."""
        # If persona is explicitly set in UI, use it
        if ui_caps.get("persona_set") and ui_caps.get("persona"):
            return ui_caps["persona"]
        
        # Use configuration mapping
        return self.config.get_persona_for_intent_mood(intent, mood)
    
    def _profile_gaps(self, ui_caps: Dict[str, Any], persona: str) -> Optional[Dict[str, Any]]:
        """Detect profile gaps for onboarding guidance."""
        gaps = {}
        
        # Check for missing project context
        if not ui_caps.get("project_name"):
            gaps["project_context"] = {
                "question": "What project are you working on?",
                "priority": "high",
                "reason": "Better context helps me provide more relevant assistance"
            }
        
        # Check for CopilotKit availability
        if not ui_caps.get("copilotkit") and self.config.enable_copilotkit:
            gaps["copilotkit_setup"] = {
                "question": "Would you like enhanced code assistance features?",
                "priority": "medium", 
                "reason": "CopilotKit can provide inline suggestions and complexity analysis"
            }
        
        # Persona-specific gaps
        if persona == "ruthless_optimizer" and not ui_caps.get("performance_goals"):
            gaps["performance_goals"] = {
                "question": "What are your main performance optimization goals?",
                "priority": "medium",
                "reason": "Understanding your goals helps me prioritize optimizations"
            }
        
        return gaps if gaps else None
    
    def _build_prompt(
        self, 
        user_text: str, 
        persona: str, 
        context: List[Dict[str, Any]], 
        intent: str, 
        mood: str, 
        entities: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Build structured prompt for LLM."""
        if self.prompt_builder:
            try:
                return self.prompt_builder.build_prompt(
                    user_text, persona, context, 
                    intent=intent, mood=mood, entities=entities
                )
            except Exception as e:
                logger.warning(f"Custom prompt builder failed: {e}")
        
        # Fallback to simple prompt construction
        system_prompt = self._build_system_prompt(persona, intent, mood)
        user_prompt = self._build_user_prompt(user_text, context, entities)
        
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    
    def _build_system_prompt(self, persona: str, intent: str, mood: str) -> str:
        """Build system prompt with persona injection."""
        persona_instructions = {
            "ruthless_optimizer": "You are a ruthless code optimizer. Focus on performance, efficiency, and clean architecture. Be direct and actionable.",
            "calm_fixit": "You are a calm problem-solver. Help users debug issues with patience and clear step-by-step guidance.",
            "technical_writer": "You are a technical documentation expert. Create clear, comprehensive documentation with examples.",
        }
        
        base_instruction = persona_instructions.get(
            persona, 
            "You are a helpful AI assistant focused on providing accurate, actionable responses."
        )
        
        context_instruction = ""
        if intent == "debug_error":
            context_instruction = " Focus on identifying root causes and providing specific solutions."
        elif intent == "optimize_code":
            context_instruction = " Prioritize performance improvements and code quality."
        elif mood == "frustrated":
            context_instruction = " Be extra patient and provide clear, step-by-step guidance."
        
        return f"{base_instruction}{context_instruction}"
    
    def _build_user_prompt(self, user_text: str, context: List[Dict[str, Any]], entities: Dict[str, Any]) -> str:
        """Build user prompt with context injection."""
        prompt_parts = []
        
        # Add context if available
        if context:
            prompt_parts.append("Relevant context:")
            for ctx in context[:3]:  # Limit to top 3 context items
                if isinstance(ctx, dict) and "text" in ctx:
                    prompt_parts.append(f"- {ctx['text']}")
            prompt_parts.append("")
        
        # Add entities if available
        if entities:
            entity_mentions = []
            for entity_type, entity_list in entities.items():
                if isinstance(entity_list, list) and entity_list:
                    entity_mentions.append(f"{entity_type}: {', '.join(str(e) for e in entity_list[:3])}")
            
            if entity_mentions:
                prompt_parts.append("Detected entities: " + "; ".join(entity_mentions))
                prompt_parts.append("")
        
        # Add user message
        prompt_parts.append("User request:")
        prompt_parts.append(user_text)
        
        return "\n".join(prompt_parts)
    
    def _select_model(self, intent: str, context_size: int) -> str:
        """Select appropriate model for the request."""
        if self.model_selector:
            try:
                return self.model_selector.select_model(intent, context_size)
            except Exception as e:
                logger.warning(f"Model selector failed: {e}")
        
        # Fallback to configuration-based selection
        if self.config.should_use_cloud(context_size):
            # Try to find a cloud model
            cloud_models = ["openai:gpt-4", "anthropic:claude-3", "openai:gpt-3.5-turbo"]
            for model in cloud_models:
                # In a real implementation, we'd check if the model is available
                return model
        
        # Default to local model
        return self.config.local_model_preference
    
    def _generate_response(self, messages: List[Dict[str, str]], model_id: str) -> str:
        """Generate response using selected model."""
        try:
            response = self.llm_client.generate(messages)
            
            # Update routing metrics
            if self.routing_counter:
                routing_type = "local" if "local:" in model_id else "cloud"
                model_type = model_id.split(":")[0] if ":" in model_id else "unknown"
                self.routing_counter.labels(
                    routing_decision=routing_type,
                    model_type=model_type
                ).inc()
            
            return response
            
        except Exception as e:
            logger.error(f"LLM generation failed with model {model_id}: {e}")
            
            # Try fallback to local model if cloud failed
            if not model_id.startswith("local:"):
                try:
                    logger.info("Attempting fallback to local model")
                    fallback_response = self.llm_client.generate(messages)
                    return fallback_response
                except Exception as fallback_error:
                    logger.error(f"Fallback generation also failed: {fallback_error}")
            
            raise e
    
    def _format_response(
        self, 
        raw_response: str, 
        intent: str, 
        persona: str, 
        ui_caps: Dict[str, Any]
    ) -> str:
        """Format raw response with consistent structure."""
        if self.response_formatter:
            try:
                formatted = self.response_formatter.format_response(
                    raw_response, intent, persona, **ui_caps
                )
                return formatted.get("content", raw_response)
            except Exception as e:
                logger.warning(f"Response formatter failed: {e}")
        
        # Fallback to basic formatting
        return self._apply_basic_formatting(raw_response, ui_caps)
    
    def _apply_basic_formatting(self, response: str, ui_caps: Dict[str, Any]) -> str:
        """Apply basic response formatting."""
        # Add CopilotKit enhancements if enabled and available
        if ui_caps.get("copilotkit") and self.config.enable_copilotkit:
            # Add basic CopilotKit hints (this would be expanded in actual implementation)
            if "```" in response:
                response += "\n\n*Enhanced code analysis available with CopilotKit*"
        
        return response
    
    def _persist_interaction(
        self, 
        user_msg: str, 
        assistant_msg: str, 
        metadata: Dict[str, Any]
    ) -> None:
        """Persist interaction to memory."""
        if not self.config.enable_memory_persistence:
            return
        
        try:
            self.memory.save_turn(user_msg, assistant_msg, metadata)
        except Exception as e:
            logger.warning(f"Memory persistence failed: {e}")
    
    def _update_metrics(self, persona: str, intent: str, model_used: str, processing_time: float) -> None:
        """Update Prometheus metrics."""
        if not self.config.enable_metrics:
            return
        
        try:
            if self.response_counter:
                model_type = model_used.split(":")[0] if ":" in model_used else "unknown"
                self.response_counter.labels(
                    persona=persona,
                    intent=intent,
                    model_type=model_type
                ).inc()
            
            if self.response_latency:
                self.response_latency.labels(
                    persona=persona,
                    intent=intent
                ).observe(processing_time)
                
        except Exception as e:
            logger.debug(f"Metrics update failed: {e}")
    
    def _create_fallback_response(self, user_text: str, error: str, correlation_id: str) -> Dict[str, Any]:
        """Create fallback response when pipeline fails."""
        return {
            "intent": "general_assist",
            "persona": self.config.persona_default,
            "mood": "neutral",
            "content": (
                "I apologize, but I encountered an issue processing your request. "
                "Please try rephrasing your question or contact support if the problem persists."
            ),
            "metadata": {
                "model_used": "fallback",
                "context_tokens": 0,
                "generation_time_ms": 0,
                "routing_decision": "fallback",
                "correlation_id": correlation_id,
                "error": error,
                "fallback_used": True,
            }
        }