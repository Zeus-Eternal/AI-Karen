"""
Tests for the PromptBuilder implementation.
"""

import pytest
from pathlib import Path
from unittest.mock import patch

from src.ai_karen_engine.core.response.prompt_builder import PromptBuilder


class TestPromptBuilder:
    """Test cases for PromptBuilder."""
    
    @pytest.fixture
    def prompt_builder(self):
        """Create a PromptBuilder instance for testing."""
        return PromptBuilder()
    
    def test_build_prompt_basic(self, prompt_builder):
        """Test basic prompt building functionality."""
        user_text = "Help me optimize this code"
        persona = "ruthless_optimizer"
        context = [{"text": "Previous discussion about performance"}]
        
        result = prompt_builder.build_prompt(
            user_text=user_text,
            persona=persona,
            context=context,
            intent="optimize_code",
            mood="neutral"
        )
        
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["role"] == "system"
        assert result[1]["role"] == "user"
        assert persona in result[0]["content"]
        assert user_text in result[1]["content"]
    
    def test_build_prompt_with_onboarding(self, prompt_builder):
        """Test prompt building with onboarding gaps."""
        user_text = "I need help with my project"
        persona = "calm_fixit"
        context = []
        gaps = ["project_context", "tech_stack"]
        
        result = prompt_builder.build_prompt(
            user_text=user_text,
            persona=persona,
            context=context,
            gaps=gaps,
            intent="general_assist",
            mood="frustrated"
        )
        
        assert len(result) == 2
        assert "project_context" in result[1]["content"]
        assert "Quick Setup Needed" in result[1]["content"]
    
    def test_build_prompt_with_context(self, prompt_builder):
        """Test prompt building with memory context."""
        user_text = "Continue with the optimization"
        persona = "ruthless_optimizer"
        context = [
            {"text": "We discussed database queries"},
            {"text": "You mentioned N+1 problems"},
            {"text": "Performance metrics were shared"}
        ]
        
        result = prompt_builder.build_prompt(
            user_text=user_text,
            persona=persona,
            context=context,
            intent="optimize_code"
        )
        
        user_content = result[1]["content"]
        assert "Context" in user_content
        assert "database queries" in user_content
        assert "N+1 problems" in user_content
    
    def test_build_prompt_copilotkit_enabled(self, prompt_builder):
        """Test prompt building with CopilotKit capabilities."""
        user_text = "Show me the code structure"
        persona = "technical_writer"
        context = []
        
        result = prompt_builder.build_prompt(
            user_text=user_text,
            persona=persona,
            context=context,
            ui_caps={"copilotkit": True},
            intent="documentation"
        )
        
        system_content = result[0]["content"]
        assert "enhanced UI features" in system_content
    
    def test_build_prompt_frustrated_mood(self, prompt_builder):
        """Test prompt building with frustrated mood handling."""
        user_text = "This isn't working at all!"
        persona = "calm_fixit"
        context = []
        
        result = prompt_builder.build_prompt(
            user_text=user_text,
            persona=persona,
            context=context,
            mood="frustrated",
            intent="debug_error"
        )
        
        system_content = result[0]["content"]
        assert "calm and patient" in system_content
        assert "overwhelmed" in system_content
    
    def test_fallback_on_template_error(self, prompt_builder):
        """Test fallback behavior when template rendering fails."""
        # Mock template loading to raise an error
        with patch.object(prompt_builder, '_get_template', side_effect=Exception("Template error")):
            result = prompt_builder.build_prompt(
                user_text="Test message",
                persona="test_persona",
                context=[]
            )
            
            assert len(result) == 2
            assert result[0]["role"] == "system"
            assert result[1]["role"] == "user"
            assert "test_persona" in result[0]["content"]
            assert "Test message" in result[1]["content"]
    
    def test_render_template_direct(self, prompt_builder):
        """Test direct template rendering."""
        result = prompt_builder.render_template(
            "system_base",
            persona="test_persona",
            intent="test_intent",
            mood="neutral",
            ui_caps={},
            copilotkit_enabled=False
        )
        
        assert isinstance(result, str)
        assert "test_persona" in result
    
    def test_template_caching(self, prompt_builder):
        """Test that templates are cached properly."""
        # First call should load template
        prompt_builder._get_template("system_base")
        assert "system_base" in prompt_builder._template_cache
        
        # Second call should use cached version
        cached_template = prompt_builder._get_template("system_base")
        assert cached_template is prompt_builder._template_cache["system_base"]
    
    def test_context_truncation(self, prompt_builder):
        """Test that context is properly truncated in templates."""
        user_text = "Help me understand"
        persona = "technical_writer"
        context = [{"text": f"Context item {i}"} for i in range(10)]
        
        result = prompt_builder.build_prompt(
            user_text=user_text,
            persona=persona,
            context=context
        )
        
        user_content = result[1]["content"]
        # Should only show first 3 context items
        assert "Context item 0" in user_content
        assert "Context item 1" in user_content
        assert "Context item 2" in user_content
        # Should indicate more items available
        assert "7 more relevant items" in user_content
    
    def test_different_personas(self, prompt_builder):
        """Test different persona handling in templates."""
        personas = ["ruthless_optimizer", "calm_fixit", "technical_writer"]
        
        for persona in personas:
            result = prompt_builder.build_prompt(
                user_text="Test message",
                persona=persona,
                context=[]
            )
            
            system_content = result[0]["content"]
            assert persona in system_content
    
    def test_different_intents(self, prompt_builder):
        """Test different intent handling in templates."""
        intents = ["optimize_code", "debug_error", "documentation", "general_assist"]
        
        for intent in intents:
            result = prompt_builder.build_prompt(
                user_text="Test message",
                persona="ruthless_optimizer",
                context=[],
                intent=intent
            )
            
            # Should not raise any errors
            assert len(result) == 2
            assert isinstance(result[0]["content"], str)
            assert isinstance(result[1]["content"], str)