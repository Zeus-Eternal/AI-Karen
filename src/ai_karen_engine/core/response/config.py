"""
Configuration dataclass for the Response Core pipeline.

This module defines the PipelineConfig dataclass that controls the behavior
of the ResponseOrchestrator and its components.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional


@dataclass(frozen=True)
class PipelineConfig:
    """Configuration for the Response Core pipeline.
    
    This configuration controls the behavior of the ResponseOrchestrator,
    including persona selection, model routing, and feature flags.
    """
    
    # Persona Configuration
    persona_default: str = "ruthless_optimizer"
    persona_mapping: Dict[str, Dict[str, str]] = field(default_factory=lambda: {
        "frustrated": {"mood": "calm_fixit"},
        "optimize_code": {"intent": "ruthless_optimizer"},
        "documentation": {"intent": "technical_writer"},
        "debug_error": {"intent": "calm_fixit"},
        "general_assist": {"intent": "ruthless_optimizer"},
    })
    
    # Model Selection Configuration
    max_context_tokens: int = 8192
    local_only: bool = True  # Cloud is optional acceleration
    local_model_preference: str = "local:tinyllama-1.1b"
    cloud_routing_threshold: int = 4096  # Use cloud for large contexts when enabled
    
    # Memory Configuration
    memory_recall_limit: int = 5
    memory_relevance_threshold: float = 0.7
    
    # Feature Flags
    enable_copilotkit: bool = True
    enable_onboarding: bool = True
    enable_persona_detection: bool = True
    enable_memory_persistence: bool = True
    
    # Performance Configuration
    request_timeout: float = 30.0
    max_retries: int = 2
    retry_backoff: float = 1.0
    
    # Observability Configuration
    enable_metrics: bool = True
    enable_audit_logging: bool = True
    correlation_id_header: str = "X-Correlation-ID"
    
    # Template Configuration
    template_directory: str = "templates/response"
    system_template: str = "system_base.jinja2"
    user_template: str = "user_frame.jinja2"
    onboarding_template: str = "onboarding.jinja2"
    
    # Security Configuration
    admin_only_cloud_config: bool = True
    admin_only_premium_plugins: bool = True
    local_privacy_guarantee: bool = True
    
    def get_persona_for_intent_mood(self, intent: str, mood: str) -> str:
        """Get persona based on intent and mood.
        
        Args:
            intent: Detected user intent
            mood: Detected user mood/sentiment
            
        Returns:
            Persona string to use for response generation
        """
        # Check mood-based mapping first (higher priority)
        if mood in self.persona_mapping:
            mood_mapping = self.persona_mapping[mood]
            if "mood" in mood_mapping:
                return mood_mapping["mood"]
        
        # Check intent-based mapping
        if intent in self.persona_mapping:
            intent_mapping = self.persona_mapping[intent]
            if "intent" in intent_mapping:
                return intent_mapping["intent"]
        
        # Return default persona
        return self.persona_default
    
    def should_use_cloud(self, context_tokens: int, explicit_cloud: bool = False) -> bool:
        """Determine if cloud routing should be used.
        
        Args:
            context_tokens: Number of tokens in context
            explicit_cloud: Whether cloud was explicitly requested
            
        Returns:
            True if cloud routing should be used
        """
        if self.local_only and not explicit_cloud:
            return False
        
        if explicit_cloud:
            return True
            
        return context_tokens > self.cloud_routing_threshold
    
    def get_template_path(self, template_type: str) -> str:
        """Get full path for a template.
        
        Args:
            template_type: Type of template ('system', 'user', 'onboarding')
            
        Returns:
            Full path to template file
        """
        template_map = {
            "system": self.system_template,
            "user": self.user_template,
            "onboarding": self.onboarding_template,
        }
        
        template_file = template_map.get(template_type, self.system_template)
        return f"{self.template_directory}/{template_file}"


# Default configuration instance
DEFAULT_CONFIG = PipelineConfig()