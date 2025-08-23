"""
LLM Profile Models and Validation

This module defines the data models for LLM profiles with copilot-specific
routing strategies, validation logic, and cloud gating requirements.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
import logging

logger = logging.getLogger(__name__)


class RoutingStrategy(Enum):
    """Routing strategies for LLM provider selection."""
    LOCAL_FIRST_OPTIONAL_CLOUD = "local_first_optional_cloud"
    CLOUD_FIRST_LOCAL_FALLBACK = "cloud_first_local_fallback"
    BALANCED = "balanced"
    LOCAL_ONLY = "local_only"


class PrivacyLevel(Enum):
    """Privacy levels that influence routing decisions."""
    PUBLIC = "public"          # Can use any provider
    INTERNAL = "internal"      # Prefer local or trusted providers
    CONFIDENTIAL = "confidential"  # Local only
    RESTRICTED = "restricted"  # Core helpers only


class TaskType(Enum):
    """Types of tasks that influence routing decisions."""
    CHAT = "chat"
    CODE = "code"
    REASONING = "reasoning"
    EMBEDDING = "embedding"
    SUMMARIZATION = "summarization"
    TRANSLATION = "translation"
    CREATIVE = "creative"
    ANALYSIS = "analysis"


@dataclass
class CloudGating:
    """Cloud gating requirements for profile validation."""
    requires_feature_flag: Optional[str] = None
    requires_api_key: Optional[str] = None
    requires_policy_approval: bool = False


@dataclass
class ModelConfig:
    """Configuration for a specific model in a profile."""
    provider: str
    model: str
    priority: int = 50
    task_types: List[str] = field(default_factory=list)
    require_api_key_ref: Optional[str] = None
    when_flag: Optional[str] = None
    privacy_levels: List[str] = field(default_factory=lambda: ["public", "internal", "confidential"])
    capabilities: List[str] = field(default_factory=list)
    max_tokens: Optional[int] = None
    timeout_seconds: Optional[int] = None


@dataclass
class RoutingConfig:
    """Routing configuration for a profile."""
    strategy: RoutingStrategy
    allow_cloud_fallback: bool = False
    enforce_local_for_sensitive: bool = True
    cloud_gating: Optional[CloudGating] = None


@dataclass
class LLMProfile:
    """Enhanced LLM profile with copilot-specific routing strategies."""
    id: str
    label: str
    description: str = ""
    default: bool = False
    
    # Routing configuration
    routing: RoutingConfig = field(default_factory=lambda: RoutingConfig(RoutingStrategy.LOCAL_FIRST_OPTIONAL_CLOUD))
    
    # Model configurations
    models: List[ModelConfig] = field(default_factory=list)
    
    # Privacy constraints
    privacy_constraints: Dict[str, List[str]] = field(default_factory=dict)
    
    # Performance settings
    max_tokens_default: Optional[int] = None
    timeout_seconds: int = 30
    cost_limit_per_operation: Optional[float] = None
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    is_active: bool = False
    
    def validate(self, settings_manager=None) -> List[str]:
        """
        Validate profile configuration and return list of validation errors.
        
        Args:
            settings_manager: Optional settings manager for checking feature flags and API keys
            
        Returns:
            List of validation error messages
        """
        errors = []
        
        # Basic validation
        if not self.id:
            errors.append("Profile ID is required")
        
        if not self.label:
            errors.append("Profile label is required")
        
        if not self.models:
            errors.append("Profile must have at least one model configuration")
        
        # Validate model configurations
        for i, model in enumerate(self.models):
            model_errors = self._validate_model_config(model, i, settings_manager)
            errors.extend(model_errors)
        
        # Validate routing configuration
        routing_errors = self._validate_routing_config(settings_manager)
        errors.extend(routing_errors)
        
        # Validate privacy constraints
        privacy_errors = self._validate_privacy_constraints()
        errors.extend(privacy_errors)
        
        return errors
    
    def _validate_model_config(self, model: ModelConfig, index: int, settings_manager=None) -> List[str]:
        """Validate individual model configuration."""
        errors = []
        
        if not model.provider:
            errors.append(f"Model {index}: Provider is required")
        
        if not model.model:
            errors.append(f"Model {index}: Model name is required")
        
        if model.priority < 0 or model.priority > 100:
            errors.append(f"Model {index}: Priority must be between 0 and 100")
        
        # Validate task types
        valid_task_types = [t.value for t in TaskType]
        for task_type in model.task_types:
            if task_type not in valid_task_types:
                errors.append(f"Model {index}: Invalid task type '{task_type}'")
        
        # Validate privacy levels
        valid_privacy_levels = [p.value for p in PrivacyLevel]
        for privacy_level in model.privacy_levels:
            if privacy_level not in valid_privacy_levels:
                errors.append(f"Model {index}: Invalid privacy level '{privacy_level}'")
        
        # Validate cloud gating requirements
        if settings_manager and (model.require_api_key_ref or model.when_flag):
            gating_errors = self._validate_cloud_gating_for_model(model, index, settings_manager)
            errors.extend(gating_errors)
        
        return errors
    
    def _validate_routing_config(self, settings_manager=None) -> List[str]:
        """Validate routing configuration."""
        errors = []
        
        # Validate cloud gating if cloud fallback is allowed
        if self.routing.allow_cloud_fallback and self.routing.cloud_gating and settings_manager:
            gating_errors = self._validate_cloud_gating(settings_manager)
            errors.extend(gating_errors)
        
        return errors
    
    def _validate_privacy_constraints(self) -> List[str]:
        """Validate privacy constraints configuration."""
        errors = []
        
        valid_privacy_levels = [p.value for p in PrivacyLevel]
        for privacy_level, providers in self.privacy_constraints.items():
            if privacy_level not in valid_privacy_levels:
                errors.append(f"Invalid privacy level in constraints: '{privacy_level}'")
            
            if not isinstance(providers, list):
                errors.append(f"Privacy constraint for '{privacy_level}' must be a list of providers")
        
        return errors
    
    def _validate_cloud_gating(self, settings_manager) -> List[str]:
        """Validate cloud gating requirements."""
        errors = []
        
        if not self.routing.cloud_gating:
            return errors
        
        # Check feature flag requirement
        if self.routing.cloud_gating.requires_feature_flag:
            flag_name = self.routing.cloud_gating.requires_feature_flag
            if not settings_manager.get_feature_flag(flag_name):
                errors.append(f"Required feature flag '{flag_name}' is not enabled")
        
        # Check API key requirement
        if self.routing.cloud_gating.requires_api_key:
            key_name = self.routing.cloud_gating.requires_api_key
            if not settings_manager.has_secret(key_name):
                errors.append(f"Required API key '{key_name}' is not configured")
        
        return errors
    
    def _validate_cloud_gating_for_model(self, model: ModelConfig, index: int, settings_manager) -> List[str]:
        """Validate cloud gating requirements for a specific model."""
        errors = []
        
        # Check feature flag requirement
        if model.when_flag:
            if not settings_manager.get_feature_flag(model.when_flag):
                errors.append(f"Model {index}: Required feature flag '{model.when_flag}' is not enabled")
        
        # Check API key requirement
        if model.require_api_key_ref:
            if not settings_manager.has_secret(model.require_api_key_ref):
                errors.append(f"Model {index}: Required API key '{model.require_api_key_ref}' is not configured")
        
        return errors
    
    def get_models_for_task(self, task_type: str, privacy_level: PrivacyLevel = PrivacyLevel.INTERNAL) -> List[ModelConfig]:
        """
        Get models suitable for a specific task type and privacy level.
        
        Args:
            task_type: The type of task to find models for
            privacy_level: The privacy level constraint
            
        Returns:
            List of suitable models sorted by priority (highest first)
        """
        suitable_models = []
        
        # Get allowed providers for this privacy level
        allowed_providers = self.privacy_constraints.get(privacy_level.value, [])
        
        for model in self.models:
            # Check if model supports this task type (empty list means all tasks)
            if model.task_types and task_type not in model.task_types:
                continue
            
            # Check privacy level constraint
            if privacy_level.value not in model.privacy_levels:
                continue
            
            # Check if provider is allowed for this privacy level
            if allowed_providers and model.provider not in allowed_providers:
                continue
            
            suitable_models.append(model)
        
        # Sort by priority (highest first)
        suitable_models.sort(key=lambda m: m.priority, reverse=True)
        
        return suitable_models
    
    def can_use_cloud_providers(self, settings_manager=None) -> bool:
        """
        Check if this profile can use cloud providers based on gating requirements.
        
        Args:
            settings_manager: Settings manager for checking flags and keys
            
        Returns:
            True if cloud providers can be used, False otherwise
        """
        if not self.routing.allow_cloud_fallback:
            return False
        
        if not self.routing.cloud_gating or not settings_manager:
            return True  # No gating requirements
        
        # Check feature flag requirement
        if self.routing.cloud_gating.requires_feature_flag:
            flag_name = self.routing.cloud_gating.requires_feature_flag
            if not settings_manager.get_feature_flag(flag_name):
                return False
        
        # Check API key requirement
        if self.routing.cloud_gating.requires_api_key:
            key_name = self.routing.cloud_gating.requires_api_key
            if not settings_manager.has_secret(key_name):
                return False
        
        return True


@dataclass
class CapabilityRouting:
    """Routing configuration for specific copilot capabilities."""
    preferred_providers: List[str] = field(default_factory=list)
    required_capabilities: List[str] = field(default_factory=list)
    privacy_level: str = "internal"
    force_local: bool = False


@dataclass
class ProfilesConfig:
    """Complete profiles configuration including global settings."""
    profiles: List[LLMProfile] = field(default_factory=list)
    capability_routing: Dict[str, CapabilityRouting] = field(default_factory=dict)
    routing_policies: Dict[str, Any] = field(default_factory=dict)
    performance_settings: Dict[str, Any] = field(default_factory=dict)
    
    def get_default_profile(self) -> Optional[LLMProfile]:
        """Get the default profile."""
        for profile in self.profiles:
            if profile.default:
                return profile
        return self.profiles[0] if self.profiles else None
    
    def get_profile_by_id(self, profile_id: str) -> Optional[LLMProfile]:
        """Get profile by ID."""
        for profile in self.profiles:
            if profile.id == profile_id:
                return profile
        return None
    
    def validate_all_profiles(self, settings_manager=None) -> Dict[str, List[str]]:
        """
        Validate all profiles and return validation results.
        
        Returns:
            Dictionary mapping profile IDs to lists of validation errors
        """
        validation_results = {}
        
        for profile in self.profiles:
            errors = profile.validate(settings_manager)
            if errors:
                validation_results[profile.id] = errors
        
        return validation_results