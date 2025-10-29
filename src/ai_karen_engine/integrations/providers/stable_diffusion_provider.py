"""
Stable Diffusion Provider Implementation

Supports both local model execution and API-based image generation for Stable Diffusion models.
"""

import logging
import time
import os
import base64
import io
from typing import Any, Dict, List, Optional, Union
from pathlib import Path

from ai_karen_engine.integrations.llm_utils import LLMProviderBase, GenerationFailed, record_llm_metric

logger = logging.getLogger("kari.stable_diffusion_provider")


class StableDiffusionProvider(LLMProviderBase):
    """Stable Diffusion provider for image generation."""
    
    def __init__(
        self,
        model: str = "runwayml/stable-diffusion-v1-5",
        model_path: Optional[str] = None,
        use_local: bool = True,
        device: str = "auto",
        safety_checker: bool = True,
        torch_dtype: str = "float16"
    ):
        """
        Initialize Stable Diffusion provider.
        
        Args:
            model: Model name/path (e.g., "runwayml/stable-diffusion-v1-5")
            model_path: Local path to model files (overrides model if provided)
            use_local: Whether to use local model execution
            device: Device to use ("cuda", "cpu", or "auto")
            safety_checker: Whether to use NSFW safety checker
            torch_dtype: Torch data type for model ("float16", "float32")
        """
        self.model = model
        self.model_path = model_path
        self.use_local = use_local
        self.device = device
        self.safety_checker = safety_checker
        self.torch_dtype = torch_dtype
        self._pipeline = None
        self._img2img_pipeline = None
        self._inpaint_pipeline = None
        self.last_usage = {}
        
        # Model metadata
        self.metadata = {
            "type": "image",
            "subtype": "stable-diffusion",
            "capabilities": ["text2img"],
            "base_model": "SD 1.5",
            "resolution": [512, 512],
            "supports_img2img": False,
            "supports_inpainting": False
        }
        
        if self.use_local:
            self._initialize_local_model()
    
    def _initialize_local_model(self):
        """Initialize local diffusers pipeline."""
        try:
            from diffusers import StableDiffusionPipeline, StableDiffusionImg2ImgPipeline, StableDiffusionInpaintPipeline
            import torch
            
            logger.info(f"Loading local Stable Diffusion model: {self.model}")
            
            # Determine device
            if self.device == "auto":
                device = "cuda" if torch.cuda.is_available() else "cpu"
            else:
                device = self.device
            
            # Determine torch dtype
            dtype = torch.float16 if self.torch_dtype == "float16" and device == "cuda" else torch.float32
            
            # Load model from local path or HuggingFace
            model_source = self.model_path if self.model_path else self.model
            
            # Initialize text-to-image pipeline
            self._pipeline = StableDiffusionPipeline.from_pretrained(
                model_source,
                torch_dtype=dtype,
                safety_checker=None if not self.safety_checker else "default",
                requires_safety_checker=self.safety_checker
            )
            self._pipeline = self._pipeline.to(device)
            
            # Enable memory efficient attention if available
            if hasattr(self._pipeline, "enable_attention_slicing"):
                self._pipeline.enable_attention_slicing()
            
            if hasattr(self._pipeline, "enable_model_cpu_offload") and device == "cuda":
                self._pipeline.enable_model_cpu_offload()
            
            # Update metadata based on loaded model
            self._update_metadata_from_model()
            
            # Initialize additional pipelines if supported
            try:
                self._img2img_pipeline = StableDiffusionImg2ImgPipeline.from_pretrained(
                    model_source,
                    torch_dtype=dtype,
                    safety_checker=None if not self.safety_checker else "default",
                    requires_safety_checker=self.safety_checker
                )
                self._img2img_pipeline = self._img2img_pipeline.to(device)
                self.metadata["supports_img2img"] = True
                self.metadata["capabilities"].append("img2img")
                
                if hasattr(self._img2img_pipeline, "enable_attention_slicing"):
                    self._img2img_pipeline.enable_attention_slicing()
                
            except Exception as e:
                logger.warning(f"Could not load img2img pipeline: {e}")
            
            try:
                self._inpaint_pipeline = StableDiffusionInpaintPipeline.from_pretrained(
                    model_source,
                    torch_dtype=dtype,
                    safety_checker=None if not self.safety_checker else "default",
                    requires_safety_checker=self.safety_checker
                )
                self._inpaint_pipeline = self._inpaint_pipeline.to(device)
                self.metadata["supports_inpainting"] = True
                self.metadata["capabilities"].append("inpainting")
                
                if hasattr(self._inpaint_pipeline, "enable_attention_slicing"):
                    self._inpaint_pipeline.enable_attention_slicing()
                
            except Exception as e:
                logger.warning(f"Could not load inpainting pipeline: {e}")
            
            logger.info(f"Successfully loaded Stable Diffusion model: {self.model}")
            
        except ImportError:
            raise GenerationFailed(
                "diffusers library not installed. Install with: pip install diffusers torch transformers accelerate"
            )
        except Exception as ex:
            raise GenerationFailed(f"Failed to load Stable Diffusion model {self.model}: {ex}")
    
    def _update_metadata_from_model(self):
        """Update metadata based on loaded model characteristics."""
        if not self._pipeline:
            return
        
        try:
            # Try to determine model variant from config
            if hasattr(self._pipeline, "unet") and hasattr(self._pipeline.unet, "config"):
                config = self._pipeline.unet.config
                
                # Check for SDXL
                if hasattr(config, "attention_head_dim") and config.attention_head_dim == [5, 10, 20, 20]:
                    self.metadata["base_model"] = "SDXL"
                    self.metadata["resolution"] = [1024, 1024]
                elif hasattr(config, "cross_attention_dim") and config.cross_attention_dim == 2048:
                    self.metadata["base_model"] = "SDXL"
                    self.metadata["resolution"] = [1024, 1024]
                else:
                    # Default to SD 1.5
                    self.metadata["base_model"] = "SD 1.5"
                    self.metadata["resolution"] = [512, 512]
            
            # Update scheduler type
            if hasattr(self._pipeline, "scheduler"):
                scheduler_name = self._pipeline.scheduler.__class__.__name__
                self.metadata["scheduler_type"] = scheduler_name.lower().replace("scheduler", "")
            
        except Exception as e:
            logger.warning(f"Could not update metadata from model: {e}")
    
    def generate_text(self, prompt: str, **kwargs) -> str:
        """Generate text response (not applicable for image models, but required by base class)."""
        raise GenerationFailed("Text generation not supported by Stable Diffusion provider. Use generate_image instead.")
    
    def generate_image(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        width: int = 512,
        height: int = 512,
        num_inference_steps: int = 20,
        guidance_scale: float = 7.5,
        num_images_per_prompt: int = 1,
        seed: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate image using Stable Diffusion.
        
        Args:
            prompt: Text prompt for image generation
            negative_prompt: Negative prompt to avoid certain features
            width: Image width in pixels
            height: Image height in pixels
            num_inference_steps: Number of denoising steps
            guidance_scale: Guidance scale for classifier-free guidance
            num_images_per_prompt: Number of images to generate per prompt
            seed: Random seed for reproducible generation
            **kwargs: Additional generation parameters
            
        Returns:
            Dict containing generated images and metadata
        """
        if not self._pipeline:
            raise GenerationFailed("Stable Diffusion pipeline not initialized")
        
        t0 = time.time()
        
        try:
            import torch
            
            # Set random seed if provided
            if seed is not None:
                torch.manual_seed(seed)
                if torch.cuda.is_available():
                    torch.cuda.manual_seed(seed)
            
            # Generate image
            result = self._pipeline(
                prompt=prompt,
                negative_prompt=negative_prompt,
                width=width,
                height=height,
                num_inference_steps=num_inference_steps,
                guidance_scale=guidance_scale,
                num_images_per_prompt=num_images_per_prompt,
                **{k: v for k, v in kwargs.items() if k not in [
                    "prompt", "negative_prompt", "width", "height", 
                    "num_inference_steps", "guidance_scale", "num_images_per_prompt", "seed"
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
                "resolution": f"{width}x{height}"
            }
            
            # Record metrics
            record_llm_metric(
                "generate_image", generation_time, True, "stable-diffusion",
                num_images=len(result.images), steps=num_inference_steps
            )
            
            return {
                "images": images_b64,
                "prompt": prompt,
                "negative_prompt": negative_prompt,
                "parameters": {
                    "width": width,
                    "height": height,
                    "num_inference_steps": num_inference_steps,
                    "guidance_scale": guidance_scale,
                    "seed": seed
                },
                "metadata": self.metadata,
                "generation_time": generation_time
            }
            
        except Exception as ex:
            record_llm_metric(
                "generate_image", time.time() - t0, False, "stable-diffusion", error=str(ex)
            )
            raise GenerationFailed(f"Stable Diffusion image generation failed: {ex}")
    
    def generate_img2img(
        self,
        prompt: str,
        image: Union[str, bytes],  # Base64 encoded image or bytes
        strength: float = 0.8,
        negative_prompt: Optional[str] = None,
        num_inference_steps: int = 20,
        guidance_scale: float = 7.5,
        seed: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate image-to-image transformation."""
        if not self._img2img_pipeline:
            raise GenerationFailed("Image-to-image pipeline not available")
        
        try:
            from PIL import Image
            import torch
            
            # Decode input image
            if isinstance(image, str):
                # Assume base64 encoded
                image_data = base64.b64decode(image)
                input_image = Image.open(io.BytesIO(image_data)).convert("RGB")
            else:
                input_image = Image.open(io.BytesIO(image)).convert("RGB")
            
            # Set random seed if provided
            if seed is not None:
                torch.manual_seed(seed)
                if torch.cuda.is_available():
                    torch.cuda.manual_seed(seed)
            
            t0 = time.time()
            
            result = self._img2img_pipeline(
                prompt=prompt,
                image=input_image,
                strength=strength,
                negative_prompt=negative_prompt,
                num_inference_steps=num_inference_steps,
                guidance_scale=guidance_scale,
                **kwargs
            )
            
            # Convert result to base64
            buffer = io.BytesIO()
            result.images[0].save(buffer, format="PNG")
            img_b64 = base64.b64encode(buffer.getvalue()).decode()
            
            generation_time = time.time() - t0
            
            return {
                "images": [img_b64],
                "prompt": prompt,
                "parameters": {
                    "strength": strength,
                    "num_inference_steps": num_inference_steps,
                    "guidance_scale": guidance_scale,
                    "seed": seed
                },
                "generation_time": generation_time
            }
            
        except Exception as ex:
            raise GenerationFailed(f"Image-to-image generation failed: {ex}")
    
    def embed(self, text: Union[str, List[str]], **kwargs) -> List[float]:
        """Embedding not supported for image generation models."""
        raise GenerationFailed("Text embedding not supported by Stable Diffusion provider")
    
    def get_available_models(self) -> List[str]:
        """Get list of available Stable Diffusion models."""
        return [
            "runwayml/stable-diffusion-v1-5",
            "stabilityai/stable-diffusion-2-1",
            "stabilityai/stable-diffusion-xl-base-1.0",
            "CompVis/stable-diffusion-v1-4",
            "stabilityai/stable-diffusion-2-1-base"
        ]
    
    def is_available(self) -> bool:
        """Check if provider is available."""
        try:
            import diffusers
            import torch
            return True
        except ImportError:
            return False
    
    async def get_status(self) -> Dict[str, Any]:
        """Get provider status."""
        try:
            import torch
            
            status = {
                "provider": "stable-diffusion",
                "model": self.model,
                "available": self.is_available(),
                "pipeline_loaded": self._pipeline is not None,
                "device": self.device,
                "torch_dtype": self.torch_dtype,
                "capabilities": self.metadata["capabilities"],
                "supports_img2img": self.metadata["supports_img2img"],
                "supports_inpainting": self.metadata["supports_inpainting"]
            }
            
            if torch.cuda.is_available():
                status["gpu_available"] = True
                status["gpu_memory"] = torch.cuda.get_device_properties(0).total_memory
            else:
                status["gpu_available"] = False
            
            return status
            
        except Exception as ex:
            return {
                "provider": "stable-diffusion",
                "available": False,
                "error": str(ex)
            }
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on Stable Diffusion provider."""
        try:
            if not self.is_available():
                return {
                    "status": "unhealthy",
                    "error": "Required dependencies not installed (diffusers, torch)"
                }
            
            if not self._pipeline:
                return {
                    "status": "unhealthy",
                    "error": "Pipeline not initialized"
                }
            
            # Test image generation with minimal parameters
            start_time = time.time()
            try:
                test_result = self.generate_image(
                    "test image",
                    width=64,
                    height=64,
                    num_inference_steps=1,
                    guidance_scale=1.0
                )
                response_time = time.time() - start_time
                
                health_result = {
                    "status": "healthy",
                    "response_time": response_time,
                    "model_tested": self.model,
                    "capabilities": self.metadata["capabilities"],
                    "base_model": self.metadata["base_model"],
                    "resolution": self.metadata["resolution"]
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
                validation = compatibility_service.validate_provider_model_setup("stable-diffusion")
                
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
            "device": self.device,
            "torch_dtype": self.torch_dtype,
            "safety_checker": self.safety_checker,
            "pipeline_loaded": self._pipeline is not None,
            "last_usage": self.last_usage
        }
    
    def get_generation_parameters(self) -> Dict[str, Any]:
        """Get available generation parameters and their defaults."""
        base_params = {
            "prompt": {"type": "string", "required": True, "description": "Text prompt for image generation"},
            "negative_prompt": {"type": "string", "required": False, "description": "Negative prompt to avoid certain features"},
            "width": {"type": "integer", "default": self.metadata["resolution"][0], "min": 64, "max": 2048, "step": 64},
            "height": {"type": "integer", "default": self.metadata["resolution"][1], "min": 64, "max": 2048, "step": 64},
            "num_inference_steps": {"type": "integer", "default": 20, "min": 1, "max": 100},
            "guidance_scale": {"type": "float", "default": 7.5, "min": 1.0, "max": 20.0},
            "num_images_per_prompt": {"type": "integer", "default": 1, "min": 1, "max": 4},
            "seed": {"type": "integer", "required": False, "description": "Random seed for reproducible generation"}
        }
        
        # Add img2img specific parameters if supported
        if self.metadata["supports_img2img"]:
            base_params["strength"] = {
                "type": "float", "default": 0.8, "min": 0.0, "max": 1.0,
                "description": "Strength of transformation for img2img (only for img2img mode)"
            }
        
        return base_params