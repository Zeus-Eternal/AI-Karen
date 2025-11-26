"""
LLM Profile Management Service

Manages LLM profiles with router policies, guardrails, memory budgets, and provider preferences.
Replaces mock examples with real working profile logic.
"""

import json
import logging
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from ai_karen_engine.integrations.registry import get_registry

logger = logging.getLogger("kari.profile_manager")


@dataclass
class RouterPolicy:
    """Router policy configuration for model selection."""
    privacy_level: str = "standard"  # low, standard, high
    performance_preference: str = "balanced"  # speed, balanced, quality
    cost_preference: str = "balanced"  # low, balanced, high
    context_awareness: bool = True
    fallback_strategy: str = "graceful"  # strict, graceful, aggressive


@dataclass
class Guardrails:
    """Guardrails configuration for content filtering and safety."""
    content_filtering: bool = True
    pii_detection: bool = True
    toxicity_filtering: bool = True
    code_execution_safety: bool = True
    max_tokens_per_request: int = 4096
    rate_limit_per_minute: int = 60
    allowed_capabilities: Set[str] = field(default_factory=lambda: {"text", "code", "reasoning"})


@dataclass
class MemoryBudget:
    """Memory budget configuration for model resource management."""
    max_context_length: int = 8192
    max_concurrent_requests: int = 5
    memory_limit_mb: int = 2048
    gpu_memory_fraction: float = 0.8
    enable_kv_cache: bool = True
    cache_size_mb: int = 512


@dataclass
class ProviderPreferences:
    """Provider preferences for different task types."""
    chat: str = "openai"
    code: str = "deepseek"
    reasoning: str = "openai"
    embedding: str = "openai"
    vision: str = "gemini"
    local_fallback: str = "local"
    privacy_tasks: str = "local"


@dataclass
class LLMProfile:
    """Complete LLM profile configuration."""
    name: str
    description: str = ""
    router_policy: RouterPolicy = field(default_factory=RouterPolicy)
    guardrails: Guardrails = field(default_factory=Guardrails)
    memory_budget: MemoryBudget = field(default_factory=MemoryBudget)
    provider_preferences: ProviderPreferences = field(default_factory=ProviderPreferences)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    is_active: bool = False
    is_system: bool = False  # System profiles cannot be deleted


class ProfileManager:
    """Manages LLM profiles with validation and compatibility checking."""
    
    def __init__(self, profiles_path: Optional[Path] = None):
        """
        Initialize profile manager.
        
        Args:
            profiles_path: Path to profiles JSON file
        """
        self.profiles_path = profiles_path or Path("config/llm_profiles.json")
        self._profiles: Dict[str, LLMProfile] = {}
        self._active_profile: Optional[str] = None
        self._registry = get_registry()
        
        # Ensure config directory exists
        self.profiles_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing profiles or create defaults
        self._load_profiles()
        
        # Ensure we have an active profile
        if not self._active_profile:
            self._set_default_active_profile()
    
    def _load_profiles(self) -> None:
        """Load profiles from JSON file."""
        if self.profiles_path.exists():
            try:
                with open(self.profiles_path, 'r') as f:
                    data = json.load(f)
                
                # Load profiles
                for profile_data in data.get("profiles", []):
                    profile = self._deserialize_profile(profile_data)
                    if profile:
                        self._profiles[profile.name] = profile
                
                # Load active profile
                self._active_profile = data.get("active_profile")
                
                logger.info(f"Loaded {len(self._profiles)} profiles from {self.profiles_path}")
                
            except Exception as e:
                logger.error(f"Failed to load profiles from {self.profiles_path}: {e}")
                self._create_default_profiles()
        else:
            self._create_default_profiles()
    
    def _save_profiles(self) -> None:
        """Save profiles to JSON file."""
        try:
            data = {
                "active_profile": self._active_profile,
                "profiles": [self._serialize_profile(profile) for profile in self._profiles.values()]
            }
            
            with open(self.profiles_path, 'w') as f:
                json.dump(data, f, indent=2)
                
            logger.info(f"Saved {len(self._profiles)} profiles to {self.profiles_path}")
            
        except Exception as e:
            logger.error(f"Failed to save profiles to {self.profiles_path}: {e}")
    
    def _serialize_profile(self, profile: LLMProfile) -> Dict[str, Any]:
        """Serialize profile to dictionary."""
        return {
            "name": profile.name,
            "description": profile.description,
            "router_policy": asdict(profile.router_policy),
            "guardrails": {
                **asdict(profile.guardrails),
                "allowed_capabilities": list(profile.guardrails.allowed_capabilities)
            },
            "memory_budget": asdict(profile.memory_budget),
            "provider_preferences": asdict(profile.provider_preferences),
            "created_at": profile.created_at,
            "updated_at": profile.updated_at,
            "is_active": profile.is_active,
            "is_system": profile.is_system
        }
    
    def _deserialize_profile(self, data: Dict[str, Any]) -> Optional[LLMProfile]:
        """Deserialize profile from dictionary."""
        try:
            # Handle guardrails allowed_capabilities set conversion
            guardrails_data = data.get("guardrails", {})
            if "allowed_capabilities" in guardrails_data:
                guardrails_data["allowed_capabilities"] = set(guardrails_data["allowed_capabilities"])
            
            profile = LLMProfile(
                name=data["name"],
                description=data.get("description", ""),
                router_policy=RouterPolicy(**data.get("router_policy", {})),
                guardrails=Guardrails(**guardrails_data),
                memory_budget=MemoryBudget(**data.get("memory_budget", {})),
                provider_preferences=ProviderPreferences(**data.get("provider_preferences", {})),
                created_at=data.get("created_at", time.time()),
                updated_at=data.get("updated_at", time.time()),
                is_active=data.get("is_active", False),
                is_system=data.get("is_system", False)
            )
            
            return profile
            
        except Exception as e:
            logger.error(f"Failed to deserialize profile {data.get('name', 'unknown')}: {e}")
            return None
    
    def _create_default_profiles(self) -> None:
        """Create default system profiles."""
        # Default balanced profile
        default_profile = LLMProfile(
            name="default",
            description="Balanced profile for general use with good performance and privacy",
            router_policy=RouterPolicy(
                privacy_level="standard",
                performance_preference="balanced",
                cost_preference="balanced"
            ),
            provider_preferences=ProviderPreferences(
                chat="openai",
                code="deepseek", 
                reasoning="openai",
                embedding="openai",
                vision="gemini",
                local_fallback="local",
                privacy_tasks="local"
            ),
            is_system=True
        )
        
        # Privacy-focused profile
        privacy_profile = LLMProfile(
            name="privacy",
            description="Privacy-focused profile using local models when possible",
            router_policy=RouterPolicy(
                privacy_level="high",
                performance_preference="balanced",
                cost_preference="low"
            ),
            provider_preferences=ProviderPreferences(
                chat="local",
                code="local",
                reasoning="local", 
                embedding="local",
                vision="local",
                local_fallback="local",
                privacy_tasks="local"
            ),
            is_system=True
        )
        
        # Performance profile
        performance_profile = LLMProfile(
            name="performance",
            description="High-performance profile optimized for speed and quality",
            router_policy=RouterPolicy(
                privacy_level="low",
                performance_preference="quality",
                cost_preference="high"
            ),
            memory_budget=MemoryBudget(
                max_context_length=16384,
                max_concurrent_requests=10,
                memory_limit_mb=4096
            ),
            provider_preferences=ProviderPreferences(
                chat="openai",
                code="deepseek",
                reasoning="openai",
                embedding="openai", 
                vision="gemini",
                local_fallback="openai",
                privacy_tasks="openai"
            ),
            is_system=True
        )
        
        # Cost-optimized profile
        cost_profile = LLMProfile(
            name="cost-optimized",
            description="Cost-optimized profile using efficient models and local execution",
            router_policy=RouterPolicy(
                privacy_level="standard",
                performance_preference="speed",
                cost_preference="low"
            ),
            guardrails=Guardrails(
                max_tokens_per_request=2048,
                rate_limit_per_minute=30
            ),
            memory_budget=MemoryBudget(
                max_context_length=4096,
                memory_limit_mb=1024
            ),
            provider_preferences=ProviderPreferences(
                chat="local",
                code="local",
                reasoning="local",
                embedding="huggingface",
                vision="local",
                local_fallback="local",
                privacy_tasks="local"
            ),
            is_system=True
        )
        
        # Add profiles
        self._profiles = {
            "default": default_profile,
            "privacy": privacy_profile,
            "performance": performance_profile,
            "cost-optimized": cost_profile
        }
        
        # Set default as active
        self._active_profile = "default"
        default_profile.is_active = True
        
        # Save to file
        self._save_profiles()
        
        logger.info("Created default system profiles")
    
    def _set_default_active_profile(self) -> None:
        """Set a default active profile if none is set."""
        if self._profiles:
            # Prefer 'default' profile, otherwise use first available
            if "default" in self._profiles:
                self._active_profile = "default"
                self._profiles["default"].is_active = True
            else:
                first_profile = next(iter(self._profiles.keys()))
                self._active_profile = first_profile
                self._profiles[first_profile].is_active = True
            
            self._save_profiles()
    
    def list_profiles(self) -> List[LLMProfile]:
        """Get list of all profiles."""
        return list(self._profiles.values())
    
    def get_profile(self, name: str) -> Optional[LLMProfile]:
        """Get profile by name."""
        return self._profiles.get(name)
    
    def get_active_profile(self) -> Optional[LLMProfile]:
        """Get currently active profile."""
        if self._active_profile:
            return self._profiles.get(self._active_profile)
        return None
    
    def create_profile(self, profile: LLMProfile) -> bool:
        """
        Create a new profile.
        
        Args:
            profile: Profile to create
            
        Returns:
            True if created successfully, False if name already exists
        """
        if profile.name in self._profiles:
            return False
        
        profile.created_at = time.time()
        profile.updated_at = time.time()
        self._profiles[profile.name] = profile
        self._save_profiles()
        
        logger.info(f"Created profile: {profile.name}")
        return True
    
    def update_profile(self, name: str, updates: Dict[str, Any]) -> bool:
        """
        Update an existing profile.
        
        Args:
            name: Profile name
            updates: Dictionary of updates to apply
            
        Returns:
            True if updated successfully, False if profile not found
        """
        if name not in self._profiles:
            return False
        
        profile = self._profiles[name]
        
        # Apply updates
        for key, value in updates.items():
            if hasattr(profile, key):
                if key in ["router_policy", "guardrails", "memory_budget", "provider_preferences"]:
                    # Handle nested object updates
                    current_obj = getattr(profile, key)
                    if isinstance(value, dict):
                        for sub_key, sub_value in value.items():
                            if hasattr(current_obj, sub_key):
                                setattr(current_obj, sub_key, sub_value)
                else:
                    setattr(profile, key, value)
        
        profile.updated_at = time.time()
        self._save_profiles()
        
        logger.info(f"Updated profile: {name}")
        return True
    
    def delete_profile(self, name: str) -> bool:
        """
        Delete a profile.
        
        Args:
            name: Profile name
            
        Returns:
            True if deleted successfully, False if not found or is system profile
        """
        if name not in self._profiles:
            return False
        
        profile = self._profiles[name]
        if profile.is_system:
            logger.warning(f"Cannot delete system profile: {name}")
            return False
        
        # If deleting active profile, switch to default
        if self._active_profile == name:
            self.switch_profile("default")
        
        del self._profiles[name]
        self._save_profiles()
        
        logger.info(f"Deleted profile: {name}")
        return True
    
    def switch_profile(self, name: str) -> bool:
        """
        Switch to a different profile.
        
        Args:
            name: Profile name to switch to
            
        Returns:
            True if switched successfully, False if profile not found
        """
        if name not in self._profiles:
            return False
        
        # Deactivate current profile
        if self._active_profile and self._active_profile in self._profiles:
            self._profiles[self._active_profile].is_active = False
        
        # Activate new profile
        self._active_profile = name
        self._profiles[name].is_active = True
        
        self._save_profiles()
        
        logger.info(f"Switched to profile: {name}")
        return True
    
    def validate_profile(self, profile: LLMProfile) -> Dict[str, List[str]]:
        """
        Validate profile configuration against available providers.
        
        Args:
            profile: Profile to validate
            
        Returns:
            Dictionary with validation errors by category
        """
        errors = {
            "providers": [],
            "capabilities": [],
            "resources": [],
            "configuration": []
        }
        
        # Validate provider preferences
        available_providers = self._registry.list_llm_providers()
        
        for task, provider in asdict(profile.provider_preferences).items():
            if provider not in available_providers:
                errors["providers"].append(f"Provider '{provider}' for task '{task}' is not available")
            else:
                # Check if provider supports required capabilities
                spec = self._registry.get_provider_spec(provider)
                if spec:
                    task_capabilities = {
                        "chat": {"streaming"},
                        "code": {"function_calling"},
                        "vision": {"vision"},
                        "embedding": {"embeddings"}
                    }
                    
                    required_caps = task_capabilities.get(task, set())
                    if not required_caps.issubset(spec.capabilities):
                        missing = required_caps - spec.capabilities
                        errors["capabilities"].append(
                            f"Provider '{provider}' for task '{task}' missing capabilities: {missing}"
                        )
        
        # Validate memory budget
        if profile.memory_budget.max_context_length > 100000:
            errors["resources"].append("Max context length is very high and may cause memory issues")
        
        if profile.memory_budget.memory_limit_mb < 512:
            errors["resources"].append("Memory limit is very low and may cause performance issues")
        
        # Validate guardrails
        if profile.guardrails.max_tokens_per_request > profile.memory_budget.max_context_length:
            errors["configuration"].append("Max tokens per request exceeds max context length")
        
        if profile.guardrails.rate_limit_per_minute > 1000:
            errors["configuration"].append("Rate limit is very high and may cause API issues")
        
        return errors
    
    def get_routing_decision(self, task_type: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get routing decision based on active profile and context.
        
        Args:
            task_type: Type of task (chat, code, reasoning, etc.)
            context: Optional context information
            
        Returns:
            Routing decision with provider, reasoning, and metadata
        """
        active_profile = self.get_active_profile()
        if not active_profile:
            return {
                "provider": "openai",
                "reason": "No active profile, using default",
                "confidence": 0.5
            }
        
        context = context or {}
        
        # Get preferred provider for task type
        provider_prefs = active_profile.provider_preferences
        preferred_provider = getattr(provider_prefs, task_type, "openai")
        
        # Apply router policy
        policy = active_profile.router_policy
        
        # Privacy considerations
        if policy.privacy_level == "high" or context.get("contains_pii", False):
            preferred_provider = provider_prefs.privacy_tasks
            reason = "High privacy requirements"
        elif policy.privacy_level == "low" and context.get("performance_critical", False):
            # Use best performance provider
            if task_type == "code":
                preferred_provider = "deepseek"
            else:
                preferred_provider = "openai"
            reason = "Performance optimization"
        else:
            reason = f"Profile preference for {task_type}"
        
        # Check provider availability
        available_providers = self._registry.get_healthy_providers("LLM")
        if preferred_provider not in available_providers:
            # Fallback logic
            if policy.fallback_strategy == "graceful":
                preferred_provider = provider_prefs.local_fallback
                reason = f"Fallback to {preferred_provider} (original provider unavailable)"
            elif policy.fallback_strategy == "aggressive":
                preferred_provider = available_providers[0] if available_providers else "local"
                reason = f"Aggressive fallback to {preferred_provider}"
        
        # Calculate confidence based on various factors
        confidence = 0.8
        if preferred_provider not in available_providers:
            confidence -= 0.3
        if context.get("complex_task", False):
            confidence += 0.1
        
        return {
            "provider": preferred_provider,
            "reason": reason,
            "confidence": max(0.1, min(1.0, confidence)),
            "policy": policy.performance_preference,
            "privacy_level": policy.privacy_level,
            "fallback_used": preferred_provider == provider_prefs.local_fallback
        }


# Global profile manager instance
_profile_manager: Optional[ProfileManager] = None


def get_profile_manager() -> ProfileManager:
    """Get global profile manager instance."""
    global _profile_manager
    if _profile_manager is None:
        _profile_manager = ProfileManager()
    return _profile_manager


__all__ = [
    "RouterPolicy",
    "Guardrails", 
    "MemoryBudget",
    "ProviderPreferences",
    "LLMProfile",
    "ProfileManager",
    "get_profile_manager"
]