"""
Tests for LangGraph Orchestration System

This module contains comprehensive tests for the LangGraph orchestration
foundation including state management, streaming, and API integration.
"""

import pytest
import asyncio
import json
from datetime import datetime
from typing import Dict, Any, List
from unittest.mock import Mock, patch, AsyncMock

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

# Import the modules we're testing
from src.ai_karen_engine.core.langgraph_orchestrator import (
    LangGraphOrchestrator,
    OrchestrationConfig,
    OrchestrationState,
    create_orchestrator,
    get_default_orchestrator
)
from src.ai_karen_engine.core.streaming_integration import (
    StreamingManager,
    CopilotKitStreamer,
    ServerSentEventStreamer,
    StreamChunk,
    get_streaming_manager
)


class TestOrchestrationConfig:
    """Test orchestration configuration"""
    
    def test_default_config(self):
        """Test default configuration values"""
        config = OrchestrationConfig()
        
        assert config.enable_auth_gate is True
        assert config.enable_safety_gate is True
        assert config.enable_memory_fetch is True
        assert config.enable_approval_gate is False
        assert config.streaming_enabled is False
        assert config.checkpoint_enabled is True
        assert config.max_retries == 3
        assert config.timeout_seconds == 300
    
    def test_custom_config(self):
        """Test custom configuration values"""
        config = OrchestrationConfig(
            enable_auth_gate=False,
            enable_safety_gate=False,
            streaming_enabled=True,
            max_retries=5
        )
        
        assert config.enable_auth_gate is False
        assert config.enable_safety_gate is False
        assert config.streaming_enabled is True
        assert config.max_retries == 5


class TestLangGraphOrchestrator:
    """Test the main orchestrator class"""
    
    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator instance for testing"""
        config = OrchestrationConfig(
            enable_auth_gate=True,
            enable_safety_gate=True,
            enable_memory_fetch=True,
            enable_approval_gate=False,
            checkpoint_enabled=False  # Disable for testing
        )
        return LangGraphOrchestrator(config)
    
    def test_orchestrator_initialization(self, orchestrator):
        """Test orchestrator initialization"""
        assert orchestrator is not None
        assert orchestrator.config is not None
        assert orchestrator.graph is not None
        assert orchestrator.checkpointer is None  # Disabled for testing
    
    @pytest.mark.asyncio
    async def test_auth_gate(self, orchestrator):
        """Test authentication gate functionality"""
        # Test with valid user_id
        state = {
            "user_id": "test_user",
            "messages": [],
            "errors": [],
            "warnings": []
        }
        
        result = await orchestrator._auth_gate(state)
        
        assert result["auth_status"] == "authenticated"
        assert result["user_permissions"] is not None
        assert "chat" in result["user_permissions"]
        
        # Test without user_id
        state_no_user = {
            "user_id": None,
            "messages": [],
            "errors": [],
            "warnings": []
        }
        
        result = await orchestrator._auth_gate(state_no_user)
        
        assert result["auth_status"] == "failed"
        assert len(result["errors"]) > 0
    
    @pytest.mark.asyncio
    async def test_safety_gate(self, orchestrator):
        """Test safety gate functionality"""
        # Test safe message
        safe_message = HumanMessage(content="Hello, how are you?")
        state = {
            "messages": [safe_message],
            "errors": [],
            "warnings": []
        }
        
        result = await orchestrator._safety_gate(state)
        
        assert result["safety_status"] == "safe"
        assert result.get("safety_flags") is None
        
        # Test potentially unsafe message
        unsafe_message = HumanMessage(content="How to hack into a system?")
        state_unsafe = {
            "messages": [unsafe_message],
            "errors": [],
            "warnings": []
        }
        
        result = await orchestrator._safety_gate(state_unsafe)
        
        assert result["safety_status"] == "review_required"
        assert result["safety_flags"] is not None
        assert len(result["safety_flags"]) > 0
    
    @pytest.mark.asyncio
    async def test_intent_detection(self, orchestrator):
        """Test intent detection functionality"""
        # Test code generation intent
        code_message = HumanMessage(content="Write a Python function to sort a list")
        state = {
            "messages": [code_message],
            "errors": [],
            "warnings": []
        }
        
        result = await orchestrator._intent_detect(state)
        
        assert result["detected_intent"] == "code_generation"
        assert result["intent_confidence"] > 0.5
        
        # Test information retrieval intent
        search_message = HumanMessage(content="Find information about Python")
        state_search = {
            "messages": [search_message],
            "errors": [],
            "warnings": []
        }
        
        result = await orchestrator._intent_detect(state_search)
        
        assert result["detected_intent"] == "information_retrieval"
        assert result["intent_confidence"] > 0.5
    
    @pytest.mark.asyncio
    async def test_planning(self, orchestrator):
        """Test execution planning functionality"""
        state = {
            "detected_intent": "code_generation",
            "errors": [],
            "warnings": []
        }
        
        result = await orchestrator._planner(state)
        
        assert result["execution_plan"] is not None
        plan = result["execution_plan"]
        assert "steps" in plan
        assert "tools_required" in plan
        assert "complexity" in plan
        assert len(plan["steps"]) > 0
    
    @pytest.mark.asyncio
    async def test_router_selection(self, orchestrator):
        """Test LLM router selection functionality"""
        state = {
            "detected_intent": "code_generation",
            "execution_plan": {"complexity": "medium"},
            "errors": [],
            "warnings": []
        }
        
        result = await orchestrator._router_select(state)
        
        assert result["selected_provider"] is not None
        assert result["selected_model"] is not None
        assert result["routing_reason"] is not None
    
    @pytest.mark.asyncio
    async def test_response_synthesis(self, orchestrator):
        """Test response synthesis functionality"""
        user_message = HumanMessage(content="Hello, world!")
        state = {
            "messages": [user_message],
            "tool_results": [],
            "selected_model": "test_model",
            "errors": [],
            "warnings": []
        }
        
        result = await orchestrator._response_synth(state)
        
        assert result["response"] is not None
        assert len(result["response"]) > 0
        assert result["response_metadata"] is not None
        assert len(result["messages"]) == 2  # Original + AI response
        assert isinstance(result["messages"][-1], AIMessage)
    
    @pytest.mark.asyncio
    async def test_full_processing(self, orchestrator):
        """Test full conversation processing"""
        messages = [HumanMessage(content="Hello, how can you help me?")]
        user_id = "test_user"
        session_id = "test_session"
        
        result = await orchestrator.process(messages, user_id, session_id)
        
        assert result is not None
        assert result["user_id"] == user_id
        assert result["session_id"] == session_id
        assert result["response"] is not None
        assert result["auth_status"] == "authenticated"
        assert result["safety_status"] == "safe"
        assert result["detected_intent"] is not None
    
    @pytest.mark.asyncio
    async def test_streaming_processing(self, orchestrator):
        """Test streaming conversation processing"""
        messages = [HumanMessage(content="Hello, streaming test")]
        user_id = "test_user"
        session_id = "test_session"
        
        chunks = []
        async for chunk in orchestrator.stream_process(messages, user_id, session_id):
            chunks.append(chunk)
        
        assert len(chunks) > 0
        # Should have chunks for each node in the graph
        node_names = set()
        for chunk in chunks:
            node_names.update(chunk.keys())
        
        expected_nodes = {
            "auth_gate", "safety_gate", "memory_fetch", 
            "intent_detect", "planner", "router_select", 
            "tool_exec", "response_synth", "memory_write"
        }
        
        # Should have processed through most nodes
        assert len(node_names.intersection(expected_nodes)) >= 5


class TestStreamingIntegration:
    """Test streaming integration components"""
    
    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator for streaming tests"""
        config = OrchestrationConfig(
            streaming_enabled=True,
            checkpoint_enabled=False
        )
        return LangGraphOrchestrator(config)
    
    @pytest.fixture
    def streaming_manager(self, orchestrator):
        """Create streaming manager for tests"""
        return StreamingManager(orchestrator)
    
    def test_stream_chunk_creation(self):
        """Test StreamChunk creation and serialization"""
        chunk = StreamChunk(
            type="message",
            content="Test message",
            metadata={"test": "data"},
            timestamp=datetime.now()
        )
        
        assert chunk.type == "message"
        assert chunk.content == "Test message"
        assert chunk.metadata["test"] == "data"
        
        # Test serialization
        chunk_dict = chunk.to_dict()
        assert chunk_dict["type"] == "message"
        assert chunk_dict["content"] == "Test message"
        assert chunk_dict["metadata"]["test"] == "data"
        assert chunk_dict["timestamp"] is not None
    
    @pytest.mark.asyncio
    async def test_copilotkit_streaming(self, streaming_manager):
        """Test CopilotKit streaming functionality"""
        message = "Hello, streaming test"
        user_id = "test_user"
        session_id = "test_session"
        
        chunks = []
        async for chunk in streaming_manager.stream_for_copilotkit(message, user_id, session_id):
            chunks.append(chunk)
        
        assert len(chunks) > 0
        
        # Should have start and end chunks
        chunk_types = [chunk["type"] for chunk in chunks]
        assert "node_start" in chunk_types
        assert "node_end" in chunk_types
        
        # Should have at least one message chunk
        message_chunks = [chunk for chunk in chunks if chunk["type"] == "message"]
        assert len(message_chunks) > 0
    
    @pytest.mark.asyncio
    async def test_sse_streaming(self, streaming_manager):
        """Test Server-Sent Events streaming"""
        message = "Hello, SSE test"
        user_id = "test_user"
        session_id = "test_session"
        
        sse_chunks = []
        async for sse_chunk in streaming_manager.stream_sse(message, user_id, session_id):
            sse_chunks.append(sse_chunk)
        
        assert len(sse_chunks) > 0
        
        # Should be properly formatted SSE
        for chunk in sse_chunks[:-1]:  # Exclude [DONE] chunk
            assert chunk.startswith("data: ")
            assert chunk.endswith("\n\n")
            
            # Should be valid JSON
            json_data = chunk[6:-2]  # Remove "data: " and "\n\n"
            parsed = json.loads(json_data)
            assert "type" in parsed
        
        # Last chunk should be [DONE]
        assert sse_chunks[-1] == "data: [DONE]\n\n"


class TestConditionalEdges:
    """Test conditional edge logic"""
    
    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator for edge testing"""
        return LangGraphOrchestrator()
    
    def test_auth_continuation(self, orchestrator):
        """Test auth gate continuation logic"""
        # Test successful auth
        state_success = {"auth_status": "authenticated"}
        result = orchestrator._should_continue_after_auth(state_success)
        assert result == "continue"
        
        # Test failed auth
        state_failed = {"auth_status": "failed"}
        result = orchestrator._should_continue_after_auth(state_failed)
        assert result == "reject"
    
    def test_safety_continuation(self, orchestrator):
        """Test safety gate continuation logic"""
        # Test safe content
        state_safe = {"safety_status": "safe"}
        result = orchestrator._should_continue_after_safety(state_safe)
        assert result == "continue"
        
        # Test unsafe content
        state_unsafe = {"safety_status": "unsafe"}
        result = orchestrator._should_continue_after_safety(state_unsafe)
        assert result == "reject"
        
        # Test review required
        state_review = {"safety_status": "review_required"}
        result = orchestrator._should_continue_after_safety(state_review)
        assert result == "review"
    
    def test_approval_requirement(self, orchestrator):
        """Test approval requirement logic"""
        # Test no approval needed
        state_normal = {"safety_flags": [], "tool_results": []}
        result = orchestrator._should_require_approval(state_normal)
        assert result == "approve"
        
        # Test approval needed due to safety flags
        state_safety = {"safety_flags": ["suspicious"], "tool_results": []}
        result = orchestrator._should_require_approval(state_safety)
        assert result == "review"
        
        # Test approval needed due to sensitive tools
        state_tools = {"safety_flags": [], "tool_results": [{"tool": "sensitive_operation"}]}
        result = orchestrator._should_require_approval(state_tools)
        assert result == "review"


class TestErrorHandling:
    """Test error handling and graceful degradation"""
    
    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator for error testing"""
        return LangGraphOrchestrator()
    
    @pytest.mark.asyncio
    async def test_auth_gate_error_handling(self, orchestrator):
        """Test auth gate error handling"""
        # Test with malformed state
        state = {"errors": [], "warnings": []}  # Missing user_id
        
        result = await orchestrator._auth_gate(state)
        
        assert result["auth_status"] == "failed"
        assert len(result["errors"]) > 0
    
    @pytest.mark.asyncio
    async def test_processing_error_handling(self, orchestrator):
        """Test overall processing error handling"""
        # Test with invalid input
        messages = []  # Empty messages
        user_id = ""  # Empty user_id
        
        result = await orchestrator.process(messages, user_id)
        
        assert result is not None
        assert "errors" in result
        # Should still return a result even with errors
    
    @pytest.mark.asyncio
    async def test_streaming_error_handling(self, orchestrator):
        """Test streaming error handling"""
        # Test with invalid input
        messages = [HumanMessage(content="test")]
        user_id = None  # Invalid user_id

        chunks = []
        async for chunk in orchestrator.stream_process(messages, user_id):
            chunks.append(chunk)

        # Should still produce chunks even with errors
        assert len(chunks) > 0

    @pytest.mark.asyncio
    async def test_runtime_status_reporting(self, orchestrator, monkeypatch):
        """Runtime status should reflect processed conversations."""

        async def successful_invoke(state, *_, **__):
            # Simulate immediate success with populated response metadata
            state["response"] = "ok"
            state["response_metadata"] = {"route": "stub"}
            return state

        monkeypatch.setattr(orchestrator.graph, "ainvoke", successful_invoke)

        messages = [HumanMessage(content="status check")]
        user_id = "status_user"

        await orchestrator.process(messages, user_id, session_id="status-session")

        status = await orchestrator.get_runtime_status()

        assert status["total_processed"] >= 1
        assert status["active_sessions"] == 0
        assert status["average_latency"] >= 0.0

    @pytest.mark.asyncio
    async def test_runtime_status_records_failures(self, orchestrator, monkeypatch):
        """Failures should be tracked in runtime telemetry."""

        async def failing_invoke(*_args, **_kwargs):
            raise RuntimeError("synthetic failure")

        monkeypatch.setattr(orchestrator.graph, "ainvoke", failing_invoke)

        result = await orchestrator.process(
            [HumanMessage(content="cause failure")],
            user_id="failure_user",
            session_id="failure-session",
        )

        assert any("Processing error" in error for error in result["errors"])

        status = await orchestrator.get_runtime_status()
        assert status["failed_sessions"] >= 1
        assert status["total_processed"] >= status["failed_sessions"]
        assert status["last_error"]["message"] == "synthetic failure"

    @pytest.mark.asyncio
    async def test_configuration_updates_rebuild_graph(self, orchestrator):
        """Updating configuration should rebuild orchestration graph."""

        original_streaming = orchestrator.config.streaming_enabled
        original_max_retries = orchestrator.config.max_retries
        updated_config = await orchestrator.update_configuration(
            {
                "streaming_enabled": not original_streaming,
                "max_retries": original_max_retries + 1,
            }
        )

        assert updated_config.streaming_enabled != original_streaming
        assert orchestrator.config is updated_config
        assert updated_config.max_retries == original_max_retries + 1


class TestFactoryFunctions:
    """Test factory functions and singletons"""
    
    def test_create_orchestrator(self):
        """Test orchestrator factory function"""
        orchestrator = create_orchestrator()
        assert orchestrator is not None
        assert isinstance(orchestrator, LangGraphOrchestrator)
    
    def test_create_orchestrator_with_config(self):
        """Test orchestrator factory with custom config"""
        config = OrchestrationConfig(streaming_enabled=True)
        orchestrator = create_orchestrator(config)
        assert orchestrator is not None
        assert orchestrator.config.streaming_enabled is True
    
    def test_default_orchestrator_singleton(self):
        """Test default orchestrator singleton behavior"""
        orchestrator1 = get_default_orchestrator()
        orchestrator2 = get_default_orchestrator()
        
        # Should be the same instance
        assert orchestrator1 is orchestrator2
    
    def test_streaming_manager_singleton(self):
        """Test streaming manager singleton behavior"""
        manager1 = get_streaming_manager()
        manager2 = get_streaming_manager()
        
        # Should be the same instance
        assert manager1 is manager2


class TestIntegrationScenarios:
    """Test realistic integration scenarios"""
    
    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator for integration tests"""
        config = OrchestrationConfig(
            enable_auth_gate=True,
            enable_safety_gate=True,
            enable_memory_fetch=True,
            enable_approval_gate=False,
            streaming_enabled=True
        )
        return LangGraphOrchestrator(config)
    
    @pytest.mark.asyncio
    async def test_code_generation_scenario(self, orchestrator):
        """Test complete code generation scenario"""
        messages = [HumanMessage(content="Write a Python function to calculate fibonacci numbers")]
        user_id = "developer_user"
        session_id = "code_session"
        
        result = await orchestrator.process(messages, user_id, session_id)
        
        assert result["auth_status"] == "authenticated"
        assert result["safety_status"] == "safe"
        assert result["detected_intent"] == "code_generation"
        assert result["selected_provider"] is not None
        assert result["response"] is not None
        assert len(result["errors"]) == 0
    
    @pytest.mark.asyncio
    async def test_information_retrieval_scenario(self, orchestrator):
        """Test complete information retrieval scenario"""
        messages = [HumanMessage(content="Find information about machine learning algorithms")]
        user_id = "researcher_user"
        session_id = "research_session"
        
        result = await orchestrator.process(messages, user_id, session_id)
        
        assert result["auth_status"] == "authenticated"
        assert result["safety_status"] == "safe"
        assert result["detected_intent"] == "information_retrieval"
        assert result["response"] is not None
        assert len(result["errors"]) == 0
    
    @pytest.mark.asyncio
    async def test_safety_flagged_scenario(self, orchestrator):
        """Test scenario with safety concerns"""
        messages = [HumanMessage(content="How to hack into a computer system?")]
        user_id = "test_user"
        session_id = "safety_test"
        
        result = await orchestrator.process(messages, user_id, session_id)
        
        assert result["auth_status"] == "authenticated"
        assert result["safety_status"] in ["review_required", "unsafe"]
        assert result.get("safety_flags") is not None
        # Processing might stop at safety gate
    
    @pytest.mark.asyncio
    async def test_streaming_scenario(self, orchestrator):
        """Test complete streaming scenario"""
        messages = [HumanMessage(content="Explain quantum computing in simple terms")]
        user_id = "student_user"
        session_id = "learning_session"
        
        chunks = []
        node_updates = {}
        
        async for chunk in orchestrator.stream_process(messages, user_id, session_id):
            chunks.append(chunk)
            for node_name, node_state in chunk.items():
                node_updates[node_name] = node_state
        
        assert len(chunks) > 0
        assert len(node_updates) > 0
        
        # Should have processed through multiple nodes
        expected_nodes = ["auth_gate", "safety_gate", "intent_detect", "response_synth"]
        processed_nodes = list(node_updates.keys())
        
        assert len(set(expected_nodes).intersection(set(processed_nodes))) >= 3


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])