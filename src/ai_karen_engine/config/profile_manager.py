"""
LLM Profile Manager

This module manages LLM profiles including loading from YAML configuration,
validation, switching between profiles, and audit logging.
"""

import logging
import yaml
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .profile_models import (
    LLMProfile, ProfilesConfig, RoutingConfig, ModelConfig, CloudGating,
    RoutingStrategy, CapabilityRouting
)

logger = logging.getLogger(__name__)


class ProfileManager:
    """
    Manages LLM profiles with validation, switching, and audit logging.
    """
    
    def __init__(self, config_path: Optional[Path] = None, settings_manager=None):
        """
        Initialize profile manager.
        
        Args:
            config_path: Path to llm_profiles.yml file
            settings_manager: Settings manager for validation
        """
        self.config_path = config_path or Path("config/llm_profiles.yml")
        self.settings_manager = settings_manager
        self.profiles_config: Optional[ProfilesConfig] = None
        self.active_profile_id: Optional[str] = None
        self._load_profiles()
    
    def _load_profiles(self) -> None:
        """Load profiles from YAML configuration file."""
        try:
            if not self.config_path.exists():
                logger.warning(f"Profile config file not found: {self.config_path}")
                self.profiles_config = ProfilesConfig()
                return
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            
            self.profiles_config = self._parse_config(config_data)
            
            # Set active profile to default
            default_profile = self.profiles_config.get_default_profile()
            if default_profile:
                self.active_profile_id = default_profile.id
                default_profile.is_active = True
            
            logger.info(f"Loaded {len(self.profiles_config.profiles)} profiles from {self.config_path}")
            
        except Exception as e:
            logger.error(f"Failed to load profiles from {self.config_path}: {e}")
            self.profiles_config = ProfilesConfig()
    
    def _parse_config(self, config_data: Dict[str, Any]) -> ProfilesConfig:
        """Parse YAML configuration data into ProfilesConfig object."""
        profiles = []
        
        # Parse profiles
        for profile_data in config_data.get('profiles', []):
            profile = self._parse_profile(profile_data)
            profiles.append(profile)
        
        # Parse capability routing
        capability_routing = {}
        for cap_id, cap_data in config_data.get('capability_routing', {}).items():
            capability_routing[cap_id] = CapabilityRouting(
                preferred_providers=cap_data.get('preferred_providers', []),
                required_capabilities=cap_data.get('required_capabilities', []),
                privacy_level=cap_data.get('privacy_level', 'internal'),
                force_local=cap_data.get('force_local', False)
            )
        
        return ProfilesConfig(
            profiles=profiles,
            capability_routing=capability_routing,
            routing_policies=config_data.get('routing_policies', {}),
            performance_settings=config_data.get('performance_settings', {})
        )
    
    def _parse_profile(self, profile_data: Dict[str, Any]) -> LLMProfile:
        """Parse individual profile data."""
        # Parse routing configuration
        routing_data = profile_data.get('routing', {})
        cloud_gating_data = routing_data.get('cloud_gating', {})
        
        cloud_gating = None
        if cloud_gating_data:
            cloud_gating = CloudGating(
                requires_feature_flag=cloud_gating_data.get('requires_feature_flag'),
                requires_api_key=cloud_gating_data.get('requires_api_key'),
                requires_policy_approval=cloud_gating_data.get('requires_policy_approval', False)
            )
        
        routing = RoutingConfig(
            strategy=RoutingStrategy(routing_data.get('strategy', 'local_first_optional_cloud')),
            allow_cloud_fallback=routing_data.get('allow_cloud_fallback', False),
            enforce_local_for_sensitive=routing_data.get('enforce_local_for_sensitive', True),
            cloud_gating=cloud_gating
        )
        
        # Parse model configurations
        models = []
        for model_data in profile_data.get('models', []):
            model = ModelConfig(
                provider=model_data['provider'],
                model=model_data['model'],
                priority=model_data.get('priority', 50),
                task_types=model_data.get('task_types', []),
                require_api_key_ref=model_data.get('require_api_key_ref'),
                when_flag=model_data.get('when_flag'),
                privacy_levels=model_data.get('privacy_levels', ['public', 'internal', 'confidential']),
                capabilities=model_data.get('capabilities', []),
                max_tokens=model_data.get('max_tokens'),
                timeout_seconds=model_data.get('timeout_seconds')
            )
            models.append(model)
        
        return LLMProfile(
            id=profile_data['id'],
            label=profile_data['label'],
            description=profile_data.get('description', ''),
            default=profile_data.get('default', False),
            routing=routing,
            models=models,
            privacy_constraints=profile_data.get('privacy_constraints', {}),
            max_tokens_default=profile_data.get('max_tokens_default'),
            timeout_seconds=profile_data.get('timeout_seconds', 30),
            cost_limit_per_operation=profile_data.get('cost_limit_per_operation')
        )
    
    def get_active_profile(self) -> Optional[LLMProfile]:
        """Get the currently active profile."""
        if not self.profiles_config or not self.active_profile_id:
            return None
        
        return self.profiles_config.get_profile_by_id(self.active_profile_id)
    
    def get_profile_by_id(self, profile_id: str) -> Optional[LLMProfile]:
        """Get profile by ID."""
        if not self.profiles_config:
            return None
        
        return self.profiles_config.get_profile_by_id(profile_id)
    
    def list_profiles(self) -> List[LLMProfile]:
        """Get list of all available profiles."""
        if not self.profiles_config:
            return []
        
        return self.profiles_config.profiles
    
    def set_active_profile(self, profile_id: str, user_id: Optional[str] = None) -> LLMProfile:
        """
        Set the active profile with validation and audit logging.
        
        Args:
            profile_id: ID of the profile to activate
            user_id: ID of the user making the change (for audit logging)
            
        Returns:
            The activated profile
            
        Raises:
            ValueError: If profile not found or validation fails
        """
        if not self.profiles_config:
            raise ValueError("No profiles configuration loaded")
        
        # Find the profile
        new_profile = self.profiles_config.get_profile_by_id(profile_id)
        if not new_profile:
            raise ValueError(f"Profile not found: {profile_id}")
        
        # Validate the profile
        validation_errors = new_profile.validate(self.settings_manager)
        if validation_errors:
            error_msg = f"Profile validation failed: {'; '.join(validation_errors)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Deactivate current profile
        if self.active_profile_id:
            current_profile = self.profiles_config.get_profile_by_id(self.active_profile_id)
            if current_profile:
                current_profile.is_active = False
        
        # Activate new profile
        new_profile.is_active = True
        new_profile.updated_at = datetime.utcnow()
        self.active_profile_id = profile_id
        
        # Log the profile change
        self._log_profile_change(profile_id, user_id)
        
        logger.info(f"Switched to profile: {profile_id} ({new_profile.label})")
        
        return new_profile
    
    def validate_profile(self, profile_id: str) -> List[str]:
        """
        Validate a specific profile.
        
        Args:
            profile_id: ID of the profile to validate
            
        Returns:
            List of validation error messages (empty if valid)
        """
        if not self.profiles_config:
            return ["No profiles configuration loaded"]
        
        profile = self.profiles_config.get_profile_by_id(profile_id)
        if not profile:
            return [f"Profile not found: {profile_id}"]
        
        return profile.validate(self.settings_manager)
    
    def validate_all_profiles(self) -> Dict[str, List[str]]:
        """
        Validate all profiles.
        
        Returns:
            Dictionary mapping profile IDs to lists of validation errors
        """
        if not self.profiles_config:
            return {"_global": ["No profiles configuration loaded"]}
        
        return self.profiles_config.validate_all_profiles(self.settings_manager)
    
    def get_capability_routing(self, capability_id: str) -> Optional[CapabilityRouting]:
        """Get routing configuration for a specific capability."""
        if not self.profiles_config:
            return None
        
        return self.profiles_config.capability_routing.get(capability_id)
    
    def get_routing_policies(self) -> Dict[str, Any]:
        """Get global routing policies."""
        if not self.profiles_config:
            return {}
        
        return self.profiles_config.routing_policies
    
    def get_performance_settings(self) -> Dict[str, Any]:
        """Get global performance settings."""
        if not self.profiles_config:
            return {}
        
        return self.profiles_config.performance_settings
    
    def reload_profiles(self) -> None:
        """Reload profiles from configuration file."""
        logger.info("Reloading profiles configuration")
        self._load_profiles()
    
    def get_profile_status(self) -> Dict[str, Any]:
        """
        Get comprehensive status of all profiles.
        
        Returns:
            Dictionary with profile status information
        """
        if not self.profiles_config:
            return {
                "active_profile": None,
                "total_profiles": 0,
                "profiles": [],
                "validation_errors": {"_global": ["No profiles configuration loaded"]}
            }
        
        # Validate all profiles
        validation_results = self.validate_all_profiles()
        
        # Build profile status list
        profile_status = []
        for profile in self.profiles_config.profiles:
            can_use_cloud = profile.can_use_cloud_providers(self.settings_manager)
            
            status = {
                "id": profile.id,
                "label": profile.label,
                "description": profile.description,
                "is_active": profile.is_active,
                "is_default": profile.default,
                "routing_strategy": profile.routing.strategy.value,
                "allow_cloud_fallback": profile.routing.allow_cloud_fallback,
                "can_use_cloud": can_use_cloud,
                "model_count": len(profile.models),
                "validation_errors": validation_results.get(profile.id, []),
                "is_valid": profile.id not in validation_results,
                "updated_at": profile.updated_at.isoformat() if profile.updated_at else None
            }
            profile_status.append(status)
        
        return {
            "active_profile": self.active_profile_id,
            "total_profiles": len(self.profiles_config.profiles),
            "profiles": profile_status,
            "validation_errors": validation_results,
            "capability_routing_count": len(self.profiles_config.capability_routing),
            "config_path": str(self.config_path)
        }
    
    def _log_profile_change(self, profile_id: str, user_id: Optional[str] = None) -> None:
        """Log profile change for audit purposes."""
        try:
            # Import here to avoid circular imports
            from ai_karen_engine.services.audit_logger import get_audit_logger
            
            audit_logger = get_audit_logger()
            if audit_logger:
                audit_logger.log_event(
                    event_type="copilot.profile.changed",
                    user_id=user_id,
                    details={
                        "new_profile": profile_id,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
        except Exception as e:
            logger.warning(f"Failed to log profile change: {e}")


# Global profile manager instance
_profile_manager_instance: Optional[ProfileManager] = None


def get_profile_manager(settings_manager=None) -> ProfileManager:
    """Get global profile manager instance."""
    global _profile_manager_instance
    if _profile_manager_instance is None:
        _profile_manager_instance = ProfileManager(settings_manager=settings_manager)
    return _profile_manager_instance


def reload_profile_manager(settings_manager=None) -> ProfileManager:
    """Reload the global profile manager instance."""
    global _profile_manager_instance
    _profile_manager_instance = ProfileManager(settings_manager=settings_manager)
    return _profile_manager_instance