"""
Model Availability Handler

This service ensures models are available and ready for use.
"""

import logging
import os
import subprocess
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import time


class ModelAvailabilityStatus(Enum):
    """Model availability status."""
    AVAILABLE = "available"
    LOADING = "loading"
    UNAVAILABLE = "unavailable"
    ERROR = "error"


@dataclass
class ModelAvailabilityInfo:
    """Information about model availability."""
    model_id: str
    status: ModelAvailabilityStatus
    load_time_ms: int = 0
    memory_usage_mb: int = 0
    gpu_usage_mb: int = 0
    last_checked: float = 0
    error_message: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


class ModelAvailabilityHandler:
    """
    Model Availability Handler ensures models are available and ready for use.
    
    This service provides model loading, health checking, and resource
    monitoring for GPU/CPU compatibility.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Model Availability Handler.
        
        Args:
            config: Configuration for the availability handler
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Model availability tracking
        self.model_availability: Dict[str, ModelAvailabilityInfo] = {}
        
        # Configuration
        self.health_check_interval = config.get("health_check_interval", 60)  # seconds
        self.load_timeout = config.get("load_timeout", 300)  # seconds
        
        # Start health checker
        self.health_checker_task = asyncio.create_task(self._health_checker_loop())
    
    async def _health_checker_loop(self):
        """Background task to check model health."""
        while True:
            try:
                await self._check_all_models()
                await asyncio.sleep(self.health_check_interval)
            except Exception as e:
                self.logger.error(f"Error in health checker loop: {e}")
                await asyncio.sleep(self.health_check_interval)
    
    async def _check_all_models(self):
        """Check health of all models."""
        for model_id, info in self.model_availability.items():
            if info.status == ModelAvailabilityStatus.AVAILABLE:
                await self._check_model_health(model_id)
    
    async def _check_model_health(self, model_id: str):
        """Check health of a specific model."""
        info = self.model_availability.get(model_id)
        if not info:
            return
        
        try:
            # Check if model process is running
            is_healthy = await self._is_model_healthy(model_id)
            
            if not is_healthy:
                info.status = ModelAvailabilityStatus.ERROR
                info.error_message = "Model health check failed"
                self.logger.warning(f"Model {model_id} health check failed")
            else:
                # Update resource usage
                await self._update_resource_usage(model_id)
                
        except Exception as e:
            info.status = ModelAvailabilityStatus.ERROR
            info.error_message = str(e)
            self.logger.error(f"Error checking model health {model_id}: {e}")
        
        info.last_checked = time.time()
    
    async def _is_model_healthy(self, model_id: str) -> bool:
        """Check if a model is healthy."""
        # Implementation would check actual model health
        # For now, return True
        return True
    
    async def _update_resource_usage(self, model_id: str):
        """Update resource usage for a model."""
        info = self.model_availability.get(model_id)
        if not info:
            return
        
        try:
            # Get memory usage
            memory_usage = await self._get_model_memory_usage(model_id)
            if memory_usage:
                info.memory_usage_mb = memory_usage
            
            # Get GPU usage if available
            gpu_usage = await self._get_model_gpu_usage(model_id)
            if gpu_usage:
                info.gpu_usage_mb = gpu_usage
            
        except Exception as e:
            self.logger.error(f"Error updating resource usage for {model_id}: {e}")
    
    async def _get_model_memory_usage(self, model_id: str) -> Optional[int]:
        """Get memory usage for a model."""
        # Implementation would get actual memory usage
        # For now, return mock value
        return 512  # MB
    
    async def _get_model_gpu_usage(self, model_id: str) -> Optional[int]:
        """Get GPU usage for a model."""
        # Implementation would get actual GPU usage
        # For now, return mock value
        return 1024  # MB
    
    async def load_model(self, model_id: str, model_path: str) -> bool:
        """
        Load a model into memory.
        
        Args:
            model_id: The model ID
            model_path: Path to the model files
            
        Returns:
            True if loaded successfully, False otherwise
        """
        # Check if already loaded
        if model_id in self.model_availability:
            info = self.model_availability[model_id]
            if info.status == ModelAvailabilityStatus.AVAILABLE:
                return True
        
        # Create availability info
        info = ModelAvailabilityInfo(
            model_id=model_id,
            status=ModelAvailabilityStatus.LOADING
        )
        self.model_availability[model_id] = info
        
        try:
            # Load the model
            start_time = time.time()
            
            # Implementation would actually load the model
            # For now, simulate loading
            await asyncio.sleep(2)  # Simulate loading time
            
            # Check if model files exist
            if not os.path.exists(model_path):
                raise Exception(f"Model path does not exist: {model_path}")
            
            # Update info
            info.status = ModelAvailabilityStatus.AVAILABLE
            info.load_time_ms = int((time.time() - start_time) * 1000)
            
            # Update resource usage
            await self._update_resource_usage(model_id)
            
            self.logger.info(f"Loaded model: {model_id}")
            return True
            
        except Exception as e:
            info.status = ModelAvailabilityStatus.ERROR
            info.error_message = str(e)
            self.logger.error(f"Error loading model {model_id}: {e}")
            return False
    
    async def unload_model(self, model_id: str) -> bool:
        """
        Unload a model from memory.
        
        Args:
            model_id: The model ID to unload
            
        Returns:
            True if unloaded successfully, False otherwise
        """
        info = self.model_availability.get(model_id)
        if not info:
            return False
        
        try:
            # Implementation would actually unload the model
            # For now, just update status
            info.status = ModelAvailabilityStatus.UNAVAILABLE
            
            self.logger.info(f"Unloaded model: {model_id}")
            return True
            
        except Exception as e:
            info.status = ModelAvailabilityStatus.ERROR
            info.error_message = str(e)
            self.logger.error(f"Error unloading model {model_id}: {e}")
            return False
    
    async def get_model_availability(self, model_id: str) -> Optional[ModelAvailabilityInfo]:
        """
        Get availability information for a model.
        
        Args:
            model_id: The model ID
            
        Returns:
            Model availability information if found, None otherwise
        """
        return self.model_availability.get(model_id)
    
    async def list_available_models(self) -> List[str]:
        """
        List all available models.
        
        Returns:
            List of available model IDs
        """
        return [
            model_id for model_id, info in self.model_availability.items()
            if info.status == ModelAvailabilityStatus.AVAILABLE
        ]
    
    async def ensure_model_available(self, model_id: str, model_path: str) -> bool:
        """
        Ensure a model is available, loading it if necessary.
        
        Args:
            model_id: The model ID
            model_path: Path to the model files
            
        Returns:
            True if the model is available, False otherwise
        """
        info = self.model_availability.get(model_id)
        
        # Check if already available
        if info and info.status == ModelAvailabilityStatus.AVAILABLE:
            return True
        
        # Load the model
        return await self.load_model(model_id, model_path)
    
    async def get_availability_stats(self) -> Dict[str, Any]:
        """
        Get availability statistics.
        
        Returns:
            Dictionary of statistics
        """
        status_counts = {}
        for status in ModelAvailabilityStatus:
            status_counts[status.value] = sum(
                1 for info in self.model_availability.values()
                if info.status == status
            )
        
        total_memory = sum(info.memory_usage_mb for info in self.model_availability.values())
        total_gpu = sum(info.gpu_usage_mb for info in self.model_availability.values())
        
        return {
            "total_models": len(self.model_availability),
            "status_counts": status_counts,
            "total_memory_mb": total_memory,
            "total_gpu_mb": total_gpu,
            "health_check_interval": self.health_check_interval
        }
    
    async def close(self):
        """Close the availability handler."""
        # Unload all models
        for model_id in list(self.model_availability.keys()):
            await self.unload_model(model_id)
        
        # Cancel health checker task
        if self.health_checker_task:
            self.health_checker_task.cancel()
            try:
                await self.health_checker_task
            except asyncio.CancelledError:
                pass
