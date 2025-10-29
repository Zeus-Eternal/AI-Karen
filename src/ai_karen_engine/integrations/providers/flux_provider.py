"""
Flux Provider Implementation

Supports local model execution for Flux image generation models.
"""

import logging
import time
import os
import base64
import io
from typing import Any, Dict, List, Optional, Union
from pathlib import Path

from ai_karen_engine.integrations.llm_utils import LLMProviderBase, GenerationFailed, record_llm_metric

logger = logging.getLogger("kari.flux_provider")


class FluxProvider(LLMProviderBase):
    """Flux provider for advanced image generation."""
    
    def __init__(
        self,
        model: str = "black-forest-labs/FLUX.1-dev",
        model_path: Optional[str] = None,
        variant: str = "dev",
        device: str = "auto",
        torch_dtype: str = "bfloat16",
        enable_cpu_offload: bool = True
    ):
        """
        Initialize Flux provider.
        
        Args:
            model: Model name/path (e.g., "black-forest-labs/FLUX.1-dev")
            model_path: Local path to model files (overrides model if provided)
            variant: Model variant ("dev", "schnell")
            device: Device to use ("cuda", "cpu", or "auto")
            torch_dtype: Torch data type for model ("bfloat16", "float16", "float32")
            enable_cpu_offload: Whether to enable CPU offloading for memory efficiency
        """
        self.model = model
        self.model_path = model_path
        self.variant = variant
        self.device = device
        self.torch_dtype = torch_dtype
        self.enable_cpu_offload = enable_cpu_offload
        self._pipeline = None
        self.last_usage = {}
        
        # Model metadata based on variant
        self.metadata = {
            "type": "image",
            "subtype": "flux",
            "capabilities": ["text2img"],
            "variant": variant,
            "resolution": [1024, 1024],  # Flux typically works at higher resolutions
            "guidance_scale_range": [1.0, 10.0],
            "steps_range": [4, 50] if variant == "schnell" else [20, 100],
            "supports_controlnet": False  # Can be extended later
        }
        
        self._initialize_local_model()
    
    def _initialize_local_model(self):
        """Initialize local Flux pipeline."""
        try:
            from diffusers import FluxPipeline
            import torch
            
            logger.info(f"Loading local Flux model: {self.model} (variant: {self.variant})")
            
            # Determine device
            if self.device == "auto":
                device = "cuda" if torch.cuda.is_available() else "cpu"
            else:
                device = self.device
            
            # Determine torch dtype
            if self.torch_dtype == "bfloat16" and device == "cuda":
                dtype = torch.bfloat16
            elif self.torch_dtype == "float16" and device == "cuda":
                dtype = torch.float16
            else:
                dtype = torch.float32
            
            # Load model from local path or HuggingFace
            model_source = self.model_path if self.model_path else self.model
            
            # Initialize Flux pipeline
            self._pipeline = FluxPipeline.from_pretrained(
                model_source,
                torch_dtype=dtype
            )
            
            # Apply optimizations based on device and settings
            if device == "cuda":
                self._pipeline = self._pipeline.to(device)
                
                # Enable CPU offloading for memory efficiency
                if self.enable_cpu_offload:
                    if hasattr(self._pipeline, "enable_model_cpu_offload"):
                        self._pipeline.enable_model_cpu_offload()
                    elif hasattr(self._pipeline, "enable_sequential_cpu_offload"):
                        self._pipeline.enable_sequential_cpu_offload()
                
                # Enable memory efficient attention if available
                if hasattr(self._pipeline, "enable_attention_slicing"):
                    self._pipeline.enable_attention_slicing()
                
                # Enable VAE slicing for memory efficiency
                if hasattr(self._pipeline, "vae") and hasattr(self._pipeline.vae, "enable_slicing"):
                    self._pipeline.vae.enable_slicing()
            else:
                self._pipeline = self._pipeline.to(device)
            
            # Update metadata based on variant
            self._update_metadata_from_variant()
            
            logger.info(f"Successfully loaded Flux model: {self.model}")
            
        except ImportError:
            raise GenerationFailed(
                "diffusers library with Flux support not installed. "
                "Install with: pip install diffusers[flux] torch transformers accelerate"
            )
        except Exception as ex:
            raise GenerationFailed(f"Failed to load Flux model {self.model}: {ex}")
    
    def _update_metadata_from_variant(self):
        """Update metadata based on model variant."""
        if self.variant == "schnell":
            # Schnell is optimized for speed
            self.metadata["steps_range"] = [1, 8]
            self.metadata["guidance_scale_range"] = [0.0, 2.0]
            self.metadata["description"] = "Fast Flux variant optimized for speed"
        elif self.variant == "dev":
            # Dev is the standard variant
            self.metadata["steps_range"] = [20, 50]
            self.metadata["guidance_scale_range"] = [3.0, 10.0]
            self.metadata["description"] = "Standard Flux variant for high quality"
        
        # Update scheduler information if available
        if self._pipeline and hasattr(self._pipeline, "scheduler"):
            scheduler_name = self._pipeline.scheduler.__class__.__name__
            self.metadata["scheduler_type"] = scheduler_name.lower().replace("scheduler", "")
    
    def generate_text(self, prompt: str, **kwargs) -> str:
        """Generate text response (not applicable for image models, but required by base class)."""
        raise GenerationFailed("Text generation not supported by Flux provider. Use generate_image instead.")
    
    def generate_image(
        self,
        prompt: str,
        width: int = 1024,
        height: int = 1024,
        num_inference_steps: int = None,
        guidance_scale: float = None,
        num_images_per_prompt: int = 1,
        seed: Optional[int] = None,
        max_sequence_length: int = 512,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate image using Flux.
        
        Args:
            prompt: Text prompt for image generation
            width: Image width in pixels
            height: Image height in pixels
            num_inference_steps: Number of denoising steps (auto-selected based on variant if None)
            guidance_scale: Guidance scale (auto-selected based on variant if None)
            num_images_per_prompt: Number of images to generate per prompt
            seed: Random seed for reproducible generation
            max_sequence_length: Maximum sequence length for text encoder
            **kwargs: Additional generation parameters
            
        Returns:
            Dict containing generated images and metadata
        """
        if not self._pipeline:
            raise GenerationFailed("Flux pipeline not initialized")
        
        t0 = time.time()
        
        try:
            import torch
            
            # Set default parameters based on variant
            if num_inference_steps is None:
                num_inference_steps = 4 if self.variant == "schnell" else 28
            
            if guidance_scale is None:
                guidance_scale = 0.0 if self.variant == "schnell" else 3.5
            
            # Set random seed if provided
            if seed is not None:
                torch.manual_seed(seed)
                if torch.cuda.is_available():
                    torch.cuda.manual_seed(seed)
            
            # Generate image
            result = self._pipeline(
                prompt=prompt,
                width=width,
                height=height,
                num_inference_steps=num_inference_steps,
                guidance_scale=guidance_scale,
                num_images_per_prompt=num_images_per_prompt,
                max_sequence_length=max_sequence_length,
                **{k: v for k, v in kwargs.items() if k not in [
                    "prompt", "width", "height", "num_inference_steps", 
                    "guidance_scale", "num_images_per_prompt", "seed", "max_sequence_length"
                ]}
            )
            
            # Convert images to base64 for transport
            images_b64 = []
            for image in result.images:
                buffer = io.BytesIO()
                image.save(buffer, format="PNG")
                img_b64 = base64.b64encode(buffer.getvalue()).decode()
                images_b64.append(img_b64)
            
            # Update usage statistics
            generation_time = time.time() - t0
            self.last_usage = {
                "generation_time": generation_time,
                "num_images": len(result.images),
                "steps": num_inference_steps,
                "guidance_scale": guidance_scale,
                "resolution": f"{width}x{height}",
                "variant": self.variant
            }
            
            # Record metrics
            record_llm_metric(
                "generate_image", generation_time, True, "flux",
                num_images=len(result.images), steps=num_inference_steps, variant=self.variant
            )
            
            return {
                "images": images_b64,
                "prompt": prompt,
                "parameters": {
                    "width": width,
                    "height": height,
                    "num_inference_steps": num_inference_steps,
                    "guidance_scale": guidance_scale,
                    "seed": seed,
                    "max_sequence_length": max_sequence_length,
                    "variant": self.variant
                },
                "metadata": self.metadata,
                "generation_time": generation_time
            }
            
        except Exception as ex:
            record_llm_metric(
                "generate_image", time.time() - t0, False, "flux", error=str(ex)
            )
            raise GenerationFailed(f"Flux image generation failed: {ex}")
    
    def embed(self, text: Union[str, List[str]], **kwargs) -> List[float]:
        """Embedding not supported for image generation models."""
        raise GenerationFailed("Text embedding not supported by Flux provider")
    
    def get_available_models(self) -> List[str]:
        """Get list of available Flux models."""
        return [
            "black-forest-labs/FLUX.1-dev",
            "black-forest-labs/FLUX.1-schnell"
        ]
    
    def is_available(self) -> bool:
        """Check if provider is available."""
        try:
            from diffusers import FluxPipeline
            import torch
            return True
        except ImportError:
            return False
    
    async def get_status(self) -> Dict[str, Any]:
        """Get provider status."""
        try:
            import torch
            
            status = {
                "provider": "flux",
                "model": self.model,
                "variant": self.variant,
                "available": self.is_available(),
                "pipeline_loaded": self._pipeline is not None,
                "device": self.device,
                "torch_dtype": self.torch_dtype,
                "capabilities": self.metadata["capabilities"],
                "resolution": self.metadata["resolution"],
                "steps_range": self.metadata["steps_range"],
                "guidance_scale_range": self.metadata["guidance_scale_range"]
            }
            
            if torch.cuda.is_available():
                status["gpu_available"] = True
                status["gpu_memory"] = torch.cuda.get_device_properties(0).total_memory
                status["cpu_offload_enabled"] = self.enable_cpu_offload
            else:
                status["gpu_available"] = False
            
            return status
            
        except Exception as ex:
            return {
                "provider": "flux",
                "available": False,
                "error": str(ex)
            }
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on Flux provider."""
        try:
            if not self.is_available():
                return {
                    "status": "unhealthy",
                    "error": "Required dependencies not installed (diffusers with Flux support, torch)"
                }
            
            if not self._pipeline:
                return {
                    "status": "unhealthy",
                    "error": "Pipeline not initialized"
                }
            
            # Test image generation with minimal parameters
            start_time = time.time()
            try:
                # Use very small resolution and minimal steps for health check
                test_steps = 1 if self.variant == "schnell" else 4
                test_result = self.generate_image(
                    "test image",
                    width=64,
                    height=64,
                    num_inference_steps=test_steps,
                    guidance_scale=0.0 if self.variant == "schnell" else 1.0
                )
                response_time = time.time() - start_time
                
                health_result = {
                    "status": "healthy",
                    "response_time": response_time,
                    "model_tested": self.model,
                    "variant": self.variant,
                    "capabilities": self.metadata["capabilities"],
                    "resolution": self.metadata["resolution"],
                    "optimal_steps": self.metadata["steps_range"],
                    "optimal_guidance": self.metadata["guidance_scale_range"]
                }
                
            except Exception as e:
                return {
                    "status": "unhealthy",
                    "error": f"Image generation test failed: {str(e)}"
                }
            
            # Add Model Library compatibility check
            try:
                from ai_karen_engine.services.provider_model_compatibility import ProviderModelCompatibilityService
                compatibility_service = ProviderModelCompatibilityService()
                validation = compatibility_service.validate_provider_model_setup("flux")
                
                health_result["model_library"] = {
                    "available": True,
                    "compatible_models_count": validation.get("total_compatible", 0),
                    "validation_status": validation.get("status", "unknown")
                }
                
                if validation.get("total_compatible", 0) == 0:
                    health_result["warnings"] = health_result.get("warnings", [])
                    health_result["warnings"].append("No compatible models found in Model Library")
                
            except Exception as e:
                health_result["model_library"] = {
                    "available": False,
                    "error": str(e)
                }
                health_result["warnings"] = health_result.get("warnings", [])
                health_result["warnings"].append(f"Model Library unavailable: {e}")
            
            return health_result
            
        except Exception as ex:
            return {
                "status": "unhealthy",
                "error": str(ex),
                "model_library": {
                    "available": False,
                    "error": "Provider health check failed"
                }
            }
    
    def get_model_metadata(self) -> Dict[str, Any]:
        """Get detailed model metadata."""
        return {
            **self.metadata,
            "model_name": self.model,
            "model_path": self.model_path,
            "variant": self.variant,
            "device": self.device,
            "torch_dtype": self.torch_dtype,
            "enable_cpu_offload": self.enable_cpu_offload,
            "pipeline_loaded": self._pipeline is not None,
            "last_usage": self.last_usage
        }
    
    def get_generation_parameters(self) -> Dict[str, Any]:
        """Get available generation parameters and their defaults."""
        # Base parameters for Flux
        params = {
            "prompt": {
                "type": "string", 
                "required": True, 
                "description": "Text prompt for image generation"
            },
            "width": {
                "type": "integer", 
                "default": self.metadata["resolution"][0], 
                "min": 256, 
                "max": 2048, 
                "step": 64,
                "description": "Image width in pixels"
            },
            "height": {
                "type": "integer", 
                "default": self.metadata["resolution"][1], 
                "min": 256, 
                "max": 2048, 
                "step": 64,
                "description": "Image height in pixels"
            },
            "num_inference_steps": {
                "type": "integer", 
                "default": 4 if self.variant == "schnell" else 28,
                "min": self.metadata["steps_range"][0], 
                "max": self.metadata["steps_range"][1],
                "description": f"Number of denoising steps (optimal: {self.metadata['steps_range']})"
            },
            "guidance_scale": {
                "type": "float", 
                "default": 0.0 if self.variant == "schnell" else 3.5,
                "min": self.metadata["guidance_scale_range"][0], 
                "max": self.metadata["guidance_scale_range"][1],
                "description": f"Guidance scale (optimal: {self.metadata['guidance_scale_range']})"
            },
            "num_images_per_prompt": {
                "type": "integer", 
                "default": 1, 
                "min": 1, 
                "max": 4,
                "description": "Number of images to generate per prompt"
            },
            "seed": {
                "type": "integer", 
                "required": False, 
                "description": "Random seed for reproducible generation"
            },
            "max_sequence_length": {
                "type": "integer", 
                "default": 512, 
                "min": 128, 
                "max": 1024,
                "description": "Maximum sequence length for text encoder"
            }
        }
        
        return params
    
    def get_optimal_parameters(self) -> Dict[str, Any]:
        """Get optimal generation parameters for current model variant."""
        if self.variant == "schnell":
            return {
                "num_inference_steps": 4,
                "guidance_scale": 0.0,
                "width": 1024,
                "height": 1024,
                "description": "Optimized for speed with minimal steps"
            }
        else:  # dev variant
            return {
                "num_inference_steps": 28,
                "guidance_scale": 3.5,
                "width": 1024,
                "height": 1024,
                "description": "Balanced quality and speed settings"
            }