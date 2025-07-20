"""
Operation MirrorSnap: LLM Profile Router
Context-sensitive model routing with fallback and metrics
"""

import os
import time
import json
from typing import Dict, Any, Optional, List, Tuple
from enum import Enum
from dataclasses import dataclass
import requests


class LLMProfile(Enum):
    """LLM execution profiles for different use cases"""
    FAST_LOCAL = "fast_local"          # Speed-optimized local models
    PRECISE = "precise"                # Accuracy-focused models
    CREATIVE = "creative"              # Creative/generative tasks
    ANALYTICAL = "analytical"          # Data analysis and reasoning
    CONVERSATIONAL = "conversational"  # Chat and dialogue
    TECHNICAL = "technical"            # Code and technical tasks


@dataclass
class ModelConfig:
    """Configuration for a specific model"""
    name: str
    profile: LLMProfile
    max_tokens: int
    temperature: float
    capabilities: List[str]
    priority: int  # Lower = higher priority
    fallback_model: Optional[str] = None


@dataclass
class RoutingDecision:
    """Result of model routing decision"""
    selected_model: str
    profile_used: LLMProfile
    reasoning: str
    fallback_used: bool
    routing_time: float
    confidence: float


class LLMProfileRouter:
    """
    Operation MirrorSnap: Intelligent LLM Router
    Routes requests to optimal models based on context, task, and user preferences
    """
    
    def __init__(self):
        self.api_url = os.getenv("KARI_API_URL", "http://localhost:8001")
        self.session = requests.Session()
        
        # Model configurations
        self.model_configs = {
            "distilbert-base-uncased": ModelConfig(
                name="distilbert-base-uncased",
                profile=LLMProfile.FAST_LOCAL,
                max_tokens=512,
                temperature=0.3,
                capabilities=["classification", "sentiment", "fast_inference"],
                priority=1
            ),
            "sentence-transformers/all-MiniLM-L6-v2": ModelConfig(
                name="sentence-transformers/all-MiniLM-L6-v2",
                profile=LLMProfile.ANALYTICAL,
                max_tokens=256,
                temperature=0.1,
                capabilities=["embeddings", "similarity", "search"],
                priority=2
            ),
            "default": ModelConfig(
                name="default",
                profile=LLMProfile.CONVERSATIONAL,
                max_tokens=2048,
                temperature=0.7,
                capabilities=["chat", "general", "conversation"],
                priority=3
            )
        }
        
        # Routing metrics
        self.metrics = {
            "routing_decisions": 0,
            "fallback_uses": 0,
            "profile_usage": {profile.value: 0 for profile in LLMProfile},
            "model_usage": {},
            "routing_latency": [],
            "success_rate": 0.0
        }
        
        # Context-to-profile mapping
        self.context_profiles = {
            "code": LLMProfile.TECHNICAL,
            "analysis": LLMProfile.ANALYTICAL,
            "creative": LLMProfile.CREATIVE,
            "chat": LLMProfile.CONVERSATIONAL,
            "classification": LLMProfile.FAST_LOCAL,
            "search": LLMProfile.ANALYTICAL
        }
    
    def route_request(self, prompt: str, context: Dict[str, Any], 
                     user_preferences: Optional[Dict[str, Any]] = None) -> RoutingDecision:
        """
        Route LLM request to optimal model based on context and preferences
        """
        start_time = time.time()
        
        # Determine optimal profile
        profile = self._determine_profile(prompt, context, user_preferences)
        
        # Select model for profile
        selected_model, fallback_used = self._select_model_for_profile(profile, context)
        
        # Calculate confidence
        confidence = self._calculate_routing_confidence(prompt, context, selected_model)
        
        routing_time = time.time() - start_time
        
        # Create routing decision
        decision = RoutingDecision(
            selected_model=selected_model,
            profile_used=profile,
            reasoning=self._generate_routing_reasoning(profile, selected_model, context),
            fallback_used=fallback_used,
            routing_time=routing_time,
            confidence=confidence
        )
        
        # Update metrics
        self._update_metrics(decision)
        
        return decision
    
    def _determine_profile(self, prompt: str, context: Dict[str, Any], 
                          user_preferences: Optional[Dict[str, Any]]) -> LLMProfile:
        """Determine optimal LLM profile based on context analysis"""
        
        # User preference override
        if user_preferences and "preferred_profile" in user_preferences:
            try:
                return LLMProfile(user_preferences["preferred_profile"])
            except ValueError:
                pass
        
        # Context-based routing
        task_type = context.get("task_type", "").lower()
        if task_type in self.context_profiles:
            return self.context_profiles[task_type]
        
        # Content analysis
        prompt_lower = prompt.lower()
        
        # Technical content detection
        if any(keyword in prompt_lower for keyword in ["code", "function", "class", "import", "def", "var"]):
            return LLMProfile.TECHNICAL
        
        # Analytical content detection
        if any(keyword in prompt_lower for keyword in ["analyze", "calculate", "compare", "data", "statistics"]):
            return LLMProfile.ANALYTICAL
        
        # Creative content detection
        if any(keyword in prompt_lower for keyword in ["create", "write", "story", "poem", "creative", "imagine"]):
            return LLMProfile.CREATIVE
        
        # Fast/simple tasks
        if len(prompt) < 50 or any(keyword in prompt_lower for keyword in ["classify", "sentiment", "category"]):
            return LLMProfile.FAST_LOCAL
        
        # Default to conversational
        return LLMProfile.CONVERSATIONAL
    
    def _select_model_for_profile(self, profile: LLMProfile, context: Dict[str, Any]) -> Tuple[str, bool]:
        """Select best available model for the given profile"""
        
        # Find models matching the profile
        matching_models = [
            (name, config) for name, config in self.model_configs.items()
            if config.profile == profile
        ]
        
        if matching_models:
            # Sort by priority (lower = better)
            matching_models.sort(key=lambda x: x[1].priority)
            selected_model = matching_models[0][0]
            return selected_model, False
        
        # Fallback: find any model that can handle the task
        fallback_models = [
            (name, config) for name, config in self.model_configs.items()
            if "general" in config.capabilities or "chat" in config.capabilities
        ]
        
        if fallback_models:
            fallback_models.sort(key=lambda x: x[1].priority)
            selected_model = fallback_models[0][0]
            return selected_model, True
        
        # Ultimate fallback
        return "default", True
    
    def _calculate_routing_confidence(self, prompt: str, context: Dict[str, Any], model: str) -> float:
        """Calculate confidence in routing decision"""
        confidence = 0.8  # Base confidence
        
        # Adjust based on context clarity
        if context.get("task_type"):
            confidence += 0.1
        
        # Adjust based on model availability
        if model in self.model_configs:
            confidence += 0.1
        
        # Adjust based on prompt clarity
        if len(prompt) > 20:
            confidence += 0.05
        
        return min(confidence, 1.0)
    
    def _generate_routing_reasoning(self, profile: LLMProfile, model: str, context: Dict[str, Any]) -> str:
        """Generate human-readable reasoning for routing decision"""
        reasons = []
        
        reasons.append(f"Selected profile: {profile.value}")
        reasons.append(f"Chosen model: {model}")
        
        if context.get("task_type"):
            reasons.append(f"Task type: {context['task_type']}")
        
        if model in self.model_configs:
            config = self.model_configs[model]
            reasons.append(f"Model capabilities: {', '.join(config.capabilities)}")
        
        return " | ".join(reasons)
    
    def _update_metrics(self, decision: RoutingDecision):
        """Update routing metrics"""
        self.metrics["routing_decisions"] += 1
        
        if decision.fallback_used:
            self.metrics["fallback_uses"] += 1
        
        self.metrics["profile_usage"][decision.profile_used.value] += 1
        
        if decision.selected_model not in self.metrics["model_usage"]:
            self.metrics["model_usage"][decision.selected_model] = 0
        self.metrics["model_usage"][decision.selected_model] += 1
        
        self.metrics["routing_latency"].append(decision.routing_time)
        
        # Update success rate based on confidence
        current_success = self.metrics["success_rate"]
        new_success = (current_success * (self.metrics["routing_decisions"] - 1) + decision.confidence) / self.metrics["routing_decisions"]
        self.metrics["success_rate"] = new_success
    
    def get_routing_metrics(self) -> Dict[str, Any]:
        """Get comprehensive routing metrics"""
        return {
            "total_decisions": self.metrics["routing_decisions"],
            "fallback_rate": self.metrics["fallback_uses"] / max(self.metrics["routing_decisions"], 1),
            "avg_routing_latency": sum(self.metrics["routing_latency"]) / max(len(self.metrics["routing_latency"]), 1),
            "success_rate": self.metrics["success_rate"],
            "profile_distribution": self.metrics["profile_usage"],
            "model_distribution": self.metrics["model_usage"],
            "available_profiles": [profile.value for profile in LLMProfile],
            "available_models": list(self.model_configs.keys())
        }
    
    def add_model_config(self, config: ModelConfig):
        """Add new model configuration"""
        self.model_configs[config.name] = config
    
    def update_user_preferences(self, user_id: str, preferences: Dict[str, Any]):
        """Update user-specific routing preferences"""
        # This would integrate with user preference storage
        pass
    
    def get_model_recommendations(self, context: Dict[str, Any]) -> List[Tuple[str, float]]:
        """Get model recommendations with confidence scores"""
        recommendations = []
        
        for model_name, config in self.model_configs.items():
            # Calculate recommendation score
            score = 0.5  # Base score
            
            # Context matching
            task_type = context.get("task_type", "").lower()
            if task_type in [cap.lower() for cap in config.capabilities]:
                score += 0.3
            
            # Priority bonus (lower priority = higher score)
            score += (10 - config.priority) / 20
            
            recommendations.append((model_name, min(score, 1.0)))
        
        # Sort by score
        recommendations.sort(key=lambda x: x[1], reverse=True)
        return recommendations


# Create singleton instance
llm_router = LLMProfileRouter()