"""
Jinja2-based prompt construction for the Response Core orchestrator.

This module implements the PromptBuilder protocol to create structured prompts
using Jinja2 templates with persona and context data injection.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
import logging

from jinja2 import Environment, FileSystemLoader, Template, TemplateNotFound

from .protocols import PromptBuilder as PromptBuilderProtocol

logger = logging.getLogger(__name__)


class PromptBuilder(PromptBuilderProtocol):
    """Jinja2-based prompt builder implementing the PromptBuilder protocol."""
    
    def __init__(self, template_dir: Optional[Path] = None):
        """Initialize the PromptBuilder with template directory.
        
        Args:
            template_dir: Directory containing Jinja2 templates. 
                         Defaults to templates/ in the same directory as this file.
        """
        if template_dir is None:
            template_dir = Path(__file__).parent / "templates"
        
        self.template_dir = Path(template_dir)
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True,
        )
        
        # Cache for loaded templates
        self._template_cache: Dict[str, Template] = {}
        
        logger.info(f"PromptBuilder initialized with template directory: {self.template_dir}")
    
    def build_prompt(
        self, 
        user_text: str, 
        persona: str, 
        context: List[Dict[str, Any]], 
        **kwargs
    ) -> List[Dict[str, str]]:
        """Build structured prompt from components.
        
        Args:
            user_text: User's input text
            persona: Selected persona
            context: Retrieved context from memory
            **kwargs: Additional prompt variables (intent, mood, gaps, etc.)
            
        Returns:
            List of message dictionaries for LLM with 'role' and 'content' keys
        """
        try:
            # Extract additional variables
            intent = kwargs.get('intent', 'general_assist')
            mood = kwargs.get('mood', 'neutral')
            gaps = kwargs.get('gaps', [])
            ui_caps = kwargs.get('ui_caps', {})
            
            # Build system message with persona and context
            system_content = self._render_system_base(
                persona=persona,
                intent=intent,
                mood=mood,
                ui_caps=ui_caps
            )
            
            # Build user message with context and user input
            user_content = self._render_user_frame(
                user_text=user_text,
                context=context,
                intent=intent,
                persona=persona
            )
            
            # Add onboarding guidance if gaps exist
            if gaps:
                onboarding_content = self._render_onboarding(
                    gaps=gaps,
                    persona=persona,
                    intent=intent
                )
                user_content += "\n\n" + onboarding_content
            
            messages = [
                {"role": "system", "content": system_content},
                {"role": "user", "content": user_content}
            ]
            
            logger.debug(f"Built prompt with persona={persona}, intent={intent}, context_items={len(context)}")
            return messages
            
        except Exception as e:
            logger.error(f"Error building prompt: {e}")
            # Fallback to simple prompt structure
            return self._build_fallback_prompt(user_text, persona)
    
    def _render_system_base(self, persona: str, intent: str, mood: str, ui_caps: Dict[str, Any]) -> str:
        """Render the system_base template with persona and context."""
        try:
            template = self._get_template("system_base")
            return template.render(
                persona=persona,
                intent=intent,
                mood=mood,
                ui_caps=ui_caps,
                copilotkit_enabled=ui_caps.get('copilotkit', False)
            )
        except TemplateNotFound:
            logger.warning("system_base template not found, using fallback")
            return f"You are {persona}. The user's intent appears to be {intent} and their mood is {mood}."
    
    def _render_user_frame(self, user_text: str, context: List[Dict[str, Any]], intent: str, persona: str) -> str:
        """Render the user_frame template with user input and context."""
        try:
            template = self._get_template("user_frame")
            return template.render(
                user_text=user_text,
                context=context,
                intent=intent,
                persona=persona,
                context_count=len(context)
            )
        except TemplateNotFound:
            logger.warning("user_frame template not found, using fallback")
            context_text = ""
            if context:
                context_text = "\n\nRelevant context:\n" + "\n".join([
                    f"- {ctx.get('text', str(ctx))}" for ctx in context[:3]
                ])
            return f"{user_text}{context_text}"
    
    def _render_onboarding(self, gaps: List[str], persona: str, intent: str) -> str:
        """Render the onboarding template with profile gaps."""
        try:
            template = self._get_template("onboarding")
            return template.render(
                gaps=gaps,
                persona=persona,
                intent=intent,
                primary_gap=gaps[0] if gaps else None
            )
        except TemplateNotFound:
            logger.warning("onboarding template not found, using fallback")
            if gaps:
                return f"To help you better, I need to know: {gaps[0]}"
            return ""
    
    def _get_template(self, template_name: str) -> Template:
        """Get template from cache or load it."""
        if template_name not in self._template_cache:
            try:
                self._template_cache[template_name] = self.env.get_template(f"{template_name}.j2")
            except TemplateNotFound:
                logger.error(f"Template {template_name}.j2 not found in {self.template_dir}")
                raise
        return self._template_cache[template_name]
    
    def _build_fallback_prompt(self, user_text: str, persona: str) -> List[Dict[str, str]]:
        """Build a simple fallback prompt when template rendering fails."""
        return [
            {"role": "system", "content": f"You are {persona}."},
            {"role": "user", "content": user_text}
        ]
    
    # Convenience methods for direct template rendering
    def render_template(self, template_name: str, **variables) -> str:
        """Render a specific template with variables.
        
        Args:
            template_name: Name of template (without .j2 extension)
            **variables: Template variables
            
        Returns:
            Rendered template content
        """
        try:
            template = self._get_template(template_name)
            return template.render(**variables)
        except Exception as e:
            logger.error(f"Error rendering template {template_name}: {e}")
            return f"Template rendering failed: {e}"