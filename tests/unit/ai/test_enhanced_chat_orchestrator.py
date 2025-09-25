"""
Integration tests for the enhanced ChatOrchestrator with instruction processing and context integration.

This module tests the complete enhanced chat orchestrator functionality including
instruction extraction, context integration, and enhanced response generation.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from ai_karen_engine.chat.chat_orchestrator import (
    ChatOrchestrator,
    ChatRequest,
    ChatResponse,
    ProcessingContext
)
from ai_karen_engine.chat.instruction_processor import (
    InstructionProcessor,
    InstructionContext,
    ExtractedInstruction,
    InstructionType,
    InstructionPriority,
    InstructionScope
)
from ai_karen_engine.chat.context_integrator import (
    ContextIntegrator,
    ContextItem,
    ContextType,
    IntegratedContext
)
from ai_karen_engine.services.spacy_service import ParsedMessage


class TestEnhancedChatOrchestrator:
    """Test the enhanced ChatOrchestrator with instruction processing and context integration."""
    
    @pytest.fixture
    def mock_memory_processor(self):
        """Create a mock memory processor."""
        mock = MagicMock()
        mock.extract_memories = AsyncMock(return_value=[])
        mock.get_relevant_context = AsyncMock(return_value=MagicMock(
            memories=[],
            entities=[],
            preferences=[],
            facts=[],
            relationships=[],
            context_summary="Mock context",
            retrieval_time=0.1,
            total_memories_considered=0
        ))
        return mock
    
    @pytest.fixture
    def mock_instruction_processor(self):
        """Create a mock instruction processor."""
        mock = MagicMock(spec=InstructionProcessor)
        mock.extract_instructions = AsyncMock(return_value=[])
        mock.store_instructions = AsyncMock()
        mock.get_active_instructions = AsyncMock(return_value=[])
        mock.apply_instructions_to_prompt = AsyncMock(side_effect=lambda prompt, *args: prompt)
        return mock
    
    @pytest.fixture
    def mock_context_integrator(self):
        """Create a mock context integrator."""
        mock = MagicMock(spec=ContextIntegrator)
        mock.integrate_context = AsyncMock(return_value=IntegratedContext(
            primary_context="Mock primary context",
            supporting_context="Mock supporting context",
            context_summary="Mock context summary",
            token_count=100,
            items_included=[],
            items_excluded=[],
            relevance_threshold=0.3
        ))
        return mock
    
    @pytest.fixture
    def enhanced_orchestrator(self, mock_memory_processor, mock_instruction_processor, mock_context_integrator):
        """Create an enhanced ChatOrchestrator with mocked dependencies."""
        return ChatOrchestrator(
            memory_processor=mock_memory_processor,
            instruction_processor=mock_instruction_processor,
            context_integrator=mock_context_integrator,
            timeout_seconds=5.0
        )
    
    @pytest.fixture
    def sample_chat_request(self):
        """Create a sample chat request."""
        return ChatRequest(
            message="Please explain machine learning in simple terms with examples.",
            user_id="test_user",
            conversation_id="test_conversation",
            session_id="test_session",
            stream=False,
            include_context=True
        )
    
    @pytest.fixture
    def sample_parsed_message(self):
        """Create a sample parsed message."""
        return ParsedMessage(
            text="Please explain machine learning in simple terms with examples.",
            tokens=["please", "explain", "machine", "learning", "in", "simple", "terms", "with", "examples"],
            entities=[("machine learning", "TOPIC"), ("examples", "REQUEST")],
            pos_tags=[("please", "ADV"), ("explain", "VERB")],
            dependencies=[],
            sentiment_score=0.1,
            used_fallback=False
        )
    
    @pytest.mark.asyncio
    async def test_enhanced_message_processing_with_instructions(
        self, enhanced_orchestrator, sample_chat_request, sample_parsed_message, 
        mock_instruction_processor, mock_context_integrator
    ):
        """Test enhanced message processing with instruction extraction."""
        # Setup instruction processor to return sample instructions
        sample_instructions = [
            ExtractedInstruction(
                id="task_1",
                type=InstructionType.TASK,
                content="explain machine learning",
                priority=InstructionPriority.HIGH,
                scope=InstructionScope.CURRENT_MESSAGE,
                confidence=0.9,
                extracted_at=datetime.utcnow()
            ),
            ExtractedInstruction(
                id="style_1",
                type=InstructionType.STYLE,
                content="simple terms",
                priority=InstructionPriority.MEDIUM,
                scope=InstructionScope.CURRENT_MESSAGE,
                confidence=0.8,
                extracted_at=datetime.utcnow()
            )
        ]
        
        mock_instruction_processor.extract_instructions.return_value = sample_instructions
        mock_instruction_processor.get_active_instructions.return_value = sample_instructions
        
        # Mock NLP services
        with patch("ai_karen_engine.chat.chat_orchestrator.nlp_service_manager") as mock_nlp:
            mock_nlp.parse_message.return_value = sample_parsed_message
            mock_nlp.get_embeddings.return_value = [0.1] * 768
            
            # Process the message
            response = await enhanced_orchestrator.process_message(sample_chat_request)
            
            assert isinstance(response, ChatResponse)
            assert response.response is not None
            assert response.correlation_id is not None
            
            # Verify instruction processing was called
            mock_instruction_processor.extract_instructions.assert_called_once()
            mock_instruction_processor.store_instructions.assert_called_once()
            mock_instruction_processor.get_active_instructions.assert_called_once()
            
            # Verify context integration was called
            mock_context_integrator.integrate_context.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_enhanced_context_integration(
        self, enhanced_orchestrator, sample_chat_request, sample_parsed_message,
        mock_context_integrator
    ):
        """Test enhanced context integration functionality."""
        # Setup context integrator to return detailed context
        integrated_context = IntegratedContext(
            primary_context="KEY ENTITIES: machine learning: TOPIC\nRELEVANT CONTEXT: User prefers simple explanations",
            supporting_context="USER PREFERENCES: Use examples in explanations",
            context_summary="Context includes: 2 memory, 1 entities, 1 user_preferences",
            token_count=150,
            items_included=[
                ContextItem(
                    id="memory_1",
                    type=ContextType.MEMORY,
                    content="User prefers simple explanations",
                    relevance_score=0.8,
                    recency_score=0.7,
                    importance_score=0.6,
                    combined_score=0.7
                )
            ],
            items_excluded=[],
            relevance_threshold=0.3
        )
        
        mock_context_integrator.integrate_context.return_value = integrated_context
        
        # Mock NLP services
        with patch("ai_karen_engine.chat.chat_orchestrator.nlp_service_manager") as mock_nlp:
            mock_nlp.parse_message.return_value = sample_parsed_message
            mock_nlp.get_embeddings.return_value = [0.1] * 768
            
            # Process the message
            response = await enhanced_orchestrator.process_message(sample_chat_request)
            
            assert isinstance(response, ChatResponse)
            assert response.context_used is True
            
            # Verify context integration was called with correct parameters
            mock_context_integrator.integrate_context.assert_called_once()
            call_args = mock_context_integrator.integrate_context.call_args
            assert call_args[0][1] == sample_chat_request.message  # current_message
            assert call_args[0][2] == sample_chat_request.user_id
            assert call_args[0][3] == sample_chat_request.conversation_id
    
    @pytest.mark.asyncio
    async def test_instruction_persistence_across_turns(
        self, enhanced_orchestrator, mock_instruction_processor
    ):
        """Test that instructions persist across conversation turns."""
        # Setup persistent instructions
        persistent_instruction = ExtractedInstruction(
            id="persistent_1",
            type=InstructionType.PREFERENCE,
            content="always use bullet points",
            priority=InstructionPriority.MEDIUM,
            scope=InstructionScope.SESSION,
            confidence=0.8,
            extracted_at=datetime.utcnow()
        )
        
        mock_instruction_processor.get_active_instructions.return_value = [persistent_instruction]
        
        # First message
        request_1 = ChatRequest(
            message="Explain Python basics.",
            user_id="test_user",
            conversation_id="test_conversation",
            stream=False
        )
        
        # Second message
        request_2 = ChatRequest(
            message="Now explain functions.",
            user_id="test_user",
            conversation_id="test_conversation",
            stream=False
        )
        
        with patch("ai_karen_engine.chat.chat_orchestrator.nlp_service_manager") as mock_nlp:
            mock_nlp.parse_message.return_value = ParsedMessage(
                text="test", tokens=["test"], entities=[], pos_tags=[], 
                dependencies=[], sentiment_score=0.0, used_fallback=False
            )
            mock_nlp.get_embeddings.return_value = [0.1] * 768
            
            # Process both messages
            await enhanced_orchestrator.process_message(request_1)
            await enhanced_orchestrator.process_message(request_2)
            
            # Verify that active instructions were retrieved for both messages
            assert mock_instruction_processor.get_active_instructions.call_count == 2
    
    @pytest.mark.asyncio
    async def test_enhanced_prompt_building(self, enhanced_orchestrator, mock_instruction_processor):
        """Test enhanced prompt building with instructions."""
        # Setup instructions
        instructions = [
            ExtractedInstruction(
                id="constraint_1",
                type=InstructionType.CONSTRAINT,
                content="don't use technical jargon",
                priority=InstructionPriority.HIGH,
                scope=InstructionScope.CONVERSATION,
                confidence=0.9,
                extracted_at=datetime.utcnow()
            ),
            ExtractedInstruction(
                id="format_1",
                type=InstructionType.FORMAT,
                content="use bullet points",
                priority=InstructionPriority.MEDIUM,
                scope=InstructionScope.CURRENT_MESSAGE,
                confidence=0.7,
                extracted_at=datetime.utcnow()
            )
        ]
        
        # Mock the apply_instructions_to_prompt method
        def mock_apply_instructions(base_prompt, instructions_list, context):
            enhanced = f"IMPORTANT INSTRUCTIONS:\n- {instructions[0].content}\n\nSTYLE & FORMAT:\n- {instructions[1].content}\n\n{base_prompt}"
            return enhanced
        
        mock_instruction_processor.apply_instructions_to_prompt.side_effect = mock_apply_instructions
        
        # Test the enhanced prompt building
        integrated_context = IntegratedContext(
            primary_context="Test context",
            supporting_context="",
            context_summary="Test summary",
            token_count=50,
            items_included=[],
            items_excluded=[],
            relevance_threshold=0.3
        )
        
        enhanced_prompt = await enhanced_orchestrator._build_enhanced_prompt(
            "Explain machine learning", integrated_context, instructions
        )
        
        assert "IMPORTANT INSTRUCTIONS" in enhanced_prompt
        assert "don't use technical jargon" in enhanced_prompt
        assert "STYLE & FORMAT" in enhanced_prompt
        assert "use bullet points" in enhanced_prompt
        assert "Explain machine learning" in enhanced_prompt
        assert "CONTEXT:" in enhanced_prompt
        assert "Test context" in enhanced_prompt
    
    @pytest.mark.asyncio
    async def test_enhanced_fallback_response(self, enhanced_orchestrator):
        """Test enhanced fallback response generation."""
        # Create sample data
        parsed_message = ParsedMessage(
            text="Explain Python",
            tokens=["explain", "python"],
            entities=[("Python", "LANGUAGE")],
            pos_tags=[],
            dependencies=[],
            sentiment_score=0.0,
            used_fallback=False
        )
        
        integrated_context = IntegratedContext(
            primary_context="KEY ENTITIES: Python: LANGUAGE",
            supporting_context="USER PREFERENCES: Use examples",
            context_summary="Context includes: 1 entities, 1 user_preferences",
            token_count=100,
            items_included=[
                ContextItem(
                    id="entity_1",
                    type=ContextType.ENTITIES,
                    content="Python: LANGUAGE",
                    relevance_score=0.8,
                    recency_score=1.0,
                    importance_score=0.7,
                    combined_score=0.8
                )
            ],
            items_excluded=[],
            relevance_threshold=0.3
        )
        
        instructions = [
            ExtractedInstruction(
                id="high_priority",
                type=InstructionType.CONSTRAINT,
                content="use simple language",
                priority=InstructionPriority.HIGH,
                scope=InstructionScope.CONVERSATION,
                confidence=0.9,
                extracted_at=datetime.utcnow()
            )
        ]
        
        response = await enhanced_orchestrator._generate_enhanced_fallback_response(
            "Explain Python", parsed_message, integrated_context, instructions
        )
        
        assert isinstance(response, str)
        assert len(response) > 0
        assert "I'll keep your instructions in mind" in response
        assert "use simple language" in response
        assert "Explain Python" in response
        assert "Using context: entities" in response
    
    @pytest.mark.asyncio
    async def test_error_handling_in_enhanced_processing(
        self, enhanced_orchestrator, sample_chat_request, mock_instruction_processor
    ):
        """Test error handling in enhanced processing components."""
        # Make instruction processor fail
        mock_instruction_processor.extract_instructions.side_effect = Exception("Instruction processing failed")
        
        with patch("ai_karen_engine.chat.chat_orchestrator.nlp_service_manager") as mock_nlp:
            mock_nlp.parse_message.return_value = ParsedMessage(
                text="test", tokens=["test"], entities=[], pos_tags=[], 
                dependencies=[], sentiment_score=0.0, used_fallback=False
            )
            mock_nlp.get_embeddings.return_value = [0.1] * 768
            
            # Should not fail completely due to instruction processing error
            response = await enhanced_orchestrator.process_message(sample_chat_request)
            
            assert isinstance(response, ChatResponse)
            assert response.response is not None
            # Should still process the message despite instruction processing failure
    
    @pytest.mark.asyncio
    async def test_streaming_with_enhanced_features(
        self, enhanced_orchestrator, mock_instruction_processor, mock_context_integrator
    ):
        """Test streaming response with enhanced features."""
        streaming_request = ChatRequest(
            message="Explain AI in simple terms",
            user_id="test_user",
            conversation_id="test_conversation",
            stream=True,
            include_context=True
        )
        
        # Setup mocks
        mock_instruction_processor.extract_instructions.return_value = []
        mock_instruction_processor.get_active_instructions.return_value = []
        
        with patch("ai_karen_engine.chat.chat_orchestrator.nlp_service_manager") as mock_nlp:
            mock_nlp.parse_message.return_value = ParsedMessage(
                text="test", tokens=["test"], entities=[], pos_tags=[], 
                dependencies=[], sentiment_score=0.0, used_fallback=False
            )
            mock_nlp.get_embeddings.return_value = [0.1] * 768
            
            # Process streaming message
            stream_generator = await enhanced_orchestrator.process_message(streaming_request)
            
            # Collect streaming chunks
            chunks = []
            async for chunk in stream_generator:
                chunks.append(chunk)
            
            assert len(chunks) > 0
            
            # Should have metadata chunk
            metadata_chunks = [chunk for chunk in chunks if chunk.type == "metadata"]
            assert len(metadata_chunks) > 0
            
            # Should have content chunks
            content_chunks = [chunk for chunk in chunks if chunk.type == "content"]
            assert len(content_chunks) > 0
            
            # Should have completion chunk
            complete_chunks = [chunk for chunk in chunks if chunk.type == "complete"]
            assert len(complete_chunks) > 0
    
    @pytest.mark.asyncio
    async def test_instruction_scope_filtering_in_processing(
        self, enhanced_orchestrator, mock_instruction_processor
    ):
        """Test that instruction scope filtering works in processing."""
        # Setup instructions with different scopes
        instructions = [
            ExtractedInstruction(
                id="current",
                type=InstructionType.TASK,
                content="current message task",
                priority=InstructionPriority.HIGH,
                scope=InstructionScope.CURRENT_MESSAGE,
                confidence=0.8,
                extracted_at=datetime.utcnow()
            ),
            ExtractedInstruction(
                id="session",
                type=InstructionType.PREFERENCE,
                content="session preference",
                priority=InstructionPriority.MEDIUM,
                scope=InstructionScope.SESSION,
                confidence=0.7,
                extracted_at=datetime.utcnow()
            )
        ]
        
        mock_instruction_processor.extract_instructions.return_value = []
        mock_instruction_processor.get_active_instructions.return_value = instructions
        
        request = ChatRequest(
            message="Test message",
            user_id="test_user",
            conversation_id="test_conversation",
            stream=False
        )
        
        with patch("ai_karen_engine.chat.chat_orchestrator.nlp_service_manager") as mock_nlp:
            mock_nlp.parse_message.return_value = ParsedMessage(
                text="test", tokens=["test"], entities=[], pos_tags=[], 
                dependencies=[], sentiment_score=0.0, used_fallback=False
            )
            mock_nlp.get_embeddings.return_value = [0.1] * 768
            
            response = await enhanced_orchestrator.process_message(request)
            
            assert isinstance(response, ChatResponse)
            
            # Verify that get_active_instructions was called
            mock_instruction_processor.get_active_instructions.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_context_token_limit_handling(
        self, enhanced_orchestrator, mock_context_integrator
    ):
        """Test handling of context token limits."""
        # Setup context integrator to return context at token limit
        large_context = IntegratedContext(
            primary_context="Very large primary context " * 100,
            supporting_context="Large supporting context " * 50,
            context_summary="Large context summary",
            token_count=1500,  # Near token limit
            items_included=[],
            items_excluded=[
                ContextItem(
                    id="excluded_1",
                    type=ContextType.MEMORY,
                    content="Excluded due to token limit",
                    relevance_score=0.6,
                    recency_score=0.5,
                    importance_score=0.4,
                    combined_score=0.5
                )
            ],
            relevance_threshold=0.3
        )
        
        mock_context_integrator.integrate_context.return_value = large_context
        
        request = ChatRequest(
            message="Test with large context",
            user_id="test_user",
            conversation_id="test_conversation",
            stream=False,
            include_context=True
        )
        
        with patch("ai_karen_engine.chat.chat_orchestrator.nlp_service_manager") as mock_nlp:
            mock_nlp.parse_message.return_value = ParsedMessage(
                text="test", tokens=["test"], entities=[], pos_tags=[], 
                dependencies=[], sentiment_score=0.0, used_fallback=False
            )
            mock_nlp.get_embeddings.return_value = [0.1] * 768
            
            response = await enhanced_orchestrator.process_message(request)
            
            assert isinstance(response, ChatResponse)
            assert response.context_used is True
            
            # Should handle large context gracefully
            assert "token_count" in response.metadata
    
    def test_enhanced_orchestrator_initialization(self):
        """Test that enhanced orchestrator initializes correctly."""
        orchestrator = ChatOrchestrator()
        
        # Should have default instruction processor and context integrator
        assert orchestrator.instruction_processor is not None
        assert orchestrator.context_integrator is not None
        
        # Should be instances of the correct classes
        assert isinstance(orchestrator.instruction_processor, InstructionProcessor)
        assert isinstance(orchestrator.context_integrator, ContextIntegrator)