"""
Routing Policy Configuration System

This module provides a flexible system for defining and managing routing policies
that determine how LLM requests are routed to providers and runtimes based on
various criteria like task type, privacy level, and performance requirements.

Key Features:
- Predefined routing policies for common scenarios
- Custom policy creation and validation
- Policy inheritance and composition
- Dynamic policy updates
- Policy-based confidence scoring
"""

import json
import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from ai_karen_engine.integrations.llm_router import (
    PerformanceRequirement,
    PrivacyLevel,
    RoutingPolicy,
    TaskType,
)

logger = logging.getLogger(__name__)


@dataclass
class PolicyRule:
    """A single routing rule within a policy."""
    name: str
    description: str = ""
    conditions: Dict[str, Any] = field(default_factory=dict)
    provider_preference: Optional[str] = None
    runtime_preference: Optional[str] = None
    confidence_boost: float = 0.0
    priority: int = 50


@dataclass
class PolicyTemplate:
    """Template for creating routing policies."""
    name: str
    description: str
    base_policy: Optional[str] = None
    rules: List[PolicyRule] = field(default_factory=list)
    overrides: Dict[str, Any] = field(default_factory=dict)


class RoutingPolicyManager:
    """
    Manager for routing policies with support for templates, inheritance, and validation.
    """
    
    def __init__(self, config_dir: Optional[Path] = None):
        self.config_dir = config_dir or Path(__file__).parents[2] / "config" / "routing_policies"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.policies: Dict[str, RoutingPolicy] = {}
        self.templates: Dict[str, PolicyTemplate] = {}
        
        # Load built-in policies and templates
        self._load_builtin_policies()
        self._load_builtin_templates()
        
        # Load custom policies from config directory
        self._load_custom_policies()
    
    def _load_builtin_policies(self) -> None:
        """Load built-in routing policies."""
        
        # Privacy-First Policy
        privacy_policy = RoutingPolicy(
            name="privacy_first",
            description="Prioritizes privacy and local execution over performance",
            
            task_provider_map={
                TaskType.CHAT: "local",
                TaskType.CODE: "local", 
                TaskType.REASONING: "local",
                TaskType.EMBEDDING: "huggingface",
                TaskType.SUMMARIZATION: "local",
                TaskType.TRANSLATION: "local",
                TaskType.CREATIVE: "local",
                TaskType.ANALYSIS: "local",
            },
            
            task_runtime_map={
                TaskType.CHAT: "llama.cpp",
                TaskType.CODE: "llama.cpp",
                TaskType.REASONING: "llama.cpp", 
                TaskType.EMBEDDING: "transformers",
                TaskType.SUMMARIZATION: "llama.cpp",
                TaskType.TRANSLATION: "llama.cpp",
                TaskType.CREATIVE: "llama.cpp",
                TaskType.ANALYSIS: "llama.cpp",
            },
            
            privacy_provider_map={
                PrivacyLevel.PUBLIC: ["local", "huggingface"],
                PrivacyLevel.INTERNAL: ["local", "huggingface"],
                PrivacyLevel.CONFIDENTIAL: ["local"],
                PrivacyLevel.RESTRICTED: ["local"],
            },
            
            privacy_runtime_map={
                PrivacyLevel.PUBLIC: ["llama.cpp", "transformers", "core_helpers"],
                PrivacyLevel.INTERNAL: ["llama.cpp", "transformers", "core_helpers"],
                PrivacyLevel.CONFIDENTIAL: ["llama.cpp", "core_helpers"],
                PrivacyLevel.RESTRICTED: ["core_helpers"],
            },
            
            performance_provider_map={
                PerformanceRequirement.INTERACTIVE: "local",
                PerformanceRequirement.BATCH: "local",
                PerformanceRequirement.BACKGROUND: "local",
            },
            
            performance_runtime_map={
                PerformanceRequirement.INTERACTIVE: "llama.cpp",
                PerformanceRequirement.BATCH: "transformers",
                PerformanceRequirement.BACKGROUND: "llama.cpp",
            },
            
            fallback_providers=["local", "huggingface"],
            fallback_runtimes=["llama.cpp", "core_helpers"],
            
            privacy_weight=0.6,
            performance_weight=0.2,
            cost_weight=0.1,
            availability_weight=0.1,
        )
        self.policies["privacy_first"] = privacy_policy
        
        # Performance-First Policy
        performance_policy = RoutingPolicy(
            name="performance_first",
            description="Prioritizes performance and speed over privacy and cost",
            
            task_provider_map={
                TaskType.CHAT: "openai",
                TaskType.CODE: "deepseek", 
                TaskType.REASONING: "gemini",
                TaskType.EMBEDDING: "openai",
                TaskType.SUMMARIZATION: "openai",
                TaskType.TRANSLATION: "gemini",
                TaskType.CREATIVE: "openai",
                TaskType.ANALYSIS: "gemini",
            },
            
            task_runtime_map={
                TaskType.CHAT: "vllm",
                TaskType.CODE: "vllm",
                TaskType.REASONING: "vllm", 
                TaskType.EMBEDDING: "vllm",
                TaskType.SUMMARIZATION: "vllm",
                TaskType.TRANSLATION: "vllm",
                TaskType.CREATIVE: "vllm",
                TaskType.ANALYSIS: "vllm",
            },
            
            privacy_provider_map={
                PrivacyLevel.PUBLIC: ["openai", "gemini", "deepseek", "huggingface", "local"],
                PrivacyLevel.INTERNAL: ["huggingface", "local"],
                PrivacyLevel.CONFIDENTIAL: ["local"],
                PrivacyLevel.RESTRICTED: ["local"],
            },
            
            privacy_runtime_map={
                PrivacyLevel.PUBLIC: ["vllm", "transformers", "llama.cpp", "core_helpers"],
                PrivacyLevel.INTERNAL: ["vllm", "transformers", "llama.cpp", "core_helpers"],
                PrivacyLevel.CONFIDENTIAL: ["llama.cpp", "core_helpers"],
                PrivacyLevel.RESTRICTED: ["core_helpers"],
            },
            
            performance_provider_map={
                PerformanceRequirement.INTERACTIVE: "openai",
                PerformanceRequirement.BATCH: "local",
                PerformanceRequirement.BACKGROUND: "local",
            },
            
            performance_runtime_map={
                PerformanceRequirement.INTERACTIVE: "vllm",
                PerformanceRequirement.BATCH: "vllm",
                PerformanceRequirement.BACKGROUND: "transformers",
            },
            
            fallback_providers=["local", "huggingface"],
            fallback_runtimes=["vllm", "transformers", "llama.cpp"],
            
            privacy_weight=0.1,
            performance_weight=0.6,
            cost_weight=0.2,
            availability_weight=0.1,
        )
        self.policies["performance_first"] = performance_policy
        
        # Cost-Optimized Policy
        cost_policy = RoutingPolicy(
            name="cost_optimized",
            description="Prioritizes cost efficiency while maintaining reasonable performance",
            
            task_provider_map={
                TaskType.CHAT: "local",
                TaskType.CODE: "deepseek", 
                TaskType.REASONING: "local",
                TaskType.EMBEDDING: "huggingface",
                TaskType.SUMMARIZATION: "local",
                TaskType.TRANSLATION: "local",
                TaskType.CREATIVE: "deepseek",
                TaskType.ANALYSIS: "local",
            },
            
            task_runtime_map={
                TaskType.CHAT: "llama.cpp",
                TaskType.CODE: "transformers",
                TaskType.REASONING: "transformers", 
                TaskType.EMBEDDING: "transformers",
                TaskType.SUMMARIZATION: "llama.cpp",
                TaskType.TRANSLATION: "transformers",
                TaskType.CREATIVE: "transformers",
                TaskType.ANALYSIS: "transformers",
            },
            
            privacy_provider_map={
                PrivacyLevel.PUBLIC: ["local", "deepseek", "huggingface", "gemini", "openai"],
                PrivacyLevel.INTERNAL: ["local", "huggingface"],
                PrivacyLevel.CONFIDENTIAL: ["local"],
                PrivacyLevel.RESTRICTED: ["local"],
            },
            
            privacy_runtime_map={
                PrivacyLevel.PUBLIC: ["llama.cpp", "transformers", "vllm", "core_helpers"],
                PrivacyLevel.INTERNAL: ["llama.cpp", "transformers", "core_helpers"],
                PrivacyLevel.CONFIDENTIAL: ["llama.cpp", "core_helpers"],
                PrivacyLevel.RESTRICTED: ["core_helpers"],
            },
            
            performance_provider_map={
                PerformanceRequirement.INTERACTIVE: "deepseek",
                PerformanceRequirement.BATCH: "local",
                PerformanceRequirement.BACKGROUND: "local",
            },
            
            performance_runtime_map={
                PerformanceRequirement.INTERACTIVE: "transformers",
                PerformanceRequirement.BATCH: "transformers",
                PerformanceRequirement.BACKGROUND: "llama.cpp",
            },
            
            fallback_providers=["local", "huggingface"],
            fallback_runtimes=["llama.cpp", "transformers"],
            
            privacy_weight=0.2,
            performance_weight=0.2,
            cost_weight=0.5,
            availability_weight=0.1,
        )
        self.policies["cost_optimized"] = cost_policy
        
        # Balanced Policy (default)
        balanced_policy = RoutingPolicy(
            name="balanced",
            description="Balanced approach considering all factors equally",
            
            task_provider_map={
                TaskType.CHAT: "openai",
                TaskType.CODE: "deepseek", 
                TaskType.REASONING: "gemini",
                TaskType.EMBEDDING: "huggingface",
                TaskType.SUMMARIZATION: "local",
                TaskType.TRANSLATION: "gemini",
                TaskType.CREATIVE: "openai",
                TaskType.ANALYSIS: "gemini",
            },
            
            task_runtime_map={
                TaskType.CHAT: "vllm",
                TaskType.CODE: "transformers",
                TaskType.REASONING: "vllm", 
                TaskType.EMBEDDING: "transformers",
                TaskType.SUMMARIZATION: "llama.cpp",
                TaskType.TRANSLATION: "transformers",
                TaskType.CREATIVE: "vllm",
                TaskType.ANALYSIS: "transformers",
            },
            
            privacy_provider_map={
                PrivacyLevel.PUBLIC: ["openai", "gemini", "deepseek", "huggingface", "local"],
                PrivacyLevel.INTERNAL: ["huggingface", "local"],
                PrivacyLevel.CONFIDENTIAL: ["local"],
                PrivacyLevel.RESTRICTED: ["local"],
            },
            
            privacy_runtime_map={
                PrivacyLevel.PUBLIC: ["vllm", "transformers", "llama.cpp", "core_helpers"],
                PrivacyLevel.INTERNAL: ["transformers", "llama.cpp", "core_helpers"],
                PrivacyLevel.CONFIDENTIAL: ["llama.cpp", "core_helpers"],
                PrivacyLevel.RESTRICTED: ["core_helpers"],
            },
            
            performance_provider_map={
                PerformanceRequirement.INTERACTIVE: "openai",
                PerformanceRequirement.BATCH: "local",
                PerformanceRequirement.BACKGROUND: "local",
            },
            
            performance_runtime_map={
                PerformanceRequirement.INTERACTIVE: "vllm",
                PerformanceRequirement.BATCH: "transformers",
                PerformanceRequirement.BACKGROUND: "llama.cpp",
            },
            
            fallback_providers=["local", "huggingface"],
            fallback_runtimes=["llama.cpp", "core_helpers"],
            
            privacy_weight=0.25,
            performance_weight=0.25,
            cost_weight=0.25,
            availability_weight=0.25,
        )
        self.policies["balanced"] = balanced_policy
        self.policies["default"] = balanced_policy  # Alias
    
    def _load_builtin_templates(self) -> None:
        """Load built-in policy templates."""
        
        # Enterprise Template
        enterprise_template = PolicyTemplate(
            name="enterprise",
            description="Template for enterprise deployments with strict privacy requirements",
            base_policy="privacy_first",
            rules=[
                PolicyRule(
                    name="confidential_data",
                    description="Route confidential data to local models only",
                    conditions={"privacy_level": "confidential"},
                    provider_preference="local",
                    runtime_preference="llama.cpp",
                    confidence_boost=0.3,
                    priority=90,
                ),
                PolicyRule(
                    name="code_review",
                    description="Use specialized code models for code review tasks",
                    conditions={"task_type": "code", "metadata.code_review": True},
                    provider_preference="deepseek",
                    runtime_preference="transformers",
                    confidence_boost=0.2,
                    priority=80,
                ),
            ],
            overrides={
                "privacy_weight": 0.7,
                "performance_weight": 0.2,
                "cost_weight": 0.05,
                "availability_weight": 0.05,
            }
        )
        self.templates["enterprise"] = enterprise_template
        
        # Development Template
        dev_template = PolicyTemplate(
            name="development",
            description="Template for development environments prioritizing speed and flexibility",
            base_policy="performance_first",
            rules=[
                PolicyRule(
                    name="debug_mode",
                    description="Use local models for debugging to avoid API costs",
                    conditions={"metadata.debug": True},
                    provider_preference="local",
                    runtime_preference="llama.cpp",
                    confidence_boost=0.1,
                    priority=70,
                ),
                PolicyRule(
                    name="testing",
                    description="Use fast models for testing scenarios",
                    conditions={"metadata.testing": True},
                    provider_preference="openai",
                    runtime_preference="vllm",
                    confidence_boost=0.2,
                    priority=75,
                ),
            ],
            overrides={
                "privacy_weight": 0.1,
                "performance_weight": 0.5,
                "cost_weight": 0.3,
                "availability_weight": 0.1,
            }
        )
        self.templates["development"] = dev_template
    
    def _load_custom_policies(self) -> None:
        """Load custom policies from configuration files."""
        try:
            for policy_file in self.config_dir.glob("*.json"):
                try:
                    with open(policy_file, 'r') as f:
                        policy_data = json.load(f)
                    
                    if "name" not in policy_data:
                        policy_data["name"] = policy_file.stem
                    
                    policy = self._create_policy_from_dict(policy_data)
                    self.policies[policy.name] = policy
                    logger.info(f"Loaded custom policy: {policy.name}")
                    
                except Exception as e:
                    logger.error(f"Failed to load policy from {policy_file}: {e}")
                    
        except Exception as e:
            logger.error(f"Failed to load custom policies: {e}")
    
    def _create_policy_from_dict(self, data: Dict[str, Any]) -> RoutingPolicy:
        """Create a RoutingPolicy from dictionary data."""
        # Convert string enums to actual enum values
        task_provider_map = {}
        for task_str, provider in data.get("task_provider_map", {}).items():
            try:
                task_type = TaskType(task_str)
                task_provider_map[task_type] = provider
            except ValueError:
                logger.warning(f"Unknown task type: {task_str}")
        
        task_runtime_map = {}
        for task_str, runtime in data.get("task_runtime_map", {}).items():
            try:
                task_type = TaskType(task_str)
                task_runtime_map[task_type] = runtime
            except ValueError:
                logger.warning(f"Unknown task type: {task_str}")
        
        privacy_provider_map = {}
        for privacy_str, providers in data.get("privacy_provider_map", {}).items():
            try:
                privacy_level = PrivacyLevel(privacy_str)
                privacy_provider_map[privacy_level] = providers
            except ValueError:
                logger.warning(f"Unknown privacy level: {privacy_str}")
        
        privacy_runtime_map = {}
        for privacy_str, runtimes in data.get("privacy_runtime_map", {}).items():
            try:
                privacy_level = PrivacyLevel(privacy_str)
                privacy_runtime_map[privacy_level] = runtimes
            except ValueError:
                logger.warning(f"Unknown privacy level: {privacy_str}")
        
        performance_provider_map = {}
        for perf_str, provider in data.get("performance_provider_map", {}).items():
            try:
                perf_req = PerformanceRequirement(perf_str)
                performance_provider_map[perf_req] = provider
            except ValueError:
                logger.warning(f"Unknown performance requirement: {perf_str}")
        
        performance_runtime_map = {}
        for perf_str, runtime in data.get("performance_runtime_map", {}).items():
            try:
                perf_req = PerformanceRequirement(perf_str)
                performance_runtime_map[perf_req] = runtime
            except ValueError:
                logger.warning(f"Unknown performance requirement: {perf_str}")
        
        return RoutingPolicy(
            name=data["name"],
            description=data.get("description", ""),
            task_provider_map=task_provider_map,
            task_runtime_map=task_runtime_map,
            privacy_provider_map=privacy_provider_map,
            privacy_runtime_map=privacy_runtime_map,
            performance_provider_map=performance_provider_map,
            performance_runtime_map=performance_runtime_map,
            fallback_providers=data.get("fallback_providers", []),
            fallback_runtimes=data.get("fallback_runtimes", []),
            privacy_weight=data.get("privacy_weight", 0.25),
            performance_weight=data.get("performance_weight", 0.25),
            cost_weight=data.get("cost_weight", 0.25),
            availability_weight=data.get("availability_weight", 0.25),
        )
    
    def get_policy(self, name: str) -> Optional[RoutingPolicy]:
        """Get a routing policy by name."""
        return self.policies.get(name)
    
    def list_policies(self) -> List[str]:
        """List all available policy names."""
        return list(self.policies.keys())
    
    def create_policy_from_template(self, template_name: str, policy_name: str, **overrides) -> RoutingPolicy:
        """Create a new policy from a template."""
        template = self.templates.get(template_name)
        if not template:
            raise ValueError(f"Template '{template_name}' not found")
        
        # Start with base policy if specified
        if template.base_policy:
            base_policy = self.get_policy(template.base_policy)
            if not base_policy:
                raise ValueError(f"Base policy '{template.base_policy}' not found")
            
            # Create a copy of the base policy
            policy_dict = asdict(base_policy)
        else:
            # Start with default policy structure
            policy_dict = asdict(self.policies["balanced"])
        
        # Apply template overrides
        policy_dict.update(template.overrides)
        
        # Apply user overrides
        policy_dict.update(overrides)
        
        # Set the new name
        policy_dict["name"] = policy_name
        
        # Create the policy
        policy = self._create_policy_from_dict(policy_dict)
        
        # Store the policy
        self.policies[policy_name] = policy
        
        return policy
    
    def save_policy(self, policy: RoutingPolicy) -> None:
        """Save a policy to the configuration directory."""
        policy_file = self.config_dir / f"{policy.name}.json"
        
        # Convert policy to serializable dict
        policy_dict = asdict(policy)
        
        # Convert enum keys to strings
        def convert_enum_keys(obj):
            if isinstance(obj, dict):
                new_dict = {}
                for key, value in obj.items():
                    if hasattr(key, 'value'):  # Enum
                        new_dict[key.value] = convert_enum_keys(value)
                    else:
                        new_dict[key] = convert_enum_keys(value)
                return new_dict
            elif isinstance(obj, list):
                return [convert_enum_keys(item) for item in obj]
            else:
                return obj
        
        policy_dict = convert_enum_keys(policy_dict)
        
        with open(policy_file, 'w') as f:
            json.dump(policy_dict, f, indent=2)
        
        logger.info(f"Saved policy '{policy.name}' to {policy_file}")
    
    def delete_policy(self, name: str) -> bool:
        """Delete a policy."""
        if name in ["default", "balanced", "privacy_first", "performance_first", "cost_optimized"]:
            raise ValueError(f"Cannot delete built-in policy '{name}'")
        
        if name not in self.policies:
            return False
        
        # Remove from memory
        del self.policies[name]
        
        # Remove file if it exists
        policy_file = self.config_dir / f"{name}.json"
        if policy_file.exists():
            policy_file.unlink()
        
        logger.info(f"Deleted policy '{name}'")
        return True
    
    def validate_policy(self, policy: RoutingPolicy) -> List[str]:
        """Validate a routing policy and return any issues."""
        issues = []
        
        # Check that all required mappings are present
        required_tasks = list(TaskType)
        required_privacy_levels = list(PrivacyLevel)
        required_performance_reqs = list(PerformanceRequirement)
        
        # Check task mappings
        missing_task_providers = [t for t in required_tasks if t not in policy.task_provider_map]
        if missing_task_providers:
            issues.append(f"Missing task provider mappings: {[t.value for t in missing_task_providers]}")
        
        missing_task_runtimes = [t for t in required_tasks if t not in policy.task_runtime_map]
        if missing_task_runtimes:
            issues.append(f"Missing task runtime mappings: {[t.value for t in missing_task_runtimes]}")
        
        # Check privacy mappings
        missing_privacy_providers = [p for p in required_privacy_levels if p not in policy.privacy_provider_map]
        if missing_privacy_providers:
            issues.append(f"Missing privacy provider mappings: {[p.value for p in missing_privacy_providers]}")
        
        missing_privacy_runtimes = [p for p in required_privacy_levels if p not in policy.privacy_runtime_map]
        if missing_privacy_runtimes:
            issues.append(f"Missing privacy runtime mappings: {[p.value for p in missing_privacy_runtimes]}")
        
        # Check performance mappings
        missing_perf_providers = [p for p in required_performance_reqs if p not in policy.performance_provider_map]
        if missing_perf_providers:
            issues.append(f"Missing performance provider mappings: {[p.value for p in missing_perf_providers]}")
        
        missing_perf_runtimes = [p for p in required_performance_reqs if p not in policy.performance_runtime_map]
        if missing_perf_runtimes:
            issues.append(f"Missing performance runtime mappings: {[p.value for p in missing_perf_runtimes]}")
        
        # Check weights sum to 1.0
        total_weight = (policy.privacy_weight + policy.performance_weight + 
                       policy.cost_weight + policy.availability_weight)
        if abs(total_weight - 1.0) > 0.01:
            issues.append(f"Policy weights sum to {total_weight}, should sum to 1.0")
        
        # Check fallback chains
        if not policy.fallback_providers:
            issues.append("No fallback providers specified")
        
        if not policy.fallback_runtimes:
            issues.append("No fallback runtimes specified")
        
        return issues
    
    def get_policy_recommendations(self, use_case: str) -> List[str]:
        """Get policy recommendations for a specific use case."""
        recommendations = []
        
        use_case_lower = use_case.lower()
        
        if any(keyword in use_case_lower for keyword in ["enterprise", "corporate", "business"]):
            recommendations.extend(["privacy_first", "enterprise"])
        
        if any(keyword in use_case_lower for keyword in ["development", "dev", "testing", "debug"]):
            recommendations.extend(["performance_first", "development"])
        
        if any(keyword in use_case_lower for keyword in ["cost", "budget", "cheap", "economical"]):
            recommendations.extend(["cost_optimized"])
        
        if any(keyword in use_case_lower for keyword in ["privacy", "confidential", "secure", "private"]):
            recommendations.extend(["privacy_first"])
        
        if any(keyword in use_case_lower for keyword in ["performance", "speed", "fast", "real-time"]):
            recommendations.extend(["performance_first"])
        
        # Always include balanced as a safe default
        if "balanced" not in recommendations:
            recommendations.append("balanced")
        
        return recommendations


# Global policy manager instance
_global_policy_manager: Optional[RoutingPolicyManager] = None


def get_policy_manager() -> RoutingPolicyManager:
    """Get the global routing policy manager."""
    global _global_policy_manager
    if _global_policy_manager is None:
        _global_policy_manager = RoutingPolicyManager()
    return _global_policy_manager


def get_routing_policy(name: str) -> Optional[RoutingPolicy]:
    """Get a routing policy by name."""
    return get_policy_manager().get_policy(name)


def list_routing_policies() -> List[str]:
    """List all available routing policies."""
    return get_policy_manager().list_policies()


__all__ = [
    "PolicyRule",
    "PolicyTemplate",
    "RoutingPolicyManager",
    "get_policy_manager",
    "get_routing_policy",
    "list_routing_policies",
]