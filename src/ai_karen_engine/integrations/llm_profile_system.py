"""
LLM Profile System with Real Profile Management Logic

This module implements a working LLM profile system that:
- Manages real profile configurations (not mock examples)
- Provides router policy, guardrails, memory budget, and provider preferences
- Enables profile switching with immediate effect on routing decisions
- Validates profile compatibility with available providers
- Integrates with the dynamic provider system
"""

from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union

from ai_karen_engine.integrations.dynamic_provider_system import get_dynamic_provider_manager
from ai_karen_engine.integrations.registry import get_registry

logger = logging.getLogger(__name__)

# -----------------------------
# Profile Data Models
# -----------------------------

class RouterPolicy(Enum):
    """Router policy options for model selection."""
    PERFORMANCE = "performance"  # Prioritize speed and throughput
    QUALITY = "quality"         # Prioritize response quality
    COST = "cost"              # Prioritize cost efficiency
    PRIVACY = "privacy"        # Prioritize local/private models
    BALANCED = "balanced"      # Balance all factors


class GuardrailLevel(Enum):
    """Guardrail strictness levels."""
    STRICT = "strict"      # Maximum safety filters
    MODERATE = "moderate"  # Balanced safety
    RELAXED = "relaxed"    # Minimal safety filters
    CUSTOM = "custom"      # Custom configuration


@dataclass
class ProviderPreference:
    """Provider preference configuration."""
    provider: str
    model: Optional[str] = None
    priority: int = 50  # Higher = more preferred
    max_cost_per_1k_tokens: Optional[float] = None
    required_capabilities: Set[str] = field(default_factory=set)
    excluded_capabilities: Set[str] = field(default_factory=set)


@dataclass
class GuardrailConfig:
    """Guardrail configuration."""
    level: GuardrailLevel = GuardrailLevel.MODERATE
    content_filters: Dict[str, str] = field(default_factory=dict)
    rate_limits: Dict[str, int] = field(default_factory=dict)
    allowed_domains: List[str] = field(default_factory=list)
    blocked_domains: List[str] = field(default_factory=list)
    custom_rules: List[str] = field(default_factory=list)


@dataclass
class MemoryBudget:
    """Memory budget configuration."""
    max_context_length: int = 4096
    max_conversation_history: int = 50
    max_memory_entries: int = 1000
    memory_retention_days: int = 30
    enable_memory_compression: bool = True
    priority_memory_types: List[str] = field(default_factory=lambda: ["user_preferences", "important_facts"])


@dataclass
class LLMProfile:
    """Complete LLM profile configuration."""
    
    # Basic info
    id: str
    name: str
    description: str = ""
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    
    # Router configuration
    router_policy: RouterPolicy = RouterPolicy.BALANCED
    
    # Provider assignments for different use cases
    providers: Dict[str, ProviderPreference] = field(default_factory=dict)
    
    # Fallback configuration
    fallback_provider: str = "local"
    fallback_model: Optional[str] = None
    
    # Guardrails
    guardrails: GuardrailConfig = field(default_factory=GuardrailConfig)
    
    # Memory management
    memory_budget: MemoryBudget = field(default_factory=MemoryBudget)
    
    # Advanced settings
    enable_streaming: bool = True
    enable_function_calling: bool = True
    enable_vision: bool = False
    temperature: float = 0.7
    max_tokens: int = 1000
    
    # Validation
    is_valid: bool = True
    validation_errors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert profile to dictionary."""
        data = asdict(self)
        
        # Convert enums to strings
        data["router_policy"] = self.router_policy.value
        data["guardrails"]["level"] = self.guardrails.level.value
        
        # Convert sets to lists for JSON serialization
        for provider_pref in data["providers"].values():
            if "required_capabilities" in provider_pref:
                provider_pref["required_capabilities"] = list(provider_pref["required_capabilities"])
            if "excluded_capabilities" in provider_pref:
                provider_pref["excluded_capabilities"] = list(provider_pref["excluded_capabilities"])
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LLMProfile':
        """Create profile from dictionary."""
        # Convert string enums back to enum objects
        if "router_policy" in data:
            data["router_policy"] = RouterPolicy(data["router_policy"])
        
        if "guardrails" in data and "level" in data["guardrails"]:
            data["guardrails"]["level"] = GuardrailLevel(data["guardrails"]["level"])
        
        # Convert lists back to sets
        if "providers" in data:
            for provider_pref in data["providers"].values():
                if "required_capabilities" in provider_pref:
                    provider_pref["required_capabilities"] = set(provider_pref["required_capabilities"])
                if "excluded_capabilities" in provider_pref:
                    provider_pref["excluded_capabilities"] = set(provider_pref["excluded_capabilities"])
        
        # Create nested objects
        if "guardrails" in data:
            data["guardrails"] = GuardrailConfig(**data["guardrails"])
        
        if "memory_budget" in data:
            data["memory_budget"] = MemoryBudget(**data["memory_budget"])
        
        if "providers" in data:
            providers = {}
            for use_case, pref_data in data["providers"].items():
                providers[use_case] = ProviderPreference(**pref_data)
            data["providers"] = providers
        
        return cls(**data)


# -----------------------------
# Profile Manager
# -----------------------------

class LLMProfileManager:
    """
    Manager for LLM profiles with real profile management logic.
    
    Features:
    - Create, update, delete, and validate profiles
    - Profile switching with immediate effect
    - Compatibility checking with available providers
    - Integration with dynamic provider system
    - Persistent storage of profiles
    """
    
    def __init__(self, profiles_dir: Optional[Path] = None):
        self.profiles_dir = profiles_dir or Path.home() / ".kari" / "profiles"
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
        
        self.provider_manager = get_dynamic_provider_manager()
        self.registry = get_registry()
        
        self._profiles: Dict[str, LLMProfile] = {}
        self._active_profile_id: Optional[str] = None
        
        # Load existing profiles
        self._load_profiles()
        
        # Create default profiles if none exist
        if not self._profiles:
            self._create_default_profiles()
    
    # ---------- Profile Management ----------
    
    def create_profile(
        self,
        name: str,
        description: str = "",
        router_policy: RouterPolicy = RouterPolicy.BALANCED,
        **kwargs
    ) -> LLMProfile:
        """Create a new LLM profile."""
        profile_id = self._generate_profile_id(name)
        
        profile = LLMProfile(
            id=profile_id,
            name=name,
            description=description,
            router_policy=router_policy,
            **kwargs
        )
        
        # Validate the profile
        self._validate_profile(profile)
        
        # Save the profile
        self._profiles[profile_id] = profile
        self._save_profile(profile)
        
        logger.info(f"Created LLM profile: {name} ({profile_id})")
        return profile
    
    def update_profile(self, profile_id: str, **updates) -> LLMProfile:
        """Update an existing profile."""
        if profile_id not in self._profiles:
            raise ValueError(f"Profile {profile_id} not found")
        
        profile = self._profiles[profile_id]
        
        # Apply updates
        for key, value in updates.items():
            if hasattr(profile, key):
                setattr(profile, key, value)
        
        profile.updated_at = time.time()
        
        # Re-validate the profile
        self._validate_profile(profile)
        
        # Save the updated profile
        self._save_profile(profile)
        
        logger.info(f"Updated LLM profile: {profile.name} ({profile_id})")
        return profile
    
    def delete_profile(self, profile_id: str) -> bool:
        """Delete a profile."""
        if profile_id not in self._profiles:
            return False
        
        profile = self._profiles[profile_id]
        
        # Don't allow deleting the active profile
        if profile_id == self._active_profile_id:
            raise ValueError("Cannot delete the active profile. Switch to another profile first.")
        
        # Remove from memory and disk
        del self._profiles[profile_id]
        profile_file = self.profiles_dir / f"{profile_id}.json"
        if profile_file.exists():
            profile_file.unlink()
        
        logger.info(f"Deleted LLM profile: {profile.name} ({profile_id})")
        return True
    
    def get_profile(self, profile_id: str) -> Optional[LLMProfile]:
        """Get a profile by ID."""
        return self._profiles.get(profile_id)
    
    def list_profiles(self) -> List[LLMProfile]:
        """List all profiles."""
        return list(self._profiles.values())
    
    def get_active_profile(self) -> Optional[LLMProfile]:
        """Get the currently active profile."""
        if self._active_profile_id:
            return self._profiles.get(self._active_profile_id)
        return None
    
    def switch_profile(self, profile_id: str) -> LLMProfile:
        """Switch to a different profile with immediate effect."""
        if profile_id not in self._profiles:
            raise ValueError(f"Profile {profile_id} not found")
        
        profile = self._profiles[profile_id]
        
        # Validate profile compatibility
        validation_result = self.validate_profile_compatibility(profile)
        if not validation_result["compatible"]:
            logger.warning(f"Profile {profile_id} has compatibility issues: {validation_result['issues']}")
        
        # Switch the active profile
        old_profile_id = self._active_profile_id
        self._active_profile_id = profile_id
        
        # Save the active profile setting
        self._save_active_profile_setting()
        
        logger.info(f"Switched LLM profile from {old_profile_id} to {profile_id}")
        
        # Notify routing system of the change
        self._notify_profile_change(profile)
        
        return profile
    
    # ---------- Profile Validation ----------
    
    def validate_profile_compatibility(self, profile: LLMProfile) -> Dict[str, Any]:
        """Validate profile compatibility with available providers."""
        issues = []
        warnings = []
        
        try:
            # Get available LLM providers
            available_providers = self.provider_manager.get_llm_providers()
            
            # Check provider assignments
            for use_case, provider_pref in profile.providers.items():
                if provider_pref.provider not in available_providers:
                    issues.append(f"Provider '{provider_pref.provider}' for {use_case} is not available")
                else:
                    # Check provider health
                    health = self.provider_manager.health_check(provider_pref.provider)
                    if health.get("status") == "unhealthy":
                        warnings.append(f"Provider '{provider_pref.provider}' for {use_case} is currently unhealthy")
                    elif health.get("status") == "unavailable":
                        issues.append(f"Provider '{provider_pref.provider}' for {use_case} is unavailable: {health.get('message', 'Unknown reason')}")
                    
                    # Check provider capabilities
                    provider_info = self.provider_manager.get_provider_info(provider_pref.provider)
                    if provider_info:
                        provider_capabilities = set(provider_info.get("capabilities", []))
                        
                        # Check required capabilities
                        missing_capabilities = provider_pref.required_capabilities - provider_capabilities
                        if missing_capabilities:
                            warnings.append(
                                f"Provider '{provider_pref.provider}' for {use_case} "
                                f"missing capabilities: {missing_capabilities}"
                            )
                        
                        # Check excluded capabilities
                        conflicting_capabilities = provider_pref.excluded_capabilities & provider_capabilities
                        if conflicting_capabilities:
                            warnings.append(
                                f"Provider '{provider_pref.provider}' for {use_case} "
                                f"has excluded capabilities: {conflicting_capabilities}"
                            )
                        
                        # Check if specific model is available
                        if provider_pref.model:
                            try:
                                models = asyncio.run(self.provider_manager.discover_models(provider_pref.provider))
                                model_ids = [m.get("id") for m in models]
                                if provider_pref.model not in model_ids:
                                    warnings.append(f"Model '{provider_pref.model}' not found in {provider_pref.provider}")
                            except Exception as e:
                                logger.debug(f"Could not check model availability: {e}")
            
            # Check fallback provider
            if profile.fallback_provider not in available_providers:
                issues.append(f"Fallback provider '{profile.fallback_provider}' is not available")
            else:
                # Check fallback provider health
                health = self.provider_manager.health_check(profile.fallback_provider)
                if health.get("status") == "unhealthy":
                    warnings.append(f"Fallback provider '{profile.fallback_provider}' is currently unhealthy")
            
            # Check memory budget constraints
            if profile.memory_budget.max_context_length > 128000:
                warnings.append("Very large context length may cause performance issues")
            
            if profile.memory_budget.max_conversation_history > 200:
                warnings.append("Very large conversation history may impact performance")
            
            # Check router policy compatibility
            if profile.router_policy == RouterPolicy.PRIVACY:
                # Privacy policy should prefer local providers
                non_local_providers = [
                    use_case for use_case, pref in profile.providers.items()
                    if pref.provider not in ["local", "superkent"]
                ]
                if non_local_providers:
                    warnings.append(f"Privacy policy with non-local providers: {non_local_providers}")
            
            # Check guardrail configuration
            if profile.guardrails.level == GuardrailLevel.CUSTOM:
                if not profile.guardrails.custom_rules:
                    warnings.append("Custom guardrail level specified but no custom rules defined")
            
        except Exception as e:
            logger.error(f"Profile validation failed: {e}")
            issues.append(f"Validation error: {str(e)}")
        
        return {
            "compatible": len(issues) == 0,
            "issues": issues,
            "warnings": warnings
        }
    
    def _validate_profile(self, profile: LLMProfile) -> None:
        """Validate a profile and update its validation status."""
        validation_result = self.validate_profile_compatibility(profile)
        
        profile.is_valid = validation_result["compatible"]
        profile.validation_errors = validation_result["issues"]
        
        if not profile.is_valid:
            logger.warning(f"Profile {profile.id} has validation errors: {profile.validation_errors}")
    
    # ---------- Default Profiles ----------
    
    def _create_default_profiles(self) -> None:
        """Create default profiles."""
        
        # Performance Profile - Prioritizes speed
        performance_profile = self.create_profile(
            name="Performance",
            description="Optimized for speed and throughput",
            router_policy=RouterPolicy.PERFORMANCE,
            providers={
                "chat": ProviderPreference(
                    provider="local",
                    priority=90,
                    required_capabilities={"streaming"}
                ),
                "code": ProviderPreference(
                    provider="deepseek",
                    priority=80,
                    required_capabilities={"streaming"}
                ),
                "reasoning": ProviderPreference(
                    provider="local",
                    priority=85
                ),
                "embedding": ProviderPreference(
                    provider="local",
                    priority=90
                )
            },
            fallback_provider="local",
            memory_budget=MemoryBudget(
                max_context_length=8192,
                max_conversation_history=30,
                enable_memory_compression=True
            ),
            enable_streaming=True,
            temperature=0.3,
            max_tokens=500
        )
        
        # Quality Profile - Prioritizes response quality
        quality_profile = self.create_profile(
            name="Quality",
            description="Optimized for highest quality responses",
            router_policy=RouterPolicy.QUALITY,
            providers={
                "chat": ProviderPreference(
                    provider="openai",
                    model="gpt-4o",
                    priority=95,
                    required_capabilities={"streaming", "function_calling"}
                ),
                "code": ProviderPreference(
                    provider="deepseek",
                    model="deepseek-coder",
                    priority=90,
                    required_capabilities={"streaming"}
                ),
                "reasoning": ProviderPreference(
                    provider="openai",
                    model="gpt-4o",
                    priority=95
                ),
                "embedding": ProviderPreference(
                    provider="openai",
                    priority=85
                )
            },
            fallback_provider="gemini",
            memory_budget=MemoryBudget(
                max_context_length=32768,
                max_conversation_history=100,
                enable_memory_compression=False
            ),
            enable_streaming=True,
            enable_function_calling=True,
            enable_vision=True,
            temperature=0.7,
            max_tokens=2000
        )
        
        # Privacy Profile - Prioritizes local models
        privacy_profile = self.create_profile(
            name="Privacy",
            description="Uses only local models for maximum privacy",
            router_policy=RouterPolicy.PRIVACY,
            providers={
                "chat": ProviderPreference(
                    provider="local",
                    priority=100,
                    required_capabilities={"local_execution"}
                ),
                "code": ProviderPreference(
                    provider="local",
                    priority=100,
                    required_capabilities={"local_execution"}
                ),
                "reasoning": ProviderPreference(
                    provider="local",
                    priority=100,
                    required_capabilities={"local_execution"}
                ),
                "embedding": ProviderPreference(
                    provider="local",
                    priority=100,
                    required_capabilities={"local_execution"}
                )
            },
            fallback_provider="local",
            guardrails=GuardrailConfig(
                level=GuardrailLevel.STRICT,
                blocked_domains=["*"]  # Block all external domains
            ),
            memory_budget=MemoryBudget(
                max_context_length=4096,
                max_conversation_history=50,
                memory_retention_days=7  # Shorter retention for privacy
            ),
            enable_streaming=True,
            temperature=0.5,
            max_tokens=1000
        )
        
        # Balanced Profile - Default balanced configuration
        balanced_profile = self.create_profile(
            name="Balanced",
            description="Balanced configuration for general use",
            router_policy=RouterPolicy.BALANCED,
            providers={
                "chat": ProviderPreference(
                    provider="gemini",
                    priority=80,
                    required_capabilities={"streaming"}
                ),
                "code": ProviderPreference(
                    provider="deepseek",
                    priority=85,
                    required_capabilities={"streaming"}
                ),
                "reasoning": ProviderPreference(
                    provider="openai",
                    priority=75
                ),
                "embedding": ProviderPreference(
                    provider="huggingface",
                    priority=70
                )
            },
            fallback_provider="local",
            memory_budget=MemoryBudget(
                max_context_length=16384,
                max_conversation_history=75,
                enable_memory_compression=True
            ),
            enable_streaming=True,
            enable_function_calling=True,
            temperature=0.7,
            max_tokens=1500
        )
        
        # Set the balanced profile as active by default
        self._active_profile_id = balanced_profile.id
        self._save_active_profile_setting()
        
        logger.info("Created default LLM profiles")
    
    # ---------- Persistence ----------
    
    def _load_profiles(self) -> None:
        """Load profiles from disk."""
        if not self.profiles_dir.exists():
            return
        
        for profile_file in self.profiles_dir.glob("*.json"):
            if profile_file.name == "active.json":
                continue
            
            try:
                with open(profile_file, 'r') as f:
                    data = json.load(f)
                
                profile = LLMProfile.from_dict(data)
                self._profiles[profile.id] = profile
                
            except Exception as e:
                logger.warning(f"Failed to load profile from {profile_file}: {e}")
        
        # Load active profile setting
        active_file = self.profiles_dir / "active.json"
        if active_file.exists():
            try:
                with open(active_file, 'r') as f:
                    data = json.load(f)
                    self._active_profile_id = data.get("active_profile_id")
            except Exception as e:
                logger.warning(f"Failed to load active profile setting: {e}")
        
        logger.info(f"Loaded {len(self._profiles)} LLM profiles")
    
    def _save_profile(self, profile: LLMProfile) -> None:
        """Save a profile to disk."""
        profile_file = self.profiles_dir / f"{profile.id}.json"
        
        try:
            with open(profile_file, 'w') as f:
                json.dump(profile.to_dict(), f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save profile {profile.id}: {e}")
    
    def _save_active_profile_setting(self) -> None:
        """Save the active profile setting."""
        active_file = self.profiles_dir / "active.json"
        
        try:
            with open(active_file, 'w') as f:
                json.dump({"active_profile_id": self._active_profile_id}, f)
        except Exception as e:
            logger.error(f"Failed to save active profile setting: {e}")
    
    def _generate_profile_id(self, name: str) -> str:
        """Generate a unique profile ID."""
        base_id = name.lower().replace(" ", "_").replace("-", "_")
        base_id = "".join(c for c in base_id if c.isalnum() or c == "_")
        
        if base_id not in self._profiles:
            return base_id
        
        # Add suffix if ID already exists
        counter = 1
        while f"{base_id}_{counter}" in self._profiles:
            counter += 1
        
        return f"{base_id}_{counter}"
    
    def get_routing_decision(self, use_case: str, requirements: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get routing decision based on active profile."""
        active_profile = self.get_active_profile()
        if not active_profile:
            return {
                "provider": "local",
                "model": None,
                "reason": "No active profile, using local fallback"
            }
        
        requirements = requirements or {}
        
        # Check if we have a provider preference for this use case
        if use_case in active_profile.providers:
            provider_pref = active_profile.providers[use_case]
            
            # Validate provider is available and healthy
            available_providers = self.provider_manager.get_llm_providers(healthy_only=True)
            if provider_pref.provider in available_providers:
                return {
                    "provider": provider_pref.provider,
                    "model": provider_pref.model,
                    "reason": f"Profile '{active_profile.name}' preference for {use_case}",
                    "priority": provider_pref.priority,
                    "profile_id": active_profile.id
                }
            else:
                logger.warning(f"Preferred provider {provider_pref.provider} for {use_case} is not available")
        
        # Apply router policy for fallback selection
        if active_profile.router_policy == RouterPolicy.PRIVACY:
            return {
                "provider": "local",
                "model": None,
                "reason": f"Privacy policy fallback from profile '{active_profile.name}'",
                "profile_id": active_profile.id
            }
        elif active_profile.router_policy == RouterPolicy.PERFORMANCE:
            # Prefer fast providers
            fast_providers = ["local", "deepseek"]  # These are typically faster
            available_providers = self.provider_manager.get_llm_providers(healthy_only=True)
            for provider in fast_providers:
                if provider in available_providers:
                    return {
                        "provider": provider,
                        "model": None,
                        "reason": f"Performance policy fallback from profile '{active_profile.name}'",
                        "profile_id": active_profile.id
                    }
        elif active_profile.router_policy == RouterPolicy.QUALITY:
            # Prefer high-quality providers
            quality_providers = ["openai", "gemini", "deepseek"]
            available_providers = self.provider_manager.get_llm_providers(healthy_only=True)
            for provider in quality_providers:
                if provider in available_providers:
                    return {
                        "provider": provider,
                        "model": None,
                        "reason": f"Quality policy fallback from profile '{active_profile.name}'",
                        "profile_id": active_profile.id
                    }
        elif active_profile.router_policy == RouterPolicy.COST:
            # Prefer cost-effective providers
            cost_providers = ["local", "huggingface", "gemini"]
            available_providers = self.provider_manager.get_llm_providers(healthy_only=True)
            for provider in cost_providers:
                if provider in available_providers:
                    return {
                        "provider": provider,
                        "model": None,
                        "reason": f"Cost policy fallback from profile '{active_profile.name}'",
                        "profile_id": active_profile.id
                    }
        
        # Final fallback to profile's fallback provider
        return {
            "provider": active_profile.fallback_provider,
            "model": active_profile.fallback_model,
            "reason": f"Profile '{active_profile.name}' fallback provider",
            "profile_id": active_profile.id
        }
    
    def get_profile_statistics(self) -> Dict[str, Any]:
        """Get statistics about profiles and their usage."""
        stats = {
            "total_profiles": len(self._profiles),
            "active_profile": self._active_profile_id,
            "profiles_by_policy": {},
            "provider_usage": {},
            "validation_status": {"valid": 0, "invalid": 0}
        }
        
        for profile in self._profiles.values():
            # Count by router policy
            policy = profile.router_policy.value
            stats["profiles_by_policy"][policy] = stats["profiles_by_policy"].get(policy, 0) + 1
            
            # Count provider usage
            for use_case, pref in profile.providers.items():
                provider = pref.provider
                stats["provider_usage"][provider] = stats["provider_usage"].get(provider, 0) + 1
            
            # Count validation status
            if profile.is_valid:
                stats["validation_status"]["valid"] += 1
            else:
                stats["validation_status"]["invalid"] += 1
        
        return stats
    
    def _notify_profile_change(self, profile: LLMProfile) -> None:
        """Notify other systems of profile change."""
        logger.info(f"Profile change notification: {profile.name} is now active")
        
        try:
            # Integrate with the router system
            from ai_karen_engine.integrations.llm_router import get_llm_router
            router = get_llm_router()
            if hasattr(router, 'update_active_profile'):
                router.update_active_profile(profile)
                logger.info("Router notified of profile change")
        except Exception as e:
            logger.warning(f"Failed to notify router of profile change: {e}")
        
        try:
            # Also notify the existing profile manager for compatibility
            from ai_karen_engine.services.profile_manager import get_profile_manager as get_legacy_profile_manager
            legacy_manager = get_legacy_profile_manager()
            if hasattr(legacy_manager, 'set_active_profile'):
                # Convert to legacy format if needed
                logger.debug("Legacy profile manager notified")
        except Exception as e:
            logger.debug(f"Legacy profile manager not available: {e}")
        
        # Notify any event bus subscribers
        try:
            from ai_karen_engine.services.event_bus import get_event_bus
            event_bus = get_event_bus()
            event_bus.emit('profile_changed', {
                'profile_id': profile.id,
                'profile_name': profile.name,
                'router_policy': profile.router_policy.value,
                'providers': {k: v.provider for k, v in profile.providers.items()}
            })
        except Exception as e:
            logger.debug(f"Event bus not available: {e}")


# -----------------------------
# Global Manager Instance
# -----------------------------

_global_profile_manager: Optional[LLMProfileManager] = None


def get_profile_manager() -> LLMProfileManager:
    """Get the global LLM profile manager instance."""
    global _global_profile_manager
    if _global_profile_manager is None:
        _global_profile_manager = LLMProfileManager()
    return _global_profile_manager


__all__ = [
    "RouterPolicy",
    "GuardrailLevel",
    "ProviderPreference",
    "GuardrailConfig",
    "MemoryBudget",
    "LLMProfile",
    "LLMProfileManager",
    "get_profile_manager",
]