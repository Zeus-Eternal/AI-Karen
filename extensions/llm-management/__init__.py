"""
LLM Management Extension - Comprehensive LLM provider and model management

This extension provides advanced LLM management capabilities including:
- Provider registration and configuration
- Model performance monitoring
- AI-powered optimization recommendations
- Health checking and failover management
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ai_karen_engine.extensions.base import BaseExtension
from ai_karen_engine.hooks.hook_mixin import HookMixin

logger = logging.getLogger(__name__)


class ProviderConfig(BaseModel):
    """Configuration model for LLM providers."""
    name: str
    provider_type: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    models: List[str] = []
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    enabled: bool = True


class ModelPerformance(BaseModel):
    """Model performance metrics."""
    model_name: str
    provider: str
    avg_response_time: float
    success_rate: float
    token_efficiency: float
    cost_per_token: Optional[float] = None
    last_updated: str


class OptimizationRequest(BaseModel):
    """Request for AI-powered optimization."""
    target_metric: str  # "speed", "cost", "quality", "balanced"
    workload_type: str  # "chat", "completion", "analysis", "creative"
    constraints: Optional[Dict[str, Any]] = None


class LLMManagementExtension(BaseExtension, HookMixin):
    """LLM Management Extension with AI-powered optimization."""
    
    async def _initialize(self) -> None:
        """Initialize the LLM Management Extension."""
        self.logger.info("LLM Management Extension initializing...")
        
        # Initialize management data
        self.providers: Dict[str, Dict[str, Any]] = {}
        self.model_performance: Dict[str, ModelPerformance] = {}
        self.optimization_history: List[Dict[str, Any]] = []
        self.health_status: Dict[str, Dict[str, Any]] = {}
        
        # Load existing providers and models
        await self._discover_existing_providers()
        
        # Set up MCP tools for AI integration
        await self._setup_mcp_tools()
        
        # Register hooks for performance monitoring
        await self._register_performance_hooks()
        
        self.logger.info("LLM Management Extension initialized successfully")
    
    async def _discover_existing_providers(self) -> None:
        """Discover existing LLM providers in the system."""
        try:
            # This would typically query the system's provider registry
            # For now, we'll simulate with common providers
            default_providers = {
                "openai": {
                    "name": "OpenAI",
                    "provider_type": "openai",
                    "models": ["gpt-4", "gpt-3.5-turbo", "gpt-4-turbo"],
                    "enabled": True,
                    "discovered_at": datetime.utcnow().isoformat()
                },
                "anthropic": {
                    "name": "Anthropic",
                    "provider_type": "anthropic",
                    "models": ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"],
                    "enabled": True,
                    "discovered_at": datetime.utcnow().isoformat()
                },
                "huggingface": {
                    "name": "Hugging Face",
                    "provider_type": "huggingface",
                    "models": ["microsoft/DialoGPT-medium", "facebook/blenderbot-400M-distill"],
                    "enabled": True,
                    "discovered_at": datetime.utcnow().isoformat()
                }
            }
            
            self.providers.update(default_providers)
            self.logger.info(f"Discovered {len(default_providers)} LLM providers")
            
        except Exception as e:
            self.logger.error(f"Failed to discover existing providers: {e}")
    
    async def _setup_mcp_tools(self) -> None:
        """Set up MCP tools for AI-powered LLM management."""
        mcp_server = self.create_mcp_server()
        if mcp_server:
            # Register LLM management tools
            await self.register_mcp_tool(
                name="register_provider",
                handler=self._register_provider_tool,
                schema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Provider name"},
                        "provider_type": {"type": "string", "description": "Provider type (openai, anthropic, etc.)"},
                        "api_key": {"type": "string", "description": "API key for the provider"},
                        "models": {"type": "array", "items": {"type": "string"}, "description": "Available models"}
                    },
                    "required": ["name", "provider_type"]
                },
                description="Register a new LLM provider"
            )
            
            await self.register_mcp_tool(
                name="optimize_model_selection",
                handler=self._optimize_model_selection_tool,
                schema={
                    "type": "object",
                    "properties": {
                        "task_description": {"type": "string", "description": "Description of the task"},
                        "target_metric": {"type": "string", "enum": ["speed", "cost", "quality", "balanced"], "description": "Optimization target"},
                        "constraints": {"type": "object", "description": "Additional constraints"}
                    },
                    "required": ["task_description", "target_metric"]
                },
                description="Get AI-powered model selection recommendations"
            )
            
            await self.register_mcp_tool(
                name="analyze_performance",
                handler=self._analyze_performance_tool,
                schema={
                    "type": "object",
                    "properties": {
                        "model_name": {"type": "string", "description": "Model to analyze"},
                        "timeframe": {"type": "string", "enum": ["1h", "24h", "7d", "30d"], "default": "24h", "description": "Analysis timeframe"}
                    },
                    "required": ["model_name"]
                },
                description="Analyze model performance metrics"
            )
    
    async def _register_performance_hooks(self) -> None:
        """Register hooks for performance monitoring."""
        try:
            await self.register_hook(
                'llm_response',
                self._track_model_performance,
                priority=95
            )
            
            await self.register_hook(
                'llm_error',
                self._track_model_errors,
                priority=95
            )
            
            self.logger.info("Performance monitoring hooks registered")
            
        except Exception as e:
            self.logger.error(f"Failed to register performance hooks: {e}")
    
    async def _register_provider_tool(self, name: str, provider_type: str, api_key: Optional[str] = None, models: Optional[List[str]] = None) -> Dict[str, Any]:
        """MCP tool to register a new LLM provider."""
        try:
            provider_config = {
                "name": name,
                "provider_type": provider_type,
                "api_key": api_key,
                "models": models or [],
                "enabled": True,
                "registered_at": datetime.utcnow().isoformat(),
                "health_status": "unknown"
            }
            
            self.providers[name.lower()] = provider_config
            
            # Initialize health status
            self.health_status[name.lower()] = {
                "status": "unknown",
                "last_check": datetime.utcnow().isoformat(),
                "response_time": None,
                "error_count": 0
            }
            
            return {
                "success": True,
                "provider": provider_config,
                "message": f"Provider '{name}' registered successfully"
            }
            
        except Exception as e:
            self.logger.error(f"Failed to register provider: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _optimize_model_selection_tool(self, task_description: str, target_metric: str, constraints: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """MCP tool for AI-powered model selection optimization."""
        try:
            # Use plugin orchestration for AI-powered analysis
            analysis_result = await self.plugin_orchestrator.execute_plugin(
                intent="analyze_text",
                params={
                    "text": task_description,
                    "analysis_type": "task_classification"
                },
                user_context={"roles": ["admin"]}
            )
            
            task_type = analysis_result.get("category", "general") if analysis_result else "general"
            
            # Get model recommendations based on task type and target metric
            recommendations = self._get_model_recommendations(task_type, target_metric, constraints)
            
            # Store optimization request
            optimization_record = {
                "task_description": task_description,
                "task_type": task_type,
                "target_metric": target_metric,
                "constraints": constraints,
                "recommendations": recommendations,
                "timestamp": datetime.utcnow().isoformat()
            }
            self.optimization_history.append(optimization_record)
            
            return {
                "success": True,
                "task_type": task_type,
                "recommendations": recommendations,
                "reasoning": self._generate_optimization_reasoning(recommendations, target_metric)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to optimize model selection: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _analyze_performance_tool(self, model_name: str, timeframe: str = "24h") -> Dict[str, Any]:
        """MCP tool to analyze model performance."""
        try:
            # Get performance data for the model
            performance_data = self.model_performance.get(model_name)
            
            if not performance_data:
                return {
                    "success": False,
                    "error": f"No performance data available for model '{model_name}'"
                }
            
            # Generate performance analysis
            analysis = {
                "model_name": model_name,
                "timeframe": timeframe,
                "metrics": {
                    "avg_response_time": performance_data.avg_response_time,
                    "success_rate": performance_data.success_rate,
                    "token_efficiency": performance_data.token_efficiency,
                    "cost_per_token": performance_data.cost_per_token
                },
                "health_status": self.health_status.get(performance_data.provider, {}).get("status", "unknown"),
                "recommendations": self._generate_performance_recommendations(performance_data)
            }
            
            return {
                "success": True,
                "analysis": analysis
            }
            
        except Exception as e:
            self.logger.error(f"Failed to analyze performance: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _get_model_recommendations(self, task_type: str, target_metric: str, constraints: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get model recommendations based on task type and optimization target."""
        recommendations = []
        
        # Define model characteristics (in a real implementation, this would be data-driven)
        model_characteristics = {
            "gpt-4": {"speed": 6, "cost": 3, "quality": 10, "creativity": 9},
            "gpt-3.5-turbo": {"speed": 9, "cost": 8, "quality": 7, "creativity": 7},
            "claude-3-opus": {"speed": 5, "cost": 4, "quality": 9, "creativity": 8},
            "claude-3-sonnet": {"speed": 7, "cost": 6, "quality": 8, "creativity": 7},
            "claude-3-haiku": {"speed": 9, "cost": 9, "quality": 6, "creativity": 6}
        }
        
        # Score models based on target metric
        for model, characteristics in model_characteristics.items():
            if target_metric == "balanced":
                score = sum(characteristics.values()) / len(characteristics)
            else:
                score = characteristics.get(target_metric, 5)
            
            # Apply task-specific adjustments
            if task_type == "creative" and target_metric != "cost":
                score += characteristics.get("creativity", 5) * 0.2
            elif task_type == "analytical" and target_metric != "cost":
                score += characteristics.get("quality", 5) * 0.2
            
            recommendations.append({
                "model": model,
                "score": round(score, 2),
                "characteristics": characteristics,
                "reasoning": f"Optimized for {target_metric} with {task_type} tasks"
            })
        
        # Sort by score (descending)
        recommendations.sort(key=lambda x: x["score"], reverse=True)
        
        return recommendations[:3]  # Return top 3 recommendations
    
    def _generate_optimization_reasoning(self, recommendations: List[Dict[str, Any]], target_metric: str) -> str:
        """Generate human-readable reasoning for optimization recommendations."""
        if not recommendations:
            return "No suitable models found for the given criteria."
        
        top_model = recommendations[0]
        reasoning = f"Based on your optimization target of '{target_metric}', I recommend {top_model['model']} "
        reasoning += f"with a score of {top_model['score']}/10. "
        
        if target_metric == "speed":
            reasoning += "This model offers the best response time for your use case."
        elif target_metric == "cost":
            reasoning += "This model provides the most cost-effective solution."
        elif target_metric == "quality":
            reasoning += "This model delivers the highest quality responses."
        else:
            reasoning += "This model offers the best overall balance of performance metrics."
        
        return reasoning
    
    def _generate_performance_recommendations(self, performance_data: ModelPerformance) -> List[str]:
        """Generate performance improvement recommendations."""
        recommendations = []
        
        if performance_data.avg_response_time > 5000:  # > 5 seconds
            recommendations.append("Consider switching to a faster model for better response times")
        
        if performance_data.success_rate < 0.95:  # < 95%
            recommendations.append("Monitor error rates and consider implementing retry logic")
        
        if performance_data.token_efficiency < 0.7:  # < 70%
            recommendations.append("Optimize prompts to improve token efficiency")
        
        if not recommendations:
            recommendations.append("Performance is within acceptable ranges")
        
        return recommendations
    
    async def _track_model_performance(self, context: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Hook to track model performance metrics."""
        try:
            response = context.get('response', {})
            model_name = response.get('model', 'unknown')
            provider = response.get('provider', 'unknown')
            
            # Update performance metrics
            if model_name != 'unknown':
                current_performance = self.model_performance.get(model_name)
                
                if current_performance:
                    # Update existing metrics (simple moving average)
                    current_performance.avg_response_time = (
                        current_performance.avg_response_time * 0.9 + 
                        response.get('processing_time', 0) * 0.1
                    )
                    current_performance.success_rate = min(current_performance.success_rate + 0.01, 1.0)
                else:
                    # Create new performance record
                    self.model_performance[model_name] = ModelPerformance(
                        model_name=model_name,
                        provider=provider,
                        avg_response_time=response.get('processing_time', 0),
                        success_rate=1.0,
                        token_efficiency=response.get('token_usage', 0) / max(len(response.get('content', '')), 1),
                        last_updated=datetime.utcnow().isoformat()
                    )
            
            return {'success': True, 'performance_tracked': True}
            
        except Exception as e:
            self.logger.error(f"Failed to track model performance: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _track_model_errors(self, context: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Hook to track model errors."""
        try:
            error_info = context.get('error', {})
            model_name = error_info.get('model', 'unknown')
            
            # Update error metrics
            if model_name in self.model_performance:
                current_performance = self.model_performance[model_name]
                current_performance.success_rate = max(current_performance.success_rate - 0.05, 0.0)
            
            # Update health status
            provider = error_info.get('provider', 'unknown')
            if provider in self.health_status:
                self.health_status[provider]['error_count'] += 1
                self.health_status[provider]['last_error'] = datetime.utcnow().isoformat()
            
            return {'success': True, 'error_tracked': True}
            
        except Exception as e:
            self.logger.error(f"Failed to track model error: {e}")
            return {'success': False, 'error': str(e)}
    
    def create_api_router(self) -> APIRouter:
        """Create API routes for the LLM Management Extension."""
        router = APIRouter(prefix=f"/api/extensions/{self.manifest.name}")
        
        @router.get("/providers")
        async def list_providers():
            """List all registered LLM providers."""
            return {"providers": list(self.providers.values())}
        
        @router.post("/providers")
        async def register_provider(config: ProviderConfig):
            """Register a new LLM provider."""
            result = await self._register_provider_tool(
                config.name, config.provider_type, config.api_key, config.models
            )
            if not result["success"]:
                raise HTTPException(status_code=400, detail=result["error"])
            return result
        
        @router.get("/models")
        async def list_models():
            """List all available models with performance data."""
            models = []
            for provider_name, provider_info in self.providers.items():
                for model in provider_info.get("models", []):
                    performance = self.model_performance.get(model)
                    models.append({
                        "name": model,
                        "provider": provider_name,
                        "performance": performance.dict() if performance else None
                    })
            return {"models": models}
        
        @router.post("/optimize")
        async def optimize_model_selection(request: OptimizationRequest):
            """Get AI-powered model selection recommendations."""
            result = await self._optimize_model_selection_tool(
                f"Task type: {request.workload_type}",
                request.target_metric,
                request.constraints
            )
            if not result["success"]:
                raise HTTPException(status_code=400, detail=result["error"])
            return result
        
        @router.get("/performance/{model_name}")
        async def get_model_performance(model_name: str, timeframe: str = Query(default="24h")):
            """Get performance analysis for a specific model."""
            result = await self._analyze_performance_tool(model_name, timeframe)
            if not result["success"]:
                raise HTTPException(status_code=404, detail=result["error"])
            return result
        
        @router.get("/health")
        async def get_health_status():
            """Get health status of all providers."""
            return {"health_status": self.health_status}
        
        @router.get("/optimization-history")
        async def get_optimization_history(limit: int = Query(default=10, le=100)):
            """Get optimization request history."""
            return {
                "history": self.optimization_history[-limit:] if limit > 0 else self.optimization_history
            }
        
        return router
    
    def create_background_tasks(self) -> List:
        """Create background tasks for the extension."""
        tasks = super().create_background_tasks()
        
        # Background tasks are defined in the manifest and scheduled automatically
        # The actual task functions would be implemented here
        
        return tasks
    
    def create_ui_components(self) -> Dict[str, Any]:
        """Create UI components for the LLM Management dashboard."""
        components = super().create_ui_components()
        
        # Add LLM management dashboard data
        components["llm_dashboard"] = {
            "title": "LLM Management Dashboard",
            "description": "Comprehensive LLM provider and model management",
            "data": {
                "total_providers": len(self.providers),
                "total_models": sum(len(p.get("models", [])) for p in self.providers.values()),
                "optimization_requests": len(self.optimization_history),
                "healthy_providers": sum(1 for status in self.health_status.values() if status.get("status") == "healthy")
            }
        }
        
        return components
    
    async def _shutdown(self) -> None:
        """Cleanup the LLM Management Extension."""
        self.logger.info("LLM Management Extension shutting down...")
        
        # Save performance data and optimization history if needed
        # Clear caches
        self.providers.clear()
        self.model_performance.clear()
        self.optimization_history.clear()
        self.health_status.clear()
        
        self.logger.info("LLM Management Extension shut down successfully")


# Export the extension class
__all__ = ["LLMManagementExtension"]