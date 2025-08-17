import logging
from typing import Any, Dict, List, Optional


class PromptManager:
    """
    Handles structured prompt templates and generation.
    """
    
    def __init__(self):
        self.logger = logging.getLogger("ai_orchestrator.prompt_manager")
        self._templates: Dict[str, Dict[str, Any]] = self._load_default_templates()
        for name in self._templates:
            self.logger.info(f"Registered prompt template: {name}")
    
    def _load_default_templates(self) -> Dict[str, Dict[str, Any]]:
        """Load default prompt templates. For production, this should load from a config file."""
        return {
            "conversation_processing": {
                "system_prompt": """You are Karen, an advanced AI assistant with persistent memory and access to plugins. Your goal is to be exceptionally helpful and proactive. Use the provided context, memories, and user preferences to deliver a personalized and intelligent response.

{personality_instructions}

{custom_instructions}""",
                "user_template": """**User Query:** "{prompt}"

**Available Context:**
{context_info}

**Available Plugins:**
{plugin_info}

**Relevant Memories:**
{memory_info}

**User Preferences:**
{user_preferences}

**Instructions:**
Provide a comprehensive response. Integrate relevant memories naturally. Assess if a plugin is needed. Identify new information to remember. Be proactive.""",
                "variables": ["prompt", "context_info", "plugin_info", "memory_info", "user_preferences", "personality_instructions", "custom_instructions"]
            },
            "decision_making": {
                "system_prompt": """You are Karen, an AI assistant focused on understanding user intent and deciding the best course of action. Analyze the user's request and determine if any tools or plugins are needed.

{personality_instructions}

{custom_instructions}""",
                "user_template": """**User Request:** "{prompt}"

**Available Tools:** {available_tools}

**Context:** {context_info}

**Instructions:**
Analyze the user's intent and decide if any tools are needed. If tools are required, specify which ones and why. If not, provide a helpful response.""",
                "variables": ["prompt", "available_tools", "context_info", "personality_instructions", "custom_instructions"]
            }
        }
    
    def get_template(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a registered template."""
        return self._templates.get(name)
    
    def get_available_templates(self) -> List[str]:
        """Get list of available template names."""
        return list(self._templates.keys())
    
    def build_system_prompt(self, template_name: str, user_settings: Dict[str, Any]) -> str:
        """Build a dynamic system prompt with user preferences."""
        template = self.get_template(template_name)
        if not template:
            self.logger.warning(f"Template '{template_name}' not found, using default")
            return "You are Karen, an AI assistant. Be helpful and conversational."
        
        # Extract user preferences
        personality_tone = user_settings.get("personality_tone", "friendly")
        personality_verbosity = user_settings.get("personality_verbosity", "balanced")
        custom_persona_instructions = user_settings.get("custom_persona_instructions", "")
        
        # Build personality instructions
        personality_instructions = self._build_personality_instructions(
            personality_tone, personality_verbosity
        )
        
        # Build custom instructions
        custom_instructions = ""
        if custom_persona_instructions:
            custom_instructions = f"**Custom Instructions:** {custom_persona_instructions}"
        
        # Format the system prompt
        try:
            system_prompt = template["system_prompt"].format(
                personality_instructions=personality_instructions,
                custom_instructions=custom_instructions
            )
            return system_prompt
        except KeyError as e:
            self.logger.error(f"Missing template variable: {e}")
            return template["system_prompt"]
    
    def _build_personality_instructions(self, tone: str, verbosity: str) -> str:
        """Build personality instructions based on user preferences."""
        instructions = []
        
        # Tone instructions
        tone_instructions = {
            "friendly": "Maintain a warm, approachable, and friendly tone in all interactions.",
            "formal": "Use a professional, formal tone while remaining helpful and clear.",
            "humorous": "Incorporate appropriate humor and wit while staying helpful and informative.",
            "neutral": "Use a balanced, neutral tone that is neither too casual nor too formal."
        }
        
        if tone in tone_instructions:
            instructions.append(tone_instructions[tone])
        
        # Verbosity instructions
        verbosity_instructions = {
            "concise": "Keep responses brief and to the point. Avoid unnecessary elaboration.",
            "balanced": "Provide comprehensive responses with appropriate detail level.",
            "detailed": "Provide thorough, detailed explanations with examples and context when helpful."
        }
        
        if verbosity in verbosity_instructions:
            instructions.append(verbosity_instructions[verbosity])
        
        return " ".join(instructions) if instructions else ""
    
    def build_user_prompt(self, template_name: str, **kwargs) -> str:
        """Build a user prompt from template with provided variables."""
        template = self.get_template(template_name)
        if not template:
            self.logger.warning(f"Template '{template_name}' not found")
            return kwargs.get("prompt", "")
        
        try:
            # Ensure all required variables have default values
            template_vars = template.get("variables", [])
            formatted_kwargs = {}
            
            for var in template_vars:
                if var in kwargs:
                    formatted_kwargs[var] = kwargs[var]
                else:
                    # Provide sensible defaults
                    defaults = {
                        "prompt": "",
                        "context_info": "No additional context available",
                        "plugin_info": "No plugins available",
                        "memory_info": "No relevant memories",
                        "user_preferences": "No specific preferences",
                        "personality_instructions": "",
                        "custom_instructions": "",
                        "available_tools": "No tools available"
                    }
                    formatted_kwargs[var] = defaults.get(var, "")
            
            return template["user_template"].format(**formatted_kwargs)
        except KeyError as e:
            self.logger.error(f"Missing template variable: {e}")
            return kwargs.get("prompt", "")
