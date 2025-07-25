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
                "system_prompt": """You are Karen, an advanced AI assistant with persistent memory and access to plugins. Your goal is to be exceptionally helpful and proactive. Use the provided context, memories, and user preferences to deliver a personalized and intelligent response.""",
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
                "variables": ["prompt", "context_info", "plugin_info", "memory_info", "user_preferences"]
            }
        }
    
    def get_template(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a registered template."""
        return self._templates.get(name)
    
    def get_available_templates(self) -> List[str]:
        """Get list of available template names."""
        return list(self._templates.keys())
