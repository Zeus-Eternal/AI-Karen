"""
Intelligent Scaffolding Service

Replaces the dedicated TinyLlama service with a flexible scaffolding service
that uses the model discovery and routing system to select the best available
model for fast reasoning scaffolding tasks.

This eliminates the architectural inconsistency of having a dedicated model
while providing the same functionality through the intelligent routing system.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import hashlib

from ai_karen_engine.services.intelligent_model_router import (
    ModelRouter, get_model_router
)
from ai_karen_engine.services.model_discovery_engine import (
    ModelDiscoveryEngine, get_model_discovery_engine
)
from ai_karen_engine.services.profile_manager import (
    ProfileManager, get_profile_manager
)

logger = logging.getLogger("kari.intelligent_scaffolding_service")

@dataclass
class ScaffoldingConfig:
    """Configuration for scaffolding operations."""
    preferred_model_size: str = "small"  # small, medium, large
    max_response_time_ms: int = 2000  # 2 seconds max for scaffolding
    fallback_to_rule_based: bool = True
    cache_scaffolding_results: bool = True
    preferred_capabilities: List[str] = field(default_factory=lambda: ["CHAT", "REASONING"])
    max_context_length: int = 2048  # Smaller context for speed

@dataclass
class ScaffoldingResult:
    """Result of scaffolding generation."""
    content: str
    processing_time: float
    model_used: str
    model_type: str  # "llm" or "rule_based"
    input_length: int = 0
    output_tokens: int = 0
    cached: bool = False

class IntelligentScaffoldingService:
    """
    Intelligent scaffolding service that uses model discovery and routing
    to select the best available model for fast reasoning scaffolding tasks.
    
    This replaces the dedicated TinyLlama service with a more flexible approach.
    """
    
    def __init__(self, config: Optional[ScaffoldingConfig] = None):
        self.config = config or ScaffoldingConfig()
        self.logger = logging.getLogger("kari.intelligent_scaffolding_service")
        
        # Core services
        self.model_router = get_model_router()
        self.model_discovery = get_model_discovery_engine()
        self.profile_manager = get_profile_manager()
        
        # Model selection cache
        self._model_cache: Dict[str, str] = {}  # task_type -> model_id
        self._model_cache_expiry: Dict[str, datetime] = {}
        self._cache_duration = timedelta(minutes=30)
        
        # Performance tracking
        self._performance_history: Dict[str, List[float]] = {}
        
        self.logger.info("Intelligent Scaffolding Service initialized")
    
    async def generate_scaffold(
        self, 
        text: str, 
        scaffold_type: str = "reasoning",
        max_tokens: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> ScaffoldingResult:
        """
        Generate scaffolding using the best available model for the task.
        
        This replaces the TinyLlama-specific scaffolding with intelligent model selection.
        """
        start_time = time.time()
        
        try:
            # Select best model for scaffolding
            selected_model = await self._select_scaffolding_model(scaffold_type, context)
            
            if selected_model["type"] == "llm":
                # Use LLM for scaffolding
                result = await self._generate_llm_scaffold(
                    text, scaffold_type, selected_model["model_id"], max_tokens, context
                )
            else:
                # Use rule-based fallback
                result = await self._generate_rule_based_scaffold(
                    text, scaffold_type, context
                )
            
            # Track performance
            processing_time = time.time() - start_time
            self._track_performance(selected_model["model_id"], processing_time)
            
            return ScaffoldingResult(
                content=result,
                processing_time=processing_time,
                model_used=selected_model["model_id"],
                model_type=selected_model["type"],
                input_length=len(text),
                output_tokens=len(result.split()) if result else 0
            )
            
        except Exception as e:
            self.logger.error(f"Scaffolding generation failed: {e}")
            
            # Fallback to rule-based
            if self.config.fallback_to_rule_based:
                result = await self._generate_rule_based_scaffold(text, scaffold_type, context)
                processing_time = time.time() - start_time
                
                return ScaffoldingResult(
                    content=result,
                    processing_time=processing_time,
                    model_used="rule_based_fallback",
                    model_type="rule_based",
                    input_length=len(text),
                    output_tokens=len(result.split()) if result else 0
                )
            else:
                raise
    
    async def generate_outline(
        self, 
        text: str, 
        outline_style: str = "bullet",
        max_points: int = 5
    ) -> ScaffoldingResult:
        """Generate outline using intelligent model selection."""
        return await self.generate_scaffold(
            text, 
            scaffold_type="outline", 
            context={
                "outline_style": outline_style,
                "max_points": max_points
            }
        )
    
    async def generate_short_fill(
        self, 
        context: str, 
        prompt: str, 
        max_tokens: Optional[int] = None,
        fill_type: str = "continuation"
    ) -> ScaffoldingResult:
        """Generate short fill using intelligent model selection."""
        combined_input = f"{context}\n\n{prompt}"
        return await self.generate_scaffold(
            combined_input,
            scaffold_type="fill",
            max_tokens=max_tokens or 50,
            context={"fill_type": fill_type}
        )
    
    async def summarize_context(
        self, 
        text: str, 
        summary_type: str = "concise",
        max_tokens: Optional[int] = None
    ) -> ScaffoldingResult:
        """Generate summary using intelligent model selection."""
        return await self.generate_scaffold(
            text,
            scaffold_type="summary",
            max_tokens=max_tokens or 120,
            context={"summary_type": summary_type}
        )
    
    async def _select_scaffolding_model(
        self, 
        scaffold_type: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, str]:
        """
        Select the best model for scaffolding based on:
        1. Model size (prefer smaller for speed)
        2. Model capabilities
        3. Current performance
        4. Availability
        """
        try:
            # Check cache first
            cache_key = f"{scaffold_type}_{hash(str(context))}"
            if (cache_key in self._model_cache and 
                cache_key in self._model_cache_expiry and
                datetime.now() < self._model_cache_expiry[cache_key]):
                
                return {
                    "model_id": self._model_cache[cache_key],
                    "type": "llm"
                }
            
            # Get available models
            available_models = await self.model_discovery.get_all_models()
            
            # Filter models suitable for scaffolding
            suitable_models = []
            for model in available_models:
                # Check capabilities
                model_capabilities = {cap.value for cap in model.capabilities}
                if not set(self.config.preferred_capabilities).intersection(model_capabilities):
                    continue
                
                # Check context length
                if (hasattr(model, 'metadata') and model.metadata and 
                    hasattr(model.metadata, 'context_length') and
                    model.metadata.context_length < self.config.max_context_length):
                    continue
                
                # Prefer smaller models for speed
                model_score = self._calculate_scaffolding_score(model)
                suitable_models.append((model, model_score))
            
            if not suitable_models:
                self.logger.warning("No suitable models found for scaffolding, using rule-based fallback")
                return {"model_id": "rule_based", "type": "rule_based"}
            
            # Sort by score (higher is better)
            suitable_models.sort(key=lambda x: x[1], reverse=True)
            best_model = suitable_models[0][0]
            
            # Cache the selection
            self._model_cache[cache_key] = best_model.id
            self._model_cache_expiry[cache_key] = datetime.now() + self._cache_duration
            
            return {
                "model_id": best_model.id,
                "type": "llm"
            }
            
        except Exception as e:
            self.logger.error(f"Model selection failed: {e}")
            return {"model_id": "rule_based", "type": "rule_based"}
    
    def _calculate_scaffolding_score(self, model: Any) -> float:
        """
        Calculate a score for how suitable a model is for scaffolding.
        Higher score = better for scaffolding.
        """
        score = 0.0
        
        # Prefer smaller models (faster)
        if hasattr(model, 'size'):
            # Smaller size gets higher score
            size_gb = model.size / (1024 * 1024 * 1024)
            if size_gb < 2:
                score += 3.0  # Very small model
            elif size_gb < 7:
                score += 2.0  # Small model
            elif size_gb < 15:
                score += 1.0  # Medium model
            # Large models get 0 points
        
        # Prefer models with reasoning capability
        if hasattr(model, 'capabilities'):
            capabilities = {cap.value for cap in model.capabilities}
            if "REASONING" in capabilities:
                score += 2.0
            if "CHAT" in capabilities:
                score += 1.0
        
        # Consider historical performance
        if model.id in self._performance_history:
            avg_time = sum(self._performance_history[model.id]) / len(self._performance_history[model.id])
            if avg_time < 1.0:  # Less than 1 second
                score += 2.0
            elif avg_time < 2.0:  # Less than 2 seconds
                score += 1.0
        
        # Prefer quantized models (usually faster)
        if (hasattr(model, 'metadata') and model.metadata and 
            hasattr(model.metadata, 'quantization') and model.metadata.quantization):
            score += 1.0
        
        return score
    
    async def _generate_llm_scaffold(
        self,
        text: str,
        scaffold_type: str,
        model_id: str,
        max_tokens: Optional[int],
        context: Optional[Dict[str, Any]]
    ) -> str:
        """Generate scaffolding using an LLM through the model router."""
        try:
            # Create appropriate prompt based on scaffold type
            prompt = self._create_scaffold_prompt(text, scaffold_type, context)
            
            # Use model router to generate response
            routing_decision = await self.model_router.route_request(
                query=prompt,
                task_type="reasoning",
                context={
                    "preferred_model": model_id,
                    "max_tokens": max_tokens or 100,
                    "temperature": 0.7,
                    "scaffolding_task": True
                }
            )
            
            if routing_decision.success and routing_decision.response:
                return routing_decision.response.strip()
            else:
                raise Exception(f"Model routing failed: {routing_decision.error}")
                
        except Exception as e:
            self.logger.error(f"LLM scaffolding failed: {e}")
            raise
    
    def _create_scaffold_prompt(
        self, 
        text: str, 
        scaffold_type: str, 
        context: Optional[Dict[str, Any]]
    ) -> str:
        """Create appropriate prompt for scaffolding task."""
        context = context or {}
        
        if scaffold_type == "reasoning":
            return f"Create a brief step-by-step reasoning outline for: {text}\n\nReasoning steps:"
        
        elif scaffold_type == "outline":
            style = context.get("outline_style", "bullet")
            max_points = context.get("max_points", 5)
            return f"Create a {style} point outline with {max_points} main points for: {text}\n\nOutline:"
        
        elif scaffold_type == "fill":
            fill_type = context.get("fill_type", "continuation")
            return f"{text}\n\nContinue logically ({fill_type}):"
        
        elif scaffold_type == "summary":
            summary_type = context.get("summary_type", "concise")
            return f"Provide a {summary_type} summary of: {text}\n\nSummary:"
        
        else:
            return f"Create a structured scaffold for: {text}\n\nScaffold:"
    
    async def _generate_rule_based_scaffold(
        self,
        text: str,
        scaffold_type: str,
        context: Optional[Dict[str, Any]]
    ) -> str:
        """Generate scaffolding using rule-based approach as fallback."""
        context = context or {}
        
        if scaffold_type == "reasoning":
            sentences = text.replace('?', '.').replace('!', '.').split('.')
            sentences = [s.strip() for s in sentences if s.strip()]
            if len(sentences) > 1:
                return f"1. Analyze: {sentences[0][:60]}...\n2. Evaluate: {sentences[-1][:60]}...\n3. Synthesize findings\n4. Draw conclusions"
            else:
                return "1. Break down the core question\n2. Identify key factors\n3. Analyze relationships\n4. Formulate conclusions"
        
        elif scaffold_type == "outline":
            style = context.get("outline_style", "bullet")
            max_points = context.get("max_points", 5)
            words = text.split()
            points = []
            
            if len(words) > 10:
                chunk_size = len(words) // max_points
                for i in range(max_points):
                    start = i * chunk_size
                    end = start + min(chunk_size, 10)
                    chunk = " ".join(words[start:end])
                    points.append(f"{'•' if style == 'bullet' else f'{i+1}.'} {chunk}...")
            else:
                points = [f"{'•' if style == 'bullet' else '1.'} {text[:100]}..."]
            
            return "\n".join(points)
        
        elif scaffold_type == "fill":
            words = text.split()
            if words:
                last_word = words[-1]
                return f"Building on '{last_word}', the logical continuation involves..."
            else:
                return "The discussion continues with relevant analysis..."
        
        elif scaffold_type == "summary":
            summary_type = context.get("summary_type", "concise")
            words = text.split()
            if len(words) > 50:
                if summary_type == "concise":
                    return f"Summary: {' '.join(words[:20])}... {' '.join(words[-10:])}"
                else:
                    return f"Detailed summary: {' '.join(words[:30])}... Key points include the main themes and conclusions."
            else:
                return f"Summary: {text[:200]}..."
        
        else:
            return f"Structured analysis of: {text[:100]}...\n• Key points and relationships\n• Implications and conclusions"
    
    def _track_performance(self, model_id: str, processing_time: float):
        """Track model performance for future selection."""
        if model_id not in self._performance_history:
            self._performance_history[model_id] = []
        
        self._performance_history[model_id].append(processing_time)
        
        # Keep only recent performance data
        if len(self._performance_history[model_id]) > 100:
            self._performance_history[model_id] = self._performance_history[model_id][-50:]
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics for all models used."""
        stats = {}
        for model_id, times in self._performance_history.items():
            if times:
                stats[model_id] = {
                    "avg_time": sum(times) / len(times),
                    "min_time": min(times),
                    "max_time": max(times),
                    "total_uses": len(times)
                }
        return stats
    
    def clear_model_cache(self):
        """Clear the model selection cache."""
        self._model_cache.clear()
        self._model_cache_expiry.clear()
        self.logger.info("Model selection cache cleared")

# Global instance
_intelligent_scaffolding_service: Optional[IntelligentScaffoldingService] = None

def get_intelligent_scaffolding_service(
    config: Optional[ScaffoldingConfig] = None
) -> IntelligentScaffoldingService:
    """Get the global intelligent scaffolding service instance."""
    global _intelligent_scaffolding_service
    if _intelligent_scaffolding_service is None:
        _intelligent_scaffolding_service = IntelligentScaffoldingService(config)
    return _intelligent_scaffolding_service