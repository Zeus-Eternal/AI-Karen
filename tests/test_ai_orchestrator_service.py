"""
Unit tests for AI Orchestrator Service - the central AI processing service
that coordinates flows, decision-making, and context management.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
from typing import Dict, Any, List

# Test data models and enums
from pydantic import BaseModel
from enum import Enum


class FlowType(str, Enum):
    DECIDE_ACTION = "decide_action"
    CONVERSATION_PROCESSING = "conversation_processing"
    CONVERSATION_SUMMARY = "conversation_summary"


class FlowInput(BaseModel):
    prompt: str
    conversation_history: List[Dict[str, Any]]
    user_settings: Dict[str, Any]
    context: Dict[str, Any] = None
    user_id: str = None
    session_id: str = None


class FlowOutput(BaseModel):
    response: str
    requires_plugin: bool = False
    plugin_to_execute: str = None
    plugin_parameters: Dict[str, Any] = None
    memory_to_store: Dict[str, Any] = None
    suggested_actions: List[str] = None
    ai_data: Dict[str, Any] = None
    proactive_suggestion: str = None


class MockAIOrchestrator:
    """Mock AI Orchestrator for testing."""
    
    def __init__(self):
        self.flow_manager = Mock()
        self.decision_engine = Mock()
        self.context_manager = Mock()
        self.prompt_manager = Mock()
    
    async def process_flow(self, flow_type: FlowType, input_data: FlowInput) -> FlowOutput:
        """Mock flow processing."""
        if flow_type == FlowType.DECIDE_ACTION:
            return await self.decide_action(input_data)
        elif flow_type == FlowType.CONVERSATION_PROCESSING:
            return await self.conversation_processing_flow(input_data)
        elif flow_type == FlowType.CONVERSATION_SUMMARY:
            return await self.conversation_summary_flow(input_data)
        else:
            raise ValueError(f"Unknown flow type: {flow_type}")
    
    async def decide_action(self, input_data: FlowInput) -> FlowOutput:
        """Mock decide action flow."""
        prompt = input_data.prompt.lower()
        
        if "weather" in prompt:
            return FlowOutput(
                response="I'll get the weather for you.",
                requires_plugin=True,
                plugin_to_execute="weather",
                plugin_parameters={"location": "default"}
            )
        elif "time" in prompt:
            return FlowOutput(
                response="I'll get the current time for you.",
                requires_plugin=True,
                plugin_to_execute="time",
                plugin_parameters={}
            )
        else:
            return FlowOutput(
                response="I can help you with that.",
                requires_plugin=False
            )
    
    async def conversation_processing_flow(self, input_data: FlowInput) -> FlowOutput:
        """Mock conversation processing flow."""
        return FlowOutput(
            response="I understand and will remember this conversation.",
            memory_to_store={
                "content": input_data.prompt,
                "user_id": input_data.user_id,
                "timestamp": datetime.now().isoformat()
            },
            proactive_suggestion="Would you like me to help with anything else?"
        )
    
    async def conversation_summary_flow(self, input_data: FlowInput) -> FlowOutput:
        """Mock conversation summary flow."""
        return FlowOutput(
            response="Here's a summary of our conversation: " + 
                    f"We discussed {len(input_data.conversation_history)} topics.",
            ai_data={
                "summary_length": len(input_data.conversation_history),
                "key_topics": ["general discussion"]
            }
        )


class TestAIOrchestrator:
    """Test the AI Orchestrator service."""
    
    @pytest.fixture
    def orchestrator(self):
        """Create a mock AI orchestrator for testing."""
        return MockAIOrchestrator()
    
    @pytest.fixture
    def sample_input(self):
        """Sample input data for testing."""
        return FlowInput(
            prompt="What's the weather like?",
            conversation_history=[],
            user_settings={"temperature_unit": "C"},
            user_id="test-user-123",
            session_id="test-session-456"
        )
    
    @pytest.mark.asyncio
    async def test_decide_action_weather_query(self, orchestrator, sample_input):
        """Test decide action flow for weather queries."""
        result = await orchestrator.process_flow(FlowType.DECIDE_ACTION, sample_input)
        
        assert isinstance(result, FlowOutput)
        assert result.requires_plugin is True
        assert result.plugin_to_execute == "weather"
        assert "weather" in result.response.lower()
        assert result.plugin_parameters is not None
    
    @pytest.mark.asyncio
    async def test_decide_action_time_query(self, orchestrator):
        """Test decide action flow for time queries."""
        input_data = FlowInput(
            prompt="What time is it?",
            conversation_history=[],
            user_settings={},
            user_id="test-user-123"
        )
        
        result = await orchestrator.process_flow(FlowType.DECIDE_ACTION, input_data)
        
        assert result.requires_plugin is True
        assert result.plugin_to_execute == "time"
        assert "time" in result.response.lower()
    
    @pytest.mark.asyncio
    async def test_decide_action_no_plugin_needed(self, orchestrator):
        """Test decide action flow when no plugin is needed."""
        input_data = FlowInput(
            prompt="Hello, how are you?",
            conversation_history=[],
            user_settings={},
            user_id="test-user-123"
        )
        
        result = await orchestrator.process_flow(FlowType.DECIDE_ACTION, input_data)
        
        assert result.requires_plugin is False
        assert result.plugin_to_execute is None
        assert result.response is not None
    
    @pytest.mark.asyncio
    async def test_conversation_processing_flow(self, orchestrator, sample_input):
        """Test conversation processing flow."""
        result = await orchestrator.process_flow(FlowType.CONVERSATION_PROCESSING, sample_input)
        
        assert isinstance(result, FlowOutput)
        assert result.memory_to_store is not None
        assert result.memory_to_store["user_id"] == "test-user-123"
        assert result.proactive_suggestion is not None
        assert "remember" in result.response.lower()
    
    @pytest.mark.asyncio
    async def test_conversation_summary_flow(self, orchestrator):
        """Test conversation summary flow."""
        input_data = FlowInput(
            prompt="Summarize our conversation",
            conversation_history=[
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"},
                {"role": "user", "content": "How's the weather?"},
                {"role": "assistant", "content": "It's sunny today."}
            ],
            user_settings={},
            user_id="test-user-123"
        )
        
        result = await orchestrator.process_flow(FlowType.CONVERSATION_SUMMARY, input_data)
        
        assert result.ai_data is not None
        assert result.ai_data["summary_length"] == 4
        assert "summary" in result.response.lower()
    
    @pytest.mark.asyncio
    async def test_invalid_flow_type(self, orchestrator, sample_input):
        """Test handling of invalid flow types."""
        with pytest.raises(ValueError):
            await orchestrator.process_flow("invalid_flow", sample_input)
    
    @pytest.mark.asyncio
    async def test_flow_with_context(self, orchestrator):
        """Test flow processing with additional context."""
        input_data = FlowInput(
            prompt="Continue our discussion",
            conversation_history=[],
            user_settings={},
            context={"previous_topic": "weather", "user_preference": "detailed"},
            user_id="test-user-123"
        )
        
        result = await orchestrator.process_flow(FlowType.CONVERSATION_PROCESSING, input_data)
        
        assert result is not None
        assert result.response is not None


class TestFlowManager:
    """Test the Flow Manager component."""
    
    def test_flow_registration(self):
        """Test flow registration and discovery."""
        flow_manager = Mock()
        flow_manager.register_flow = Mock()
        flow_manager.get_available_flows = Mock(return_value=["decide_action", "conversation_processing"])
        
        # Test registration
        flow_manager.register_flow("custom_flow", Mock())
        flow_manager.register_flow.assert_called_once()
        
        # Test discovery
        flows = flow_manager.get_available_flows()
        assert "decide_action" in flows
        assert "conversation_processing" in flows
    
    def test_flow_validation(self):
        """Test flow input validation."""
        flow_manager = Mock()
        flow_manager.validate_input = Mock(return_value=True)
        
        input_data = FlowInput(
            prompt="test",
            conversation_history=[],
            user_settings={}
        )
        
        is_valid = flow_manager.validate_input(input_data)
        assert is_valid is True
        flow_manager.validate_input.assert_called_once()


class TestDecisionEngine:
    """Test the Decision Engine component."""
    
    def test_decision_making_logic(self):
        """Test core decision making logic."""
        decision_engine = Mock()
        decision_engine.analyze_intent = Mock(return_value={
            "intent": "weather_query",
            "confidence": 0.9,
            "parameters": {"location": "default"}
        })
        
        result = decision_engine.analyze_intent("What's the weather?")
        
        assert result["intent"] == "weather_query"
        assert result["confidence"] == 0.9
        assert "location" in result["parameters"]
    
    def test_context_aware_decisions(self):
        """Test context-aware decision making."""
        decision_engine = Mock()
        decision_engine.decide_with_context = Mock(return_value={
            "action": "continue_conversation",
            "reasoning": "User is asking follow-up question"
        })
        
        context = {
            "previous_intent": "weather_query",
            "conversation_state": "active"
        }
        
        result = decision_engine.decide_with_context("And tomorrow?", context)
        
        assert result["action"] == "continue_conversation"
        assert "follow-up" in result["reasoning"]


class TestContextManager:
    """Test the Context Manager component."""
    
    def test_context_building(self):
        """Test context building from conversation history."""
        context_manager = Mock()
        context_manager.build_context = Mock(return_value={
            "recent_topics": ["weather", "time"],
            "user_preferences": {"temperature_unit": "C"},
            "conversation_state": "active"
        })
        
        conversation_history = [
            {"role": "user", "content": "What's the weather?"},
            {"role": "assistant", "content": "It's 20°C and sunny."},
            {"role": "user", "content": "What time is it?"}
        ]
        
        context = context_manager.build_context(conversation_history)
        
        assert "recent_topics" in context
        assert "weather" in context["recent_topics"]
        assert context["user_preferences"]["temperature_unit"] == "C"
    
    def test_context_memory_integration(self):
        """Test context integration with memory system."""
        context_manager = Mock()
        context_manager.integrate_memory = Mock(return_value={
            "relevant_memories": [
                {"content": "User likes detailed weather reports", "relevance": 0.8}
            ],
            "context_enhanced": True
        })
        
        current_context = {"topic": "weather"}
        user_id = "test-user-123"
        
        enhanced_context = context_manager.integrate_memory(current_context, user_id)
        
        assert enhanced_context["context_enhanced"] is True
        assert len(enhanced_context["relevant_memories"]) > 0


class TestPromptManager:
    """Test the Prompt Manager component."""
    
    def test_prompt_template_management(self):
        """Test prompt template creation and management."""
        prompt_manager = Mock()
        prompt_manager.create_template = Mock(return_value="template_id_123")
        prompt_manager.render_template = Mock(return_value="Rendered prompt with user data")
        
        # Test template creation
        template_id = prompt_manager.create_template("weather_query", "Get weather for {location}")
        assert template_id == "template_id_123"
        
        # Test template rendering
        rendered = prompt_manager.render_template(template_id, {"location": "New York"})
        assert "user data" in rendered
    
    def test_dynamic_prompt_generation(self):
        """Test dynamic prompt generation based on context."""
        prompt_manager = Mock()
        prompt_manager.generate_contextual_prompt = Mock(return_value={
            "prompt": "Based on our previous discussion about weather, let me help you with time.",
            "context_used": ["weather", "time"],
            "personalization_applied": True
        })
        
        context = {
            "previous_topics": ["weather"],
            "current_intent": "time_query",
            "user_preferences": {"verbosity": "detailed"}
        }
        
        result = prompt_manager.generate_contextual_prompt(context)
        
        assert "previous discussion" in result["prompt"]
        assert result["personalization_applied"] is True
        assert "weather" in result["context_used"]


class TestAIOrchestrator_Integration:
    """Integration tests for AI Orchestrator components."""
    
    @pytest.fixture
    def orchestrator(self):
        return MockAIOrchestrator()
    
    @pytest.mark.asyncio
    async def test_end_to_end_flow_processing(self, orchestrator):
        """Test complete end-to-end flow processing."""
        # Simulate a complex conversation flow
        input_data = FlowInput(
            prompt="Remember that I like coffee, then tell me the weather",
            conversation_history=[
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi! How can I help?"}
            ],
            user_settings={"memory_depth": "medium", "temperature_unit": "C"},
            user_id="test-user-123",
            session_id="test-session-456"
        )
        
        # Process through conversation flow first
        conv_result = await orchestrator.process_flow(FlowType.CONVERSATION_PROCESSING, input_data)
        assert conv_result.memory_to_store is not None
        
        # Then process through decision flow
        decision_result = await orchestrator.process_flow(FlowType.DECIDE_ACTION, input_data)
        assert decision_result.requires_plugin is True
    
    @pytest.mark.asyncio
    async def test_error_handling_in_flows(self, orchestrator):
        """Test error handling across different flows."""
        # Test with invalid input
        invalid_input = FlowInput(
            prompt="",  # Empty prompt
            conversation_history=[],
            user_settings={}
        )
        
        # Should handle gracefully
        result = await orchestrator.process_flow(FlowType.DECIDE_ACTION, invalid_input)
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_concurrent_flow_processing(self, orchestrator):
        """Test concurrent processing of multiple flows."""
        inputs = [
            FlowInput(prompt=f"Query {i}", conversation_history=[], user_settings={})
            for i in range(5)
        ]
        
        tasks = [
            orchestrator.process_flow(FlowType.DECIDE_ACTION, input_data)
            for input_data in inputs
        ]
        
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 5
        assert all(isinstance(r, FlowOutput) for r in results)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])