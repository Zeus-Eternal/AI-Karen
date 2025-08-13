"""
Tests for the InstructionProcessor module.

This module tests the enhanced instruction processing capabilities including
instruction extraction, persistence, and application to prompts.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

from ai_karen_engine.chat.instruction_processor import (
    InstructionProcessor,
    InstructionContext,
    ExtractedInstruction,
    InstructionType,
    InstructionPriority,
    InstructionScope
)


class TestInstructionProcessor:
    """Test the InstructionProcessor class."""
    
    @pytest.fixture
    def processor(self):
        """Create an InstructionProcessor instance for testing."""
        return InstructionProcessor()
    
    @pytest.fixture
    def sample_context(self):
        """Create a sample instruction context."""
        return InstructionContext(
            user_id="test_user",
            conversation_id="test_conversation",
            session_id="test_session"
        )
    
    @pytest.mark.asyncio
    async def test_extract_task_instructions(self, processor, sample_context):
        """Test extraction of task-type instructions."""
        message = "Please analyze this data and create a summary report."
        
        instructions = await processor.extract_instructions(message, sample_context)
        
        assert len(instructions) > 0
        task_instructions = [inst for inst in instructions if inst.type == InstructionType.TASK]
        assert len(task_instructions) > 0
        
        task_inst = task_instructions[0]
        assert "analyze this data and create a summary report" in task_inst.content.lower()
        assert task_inst.priority == InstructionPriority.HIGH
        assert task_inst.confidence > 0.5
    
    @pytest.mark.asyncio
    async def test_extract_preference_instructions(self, processor, sample_context):
        """Test extraction of preference-type instructions."""
        message = "I prefer detailed explanations with examples."
        
        instructions = await processor.extract_instructions(message, sample_context)
        
        preference_instructions = [inst for inst in instructions if inst.type == InstructionType.PREFERENCE]
        assert len(preference_instructions) > 0
        
        pref_inst = preference_instructions[0]
        assert "detailed explanations with examples" in pref_inst.content.lower()
        assert pref_inst.scope == InstructionScope.SESSION
    
    @pytest.mark.asyncio
    async def test_extract_constraint_instructions(self, processor, sample_context):
        """Test extraction of constraint-type instructions."""
        message = "Don't include any personal information in your response."
        
        instructions = await processor.extract_instructions(message, sample_context)
        
        constraint_instructions = [inst for inst in instructions if inst.type == InstructionType.CONSTRAINT]
        assert len(constraint_instructions) > 0
        
        constraint_inst = constraint_instructions[0]
        assert "include any personal information" in constraint_inst.content.lower()
        assert constraint_inst.priority == InstructionPriority.HIGH
    
    @pytest.mark.asyncio
    async def test_extract_format_instructions(self, processor, sample_context):
        """Test extraction of format-type instructions."""
        message = "Format your response as a bulleted list."
        
        instructions = await processor.extract_instructions(message, sample_context)
        
        format_instructions = [inst for inst in instructions if inst.type == InstructionType.FORMAT]
        assert len(format_instructions) > 0
        
        format_inst = format_instructions[0]
        assert "bulleted list" in format_inst.content.lower()
        assert format_inst.scope == InstructionScope.CURRENT_MESSAGE
    
    @pytest.mark.asyncio
    async def test_extract_style_instructions(self, processor, sample_context):
        """Test extraction of style-type instructions."""
        message = "Be more formal in your responses."
        
        instructions = await processor.extract_instructions(message, sample_context)
        
        style_instructions = [inst for inst in instructions if inst.type == InstructionType.STYLE]
        assert len(style_instructions) > 0
        
        style_inst = style_instructions[0]
        assert style_inst.scope == InstructionScope.SESSION
    
    @pytest.mark.asyncio
    async def test_extract_behavior_instructions(self, processor, sample_context):
        """Test extraction of behavior-type instructions."""
        message = "Act like a professional consultant when responding."
        
        instructions = await processor.extract_instructions(message, sample_context)
        
        behavior_instructions = [inst for inst in instructions if inst.type == InstructionType.BEHAVIOR]
        assert len(behavior_instructions) > 0
        
        behavior_inst = behavior_instructions[0]
        assert "professional consultant" in behavior_inst.content.lower()
        assert behavior_inst.priority == InstructionPriority.HIGH
    
    @pytest.mark.asyncio
    async def test_extract_correction_instructions(self, processor, sample_context):
        """Test extraction of correction-type instructions."""
        message = "Actually, I meant to ask about Python, not Java."
        
        instructions = await processor.extract_instructions(message, sample_context)
        
        correction_instructions = [inst for inst in instructions if inst.type == InstructionType.CORRECTION]
        assert len(correction_instructions) > 0
        
        correction_inst = correction_instructions[0]
        assert "python, not java" in correction_inst.content.lower()
        assert correction_inst.priority == InstructionPriority.HIGH
    
    @pytest.mark.asyncio
    async def test_instruction_confidence_adjustment(self, processor, sample_context):
        """Test that instruction confidence is adjusted based on context."""
        # Message with explicit instruction words should have higher confidence
        explicit_message = "Please make sure to include examples in your response!"
        
        instructions = await processor.extract_instructions(explicit_message, sample_context)
        
        assert len(instructions) > 0
        # Should have boosted confidence due to "please" and "!"
        high_confidence_inst = max(instructions, key=lambda x: x.confidence)
        assert high_confidence_inst.confidence > 0.7
        
        # Question should have lower confidence
        question_message = "Should I include examples in responses?"
        question_instructions = await processor.extract_instructions(question_message, sample_context)
        
        if question_instructions:
            question_inst = question_instructions[0]
            assert question_inst.confidence < high_confidence_inst.confidence
    
    @pytest.mark.asyncio
    async def test_instruction_storage_and_retrieval(self, processor, sample_context):
        """Test storing and retrieving instructions."""
        message = "Always use bullet points in your responses."
        
        # Extract and store instructions
        instructions = await processor.extract_instructions(message, sample_context)
        await processor.store_instructions(instructions, sample_context)
        
        # Retrieve active instructions
        active_instructions = await processor.get_active_instructions(sample_context)
        
        assert len(active_instructions) > 0
        stored_inst = active_instructions[0]
        assert "bullet points" in stored_inst.content.lower()
        assert stored_inst.scope == InstructionScope.GLOBAL
    
    @pytest.mark.asyncio
    async def test_instruction_expiry(self, processor, sample_context):
        """Test that instructions expire based on their scope."""
        # Create an instruction that should expire quickly
        instruction = ExtractedInstruction(
            id="test_instruction",
            type=InstructionType.TASK,
            content="test content",
            priority=InstructionPriority.MEDIUM,
            scope=InstructionScope.CURRENT_MESSAGE,
            confidence=0.8,
            extracted_at=datetime.utcnow(),
            expires_at=datetime.utcnow() - timedelta(minutes=1)  # Already expired
        )
        
        assert instruction.is_expired()
        
        # Create a non-expiring instruction
        global_instruction = ExtractedInstruction(
            id="global_instruction",
            type=InstructionType.PREFERENCE,
            content="global preference",
            priority=InstructionPriority.MEDIUM,
            scope=InstructionScope.GLOBAL,
            confidence=0.8,
            extracted_at=datetime.utcnow(),
            expires_at=None
        )
        
        assert not global_instruction.is_expired()
    
    @pytest.mark.asyncio
    async def test_apply_instructions_to_prompt(self, processor, sample_context):
        """Test applying instructions to enhance a prompt."""
        base_prompt = "Explain machine learning."
        
        # Create sample instructions
        instructions = [
            ExtractedInstruction(
                id="high_priority",
                type=InstructionType.CONSTRAINT,
                content="don't use technical jargon",
                priority=InstructionPriority.HIGH,
                scope=InstructionScope.CONVERSATION,
                confidence=0.9,
                extracted_at=datetime.utcnow()
            ),
            ExtractedInstruction(
                id="preference",
                type=InstructionType.PREFERENCE,
                content="include practical examples",
                priority=InstructionPriority.MEDIUM,
                scope=InstructionScope.SESSION,
                confidence=0.8,
                extracted_at=datetime.utcnow()
            ),
            ExtractedInstruction(
                id="format",
                type=InstructionType.FORMAT,
                content="use bullet points",
                priority=InstructionPriority.MEDIUM,
                scope=InstructionScope.CURRENT_MESSAGE,
                confidence=0.7,
                extracted_at=datetime.utcnow()
            )
        ]
        
        enhanced_prompt = await processor.apply_instructions_to_prompt(
            base_prompt, instructions, sample_context
        )
        
        assert "IMPORTANT INSTRUCTIONS" in enhanced_prompt
        assert "don't use technical jargon" in enhanced_prompt
        assert "USER PREFERENCES" in enhanced_prompt
        assert "include practical examples" in enhanced_prompt
        assert "STYLE & FORMAT" in enhanced_prompt
        assert "use bullet points" in enhanced_prompt
        assert base_prompt in enhanced_prompt
    
    @pytest.mark.asyncio
    async def test_instruction_scope_filtering(self, processor, sample_context):
        """Test filtering instructions by scope."""
        # Store instructions with different scopes
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
            ),
            ExtractedInstruction(
                id="global",
                type=InstructionType.BEHAVIOR,
                content="global behavior",
                priority=InstructionPriority.LOW,
                scope=InstructionScope.GLOBAL,
                confidence=0.6,
                extracted_at=datetime.utcnow()
            )
        ]
        
        await processor.store_instructions(instructions, sample_context)
        
        # Filter by specific scopes
        session_and_global = await processor.get_active_instructions(
            sample_context,
            scope_filter={InstructionScope.SESSION, InstructionScope.GLOBAL}
        )
        
        assert len(session_and_global) == 2
        scopes = {inst.scope for inst in session_and_global}
        assert InstructionScope.SESSION in scopes
        assert InstructionScope.GLOBAL in scopes
        assert InstructionScope.CURRENT_MESSAGE not in scopes
    
    @pytest.mark.asyncio
    async def test_instruction_summary(self, processor, sample_context):
        """Test getting instruction summary."""
        # Store some instructions
        instructions = [
            ExtractedInstruction(
                id="task1",
                type=InstructionType.TASK,
                content="task instruction",
                priority=InstructionPriority.HIGH,
                scope=InstructionScope.CONVERSATION,
                confidence=0.8,
                extracted_at=datetime.utcnow()
            ),
            ExtractedInstruction(
                id="pref1",
                type=InstructionType.PREFERENCE,
                content="preference instruction",
                priority=InstructionPriority.MEDIUM,
                scope=InstructionScope.SESSION,
                confidence=0.7,
                extracted_at=datetime.utcnow()
            )
        ]
        
        await processor.store_instructions(instructions, sample_context)
        
        summary = processor.get_instruction_summary(sample_context)
        
        assert summary["total"] == 2
        assert summary["by_type"]["task"] == 1
        assert summary["by_type"]["preference"] == 1
        assert summary["by_priority"]["high"] == 1
        assert summary["by_priority"]["medium"] == 1
        assert summary["most_recent"] is not None
    
    @pytest.mark.asyncio
    async def test_clear_instructions(self, processor, sample_context):
        """Test clearing instructions."""
        # Store some instructions
        instructions = [
            ExtractedInstruction(
                id="task1",
                type=InstructionType.TASK,
                content="task instruction",
                priority=InstructionPriority.HIGH,
                scope=InstructionScope.CONVERSATION,
                confidence=0.8,
                extracted_at=datetime.utcnow()
            ),
            ExtractedInstruction(
                id="pref1",
                type=InstructionType.PREFERENCE,
                content="preference instruction",
                priority=InstructionPriority.MEDIUM,
                scope=InstructionScope.SESSION,
                confidence=0.7,
                extracted_at=datetime.utcnow()
            )
        ]
        
        await processor.store_instructions(instructions, sample_context)
        
        # Clear specific type
        cleared_count = processor.clear_instructions(sample_context, InstructionType.TASK)
        assert cleared_count == 1
        
        # Verify only preference remains
        remaining = await processor.get_active_instructions(sample_context)
        assert len(remaining) == 1
        assert remaining[0].type == InstructionType.PREFERENCE
        
        # Clear all
        cleared_count = processor.clear_instructions(sample_context)
        assert cleared_count == 1
        
        # Verify all cleared
        remaining = await processor.get_active_instructions(sample_context)
        assert len(remaining) == 0
    
    @pytest.mark.asyncio
    async def test_complex_instruction_extraction(self, processor, sample_context):
        """Test extraction from complex messages with multiple instruction types."""
        complex_message = """
        Please analyze the sales data and create a detailed report. 
        I prefer visual charts over tables. 
        Make sure to highlight any anomalies, but don't include customer names. 
        Format the response as a structured document with clear sections.
        """
        
        instructions = await processor.extract_instructions(complex_message, sample_context)
        
        # Should extract multiple types of instructions
        instruction_types = {inst.type for inst in instructions}
        
        # Should have at least task, preference, constraint, and format instructions
        assert InstructionType.TASK in instruction_types
        assert len(instructions) >= 3  # Should extract multiple instructions
        
        # Verify specific content
        task_instructions = [inst for inst in instructions if inst.type == InstructionType.TASK]
        assert any("analyze the sales data" in inst.content.lower() for inst in task_instructions)
        
        constraint_instructions = [inst for inst in instructions if inst.type == InstructionType.CONSTRAINT]
        assert any("customer names" in inst.content.lower() for inst in constraint_instructions)
    
    @pytest.mark.asyncio
    async def test_empty_message_handling(self, processor, sample_context):
        """Test handling of empty or very short messages."""
        empty_message = ""
        short_message = "Hi"
        
        empty_instructions = await processor.extract_instructions(empty_message, sample_context)
        short_instructions = await processor.extract_instructions(short_message, sample_context)
        
        assert len(empty_instructions) == 0
        # Short messages might not contain meaningful instructions
        assert len(short_instructions) == 0 or all(len(inst.content) >= 3 for inst in short_instructions)
    
    def test_instruction_serialization(self):
        """Test instruction serialization and deserialization."""
        instruction = ExtractedInstruction(
            id="test_id",
            type=InstructionType.PREFERENCE,
            content="test content",
            priority=InstructionPriority.HIGH,
            scope=InstructionScope.SESSION,
            confidence=0.8,
            extracted_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=1),
            metadata={"test": "value"}
        )
        
        # Test to_dict
        data = instruction.to_dict()
        assert data["id"] == "test_id"
        assert data["type"] == "preference"
        assert data["priority"] == "high"
        assert data["scope"] == "session"
        assert data["confidence"] == 0.8
        assert data["metadata"]["test"] == "value"
        
        # Test from_dict
        reconstructed = ExtractedInstruction.from_dict(data)
        assert reconstructed.id == instruction.id
        assert reconstructed.type == instruction.type
        assert reconstructed.priority == instruction.priority
        assert reconstructed.scope == instruction.scope
        assert reconstructed.confidence == instruction.confidence
        assert reconstructed.metadata == instruction.metadata