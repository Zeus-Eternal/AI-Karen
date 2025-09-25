"""
Tests for AI Orchestrator Service.
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock

from ai_karen_engine.services.ai_orchestrator.ai_orchestrator import (
    AIOrchestrator, FlowManager, DecisionEngine, ContextManager, PromptManager,
    FlowRegistrationError, FlowExecutionError
)
from src.ai_karen_engine.core.services.base import ServiceConfig
from src.ai_karen_engine.models.shared_types import (
    FlowType, FlowInput, FlowOutput, DecideActionInput, DecideActionOutput,
    ToolType, ToolInput, MemoryDepth, PersonalityTone, PersonalityVerbosity,
    MemoryContext
)


class TestFlowManager:
    """Test FlowManager functionality."""
    
    def test_flow_manager_initialization(self):
        """Test FlowManager initializes correctly."""
        manager = FlowManager()
        
        assert manager._flows == {}
        assert manager._flow_metadata == {}
        assert len(manager._execution_stats) == len(FlowType)
        
        # Check that all flow types have initialized stats
        for flow_type in FlowType:
            assert flow_type in manager._execution_stats
            stats = manager._execution_stats[flow_type]
            assert stats["total_executions"] == 0
            assert stats["successful_executions"] == 0
            assert stats["failed_executions"] == 0
            assert stats["average_duration"] == 0.0
            assert stats["last_execution"] is None
    
    def test_register_flow(self):
        """Test flow registration."""
        manager = FlowManager()
        
        async def dummy_handler(input_data):
            return FlowOutput(response="test")
        
        metadata = {"description": "Test flow"}
        
        manager.register_flow(FlowType.DECIDE_ACTION, dummy_handler, metadata)
        
        assert FlowType.DECIDE_ACTION in manager._flows
        assert manager._flows[FlowType.DECIDE_ACTION] == dummy_handler
        assert manager._flow_metadata[FlowType.DECIDE_ACTION] == metadata
    
    def test_get_available_flows(self):
        """Test getting available flows."""
        manager = FlowManager()
        
        async def dummy_handler(input_data):
            return FlowOutput(response="test")
        
        manager.register_flow(FlowType.DECIDE_ACTION, dummy_handler)
        
        available = manager.get_available_flows()
        assert FlowType.DECIDE_ACTION in available
        assert len(available) == 1
    
    @pytest.mark.asyncio
    async def test_execute_flow_success(self):
        """Test successful flow execution."""
        manager = FlowManager()
        
        async def dummy_handler(input_data):
            return FlowOutput(response="test response")
        
        manager.register_flow(FlowType.DECIDE_ACTION, dummy_handler)
        
        input_data = FlowInput(
            prompt="test prompt",
            conversation_history=[],
            user_settings={}
        )
        
        result = await manager.execute_flow(FlowType.DECIDE_ACTION, input_data)
        
        assert result.response == "test response"
        
        # Check stats were updated
        stats = manager.get_flow_stats(FlowType.DECIDE_ACTION)
        assert stats["total_executions"] == 1
        assert stats["successful_executions"] == 1
        assert stats["failed_executions"] == 0
        assert stats["last_execution"] is not None
    
    @pytest.mark.asyncio
    async def test_execute_flow_not_registered(self):
        """Test executing unregistered flow raises error."""
        manager = FlowManager()
        
        input_data = FlowInput(
            prompt="test prompt",
            conversation_history=[],
            user_settings={}
        )
        
        with pytest.raises(FlowExecutionError):
            await manager.execute_flow(FlowType.DECIDE_ACTION, input_data)


class TestDecisionEngine:
    """Test DecisionEngine functionality."""
    
    def test_decision_engine_initialization(self):
        """Test DecisionEngine initializes correctly."""
        engine = DecisionEngine()
        
        assert engine._decision_rules == []
        assert len(engine._tool_registry) > 0
        
        # Check default tools are registered
        tools = engine.get_available_tools()
        assert ToolType.GET_CURRENT_DATE.value in tools
        assert ToolType.GET_WEATHER.value in tools
    
    @pytest.mark.asyncio
    async def test_analyze_intent_weather(self):
        """Test intent analysis for weather queries."""
        engine = DecisionEngine()
        
        result = await engine.analyze_intent("What's the weather in London?", {})
        
        assert result["primary_intent"] == "weather_query"
        assert result["confidence"] == 0.8
        assert ToolType.GET_WEATHER.value in result["suggested_tools"]
        
        # Check location entity extraction
        location_entities = [e for e in result["entities"] if e["type"] == "location"]
        assert len(location_entities) > 0
        assert "London" in location_entities[0]["value"]
    
    @pytest.mark.asyncio
    async def test_analyze_intent_time(self):
        """Test intent analysis for time queries."""
        engine = DecisionEngine()
        
        result = await engine.analyze_intent("What time is it?", {})
        
        assert result["primary_intent"] == "time_query"
        assert result["confidence"] == 0.8
        assert ToolType.GET_CURRENT_TIME.value in result["suggested_tools"]
    
    @pytest.mark.asyncio
    async def test_analyze_intent_conversation(self):
        """Test intent analysis for conversational queries."""
        engine = DecisionEngine()
        
        result = await engine.analyze_intent("Hello, how are you?", {})
        
        assert result["primary_intent"] == "conversation"
        assert result["confidence"] == 0.6
        assert result["suggested_tools"] == []
    
    @pytest.mark.asyncio
    async def test_decide_action_weather_with_location(self):
        """Test decide action for weather query with location."""
        engine = DecisionEngine()
        
        input_data = DecideActionInput(
            prompt="What's the weather in Paris?",
            personality_tone=PersonalityTone.FRIENDLY
        )
        
        result = await engine.decide_action(input_data)
        
        assert result.tool_to_call == ToolType.GET_WEATHER
        assert result.tool_input is not None
        assert result.tool_input.location == "Paris"
        assert "weather" in result.intermediate_response.lower()
    
    @pytest.mark.asyncio
    async def test_decide_action_weather_no_location(self):
        """Test decide action for weather query without location."""
        engine = DecisionEngine()
        
        input_data = DecideActionInput(
            prompt="What's the weather like?",
            personality_tone=PersonalityTone.FRIENDLY
        )
        
        result = await engine.decide_action(input_data)
        
        assert result.tool_to_call == ToolType.NONE
        assert "location" in result.intermediate_response.lower()
    
    @pytest.mark.asyncio
    async def test_decide_action_conversation(self):
        """Test decide action for conversational input."""
        engine = DecisionEngine()
        
        input_data = DecideActionInput(
            prompt="Hello, how are you?",
            personality_tone=PersonalityTone.FRIENDLY
        )
        
        result = await engine.decide_action(input_data)
        
        assert result.tool_to_call == ToolType.NONE
        assert len(result.intermediate_response) > 0
        assert "help" in result.intermediate_response.lower()
    
    @pytest.mark.asyncio
    async def test_identify_new_facts(self):
        """Test new fact identification."""
        engine = DecisionEngine()
        
        existing_facts = ["User likes coffee"]
        
        # Test name extraction
        new_facts = await engine._identify_new_facts("My name is John", existing_facts)
        assert new_facts is not None
        assert any("John" in fact for fact in new_facts)
        
        # Test like extraction
        new_facts = await engine._identify_new_facts("I like pizza", existing_facts)
        assert new_facts is not None
        assert any("pizza" in fact for fact in new_facts)
        
        # Test no new facts
        new_facts = await engine._identify_new_facts("I like coffee", existing_facts)
        assert new_facts is None


class TestContextManager:
    """Test ContextManager functionality."""
    
    def test_context_manager_initialization(self):
        """Test ContextManager initializes correctly."""
        manager = ContextManager()
        
        assert manager._context_cache == {}
        assert manager._cache_ttl == 300
    
    @pytest.mark.asyncio
    async def test_build_context_basic(self):
        """Test basic context building."""
        manager = ContextManager()
        
        context = await manager.build_context(
            user_id="user123",
            session_id="session456",
            prompt="Hello",
            conversation_history=[],
            user_settings={"personality_tone": "friendly"},
            memories=None
        )
        
        assert context["user_id"] == "user123"
        assert context["session_id"] == "session456"
        assert context["current_prompt"] == "Hello"
        assert context["user_settings"]["personality_tone"] == "friendly"
        assert context["memories"] == []
        assert "timestamp" in context
    
    @pytest.mark.asyncio
    async def test_build_context_with_memories(self):
        """Test context building with memories."""
        manager = ContextManager()
        
        memories = [
            MemoryContext(
                content="User likes coffee",
                similarity_score=0.8,
                tags=["preference"]
            )
        ]
        
        context = await manager.build_context(
            user_id="user123",
            session_id="session456",
            prompt="Hello",
            conversation_history=[],
            user_settings={},
            memories=memories
        )
        
        assert len(context["relevant_facts"]) == 1
        assert context["relevant_facts"][0]["content"] == "User likes coffee"
        assert context["relevant_facts"][0]["relevance"] == 0.8
    
    @pytest.mark.asyncio
    async def test_extract_conversation_themes(self):
        """Test conversation theme extraction."""
        manager = ContextManager()
        
        conversation_history = [
            {"content": "What's the weather like today?"},
            {"content": "It's sunny and warm"},
            {"content": "Great! I love good weather"}
        ]
        
        themes = await manager._extract_conversation_themes(conversation_history)
        
        assert "weather" in themes
    
    def test_context_caching(self):
        """Test context caching functionality."""
        manager = ContextManager()
        
        # Test cache miss
        cached = manager.get_cached_context("user123", "session456")
        assert cached is None
        
        # Manually add to cache
        test_context = {"test": "data"}
        manager._context_cache["user123:session456"] = {
            "context": test_context,
            "timestamp": datetime.now()
        }
        
        # Test cache hit
        cached = manager.get_cached_context("user123", "session456")
        assert cached == test_context
        
        # Test cache clearing
        manager.clear_context_cache("user123", "session456")
        cached = manager.get_cached_context("user123", "session456")
        assert cached is None


class TestPromptManager:
    """Test PromptManager functionality."""
    
    def test_prompt_manager_initialization(self):
        """Test PromptManager initializes correctly."""
        manager = PromptManager()
        
        assert len(manager._templates) > 0
        assert "decide_action" in manager._templates
        assert "conversation_processing" in manager._templates
    
    def test_register_template(self):
        """Test template registration."""
        manager = PromptManager()
        
        template = {
            "system_prompt": "You are a test assistant",
            "user_template": "User says: {message}",
            "variables": ["message"]
        }
        
        manager.register_template("test_template", template)
        
        assert "test_template" in manager._templates
        assert manager.get_template("test_template") == template
    
    def test_render_prompt(self):
        """Test prompt rendering."""
        manager = PromptManager()
        
        template = {
            "system_prompt": "You are a test assistant",
            "user_template": "User says: {message}",
            "variables": ["message"]
        }
        
        manager.register_template("test_template", template)
        
        rendered = manager.render_prompt("test_template", {"message": "Hello"})
        
        assert rendered["system_prompt"] == "You are a test assistant"
        assert rendered["user_prompt"] == "User says: Hello"
    
    def test_validate_template(self):
        """Test template validation."""
        manager = PromptManager()
        
        # Valid template
        valid_template = {
            "system_prompt": "You are a test assistant",
            "user_template": "User says: {message}",
            "variables": ["message"]
        }
        
        assert manager.validate_template(valid_template) is True
        
        # Invalid template - missing field
        invalid_template = {
            "system_prompt": "You are a test assistant",
            "variables": ["message"]
        }
        
        assert manager.validate_template(invalid_template) is False


class TestAIOrchestrator:
    """Test AIOrchestrator service."""
    
    def test_ai_orchestrator_initialization(self):
        """Test AIOrchestrator initializes correctly."""
        config = ServiceConfig(name="test_orchestrator")
        orchestrator = AIOrchestrator(config)
        
        assert orchestrator.flow_manager is not None
        assert orchestrator.decision_engine is not None
        assert orchestrator.context_manager is not None
        assert orchestrator.prompt_manager is not None
        assert orchestrator._initialized is False
    
    @pytest.mark.asyncio
    async def test_ai_orchestrator_startup(self):
        """Test AIOrchestrator startup sequence."""
        config = ServiceConfig(name="test_orchestrator")
        orchestrator = AIOrchestrator(config)
        
        await orchestrator.startup()
        
        assert orchestrator._initialized is True
        assert orchestrator.status.value == "running"
        
        # Check that default flows are registered
        available_flows = orchestrator.get_available_flows()
        assert FlowType.DECIDE_ACTION in available_flows
        assert FlowType.CONVERSATION_PROCESSING in available_flows
        
        await orchestrator.shutdown()
    
    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test health check functionality."""
        config = ServiceConfig(name="test_orchestrator")
        orchestrator = AIOrchestrator(config)
        
        # Health check should fail before initialization
        health = await orchestrator.health_check()
        assert health is False
        
        # Initialize and check health
        await orchestrator.startup()
        health = await orchestrator.health_check()
        assert health is True
        
        await orchestrator.shutdown()
    
    @pytest.mark.asyncio
    async def test_decide_action_flow(self):
        """Test decide action flow execution."""
        config = ServiceConfig(name="test_orchestrator")
        orchestrator = AIOrchestrator(config)
        
        await orchestrator.startup()
        
        input_data = FlowInput(
            prompt="What's the weather in London?",
            conversation_history=[],
            user_settings={}
        )
        
        result = await orchestrator.decide_action(input_data)
        
        assert result.response is not None
        assert isinstance(result.requires_plugin, bool)
        
        await orchestrator.shutdown()
    
    @pytest.mark.asyncio
    async def test_conversation_processing_flow(self):
        """Test conversation processing flow execution."""
        config = ServiceConfig(name="test_orchestrator")
        orchestrator = AIOrchestrator(config)
        
        await orchestrator.startup()
        
        input_data = FlowInput(
            prompt="Remember that I like coffee",
            conversation_history=[],
            user_settings={},
            user_id="test_user",
            session_id="test_session"
        )
        
        result = await orchestrator.conversation_processing_flow(input_data)
        
        assert result.response is not None
        assert result.memory_to_store is not None
        
        await orchestrator.shutdown()
    
    def test_get_metrics(self):
        """Test metrics collection."""
        config = ServiceConfig(name="test_orchestrator")
        orchestrator = AIOrchestrator(config)
        
        metrics = orchestrator.get_metrics()
        
        assert "status" in metrics
        assert "flows" in metrics
        assert "available_flows" in metrics
        assert "available_tools" in metrics
        assert "available_templates" in metrics


if __name__ == "__main__":
    pytest.main([__file__])