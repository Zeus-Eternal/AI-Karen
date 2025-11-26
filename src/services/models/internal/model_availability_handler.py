"""
Model Availability and Routing Error Handler

This module handles model availability issues and routing errors,
providing intelligent fallback mechanisms with modality consideration.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple, Any
from collections import defaultdict

from ...internal..core.types.shared_types import (
    ModelInfo, Modality, ModalityType, ModelStatus, ModelType
)


class ModelAvailabilityStatus(Enum):
    """Model availability status."""
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    LOADING = "loading"
    ERROR = "error"
    TIMEOUT = "timeout"
    OVERLOADED = "overloaded"


@dataclass
class ModelHealthCheck:
    """Model health check result."""
    model_id: str
    status: ModelAvailabilityStatus
    response_time: float
    error_message: Optional[str] = None
    last_check: float = field(default_factory=time.time)
    consecutive_failures: int = 0
    load_percentage: float = 0.0


@dataclass
class ModalityRequirement:
    """Requirement for specific modality support."""
    modality_type: ModalityType
    input_required: bool = True
    output_required: bool = True
    formats: Optional[List[str]] = None
    priority: int = 1  # 1 = required, 2 = preferred, 3 = optional


@dataclass
class FallbackCandidate:
    """Candidate model for fallback."""
    model_info: ModelInfo
    compatibility_score: float
    modality_coverage: Dict[ModalityType, float]
    estimated_performance: float
    availability_score: float


class ModelAvailabilityHandler:
    """
    Handles model availability monitoring and provides intelligent
    fallback mechanisms with modality consideration.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Model health tracking
        self.model_health: Dict[str, ModelHealthCheck] = {}
        self.health_check_interval = 30.0  # seconds
        self.max_consecutive_failures = 3
        
        # Fallback model registry organized by modality
        self.fallback_registry: Dict[ModalityType, List[str]] = {
            ModalityType.TEXT: [
                "tinyllama-1.1b-chat",
                "gpt-3.5-turbo",
                "claude-3-haiku",
                "llama-2-7b-chat"
            ],
            ModalityType.IMAGE: [
                "clip-vit-base-patch32",
                "blip-2-opt-2.7b",
                "stable-diffusion-v1-5"
            ],
            ModalityType.AUDIO: [
                "whisper-tiny",
                "whisper-base",
                "wav2vec2-base"
            ],
            ModalityType.VIDEO: [
                "clip-vit-base-patch32",  # Can handle video frames
                "videomae-base"
            ]
        }
        
        # Model compatibility matrix
        self.compatibility_matrix: Dict[str, Dict[ModalityType, float]] = {}
        
        # Performance baselines
        self.performance_baselines: Dict[str, Dict[str, float]] = {}
        
        # Circuit breaker states
        self.circuit_breakers: Dict[str, bool] = {}
        
        # Load balancing
        self.model_loads: Dict[str, int] = defaultdict(int)
        self.max_concurrent_requests = 10
    
    async def check_model_availability(
        self, 
        model_id: str,
        timeout: float = 5.0
    ) -> ModelHealthCheck:
        """
        Check if a specific model is available and responsive.
        """
        try:
            start_time = time.time()
            
            # Check circuit breaker
            if self.circuit_breakers.get(model_id, False):
                return ModelHealthCheck(
                    model_id=model_id,
                    status=ModelAvailabilityStatus.UNAVAILABLE,
                    response_time=0.0,
                    error_message="Circuit breaker open"
                )
            
            # Check current load
            current_load = self.model_loads.get(model_id, 0)
            if current_load >= self.max_concurrent_requests:
                return ModelHealthCheck(
                    model_id=model_id,
                    status=ModelAvailabilityStatus.OVERLOADED,
                    response_time=0.0,
                    load_percentage=(current_load / self.max_concurrent_requests) * 100
                )
            
            # Perform health check
            health_result = await self._perform_health_check(model_id, timeout)
            
            # Update health tracking
            self.model_health[model_id] = health_result
            
            # Update circuit breaker
            if health_result.status == ModelAvailabilityStatus.AVAILABLE:
                health_result.consecutive_failures = 0
                self.circuit_breakers[model_id] = False
            else:
                previous_health = self.model_health.get(model_id)
                if previous_health:
                    health_result.consecutive_failures = previous_health.consecutive_failures + 1
                else:
                    health_result.consecutive_failures = 1
                
                # Open circuit breaker if too many failures
                if health_result.consecutive_failures >= self.max_consecutive_failures:
                    self.circuit_breakers[model_id] = True
                    self.logger.warning(f"Circuit breaker opened for model {model_id}")
            
            return health_result
            
        except Exception as e:
            self.logger.error(f"Health check failed for model {model_id}: {str(e)}")
            return ModelHealthCheck(
                model_id=model_id,
                status=ModelAvailabilityStatus.ERROR,
                response_time=0.0,
                error_message=str(e)
            )
    
    async def find_fallback_models(
        self,
        failed_model_id: str,
        modality_requirements: List[ModalityRequirement],
        max_candidates: int = 5
    ) -> List[FallbackCandidate]:
        """
        Find suitable fallback models based on modality requirements.
        """
        try:
            candidates = []
            
            # Get all potential fallback models
            potential_models = set()
            for req in modality_requirements:
                fallback_models = self.fallback_registry.get(req.modality_type, [])
                potential_models.update(fallback_models)
            
            # Remove the failed model
            potential_models.discard(failed_model_id)
            
            # Evaluate each candidate
            for model_id in potential_models:
                try:
                    # Check availability
                    health_check = await self.check_model_availability(model_id)
                    if health_check.status != ModelAvailabilityStatus.AVAILABLE:
                        continue
                    
                    # Get model info (simulated)
                    model_info = await self._get_model_info(model_id)
                    if not model_info:
                        continue
                    
                    # Calculate compatibility score
                    compatibility_score = await self._calculate_compatibility_score(
                        model_info, modality_requirements
                    )
                    
                    # Calculate modality coverage
                    modality_coverage = await self._calculate_modality_coverage(
                        model_info, modality_requirements
                    )
                    
                    # Estimate performance
                    estimated_performance = await self._estimate_model_performance(
                        model_id, modality_requirements
                    )
                    
                    # Calculate availability score
                    availability_score = await self._calculate_availability_score(
                        model_id, health_check
                    )
                    
                    candidate = FallbackCandidate(
                        model_info=model_info,
                        compatibility_score=compatibility_score,
                        modality_coverage=modality_coverage,
                        estimated_performance=estimated_performance,
                        availability_score=availability_score
                    )
                    
                    candidates.append(candidate)
                    
                except Exception as e:
                    self.logger.warning(f"Failed to evaluate candidate {model_id}: {str(e)}")
                    continue
            
            # Sort candidates by overall score
            candidates.sort(
                key=lambda c: (
                    c.compatibility_score * 0.4 +
                    c.estimated_performance * 0.3 +
                    c.availability_score * 0.3
                ),
                reverse=True
            )
            
            return candidates[:max_candidates]
            
        except Exception as e:
            self.logger.error(f"Failed to find fallback models: {str(e)}")
            return []
    
    async def handle_routing_error(
        self,
        original_model_id: str,
        error: Exception,
        modality_requirements: List[ModalityRequirement],
        retry_count: int = 0,
        max_retries: int = 2
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Handle routing errors by finding alternative routes or models.
        
        Returns:
            Tuple of (fallback_model_id, error_message)
        """
        try:
            self.logger.warning(
                f"Handling routing error for model {original_model_id}: {str(error)}"
            )
            
            # If we haven't exceeded retry limit, try the same model again
            if retry_count < max_retries:
                await asyncio.sleep(2 ** retry_count)  # Exponential backoff
                
                health_check = await self.check_model_availability(original_model_id)
                if health_check.status == ModelAvailabilityStatus.AVAILABLE:
                    return original_model_id, None
            
            # Find fallback models
            fallback_candidates = await self.find_fallback_models(
                original_model_id, modality_requirements
            )
            
            if not fallback_candidates:
                return None, "No suitable fallback models available"
            
            # Try the best candidate
            best_candidate = fallback_candidates[0]
            
            # Verify the fallback model is actually available
            health_check = await self.check_model_availability(
                best_candidate.model_info.id
            )
            
            if health_check.status == ModelAvailabilityStatus.AVAILABLE:
                self.logger.info(
                    f"Successfully routed to fallback model: {best_candidate.model_info.id}"
                )
                return best_candidate.model_info.id, None
            else:
                return None, f"Fallback model {best_candidate.model_info.id} is not available"
                
        except Exception as e:
            self.logger.error(f"Routing error handling failed: {str(e)}")
            return None, str(e)
    
    async def monitor_model_health(self):
        """
        Background task to continuously monitor model health.
        """
        while True:
            try:
                # Get all registered models
                all_models = set()
                for modality_models in self.fallback_registry.values():
                    all_models.update(modality_models)
                
                # Check health of each model
                health_checks = []
                for model_id in all_models:
                    health_checks.append(self.check_model_availability(model_id))
                
                # Wait for all health checks to complete
                results = await asyncio.gather(*health_checks, return_exceptions=True)
                
                # Log health status
                available_count = 0
                for result in results:
                    if isinstance(result, ModelHealthCheck):
                        if result.status == ModelAvailabilityStatus.AVAILABLE:
                            available_count += 1
                
                self.logger.info(
                    f"Model health check complete: {available_count}/{len(all_models)} models available"
                )
                
                # Wait before next check
                await asyncio.sleep(self.health_check_interval)
                
            except Exception as e:
                self.logger.error(f"Model health monitoring failed: {str(e)}")
                await asyncio.sleep(self.health_check_interval)
    
    # Helper methods
    
    async def _perform_health_check(
        self, 
        model_id: str, 
        timeout: float
    ) -> ModelHealthCheck:
        """Perform actual health check on model."""
        start_time = time.time()
        
        try:
            # Simulate health check (in real implementation, this would ping the model)
            await asyncio.wait_for(
                self._simulate_model_ping(model_id),
                timeout=timeout
            )
            
            response_time = time.time() - start_time
            
            return ModelHealthCheck(
                model_id=model_id,
                status=ModelAvailabilityStatus.AVAILABLE,
                response_time=response_time
            )
            
        except asyncio.TimeoutError:
            return ModelHealthCheck(
                model_id=model_id,
                status=ModelAvailabilityStatus.TIMEOUT,
                response_time=timeout,
                error_message="Health check timeout"
            )
        except Exception as e:
            return ModelHealthCheck(
                model_id=model_id,
                status=ModelAvailabilityStatus.ERROR,
                response_time=time.time() - start_time,
                error_message=str(e)
            )
    
    async def _simulate_model_ping(self, model_id: str):
        """Simulate model ping for health check."""
        # Simulate variable response times
        if "tiny" in model_id.lower():
            await asyncio.sleep(0.1)
        elif "large" in model_id.lower():
            await asyncio.sleep(0.5)
        else:
            await asyncio.sleep(0.2)
    
    async def _get_model_info(self, model_id: str) -> Optional[ModelInfo]:
        """Get model information."""
        # Simulate model info retrieval
        return ModelInfo(
            id=model_id,
            name=model_id,
            display_name=model_id.replace("-", " ").title(),
            type=ModelType.LLAMA_CPP,
            path=f"/models/{model_id}",
            size=1000000,
            modalities=[],
            capabilities=[],
            requirements=None,
            status=ModelStatus.AVAILABLE,
            metadata=None
        )
    
    async def _calculate_compatibility_score(
        self,
        model_info: ModelInfo,
        requirements: List[ModalityRequirement]
    ) -> float:
        """Calculate compatibility score between model and requirements."""
        if not requirements:
            return 1.0
        
        total_score = 0.0
        total_weight = 0.0
        
        for req in requirements:
            weight = 1.0 / req.priority  # Higher priority = higher weight
            
            # Check if model supports this modality
            supports_modality = any(
                m.type == req.modality_type for m in model_info.modalities
            )
            
            if supports_modality:
                score = 1.0
            else:
                # Partial credit for related modalities
                score = 0.3 if req.priority > 1 else 0.0
            
            total_score += score * weight
            total_weight += weight
        
        return total_score / total_weight if total_weight > 0 else 0.0
    
    async def _calculate_modality_coverage(
        self,
        model_info: ModelInfo,
        requirements: List[ModalityRequirement]
    ) -> Dict[ModalityType, float]:
        """Calculate modality coverage for the model."""
        coverage = {}
        
        for req in requirements:
            # Check if model supports this modality
            supports_modality = any(
                m.type == req.modality_type for m in model_info.modalities
            )
            
            coverage[req.modality_type] = 1.0 if supports_modality else 0.0
        
        return coverage
    
    async def _estimate_model_performance(
        self,
        model_id: str,
        requirements: List[ModalityRequirement]
    ) -> float:
        """Estimate model performance for given requirements."""
        # Get baseline performance
        baseline = self.performance_baselines.get(model_id, {})
        
        # Estimate based on model characteristics
        if "tiny" in model_id.lower():
            return 0.9  # Fast but lower quality
        elif "large" in model_id.lower():
            return 0.7  # Slower but higher quality
        else:
            return 0.8  # Balanced
    
    async def _calculate_availability_score(
        self,
        model_id: str,
        health_check: ModelHealthCheck
    ) -> float:
        """Calculate availability score based on health and load."""
        if health_check.status != ModelAvailabilityStatus.AVAILABLE:
            return 0.0
        
        # Factor in response time
        response_time_score = max(0.0, 1.0 - (health_check.response_time / 5.0))
        
        # Factor in current load
        current_load = self.model_loads.get(model_id, 0)
        load_score = max(0.0, 1.0 - (current_load / self.max_concurrent_requests))
        
        # Factor in consecutive failures
        failure_penalty = max(0.0, 1.0 - (health_check.consecutive_failures * 0.2))
        
        return (response_time_score * 0.4 + load_score * 0.4 + failure_penalty * 0.2)
    
    # Load balancing methods
    
    async def acquire_model_slot(self, model_id: str) -> bool:
        """Acquire a slot for model usage."""
        current_load = self.model_loads.get(model_id, 0)
        if current_load >= self.max_concurrent_requests:
            return False
        
        self.model_loads[model_id] = current_load + 1
        return True
    
    async def release_model_slot(self, model_id: str):
        """Release a model usage slot."""
        current_load = self.model_loads.get(model_id, 0)
        if current_load > 0:
            self.model_loads[model_id] = current_load - 1


# Global model availability handler instance
model_availability_handler = ModelAvailabilityHandler()