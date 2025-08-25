"""
Tests for the Response Core orchestrator implementation.

This module tests the core pipeline infrastructure including the ResponseOrchestrator,
protocol interfaces, and adapter implementations.
"""

import pytest
from unittest.mock import Mock, patch
from typing import Dict, List, Any

from src.ai_karen_engine.core.response import (
    ResponseOrchestrator,
    PipelineConfig,
    create_response_orchestrator,
    create_local_only_orchestrator,
    SpacyAnalyzerAdapter,
    MemoryManagerAdapter,
    LLMOrchestratorAdapter,
)
from src.ai_karen_engine.core.response.protocols import Analyzer, Memory, LLMClient


class TestResponseOrchestrator:
    """Test the ResponseOrchestrator class."""
    
    def test_orchestrator_initialization(self):
        """Test that ResponseOrchestrator initializes correctly."""
        # Create mock components
        analyzer = Mock(spec=Analyzer)
        memory = Mock(spec=Memory)
        llm_client = Mock(spec=LLMClient)
        config = PipelineConfig()
        
        # Initialize orchestrator
        orchestrator = ResponseOrchestrator(
            analyzer=analyzer,
            memory=memory,
            llm_client=llm_client,
            config=config
        )
        
        assert orchestrator.analyzer == analyzer
        assert orchestrator.memory == memory
        assert orchestrator.llm_client == llm_client
        assert orchestrator.config == config
    
    def test_respond_basic_flow(self):
        """Test the basic response generation flow."""
        # Create mock components
        analyzer = Mock(spec=Analyzer)
        analyzer.detect_intent.return_value = "general_assist"
        analyzer.sentiment.return_value = "neutral"
        analyzer.entities.return_value = {}
        
        memory = Mock(spec=Memory)
        memory.recall.return_value = []
        
        llm_client = Mock(spec=LLMClient)
        llm_client.generate.return_value = "This is a test response."
        
        config = PipelineConfig(enable_metrics=False)
        
        # Initialize orchestrator
        orchestrator = ResponseOrchestrator(
            analyzer=analyzer,
            memory=memory,
            llm_client=llm_client,
            config=config
        )
        
        # Test response generation
        response = orchestrator.respond("Hello, how are you?")
        
        # Verify response structure
        assert isinstance(response, dict)
        assert "intent" in response
        assert "persona" in response
        assert "mood" in response
        assert "content" in response
        assert "metadata" in response
        
        assert response["intent"] == "general_assist"
        assert response["mood"] == "neutral"
        assert response["content"] == "This is a test response."
        
        # Verify components were called
        analyzer.detect_intent.assert_called_once()
        analyzer.sentiment.assert_called_once()
        analyzer.entities.assert_called_once()
        memory.recall.assert_called_once()
        llm_client.generate.assert_called_once()
    
    def test_persona_selection(self):
        """Test persona selection logic."""
        analyzer = Mock(spec=Analyzer)
        analyzer.detect_intent.return_value = "optimize_code"
        analyzer.sentiment.return_value = "neutral"
        analyzer.entities.return_value = {}
        
        memory = Mock(spec=Memory)
        memory.recall.return_value = []
        
        llm_client = Mock(spec=LLMClient)
        llm_client.generate.return_value = "Optimization response."
        
        config = PipelineConfig(enable_metrics=False)
        
        orchestrator = ResponseOrchestrator(
            analyzer=analyzer,
            memory=memory,
            llm_client=llm_client,
            config=config
        )
        
        response = orchestrator.respond("Make this code faster")
        
        # Should select ruthless_optimizer persona for optimize_code intent
        assert response["persona"] == "ruthless_optimizer"
    
    def test_error_handling_fallback(self):
        """Test error handling and fallback response."""
        analyzer = Mock(spec=Analyzer)
        analyzer.detect_intent.side_effect = Exception("Analysis failed")
        
        memory = Mock(spec=Memory)
        llm_client = Mock(spec=LLMClient)
        
        config = PipelineConfig(enable_metrics=False)
        
        orchestrator = ResponseOrchestrator(
            analyzer=analyzer,
            memory=memory,
            llm_client=llm_client,
            config=config
        )
        
        response = orchestrator.respond("Test message")
        
        # Should return fallback response
        assert response["metadata"]["fallback_used"] is True
        assert "error" in response["metadata"]
    
    def test_local_only_configuration(self):
        """Test local-only configuration behavior."""
        config = PipelineConfig(local_only=True)
        
        # Test cloud routing decision
        assert not config.should_use_cloud(1000)  # Small context
        assert not config.should_use_cloud(10000)  # Large context
        assert config.should_use_cloud(1000, explicit_cloud=True)  # Explicit override


class TestSpacyAnalyzerAdapter:
    """Test the SpacyAnalyzerAdapter."""
    
    def test_keyword_intent_detection(self):
        """Test fallback keyword-based intent detection."""
        adapter = SpacyAnalyzerAdapter()
        
        # Test optimization intent
        assert adapter._keyword_intent_detection("make this code faster") == "optimize_code"
        assert adapter._keyword_intent_detection("optimize performance") == "optimize_code"
        
        # Test debug intent
        assert adapter._keyword_intent_detection("fix this error") == "debug_error"
        assert adapter._keyword_intent_detection("debug this issue") == "debug_error"
        
        # Test documentation intent
        assert adapter._keyword_intent_detection("how to use this") == "documentation"
        assert adapter._keyword_intent_detection("explain this code") == "documentation"
        
        # Test general assist
        assert adapter._keyword_intent_detection("hello") == "general_assist"
    
    def test_keyword_sentiment_analysis(self):
        """Test fallback keyword-based sentiment analysis."""
        adapter = SpacyAnalyzerAdapter()
        
        # Test frustrated sentiment
        assert adapter._keyword_sentiment_analysis("this is so frustrating") == "frustrated"
        assert adapter._keyword_sentiment_analysis("I hate this bug") == "frustrated"
        
        # Test positive sentiment
        assert adapter._keyword_sentiment_analysis("this is awesome") == "positive"
        assert adapter._keyword_sentiment_analysis("love this feature") == "positive"
        
        # Test negative sentiment
        assert adapter._keyword_sentiment_analysis("this is bad") == "negative"
        assert adapter._keyword_sentiment_analysis("having problems") == "negative"
        
        # Test neutral sentiment
        assert adapter._keyword_sentiment_analysis("hello world") == "neutral"
    
    def test_basic_entity_extraction(self):
        """Test basic entity extraction."""
        adapter = SpacyAnalyzerAdapter()
        
        # Test file type extraction
        entities = adapter._basic_entity_extraction("check this .py file and .js script")
        assert "file_types" in entities
        assert ".py" in entities["file_types"]
        assert ".js" in entities["file_types"]
        
        # Test programming language detection
        entities = adapter._basic_entity_extraction("python django application with javascript")
        assert "programming_languages" in entities
        assert "python" in entities["programming_languages"]
        assert "javascript" in entities["programming_languages"]


class TestMemoryManagerAdapter:
    """Test the MemoryManagerAdapter."""
    
    @patch('src.ai_karen_engine.core.response.adapters.recall_context')
    def test_recall_success(self, mock_recall):
        """Test successful memory recall."""
        mock_recall.return_value = [
            {"result": "Previous conversation", "score": 0.9, "timestamp": 1234567890}
        ]
        
        adapter = MemoryManagerAdapter("test_user")
        results = adapter.recall("test query")
        
        assert len(results) == 1
        assert results[0]["text"] == "Previous conversation"
        assert results[0]["relevance_score"] == 0.9
        assert results[0]["source"] == "memory"
    
    @patch('src.ai_karen_engine.core.response.adapters.recall_context')
    def test_recall_failure(self, mock_recall):
        """Test memory recall failure handling."""
        mock_recall.side_effect = Exception("Memory error")
        
        adapter = MemoryManagerAdapter("test_user")
        results = adapter.recall("test query")
        
        assert results == []
    
    @patch('src.ai_karen_engine.core.response.adapters.update_memory')
    def test_save_turn_success(self, mock_update):
        """Test successful memory save."""
        mock_update.return_value = True
        
        adapter = MemoryManagerAdapter("test_user")
        adapter.save_turn("user message", "assistant response", {"intent": "test"})
        
        mock_update.assert_called_once()


class TestLLMOrchestratorAdapter:
    """Test the LLMOrchestratorAdapter."""
    
    def test_messages_to_prompt_conversion(self):
        """Test conversion of messages to prompt format."""
        adapter = LLMOrchestratorAdapter()
        
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello, how are you?"},
        ]
        
        prompt = adapter._messages_to_prompt(messages)
        
        assert "System: You are a helpful assistant." in prompt
        assert "User: Hello, how are you?" in prompt
    
    def test_fallback_response(self):
        """Test fallback response generation."""
        adapter = LLMOrchestratorAdapter()
        
        messages = [{"role": "user", "content": "Test message"}]
        response = adapter._fallback_response(messages)
        
        assert "Test message" in response
        assert "limited mode" in response


class TestFactoryFunctions:
    """Test factory functions for creating orchestrators."""
    
    @patch('src.ai_karen_engine.core.response.factory.create_spacy_analyzer')
    @patch('src.ai_karen_engine.core.response.factory.create_memory_adapter')
    @patch('src.ai_karen_engine.core.response.factory.create_llm_adapter')
    def test_create_response_orchestrator(self, mock_llm, mock_memory, mock_analyzer):
        """Test response orchestrator creation."""
        mock_analyzer.return_value = Mock(spec=Analyzer)
        mock_memory.return_value = Mock(spec=Memory)
        mock_llm.return_value = Mock(spec=LLMClient)
        
        orchestrator = create_response_orchestrator("test_user")
        
        assert isinstance(orchestrator, ResponseOrchestrator)
        mock_analyzer.assert_called_once()
        mock_memory.assert_called_once_with("test_user", None)
        mock_llm.assert_called_once()
    
    @patch('src.ai_karen_engine.core.response.factory.create_response_orchestrator')
    def test_create_local_only_orchestrator(self, mock_create):
        """Test local-only orchestrator creation."""
        mock_create.return_value = Mock(spec=ResponseOrchestrator)
        
        orchestrator = create_local_only_orchestrator("test_user")
        
        # Verify it was called with local-only config
        mock_create.assert_called_once()
        args, kwargs = mock_create.call_args
        config = kwargs.get('config') or args[2] if len(args) > 2 else None
        
        if config:
            assert config.local_only is True


class TestPipelineConfig:
    """Test the PipelineConfig dataclass."""
    
    def test_default_configuration(self):
        """Test default configuration values."""
        config = PipelineConfig()
        
        assert config.persona_default == "ruthless_optimizer"
        assert config.local_only is True
        assert config.max_context_tokens == 8192
        assert config.enable_copilotkit is True
    
    def test_persona_selection_logic(self):
        """Test persona selection based on intent and mood."""
        config = PipelineConfig()
        
        # Test mood-based selection (higher priority)
        persona = config.get_persona_for_intent_mood("general_assist", "frustrated")
        assert persona == "calm_fixit"
        
        # Test intent-based selection
        persona = config.get_persona_for_intent_mood("optimize_code", "neutral")
        assert persona == "ruthless_optimizer"
        
        # Test default fallback
        persona = config.get_persona_for_intent_mood("unknown_intent", "unknown_mood")
        assert persona == "ruthless_optimizer"
    
    def test_cloud_routing_logic(self):
        """Test cloud routing decision logic."""
        config = PipelineConfig(local_only=False, cloud_routing_threshold=4096)
        
        # Small context - should use local
        assert not config.should_use_cloud(1000)
        
        # Large context - should use cloud
        assert config.should_use_cloud(5000)
        
        # Explicit cloud request
        assert config.should_use_cloud(1000, explicit_cloud=True)
        
        # Local-only mode
        local_config = PipelineConfig(local_only=True)
        assert not local_config.should_use_cloud(10000)
        assert local_config.should_use_cloud(1000, explicit_cloud=True)  # Override


if __name__ == "__main__":
    pytest.main([__file__])